using System.Collections.Generic;
using Godot;
using Hexcom.Game.Rules;

namespace Hexcom.Game;

/// <summary>
/// The board: one unit as a blue wooden piece, and the white marks on the ground that say
/// where the cursor is, how far the unit can go, and the way there.
/// </summary>
/// <remarks>
/// The rules are asked, never guessed at: what is reachable and what a path costs come from
/// <see cref="Movement"/>, and the piece only animates what the unit has already paid for.
/// </remarks>
public partial class Board : Node3D
{
    // The proportions of a standing adult: 1.8 m tall (v1's standing body height) and about
    // 0.44 m across the shoulders, on the one-metre-per-unit scale.
    private const float PieceRadius = 0.22f;
    private const float PieceHeight = 1.8f;
    private const float PieceChamfer = 0.04f;
    private const float MoveMetresPerSecond = 5f;

    private const float HoverRadius = 0.8f;
    private const float HoverWidth = 0.06f;
    private const float ReachWidth = 0.06f;

    private static readonly Color PieceBlue = new(0.16f, 0.36f, 0.82f);

    private readonly Unit _unit = new(new Hex(0, 0));
    private HashSet<Hex> _reachable = new();

    private Material _overlay = null!;
    private MeshInstance3D _piece = null!;
    private MeshInstance3D _reach = null!;
    private MeshInstance3D _hover = null!;

    private Hex? _hovered;
    private IReadOnlyList<Hex>? _planned;
    private bool _moving;

    public TacticalCamera Camera { get; set; } = null!;

    public Hud Hud { get; set; } = null!;

    public Terrain Terrain { get; set; } = null!;

    /// <summary>A point on the ground to treat as the cursor, for captures. Null reads the mouse.</summary>
    public Vector2? PointerOverride { get; set; }

    /// <summary>Whether a move is being animated, during which nothing else is accepted.</summary>
    public bool Busy => _moving;

    public Unit Unit => _unit;

    /// <summary>The token's mesh, so a portrait can be rendered from the same thing that stands on the board.</summary>
    public Mesh PieceMesh => _piece.Mesh;

    public override void _Ready()
    {
        // Marks on the ground draw over everything: they follow the height function, and a
        // coarse far chunk can cut through them where the mesh straightens a curve.
        _overlay = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded,
            AlbedoColor = Colors.White,
            CullMode = BaseMaterial3D.CullModeEnum.Disabled,
            NoDepthTest = true,
            RenderPriority = 1,
        };

        var paint = new StandardMaterial3D
        {
            AlbedoColor = PieceBlue,
            Roughness = 0.5f,
            CullMode = BaseMaterial3D.CullModeEnum.Disabled,
        };

        _piece = new MeshInstance3D
        {
            Name = "Piece",
            Mesh = Meshes.HexPrism(PieceRadius, PieceHeight, PieceChamfer, paint),
            Position = ToScene(_unit.Position),
        };

        // Stacked a little above the ground and each other so none of them z-fights.
        _reach = new MeshInstance3D { Name = "Reach", Position = Vector3.Up * 0.015f };
        _hover = new MeshInstance3D { Name = "Hover", Visible = false, Position = Vector3.Up * 0.025f };

        AddChild(_piece);
        AddChild(_reach);
        AddChild(_hover);

        RefreshReach();
        RefreshHover();
    }

    public override void _Process(double delta)
    {
        // While the mouse is moving the camera it is not pointing at a hex.
        var point = Camera.Dragging ? null : PointerOverride ?? PointUnderMouse();
        Hex? hovered = point is { } p ? Hex.At(p.X, p.Y) : null;

        if (hovered != _hovered)
        {
            _hovered = hovered;
            RefreshHover();
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is InputEventMouseButton { ButtonIndex: MouseButton.Left, Pressed: true } && !_moving && _planned is { } path)
        {
            Order(path);
        }
    }

    /// <summary>Move to a hex if it is in reach; false if it is not.</summary>
    public bool OrderTo(Hex target)
    {
        if (_moving || target == _unit.Position || !_reachable.Contains(target)) return false;
        Order(Movement.Path(_unit.Position, target));
        return true;
    }

    /// <summary>A new turn: the unit's points come back.</summary>
    public void EndTurn()
    {
        if (_moving) return;
        _unit.Refresh();
        RefreshReach();
        RefreshHover();
    }

    private void Order(IReadOnlyList<Hex> path)
    {
        var cost = Movement.Cost(path);
        if (!_unit.CanAfford(cost)) return;

        _unit.Spend(cost);
        _moving = true;
        _planned = null;
        _reach.Mesh = null;
        Hud.ShowAp(_unit.Ap, Unit.MaxAp, null);

        var perHex = Units.HexSize * 1.7320508f / MoveMetresPerSecond;
        var tween = CreateTween();
        for (var i = 1; i < path.Count; i++)
        {
            tween.TweenProperty(_piece, "position", ToScene(path[i]), perHex);
        }

        var destination = path[^1];
        tween.Finished += () =>
        {
            _unit.Position = destination;
            _moving = false;
            RefreshReach();
            RefreshHover();
        };
    }

    /// <summary>Redraw the edge of what the unit can reach from where it stands with what it has.</summary>
    /// <remarks>
    /// The hex edges that face out of the reachable set are the true boundary, but drawn as
    /// they are they zigzag. <see cref="Outline"/> straightens them along the outer tips of the
    /// rim hexes, so every reachable hex stays inside the line, and rounds the corners to the
    /// hover ring's radius, so the two marks read as one family.
    /// </remarks>
    private void RefreshReach()
    {
        _reachable = Movement.Reachable(_unit.Position, _unit.Ap);

        // An edge is on the outline when the hex across it is out of reach.
        var edges = new List<(Vector2, Vector2)>();
        foreach (var hex in _reachable)
        {
            for (var d = 0; d < 6; d++)
            {
                if (_reachable.Contains(hex.Neighbour(d))) continue;
                edges.Add((ToPlane(hex.Corner(d)), ToPlane(hex.Corner(d + 1))));
            }
        }

        var loops = Outline.Smooth(edges, 0.55f * Units.HexSize, 0f, HoverRadius);

        var polylines = new List<IReadOnlyList<Vector3>>(loops.Count);
        foreach (var loop in loops)
        {
            var points = new List<Vector3>(loop.Count + 1);
            foreach (var p in loop) points.Add(new Vector3(p.X, 0f, p.Y));
            points.Add(points[0]);
            polylines.Add(points);
        }

        _reach.Mesh = Meshes.Ribbons(polylines, ReachWidth, _overlay, Drape);
    }

    private float Drape(float x, float z) => (float)Terrain.Height(x, z);

    /// <summary>Move the ring under the cursor, plan the path to it, and tell the HUD the cost.</summary>
    /// <remarks>The path is planned but not drawn: the ring and the cost are what the player sees.</remarks>
    private void RefreshHover()
    {
        if (_hovered is not { } hovered)
        {
            _hover.Visible = false;
            _planned = null;
            Hud.ShowAp(_unit.Ap, Unit.MaxAp, null);
            return;
        }

        _hover.Visible = true;
        _hover.Mesh = Meshes.Ring(ToScene(hovered), HoverRadius, HoverWidth, _overlay, Drape);

        if (!_moving && hovered != _unit.Position && _reachable.Contains(hovered))
        {
            _planned = Movement.Path(_unit.Position, hovered);
            Hud.ShowAp(_unit.Ap, Unit.MaxAp, Movement.Cost(_planned));
        }
        else
        {
            _planned = null;
            Hud.ShowAp(_unit.Ap, Unit.MaxAp, null);
        }
    }

    private Vector2? PointUnderMouse()
    {
        var ground = Camera.GroundUnder(GetViewport().GetMousePosition());
        return ground is { } g ? new Vector2(g.X, g.Z) : null;
    }

    /// <summary>The centre of a hex, on the ground.</summary>
    private Vector3 ToScene(Hex hex)
    {
        var (x, z) = hex.Centre;
        return new Vector3((float)x, (float)Terrain.Height(x, z), (float)z);
    }

    private static Vector2 ToPlane((double X, double Z) plane) => new((float)plane.X, (float)plane.Z);
}
