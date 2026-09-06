using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Battles;

/// <summary>What happened when a unit was told to move.</summary>
/// <param name="Refusal">Why nothing happened, in words fit to show a player.</param>
public sealed record MoveOutcome(bool Moved, IReadOnlyList<TraversalLink> Path, int ApSpent, string? Refusal)
{
    internal static MoveOutcome Refused(string why) => new(false, [], 0, why);
}

/// <summary>
/// One fight: the map, the units on it, and whose turn it is.
/// </summary>
/// <remarks>
/// Everything a unit does goes through here, and every roll comes from one seeded generator, so
/// a whole battle replays identically from a seed and a list of commands. That is what makes
/// balancing by running thousands of matches headless possible.
/// </remarks>
public sealed class Battle
{
    /// <summary>
    /// Resolution of the battle clock. Each round occupies this many ticks, which leaves ample
    /// room inside a round for initiative to order units without collisions.
    /// </summary>
    public const int TicksPerRound = 1000;

    private readonly Dictionary<UnitId, Unit> _units = [];
    private readonly TurnQueue _queue = new();
    private readonly Random _rng;
    private int _nextId = 1;

    public Battle(
        BattleMap map,
        HexLayout layout,
        MovementCosts? costs = null,
        int seed = 0,
        AwarenessModel? awareness = null)
    {
        Map = map;
        Layout = layout;
        Costs = costs ?? MovementCosts.Default;
        Graph = MovementGraph.Build(map, Costs);
        Sight = new SightSolver(map, layout);
        Awareness = new AwarenessTracker(this, awareness ?? AwarenessModel.Default);
        Seed = seed;
        _rng = new Random(seed);
    }

    public BattleMap Map { get; }
    public HexLayout Layout { get; }
    public MovementCosts Costs { get; }
    public MovementGraph Graph { get; }
    public SightSolver Sight { get; }

    /// <summary>Who knows what about whom, and how they came to know it.</summary>
    public AwarenessTracker Awareness { get; }

    /// <summary>The seed every roll in this battle comes from.</summary>
    public int Seed { get; }

    /// <summary>Zero before the fight starts, then counting up from one.</summary>
    public int Round { get; private set; }

    /// <summary>Whose turn it is, or null before the start and after the last unit falls.</summary>
    public Unit? Active { get; private set; }

    public bool IsRunning => Active is not null;

    public IReadOnlyCollection<Unit> Units => _units.Values;

    public IEnumerable<Unit> InPlay => _units.Values.Where(u => u.InPlay);

    /// <summary>Turns booked but not yet taken, soonest first. This is the order strip.</summary>
    public IReadOnlyList<TurnSlot> TurnOrder => _queue.Upcoming;

    // ---- setting up ------------------------------------------------------------

    /// <summary>Put a unit on the field. Only valid before the fight starts.</summary>
    public Unit Deploy(string name, Side side, NodeId position, UnitStats? stats = null)
    {
        if (!Graph.CanEndTurn(position))
            throw new ArgumentException($"{position} is not somewhere a unit can stand.", nameof(position));

        if (UnitAt(position) is { } sitting)
            throw new ArgumentException($"{sitting.Name} is already at {position}.", nameof(position));

        var unit = new Unit(new UnitId(_nextId++), name, side, position, stats);
        _units[unit.Id] = unit;
        return unit;
    }

    /// <summary>Roll initiative for everyone and hand the first turn to whoever won it.</summary>
    public void Start()
    {
        if (Round != 0) throw new InvalidOperationException("This battle has already started.");

        _queue.Clear();
        foreach (var unit in InPlay.OrderBy(u => u.Id.Value)) Book(unit, round: 1);
        Advance();
    }

    // ---- the turn loop ---------------------------------------------------------

    /// <summary>
    /// Book a unit into a round. Initiative is a rating plus a ten-sided roll, less the weight
    /// of what it is carrying, and a higher result buys a place earlier in the round.
    /// </summary>
    /// <remarks>
    /// Rebooking happens the moment a unit becomes active rather than when its turn ends, so
    /// the queue always holds one future turn per unit and the order strip can look ahead. To
    /// move to a continuous time system later, replace the round arithmetic here with
    /// <c>actAt += whatever the action cost</c>; nothing else has to change.
    /// </remarks>
    private void Book(Unit unit, int round)
    {
        var roll = Math.Max(1, unit.Stats.Initiative - unit.Stats.Encumbrance + _rng.Next(1, 11));
        var offset = TicksPerRound - Math.Min(roll, TicksPerRound - 1);
        _queue.Schedule(new TurnSlot(unit.Id, (long)round * TicksPerRound + offset, roll));
    }

    private void Advance()
    {
        while (_queue.TryDequeue(out var slot))
        {
            // Bookings for units that have left the fight are simply skipped.
            if (!_units.TryGetValue(slot.Unit, out var unit) || !unit.InPlay) continue;

            Round = (int)(slot.ActAt / TicksPerRound);
            Active = unit;
            unit.ActionPoints = unit.Stats.ActionPoints;
            Book(unit, Round + 1);
            return;
        }

        Active = null;
    }

    /// <summary>
    /// Hand the turn on, whether or not the active unit spent everything. The unit takes a look
    /// around before it does, which is the only moment it notices anything.
    /// </summary>
    public void EndTurn()
    {
        var unit = RequireActive();
        Awareness.Observe(unit, Round);
        Advance();
    }

    /// <summary>Take a unit out of the fight. Its booked turns and everything known about it go too.</summary>
    public void Withdraw(Unit unit)
    {
        unit.InPlay = false;
        _queue.Remove(unit.Id);
        Awareness.Forget(unit.Id);
        if (Active == unit) Advance();
    }

    // ---- acting ----------------------------------------------------------------

    /// <summary>Everywhere the active unit could get to on what it has left.</summary>
    public ReachabilityResult Reachable(Unit unit)
        => Pathfinder.Reachable(Graph, unit.Position, unit.ActionPoints, node => CanPassThrough(unit, node));

    /// <summary>Everywhere the active unit could actually finish its move.</summary>
    public IEnumerable<ReachedNode> Destinations(Unit unit)
        => Reachable(unit).Destinations.Where(d => CanStopAt(unit, d.Node));

    /// <summary>Move the active unit, spending the action points the route costs.</summary>
    public MoveOutcome Move(NodeId destination)
    {
        var unit = RequireActive();

        if (unit.Position == destination) return MoveOutcome.Refused("Already there.");
        if (!Graph.Contains(destination)) return MoveOutcome.Refused("There is nothing there to move to.");
        if (UnitAt(destination) is { } sitting) return MoveOutcome.Refused($"{sitting.Name} is standing there.");
        if (!Graph.CanEndTurn(destination)) return MoveOutcome.Refused("No room to stand there.");

        var reach = Reachable(unit);
        if (!reach.TryGetPath(destination, out var path))
            return MoveOutcome.Refused("Out of reach this turn.");

        var cost = reach.CostTo(destination)!.Value;
        unit.Position = destination;
        unit.ActionPoints -= cost;

        // Moving is heard immediately, unlike being seen, which waits for someone to look.
        Awareness.Hear(unit, LoudnessOf(unit, cost, path), Round);

        return new MoveOutcome(true, path, cost, null);
    }

    /// <summary>
    /// How much racket a move made. Effort, the worst surface crossed, and how low the unit was
    /// carrying itself: sprinting over gravel carries a long way, crawling over grass barely
    /// carries at all.
    /// </summary>
    private double LoudnessOf(Unit unit, int apSpent, IReadOnlyList<TraversalLink> path)
    {
        var surface = path
            .Select(link => Map.GetTile(link.To.Tile)?.Ground.NoiseFactor ?? 1.0)
            .DefaultIfEmpty(1.0)
            .Max();

        return apSpent * surface * StanceProfile.For(unit.Stance).NoiseFactor;
    }

    /// <summary>Drop to a crouch, go prone, or stand back up.</summary>
    public bool ChangeStance(Stance stance)
    {
        var unit = RequireActive();

        if (unit.Stance == stance) return false;
        if (unit.ActionPoints < Costs.ChangeStance) return false;

        unit.Stance = stance;
        unit.ActionPoints -= Costs.ChangeStance;
        return true;
    }

    // ---- questions anyone can ask ----------------------------------------------

    public Unit? UnitAt(NodeId node) => _units.Values.FirstOrDefault(u => u.InPlay && u.Position == node);

    public Unit? GetUnit(UnitId id) => _units.GetValueOrDefault(id);

    /// <summary>Somewhere this unit could stop, ignoring whether it can afford to get there.</summary>
    public bool CanStopAt(Unit unit, NodeId node)
    {
        if (!Graph.CanEndTurn(node)) return false;

        var sitting = UnitAt(node);
        return sitting is null || sitting == unit;
    }

    /// <summary>You can squeeze past your own side. You cannot walk through the enemy.</summary>
    private bool CanPassThrough(Unit mover, NodeId node)
    {
        var sitting = UnitAt(node);
        return sitting is null || !sitting.IsHostileTo(mover);
    }

    public SightResult Look(Unit observer, Unit target) => Sight.Trace(observer.Vantage, target.Vantage);

    public bool CanSee(Unit observer, Unit target)
        => observer.InPlay && target.InPlay && Sight.CanSee(observer.Vantage, target.Vantage);

    public IEnumerable<Unit> VisibleTo(Unit observer)
        => InPlay.Where(u => u != observer && CanSee(observer, u));

    public IEnumerable<Unit> Enemies(Unit unit) => InPlay.Where(u => u.IsHostileTo(unit));

    /// <summary>
    /// The largest share of this unit's silhouette any enemy currently has in view, from zero
    /// to one.
    /// </summary>
    /// <remarks>
    /// This one is reported to the player exactly. It is information about their own soldier,
    /// and hiding it would be fog rather than tension — unlike what an enemy believes, which
    /// they only ever get coarsely.
    /// </remarks>
    public double ExposureOf(Unit unit)
    {
        var worst = 0.0;
        foreach (var enemy in Enemies(unit))
        {
            var sight = Look(enemy, unit);
            if (sight.CanSee && sight.Exposure > worst) worst = sight.Exposure;
        }
        return worst;
    }

    /// <summary>The highest state of alarm any enemy currently holds about this unit.</summary>
    public AwarenessState HighestAwarenessOf(Unit unit) => Awareness.HighestAwarenessOf(unit.Id);

    public IEnumerable<Unit> Allies(Unit unit) => InPlay.Where(u => u != unit && u.Side == unit.Side);

    /// <summary>Sides that still have someone standing, neutrals aside.</summary>
    public IEnumerable<Side> SidesInPlay
        => InPlay.Select(u => u.Side).Where(s => s != Side.Neutral).Distinct();

    /// <summary>True once at most one side is left with anyone on the field.</summary>
    public bool IsDecided => SidesInPlay.Count() <= 1;

    private Unit RequireActive()
        => Active ?? throw new InvalidOperationException("No turn is in progress. Call Start first.");
}
