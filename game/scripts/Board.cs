using System.Collections.Generic;
using Godot;
using Hexcom.Rules;

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

    // The reach line sits this far inside the hex edges, with corners rounded to this radius:
    // clear of the grid lines, and soft enough not to look like the grid itself.
    private const float ReachInset = 0.12f;
    private const float ReachCorner = 0.25f;

    // Marks lie this far above the drawn ground, enough to win the depth test against it and
    // against each other, and far too little to float.
    private const float ReachLift = 0.015f;
    private const float UnitLift = 0.025f;
    private const float HoverLift = 0.035f;

    private static readonly Color PieceBlue = new(0.16f, 0.36f, 0.82f);

    private Unit _unit = null!;
    private Movement _movement = null!;
    private Reach _reachable = null!;

    private Material _white = null!;
    private Material _accent = null!;
    private MeshInstance3D _piece = null!;
    private MeshInstance3D _reach = null!;
    private MeshInstance3D _unitRing = null!;
    private MeshInstance3D _hover = null!;

    private Hex? _hovered;
    private Hex? _planned;
    private bool _moving;

    public TacticalCamera Camera { get; set; } = null!;

    public Hud Hud { get; set; } = null!;

    public Terrain Terrain { get; set; } = null!;

    /// <summary>A point on the ground to treat as the cursor, for captures. Null reads the mouse.</summary>
    public Vector2? PointerOverride { get; set; }

    /// <summary>The hex the unit starts on.</summary>
    public Hex Start { get; set; } = new(0, 0);

    /// <summary>Whether a move is being animated, during which nothing else is accepted.</summary>
    public bool Busy => _moving;

    public Unit Unit => _unit;

    /// <summary>The token's mesh, so a portrait can be rendered from the same thing that stands on the board.</summary>
    public Mesh PieceMesh => _piece.Mesh;

    public override void _Ready()
    {
        // Marks lie on the drawn ground and are depth tested like anything else on it, so a
        // piece standing on a ring hides the far side of it. The cursor and reach marks are
        // white; the ring under the active unit is the HUD's own colour, the one thing on the
        // board that says "this is yours".
        _white = Overlay(Colors.White);
        _accent = Overlay(SciFi.Accent);

        _movement = new Movement(Terrain);
        _unit = new Unit(Start);

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

        _reach = new MeshInstance3D { Name = "Reach" };
        _unitRing = new MeshInstance3D { Name = "UnitRing" };
        _hover = new MeshInstance3D { Name = "Hover", Visible = false };

        AddChild(_piece);
        AddChild(_reach);
        AddChild(_unitRing);
        AddChild(_hover);

        RefreshReach();
        RefreshUnitRing();
        RefreshHover();
    }

    public override void _Process(double delta)
    {
        // The ring walks with the piece, rebuilt each frame so it keeps to the ground.
        if (_moving) RefreshUnitRing();

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
        if (@event is InputEventMouseButton { ButtonIndex: MouseButton.Left, Pressed: true } && !_moving && _planned is { } to)
        {
            Order(to);
        }
    }

    /// <summary>Move to a hex if it is in reach; false if it is not.</summary>
    public bool OrderTo(Hex target)
    {
        if (_moving || target == _unit.Position || !_reachable.Contains(target)) return false;
        Order(target);
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

    /// <summary>Walk the cheapest way to a hex in reach, paying for it first.</summary>
    /// <remarks>
    /// The way there is the reach query's, not a straight line: with slopes and roads priced
    /// the cheapest route bends, and the piece walking it is how the player sees that.
    /// </remarks>
    private void Order(Hex destination)
    {
        if (_reachable.CostTo(destination) is not { } cost || !_unit.CanAfford(cost)) return;
        var path = _reachable.PathTo(destination);

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

        tween.Finished += () =>
        {
            _unit.Position = destination;
            _moving = false;
            RefreshReach();
            RefreshUnitRing();
            RefreshHover();
        };
    }

    /// <summary>The ring under the active unit, the same size as the cursor's so the two coincide when it is pointed at.</summary>
    private void RefreshUnitRing()
    {
        _unitRing.Mesh = Meshes.Ring(_piece.Position, HoverRadius, HoverWidth, _accent, Drape(UnitLift));
    }

    /// <summary>Redraw the edge of what the unit can reach from where it stands with what it has.</summary>
    /// <remarks>
    /// The hex edges that face out of the reachable set are the boundary, and the line follows
    /// them: <see cref="Outline"/> links them into loops, sets the line a little inside the
    /// edges and rounds the corners. With reach priced by the ground the boundary is notched
    /// and bent, and a line that follows it is the one that means something.
    /// </remarks>
    private void RefreshReach()
    {
        _reachable = _movement.Reachable(_unit.Position, _unit.Ap, _unit.Profile);

        // A unit that can only stand where it is has no reach to outline; the ring under it
        // already says where it is, and a second ring of another size would only argue with it.
        if (_reachable.Count <= 1)
        {
            _reach.Mesh = null;
            return;
        }

        // An edge is on the outline when the hex across it is out of reach.
        var edges = new List<(Vector2, Vector2)>();
        foreach (var hex in _reachable.Hexes)
        {
            for (var d = 0; d < 6; d++)
            {
                if (_reachable.Contains(hex.Neighbour(d))) continue;
                edges.Add((ToPlane(hex.Corner(d)), ToPlane(hex.Corner(d + 1))));
            }
        }

        var loops = Outline.Smooth(edges, ReachInset, ReachCorner);

        var polylines = new List<IReadOnlyList<Vector3>>(loops.Count);
        foreach (var loop in loops)
        {
            var points = new List<Vector3>(loop.Count + 1);
            foreach (var p in loop) points.Add(new Vector3(p.X, 0f, p.Y));
            points.Add(points[0]);
            polylines.Add(points);
        }

        _reach.Mesh = Meshes.Ribbons(polylines, ReachWidth, _white, Drape(ReachLift));
    }

    /// <summary>Lay a mark on the drawn ground, a set height above it.</summary>
    private Meshes.HeightAt Drape(float lift) => (x, z) => TerrainView.MeshHeight(Terrain, x, z) + lift;

    private static StandardMaterial3D Overlay(Color colour) => new()
    {
        ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded,
        AlbedoColor = colour,
        CullMode = BaseMaterial3D.CullModeEnum.Disabled,
    };

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
        _hover.Mesh = Meshes.Ring(ToScene(hovered), HoverRadius, HoverWidth, _white, Drape(HoverLift));

        if (!_moving && hovered != _unit.Position && _reachable.CostTo(hovered) is { } cost)
        {
            _planned = hovered;
            Hud.ShowAp(_unit.Ap, Unit.MaxAp, cost);
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
