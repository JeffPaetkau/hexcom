using System.Collections.Generic;

namespace Hexcom.Game.Rules;

/// <summary>What a unit can reach and what it costs, on an open plain.</summary>
public static class Movement
{
    /// <summary>A stride across open ground. Ten hexes of it is a turn spent doing nothing else.</summary>
    public const int CostPerHex = 5;

    /// <summary>Every hex within the unit's remaining reach, its own included.</summary>
    public static HashSet<Hex> Reachable(Hex from, int ap)
    {
        var steps = ap / CostPerHex;
        var reached = new HashSet<Hex> { from };
        var frontier = new List<Hex> { from };

        for (var step = 0; step < steps; step++)
        {
            var next = new List<Hex>();
            foreach (var hex in frontier)
            {
                for (var d = 0; d < 6; d++)
                {
                    var n = hex.Neighbour(d);
                    if (reached.Add(n)) next.Add(n);
                }
            }
            frontier = next;
        }

        return reached;
    }

    /// <summary>The path from one hex to another, both ends included.</summary>
    public static IReadOnlyList<Hex> Path(Hex from, Hex to) => from.LineTo(to);

    /// <summary>What walking a path costs.</summary>
    public static int Cost(IReadOnlyList<Hex> path) => (path.Count - 1) * CostPerHex;
}
