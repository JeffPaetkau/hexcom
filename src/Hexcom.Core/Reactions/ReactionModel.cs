namespace Hexcom.Core.Reactions;

/// <summary>
/// The dials on reacting out of turn. All balance, no structure.
/// </summary>
/// <remarks>
/// How much of an unspent turn carries into the reserve is the difficulty setting, and it
/// applies to both sides. Turned up, the whole battlefield is twitchier: every mistake gets
/// answered and committing to a move becomes frightening. Turned down, turns feel more like
/// turns. It changes the texture of the game rather than handing the player a handicap.
/// </remarks>
public sealed record ReactionModel
{
    public static readonly ReactionModel Default = new();

    /// <summary>Everything left over banks. Every mistake gets answered.</summary>
    public static readonly ReactionModel Twitchy = new() { ReserveFraction = 1.0 };

    /// <summary>Almost nothing banks. Turns feel like turns.</summary>
    public static readonly ReactionModel Deliberate = new() { ReserveFraction = 0.3 };

    /// <summary>
    /// Share of the points a unit did not spend that carries into its reaction reserve.
    /// </summary>
    /// <remarks>
    /// A share rather than a fixed number, so it scales with whatever allowance a unit actually
    /// has. That matters: the ten point turn is provisional, and the allowance is expected to
    /// vary by soldier once stats, training and kit feed into it. Nothing here assumes ten.
    /// <para>
    /// What <em>is</em> calibrated is the shape. Seven tenths puts the three rungs of the
    /// movement economy — hold everything, spend about half, spend it all — on either side of
    /// the fire mode prices, so each one is a real decision about what can still be answered
    /// with rather than a rounding accident. Against a ten point turn that lands exactly: seven
    /// banked is an aimed shot, three is a snap shot, and a sprint banks nothing. If the turn
    /// size moves, this is the dial that moves with it.
    /// </para>
    /// <para>
    /// The lever to watch is that fire mode prices are absolute while the allowance is not. A
    /// unit given more points does not merely move further; it banks a larger reserve and can
    /// afford better shots out of it. Whether that compounding is the reward a fast soldier
    /// should get is a balance question for whenever the allowance stops being a flat ten.
    /// </para>
    /// </remarks>
    public double ReserveFraction { get; init; } = 0.7;

    /// <summary>
    /// Below this, a leftover is rounded away rather than banked.
    /// </summary>
    /// <remarks>
    /// A cut for noise, not the price of any particular action. One or two points is never
    /// enough to do anything with, and carrying it around invites the interface to offer
    /// choices that are not really choices.
    /// </remarks>
    public int ReserveFloor { get; init; } = 2;

    /// <summary>
    /// What declaring an overwatch costs, on top of the shot being held back.
    /// </summary>
    /// <remarks>
    /// Deliberately small. The real price of overwatching is the whole rest of the turn spent
    /// not advancing, and charging much for the declaration on top of that would make holding
    /// an arc strictly worse than simply keeping points in hand.
    /// </remarks>
    public int OverwatchCost { get; init; } = 1;
}
