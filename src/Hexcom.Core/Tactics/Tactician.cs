using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Units;

namespace Hexcom.Core.Tactics;

/// <summary>
/// Somebody worth worrying about, and where they are standing while you worry about them.
/// </summary>
/// <remarks>
/// The pose is carried separately because the soldier you are weighing up is frequently not
/// where the question is about. Inside a reaction window the mover is halfway along a route, and
/// what matters for how you stand is where it ends up, not where it is when you flinch.
/// </remarks>
public readonly record struct Threat(Unit Unit, UnitPose Where)
{
    public static Threat At(Unit unit) => new(unit, UnitPose.Of(unit));

    public override string ToString() => $"{Unit.Name} at {Where.Position}";
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
/// <b>It reads only what its soldier knows.</b> Threats are drawn from that unit's own contacts,
/// not from the field, so an AI cannot lean into a flank it has not noticed. That is the same
/// constraint the interface works under, and it is the one an AI is most likely to breach by
/// accident.
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
                0,
                Price(plan.ApCost))
            : Appraisal.Nothing;

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
    /// </remarks>
    public double GivenAway(ShotPlan plan)
    {
        var bar = battle.Awareness.Model.Threshold(Model.ActsOn);
        if (bar <= 0) return 0;

        var told = 0.0;

        foreach (var word in battle.Awareness.WouldAnnounce(
                     plan.Shooter, plan.From, plan.Weapon, plan.Target))
        {
            var closer = Math.Clamp(word.After / bar, 0, 1) - Math.Clamp(word.Before / bar, 0, 1);
            if (closer <= 0) continue;

            told += closer * BestShot(word.Learner, UnitPose.Of(word.Learner), new Threat(plan.Shooter, plan.From));
        }

        return told;
    }

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
                if (plan.CanFire) best = Math.Max(best, Worth(plan));
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
    /// </remarks>
    public Appraisal AppraisePosture(Unit unit, UnitPose after, int apCost, IReadOnlyList<Threat> threats)
    {
        var before = UnitPose.Of(unit);
        if (after == before) return new Appraisal(0, 0, 0, Price(apCost));

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
            Model.FutureDiscount * prospect,
            Price(apCost));
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

        return worst * Aimed(threat, target, pose);
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
    /// </remarks>
    private double Aimed(Threat threat, Unit target, UnitPose pose)
    {
        var bar = battle.Awareness.Model.Threshold(Model.ActsOn);
        if (bar <= 0) return 1.0;

        var held = battle.Awareness.Of(threat.Unit.Id, target.Id).Detection;
        var coming = battle.Awareness.WouldNotice(threat.Unit, threat.Where, pose);

        return Math.Clamp((held + coming) / bar, 0, 1);
    }

    /// <summary>What being able to see this threat from that pose is worth.</summary>
    private double Noticing(Unit observer, UnitPose pose, Threat threat)
    {
        var attention = battle.Awareness.AttentionOn(pose, threat.Where.Position);
        if (attention <= 0) return 0;

        // Only worth something while there is still something left to find out. A contact you
        // already hold a live fix on is not noticed any harder by looking straight at it.
        var certainty = battle.Awareness.Of(observer.Id, threat.Unit.Id).Detection;
        var wanted = battle.Awareness.Model.Threshold(AwarenessState.Engaged);
        var missing = 1.0 - Math.Clamp(certainty / wanted, 0, 1);
        if (missing <= 0) return 0;

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
    /// is plainly not zero — they will go and look, which is most of what a squad net is for. It
    /// is scored at nothing because there is nothing derived to score it with until somebody
    /// builds a unit that acts on a stale marker.
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
    /// Everybody this unit currently has eyes on and takes seriously.
    /// </summary>
    /// <remarks>
    /// Its own contacts, not the field. A soldier does not get to stand well against a flanker it
    /// has never seen, and eyes on rather than merely remembered because a marker left two rounds
    /// ago is a belief about somewhere the threat has probably left.
    /// </remarks>
    public IEnumerable<Threat> Seen(Unit unit)
    {
        foreach (var contact in battle.Awareness.ContactsFor(unit.Id))
        {
            if (!contact.EyesOn || contact.State < Model.ActsOn) continue;
            if (battle.GetUnit(contact.Subject) is not { InPlay: true } other) continue;
            if (!other.IsHostileTo(unit)) continue;

            yield return Threat.At(other);
        }
    }

    /// <summary>What one soldier could do to that threat from that pose, at its best.</summary>
    public double BestShot(Unit shooter, UnitPose pose, Threat threat)
    {
        var best = 0.0;

        foreach (var mode in shooter.Weapon.Modes)
        {
            var plan = battle.PlanThreat(shooter, pose, threat.Unit, threat.Where, mode);
            if (plan.CanFire) best = Math.Max(best, Worth(plan));
        }

        return best;
    }

    /// <summary>What a number of action points is worth, in vitality.</summary>
    public double Price(int apCost) => apCost * Model.PointValue;

    /// <summary>The mover, plus anybody else the reactor is already watching.</summary>
    private List<Threat> Facing(Unit reactor, Threat mover)
    {
        var threats = new List<Threat> { mover };
        threats.AddRange(Seen(reactor).Where(t => t.Unit != mover.Unit));
        return threats;
    }
}
