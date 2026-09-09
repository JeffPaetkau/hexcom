using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Awareness;
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
public sealed class BattleView(CanvasItem canvas, SandboxScale scale, SandboxGeometry geometry, Font font)
{
    /// <summary>
    /// How far the attention cone is drawn, in hex radii.
    /// </summary>
    /// <remarks>
    /// A legibility figure, chosen because it reads well, and <b>not</b>
    /// <c>AwarenessModel.SightRangeMetres</c> — which at the interim
    /// <see cref="SandboxScale.MetresPerHexSize"/> reaches roughly twice across the whole demo
    /// map and would fill the viewport with flat colour. So the cone shows a soldier's
    /// <i>direction</i> honestly and its <i>range</i> not at all. That gap is a real interface
    /// problem rather than a drawing preference, and it is recorded as such in
    /// <c>docs/decisions.md</c>; it cannot be closed until the metres-per-hex figure is settled.
    /// </remarks>
    private const float ConeHexRadii = 3.4f;

    /// <summary>How far a held arc is drawn, in hex radii. Same caveat as <see cref="ConeHexRadii"/>.</summary>
    private const float HeldArcHexRadii = 5.2f;

    private readonly CanvasItem _canvas = canvas;
    private readonly SandboxScale _scale = scale;
    private readonly SandboxGeometry _geometry = geometry;
    private readonly Font _font = font;

    public void Draw(SandboxFrame frame)
    {
        DrawTiles(frame);
        DrawWalls(frame);
        DrawAuthoredLinks(frame);
        DrawPath(frame);
        DrawBeliefs(frame);
        DrawUnits(frame);
    }

    private void DrawTiles(SandboxFrame frame)
    {
        foreach (var tile in frame.Battle.Map.Tiles.Where(t => t.Address.Layer == frame.Layer))
        foreach (var region in frame.Battle.Map.RegionsOf(tile.Address))
        {
            var id = new NodeId(tile.Address, region.Index);
            var polygon = _geometry.RegionPolygon(tile.Address, region, inset: 0.06f);

            _canvas.DrawColoredPolygon(polygon, FillFor(frame, tile, region, id));

            var outline = SandboxPalette.RegionEdge;
            var weight = 1f;

            if (frame.View.TryGetValue(id, out var seen))
            {
                // Dead ground the active unit has no eyes on.
                if (!seen.CanSee) _canvas.DrawColoredPolygon(polygon, SandboxPalette.Unseen);
                else if (seen.Cover != CoverGrade.None)
                {
                    outline = SandboxPalette.CoverHue(seen.Cover);
                    weight = 2.5f;
                }
            }

            _canvas.DrawPolyline([.. polygon, polygon[0]], outline, weight, true);

            if (frame.Reach.CostTo(id) is { } cost && cost > 0 && frame.Battle.UnitAt(id) is null)
                DrawCentredText(_geometry.Centroid(tile.Address, region), cost.ToString(), 15, SandboxPalette.TextDim);
        }
    }

    private static Color FillFor(SandboxFrame frame, Tile tile, HexRegion region, NodeId id)
    {
        if (frame.Battle.Active is { } active && frame.Reach.CanReach(id) && frame.Battle.CanStopAt(active, id))
            return SandboxPalette.ReachFill;
        if (!region.Occupiable) return SandboxPalette.TransitFill;   // crossable, but nowhere to stand
        if (tile.Ground.ExtraApCost > 0) return SandboxPalette.RoughFill;
        return SandboxPalette.FloorFill;
    }

    private void DrawUnits(SandboxFrame frame)
    {
        foreach (var unit in frame.Battle.InPlay.Where(u => u.Position.Layer == frame.Layer))
        {
            var centre = _geometry.NodeCentre(frame.Battle.Map, unit.Position);
            var at = SandboxScale.ToScreen(centre);
            var hue = SandboxPalette.SideHue(unit.Side);

            // Stance, drawn as footprint. A prone soldier really is a smaller thing to see, and
            // this is the only place on screen that says so before you read a number.
            var radius = _scale.HexRadiiToPixels(unit.Stance switch
            {
                Stance.Prone => 0.16f,
                Stance.Crouching => 0.21f,
                _ => 0.27f,
            });

            DrawWatchCone(frame, unit, at, hue);
            _canvas.DrawCircle(at, radius, hue);
            _canvas.DrawCircle(at, radius, SandboxPalette.UnitOutline, false, 2f);

            if (unit == frame.Battle.Active)
                _canvas.DrawArc(at, radius + 6f, 0, Mathf.Tau, 32, SandboxPalette.TextBright, 2f, true);

            // Current over maximum, because the scorer's removal bonus is priced against the
            // maximum: a kill shot on a soldier with seven points left is worth a whole soldier
            // of twenty, and a label that only ever said seven left that arithmetic unreadable.
            DrawCentredText(
                centre + new CoreVec2(0, _scale.HexRadiiToPixels(0.42f)),
                $"{unit.Name} {unit.Vitality}/{unit.Stats.Vitality}",
                11,
                hue,
                widthRadii: 3f);   // "Watchman 20/20" is wider than a hex

            // What the other side has worked out. Coarse on purpose — a rung on a ladder, never
            // a number. Our own exposure is the figure we get to read exactly, in the HUD.
            if (unit.Side == Side.Hostile)
            {
                var readout = WorstReadout(frame, unit);
                DrawCentredText(
                    centre + new CoreVec2(0, _scale.HexRadiiToPixels(0.62f)),
                    readout.State.ToString().ToUpperInvariant(),
                    10,
                    SandboxPalette.AlarmHue(readout.State));
            }
        }
    }

    /// <summary>
    /// The arc a unit is actually watching. Outside it things are noticed slowly, and behind it
    /// barely at all — which is what makes a position flankable rather than merely approached.
    /// </summary>
    private void DrawWatchCone(SandboxFrame frame, Unit unit, Vector2 at, Color hue)
    {
        var attention = Wedge(
            at,
            unit.Facing,
            frame.Battle.Awareness.Model.FrontArcDegrees,
            _scale.HexRadiiToPixels(ConeHexRadii));

        _canvas.DrawColoredPolygon(attention, new Color(hue, unit == frame.Battle.Active ? 0.16f : 0.10f));

        // An arc being held is a different thing from an arc being attended to: anything that
        // moves inside this one gets shot at. An overwatch needs a reserve to be worth drawing;
        // an armed ambush stands whether or not this member can still contribute to it.
        if (unit.Held is not { } order) return;
        if (unit.Overwatch is not null && unit.Reserve <= 0) return;

        var tint = unit.Ambush is not null ? SandboxPalette.AmbushHue : SandboxPalette.OverwatchHue;
        var covered = Wedge(at, order.Centre, order.Arc.Degrees, _scale.HexRadiiToPixels(HeldArcHexRadii));

        _canvas.DrawColoredPolygon(covered, new Color(tint, 0.12f));
        _canvas.DrawPolyline([.. covered, covered[0]], new Color(tint, 0.55f), 1.5f, true);
    }

    /// <summary>A pie slice centred on a hex bearing, in screen space.</summary>
    private Vector2[] Wedge(Vector2 at, HexDirection centre, double degrees, float reach)
    {
        var half = Mathf.DegToRad((float)degrees / 2f);
        var bearing = (float)(centre.BearingRadians() + _scale.Canvas.RotationRadians);

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

            var centre = _geometry.NodeCentre(frame.Battle.Map, believed);
            _canvas.DrawArc(
                SandboxScale.ToScreen(centre), _scale.HexRadiiToPixels(0.30f),
                0, Mathf.Tau, 24, SandboxPalette.GhostHue, 2f, true);

            DrawCentredText(
                centre + new CoreVec2(0, -_scale.HexRadiiToPixels(0.06f)), "?", 16, SandboxPalette.GhostHue);
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

    private void DrawWalls(SandboxFrame frame)
    {
        foreach (var wall in frame.Battle.Map.Walls.Where(w => w.Layer == frame.Layer))
        {
            var (color, width) = StyleFor(wall.Profile);
            _canvas.DrawLine(
                SandboxScale.ToScreen(_scale.Canvas.Position(wall.A)),
                SandboxScale.ToScreen(_scale.Canvas.Position(wall.B)),
                color, width, true);
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

    private void DrawAuthoredLinks(SandboxFrame frame)
    {
        foreach (var link in frame.Battle.Map.Links.Where(l => l.From.Layer == frame.Layer || l.To.Layer == frame.Layer))
        {
            var address = link.From.Layer == frame.Layer ? link.From : link.To;
            var centre = _scale.Canvas.Center(address.Hex);

            _canvas.DrawCircle(
                SandboxScale.ToScreen(centre), _scale.HexRadiiToPixels(0.30f), SandboxPalette.LinkFill);
            DrawCentredText(centre, link.Kind.ToString().ToUpperInvariant(), 11, SandboxPalette.LinkText);
        }
    }

    private void DrawPath(SandboxFrame frame)
    {
        if (frame.Battle.Active is not { } active) return;
        if (frame.Hover is not { } goal || !frame.Reach.TryGetPath(goal, out var path) || path.Count == 0) return;

        var map = frame.Battle.Map;
        var points = new List<Vector2> { SandboxScale.ToScreen(_geometry.NodeCentre(map, active.Position)) };
        points.AddRange(path.Select(link => SandboxScale.ToScreen(_geometry.NodeCentre(map, link.To))));
        _canvas.DrawPolyline([.. points], SandboxPalette.PathColor, 3f, true);

        foreach (var link in path.Where(l => l.Kind != TraversalKind.Walk))
            DrawCentredText(
                _geometry.NodeCentre(map, link.To) + new CoreVec2(0, -_scale.HexRadiiToPixels(0.30f)),
                link.Kind.ToString().ToUpperInvariant(),
                11,
                SandboxPalette.PathColor);
    }

    /// <param name="widthRadii">
    /// How wide a box the text is centred in, in hex radii. Two is a hex, and Godot clips at the
    /// box edge rather than spilling over it, so anything longer than a tile-cost label asks for
    /// more.
    /// </param>
    private void DrawCentredText(CoreVec2 canvasPosition, string text, int size, Color color, float widthRadii = 2f)
    {
        var width = _scale.HexRadiiToPixels(widthRadii);
        var at = SandboxScale.ToScreen(canvasPosition) + new Vector2(-width / 2f, size * 0.36f);
        _canvas.DrawString(_font, at, text, HorizontalAlignment.Center, width, size, color);
    }
}
