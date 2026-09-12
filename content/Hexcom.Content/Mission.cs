using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;

namespace Hexcom.Content;

/// <summary>The six parts every briefing in this world has. See <c>docs/setting/missions.md</c>.</summary>
public enum BriefingPart
{
    /// <summary>Under what authority, and what this will be filed as.</summary>
    Instrument,

    /// <summary>The site, and who is on it, stated with the uncertainty it actually has.</summary>
    Presence,

    /// <summary>What you are to do, in one sentence. If it takes two, it is two missions.</summary>
    Task,

    /// <summary>What you are not to do.</summary>
    Restraint,

    /// <summary>Where you come off the ground, and by when. Nobody is coming to get you.</summary>
    WayOff,

    /// <summary>What ends the task short.</summary>
    Stop,
}

/// <summary>
/// What the squad is told, in the six parts the mission book gives a briefing.
/// </summary>
/// <remarks>
/// All six are required, and that is not pedantry. Three copies of this mission existed before
/// this file did — a prose header, a sandbox scenario and a test harness — and what let them
/// drift was that no one of them had to be complete. A briefing missing its restraint is a
/// mission whose rules of engagement live in somebody's memory.
/// </remarks>
public sealed record Briefing(
    string Instrument,
    string Presence,
    string Task,
    string Restraint,
    string WayOff,
    string Stop)
{
    /// <summary>One part by name, so a readout can loop over the six in order.</summary>
    public string Part(BriefingPart part) => part switch
    {
        BriefingPart.Instrument => Instrument,
        BriefingPart.Presence => Presence,
        BriefingPart.Task => Task,
        BriefingPart.Restraint => Restraint,
        BriefingPart.WayOff => WayOff,
        _ => Stop,
    };

    /// <summary>The six, in the order a briefing is given.</summary>
    public static readonly IReadOnlyList<BriefingPart> Order =
        [BriefingPart.Instrument, BriefingPart.Presence, BriefingPart.Task,
         BriefingPart.Restraint, BriefingPart.WayOff, BriefingPart.Stop];
}

/// <summary>One soldier, put on the ground before the fight starts.</summary>
/// <remarks>
/// The facing is not decoration and it is why a deployment cannot be a coordinate. A soldier's
/// front cone reads at acuity 1.0 and the corner of his eye at 0.45, so a garrison deployed
/// facing the wrong way has made a decision on the player's behalf. Entry 030.
/// </remarks>
/// <param name="Name">What the readouts call them.</param>
/// <param name="Side">Ours or theirs.</param>
/// <param name="Where">The tile they stand on, checked against the map when the battle is built.</param>
/// <param name="Facing">Which way they are looking.</param>
/// <param name="Role">A <see cref="UnitStats"/> preset by name, or null for the default soldier.</param>
/// <param name="Kit">A <see cref="Loadout"/> by name, or null for the default.</param>
/// <param name="Line">The line of the file this was written on, so a failure can point at it.</param>
public sealed record Deployment(
    string Name,
    Side Side,
    TileAddress Where,
    HexDirection Facing,
    string? Role = null,
    string? Kit = null,
    int Line = 0)
{
    /// <summary>The build this role names, or null for the default soldier.</summary>
    public UnitStats? Stats => Role is null ? null : MissionFile.Roles[Role];

    /// <summary>What they carry, or null for the default.</summary>
    public Loadout? Loadout => Kit is null ? null : MissionFile.Kits[Kit];
}

/// <summary>The six mission shapes of <c>docs/setting/missions.md</c>, as a file may name them.</summary>
/// <remarks>
/// All six are in the grammar and only <see cref="Withdrawal"/> can be built, because it is the
/// only one the rules have — entry 041. Naming the other five here rather than leaving them out
/// is deliberate: a file that says <c>objective sabotage</c> gets told the rules have no sabotage
/// yet, which is a true and useful thing to be told, where "unknown statement" is neither.
/// </remarks>
public enum ObjectiveKind
{
    Withdrawal,
    Reconnaissance,
    Sabotage,
    Extraction,
    Denial,
    Capture,
}

/// <summary>
/// What a side is told to do, before there is a battle to judge it against.
/// </summary>
/// <remarks>
/// A mission file names places; a <see cref="Objective"/> wants nodes in a movement graph, and
/// there is no graph until the map has been read and built. So an order is the objective with
/// the map-dependent half left unresolved, and <see cref="Build"/> is where the two meet. It is
/// abstract for the same reason <see cref="Objective"/> is: the shapes are open.
/// </remarks>
public abstract record ObjectiveOrder(ObjectiveKind Kind, Side Side, int Line = 0)
{
    /// <summary>Turn this into an objective the rules can judge, against a battle not yet started.</summary>
    public abstract Objective Build(Mission mission, Battle battle);
}

/// <summary>
/// Go out, do something, and come back — the shape all three buildable objectives share.
/// </summary>
/// <remarks>
/// Entry 061 settled that the mission book's shapes are one shape and several tasks, and this is
/// the file format agreeing with it rather than restating it. Every sortie names somewhere to
/// leave from and how loudly it may be done, so both are here, spelled the same way in every
/// statement — <c>exit</c> and <c>unnoticed</c> — and a shape adds only what is its own. The
/// commented line entry 059 left in the waystation said <c>out cottages</c>; one grammar with two
/// words for the exit is a wart, and the word that survived is the one already in the format, in
/// <c>content/README.md</c> and on <see cref="Sortie.Exit"/>.
/// </remarks>
/// <param name="Exit">The name of a <c>place</c> this side may walk off the field from.</param>
/// <param name="Unnoticed">The highest rung any enemy may hold on a departing soldier.</param>
public abstract record SortieOrder(
    ObjectiveKind Kind,
    Side Side,
    string Exit,
    AwarenessState Unnoticed,
    int Line)
    : ObjectiveOrder(Kind, Side, Line);

/// <summary>Leave by a named place with nobody the wiser. The sortie with nothing in the middle.</summary>
public sealed record WithdrawalOrder(
    Side Side,
    string Exit,
    AwarenessState Unnoticed = AwarenessState.Suspicious,
    int Line = 0)
    : SortieOrder(ObjectiveKind.Withdrawal, Side, Exit, Unnoticed, Line)
{
    public override Objective Build(Mission mission, Battle battle)
        => new Withdrawal(Side, mission.NodesOf(Exit, battle.Graph, Line), Unnoticed);
}

/// <summary>Get eyes on a named place from close enough to count, then leave by another.</summary>
/// <remarks>
/// Two places and a distance. The distance is the only number in the statement, and it is
/// optional because the rules already have an opinion about it — twelve metres, on
/// <see cref="Reconnaissance"/> — which a file that says nothing inherits rather than copies.
/// That is why <see cref="Within"/> is nullable instead of defaulted here: a balance number
/// written down in two places is a balance number that will disagree with itself.
/// </remarks>
/// <param name="Place">The name of the <c>place</c> to be looked at.</param>
/// <param name="Within">How close the look has to be taken from, in metres, or null for the rule's own.</param>
public sealed record ReconnaissanceOrder(
    Side Side,
    string Place,
    string Exit,
    double? Within = null,
    AwarenessState Unnoticed = AwarenessState.Suspicious,
    int Line = 0)
    : SortieOrder(ObjectiveKind.Reconnaissance, Side, Exit, Unnoticed, Line)
{
    public override Objective Build(Mission mission, Battle battle)
    {
        var place = mission.NodeOf(Place, battle.Graph, Line);
        var exit = mission.NodesOf(Exit, battle.Graph, Line);

        return Within is { } within
            ? new Reconnaissance(Side, place, exit, within, Unnoticed)
            : new Reconnaissance(Side, place, exit, unnoticed: Unnoticed);
    }
}

/// <summary>Spend long enough on a named place to break it, then leave by another.</summary>
/// <remarks>
/// The same two places with the task priced instead of free, and written here for the same reason
/// the grammar names all six shapes: the alternative was an error message saying the rules have
/// no sabotage, which entry 061 made untrue. No mission in the library is one yet.
/// </remarks>
/// <param name="Effort">Action points the job takes in total, or null for the rule's own.</param>
public sealed record SabotageOrder(
    Side Side,
    string Place,
    string Exit,
    int? Effort = null,
    AwarenessState Unnoticed = AwarenessState.Suspicious,
    int Line = 0)
    : SortieOrder(ObjectiveKind.Sabotage, Side, Exit, Unnoticed, Line)
{
    public override Objective Build(Mission mission, Battle battle)
    {
        var place = mission.NodeOf(Place, battle.Graph, Line);
        var exit = mission.NodesOf(Exit, battle.Graph, Line);

        return Effort is { } effort
            ? new Sabotage(Side, place, exit, effort, Unnoticed)
            : new Sabotage(Side, place, exit, unnoticed: Unnoticed);
    }
}

/// <summary>
/// A mission: a map, who is standing on it, what one side came to do, and when it stops.
/// </summary>
/// <remarks>
/// <para>
/// The four things entry 030 says a mission needs that a map deliberately cannot hold, plus the
/// squads. It is a file of its own rather than a block in the <c>.hexmap</c>, and
/// <c>content/README.md</c> gives the argument: ground outlives missions, one battlefield can
/// carry several of them, and a map with no mission at all has to stay legal because the view
/// diffs its captures against one.
/// </para>
/// <para>
/// Everything here is resolved against the map as late as possible. A place is a set of tiles
/// until there is a movement graph to ask which of them anybody can stand in, and an objective
/// is an <see cref="ObjectiveOrder"/> until then. Reading a mission therefore never needs the
/// map, which is what lets a tool list every mission in the library without building seven
/// thousand movement nodes.
/// </para>
/// </remarks>
/// <param name="Name">Whatever the <c>mission</c> line said, or the file name.</param>
/// <param name="MapName">The <c>.hexmap</c> this is fought on, by <see cref="MapLibrary"/> name.</param>
/// <param name="Brief">What the squad is told.</param>
/// <param name="Deployments">Everybody, in the order the file put them.</param>
/// <param name="Places">Named ground, by name: an exit, an objective, somewhere to say in a report.</param>
/// <param name="Objectives">What each side came to do. At most one per side, as <c>Battle</c> holds them.</param>
/// <param name="Rounds">
/// When it stops, in rounds, or null for no limit. The mission clock of the mission book's sixth
/// row, and the rules have no clock of their own yet — so whatever runs the battle applies this.
/// See <c>docs/decisions.md</c> entry 047.
/// </param>
public sealed record Mission(
    string? Name,
    string MapName,
    Briefing Brief,
    IReadOnlyList<Deployment> Deployments,
    IReadOnlyDictionary<string, IReadOnlyList<TileAddress>> Places,
    IReadOnlyList<ObjectiveOrder> Objectives,
    int? Rounds)
{
    /// <summary>
    /// One horizontal world unit is one metre, so a hex of size 1.0 is 1.73 m between centres.
    /// </summary>
    /// <remarks>
    /// Frozen contract 5 and entry 007. Rendering scale is a separate concern that must never be
    /// fed to a <see cref="Battle"/>; a caller with its own layout may pass one to
    /// <see cref="Begin"/>, and the view's <c>SandboxScale</c> is the place that knows why.
    /// </remarks>
    public static readonly HexLayout Metres = new(size: 1.0);

    /// <summary>The ground this is fought on.</summary>
    public BattleMap LoadMap() => MapLibrary.Load(MapName);

    /// <summary>
    /// Build the battle this mission describes, deployed, objectives set, and started.
    /// </summary>
    /// <remarks>
    /// The order is the one <see cref="Battle"/> insists on: everybody deployed and every
    /// objective set before <see cref="Battle.Start"/>, since both throw once the first round
    /// has begun.
    /// </remarks>
    public Battle Begin(int seed = 0, HexLayout? layout = null, BattleMap? map = null)
    {
        var battle = new Battle(map ?? LoadMap(), layout ?? Metres, seed: seed);
        Deploy(battle);
        foreach (var order in Objectives) battle.SetObjective(order.Build(this, battle));
        battle.Start();
        return battle;
    }

    /// <summary>Put everybody on a battle that has not started yet.</summary>
    public void Deploy(Battle battle)
    {
        foreach (var d in Deployments)
        {
            try
            {
                battle.Deploy(d.Name, d.Side, new NodeId(d.Where, 0), d.Stats, d.Facing, d.Loadout);
            }
            catch (ArgumentException e)
            {
                throw new MissionFormatException($"{d.Name}: {e.Message}", Name, d.Line);
            }
        }
    }

    /// <summary>
    /// Every place in a named piece of ground that a soldier could actually stop in.
    /// </summary>
    /// <remarks>
    /// A place is authored as tiles and used as nodes, and the gap between the two is regions: a
    /// hex cut by a chord is one tile and two nodes, and one of them may be an offcut nobody can
    /// stand in. Asking the graph rather than assuming region 0 is what makes <c>place</c> mean
    /// the ground rather than the coordinate.
    /// </remarks>
    public IReadOnlyList<NodeId> NodesOf(string place, MovementGraph graph, int line = 0)
    {
        if (!Places.TryGetValue(place, out var tiles))
            throw new MissionFormatException($"No place called '{place}' is declared.", Name, line);

        var nodes = graph.Nodes
            .Where(n => n.CanEndTurn && tiles.Contains(n.Id.Tile))
            .Select(n => n.Id)
            .ToList();

        if (nodes.Count == 0)
            throw new MissionFormatException($"Nobody can stand anywhere in '{place}'.", Name, line);

        return nodes;
    }

    /// <summary>
    /// The one place in a named piece of ground that stands for the whole of it: its middle.
    /// </summary>
    /// <remarks>
    /// An exit is a set of nodes because any of them will do, and a thing to look at is one node
    /// because <see cref="Reconnaissance"/> traces a line to it. So a statement that says
    /// <c>at house</c> has to choose, and the rule is the node with the least total distance to
    /// the rest of the place — the middle of the room rather than a corner of it, and the same
    /// answer whatever order the file happened to list the ground in.
    /// <para>
    /// Chosen from the nodes a soldier could stop in, which is what <see cref="NodesOf"/> gives,
    /// for two reasons: the objective prices the walk to the place as well as the look at it, so
    /// an unreachable target would flatten the gradient the commander follows; and a place nobody
    /// can enter is a place the format should refuse rather than quietly aim at a wall. The
    /// second of those is a limit worth knowing about — a sealed vault is a real thing to
    /// photograph and this cannot yet name one.
    /// </para>
    /// </remarks>
    public NodeId NodeOf(string place, MovementGraph graph, int line = 0)
    {
        var nodes = NodesOf(place, graph, line);

        return nodes
            .OrderBy(n => nodes.Sum(other => n.Hex.DistanceTo(other.Hex)))
            .ThenBy(n => n.Layer)
            .ThenBy(n => n.Hex.Q)
            .ThenBy(n => n.Hex.R)
            .First();
    }
}
