using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>
/// The world, drawn: ground, walls, ladders, the planned path, what the enemy believes, and the
/// soldiers themselves.
/// </summary>
/// <remarks>
/// <para>
/// Presentation, as distinct from the readouts in <see cref="BattleHud"/>. The split is the one
/// <c>docs/subprojects/view.md</c> describes: this class consumes the rules and draws whatever
/// they answer, while the HUD decides what the player is allowed to <i>ask</i>. They were one
/// file until the world-scale work, and separating them is what lets the two be worked on at
/// once.
/// </para>
/// <para>
/// Nothing here implements a rule. Every shape on screen is a query against
/// <c>Hexcom.Core</c> put through <see cref="SandboxGeometry"/>; if something needs deciding
/// rather than drawing, it belongs in the core and not in this file.
/// </para>
/// </remarks>
public sealed class BattleView(CanvasItem canvas, SandboxCamera camera, Font font)
{
    /// <summary>
    /// How many rings the attention field is drawn in, out to the sight range.
    /// </summary>
    /// <remarks>
    /// Six is enough for the falloff to read as a falloff and few enough that seven soldiers cost
    /// under two hundred polygons a frame. Each ring is filled at the model's own value for its
    /// middle, so the picture is a step function sampling a smooth one rather than an
    /// illustration of it.
    /// </remarks>
    private const int AttentionRings = 6;

    /// <summary>
    /// Alpha the nearest ring of the front arc is filled at, by whose attention it is.
    /// </summary>
    /// <remarks>
    /// A soldier attends to everything within 45 metres at some rate, so every one of these
    /// fields is a disc covering most of the map, and seven of them at one weight is a wash
    /// whatever the falloff does. The weights are an interface judgement about which of them a
    /// player is reading: the soldier whose turn it is, because their facing is a decision being
    /// made now, and every enemy, because the whole approach is played against those. Our own
    /// idle soldiers are the noise — where they are looking will be settled on their own turn,
    /// from wherever they are then — so they are drawn faintly rather than dropped, which would
    /// be a different claim.
    /// </remarks>
    private const float AttentionPeakActive = 0.20f;
    private const float AttentionPeakHostile = 0.14f;
    private const float AttentionPeakIdle = 0.05f;

    private readonly CanvasItem _canvas = canvas;
    private readonly SandboxCamera _camera = camera;
    private readonly Font _font = font;

    private SandboxScale Scale => _camera.Scale;
    private SandboxGeometry Geometry => _camera.Geometry;

    public void Draw(SandboxFrame frame)
    {
        DrawTiles(frame);
        DrawExit(frame);
        DrawWalls(frame);
        DrawAuthoredLinks(frame);
        DrawPath(frame);
        DrawCommitted(frame);
        DrawBeliefs(frame);
        DrawUnits(frame);
    }

    /// <remarks>
    /// The cull is what makes a map of eighteen hundred tiles drawable: at a playable zoom a
    /// twentieth of them are on screen, and the ones that are not cost a rectangle test instead
    /// of four draw calls each. What survives being zoomed out past
    /// <see cref="SandboxCamera.LegibleAt"/> is the ground and nothing written on it — a
    /// two-digit AP cost does not fit in a fourteen-pixel hex, and eighteen hundred of them
    /// overlapping hide the map they are meant to explain.
    /// </remarks>
    private void DrawTiles(SandboxFrame frame)
    {
        foreach (var tile in frame.Battle.Map.Tiles.Where(t => t.Address.Layer == frame.Layer))
        foreach (var region in frame.Battle.Map.RegionsOf(tile.Address))
        {
            var centroid = Geometry.Centroid(tile.Address, region);
            if (!frame.Visible.HasPoint(SandboxScale.ToScreen(centroid))) continue;

            var id = new NodeId(tile.Address, region.Index);
            var polygon = Geometry.RegionPolygon(tile.Address, region, inset: frame.TileDetail ? 0.06f : 0f);

            _canvas.DrawColoredPolygon(polygon, FillFor(frame, tile, region, id));

            var outline = SandboxPalette.RegionEdge;
            var weight = 1f;
            var cover = false;

            if (frame.View.TryGetValue(id, out var seen))
            {
                // Dead ground the active unit has no eyes on. Zoomed out it goes: on a map this
                // size one soldier cannot see most of it, so the wash covers nine tiles in ten
                // and takes the shape of the place with it — and the shape of the place is the
                // one thing an overview is being asked for.
                if (!seen.CanSee)
                {
                    if (frame.TileDetail) _canvas.DrawColoredPolygon(polygon, SandboxPalette.Unseen);
                }
                else if (seen.Cover != CoverGrade.None)
                {
                    outline = SandboxPalette.CoverHue(seen.Cover);
                    weight = 2.5f;
                    cover = true;
                }
            }

            // Zoomed out the grid itself goes, because a hex edge at ten pixels is noise; where
            // the cover is stays, because that is the one thing worth reading from a map you
            // cannot read a number off.
            if (frame.TileDetail || cover)
                _canvas.DrawPolyline([.. polygon, polygon[0]], outline, weight, true);

            if (frame.TileDetail && frame.Reach.CostTo(id) is { } cost && cost > 0 && frame.Battle.UnitAt(id) is null)
                DrawCentredText(centroid, cost.ToString(), 15, SandboxPalette.TextDim);
        }
    }

    /// <summary>
    /// What colour a piece of ground is, decided from what the ground <em>does</em>.
    /// </summary>
    /// <remarks>
    /// Entry 035 left a question for whoever came next: the wall styles switch on well-known ids,
    /// so a profile a <c>.hexmap</c> declares for itself draws in the default grey, and entry 038
    /// asked whether grounds should be coloured by id or by figure. <b>By figure.</b> A map may
    /// invent ground and kit — that is the whole point of the format — so a table of names is a
    /// table that is wrong about every map written after it, and silently. The waystation's
    /// <c>deep</c> is the case that settles it: it is impassable, which is the single most
    /// important thing about a tile a player is planning a route across, and no amount of adding
    /// cases would have made the <em>next</em> map's water read correctly.
    /// <para>
    /// So: impassable ground reads as impassable, ground that costs extra reads as rough, and
    /// everything else is floor. Three figures, all of them declarable, none of them a name.
    /// </para>
    /// </remarks>
    private static Color FillFor(SandboxFrame frame, Tile tile, HexRegion region, NodeId id)
    {
        if (frame.Battle.Active is { } active && frame.Reach.CanReach(id) && frame.Battle.CanStopAt(active, id))
            return SandboxPalette.ReachFill;
        if (!tile.Ground.Passable) return SandboxPalette.ImpassableFill;
        if (!region.Occupiable) return SandboxPalette.TransitFill;   // crossable, but nowhere to stand
        if (tile.Ground.ExtraApCost > 0) return SandboxPalette.RoughFill;
        return SandboxPalette.FloorFill;
    }

    private void DrawUnits(SandboxFrame frame)
    {
        // A soldier well off screen still throws attention onto ground that is on it, so the
        // cull for units is grown by the reach of the thing they cast rather than by the margin
        // the tiles use.
        var reach = Scale.MetresToPixels(frame.Battle.Awareness.Model.SightRangeMetres);
        var inShot = frame.Visible.Grow(reach);

        foreach (var unit in frame.Battle.InPlay)
        {
            var centre = Geometry.NodeCentre(frame.Battle.Map, unit.Position);
            var at = SandboxScale.ToScreen(centre);
            if (!inShot.HasPoint(at)) continue;

            var hue = SandboxPalette.SideHue(unit.Side);

            DrawAttentionField(frame, unit, at, hue);
            DrawHeldArc(unit, at);

            if (unit.Position.Layer != frame.Layer) { DrawUpstairs(frame, unit, centre, at, hue); continue; }

            // Stance, drawn as footprint. A prone soldier really is a smaller thing to see, and
            // this is the only place on screen that says so before you read a number. Floored so
            // that zoomed out a soldier is still a dot rather than nothing.
            var radius = Mathf.Max(3f, Scale.HexRadiiToPixels(unit.Stance switch
            {
                Stance.Prone => 0.16f,
                Stance.Crouching => 0.21f,
                _ => 0.27f,
            }));

            _canvas.DrawCircle(at, radius, hue);
            _canvas.DrawCircle(at, radius, SandboxPalette.UnitOutline, false, 2f);

            if (unit == frame.Battle.Active)
                _canvas.DrawArc(at, radius + 6f, 0, Mathf.Tau, 32, SandboxPalette.TextBright, 2f, true);

            // Labels are set at a fixed point size, so they stay legible zoomed out while the
            // hex under them does not — which means their offsets have to be measured off the
            // drawn footprint rather than off the hex, or the name sits on the dot.
            var name = radius + 7f;

            // Current over maximum, because the scorer's removal bonus is priced against the
            // maximum: a kill shot on a soldier with seven points left is worth a whole soldier
            // of twenty, and a label that only ever said seven left that arithmetic unreadable.
            DrawCentredText(
                centre + new CoreVec2(0, name),
                $"{unit.Name} {unit.Vitality}/{unit.Stats.Vitality}",
                11,
                hue,
                widthPixels: 132f);   // "Watchman 20/20" is wider than a hex

            // What the other side has worked out. Coarse on purpose — a rung on a ladder, never
            // a number. Our own exposure is the figure we get to read exactly, in the HUD.
            if (unit.Side == Side.Hostile)
            {
                var readout = WorstReadout(frame, unit);
                DrawCentredText(
                    centre + new CoreVec2(0, name + 9f),
                    readout.State.ToString().ToUpperInvariant(),
                    10,
                    SandboxPalette.AlarmHue(readout.State));
            }
        }
    }

    /// <summary>
    /// Somebody standing on another storey: a hollow ring where they are, and their name.
    /// </summary>
    /// <remarks>
    /// The sandbox draws one storey at a time and always has, which on a compound of two rooms
    /// was fine. On the waystation it is not: the roof of the house and the platform of the
    /// watchtower are layer one, so half the garrison — the signaller who has the radio and the
    /// rifleman who covers the crossroads — vanished off a picture of the ground they are
    /// looking at. A hollow ring says where they are without pretending they are on this floor.
    /// <para>
    /// Their attention field is drawn all the same, by the caller, because a soldier four metres
    /// up is watching this ground and not some other ground: the field is a plan of where the
    /// attention goes, and height enters the model through sight lines, which the field does not
    /// claim to draw. Leaving it out was tried first and it hid the most interesting fact on the
    /// map, which is that the tower reaches 45 metres and our people are standing at 55.
    /// </para>
    /// </remarks>
    private void DrawUpstairs(SandboxFrame frame, Unit unit, CoreVec2 centre, Vector2 at, Color hue)
    {
        var radius = Mathf.Max(3f, Scale.HexRadiiToPixels(0.20f));
        _canvas.DrawArc(at, radius, 0, Mathf.Tau, 20, new Color(hue, 0.65f), 1.5f, true);

        DrawCentredText(
            centre + new CoreVec2(0, radius + 7f),
            $"{unit.Name} ({(unit.Position.Layer > frame.Layer ? "above" : "below")})",
            10,
            new Color(hue, 0.65f),
            widthPixels: 132f);
    }

    /// <summary>
    /// How much of its attention a soldier has on each part of the ground round it, drawn at the
    /// reach the rules actually judge by.
    /// </summary>
    /// <remarks>
    /// <para>
    /// This is entry 006 in <c>docs/decisions.md</c>, closed. What was drawn before was a
    /// 3.4-hex wedge across the front arc: a figure picked because it looked right, with no
    /// relation to <c>AwarenessModel.SightRangeMetres</c>, so the cone reported a soldier's
    /// direction honestly and its range not at all. The entry says the honest version is 45
    /// metres, which at the interim viewing distance was 1980 pixels against a 1600 pixel
    /// viewport — a screen-filling wash showing nothing — and that it could not be fixed until
    /// the metres-per-hex figure was settled. It was, by entry 007; and the second half of the
    /// answer is <see cref="SandboxCamera"/>, because 45 metres is only a wash if you insist on
    /// standing four metres from the map. Seen at the zoom the whole waystation fits in, it is
    /// about half the width of the map, which is what it is.
    /// </para>
    /// <para>
    /// Two things the model says and the old wedge did not. <b>Attention is graded, not a yes or
    /// a no</b>: <c>AwarenessTracker.AttentionOn</c> gives the front arc its full rate, the
    /// peripheral band <c>PeripheralAcuity</c>, and everything behind <c>RearAcuity</c> — which
    /// is not nought, because people do turn round. The gap between the last two is the entire
    /// reason flanking works and the wedge drew neither of them. <b>And range tells against you
    /// gently and then sharply</b>: <c>LookGain</c> scales by <c>1 - (d/range)²</c>, so the fill
    /// here is the product of the two terms, sampled at the middle of each ring. What is on
    /// screen is the two factors the detection model multiplies, and nothing else — exposure and
    /// stance belong to a particular target and this is a field, not a shot.
    /// </para>
    /// <para>
    /// Drawn as nested sectors rather than as rings, outermost first, each one filled at the
    /// alpha that brings the accumulated composite to the value the model gives for that ring:
    /// <c>a = (target - carried) / (1 - carried)</c>. Sectors are convex and Godot fills them
    /// exactly; an annulus is not, and would have needed either a triangulation or a quad strip
    /// per band, for a picture no different. The circle at the edge is where a look stops being
    /// worth anything at all, however exposed you are standing.
    /// </para>
    /// </remarks>
    private void DrawAttentionField(SandboxFrame frame, Unit unit, Vector2 at, Color hue)
    {
        var model = frame.Battle.Awareness.Model;
        var reach = Scale.MetresToPixels(model.SightRangeMetres);

        var mine = unit == frame.Battle.Active;
        var peak = mine ? AttentionPeakActive
            : unit.Side == Side.Hostile ? AttentionPeakHostile
            : AttentionPeakIdle;

        var bearing = Bearing(unit.Facing);
        var front = Mathf.DegToRad((float)model.FrontArcDegrees) / 2f;
        var side = Mathf.DegToRad((float)model.PeripheralArcDegrees) / 2f;

        // The three rates AttentionOn reports, as the four arcs they apply over.
        (float From, float To, double Acuity)[] arcs =
        [
            (-front, front, 1.0),
            (front, side, model.PeripheralAcuity),
            (-side, -front, model.PeripheralAcuity),
            (side, Mathf.Tau - side, model.RearAcuity),
        ];

        foreach (var (from, to, acuity) in arcs)
        {
            var carried = 0f;
            for (var ring = AttentionRings; ring >= 1; ring--)
            {
                // LookGain's range term at the middle of this ring.
                var closeness = (ring - 0.5f) / AttentionRings;
                var target = peak * (1f - closeness * closeness) * (float)acuity;

                var alpha = (target - carried) / (1f - carried);
                carried = target;

                _canvas.DrawColoredPolygon(
                    Sector(at, bearing + from, bearing + to, reach * ring / AttentionRings),
                    new Color(hue, alpha));
            }
        }

        // Where it stops, drawn crisply for the two that are being read and left implicit in the
        // falloff for the rest. Seven of these circles on one map is a spirograph.
        if (mine || unit.Side == Side.Hostile)
            _canvas.DrawArc(at, reach, 0, Mathf.Tau, 96, new Color(hue, 0.45f), 1.5f, true);
    }

    /// <summary>
    /// The arc a unit is holding, out as far as it could actually shoot along it.
    /// </summary>
    /// <remarks>
    /// An arc being held is a different thing from an arc being attended to: anything that moves
    /// inside this one gets shot at. So its reach is the weapon's and not the eye's —
    /// <c>ReactionWindow</c> puts no range of its own on an overwatch, it just asks for a shot,
    /// and a shot is refused past <c>WeaponProfile.MaxRange</c>. The inner fill is the optimal
    /// band, which is the same figure the cursor line names. On the waystation the difference is
    /// the whole point: a slug rifle holds an arc 55 m deep and a pulse carbine 42, and on the
    /// old compound both reached clean off the map.
    /// <para>
    /// An overwatch needs a reserve to be worth drawing; an armed ambush stands whether or not
    /// this member can still contribute to it.
    /// </para>
    /// </remarks>
    private void DrawHeldArc(Unit unit, Vector2 at)
    {
        if (unit.Held is not { } order) return;
        if (unit.Overwatch is not null && unit.Reserve <= 0) return;

        var tint = unit.Ambush is not null ? SandboxPalette.AmbushHue : SandboxPalette.OverwatchHue;
        var bearing = Bearing(order.Centre);
        var half = Mathf.DegToRad((float)order.Arc.Degrees) / 2f;

        var covered = Sector(at, bearing - half, bearing + half, Scale.MetresToPixels(unit.Weapon.MaxRange));

        _canvas.DrawColoredPolygon(covered, new Color(tint, 0.08f));
        _canvas.DrawColoredPolygon(
            Sector(at, bearing - half, bearing + half, Scale.MetresToPixels(unit.Weapon.OptimalRange)),
            new Color(tint, 0.10f));
        _canvas.DrawPolyline([.. covered, covered[0]], new Color(tint, 0.55f), 1.5f, true);
    }

    /// <summary>A hex bearing as a screen angle.</summary>
    private float Bearing(HexDirection direction)
        => (float)(direction.BearingRadians() + Scale.Canvas.RotationRadians);

    /// <summary>
    /// A pie slice in screen space, from one bearing round to another.
    /// </summary>
    /// <remarks>
    /// One point every six degrees, floored at three, so an arc's smoothness follows its width
    /// rather than being a constant somebody has to remember. The constant it replaces was
    /// eighteen steps whatever the angle, and a stray change to it is the 546-pixel difference
    /// <c>docs/subprojects/view.md</c> tells the story of.
    /// </remarks>
    private static Vector2[] Sector(Vector2 at, float from, float to, float reach)
    {
        var steps = Mathf.Max(3, Mathf.CeilToInt(Mathf.Abs(to - from) / Mathf.DegToRad(6f)));
        var slice = new Vector2[steps + 2];
        slice[0] = at;

        for (var i = 0; i <= steps; i++)
        {
            var angle = Mathf.Lerp(from, to, (float)i / steps);
            // Core bearings run with +Y north; the screen runs with +Y down.
            slice[i + 1] = at + new Vector2(Mathf.Cos(angle), -Mathf.Sin(angle)) * reach;
        }

        return slice;
    }

    /// <summary>
    /// Where each enemy believes one of ours to be. The marker is what they last saw, so it
    /// goes stale the moment that soldier moves — and the gap between marker and truth is the
    /// thing the approach is played in.
    /// </summary>
    private void DrawBeliefs(SandboxFrame frame)
    {
        foreach (var hostile in frame.Battle.InPlay.Where(u => u.Side == Side.Hostile))
        foreach (var mine in frame.Battle.InPlay.Where(u => u.Side == Side.Player))
        {
            var readout = frame.Battle.Awareness.ReadoutFor(hostile.Id, mine.Id);
            if (readout.State < AwarenessState.Searching) continue;
            if (readout.LastKnownPosition is not { } believed) continue;
            if (believed == mine.Position) continue;      // they are simply right
            if (believed.Layer != frame.Layer) continue;

            var centre = Geometry.NodeCentre(frame.Battle.Map, believed);
            _canvas.DrawArc(
                SandboxScale.ToScreen(centre), Scale.HexRadiiToPixels(0.30f),
                0, Mathf.Tau, 24, SandboxPalette.GhostHue, 2f, true);

            DrawCentredText(
                centre + new CoreVec2(0, -Scale.HexRadiiToPixels(0.06f)), "?", 16, SandboxPalette.GhostHue);
        }
    }

    /// <summary>The most alarmed any of ours has made this enemy.</summary>
    private static AwarenessReadout WorstReadout(SandboxFrame frame, Unit hostile)
    {
        var worst = AwarenessReadout.Nothing;
        foreach (var mine in frame.Battle.InPlay.Where(u => u.Side == Side.Player))
        {
            var readout = frame.Battle.Awareness.ReadoutFor(hostile.Id, mine.Id);
            if (readout.State > worst.State) worst = readout;
        }
        return worst;
    }

    /// <remarks>
    /// Wall weights are pixels and stay pixels at any zoom. A solid wall drawn a tenth of a hex
    /// thick disappears from an overview of the waystation, and the walls are the one thing an
    /// overview is for: where the compound, the barn and the cottages are is the whole shape of
    /// the map. They go slightly heavy relative to the tiles when zoomed out, which is right.
    /// </remarks>
    private void DrawWalls(SandboxFrame frame)
    {
        foreach (var wall in frame.Battle.Map.Walls.Where(w => w.Layer == frame.Layer))
        {
            var a = SandboxScale.ToScreen(Scale.Canvas.Position(wall.A));
            var b = SandboxScale.ToScreen(Scale.Canvas.Position(wall.B));
            if (!frame.Visible.HasPoint(a) && !frame.Visible.HasPoint(b)) continue;

            var (color, width) = StyleFor(wall.Profile);
            _canvas.DrawLine(a, b, color, width, true);
        }
    }

    /// <summary>
    /// What a wall looks like, decided from what the wall <em>does</em>.
    /// </summary>
    /// <remarks>
    /// The same decision as <see cref="FillFor"/> and for the same reason: this used to switch on
    /// six well-known ids, so the waystation's <c>hedge</c> — a profile the map declares for
    /// itself — drew in the fallback grey along with every profile any future map invents. Entry
    /// 035 wrote that down as a gotcha and entry 038 asked for a decision. It is: <b>colour and
    /// weight come from the figures, never from the name.</b>
    /// <para>
    /// The <b>hue</b> says what it is worth to a plan: green if you can walk through it, white if
    /// it is a building wall that nothing gets over, and otherwise the colour of the cover it
    /// gives, matching the cover outlines on the tiles either side of it. The <b>weight</b> says
    /// how much of a body it stops — see-through is a hairline, walk-through is thin, vault is
    /// thicker, climb thicker again, and a wall that stops you outright is the heaviest thing on
    /// the map.
    /// </para>
    /// <para>
    /// <b>All six built-in profiles come out at exactly the colour and weight the hand-written
    /// table gave them</b>, which is the check worth having: the figures were what the names had
    /// been standing in for all along, and nobody had noticed because there was never a seventh
    /// profile to disagree. The waystation's hedge — 1.5 m, light cover, walk through, cannot see
    /// through — now draws as a hedge because of what it is rather than because it was listed.
    /// </para>
    /// </remarks>
    private static (Color Color, float Width) StyleFor(WallProfile profile)
    {
        var hue =
            !profile.BlocksMovement ? new Color("74b06a")                          // push through it
            : profile.Cover == CoverGrade.Full && !profile.Climbable ? new Color("e6e9ee")   // a building
            : profile.Cover switch
            {
                CoverGrade.Full => new Color("d1743c"),
                CoverGrade.Half => new Color("d8b25a"),
                CoverGrade.Light => new Color("6fa8c8"),
                _ => new Color("aaaaaa"),
            };

        var width =
            !profile.Opaque ? 3f                    // see through it: a railing, a parapet
            : !profile.BlocksMovement ? 5f          // walk through it: a screen, a hedge
            : profile.Vaultable ? 6f                // waist high: over it and keep going
            : profile.Climbable ? 8f                // head high: over it, slowly
            : 10f;                                  // a building wall

        return (hue, width);
    }

    private void DrawAuthoredLinks(SandboxFrame frame)
    {
        foreach (var link in frame.Battle.Map.Links.Where(l => l.From.Layer == frame.Layer || l.To.Layer == frame.Layer))
        {
            var address = link.From.Layer == frame.Layer ? link.From : link.To;
            var centre = Scale.Canvas.Center(address.Hex);
            var at = SandboxScale.ToScreen(centre);
            if (!frame.Visible.HasPoint(at)) continue;

            _canvas.DrawCircle(at, Mathf.Max(4f, Scale.HexRadiiToPixels(0.30f)), SandboxPalette.LinkFill);
            if (frame.TileDetail)
                DrawCentredText(centre, link.Kind.ToString().ToUpperInvariant(), 11, SandboxPalette.LinkText);
        }
    }

    /// <summary>
    /// The route somebody has committed to and not yet walked, with the ticks along it.
    /// </summary>
    /// <remarks>
    /// Only ever on screen while a reaction window is open, and it is the one thing that makes
    /// that state readable. The mover has paid for this walk and is still standing at the start
    /// of it — entry 040 — so without the route drawn, a player looking at the map sees a soldier
    /// who has apparently done nothing and is being shot at for it. The tick numbers are the
    /// clock the options in the readout are quoted against: a reaction placed at t3 lands where
    /// the label says 3.
    /// </remarks>
    private void DrawCommitted(SandboxFrame frame)
    {
        if (frame.Open is not { } window) return;

        var map = frame.Battle.Map;
        var steps = window.Move.Steps;
        if (steps.Count < 2) return;

        var points = steps.Select(s => SandboxScale.ToScreen(Geometry.NodeCentre(map, s.Node))).ToArray();
        _canvas.DrawPolyline(points, SandboxPalette.CommittedColor, 3f, true);

        if (!frame.TileDetail) return;

        foreach (var step in steps.Skip(1))
            DrawCentredText(
                Geometry.NodeCentre(map, step.Node) + new CoreVec2(0, -Scale.HexRadiiToPixels(0.34f)),
                $"t{step.Tick}",
                11,
                SandboxPalette.CommittedColor);
    }

    /// <summary>
    /// Where our side may walk off the field, if the mission gives us somewhere.
    /// </summary>
    /// <remarks>
    /// A named place rather than a map edge, which is entry 041's choice and not this file's, and
    /// it has to be drawn or it does not exist: an exit nobody can find is the same as no exit,
    /// and until this the only way to know where the cottages were was to read the map file.
    /// Ours only. Where the other side is going is theirs to know.
    /// </remarks>
    private void DrawExit(SandboxFrame frame)
    {
        if (frame.Battle.ObjectiveOf(Side.Player) is not Withdrawal way) return;

        foreach (var node in way.Exit.Where(n => n.Layer == frame.Layer))
        {
            var regions = frame.Battle.Map.RegionsOf(node.Tile);
            var region = regions.FirstOrDefault(r => r.Index == node.Region);
            if (region is null) continue;

            var polygon = Geometry.RegionPolygon(node.Tile, region, inset: 0.06f);
            if (!frame.Visible.HasPoint(polygon[0])) continue;

            _canvas.DrawColoredPolygon(polygon, SandboxPalette.ExitFill);
            _canvas.DrawPolyline([.. polygon, polygon[0]], SandboxPalette.CoverLightHue, 2f, true);
        }
    }

    private void DrawPath(SandboxFrame frame)
    {
        if (frame.Battle.Active is not { } active) return;
        if (frame.Hover is not { } goal || !frame.Reach.TryGetPath(goal, out var path) || path.Count == 0) return;

        var map = frame.Battle.Map;
        var points = new List<Vector2> { SandboxScale.ToScreen(Geometry.NodeCentre(map, active.Position)) };
        points.AddRange(path.Select(link => SandboxScale.ToScreen(Geometry.NodeCentre(map, link.To))));
        _canvas.DrawPolyline([.. points], SandboxPalette.PathColor, 3f, true);

        foreach (var link in path.Where(l => l.Kind != TraversalKind.Walk))
            DrawCentredText(
                Geometry.NodeCentre(map, link.To) + new CoreVec2(0, -Scale.HexRadiiToPixels(0.30f)),
                link.Kind.ToString().ToUpperInvariant(),
                11,
                SandboxPalette.PathColor);
    }

    /// <param name="widthPixels">
    /// How wide a box the text is centred in. Godot clips at the box edge rather than spilling
    /// over it, so anything longer than a tile-cost label asks for more.
    /// </param>
    /// <remarks>
    /// In pixels rather than in hex radii, which is what it used to be. Text is set at a point
    /// size and does not shrink with the zoom, so a box quoted in hexes goes narrower than the
    /// string inside it the moment the camera pulls back, and every label on the map loses its
    /// last few characters at once.
    /// </remarks>
    private void DrawCentredText(CoreVec2 canvasPosition, string text, int size, Color color, float widthPixels = 88f)
    {
        var at = SandboxScale.ToScreen(canvasPosition) + new Vector2(-widthPixels / 2f, size * 0.36f);
        _canvas.DrawString(_font, at, text, HorizontalAlignment.Center, widthPixels, size, color);
    }
}
