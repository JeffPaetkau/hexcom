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
    Appraisal? Opens = null)
{
    /// <summary>What this was ranked on: what it does, plus what it sets up.</summary>
    public double Score => Worth.Score + (Opens?.Score ?? 0);

    public override string ToString() => Kind switch
    {
        OrderKind.Move => $"move to {MoveTo} ({Score:+0.00;-0.00})",
        OrderKind.Fire => $"{Shot?.Mode.Name} at {Shot?.Target.Name} ({Score:+0.00;-0.00})",
        OrderKind.Overwatch => $"watch {Facing} on a {Arc?.Name} arc ({Score:+0.00;-0.00})",
        OrderKind.Face => $"turn to {Facing} ({Score:+0.00;-0.00})",
        _ => $"go {Stance} ({Score:+0.00;-0.00})",
    };
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
public sealed class Commander(Battle battle, UtilityModel? model = null)
{
    private readonly Tactician _judge = model is null ? battle.Tactics : new Tactician(battle, model);

    /// <summary>What this commander ranks by. The battle's own judgement unless told otherwise.</summary>
    public Tactician Judge => _judge;

    /// <summary>
    /// Take the active unit's whole turn and end it.
    /// </summary>
    /// <remarks>
    /// Returns what it did, in order, so a test or an interface can read the reasoning rather than
    /// the wreckage. The turn ends however it went, including when the answer was to do nothing at
    /// all — which banks the lot, and is frequently the right answer for a soldier who has not
    /// seen anybody.
    /// </remarks>
    public IReadOnlyList<Order> TakeTurn()
    {
        var taken = new List<Order>();

        while (battle.Active is { } unit && Next() is { } order)
        {
            if (!Carry(unit, order)) break;
            taken.Add(order);

            // Being shot at, or dropped mid-move, ends the turn for you.
            if (!unit.InPlay || battle.Active != unit) break;
        }

        if (battle.IsRunning) battle.EndTurn();
        return taken;
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
        foreach (var order in Moves(unit, threats)) yield return order;
        foreach (var order in Postures(unit, threats)) yield return order;
        foreach (var order in Watches(unit, threats)) yield return order;
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
        if (threats.Count == 0) yield break;

        var reach = battle.Reachable(unit);

        foreach (var reached in reach.Destinations)
        {
            if (reached.Node == unit.Position || !battle.CanStopAt(unit, reached.Node)) continue;

            // Facing follows the line of travel, for free, exactly as a real move would leave it.
            var arriving = Arriving(unit, reached);
            var seen = threats.Where(t => battle.Sight.CanSee(arriving.Vantage, t.Where.Vantage)).ToList();
            if (seen.Count == 0) continue;

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

    /// <summary>Carry an order out. False if the battle refused it, which ends the turn.</summary>
    private bool Carry(Unit unit, Order order) => order.Kind switch
    {
        OrderKind.Move => battle.Move(order.MoveTo!.Value).Moved,
        OrderKind.Fire => battle.Fire(order.Shot!.Target, order.Shot.Mode).Fired,
        OrderKind.Overwatch => battle.SetOverwatch(order.Arc!, order.Facing),
        OrderKind.Face => battle.Face(order.Facing!.Value),
        _ => battle.ChangeStance(order.Stance!.Value),
    };
}
