using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Hexcom.Core.Movement;

/// <param name="Via">The link that reached this node on the cheapest path, or null for the start.</param>
public sealed record ReachedNode(NodeId Node, int Cost, TraversalLink? Via);

/// <summary>Everywhere a unit can get to from one place on a given action point budget.</summary>
public sealed class ReachabilityResult
{
    private readonly Dictionary<NodeId, ReachedNode> _reached;

    internal ReachabilityResult(MovementGraph graph, NodeId start, int apBudget, Dictionary<NodeId, ReachedNode> reached)
    {
        Graph = graph;
        Start = start;
        ApBudget = apBudget;
        _reached = reached;
    }

    public MovementGraph Graph { get; }
    public NodeId Start { get; }
    public int ApBudget { get; }

    /// <summary>Every node touched, transit-only ones included.</summary>
    public IReadOnlyDictionary<NodeId, ReachedNode> Reached => _reached;

    /// <summary>
    /// The nodes a unit could actually finish its move on — transit nodes such as the halves of
    /// a bisected hex are excluded even though the path may run through them.
    /// </summary>
    public IEnumerable<ReachedNode> Destinations
        => _reached.Values.Where(r => Graph.CanEndTurn(r.Node));

    public bool CanReach(NodeId node) => _reached.ContainsKey(node);

    public int? CostTo(NodeId node) => _reached.TryGetValue(node, out var r) ? r.Cost : null;

    /// <summary>The cheapest sequence of moves from the start to <paramref name="goal"/>.</summary>
    public bool TryGetPath(NodeId goal, [NotNullWhen(true)] out IReadOnlyList<TraversalLink>? path)
    {
        path = null;
        if (!_reached.TryGetValue(goal, out var node)) return false;

        var links = new List<TraversalLink>();
        while (node.Via is not null)
        {
            links.Add(node.Via);
            node = _reached[node.Via.From];
        }

        links.Reverse();
        path = links;
        return true;
    }
}

/// <summary>
/// Dijkstra over the movement graph. Costs are action points, and because every link carries
/// its own price, "how far can this unit get" and "how do I get there" are the same query.
/// </summary>
public static class Pathfinder
{
    /// <summary>
    /// Everywhere reachable from <paramref name="start"/> within <paramref name="apBudget"/>
    /// action points. Pass <see cref="int.MaxValue"/> for the whole connected component.
    /// </summary>
    /// <param name="canEnter">
    /// Optional gate on which places may be entered at all, for things the map geometry does
    /// not know about — an enemy standing in the way, a locked door, a burning tile. The start
    /// is always allowed, so a unit already somewhere forbidden can still walk out of it.
    /// </param>
    /// <param name="price">
    /// What this particular traveller pays for a link, if not the listed price.
    /// </param>
    /// <remarks>
    /// Pricing is a parameter rather than a property of the graph on purpose. The graph describes
    /// the ground — a ladder is a ladder — and gets built once for the map; what a given soldier
    /// spends climbing it depends on them, and rebuilding the whole graph per unit to express
    /// that would be absurd.
    /// </remarks>
    public static ReachabilityResult Reachable(
        MovementGraph graph,
        NodeId start,
        int apBudget,
        Func<NodeId, bool>? canEnter = null,
        Func<TraversalLink, int>? price = null)
    {
        var reached = new Dictionary<NodeId, ReachedNode>();
        if (!graph.Contains(start)) return new ReachabilityResult(graph, start, apBudget, reached);

        var frontier = new PriorityQueue<NodeId, int>();
        reached[start] = new ReachedNode(start, 0, null);
        frontier.Enqueue(start, 0);

        while (frontier.TryDequeue(out var current, out var priority))
        {
            // Stale queue entry from a node we later reached more cheaply.
            if (priority > reached[current].Cost) continue;

            foreach (var link in graph.LinksFrom(current))
            {
                var cost = priority + (price?.Invoke(link) ?? link.ApCost);
                if (cost > apBudget) continue;
                if (canEnter is not null && !canEnter(link.To)) continue;
                if (reached.TryGetValue(link.To, out var existing) && existing.Cost <= cost) continue;

                reached[link.To] = new ReachedNode(link.To, cost, link);
                frontier.Enqueue(link.To, cost);
            }
        }

        return new ReachabilityResult(graph, start, apBudget, reached);
    }

    /// <summary>
    /// What it costs to reach the nearest of <paramref name="goals"/> from everywhere that can
    /// reach one at all.
    /// </summary>
    /// <remarks>
    /// The inverse of <see cref="Reachable"/>, and it exists because an objective needs a
    /// <em>gradient</em> rather than a destination. A place worth walking to is worth walking
    /// toward, and a search one step deep can only see that if every stride along the way scores
    /// — so something has to say how far off the goal each place is. One backward search over
    /// the whole graph answers it for every node at once, which is the difference between a
    /// commander that can afford to want something and one that cannot.
    /// <para>
    /// Walked backwards along <see cref="MovementGraph.LinksTo"/>, because the graph is directed:
    /// reading the forward links in reverse would let a soldier walk up a drop.
    /// </para>
    /// <para>
    /// Priced off the listed cost of the ground unless told otherwise. That is deliberate for the
    /// caller this was written for: the field describes the ground, once, and how quickly a
    /// particular soldier crosses it is about them.
    /// </para>
    /// </remarks>
    public static IReadOnlyDictionary<NodeId, int> CostToReach(
        MovementGraph graph,
        IEnumerable<NodeId> goals,
        Func<TraversalLink, int>? price = null)
    {
        var cost = new Dictionary<NodeId, int>();
        var frontier = new PriorityQueue<NodeId, int>();

        foreach (var goal in goals)
        {
            if (!graph.Contains(goal) || cost.ContainsKey(goal)) continue;
            cost[goal] = 0;
            frontier.Enqueue(goal, 0);
        }

        while (frontier.TryDequeue(out var current, out var priority))
        {
            if (priority > cost[current]) continue;

            foreach (var link in graph.LinksTo(current))
            {
                var reaching = priority + (price?.Invoke(link) ?? link.ApCost);
                if (cost.TryGetValue(link.From, out var existing) && existing <= reaching) continue;

                cost[link.From] = reaching;
                frontier.Enqueue(link.From, reaching);
            }
        }

        return cost;
    }

    /// <summary>The cheapest route between two nodes, ignoring any turn budget.</summary>
    public static bool TryFindPath(
        MovementGraph graph,
        NodeId start,
        NodeId goal,
        [NotNullWhen(true)] out IReadOnlyList<TraversalLink>? path,
        out int cost)
    {
        var result = Reachable(graph, start, int.MaxValue);
        cost = result.CostTo(goal) ?? 0;
        return result.TryGetPath(goal, out path);
    }
}
