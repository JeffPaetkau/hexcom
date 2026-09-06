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
    /// Seven tenths is chosen against the ten point turn. Stand still and seven bank, which is
    /// exactly an aimed shot. Spend half the turn getting somewhere and three bank, which is
    /// exactly a snap shot. Sprint the whole ten and nothing banks at all. Every rung of the
    /// movement economy therefore lands on a real choice about what can still be answered with,
    /// and the choice is made before you know whether it will pay.
    /// <para>
    /// Declaring an overwatch costs a point out of the same turn, so a watchman banks six and
    /// can never take an aimed shot off an arc. That is deliberate: overwatch pays in the aim
    /// bonus rather than in aiming time, which is what makes it land early in the window.
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
