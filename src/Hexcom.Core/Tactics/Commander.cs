using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Tactics;

/// <summary>The kinds of thing a soldier can be told to do on its own turn.</summary>
public enum OrderKind
{
    /// <summary>Go somewhere.</summary>
    Move,

    /// <summary>Shoot somebody.</summary>
    Fire,

    /// <summary>Hold an arc and wait.</summary>
    Overwatch,

    /// <summary>Turn on the spot, to watch ground you are not watching.</summary>
    Face,

    /// <summary>Change how you are carrying yourself.</summary>
    Stance,

    /// <summary>Lob a charge at a piece of ground.</summary>
    Throw,

    /// <summary>Call a contact in, so somebody who can act on it knows.</summary>
    Shout,

    /// <summary>Walk off the field, having done what you came to do.</summary>
    Leave,
}

/// <summary>
/// One thing a soldier could do next, and what it is worth.
/// </summary>
/// <remarks>
/// <see cref="Opens"/> is the reason this is a record rather than a number. A move to open ground
/// with a clear line on somebody is worth almost nothing on its own — walking is not an
/// achievement — and is worth a great deal because of the shot waiting at the other end of it.
/// Ranking a move without looking one step past it means never taking a firing position; folding
/// that shot into the move's own appraisal means claiming the move did something it did not.
/// So the two are carried separately: <see cref="Worth"/> is what this action does,
/// <see cref="Opens"/> is what it sets up, and <see cref="Score"/> is what it was chosen on.
/// </remarks>
public sealed record Order(
    OrderKind Kind,
    Appraisal Worth,
    NodeId? MoveTo = null,
    ShotPlan? Shot = null,
    OverwatchArc? Arc = null,
    HexDirection? Facing = null,
    Stance? Stance = null,
    Appraisal? Opens = null,
    BlastPlan? Throw = null,
    Unit? About = null)
{
    /// <summary>What this was ranked on: what it does, plus what it sets up.</summary>
    public double Score => Worth.Score + (Opens?.Score ?? 0);

    public override string ToString() => Kind switch
    {
        OrderKind.Move => $"move to {MoveTo} ({Score:+0.00;-0.00})",
        OrderKind.Fire => $"{Shot?.Mode.Name} at {Shot?.Target.Name} ({Score:+0.00;-0.00})",
        OrderKind.Overwatch => $"watch {Facing} on a {Arc?.Name} arc ({Score:+0.00;-0.00})",
        OrderKind.Face => $"turn to {Facing} ({Score:+0.00;-0.00})",
        OrderKind.Throw => $"{Throw?.Item.Name} at {Throw?.Aimed} ({Score:+0.00;-0.00})",
        OrderKind.Shout => $"call {About?.Name} in ({Score:+0.00;-0.00})",
        OrderKind.Leave => $"walk off the field ({Score:+0.00;-0.00})",
        _ => $"go {Stance} ({Score:+0.00;-0.00})",
    };
}

/// <summary>
/// What answers the reaction windows this commander's moves open.
/// </summary>
/// <remarks>
/// The seam has to reach through the commander or an interface never gets to use it, because the
/// case a player cares about most is the <em>enemy's</em> move: a hostile walks across our
/// sentry's arc and our sentry is the one being offered a shot. A commander that called
/// <see cref="Battle.Move"/> would run straight past a seam on the battle alone.
/// <para>
/// A pause rather than a callback, and that is forced rather than chosen. Input in a game engine
/// arrives across frames — a click is a later event, not a return value — so a callback invoked
/// from inside the turn loop would have to block the whole engine until the player chose, which
/// is not a thing a callback can do. What works is a state the battle sits in. See
/// <c>docs/decisions.md</c> entry 022.
/// </para>
/// <para>
/// The alternative View considered and argued against was making the dispatch public and letting
/// callers drive the turn themselves. That makes every interface re-implement which order goes to
/// which battle method and when a turn ends, which is how a sandbox and a headless match stop
/// replaying identically.
/// </para>
/// </remarks>
public enum WindowAnswer
{
    /// <summary>
    /// Every reactor takes its recommendation and the window resolves at once. What a headless
    /// match wants, and what the turn loop did before there was a choice.
    /// </summary>
    Recommended,

    /// <summary>
    /// The turn stops with the window open, for somebody else to answer and resolve.
    /// </summary>
    HandedOut,
}

/// <summary>
/// An order the commander carried out, and what happened when it did.
/// </summary>
/// <remarks>
/// An <see cref="Order"/> records what an action was <em>chosen</em> on and nothing about what it
/// did, which was fine while the only thing reading the list was a test of the search. It stopped
/// being fine the moment an interface wanted to narrate the enemy's turn: when the AI moves and
/// our sentries answer, there was no window, no outcome and no shot to point at, so the only
/// trace of our own soldiers reacting was that somebody's vitality label had changed. See
/// <c>docs/decisions.md</c> entry 022, which is View asking for exactly this.
/// </remarks>
/// <param name="Carried">
/// False when the battle refused the order, which ends the turn. Rare, and worth reporting rather
/// than swallowing: an order the search offered and the rules would not take is a disagreement
/// between the two, and those are bugs.
/// </param>
public sealed record Act(
    Order Order,
    bool Carried = true,
    MoveOutcome? Moved = null,
    ShotOutcome? Fired = null,
    BlastOutcome? Threw = null)
{
    public OrderKind Kind => Order.Kind;

    /// <summary>The window this act opened, if it opened one. Where reactions are read from.</summary>
    public ReactionWindow? Reactions => Moved?.Reactions;

    public override string ToString() => Carried ? Order.ToString() : $"refused: {Order}";
}

/// <summary>
/// Takes a soldier's turn for it.
/// </summary>
/// <remarks>
/// The search half of the AI. <see cref="Tactician"/> says what one action is worth and knows
/// nothing about where it came from; this generates the actions and picks between them, and it is
/// the only half that had to be written twice — once for a reaction window, which offers a short
/// list somebody else built, and once here, where the list is everywhere the unit could stand
/// crossed with everybody it could shoot from there.
/// <para>
/// <b>Greedy, with one step of lookahead on moves and nothing else.</b> Each pass picks the best
/// single action, does it, and looks again from where that left the unit. That is not optimal
/// play and it is not meant to be: a soldier deciding what to do next from what it can currently
/// see is a fair model of a soldier, and the alternative — searching whole turns — costs
/// combinatorially more for a game whose numbers have never been measured against anything. The
/// lookahead exists only because without it no unit ever moves into a firing position, since the
/// walk itself is worth nothing.
/// </para>
/// <para>
/// <b>It reads only what its soldier knows.</b> Threats come from that unit's own contact file —
/// in view where they stand, or remembered where they were — so a commander cannot walk around
/// a flank it has not seen, and it goes to look at a marker rather than at the man. The
/// consequence, and it is a real one: a unit that knows about nobody scores every option at
/// nothing and stands still. That is correct rather than convenient — there is nothing in the
/// game for it to want yet — and it is the argument for an objective system rather than for
/// cheating.
/// </para>
/// <para>
/// <b>It never fires at a marker.</b> A shot is offered only at a threat in view. The forecast of
/// a shot at a marker is what a move toward it is ranked on, but carrying that shot out would
/// hand the aim to <see cref="Battle.Fire"/>, which resolves against where the target really
/// is, and that would be the battle correcting the soldier's guess for free. So a unit that
/// walks to where it can see the marker looks at the end of its turn, like everybody else, and
/// shoots on the next one if the look found anything. Going to look costs a turn, which is the
/// window the design says the found soldier is owed.
/// </para>
/// </remarks>
public sealed class Commander(
    Battle battle,
    UtilityModel? model = null,
    WindowAnswer windows = WindowAnswer.Recommended)
{
    private readonly Tactician _judge = model is null ? battle.Tactics : new Tactician(battle, model);
    private readonly List<Act> _taken = [];
    private MoveCommitment? _open;
    private Unit? _driving;

    /// <summary>What this commander ranks by. The battle's own judgement unless told otherwise.</summary>
    public Tactician Judge => _judge;

    /// <summary>
    /// The window this commander stopped at, waiting for somebody else to answer it.
    /// </summary>
    /// <remarks>
    /// Only ever set when it was built with <see cref="WindowAnswer.HandedOut"/>. Place into it,
    /// or place nothing at all, and then call <see cref="Resume"/>.
    /// </remarks>
    public ReactionWindow? Waiting => _open?.Window;

    /// <summary>Everything the active unit has done this turn, across however many pauses.</summary>
    public IReadOnlyList<Act> Taken => _taken;

    /// <summary>
    /// Take the active unit's turn, and end it.
    /// </summary>
    /// <remarks>
    /// Returns what it did, in order and with what each one did beside it, so a test or an
    /// interface can read the reasoning rather than the wreckage. The turn ends however it went,
    /// including when the answer was to do nothing at all — which banks the lot, and is frequently
    /// the right answer for a soldier who has not seen anybody.
    /// <para>
    /// A commander handing windows out stops instead of ending the turn, as often as it has to.
    /// See <see cref="WindowAnswer"/> for why that shape and not a callback.
    /// </para>
    /// </remarks>
    public IReadOnlyList<Act> TakeTurn()
    {
        if (_open is not null)
            throw new InvalidOperationException("There is a window open. Resolve it with Resume first.");

        _taken.Clear();
        _driving = battle.Active;

        return _driving is null ? _taken : Run();
    }

    /// <summary>
    /// Resolve the window this commander stopped at, however it was answered, and carry on.
    /// </summary>
    /// <remarks>
    /// The other half of handing a window out. Whatever was placed by now is what answers the
    /// move; placing nothing at all is a real answer and means every reactor holds its fire.
    /// </remarks>
    public IReadOnlyList<Act> Resume()
    {
        if (_open is not { } commitment)
            throw new InvalidOperationException("Nothing is waiting. Call TakeTurn first.");

        _open = null;

        var order = _taken[^1].Order;
        var outcome = battle.Resolve(commitment);
        _taken[^1] = new Act(order, outcome.Moved, Moved: outcome);

        return Run();
    }

    /// <summary>
    /// Pick and carry out one action at a time until the turn is over or a window opens.
    /// </summary>
    /// <remarks>
    /// Every step is conditional on the soldier this commander set out to drive still being the
    /// one whose turn it is, and that is load-bearing rather than defensive. Three things hand
    /// the turn on without the loop asking: being dropped mid-move, having an ambush sprung on
    /// you, and — new — walking off the field, which is the first of the three a unit does to
    /// itself deliberately.
    /// <para>
    /// <b>Ending the turn is conditional on the same test</b>, and it was not, which was a bug
    /// nobody had noticed. A mover dropped mid-move left the loop with the turn already passed to
    /// somebody else, and the unconditional call then ended <em>their</em> turn — banking their
    /// allowance and handing it on before they had done anything with it. It went unseen because
    /// the only thing driving whole turns was a headless match, where a soldier that silently
    /// lost a turn looks like a soldier that decided to do nothing.
    /// </para>
    /// </remarks>
    private IReadOnlyList<Act> Run()
    {
        while (battle.Active is { } unit && unit == _driving)
        {
            if (Next() is not { } order) break;

            var act = Carry(unit, order);
            _taken.Add(act);

            if (_open is not null) return _taken;
            if (!act.Carried) break;
        }

        if (battle.Active == _driving && battle.IsRunning) battle.EndTurn();

        _driving = null;
        return _taken;
    }

    /// <summary>
    /// The best thing the active unit could do right now, or null if the best thing is nothing.
    /// </summary>
    /// <remarks>
    /// Nothing is a real answer and it has a real score: whatever the points are worth banked, out
    /// of <see cref="Tactician.AppraiseHolding"/>. An order has to beat that rather than merely
    /// beat zero, which is what stops a soldier spending its whole turn shuffling for a tenth of a
    /// point and arriving at the end of it with nothing to answer anybody with.
    /// </remarks>
    public Order? Next()
    {
        if (battle.Active is not { } unit) return null;

        var threats = _judge.Known(unit).ToList();
        var holding = _judge.AppraiseHolding(unit, unit.ActionPoints, threats);

        Order? best = null;

        foreach (var order in Options(unit, threats))
            if (order.Score > (best?.Score ?? holding.Score)) best = order;

        return best;
    }

    /// <summary>Everything worth considering, unranked.</summary>
    /// <remarks>
    /// Public because the interface wants exactly this list — "what would you do here" is a
    /// question a player should be able to ask of their own soldier — and because it is the
    /// honest way to test a search: assert over what was on the table, not only over what got
    /// picked.
    /// </remarks>
    public IEnumerable<Order> Options(Unit unit, IReadOnlyList<Threat> threats)
    {
        var inView = threats.Where(t => t.EyesOn).ToList();

        foreach (var order in Shots(unit, UnitPose.Of(unit), inView, ApSource.Turn)) yield return order;
        foreach (var order in Throws(unit, threats)) yield return order;
        foreach (var order in Leaving(unit)) yield return order;
        foreach (var order in Moves(unit, threats)) yield return order;
        foreach (var order in Postures(unit, threats)) yield return order;
        foreach (var order in Watches(unit, threats)) yield return order;
        foreach (var order in Words(unit, threats)) yield return order;
    }

    /// <summary>
    /// Walking off the field, for a soldier standing somewhere its side can leave from.
    /// </summary>
    /// <remarks>
    /// Worth the whole of what the objective is worth, because it is the objective — for this
    /// soldier there is nothing further to do about it. That is a very large number beside
    /// anything a shot can score, deliberately: a squad told to get out and not be seen should
    /// walk out through fire rather than stop to trade, and the design's complaint about
    /// elimination was that the rules made the fight the only thing worth wanting.
    /// </remarks>
    private IEnumerable<Order> Leaving(Unit unit)
    {
        if (battle.ObjectiveOf(unit.Side) is not Withdrawal way) yield break;
        if (!way.IsExit(unit.Position)) yield break;

        yield return new Order(
            OrderKind.Leave,
            new Appraisal(0, 0, _judge.TowardObjective(unit, unit.Position), 0));
    }

    // ---- what is on the table --------------------------------------------------

    /// <summary>
    /// Every shot this unit could take from a pose, one per target per way of firing, each
    /// counted at the credence of the threat it is at.
    /// </summary>
    private IEnumerable<Order> Shots(
        Unit unit, UnitPose from, IReadOnlyList<Threat> threats, ApSource paying, int purse = int.MaxValue)
    {
        foreach (var threat in threats)
            foreach (var mode in unit.Weapon.Modes)
            {
                if (unit.Stats.Costs.Fire(mode.ApCost) > purse) continue;

                var plan = from == UnitPose.Of(unit)
                    ? battle.PlanShot(unit, threat.Unit, mode, 1.0, threat.Where, paying)
                    : battle.PlanThreat(unit, from, threat.Unit, threat.Where, mode);

                if (!plan.CanFire) continue;

                yield return new Order(OrderKind.Fire, _judge.Appraise(plan) * threat.Credence, Shot: plan);
            }
    }

    /// <summary>
    /// Every charge worth lobbing, which is one per threat: at the ground under it.
    /// </summary>
    /// <remarks>
    /// A grenade is aimed at a place rather than a person, and that changes two things about the
    /// search.
    /// <para>
    /// <b>It may be thrown at a marker</b>, unlike a shot. The reason a commander never fires at
    /// one is that <see cref="Battle.Fire"/> resolves against where the target really is, so
    /// carrying the shot out would have the battle correcting the guess for free. A throw has no
    /// such problem: it is aimed at a piece of ground, the ground does not move, and if the
    /// soldier who was standing on it has gone then the grenade is simply wasted. The forecast is
    /// built against the believed threats and counted at their credence, so the decision is made
    /// on the belief and the world answers it.
    /// </para>
    /// <para>
    /// <b>Only the tile under each threat is considered.</b> Offsetting the landing point to
    /// catch two enemies at once, or to keep one of your own out of the radius, is a real
    /// decision and a real search — every node within throwing range crossed with everybody in
    /// the blast — and it is not here. What is here counts allies inside the radius at what they
    /// are worth, so the commander will decline a grenade that would catch its own; it will not
    /// go looking for the throw that avoids them.
    /// </para>
    /// </remarks>
    private IEnumerable<Order> Throws(Unit unit, IReadOnlyList<Threat> threats)
    {
        if (unit.ThrownLeft <= 0 || unit.Thrown is null) yield break;

        // Believed enemies where they are believed to be, and your own squad where it is. A
        // soldier knows where its own side is standing; that is not a leak, it is a radio.
        var candidates = threats
            .Select(t => new BlastCandidate(t.Unit, t.Where, t.Credence))
            .Concat(battle.Allies(unit).Select(BlastCandidate.At))
            .Append(BlastCandidate.At(unit))
            .ToList();

        foreach (var threat in threats)
        {
            var plan = battle.PlanThrow(unit, threat.Where.Position, unit.Thrown, candidates);
            if (!plan.CanThrow) continue;

            yield return new Order(OrderKind.Throw, _judge.Appraise(plan), Throw: plan);
        }
    }

    /// <summary>
    /// Calling a contact in, which is worth what somebody else could do about it.
    /// </summary>
    /// <remarks>
    /// Scored by <see cref="Tactician.AppraiseWord"/>, which has been able to price this since
    /// before there was any way to do it — for a while the search ranked an action the battle had
    /// no method for. It is worth a great deal to a watchman one rung short of firing down an arc
    /// it is already holding, and nothing at all to a squad that already has the contact, so it
    /// generates a candidate that is usually beaten and occasionally the best thing available.
    /// </remarks>
    private IEnumerable<Order> Words(Unit unit, IReadOnlyList<Threat> threats)
    {
        var cost = unit.Stats.Costs.Posturing(battle.Costs.Shout);
        if (cost > unit.ActionPoints || threats.Count == 0) yield break;
        if (!battle.Awareness.Earshot(unit).Any()) yield break;

        foreach (var threat in threats)
            yield return new Order(
                OrderKind.Shout,
                _judge.AppraiseWord(unit, threat.Unit, threat.Where, cost),
                About: threat.Unit);
    }

    /// <summary>
    /// Everywhere worth walking to, and what the unit would do on arrival.
    /// </summary>
    /// <remarks>
    /// Destinations are pruned to somewhere the unit can see a threat from — where the threat
    /// stands, or the marker it is remembered at. Everything else is ground, and there are a
    /// hundred hexes of ground on a small map — scoring all of them means a sight trace per hex
    /// per threat, per decision, several decisions a turn, which is the difference between a
    /// headless match taking a second and taking a minute.
    /// <para>
    /// A marker in view from the far end is what going to look <em>is</em>, and it is ranked the
    /// way a flank is: on the shot the position would open, counted at the chance they are still
    /// there. Nothing about the search changed to make a unit hunt; a remembered position is a
    /// place a shot could be taken at, and the lookahead that already sends a soldier round a
    /// man in cover sends it round a corner it heard something behind.
    /// </para>
    /// </remarks>
    private IEnumerable<Order> Moves(Unit unit, IReadOnlyList<Threat> threats)
    {
        var objective = battle.ObjectiveOf(unit.Side);
        if (threats.Count == 0 && objective is null) yield break;

        var here = objective?.Progress(battle, unit.Position) ?? 0;
        var reach = battle.Reachable(unit);

        foreach (var reached in reach.Destinations)
        {
            if (reached.Node == unit.Position || !battle.CanStopAt(unit, reached.Node)) continue;

            // Facing follows the line of travel, for free, exactly as a real move would leave it.
            var arriving = Arriving(unit, reached);
            var seen = threats.Where(t => battle.Sight.CanSee(arriving.Vantage, t.Where.Vantage)).ToList();

            // Somewhere a threat can be seen from, or somewhere nearer to what the squad came
            // for. Ground that is neither is still just ground, and there are hundreds of hexes
            // of it — pricing all of them is a sight trace per hex per threat, per decision.
            var nearer = objective is not null && objective.Progress(battle, reached.Node) > here;
            if (seen.Count == 0 && !nearer) continue;

            // What the walk itself would tell everybody. The same route the move will take, so
            // the figure it is ranked on is the figure it makes.
            if (!reach.TryGetPath(reached.Node, out var path)) continue;
            var loudness = battle.Loudness(unit, path);

            var worth = _judge.AppraiseMove(unit, arriving, reached.Cost, loudness, threats);

            // What the unit would do once it got there, out of what the walk left it. This is
            // ranking only: the order carried out is the move, and the shot is found again next
            // time round from a position the unit is actually standing in — or, for a marker,
            // after the look at the end of the turn says whether there was anybody to shoot.
            var left = unit.ActionPoints - reached.Cost;
            var opens = Shots(unit, arriving, seen, ApSource.Turn, left)
                .Select(o => o.Worth)
                .DefaultIfEmpty(Appraisal.Nothing)
                .MaxBy(a => a.Score);

            yield return new Order(OrderKind.Move, worth, MoveTo: reached.Node, Opens: opens);
        }
    }

    /// <summary>Turning on the spot, and getting lower or standing back up.</summary>
    private IEnumerable<Order> Postures(Unit unit, IReadOnlyList<Threat> threats)
    {
        if (threats.Count == 0) yield break;

        var here = UnitPose.Of(unit);

        foreach (var threat in threats)
        {
            var toward = battle.HeadingTo(unit.Position, threat.Where.Position);
            if (toward == unit.Facing) continue;
            if (battle.Costs.TurnInPlace > unit.ActionPoints) continue;

            yield return new Order(
                OrderKind.Face,
                _judge.AppraisePosture(unit, here with { Facing = toward }, battle.Costs.TurnInPlace, threats),
                Facing: toward);
        }

        if (battle.Costs.ChangeStance > unit.ActionPoints) yield break;

        foreach (var stance in new[] { Stance.Standing, Stance.Crouching, Stance.Prone })
        {
            if (stance == unit.Stance) continue;

            yield return new Order(
                OrderKind.Stance,
                _judge.AppraisePosture(unit, here with { Stance = stance }, battle.Costs.ChangeStance, threats),
                Stance: stance);
        }
    }

    /// <summary>
    /// Holding an arc, which is worth what it lets you answer with rather than what it does now.
    /// </summary>
    /// <remarks>
    /// The one order whose whole value is in <see cref="Order.Opens"/>: declaring costs points and
    /// achieves nothing this turn. What it buys is a better shot out of a reserve that is smaller
    /// for having paid for it, and the narrower the arc the better that shot — so the choice
    /// between arcs comes out of the same arithmetic as everything else rather than off a
    /// preference list.
    /// </remarks>
    private IEnumerable<Order> Watches(Unit unit, IReadOnlyList<Threat> threats)
    {
        if (threats.Count == 0 || unit.Overwatch is not null) yield break;

        var declaring = battle.Reactions.OverwatchCost;

        foreach (var arc in OverwatchArc.All)
            foreach (var toward in Bearings(unit, threats))
            {
                var cost = declaring + (toward == unit.Facing ? 0 : battle.Costs.TurnInPlace);
                if (cost > unit.ActionPoints) continue;

                // Against the reserve declaring actually leaves, and at the bonus this arc buys.
                var opens = _judge.AppraiseHolding(
                    unit, unit.ActionPoints - cost, threats, arc.AimBonus);

                yield return new Order(
                    OrderKind.Overwatch,
                    new Appraisal(0, 0, 0, _judge.Price(cost)),
                    Arc: arc,
                    Facing: toward,
                    Opens: opens);
            }
    }

    /// <summary>Where the unit is already looking, and where each threat is.</summary>
    private IEnumerable<HexDirection> Bearings(Unit unit, IReadOnlyList<Threat> threats)
    {
        var seen = new HashSet<HexDirection> { unit.Facing };
        yield return unit.Facing;

        foreach (var threat in threats)
        {
            var toward = battle.HeadingTo(unit.Position, threat.Where.Position);
            if (seen.Add(toward)) yield return toward;
        }
    }

    // ---- doing it --------------------------------------------------------------

    /// <summary>The pose a unit would be in having walked there. Moving turns you for nothing.</summary>
    private UnitPose Arriving(Unit unit, ReachedNode reached)
    {
        var facing = reached.Via is { } last
            ? last.From.Hex.DirectionTo(last.To.Hex) ?? unit.Facing
            : unit.Facing;

        return new UnitPose(reached.Node, unit.Stance, facing);
    }

    /// <summary>
    /// Carry an order out and report what happened.
    /// </summary>
    /// <remarks>
    /// A move is the one that can stop here. Committing it pays for the route and builds the
    /// window; whether this commander then resolves the window itself or leaves it open for
    /// somebody else is the whole of what <see cref="WindowAnswer"/> decides, and it is the only
    /// place in the turn loop that differs between the two.
    /// </remarks>
    private Act Carry(Unit unit, Order order)
    {
        switch (order.Kind)
        {
            case OrderKind.Move:
                var commitment = battle.Commit(order.MoveTo!.Value);
                if (!commitment.Committed) return new Act(order, Carried: false);

                if (windows == WindowAnswer.HandedOut)
                {
                    _open = commitment;
                    return new Act(order);
                }

                commitment.Window!.PlaceRecommended();
                var moved = battle.Resolve(commitment);
                return new Act(order, moved.Moved, Moved: moved);

            case OrderKind.Fire:
                var fired = battle.Fire(order.Shot!.Target, order.Shot.Mode);
                return new Act(order, fired.Fired, Fired: fired);

            case OrderKind.Throw:
                var threw = battle.Throw(order.Throw!.Aimed, order.Throw.Item);
                return new Act(order, threw.Went, Threw: threw);

            case OrderKind.Overwatch:
                return new Act(order, battle.SetOverwatch(order.Arc!, order.Facing));

            case OrderKind.Face:
                return new Act(order, battle.Face(order.Facing!.Value));

            case OrderKind.Shout:
                return new Act(order, battle.Shout(order.About!));

            case OrderKind.Leave:
                return new Act(order, battle.Extract());

            default:
                return new Act(order, battle.ChangeStance(order.Stance!.Value));
        }
    }
}
