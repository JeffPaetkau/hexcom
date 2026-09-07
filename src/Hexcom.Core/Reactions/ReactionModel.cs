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
    /// has. That matters, because the allowance is expected to vary by soldier once stats,
    /// training and kit feed into it. Nothing here may assume the standard fifty.
    /// <para>
    /// What <em>is</em> calibrated is the shape. Seven tenths puts the three rungs of the
    /// movement economy — hold everything, spend about half, spend it all — on either side of
    /// the fire mode prices, so each one is a real decision about what can still be answered
    /// with rather than a rounding accident. Against a fifty point turn it lands exactly: thirty
    /// five banked is an aimed shot, seventeen covers a snap shot with change, and a sprint banks
    /// nothing. If the turn size moves again, this is the dial that moves with it.
    /// </para>
    /// <para>
    /// The lever to watch is that fire mode prices are absolute while the allowance is not. A
    /// unit given more points does not merely move further; it banks a larger reserve and can
    /// afford better shots out of it. Whether that compounding is the reward a fast soldier
    /// should get is a balance question for whenever allowances start to differ in earnest.
    /// </para>
    /// </remarks>
    public double ReserveFraction { get; init; } = 0.7;

    /// <summary>
    /// Below this, a leftover is rounded away rather than banked.
    /// </summary>
    /// <remarks>
    /// A cut for noise, not the price of any particular action. Anything under a couple of
    /// strides is never enough to do something with, and carrying it around invites the interface
    /// to offer choices that are not really choices.
    /// </remarks>
    public int ReserveFloor { get; init; } = 10;

    /// <summary>
    /// What declaring an overwatch costs, on top of the shot being held back.
    /// </summary>
    /// <remarks>
    /// Deliberately small. The real price of overwatching is the whole rest of the turn spent
    /// not advancing, and charging much for the declaration on top of that would make holding
    /// an arc strictly worse than simply keeping points in hand.
    /// </remarks>
    public int OverwatchCost { get; init; } = 5;

    /// <summary>
    /// How sure a watchman has to be about somebody before it will fire down its arc.
    /// </summary>
    /// <remarks>
    /// Without this the trigger is purely geometric and a watchman shoots at anything it could
    /// technically see — including a prone crawler at forty metres with four per cent of itself
    /// showing, which the detection model says it has not noticed at all. Overwatch was the one
    /// place in the game where something happened to a hidden soldier without the awareness
    /// ladder being consulted. Now it is not.
    /// </remarks>
    public Awareness.AwarenessState OverwatchRequires { get; init; } = Awareness.AwarenessState.Searching;

    /// <summary>
    /// Whether holding an arc lets a watchman notice what crosses it, outside its own turn.
    /// </summary>
    /// <remarks>
    /// This is what stops the gate above from gutting overwatch. Looking normally happens only
    /// on your own turn, so a soldier who was behind a building when the sentry last looked
    /// could step out into a watched arc and cross it untouched — the canonical overwatch
    /// situation, defeated by the turn order. Watching a piece of ground is precisely the act of
    /// looking at it, so the crossing gets a detection check at the tick it happens, through the
    /// ordinary model: stance, cover, range, exposure and perception all still decide whether it
    /// registers. A careful approach still gets through. A jog across the open does not.
    /// <para>
    /// Turn this off and the gate becomes a pure test of what the watchman already knew, which
    /// is a real design position — just a much weaker overwatch.
    /// </para>
    /// <para>
    /// <b>Settled on reasoning, not on play.</b> This and <see cref="OverwatchRequires"/> are the
    /// two dials to reach for first when overwatch feels wrong in testing: too strong and the
    /// free look is the suspect, too weak and the gate is. Neither has been tried against an
    /// actual fight yet.
    /// </para>
    /// </remarks>
    public bool OverwatchLooks { get; init; } = true;
}
