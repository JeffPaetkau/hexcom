using System;
using System.Collections.Generic;

namespace Hexcom.Rules;

/// <summary>
/// What a unit can reach on a piece of ground and what each way there costs: a priced graph
/// over the hexes, with the ground asked for the price of every step as it is needed.
/// </summary>
/// <remarks>
/// <para>
/// The graph is implicit. Every hex is a node and every pair of neighbours a link, and the
/// price of a link is a question about the ground under both ends, so there is nothing to
/// build ahead of time and no edge of the map to run off. What the ground says about a hex
/// is remembered, because the height function is not cheap and a search asks about each hex
/// several times.
/// </para>
/// <para>
/// A step is priced by the surface it lands on and the grade between the two centres, then
/// scaled for the soldier taking it. Reach is Dijkstra from where the unit stands with what
/// it has left, so how far it can get and how it gets there are the same question.
/// </para>
/// </remarks>
public sealed class Movement
{
    /// <summary>Centre to neighbouring centre, metres: the run of every step.</summary>
    public static readonly double Stride = Units.HexSize * Math.Sqrt(3);

    private readonly IGround _ground;
    private readonly Dictionary<Hex, (double Height, Surface Surface)> _known = new();

    public Movement(IGround ground, MovementCosts? costs = null)
    {
        _ground = ground;
        Costs = costs ?? MovementCosts.Default;
    }

    public MovementCosts Costs { get; }

    /// <summary>The height of the ground at a hex's centre.</summary>
    public double HeightAt(Hex hex) => Ask(hex).Height;

    /// <summary>What is underfoot at a hex's centre.</summary>
    public Surface SurfaceAt(Hex hex) => Ask(hex).Surface;

    /// <summary>
    /// What one step to a neighbouring hex costs a soldier, or null if the ground refuses it.
    /// </summary>
    public int? StepCost(Hex from, Hex to, CostProfile? profile = null)
    {
        var grade = (HeightAt(to) - HeightAt(from)) / Stride;
        if (Math.Abs(grade) > Costs.MaxGrade) return null;

        var slope = grade >= 0 ? Costs.ClimbPerGrade * grade : Costs.DescentPerGrade * -grade;
        return (profile ?? CostProfile.Default).Move(Costs.Stride(SurfaceAt(to)) + slope);
    }

    /// <summary>Everywhere a soldier can get to from a hex on a budget, and the cheapest way to each.</summary>
    public Reach Reachable(Hex from, int budget, CostProfile? profile = null)
    {
        var reached = new Dictionary<Hex, (int Cost, Hex? Via)> { [from] = (0, null) };
        var frontier = new PriorityQueue<Hex, int>();
        frontier.Enqueue(from, 0);

        while (frontier.TryDequeue(out var current, out var soFar))
        {
            // A stale entry: this hex was reached more cheaply after it was queued.
            if (soFar > reached[current].Cost) continue;

            for (var d = 0; d < 6; d++)
            {
                var next = current.Neighbour(d);
                if (StepCost(current, next, profile) is not { } step) continue;

                var cost = soFar + step;
                if (cost > budget) continue;
                if (reached.TryGetValue(next, out var known) && known.Cost <= cost) continue;

                reached[next] = (cost, current);
                frontier.Enqueue(next, cost);
            }
        }

        return new Reach(from, budget, reached);
    }

    private (double Height, Surface Surface) Ask(Hex hex)
    {
        if (_known.TryGetValue(hex, out var known)) return known;

        var (x, z) = hex.Centre;
        known = (_ground.Height(x, z), _ground.SurfaceAt(x, z));
        _known[hex] = known;
        return known;
    }
}

/// <summary>The result of one reach query: every hex within the budget, its cost, and the way to it.</summary>
public sealed class Reach
{
    private readonly Dictionary<Hex, (int Cost, Hex? Via)> _reached;

    internal Reach(Hex start, int budget, Dictionary<Hex, (int Cost, Hex? Via)> reached)
    {
        Start = start;
        Budget = budget;
        _reached = reached;
    }

    public Hex Start { get; }

    public int Budget { get; }

    /// <summary>How many hexes are in reach, the start included.</summary>
    public int Count => _reached.Count;

    /// <summary>Every hex in reach, the start included.</summary>
    public IEnumerable<Hex> Hexes => _reached.Keys;

    public bool Contains(Hex hex) => _reached.ContainsKey(hex);

    /// <summary>The cheapest cost to a hex, or null if it is out of reach.</summary>
    public int? CostTo(Hex hex) => _reached.TryGetValue(hex, out var r) ? r.Cost : null;

    /// <summary>The cheapest path to a hex, start first and destination last, or empty if it is out of reach.</summary>
    public IReadOnlyList<Hex> PathTo(Hex hex)
    {
        if (!_reached.TryGetValue(hex, out var at)) return Array.Empty<Hex>();

        var path = new List<Hex> { hex };
        while (at.Via is { } via)
        {
            path.Add(via);
            at = _reached[via];
        }

        path.Reverse();
        return path;
    }
}
