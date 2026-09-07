using System.Collections.Generic;
using Hexcom.Core.Battles;
using Hexcom.Core.Geometry;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;

namespace Hexcom.Core.Reactions;

/// <summary>
/// How much ground an overwatch tries to cover, and what that costs in accuracy.
/// </summary>
/// <remarks>
/// The whole decision overwatch offers. A narrow arc is a weapon already pointed at one
/// approach and shoots very well down it; a wide one is a soldier turning their head, and buys
/// little more than not being surprised. Neither dominates, because the mover chooses the
/// approach and the watchman has to guess it.
/// <para>
/// The bonus multiplies hit chance rather than adding to it, so it is worth most where a shot
/// was already plausible. Overwatching a target that is barely visible does not turn a hopeless
/// shot into a good one.
/// </para>
/// </remarks>
/// <param name="Degrees">Total width of the watched arc, centred on the declared bearing.</param>
public sealed record OverwatchArc(string Name, double Degrees, double AimBonus)
{
    /// <summary>One approach, watched properly.</summary>
    public static readonly OverwatchArc Narrow = new("narrow", 60, 1.35);

    /// <summary>The arc a unit is normally attending to anyway.</summary>
    public static readonly OverwatchArc Standard = new("standard", 120, 1.18);

    /// <summary>Most of the ground in front, and not much of a shot down any of it.</summary>
    public static readonly OverwatchArc Wide = new("wide", 180, 1.05);

    public static readonly IReadOnlyList<OverwatchArc> All = [Narrow, Standard, Wide];

    public double HalfWidthDegrees => Degrees / 2;

    public override string ToString() => $"{Name} ({Degrees:0} deg, x{AimBonus:0.00})";
}

/// <summary>
/// A watchman holding an arc: anything hostile that moves inside it gets shot at.
/// </summary>
/// <remarks>
/// This is where facing earns its keep twice. The arc a unit watches is the same arc it
/// notices things in, so an overwatch position is also a detection position — and walking round
/// behind it defeats both at once, which is the same walk that buys the thin side of the
/// armour.
/// </remarks>
public readonly record struct OverwatchOrder(HexDirection Centre, OverwatchArc Arc)
{
    /// <summary>Whether a place falls inside the watched arc, seen from <paramref name="from"/>.</summary>
    /// <remarks>
    /// The edge is exclusive and it is decided the same way the attention cones decide theirs —
    /// see <see cref="Geometry2D.AngleEpsilonDegrees"/>. A standard arc held toward one spoke
    /// therefore does not reach the next spoke over: cover that ground and you declare a wider
    /// arc, and shoot worse down all of it.
    /// </remarks>
    public bool Covers(Battle battle, NodeId from, NodeId place)
        => battle.AngleOffDegrees(from, Centre, place) + Geometry2D.AngleEpsilonDegrees
           <= Arc.HalfWidthDegrees;

    public override string ToString() => $"watching {Centre}, {Arc}";
}
