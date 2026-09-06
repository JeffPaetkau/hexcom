using Hexcom.Core.Hexes;

namespace Hexcom.Core.Maps;

/// <summary>Where a wall segment sits relative to the hex it is inside.</summary>
public enum ChordClass
{
    /// <summary>Adjacent corners: the segment is a hex side, shared with the neighbouring hex.</summary>
    Side = 1,

    /// <summary>Corners two apart: cuts a sixth off the hex, leaving a large standable region.</summary>
    Minor = 2,

    /// <summary>Opposite corners: splits the hex in half. Neither half is roomy enough to stand in.</summary>
    Bisector = 3,
}

/// <summary>
/// A piece of wall, railing, barricade or cover, drawn between two corners of the grid.
/// </summary>
/// <remarks>
/// Because a hex has six corners and each corner connects to the other five, a single hex can
/// carry fifteen distinct segments: six sides, six minor chords and three bisectors. That is
/// the whole cover vocabulary — a low wall running diagonally across a courtyard tile, a
/// sandbag line clipping one corner, or a building face along a tile edge are all the same
/// kind of object, differing only in which corners they join.
/// </remarks>
public readonly record struct WallSegment
{
    public WallSegment(HexVertex a, HexVertex b, int layer, WallProfile profile)
    {
        if (a == b) throw new ArgumentException("A wall segment needs two distinct corners.", nameof(b));

        // Store in a canonical order so (a,b) and (b,a) are the same wall.
        if (Compare(a, b) <= 0) { A = a; B = b; }
        else { A = b; B = a; }

        Layer = layer;
        Profile = profile;
    }

    public HexVertex A { get; }
    public HexVertex B { get; }

    /// <summary>Which vertical layer the segment belongs to.</summary>
    public int Layer { get; }

    public WallProfile Profile { get; }

    private static int Compare(HexVertex x, HexVertex y)
    {
        var c = x.Q.CompareTo(y.Q);
        if (c != 0) return c;
        c = x.R.CompareTo(y.R);
        if (c != 0) return c;
        return ((int)x.Pole).CompareTo((int)y.Pole);
    }

    /// <summary>
    /// How this segment sits inside <paramref name="hex"/>, or <c>null</c> if both of its
    /// corners are not corners of that hex.
    /// </summary>
    public ChordClass? ClassifyIn(Hex hex)
    {
        var ia = hex.CornerIndexOf(A);
        if (ia < 0) return null;
        var ib = hex.CornerIndexOf(B);
        if (ib < 0) return null;
        return Classify(ia, ib);
    }

    /// <summary>Classify a chord from its two local corner indices.</summary>
    public static ChordClass Classify(int cornerA, int cornerB)
    {
        var diff = Math.Abs(cornerA - cornerB) % 6;
        var separation = Math.Min(diff, 6 - diff);
        return separation switch
        {
            1 => ChordClass.Side,
            2 => ChordClass.Minor,
            3 => ChordClass.Bisector,
            _ => throw new ArgumentException($"Corners {cornerA} and {cornerB} do not form a chord."),
        };
    }

    /// <summary>
    /// If this segment is a hex side, the two hexes it separates and the direction from each.
    /// Returns <c>false</c> for interior chords, which sit inside a single hex.
    /// </summary>
    public bool TryAsSide(out Hex left, out HexDirection fromLeft)
    {
        left = default;
        fromLeft = default;

        foreach (var hex in A.SharedHexesWith(B))
        {
            var ia = hex.CornerIndexOf(A);
            var ib = hex.CornerIndexOf(B);
            if (Classify(ia, ib) != ChordClass.Side) return false;

            // Side i is bounded by corners i and i+1, so the lower index in cyclic order names it.
            var side = (ib == (ia + 1) % 6) ? ia : ib;
            left = hex;
            fromLeft = (HexDirection)side;
            return true;
        }

        return false;
    }

    public override string ToString() => $"{Profile.Id} {A}-{B} L{Layer}";
}
