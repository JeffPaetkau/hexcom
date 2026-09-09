using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;

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
/// nothing else here uses it. An objective is not a value — it is a <em>strategy</em>, and the
/// shapes it can take are open: entry 026 lists six and content will want ones nobody has thought
/// of. A single record with a field per kind would rot as they were added, and a switch over a
/// kind enum would put every future mission type inside <see cref="Battle"/>.
/// <para>
/// It answers two questions and deliberately not a third. <see cref="Judge"/> says how the battle
/// stands, which is a <b>win condition</b>. <see cref="Progress"/> says how much of it a soldier
/// standing somewhere represents, which is what lets the scorer rank walking toward it. What it
/// does <em>not</em> do is put a price on anything: an objective is a win condition and not a
/// scoring model, and what achieving one is worth in vitality is
/// <see cref="Tactics.UtilityModel.ObjectiveValue"/> — one number, in the home where every other
/// exchange rate lives.
/// </para>
/// </remarks>
public abstract record Objective(Side Side)
{
    /// <summary>Words fit to show a player, or to put in a test failure.</summary>
    public abstract string Brief { get; }

    /// <summary>How the battle stands for this side, from where it is now.</summary>
    public abstract Verdict Judge(Battle battle);

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
    public abstract double Progress(Battle battle, NodeId at);
}

/// <summary>
/// Be there, do the thing, and leave with nobody the wiser.
/// </summary>
/// <remarks>
/// The cheapest of the six mission shapes and the purest statement of what this game is about,
/// and it needed no new measurement: <em>leave with the whole hostile side still below a given
/// rung</em> is readable off the awareness ladder, against thresholds
/// <see cref="AwarenessModel"/> already owns. What it needed was somewhere to leave from, a way
/// to tell leaving from dying, and a reading taken at the moment of departure rather than after
/// it — see <see cref="Departure"/> for why the last one is not a detail.
/// <para>
/// It is also the first thing in the game that makes the awareness ladder a <b>scoreboard</b>
/// rather than only an input.
/// </para>
/// </remarks>
/// <param name="Exit">
/// Where this side can leave from. A named place rather than a map edge, because the person
/// meeting you there has to be able to find it.
/// </param>
/// <param name="Unnoticed">
/// The highest rung any enemy may hold on a departing soldier and still have the mission count.
/// Suspicious by default: something registered, nobody knows what.
/// </param>
public sealed record Withdrawal(
    Side Side,
    IReadOnlyCollection<NodeId> Exit,
    AwarenessState Unnoticed = AwarenessState.Suspicious)
    : Objective(Side)
{
    private IReadOnlyDictionary<NodeId, int>? _approach;
    private int _builtFrom = -1;

    public override string Brief
        => $"Leave by the exit with nobody above {Unnoticed}.";

    /// <summary>Whether a place is one this side may walk off the field from.</summary>
    public bool IsExit(NodeId node) => Exit.Contains(node);

    /// <summary>
    /// Achieved when everybody got out quietly; abandoned when they got out and were noticed;
    /// failed when there is nobody left to get out.
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

        // Still somebody on the field who could yet walk out.
        if (ours.Any(u => u.InPlay)) return Verdict.Undecided;

        if (ours.All(u => u.Left!.Kind == DepartureKind.Down)) return Verdict.Failed;

        var worst = ours.Max(u => u.Left!.Noticed);
        return worst <= Unnoticed ? Verdict.Achieved : Verdict.Abandoned;
    }

    /// <summary>
    /// One at the exit, sloping away over the ground in front of it, and nothing at all beyond
    /// about a turn's walk.
    /// </summary>
    /// <remarks>
    /// Measured in action points along the movement graph rather than in hexes across the map,
    /// so a soldier the far side of a river reads as far away even when the wall is thin. The
    /// field is priced off the <b>listed</b> cost of the ground rather than off what any
    /// particular soldier pays for it, for the same reason loudness is: it describes the ground,
    /// and how quickly a given soldier crosses it is about them.
    /// </remarks>
    public override double Progress(Battle battle, NodeId at)
    {
        var approach = Approach(battle);
        if (!approach.TryGetValue(at, out var cost)) return 0;

        var horizon = battle.Costs.ActionPointsPerTurn * battle.Tactics.Model.ObjectiveHorizon;
        return horizon <= 0 ? (cost == 0 ? 1 : 0) : Math.Clamp(1.0 - cost / horizon, 0, 1);
    }

    /// <summary>
    /// What it costs to reach the exit from everywhere on the map, worked out once.
    /// </summary>
    /// <remarks>
    /// One search over the whole graph rather than one per candidate destination per decision,
    /// which is the difference between an objective a commander can afford to want and one it
    /// cannot. Rebuilt only if the map changes under it.
    /// </remarks>
    private IReadOnlyDictionary<NodeId, int> Approach(Battle battle)
    {
        if (_approach is not null && _builtFrom == battle.Map.Revision) return _approach;

        _approach = Pathfinder.CostToReach(battle.Graph, Exit);
        _builtFrom = battle.Map.Revision;
        return _approach;
    }
}
