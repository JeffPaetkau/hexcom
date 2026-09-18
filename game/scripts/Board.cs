using System;
using System.Collections.Generic;
using Godot;
using Hexcom.Rules;
using Side = Hexcom.Rules.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>
/// The board: two units as wooden pieces, ours blue and theirs red, the rings on the ground
/// that say where the cursor is and whose turn it is, the marks on the hexes the active unit
/// can reach and on the enemy it can shoot, and the tracer of a shot.
/// </summary>
/// <remarks>
/// The rules are asked, never guessed at: what is reachable and what a path costs come from
/// <see cref="Movement"/>, whether a shot can be taken and what it does from
/// <see cref="Shooting"/>, and the pieces only animate what the units have already paid for.
/// The turns alternate, ours then theirs, and both are played from the same mouse until there
/// is an opponent to play the other: End Turn passes the board to the other unit.
/// </remarks>
public partial class Board : Node3D
{
    // The proportions of a standing adult: 1.8 m tall (v1's standing body height) and about
    // 0.44 m across the shoulders, on the one-metre-per-unit scale.
    private const float PieceRadius = 0.22f;
    private const float PieceHeight = 1.8f;
    private const float PieceChamfer = 0.04f;

    // The nose that says which way a piece faces sits at eye height (v1's standing eye, 1.65 m),
    // where the look it stands for will come from.
    private const float NoseHeight = 1.65f;

    // A right button that comes up within this many pixels of where it went down is a click,
    // an order to face that way; further is the orbit the camera was already doing.
    private const float ClickSlop = 6f;

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

    // A round leaves the rifle at chest height and is aimed at the target's, a little lower
    // for the drop; a miss goes on past the target and a hand's width to one side of it.
    private const float MuzzleHeight = 1.3f;
    private const float ChestHeight = 1.15f;
    private const float MissPast = 4f;
    private const float MissAside = 0.5f;
    private const float TracerWidth = 0.03f;

    // A tracer is on screen for the moment a round takes to arrive and then fades; a piece
    // put down topples in a little over half a second.
    private const float TracerSeconds = 0.12f;
    private const float TracerFadeSeconds = 0.3f;
    private const float ToppleSeconds = 0.6f;

    private static readonly Color PieceBlue = new(0.16f, 0.36f, 0.82f);
    private static readonly Color PieceRed = new(0.80f, 0.18f, 0.14f);

    private readonly List<Unit> _units = new();
    private readonly Dictionary<Unit, MeshInstance3D> _pieces = new();
    private readonly Dictionary<Unit, StandardMaterial3D> _paints = new();
    private int _active;
    private Movement _movement = null!;

    // What the active unit makes out, and the fog drawn from it.
    private Sight _sight = null!;
    private View _view = null!;
    private SightField _field = null!;

    // What the active unit can reach carefully, and what it can reach if it hurries down the slopes.
    private Reach _reachable = null!;
    private Reach _hurried = null!;

    // The dice for falls and for shots. One seed, so a run of the game can be replayed until
    // there is a proper seeded source of chance in the rules.
    private readonly Random _dice = new(7);

    private Material _white = null!;
    private Material _accent = null!;
    private Material _hostile = null!;
    private Material _tracerGlow = null!;
    private Material _nose = null!;

    // Where the right button went down, and how far the mouse has gone since: a click faces the unit that way.
    private Hex? _rightPressedOn;
    private Vector2 _rightMoved;
    private MeshInstance3D _unitRing = null!;
    private MeshInstance3D _hover = null!;
    private MeshInstance3D _tracer = null!;
    private HexMarks _marks = null!;

    // Which hexes carry a movement mark, so a walk can take away the ones that fall out of reach.
    private readonly HashSet<Hex> _shown = new();

    private Hex? _hovered;
    private Hex? _planned;
    private Unit? _target;
    private bool _busy;

    public TacticalCamera Camera { get; set; } = null!;

    public Hud Hud { get; set; } = null!;

    public Terrain Terrain { get; set; } = null!;

    /// <summary>The ground's material, which paints the marks on the hexes.</summary>
    public ShaderMaterial Surface { get; set; } = null!;

    /// <summary>The dials on seeing: the weather, above all.</summary>
    public SightModel SightModel { get; set; } = SightModel.Default;

    /// <summary>A point on the ground to treat as the cursor, for captures. Null reads the mouse.</summary>
    public Vector2? PointerOverride { get; set; }

    /// <summary>Whether every hurried step falls, for picturing a fall.</summary>
    public bool AlwaysTrip { get; set; }

    /// <summary>A roll to use for every shot instead of the dice, for picturing a hit or a miss without luck. Null throws the dice.</summary>
    public double? ShotRoll { get; set; }

    /// <summary>The hex our unit starts on.</summary>
    public Hex Start { get; set; } = new(0, 0);

    /// <summary>The hex the enemy starts on.</summary>
    public Hex EnemyStart { get; set; } = new(5, 0);

    /// <summary>Whether a move or a shot is being animated, during which nothing else is accepted.</summary>
    public bool Busy => _busy;

    /// <summary>The unit whose turn it is.</summary>
    public Unit Unit => _units[_active];

    /// <summary>Every unit on the board, ours first. Not named for the type, which the Units class already is.</summary>
    public IReadOnlyList<Unit> Roster => _units;

    /// <summary>The active unit's token mesh, so a portrait can be rendered from the same thing that stands on the board.</summary>
    public Mesh PieceMesh => _pieces[Unit].Mesh;

    /// <summary>How many hexes carry a movement mark, for the capture's console line.</summary>
    public int MarkCount => _shown.Count;

    public override void _Ready()
    {
        // Rings lie on the drawn ground and are depth tested like anything else on it, so a
        // piece standing on a ring hides the far side of it. The cursor ring is white; the ring
        // under the active unit is its side's colour, the HUD's cyan for ours and the danger
        // red for theirs, so whose turn it is reads from the board. The marks on the hexes in
        // reach are painted by the ground itself.
        _white = Overlay(Colors.White);
        _accent = Overlay(SciFi.Accent);
        _hostile = Overlay(SciFi.Danger);
        _tracerGlow = Overlay(SciFi.Tracer);
        _nose = Overlay(SciFi.Text);
        _marks = new HexMarks(Surface, HoverRadius);

        _movement = new Movement(Terrain);
        _sight = new Sight(Terrain, SightModel);

        // The fog pass: a quad the shader stretches over the whole screen, drawn after every
        // transparent thing, never culled wherever the camera is.
        var fog = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fog.gdshader"), RenderPriority = 127 };
        fog.SetShaderParameter("hex_size", (float)Units.HexSize);
        _field = new SightField(fog);
        AddChild(new MeshInstance3D
        {
            Name = "Fog",
            Mesh = new QuadMesh { Size = new Vector2(2f, 2f), Material = fog },
            CustomAabb = new Aabb(new Vector3(-1e6f, -1e6f, -1e6f), new Vector3(2e6f, 2e6f, 2e6f)),
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        });

        // The two start facing each other: there is nothing else on the board to face.
        var ours = new Unit(Start, Side.Player, "UNIT 1", facing: Facing.Toward(Start, EnemyStart) ?? 0);
        var theirs = new Unit(EnemyStart, Side.Hostile, "HOSTILE 1", facing: Facing.Toward(EnemyStart, Start) ?? 0);
        Place(ours, PieceBlue);
        Place(theirs, PieceRed);

        _unitRing = new MeshInstance3D { Name = "UnitRing" };
        _hover = new MeshInstance3D { Name = "Hover", Visible = false };
        _tracer = new MeshInstance3D { Name = "Tracer", Visible = false, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };

        AddChild(_unitRing);
        AddChild(_hover);
        AddChild(_tracer);

        Hud.ShowUnit(Unit);
        RefreshReach(fade: false);
        RefreshUnitRing();
        RefreshHover();
    }

    /// <summary>Put a unit on the board as a piece of its side's colour.</summary>
    private void Place(Unit unit, Color colour)
    {
        var paint = new StandardMaterial3D
        {
            AlbedoColor = colour,
            Roughness = 0.5f,
            CullMode = BaseMaterial3D.CullModeEnum.Disabled,
        };

        var piece = new MeshInstance3D
        {
            Name = unit.Name.Replace(' ', '_'),
            Mesh = Meshes.HexPrism(PieceRadius, PieceHeight, PieceChamfer, paint, _nose, NoseHeight),
            Position = ToScene(unit.Position),
            Rotation = new Vector3(0f, Heading(unit.Facing), 0f),
        };

        _units.Add(unit);
        _pieces[unit] = piece;
        _paints[unit] = paint;
        AddChild(piece);
    }

    public override void _Process(double delta)
    {
        // The ring walks with the piece, rebuilt each frame so it keeps to the ground, and the
        // marks that are fading do so a frame at a time.
        if (_busy) RefreshUnitRing();
        _marks.Tick((float)delta);
        _field.Tick((float)delta);

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
        switch (@event)
        {
            case InputEventMouseButton { ButtonIndex: MouseButton.Left, Pressed: true } when !_busy:
                if (_target is { } target) Fire(target);
                else if (_planned is { } to) Order(to);
                break;

            // The right button is the camera's orbit, and a click of it, down and up without
            // moving, faces the unit towards the hex it was on. The hex is taken at the press,
            // because the camera captures the mouse while the button is held and there is no
            // cursor on the ground at the release.
            case InputEventMouseButton { ButtonIndex: MouseButton.Right, Pressed: true }:
                _rightPressedOn = _hovered;
                _rightMoved = Vector2.Zero;
                break;

            case InputEventMouseButton { ButtonIndex: MouseButton.Right, Pressed: false }:
                if (_rightPressedOn is { } toward && _rightMoved.Length() <= ClickSlop) FaceToward(toward);
                _rightPressedOn = null;
                break;

            case InputEventMouseMotion motion when _rightPressedOn is not null:
                _rightMoved += motion.Relative;
                break;
        }
    }

    /// <summary>Turn the active unit on the spot to face towards a hex, paying for it; false if it already faces that way or cannot afford to.</summary>
    /// <remarks>
    /// The piece turns the short way round in the time the turn cost, at playback speed, the
    /// same rule as a walk: what the player watches is the price. The rules do not care which
    /// way round a soldier turns, only how far, so the picture is free to choose the short way.
    /// </remarks>
    public bool FaceToward(Hex hex)
    {
        var unit = Unit;
        if (_busy || Facing.Toward(unit.Position, hex) is not { } direction) return false;
        if (_movement.Turn(unit, direction) is not { } cost || cost == 0) return false;

        var piece = _pieces[unit];
        _busy = true;
        Hud.ShowUnit(unit);
        Hud.ShowTurn(null);

        var tween = CreateTween();
        tween.TweenProperty(piece, "rotation:y", Swing(piece.Rotation.Y, Heading(direction)), cost * Units.TurnSeconds / Unit.MaxAp / PlaybackSpeed);
        tween.Finished += () =>
        {
            _busy = false;
            RefreshReach();
            RefreshHover();
        };

        return true;
    }

    /// <summary>Move to a hex if it is in reach, hurrying if that is the only way; false if it is not.</summary>
    public bool OrderTo(Hex target)
    {
        if (_busy || target == Unit.Position || !_hurried.Contains(target)) return false;
        Order(target);
        return true;
    }

    /// <summary>Fire at the enemy if the rules allow it; false if they refuse.</summary>
    public bool FireAtEnemy()
    {
        if (_busy) return false;

        foreach (var unit in _units)
        {
            if (unit.Side != Unit.Side && Shooting.Plan(Unit, unit, Seen(unit)).CanFire) return Fire(unit);
        }

        return false;
    }

    /// <summary>Whether the active unit sees another: itself always, anyone else if they stand on a hex it makes out.</summary>
    public bool Seen(Unit other) => other == Unit || _view.Sees(other.Position);

    /// <summary>How many hexes the active unit makes out at all, for the capture's console line.</summary>
    public int SeenCount => _view.Count;

    /// <summary>End the active unit's turn: the board passes to the next unit still standing, whose points come back.</summary>
    /// <remarks>
    /// Points come back at the start of a unit's own turn rather than at the end of it, so the
    /// number on the card during the other side's turn is what was left, not what will be.
    /// With one side down the turn comes straight back round.
    /// </remarks>
    public void EndTurn()
    {
        if (_busy) return;

        for (var i = 1; i <= _units.Count; i++)
        {
            var next = (_active + i) % _units.Count;
            if (_units[next].IsDown) continue;
            _active = next;
            break;
        }

        Unit.Refresh();
        Hud.ShowNote(null);
        Hud.ShowUnit(Unit);
        Hud.ShowPortrait(PieceMesh);

        // The camera goes to whoever is up, so the player is looking at the piece they are about to move.
        var piece = _pieces[Unit].Position;
        Camera.Set(focus: new Vector2(piece.X, piece.Z));

        RefreshReach();
        RefreshUnitRing();
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
        var unit = Unit;
        var piece = _pieces[unit];
        var reach = _reachable.Contains(destination) ? _reachable : _hurried;
        if (reach.CostTo(destination) is not { } cost || !unit.CanAfford(cost)) return;
        var path = reach.PathTo(destination);
        var before = unit.Ap;

        // Somebody unseen may be standing on the way. The walk stops short of them, only the
        // steps taken are paid for, and the unit turns to face whoever it walked into, which
        // is how it comes to see them: the reach did not know they were there, because the
        // unit did not.
        var end = path.Count - 1;
        var bumped = false;
        for (var i = 1; i < path.Count; i++)
        {
            if (UnitOn(path[i]) is { } someone && someone != unit && !Seen(someone))
            {
                end = i - 1;
                bumped = true;
                cost = reach.CostTo(path[end])!.Value;
                break;
            }
        }

        // A hurried step may end in a fall. The dice are thrown now for every hurried step on
        // the way and the walk is cut short at the first that comes up: the animation only
        // ever shows what has already happened.
        var fell = false;
        for (var i = 1; i <= end; i++)
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

        unit.Spend(cost);
        _planned = null;
        Hud.ShowUnit(unit);
        Hud.ShowMove(null);

        // Walked into somebody on the very first step: nothing to animate, only the turn to face them.
        if (end == 0)
        {
            unit.Facing = Facing.Toward(path[0], path[1]) ?? unit.Facing;
            piece.Rotation = new Vector3(0f, Heading(unit.Facing), 0f);
            Hud.ShowUnit(unit);
            Hud.ShowNote("WALKED INTO SOMEONE");
            RefreshReach();
            RefreshHover();
            return;
        }

        _busy = true;

        // Each step takes the share of the turn it cost, at playback speed: a stride on the
        // flat is half a second of turn, a climb longer, a road quicker. What the player
        // watches is the price. The marks stay through the walk, and with each step the hexes
        // that could no longer be afforded from the hex being stepped to fade out over that
        // step, so the reach is seen to shrink as the points are walked away.
        // The piece turns into each step as it takes it, the short way round, so it arrives
        // facing the way it came, which is the facing the rules give it at the end.
        var tween = CreateTween();
        var heading = piece.Rotation.Y;
        for (var i = 1; i <= end; i++)
        {
            var to = path[i];
            var step = reach.CostTo(to)!.Value - reach.CostTo(path[i - 1])!.Value;
            var seconds = step * Units.TurnSeconds / Unit.MaxAp / PlaybackSpeed;
            var left = before - reach.CostTo(to)!.Value;
            heading = Swing(heading, Heading(Facing.Toward(path[i - 1], to)!.Value));
            tween.TweenCallback(Callable.From(() => FadeOutOfReach(to, left, seconds)));
            tween.TweenProperty(piece, "position", ToScene(to), seconds);
            tween.Parallel().TweenProperty(piece, "rotation:y", heading, seconds);
        }

        tween.Finished += () =>
        {
            unit.Position = path[end];
            unit.Facing = Facing.Toward(path[end - 1], path[end]) ?? unit.Facing;
            _busy = false;

            // A fall costs whatever was left of the turn. Going prone and getting hurt come later.
            if (fell)
            {
                unit.Spend(unit.Ap);
                Hud.ShowNote("FELL ON THE SLOPE");
            }
            else if (bumped)
            {
                unit.Facing = Facing.Toward(path[end], path[end + 1]) ?? unit.Facing;
                piece.Rotation = new Vector3(0f, Heading(unit.Facing), 0f);
                Hud.ShowNote("WALKED INTO SOMEONE");
            }

            Hud.ShowUnit(unit);
            RefreshReach();
            RefreshUnitRing();
            RefreshHover();
        };
    }

    /// <summary>Fire the active unit's weapon at a target, paying for it first; false if the rules refuse.</summary>
    /// <remarks>
    /// The dice are thrown before anything is drawn, so the tracer shows what has already
    /// happened: it ends on the target on a hit and goes past on a miss. A target put down
    /// topples away from the shot and stays where it lies.
    /// </remarks>
    private bool Fire(Unit target)
    {
        var shooter = Unit;
        var roll = ShotRoll ?? _dice.NextDouble();
        if (Shooting.Fire(shooter, target, roll, Seen(target)) is not { } result) return false;

        _busy = true;
        _target = null;
        Hud.ShowUnit(shooter);
        Hud.ShowTurn(null);
        Hud.ShowTarget(target, Shooting.Plan(shooter, target));

        // The rules turned the shooter to the target; the piece snaps round with the shot.
        _pieces[shooter].Rotation = new Vector3(0f, Heading(shooter.Facing), 0f);

        var from = _pieces[shooter].Position + Vector3.Up * MuzzleHeight;
        var at = _pieces[target].Position + Vector3.Up * ChestHeight;
        var line = at - from;
        var flat = new Vector3(line.X, 0f, line.Z).Normalized();
        var to = result.Hit ? at : at + flat * MissPast + new Vector3(-flat.Z, 0f, flat.X) * MissAside;

        ShowTracer(from, to);

        var tween = CreateTween();
        tween.TweenInterval(TracerSeconds);
        tween.TweenProperty(_tracer, "transparency", 1f, TracerFadeSeconds);

        if (result.TargetDown) Topple(target, flat, tween);

        tween.Finished += () =>
        {
            _tracer.Visible = false;
            _busy = false;

            Hud.ShowNote(result.Hit
                ? result.TargetDown ? $"HIT · {target.Name} DOWN" : $"HIT · {result.Damage} DAMAGE"
                : "MISS");

            RefreshReach();
            RefreshHover();
        };

        return true;
    }

    /// <summary>A bright line from the muzzle to where the round went.</summary>
    private void ShowTracer(Vector3 from, Vector3 to)
    {
        var length = from.DistanceTo(to);
        _tracer.Mesh = new BoxMesh { Size = new Vector3(TracerWidth, TracerWidth, length), Material = _tracerGlow };
        _tracer.Transparency = 0f;
        _tracer.Visible = true;
        _tracer.Position = (from + to) / 2f;
        _tracer.LookAt(to, Vector3.Up);
    }

    /// <summary>Lay a piece down on the ground, falling away from the shot, in the same tween as the tracer.</summary>
    private void Topple(Unit unit, Vector3 away, Tween tween)
    {
        var piece = _pieces[unit];
        var axis = new Vector3(-away.Z, 0f, away.X);

        // The piece turns about its base edge on the far side, so it lands with its length on
        // the ground beyond it rather than sinking through it. A mesh rotates about its own
        // origin, the centre of its foot, so the pivot is faked by moving the origin as it
        // turns: to half a length away, one radius up.
        var foot = ToScene(unit.Position);
        var rest = new Vector3(foot.X + away.X * PieceHeight / 2f, foot.Y + PieceRadius, foot.Z + away.Z * PieceHeight / 2f);

        tween.Parallel().TweenProperty(piece, "quaternion", new Quaternion(axis.Normalized(), Mathf.Pi / 2f), ToppleSeconds)
            .SetEase(Tween.EaseType.In).SetTrans(Tween.TransitionType.Quad);
        tween.Parallel().TweenProperty(piece, "position", rest, ToppleSeconds)
            .SetEase(Tween.EaseType.In).SetTrans(Tween.TransitionType.Quad);

        // A piece down goes dull.
        var paint = _paints[unit];
        tween.Parallel().TweenProperty(paint, "albedo_color", paint.AlbedoColor.Darkened(0.45f), ToppleSeconds);
    }

    /// <summary>The ring under the active unit, its side's colour, the same size as the cursor's so the two coincide when it is pointed at.</summary>
    private void RefreshUnitRing()
    {
        var material = Unit.Side == Side.Player ? _accent : _hostile;
        _unitRing.Mesh = Meshes.Ring(_pieces[Unit].Position, HoverRadius, HoverWidth, material, Drape(UnitLift));
    }

    /// <summary>The hexes other units the active unit can see stand on: not to be stepped onto or through. An unseen unit's hex is not blocked, or the marks would give them away.</summary>
    private HashSet<Hex> Occupied()
    {
        var occupied = new HashSet<Hex>();
        foreach (var unit in _units)
        {
            if (unit != Unit && Seen(unit)) occupied.Add(unit.Position);
        }
        return occupied;
    }

    /// <summary>
    /// Survey what the active unit makes out from where it stands, facing as it does, fog the
    /// board from it, and show only the pieces it sees. Its own piece is always shown.
    /// </summary>
    /// <remarks>
    /// The fog is drawn from the view; the pieces are hidden by this and never by the fog. A
    /// piece the unit cannot see is not in the scene, so nothing in the drawing can leak it.
    /// </remarks>
    private void RefreshSight(bool fade)
    {
        _view = _sight.Survey(Unit.Position, Unit.Facing);
        _field.Show(_view, _sight.HeightAt, _sight.ReachHexes, fade);

        foreach (var unit in _units) _pieces[unit].Visible = Seen(unit);
    }

    /// <summary>Mark every hex the active unit can reach from where it stands with what it has, and every enemy it can shoot.</summary>
    /// <remarks>
    /// One disc per hex, the size of the cursor's ring: grey where a careful way fits the
    /// points, orange where only a hurried way down a slope does, with its chance of a fall,
    /// and red under an enemy the unit can fire at from here. The marks are per hex rather
    /// than an outline of the set because a hex can mean more than one thing, and colour is
    /// how it says which. The unit's own hex is marked like any other, under its ring, so the
    /// field of marks has no hole and none opens behind a unit as it walks.
    /// </remarks>
    private void RefreshReach(bool fade = true)
    {
        RefreshSight(fade);

        var unit = Unit;
        var occupied = Occupied();
        _reachable = _movement.Reachable(unit.Position, unit.Ap, unit.Profile, blocked: occupied);
        _hurried = _movement.Reachable(unit.Position, unit.Ap, unit.Profile, hurrying: true, blocked: occupied);

        _shown.Clear();
        _shown.UnionWith(_hurried.Hexes);
        _marks.Set(unit.Position, Coloured());
    }

    private IEnumerable<(Hex, Color)> Coloured()
    {
        foreach (var hex in _shown) yield return (hex, _reachable.Contains(hex) ? SciFi.MarkMove : SciFi.MarkWarning);

        foreach (var unit in _units)
        {
            if (unit.Side != Unit.Side && Shooting.Plan(Unit, unit, Seen(unit)).CanFire) yield return (unit.Position, SciFi.MarkDanger);
        }
    }

    /// <summary>The cost of getting to a hex and the risk on the way: careful if a careful way fits the points, hurried otherwise, or null.</summary>
    private (int Cost, double Risk)? WayTo(Hex hex)
    {
        if (_reachable.CostTo(hex) is { } careful) return (careful, 0);
        if (_hurried.CostTo(hex) is { } quick) return (quick, _hurried.RiskTo(hex)!.Value);
        return null;
    }

    /// <summary>The unit standing on a hex, down or not, or null.</summary>
    private Unit? UnitOn(Hex hex)
    {
        foreach (var unit in _units)
        {
            if (unit.Position == hex) return unit;
        }
        return null;
    }

    /// <summary>
    /// Take the marks off every hex that can no longer be afforded from a hex with a budget,
    /// fading them out over some seconds, and keep the rest.
    /// </summary>
    private void FadeOutOfReach(Hex from, int budget, float seconds)
    {
        var still = _movement.Reachable(from, budget, Unit.Profile, hurrying: true, blocked: Occupied());

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

    /// <summary>
    /// Move the ring under the cursor, and either plan the path to the hex and tell the HUD
    /// the cost, or, with an enemy standing on it, work out the shot and show the target card.
    /// </summary>
    /// <remarks>The path is planned but not drawn: the ring and the cost are what the player sees.</remarks>
    private void RefreshHover()
    {
        _planned = null;
        _target = null;

        if (_hovered is not { } hovered)
        {
            _hover.Visible = false;
            Hud.ShowMove(null);
            Hud.ShowTurn(null);
            Hud.ShowTarget(null, null);
            return;
        }

        _hover.Visible = true;
        _hover.Mesh = Meshes.Ring(ToScene(hovered), HoverRadius, HoverWidth, _white, Drape(HoverLift));

        var unit = Unit;

        // What a right click would cost: the turn to face the hovered hex, if it is not faced already.
        if (!_busy && Facing.Toward(unit.Position, hovered) is { } direction && direction != unit.Facing)
        {
            var turn = _movement.TurnCost(unit.Facing, direction, unit.Profile);
            Hud.ShowTurn(turn, unit.CanAfford(turn));
        }
        else
        {
            Hud.ShowTurn(null);
        }

        // An enemy the unit cannot see is not there as far as the cursor is concerned: the
        // hex is hovered like any empty hex, and a walk onto it finds out the hard way.
        if (!_busy && UnitOn(hovered) is { } other && other.Side != unit.Side && Seen(other))
        {
            // The card is shown whether or not the shot can be taken: the refusal is on it.
            var shot = Shooting.Plan(unit, other);
            _target = shot.CanFire ? other : null;
            Hud.ShowMove(null);
            Hud.ShowTarget(other, shot);
            return;
        }

        Hud.ShowTarget(null, null);

        if (!_busy && hovered != unit.Position && WayTo(hovered) is { } way)
        {
            _planned = hovered;
            Hud.ShowMove(way.Cost, way.Risk);
        }
        else
        {
            Hud.ShowMove(null);
        }
    }

    private Vector2? PointUnderMouse()
    {
        var ground = Camera.GroundUnder(GetViewport().GetMousePosition());
        return ground is { } g ? new Vector2(g.X, g.Z) : null;
    }

    /// <summary>
    /// The rotation about Y that points a piece's nose, built along +X, down a facing. A turn
    /// about +Y carries +X towards -Z, and a bearing is measured towards +Z, so it is the
    /// bearing negated.
    /// </summary>
    private static float Heading(int facing) => -(float)Facing.BearingRadians(facing);

    /// <summary>The angle to tween a rotation to so it arrives at a heading the short way round: the heading, wound to within half a turn of where it is.</summary>
    private static float Swing(float from, float to) => from + Mathf.Wrap(to - from, -Mathf.Pi, Mathf.Pi);

    /// <summary>The centre of a hex, on the ground.</summary>
    private Vector3 ToScene(Hex hex)
    {
        var (x, z) = hex.Centre;
        return new Vector3((float)x, (float)Terrain.Height(x, z), (float)z);
    }
}
