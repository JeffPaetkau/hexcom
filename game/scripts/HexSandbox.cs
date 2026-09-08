using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
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
/// The node keeps the scenario, the input handling and the state of the moment; the drawing is
/// split between <see cref="BattleView"/> (the world) and <see cref="BattleHud"/> (the
/// readouts), which are presentation and interface respectively and are separate types so that
/// two people can work on them at once. Between the node and both of them sits
/// <see cref="SandboxScale"/>, which is the only place that knows the difference between a metre
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

    private readonly Dictionary<NodeId, SightResult> _sight = [];

    private Battle _battle = null!;
    private SandboxScale _scale = null!;
    private SandboxGeometry _geometry = null!;
    private BattleView _view = null!;
    private BattleHud _hud = null!;
    private SandboxCapture? _capture;

    private ReachabilityResult _reach = null!;
    private NodeId? _hover;
    private int _layer;

    /// <summary>What the last committed move got shot at with, if anything. Debug readout only.</summary>
    private string _lastWindow = "";

    public override void _Ready()
    {
        var font = ThemeDB.FallbackFont;

        _scale = new SandboxScale(HexSize);
        _geometry = new SandboxGeometry(_scale);
        _view = new BattleView(this, _scale, _geometry, font);
        _hud = new BattleHud(this, font);
        _capture = SandboxCapture.Requested();

        Position = GetViewportRect().Size * 0.5f;

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
    /// Two of ours outside the compound, three of theirs inside it, one holding the roof.
    /// </summary>
    private void NewBattle()
    {
        // The metres layout, never the pixels one. Handing the drawing scale to the rules is the
        // one mistake this file has actually made; see SandboxScale.
        _battle = new Battle(DemoMaps.Compound(), _scale.World, seed: Seed);

        // Ours come from the west, looking at the compound. Theirs watch the ground we have to
        // cross, which is what makes going the long way round the back worth the action points.
        _battle.Deploy("Vance", Side.Player, Ground(-4, 0), UnitStats.Scout, HexDirection.NorthEast, Loadout.Infiltrator);
        _battle.Deploy("Orsini", Side.Player, Ground(-3, 2), UnitStats.Trooper, HexDirection.NorthEast, Loadout.Heavy);
        _battle.Deploy("Sentry", Side.Hostile, Ground(4, 2), facing: HexDirection.SouthWest, loadout: Loadout.Beamer);
        _battle.Deploy("Watchman", Side.Hostile, Ground(4, -2), facing: HexDirection.NorthWest, loadout: Loadout.Rifleman);
        _battle.Deploy(
            "Spotter", Side.Hostile, new NodeId(new Hex(4, 0), layer: 1),
            UnitStats.Signaller, HexDirection.SouthWest, Loadout.Beamer);

        _battle.Start();

        // A capture takes its cursor and its turn from the command line rather than from the
        // keyboard, which is the only way anything cursor-driven or anything belonging to a
        // soldier other than the first gets into a picture at all. See SandboxCapture.
        for (var i = 0; i < (_capture?.Passes ?? 0) && _battle.IsRunning; i++) _battle.EndTurn();

        _layer = _battle.Active?.Position.Layer ?? 0;
        _lastWindow = "";
        _hover = _capture?.Hover;

        Recalculate();
    }

    private static NodeId Ground(int q, int r) => new(new Hex(q, r), 0);

    /// <summary>
    /// Re-ask the rules everything the next frame will be drawn from. Called after anything that
    /// could have changed an answer, which is every committed action.
    /// </summary>
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
        => new(_battle, _layer, _hover, _reach, _sight, _lastWindow);

    // ---- input -----------------------------------------------------------------

    public override void _UnhandledInput(InputEvent @event)
    {
        switch (@event)
        {
            case InputEventMouseMotion:
            {
                var node = NodeUnderMouse();
                if (node != _hover) { _hover = node; QueueRedraw(); }
                break;
            }

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }:
                if (NodeUnderMouse() is { } target && _battle.Active is { } mover)
                {
                    _lastWindow = BattleHud.Describe(_battle.Move(target));

                    // A reaction can drop the mover part way, which hands the turn straight on.
                    if (_battle.Active is { } next && next != mover) _layer = next.Position.Layer;
                    Recalculate();
                }
                break;

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Right }:
                if (HoveredUnit() is { } quarry && _battle.Active is not null)
                {
                    _battle.Fire(quarry);
                    Recalculate();
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
                    Recalculate();
                }
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

            case Key.R:
                NewBattle();
                break;
        }
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
        var address = new TileAddress(_scale.Canvas.HexAt(SandboxScale.FromScreen(screen)), _layer);
        if (!_battle.Map.HasTile(address)) return null;

        var regions = _battle.Map.RegionsOf(address);
        foreach (var region in regions)
            if (SandboxGeometry.ContainsPoint(_geometry.RegionPolygon(address, region, inset: 0f), screen))
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

        // The node is centred on the viewport so the grid can run in both directions, so the
        // panels have to be pushed back out to the corners they belong in.
        _hud.Origin = -Position;
        _hud.Draw(frame, GetViewportRect().Size);
    }
}
