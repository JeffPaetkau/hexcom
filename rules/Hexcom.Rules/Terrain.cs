using System;
using System.Collections.Generic;

namespace Hexcom.Rules;

/// <summary>A road: a smooth centreline, a width, and whether it is paved or a dirt track.</summary>
public sealed class Road
{
    /// <summary>Spacing of the points the centreline is stored at, metres.</summary>
    public const double Spacing = 2.0;

    public Road(string name, bool paved, double halfWidth, IReadOnlyList<(double X, double Z)> controls)
    {
        Name = name;
        Paved = paved;
        HalfWidth = halfWidth;
        Points = Densify(controls);
        Profile = new double[Points.Count];
    }

    public string Name { get; }
    public bool Paved { get; }
    public double HalfWidth { get; }

    /// <summary>This road's position in the terrain's list, for keeping per-road tallies in arrays.</summary>
    public int Index { get; internal set; }

    /// <summary>The centreline, about <see cref="Spacing"/> metres between points.</summary>
    public IReadOnlyList<(double X, double Z)> Points { get; }

    /// <summary>The height of the road surface at each point. Filled in by the terrain.</summary>
    public double[] Profile { get; }

    /// <summary>Catmull-Rom through the control points, sampled evenly.</summary>
    private static List<(double X, double Z)> Densify(IReadOnlyList<(double X, double Z)> c)
    {
        var points = new List<(double X, double Z)>();
        for (var i = 0; i + 1 < c.Count; i++)
        {
            var p0 = c[Math.Max(i - 1, 0)];
            var p1 = c[i];
            var p2 = c[i + 1];
            var p3 = c[Math.Min(i + 2, c.Count - 1)];

            var span = Math.Sqrt((p2.X - p1.X) * (p2.X - p1.X) + (p2.Z - p1.Z) * (p2.Z - p1.Z));
            var steps = Math.Max(1, (int)Math.Ceiling(span / Spacing));
            for (var s = 0; s < steps; s++)
            {
                var t = (double)s / steps;
                points.Add((CatmullRom(p0.X, p1.X, p2.X, p3.X, t), CatmullRom(p0.Z, p1.Z, p2.Z, p3.Z, t)));
            }
        }
        points.Add(c[^1]);
        return points;
    }

    private static double CatmullRom(double p0, double p1, double p2, double p3, double t)
        => 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t);
}

/// <summary>
/// The landscape: a height for every point on the ground plane, and the roads laid over it.
/// </summary>
/// <remarks>
/// <para>
/// One continuous function of (x, z). There are no storeys or steps; at any point the height
/// and the slope are whatever the noise says, and the hex grid is a way of addressing the
/// ground rather than a thing the ground is built from. Broad hills, rolling ground and
/// small detail are three layers of fractal noise on coordinates warped by a fourth, which
/// is what makes the contours curve instead of following the noise lattice.
/// </para>
/// <para>
/// Roads are laid on top: near a centreline the ground blends onto the road's own profile,
/// which is the terrain along the road smoothed over sixty metres. That is what gives a road
/// cuttings on the way up a hill and an embankment across a dip without anybody authoring
/// them. Everything that needs to agree on where the ground is, the mesh, the camera, the
/// marks on the board and eventually the rules, calls <see cref="Height"/>.
/// </para>
/// </remarks>
public sealed class Terrain : IGround
{
    /// <summary>Roads are authored within this distance of the origin, metres.</summary>
    public const double MapHalfExtent = 1024;

    /// <summary>How far from a centreline a road can shape the ground or the surface, metres.</summary>
    public const double Influence = 24;

    /// <summary>How far past its edge a road blends into the ground, metres.</summary>
    private const double Shoulder = 8;

    private const double Bucket = 32;

    private readonly Noise _relief;
    private readonly Noise _warp;
    private readonly Dictionary<(int, int), List<(Road Road, int Segment)>> _buckets = new();

    public Terrain(int seed)
    {
        _relief = new Noise(seed);
        _warp = new Noise(seed + 1);
        Roads = Author();

        for (var i = 0; i < Roads.Count; i++)
        {
            Roads[i].Index = i;
            FillProfile(Roads[i]);
            Index(Roads[i]);
        }
    }

    public IReadOnlyList<Road> Roads { get; }

    /// <summary>The ground before any road is laid on it.</summary>
    public double BaseHeight(double x, double z)
    {
        var wx = x + 40 * _warp.Fbm(x / 300, z / 300, 2);
        var wz = z + 40 * _warp.Fbm(x / 300 + 7.3, z / 300 - 2.1, 2);

        // Hills of a few tens of metres over several hundred, a swell every few hundred metres,
        // rolling ground of a few metres over a hundred, and a little roughness. The fractal
        // sum rarely exceeds half its nominal amplitude, so the hills come to about twenty
        // metres and slopes stay under about twenty degrees.
        return 40 * _relief.Fbm(wx / 700, wz / 700, 3)
             + 12 * _relief.Fbm(wx / 280 + 11.7, wz / 280 - 5.2, 3)
             + 5 * _relief.Fbm(wx / 120 + 3.1, wz / 120, 3)
             + 0.5 * _relief.Fbm(x / 15, z / 15, 2)
             + Bluff(x, z);
    }

    /// <summary>
    /// A bluff south of the highway cutting: a three-metre table whose north face runs east to
    /// west and steepens along its length, from a ramp anyone can walk at the west end, through
    /// the grades the price list argues about, to a sheer drop at the east end. Put there so
    /// every slope the rules care about is within one turn of the standard picture, with the
    /// refusals the rest of the landscape never produces.
    /// </summary>
    private static double Bluff(double x, double z)
    {
        const double height = 3;
        const double foot = 30, west = 126, east = 174, crest = 50, back = 58;

        // The grade climbs geometrically along the face, 0.15 at the west end to 6 at the
        // east, so the walkable half and the refused half are about equal in length.
        var along = Math.Clamp((x - west) / (east - west), 0, 1);
        var grade = 0.15 * Math.Pow(40, along);
        var face = Math.Clamp((z - foot) * grade / height, 0, 1);

        // The table ends: an easy slope back down to the south, and soft caps east and west.
        var rear = Math.Clamp((back - z) / (back - crest), 0, 1);
        var caps = Rise((x - (west - 8)) / 8) * Rise(((east + 8) - x) / 8);
        return height * Math.Min(face, rear) * caps;
    }

    /// <summary>Nothing below zero, everything above one, and a smooth step between.</summary>
    private static double Rise(double v) => v <= 0 ? 0 : v >= 1 ? 1 : v * v * (3 - 2 * v);

    /// <summary>The height of the ground at a point, roads included.</summary>
    /// <remarks>
    /// Every road within reach pulls the ground towards its own profile by a weight that is
    /// one on the road and fades to nothing across the shoulder; the pulls are averaged where
    /// they overlap. Picking the nearest road instead leaves a step along the line where the
    /// choice flips at a junction, which a low sun draws as a row of shadows.
    /// </remarks>
    public double Height(double x, double z)
    {
        var h = BaseHeight(x, z);
        if (!_buckets.TryGetValue(BucketOf(x, z), out var segments)) return h;

        // The nearest segment of each road, and so each road's profile at this point.
        var nearest = new double[Roads.Count];
        var profile = new double[Roads.Count];
        for (var i = 0; i < nearest.Length; i++) nearest[i] = double.MaxValue;

        foreach (var (road, segment) in segments)
        {
            var d = DistanceToSegment(road, segment, x, z, out var t);
            if (d >= nearest[road.Index]) continue;
            nearest[road.Index] = d;
            profile[road.Index] = road.Profile[segment] + (road.Profile[segment + 1] - road.Profile[segment]) * t;
        }

        double pull = 0, weight = 0;
        for (var i = 0; i < nearest.Length; i++)
        {
            if (nearest[i] == double.MaxValue) continue;
            var w = Smooth(Roads[i].HalfWidth + Shoulder, Roads[i].HalfWidth, nearest[i]);
            pull += w * (profile[i] - h);
            weight += w;
        }

        return weight <= 0 ? h : h + pull / Math.Max(1, weight);
    }

    /// <summary>
    /// How far outside the edge of the nearest paved road, and of the nearest dirt track, a
    /// point is. Negative on the road itself; capped at <see cref="Influence"/>.
    /// </summary>
    public (double Paved, double Track) EdgeDistances(double x, double z)
    {
        double paved = Influence, track = Influence;
        if (!_buckets.TryGetValue(BucketOf(x, z), out var segments)) return (paved, track);

        foreach (var (road, segment) in segments)
        {
            var edge = DistanceToSegment(road, segment, x, z, out _) - road.HalfWidth;
            if (road.Paved) paved = Math.Min(paved, edge);
            else track = Math.Min(track, edge);
        }

        return (paved, track);
    }

    /// <summary>What is underfoot: paved on a paved road, track on a dirt track, open anywhere else.</summary>
    /// <remarks>
    /// The line is the road edge itself, the one the road map defines, so the rules and the
    /// picture agree on where the road stops even though the picture blends dirt across the
    /// shoulder. A foot on the shoulder is on a field.
    /// </remarks>
    public Surface SurfaceAt(double x, double z)
    {
        var (paved, track) = EdgeDistances(x, z);
        if (paved <= 0) return Surface.Paved;
        if (track <= 0) return Surface.Track;
        return Surface.Open;
    }

    private static double DistanceToSegment(Road road, int segment, double x, double z, out double t)
    {
        var (ax, az) = road.Points[segment];
        var (bx, bz) = road.Points[segment + 1];
        var dx = bx - ax;
        var dz = bz - az;
        var length2 = dx * dx + dz * dz;

        t = length2 < 1e-9 ? 0 : Math.Clamp(((x - ax) * dx + (z - az) * dz) / length2, 0, 1);
        var px = ax + dx * t - x;
        var pz = az + dz * t - z;
        return Math.Sqrt(px * px + pz * pz);
    }

    /// <summary>The road surface follows the ground, smoothed over thirty metres either way.</summary>
    private void FillProfile(Road road)
    {
        var heights = new double[road.Points.Count];
        for (var i = 0; i < heights.Length; i++) heights[i] = BaseHeight(road.Points[i].X, road.Points[i].Z);

        var window = (int)Math.Round(30 / Road.Spacing);
        for (var i = 0; i < heights.Length; i++)
        {
            double sum = 0;
            var count = 0;
            for (var j = Math.Max(0, i - window); j <= Math.Min(heights.Length - 1, i + window); j++)
            {
                sum += heights[j];
                count++;
            }
            road.Profile[i] = sum / count;
        }
    }

    /// <summary>
    /// File every segment under each bucket within <see cref="Influence"/> of it, so a point's
    /// own bucket lists every segment that could matter to it.
    /// </summary>
    private void Index(Road road)
    {
        for (var s = 0; s + 1 < road.Points.Count; s++)
        {
            var (ax, az) = road.Points[s];
            var (bx, bz) = road.Points[s + 1];

            var bx0 = (int)Math.Floor((Math.Min(ax, bx) - Influence) / Bucket);
            var bx1 = (int)Math.Floor((Math.Max(ax, bx) + Influence) / Bucket);
            var bz0 = (int)Math.Floor((Math.Min(az, bz) - Influence) / Bucket);
            var bz1 = (int)Math.Floor((Math.Max(az, bz) + Influence) / Bucket);

            for (var i = bx0; i <= bx1; i++)
            for (var j = bz0; j <= bz1; j++)
            {
                if (!_buckets.TryGetValue((i, j), out var list)) _buckets[(i, j)] = list = new List<(Road, int)>();
                list.Add((road, s));
            }
        }
    }

    private static (int, int) BucketOf(double x, double z)
        => ((int)Math.Floor(x / Bucket), (int)Math.Floor(z / Bucket));

    private static double Smooth(double edge0, double edge1, double x)
    {
        var t = Math.Clamp((x - edge0) / (edge1 - edge0), 0, 1);
        return t * t * (3 - 2 * t);
    }

    /// <summary>The roads of this place. Hand-laid; a map file will replace this one day.</summary>
    private static List<Road> Author() => new()
    {
        new Road("Highway", paved: true, halfWidth: 3.5, new[]
        {
            (-1100.0, 60.0), (-700.0, -90.0), (-350.0, 20.0), (0.0, -40.0), (300.0, 60.0), (650.0, -30.0), (1100.0, 40.0),
        }),
        new Road("North road", paved: true, halfWidth: 3.0, new[]
        {
            (-70.0, -1100.0), (10.0, -600.0), (-50.0, -200.0), (0.0, -40.0), (40.0, 200.0), (-30.0, 600.0), (50.0, 1100.0),
        }),
        new Road("Quarry track", paved: false, halfWidth: 2.0, new[]
        {
            (300.0, 60.0), (420.0, 250.0), (380.0, 480.0), (520.0, 700.0),
        }),
        new Road("Farm track", paved: false, halfWidth: 1.8, new[]
        {
            (-350.0, 20.0), (-450.0, -250.0), (-380.0, -520.0),
        }),
    };
}
