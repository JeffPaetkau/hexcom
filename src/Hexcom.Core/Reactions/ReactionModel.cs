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

    /// <summary>
    /// Share of the reserve a unit may spend on a reaction it never planned for.
    /// </summary>
    /// <remarks>
    /// Less than a deliberate one, because reacting is not planning. Half of a watchman's bank is
    /// still a snap shot, which is the point: catching a competent soldier with <em>nothing</em>
    /// in hand ought to take more than walking up to them. Walking round the back deserves the
    /// reward; proximity on its own does not.
    /// </remarks>
    public double SurpriseFraction { get; init; } = 0.5;

    /// <summary>
    /// How far a contact has to climb before somebody reacts to suddenly registering it.
    /// </summary>
    /// <remarks>
    /// A lower bar than an overwatch has to clear, because a flinch is not a considered shot. You
    /// duck at something registering without yet knowing quite what it is, and surprise is the
    /// reaction nobody plans for. It also has to be reachable from the corner of an eye, where a
    /// look is worth under half of what one straight ahead is worth — set any higher and being
    /// startled by something off to the side becomes impossible, which is the one case where
    /// turning to face it is worth an action.
    /// <para>
    /// What matters is <em>crossing</em> this bar, not merely rising. The moment it clicks, once
    /// per opponent. Somebody already being tracked climbing from searching to alerted is not a
    /// surprise, which is what stops a firefight throwing one of these for every move made.
    /// </para>
    /// </remarks>
    public Awareness.AwarenessState SurpriseRequires { get; init; } = Awareness.AwarenessState.Suspicious;

    /// <summary>
    /// How sure you have to be before a surprise reaction is allowed to be a <em>shot</em>.
    /// </summary>
    /// <remarks>
    /// Higher than the bar for reacting at all, and that gap is where most of the character of
    /// surprise lives. Something registering at the edge of what you can make out is enough to
    /// make you duck or spin round; it is nowhere near enough to shoot at, and a soldier who
    /// blazes away at every half-seen shape is not a competent one.
    /// <para>
    /// It also keeps the careful approach worth playing. A crawler at forty metres will make a
    /// sentry twitch, and will not draw fire for it.
    /// </para>
    /// </remarks>
    public Awareness.AwarenessState SurpriseFireRequires { get; init; } = Awareness.AwarenessState.Searching;

    /// <summary>
    /// The beat it takes to register something and start doing anything about it.
    /// </summary>
    /// <remarks>
    /// The mechanical difference between a weapon already pointed and one that is not. An
    /// overwatch starts its action at the top of the window; a surprise starts this much after
    /// the moment of noticing, so the same snap shot from the same soldier lands later and
    /// catches the mover further along a route it is already committed to.
    /// <para>
    /// Without it, declaring an arc buys only the aiming bonus and the fuller purse, and the
    /// design's claim that overwatch is strong because it <em>lands early</em> is not expressed
    /// anywhere. A stride's worth is enough to matter without being a whole action.
    /// </para>
    /// </remarks>
    public int SurpriseDelay { get; init; } = 5;

    /// <summary>Whether the involuntary reaction exists at all. Off makes the game much quieter.</summary>
    public bool Surprise { get; init; } = true;

    /// <summary>
    /// What calling a contact in costs. Cheap: it is the thing you do when nothing else is worth
    /// doing, and a reaction nobody can afford is not a reaction.
    /// </summary>
    /// <remarks>
    /// Lives here rather than on the movement price list because shouting is only a reaction so
    /// far. It moves across the moment somebody can do it on their own turn.
    /// </remarks>
    public int ShoutCost { get; init; } = 2;

    /// <summary>
    /// What arming against an agreed trigger costs, on top of the shot being held back.
    /// </summary>
    /// <remarks>
    /// Dearer than declaring an overwatch, because an ambush buys more: not a shot you take on
    /// your own but a shot the whole squad takes together, before the other side answers any of
    /// it. Paid up front by every member, so setting one is several turns spent not advancing —
    /// and if you spring it early, or wait until half of them have had their turn back and lost
    /// their reserve, you paid for coordination you did not get.
    /// </remarks>
    public int AmbushCost { get; init; } = 10;
}
