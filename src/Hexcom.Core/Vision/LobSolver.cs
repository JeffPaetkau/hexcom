using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Geometry;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;

namespace Hexcom.Core.Vision;

/// <summary>
/// One wall a line crosses, and everything either query needs to know about the crossing.
/// </summary>
/// <param name="Along">Where it sits on the line, 0 at the near end and 1 at the far end.</param>
/// <param name="Top">Height of the top of the wall, in metres above the map datum.</param>
public readonly record struct WallCrossing(WallSegment Wall, Vec2 Point, double Along, double Top)
{
    public override string ToString() => $"{Wall.Profile.Id} at {Along:0.00} along, top {Top:0.0} m";
}

/// <summary>
/// Where a thrown object comes down, and what it had to get over on the way.
/// </summary>
/// <param name="Landing">
/// Where it actually lands. The same as <paramref name="Aimed"/> whenever the throw clears.
/// </param>
/// <param name="Apex">
/// Height of the arc above the straight line between hand and landing point, at its highest, in
/// metres. Nought means the throw was flat because nothing was in the way.
/// </param>
/// <param name="Required">
/// The apex the throw would have needed to clear everything between. Larger than
/// <paramref name="Apex"/> exactly when the throw clipped something.
/// </param>
/// <param name="Clipped">The wall it caught, when it did not clear.</param>
/// <param name="Distance">Ground distance from thrower to landing point, in metres.</param>
public sealed record LobResult(
    bool Clears,
    NodeId Aimed,
    NodeId Landing,
    double Apex,
    double Required,
    WallSegment? Clipped,
    double Distance)
{
    public override string ToString()
        => Clears
            ? $"clears to {Landing} over an apex of {Apex:0.0} m"
            : $"clips {Clipped?.Profile.Id} and drops at {Landing} ({Required:0.0} m needed)";
}

/// <summary>
/// Answers whether something lobbed over the intervening walls gets there, and where it comes
/// down when it does not.
/// </summary>
/// <remarks>
/// The second trace, and the reason there had to be one. Every question the game has asked of
/// the map so far is whether a <em>straight line</em> gets through, and the whole point of
/// throwing something is that it does not have to: you lob a grenade over the wall precisely
/// because you cannot shoot through it. So the sight solver cannot answer this, and dressing a
/// throw up as a shot at a soldier would have given away the one thing that makes it worth
/// having.
/// <para>
/// It shares the crossing with <see cref="SightSolver.Crossings"/> and parts company immediately
/// after. Sight asks whether the top of each wall is above the line; an arc asks whether it is
/// above the <em>parabola</em>, which is a different question with a free parameter in it — how
/// high the thrower chose to loft the thing.
/// </para>
/// <para>
/// <b>The arc is chosen, not given.</b> A soldier throws as flat as the obstacles allow, so the
/// solver works out the lowest apex that clears everything in the way and uses that. On open
/// ground it is nought and the arc degenerates into the sight line, which is the right answer and
/// a useful sanity check. Behind a wall it is whatever that wall demands. Only when the demand
/// exceeds what an arm can manage does the throw fail, and it fails by clipping the first wall it
/// could not get over, dropping short on the near side of it — which is the bad outcome worth
/// modelling, because it is the one that lands a grenade at your own feet.
/// </para>
/// <para>
/// Why a parabola with a single apex parameter rather than a launch angle and a muzzle speed:
/// the answer wanted is a yes or no about clearance, and every projectile that starts in a hand
/// and ends on the ground is a parabola through those two points. Parametrising by the height at
/// the midpoint rather than by the angle means the free parameter is the thing being decided and
/// the two endpoints are fixed by construction, so there is no solving to do and no case where
/// the arithmetic misses the target.
/// </para>
/// </remarks>
public sealed class LobSolver(SightSolver sight, BattleMap map, HexLayout layout)
{
    /// <summary>
    /// How far short of a wall it clipped a throw comes down, as a share of the throw.
    /// </summary>
    /// <remarks>
    /// Not a balance number: it is the nudge that puts the landing point on the thrower side of
    /// the wall rather than exactly on it, where rounding decides which hex it belongs to. Small
    /// enough that a clipped throw drops against the foot of the wall, which is where a grenade
    /// that hits a wall goes.
    /// </remarks>
    private const double ClipBackoff = 0.02;

    /// <summary>Where the object leaves the hand: the thrower own eye line, near enough.</summary>
    /// <remarks>
    /// A throw comes off a shoulder rather than out of an eye, and the difference is a few
    /// centimetres against a wall band a metre tall. What matters is that it tracks the stance,
    /// so that a soldier lying flat behind a wall has to loft it far higher than one standing at
    /// the same spot — which is the interesting consequence, and it falls out for free.
    /// </remarks>
    public Vec3 Hand(Vantage thrower) => sight.Eye(thrower);

    /// <summary>
    /// Lob something from a vantage to a place, as flat as the walls in the way permit.
    /// </summary>
    /// <param name="maxApex">
    /// The highest the thrower can loft it above the straight line, in metres. Beyond this the
    /// throw clips rather than clears.
    /// </param>
    public LobResult Trace(Vantage thrower, NodeId at, double maxApex)
    {
        var hand = Hand(thrower);
        var landing = sight.Ground(at);
        var distance = Vec3.GroundDistance(hand, landing);

        // Straight down at your own feet: nothing can be in the way of that.
        if (distance < Geometry2D.Epsilon)
            return new LobResult(true, at, at, 0, 0, null, 0);

        var line = new Segment2(hand.Plane, landing.Plane);
        var crossings = sight.Crossings(line).OrderBy(c => c.Along).ToList();

        var required = 0.0;
        WallCrossing? blocking = null;

        foreach (var crossing in crossings)
        {
            var needed = ApexToClear(crossing, hand.Z, landing.Z);
            if (needed <= required) continue;

            required = needed;
            if (needed > maxApex && blocking is null) blocking = crossing;
        }

        if (blocking is not { } clipped)
            return new LobResult(true, at, at, required, required, null, distance);

        // It caught the wall, so it comes down on the near side of it rather than beyond.
        var short_ = line.PointAt(Math.Max(0, clipped.Along - ClipBackoff));

        return new LobResult(
            false, at, NodeAt(short_, thrower.Node), maxApex, required, clipped.Wall, distance);
    }

    /// <summary>
    /// How high above the straight line the arc must pass at its midpoint to get over this wall.
    /// </summary>
    /// <remarks>
    /// The arc is <c>chord(s) + 4·A·s·(1-s)</c>, which is the parabola through both endpoints
    /// whose extra height at the midpoint is <c>A</c>. Rearranging for the wall gives the apex
    /// that clears it, and the shape of the term is the interesting part: the divisor collapses
    /// toward the ends, so a wall you are standing right behind demands a far higher throw than
    /// the same wall halfway to the target. That is why hugging the thing you are trying to lob
    /// over is the hard version of the shot, and it is arithmetic rather than a rule.
    /// </remarks>
    public static double ApexToClear(WallCrossing crossing, double from, double to)
    {
        var s = crossing.Along;
        if (s <= Geometry2D.Epsilon || s >= 1 - Geometry2D.Epsilon) return 0;

        var chord = from + (to - from) * s;
        if (crossing.Top <= chord) return 0;

        return (crossing.Top - chord) / (4 * s * (1 - s));
    }

    /// <summary>
    /// The node a point on the ground belongs to, falling back to the thrower own node.
    /// </summary>
    /// <remarks>
    /// The fallback covers a throw that clips a wall standing on the edge of the map, where there
    /// is no tile on the near side to drop into. Landing at the thrower feet is the worst outcome
    /// available and it is the honest one: the thing did not get anywhere.
    /// </remarks>
    private NodeId NodeAt(Vec2 point, NodeId thrower)
    {
        var address = new TileAddress(layout.HexAt(point), thrower.Layer);
        if (!map.HasTile(address)) return thrower;

        var regions = map.RegionsOf(address);
        if (regions.Count == 0) return thrower;

        // Which side of an interior wall it fell on, by whichever region centre is nearest.
        var local = (point - layout.Center(address.Hex)) / layout.Size;
        var best = regions[0];
        var bestDistance = double.MaxValue;

        foreach (var region in regions)
        {
            var offset = Vec2.Distance(local, region.LocalCentroid);
            if (offset >= bestDistance) continue;
            bestDistance = offset;
            best = region;
        }

        return new NodeId(address, best.Index);
    }
}
