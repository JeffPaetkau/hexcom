namespace Hexcom.Core.Geometry;

/// <summary>
/// A 2D point in the horizontal plane. Deliberately engine-agnostic: the view layer converts
/// to whatever vector type it uses.
/// </summary>
public readonly record struct Vec2(double X, double Y)
{
    public static readonly Vec2 Zero = new(0, 0);

    public static Vec2 operator +(Vec2 a, Vec2 b) => new(a.X + b.X, a.Y + b.Y);
    public static Vec2 operator -(Vec2 a, Vec2 b) => new(a.X - b.X, a.Y - b.Y);
    public static Vec2 operator *(Vec2 a, double k) => new(a.X * k, a.Y * k);
    public static Vec2 operator *(double k, Vec2 a) => a * k;
    public static Vec2 operator /(Vec2 a, double k) => new(a.X / k, a.Y / k);
    public static Vec2 operator -(Vec2 a) => new(-a.X, -a.Y);

    public double Length => Math.Sqrt(X * X + Y * Y);
    public double LengthSquared => X * X + Y * Y;
    public double Angle => Math.Atan2(Y, X);

    public Vec2 Normalized
    {
        get
        {
            var len = Length;
            return len < 1e-12 ? Zero : this / len;
        }
    }

    public Vec2 Rotated(double radians)
    {
        var c = Math.Cos(radians);
        var s = Math.Sin(radians);
        return new Vec2(X * c - Y * s, X * s + Y * c);
    }

    public static double Dot(Vec2 a, Vec2 b) => a.X * b.X + a.Y * b.Y;

    /// <summary>2D cross product (the Z component of the 3D cross product).</summary>
    public static double Cross(Vec2 a, Vec2 b) => a.X * b.Y - a.Y * b.X;

    public static double Distance(Vec2 a, Vec2 b) => (a - b).Length;

    public override string ToString() => $"({X:0.###}, {Y:0.###})";
}
