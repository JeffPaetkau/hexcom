using Hexcom.Core.Geometry;

namespace Hexcom.Core.Hexes;

/// <summary>
/// Converts between hex space and world space for a <b>flat-top</b> grid.
/// </summary>
/// <remarks>
/// Flat-top is baked into the logical model, because the two-poles-per-hex corner naming in
/// <see cref="HexVertex"/> only works for one orientation. That is not a real constraint on
/// how the game looks: set <see cref="RotationRadians"/> to 30 degrees and the map renders
/// pointy-top. The logic never notices.
/// </remarks>
public sealed class HexLayout
{
    private static readonly double Sqrt3 = Math.Sqrt(3.0);

    /// <summary>Distance from a hex centre to a corner, in world units (metres).</summary>
    public double Size { get; }

    /// <summary>World position of hex (0,0).</summary>
    public Vec2 Origin { get; }

    /// <summary>Rotation applied to the whole grid. Use pi/6 to render pointy-top.</summary>
    public double RotationRadians { get; }

    public HexLayout(double size, Vec2 origin = default, double rotationRadians = 0)
    {
        if (size <= 0) throw new ArgumentOutOfRangeException(nameof(size), "Hex size must be positive.");
        Size = size;
        Origin = origin;
        RotationRadians = rotationRadians;
    }

    /// <summary>Corner-to-corner width of a hex (along the flat-top X axis).</summary>
    public double Width => Size * 2.0;

    /// <summary>Flat-to-flat height of a hex.</summary>
    public double Height => Size * Sqrt3;

    /// <summary>Centre-to-centre distance between neighbouring hexes.</summary>
    public double Pitch => Size * Sqrt3;

    private Vec2 LocalToWorld(Vec2 local)
        => (RotationRadians == 0 ? local : local.Rotated(RotationRadians)) + Origin;

    private Vec2 WorldToLocal(Vec2 world)
    {
        var p = world - Origin;
        return RotationRadians == 0 ? p : p.Rotated(-RotationRadians);
    }

    private Vec2 LocalCenter(Hex hex)
        => new(Size * 1.5 * hex.Q, Size * Sqrt3 * (hex.Q * 0.5 + hex.R));

    /// <summary>World position of a hex centre.</summary>
    public Vec2 Center(Hex hex) => LocalToWorld(LocalCenter(hex));

    /// <summary>World position of a grid corner.</summary>
    public Vec2 Position(HexVertex vertex)
    {
        var center = LocalCenter(new Hex(vertex.Q, vertex.R));
        var offset = vertex.Pole == VertexPole.East ? new Vec2(Size, 0) : new Vec2(-Size, 0);
        return LocalToWorld(center + offset);
    }

    /// <summary>World position of a hex's corner by index (0 = due east, counter-clockwise).</summary>
    public Vec2 Corner(Hex hex, int index) => Position(hex.Corner(index));

    /// <summary>The six corners of a hex in counter-clockwise order, starting due east.</summary>
    public Vec2[] Corners(Hex hex)
    {
        var result = new Vec2[6];
        for (var i = 0; i < 6; i++) result[i] = Corner(hex, i);
        return result;
    }

    /// <summary>Midpoint of the side facing <paramref name="direction"/>.</summary>
    public Vec2 SideMidpoint(Hex hex, HexDirection direction)
    {
        var (a, b) = direction.Corners();
        return (Corner(hex, a) + Corner(hex, b)) * 0.5;
    }

    /// <summary>The hex containing a world position.</summary>
    public Hex HexAt(Vec2 world) => FractionalHexAt(world).Round();

    /// <summary>Continuous hex coordinate of a world position, before rounding.</summary>
    public FractionalHex FractionalHexAt(Vec2 world)
    {
        var p = WorldToLocal(world);
        var q = (2.0 / 3.0) * p.X / Size;
        var r = (-1.0 / 3.0 * p.X + (Sqrt3 / 3.0) * p.Y) / Size;
        return new FractionalHex(q, r);
    }
}
