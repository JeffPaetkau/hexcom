namespace Hexcom.Core.Hexes;

/// <summary>
/// The six neighbour directions of a hex, ordered counter-clockwise starting at 30 degrees.
/// </summary>
/// <remarks>
/// The core works in <b>flat-top</b> hex space. Direction <c>i</c> points at bearing
/// <c>30 + 60*i</c> degrees, and — importantly — side <c>i</c> of a hex is bounded by
/// corners <c>i</c> and <c>i+1</c>. That one-to-one relationship between direction index and
/// corner index is why the directions are ordered counter-clockwise rather than in the more
/// commonly published clockwise order; it removes a whole class of off-by-one bugs from the
/// wall and cover code.
/// <para>
/// Compass names assume +Y is north. The view layer is free to flip or rotate.
/// </para>
/// </remarks>
public enum HexDirection
{
    NorthEast = 0,
    North = 1,
    NorthWest = 2,
    SouthWest = 3,
    South = 4,
    SouthEast = 5,
}

public static class HexDirectionExtensions
{
    /// <summary>Axial offsets, indexed by <see cref="HexDirection"/>.</summary>
    internal static readonly Hex[] Offsets =
    [
        new(1, 0),   // NE, 30 deg
        new(0, 1),   // N,  90 deg
        new(-1, 1),  // NW, 150 deg
        new(-1, 0),  // SW, 210 deg
        new(0, -1),  // S,  270 deg
        new(1, -1),  // SE, 330 deg
    ];

    public static readonly HexDirection[] All =
    [
        HexDirection.NorthEast, HexDirection.North, HexDirection.NorthWest,
        HexDirection.SouthWest, HexDirection.South, HexDirection.SouthEast,
    ];

    /// <summary>The direction pointing the opposite way.</summary>
    public static HexDirection Opposite(this HexDirection d) => (HexDirection)(((int)d + 3) % 6);

    /// <summary>Rotate <paramref name="steps"/> sixths counter-clockwise (negative for clockwise).</summary>
    public static HexDirection Rotate(this HexDirection d, int steps)
        => (HexDirection)(((((int)d + steps) % 6) + 6) % 6);

    /// <summary>The axial offset for this direction.</summary>
    public static Hex Offset(this HexDirection d) => Offsets[(int)d];

    /// <summary>
    /// The two corner indices bounding the side that faces <paramref name="d"/>, in
    /// counter-clockwise order. Side <c>i</c> is always bounded by corners <c>i</c> and <c>i+1</c>.
    /// </summary>
    public static (int A, int B) Corners(this HexDirection d) => ((int)d, ((int)d + 1) % 6);

    /// <summary>Bearing of this direction in radians, for a flat-top layout with +Y north.</summary>
    public static double BearingRadians(this HexDirection d) => (Math.PI / 6.0) + (Math.PI / 3.0) * (int)d;
}
