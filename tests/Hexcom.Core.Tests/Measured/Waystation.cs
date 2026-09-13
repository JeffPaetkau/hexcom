using System.Collections.Generic;
using System.Linq;
using Hexcom.Content;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;

namespace Hexcom.Core.Tests.Measured;

/// <summary>
/// The waystation, set up as the mission it is rather than as the mission its file can currently
/// say.
/// </summary>
/// <remarks>
/// The file says reconnaissance now — entry 081 uncommented the line — and this still builds
/// the objective by hand for one reason: the clock. <c>rounds 30</c> is read by nothing in the
/// format yet (entry 082's half for Content is open), and an objective's <c>Stop</c> is set at
/// construction, so the only way to fight the file's mission <em>with</em> the file's hour is to
/// build the same reconnaissance off the same places and hang the deadline on it here. Everything
/// else — the map, the squads, their posts and kit, the exit — comes off the file unchanged.
/// Delete this in favour of <c>Mission.Objectives</c> the day the file writes its own deadline.
/// </remarks>
public static class Waystation
{
    /// <summary>The mission, read once. The map is read per battle because a map is mutable.</summary>
    public static Mission Mission { get; } = MissionLibrary.Load("waystation");

    /// <summary>
    /// The thing to get eyes on: the house, by the name the file gives it.
    /// </summary>
    /// <remarks>
    /// A place is a set of tiles and an objective wants one node, so this takes the one nearest
    /// the middle of the place — which for a disc is its centre, and for anything else is the
    /// least arbitrary choice available. Whatever Content's grammar eventually does for
    /// <c>at house</c> has the same decision to make.
    /// </remarks>
    public static NodeId Target(Battle battle)
    {
        var tiles = Mission.Places["house"];
        var centre = Middle(tiles.Select(t => t.Hex).ToList());

        var nodes = battle.Graph.Nodes
            .Where(n => tiles.Contains(n.Id.Tile))
            .Select(n => n.Id)
            .OrderBy(n => n.Hex.DistanceTo(centre))
            .ThenBy(n => n.Layer)
            .ToList();

        if (nodes.Count == 0)
            throw new InvalidOperationException("Nothing in 'house' is on the movement graph.");

        return nodes[0];
    }

    private static Hex Middle(IReadOnlyList<Hex> hexes)
        => hexes.OrderBy(h => hexes.Sum(other => h.DistanceTo(other))).First();

    /// <summary>
    /// Start the fight, with the reconnaissance the briefing describes.
    /// </summary>
    /// <param name="listPrice">
    /// Deploy everybody at list price rather than in the post the file names, which is the only
    /// way to ask what the two cost archetypes are doing. Entry 062 turned them on in a live
    /// behaviour change that 391 tests did not notice.
    /// </param>
    /// <param name="swapPosts">
    /// Put the scout where the trooper stands and the trooper where the scout stands, keeping
    /// everything else. Entry 048 reads the scout as the one nobody notices and the trooper as the
    /// one everybody does; swapping the two posts is what tells the man from the ground he was
    /// given, and nothing else does.
    /// </param>
    /// <param name="clock">
    /// What stops the mission, or null for the file's own round limit and nothing else.
    /// </param>
    /// <param name="slope">
    /// The model the battle itself is built with, which is where an objective reads its horizon
    /// from — once, at <c>Start</c>. A horizon handed only to a commander is never read: the first
    /// run of this batch did exactly that and measured the shipped slope six times over.
    /// </param>
    /// <param name="briefed">
    /// Hand the squad what its own briefing says: the four posts, as markers at
    /// <see cref="AwarenessState.Searching"/>, the rung a soldier will go and check. The file's
    /// <c>presence</c> part names every one of them, and the rules had nowhere to hold it; without
    /// this the scout walks its first turn blind into the view of a man the briefing describes.
    /// </param>
    /// <param name="firing">
    /// A multiplier on what every soldier on both sides pays to fire, on top of whatever their
    /// archetype already pays, so a scout stays slower on the trigger than a gunner at every
    /// setting. Both sides, because the question it serves is what shape of fight a price makes
    /// and not which side a cheaper shot favours — entry 094's item 14.
    /// </param>
    public static Battle Begin(
        int seed, bool listPrice = false, bool swapPosts = false, Deadline? clock = null, UtilityModel? slope = null,
        bool briefed = false, double firing = 1.0)
    {
        var battle = new Battle(Mission.LoadMap(), Mission.Metres, seed: seed, utility: slope);

        foreach (var d in Posted(swapPosts))
        {
            var stats = d.Stats ?? UnitStats.Default;
            if (listPrice) stats = stats with { Costs = CostProfile.Default };
            if (firing != 1.0) stats = stats with { Costs = stats.Costs with { Firing = stats.Costs.Firing * firing } };

            battle.Deploy(d.Name, d.Side, new NodeId(d.Where, 0), stats, d.Facing, d.Loadout);
        }

        if (briefed)
            foreach (var hostile in battle.Units.Where(u => u.Side == Side.Hostile).ToList())
                battle.Brief(Side.Player, hostile, AwarenessState.Searching);

        var exit = Mission.NodesOf("cottages", battle.Graph);

        battle.SetObjective(new Reconnaissance(Side.Player, Target(battle), exit)
        {
            Stop = clock ?? new Deadline(Round: Mission.Rounds),
        });

        battle.Start();
        return battle;
    }

    /// <summary>Everybody the file deploys, with the two ours optionally standing in each
    /// other's place.</summary>
    private static IEnumerable<Deployment> Posted(bool swap)
    {
        if (!swap) return Mission.Deployments;

        var scout = Mission.Deployments.First(d => d.Role == "scout");
        var trooper = Mission.Deployments.First(d => d.Role == "trooper");

        return Mission.Deployments.Select(d =>
            d == scout ? d with { Where = trooper.Where, Facing = trooper.Facing }
            : d == trooper ? d with { Where = scout.Where, Facing = scout.Facing }
            : d);
    }
}
