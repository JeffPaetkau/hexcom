using System.Linq;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// The demo map is the greybox the view layer loads, so it doubles as an end-to-end check that
/// the whole pipeline — tiles, walls, regions, graph, pathfinding — holds together.
/// </summary>
public class DemoMapTests
{
    private static readonly BattleMap Map = DemoMaps.Compound();
    private static readonly MovementGraph Graph = MovementGraph.Build(Map);

    [Fact]
    public void ItBuildsAndEveryTraversalKindTheBuilderKnowsShowsUp()
    {
        var kinds = Graph.AllLinks.Select(l => l.Kind).ToHashSet();

        Assert.Contains(TraversalKind.Walk, kinds);
        Assert.Contains(TraversalKind.Rough, kinds);
        Assert.Contains(TraversalKind.Vault, kinds);
        Assert.Contains(TraversalKind.Ladder, kinds);
    }

    [Fact]
    public void TheGroundFloorIsOneConnectedSpace()
    {
        var start = new NodeId(new Hex(-2, 0), 0);
        var reach = Pathfinder.Reachable(Graph, start, int.MaxValue);

        var groundNodes = Graph.Nodes.Where(n => n.Id.Layer == 0 && n.CanEndTurn);
        Assert.All(groundNodes, n => Assert.True(reach.CanReach(n.Id), $"{n.Id} was cut off"));
    }

    [Fact]
    public void TheRoofIsOnlyReachableByTheLadder()
    {
        var roof = new NodeId(new Hex(4, 0), layer: 1);
        var below = new NodeId(new Hex(4, 0), layer: 0);

        var link = Assert.Single(Graph.LinksFrom(below).Where(l => l.To == roof));
        Assert.Equal(TraversalKind.Ladder, link.Kind);

        // Every other way onto the roof would have to come from a neighbouring ground tile.
        var otherWaysUp = Graph.AllLinks
            .Where(l => l.To.Layer == 1 && l.From.Layer == 0 && l.Kind != TraversalKind.Ladder);
        Assert.Empty(otherWaysUp);
    }

    [Fact]
    public void ClimbingTheLadderCostsMostOfATurn()
    {
        var reach = Pathfinder.Reachable(Graph, new NodeId(new Hex(4, 0), 0), MovementCosts.Default.ActionPointsPerTurn);
        var onTheRoof = reach.CostTo(new NodeId(new Hex(4, 0), layer: 1));

        Assert.Equal(MovementCosts.Default.Ladder, onTheRoof);
        Assert.True(onTheRoof > MovementCosts.Default.ActionPointsPerTurn / 2);
    }

    [Fact]
    public void TheCompoundWallForcesTraffficThroughTheBreach()
    {
        // Outside the wall, level with the gap.
        var outside = new NodeId(new Hex(1, 0), 0);
        var inside = new NodeId(new Hex(2, 0), 0);
        var reach = Pathfinder.Reachable(Graph, outside, int.MaxValue);

        Assert.Equal(1, reach.CostTo(inside));

        // One column north the wall is unbroken, so that crossing costs a detour.
        var blockedOutside = new NodeId(new Hex(1, 1), 0);
        var blockedInside = new NodeId(new Hex(2, 1), 0);
        Assert.True(Pathfinder.Reachable(Graph, blockedOutside, int.MaxValue).CostTo(blockedInside) > 1);
    }

    [Fact]
    public void TheBisectedTileIsCrossableButNotSomewhereToStand()
    {
        var split = new TileAddress(new Hex(0, -3), 0);

        Assert.Equal(2, Map.RegionsOf(split).Count);
        Assert.All(Map.RegionsOf(split), r => Assert.False(Graph.CanEndTurn(new NodeId(split, r.Index))));

        // Still passable: the two halves are joined by a vault over the barricade.
        var north = Map.RegionOnSide(split, HexDirection.North)!;
        var south = Map.RegionOnSide(split, HexDirection.South)!;
        Assert.Contains(
            Graph.LinksFrom(new NodeId(split, north.Index)),
            l => l.To == new NodeId(split, south.Index) && l.Kind == TraversalKind.Vault);
    }

    [Fact]
    public void TheClippedTileKeepsMostOfItsFloor()
    {
        var clipped = new TileAddress(new Hex(0, 3), 0);
        var regions = Map.RegionsOf(clipped);

        Assert.Equal(2, regions.Count);
        Assert.True(Graph.CanEndTurn(new NodeId(clipped, regions[0].Index)));
        Assert.Equal(5.0 / 6.0, regions[0].AreaFraction, 9);
    }

    [Fact]
    public void ATurnOfMovementCoversAMeaningfulButLimitedPatch()
    {
        var reach = Pathfinder.Reachable(
            Graph,
            new NodeId(new Hex(-2, 0), 0),
            MovementCosts.Default.ActionPointsPerTurn);

        // Enough room to manoeuvre, not enough to cross the map in one go.
        var count = reach.Destinations.Count();
        Assert.InRange(count, 40, Graph.Nodes.Count(n => n.CanEndTurn) - 1);
    }
}
