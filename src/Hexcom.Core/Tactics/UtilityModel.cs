using Hexcom.Core.Awareness;

namespace Hexcom.Core.Tactics;

/// <summary>
/// The exchange rates a judgement is made at. All balance, no structure.
/// </summary>
/// <remarks>
/// <b>Everything here is denominated in vitality</b>, because vitality is the only thing in the
/// game that ends a fight. A score is not an abstract number between nought and one; it is an
/// answer to "how many points of soldier is this worth", and every dial below exists to turn
/// something that is not vitality — a point of action, a plate worn through, a contact passed on
/// — into vitality so that it can be compared with something that is.
/// <para>
/// That choice is what makes the scorer usable inside a reaction window, where the currency is
/// already fixed. A window runs on action points and an action point is a tick of the mover's
/// timeline, so a ranking that could not price a point against a wound would have nothing to say
/// about the one decision the window actually poses: a cheap poor shot now against a good slow
/// one that arrives after they reach cover.
/// </para>
/// <para>
/// <b>Every figure below is an argument rather than a measurement</b>, like every other number in
/// this game. Unlike the others, these are the ones the AI-versus-AI runs will actually be able
/// to test, because a scorer that plays badly loses matches and says so.
/// </para>
/// </remarks>
public sealed record UtilityModel
{
    public static readonly UtilityModel Default = new();

    /// <summary>
    /// What one action point is worth, in vitality.
    /// </summary>
    /// <remarks>
    /// The opportunity cost of spending, not the value of a point at the trigger. A soldier who
    /// spends a whole turn shooting well converts fifty points into something on the order of
    /// five or six points of vitality once shields and plate have taken their cut, which is about
    /// a tenth of a point each — but most of the points this prices are reserve, and most reserve
    /// is never spent on anything, because a soldier answers about one move a round. Halving for
    /// that gives the figure here.
    /// <para>
    /// It is deliberately small. Inside a window there is usually nothing else to do with the
    /// points, so cost should break ties between comparable options and never beat a real gain:
    /// at this rate the twenty points between a snap shot and an aimed one are worth a single
    /// point of vitality, which is enough to prefer the cheap shot when they are otherwise level
    /// and nowhere near enough to prefer it when the slow one lands and the quick one does not.
    /// </para>
    /// </remarks>
    public double PointValue { get; init; } = 0.05;

    /// <summary>
    /// What a point of ablative plate worn off is worth, against a point of vitality.
    /// </summary>
    /// <remarks>
    /// Plate does not come back, so stripping it is vitality banked rather than vitality wasted.
    /// This matters more than it sounds: a slug rifle against a fresh face puts eight of its
    /// eleven points into the plate and one into the soldier, so a scorer that counted only
    /// vitality would rate the opening exchanges of every firefight at close to nothing and
    /// prefer almost any posture to shooting. Wearing the armour off <em>is</em> the work.
    /// <para>
    /// Half rather than the whole, because it is only worth what somebody eventually collects,
    /// and the same face has to be presented again for that to happen.
    /// </para>
    /// </remarks>
    public double PlateValue { get; init; } = 0.5;

    /// <summary>
    /// What a point of force shield soaked is worth, against a point of vitality.
    /// </summary>
    /// <remarks>
    /// Nearly nothing, and for the opposite reason to plate: shields recharge every turn, so a
    /// face stripped now is a face restored shortly. What keeps it above zero is the volley and
    /// the ambush — inside one window, or one round of focused fire, the second shot really does
    /// walk through the hole the first made, and a scorer that valued the first at nothing would
    /// never set that up.
    /// </remarks>
    public double ShieldValue { get; init; } = 0.15;

    /// <summary>
    /// What putting a soldier down is worth, as a multiple of the vitality they started with,
    /// over and above the damage that did it.
    /// </summary>
    /// <remarks>
    /// One whole soldier again. Everything they would have done for the rest of the fight goes
    /// with them, and that is worth at least what it took to get them there — which is also what
    /// makes focused fire beat spread fire without anybody having to write down a rule saying so.
    /// The last two points of a wounded man are worth as much as the first eighteen were.
    /// <para>
    /// Measured against the target's own starting vitality rather than a flat number, so a
    /// tougher soldier is worth more to remove without anything having to be said about tiers.
    /// <b>Open:</b> nothing here yet says that the signaller is worth more than the rifleman
    /// standing next to them, and it plainly is. Weighting removal by what the soldier does for
    /// its side — carrying the net, holding the only arc that covers the door — is the obvious
    /// next thing this wants and is not yet derived from anything.
    /// </para>
    /// </remarks>
    public double RemovalBonus { get; init; } = 1.0;

    /// <summary>
    /// What a thing worth doing next round is worth now.
    /// </summary>
    /// <remarks>
    /// Applied to everything that is not this instant: damage kept off you by how you are left
    /// standing, a shot your own turn now opens, a shot you handed somebody by calling a contact
    /// in. A third, because between now and then the other side gets a turn, the threat may not
    /// shoot at you at all, and the ground will have moved.
    /// <para>
    /// It is the single dial that decides how much of a coward the AI is. Turned up, soldiers
    /// dive for cover at every noise; turned down, they trade shots and never posture. It is also
    /// the first thing to reach for if the reaction window starts producing behaviour that looks
    /// timid rather than careful.
    /// </para>
    /// </remarks>
    public double FutureDiscount { get; init; } = 0.35;

    /// <summary>
    /// What a remembered position is worth, per round it goes unconfirmed past the fresh ones,
    /// as a share of what it was worth the round before.
    /// </summary>
    /// <remarks>
    /// A marker is where somebody was when contact was last made, and it is right until they
    /// move, which they do on their own turn. This is the chance they did not. A half, because a
    /// soldier who has stayed put through one whole turn — a sentry, a man in cover, somebody who
    /// has just fired and is watching for the answer — is about as likely as not to stay through
    /// the next, and there is nothing yet to say which kind of soldier the marker belongs to.
    /// Applied by <see cref="Tactician.Credence"/>, which says which rounds count as fresh and
    /// why; the argument for the shape of the curve is there too.
    /// <para>
    /// Turned up, the AI walks to old news and finds nobody; turned down, it forgets a contact
    /// the moment it loses the line and never goes round the corner. It is the dial to reach for
    /// when a unit either chases ghosts or gives up the hunt too soon.
    /// </para>
    /// </remarks>
    public double MarkerDecay { get; init; } = 0.5;

    /// <summary>
    /// What having a charge still on your belt is worth, in vitality.
    /// </summary>
    /// <remarks>
    /// The first thing in this game that runs out, and therefore the first thing whose
    /// <em>opportunity</em> cost has to be written down. Points come back every turn and shields
    /// recharge; a grenade thrown is gone, and a scorer that priced only the action points would
    /// throw both of them at the first soldier it saw. It measurably did.
    /// <para>
    /// Set at about what one clean rifle shot achieves in this economy. That is the figure that
    /// makes the distinction the design wants: against a soldier standing in the open a rifle is
    /// nearly as good and costs nothing, so the charge stays on the belt; against one behind a
    /// wall the rifle is worth nothing at all, so it comes off. A grenade is for the shot you
    /// cannot take, and this number and no rule is what says so.
    /// </para>
    /// <para>
    /// What it does not model is that the <em>last</em> one should be dearer than the first, and
    /// that a charge you carry out of the fight was worth nothing. Both are real and both need a
    /// notion of how much fight is left, which nothing here has.
    /// </para>
    /// </remarks>
    public double ChargeValue { get; init; } = 3.5;

    /// <summary>
    /// What a point of damage done to your own side is worth, against a point done to theirs.
    /// </summary>
    /// <remarks>
    /// One, and symmetry is the honest default rather than a failure to think about it: a point
    /// of soldier is a point of soldier, and the arithmetic already knows that hurting one of
    /// yours gains you none of the enemy. Nothing in the game could tell the difference until
    /// something could catch both sides at once, which is what a blast radius is and what nothing
    /// before it was.
    /// <para>
    /// It is the dial to turn up the moment a commander starts making trades a squad would not:
    /// at one, a grenade that takes one and a bit off them and one off you scores positive, and
    /// whether that is a decision or a bug is a question only matches can answer. Turned up, it
    /// is the difference between troops who will accept casualties and troops who will not.
    /// </para>
    /// </remarks>
    public double FriendlyHarm { get; init; } = 1.0;

    /// <summary>
    /// How sure somebody has to be before a shot they could take counts as a shot they will take.
    /// </summary>
    /// <remarks>
    /// The bar an ally has to be carried over for telling them to be worth anything, and it is
    /// the same bar the reaction model already makes a watchman clear before it will fire down
    /// its own arc — because it is the same question. Shouting at somebody who already knows buys
    /// nothing, and shouting at somebody the news will not carry far enough to move buys nothing
    /// either.
    /// </remarks>
    public AwarenessState ActsOn { get; init; } = AwarenessState.Searching;
}
