using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Geometry;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;

namespace Hexcom.Core.Vision;

/// <summary>
/// Answers who can see whom, and how exposed they are.
/// </summary>
/// <remarks>
/// One trace produces both answers, because they are the same question. The sight line is
/// projected onto the ground and intersected with the wall segments it crosses. For each
/// crossing, the top of the wall is projected back along the line onto the target as a
/// waterline: everything below it is hidden, everything above it can be seen and shot. Cover is
/// graded by how much of the silhouette falls below that line, and the target is invisible when
/// an opaque wall submerges all of it.
/// <para>
/// Rules that would otherwise be special cases fall straight out of that geometry. A standing
/// soldier is visible over a waist-high wall while the same soldier prone behind it is not. A
/// low wall far down the line hides nothing, because the waterline it projects is below the
/// target's feet by then. Point-blank attackers get to shoot down over the wall their target is
/// hugging. And height advantage cancels low cover by itself: from a roof the line comes in so
/// steeply that a one-metre wall stops protecting anything more than a pace behind it.
/// </para>
/// <para>
/// <b>Sight and cover are scale-free, by construction, and that is a property to keep.</b> The
/// waterline is built from <c>along</c> — the fraction of the way down the sight line at which
/// the wall sits — and a fraction has no units, so nothing in the visibility or cover answer
/// depends on how many metres a hex is. Stretch the layout by any factor and every grade and
/// every hidden share comes out identical, node for node; this was measured, not assumed, when
/// the sandbox was found feeding a pixel layout into the rules (see <c>docs/decisions.md</c>,
/// entries 002 and 005). Only two things here carry horizontal units at all: the
/// <see cref="SightResult.Distance"/> handed back for range and detection to price, and
/// <see cref="CoverRadius"/>, which defaults to the layout's own pitch so that even the question
/// of which walls count as a target's cover scales with the grid.
/// </para>
/// <para>
/// The consequence is the one worth remembering, because the obvious guess is wrong. A
/// violation of the one-metre contract does <em>not</em> show up as weak cover or as men seen
/// through walls — those cannot change. It shows up in everything priced in metres: detection,
/// noise, voice, weapon range. The symptom is a stealth game in which nobody is ever found,
/// which looks very like a stealth game being played well. Anybody surprised by that will look
/// here first, which is why it is written here.
/// </para>
/// </remarks>
public sealed class SightSolver
{
    private readonly BattleMap _map;
    private readonly HexLayout _layout;

    public SightSolver(BattleMap map, HexLayout layout, double? coverRadius = null)
    {
        _map = map;
        _layout = layout;
        CoverRadius = coverRadius ?? layout.Pitch;
    }

    /// <summary>
    /// How close a wall must be to the target to count as that target's cover. Obstructions
    /// further back along the line are the shooter's problem, not the target's protection.
    /// </summary>
    public double CoverRadius { get; }

    /// <summary>Share of the silhouette that must be hidden before cover counts as full.</summary>
    public double FullCoverFraction { get; init; } = 0.70;

    /// <summary>Share of the silhouette that must be hidden before cover counts as half.</summary>
    public double HalfCoverFraction { get; init; } = 0.35;

    /// <summary>Below this share, an obstruction is not worth calling cover at all.</summary>
    public double LightCoverFraction { get; init; } = 0.10;

    /// <summary>
    /// Treated as total concealment. A silhouette exactly the height of what hides it produces
    /// a share a hair under one in floating point, and that must not read as a sliver of head
    /// showing over the wall.
    /// </summary>
    private const double FullyConcealed = 1.0 - 1e-9;

    // ---- positions -------------------------------------------------------------

    /// <summary>Where a unit stands, in world space.</summary>
    public Vec3 Ground(NodeId node)
    {
        var tile = _map.GetTile(node.Tile)
                   ?? throw new ArgumentException($"There is no tile at {node.Tile}.", nameof(node));

        var regions = _map.RegionsOf(node.Tile);
        var region = regions.FirstOrDefault(r => r.Index == node.Region) ?? regions[0];
        var plane = _layout.Center(node.Hex) + region.LocalCentroid * _layout.Size;

        return new Vec3(plane, tile.FloorHeight);
    }

    /// <summary>Where a unit looks from.</summary>
    public Vec3 Eye(Vantage vantage) => Ground(vantage.Node).Raised(vantage.Profile.EyeHeight);

    /// <summary>Top of the silhouette, the last part to vanish behind cover.</summary>
    public Vec3 Crown(Vantage vantage) => Ground(vantage.Node).Raised(vantage.Profile.BodyHeight);

    /// <summary>Centre of mass, which is what a shot is aimed at.</summary>
    public Vec3 Centre(Vantage vantage) => Ground(vantage.Node).Raised(vantage.Profile.CentreHeight);

    // ---- queries ---------------------------------------------------------------

    public bool CanSee(Vantage observer, Vantage target) => Trace(observer, target).CanSee;

    /// <summary>Which of these can the observer see? Detection and the interface both ask this.</summary>
    public IEnumerable<Vantage> Visible(Vantage observer, IEnumerable<Vantage> candidates)
        => candidates.Where(c => CanSee(observer, c));

    /// <summary>Trace between two vantages, returning both visibility and cover.</summary>
    public SightResult Trace(Vantage observer, Vantage target)
        => TraceFrom(Eye(observer), Ground(observer.Node).Z, target);

    /// <summary>
    /// The same trace, from a point that is not anybody eye.
    /// </summary>
    /// <remarks>
    /// A charge going off has a position, no stance, and the same question to ask: how much of
    /// that soldier can it get at from here. Everything below this line was always working on a
    /// point and a target rather than on two soldiers, so exposing it costs nothing and saves the
    /// blast model from either duplicating the waterline arithmetic or pretending a grenade is
    /// crouching.
    /// </remarks>
    /// <param name="sourceFloor">
    /// Floor height at the far end, for <see cref="SightResult.HeightAdvantage"/>. Only high
    /// ground reads it, so anything that is not a soldier can pass its own height and ignore it.
    /// </param>
    public SightResult TraceFrom(Vec3 eye, double sourceFloor, Vantage target)
    {
        var footing = Ground(target.Node);
        var body = target.Profile.BodyHeight;
        var crown = footing.Z + body;

        var distance = Vec3.Distance(eye, footing.Raised(target.Profile.CentreHeight));
        var heightAdvantage = sourceFloor - footing.Z;

        // The same place, or near enough: nothing can be in between.
        if (Vec2.Distance(eye.Plane, footing.Plane) < Geometry2D.Epsilon)
            return new SightResult(true, CoverGrade.None, null, 1, null, distance, heightAdvantage, []);

        var sightLine = new Segment2(eye.Plane, footing.Plane);

        var obstructions = new List<Obstruction>();
        var hiddenShare = 0.0;
        var cover = CoverGrade.None;
        WallSegment? coverSource = null;
        WallSegment? blocker = null;

        foreach (var (wall, point, along) in Intersections(sightLine))
        {
            var top = _map.WallTopHeight(wall);
            var hidden = HiddenFraction(wall, top, along, eye.Z, footing.Z, crown, body);
            if (hidden <= 0) continue;

            var toTarget = Vec2.Distance(point, footing.Plane);
            obstructions.Add(new Obstruction(wall, along, hidden, top, toTarget));

            if (wall.Profile.Opaque && hidden > hiddenShare)
            {
                hiddenShare = hidden;
                if (hidden >= FullyConcealed) blocker ??= wall;
            }

            // Only something the target could be pressed against counts as their cover.
            if (toTarget > CoverRadius) continue;

            var grade = Grade(hidden, wall.Profile.Cover);
            if (grade > cover)
            {
                cover = grade;
                coverSource = wall;
            }
        }

        obstructions.Sort((a, b) => a.Along.CompareTo(b.Along));

        if (blocker is not null)
            return SightResult.Hidden(blocker, distance, heightAdvantage, obstructions);

        var exposure = Math.Clamp(1.0 - hiddenShare, 0, 1);
        return new SightResult(true, cover, coverSource, exposure, null, distance, heightAdvantage, obstructions);
    }

    // ---- internals -------------------------------------------------------------

    /// <summary>
    /// How much of the target silhouette this wall hides.
    /// </summary>
    /// <remarks>
    /// A wall spans heights from its base to its top. Projected back along the sight line onto
    /// the target, that becomes a band of target heights the wall conceals; the answer is how
    /// much of the body falls inside it. Projecting the whole band rather than just the top is
    /// what lets a raised walkway be seen underneath.
    /// </remarks>
    private static double HiddenFraction(
        WallSegment wall,
        double wallTop,
        double along,
        double eyeHeight,
        double footing,
        double crown,
        double body)
    {
        if (along <= Geometry2D.Epsilon || body <= 0) return 0;

        var wallBase = wallTop - wall.Profile.HeightMetres;

        // Height on the target that a ray grazing a given point on the wall arrives at.
        double Project(double wallHeight) => eyeHeight + (wallHeight - eyeHeight) / along;

        var bandLow = Project(wallBase);
        var bandHigh = Project(wallTop);

        var overlap = Math.Min(bandHigh, crown) - Math.Max(bandLow, footing);
        return overlap <= 0 ? 0 : Math.Min(overlap / body, 1.0);
    }

    /// <summary>
    /// Turn a hidden share into a cover grade, capped by what the material can ever give: you
    /// do not get full cover from chain link however much of you is behind it.
    /// </summary>
    private CoverGrade Grade(double hiddenFraction, CoverGrade cap)
    {
        var grade =
            hiddenFraction >= FullCoverFraction ? CoverGrade.Full :
            hiddenFraction >= HalfCoverFraction ? CoverGrade.Half :
            hiddenFraction >= LightCoverFraction ? CoverGrade.Light :
            CoverGrade.None;

        return grade < cap ? grade : cap;
    }

    /// <summary>
    /// Every wall the ground projection of a line runs into, with how far along it each one sits.
    /// </summary>
    /// <remarks>
    /// Linear in the wall count, narrowed by a bounding box reject. Ample for the map sizes in
    /// play; if detection ever makes this hot, the walls want a spatial index rather than a
    /// cleverer loop here.
    /// <para>
    /// Public because a straight line is not the only thing that has to get past a wall. An arc
    /// crosses exactly the same walls in exactly the same order and asks a different question of
    /// each — not whether the top is above the sight line but whether it is above the parabola —
    /// so the two queries share the crossing and part company after it. See
    /// <see cref="LobSolver"/>.
    /// </para>
    /// </remarks>
    public IEnumerable<WallCrossing> Crossings(Segment2 line)
    {
        foreach (var (wall, point, along) in Intersections(line))
            yield return new WallCrossing(wall, point, along, _map.WallTopHeight(wall));
    }

    private IEnumerable<(WallSegment Wall, Vec2 Point, double Along)> Intersections(Segment2 sightLine)
    {
        var loX = Math.Min(sightLine.A.X, sightLine.B.X);
        var hiX = Math.Max(sightLine.A.X, sightLine.B.X);
        var loY = Math.Min(sightLine.A.Y, sightLine.B.Y);
        var hiY = Math.Max(sightLine.A.Y, sightLine.B.Y);

        foreach (var wall in _map.Walls)
        {
            var a = _layout.Position(wall.A);
            var b = _layout.Position(wall.B);

            if (Math.Max(a.X, b.X) < loX || Math.Min(a.X, b.X) > hiX) continue;
            if (Math.Max(a.Y, b.Y) < loY || Math.Min(a.Y, b.Y) > hiY) continue;

            if (Geometry2D.Intersect(sightLine, new Segment2(a, b), out var point, out var along))
                yield return (wall, point, along);
        }
    }
}
