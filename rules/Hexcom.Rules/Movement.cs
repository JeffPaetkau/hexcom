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
/// scaled for the soldier taking it. It is refused if that grade is past the limit, and also
/// if the ground under the far hex is itself steeper than the limit, whatever the rise of the
/// step: without that a soldier could climb a bank where it is gentle and sidle along the
/// contour onto its cliff. Reach is Dijkstra from where the unit stands with what it has
/// left, so how far it can get and how it gets there are the same question.
/// </para>
/// <para>
/// A steep enough descent can also be hurried: a cheaper step with a chance of a fall. Reach
/// is asked for either the careful kind, where no step is hurried, or the hurrying kind, where
/// a step is hurried whenever that is cheaper, and each hex then carries the risk of the way
/// to it, the falls compounded along the path. Between two ways of the same price the safer
/// is kept.
/// </para>
/// </remarks>
public sealed class Movement
{
    /// <summary>Centre to neighbouring centre, metres: the run of every step.</summary>
    public const double Stride = Units.Stride;

    /// <summary>How many times the ground is asked for a height per hex: the centre and four points half a stride out, for the slope.</summary>
    public const int HeightsPerHex = 5;

    private readonly IGround _ground;
    private readonly Dictionary<Hex, (double Height, Surface Surface, double Grade)> _known = new();

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

    /// <summary>How steep the ground under a hex is: rise over run of the slope at its centre.</summary>
    public double GradeAt(Hex hex) => Ask(hex).Grade;

    /// <summary>Whether a soldier can stand on a hex at all: its ground is no steeper than the limit.</summary>
    public bool CanStand(Hex hex) => GradeAt(hex) <= Costs.MaxGrade;

    /// <summary>
    /// What one step to a neighbouring hex costs a soldier, or null if the ground refuses it.
    /// </summary>
    public int? StepCost(Hex from, Hex to, CostProfile? profile = null)
    {
        if (!CanStand(to)) return null;

        var grade = (HeightAt(to) - HeightAt(from)) / Stride;
        if (Math.Abs(grade) > Costs.MaxGrade) return null;

        var slope = grade >= 0 ? Costs.ClimbPerGrade * grade : Costs.DescentPerGrade * -grade;
        return (profile ?? CostProfile.Default).Move(Costs.Stride(SurfaceAt(to)) + slope);
    }

    /// <summary>
    /// What one hurried step to a neighbouring hex costs a soldier: a descent taken at a run,
    /// cheaper than the careful step. Null where there is no hurried way, because the ground
    /// does not fall steeply enough, or refuses the step altogether.
    /// </summary>
    public int? HurriedStepCost(Hex from, Hex to, CostProfile? profile = null)
    {
        if (!CanStand(to)) return null;

        var descent = (HeightAt(from) - HeightAt(to)) / Stride;
        if (descent < Costs.HurryGrade || descent > Costs.MaxGrade) return null;

        return (profile ?? CostProfile.Default).Move(Costs.Stride(SurfaceAt(to)) - Costs.HurryPerGrade * descent);
    }

    /// <summary>The chance that a hurried step from one hex to the next ends in a fall.</summary>
    public double TripChance(Hex from, Hex to)
    {
        var descent = (HeightAt(from) - HeightAt(to)) / Stride;
        return Math.Clamp(Costs.TripPerGrade * descent, 0, 1);
    }

    /// <summary>
    /// Everywhere a soldier can get to from a hex on a budget, and the cheapest way to each:
    /// carefully, or hurrying down every slope where that is cheaper.
    /// </summary>
    public Reach Reachable(Hex from, int budget, CostProfile? profile = null, bool hurrying = false)
    {
        var reached = new Dictionary<Hex, Arrival> { [from] = new(0, null, 1.0, false) };
        var frontier = new PriorityQueue<Hex, int>();
        frontier.Enqueue(from, 0);

        while (frontier.TryDequeue(out var current, out var soFar))
        {
            // A stale entry: this hex was reached more cheaply after it was queued.
            if (soFar > reached[current].Cost) continue;

            for (var d = 0; d < 6; d++)
            {
                var next = current.Neighbour(d);
                var step = StepCost(current, next, profile);
                var hurried = false;

                if (hurrying && HurriedStepCost(current, next, profile) is { } quick && (step is null || quick < step))
                {
                    step = quick;
                    hurried = true;
                }

                if (step is not { } price) continue;

                var cost = soFar + price;
                if (cost > budget) continue;

                var survival = reached[current].Survival * (hurried ? 1 - TripChance(current, next) : 1);
                if (reached.TryGetValue(next, out var known) && (known.Cost < cost || (known.Cost == cost && known.Survival >= survival))) continue;

                reached[next] = new Arrival(cost, current, survival, hurried);
                frontier.Enqueue(next, cost);
            }
        }

        return new Reach(from, budget, reached);
    }

    private (double Height, Surface Surface, double Grade) Ask(Hex hex)
    {
        if (_known.TryGetValue(hex, out var known)) return known;

        // The slope from central differences half a stride out, so a hex on a bank between
        // two level neighbours still reads as steep.
        var (x, z) = hex.Centre;
        const double d = Stride / 2;
        var gx = (_ground.Height(x + d, z) - _ground.Height(x - d, z)) / (2 * d);
        var gz = (_ground.Height(x, z + d) - _ground.Height(x, z - d)) / (2 * d);

        known = (_ground.Height(x, z), _ground.SurfaceAt(x, z), Math.Sqrt(gx * gx + gz * gz));
        _known[hex] = known;
        return known;
    }
}

/// <summary>How a hex was got to: at what cost, from where, how likely on one's feet, and whether the last step was hurried.</summary>
internal readonly record struct Arrival(int Cost, Hex? Via, double Survival, bool Hurried);

/// <summary>The result of one reach query: every hex within the budget, its cost, the risk, and the way to it.</summary>
public sealed class Reach
{
    private readonly Dictionary<Hex, Arrival> _reached;

    internal Reach(Hex start, int budget, Dictionary<Hex, Arrival> reached)
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

    /// <summary>The chance of a fall somewhere on the way to a hex, zero on a careful way, or null if it is out of reach.</summary>
    public double? RiskTo(Hex hex) => _reached.TryGetValue(hex, out var r) ? 1 - r.Survival : null;

    /// <summary>Whether the step that arrives at a hex on the way to it is hurried.</summary>
    public bool HurriedInto(Hex hex) => _reached.TryGetValue(hex, out var r) && r.Hurried;

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
