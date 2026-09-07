using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;

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
/// A reactor putting an action on the mover's timeline.
/// </summary>
/// <param name="At">Tick the reactor starts the action.</param>
/// <param name="Forecast">
/// The shot as it looked when it was placed — against where the mover <em>will</em> be when it
/// lands, not where they were when the window opened. This is the number an interface shows.
/// </param>
public sealed record ReactionShot(
    Unit Reactor,
    Unit Target,
    ReactionKind Kind,
    FireMode Mode,
    int At,
    double AimBonus,
    ShotPlan Forecast)
{
    /// <summary>
    /// The tick this lands on. Action points are time inside the window, and it is the price
    /// <em>this</em> reactor pays that counts, not the one on the mode.
    /// </summary>
    public int ResolvesAt => At + Forecast.ApCost;

    public override string ToString()
        => $"{Reactor.Name} {Mode.Name} at t{At}, lands t{ResolvesAt} ({Forecast.HitChance:P0})";
}

/// <summary>
/// One reactor who could act, and everything it could do about the move.
/// </summary>
/// <remarks>
/// Only units that could actually act are offered anything: reserve in hand, the mover crossing
/// their arc at some point in the window, and a shot they can afford. That is a short list most
/// of the time and an empty one mid-firefight, which is most of what keeps a reaction window
/// from turning into a cascade.
/// </remarks>
public sealed record ReactionOffer(
    Unit Reactor,
    ReactionKind Kind,
    int Reserve,
    IReadOnlyList<ReactionShot> Options,
    ReactionShot Recommended);

/// <param name="Caught">Where the mover actually was when this landed.</param>
public sealed record ReactionResolution(ReactionShot Shot, int At, NodeId Caught, ShotOutcome Outcome);

/// <summary>
/// The window a committed move opens, and everything that happens inside it.
/// </summary>
/// <remarks>
/// A reaction does not resolve before or after the move that triggered it. It resolves
/// <em>during</em> it, on a shared clock whose currency is action points. Because the move is
/// already committed, both sides know the future for its duration: at tick three the mover is
/// three points along a route that is not in doubt.
/// <para>
/// Resolution walks the mover along that route, stopping at each tick something lands and
/// firing from there. Nothing about sight, cover or which face a round arrives at needs a
/// special case — the mover is genuinely standing where the timeline says it is, and the
/// existing geometry answers the question it always answers.
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
    private readonly List<ReactionShot> _placements = [];
    private readonly List<ReactionResolution> _resolutions = [];
    private bool _resolved;

    internal ReactionWindow(Battle battle, Unit mover, CommittedMove move)
    {
        _battle = battle;
        Mover = mover;
        Move = move;
        BuildOffers();
    }

    public Unit Mover { get; }

    public CommittedMove Move { get; }

    /// <summary>Everyone who could do something about this move, and what.</summary>
    public IReadOnlyList<ReactionOffer> Offers => _offers;

    /// <summary>What was actually placed on the timeline.</summary>
    public IReadOnlyList<ReactionShot> Placements => _placements;

    /// <summary>What each placement did, in the order the ticks ran.</summary>
    public IReadOnlyList<ReactionResolution> Resolutions => _resolutions;

    /// <summary>The tick the mover got no further than. The full duration unless it was dropped.</summary>
    public int StoppedAt { get; private set; }

    /// <summary>True if the mover never reached where it was going.</summary>
    public bool Interrupted => StoppedAt < Move.Duration;

    public bool AnyReactions => _placements.Count > 0;

    // ---- placing ---------------------------------------------------------------

    /// <summary>Put an action on the timeline. Must come from an offer this window made.</summary>
    public void Place(ReactionShot shot)
    {
        if (_resolved) throw new InvalidOperationException("This window has already resolved.");

        if (!_offers.Any(o => o.Reactor == shot.Reactor))
            throw new ArgumentException($"{shot.Reactor.Name} was not offered a reaction to this move.", nameof(shot));

        if (_placements.Any(p => p.Reactor == shot.Reactor))
            throw new ArgumentException($"{shot.Reactor.Name} has already placed one.", nameof(shot));

        _placements.Add(shot);
    }

    /// <summary>Take every recommendation. This is what happens when nobody is choosing by hand.</summary>
    public void PlaceRecommended()
    {
        foreach (var offer in _offers) Place(offer.Recommended);
    }

    // ---- resolving -------------------------------------------------------------

    /// <summary>
    /// Run the window: walk the mover along its route and fire each placement at the tick it
    /// lands on.
    /// </summary>
    /// <remarks>
    /// Ties are broken by unit id rather than by anything in the fiction, so a battle replays
    /// identically from its seed. Two shots landing on the same tick are simultaneous as far as
    /// the player is concerned, and if the first drops the mover the second is never fired —
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

        foreach (var shot in ordered)
        {
            if (!Mover.InPlay) break;
            if (!shot.Reactor.InPlay) continue;

            var tick = Math.Min(shot.ResolvesAt, Move.Duration);
            StepTo(tick);

            var outcome = _battle.FireReaction(shot);
            _resolutions.Add(new ReactionResolution(shot, tick, Mover.Position, outcome));
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

    private void BuildOffers()
    {
        foreach (var reactor in _battle.Enemies(Mover).OrderBy(u => u.Id.Value))
        {
            if (reactor == Mover) continue;
            if (reactor.Reserve <= 0) continue;
            if (reactor.Overwatch is not { } order) continue;
            if (!Registers(reactor, order)) continue;

            var options = OverwatchOptions(reactor, order);
            if (options.Count == 0) continue;

            // Best expected damage, and where two are equal the one that lands soonest — a
            // shot in hand beats the same shot later, because the situation can only get worse.
            var best = options
                .OrderByDescending(o => o.Forecast.ExpectedDamage)
                .ThenBy(o => o.ResolvesAt)
                .ThenBy(o => o.Mode.ApCost)
                .First();

            _offers.Add(new ReactionOffer(reactor, ReactionKind.Overwatch, reactor.Reserve, options, best));
        }
    }

    /// <summary>
    /// Whether the watchman actually notices the crossing, and is sure enough to shoot at it.
    /// </summary>
    /// <remarks>
    /// Holding an arc is the act of looking down it, so the crossing gets a proper look at the
    /// tick it happens — through the ordinary detection model, which means stance, cover, range
    /// and exposure all still protect a careful approach. What comes out of that look, on top of
    /// whatever the watchman already believed, has to clear the bar in the reaction model before
    /// a trigger is pulled. A soldier nobody has noticed is not shot at.
    /// </remarks>
    private bool Registers(Unit reactor, OverwatchOrder order)
    {
        var rules = _battle.Reactions;

        if (rules.OverwatchLooks && TriggerTick(reactor, order) is { } tick)
            _battle.Awareness.Notice(reactor, Mover, Move.PoseAt(tick), _battle.Round);

        return _battle.Awareness.Of(reactor.Id, Mover.Id).State >= rules.OverwatchRequires;
    }

    /// <summary>
    /// The first moment on the timeline the mover is both inside the arc and in view. Null if it
    /// never is, in which case there was nothing to notice.
    /// </summary>
    private int? TriggerTick(Unit reactor, OverwatchOrder order)
    {
        foreach (var tick in Move.ArrivalTicks)
        {
            var pose = Move.PoseAt(tick);
            if (!order.Covers(_battle, reactor.Position, pose.Position)) continue;
            if (!_battle.Sight.CanSee(reactor.Vantage, pose.Vantage)) continue;

            return tick;
        }

        return null;
    }

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
    private List<ReactionShot> OverwatchOptions(Unit reactor, OverwatchOrder order)
    {
        var options = new List<ReactionShot>();

        foreach (var mode in reactor.Weapon.Modes)
        {
            // What this watchman pays, not what the mode lists — and inside a window that price
            // is also how long the shot takes, so a slow shooter catches the mover later.
            var cost = reactor.Stats.Costs.Fire(mode.ApCost);
            if (cost > reactor.Reserve) continue;

            ReactionShot? best = null;

            foreach (var start in StartTicksFor(cost))
            {
                var landing = Math.Min(start + cost, Move.Duration);
                var pose = Move.PoseAt(landing);

                if (!order.Covers(_battle, reactor.Position, pose.Position)) continue;

                var forecast = _battle.PlanShot(
                    reactor, Mover, mode, order.Arc.AimBonus, pose, ApSource.Reserve);
                if (!forecast.CanFire) continue;

                var shot = new ReactionShot(
                    reactor, Mover, ReactionKind.Overwatch, mode, start, order.Arc.AimBonus, forecast);

                if (best is null || shot.Forecast.ExpectedDamage > best.Forecast.ExpectedDamage) best = shot;
            }

            if (best is not null) options.Add(best);
        }

        return options;
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
