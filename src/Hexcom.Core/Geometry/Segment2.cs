using System.Collections.Generic;

namespace Hexcom.Core.Geometry;

/// <summary>A line segment between two points.</summary>
public readonly record struct Segment2(Vec2 A, Vec2 B)
{
    public Vec2 Delta => B - A;
    public Vec2 Midpoint => (A + B) * 0.5;
    public double Length => Delta.Length;

    public Vec2 PointAt(double t) => A + Delta * t;
}

public static class Geometry2D
{
    public const double Epsilon = 1e-9;

    /// <summary>
    /// True when two segments cross at a point strictly interior to both. Segments that merely
    /// touch at an endpoint — which is the normal case for walls meeting at a shared corner —
    /// are <b>not</b> proper crossings.
    /// </summary>
    public static bool ProperlyCross(Segment2 p, Segment2 q, out Vec2 intersection)
    {
        intersection = Vec2.Zero;

        var r = p.Delta;
        var s = q.Delta;
        var denom = Vec2.Cross(r, s);
        if (Math.Abs(denom) < Epsilon) return false; // parallel or collinear

        var t = Vec2.Cross(q.A - p.A, s) / denom;
        var u = Vec2.Cross(q.A - p.A, r) / denom;

        if (t <= Epsilon || t >= 1 - Epsilon) return false;
        if (u <= Epsilon || u >= 1 - Epsilon) return false;

        intersection = p.PointAt(t);
        return true;
    }

    /// <summary>
    /// True when the segments intersect anywhere, including at shared endpoints. Used for
    /// line-of-fire tests, where grazing a wall corner still counts.
    /// </summary>
    public static bool Intersect(Segment2 p, Segment2 q, out Vec2 intersection, out double tOnP)
    {
        intersection = Vec2.Zero;
        tOnP = 0;

        var r = p.Delta;
        var s = q.Delta;
        var denom = Vec2.Cross(r, s);
        if (Math.Abs(denom) < Epsilon) return false;

        var t = Vec2.Cross(q.A - p.A, s) / denom;
        var u = Vec2.Cross(q.A - p.A, r) / denom;

        if (t < -Epsilon || t > 1 + Epsilon) return false;
        if (u < -Epsilon || u > 1 + Epsilon) return false;

        tOnP = t;
        intersection = p.PointAt(t);
        return true;
    }

    /// <summary>
    /// Signed area of a simple polygon. Positive when the vertices wind counter-clockwise.
    /// </summary>
    public static double SignedArea(IReadOnlyList<Vec2> polygon)
    {
        if (polygon.Count < 3) return 0;
        double sum = 0;
        for (var i = 0; i < polygon.Count; i++)
        {
            var a = polygon[i];
            var b = polygon[(i + 1) % polygon.Count];
            sum += a.X * b.Y - b.X * a.Y;
        }
        return sum * 0.5;
    }

    /// <summary>The smaller angle between two bearings, always in [0, pi].</summary>
    public static double AngleBetween(double a, double b)
    {
        var difference = Math.Abs(NormalizeAngle(a) - NormalizeAngle(b));
        return difference > Math.PI ? Math.PI * 2 - difference : difference;
    }

    /// <summary>Normalise an angle to [0, 2*pi).</summary>
    public static double NormalizeAngle(double radians)
    {
        var twoPi = Math.PI * 2;
        var a = radians % twoPi;
        return a < 0 ? a + twoPi : a;
    }
}
