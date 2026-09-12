using System.Collections.Generic;
using System.Linq;
using Hexcom.Content;
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
/// The file carries a withdrawal because until now the rules had no other shape, and it carries
/// the reconnaissance line it wants beside it, commented out, waiting on Content to uncomment.
/// Measuring an objective dial against the withdrawal would measure the wrong thing: a withdrawal
/// on this ground is achieved by turning round and going home, which a dozen matches already do.
/// So the batch builds the reconnaissance the file describes, off the same places the file
/// declares, and everything else — the map, the squads, their posts and kit, the clock — comes
/// off the file unchanged. There is still one copy of the waystation.
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
    public static Battle Begin(
        int seed, bool listPrice = false, bool swapPosts = false, Deadline? clock = null, UtilityModel? slope = null)
    {
        var battle = new Battle(Mission.LoadMap(), Mission.Metres, seed: seed, utility: slope);

        foreach (var d in Posted(swapPosts))
        {
            var stats = d.Stats ?? UnitStats.Default;
            if (listPrice) stats = stats with { Costs = CostProfile.Default };

            battle.Deploy(d.Name, d.Side, new NodeId(d.Where, 0), stats, d.Facing, d.Loadout);
        }

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
