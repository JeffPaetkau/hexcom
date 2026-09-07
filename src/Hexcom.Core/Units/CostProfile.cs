namespace Hexcom.Core.Units;

/// <summary>
/// What one soldier pays for things, as multipliers on the shared price list.
/// </summary>
/// <remarks>
/// The price list in <c>MovementCosts</c> and on <c>FireMode</c> describes the world: a ladder is
/// a ladder and a snap shot is a snap shot. What a <em>particular</em> soldier pays for one is a
/// question about them — their training, their kit, how much of it they are carrying — and it
/// belongs here rather than in the terrain.
/// <para>
/// This is what lets a scout and a heavy trooper spend the same ten points on different things.
/// It is also where gear hangs: a stabilised mount that takes a standard shot from five points to
/// four is a firing multiplier on the wearer, not a change to what a standard shot is.
/// </para>
/// <para>
/// Cost is time inside a reaction window, so these multipliers are not only an economy. A soldier
/// who fires slowly places its reactions later on the mover's timeline and catches them further
/// along the route, which is a real consequence of being the slow one.
/// </para>
/// </remarks>
public sealed record CostProfile
{
    public static readonly CostProfile Default = new();

    /// <summary>Quick over ground, slow to bring a weapon to bear.</summary>
    public static readonly CostProfile Scout = new() { Movement = 0.8, Firing = 1.4 };

    /// <summary>Ponderous, and fast on the trigger once planted.</summary>
    public static readonly CostProfile Gunner = new() { Movement = 1.5, Firing = 0.8 };

    /// <summary>Multiplier on what every traversal costs this soldier.</summary>
    public double Movement { get; init; } = 1.0;

    /// <summary>Multiplier on what every way of firing costs this soldier.</summary>
    public double Firing { get; init; } = 1.0;

    /// <param name="situational">
    /// Anything about the moment rather than the soldier — carrying yourself low, most obviously.
    /// Folded in before rounding, so a crouching scout is not rounded twice.
    /// </param>
    public int Move(int listed, double situational = 1.0) => Scale(listed, Movement * situational);

    public int Fire(int listed) => Scale(listed, Firing);

    /// <summary>
    /// Nothing free, nothing fractional.
    /// </summary>
    /// <remarks>
    /// The floor of one is where the current turn size shows its limits. A walk is priced at a
    /// single point, so no multiplier can make one cheaper, and a soldier who genuinely covers
    /// twice the ground per point cannot be expressed until the turn carries more resolution
    /// than ten. That is a reason to revisit the turn size, not a reason to allow half points.
    /// </remarks>
    private static int Scale(int listed, double factor)
        => listed <= 0
            ? listed
            : Math.Max(1, (int)Math.Round(listed * factor, MidpointRounding.AwayFromZero));
}
