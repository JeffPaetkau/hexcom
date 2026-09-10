using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Battles;

/// <summary>Why a soldier is no longer on the field.</summary>
/// <remarks>
/// Two ways off it, and until there were objectives nothing had to tell them apart: a squad that
/// walked away ended a battle in exactly the state a squad killed to the last man ended it. See
/// <c>docs/decisions.md</c> entry 030.
/// </remarks>
public enum DepartureKind
{
    /// <summary>Put down.</summary>
    Down,

    /// <summary>Walked off the field, under its own power, from somewhere its side could leave.</summary>
    Extracted,
}

/// <summary>
/// How a soldier left, and what the other side knew about it at that moment.
/// </summary>
/// <remarks>
/// The reading is <b>sampled here and kept</b> rather than polled afterwards, and that is not an
/// optimisation. <see cref="Battle.Withdraw"/> makes the tracker forget everything about a unit
/// that has left, so a win condition of the form <em>get out with nobody above a suspicion</em>,
/// asked after the squad had gone, would read Unaware for everybody, trivially and always.
/// <para>
/// It is deliberately a sample per departure rather than a high-water mark held across the
/// battle, because forgetting is also what makes the best move in the game work: silencing a
/// witness really does take his contact out of the world, with no rule saying so. A monotone
/// mark would forbid that. This keeps it, and keeps the counter-play — if he called it in before
/// he died, his side holds a fraction of what he had and that survives him.
/// </para>
/// </remarks>
/// <param name="Noticed">The highest state any enemy held on this soldier as it left.</param>
public sealed record Departure(DepartureKind Kind, int Round, AwarenessState Noticed)
{
    public override string ToString() => $"{Kind} in round {Round}, {Noticed}";
}

/// <summary>How a battle finished, for one side.</summary>
/// <remarks>
/// Three endings rather than two, which is the shape the fiction asked for and the rules did not
/// have. Elimination is not among them: a battle in this game is decided by whether the thing
/// the squad came to do got done, and <b>casualties are the campaign's to grade</b> — it holds
/// the roster, soldiers persist between missions and plate never recovers, so it already has the
/// measurement. Nothing tactical should be made to weigh a dead rifleman against a records core.
/// See <c>docs/decisions.md</c> entry 030.
/// </remarks>
public enum Verdict
{
    /// <summary>Still going. Nothing has settled it either way.</summary>
    Undecided,

    /// <summary>Done, and done the way it was meant to be done.</summary>
    Achieved,

    /// <summary>Settled against them. There is nobody left who could finish it.</summary>
    Failed,

    /// <summary>
    /// It stopped being reachable and everybody came home anyway.
    /// </summary>
    /// <remarks>
    /// The commonest honest outcome of quiet work, and the reason two endings were not enough.
    /// A squad that is seen has lost the mission and has not lost the squad, and those are
    /// different results that a win-or-die model reports identically.
    /// </remarks>
    Abandoned,
}

/// <summary>
/// What one side is on the field to do.
/// </summary>
/// <remarks>
/// The one place in these rules where polymorphism earns its keep, and it wants justifying since
/// nothing else here uses it. An objective is not a value — it is a <em>strategy</em> with state,
/// and the shapes it can take are open: entry 026 lists six. A single record with a field per
/// kind would rot as they were added, and a switch over a kind enum would put every future
/// mission type inside <see cref="Battle"/>.
/// <para>
/// It answers two questions and deliberately not a third. <see cref="Judge"/> says how the battle
/// stands, which is a <b>win condition</b>. <see cref="Progress"/> says how much of it a soldier
/// standing somewhere represents, which is what lets the scorer rank walking toward it. What it
/// does <em>not</em> do is put a price on anything: an objective is a win condition and not a
/// scoring model, and what achieving one is worth in vitality is
/// <see cref="Tactics.UtilityModel.ObjectiveValue"/> — one number, in the home where every other
/// exchange rate lives.
/// </para>
/// <para>
/// A class rather than a record, because it holds how far along the mission is and a record that
/// changes is a record in name only.
/// </para>
/// </remarks>
public abstract class Objective(Side side)
{
    /// <summary>Further than anything on the map. What an unreachable place costs to get to.</summary>
    protected const int Unreachable = int.MaxValue;

    private double _horizon;

    public Side Side { get; } = side;

    /// <summary>Words fit to show a player, or to put in a test failure.</summary>
    public abstract string Brief { get; }

    /// <summary>How the battle stands for this side, from where it is now.</summary>
    public abstract Verdict Judge(Battle battle);

    /// <summary>
    /// What is still to be done from there, in action points: the walking and the working
    /// together. <see cref="Unreachable"/> when the rest of the job cannot be got at from there.
    /// </summary>
    /// <remarks>
    /// One quantity for the whole mission, and that is the trick the rest of this rests on.
    /// Walking twenty points closer and spending twenty points on the charge are the same
    /// twenty points of progress, so a two-stage mission needs no second scale and no seam
    /// between its stages — see <see cref="Sortie"/>.
    /// </remarks>
    protected abstract int Remaining(Battle battle, NodeId at);

    /// <summary>
    /// How much of the objective a soldier of this side standing at that place represents, from
    /// nothing to all of it.
    /// </summary>
    /// <remarks>
    /// A gradient rather than a flag, and that is the whole of what makes an objective able to
    /// draw a soldier. A flag would be worth something only from inside the exit itself, and a
    /// search one step deep cannot see a place it takes three turns to reach — so nobody would
    /// ever set off. Sloping the value over the approach means every stride toward it scores,
    /// which is the same trick that makes a move to a firing position worth taking.
    /// </remarks>
    public double Progress(Battle battle, NodeId at)
    {
        var left = Remaining(battle, at);
        if (left >= Unreachable) return 0;
        if (_horizon <= 0) return left == 0 ? 1 : 0;

        return Math.Clamp(1.0 - left / _horizon, 0, 1);
    }

    /// <summary>
    /// How much of the objective one action point of progress is worth, from nought to one.
    /// </summary>
    /// <remarks>
    /// The slope, exposed so that anything which shortens <see cref="Remaining"/> by some number
    /// of points can be priced without asking what shortened it. Walking a stride toward the
    /// place and spending a stride on the charge earn the same, which is the point of measuring
    /// the whole mission in one currency.
    /// </remarks>
    public double PerPoint => _horizon <= 0 ? 0 : 1.0 / _horizon;

    /// <summary>
    /// Told where the squad is standing, once, as the fight starts.
    /// </summary>
    /// <remarks>
    /// This is what stops the gradient from having the very problem it was invented to solve.
    /// <see cref="Tactics.UtilityModel.ObjectiveHorizon"/> says how many turns of walking still
    /// count as being on the way, and a mission longer than that would read as nothing worth
    /// starting from anywhere near the start — which is a flag again, with extra steps. So the
    /// horizon is stretched to the actual length of the job when the job is longer: it decides
    /// how <em>steep</em> the slope is on a short mission and never how far it reaches.
    /// <para>
    /// Measured off the deployment rather than off the map, because the map's diameter is not the
    /// mission's length and using it would flatten every objective on a large map to nothing.
    /// </para>
    /// </remarks>
    internal virtual void Begin(Battle battle)
    {
        var configured = battle.Costs.ActionPointsPerTurn * battle.Tactics.Model.ObjectiveHorizon;

        var journey = battle.Units
            .Where(u => u.Side == Side)
            .Select(u => Remaining(battle, u.Position))
            .Where(cost => cost < Unreachable)
            .DefaultIfEmpty(0)
            .Max();

        _horizon = Math.Max(configured, journey);
    }

    /// <summary>
    /// One of this side's soldiers has taken its look around, at the end of its turn.
    /// </summary>
    /// <remarks>
    /// The only moment anybody sees anything, so it is the only moment a mission that is
    /// <em>about</em> seeing something can be completed. Nothing else needs it.
    /// </remarks>
    internal virtual void Looked(Battle battle, Unit unit) { }

    public override string ToString() => Brief;
}

/// <summary>
/// Go out, do something, and come back: the shape every mission in the book shares.
/// </summary>
/// <remarks>
/// <b>The answer to whether reconnaissance and sabotage are one kind or two is: one shape and
/// three tasks.</b> The brief asked for that choice to be made deliberately rather than fallen
/// into, so here is the argument. What the shapes share is nearly everything — the exit, the
/// reading taken as each soldier leaves, the three endings, and a journey that runs out and back.
/// What differs is one question: has the thing been done. Looking at a place is a geometric fact
/// checked when somebody looks; spending points on a charge is an action with a price and a verb.
/// Those are different enough that a predicate on a shared record would have to be a delegate,
/// which content written as a text file cannot hold — so they are subclasses, and the shared
/// nine tenths is here.
/// <para>
/// <b>And the task and the walking are measured in the same currency</b>, which is what makes a
/// two-stage mission need no seam. <see cref="Remaining"/> is the action points still owed:
/// getting to the place, doing what is there, and getting to the exit. Twenty points spent
/// walking and twenty spent working move it by the same amount, so the gradient is continuous
/// across the moment the task completes — doing the thing does not jolt the score, it changes
/// what is left.
/// </para>
/// <para>
/// The consequence entry 048 measured is the one this exists to fix. With only the leaving
/// modelled, the best play on the waystation was to walk to the exit in round 2 and call the
/// mission done, because the exit was one turn away and the thing to look at was two turns past
/// it in the other direction. Now the exit is not the end of the journey; it is the end of a
/// journey that goes by way of the compound.
/// </para>
/// </remarks>
/// <param name="exit">
/// Where this side can leave from. A named place rather than a map edge, because the person
/// meeting you there has to be able to find it.
/// </param>
/// <param name="unnoticed">
/// The highest rung any enemy may hold on a departing soldier and still have the mission count.
/// Suspicious by default: something registered, nobody knows what.
/// </param>
public abstract class Sortie(
    Side side,
    IReadOnlyCollection<NodeId> exit,
    AwarenessState unnoticed = AwarenessState.Suspicious)
    : Objective(side)
{
    private IReadOnlyDictionary<NodeId, int>? _toExit;
    private IReadOnlyDictionary<NodeId, int>? _toPlace;
    private int _builtFrom = -1;

    public IReadOnlyCollection<NodeId> Exit { get; } = exit;

    public AwarenessState Unnoticed { get; } = unnoticed;

    /// <summary>Whether a place is one this side may walk off the field from.</summary>
    public bool IsExit(NodeId node) => Exit.Contains(node);

    /// <summary>Where the thing to be done is, or null for a mission whose only task is leaving.</summary>
    public virtual NodeId? Place => null;

    /// <summary>Whether the thing the squad came for has been done.</summary>
    public abstract bool Done { get; }

    /// <summary>Action points still owed to the task itself, once somebody is standing at it.</summary>
    protected virtual int WorkLeft => 0;

    /// <summary>
    /// Achieved when the job was done and everybody got out quietly; abandoned when they got out
    /// without it, or were noticed doing it; failed when there is nobody left to get out.
    /// </summary>
    /// <remarks>
    /// Casualties are not a term. A soldier put down departs like any other and contributes the
    /// reading the enemy held on him, which will be a high one — so losing a man usually costs
    /// the <em>mission</em> rather than being counted as a loss in its own right, which is the
    /// right way round for a squad whose orders were to go unnoticed. Nobody grades the body
    /// count here; the campaign holds the roster.
    /// </remarks>
    public override Verdict Judge(Battle battle)
    {
        var ours = battle.Units.Where(u => u.Side == Side).ToList();
        if (ours.Count == 0) return Verdict.Undecided;

        // Still somebody on the field who could yet finish it, or walk out.
        if (ours.Any(u => u.InPlay)) return Verdict.Undecided;

        if (ours.All(u => u.Left!.Kind == DepartureKind.Down)) return Verdict.Failed;
        if (!Done) return Verdict.Abandoned;

        return ours.Max(u => u.Left!.Noticed) <= Unnoticed ? Verdict.Achieved : Verdict.Abandoned;
    }

    /// <summary>
    /// The way home, by way of whatever is not done yet.
    /// </summary>
    /// <remarks>
    /// Two fields over the graph and one addition. Priced off the <b>listed</b> cost of the
    /// ground rather than off what any particular soldier pays for it, for the same reason
    /// loudness is: it describes the ground, and how quickly a given soldier crosses it is about
    /// them.
    /// </remarks>
    protected override int Remaining(Battle battle, NodeId at)
    {
        var home = Approach(battle, Exit, ref _toExit);

        if (Done || Place is not { } place)
            return home.TryGetValue(at, out var direct) ? direct : Unreachable;

        var outward = Approach(battle, [place], ref _toPlace);

        if (!outward.TryGetValue(at, out var there)) return Unreachable;
        if (!home.TryGetValue(place, out var back)) return Unreachable;

        return there + WorkLeft + back;
    }

    /// <summary>
    /// What it costs to reach a set of places from everywhere on the map, worked out once.
    /// </summary>
    /// <remarks>
    /// One backward search over the whole graph rather than one per candidate destination per
    /// decision, which is the difference between an objective a commander can afford to want and
    /// one it cannot. Rebuilt only if the map changes under it.
    /// </remarks>
    private IReadOnlyDictionary<NodeId, int> Approach(
        Battle battle,
        IEnumerable<NodeId> goals,
        ref IReadOnlyDictionary<NodeId, int>? cache)
    {
        if (cache is not null && _builtFrom == battle.Map.Revision) return cache;

        if (_builtFrom != battle.Map.Revision)
        {
            _toExit = null;
            _toPlace = null;
            _builtFrom = battle.Map.Revision;
        }

        cache = Pathfinder.CostToReach(battle.Graph, goals);
        return cache;
    }
}

/// <summary>
/// Be there, and leave with nobody the wiser. The mission with nothing in the middle.
/// </summary>
/// <remarks>
/// The cheapest of the six shapes and the purest statement of what this game is about, and it
/// needed no new measurement: <em>leave with the whole hostile side still below a given rung</em>
/// is readable off the awareness ladder, against thresholds <see cref="AwarenessModel"/> already
/// owns. What it needed was somewhere to leave from, a way to tell leaving from dying, and a
/// reading taken at the moment of departure rather than after it.
/// <para>
/// It is also the first thing in the game that makes the awareness ladder a <b>scoreboard</b>
/// rather than only an input. Kept as a shape of its own rather than folded away, because a
/// mission whose whole content is <em>get in and get out again unseen</em> is a real one.
/// </para>
/// </remarks>
public sealed class Withdrawal(
    Side side,
    IReadOnlyCollection<NodeId> exit,
    AwarenessState unnoticed = AwarenessState.Suspicious)
    : Sortie(side, exit, unnoticed)
{
    public override string Brief => $"Leave by the exit with nobody above {Unnoticed}.";

    /// <summary>Nothing to do but go, so there is never anything outstanding but the leaving.</summary>
    public override bool Done => true;
}

/// <summary>
/// Put eyes on a place and get out again.
/// </summary>
/// <remarks>
/// Entry 030 costed this down to two calls that already existed, and it was right: a sight trace
/// to a vantage at the place, and the attention test that says the soldier was <em>looking</em> at
/// it rather than catching it in the corner of an eye. Both are ordinary queries and neither is
/// new geometry.
/// <para>
/// Checked when a soldier looks, which is the end of its own turn and the only moment anybody
/// sees anything in this game. A mission about seeing something therefore completes on the same
/// clock as every other observation, rather than on a continuous test nobody else is subject to.
/// </para>
/// </remarks>
/// <param name="place">The thing to get eyes on.</param>
/// <param name="within">
/// How close a soldier has to be for a look to count as having confirmed anything, in metres.
/// A line to a building from eighty metres away is a line; it is not a report.
/// </param>
public sealed class Reconnaissance(
    Side side,
    NodeId place,
    IReadOnlyCollection<NodeId> exit,
    double within = 12.0,
    AwarenessState unnoticed = AwarenessState.Suspicious)
    : Sortie(side, exit, unnoticed)
{
    private bool _seen;

    public override string Brief
        => $"Get eyes on {place} from within {within:0} m and leave with nobody above {Unnoticed}.";

    public override NodeId? Place => place;

    public override bool Done => _seen;

    /// <summary>Who confirmed it, and when. Null until somebody has.</summary>
    public (Unit By, int Round)? Confirmed { get; private set; }

    /// <summary>How close a look has to be taken from.</summary>
    public double Within => within;

    internal override void Looked(Battle battle, Unit unit)
    {
        if (_seen || unit.Side != Side) return;

        var target = new Vantage(place);
        var sight = battle.Sight.Trace(unit.Vantage, target);

        if (!sight.CanSee || sight.Distance > within) return;
        if (!battle.Awareness.IsWatching(unit, place)) return;

        _seen = true;
        Confirmed = (unit, battle.Round);
    }
}

/// <summary>
/// Reach a thing and spend long enough on it, then get out.
/// </summary>
/// <remarks>
/// The same shape as reconnaissance with the task priced instead of free, and the price is in the
/// currency the rest of the mission is already measured in: action points. So a charge that takes
/// most of a turn to set is exactly as far from done as being most of a turn's walk away, and the
/// gradient carries a soldier through the work as smoothly as it carries them to it.
/// <para>
/// Anybody may contribute. A squad that splits the work between two soldiers is doing the same
/// job faster, which is what a squad is for, and nothing about the arithmetic notices.
/// </para>
/// </remarks>
/// <param name="effort">Action points the job takes, in total, from however many soldiers.</param>
public sealed class Sabotage(
    Side side,
    NodeId place,
    IReadOnlyCollection<NodeId> exit,
    int effort = 40,
    AwarenessState unnoticed = AwarenessState.Suspicious)
    : Sortie(side, exit, unnoticed)
{
    private int _spent;

    public override string Brief
        => $"Spend {effort} points at {place} and leave with nobody above {Unnoticed}.";

    public override NodeId? Place => place;

    public override bool Done => _spent >= effort;

    /// <summary>Action points the job takes in total.</summary>
    public int Effort => effort;

    /// <summary>What has gone into it so far.</summary>
    public int Spent => _spent;

    /// <summary>What it still wants.</summary>
    public int Owing => Math.Max(0, effort - _spent);

    protected override int WorkLeft => Owing;

    internal void Work(int points) => _spent += Math.Max(0, points);
}
