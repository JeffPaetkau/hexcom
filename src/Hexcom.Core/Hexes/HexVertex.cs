using System.Collections.Generic;

namespace Hexcom.Core.Hexes;

/// <summary>Which of a hex's two "owned" corners a <see cref="HexVertex"/> refers to.</summary>
public enum VertexPole
{
    /// <summary>The corner due east of the hex centre (corner index 0).</summary>
    East = 0,

    /// <summary>The corner due west of the hex centre (corner index 3).</summary>
    West = 1,
}

/// <summary>
/// A corner of the hex grid, named canonically.
/// </summary>
/// <remarks>
/// Every corner is shared by exactly three hexes, and a hex has six corners, so there are
/// exactly two corners per hex. In a flat-top layout the natural owners are the due-east and
/// due-west corners: every corner in the plane is the east corner of exactly one hex or the
/// west corner of exactly one hex, never both. Naming corners this way means the same physical
/// corner produces the same <see cref="HexVertex"/> whichever of its three hexes you ask
/// through, which is what lets walls live on a single global corner graph instead of being
/// duplicated per tile.
/// <para>
/// Each corner connects to twelve others: three along hex sides (the honeycomb lattice) and
/// nine interior chords, three in each of the three hexes it touches.
/// </para>
/// </remarks>
public readonly record struct HexVertex(int Q, int R, VertexPole Pole)
{
    /// <summary>The hex that owns this corner, and the corner index on it (0 for east, 3 for west).</summary>
    public (Hex Hex, int CornerIndex) Owner => (new Hex(Q, R), Pole == VertexPole.East ? 0 : 3);

    /// <summary>
    /// The three hexes that meet at this corner, each paired with the corner index this
    /// vertex occupies on that hex.
    /// </summary>
    public IEnumerable<(Hex Hex, int CornerIndex)> IncidentCorners()
    {
        if (Pole == VertexPole.East)
        {
            yield return (new Hex(Q, R), 0);
            yield return (new Hex(Q + 1, R - 1), 2);
            yield return (new Hex(Q + 1, R), 4);
        }
        else
        {
            yield return (new Hex(Q, R), 3);
            yield return (new Hex(Q - 1, R), 1);
            yield return (new Hex(Q - 1, R + 1), 5);
        }
    }

    /// <summary>The three hexes that meet at this corner.</summary>
    public IEnumerable<Hex> IncidentHexes()
    {
        foreach (var (hex, _) in IncidentCorners()) yield return hex;
    }

    /// <summary>
    /// The hexes in which both corners are present — i.e. the hexes a wall between them could
    /// belong to. Adjacent corners share two hexes (the wall is a hex side); chord pairs share one.
    /// </summary>
    public IEnumerable<Hex> SharedHexesWith(HexVertex other)
    {
        foreach (var hex in IncidentHexes())
            if (hex.CornerIndexOf(other) >= 0)
                yield return hex;
    }

    public override string ToString() => $"V({Q},{R},{(Pole == VertexPole.East ? "E" : "W")})";
}
