namespace Hexcom.Core.Geometry;

/// <summary>
/// A point in the battlefield. <c>X</c> and <c>Y</c> are the horizontal plane, matching
/// <see cref="Vec2"/>; <c>Z</c> is height above the map datum, in metres.
/// </summary>
public readonly record struct Vec3(double X, double Y, double Z)
{
    public static readonly Vec3 Zero = new(0, 0, 0);

    public Vec3(Vec2 plane, double z) : this(plane.X, plane.Y, z) { }

    /// <summary>This point with its height discarded.</summary>
    public Vec2 Plane => new(X, Y);

    public static Vec3 operator +(Vec3 a, Vec3 b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);
    public static Vec3 operator -(Vec3 a, Vec3 b) => new(a.X - b.X, a.Y - b.Y, a.Z - b.Z);
    public static Vec3 operator *(Vec3 a, double k) => new(a.X * k, a.Y * k, a.Z * k);

    /// <summary>This point raised by <paramref name="metres"/>.</summary>
    public Vec3 Raised(double metres) => this with { Z = Z + metres };

    public double Length => Math.Sqrt(X * X + Y * Y + Z * Z);

    public static double Distance(Vec3 a, Vec3 b) => (a - b).Length;

    /// <summary>Distance ignoring height, which is what a map ruler measures.</summary>
    public static double GroundDistance(Vec3 a, Vec3 b) => Vec2.Distance(a.Plane, b.Plane);

    public override string ToString() => $"({X:0.##}, {Y:0.##}, {Z:0.##})";
}
