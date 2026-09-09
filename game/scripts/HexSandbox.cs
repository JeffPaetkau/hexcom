using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>
/// A flat debug view of a battle: click to move whoever is up, space to pass the turn, and
/// watch the order strip decide who goes next.
/// </summary>
/// <remarks>
/// <para>
/// Everything interesting here is a query against <c>Hexcom.Core</c>. This layer draws and reads
/// input and does nothing else — no rule may be implemented in it, or the rules stop being
/// testable headless.
/// </para>
/// <para>
/// The node keeps the input handling and the state of the moment; the map and the deployments
/// are <see cref="SandboxScenario"/>'s, and the drawing is split between
/// <see cref="BattleView"/> (the world) and <see cref="BattleHud"/> (the readouts), which are
/// presentation and interface respectively and are separate types so that two people can work on
/// them at once. Between the node and both of them sits <see cref="SandboxCamera"/>, which holds
/// the <see cref="SandboxScale"/> that is the only place knowing the difference between a metre
/// and a pixel.
/// </para>
/// </remarks>
public partial class HexSandbox : Node2D
{
    /// <summary>
    /// Hex radius in pixels — how big the map is drawn, and nothing else.
    /// </summary>
    /// <remarks>
    /// Exported because rendering scale is a matter of taste. It is emphatically <i>not</i> the
    /// world scale: that is <see cref="SandboxScale.MetresPerHexSize"/>, it is a constant, and
    /// changing this one must not move it. The two used to be the same number, which is the bug
    /// <c>docs/decisions.md</c> entry 002 describes.
    /// </remarks>
    [Export] public float HexSize { get; set; } = 44f;

    [Export] public int Seed { get; set; } = 7;

    /// <summary>
    /// Which of <see cref="SandboxScenario.All"/> to open with. Blank takes the first.
    /// </summary>
    /// <remarks>
    /// The waystation, by default. The compound is still here and still reachable, but every
    /// range in the game overshoots it by a factor of three — <c>docs/decisions.md</c> entry 007
    /// — so a sandbox that opens on it is a sandbox in which none of the distances mean anything.
    /// </remarks>
    [Export] public string Scenario { get; set; } = "";

    private readonly Dictionary<NodeId, SightResult> _sight = [];

    private Battle _battle = null!;
    private SandboxScenario _scenario = null!;
    private SandboxCamera _camera = null!;
    private BattleView _view = null!;
    private BattleHud _hud = null!;
    private SandboxCapture? _capture;

    private ReachabilityResult _reach = null!;
    private NodeId? _hover;
    private int _layer;

    /// <summary>Where a middle-button drag started, while one is in progress.</summary>
    private Vector2? _dragging;

    /// <summary>What the last committed move got shot at with, if anything. Debug readout only.</summary>
    private string _lastWindow = "";

    /// <summary>
    /// Whether the hostile side is being driven by <see cref="Commander"/> rather than by hand.
    /// </summary>
    /// <remarks>
    /// Off by default, because the sandbox exists to try things on both sides. Switching it on
    /// is the first time anybody watches the enemy behave like an enemy — entry 009 in
    /// <c>docs/decisions.md</c> — and what makes every readout in the HUD a readout of something
    /// the other side is visibly acting on rather than a figure with nothing to check it against.
    /// </remarks>
    private bool _auto;

    /// <summary>The turns the AI has taken since a person last did anything. Newest last.</summary>
    private readonly List<TakenTurn> _turns = [];

    public override void _Ready()
    {
        var font = ThemeDB.FallbackFont;

        _capture = SandboxCapture.Requested();
        _camera = new SandboxCamera(_capture?.HexPixels ?? HexSize);
        _view = new BattleView(this, _camera, font);
        _hud = new BattleHud(this, font);

        // A capture has to be reproducible, and input is the one thing here that is not: the
        // window opens under whatever the pointer was already doing, so the cursor readout and
        // the previewed path land in the picture and two runs disagree. Capturing is therefore
        // deaf as well as brief.
        SetProcess(_capture is not null);
        SetProcessUnhandledInput(_capture is null);

        NewBattle();
    }

    public override void _Process(double delta) => _capture?.Tick(this);

    /// <summary>
    /// Load the scenario asked for and put everybody on it.
    /// </summary>
    /// <remarks>
    /// The map comes from <c>content/</c> and the deployments do not, because there is nowhere
    /// yet to put them. Both are <see cref="SandboxScenario"/>'s problem; this method's job is
    /// only to hand the rules the metres layout and never the pixels one, which is the single
    /// mistake this file has actually made. See <see cref="SandboxScale"/>.
    /// </remarks>
    private void NewBattle()
    {
        _scenario = SandboxScenario.ByName(_capture?.Scenario ?? (Scenario.Length > 0 ? Scenario : null));

        _battle = new Battle(_scenario.LoadMap(), _camera.Scale.World, seed: Seed);
        _scenario.DeployInto(_battle);
        _battle.Start();

        // A capture takes its cursor, its turn and whether the enemy plays itself from the
        // command line rather than from the keyboard, which is the only way anything
        // cursor-driven, anything belonging to a later soldier, or anything the AI decided gets
        // into a picture at all. See SandboxCapture.
        _auto = _capture?.Automatic ?? false;
        _turns.Clear();
        Settle();
        for (var i = 0; i < (_capture?.Passes ?? 0) && _battle.IsRunning; i++)
        {
            _battle.EndTurn();
            Settle();
        }

        _layer = _battle.Active?.Position.Layer ?? 0;
        _lastWindow = "";
        _hover = _capture?.Hover;

        // The waystation is 85 metres across and does not fit on a screen at a size anybody can
        // read a tile at, so a battle opens looking at whoever is up rather than at the origin,
        // which is only where the compound happened to be centred. A capture can ask for either,
        // and for the whole map at once.
        var fit = _capture?.Fit ?? false;
        if (fit) _camera.Fit(_battle.Map, GetViewportRect().Size);

        if (_capture?.Look is { } look) _camera.LookAt(look);
        else if (!fit && _battle.Active is { } up) _camera.LookAt(up.Position.Tile.Hex);

        CameraMoved();
        Recalculate();
    }

    /// <summary>
    /// Give every hostile turn that is up to the AI, if the hostile side is on automatic, and
    /// keep what it decided for the HUD.
    /// </summary>
    /// <remarks>
    /// The record is replaced rather than appended to, so what is on screen is always what the
    /// other side did <em>since you last acted</em> — several turns of it when the initiative
    /// order puts two or three of theirs together, which is exactly when a reader most needs to
    /// know which of them did what. Nothing is kept from before, because a readout that scrolls
    /// is a log, and the HUD is not one.
    /// <para>
    /// The battle does not stop when one side is gone; the survivors keep taking turns. So this
    /// has to, or a side on automatic with nobody left to fight would take turns forever.
    /// </para>
    /// </remarks>
    private void Settle(bool keepRecord = false)
    {
        if (!_auto || _battle.Active is not { Side: Side.Hostile }) return;

        if (!keepRecord) _turns.Clear();
        while (_auto && !_battle.IsDecided && _battle.Active is { Side: Side.Hostile } unit)
            TakeTurnWithAi(unit);
    }

    /// <summary>Let <see cref="Commander"/> take the active unit's whole turn, and remember why.</summary>
    private void TakeTurnWithAi(Unit unit)
    {
        // Core change, kept to one line here: TakeTurn hands back an Act per order now, with the
        // outcome beside it. The readout still wants only the orders; see decisions.md entry 022,
        // which is where View asked for the outcomes in the first place.
        var acts = new Commander(_battle).TakeTurn();
        _turns.Add(new TakenTurn(unit, [.. acts.Select(a => a.Order)], unit.Reserve));
    }

    /// <summary>
    /// What follows anything a person did: the other side gets its go if it is on automatic,
    /// and the screen follows whoever is up next.
    /// </summary>
    private void AfterAction(bool keepRecord = false)
    {
        var before = _battle.Active;
        Settle(keepRecord);
        if (_battle.Active is { } next && next != before) _layer = next.Position.Layer;
        Recalculate();
        FollowActive();
    }

    /// <summary>
    /// Re-ask the rules everything the next frame will be drawn from. Called after anything that
    /// could have changed an answer, which is every committed action.
    /// </summary>
    /// <remarks>
    /// The sight sweep is the expensive part and it is proportional to the storey, not to what
    /// is on screen: eighteen hundred traces on the waystation's ground floor, measured at 25 ms
    /// once the code is warm. That is well inside a frame for something that runs on an action
    /// rather than on a redraw, which is why moving the camera does not trigger it — the camera
    /// changes what is drawn and never what is true, so panning and zooming only queue a redraw.
    /// </remarks>
    private void Recalculate()
    {
        var active = _battle.Active;
        _reach = active is null
            ? Pathfinder.Reachable(_battle.Graph, default, 0)
            : _battle.Reachable(active);

        _sight.Clear();
        if (active is not null)
        {
            foreach (var tile in _battle.Map.Tiles.Where(t => t.Address.Layer == _layer))
            foreach (var region in _battle.Map.RegionsOf(tile.Address))
            {
                var id = new NodeId(tile.Address, region.Index);
                _sight[id] = _battle.Sight.Trace(active.Vantage, new Vantage(id));
            }
        }

        QueueRedraw();
    }

    /// <summary>The moment as the drawing sees it. Assembled once, read by both halves.</summary>
    private SandboxFrame Frame()
        => new(
            _battle, _layer, _hover, _reach, _sight, _lastWindow, _turns, _auto,
            _scenario, _camera.Visible(GetViewportRect().Size), _camera.ShowsTileDetail);

    // ---- input -----------------------------------------------------------------

    public override void _UnhandledInput(InputEvent @event)
    {
        switch (@event)
        {
            case InputEventMouseMotion motion:
            {
                // A drag moves the map under the cursor and does not move the cursor's readout
                // with it: while the middle button is down the pointer is holding ground, not
                // pointing at it.
                if (_dragging is { } from)
                {
                    _camera.Pan(motion.Position - from);
                    _dragging = motion.Position;
                    CameraMoved();
                    break;
                }

                var node = NodeUnderMouse();
                if (node != _hover) { _hover = node; QueueRedraw(); }
                break;
            }

            case InputEventMouseButton { ButtonIndex: MouseButton.Middle } drag:
                _dragging = drag.Pressed ? drag.Position : null;
                break;

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.WheelUp or MouseButton.WheelDown } wheel:
                _camera.ZoomAbout(
                    wheel.ButtonIndex == MouseButton.WheelUp ? 1 : -1,
                    SandboxScale.FromScreen(GetLocalMousePosition()));
                CameraMoved();
                _hover = NodeUnderMouse();
                break;

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }:
                if (NodeUnderMouse() is { } target && _battle.Active is { } mover)
                {
                    _lastWindow = BattleHud.Describe(_battle.Move(target));

                    // A reaction can drop the mover part way, which hands the turn straight on.
                    if (_battle.Active is { } next && next != mover) _layer = next.Position.Layer;
                    AfterAction();
                }
                break;

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Right }:
                if (HoveredUnit() is { } quarry && _battle.Active is not null)
                {
                    _battle.Fire(quarry);
                    AfterAction();
                }
                break;

            case InputEventKey { Pressed: true, Echo: false } key:
                HandleKey(key.Keycode);
                break;
        }
    }

    private void HandleKey(Key key)
    {
        switch (key)
        {
            case Key.Space or Key.Enter:
                if (_battle.IsRunning)
                {
                    _battle.EndTurn();
                    if (_battle.Active is { } next) _layer = next.Position.Layer;
                    AfterAction();
                }
                break;

            case Key.A:
                // Whoever is up, theirs or ours: "what would you do here" is a question a player
                // should be able to ask of their own soldier, and the answer is the same search
                // the enemy runs.
                if (_battle.Active is { } soldier)
                {
                    _turns.Clear();
                    TakeTurnWithAi(soldier);
                    if (_battle.Active is { } next) _layer = next.Position.Layer;
                    AfterAction(keepRecord: true);
                }
                break;

            case Key.H:
                _auto = !_auto;
                AfterAction();
                break;

            case Key.C:
                if (_battle.Active is { } unit)
                {
                    _battle.ChangeStance(unit.Stance switch
                    {
                        Stance.Standing => Stance.Crouching,
                        Stance.Crouching => Stance.Prone,
                        _ => Stance.Standing,
                    });
                    Recalculate();
                }
                break;

            case Key.Z or Key.X:
                if (_battle.Active is { } turner)
                {
                    _battle.Face(turner.Facing.Rotate(key == Key.Z ? 1 : -1));
                    Recalculate();
                }
                break;

            case Key.V:
                if (_battle.Active is { } watchman)
                {
                    // Cycle none, narrow, standard, wide. Each declaration costs a point, which
                    // is honest: changing your mind about what you are watching is not free.
                    var next = NextArc(watchman.Overwatch?.Arc);
                    if (next is null) _battle.ClearOverwatch();
                    else _battle.SetOverwatch(next);
                    Recalculate();
                }
                break;

            case Key.B:
                if (_battle.Active is { } trapper)
                {
                    // Arm against the arc already being watched, or spring it if already armed.
                    if (trapper.Ambush is null) _battle.Arm(OverwatchArc.Standard);
                    else if (HoveredUnit() is { } prey) _lastWindow = BattleHud.Describe(_battle.SpringAmbush(prey));
                    Recalculate();
                }
                break;

            case Key.Pageup or Key.E:
                _layer++;
                Recalculate();
                break;

            case Key.Pagedown or Key.Q:
                _layer--;
                Recalculate();
                break;

            case Key.Left or Key.Right or Key.Up or Key.Down:
                _camera.Pan(PanStep * key switch
                {
                    Key.Left => Vector2.Right,      // the map goes right, so the view goes left
                    Key.Right => Vector2.Left,
                    Key.Up => Vector2.Down,
                    _ => Vector2.Up,
                });
                CameraMoved();
                break;

            case Key.Equal or Key.KpAdd:
                _camera.ZoomBy(1);
                CameraMoved();
                break;

            case Key.Minus or Key.KpSubtract:
                _camera.ZoomBy(-1);
                CameraMoved();
                break;

            case Key.F:
                _camera.Fit(_battle.Map, GetViewportRect().Size);
                CameraMoved();
                break;

            case Key.G:
                if (_battle.Active is { } here)
                {
                    _camera.LookAt(here.Position.Tile.Hex);
                    CameraMoved();
                }
                break;

            case Key.R:
                NewBattle();
                break;
        }
    }

    /// <summary>How far one arrow key moves the view, in pixels.</summary>
    private const float PanStep = 160f;

    /// <summary>Point the node at wherever the camera now is, and redraw.</summary>
    /// <remarks>
    /// The node's own <c>Position</c> is the pan: the grid runs in both directions from the
    /// origin, so putting a canvas point in the middle of the viewport is a matter of offsetting
    /// the whole node. That is what the single <c>Position = viewport / 2</c> in <c>_Ready</c>
    /// used to do, for a map whose middle was the origin and which fitted on the screen anyway.
    /// The hit test reads <c>GetLocalMousePosition</c>, which is relative to this same offset,
    /// so it needs nothing said to it.
    /// </remarks>
    private void CameraMoved()
    {
        Position = _camera.ScreenOffset(GetViewportRect().Size);
        QueueRedraw();
    }

    /// <summary>
    /// Keep whoever is up on screen, and only if they are not already.
    /// </summary>
    /// <remarks>
    /// A camera that recentres after every action takes the map away from a player who was
    /// deliberately looking somewhere else — at the ground they are about to cross, usually. So
    /// the test is whether the next soldier is comfortably in shot rather than whether they are
    /// in the middle of it, and the margin is negative for that reason.
    /// </remarks>
    private void FollowActive()
    {
        if (_battle.Active is not { } up) return;
        if (up.Position.Layer != _layer) return;

        var at = SandboxScale.ToScreen(_camera.Geometry.NodeCentre(_battle.Map, up.Position));
        if (_camera.Visible(GetViewportRect().Size, marginHexRadii: -3f).HasPoint(at)) return;

        _camera.LookAt(up.Position.Tile.Hex);
        CameraMoved();
    }

    /// <summary>The next arc in the cycle, or null to stop holding one.</summary>
    private static OverwatchArc? NextArc(OverwatchArc? held)
    {
        if (held is null) return OverwatchArc.All[0];

        var index = OverwatchArc.All.ToList().IndexOf(held);
        return index >= 0 && index + 1 < OverwatchArc.All.Count ? OverwatchArc.All[index + 1] : null;
    }

    /// <summary>
    /// Which region of which tile the cursor is over. Uses the actual region polygons, so a
    /// tile split by a barricade picks whichever side the cursor is really on.
    /// </summary>
    private NodeId? NodeUnderMouse()
    {
        // Pixels throughout: the cursor is a screen thing, and the canvas layout is what turns
        // it into a hex. The rules are never asked where the mouse is.
        var screen = GetLocalMousePosition();
        var address = new TileAddress(_camera.Scale.Canvas.HexAt(SandboxScale.FromScreen(screen)), _layer);
        if (!_battle.Map.HasTile(address)) return null;

        var regions = _battle.Map.RegionsOf(address);
        foreach (var region in regions)
            if (SandboxGeometry.ContainsPoint(_camera.Geometry.RegionPolygon(address, region, inset: 0f), screen))
                return new NodeId(address, region.Index);

        return new NodeId(address, regions[0].Index);
    }

    private Unit? HoveredUnit() => _hover is { } node ? _battle.UnitAt(node) : null;

    // ---- drawing ---------------------------------------------------------------

    public override void _Draw()
    {
        var frame = Frame();

        DrawRect(new Rect2(-Position, GetViewportRect().Size), SandboxPalette.Background);

        _view.Draw(frame);

        // The node is offset by the camera so the grid can run in both directions, so the panels
        // have to be pushed back out to the corners they belong in. They are the one thing on
        // screen the camera must not move.
        _hud.Origin = -Position;
        _hud.Draw(frame, GetViewportRect().Size);
    }
}
