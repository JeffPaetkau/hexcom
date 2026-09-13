using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Combat;
using Hexcom.Core.Geometry;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
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
/// A move that has been paid for and not yet resolved.
/// </summary>
/// <remarks>
/// The state an interface needs and a single call cannot give it. Input arrives across frames —
/// a click is a later event, not a return value — so a player cannot answer a question asked from
/// inside <see cref="Battle.Move"/>, and no callback can wait for them without stopping the
/// engine. What works is a state the battle sits in: a window built and not yet run, which the
/// interface can draw for as many frames as it likes, place into, and resolve when the player is
/// done. See <c>docs/decisions.md</c> entries 004 and 022, the second of which is View saying
/// which of the two shapes it can actually use.
/// <para>
/// It carries the receipt as well as the window because <see cref="Battle.Resolve(MoveCommitment)"/> needs both
/// and so does the caller: the route was priced and paid for at <see cref="Battle.Commit"/>, and
/// a refusal has to come back from somewhere.
/// </para>
/// </remarks>
/// <param name="Window">The window the move opened, with its offers built and nothing placed.</param>
/// <param name="Refusal">Why nothing was committed, in words fit to show a player.</param>
public sealed record MoveCommitment(
    ReactionWindow? Window,
    IReadOnlyList<TraversalLink> Path,
    int ApCost,
    string? Refusal)
{
    internal static MoveCommitment Refused(string why) => new(null, [], 0, why);

    /// <summary>True when the move is paid for and waiting to be resolved.</summary>
    public bool Committed => Refusal is null;

    /// <summary>The outcome this commitment turns into if it is refused rather than resolved.</summary>
    internal MoveOutcome AsRefusal() => MoveOutcome.Refused(Refusal!);
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
    private readonly List<Mine> _mines = [];
    private readonly List<Objective> _objectives = [];
    private readonly Random _rng;
    private int _nextId = 1;

    public Battle(
        BattleMap map,
        HexLayout layout,
        MovementCosts? costs = null,
        int seed = 0,
        AwarenessModel? awareness = null,
        GunneryModel? gunnery = null,
        ReactionModel? reactions = null,
        UtilityModel? utility = null,
        BlastModel? blast = null)
    {
        Map = map;
        Layout = layout;
        Costs = costs ?? MovementCosts.Default;
        Graph = MovementGraph.Build(map, Costs);
        Sight = new SightSolver(map, layout);
        Lob = new LobSolver(Sight, map, layout);
        Awareness = new AwarenessTracker(this, awareness ?? AwarenessModel.Default);
        Gunnery = new Gunnery(gunnery);
        Ordnance = new Ordnance(blast);
        Reactions = reactions ?? ReactionModel.Default;
        Tactics = new Tactician(this, utility);
        Seed = seed;
        _rng = new Random(seed);
    }

    public BattleMap Map { get; }
    public HexLayout Layout { get; }
    public MovementCosts Costs { get; }
    public MovementGraph Graph { get; }
    public SightSolver Sight { get; }

    /// <summary>Whether a thrown object clears what is in the way, and where it comes down.</summary>
    public LobSolver Lob { get; }

    /// <summary>Who knows what about whom, and how they came to know it.</summary>
    public AwarenessTracker Awareness { get; }

    /// <summary>Whether a shot connects.</summary>
    public Gunnery Gunnery { get; }

    /// <summary>What a charge going off does to whoever is standing near it.</summary>
    public Ordnance Ordnance { get; }

    /// <summary>How much of a turn banks for acting out of it. The difficulty dial.</summary>
    public ReactionModel Reactions { get; }

    /// <summary>
    /// What an action is worth. What the AI ranks by, and what an interface can show a player.
    /// </summary>
    /// <remarks>
    /// One judgement, available to both sides and to whatever is drawing the screen, because the
    /// alternative is an AI reasoning from something the player cannot be shown.
    /// </remarks>
    public Tactician Tactics { get; }

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

    /// <summary>
    /// What each side is on the field to do. Empty means the old rule: last side standing.
    /// </summary>
    public IReadOnlyList<Objective> Objectives => _objectives;

    /// <summary>Give a side something to do. Only valid before the fight starts.</summary>
    /// <remarks>
    /// Content decides which objective a mission carries and where; these rules decide what one
    /// <em>is</em>. A battle with none behaves exactly as it always did, which is what keeps
    /// every existing scenario and every test that predates objectives honest.
    /// </remarks>
    public void SetObjective(Objective objective)
    {
        if (Round != 0) throw new InvalidOperationException("Objectives are set before the fight starts.");
        _objectives.RemoveAll(o => o.Side == objective.Side);
        _objectives.Add(objective);
    }

    /// <summary>What this side came to do, if anything.</summary>
    public Objective? ObjectiveOf(Side side) => _objectives.FirstOrDefault(o => o.Side == side);

    /// <summary>
    /// Tell one side, before the fight, that a soldier of the other is standing where it is
    /// standing — as firmly as the rung says. Only valid before the fight starts.
    /// </summary>
    /// <remarks>
    /// The <em>presence</em> part of a briefing, handed to the rules. Content decides what a
    /// mission tells its squad and how sure it is; this hands every soldier of the side the same
    /// marker, through <see cref="AwarenessTracker.Brief"/>, at the post the soldier is actually
    /// deployed to — because a briefing that named the wrong post would be a different mission,
    /// and the format can say that by not briefing the post at all.
    /// </remarks>
    public void Brief(Side side, Unit about, AwarenessState state)
    {
        if (Round != 0) throw new InvalidOperationException("A side is briefed before the fight starts.");
        if (about.Side == side) throw new ArgumentException("A side is briefed about the other side.", nameof(about));

        foreach (var unit in _units.Values.Where(u => u.Side == side))
            Awareness.Brief(unit, about, about.Position, state, about.Facing);
    }

    /// <summary>
    /// Every charge still lying on the field.
    /// </summary>
    /// <remarks>
    /// Reported plainly, and contract 3 is why that is not a leak. A mine is a fact about the
    /// ground rather than a belief anybody holds, so the asymmetry the interface has to honour is
    /// not here but in what it chooses to draw: <see cref="MinesOf"/> is the query a player
    /// interface wants, and it is the one an enemy commander must not ask.
    /// </remarks>
    public IEnumerable<Mine> Mines => _mines.Where(m => !m.Spent);

    /// <summary>The charges one side laid, which is the set that side is allowed to see.</summary>
    public IEnumerable<Mine> MinesOf(Side side) => Mines.Where(m => m.LaidBy == side);

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

        // An objective wants to know how long the job is, and the only moment that is knowable
        // is now: everybody is deployed and nobody has moved. See Objective.Begin.
        foreach (var objective in _objectives) objective.Begin(this);

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

        // The same look, asked a second question: was that the thing we came to see. Nothing but
        // a reconnaissance answers, and it answers here because this is the only moment in the
        // game at which anybody sees anything at all.
        if (ObjectiveOf(unit.Side) is { } objective) objective.Looked(this, unit);

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
        unit.Reserve = Reactions.Banked(unit.ActionPoints);
        unit.ActionPoints = 0;
    }

    /// <summary>
    /// Take a unit out of the fight. Its booked turns and everything known about it go too.
    /// </summary>
    /// <remarks>
    /// The reading the other side held is sampled <b>here</b>, before the forgetting, and kept on
    /// the unit. Asking afterwards is not an option: the next line wipes every contact about this
    /// soldier, so a win condition of the form <em>get out with nobody above a suspicion</em>
    /// would read Unaware for everybody, trivially and always. See <see cref="Departure"/>.
    /// </remarks>
    /// <param name="kind">
    /// Whether the soldier walked off or was carried off. Nothing before objectives had to tell
    /// the two apart, and a win condition is exactly the thing that does.
    /// </param>
    public void Withdraw(Unit unit, DepartureKind kind = DepartureKind.Down)
    {
        unit.Left = new Departure(kind, Round, HighestAwarenessOf(unit));
        _queue.Remove(unit.Id);
        Awareness.Forget(unit.Id);
        if (Active == unit) Advance();
    }

    /// <summary>
    /// The active unit works on whatever it came to do, spending what it can spare on it.
    /// </summary>
    /// <remarks>
    /// Priced in action points because that is what the rest of the mission is priced in: the job
    /// is so many points of somebody's turn, and it does not care whose. A squad that splits it
    /// between two soldiers finishes sooner, which is what a squad is for.
    /// <para>
    /// It spends everything it can rather than a fixed chunk, so a soldier that walked most of the
    /// way there still puts its remaining points into the charge rather than standing over it with
    /// nothing to do. Returns what went in, which is nought when there is nothing to work on.
    /// </para>
    /// </remarks>
    public int Work()
    {
        var unit = RequireActive();

        if (ObjectiveOf(unit.Side) is not Sabotage job) return 0;
        if (job.Place != unit.Position) return 0;

        var spend = Math.Min(unit.ActionPoints, job.Owing);
        if (spend <= 0) return 0;

        unit.ActionPoints -= spend;
        job.Work(spend);
        return spend;
    }

    /// <summary>
    /// The active unit walks off the field, from somewhere its side may leave.
    /// </summary>
    /// <remarks>
    /// Free, and the price is having walked there. Charging for the last step out would be
    /// charging twice for the whole approach that got the soldier to it.
    /// </remarks>
    public bool Extract()
    {
        var unit = RequireActive();

        if (ObjectiveOf(unit.Side) is not Sortie sortie) return false;
        if (!sortie.IsExit(unit.Position)) return false;

        Withdraw(unit, DepartureKind.Extracted);
        return true;
    }

    // ---- acting ----------------------------------------------------------------

    /// <summary>Everywhere the active unit could get to on what it has left.</summary>
    /// <remarks>
    /// Priced for this soldier rather than off the graph, so a heavy trooper and a scout reading
    /// the same ground get different answers about how far they can cross it.
    /// </remarks>
    public ReachabilityResult Reachable(Unit unit)
        => Pathfinder.Reachable(
            Graph,
            unit.Position,
            unit.ActionPoints,
            node => CanPassThrough(unit, node),
            MovementPrice(unit));

    /// <summary>
    /// What this soldier, carrying itself the way it currently is, pays per link.
    /// </summary>
    /// <remarks>
    /// The one place movement gets priced. Everything that needs to agree about what a route
    /// costs — the reachable set, the points deducted, and the tick clock a reaction window runs
    /// on — goes through here, because if any of them disagreed the window would resolve against
    /// a timeline the mover never paid for.
    /// </remarks>
    public Func<TraversalLink, int> MovementPrice(Unit unit)
    {
        var stance = StanceProfile.For(unit.Stance).MovementFactor;
        return link => unit.Stats.Costs.Move(link.ApCost, stance);
    }

    /// <summary>Everywhere the active unit could actually finish its move.</summary>
    public IEnumerable<ReachedNode> Destinations(Unit unit)
        => Reachable(unit).Destinations.Where(d => CanStopAt(unit, d.Node));

    /// <summary>
    /// Commit the active unit to a route and pay for it, without resolving what answers it.
    /// </summary>
    /// <remarks>
    /// The first half of <see cref="Move"/>, and the seam an interface needs. Everything up to
    /// and including building the window happens here — the route is priced, the points are
    /// spent, the offers are made — and nothing is placed. The caller may then draw the window,
    /// place into it over as long as it likes, and hand it back to <see cref="Resolve(MoveCommitment)"/>.
    /// <para>
    /// The move is genuinely committed at this point, which is the property the whole reaction
    /// timeline rests on: both sides know the future for its duration precisely because it is no
    /// longer in doubt. The mover has not stepped yet — it stands at the start until
    /// <see cref="Resolve(MoveCommitment)"/> walks it along — so anything reading the field while the window is
    /// open sees a soldier who has paid for a walk it has not taken.
    /// </para>
    /// </remarks>
    public MoveCommitment Commit(NodeId destination)
    {
        var unit = RequireActive();

        if (unit.Position == destination) return MoveCommitment.Refused("Already there.");
        if (!Graph.Contains(destination)) return MoveCommitment.Refused("There is nothing there to move to.");
        if (UnitAt(destination) is { } sitting) return MoveCommitment.Refused($"{sitting.Name} is standing there.");
        if (!Graph.CanEndTurn(destination)) return MoveCommitment.Refused("No room to stand there.");

        var reach = Reachable(unit);
        if (!reach.TryGetPath(destination, out var path))
            return MoveCommitment.Refused("Out of reach this turn.");

        var cost = reach.CostTo(destination)!.Value;
        unit.ActionPoints -= cost;

        var window = ReactionWindow.ForMove(
            this, unit, new CommittedMove(unit.Position, path, unit.Facing, unit.Stance, MovementPrice(unit)));

        return new MoveCommitment(window, path, cost, null);
    }

    /// <summary>
    /// Run a committed move: resolve the window, walk the mover, and make the noise.
    /// </summary>
    /// <remarks>
    /// The second half. Whatever was placed into the window by then is what answers the move —
    /// the recommendations, a player's own choices, or nothing at all.
    /// </remarks>
    public MoveOutcome Resolve(MoveCommitment commitment)
    {
        if (!commitment.Committed) return commitment.AsRefusal();

        var window = commitment.Window!;
        var unit = window.Mover;

        window.Resolve();

        // A trap springs once. Whoever it caught, everybody who armed for it is done waiting.
        if (window.SprungBy is { } springer) StandDown(springer.Side);

        // Moving is heard immediately, unlike being seen, which waits for someone to look.
        if (unit.InPlay) Awareness.Hear(unit, Loudness(unit, commitment.Path), Round);

        return new MoveOutcome(true, commitment.Path, commitment.ApCost, null, window);
    }

    /// <summary>Move the active unit, spending the action points the route costs.</summary>
    /// <remarks>
    /// The two halves in sequence with every recommendation taken between them, which is what
    /// every caller that does not want to answer a window by hand wants — the turn loop, a
    /// headless match, and a test. An interface calls <see cref="Commit"/> and
    /// <see cref="Resolve(MoveCommitment)"/> instead and does its own placing in the gap.
    /// </remarks>
    public MoveOutcome Move(NodeId destination)
    {
        var commitment = Commit(destination);
        if (!commitment.Committed) return commitment.AsRefusal();

        commitment.Window!.PlaceRecommended();
        return Resolve(commitment);
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
        unit.Overwatch = new HeldArc(watching, arc);
        return true;
    }

    /// <summary>Stop holding an arc. Refunds nothing.</summary>
    public bool ClearOverwatch()
    {
        var unit = RequireActive();
        if (unit.Overwatch is null && unit.Ambush is null) return false;

        unit.Overwatch = null;
        unit.Ambush = null;
        return true;
    }

    /// <summary>
    /// Arm against an agreed trigger, as part of an ambush. Anything the squad springs it on gets
    /// answered by every member at once, before it acts.
    /// </summary>
    /// <remarks>
    /// The answer to the problem interleaved initiative creates. Normally the enemy acts between
    /// your shots and a coordinated opening is impossible to execute; armed, every member resolves
    /// in the same window. It costs each of them a turn spent not advancing, which is what makes
    /// setting one a commitment rather than a free posture.
    /// </remarks>
    public bool Arm(OverwatchArc arc, HexDirection? centre = null)
    {
        var unit = RequireActive();
        var watching = centre ?? unit.Facing;

        var cost = Reactions.AmbushCost + (watching == unit.Facing ? 0 : Costs.TurnInPlace);
        if (unit.ActionPoints < cost) return false;

        unit.ActionPoints -= cost;
        unit.Facing = watching;
        unit.Ambush = new HeldArc(watching, arc);
        unit.Overwatch = null; // one posture at a time
        return true;
    }

    /// <summary>
    /// Say now. Every armed unit on this side that can see the target answers in one window,
    /// before the target does anything about any of it.
    /// </summary>
    /// <remarks>
    /// The springer fires out of its own turn; everybody else fires out of the reserve they
    /// banked when they armed. Springing calls the contact in first, so the squad has to be able
    /// to <em>hear</em> each other for the trap to close — which puts the radio operator back at
    /// the centre of things, and makes an ambusher who cannot be reached simply not fire.
    /// </remarks>
    public ReactionWindow? SpringAmbush(Unit target, FireMode? mode = null)
    {
        var springer = RequireActive();

        if (springer.Ambush is not { } arc) return null;
        if (!target.InPlay || !target.IsHostileTo(springer)) return null;
        if (!arc.Covers(this, springer.Position, target.Position)) return null;
        if (!CanSee(springer, target)) return null;

        // One of them says now, and everybody who was waiting hears it.
        Awareness.CallOut(springer, target.Id, Round);

        var window = ReactionWindow.ForAmbush(this, target, springer);
        if (window.Offers.Count == 0) return null;

        if (mode is not null &&
            window.Offers.FirstOrDefault(o => o.Reactor == springer) is { } mine &&
            mine.Options.FirstOrDefault(o => o.Mode == mode) is { } chosen)
        {
            window.Place(chosen);
        }

        window.Run();
        StandDown(springer.Side);

        return window;
    }

    /// <summary>Everybody on a side stops waiting. A trap only springs once.</summary>
    internal void StandDown(Side side)
    {
        foreach (var unit in _units.Values.Where(u => u.Side == side)) unit.Ambush = null;
    }

    /// <summary>Turn on the spot, to watch somewhere other than where you last went.</summary>
    /// <remarks>
    /// Priced through the soldier own <see cref="CostProfile"/> like moving and firing. It was
    /// not, for a while, and that was the one rule about prices this project states plainly being
    /// broken in the two places nobody read — see <c>docs/decisions.md</c> entry 012.
    /// </remarks>
    public bool Face(HexDirection direction)
    {
        var unit = RequireActive();
        var cost = unit.Stats.Costs.Posturing(Costs.TurnInPlace);

        if (unit.Facing == direction) return false;
        if (unit.ActionPoints < cost) return false;

        unit.Facing = direction;
        unit.ActionPoints -= cost;
        return true;
    }

    /// <summary>
    /// Call a contact in on your own turn, so somebody who can do something about it knows.
    /// </summary>
    /// <remarks>
    /// The turn action behind a thing the scorer could already price and nobody could do.
    /// <see cref="Tactician.AppraiseWord"/> has always said what shouting is worth and
    /// <see cref="ReactionAction.Shout"/> has always been placeable inside a window, so for a
    /// while the AI ranked an action it had no way to take and the interface had nothing to offer
    /// a player. See <c>docs/decisions.md</c> entry 012.
    /// <para>
    /// Word travels the ordinary way and arrives at a discount, so this is worth a great deal to a
    /// watchman one rung short of firing down the arc it is already holding, and worth nothing at
    /// all to a squad that already has the contact. It is not a free look: what is passed on is
    /// what the caller holds, and calling in somebody you have merely heard passes on a rumour.
    /// </para>
    /// </remarks>
    public bool Shout(Unit about)
    {
        var unit = RequireActive();
        var cost = unit.Stats.Costs.Posturing(Costs.Shout);

        if (unit.ActionPoints < cost) return false;
        if (Awareness.Of(unit.Id, about.Id).State == AwarenessState.Unaware) return false;

        unit.ActionPoints -= cost;
        Awareness.CallOut(unit, about.Id, Round);
        return true;
    }

    /// <summary>
    /// How much racket a move made. Effort, the worst surface crossed, and how low the unit was
    /// carrying itself: sprinting over gravel carries a long way, crawling over grass barely
    /// carries at all.
    /// </summary>
    /// <remarks>
    /// Effort is the <b>listed</b> price of the ground crossed, not what this soldier paid for
    /// it. Otherwise stance counts twice and cancels itself out: crawling costs three times as
    /// much, so a crawler spending three times the points to cross one hex would be almost
    /// exactly as loud as somebody strolling across it, which is the opposite of the point. The
    /// same reasoning says a slow soldier is not noisier than a quick one over the same route.
    /// <para>
    /// Public so a route can be priced before it is taken. <see cref="Move"/> uses exactly this
    /// figure afterwards, so what an AI or a cursor line was told a route would make is what it
    /// makes; pair it with <see cref="AwarenessTracker.WouldHear"/> for who would hear it.
    /// </para>
    /// </remarks>
    public double Loudness(Unit unit, IReadOnlyList<TraversalLink> path)
    {
        var surface = path
            .Select(link => Map.GetTile(link.To.Tile)?.Ground.NoiseFactor ?? 1.0)
            .DefaultIfEmpty(1.0)
            .Max();

        var effort = path.Sum(link => link.ApCost);

        return effort * surface * StanceProfile.For(unit.Stance).NoiseFactor;
    }

    // ---- reach -----------------------------------------------------------------

    /// <summary>
    /// Whether a weapon carried from one place could touch somebody standing at another.
    /// </summary>
    /// <remarks>
    /// Two instruments, because there are two kinds of weapon. Anything fired or thrown is
    /// measured in metres along the sight line, and anything with
    /// <see cref="WeaponReach.Adjacent"/> reach is not measured at all: it asks the movement
    /// graph, which already knows about the wall in between and the storey above.
    /// <para>
    /// The graph is the right authority and not merely a convenient one. A blade reaches over a
    /// sandbag line because a soldier can vault it, does not reach through a building wall because
    /// nothing crosses one, and does not reach a man on a three metre roof because nobody climbs
    /// that — which is the behaviour <c>docs/decisions.md</c> entry 008 asked to keep, arrived at
    /// on purpose rather than by accident of measuring a knife along the line of a rifle.
    /// </para>
    /// </remarks>
    public bool InReach(WeaponProfile weapon, NodeId from, NodeId at, SightResult sight)
        => weapon.Reach == WeaponReach.Adjacent ? Adjacent(from, at) : weapon.Reaches(sight.Distance);

    /// <summary>
    /// Whether two places are one traversal apart, which is what adjacency means here.
    /// </summary>
    /// <remarks>
    /// The graph rather than the grid, so it is adjacency a soldier could actually act across
    /// rather than adjacency on paper. The same place counts: two soldiers cannot share a node,
    /// but a pose weighed up before the walk can sit on one somebody else is standing in.
    /// </remarks>
    public bool Adjacent(NodeId a, NodeId b)
        => a == b || Graph.LinksFrom(a).Any(link => link.To == b);

    // ---- shooting --------------------------------------------------------------

    /// <summary>
    /// What a shot would look like, worked out before anyone commits to it. Nothing changes.
    /// </summary>
    public ShotPlan PlanShot(Unit shooter, Unit target, FireMode? mode = null, BodyFace? calledAt = null)
        => PlanShot(
            shooter,
            target,
            mode ?? shooter.Weapon.DefaultMode,
            aimBonus: 1.0,
            UnitPose.Of(target),
            ApSource.Turn,
            calledAt);

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
        ApSource paying,
        BodyFace? calledAt = null)
        => Plan(shooter, UnitPose.Of(shooter), target, targetPose, mode, aimBonus, paying, calledAt, affordable: true);

    /// <summary>
    /// What <paramref name="shooter"/> could do to a soldier standing like that, if it had the
    /// points. The question you ask about a <em>threat</em> rather than about this moment.
    /// </summary>
    /// <remarks>
    /// Two things are deliberately left out that
    /// <see cref="PlanShot(Unit, Unit, FireMode, double, UnitPose, ApSource, BodyFace?)"/> insists
    /// on, and both for the same reason: posture is a bet on the next round, not this one.
    /// <para>
    /// The affordability test goes, because turning to face somebody who has just spent their
    /// whole turn walking past you is worth exactly what turning to face somebody who has not is
    /// worth — the round after, they both have a full allowance again. A threat with an empty
    /// purse is still a threat.
    /// </para>
    /// <para>
    /// And the shooter gets a pose of its own, because the soldier you are weighing up is often
    /// not where it will be shooting from. Inside a reaction window the mover is halfway along a
    /// route; the question worth asking is what it does to you from the end of it.
    /// </para>
    /// </remarks>
    public ShotPlan PlanThreat(
        Unit shooter,
        UnitPose shooterPose,
        Unit target,
        UnitPose targetPose,
        FireMode? mode = null,
        double aimBonus = 1.0)
        => Plan(
            shooter, shooterPose, target, targetPose,
            mode ?? shooter.Weapon.DefaultMode,
            aimBonus, ApSource.Turn, calledAt: null, affordable: false);

    private ShotPlan Plan(
        Unit shooter,
        UnitPose shooterPose,
        Unit target,
        UnitPose targetPose,
        FireMode mode,
        double aimBonus,
        ApSource paying,
        BodyFace? calledAt,
        bool affordable)
    {
        var weapon = shooter.Weapon;
        var sight = Sight.Trace(shooterPose.Vantage, targetPose.Vantage);
        var aspects = FacesPresentedTo(targetPose, shooterPose.Position);
        var purse = paying == ApSource.Reserve ? shooter.Reserve : shooter.ActionPoints;

        // The list price is what the action is; what this soldier pays for it is about them.
        var cost = shooter.Stats.Costs.Fire(mode.ApCost);

        var reaches = InReach(weapon, shooterPose.Position, targetPose.Position, sight);

        var refusal =
            !weapon.Modes.Contains(mode) ? $"{weapon.Name} cannot fire {mode.Name}." :
            shooter == target ? "Pick somebody else." :
            !target.InPlay ? "Nothing there to shoot at." :
            !target.IsHostileTo(shooter) ? "That is one of ours." :
            affordable && purse < cost ? $"Needs {cost} points, has {purse}." :
            !sight.CanSee ? "No line on them." :
            !reaches && weapon.Reach == WeaponReach.Adjacent ? "Not close enough to reach them." :
            !reaches ? $"Out of range at {sight.Distance:0} m." :
            calledAt is not null && !shooter.Stats.CanCallShots ? $"{shooter.Name} cannot place a round like that." :
            calledAt is { } wanted && aspects.All(a => a.Face != wanted) ? $"Their {wanted} is not in view." :
            null;

        var chance = refusal is null
            ? Gunnery.HitChance(weapon, mode, sight, shooterPose.Stance, aimBonus, reaches)
              * (calledAt is null ? 1.0 : Gunnery.Model.CalledShotAccuracy)
            : 0;

        // Flattened against the head-on case, so the bearing decides which plate wears without
        // also deciding how much gets through it.
        var scale = Gunnery.NormalisingScale(weapon.Kind, aspects);
        var glancing = 1.0;

        if (aspects.Count > 0)
        {
            // A called shot takes the angle of the plate it named; anything else takes the
            // average over the plates it might find. Normalisation makes that average the same
            // from every bearing, so it comes out as the head-on figure whichever way they face.
            if (calledAt is { } named && aspects.FirstOrDefault(a => a.Face == named) is { Share: > 0 } picked)
            {
                glancing = Gunnery.GlancingFactor(weapon.Kind, picked.ObliquityDegrees) * scale;
            }
            else
            {
                var mean = 0.0;
                foreach (var aspect in aspects)
                    mean += aspect.Share * Gunnery.GlancingFactor(weapon.Kind, aspect.ObliquityDegrees);
                glancing = mean * scale;
            }
        }

        return new ShotPlan(
            shooter, target, weapon, mode, sight, chance, cost, aspects, refusal,
            aimBonus, targetPose, paying, glancing, scale, calledAt, shooterPose);
    }

    /// <summary>
    /// The active unit fires. Every roll comes from the battle generator, so the whole exchange
    /// replays from the seed.
    /// </summary>
    /// <param name="calledAt">
    /// A particular side to place the round on, for shooters who can. Left null, the geometry
    /// decides — which is what happens for everybody else.
    /// </param>
    public ShotOutcome Fire(Unit target, FireMode? mode = null, BodyFace? calledAt = null)
        => Resolve(PlanShot(shooter: RequireActive(), target, mode, calledAt));

    /// <summary>
    /// A reactor acts out of turn, out of its reserve, at whatever tick of the window it placed
    /// the action on. The mover is already standing where the timeline says it is.
    /// </summary>
    /// <remarks>
    /// Only a shot reports anything back; turning, dropping and shouting change the reactor
    /// rather than the mover. All of them are paid for the same way, because the reserve is the
    /// single resource every way of acting out of turn draws on.
    /// </remarks>
    internal ShotOutcome? ResolveReaction(ReactionPlacement placement)
    {
        var reactor = placement.Reactor;

        // The member who springs an ambush pays out of the turn it is taking. Everybody else, and
        // every other kind of reaction, pays out of the reserve.
        var paying = placement.Forecast?.Paying ?? ApSource.Reserve;
        var purse = paying == ApSource.Reserve ? reactor.Reserve : reactor.ActionPoints;
        if (placement.ApCost > purse) return null;

        switch (placement.Action)
        {
            // Held fire. Nothing happens and nothing is spent, which is the whole of it.
            case ReactionAction.Nothing:
                return null;

            case ReactionAction.Fire:
                return Resolve(PlanShot(
                    reactor,
                    placement.Subject,
                    placement.Forecast!.Mode,
                    placement.Forecast.AimBonus,
                    UnitPose.Of(placement.Subject),
                    paying));

            case ReactionAction.Turn:
                reactor.Reserve -= placement.ApCost;
                if (placement.Facing is { } facing) reactor.Facing = facing;
                return null;

            case ReactionAction.Drop:
                reactor.Reserve -= placement.ApCost;
                if (placement.Stance is { } stance) reactor.Stance = stance;
                return null;

            default:
                reactor.Reserve -= placement.ApCost;
                Awareness.CallOut(reactor, placement.Subject.Id, Round);
                return null;
        }
    }

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

            // Which side of them it found, weighted by how wide each looks from here — unless
            // the shooter was good enough to name one.
            var aspect = plan.CalledAt is { } named
                ? plan.Aspects.FirstOrDefault(a => a.Face == named, PickFace(plan.Aspects))
                : PickFace(plan.Aspects);

            var arriving = Gunnery.DamageAt(plan.Weapon, aspect.ObliquityDegrees, plan.GlancingScale);

            var damage = target.Protection.Absorb(
                aspect.Face, plan.Weapon.Kind, arriving, aspect.ObliquityDegrees);

            target.Vitality -= damage.ToVitality;
            shots.Add(new ShotHit(true, roll, damage));

            if (target.IsDown) break;
        }

        AnnounceFire(shooter, target, plan);

        var down = target.IsDown;
        if (down) Withdraw(target, DepartureKind.Down);

        return new ShotOutcome(true, shots, plan.ApCost, plan.HitChance, down, null);
    }

    /// <summary>
    /// Roll which of the sides in view a round actually finds, weighted by how wide each of them
    /// looks from where the shot came from.
    /// </summary>
    /// <remarks>
    /// The roll comes from the battle generator like every other, so a whole exchange still
    /// replays from the seed. Aiming at a particular plate is deliberately not offered: you
    /// shoot at a soldier, and the geometry decides where it lands.
    /// </remarks>
    private FacingAspect PickFace(IReadOnlyList<FacingAspect> aspects)
    {
        if (aspects.Count == 0) return new FacingAspect(BodyFace.Front, 1.0, 0);
        if (aspects.Count == 1) return aspects[0];

        var roll = _rng.NextDouble();
        var running = 0.0;

        foreach (var aspect in aspects)
        {
            running += aspect.Share;
            if (roll < running) return aspect;
        }

        return aspects[^1];
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

    // ---- things that go off ----------------------------------------------------

    /// <summary>
    /// What lobbing a charge at a place would do, worked out before anyone commits to it.
    /// </summary>
    /// <remarks>
    /// Two things about this are deliberately unlike <see cref="PlanShot(Unit, Unit, FireMode, BodyFace?)"/>.
    /// <para>
    /// It is aimed at a <b>place</b>, so it can be aimed at somewhere nobody can see and somewhere
    /// nobody turns out to be. That is the whole point of a grenade and it is also what keeps a
    /// throw at a remembered position honest: the plan is made against what the thrower believes
    /// is there, and <see cref="Throw"/> resolves against whoever really is.
    /// </para>
    /// <para>
    /// And it takes the people it might catch as an argument. Left null they are everybody on the
    /// field, which is what actually going off means; a commander weighing one up passes the
    /// enemies it believes in and the allies it can see, so that it cannot discover a marker has
    /// gone stale by noticing that the grenade it was about to throw would catch nobody.
    /// </para>
    /// </remarks>
    public BlastPlan PlanThrow(
        Unit thrower,
        NodeId at,
        ThrownProfile? charge = null,
        IEnumerable<BlastCandidate>? against = null,
        ApSource paying = ApSource.Turn)
    {
        var item = charge ?? thrower.Thrown;
        var cost = item is null ? 0 : thrower.Stats.Costs.Fire(item.ApCost);
        var purse = paying == ApSource.Reserve ? thrower.Reserve : thrower.ActionPoints;

        if (item is null)
            return new BlastPlan(thrower, thrower.Side, ThrownProfile.FragGrenade, at, at, [], 0, $"{thrower.Name} is carrying nothing to throw.");

        var lob = Graph.Contains(at) ? Lob.Trace(thrower.Vantage, at, item.MaxArc) : null;

        var refusal =
            !Graph.Contains(at) ? "There is nothing there to throw at." :
            thrower.ThrownLeft <= 0 ? $"{thrower.Name} has no {item.Name} left." :
            purse < cost ? $"Needs {cost} points, has {purse}." :
            lob!.Distance > item.MaxThrow ? $"Too far to throw at {lob.Distance:0} m." :
            null;

        var landing = lob?.Landing ?? at;
        var caught = refusal is null ? Caught(item, landing, thrower.Side, against) : [];

        return new BlastPlan(thrower, thrower.Side, item, at, landing, caught, cost, refusal, lob);
    }

    /// <summary>What a mine under that tile would do to the people currently near it.</summary>
    public BlastPlan PlanBlast(Mine mine, IEnumerable<BlastCandidate>? against = null)
        => new(
            mine.Layer is { } id ? GetUnit(id) : null,
            mine.LaidBy,
            mine.Charge,
            mine.Node,
            mine.Node,
            Caught(mine.Charge, mine.Node, mine.LaidBy, against),
            0,
            null);

    /// <summary>
    /// Everybody near enough to a burst to feel it, and what it is expected to do to each.
    /// </summary>
    /// <remarks>
    /// The trace runs from the burst point outwards, which is what makes cover work in the
    /// direction it should. A soldier flat behind a knee-high wall is sheltered from a charge on
    /// the far side of it and not at all from the same charge lobbed over — same wall, same
    /// waterline arithmetic, opposite answer, and nothing had to be written down about explosions
    /// and cover to get it.
    /// </remarks>
    private IReadOnlyList<BlastEffect> Caught(
        ThrownProfile item,
        NodeId landing,
        Side from,
        IEnumerable<BlastCandidate>? against)
    {
        var candidates = against?.ToList() ?? InPlay.Select(BlastCandidate.At).ToList();
        var burst = Sight.Ground(landing).Raised(Ordnance.Model.BurstHeight);
        var effects = new List<BlastEffect>();

        foreach (var candidate in candidates.OrderBy(c => c.Unit.Id.Value))
        {
            var pose = candidate.Where;
            var sight = Sight.TraceFrom(burst, burst.Z, pose.Vantage);
            var distance = Vec3.Distance(
                burst, Sight.Ground(pose.Position).Raised(pose.Vantage.Profile.CentreHeight));

            var share = Ordnance.Share(distance, item, sight, pose.Stance);
            if (share <= 0) continue;

            var arriving = (int)Math.Round(item.Damage * share, MidpointRounding.AwayFromZero);
            if (arriving <= 0) continue;

            var aspects = FacesPresentedTo(pose, landing);
            var expectation = Ordnance.Expect(candidate.Unit, item, arriving, aspects);

            effects.Add(new BlastEffect(
                candidate.Unit, pose, distance, share, arriving, aspects, expectation,
                Friendly: candidate.Unit.Side == from, candidate.Credence));
        }

        return effects;
    }

    /// <summary>The active unit throws a charge at a place.</summary>
    /// <remarks>
    /// Resolved against whoever is actually standing there, which is the point: a grenade lobbed
    /// at where somebody was last seen catches them if they stayed and wastes itself if they did
    /// not. The decision was made on a belief and the world answers it, so nothing here corrects
    /// the thrower guess for free.
    /// </remarks>
    public BlastOutcome Throw(NodeId at, ThrownProfile? charge = null)
    {
        var thrower = RequireActive();
        var plan = PlanThrow(thrower, at, charge);
        if (!plan.CanThrow) return BlastOutcome.Refused(plan.Refusal!);

        thrower.ActionPoints -= plan.ApCost;
        thrower.ThrownLeft--;

        return Detonate(plan);
    }

    /// <summary>
    /// Leave a charge on the ground under your own feet, armed.
    /// </summary>
    /// <remarks>
    /// A turn spent buying a piece of ground for the rest of the fight. There is no arc to solve
    /// and nothing to clear, because it goes exactly where the soldier is standing.
    /// </remarks>
    public bool LayMine(ThrownProfile? charge = null)
    {
        var unit = RequireActive();
        var item = charge ?? unit.Thrown;
        if (item is null || unit.ThrownLeft <= 0) return false;

        var cost = unit.Stats.Costs.Fire(item.ApCost);
        if (unit.ActionPoints < cost) return false;
        if (_mines.Any(m => !m.Spent && m.Node == unit.Position)) return false;

        unit.ActionPoints -= cost;
        unit.ThrownLeft--;
        _mines.Add(new Mine(unit.Position, unit.Side, item, unit.Id));
        return true;
    }

    /// <summary>Set a mine off, on whoever is standing near it now.</summary>
    internal BlastOutcome Detonate(Mine mine)
    {
        if (mine.Spent) return BlastOutcome.Refused("Already gone off.");
        mine.Spent = true;

        return Detonate(PlanBlast(mine));
    }

    /// <summary>
    /// Put a blast through everybody it caught.
    /// </summary>
    /// <remarks>
    /// Which plate the wave finds is rolled from the battle generator like every other roll, so a
    /// whole exchange still replays from the seed. What it does not roll is whether it lands: a
    /// charge going off does not miss, and the only uncertainty is where on a body it arrives.
    /// <para>
    /// The bang is heard from <b>where it went off</b>, not from where it was thrown. Everybody
    /// in earshot learns that there is somebody about and marks them at the crater, which is
    /// wrong and is meant to be — a grenade is the one way in this game to make a great deal of
    /// noise somewhere you are not standing. Nothing else about a burst gives the thrower away:
    /// being blown up does not tell you who did it, unlike being shot at.
    /// </para>
    /// </remarks>
    private BlastOutcome Detonate(BlastPlan plan)
    {
        var hits = new List<BlastHit>();

        foreach (var effect in plan.Caught)
        {
            var caught = effect.Caught;
            if (!caught.InPlay) continue;

            var aspect = PickFace(effect.Aspects);
            var damage = caught.Protection.Absorb(aspect.Face, plan.Item.Kind, effect.Arriving);

            caught.Vitality -= damage.ToVitality;
            var down = caught.IsDown;
            hits.Add(new BlastHit(caught, damage, down));

            if (down) Withdraw(caught);
        }

        if (plan.Thrower is { InPlay: true } thrower)
            Awareness.Hear(thrower, plan.Landing, plan.Item.Loudness, Round);

        return new BlastOutcome(true, plan.Landing, hits, plan.ApCost, null);
    }

    /// <summary>
    /// Which of <paramref name="target"/>'s faces something at <paramref name="from"/> arrives at.
    /// </summary>
    public BodyFace FaceToward(Unit target, Unit from) => FacesPresentedTo(UnitPose.Of(target), from.Position)[0].Face;

    /// <summary>
    /// Which of a unit's own sides something arriving from <paramref name="from"/> can reach, and
    /// how squarely, widest first.
    /// </summary>
    /// <remarks>
    /// Never one side. A body is a hexagon, so standing in front of somebody puts you in view of
    /// their front plate and a sliver of each shoulder; standing toward a corner shows you two
    /// plates at equal angles. Which of them a given round finds is rolled when it is fired, so
    /// this is a distribution rather than an answer.
    /// </remarks>
    public IReadOnlyList<FacingAspect> FacesPresentedTo(UnitPose target, NodeId from)
        => BodyFaces.Presented(SignedAngleOffDegrees(target.Position, target.Facing, from));

    /// <summary>
    /// What taking this shot would tell each of the shooter enemies, without taking it.
    /// </summary>
    /// <remarks>
    /// Contract 2 in the ordinary direction: the scorer has always priced what a shot gives away
    /// and nothing let an interface show it, so a player could see what a shot would do to the
    /// target and not what it would cost them in attention. It is one call rather than a new
    /// model — the preview was already there on the tracker; nothing said so.
    /// </remarks>
    public IEnumerable<Announcement> WouldAnnounce(ShotPlan plan)
        => Awareness.WouldAnnounce(plan.Shooter, plan.From, plan.Weapon, plan.Target);

    /// <summary>The same, for a charge, which is heard from where it lands rather than thrown.</summary>
    public IEnumerable<Announcement> WouldAnnounce(BlastPlan plan)
        => plan.Thrower is { } thrower
            ? Awareness.WouldHear(thrower, plan.Landing, plan.Item.Loudness)
            : [];

    /// <summary>Which way a unit would have to look to face a place.</summary>
    public HexDirection HeadingTo(NodeId from, NodeId place)
    {
        var here = Sight.Ground(from).Plane;
        var there = Sight.Ground(place).Plane;

        var offset = there - here;
        if (offset.LengthSquared < Geometry2D.Epsilon) return HexDirection.NorthEast;

        return HexDirectionExtensions.FromBearing(offset.Angle - Layout.RotationRadians);
    }

    /// <summary>
    /// How far off a bearing a place lies, in degrees, seen from somewhere on the map.
    /// </summary>
    /// <remarks>
    /// One answer for two questions that keep turning out to be the same one: how much of an
    /// observer's attention a place has, and whether it falls inside a declared overwatch arc.
    /// </remarks>
    public double AngleOffDegrees(NodeId from, HexDirection direction, NodeId place)
        => Math.Abs(SignedAngleOffDegrees(from, direction, place));

    /// <summary>
    /// The same angle, signed: positive when the place lies to the left of the bearing.
    /// </summary>
    /// <remarks>
    /// Which side matters once faces are body-relative — a shoulder is not the same plate as the
    /// other shoulder. The grid can be drawn rotated, so the bearing is rotated with it, and
    /// hex directions run counter-clockwise, so a positive step is a step to the left.
    /// </remarks>
    public double SignedAngleOffDegrees(NodeId from, HexDirection direction, NodeId place)
    {
        var here = Sight.Ground(from).Plane;
        var there = Sight.Ground(place).Plane;

        var offset = there - here;
        if (offset.LengthSquared < Geometry2D.Epsilon) return 0;

        var bearing = direction.BearingRadians() + Layout.RotationRadians;
        return Geometry2D.SignedAngleBetween(bearing, offset.Angle) * (180.0 / Math.PI);
    }

    /// <summary>Drop to a crouch, go prone, or stand back up.</summary>
    public bool ChangeStance(Stance stance)
    {
        var unit = RequireActive();
        var cost = unit.Stats.Costs.Posturing(Costs.ChangeStance);

        if (unit.Stance == stance) return false;
        if (unit.ActionPoints < cost) return false;

        unit.Stance = stance;
        unit.ActionPoints -= cost;
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

    /// <summary>
    /// How the battle stands for one side.
    /// </summary>
    /// <remarks>
    /// Its objective decides, if it has one. A side with none falls back on the rule that was the
    /// only rule until objectives existed: last one standing.
    /// </remarks>
    public Verdict VerdictFor(Side side)
    {
        if (ObjectiveOf(side) is { } objective) return objective.Judge(this);

        var standing = SidesInPlay.ToList();
        if (standing.Count > 1) return Verdict.Undecided;
        return standing.Contains(side) ? Verdict.Achieved : Verdict.Failed;
    }

    /// <summary>
    /// True once the battle has an answer.
    /// </summary>
    /// <remarks>
    /// An objective settling ends it, however many soldiers are still on the field — which is the
    /// whole point of having one, since a squad that got what it came for and left has finished
    /// whether or not anybody was killed. Elimination still ends a battle nobody gave an
    /// objective to.
    /// </remarks>
    public bool IsDecided
        => _objectives.Any(o => o.Judge(this) != Verdict.Undecided) || SidesInPlay.Count() <= 1;

    private Unit RequireActive()
        => Active ?? throw new InvalidOperationException("No turn is in progress. Call Start first.");
}
