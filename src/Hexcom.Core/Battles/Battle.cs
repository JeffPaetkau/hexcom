using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Combat;
using Hexcom.Core.Geometry;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Battles;

/// <summary>What happened when a unit was told to move.</summary>
/// <param name="Refusal">Why nothing happened, in words fit to show a player.</param>
/// <param name="Reactions">
/// The window the move opened, and everything that happened inside it. Present whenever the
/// move actually took place, even if nobody was in a position to answer it.
/// </param>
public sealed record MoveOutcome(
    bool Moved,
    IReadOnlyList<TraversalLink> Path,
    int ApSpent,
    string? Refusal,
    ReactionWindow? Reactions = null)
{
    internal static MoveOutcome Refused(string why) => new(false, [], 0, why);

    /// <summary>True if the mover was stopped before it arrived — dropped en route.</summary>
    public bool Interrupted => Reactions?.Interrupted ?? false;
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
        AwarenessModel? awareness = null,
        GunneryModel? gunnery = null,
        ReactionModel? reactions = null)
    {
        Map = map;
        Layout = layout;
        Costs = costs ?? MovementCosts.Default;
        Graph = MovementGraph.Build(map, Costs);
        Sight = new SightSolver(map, layout);
        Awareness = new AwarenessTracker(this, awareness ?? AwarenessModel.Default);
        Gunnery = new Gunnery(gunnery);
        Reactions = reactions ?? ReactionModel.Default;
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

    /// <summary>Whether a shot connects.</summary>
    public Gunnery Gunnery { get; }

    /// <summary>How much of a turn banks for acting out of it. The difficulty dial.</summary>
    public ReactionModel Reactions { get; }

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
    public Unit Deploy(
        string name,
        Side side,
        NodeId position,
        UnitStats? stats = null,
        HexDirection facing = HexDirection.NorthEast,
        Loadout? loadout = null)
    {
        if (!Graph.CanEndTurn(position))
            throw new ArgumentException($"{position} is not somewhere a unit can stand.", nameof(position));

        if (UnitAt(position) is { } sitting)
            throw new ArgumentException($"{sitting.Name} is already at {position}.", nameof(position));

        var unit = new Unit(new UnitId(_nextId++), name, side, position, stats, facing, loadout);
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
            unit.Protection.Recharge();

            // Whatever was held back for reacting expires the moment its own turn comes round,
            // spent or not, and so does any arc it was holding. A watchman that answered nothing
            // gets its turn back; it does not get to accumulate.
            unit.Reserve = 0;
            unit.Overwatch = null;

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
        Bank(unit);
        Advance();
    }

    /// <summary>
    /// Turn what a unit did not spend into a reaction reserve.
    /// </summary>
    /// <remarks>
    /// This is what closes the loop on the action point economy. Sprinting somewhere leaves you
    /// with nothing to answer with; hanging back with points in hand is how you cover an
    /// approach. The choice to reserve is made before you know whether it will pay, which is
    /// the right shape for a decision.
    /// </remarks>
    private void Bank(Unit unit)
    {
        var carried = (int)(unit.ActionPoints * Reactions.ReserveFraction);
        unit.Reserve = carried >= Reactions.ReserveFloor ? carried : 0;
        unit.ActionPoints = 0;
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
        unit.ActionPoints -= cost;

        // The route is committed from here, which is what lets both sides read the future for
        // its duration. The window walks the unit along it and ends it where it got to — at the
        // destination, facing the way it was going, unless somebody stopped it en route.
        var window = new ReactionWindow(this, unit, new CommittedMove(unit.Position, path, unit.Facing, unit.Stance));
        window.Run();

        // Moving is heard immediately, unlike being seen, which waits for someone to look.
        if (unit.InPlay) Awareness.Hear(unit, LoudnessOf(unit, cost, path), Round);

        return new MoveOutcome(true, path, cost, null, window);
    }

    /// <summary>
    /// Hold an arc. Anything hostile that moves inside it during someone else's turn is shot
    /// at, out of the reserve this unit banks when the turn ends.
    /// </summary>
    /// <remarks>
    /// Declaring costs almost nothing on its own; the price of overwatching is the rest of the
    /// turn spent not advancing, and whatever is left over is what the shot comes out of. A
    /// unit that declares an arc and then spends everything getting somewhere has declared
    /// nothing.
    /// </remarks>
    public bool SetOverwatch(OverwatchArc arc, HexDirection? centre = null)
    {
        var unit = RequireActive();
        var watching = centre ?? unit.Facing;

        var cost = Reactions.OverwatchCost + (watching == unit.Facing ? 0 : Costs.TurnInPlace);
        if (unit.ActionPoints < cost) return false;

        unit.ActionPoints -= cost;
        unit.Facing = watching;
        unit.Overwatch = new OverwatchOrder(watching, arc);
        return true;
    }

    /// <summary>Stop holding an arc. Refunds nothing.</summary>
    public bool ClearOverwatch()
    {
        var unit = RequireActive();
        if (unit.Overwatch is null) return false;

        unit.Overwatch = null;
        return true;
    }

    /// <summary>Turn on the spot, to watch somewhere other than where you last went.</summary>
    public bool Face(HexDirection direction)
    {
        var unit = RequireActive();

        if (unit.Facing == direction) return false;
        if (unit.ActionPoints < Costs.TurnInPlace) return false;

        unit.Facing = direction;
        unit.ActionPoints -= Costs.TurnInPlace;
        return true;
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

    // ---- shooting --------------------------------------------------------------

    /// <summary>
    /// What a shot would look like, worked out before anyone commits to it. Nothing changes.
    /// </summary>
    public ShotPlan PlanShot(Unit shooter, Unit target, FireMode? mode = null)
        => PlanShot(
            shooter,
            target,
            mode ?? shooter.Weapon.DefaultMode,
            aimBonus: 1.0,
            UnitPose.Of(target),
            ApSource.Turn);

    /// <summary>
    /// What a shot would look like against a target somewhere other than where it is standing.
    /// </summary>
    /// <remarks>
    /// The reaction window asks this question constantly: not "what would this shot do to them"
    /// but "what would it do to them three ticks from now, when it actually lands". Nothing
    /// about the arithmetic changes — the sight trace runs to a vantage rather than a unit, and
    /// which face the round arrives at is worked out from where they will be facing, so
    /// catching somebody mid-run in the back is a natural consequence rather than a rule.
    /// </remarks>
    public ShotPlan PlanShot(
        Unit shooter,
        Unit target,
        FireMode mode,
        double aimBonus,
        UnitPose targetPose,
        ApSource paying)
    {
        var weapon = shooter.Weapon;
        var sight = Sight.Trace(shooter.Vantage, targetPose.Vantage);
        var face = FaceToward(targetPose, shooter.Position);
        var purse = paying == ApSource.Reserve ? shooter.Reserve : shooter.ActionPoints;

        var refusal =
            !weapon.Modes.Contains(mode) ? $"{weapon.Name} cannot fire {mode.Name}." :
            shooter == target ? "Pick somebody else." :
            !target.InPlay ? "Nothing there to shoot at." :
            !target.IsHostileTo(shooter) ? "That is one of ours." :
            purse < mode.ApCost ? $"Needs {mode.ApCost} points, has {purse}." :
            !sight.CanSee ? "No line on them." :
            sight.Distance > weapon.MaxRange ? $"Out of range at {sight.Distance:0} m." :
            null;

        var chance = refusal is null
            ? Gunnery.HitChance(weapon, mode, sight, shooter.Stance, aimBonus)
            : 0;

        return new ShotPlan(
            shooter, target, weapon, mode, sight, chance, mode.ApCost, face, refusal,
            aimBonus, targetPose, paying);
    }

    /// <summary>
    /// The active unit fires. Every roll comes from the battle generator, so the whole exchange
    /// replays from the seed.
    /// </summary>
    public ShotOutcome Fire(Unit target, FireMode? mode = null)
        => Resolve(PlanShot(shooter: RequireActive(), target, mode));

    /// <summary>
    /// A reactor fires out of turn, out of its reserve, at whatever tick of the window it
    /// placed the shot on. The mover is already standing where the timeline says it is.
    /// </summary>
    internal ShotOutcome FireReaction(ReactionShot shot)
        => Resolve(PlanShot(
            shot.Reactor,
            shot.Target,
            shot.Mode,
            shot.AimBonus,
            UnitPose.Of(shot.Target),
            ApSource.Reserve));

    private ShotOutcome Resolve(ShotPlan plan)
    {
        if (!plan.CanFire) return ShotOutcome.Refused(plan.Refusal!);

        var shooter = plan.Shooter;
        var target = plan.Target;

        if (plan.Paying == ApSource.Reserve) shooter.Reserve -= plan.ApCost;
        else shooter.ActionPoints -= plan.ApCost;

        var shots = new List<ShotHit>(plan.Mode.Shots);
        for (var i = 0; i < plan.Mode.Shots; i++)
        {
            var roll = _rng.NextDouble();
            if (roll >= plan.HitChance)
            {
                shots.Add(new ShotHit(false, roll, null));
                continue;
            }

            var damage = target.Protection.Absorb(plan.FaceHit, plan.Weapon.Kind, plan.Weapon.Damage);
            target.Vitality -= damage.ToVitality;
            shots.Add(new ShotHit(true, roll, damage));

            if (target.IsDown) break;
        }

        AnnounceFire(shooter, target, plan);

        var down = target.IsDown;
        if (down) Withdraw(target);

        return new ShotOutcome(true, shots, plan.ApCost, plan.HitChance, down, null);
    }

    /// <summary>
    /// Firing tells people where you are, and the two weapon families tell them differently.
    /// </summary>
    private void AnnounceFire(Unit shooter, Unit target, ShotPlan plan)
    {
        if (target.InPlay) Awareness.TakeFireFrom(target, shooter, Round);

        Awareness.Hear(shooter, plan.Weapon.Loudness, Round);
        Awareness.Reveal(shooter, plan.Weapon.Flash, Round);
    }

    /// <summary>
    /// Which of <paramref name="target"/>'s faces something at <paramref name="from"/> arrives at.
    /// </summary>
    public HexDirection FaceToward(Unit target, Unit from) => FaceToward(UnitPose.Of(target), from.Position);

    /// <summary>
    /// Which face of a unit in a given pose something arriving from <paramref name="from"/> hits.
    /// </summary>
    public HexDirection FaceToward(UnitPose target, NodeId from)
    {
        var here = Sight.Ground(target.Position).Plane;
        var there = Sight.Ground(from).Plane;

        var offset = there - here;
        if (offset.LengthSquared < Geometry2D.Epsilon) return target.Facing;

        return HexDirectionExtensions.FromBearing(offset.Angle - Layout.RotationRadians);
    }

    /// <summary>
    /// How far off a bearing a place lies, in degrees, seen from somewhere on the map.
    /// </summary>
    /// <remarks>
    /// One answer for two questions that keep turning out to be the same one: how much of an
    /// observer's attention a place has, and whether it falls inside a declared overwatch arc.
    /// The grid can be drawn rotated, so the facing bearing is rotated with it.
    /// </remarks>
    public double AngleOffDegrees(NodeId from, HexDirection direction, NodeId place)
    {
        var here = Sight.Ground(from).Plane;
        var there = Sight.Ground(place).Plane;

        var offset = there - here;
        if (offset.LengthSquared < Geometry2D.Epsilon) return 0;

        var bearing = direction.BearingRadians() + Layout.RotationRadians;
        return Geometry2D.AngleBetween(bearing, offset.Angle) * (180.0 / Math.PI);
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
