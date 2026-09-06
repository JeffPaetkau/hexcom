using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Geometry;
using Hexcom.Core.Hexes;

namespace Hexcom.Core.Maps;

/// <summary>Thrown when a hex's wall layout cannot be turned into a set of regions.</summary>
public sealed class HexPartitionException(string message) : Exception(message);

/// <summary>
/// One walkable (or merely crossable) piece of a hex, after interior walls have cut it up.
/// </summary>
/// <param name="Index">Stable index within the tile; region 0 is always the largest.</param>
/// <param name="CornerIndices">The region polygon, as local corner indices in counter-clockwise order.</param>
/// <param name="AreaFraction">Share of the whole hex, in [0,1]. The fractions of a tile sum to 1.</param>
/// <param name="Sides">Which of the six hex sides bound this region, i.e. where you can enter and leave.</param>
/// <param name="Chords">Interior walls bounding this region, as local corner pairs.</param>
/// <param name="LocalCentroid">Centroid relative to the hex centre, in units of hex size.</param>
/// <param name="Occupiable">
/// Whether a unit can stand here and end its turn. Small offcuts and the halves of a bisected
/// hex are crossable but not occupiable — you can vault through, you cannot stop.
/// </param>
public sealed record HexRegion(
    int Index,
    IReadOnlyList<int> CornerIndices,
    double AreaFraction,
    IReadOnlyList<HexDirection> Sides,
    IReadOnlyList<(int A, int B)> Chords,
    Vec2 LocalCentroid,
    bool Occupiable)
{
    public bool BoundsSide(HexDirection direction) => Sides.Contains(direction);
}

/// <summary>
/// Cuts a hex into regions given the interior walls crossing it.
/// </summary>
/// <remarks>
/// The hex plus its chords is a small planar graph whose vertices are the six corners. Walking
/// its faces gives the regions exactly, so this handles any legal combination of chords rather
/// than special-casing the common ones.
/// <para>
/// Current limitation: chords that properly cross each other inside the hex (for example two
/// bisectors meeting at the centre) are rejected. Model that shape by putting the two walls in
/// neighbouring hexes instead.
/// </para>
/// </remarks>
public static class HexPartition
{
    /// <summary>Area of a hexagon with circumradius 1.</summary>
    public const double UnitHexArea = 2.598076211353316; // 3*sqrt(3)/2

    /// <summary>
    /// A region must hold at least this share of a hex for a unit to stand in it. Set between
    /// the two natural cut sizes: a minor chord leaves 5/6, a bisector leaves 1/2.
    /// </summary>
    public const double DefaultOccupancyThreshold = 0.6;

    private static readonly Vec2[] UnitCorners = BuildUnitCorners();

    private static readonly HexRegion WholeHex = new(
        Index: 0,
        CornerIndices: [0, 1, 2, 3, 4, 5],
        AreaFraction: 1.0,
        Sides: HexDirectionExtensions.All,
        Chords: [],
        LocalCentroid: Vec2.Zero,
        Occupiable: true);

    private static readonly IReadOnlyList<HexRegion> UndividedHex = [WholeHex];

    private static Vec2[] BuildUnitCorners()
    {
        var corners = new Vec2[6];
        for (var i = 0; i < 6; i++)
        {
            var angle = Math.PI / 3.0 * i;
            corners[i] = new Vec2(Math.Cos(angle), Math.Sin(angle));
        }
        return corners;
    }

    /// <summary>Corner position on a hexagon of circumradius 1, centred on the origin.</summary>
    public static Vec2 UnitCorner(int index) => UnitCorners[((index % 6) + 6) % 6];

    /// <summary>
    /// Compute the regions of a hex. <paramref name="chords"/> may include hex sides; they are
    /// ignored, because a wall along a side bounds the hex rather than dividing it.
    /// </summary>
    public static IReadOnlyList<HexRegion> Compute(
        IEnumerable<(int A, int B)> chords,
        double occupancyThreshold = DefaultOccupancyThreshold)
    {
        var interior = Normalize(chords);
        if (interior.Count == 0) return UndividedHex;

        RejectCrossings(interior);

        var adjacency = BuildAdjacency(interior);
        var faces = TraverseFaces(adjacency);

        var regions = faces
            .Select(face => BuildRegion(face, occupancyThreshold))
            .Where(r => r.AreaFraction > 1e-6)
            .OrderByDescending(r => r.AreaFraction)
            .ToList();

        // Re-index so region 0 is always the largest piece.
        return regions.Select((r, i) => r with { Index = i }).ToList();
    }

    private static List<(int A, int B)> Normalize(IEnumerable<(int A, int B)> chords)
    {
        var set = new HashSet<(int, int)>();
        foreach (var (rawA, rawB) in chords)
        {
            var a = ((rawA % 6) + 6) % 6;
            var b = ((rawB % 6) + 6) % 6;
            if (a == b) continue;
            if (WallSegment.Classify(a, b) == ChordClass.Side) continue; // bounds, does not divide
            set.Add(a < b ? (a, b) : (b, a));
        }
        return set.OrderBy(c => c.Item1).ThenBy(c => c.Item2).ToList();
    }

    private static void RejectCrossings(List<(int A, int B)> chords)
    {
        for (var i = 0; i < chords.Count; i++)
        for (var j = i + 1; j < chords.Count; j++)
        {
            var p = new Segment2(UnitCorner(chords[i].A), UnitCorner(chords[i].B));
            var q = new Segment2(UnitCorner(chords[j].A), UnitCorner(chords[j].B));
            if (Geometry2D.ProperlyCross(p, q, out _))
                throw new HexPartitionException(
                    $"Walls {chords[i]} and {chords[j]} cross inside the same hex. " +
                    "Split the shape across neighbouring hexes instead.");
        }
    }

    private static List<int>[] BuildAdjacency(List<(int A, int B)> chords)
    {
        var neighbours = new List<int>[6];
        for (var i = 0; i < 6; i++) neighbours[i] = [];

        void Connect(int a, int b)
        {
            if (!neighbours[a].Contains(b)) neighbours[a].Add(b);
            if (!neighbours[b].Contains(a)) neighbours[b].Add(a);
        }

        for (var i = 0; i < 6; i++) Connect(i, (i + 1) % 6); // the hex boundary
        foreach (var (a, b) in chords) Connect(a, b);

        // Order each corner's neighbours counter-clockwise by outgoing bearing; the face walk
        // depends on this rotational ordering.
        for (var v = 0; v < 6; v++)
        {
            var origin = UnitCorner(v);
            neighbours[v] = neighbours[v]
                .OrderBy(u => Geometry2D.NormalizeAngle((UnitCorner(u) - origin).Angle))
                .ToList();
        }

        return neighbours;
    }

    /// <summary>
    /// Walk the planar graph's faces. Following each half-edge by turning as far clockwise as
    /// possible at the far end keeps the interior on the left, so bounded faces come out
    /// counter-clockwise (positive area) and the surrounding outer face comes out clockwise.
    /// </summary>
    private static List<List<int>> TraverseFaces(List<int>[] adjacency)
    {
        var visited = new HashSet<(int From, int To)>();
        var faces = new List<List<int>>();

        for (var start = 0; start < 6; start++)
        foreach (var first in adjacency[start])
        {
            if (!visited.Add((start, first))) continue;

            var face = new List<int> { start };
            var from = start;
            var to = first;

            while (true)
            {
                var ring = adjacency[to];
                var back = ring.IndexOf(from);
                var next = ring[(back - 1 + ring.Count) % ring.Count];

                if (to == start && next == first) break;

                face.Add(to);
                visited.Add((to, next));
                from = to;
                to = next;

                if (face.Count > 32)
                    throw new HexPartitionException("Face traversal failed to terminate.");
            }

            faces.Add(face);
        }

        // Positive signed area means counter-clockwise, which means a bounded interior face.
        return faces
            .Where(f => f.Count >= 3 && Geometry2D.SignedArea(f.Select(UnitCorner).ToList()) > 1e-9)
            .ToList();
    }

    private static HexRegion BuildRegion(List<int> face, double occupancyThreshold)
    {
        var polygon = face.Select(UnitCorner).ToList();
        var area = Geometry2D.SignedArea(polygon);
        var fraction = area / UnitHexArea;

        var sides = new List<HexDirection>();
        var chords = new List<(int A, int B)>();

        for (var i = 0; i < face.Count; i++)
        {
            var a = face[i];
            var b = face[(i + 1) % face.Count];
            if (WallSegment.Classify(a, b) == ChordClass.Side)
                sides.Add((HexDirection)(b == (a + 1) % 6 ? a : b));
            else
                chords.Add(a < b ? (a, b) : (b, a));
        }

        sides.Sort();

        return new HexRegion(
            Index: 0,
            CornerIndices: face,
            AreaFraction: fraction,
            Sides: sides,
            Chords: chords,
            LocalCentroid: Centroid(polygon, area),
            Occupiable: fraction >= occupancyThreshold);
    }

    private static Vec2 Centroid(IReadOnlyList<Vec2> polygon, double signedArea)
    {
        if (Math.Abs(signedArea) < 1e-12) return Vec2.Zero;

        double cx = 0, cy = 0;
        for (var i = 0; i < polygon.Count; i++)
        {
            var p = polygon[i];
            var q = polygon[(i + 1) % polygon.Count];
            var cross = p.X * q.Y - q.X * p.Y;
            cx += (p.X + q.X) * cross;
            cy += (p.Y + q.Y) * cross;
        }

        return new Vec2(cx / (6 * signedArea), cy / (6 * signedArea));
    }
}
