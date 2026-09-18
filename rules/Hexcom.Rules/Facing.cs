using System;

namespace Hexcom.Rules;

/// <summary>
/// Which way a soldier faces: one of the six hex directions, the one their front is towards.
/// </summary>
/// <remarks>
/// <para>
/// Six rather than any angle because the hex grid already has six directions and everything
/// that will ask about facing asks per hex: which neighbours are in front, which hexes a look
/// reaches, which side a shot arrives at. A facing is the index of a <see cref="Hex.Directions"/>
/// entry, so a soldier facing <c>d</c> is looking straight at <c>Position.Neighbour(d)</c>, and
/// the bearing is thirty degrees plus sixty per step, measured from +X towards +Z, so that
/// direction four is north, up the -Z axis.
/// </para>
/// <para>
/// Facing is set by moving, since a soldier arrives facing the way they came, and by shooting,
/// since a soldier faces what they fire at, and otherwise by turning on the spot, which is
/// priced by the sixths turned through (<see cref="MovementCosts.TurnPerSixth"/>). It matters
/// for nothing yet but the picture; perception, the next thing, reads it for where a soldier is
/// looking.
/// </para>
/// </remarks>
public static class Facing
{
    /// <summary>How many directions there are.</summary>
    public const int Count = 6;

    private static readonly string[] Names = { "SE", "S", "SW", "NW", "N", "NE" };

    /// <summary>The compass name of a direction, north being -Z.</summary>
    public static string Name(int direction) => Names[Wrap(direction)];

    /// <summary>The bearing of a direction in degrees from +X towards +Z: thirty plus sixty a step.</summary>
    public static double BearingDegrees(int direction) => 30 + 60 * Wrap(direction);

    /// <summary>The bearing of a direction in radians from +X towards +Z.</summary>
    public static double BearingRadians(int direction) => BearingDegrees(direction) * Math.PI / 180;

    /// <summary>
    /// The direction from one hex nearest to another: the one a soldier on the first would turn
    /// to in order to face the second. Null when the two are the same hex, which faces no way.
    /// </summary>
    public static int? Toward(Hex from, Hex to)
    {
        if (from == to) return null;

        var (x0, z0) = from.Centre;
        var (x1, z1) = to.Centre;
        var degrees = Math.Atan2(z1 - z0, x1 - x0) * 180 / Math.PI;
        return Wrap((int)Math.Round((degrees - 30) / 60));
    }

    /// <summary>The fewest sixths of a turn between two directions, either way round: nothing up to three, an about-face.</summary>
    public static int Steps(int from, int to)
    {
        var apart = Math.Abs(Wrap(from) - Wrap(to));
        return Math.Min(apart, Count - apart);
    }

    private static int Wrap(int direction) => ((direction % Count) + Count) % Count;
}
