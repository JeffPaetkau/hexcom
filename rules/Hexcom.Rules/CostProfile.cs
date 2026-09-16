using System;

namespace Hexcom.Rules;

/// <summary>What one soldier pays for things, as multipliers on the shared price list.</summary>
/// <remarks>
/// <para>
/// The price list in <see cref="MovementCosts"/> describes the world: a road is a road and a
/// slope is a slope. What a particular soldier pays to cross one is a question about them,
/// their training and what they are carrying, and it belongs here rather than in the ground.
/// It is what lets a scout and a heavy trooper spend the same fifty points on different things.
/// </para>
/// <para>
/// Only movement is priced yet. Firing and posture will get their own dials when they exist,
/// so a scout can be quick on their feet and slow to bring a weapon to bear.
/// </para>
/// </remarks>
public sealed record CostProfile
{
    public static readonly CostProfile Default = new();

    /// <summary>Quick over ground.</summary>
    public static readonly CostProfile Scout = new() { Movement = 0.8 };

    /// <summary>Ponderous.</summary>
    public static readonly CostProfile Gunner = new() { Movement = 1.5 };

    /// <summary>Multiplier on what every step costs this soldier.</summary>
    public double Movement { get; init; } = 1.0;

    /// <summary>What a step at a listed price costs this soldier: nothing free, nothing fractional.</summary>
    /// <remarks>
    /// The listed price arrives unrounded, surface and slope already summed, so the soldier's
    /// multiplier and the ground's are rounded once together rather than twice apart. The floor
    /// of one is the turn's resolution showing: no multiplier can make a step free.
    /// </remarks>
    public int Move(double listed)
        => Math.Max(1, (int)Math.Round(listed * Movement, MidpointRounding.AwayFromZero));
}
