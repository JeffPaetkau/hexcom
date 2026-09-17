using System;
using System.Collections.Generic;
using Godot;
using Hexcom.Rules;

namespace Hexcom.Game;

/// <summary>
/// The board: one unit as a blue wooden piece, the rings on the ground that say where the
/// cursor is and which unit is active, and the marks on the hexes the unit can reach.
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

    // Animations are timed to the turn (a step takes the share of the ten seconds it cost) and
    // then played this many times faster. One is real time; two keeps the proportions while
    // halving the wait, which is what a player watching several units will want.
    public const float PlaybackSpeed = 2f;

    // The cursor ring and every hex mark share one size, just inside the hex, whose edges are
    // half a metre from its centre, so a mark and the cursor over it coincide.
    private const float HoverRadius = 0.46f;
    private const float HoverWidth = 0.05f;

    // Rings lie this far above the drawn ground, enough to win the depth test against it and
    // against each other, and far too little to float.
    private const float UnitLift = 0.025f;
    private const float HoverLift = 0.035f;

    private static readonly Color PieceBlue = new(0.16f, 0.36f, 0.82f);

    private Unit _unit = null!;
    private Movement _movement = null!;

    // What the unit can reach carefully, and what it can reach if it hurries down the slopes.
    private Reach _reachable = null!;
    private Reach _hurried = null!;

    // The dice for falls. One seed, so a run of the game can be replayed until there is a
    // proper seeded source of chance in the rules.
    private readonly Random _dice = new(7);

    private Material _white = null!;
    private Material _accent = null!;
    private MeshInstance3D _piece = null!;
    private MeshInstance3D _unitRing = null!;
    private MeshInstance3D _hover = null!;
    private HexMarks _marks = null!;

    // Which hexes carry a mark, so a walk can take away the ones that fall out of reach.
    private readonly HashSet<Hex> _shown = new();

    private Hex? _hovered;
    private Hex? _planned;
    private bool _moving;

    public TacticalCamera Camera { get; set; } = null!;

    public Hud Hud { get; set; } = null!;

    public Terrain Terrain { get; set; } = null!;

    /// <summary>The ground's material, which paints the marks on the hexes.</summary>
    public ShaderMaterial Surface { get; set; } = null!;

    /// <summary>A point on the ground to treat as the cursor, for captures. Null reads the mouse.</summary>
    public Vector2? PointerOverride { get; set; }

    /// <summary>Whether every hurried step falls, for picturing a fall.</summary>
    public bool AlwaysTrip { get; set; }

    /// <summary>The hex the unit starts on.</summary>
    public Hex Start { get; set; } = new(0, 0);

    /// <summary>Whether a move is being animated, during which nothing else is accepted.</summary>
    public bool Busy => _moving;

    public Unit Unit => _unit;

    /// <summary>The token's mesh, so a portrait can be rendered from the same thing that stands on the board.</summary>
    public Mesh PieceMesh => _piece.Mesh;

    /// <summary>How many hexes carry a mark, for the capture's console line.</summary>
    public int MarkCount => _shown.Count;

    public override void _Ready()
    {
        // Rings lie on the drawn ground and are depth tested like anything else on it, so a
        // piece standing on a ring hides the far side of it. The cursor ring is white; the ring
        // under the active unit is the HUD's own colour, the one thing on the board that says
        // "this is yours". The marks on the hexes in reach are painted by the ground itself.
        _white = Overlay(Colors.White);
        _accent = Overlay(SciFi.Accent);
        _marks = new HexMarks(Surface, HoverRadius);

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

        _unitRing = new MeshInstance3D { Name = "UnitRing" };
        _hover = new MeshInstance3D { Name = "Hover", Visible = false };

        AddChild(_piece);
        AddChild(_unitRing);
        AddChild(_hover);

        RefreshReach();
        RefreshUnitRing();
        RefreshHover();
    }

    public override void _Process(double delta)
    {
        // The ring walks with the piece, rebuilt each frame so it keeps to the ground, and the
        // marks that are fading do so a frame at a time.
        if (_moving) RefreshUnitRing();
        _marks.Tick((float)delta);

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

    /// <summary>Move to a hex if it is in reach, hurrying if that is the only way; false if it is not.</summary>
    public bool OrderTo(Hex target)
    {
        if (_moving || target == _unit.Position || !_hurried.Contains(target)) return false;
        Order(target);
        return true;
    }

    /// <summary>A new turn: the unit's points come back.</summary>
    public void EndTurn()
    {
        if (_moving) return;
        _unit.Refresh();
        Hud.ShowNote(null);
        RefreshReach();
        RefreshHover();
    }

    /// <summary>Walk the cheapest way to a hex in reach, paying for it first.</summary>
    /// <remarks>
    /// The way there is the reach query's, not a straight line: with slopes and roads priced
    /// the cheapest route bends, and the piece walking it is how the player sees that. A hex
    /// the unit can get to carefully is got to carefully, whatever a hurried way would save;
    /// clicking a hex that only hurrying reaches is accepting the risk.
    /// </remarks>
    private void Order(Hex destination)
    {
        var reach = _reachable.Contains(destination) ? _reachable : _hurried;
        if (reach.CostTo(destination) is not { } cost || !_unit.CanAfford(cost)) return;
        var path = reach.PathTo(destination);
        var before = _unit.Ap;

        // A hurried step may end in a fall. The dice are thrown now for every hurried step on
        // the way and the walk is cut short at the first that comes up: the animation only
        // ever shows what has already happened.
        var end = path.Count - 1;
        var fell = false;
        for (var i = 1; i < path.Count; i++)
        {
            if (!reach.HurriedInto(path[i])) continue;
            var roll = AlwaysTrip ? 0.0 : _dice.NextDouble();
            if (roll < _movement.TripChance(path[i - 1], path[i]))
            {
                end = i;
                fell = true;
                break;
            }
        }

        _unit.Spend(cost);
        _moving = true;
        _planned = null;
        Hud.ShowAp(_unit.Ap, Unit.MaxAp, null);

        // Each step takes the share of the turn it cost, at playback speed: a stride on the
        // flat is half a second of turn, a climb longer, a road quicker. What the player
        // watches is the price. The marks stay through the walk, and with each step the hexes
        // that could no longer be afforded from the hex being stepped to fade out over that
        // step, so the reach is seen to shrink as the points are walked away.
        var tween = CreateTween();
        for (var i = 1; i <= end; i++)
        {
            var to = path[i];
            var step = reach.CostTo(to)!.Value - reach.CostTo(path[i - 1])!.Value;
            var seconds = step * Units.TurnSeconds / Unit.MaxAp / PlaybackSpeed;
            var left = before - reach.CostTo(to)!.Value;
            tween.TweenCallback(Callable.From(() => FadeOutOfReach(to, left, seconds)));
            tween.TweenProperty(_piece, "position", ToScene(to), seconds);
        }

        tween.Finished += () =>
        {
            _unit.Position = path[end];
            _moving = false;

            // A fall costs whatever was left of the turn. Going prone and getting hurt come later.
            if (fell)
            {
                _unit.Spend(_unit.Ap);
                Hud.ShowNote("FELL ON THE SLOPE");
            }

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

    /// <summary>Mark every hex the unit can reach from where it stands with what it has.</summary>
    /// <remarks>
    /// One disc per hex, the size of the cursor's ring: grey where a careful way fits the
    /// points, orange where only a hurried way down a slope does, with its chance of a fall.
    /// The marks are per hex rather than an outline of the set because a hex can mean more
    /// than one thing, and colour is how it says which; red waits for danger. The unit's own
    /// hex is marked like any other, under its ring, so the field of marks has no hole and
    /// none opens behind a unit as it walks.
    /// </remarks>
    private void RefreshReach()
    {
        _reachable = _movement.Reachable(_unit.Position, _unit.Ap, _unit.Profile);
        _hurried = _movement.Reachable(_unit.Position, _unit.Ap, _unit.Profile, hurrying: true);

        _shown.Clear();
        _shown.UnionWith(_hurried.Hexes);
        _marks.Set(_unit.Position, Coloured());
    }

    private IEnumerable<(Hex, Color)> Coloured()
    {
        foreach (var hex in _shown) yield return (hex, _reachable.Contains(hex) ? SciFi.MarkMove : SciFi.MarkWarning);
    }

    /// <summary>The cost of getting to a hex and the risk on the way: careful if a careful way fits the points, hurried otherwise, or null.</summary>
    private (int Cost, double Risk)? WayTo(Hex hex)
    {
        if (_reachable.CostTo(hex) is { } careful) return (careful, 0);
        if (_hurried.CostTo(hex) is { } quick) return (quick, _hurried.RiskTo(hex)!.Value);
        return null;
    }

    /// <summary>
    /// Take the marks off every hex that can no longer be afforded from a hex with a budget,
    /// fading them out over some seconds, and keep the rest.
    /// </summary>
    private void FadeOutOfReach(Hex from, int budget, float seconds)
    {
        var still = _movement.Reachable(from, budget, _unit.Profile, hurrying: true);

        var leaving = new List<Hex>();
        foreach (var hex in _shown)
        {
            if (!still.Contains(hex)) leaving.Add(hex);
        }

        if (leaving.Count == 0) return;

        _shown.ExceptWith(leaving);
        _marks.Fade(leaving, seconds);
    }

    /// <summary>Lay a mark on the drawn ground, a set height above it.</summary>
    private Meshes.HeightAt Drape(float lift) => (x, z) => TerrainView.MeshHeight(Terrain, x, z) + lift;

    /// <summary>A flat, unlit colour for a mark on the ground; see-through if the colour is.</summary>
    private static StandardMaterial3D Overlay(Color colour) => new()
    {
        ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded,
        AlbedoColor = colour,
        CullMode = BaseMaterial3D.CullModeEnum.Disabled,
        Transparency = colour.A < 1f ? BaseMaterial3D.TransparencyEnum.Alpha : BaseMaterial3D.TransparencyEnum.Disabled,
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

        if (!_moving && hovered != _unit.Position && WayTo(hovered) is { } way)
        {
            _planned = hovered;
            Hud.ShowAp(_unit.Ap, Unit.MaxAp, way.Cost, way.Risk);
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
