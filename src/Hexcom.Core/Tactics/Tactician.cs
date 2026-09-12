using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Tactics;

/// <summary>
/// Somebody worth worrying about, where you think they are standing, and how far you trust it.
/// </summary>
/// <remarks>
/// The pose is carried separately because the soldier you are weighing up is frequently not
/// where the question is about. Inside a reaction window the mover is halfway along a route, and
/// what matters for how you stand is where it ends up, not where it is when you flinch.
/// <para>
/// A threat is a <b>belief</b>, not a fact, and the two extra fields say how good a belief it is.
/// <see cref="EyesOn"/> is true when the pose is where the soldier actually is, as far as the
/// believer can currently see; false when it is a marker — where they were when contact was
/// last made, which is wrong the moment they move. <see cref="Credence"/> is how much of what
/// the threat could do, or have done to it, to count: one for somebody in view, less for a
/// marker, and less again each round the marker goes without being confirmed. Every term in
/// <see cref="Tactician"/> that involves the threat is scaled by it, so a stale contact is worth
/// worrying about and worth going to look at, and not worth as much as a live one.
/// </para>
/// </remarks>
/// <param name="Credence">How much of this threat to count, from nothing to all of it.</param>
/// <param name="EyesOn">
/// Whether <paramref name="Where"/> is where they are, rather than where they were.
/// </param>
public readonly record struct Threat(Unit Unit, UnitPose Where, double Credence = 1.0, bool EyesOn = true)
{
    /// <summary>A threat in plain view, standing exactly where it is.</summary>
    public static Threat At(Unit unit) => new(unit, UnitPose.Of(unit));

    /// <summary>A threat remembered at a marker, standing however the believer imagines it.</summary>
    public static Threat Believed(Unit unit, UnitPose where, double credence) => new(unit, where, credence, EyesOn: false);

    public override string ToString()
        => EyesOn ? $"{Unit.Name} at {Where.Position}" : $"{Unit.Name} believed at {Where.Position} ({Credence:0.00})";
}

/// <summary>
/// What an action is worth, in vitality.
/// </summary>
/// <remarks>
/// The judgement the AI ranks by and the interface can show. There is one of these per battle and
/// both sides use it, which is deliberate: the moment the AI scores an option against something
/// the player cannot be shown, the interface is wrong and nobody finds out.
/// <para>
/// <b>It scores one action, and that is all it does.</b> What varies between an AI picking a
/// reaction and an AI taking a turn is which candidates get generated and how they are chained
/// together, not what any of them is worth — a snap shot at somebody crossing your arc is worth
/// what it is worth whether the points come out of a reserve or an allowance. So the search
/// lives with whatever is doing the searching, and the arithmetic lives here, once.
/// </para>
/// <para>
/// <b>It reads only what its soldier knows.</b> Threats are drawn from that unit's own contact
/// file, not from the field, so an AI cannot lean into a flank it has not noticed; and what the
/// enemy knows about the soldier is read at the rung the interface shows and never as the
/// number behind it. That is the same constraint the interface works under, and it is the one
/// an AI is most likely to breach by accident — it was breached once, by <see cref="Aimed"/>,
/// and the interface audit found it rather than Core.
/// </para>
/// </remarks>
public sealed class Tactician(Battle battle, UtilityModel? model = null)
{
    /// <summary>The exchange rates every score below is worked out at.</summary>
    public UtilityModel Model { get; } = model ?? UtilityModel.Default;

    // ---- shots -----------------------------------------------------------------

    /// <summary>
    /// What a shot is worth, in vitality, once the layers have had their say.
    /// </summary>
    /// <remarks>
    /// Four things, and the last is much the biggest: what reaches the soldier, what it wears off
    /// their plate, what it soaks out of their shield, and the chance it takes them out of the
    /// fight altogether. Nothing here is a ladder — every term comes out of
    /// <see cref="Gunnery.Expect"/>, which puts the rounds through the armour they are actually
    /// going to meet, so a beam into a full shield comes back as the nothing it is.
    /// </remarks>
    public double Worth(ShotPlan plan)
    {
        if (!plan.CanFire) return 0;

        var expected = battle.Gunnery.Expect(plan);

        return expected.Vitality
               + Model.PlateValue * expected.PlateStripped
               + Model.ShieldValue * expected.ShieldStripped
               + Model.RemovalBonus * expected.DownChance * plan.Target.Stats.Vitality;
    }

    /// <summary>
    /// A shot, appraised: what it does to them, less what it tells everybody about you.
    /// </summary>
    /// <remarks>
    /// The second term is why a stealth game cannot score a shot on its damage alone. Pulling a
    /// trigger is the loudest thing a soldier does — a slug rifle is heard through walls for
    /// forty metres and a beam paints a line straight back down its own path — and a scorer blind
    /// to that will empty a magazine into the first sentry it sees and bring the compound down on
    /// itself. It goes in <see cref="Appraisal.Spared"/> as a negative, because it is exactly
    /// that: vitality that will not be staying on us.
    /// </remarks>
    public Appraisal Appraise(ShotPlan plan)
        => plan.CanFire
            ? new Appraisal(
                Worth(plan),
                -Model.FutureDiscount * GivenAway(plan),
                Blowing(plan),
                Price(plan.ApCost))
            : Appraisal.Nothing;

    /// <summary>
    /// What firing this shot costs the mission, in vitality: never more than nothing.
    /// </summary>
    /// <remarks>
    /// The same announcements <see cref="GivenAway(ShotPlan)"/> reads, priced against the rung the
    /// mission is lost at rather than against what the listeners could do about it — see
    /// <see cref="Quiet"/>. One thing is different here and it is the whole argument for the
    /// quiet kill: the man being shot at is counted only at the chance he is still standing
    /// afterwards. If the round puts him down, whatever he learned goes with him, because the
    /// battle forgets everything a departed soldier held. Everybody else who heard it is
    /// counted in full — the noise happened.
    /// </remarks>
    public double Blowing(ShotPlan plan)
    {
        if (Bar(plan.Shooter) <= 0) return 0;

        var survives = 1.0 - battle.Gunnery.Expect(plan).DownChance;
        var heard = battle.Awareness.WouldAnnounce(plan.Shooter, plan.From, plan.Weapon, plan.Target)
            .Select(word => word.Learner == plan.Target
                ? word with { After = word.Before + survives * word.Gained }
                : word)
            .ToList();

        return Model.ObjectiveValue * (Quiet(plan.Shooter, plan.From, [], heard) - Quiet(plan.Shooter, plan.From, []));
    }

    /// <summary>
    /// What firing this shot hands the other side, in vitality.
    /// </summary>
    /// <remarks>
    /// The inverse of <see cref="AppraiseWord"/>, and derived the same way: for everybody the shot
    /// carries closer to acting, how much closer, times what they would do about you once they
    /// were. A soldier who already has a live fix on you learns nothing worth having and costs
    /// nothing; one who had no idea you existed learns the most and costs the most.
    /// <para>
    /// A shot that puts the target down still gives you away to everybody else — the noise
    /// happened — but the target itself is no longer anybody. That is not modelled here, and it
    /// should be: it is the whole argument for the quiet kill, and it needs the announcement
    /// preview to know which enemies survive the shot it is previewing.
    /// </para>
    /// <para>
    /// <b>Open:</b> somebody who hears you and has no line on you is priced at what they could do
    /// from where they stand, which is nothing. They will now come and look — a unit acts on a
    /// marker — but what that costs you is the best shot they could reach in a turn, and finding
    /// it means running their reachable set and a sight trace per node inside every shot this
    /// scorer appraises. That is a search inside a score, and it is the same shape of limit as
    /// the blade carrier that will not cross open ground: something a deeper search fixes, not a
    /// missing term.
    /// </para>
    /// </remarks>
    public double GivenAway(ShotPlan plan)
        => Told(
            battle.Awareness.WouldAnnounce(plan.Shooter, plan.From, plan.Weapon, plan.Target),
            new Threat(plan.Shooter, plan.From));

    /// <summary>
    /// What making that much noise at that place hands the other side, in vitality.
    /// </summary>
    /// <remarks>
    /// The same sum as for a shot, for a move: everybody the sound carries closer to acting, how
    /// much closer, times what they could then do about a soldier standing where the route ends.
    /// Sound reports a place rather than a person, so the pose the listeners are scored against
    /// is the arrival, which is where they would find you.
    /// </remarks>
    public double GivenAway(Unit mover, UnitPose arriving, double loudness)
        => Told(
            battle.Awareness.WouldHear(mover, arriving.Position, loudness),
            new Threat(mover, arriving));

    private double Told(IEnumerable<Announcement> announcements, Threat about)
    {
        var bar = battle.Awareness.Model.Threshold(Model.ActsOn);
        if (bar <= 0) return 0;

        var told = 0.0;

        foreach (var word in announcements)
        {
            var closer = Math.Clamp(word.After / bar, 0, 1) - Math.Clamp(word.Before / bar, 0, 1);
            if (closer <= 0) continue;

            told += closer * BestShot(word.Learner, UnitPose.Of(word.Learner), about);
        }

        return told;
    }

    /// <summary>
    /// What a charge going off is worth, in vitality, counting everybody it catches.
    /// </summary>
    /// <remarks>
    /// The same four terms a shot is worth, summed over the soldiers in the radius and signed by
    /// whose they are. That is the whole of what makes a blast different to score: it is the only
    /// action in the game that can be worth a negative number because of who else was standing
    /// there, and a scorer that counted only the enemy would lob grenades into its own squad.
    /// <para>
    /// Each enemy is counted at the credence of the belief that put them there, exactly as a shot
    /// at a marker is. A grenade thrown at where somebody was three rounds ago is worth a quarter
    /// of a grenade thrown at somebody in view, which is usually not worth the one you have.
    /// </para>
    /// </remarks>
    public double Worth(BlastPlan plan)
    {
        if (!plan.CanThrow) return 0;

        var worth = 0.0;

        foreach (var effect in plan.Caught)
        {
            var got = effect.Expectation;
            var value = got.Vitality
                        + Model.PlateValue * got.PlateStripped
                        + Model.ShieldValue * got.ShieldStripped
                        + Model.RemovalBonus * got.DownChance * effect.Caught.Stats.Vitality;

            worth += effect.Friendly
                ? -Model.FriendlyHarm * value
                : effect.Credence * value;
        }

        return worth;
    }

    /// <summary>
    /// A charge, appraised: what it does to everybody it catches, less what the bang costs you.
    /// </summary>
    /// <remarks>
    /// The noise term is the same one a shot pays and it is louder, because an explosion is the
    /// loudest thing on the field. What is different is <em>where</em> it is paid from: a burst is
    /// heard at the crater rather than at the thrower, so what it hands the other side is priced
    /// against a place the thrower is not standing in. Making a great deal of noise somewhere else
    /// is cheap, and the scorer can see that it is.
    /// <para>
    /// What is spent is not only the points. A charge thrown is a charge gone, and
    /// <see cref="UtilityModel.ChargeValue"/> is the whole of what stops a commander leading with
    /// grenades — measurably, because before it was there one did.
    /// </para>
    /// </remarks>
    public Appraisal Appraise(BlastPlan plan)
        => plan.CanThrow
            ? new Appraisal(
                Worth(plan),
                -Model.FutureDiscount * GivenAway(plan),
                Blowing(plan),
                Price(plan.ApCost) + Model.ChargeValue)
            : Appraisal.Nothing;

    /// <summary>What the bang costs the mission, in vitality: never more than nothing.</summary>
    /// <remarks>
    /// The noise is heard at the crater and marks the thrower there, so what it hands the other
    /// side about <em>where you are</em> is cheap — but what it hands them about <em>that you
    /// are</em> is the rung, and the rung is what the mission is judged on. A charge is the
    /// loudest thing on the field and this is where a squad told not to be seen learns that.
    /// </remarks>
    public double Blowing(BlastPlan plan)
    {
        if (plan.Thrower is not { } thrower || Bar(thrower) <= 0) return 0;

        var pose = UnitPose.Of(thrower);
        return Model.ObjectiveValue * (Quiet(thrower, pose, [], battle.WouldAnnounce(plan).ToList()) - Quiet(thrower, pose, []));
    }

    /// <summary>What the bang hands the other side, in vitality.</summary>
    public double GivenAway(BlastPlan plan)
        => plan.Thrower is { } thrower
            ? Told(
                battle.WouldAnnounce(plan),
                new Threat(thrower, UnitPose.Of(thrower)))
            : 0;

    /// <summary>
    /// What ending a turn with points still in hand is worth.
    /// </summary>
    /// <remarks>
    /// Not the same as the points being unspent, which <see cref="Price"/> already accounts for.
    /// This is the other side of that: leftover points <em>become</em> something — a reserve, and
    /// with it the ability to answer somebody else's move — and what the reserve is worth is
    /// whatever it can afford to do about the threats this soldier knows about.
    /// <para>
    /// It has a cliff in it, on purpose, and the cliff is the reason this is a query rather than a
    /// multiplication. Below the floor a leftover banks nothing whatever; above it, a bank that
    /// cannot afford the cheapest way of firing is worth nothing to shoot with either. Holding
    /// back is worth a great deal or nothing much, and rarely anything in between.
    /// </para>
    /// </remarks>
    /// <param name="aimBonus">
    /// What the weapon being already pointed is worth, for a unit that is holding an arc or
    /// weighing up whether to declare one. One for a soldier simply keeping points in hand.
    /// </param>
    public Appraisal AppraiseHolding(
        Unit unit, int leftover, IReadOnlyList<Threat> threats, double aimBonus = 1.0)
    {
        var banked = battle.Reactions.Banked(leftover);
        if (banked <= 0) return Appraisal.Nothing;

        var pose = UnitPose.Of(unit);
        var best = 0.0;

        foreach (var threat in threats)
            foreach (var mode in unit.Weapon.Modes)
            {
                if (unit.Stats.Costs.Fire(mode.ApCost) > banked) continue;

                var plan = battle.PlanThreat(unit, pose, threat.Unit, threat.Where, mode, aimBonus);
                if (plan.CanFire) best = Math.Max(best, threat.Credence * Worth(plan));
            }

        return new Appraisal(0, 0, Model.FutureDiscount * best, 0);
    }

    // ---- how you are left standing ---------------------------------------------

    /// <summary>
    /// What moving to a different facing or a different stance is worth.
    /// </summary>
    /// <remarks>
    /// Both halves are derived by asking the ordinary questions twice, once about the soldier as
    /// they are and once about the soldier as they would be. Nothing says that turning is better
    /// than dropping or the other way round; the geometry says it, differently every time.
    /// <para>
    /// <b>Spared</b> is the difference in what the threats could do to you. Dropping earns it by
    /// putting cover between you and them and taking exposure out of the hit chance; turning
    /// earns it by presenting a face with something left on it. On a soldier whose plate is still
    /// even all the way round, turning earns nothing here at all — which is right, and is why the
    /// other half exists.
    /// </para>
    /// <para>
    /// <b>Prospect</b> is the share of a look the new facing buys, times what you would do with
    /// what you saw. That is the real reason to turn round: you cannot shoot what you have not
    /// noticed, so a full look is worth a whole shot. It is scaled by how far short of a live fix
    /// the contact still is, because staring harder at somebody you already have dead to rights
    /// buys nothing.
    /// </para>
    /// <para>
    /// The same two questions serve a <em>walk</em>: the pose after is simply further away. A
    /// step toward a marker faces it and closes on it, so the look it buys is worth more, and the
    /// scorer wants to go there for the same reason it wants to turn round. That is most of what
    /// going to look is, and it needed no rule of its own — see <see cref="AppraiseMove"/> for
    /// the one thing a walk has that a turn does not.
    /// </para>
    /// </remarks>
    /// <param name="noise">
    /// What getting into that pose would be heard doing, for a pose reached by walking. Nothing
    /// for a turn or a change of stance, which are silent.
    /// </param>
    public Appraisal AppraisePosture(
        Unit unit, UnitPose after, int apCost, IReadOnlyList<Threat> threats, IReadOnlyList<Announcement>? noise = null)
    {
        var before = UnitPose.Of(unit);
        if (after == before && (noise is null || noise.Count == 0)) return new Appraisal(0, 0, 0, Price(apCost));

        var spared = 0.0;
        var prospect = 0.0;

        foreach (var threat in threats)
        {
            // Netted rather than clamped per threat: turning your back on one man to face
            // another is supposed to come out as the trade it is.
            spared += Incoming(threat, unit, before) - Incoming(threat, unit, after);
            prospect += Noticing(unit, after, threat) - Noticing(unit, before, threat);
        }

        return new Appraisal(
            0,
            Model.FutureDiscount * spared,
            Model.FutureDiscount * prospect + Keeping(unit, before, after, noise),
            Price(apCost));
    }

    // ---- not being seen --------------------------------------------------------

    /// <summary>
    /// What ending up standing like that, having made that noise, does to the mission, in
    /// vitality. Positive for a pose that takes you out of somebody's eye, negative for one that
    /// puts you in it.
    /// </summary>
    /// <remarks>
    /// The term that was missing, and entry 083 in <c>docs/decisions.md</c> measured what its
    /// absence cost: a hundred paired seeds on the waystation in every arm, the squad seen in
    /// every one, the mission won twice in two thousand four hundred. The objective paid for
    /// getting there and getting home, and nothing paid for getting there unseen — so a
    /// reconnaissance was scored as a race and run as one.
    /// <para>
    /// Undiscounted, like the objective it is a share of and unlike a posture's other terms: a
    /// posture is a bet on next round, and the mission is the reason the squad is on the map.
    /// And a difference between two poses rather than a reading of one, for the reason
    /// <see cref="AppraisePosture"/> gives for everything else it scores — a soldier standing in a
    /// sentry's eye has to be able to see that stepping out of it is worth something, and a
    /// reading of the pose after alone would have staying put score nothing and moving cost the
    /// walk.
    /// </para>
    /// </remarks>
    public double Keeping(Unit unit, UnitPose before, UnitPose after, IReadOnlyList<Announcement>? noise = null)
    {
        if (Bar(unit) <= 0) return 0;

        var sensed = Sensed(unit);
        return Model.ObjectiveValue * (Quiet(unit, after, sensed, noise) - Quiet(unit, before, sensed));
    }

    /// <summary>
    /// How much of the mission a soldier standing like that, making that noise, keeps: all of it
    /// while nobody is anywhere near the rung the mission is lost at, none once somebody will be
    /// over it.
    /// </summary>
    /// <remarks>
    /// <b>A slope up to the rung, not a cliff at it</b>, and the brief asked for that to be
    /// settled deliberately. The win condition is a cliff: the departure reading is either over
    /// the bar or it is not. But the reading is reached by accumulation — a look a turn, a noise
    /// a move — and a search one step deep priced against the cliff alone would walk a soldier
    /// happily to one point short of it and then find that every remaining move, and the
    /// sentry's own next look, costs the whole mission. That is entry 044's argument for
    /// gradients over flags again, from the other side: what is priced here is how far up the
    /// ladder somebody is, which is as much of a bet on the mission as the certainty figure is a
    /// bet on the man. It is the same curve <see cref="GivenAway(ShotPlan)"/> uses for how much
    /// closer to acting a listener gets — a share of the way to a bar — with the mission's bar in
    /// place of the one a listener acts at, and the mission in place of what the listener could do.
    /// <para>
    /// <b>Three things go into what each enemy will hold.</b> What they hold now, read as the
    /// rung and never the number, for the reason <see cref="Aimed"/> gives: the enemy's certainty
    /// about you is the one figure this game blurs on purpose. The look the pose hands them on
    /// their next turn, from where the soldier believes they are — in view, exactly; at a marker,
    /// averaged over every way they could be facing and discounted for how stale the marker is.
    /// And whatever the noise hands them, if there is noise. Read against every enemy who has
    /// registered anything at all, not only the ones this soldier would shoot at: a place you
    /// half-glimpsed something in is a place to keep out of the eye of, well before it is
    /// somebody to fire on.
    /// </para>
    /// <para>
    /// <b>The worst of them, not the sum</b>, because one enemy over the bar loses the mission
    /// and a second one over it loses nothing more. That is also what makes going loud free once
    /// you are seen: a soldier already held at the rung has nothing left here to keep, and the
    /// scorer knows it, which is the briefing's own line — if the shift sees you the task is
    /// over. And it is a soldier's own reading rather than the squad's worst, deliberately. The
    /// mission is lost by any one of them being seen, but a contact decays and a witness can be
    /// silenced, and a squad that stopped being careful the moment one of its own was noticed
    /// would be throwing away the recovery; each soldier keeps itself quiet.
    /// </para>
    /// </remarks>
    /// <param name="threats">Everybody whose next look is to be priced, from <see cref="Sensed"/>.</param>
    /// <param name="noise">What the listeners would be handed, from a walk or a shot. Null for silence.</param>
    public double Quiet(Unit unit, UnitPose pose, IReadOnlyList<Threat> threats, IReadOnlyList<Announcement>? noise = null)
    {
        var bar = Bar(unit);
        if (bar <= 0) return 1;

        var awareness = battle.Awareness;
        var held = new Dictionary<UnitId, double>();

        foreach (var contact in awareness.ContactsOn(unit.Id))
            held[contact.Observer] = awareness.Model.Threshold(contact.State);

        foreach (var threat in threats)
            held[threat.Unit.Id] = held.GetValueOrDefault(threat.Unit.Id) + threat.Credence * Coming(threat, pose);

        if (noise is not null)
            foreach (var word in noise)
                held[word.Learner.Id] = held.GetValueOrDefault(word.Learner.Id) + Math.Max(0, word.Gained);

        var worst = 0.0;
        foreach (var figure in held.Values) worst = Math.Max(worst, Math.Clamp(figure / bar, 0, 1));

        return 1 - worst;
    }

    /// <summary>
    /// The certainty at which somebody holding it on one of this unit's side has lost them the
    /// mission, or nought for a soldier whose mission cannot be lost that way.
    /// </summary>
    /// <remarks>
    /// One rung above what the objective tolerates, read off the same four numbers the ladder
    /// is. A mission that tolerates the top rung has no rung above it, and the threshold of a
    /// rung that does not exist is nought, which is what makes every term derived from this
    /// vanish for a side with no objective, or with one that being seen cannot cost.
    /// </remarks>
    public double Bar(Unit unit)
        => battle.ObjectiveOf(unit.Side) is { } objective
            ? battle.Awareness.Model.Threshold(objective.Unnoticed + 1)
            : 0;

    /// <summary>
    /// What being somewhere is worth toward what this soldier came to do.
    /// </summary>
    /// <remarks>
    /// The whole of the objective system as the scorer sees it, and it is deliberately one
    /// multiplication. The objective says how much of itself a place represents, from nothing to
    /// all of it; this says what all of it is worth. Nothing about which mission it is reaches
    /// here, which is what keeps a win condition from turning into a scoring model.
    /// <para>
    /// It goes in <see cref="Appraisal.Prospect"/>, undiscounted, and both halves of that are
    /// deliberate. Prospect, because getting closer to the exit delivers nothing at all this turn
    /// and is worth having entirely because of what it sets up — the same term a move to a firing
    /// position is ranked on. Undiscounted, because the mission is not a bet on next round the
    /// way a posture is: it is the reason the squad is on the map, and the future it belongs to
    /// is the one after the battle.
    /// </para>
    /// <para>
    /// A soldier with no objective scores nothing here and behaves exactly as it always did,
    /// which is what makes this safe to add to every appraisal rather than to a special path.
    /// </para>
    /// </remarks>
    /// <summary>
    /// What walking off the field is worth to a soldier whose job is done.
    /// </summary>
    /// <remarks>
    /// The whole objective, because leaving is the act that settles it — the gradient is a guide
    /// along the way and the mission is not achieved until everybody is off. That double-counts
    /// against <see cref="TowardObjective"/>, which has already paid for the walk, and it is
    /// allowed to: the two are never compared with each other, only with what else the soldier
    /// could do instead, and standing on the exit doing nothing has to lose.
    /// </remarks>
    public double Finishing(Unit unit)
        => battle.ObjectiveOf(unit.Side) is null ? 0 : Model.ObjectiveValue;

    /// <summary>
    /// What putting action points into the job is worth: the rate walking toward it earns.
    /// </summary>
    /// <remarks>
    /// The difference of two readings rather than a rate times the points, because the rate is
    /// only constant while there is all night. Once the hour is closing the slope steepens, and a
    /// stride spent on the charge has to earn what a stride walked toward it would.
    /// </remarks>
    public double WorkWorth(Unit unit, int points)
    {
        if (battle.ObjectiveOf(unit.Side) is not { } objective) return 0;

        var owed = objective.Owed(battle, unit.Position);
        if (owed == int.MaxValue) return 0;

        return Model.ObjectiveValue * (objective.Toward(battle, Math.Max(0, owed - points)) - objective.Toward(battle, owed));
    }

    public double TowardObjective(Unit unit, NodeId at)
        => battle.ObjectiveOf(unit.Side) is { } objective
            ? Model.ObjectiveValue * objective.Progress(battle, at)
            : 0;

    /// <summary>
    /// What walking a route is worth: how it leaves you standing, less what the walk told
    /// everybody.
    /// </summary>
    /// <remarks>
    /// A move is a posture with a noise attached. The posture half is
    /// <see cref="AppraisePosture"/> asked about the far end of the route; the noise half is
    /// <see cref="GivenAway(Unit, UnitPose, double)"/>, and it goes in
    /// <see cref="Appraisal.Spared"/> as a negative exactly as firing does. Going to look is
    /// worth less when the going gives you away, which is the argument for the long quiet way
    /// round — and until this existed a move's loudness was worked out after the decision and
    /// thrown away, so nothing could make that argument.
    /// </remarks>
    /// <param name="loudness">What the route makes, from <see cref="Battle.Loudness"/>.</param>
    public Appraisal AppraiseMove(
        Unit unit, UnitPose arriving, int apCost, double loudness, IReadOnlyList<Threat> threats)
    {
        var heard = battle.Awareness.WouldHear(unit, arriving.Position, loudness).ToList();

        return AppraisePosture(unit, arriving, apCost, threats, heard)
               + new Appraisal(
                   0,
                   -Model.FutureDiscount * Told(heard, new Threat(unit, arriving)),
                   TowardObjective(unit, arriving.Position) - TowardObjective(unit, unit.Position),
                   0);
    }

    /// <summary>
    /// The worst one shot from this threat would do to a soldier standing like that, weighed by
    /// how likely they are to be taking it.
    /// </summary>
    /// <remarks>
    /// One shot rather than a turn's worth, so that what is saved is denominated exactly as what
    /// is dealt. What posture actually avoids is <em>the</em> shot — the one that comes because
    /// you were standing there badly — and the discount applied on the way out of
    /// <see cref="AppraisePosture"/> is what says it might not come at all.
    /// <para>
    /// The two halves of getting low are both here, and they are not the same half. Cover and a
    /// smaller silhouette come through the shot itself, which is worth less against somebody
    /// hard to see. Being harder to <em>find</em> comes through
    /// <see cref="Aimed"/>, and on open ground with nothing to hide behind it is the only one of
    /// the two that changes at all — which is precisely right, and is why going flat in the open
    /// is worth doing and not worth much.
    /// </para>
    /// </remarks>
    private double Incoming(Threat threat, Unit target, UnitPose pose)
    {
        var worst = 0.0;

        foreach (var mode in threat.Unit.Weapon.Modes)
        {
            var plan = battle.PlanThreat(threat.Unit, threat.Where, target, pose, mode);
            if (plan.CanFire) worst = Math.Max(worst, Worth(plan));
        }

        return threat.Credence * worst * Aimed(threat, target, pose);
    }

    /// <summary>
    /// How likely this threat is to be shooting at that soldier at all, from nothing to certain.
    /// </summary>
    /// <remarks>
    /// What they already hold on you, plus the look your next pose hands them, against the bar
    /// they have to clear before they will act on any of it. Somebody standing up in the open in
    /// front of a sentry is over that bar on the strength of the look alone; somebody flat in the
    /// same place is worth less than half as much of one, because a concealed silhouette divides
    /// what a look is worth.
    /// <para>
    /// What they hold is read as the <b>rung</b>, not the number. The enemy's certainty about
    /// you is the one figure this game blurs on purpose — the interface shows a step on the
    /// ladder and never what is behind it — and for two increments this read the number anyway.
    /// That was a live cheat rather than a display problem: a soldier who knows to the point how
    /// spotted they are breaks cover at exactly the right moment and never a moment early, which
    /// reads as uncanny competence. Quantising to the rung the player is shown costs the scorer
    /// some resolution and buys back the promise in the class comment. It also means
    /// <see cref="Appraisal.Spared"/> can go on screen at last.
    /// </para>
    /// <para>
    /// Against a <b>marker</b> the look is averaged over every way the man could be facing,
    /// because nobody knows which way he is. The alternative — assuming he is looking straight
    /// at you — was measured and it prices going round a corner at more than the shot it opens
    /// on every geometry tried, so nobody ever goes. An expected look is also how the rest of the
    /// scorer treats what it cannot know: a round is rolled against a distribution of plates,
    /// not against the worst one.
    /// </para>
    /// </remarks>
    private double Aimed(Threat threat, Unit target, UnitPose pose)
    {
        var awareness = battle.Awareness;
        var bar = awareness.Model.Threshold(Model.ActsOn);
        if (bar <= 0) return 1.0;

        var held = awareness.Model.Threshold(awareness.ReadoutFor(threat.Unit.Id, target.Id).State);

        return Math.Clamp((held + Coming(threat, pose)) / bar, 0, 1);
    }

    /// <summary>
    /// What one look from this threat, on its next turn, would hand it about a soldier standing
    /// like that: exactly, for a threat in view; averaged over every facing, for a marker.
    /// </summary>
    private double Coming(Threat threat, UnitPose pose)
    {
        var awareness = battle.Awareness;

        return threat.EyesOn
            ? awareness.WouldNotice(threat.Unit, threat.Where, pose)
            : HexDirectionExtensions.All.Average(
                facing => awareness.WouldNotice(threat.Unit, threat.Where with { Facing = facing }, pose));
    }

    /// <summary>What being able to see this threat from that pose is worth.</summary>
    /// <remarks>
    /// Only worth something while there is still something left to find out. A contact you
    /// already hold a live fix on is not noticed any harder by looking straight at it. For a
    /// marker <em>everything</em> is left to find out — however sure you are that somebody is
    /// out there, you cannot shoot a man you have not found — so the look is worth the whole
    /// shot rather than the share of it the certainty figure would leave. Scaling a marker by
    /// certainty was the first thing tried, and it left a heard contact at fifty-five points
    /// worth less than half a look, which is not what half a look means.
    /// </remarks>
    private double Noticing(Unit observer, UnitPose pose, Threat threat)
    {
        var attention = battle.Awareness.AttentionOn(pose, threat.Where.Position);
        if (attention <= 0) return 0;

        var missing = 1.0;

        if (threat.EyesOn)
        {
            var certainty = battle.Awareness.Of(observer.Id, threat.Unit.Id).Detection;
            var wanted = battle.Awareness.Model.Threshold(AwarenessState.Engaged);
            missing = 1.0 - Math.Clamp(certainty / wanted, 0, 1);
            if (missing <= 0) return 0;
        }

        return attention * missing * BestShot(observer, pose, threat);
    }

    // ---- passing it on ---------------------------------------------------------

    /// <summary>
    /// What calling a contact in is worth: whatever the people who hear it can now do about it.
    /// </summary>
    /// <remarks>
    /// Derived rather than assumed, which makes shouting situational in the way it should be.
    /// Word is worth nothing to an ally who already knew, nothing to one the news will not carry
    /// far enough to move — second-hand certainty arrives at a fraction of its strength — and
    /// nothing to one with no line on the subject. It is worth a great deal to a watchman who was
    /// one rung short of being allowed to fire down the arc they are already holding.
    /// <para>
    /// <b>Open:</b> word to an ally who <em>cannot</em> see the subject is counted at zero, and it
    /// is plainly not zero — they will go and look, which is most of what a squad net is for, and
    /// a unit now does. What it is worth is the best shot they could reach in a turn, and that is
    /// the same search inside a score that <see cref="GivenAway(ShotPlan)"/> declines to run.
    /// </para>
    /// </remarks>
    public Appraisal AppraiseWord(Unit caller, Unit about, UnitPose where, int apCost)
    {
        var awareness = battle.Awareness;
        var bar = awareness.Model.Threshold(Model.ActsOn);
        var passed = awareness.Of(caller.Id, about.Id).Detection * awareness.Model.RelayFraction;

        var prospect = 0.0;

        if (passed >= bar)
        {
            foreach (var ally in awareness.Earshot(caller))
            {
                var theirs = awareness.Of(ally.Id, about.Id);
                if (theirs.Detection >= bar) continue;
                if (passed <= theirs.Detection) continue;

                prospect += BestShot(ally, UnitPose.Of(ally), new Threat(about, where));
            }
        }

        return new Appraisal(0, 0, Model.FutureDiscount * prospect, Price(apCost));
    }

    // ---- reactions -------------------------------------------------------------

    /// <summary>
    /// One reaction, appraised against the move that opened the window.
    /// </summary>
    /// <remarks>
    /// The mover is weighed as a threat at its <em>destination</em> rather than at the tick the
    /// reaction lands on, because that is where it will be standing when it shoots back. How you
    /// are left facing matters for the round after this one; the shot you take matters now, and
    /// that one is already forecast against the exact instant it arrives.
    /// </remarks>
    public Appraisal Appraise(ReactionPlacement placement, CommittedMove move)
    {
        var reactor = placement.Reactor;
        var mover = new Threat(placement.Subject, move.PoseAt(move.Duration));

        return placement.Action switch
        {
            // A held shot gives you away exactly as a deliberate one does. An overwatch that
            // fires has stopped being an ambush position.
            ReactionAction.Fire => placement.Forecast is { } forecast
                ? Appraise(forecast)
                : Appraisal.Nothing,

            // Exactly nothing, in every term. That is what makes it beat a shot that will be
            // soaked entirely, without anything anywhere saying that it should.
            ReactionAction.Nothing => Appraisal.Nothing,

            ReactionAction.Shout => AppraiseWord(reactor, placement.Subject, mover.Where, placement.ApCost),

            _ => AppraisePosture(
                reactor,
                UnitPose.Of(reactor) with
                {
                    Facing = placement.Facing ?? reactor.Facing,
                    Stance = placement.Stance ?? reactor.Stance,
                },
                placement.ApCost,
                Facing(reactor, mover)),
        };
    }

    /// <summary>
    /// Whichever of these is worth most.
    /// </summary>
    /// <remarks>
    /// Ties fall to whatever lands soonest and then to whatever is cheapest, because a thing in
    /// hand beats the same thing later and points not spent are points still available — and
    /// finally to the order the actions are declared in, so a battle replays identically from its
    /// seed however the arithmetic happens to round.
    /// </remarks>
    public ReactionPlacement Best(IReadOnlyList<ReactionPlacement> options, CommittedMove move)
        => options
            .OrderByDescending(o => Appraise(o, move).Score)
            .ThenBy(o => o.ResolvesAt)
            .ThenBy(o => o.ApCost)
            .ThenBy(o => (int)o.Action)
            .First();

    // ---- what a soldier knows --------------------------------------------------

    /// <summary>
    /// Everybody this unit takes seriously: in view where they stand, or remembered where they
    /// were.
    /// </summary>
    /// <remarks>
    /// Its own contact file, not the field. A soldier does not get to stand well against a
    /// flanker it has never seen, and it does not get to know where anybody has gone since it
    /// last looked.
    /// <para>
    /// A contact is <b>in view</b> when the last look found them and they are still in the line
    /// of it now; then the threat stands where they actually stand. The second test is what
    /// stops a look from last round following somebody round a corner — without it a unit would
    /// plan shots at the true position of a man it can no longer see, on the strength of having
    /// seen him once.
    /// </para>
    /// <para>
    /// Otherwise the threat stands at the <b>marker</b>: where contact was last made, upright,
    /// and nominally facing this way. Upright because the question a marker answers is <em>can I
    /// see the place</em>, and a standing man is the most visible thing that could be there. The
    /// facing is a placeholder — a pose has to have one — and nothing that matters reads it:
    /// <see cref="Aimed"/> averages the look he would get over every way he could be facing,
    /// and the plates a shot at him would find are even on a fresh soldier whichever way he
    /// stands. Recording the stance and facing they were last seen in was considered and left
    /// out: a marker made by ear has neither, and a look that found them will replace the
    /// marker with the man.
    /// </para>
    /// <para>
    /// A marker is discounted by <see cref="Credence"/> for how long it has gone unconfirmed.
    /// That, and not the ladder, is what stops a unit chasing a ghost round the map: the ladder
    /// says how sure you are that somebody is out there, and this says how sure you are that
    /// they are still <em>there</em>.
    /// </para>
    /// </remarks>
    public IEnumerable<Threat> Known(Unit unit) => Known(unit, Model.ActsOn);

    /// <summary>
    /// Everybody this unit has registered at all: the same contacts as <see cref="Known(Unit)"/>, down
    /// to a suspicion.
    /// </summary>
    /// <remarks>
    /// Not for shooting at, or for standing well against — a soldier does not aim at something
    /// it has half-glimpsed, and <see cref="Known(Unit)"/> stops at the rung where it would. For
    /// keeping out of an eye, a suspicion is plenty: a careful soldier does not walk into the
    /// view of a place it registered <em>something</em> in, and the term that prices not being
    /// seen reads this list so that it can say so.
    /// </remarks>
    public IReadOnlyList<Threat> Sensed(Unit unit) => Known(unit, AwarenessState.Suspicious).ToList();

    private IEnumerable<Threat> Known(Unit unit, AwarenessState atLeast)
    {
        foreach (var contact in battle.Awareness.ContactsFor(unit.Id))
        {
            if (contact.State < atLeast) continue;
            if (battle.GetUnit(contact.Subject) is not { InPlay: true } other) continue;
            if (!other.IsHostileTo(unit)) continue;

            if (contact.EyesOn && battle.CanSee(unit, other))
            {
                yield return Threat.At(other);
                continue;
            }

            if (contact.LastKnownPosition is not { } marker) continue;

            var since = battle.Awareness.ReadoutFor(unit.Id, other.Id).RoundsSinceContact;
            var facing = battle.HeadingTo(marker, unit.Position);

            yield return Threat.Believed(other, new UnitPose(marker, Stance.Standing, facing), Credence(since));
        }
    }

    /// <summary>
    /// How much a marker that many rounds old is worth, against a live fix.
    /// </summary>
    /// <remarks>
    /// The dial that decides whether the AI hunts or chases ghosts, so the argument is worth
    /// setting out. A marker is right until the subject moves, and the subject moves on its own
    /// turn. A marker made this round or last is <em>fresh</em>: turn order interleaves, so the
    /// subject may not have had a turn since, and the interface draws the same line —
    /// <see cref="AwarenessReadout.IsStale"/> turns over at two rounds, for the same reason. From
    /// there on the subject has certainly had a turn to leave, and each further round is another,
    /// so the credence halves per round: a soldier who stayed put through one turn is about as
    /// likely as not to stay through the next. Three rounds on, a marker is worth a quarter of a
    /// sighting, which is enough to turn toward and rarely enough to walk to.
    /// <para>
    /// Geometric rather than a cliff at the stale line, because a cliff makes the AI forget a
    /// contact all at once, and a soldier does not. Geometric rather than linear because the
    /// area the subject could be in grows with every turn, and the chance the marker is still
    /// inside the part of it a look would cover shrinks faster than a straight line.
    /// </para>
    /// </remarks>
    public double Credence(int roundsSinceContact)
        => roundsSinceContact <= 1 ? 1.0 : Math.Pow(Model.MarkerDecay, roundsSinceContact - 1);

    /// <summary>
    /// What one soldier could do to that threat from that pose, at its best — counted at the
    /// credence of the threat, since a shot at where somebody was is worth what the chance they
    /// are still there makes it.
    /// </summary>
    public double BestShot(Unit shooter, UnitPose pose, Threat threat)
    {
        var best = 0.0;

        foreach (var mode in shooter.Weapon.Modes)
        {
            var plan = battle.PlanThreat(shooter, pose, threat.Unit, threat.Where, mode);
            if (plan.CanFire) best = Math.Max(best, Worth(plan));
        }

        return threat.Credence * best;
    }

    /// <summary>What a number of action points is worth, in vitality.</summary>
    public double Price(int apCost) => apCost * Model.PointValue;

    /// <summary>The mover, plus anybody else the reactor is already watching.</summary>
    private List<Threat> Facing(Unit reactor, Threat mover)
    {
        var threats = new List<Threat> { mover };
        threats.AddRange(Known(reactor).Where(t => t.Unit != mover.Unit));
        return threats;
    }
}
