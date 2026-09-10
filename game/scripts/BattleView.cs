using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>
/// A soldier part way along a route it has, in the rules, already finished walking.
/// </summary>
/// <param name="Mover">Whose walk it is. Drawn here instead of where the battle says it stands.</param>
/// <param name="At">Where on the plane it has got to.</param>
/// <param name="Floor">The height of the ground under that point.</param>
/// <param name="Bearing">Which way it is heading, so the facing bar points along the route.</param>
/// <param name="Ahead">The rest of the route, drawn so the walk has somewhere visible to be going.</param>
/// <remarks>
/// <b>The rules are finished before any of this is drawn.</b> Entry 040 says the mover has not
/// stepped until the window resolves, so the walk is that resolution shown over time and never a
/// state the battle is in: by the time a walk starts the soldier is already at the far end, every
/// reaction has been taken, and what moves is the picture catching up. Nothing may be asked of
/// the battle part way along one, and nothing here does — the interpolation is between two points
/// the rules handed back.
/// </remarks>
public sealed record UnitWalk(UnitId Mover, CoreVec2 At, double Floor, double Bearing, IReadOnlyList<NodeId> Ahead);

/// <summary>
/// The world, built: ground at its floor heights, walls at their band heights, ladders, the
/// planned route, what each side knows of the other, and the soldiers as bodies.
/// </summary>
/// <remarks>
/// <para>
/// Presentation, as distinct from the readouts in <see cref="BattleHud"/>. This class consumes
/// the rules and builds whatever they answer into meshes under one <c>Node3D</c>, plus the
/// labels that belong to the map, which it paints on a flat canvas over the picture because text
/// is set at a point size and does not shrink with distance. The HUD decides what the player is
/// allowed to <i>ask</i>; this decides only how it looks. They can reach nothing of each other's
/// — each takes a <see cref="SandboxFrame"/> and its own surface to draw on.
/// </para>
/// <para>
/// Nothing here implements a rule, and the third dimension made that easier rather than harder:
/// every height on screen is a figure the rules already hold. A tile stands at
/// <c>Tile.FloorHeight</c>, a wall runs from <c>WallBaseHeight</c> to <c>WallTopHeight</c>, a
/// body is <c>StanceProfile.BodyHeight</c> tall with its eye at <c>EyeHeight</c> — the numbers
/// contract 6 in <c>docs/map.md</c> freezes, read from the source rather than remembered. What
/// the picture shows is the geometry <c>SightSolver</c> traces against, so a wall that looks as
/// though it should hide a soldier and does not is a finding about the rules and not about
/// the drawing.
/// </para>
/// <para>
/// <b>Readouts on the ground are tinted hexes, not shapes.</b> The flat view drew the attention
/// field as nested pie slices and the held arc as a wedge. Here both are painted onto the tiles
/// they cover, one hex at a time, at the value the model gives for that hex: the attention
/// field asks <c>AttentionOn</c> for the tile and scales it by the range term the look-gain
/// uses, and the arc asks <c>AngleOffDegrees</c> whether the tile is inside it. Two reasons. A
/// flat disc drawn at one height vanishes under a ridge and floats over a hollow, where a tint
/// on the tile follows the ground. And it is the rules' own answer per place rather than an
/// illustration of the rule — which is contract 2, and also means that when a balance dial
/// moves the picture moves with it, with nothing here to update.
/// </para>
/// <para>
/// <b>What the picture shows of the other side is decided by the frame, not here.</b>
/// <see cref="SandboxFrame.Sees"/> says whether a hostile is a body, and
/// <see cref="SandboxFrame.Knowledge"/> says where a ghost stands and how much it is worth. This
/// class asks and draws. The one thing it adds is what a ghost looks like — a translucent
/// standing body at the marker, because a marker is a soldier who was there — and that a hostile
/// nobody has heard of is not drawn at all, which is the whole of what makes this a game rather
/// than a tool.
/// </para>
/// </remarks>
public sealed class BattleView
{
    /// <summary>
    /// Alpha the front arc of an attention field is tinted at, nearest the soldier, by whose it is.
    /// </summary>
    /// <remarks>
    /// A soldier attends to everything within 45 metres at some rate, so every one of these
    /// fields covers most of the map, and seven of them at one weight is a wash whatever the
    /// falloff does. The weights are an interface judgement about which of them a player is
    /// reading: the soldier whose turn it is, because their facing is a decision being made now,
    /// and every enemy, because the whole approach is played against those. Our own idle
    /// soldiers are the noise and are drawn faintly rather than dropped, which would be a
    /// different claim.
    /// </remarks>
    private const float AttentionPeakActive = 0.20f;
    private const float AttentionPeakHostile = 0.10f;
    private const float AttentionPeakIdle = 0.04f;

    /// <summary>How far above a tile's top its tints and ribbons sit, so they win the depth test against it.</summary>
    private const float Lift = 0.04f;

    /// <summary>How far below its floor a tile's plinth reaches, so raised ground has a face.</summary>
    private const double Plinth = 0.3;

    /// <summary>What a storey above the one being looked at is drawn at, so the floor under it can be read.</summary>
    private const float GhostedAlpha = 0.16f;

    private readonly Node3D _root;
    private readonly CanvasItem _labels;
    private readonly SandboxCamera _camera;
    private readonly Font _font;

    private readonly MeshInstance3D _ground;
    private readonly MeshInstance3D _structure;
    private readonly MeshInstance3D _bodies;
    private readonly MeshInstance3D _ghosted;
    private readonly MeshInstance3D _overlay;
    private readonly MeshInstance3D _cursor;

    /// <summary>The moment the meshes were built from, kept so the labels are drawn from the same answers.</summary>
    private SandboxFrame? _frame;

    /// <summary>
    /// The walk being drawn, or null when nobody is part way along one.
    /// </summary>
    /// <remarks>
    /// Not on <see cref="SandboxFrame"/>, and deliberately: a frame is one moment's <em>answers</em>
    /// from the rules, read by the view and the HUD alike, and where a body has got to along a
    /// route the rules have already finished is neither an answer nor anything the readouts want.
    /// It is set by the node once a frame while a walk is running and is presentation's alone.
    /// </remarks>
    public UnitWalk? Walk { get; set; }

    public BattleView(Node3D root, CanvasItem labels, SandboxCamera camera, Font font)
    {
        _root = root;
        _labels = labels;
        _camera = camera;
        _font = font;

        _ground = Instance("Ground", SandboxPalette.Solid);
        _structure = Instance("Structure", SandboxPalette.Solid);
        _bodies = Instance("Bodies", SandboxPalette.Solid);
        _ghosted = Instance("Ghosted", SandboxPalette.ClearBehind);
        _overlay = Instance("Overlay", SandboxPalette.Clear);
        _cursor = Instance("Cursor", SandboxPalette.Clear);
    }

    private MeshInstance3D Instance(string name, Material material)
    {
        var instance = new MeshInstance3D { Name = name, MaterialOverride = material };
        _root.AddChild(instance);
        return instance;
    }

    /// <summary>
    /// Rebuild everything that depends on the battle: called after any action, and never on a
    /// camera move.
    /// </summary>
    /// <remarks>
    /// Six meshes, rebuilt whole. It is tempting to keep the ground and only rebuild the tints,
    /// and it would be wrong: the ground's colour depends on the active soldier's reach, so it
    /// changes on every pass anyway, and one path that rebuilds everything is one path that
    /// cannot leave a stale mesh behind. Measured on the waystation the whole rebuild is a few
    /// milliseconds, well inside the sight sweep that precedes it.
    /// </remarks>
    public void Rebuild(SandboxFrame frame)
    {
        _frame = frame;

        var ground = new MeshBuilder();
        var structure = new MeshBuilder();
        var bodies = new MeshBuilder();
        var ghosted = new MeshBuilder();
        var overlay = new MeshBuilder();

        BuildTiles(frame, ground, ghosted);
        BuildWalls(frame, structure, ghosted);
        BuildLinks(frame, structure);
        BuildExit(frame, overlay);
        BuildUnseen(frame, overlay);
        BuildAttention(frame, overlay);
        BuildHeldArcs(frame, overlay);
        BuildCoverOutlines(frame, overlay);
        BuildCommitted(frame, overlay);
        BuildBeliefs(frame, overlay);
        BuildGhosts(frame, overlay);

        _ground.Mesh = ground.Build();
        _structure.Mesh = structure.Build();
        _ghosted.Mesh = ghosted.Build();
        _overlay.Mesh = overlay.Build();

        RebuildBodies(frame);
        RebuildCursor(frame);
    }

    /// <summary>Rebuild only the soldiers, which is what a walk moves and nothing else.</summary>
    /// <remarks>
    /// Its own mesh and its own entry point because a walk redraws the bodies on every frame it
    /// runs for, and the rebuild above is a sight sweep's worth of work behind it. Seven bodies
    /// and their rings is a few dozen triangles. The rings moved into this mesh from the overlay
    /// to make it possible: a ring left behind in the overlay would stay on the tile the soldier
    /// set off from while the soldier walked away from it.
    /// </remarks>
    public void RebuildBodies(SandboxFrame frame)
    {
        _frame = frame;

        var bodies = new MeshBuilder();
        BuildBodies(frame, bodies);
        _bodies.Mesh = bodies.Build();
    }

    /// <summary>Rebuild only what follows the cursor: the previewed route and the hovered hex.</summary>
    /// <remarks>
    /// Its own mesh because the cursor moves every frame the mouse does and the rest of the
    /// world does not. Eighteen hundred prisms per mouse-motion event would be felt.
    /// </remarks>
    public void RebuildCursor(SandboxFrame frame)
    {
        _frame = frame;

        var cursor = new MeshBuilder();
        BuildHover(frame, cursor);
        BuildPath(frame, cursor);
        BuildWalkRoute(frame, cursor);
        _cursor.Mesh = cursor.Build();

        _labels.QueueRedraw();
    }

    /// <summary>The part of a walk that has not been drawn yet, so the body has somewhere to be going.</summary>
    /// <remarks>
    /// In the committed colour rather than the path colour, because it is the same object: a
    /// route that has been paid for. While a window is open it is the yellow line the reaction
    /// options are quoted against; once the window resolves it is this, running out from under
    /// the soldier's feet as it walks. The tick labels go with it — see
    /// <see cref="DrawRouteLabels"/> — which is what the brief meant by drawing the ticks the
    /// reaction line quotes as the soldier passes them.
    /// </remarks>
    private void BuildWalkRoute(SandboxFrame frame, MeshBuilder cursor)
    {
        if (Walk is not { } walk || walk.Ahead.Count == 0) return;

        var map = frame.Battle.Map;
        var points = new List<Vector3> { SandboxScale.ToScene(walk.At, walk.Floor + Lift * 2) };
        points.AddRange(walk.Ahead.Select(node => SandboxGeometry.NodeScene(map, node) + Vector3.Up * (Lift * 2)));

        cursor.Ribbon(points, 0.28f, SandboxPalette.CommittedColor);
    }

    // ---- the world -------------------------------------------------------------------

    /// <remarks>
    /// Every storey is built, and where it is relative to the one being looked at decides how.
    /// At or below it, solid. Above it, ghosted — drawn see-through so that a roof says there is
    /// a roof without hiding the room, which is the third decision in the greybox brief. Cutting
    /// the upper storeys away was the alternative and it loses the tower and the ridge from every
    /// picture of the ground; nothing at all was tried on the flat view and it lost the soldiers
    /// standing on them. Ghosting keeps the shape and gives up only the roof's own labels.
    /// </remarks>
    private static void BuildTiles(SandboxFrame frame, MeshBuilder solid, MeshBuilder ghosted)
    {
        var map = frame.Battle.Map;

        foreach (var tile in map.Tiles)
        {
            var above = tile.Address.Layer > frame.Layer;
            var shown = tile.Address.Layer == frame.Layer;

            foreach (var region in map.RegionsOf(tile.Address))
            {
                var id = new NodeId(tile.Address, region.Index);
                var outline = SandboxGeometry.RegionOutline(tile.Address, region, inset: shown && frame.TileDetail ? 0.06 : 0);
                var fill = FillFor(frame, tile, region, id);

                if (above)
                {
                    ghosted.Flat(outline, tile.FloorHeight, new Color(fill.Lightened(0.3f), GhostedAlpha));
                    continue;
                }

                var bottom = tile.Address.Layer == 0 ? -Plinth : tile.FloorHeight - Plinth;
                solid.Prism(outline, bottom, tile.FloorHeight, fill);
            }
        }
    }

    /// <summary>
    /// What colour a piece of ground is, decided from what the ground <em>does</em>.
    /// </summary>
    /// <remarks>
    /// Entry 049 in <c>docs/decisions.md</c>: <b>by figure, never by name.</b> A map may invent
    /// ground and kit — that is the whole point of the format — so a table of names is a table
    /// that is wrong about every map written after it, and silently. Impassable ground reads as
    /// impassable, ground that costs extra reads as rough, and everything else is floor. Three
    /// figures, all of them declarable, none of them a name.
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

    /// <remarks>
    /// A wall is a box from the height the map says its foot is at to the height the map says
    /// its top is at, which are the two figures the sight trace uses. So a low wall is a metre
    /// tall and a solid one three, because <c>WallProfile.HeightMetres</c> says so, and the
    /// picture is the first place those bands have been visible as bands rather than as a line
    /// weight. The weight survives as thickness: a see-through railing is a hairline and a
    /// building wall is a quarter of a metre.
    /// </remarks>
    private static void BuildWalls(SandboxFrame frame, MeshBuilder solid, MeshBuilder ghosted)
    {
        var map = frame.Battle.Map;
        var layout = SandboxScale.World;

        foreach (var wall in map.Walls)
        {
            var a = layout.Position(wall.A);
            var b = layout.Position(wall.B);
            var bottom = map.WallBaseHeight(wall);
            var top = map.WallTopHeight(wall);
            var (hue, thickness) = StyleFor(wall.Profile);

            if (wall.Layer > frame.Layer)
            {
                ghosted.Slab(a, b, thickness, bottom, top, new Color(hue, GhostedAlpha));
            }
            else if (!wall.Profile.Opaque)
            {
                // A railing or a parapet: the sight trace goes through it, so the eye should too.
                ghosted.Slab(a, b, thickness, bottom, top, new Color(hue, 0.45f));
            }
            else
            {
                solid.Slab(a, b, thickness, bottom, top, hue);
            }
        }
    }

    /// <summary>
    /// What a wall looks like, decided from what the wall <em>does</em>.
    /// </summary>
    /// <remarks>
    /// The same decision as <see cref="FillFor"/> and for the same reason — entry 049. The
    /// <b>hue</b> says what it is worth to a plan: green if you can walk through it, white if it
    /// is a building wall that nothing gets over, and otherwise the colour of the cover it gives,
    /// matching the cover outlines on the tiles either side of it. The <b>thickness</b> says how
    /// much of a body it stops — see-through is a hairline, walk-through is thin, vault is
    /// thicker, climb thicker again, and a wall that stops you outright is the heaviest thing on
    /// the map. All six built-in profiles keep the hue and the ordering the flat table gave them,
    /// which is the check worth having.
    /// </remarks>
    private static (Color Hue, double Thickness) StyleFor(WallProfile profile)
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

        var thickness =
            !profile.Opaque ? 0.05                  // see through it: a railing, a parapet
            : !profile.BlocksMovement ? 0.10        // walk through it: a screen, a hedge
            : profile.Vaultable ? 0.14              // waist high: over it and keep going
            : profile.Climbable ? 0.20              // head high: over it, slowly
            : 0.26;                                 // a building wall

        return (hue, thickness);
    }

    /// <remarks>
    /// A ladder or a stair is a post from the lower floor to the upper one at the hex it starts
    /// in — the one shape that says <em>you can get up here</em> from any angle. Its kind is a
    /// label, because a post that was a ladder and a post that was a stair would be the same
    /// post.
    /// </remarks>
    private static void BuildLinks(SandboxFrame frame, MeshBuilder solid)
    {
        var map = frame.Battle.Map;

        foreach (var link in map.Links)
        {
            var low = System.Math.Min(SandboxGeometry.FloorOf(map, new NodeId(link.From, link.FromRegion)),
                SandboxGeometry.FloorOf(map, new NodeId(link.To, link.ToRegion)));
            var high = System.Math.Max(SandboxGeometry.FloorOf(map, new NodeId(link.From, link.FromRegion)),
                SandboxGeometry.FloorOf(map, new NodeId(link.To, link.ToRegion)));

            var foot = link.From.Layer <= link.To.Layer ? link.From : link.To;
            solid.Cylinder(SandboxScale.World.Center(foot.Hex), 0.16, low, high + 0.4, SandboxPalette.LinkFill, segments: 8);
        }
    }

    // ---- readouts on the ground ------------------------------------------------------

    /// <summary>The top of a node's hex as a tint, lifted clear of the ground.</summary>
    private static void Tint(MeshBuilder overlay, BattleMap map, NodeId node, Color color)
    {
        var regions = map.RegionsOf(node.Tile);
        var region = regions.FirstOrDefault(r => r.Index == node.Region) ?? regions[0];
        overlay.Flat(SandboxGeometry.RegionOutline(node.Tile, region), SandboxGeometry.FloorOf(map, node) + Lift, color);
    }

    /// <summary>The outline of a node's region as a ribbon, lifted clear of the ground.</summary>
    private static void Outline(MeshBuilder overlay, BattleMap map, NodeId node, Color color, float width, double inset = 0.06)
    {
        var regions = map.RegionsOf(node.Tile);
        var region = regions.FirstOrDefault(r => r.Index == node.Region) ?? regions[0];
        var height = SandboxGeometry.FloorOf(map, node) + Lift * 1.5;

        var corners = SandboxGeometry.RegionOutline(node.Tile, region, inset)
            .Select(c => SandboxScale.ToScene(c, height)).ToList();
        corners.Add(corners[0]);
        overlay.Ribbon(corners, width, color);
    }

    /// <remarks>
    /// Dead ground the active unit has no eyes on. Close up it goes dark; from a distance it is
    /// left alone, because on a map this size one soldier cannot see most of it, so the wash
    /// covers nine tiles in ten and takes the shape of the place with it — and the shape of the
    /// place is the one thing an overview is being asked for.
    /// </remarks>
    private static void BuildUnseen(SandboxFrame frame, MeshBuilder overlay)
    {
        if (!frame.TileDetail || frame.Battle.Active is null) return;

        foreach (var (node, seen) in frame.View)
            if (!seen.CanSee) Tint(overlay, frame.Battle.Map, node, SandboxPalette.Unseen);
    }

    /// <remarks>
    /// Where the cover is, on the tiles the active soldier can see, in the colour of the grade.
    /// Kept when zoomed out, because that is the one thing worth reading from a map you cannot
    /// read a number off.
    /// </remarks>
    private static void BuildCoverOutlines(SandboxFrame frame, MeshBuilder overlay)
    {
        foreach (var (node, seen) in frame.View)
            if (seen.CanSee && seen.Cover != CoverGrade.None)
                Outline(overlay, frame.Battle.Map, node, SandboxPalette.CoverHue(seen.Cover), 0.12f);
    }

    /// <summary>
    /// How much of its attention a soldier has on each piece of ground round it, at the reach
    /// the rules actually judge by.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Entry 006 in <c>docs/decisions.md</c>, closed on the flat view and kept closed here. Two
    /// things the model says: <b>attention is graded, not a yes or a no</b> — the front arc at
    /// full rate, the peripheral band at <c>PeripheralAcuity</c>, everything behind at
    /// <c>RearAcuity</c>, and the gap between the last two is the entire reason flanking works —
    /// and <b>range tells against you gently and then sharply</b>, by <c>1 - (d/range)²</c>. The
    /// tint on each hex is the product of the two, which are the two factors the detection
    /// model multiplies that belong to the observer; exposure and stance belong to a particular
    /// target, and this is a field and not a shot.
    /// </para>
    /// <para>
    /// Asked of the rules per hex — <c>AttentionOn</c> is the query, and the same one the cursor
    /// line quotes — rather than drawn as sectors and trusted to agree. The tiles tinted are the
    /// storey being looked at, so a sentry in the tower tints the ground it watches and not the
    /// air at its own height, which is what the flat view drew and was right to.
    /// </para>
    /// </remarks>
    private static void BuildAttention(SandboxFrame frame, MeshBuilder overlay)
    {
        var battle = frame.Battle;
        var model = battle.Awareness.Model;
        var range = model.SightRangeMetres;
        var layout = SandboxScale.World;

        var ground = battle.Map.Tiles
            .Where(t => t.Address.Layer == frame.Layer)
            .Select(t => (Node: new NodeId(t.Address, 0), Plane: layout.Center(t.Address.Hex)))
            .ToList();

        foreach (var unit in battle.InPlay)
        {
            if (!frame.Sees(unit)) continue;

            var peak = unit == battle.Active ? AttentionPeakActive
                : unit.Side == Side.Hostile ? AttentionPeakHostile
                : AttentionPeakIdle;

            // The field's own hue and not the body's — see SandboxPalette.AttentionHue. This
            // tint covers most of the map, so it is the one readout a soldier cannot be made to
            // stand out against by making the soldier brighter.
            var hue = SandboxPalette.AttentionHue(unit.Side);
            var pose = UnitPose.Of(unit);
            var from = SandboxGeometry.NodePlane(battle.Map, unit.Position);

            foreach (var (node, plane) in ground)
            {
                if (node == unit.Position) continue;

                var distance = CoreVec2.Distance(from, plane);
                if (distance >= range) continue;

                var closeness = distance / range;
                var weight = peak * (1 - closeness * closeness) * battle.Awareness.AttentionOn(pose, node);
                if (weight < 0.006) continue;

                Tint(overlay, battle.Map, node, new Color(hue, (float)weight));
            }
        }
    }

    /// <summary>
    /// The arc a unit is holding, out as far as it could actually shoot along it.
    /// </summary>
    /// <remarks>
    /// An arc being held is a different thing from an arc being attended to: anything that moves
    /// inside this one gets shot at. So its reach is the weapon's and not the eye's — a shot is
    /// refused past <c>WeaponProfile.MaxRange</c> — and the inner band is the optimal range, the
    /// same figure the cursor line names. Whether a tile is inside the arc is
    /// <c>AngleOffDegrees</c>'s answer, which is what the reaction model asks.
    /// <para>
    /// Only the arcs of soldiers the picture shows as bodies, so in the game a hostile's held
    /// arc is not drawn even when the hostile is: what it is covering is its intent, and the
    /// attention field already says where it is looking. Omniscient, every arc is drawn, because
    /// a capture checking a sentry answered a move needs to see what it was holding.
    /// </para>
    /// </remarks>
    private static void BuildHeldArcs(SandboxFrame frame, MeshBuilder overlay)
    {
        var battle = frame.Battle;
        var layout = SandboxScale.World;

        var ground = battle.Map.Tiles
            .Where(t => t.Address.Layer == frame.Layer)
            .Select(t => (Node: new NodeId(t.Address, 0), Plane: layout.Center(t.Address.Hex)))
            .ToList();

        foreach (var unit in battle.InPlay)
        {
            if (unit.Held is not { } order) continue;
            if (unit.Overwatch is not null && unit.Reserve <= 0) continue;
            if (unit.Side == Side.Hostile && !frame.Omniscient) continue;

            var tint = unit.Ambush is not null ? SandboxPalette.AmbushHue : SandboxPalette.OverwatchHue;
            var half = order.Arc.Degrees / 2;
            var from = SandboxGeometry.NodePlane(battle.Map, unit.Position);

            foreach (var (node, plane) in ground)
            {
                if (node == unit.Position) continue;

                var distance = CoreVec2.Distance(from, plane);
                if (distance > unit.Weapon.MaxRange) continue;
                if (battle.AngleOffDegrees(unit.Position, order.Centre, node) > half) continue;

                Tint(overlay, battle.Map, node, new Color(tint, distance <= unit.Weapon.OptimalRange ? 0.26f : 0.13f));
            }
        }
    }

    /// <summary>
    /// The route somebody has committed to and not yet walked.
    /// </summary>
    /// <remarks>
    /// Only ever on screen while a reaction window is open, and it is the one thing that makes
    /// that state readable: the mover has paid for this walk and is still standing at the start
    /// of it — entry 040 — so without the route drawn a player sees a soldier who has apparently
    /// done nothing and is being shot at for it. The tick numbers are labels, drawn with the
    /// rest, and they are the clock the options in the readout are quoted against.
    /// </remarks>
    private static void BuildCommitted(SandboxFrame frame, MeshBuilder overlay)
    {
        if (frame.Open is not { } window || window.Move.Steps.Count < 2) return;

        var map = frame.Battle.Map;
        var points = window.Move.Steps
            .Select(s => SandboxGeometry.NodeScene(map, s.Node) + Vector3.Up * (Lift * 2))
            .ToList();

        overlay.Ribbon(points, 0.28f, SandboxPalette.CommittedColor);
    }

    /// <summary>
    /// Where our side may walk off the field, if the mission gives us somewhere.
    /// </summary>
    /// <remarks>
    /// A named place rather than a map edge, which is entry 041's choice, and it has to be drawn
    /// or it does not exist. Ours only; where the other side is going is theirs to know.
    /// </remarks>
    private static void BuildExit(SandboxFrame frame, MeshBuilder overlay)
    {
        if (frame.Battle.ObjectiveOf(Side.Player) is not Withdrawal way) return;

        foreach (var node in way.Exit.Where(n => n.Tile.Layer <= frame.Layer))
        {
            Tint(overlay, frame.Battle.Map, node, SandboxPalette.ExitFill);
            Outline(overlay, frame.Battle.Map, node, SandboxPalette.CoverLightHue, 0.10f);
        }
    }

    /// <summary>
    /// Where each enemy believes one of ours to be.
    /// </summary>
    /// <remarks>
    /// The marker is what they last saw, so it goes stale the moment that soldier moves, and the
    /// gap between marker and truth is the thing the approach is played in. Section 07 of the
    /// design doc names this as the one thing of the enemy's a player sees at all, so it is
    /// drawn in both modes — it is coarse, a place and not a number, and it is the payoff.
    /// </remarks>
    private static void BuildBeliefs(SandboxFrame frame, MeshBuilder overlay)
    {
        var battle = frame.Battle;

        foreach (var hostile in battle.InPlay.Where(u => u.Side == Side.Hostile))
        foreach (var mine in battle.InPlay.Where(u => u.Side == Side.Player))
        {
            var readout = battle.Awareness.ReadoutFor(hostile.Id, mine.Id);
            if (readout.State < AwarenessState.Searching) continue;
            if (readout.LastKnownPosition is not { } believed) continue;
            if (believed == mine.Position) continue;      // they are simply right

            Outline(overlay, battle.Map, believed, SandboxPalette.GhostHue, 0.14f, inset: 0.3);
        }
    }

    // ---- soldiers ----------------------------------------------------------------------

    /// <summary>
    /// Every soldier the picture is allowed to show, as a body at its stance height with its
    /// facing marked.
    /// </summary>
    /// <remarks>
    /// The heights are <c>StanceProfile</c>'s — 1.80, 1.25 and 0.45 metres — because those are
    /// the heights the sight trace uses, and a body drawn any other size would be a picture that
    /// disagreed with the rules about whether a wall hides it. A standing or crouching soldier is
    /// a cylinder; a prone one is a slab lying along its facing, because that is the one stance
    /// where the footprint is not round. The facing is a short bar at eye height sticking out of
    /// the front — the one mark that reads from every one of the six camera bearings — and the
    /// active soldier gets a ring on the ground.
    /// </remarks>
    private void BuildBodies(SandboxFrame frame, MeshBuilder solid)
    {
        var battle = frame.Battle;
        var walk = Walk;

        foreach (var unit in battle.InPlay)
        {
            if (!frame.Sees(unit)) continue;

            var walking = walk is not null && walk.Mover == unit.Id;

            var hue = SandboxPalette.SideHue(unit.Side);
            var at = walking ? walk!.At : SandboxGeometry.NodePlane(battle.Map, unit.Position);
            var floor = walking ? walk!.Floor : SandboxGeometry.FloorOf(battle.Map, unit.Position);

            // A walking soldier is drawn standing whatever it ends the move in: the stance it
            // takes at the far end is a thing it does on arrival, and a prone slab sliding along
            // the ground reads as a body being dragged.
            var profile = StanceProfile.For(walking ? Stance.Standing : unit.Stance);
            var bearing = walking ? walk!.Bearing : unit.Facing.BearingRadians();

            var radius = Body(solid, at, floor, profile, bearing, hue);

            // Every soldier stands on a ring of its own side's colour, and that is the whole of
            // the answer to the play-through's fifth finding: a body is a small shape a long way
            // off, and at --fit distance it is a few pixels of a hue the ground is entitled to
            // use. A ring is wider than the body, it is the same width whatever the stance, and
            // it sits on the floor rather than above it, so it survives being seen from a
            // distance and from behind a wall. The active one is brighter and wider still,
            // because whose go it is has to beat everything else on the map.
            Rings(solid, at, radius, floor, hue, unit == battle.Active, frame.TileDetail);

            // The facing bar, at the eye, out the front.
            var nose = at + new CoreVec2(System.Math.Cos(bearing), System.Math.Sin(bearing)) * (radius + 0.12);
            solid.Box(nose, bearing, 0.36, 0.12, floor + profile.EyeHeight - 0.06, floor + profile.EyeHeight + 0.06,
                SandboxPalette.TextBright, SandboxPalette.TextBright);
        }
    }

    /// <summary>The dark contact ring under a body and the side-coloured one outside it.</summary>
    /// <remarks>
    /// <para>
    /// Two rings rather than one, and the dark one matters more. A blockout has no ambient
    /// occlusion, so a cylinder standing on a floor of a similar value has no edge where the two
    /// meet and appears to hover; a dark band at the foot supplies the shadow the renderer does
    /// not, and it works on every ground colour because it is darker than all of them. The
    /// coloured ring outside it is what carries at distance.
    /// </para>
    /// <para>
    /// <b>Both grow when the camera is far enough back to have switched tile detail off.</b> The
    /// brief asked for the check at <c>--fit</c> as well as close in, and it is a different
    /// problem there: at 80 metres a soldier is a handful of pixels and a ring drawn to look
    /// right at 36 is a hairline. Widening it is the same trade the tile labels already make at
    /// the same threshold — see <see cref="SandboxCamera.LegibleAt"/> — so it is one distance
    /// switch in the frame and not a second one, and it is a step rather than a taper because a
    /// ring that grew continuously would make every zoom a redraw of the bodies.
    /// </para>
    /// </remarks>
    private static void Rings(MeshBuilder solid, CoreVec2 at, double radius, double floor, Color hue, bool active, bool near)
    {
        var scale = near ? 1f : 2.2f;

        solid.Ribbon(Ring(at, radius + 0.10 * scale, floor + Lift, 20), 0.22f * scale, SandboxPalette.UnitShadow);
        solid.Ribbon(Ring(at, radius + 0.34 * scale, floor + Lift * 1.5, 24), (active ? 0.16f : 0.10f) * scale,
            active ? SandboxPalette.TextBright : hue);
    }

    /// <summary>The body itself, by stance. Returns the radius of its footprint so the marks can sit outside it.</summary>
    private static double Body(MeshBuilder solid, CoreVec2 at, double floor, StanceProfile profile, double bearing, Color hue)
    {
        switch (profile.Stance)
        {
            case Stance.Prone:
                // Lying along the facing, head forward: the slab is offset so the eye end is
                // where the facing bar goes.
                var ahead = new CoreVec2(System.Math.Cos(bearing), System.Math.Sin(bearing)) * 0.35;
                solid.Box(at + ahead, bearing, 1.6, 0.5, floor, floor + profile.BodyHeight, hue);
                return 1.15;

            case Stance.Crouching:
                solid.Cylinder(at, 0.34, floor, floor + profile.BodyHeight, hue);
                return 0.34;

            default:
                solid.Cylinder(at, 0.28, floor, floor + profile.BodyHeight, hue);
                return 0.28;
        }
    }

    /// <summary>
    /// A hostile our side knows about and cannot see: a see-through body at the marker.
    /// </summary>
    /// <remarks>
    /// Standing, whatever it was doing when last seen, because a marker is a place and not a
    /// posture — <c>Tactician.Known</c> builds the believed pose standing for the same reason.
    /// Its credence is a label; it is the figure the scorer discounts the threat by, and entry
    /// 042 says our own side's certainty is shown exactly.
    /// </remarks>
    private static void BuildGhosts(SandboxFrame frame, MeshBuilder overlay)
    {
        foreach (var (hostile, threat) in Ghosts(frame))
        {
            var at = SandboxGeometry.NodePlane(frame.Battle.Map, threat.Where.Position);
            var floor = SandboxGeometry.FloorOf(frame.Battle.Map, threat.Where.Position);

            overlay.Cylinder(at, 0.28, floor, floor + StanceProfile.Standing.BodyHeight,
                new Color(SandboxPalette.HostileHue, 0.22f + 0.28f * (float)threat.Credence));
        }
    }

    /// <summary>The hostiles drawn as ghosts: known about, not in view, and not otherwise drawn.</summary>
    private static IEnumerable<(Unit Hostile, Threat Threat)> Ghosts(SandboxFrame frame)
    {
        foreach (var hostile in frame.Battle.InPlay.Where(u => u.Side == Side.Hostile))
        {
            if (frame.Sees(hostile)) continue;
            if (!frame.Knowledge.TryGetValue(hostile.Id, out var threat)) continue;
            yield return (hostile, threat);
        }
    }

    /// <summary>A loop of scene points round a plane point, closed.</summary>
    private static List<Vector3> Ring(CoreVec2 centre, double radius, double height, int segments)
    {
        var points = new List<Vector3>(segments + 1);
        for (var i = 0; i <= segments; i++)
        {
            var angle = System.Math.Tau * i / segments;
            points.Add(SandboxScale.ToScene(centre + new CoreVec2(System.Math.Cos(angle), System.Math.Sin(angle)) * radius, height));
        }
        return points;
    }

    // ---- the cursor --------------------------------------------------------------------

    private static void BuildHover(SandboxFrame frame, MeshBuilder cursor)
    {
        if (frame.Hover is not { } node) return;
        Outline(cursor, frame.Battle.Map, node, SandboxPalette.HoverEdge, 0.08f, inset: 0.02);
    }

    private static void BuildPath(SandboxFrame frame, MeshBuilder cursor)
    {
        if (frame.Battle.Active is not { } active) return;
        if (frame.Hover is not { } goal || !frame.Reach.TryGetPath(goal, out var path) || path.Count == 0) return;

        var map = frame.Battle.Map;
        var points = new List<Vector3> { SandboxGeometry.NodeScene(map, active.Position) + Vector3.Up * (Lift * 2) };
        points.AddRange(path.Select(link => SandboxGeometry.NodeScene(map, link.To) + Vector3.Up * (Lift * 2)));

        cursor.Ribbon(points, 0.22f, SandboxPalette.PathColor);
    }

    // ---- labels ----------------------------------------------------------------------

    /// <summary>
    /// Everything written on the map, painted over the picture at a fixed point size.
    /// </summary>
    /// <remarks>
    /// Called by the label canvas on every redraw, and it redraws on every camera move because
    /// each label has to be re-projected. The frame is the one the meshes were built from, so a
    /// label cannot say something the shape under it does not.
    /// </remarks>
    public void DrawLabels(CanvasItem canvas)
    {
        if (_frame is not { } frame) return;

        DrawCostLabels(canvas, frame);
        DrawLinkLabels(canvas, frame);
        DrawPlaceLabels(canvas, frame);
        DrawRouteLabels(canvas, frame);
        DrawBeliefLabels(canvas, frame);
        DrawGhostLabels(canvas, frame);
        DrawUnitLabels(canvas, frame);
    }

    private void DrawCostLabels(CanvasItem canvas, SandboxFrame frame)
    {
        if (!frame.TileDetail) return;

        var map = frame.Battle.Map;
        foreach (var (node, reached) in frame.Reach.Reached)
        {
            if (node.Tile.Layer != frame.Layer || reached.Cost <= 0) continue;
            if (frame.Battle.UnitAt(node) is not null) continue;

            Label(canvas, SandboxGeometry.NodeScene(map, node), reached.Cost.ToString(), 14, SandboxPalette.TextDim);
        }
    }

    private void DrawLinkLabels(CanvasItem canvas, SandboxFrame frame)
    {
        if (!frame.TileDetail) return;

        var map = frame.Battle.Map;
        foreach (var link in map.Links)
        {
            if (link.From.Layer != frame.Layer && link.To.Layer != frame.Layer) continue;

            var foot = link.From.Layer <= link.To.Layer ? link.From : link.To;
            var top = System.Math.Max(SandboxGeometry.FloorOf(map, new NodeId(link.From, link.FromRegion)),
                SandboxGeometry.FloorOf(map, new NodeId(link.To, link.ToRegion)));

            Label(canvas, SandboxScale.ToScene(SandboxScale.World.Center(foot.Hex), top + 0.6),
                link.Kind.ToString().ToUpperInvariant(), 11, SandboxPalette.LinkText);
        }
    }

    /// <remarks>
    /// One label per place, at the middle of the tiles it covers and a little above the ground,
    /// only when a tile is big enough to carry writing at all. A mission talks in places and the
    /// rules talk in nodes; a place a briefing names and a player cannot find is a name and not
    /// a place. Entry 052.
    /// </remarks>
    private void DrawPlaceLabels(CanvasItem canvas, SandboxFrame frame)
    {
        if (!frame.TileDetail || frame.Mission is not { } mission) return;

        var map = frame.Battle.Map;
        foreach (var (name, tiles) in mission.Places)
        {
            var here = tiles.Where(t => t.Layer == frame.Layer).ToList();
            if (here.Count == 0) continue;

            var middle = here.Select(t => SandboxScale.World.Center(t.Hex)).Aggregate(CoreVec2.Zero, (a, b) => a + b) / here.Count;
            var height = here.Max(t => map.GetTile(t)?.FloorHeight ?? 0) + 2.5;

            Label(canvas, SandboxScale.ToScene(middle, height), name.ToUpperInvariant(), 12, SandboxPalette.LinkText, width: 200f);
        }
    }

    private void DrawRouteLabels(CanvasItem canvas, SandboxFrame frame)
    {
        if (!frame.TileDetail) return;

        var map = frame.Battle.Map;

        if (frame.Open is { } window)
            foreach (var step in window.Move.Steps.Skip(1))
                Label(canvas, SandboxGeometry.NodeScene(map, step.Node) + Vector3.Up * 0.5f, $"t{step.Tick}", 11, SandboxPalette.CommittedColor);

        if (frame.Hover is { } goal && frame.Reach.TryGetPath(goal, out var path))
            foreach (var link in path.Where(l => l.Kind != TraversalKind.Walk))
                Label(canvas, SandboxGeometry.NodeScene(map, link.To) + Vector3.Up * 0.5f, link.Kind.ToString().ToUpperInvariant(), 11, SandboxPalette.PathColor);
    }

    private void DrawBeliefLabels(CanvasItem canvas, SandboxFrame frame)
    {
        var battle = frame.Battle;

        foreach (var hostile in battle.InPlay.Where(u => u.Side == Side.Hostile))
        foreach (var mine in battle.InPlay.Where(u => u.Side == Side.Player))
        {
            var readout = battle.Awareness.ReadoutFor(hostile.Id, mine.Id);
            if (readout.State < AwarenessState.Searching) continue;
            if (readout.LastKnownPosition is not { } believed) continue;
            if (believed == mine.Position) continue;

            Label(canvas, SandboxGeometry.NodeScene(battle.Map, believed) + Vector3.Up * 0.3f, "?", 16, SandboxPalette.GhostHue);
        }
    }

    private void DrawGhostLabels(CanvasItem canvas, SandboxFrame frame)
    {
        foreach (var (hostile, threat) in Ghosts(frame))
        {
            var top = SandboxGeometry.NodeScene(frame.Battle.Map, threat.Where.Position) + Vector3.Up * (float)(StanceProfile.Standing.BodyHeight + 0.4);
            Label(canvas, top, $"{hostile.Name}? x{threat.Credence:P0}", 11, SandboxPalette.GhostHue, width: 132f);
        }
    }

    /// <remarks>
    /// Current over maximum, because the scorer's removal bonus is priced against the maximum:
    /// a kill shot on a soldier with seven points left is worth a whole soldier of twenty, and a
    /// label that only ever said seven left that arithmetic unreadable. Under a hostile's name,
    /// what the other side has worked out — coarse on purpose, a rung and never a number. A
    /// soldier on another storey says so, because the ground it stands on is ghosted.
    /// </remarks>
    private void DrawUnitLabels(CanvasItem canvas, SandboxFrame frame)
    {
        var battle = frame.Battle;

        foreach (var unit in battle.InPlay)
        {
            if (!frame.Sees(unit)) continue;

            var hue = SandboxPalette.SideHue(unit.Side);

            // A label goes over the body and not over the position, and during a walk those are
            // different places: the rules have the mover at the far end already and the picture
            // has not caught up. A name hanging over the destination while the soldier is still
            // half way there is the map disagreeing with itself, which is the one thing the
            // frame exists to prevent — so the walk is read here as well as in BuildBodies.
            var walking = Walk is not null && Walk.Mover == unit.Id;

            var crown = (walking
                            ? SandboxScale.ToScene(Walk!.At, Walk.Floor)
                            : SandboxGeometry.NodeScene(battle.Map, unit.Position))
                        + Vector3.Up * (float)(StanceProfile.For(walking ? Stance.Standing : unit.Stance).BodyHeight + 0.35);

            if (_camera.Project(crown) is not { } at) continue;

            var storey = unit.Position.Layer == frame.Layer ? ""
                : unit.Position.Layer > frame.Layer ? " (above)" : " (below)";

            Text(canvas, at + new Vector2(0, -6), $"{unit.Name} {unit.Vitality}/{unit.Stats.Vitality}{storey}", 11, hue, 160f);

            if (unit.Side == Side.Hostile)
            {
                var readout = WorstReadout(frame, unit);
                Text(canvas, at + new Vector2(0, 8), readout.State.ToString().ToUpperInvariant(), 10, SandboxPalette.AlarmHue(readout.State), 88f);
            }
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

    /// <summary>A label at a scene point, if that point is in front of the camera.</summary>
    private void Label(CanvasItem canvas, Vector3 scene, string text, int size, Color color, float width = 88f)
    {
        if (_camera.Project(scene) is { } at) Text(canvas, at, text, size, color, width);
    }

    /// <param name="width">
    /// How wide a box the text is centred in. Godot clips at the box edge rather than spilling
    /// over it, so anything longer than a tile-cost label asks for more.
    /// </param>
    private void Text(CanvasItem canvas, Vector2 at, string text, int size, Color color, float width)
    {
        canvas.DrawString(_font, at + new Vector2(-width / 2f, size * 0.36f), text,
            HorizontalAlignment.Center, width, size, color);
    }
}
