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
/// <see cref="SandboxFrame.Knowledge"/> says where a marker stands and how much it is worth. This
/// class asks and draws. What it adds is what the enemy's file looks like — brief two: his rung as a
/// badge on his body, his belief about us as that badge at a place, and ours about him as a mark at a
/// place that is never a body — and that a hostile nobody has heard of is not drawn at all, which is the
/// whole of what makes this a game rather than a tool.
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
        BuildReachBands(frame, overlay);
        BuildCommitted(frame, overlay);
        BuildBeliefs(frame, overlay);
        BuildMarkers(frame, overlay);

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
        BuildAim(frame, cursor);
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
    /// <para>
    /// Reach used to be a fill here and is an edge now — see <see cref="BuildReachBands"/>. A fill
    /// is a graded field's way of drawing and cannot carry a cliff, and every photographed game in
    /// the reference set draws its move range as an outline.
    /// </para>
    /// </remarks>
    private static Color FillFor(SandboxFrame frame, Tile tile, HexRegion region, NodeId id)
    {
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
        if (!frame.TileDetail || frame.Battle.Active is null || frame.Withheld) return;

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
        // The view from whoever is up; a hostile the picture may not describe has none of it drawn. Entry 090.
        if (frame.Withheld) return;

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
    /// <b>The arc of every soldier the picture shows as a body, a hostile's included — since brief two,
    /// and a departure from nothing.</b> It used to stop at our side, on the argument that what a hostile
    /// covers is his intent and the attention field already says where he looks. <i>Amending Two</i>
    /// corrects the reason brief two gave for reversing that and keeps the reversal: no game in ten draws
    /// a hostile's reaction zone, and the stealth shelf's cones are vision, not a held shot, so there is
    /// no borrowing to cite. The argument is this game's own. A held arc here is not a posture he might
    /// be in; it is a declared order, banked and priced, that shoots whatever moves inside it before the
    /// mover can act. A body is drawn only while one of ours has eyes on him, and anybody standing where
    /// they can see him could see which way his weapon is laid. A player who walks into an arc held by a
    /// soldier they could see holding it will say, rightly, that the picture lied — and there is no
    /// deciding against it when it is not drawn, which is the only reason to draw anything. A hostile
    /// the picture does not show holds no drawn arc, so it says nothing about anybody unfound.
    /// </para>
    /// <para>
    /// <b>An arc with nothing banked behind it is not drawn — except on the soldier whose go it is.</b>
    /// A watchman whose reserve is spent is holding an arc it cannot shoot down, and a wedge on the
    /// ground would be a threat that is not there. But a soldier's reserve is set to nought when its
    /// own go comes round and banked when the go ends, so on the soldier declaring the arc that test
    /// read nought always, and <c>V</c> charged for an arc the player then never saw — entry 094, item
    /// 6, confirmed by capture on the compound before this was changed. So the soldier up is asked
    /// what it <i>will</i> bank, of <c>Battle</c>: <c>Reactions.Banked</c> of its points now, against
    /// its own price for its quickest shot. Enough, and the arc is drawn as held; not enough, and it is
    /// drawn faint — declared, and holding nothing yet, which is true and is what the player is
    /// deciding against.
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
            if (!frame.Sees(unit)) continue;

            // The reserve a soldier holds is the one it banked; the one up has not banked yet, so it
            // is asked what it would. See the remarks.
            var declaring = unit == battle.Active;
            var backed = declaring
                ? battle.Reactions.Banked(unit.ActionPoints) >= unit.Stats.Costs.Fire(unit.Weapon.QuickestMode.ApCost)
                : unit.Reserve > 0;
            if (unit.Overwatch is not null && !backed && !declaring) continue;

            var strength = unit.Overwatch is not null && !backed ? 0.45f : 1f;
            var tint = unit.Ambush is not null ? SandboxPalette.AmbushHue : SandboxPalette.OverwatchHue;
            var half = order.Arc.Degrees / 2;
            var from = SandboxGeometry.NodePlane(battle.Map, unit.Position);

            foreach (var (node, plane) in ground)
            {
                if (node == unit.Position) continue;

                var distance = CoreVec2.Distance(from, plane);
                if (distance > unit.Weapon.MaxRange) continue;
                if (battle.AngleOffDegrees(unit.Position, order.Centre, node) > half) continue;

                Tint(overlay, battle.Map, node, new Color(tint, (distance <= unit.Weapon.OptimalRange ? 0.26f : 0.13f) * strength));
            }
        }
    }

    /// <summary>
    /// Where the active soldier can get to, cut into bands at the reserve's own rungs and drawn as
    /// edges along the tiles: how far it may go and still bank the dearest shot, the cheapest shot,
    /// anything at all, and how far it may go.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Brief one's reserve cliffs, on the ground, where the decision is being taken.</b> The
    /// amendment's finding: four of the six grid games in the reference set band the move range, and
    /// three of them put the band exactly at <i>can I still act when I arrive</i>. The soldier's own
    /// points say what it holds now; these say what it will hold <i>there</i>. The rungs are
    /// <see cref="SandboxFrame.Ladder"/>'s, so a band edge falls where
    /// <c>ReactionModel.Banked</c> steps and nowhere the fraction merely suggests.
    /// </para>
    /// <para>
    /// <b>Edges, not fills.</b> <i>Settling One</i>: Future War Tactics draws nested outlines stepped
    /// along its tile edges and no tint, and Invisible, Inc.'s reach is an outline too. An edge laid
    /// over the attention tint does not fight it, where a second fill would have.
    /// </para>
    /// <para>
    /// <b>Three rungs on the ground and every rung on the soldier.</b> A rifle has three fire modes,
    /// and five nested lines — reach, floor and a band per mode — stop reading as bands. The brief
    /// names the floor and <i>a shot and then the better one</i>, so the ground carries the cheapest
    /// mode and the dearest one a move can keep, and the points bar on the soldier carries every rung.
    /// A band that would enclose
    /// the same tiles as the one outside it is not drawn, and neither is one that encloses only the
    /// tile the soldier is standing on: both would be a line saying nothing a line beside it does not.
    /// </para>
    /// <para>
    /// <b>A hostile up and withheld from the picture has nothing drawn — not its reach, not its bands.</b>
    /// Entry 090 found the map drawing whoever was up whichever side, so the AI's hostile stopped at a
    /// window of ours had its reach edged round a house nobody of ours could see into; brief two settled it
    /// with <see cref="SandboxFrame.Withheld"/>, the gate the readouts already used. The same gate takes
    /// its sight — the dead-ground wash and the cover outlines — its route preview and its cost labels.
    /// </para>
    /// </remarks>
    private static void BuildReachBands(SandboxFrame frame, MeshBuilder overlay)
    {
        if (frame.Battle.Active is not { } active || frame.Withheld) return;

        var map = frame.Battle.Map;

        // The cheapest a stoppable place on each tile is reached for. A tile split by a barricade
        // is in a band if any side of it is, which is what an edge along the tile can say.
        var costs = new Dictionary<TileAddress, int> { [active.Position.Tile] = 0 };
        foreach (var (node, reached) in frame.Reach.Reached)
        {
            if (node.Tile.Layer > frame.Layer || !frame.Battle.CanStopAt(active, node)) continue;
            if (!costs.TryGetValue(node.Tile, out var best) || reached.Cost < best) costs[node.Tile] = reached.Cost;
        }

        HashSet<TileAddress> Within(int spend) => costs.Where(pair => pair.Value <= spend).Select(pair => pair.Key).ToHashSet();

        var bands = new List<(HashSet<TileAddress> Inside, Color Hue, float Width, double Inset)>
        {
            (Within(int.MaxValue), SandboxPalette.ReachEdge, 0.08f, 0.03),
        };

        if (frame.Ladder is { } ladder)
        {
            if (ladder.Floor is { } floor)
                bands.Add((Within(active.ActionPoints - floor.Leftover), SandboxPalette.BandHue(SandboxPalette.Band.Floor), 0.09f, 0.10));
            if (ladder.Cheapest is { } cheap)
                bands.Add((Within(active.ActionPoints - cheap.Leftover), SandboxPalette.BandHue(SandboxPalette.Band.Cheapest), 0.11f, 0.17));

            // The better shot is the dearest one a move can still keep. A fresh rifleman keeps an
            // aimed shot only by not moving at all, and a band round the tile it stands on says
            // nothing; the rung below it is the one a player is actually choosing a move against.
            var better = ladder.Rungs
                .Where(rung => ladder.Better is { } first && rung.Price >= first.Price)
                .OrderByDescending(rung => rung.Price)
                .Select(rung => Within(active.ActionPoints - rung.Leftover))
                .FirstOrDefault(inside => inside.Count > 1);
            if (better is not null)
                bands.Add((better, SandboxPalette.BandHue(SandboxPalette.Band.Better), 0.13f, 0.24));
        }

        HashSet<TileAddress>? outside = null;
        foreach (var (inside, hue, width, inset) in bands)
        {
            if (inside.Count <= 1) break;                          // nothing left but where it stands
            if (outside is not null && inside.SetEquals(outside)) continue;
            outside = inside;

            foreach (var address in inside)
            {
                if (map.GetTile(address) is not { } tile) continue;
                var centre = SandboxScale.World.Center(address.Hex);
                var height = tile.FloorHeight + Lift * 2;

                foreach (var side in HexDirectionExtensions.All)
                {
                    if (inside.Contains(new TileAddress(address.Hex.Neighbor(side), address.Layer))) continue;

                    var (a, b) = side.Corners();
                    var from = SandboxScale.World.Corner(address.Hex, a);
                    var to = SandboxScale.World.Corner(address.Hex, b);
                    overlay.Ribbon(
                        [
                            SandboxScale.ToScene(from + (centre - from) * inset, height),
                            SandboxScale.ToScene(to + (centre - to) * inset, height),
                        ],
                        width, hue);
                }
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
    /// Where the other side believes one of ours to be: a place, the rung they hold it at, and who of
    /// ours it is about.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The marker is what they last had, so it goes stale the moment that soldier moves, and the gap
    /// between marker and truth is the thing the approach is played in. Section 07 of the design doc
    /// names this as the one thing of the enemy's a player sees at all, so it is drawn in both modes —
    /// it is coarse, a place and not a number, and it is the payoff.
    /// </para>
    /// <para>
    /// <b>A glyph at a place, not a ghost of our soldier.</b> Brief two proposed a translucent copy of the
    /// soldier they are wrong about, with a line to the truth; entry 089 then found the one persisted
    /// marker in ten games is a glyph at a place — Invisible, Inc.'s second <c>?</c> at the point a guard
    /// walks toward, which is this object exactly. A copy of a body is what this brief exists to stop the
    /// map drawing for things that are not bodies. So it is his rung's badge, standing over the tile he
    /// believes in, with that tile outlined, and the line to the truth is kept for the soldier who is up —
    /// the one a player is deciding for — rather than drawn from every marker at once.
    /// </para>
    /// <para>
    /// <b>A place is drawn in the shape of a tile and a soldier in the shape of a ring.</b> Every body
    /// stands on round rings; the first captures drew both kinds of marker on round rings too, and a ring
    /// with a thin pole in it is a soldier with no body, from any distance. So a marker of either side's
    /// outlines the hex, and nothing round on the ground is ever a place.
    /// </para>
    /// <para>
    /// From <i>noticed something</i> up, where it was from <i>looking for you</i>: a man who heard a noise
    /// and is coming to see holds a place too, and where he is coming to is the most useful thing on the
    /// map about him. One mark per place, at the highest rung any of them holds it at.
    /// </para>
    /// </remarks>
    private static void BuildBeliefs(SandboxFrame frame, MeshBuilder overlay)
    {
        var battle = frame.Battle;

        foreach (var belief in Beliefs(frame))
        {
            var at = SandboxGeometry.NodePlane(battle.Map, belief.Place);
            var floor = SandboxGeometry.FloorOf(battle.Map, belief.Place);
            var hue = SandboxPalette.AlarmHue(belief.State);

            Outline(overlay, battle.Map, belief.Place, hue, 0.12f, inset: 0.3);
            overlay.Box(at, 0, 0.05, 0.05, floor, floor + BeliefHeight - 0.25, new Color(hue, 0.6f));

            if (battle.Active is not { Side: Side.Player } up || !belief.About.Contains(up)) continue;

            overlay.Ribbon(
                [
                    SandboxScale.ToScene(at, floor + Lift * 3),
                    SandboxGeometry.NodeScene(battle.Map, up.Position) + Vector3.Up * (Lift * 3),
                ],
                0.05f, new Color(hue, 0.55f));
        }
    }

    /// <summary>How high over the ground a belief's badge hangs, in metres: a little above a standing head, so it is not read as one.</summary>
    private const double BeliefHeight = 2.4;

    /// <summary>One place the other side believes some of ours to be, and the highest rung it is held at.</summary>
    private sealed record Belief(NodeId Place, AwarenessState State, List<Unit> About);

    /// <summary>Every place the other side holds one of ours at and is wrong about, grouped by place.</summary>
    private static List<Belief> Beliefs(SandboxFrame frame)
    {
        var battle = frame.Battle;
        var beliefs = new Dictionary<NodeId, Belief>();

        foreach (var hostile in battle.InPlay.Where(u => u.Side == Side.Hostile))
        foreach (var mine in battle.InPlay.Where(u => u.Side == Side.Player))
        {
            var readout = battle.Awareness.ReadoutFor(hostile.Id, mine.Id);
            if (readout.State < AwarenessState.Suspicious) continue;
            if (readout.LastKnownPosition is not { } believed) continue;
            if (believed == mine.Position) continue;      // they are simply right

            if (!beliefs.TryGetValue(believed, out var belief))
                beliefs[believed] = belief = new Belief(believed, readout.State, []);
            else if (readout.State > belief.State)
                beliefs[believed] = belief = belief with { State = readout.State };

            if (!belief.About.Contains(mine)) belief.About.Add(mine);
        }

        return [.. beliefs.Values];
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
    /// A hostile our side knows about and cannot see, as a mark at the place our file puts him: brackets
    /// on the tile for what we were told, a beacon for what we saw and lost.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>This was a see-through standing body at the marker, and on turn one it was sight.</b> The
    /// waystation's mission file tells the squad where four of the garrison stand, nobody has moved on turn
    /// one, so every report is exactly where its man is, and a body at the truth reads as a man seen — entry
    /// 094, item 5: <i>I can see all the enemies as soon as it loads, but not shoot at.</i> A mark that is
    /// not a body cannot be read as one, and entry 089 found that the one persisted marker in ten games is
    /// exactly that: Future War Tactics' beacon where a lost enemy was last seen, and Invisible, Inc.'s
    /// interest point, a glyph on a bracketed tile.
    /// </para>
    /// <para>
    /// <b>Told and lost are different claims and get different shapes.</b> A briefed contact is where a man
    /// was put and holds until the ground contradicts it (entry 091); a lost one is where he was and decays.
    /// So <i>told</i> is the bracketed tile — a place somebody pointed at — and <i>lost</i> is the beacon,
    /// whose height and strength are our side's credence, so that a contact going cold is seen going down
    /// between two turns without a word read. <see cref="SandboxFrame.Told"/> says which.
    /// </para>
    /// <para>
    /// <b>In our file's colour</b>, because it is our belief: the mark is in the colour of whose belief it
    /// is and the name over it in the colour of whom it is about, the rule <see cref="BuildBeliefs"/> keeps
    /// the other way round. Not our side's teal, which was tried first: a teal ring on the ground under a
    /// pole is what one of our soldiers standing there looks like from a distance, and the capture said
    /// so. <see cref="SandboxPalette.OurFile"/> is pale, which nothing of the enemy's uses. And lit rather
    /// than dim, since entry 097's unlit ground is coming and a dim mark on it would be buried.
    /// </para>
    /// </remarks>
    private static void BuildMarkers(SandboxFrame frame, MeshBuilder overlay)
    {
        var map = frame.Battle.Map;

        foreach (var (_, threat, told) in Markers(frame))
        {
            var place = threat.Where.Position;
            var at = SandboxGeometry.NodePlane(map, place);
            var floor = SandboxGeometry.FloorOf(map, place);

            if (told)
            {
                Brackets(overlay, map, place, SandboxPalette.OurFile);
                continue;
            }

            var credence = (float)System.Math.Clamp(threat.Credence, 0, 1);
            var hue = new Color(SandboxPalette.OurFile, 0.35f + 0.65f * credence);
            Outline(overlay, map, place, hue, 0.11f, inset: 0.2);
            overlay.Box(at, 0, 0.12, 0.12, floor, floor + 0.2 + (StanceProfile.Standing.BodyHeight + 0.2) * credence, hue);
        }
    }

    /// <summary>Six short ribbons, one at each corner of a tile, along both edges that meet there.</summary>
    private static void Brackets(MeshBuilder overlay, BattleMap map, NodeId node, Color color)
    {
        var hex = node.Tile.Hex;
        var height = SandboxGeometry.FloorOf(map, node) + Lift * 2;
        var inset = 0.12;
        var centre = SandboxScale.World.Center(hex);

        var corners = Enumerable.Range(0, 6)
            .Select(i => SandboxScale.World.Corner(hex, i))
            .Select(c => c + (centre - c) * inset)
            .ToList();

        for (var i = 0; i < 6; i++)
        {
            var corner = corners[i];
            var before = corners[(i + 5) % 6];
            var after = corners[(i + 1) % 6];

            overlay.Ribbon(
                [
                    SandboxScale.ToScene(corner + (before - corner) * 0.32, height),
                    SandboxScale.ToScene(corner, height),
                    SandboxScale.ToScene(corner + (after - corner) * 0.32, height),
                ],
                0.17f, color);
        }
    }

    /// <summary>The hostiles drawn as marks: known about, not in view, with whether our file on him is the briefing's.</summary>
    private static IEnumerable<(Unit Hostile, Threat Threat, bool Told)> Markers(SandboxFrame frame)
    {
        foreach (var hostile in frame.Battle.InPlay.Where(u => u.Side == Side.Hostile))
        {
            if (frame.Sees(hostile)) continue;
            if (!frame.Knowledge.TryGetValue(hostile.Id, out var threat)) continue;
            yield return (hostile, threat, frame.Told(hostile));
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

    /// <summary>The firing mode, drawn: a line from the shooter's eye to the target, and a ring round the target.</summary>
    /// <remarks>
    /// In the cursor mesh because it follows a gesture and not the rules — pointing the mode at
    /// somebody else changes nothing true, so it must not cost a sight sweep. The line runs eye to
    /// chest so that it reads as a shot rather than a route, and it is drawn whether or not the
    /// shot is possible: the shot line says why not, and a line that vanished when the answer was
    /// no would be the map hiding the one thing the player is looking at.
    /// </remarks>
    private static void BuildAim(SandboxFrame frame, MeshBuilder cursor)
    {
        if (frame.Aim is not { } quarry || frame.Battle.Active is not { } shooter) return;

        var map = frame.Battle.Map;
        var from = SandboxGeometry.NodePlane(map, shooter.Position);
        var to = SandboxGeometry.NodePlane(map, quarry.Position);
        var eye = SandboxGeometry.FloorOf(map, shooter.Position) + StanceProfile.For(shooter.Stance).EyeHeight;
        var floor = SandboxGeometry.FloorOf(map, quarry.Position);
        var chest = floor + StanceProfile.For(quarry.Stance).BodyHeight * 0.6;

        cursor.Ribbon([SandboxScale.ToScene(from, eye), SandboxScale.ToScene(to, chest)], 0.08f, SandboxPalette.AimColor);

        // Outside the side-coloured ring, so the two are never mistaken: that one says whose
        // soldier it is and this one says it is the one being aimed at.
        var radius = quarry.Stance == Stance.Prone ? 1.8 : 0.95;
        var scale = frame.TileDetail ? 1f : 2.2f;
        cursor.Ribbon(Ring(to, radius * scale, floor + Lift * 3, 32), 0.14f * scale, SandboxPalette.AimColor);
    }

    private static void BuildPath(SandboxFrame frame, MeshBuilder cursor)
    {
        if (frame.Battle.Active is not { } active || frame.Withheld) return;

        // While aiming a click on the ground drops the aim and moves nobody, so a route drawn out
        // to it would be promising a move the click will not make.
        if (frame.Aim is not null) return;
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
        DrawMarkerLabels(canvas, frame);
        DrawUnitLabels(canvas, frame);
        DrawBillLabels(canvas, frame);
    }

    private void DrawCostLabels(CanvasItem canvas, SandboxFrame frame)
    {
        if (!frame.TileDetail || frame.Withheld) return;

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

        if (frame.Aim is null && !frame.Withheld && frame.Hover is { } goal && frame.Reach.TryGetPath(goal, out var path))
            foreach (var link in path.Where(l => l.Kind != TraversalKind.Walk))
                Label(canvas, SandboxGeometry.NodeScene(map, link.To) + Vector3.Up * 0.5f, link.Kind.ToString().ToUpperInvariant(), 11, SandboxPalette.PathColor);
    }

    /// <remarks>
    /// <b>The mark is in the colour of whose belief it is, and the name under it in the colour of whom it
    /// is about.</b> His badge, in his rung's colour, over the name of ours he is wrong about in ours. Our
    /// markers on him are the same rule turned round — see <see cref="DrawMarkerLabels"/> — so a player who
    /// has learned one has learned both.
    /// </remarks>
    private void DrawBeliefLabels(CanvasItem canvas, SandboxFrame frame)
    {
        var map = frame.Battle.Map;

        foreach (var belief in Beliefs(frame))
        {
            if (_camera.Project(SandboxGeometry.NodeScene(map, belief.Place) + Vector3.Up * (float)BeliefHeight) is not { } at) continue;

            SandboxRung.Draw(canvas, _font, at, belief.State, 0, false);
            Text(canvas, at + new Vector2(0, SandboxRung.Radius + 11), string.Join(", ", belief.About.Select(u => u.Name)), 10,
                SandboxPalette.PlayerHue, 160f);
        }
    }

    /// <remarks>
    /// <para>
    /// What our file says of him, in his side's colour: <i>told</i> for a briefed contact nothing has
    /// checked, or how much of him our side still credits for a lost one — our own side's figure, which
    /// entry 042 says is shown exactly. The marker's own shape already says which of the two it is; the
    /// word is for the reader who has not learned the shapes.
    /// </para>
    /// <para>
    /// <b>A name only for a man we saw.</b> The ghost label printed every marker's name, and two kinds of
    /// marker have none to give. A sound says where and never who, which the account of their go already
    /// keeps (<see cref="BattleHud.Perceived"/>, <i>somebody unseen, marked at</i>); and the waystation's own
    /// mission file says the Commission does not know that the man outside the west gate is called Cobb.
    /// So a lost contact whose facing our side holds was seen, and is named; one without was heard, and is
    /// <i>heard</i>; and a briefed one is <i>told</i> and nameless. Brief two found it, reading the label
    /// beside a window line that said <i>somebody unseen</i> about the same man.
    /// </para>
    /// </remarks>
    private void DrawMarkerLabels(CanvasItem canvas, SandboxFrame frame)
    {
        foreach (var (hostile, threat, told) in Markers(frame))
        {
            var top = SandboxGeometry.NodeScene(frame.Battle.Map, threat.Where.Position) + Vector3.Up * (float)(StanceProfile.Standing.BodyHeight + 0.4);
            var said = told ? "told"
                : threat.FacingKnown ? $"{hostile.Name} · {threat.Credence:P0}"
                : $"heard · {threat.Credence:P0}";
            Label(canvas, top, said, 11, SandboxPalette.HostileHue, width: 132f);
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
            // frame exists to prevent — so Crown reads the walk as well as BuildBodies does.
            if (Crown(frame, unit) is not { } at) continue;

            var storey = unit.Position.Layer == frame.Layer ? ""
                : unit.Position.Layer > frame.Layer ? " (above)" : " (below)";

            var name = $"{unit.Name} {unit.Vitality}/{unit.Stats.Vitality}{storey}";
            Text(canvas, at + new Vector2(0, -6), name, 11, hue, 160f);

            // His rung on us, as a badge hung on his own label, where nothing of ours about him is ever
            // drawn. See SandboxRung for the glyphs and BadgeGap for where it sits.
            if (unit.Side == Side.Hostile)
            {
                var half = Mathf.Min(_font.GetStringSize(name, HorizontalAlignment.Left, -1, 11).X, 160f) / 2;
                SandboxRung.Draw(canvas, _font, at + new Vector2(-half - BadgeGap, -6), frame.Rung(unit).State,
                    frame.RungMoved.GetValueOrDefault(unit.Id), frame.LooksFirst(unit));
            }
        }
    }

    /// <summary>
    /// The staged shot's bill on the map: a mark under the target when the shot would tell anybody
    /// else, and a <c>!</c> over each of those the picture shows.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Brief four's amendment puts the warning on the thing under the cursor, because that is where
    /// the three stealth games in the reference set put theirs and where the one that did not — XCOM
    /// 2 — had a community draw it for them. For a shot the thing under the cursor is the target, so
    /// the mark goes at its feet; the <c>!</c> over each listener is the other half, and answers
    /// <i>which of them</i> without a player having to read the HUD line.
    /// </para>
    /// <para>
    /// <b>The glyphs are provisional.</b> Which marks read at a glance on a hovered target is what
    /// capture C8 in <c>docs/interface/captures.md</c> is for — the Gotcha Again mod's vocabulary —
    /// and it has not been taken. These are text in the label font because that is what the
    /// greybox can draw today. Nothing is marked for a listener the picture does not show, and
    /// nothing counts them: the mark under the target says <i>somebody else</i>, never how many.
    /// </para>
    /// </remarks>
    private void DrawBillLabels(CanvasItem canvas, SandboxFrame frame)
    {
        if (frame.StagedShot is not { CanFire: true } plan) return;

        var others = frame.Giveaway.Select(word => word.Learner).Where(u => u != plan.Target).ToList();
        if (others.Count == 0) return;

        // Offset in pixels from the point the name label hangs from, not in metres: the name and
        // rung are placed that way, and a mark placed in metres lands on top of them at any distance
        // a rifle shot is taken from. The target's mark goes under its rung; a listener's over its name.
        if (Crown(frame, plan.Target) is { } target)
            Text(canvas, target + new Vector2(0, 24), "((( ! )))", 14, SandboxPalette.OverwatchHue, 120f);

        foreach (var listener in others.Where(frame.Sees))
            if (Crown(frame, listener) is { } over)
                Text(canvas, over + new Vector2(0, -24), "!", 20, SandboxPalette.OverwatchHue, 40f);
    }

    /// <summary>Where a unit's labels hang from on screen, if it is in front of the camera.</summary>
    /// <remarks>
    /// Over the body rather than over the position, which during a walk are different places — see
    /// <see cref="DrawUnitLabels"/>. Public because the HUD hangs its readouts from the same point:
    /// brief one put the figures on the things they describe, and a figure hung from the position
    /// while the name hangs from the body would be the map disagreeing with itself again. The HUD is
    /// handed this as a function and learns nothing else about the walk.
    /// </remarks>
    public Vector2? Crown(SandboxFrame frame, Unit unit)
    {
        var walking = Walk is not null && Walk.Mover == unit.Id;
        var foot = walking
            ? SandboxScale.ToScene(Walk!.At, Walk.Floor)
            : SandboxGeometry.NodeScene(frame.Battle.Map, unit.Position);

        return _camera.Project(foot + Vector3.Up * (float)(StanceProfile.For(walking ? Stance.Standing : unit.Stance).BodyHeight + 0.35));
    }

    /// <summary>How far left of a hostile's name his rung badge is centred, in pixels from the name's edge.</summary>
    /// <remarks>
    /// <b>Beside the name, in the name's line.</b> The first place tried was under the name, where the
    /// rung's word had been, and in the capture the badge sat squarely over the body at any distance a
    /// rifle is fired from — which is entry 094's item 12 made worse by the fix for item 8. Over the name
    /// is the HUD's: the shot's headline and the bill's <c>!</c> stack upwards from there. Beside it is
    /// free, still unmistakably his, and the adornments go further out on the same side.
    /// </remarks>
    public const float BadgeGap = 13f;

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
