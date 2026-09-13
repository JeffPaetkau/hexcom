using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Vision;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// The sight solver remembers what it has traced, and forgets it the moment the map changes.
/// </summary>
public class SightMemoryTests
{
    private static Vantage At(int q, int r) => new(new NodeId(new Hex(q, r), 0));

    /// <summary>
    /// The same pair asked twice hands back the same answer without tracing again; a wall going
    /// up between them is a different map, and the answer changes with it.
    /// </summary>
    [Fact]
    public void ATraceIsRememberedUntilAWallGoesUp()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 6);
        var solver = new SightSolver(map, new HexLayout(size: 1.0));

        var here = At(0, 0);
        var there = At(3, 0);

        Assert.True(solver.CanSee(here, there));
        Assert.Same(solver.Trace(here, there), solver.Trace(here, there));

        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Solid);

        Assert.False(solver.CanSee(here, there));
        Assert.False(solver.Trace(there, here).CanSee);
    }
}
