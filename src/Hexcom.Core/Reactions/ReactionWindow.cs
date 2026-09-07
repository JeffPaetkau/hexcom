using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Reactions;

/// <summary>Which of the three ways of acting out of turn a reaction is.</summary>
public enum ReactionKind
{
    /// <summary>A declared arc, held deliberately, triggered by movement inside it.</summary>
    Overwatch,

    /// <summary>A squad armed against an agreed trigger, resolving together.</summary>
    Ambush,

    /// <summary>The involuntary one: suddenly registering somebody, and doing something about it.</summary>
    Surprise,
}

/// <summary>
/// What a reactor does with the moment.
/// </summary>
/// <remarks>
/// Overwatch only ever shoots — it is a held shot by definition. Surprise is the one that needs
/// the rest of these, because the point of it is that a soldier caught out does <em>something</em>
/// rather than nothing, and shooting is often not the something available.
/// </remarks>
public enum ReactionAction
{
    Fire,

    /// <summary>Turn to put the threat in front of you, where you can watch it and armour is thicker.</summary>
    Turn,

    /// <summary>Get lower. Costs almost nothing and changes what the next shot at you can see.</summary>
    Drop,

    /// <summary>Call it in, so somebody who <em>can</em> do something about it knows.</summary>
    Shout,
}

/// <summary>
/// A reactor putting one action on the mover's timeline.
/// </summary>
/// <param name="At">
/// Tick the reactor starts the action. Overwatch starts at nought because the weapon was already
/// pointed; a surprise starts at the moment of registering, which is why it lands later.
/// </param>
/// <param name="ApCost">What this reactor pays, which is not always what the action lists.</param>
/// <param name="Forecast">
/// For a shot: how it looked when it was placed, against where the mover <em>will</em> be when it
/// lands. Null for everything else.
/// </param>
public sealed record ReactionPlacement(
    Unit Reactor,
    Unit Subject,
    ReactionKind Kind,
    ReactionAction Action,
    int At,
    int ApCost,
    ShotPlan? Forecast = null,
    HexDirection? Facing = null,
    Stance? Stance = null)
{
    /// <summary>The tick this lands on. Action points are time inside the window.</summary>
    public int ResolvesAt => At + ApCost;

    /// <summary>The way of firing, for a shot. Null for everything else.</summary>
    public FireMode? Mode => Forecast?.Mode;

    /// <summary>What an interface would sort by. Anything that is not a shot scores nothing.</summary>
    public double ExpectedDamage => Forecast?.ExpectedDamage ?? 0;

    public override string ToString() => Action switch
    {
        ReactionAction.Fire => $"{Reactor.Name} {Mode?.Name} at t{At}, lands t{ResolvesAt} ({Forecast?.HitChance:P0})",
        ReactionAction.Turn => $"{Reactor.Name} turns to {Facing} at t{At}",
        ReactionAction.Drop => $"{Reactor.Name} goes {Stance} at t{At}",
        _ => $"{Reactor.Name} calls it in at t{At}",
    };
}

/// <summary>
/// One reactor who could act, and everything it could do about the move.
/// </summary>
/// <remarks>
/// Only units that could actually act are offered anything: reserve in hand, the mover crossing
/// the arc they care about at some point in the window, and something they can afford. That is a
/// short list most of the time and an empty one mid-firefight, which is most of what keeps a
/// reaction window from turning into a cascade.
/// </remarks>
public sealed record ReactionOffer(
    Unit Reactor,
    ReactionKind Kind,
    int Reserve,
    int Purse,
    IReadOnlyList<ReactionPlacement> Options,
    ReactionPlacement Recommended);

/// <param name="Caught">Where the mover actually was when this landed.</param>
/// <param name="Outcome">What the round did, for a shot. Null for everything else.</param>
public sealed record ReactionResolution(
    ReactionPlacement Placement,
    int At,
    NodeId Caught,
    ShotOutcome? Outcome);

/// <summary>
/// The window a committed move opens, and everything that happens inside it.
/// </summary>
/// <remarks>
/// A reaction does not resolve before or after the move that triggered it. It resolves
/// <em>during</em> it, on a shared clock whose currency is action points. Because the move is
/// already committed, both sides know the future for its duration: at tick three the mover is
/// three points along a route that is not in doubt.
/// <para>
/// Resolution walks the mover along that route, stopping at each tick something lands and acting
/// from there. Nothing about sight, cover or which face a round arrives at needs a special case —
/// the mover is genuinely standing where the timeline says it is, and the existing geometry
/// answers the question it always answers.
/// </para>
/// <para>
/// Offers and resolution are separate on purpose. An interface will want to show the choices,
/// let the player place their own, and only then resolve; the automatic path used by the turn
/// loop simply takes every recommendation. That split is also where an AI will plug in.
/// </para>
/// </remarks>
public sealed class ReactionWindow
{
    private readonly Battle _battle;
    private readonly List<ReactionOffer> _offers = [];
    private readonly List<ReactionPlacement> _placements = [];
    private readonly List<ReactionResolution> _resolutions = [];
    private bool _resolved;
    private int _sprungAt;

    private ReactionWindow(Battle battle, Unit subject, CommittedMove move, Unit? springer)
    {
        _battle = battle;
        Mover = subject;
        Move = move;
        SprungBy = springer;

        if (springer is null) BuildOffers();
        else BuildAmbushOffers(springer, tick: 0);
    }

    /// <summary>The window a committed move opens. Overwatch and surprise answer into it.</summary>
    internal static ReactionWindow ForMove(Battle battle, Unit mover, CommittedMove move)
        => new(battle, mover, move, springer: null);

    /// <summary>
    /// The window one member of an ambush opens by choosing the moment.
    /// </summary>
    /// <remarks>
    /// The subject is standing still, so the timeline is a single instant — but it is the same
    /// timeline, which is what makes cheap shots resolve before expensive ones. If the snap shots
    /// put the target down, the aimed ones are never taken and their reserves are never spent.
    /// </remarks>
    internal static ReactionWindow ForAmbush(Battle battle, Unit target, Unit springer)
        => new(battle, target, new CommittedMove(target.Position, [], target.Facing, target.Stance), springer);

    /// <summary>The subject of the window. Moving, unless an ambush was sprung on it.</summary>
    public Unit Mover { get; }

    /// <summary>Who said now, for an ambush. Null for an ordinary move window.</summary>
    public Unit? SprungBy { get; private set; }

    public bool IsAmbush => SprungBy is not null;

    public CommittedMove Move { get; }

    /// <summary>Everyone who could do something about this move, and what.</summary>
    public IReadOnlyList<ReactionOffer> Offers => _offers;

    /// <summary>What was actually placed on the timeline.</summary>
    public IReadOnlyList<ReactionPlacement> Placements => _placements;

    /// <summary>What each placement did, in the order the ticks ran.</summary>
    public IReadOnlyList<ReactionResolution> Resolutions => _resolutions;

    /// <summary>The tick the mover got no further than. The full duration unless it was dropped.</summary>
    public int StoppedAt { get; private set; }

    /// <summary>True if the mover never reached where it was going.</summary>
    public bool Interrupted => StoppedAt < Move.Duration;

    public bool AnyReactions => _placements.Count > 0;

    // ---- placing ---------------------------------------------------------------

    /// <summary>Put an action on the timeline. Must come from an offer this window made.</summary>
    public void Place(ReactionPlacement placement)
    {
        if (_resolved) throw new InvalidOperationException("This window has already resolved.");

        if (!_offers.Any(o => o.Reactor == placement.Reactor))
            throw new ArgumentException($"{placement.Reactor.Name} was not offered a reaction to this move.", nameof(placement));

        if (_placements.Any(p => p.Reactor == placement.Reactor))
            throw new ArgumentException($"{placement.Reactor.Name} has already placed one.", nameof(placement));

        _placements.Add(placement);
    }

    /// <summary>
    /// Take every recommendation that nobody has already answered by hand.
    /// </summary>
    /// <remarks>
    /// Skipping reactors who already placed is what lets a player, or the unit springing an
    /// ambush, choose their own action and leave the rest of the squad on the default.
    /// </remarks>
    public void PlaceRecommended()
    {
        foreach (var offer in _offers)
            if (!_placements.Any(p => p.Reactor == offer.Reactor))
                Place(offer.Recommended);
    }

    // ---- resolving -------------------------------------------------------------

    /// <summary>
    /// Run the window: walk the mover along its route and resolve each placement at the tick it
    /// lands on.
    /// </summary>
    /// <remarks>
    /// Ties are broken by unit id rather than by anything in the fiction, so a battle replays
    /// identically from its seed. Two actions landing on the same tick are simultaneous as far as
    /// the player is concerned, and if the first drops the mover the rest are never taken —
    /// nobody spends a reserve on a target that has already gone down.
    /// </remarks>
    public void Resolve()
    {
        if (_resolved) throw new InvalidOperationException("This window has already resolved.");
        _resolved = true;

        var ordered = _placements
            .OrderBy(p => p.ResolvesAt)
            .ThenBy(p => p.Reactor.Id.Value)
            .ToList();

        foreach (var placement in ordered)
        {
            if (!Mover.InPlay) break;
            if (!placement.Reactor.InPlay) continue;

            var tick = Math.Min(placement.ResolvesAt, Move.Duration);
            StepTo(tick);

            var outcome = _battle.ResolveReaction(placement);
            _resolutions.Add(new ReactionResolution(placement, tick, Mover.Position, outcome));
        }

        if (Mover.InPlay) StepTo(Move.Duration);
    }

    /// <summary>Offer, take every recommendation, and run it. The turn loop's path.</summary>
    internal void Run()
    {
        PlaceRecommended();
        Resolve();
    }

    /// <summary>
    /// Put the mover where the timeline says it is. This is a real move, not a hypothetical:
    /// everything that looks at the mover from here on sees it there.
    /// </summary>
    private void StepTo(int tick)
    {
        var step = Move.StepAt(tick);
        Mover.Position = step.Node;
        Mover.Facing = step.Facing;
        StoppedAt = tick;
    }

    // ---- working out who could do what -----------------------------------------

    /// <remarks>
    /// Reserve in hand is checked before anything else, and it does double duty. It is what an
    /// answer is paid out of, and it is also the closest thing the model has to <em>alertness</em>
    /// — a soldier who spent the lot is head down and busy, and does not get the extra look that
    /// noticing somebody mid-window requires. Hanging back keeps your eyes up as well as your
    /// options open.
    /// </remarks>
    private void BuildOffers()
    {
        foreach (var reactor in _battle.Enemies(Mover).OrderBy(u => u.Id.Value))
        {
            if (reactor == Mover) continue;
            if (reactor.Reserve <= 0) continue;

            if (OfferFor(reactor) is { } offer) _offers.Add(offer);
        }

        // Somebody walking into an armed arc springs the trap, and the trap is not one soldier.
        if (SprungBy is { } springer) BuildAmbushOffers(springer, _sprungAt);
    }

    /// <summary>
    /// What this one reactor gets asked, if anything.
    /// </summary>
    /// <remarks>
    /// A declared arc is tried first, because it is both a wider net and a better answer. Failing
    /// that — the arc does not reach, or nothing in it can be afforded — the reactor may still be
    /// startled by somebody walking across its front, and answers worse for it.
    /// <para>
    /// Whichever path is taken, the reactor gets <b>one</b> look. Letting overwatch look and then
    /// letting surprise look again would hand a watchman two turns worth of certainty for one
    /// crossing, and would break the rise test surprise depends on by comparing a state against
    /// itself.
    /// </para>
    /// </remarks>
    private ReactionOffer? OfferFor(Unit reactor)
    {
        var rules = _battle.Reactions;

        if (reactor.Held is { } order
            && TriggerTick(reactor, place => order.Covers(_battle, reactor.Position, place)) is { } watched)
        {
            var seen = Look(reactor, watched, rules.OverwatchLooks);

            if (seen.After >= rules.OverwatchRequires)
            {
                // An armed unit never answers alone. Whoever's arc was crossed earliest says now,
                // and the whole squad is dealt with together once the loop is done.
                if (reactor.Overwatch is null)
                {
                    if (SprungBy is null || watched < _sprungAt)
                    {
                        SprungBy = reactor;
                        _sprungAt = watched;
                    }

                    return null;
                }

                var options = OverwatchOptions(reactor, order);
                if (options.Count > 0)
                    return new ReactionOffer(
                        reactor, ReactionKind.Overwatch, reactor.Reserve, reactor.Reserve, options, Best(options));
            }

            return SurpriseFrom(reactor, watched, seen);
        }

        if (TriggerTick(reactor, place => NotBehind(reactor, place)) is not { } moment)
            return null;

        return SurpriseFrom(reactor, moment, Look(reactor, moment, allowed: true));
    }

    /// <summary>
    /// Take a look at the mover as it will be at one tick, and report what that did to the state.
    /// </summary>
    /// <remarks>
    /// Ordinary in every respect — stance, cover, range, exposure and perception all still decide
    /// whether it registers, so a careful approach is as invisible mid-window as it is on anyone's
    /// turn. What is not ordinary is that it happens at all outside the observer's own turn, which
    /// is what an arc, or having your wits about you, buys.
    /// </remarks>
    private (AwarenessState Before, AwarenessState After) Look(Unit reactor, int tick, bool allowed)
    {
        var before = _battle.Awareness.Of(reactor.Id, Mover.Id).State;
        if (allowed) _battle.Awareness.Notice(reactor, Mover, Move.PoseAt(tick), _battle.Round);

        return (before, _battle.Awareness.Of(reactor.Id, Mover.Id).State);
    }

    // ---- overwatch -------------------------------------------------------------

    /// <summary>
    /// Every distinct shot a watchman could take at this move: one per fire mode, placed at the
    /// tick that catches the mover at its worst.
    /// </summary>
    /// <remarks>
    /// The mover only changes where it is at the ticks it arrives somewhere, so those are the
    /// only landing times worth considering. Working backwards from each of them gives the tick
    /// to start on, and anything that cannot be started before the window opens falls back to
    /// firing immediately — the weapon was already pointed, after all.
    /// </remarks>
    private List<ReactionPlacement> OverwatchOptions(Unit reactor, HeldArc order)
    {
        var options = new List<ReactionPlacement>();

        foreach (var mode in reactor.Weapon.Modes)
        {
            // What this watchman pays, not what the mode lists — and inside a window that price
            // is also how long the shot takes, so a slow shooter catches the mover later.
            var cost = reactor.Stats.Costs.Fire(mode.ApCost);
            if (cost > reactor.Reserve) continue;

            ReactionPlacement? best = null;

            foreach (var start in StartTicksFor(cost))
            {
                var landing = Math.Min(start + cost, Move.Duration);
                var pose = Move.PoseAt(landing);

                if (!order.Covers(_battle, reactor.Position, pose.Position)) continue;

                var forecast = _battle.PlanShot(
                    reactor, Mover, mode, order.Arc.AimBonus, pose, ApSource.Reserve);
                if (!forecast.CanFire) continue;

                var shot = new ReactionPlacement(
                    reactor, Mover, ReactionKind.Overwatch, ReactionAction.Fire, start, cost, forecast);

                if (best is null || shot.ExpectedDamage > best.ExpectedDamage) best = shot;
            }

            if (best is not null) options.Add(best);
        }

        return options;
    }

    // ---- ambush ----------------------------------------------------------------

    /// <summary>
    /// Every armed member of the springer's side that can answer, all placed on the same tick.
    /// </summary>
    /// <remarks>
    /// This is the whole point of arming, and the answer to what interleaved initiative does to a
    /// coordinated opening. Normally the other side acts between your shots; here every member
    /// resolves inside one window, before the target does anything about any of it.
    /// <para>
    /// The springer pays out of the turn it is taking. Everybody else pays out of the reserve
    /// they banked when they armed — so the trap is only fully loaded while nobody has had their
    /// turn back yet, and the member whose turn came round is standing there with an armed arc
    /// and nothing to fire out of it.
    /// </para>
    /// <para>
    /// Being told counts. Springing calls the contact in first, so an ambusher out of earshot and
    /// with no eyes on the target simply does not fire.
    /// </para>
    /// </remarks>
    private void BuildAmbushOffers(Unit springer, int tick)
    {
        var bar = _battle.Reactions.OverwatchRequires;

        foreach (var member in _battle.InPlay
                     .Where(u => u.Side == springer.Side && u.Ambush is not null)
                     .OrderBy(u => u.Id.Value))
        {
            if (_offers.Any(o => o.Reactor == member)) continue;

            var arc = member.Ambush!.Value;
            if (!arc.Covers(_battle, member.Position, Mover.Position)) continue;
            if (_battle.Awareness.Of(member.Id, Mover.Id).State < bar) continue;

            // Out of the turn you are taking, if you are taking one. A trap sprung by somebody
            // walking into it is answered by everybody out of their reserves, the member whose
            // arc they crossed included — nobody is having a turn at that moment.
            var paying = member == springer && member == _battle.Active ? ApSource.Turn : ApSource.Reserve;
            var purse = paying == ApSource.Turn ? member.ActionPoints : member.Reserve;
            if (purse <= 0) continue;

            var options = AmbushOptions(member, arc, paying, purse, tick);
            if (options.Count == 0) continue;

            _offers.Add(new ReactionOffer(
                member, ReactionKind.Ambush, member.Reserve, purse, options, Best(options)));
        }
    }

    private List<ReactionPlacement> AmbushOptions(
        Unit member,
        HeldArc arc,
        ApSource paying,
        int purse,
        int tick)
    {
        var options = new List<ReactionPlacement>();

        foreach (var mode in member.Weapon.Modes)
        {
            var cost = member.Stats.Costs.Fire(mode.ApCost);
            if (cost > purse) continue;

            // A held shot down a declared arc, so it aims like one — and it lands the moment the
            // trap springs rather than a beat later, because it was waiting for exactly this.
            var landing = Math.Min(tick + cost, Move.Duration);
            var forecast = _battle.PlanShot(
                member, Mover, mode, arc.Arc.AimBonus, Move.PoseAt(landing), paying);

            if (!forecast.CanFire) continue;

            options.Add(new ReactionPlacement(
                member, Mover, ReactionKind.Ambush, ReactionAction.Fire, tick, cost, forecast));
        }

        return options;
    }

    // ---- surprise --------------------------------------------------------------

    /// <summary>
    /// The involuntary one. Nobody sets it up and everybody has it, so the gates on it are what
    /// keep every move in a firefight from generating a volley of answers.
    /// </summary>
    /// <remarks>
    /// The one that matters is that the contact has to <em>rise</em>. Being surprised is the
    /// moment it clicks; somebody you were already tracking is not a surprise however plainly
    /// they walk past you, so a unit gets at most one of these per opponent as that opponent
    /// climbs its awareness ladder, and none at all once the shooting has started.
    /// </remarks>
    private ReactionOffer? SurpriseFrom(
        Unit reactor,
        int tick,
        (AwarenessState Before, AwarenessState After) seen)
    {
        var rules = _battle.Reactions;
        if (!rules.Surprise) return null;

        // The moment it clicks, and only that moment. Crossing the bar is the surprise; climbing
        // further up the ladder once across it is only learning more about somebody already being
        // tracked, and that is what keeps a firefight from throwing one of these for every move.
        if (seen.Before >= rules.SurpriseRequires) return null;
        if (seen.After < rules.SurpriseRequires) return null;

        // Half a bank, because reacting is not planning.
        var purse = (int)(reactor.Reserve * rules.SurpriseFraction);
        if (purse <= 0) return null;

        var options = SurpriseOptions(reactor, tick, purse, seen.After >= rules.SurpriseFireRequires);
        if (options.Count == 0) return null;

        return new ReactionOffer(
            reactor, ReactionKind.Surprise, reactor.Reserve, purse, options, Best(options));
    }

    /// <summary>Something rather than nothing: shoot, turn, get low, or tell somebody.</summary>
    /// <remarks>
    /// Everything here starts a beat after the moment of noticing rather than at the top of the
    /// window, which is the whole of what a declared arc buys in timing: the weapon was already
    /// pointed, so an overwatch does not pay this.
    /// </remarks>
    private List<ReactionPlacement> SurpriseOptions(Unit reactor, int tick, int purse, bool mayShoot)
    {
        var options = new List<ReactionPlacement>();
        var rules = _battle.Reactions;
        var prices = _battle.Costs;
        var start = tick + rules.SurpriseDelay;

        ReactionPlacement Placed(ReactionAction action, int cost, ShotPlan? forecast = null,
            HexDirection? facing = null, Stance? stance = null)
            => new(reactor, Mover, ReactionKind.Surprise, action, start, cost, forecast, facing, stance);

        foreach (var mode in mayShoot ? reactor.Weapon.Modes : [])
        {
            var cost = reactor.Stats.Costs.Fire(mode.ApCost);
            if (cost > purse) continue;

            // No aim bonus: the weapon was pointed at nothing in particular a moment ago.
            var landing = Math.Min(start + cost, Move.Duration);
            var forecast = _battle.PlanShot(reactor, Mover, mode, 1.0, Move.PoseAt(landing), ApSource.Reserve);
            if (!forecast.CanFire) continue;

            options.Add(Placed(ReactionAction.Fire, cost, forecast));
        }

        // Turning is only worth offering to somebody who caught this in the corner of an eye.
        // Anything already dead ahead cannot be faced any better than it is.
        var caught = Move.PositionAt(tick);
        if (!_battle.Awareness.IsWatching(reactor, caught) && prices.TurnInPlace <= purse)
        {
            var toward = _battle.HeadingTo(reactor.Position, caught);
            if (toward != reactor.Facing)
                options.Add(Placed(ReactionAction.Turn, prices.TurnInPlace, facing: toward));
        }

        if (prices.ChangeStance <= purse)
            foreach (var lower in Lower(reactor.Stance))
                options.Add(Placed(ReactionAction.Drop, prices.ChangeStance, stance: lower));

        if (rules.ShoutCost <= purse && _battle.Awareness.Earshot(reactor).Any())
            options.Add(Placed(ReactionAction.Shout, rules.ShoutCost));

        return options;
    }

    /// <summary>
    /// Whether a place is anywhere in view at all rather than squarely behind the reactor.
    /// </summary>
    /// <remarks>
    /// The surprise trigger, and wider than the arc a unit is properly attending to on purpose:
    /// catching something in the corner of an eye is exactly the moment being modelled, and it is
    /// the only one where turning to face it is worth an action. Behind is behind — walk round
    /// the back of a sentry and it does not flinch, which is the reward the whole approach is
    /// played for.
    /// </remarks>
    private bool NotBehind(Unit reactor, NodeId place)
        => _battle.Awareness.AttentionOn(reactor, place) > _battle.Awareness.Model.RearAcuity;

    /// <summary>Stances lower than this one, cheapest commitment first.</summary>
    private static IEnumerable<Stance> Lower(Stance stance) => stance switch
    {
        Stance.Standing => [Stance.Crouching, Stance.Prone],
        Stance.Crouching => [Stance.Prone],
        _ => [],
    };

    // ---- shared --------------------------------------------------------------

    /// <summary>
    /// Whichever option looks best, with a deliberate placeholder of a policy.
    /// </summary>
    /// <remarks>
    /// Shoot if you can, otherwise turn to face them, otherwise get low, otherwise call it in.
    /// Ranking a shot against a shove into cover is exactly the judgement utility scoring exists
    /// to make, so this stays a stand-in until the AI arrives rather than pretending to be one.
    /// Among shots, best expected damage wins and ties go to whichever lands soonest, because a
    /// shot in hand beats the same shot later.
    /// </remarks>
    private static ReactionPlacement Best(IReadOnlyList<ReactionPlacement> options)
    {
        var shots = options.Where(o => o.Action == ReactionAction.Fire).ToList();

        if (shots.Count > 0)
            return shots
                .OrderByDescending(o => o.ExpectedDamage)
                .ThenBy(o => o.ResolvesAt)
                .ThenBy(o => o.ApCost)
                .First();

        return options.OrderBy(o => o.Action switch
        {
            ReactionAction.Turn => 0,
            ReactionAction.Drop => 1,
            _ => 2,
        }).First();
    }

    /// <summary>
    /// The first moment on the timeline the mover is both inside the arc that matters and in
    /// view. Null if it never is, in which case there was nothing to notice.
    /// </summary>
    private int? TriggerTick(Unit reactor, Func<NodeId, bool> inside)
    {
        foreach (var tick in Move.ArrivalTicks)
        {
            var pose = Move.PoseAt(tick);
            if (!inside(pose.Position)) continue;
            if (!_battle.Sight.CanSee(reactor.Vantage, pose.Vantage)) continue;

            return tick;
        }

        return null;
    }

    /// <summary>
    /// Ticks worth starting an action of a given price on, so that it lands the moment the mover
    /// arrives somewhere new.
    /// </summary>
    private IEnumerable<int> StartTicksFor(int cost)
    {
        var seen = new HashSet<int> { 0 };
        yield return 0;

        foreach (var arrival in Move.ArrivalTicks)
        {
            var start = arrival - cost;
            if (start > 0 && seen.Add(start)) yield return start;
        }
    }
}
