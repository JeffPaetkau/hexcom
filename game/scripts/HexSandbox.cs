using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>
/// A flat debug view of a battle: click to move whoever is up, space to pass the turn, and
/// watch the order strip decide who goes next.
/// </summary>
/// <remarks>
/// Everything interesting here is a query against <c>Hexcom.Core</c>. This file draws and reads
/// input and does nothing else — no rule may be implemented in it, or the rules stop being
/// testable headless.
/// </remarks>
public partial class HexSandbox : Node2D
{
    [Export] public float HexSize { get; set; } = 44f;
    [Export] public int Seed { get; set; } = 7;

    private static readonly Color Background = new("14171c");
    private static readonly Color FloorFill = new("2b3038");
    private static readonly Color RoughFill = new("3b332a");
    private static readonly Color TransitFill = new("3a2630");
    private static readonly Color ReachFill = new("1f4438");
    private static readonly Color RegionEdge = new("434a55");
    private static readonly Color PathColor = new("6fd3b0");
    private static readonly Color TextDim = new("8d96a5");
    private static readonly Color TextBright = new("dfe5ee");
    private static readonly Color Unseen = new("0b0d10", 0.66f);
    private static readonly Color CoverLightHue = new("6fa8c8");
    private static readonly Color CoverHalfHue = new("d8b25a");
    private static readonly Color CoverFullHue = new("d1743c");
    private static readonly Color PlayerHue = new("74d3b4");
    private static readonly Color HostileHue = new("e0674a");
    private static readonly Color NeutralHue = new("aab2bd");
    private static readonly Color Panel = new("1b1f26", 0.92f);
    private static readonly Color GhostHue = new("e0674a", 0.55f);
    private static readonly Color OverwatchHue = new("f2c14e");

    private readonly Dictionary<NodeId, SightResult> _view = [];

    private Battle _battle = null!;
    private HexLayout _layout = null!;
    private ReachabilityResult _reach = null!;
    private Font _font = null!;

    private NodeId? _hover;
    private int _layer;

    /// <summary>What the last committed move got shot at with, if anything. Debug readout only.</summary>
    private string _lastWindow = "";

    public override void _Ready()
    {
        _font = ThemeDB.FallbackFont;
        _layout = new HexLayout(HexSize);
        Position = GetViewportRect().Size * 0.5f;
        NewBattle();
    }

    /// <summary>
    /// Two of ours outside the compound, three of theirs inside it, one holding the roof.
    /// </summary>
    private void NewBattle()
    {
        _battle = new Battle(DemoMaps.Compound(), _layout, seed: Seed);

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
        _layer = _battle.Active!.Position.Layer;
        _lastWindow = "";
        Recalculate();
    }

    private static NodeId Ground(int q, int r) => new(new Hex(q, r), 0);

    private void Recalculate()
    {
        var active = _battle.Active;
        _reach = active is null
            ? Pathfinder.Reachable(_battle.Graph, default, 0)
            : _battle.Reachable(active);

        _view.Clear();
        if (active is not null)
        {
            foreach (var tile in _battle.Map.Tiles.Where(t => t.Address.Layer == _layer))
            foreach (var region in _battle.Map.RegionsOf(tile.Address))
            {
                var id = new NodeId(tile.Address, region.Index);
                _view[id] = _battle.Sight.Trace(active.Vantage, new Vantage(id));
            }
        }

        QueueRedraw();
    }

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
                    _lastWindow = Describe(_battle.Move(target));

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

    /// <summary>What the reaction window did to a committed move, for the readout.</summary>
    private static string Describe(MoveOutcome outcome)
    {
        if (outcome.Reactions is not { } window) return "";
        if (window.Resolutions.Count == 0) return "";

        var shots = window.Resolutions.Select(r =>
            $"t{r.At} {r.Shot.Reactor.Name} {r.Shot.Mode.Name} at {r.Caught}: "
            + (r.Outcome.AnyHit ? $"hit for {r.Outcome.TotalDamage}" : "missed")
            + (r.Outcome.TargetDown ? ", down" : ""));

        return "reactions — " + string.Join("    ", shots);
    }

    /// <summary>
    /// Which region of which tile the cursor is over. Uses the actual region polygons, so a
    /// tile split by a barricade picks whichever side the cursor is really on.
    /// </summary>
    private NodeId? NodeUnderMouse()
    {
        var point = ToCore(GetLocalMousePosition());
        var address = new TileAddress(_layout.HexAt(point), _layer);
        if (!_battle.Map.HasTile(address)) return null;

        var regions = _battle.Map.RegionsOf(address);
        foreach (var region in regions)
            if (ContainsPoint(RegionPolygon(address, region, inset: 0f), ToScreen(point)))
                return new NodeId(address, region.Index);

        return new NodeId(address, regions[0].Index);
    }

    private Unit? HoveredUnit() => _hover is { } node ? _battle.UnitAt(node) : null;

    // ---- drawing ---------------------------------------------------------------

    public override void _Draw()
    {
        DrawRect(new Rect2(-Position, GetViewportRect().Size), Background);

        DrawTiles();
        DrawWalls();
        DrawAuthoredLinks();
        DrawPath();
        DrawBeliefs();
        DrawUnits();
        DrawOrderStrip();
        DrawHud();
    }

    private void DrawTiles()
    {
        foreach (var tile in _battle.Map.Tiles.Where(t => t.Address.Layer == _layer))
        foreach (var region in _battle.Map.RegionsOf(tile.Address))
        {
            var id = new NodeId(tile.Address, region.Index);
            var polygon = RegionPolygon(tile.Address, region, inset: 0.06f);

            DrawColoredPolygon(polygon, FillFor(tile, region, id));

            var outline = RegionEdge;
            var weight = 1f;

            if (_view.TryGetValue(id, out var seen))
            {
                // Dead ground the active unit has no eyes on.
                if (!seen.CanSee) DrawColoredPolygon(polygon, Unseen);
                else if (seen.Cover != CoverGrade.None)
                {
                    outline = CoverHue(seen.Cover);
                    weight = 2.5f;
                }
            }

            DrawPolyline([.. polygon, polygon[0]], outline, weight, true);

            if (_reach.CostTo(id) is { } cost && cost > 0 && _battle.UnitAt(id) is null)
                DrawCentredText(Centroid(tile.Address, region), cost.ToString(), 15, TextDim);
        }
    }

    private Color FillFor(Tile tile, HexRegion region, NodeId id)
    {
        if (_battle.Active is { } active && _reach.CanReach(id) && _battle.CanStopAt(active, id))
            return ReachFill;
        if (!region.Occupiable) return TransitFill;      // crossable, but nowhere to stand
        if (tile.Ground.ExtraApCost > 0) return RoughFill;
        return FloorFill;
    }

    private static Color CoverHue(CoverGrade grade) => grade switch
    {
        CoverGrade.Full => CoverFullHue,
        CoverGrade.Half => CoverHalfHue,
        _ => CoverLightHue,
    };

    private static Color SideHue(Side side) => side switch
    {
        Side.Player => PlayerHue,
        Side.Hostile => HostileHue,
        _ => NeutralHue,
    };

    private void DrawUnits()
    {
        foreach (var unit in _battle.InPlay.Where(u => u.Position.Layer == _layer))
        {
            var at = ToScreen(NodeCentre(unit.Position));
            var hue = SideHue(unit.Side);
            var radius = unit.Stance switch
            {
                Stance.Prone => HexSize * 0.16f,
                Stance.Crouching => HexSize * 0.21f,
                _ => HexSize * 0.27f,
            };

            DrawWatchCone(unit, at, hue);
            DrawCircle(at, radius, hue);
            DrawCircle(at, radius, new Color("0a0c0f", 0.7f), false, 2f);

            if (unit == _battle.Active)
                DrawArc(at, radius + 6f, 0, Mathf.Tau, 32, TextBright, 2f, true);

            DrawCentredText(
                NodeCentre(unit.Position) + new CoreVec2(0, HexSize * 0.42),
                $"{unit.Name} {unit.Vitality}",
                11,
                hue);

            // What the other side has worked out. Coarse on purpose — a rung on a ladder, never
            // a number. Our own exposure is the figure we get to read exactly, in the HUD.
            if (unit.Side == Side.Hostile)
            {
                var readout = WorstReadout(unit);
                DrawCentredText(
                    NodeCentre(unit.Position) + new CoreVec2(0, HexSize * 0.62),
                    readout.State.ToString().ToUpperInvariant(),
                    10,
                    AlarmHue(readout.State));
            }
        }
    }

    /// <summary>
    /// The arc a unit is actually watching. Outside it things are noticed slowly, and behind it
    /// barely at all — which is what makes a position flankable rather than merely approached.
    /// </summary>
    private void DrawWatchCone(Unit unit, Vector2 at, Color hue)
    {
        var attention = Wedge(
            at,
            unit.Facing,
            _battle.Awareness.Model.FrontArcDegrees,
            HexSize * 3.4f);

        DrawColoredPolygon(attention, new Color(hue, unit == _battle.Active ? 0.16f : 0.10f));

        // An arc being held is a different thing from an arc being attended to: anything that
        // moves inside this one gets shot at, out of whatever the watchman banked.
        if (unit.Overwatch is not { } order || unit.Reserve <= 0) return;

        var covered = Wedge(at, order.Centre, order.Arc.Degrees, HexSize * 5.2f);
        DrawColoredPolygon(covered, new Color(OverwatchHue, 0.12f));
        DrawPolyline([.. covered, covered[0]], new Color(OverwatchHue, 0.55f), 1.5f, true);
    }

    /// <summary>A pie slice centred on a hex bearing, in screen space.</summary>
    private Vector2[] Wedge(Vector2 at, HexDirection centre, double degrees, float reach)
    {
        var half = Mathf.DegToRad((float)degrees / 2f);
        var bearing = (float)(centre.BearingRadians() + _layout.RotationRadians);

        const int steps = 18;
        var wedge = new Vector2[steps + 2];
        wedge[0] = at;
        for (var i = 0; i <= steps; i++)
        {
            var angle = bearing - half + half * 2f * i / steps;
            // Core bearings run with +Y north; the screen runs with +Y down.
            wedge[i + 1] = at + new Vector2(Mathf.Cos(angle), -Mathf.Sin(angle)) * reach;
        }

        return wedge;
    }

    /// <summary>
    /// Where each enemy believes one of ours to be. The marker is what they last saw, so it
    /// goes stale the moment that soldier moves — and the gap between marker and truth is the
    /// thing the approach is played in.
    /// </summary>
    private void DrawBeliefs()
    {
        foreach (var hostile in _battle.InPlay.Where(u => u.Side == Side.Hostile))
        foreach (var mine in _battle.InPlay.Where(u => u.Side == Side.Player))
        {
            var readout = _battle.Awareness.ReadoutFor(hostile.Id, mine.Id);
            if (readout.State < AwarenessState.Searching) continue;
            if (readout.LastKnownPosition is not { } believed) continue;
            if (believed == mine.Position) continue;      // they are simply right
            if (believed.Layer != _layer) continue;

            var at = ToScreen(NodeCentre(believed));
            DrawArc(at, HexSize * 0.30f, 0, Mathf.Tau, 24, GhostHue, 2f, true);
            DrawCentredText(NodeCentre(believed) + new CoreVec2(0, -HexSize * 0.06), "?", 16, GhostHue);
        }
    }

    /// <summary>The most alarmed any of ours has made this enemy.</summary>
    private AwarenessReadout WorstReadout(Unit hostile)
    {
        var worst = AwarenessReadout.Nothing;
        foreach (var mine in _battle.InPlay.Where(u => u.Side == Side.Player))
        {
            var readout = _battle.Awareness.ReadoutFor(hostile.Id, mine.Id);
            if (readout.State > worst.State) worst = readout;
        }
        return worst;
    }

    private static Color AlarmHue(AwarenessState state) => state switch
    {
        AwarenessState.Engaged => new Color("ff6a4d"),
        AwarenessState.Alerted => new Color("e0674a"),
        AwarenessState.Searching => new Color("d8942a"),
        AwarenessState.Suspicious => new Color("c9b04a"),
        _ => new Color("6b7480"),
    };

    private void DrawWalls()
    {
        foreach (var wall in _battle.Map.Walls.Where(w => w.Layer == _layer))
        {
            var (color, width) = StyleFor(wall.Profile);
            DrawLine(ToScreen(_layout.Position(wall.A)), ToScreen(_layout.Position(wall.B)), color, width, true);
        }
    }

    private static (Color Color, float Width) StyleFor(WallProfile profile) => profile.Id switch
    {
        "low" => (new Color("d8b25a"), 6f),      // waist high: half cover, vault it
        "high" => (new Color("d1743c"), 8f),     // head high: full cover, climb it
        "solid" => (new Color("e6e9ee"), 10f),   // building: nothing gets through
        "railing" => (new Color("6fa8c8"), 3f),  // light cover only
        "screen" => (new Color("74b06a"), 5f),   // blocks sight, not movement
        _ => (new Color("aaaaaa"), 4f),
    };

    private void DrawAuthoredLinks()
    {
        foreach (var link in _battle.Map.Links.Where(l => l.From.Layer == _layer || l.To.Layer == _layer))
        {
            var address = link.From.Layer == _layer ? link.From : link.To;
            DrawCircle(ToScreen(_layout.Center(address.Hex)), HexSize * 0.30f, new Color("c8a24a", 0.28f));
            DrawCentredText(_layout.Center(address.Hex), link.Kind.ToString().ToUpperInvariant(), 11, new Color("f0d190"));
        }
    }

    private void DrawPath()
    {
        if (_battle.Active is not { } active) return;
        if (_hover is not { } goal || !_reach.TryGetPath(goal, out var path) || path.Count == 0) return;

        var points = new List<Vector2> { ToScreen(NodeCentre(active.Position)) };
        points.AddRange(path.Select(link => ToScreen(NodeCentre(link.To))));
        DrawPolyline([.. points], PathColor, 3f, true);

        foreach (var link in path.Where(l => l.Kind != TraversalKind.Walk))
            DrawCentredText(
                NodeCentre(link.To) + new CoreVec2(0, -HexSize * 0.30),
                link.Kind.ToString().ToUpperInvariant(),
                11,
                PathColor);
    }

    /// <summary>The next few bookings, so the player can see the interleaving coming.</summary>
    private void DrawOrderStrip()
    {
        var origin = -Position + new Vector2(GetViewportRect().Size.X - 190, 26);
        DrawString(_font, origin, "TURN ORDER", HorizontalAlignment.Left, -1, 11, TextDim);

        var slots = _battle.TurnOrder.Take(6).ToList();
        for (var i = 0; i < slots.Count; i++)
        {
            var unit = _battle.GetUnit(slots[i].Unit);
            if (unit is null) continue;

            var box = new Rect2(origin + new Vector2(0, 12 + i * 26), new Vector2(170, 22));
            DrawRect(box, Panel);
            DrawRect(new Rect2(box.Position, new Vector2(4, box.Size.Y)), SideHue(unit.Side));
            DrawString(_font, box.Position + new Vector2(12, 16), unit.Name,
                HorizontalAlignment.Left, -1, 13, TextBright);
            DrawString(_font, box.Position + new Vector2(120, 16), $"init {slots[i].Roll}",
                HorizontalAlignment.Left, -1, 11, TextDim);

            // What this one could still answer a move with, and whether it is holding an arc.
            if (unit.Reserve > 0)
                DrawString(_font, box.Position + new Vector2(80, 16),
                    unit.Overwatch is { } held ? $"{unit.Reserve}▸{held.Arc.Name[..1]}" : $"{unit.Reserve}•",
                    HorizontalAlignment.Left, -1, 11, OverwatchHue);
        }
    }

    private void DrawHud()
    {
        var active = _battle.Active;
        var lines = new[]
        {
            active is null
                ? $"round {_battle.Round}    nobody left to act"
                : $"round {_battle.Round}    {active.Name} ({active.Side})    "
                  + $"{active.ActionPoints}/{active.Stats.ActionPoints} AP    "
                  + $"{active.Stance.ToString().ToLowerInvariant()}    facing {active.Facing}    layer {_layer}",
            active is null
                ? ""
                : $"exposed {_battle.ExposureOf(active):P0}    "
                  + $"they are: {_battle.HighestAwarenessOf(active).ToString().ToUpperInvariant()}",
            active is null ? "" : ReserveLine(active),
            _hover is { } h
                ? $"cursor {h}    {(_reach.CostTo(h) is { } c ? $"{c} AP" : "out of reach")}    {SightLine(h)}"
                : "cursor —",
            ShotLine(),
            _lastWindow,
            "left-click: move    right-click: fire    space: end turn    C: stance    Z/X: turn    "
            + "V: overwatch arc    Q/E: layer    R: new battle",
        }.Where(line => line.Length > 0).ToArray();

        var top = -Position + new Vector2(18, 30);
        for (var i = 0; i < lines.Length; i++)
            DrawString(_font, top + new Vector2(0, i * 20), lines[i],
                HorizontalAlignment.Left, -1, 14, i == lines.Length - 1 ? TextDim : TextBright);
    }

    /// <summary>
    /// What ending the turn now would leave this unit to answer other people's moves with, and
    /// what it is holding. The reserve is the whole reason to stop moving early.
    /// </summary>
    private string ReserveLine(Unit active)
    {
        var model = _battle.Reactions;
        var would = (int)(active.ActionPoints * model.ReserveFraction);
        if (would < model.ReserveFloor) would = 0;

        var holding = active.Overwatch is { } order
            ? $"holding a {order.Arc.Name} arc {order.Centre} (x{order.Arc.AimBonus:0.00} to hit)"
            : "watching nothing in particular";

        return $"reserve {active.Reserve}, {would} if you stop here    {holding}";
    }

    /// <summary>The shot the active unit would take at whoever is under the cursor.</summary>
    private string ShotLine()
    {
        if (_battle.Active is not { } shooter) return "";
        if (HoveredUnit() is not { } quarry || !quarry.IsHostileTo(shooter)) return "";

        var plan = _battle.PlanShot(shooter, quarry);
        if (!plan.CanFire) return $"shot at {quarry.Name}: {plan.Refusal}";

        var armour = plan.Target.Protection;

        // A body is a hexagon, so a shot is never at one plate. Show the spread and what each is
        // still carrying, because which side is worn is what turning is for.
        var faces = string.Join(", ", plan.Aspects.Select(a =>
            $"{a.Face} {a.Share:P0} (s{armour.ShieldOn(a.Face)}/p{armour.ArmourOn(a.Face)})"));

        var glancing = plan.GlancingFactor < 0.995
            ? $"    glancing {plan.GlancingFactor:P0}"
            : "";

        return $"shot at {quarry.Name}: {plan.HitChance:P0} for {plan.ApCost} AP    "
               + $"{plan.Weapon.Name} ({plan.Weapon.Kind}){glancing}    "
               + faces
               + "    right-click to fire";
    }

    /// <summary>What the active unit can make out at the cursor, and what is protecting it.</summary>
    private string SightLine(NodeId node)
    {
        if (!_view.TryGetValue(node, out var seen)) return "no sight data";
        if (!seen.CanSee) return $"hidden by {seen.Blocker?.Profile.Id ?? "terrain"}";

        var cover = seen.Cover == CoverGrade.None
            ? "in the open"
            : $"{seen.Cover.ToString().ToLowerInvariant()} cover behind {seen.CoverSource?.Profile.Id}";

        return $"{cover}    {seen.Exposure:P0} exposed    {seen.Distance:0.0} m";
    }

    // ---- geometry helpers ------------------------------------------------------

    private static Vector2 ToScreen(CoreVec2 v) => new((float)v.X, (float)-v.Y);

    private static CoreVec2 ToCore(Vector2 v) => new(v.X, -v.Y);

    private CoreVec2 Centroid(TileAddress address, HexRegion region)
        => _layout.Center(address.Hex) + region.LocalCentroid * _layout.Size;

    private CoreVec2 NodeCentre(NodeId id)
    {
        var regions = _battle.Map.RegionsOf(id.Tile);
        var region = regions.FirstOrDefault(r => r.Index == id.Region) ?? regions[0];
        return Centroid(id.Tile, region);
    }

    private Vector2[] RegionPolygon(TileAddress address, HexRegion region, float inset)
    {
        var center = _layout.Center(address.Hex);
        var centroid = Centroid(address, region);

        return region.CornerIndices
            .Select(i =>
            {
                var corner = center + HexPartition.UnitCorner(i) * _layout.Size;
                return ToScreen(corner + (centroid - corner) * inset);
            })
            .ToArray();
    }

    private void DrawCentredText(CoreVec2 worldPosition, string text, int size, Color color)
    {
        var at = ToScreen(worldPosition) + new Vector2(-HexSize, size * 0.36f);
        DrawString(_font, at, text, HorizontalAlignment.Center, HexSize * 2, size, color);
    }

    private static bool ContainsPoint(IReadOnlyList<Vector2> polygon, Vector2 point)
    {
        var inside = false;
        for (int i = 0, j = polygon.Count - 1; i < polygon.Count; j = i++)
        {
            var a = polygon[i];
            var b = polygon[j];
            if (a.Y > point.Y != b.Y > point.Y &&
                point.X < (b.X - a.X) * (point.Y - a.Y) / (b.Y - a.Y) + a.X)
                inside = !inside;
        }
        return inside;
    }
}
