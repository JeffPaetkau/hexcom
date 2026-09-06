using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Xunit;

namespace Hexcom.Core.Tests;

public class MovementTests
{
    private static readonly MovementCosts Costs = MovementCosts.Default;

    private static BattleMap Corridor(params int[] qs)
    {
        var map = new BattleMap();
        foreach (var q in qs) map.SetTile(new TileAddress(new Hex(q, 0), 0), 0);
        return map;
    }

    private static NodeId Node(int q, int r, int layer = 0, int region = 0)
        => new(new TileAddress(new Hex(q, r), layer), region);

    // ---- open ground -----------------------------------------------------------

    [Fact]
    public void OnOpenGroundActionPointCostEqualsHexDistance()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 4);
        var graph = MovementGraph.Build(map);

        var reach = Pathfinder.Reachable(graph, Node(0, 0), int.MaxValue);

        foreach (var hex in Hex.Zero.WithinRange(4))
            Assert.Equal(Hex.Zero.DistanceTo(hex), reach.CostTo(new NodeId(hex, 0)));
    }

    [Fact]
    public void ATurnsWorthOfPointsReachesExactlyThatManyHexes()
    {
        // The ground must reach further than the budget, or the map is what limits the answer.
        var map = new BattleMap().FillDisc(Hex.Zero, Costs.ActionPointsPerTurn + 2);
        var graph = MovementGraph.Build(map);

        var reach = Pathfinder.Reachable(graph, Node(0, 0), Costs.ActionPointsPerTurn);
        var destinations = reach.Destinations.Select(d => d.Node.Hex).ToHashSet();

        Assert.Equal(Hex.Zero.WithinRange(Costs.ActionPointsPerTurn).ToHashSet(), destinations);
    }

    [Fact]
    public void PathLinksChainFromStartToGoalAndSumToTheReportedCost()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 4);
        var graph = MovementGraph.Build(map);
        var goal = Node(3, -1);

        var reach = Pathfinder.Reachable(graph, Node(0, 0), int.MaxValue);
        Assert.True(reach.TryGetPath(goal, out var path));

        Assert.Equal(Node(0, 0), path[0].From);
        Assert.Equal(goal, path[^1].To);
        for (var i = 0; i < path.Count - 1; i++)
            Assert.Equal(path[i].To, path[i + 1].From);

        Assert.Equal(reach.CostTo(goal), path.Sum(l => l.ApCost));
    }

    [Fact]
    public void UnreachablePlacesReportNoPath()
    {
        var map = Corridor(0, 1);
        map.SetTile(new TileAddress(new Hex(9, 0), 0), 0); // an island
        var graph = MovementGraph.Build(map);

        var reach = Pathfinder.Reachable(graph, Node(0, 0), int.MaxValue);

        Assert.False(reach.CanReach(Node(9, 0)));
        Assert.Null(reach.CostTo(Node(9, 0)));
        Assert.False(reach.TryGetPath(Node(9, 0), out _));
    }

    // ---- walls on sides --------------------------------------------------------

    [Fact]
    public void ASolidWallOnASideStopsMovementThroughIt()
    {
        var map = Corridor(0, 1);
        map.AddSideWall(new Hex(0, 0), HexDirection.NorthEast, 0, WallProfile.Solid);
        var graph = MovementGraph.Build(map);

        Assert.Empty(graph.LinksFrom(Node(0, 0)));
        Assert.False(Pathfinder.Reachable(graph, Node(0, 0), int.MaxValue).CanReach(Node(1, 0)));
    }

    [Fact]
    public void ALowWallCostsAVaultRatherThanBlocking()
    {
        var map = Corridor(0, 1);
        map.AddSideWall(new Hex(0, 0), HexDirection.NorthEast, 0, WallProfile.Low);
        var graph = MovementGraph.Build(map);

        var link = Assert.Single(graph.LinksFrom(Node(0, 0)));
        Assert.Equal(TraversalKind.Vault, link.Kind);
        Assert.Equal(Costs.Vault, link.ApCost);
    }

    [Fact]
    public void AHighWallCanBeClimbedButNotVaulted()
    {
        var map = Corridor(0, 1);
        map.AddSideWall(new Hex(0, 0), HexDirection.NorthEast, 0, WallProfile.High);
        var graph = MovementGraph.Build(map);

        var link = Assert.Single(graph.LinksFrom(Node(0, 0)));
        Assert.Equal(TraversalKind.Climb, link.Kind);
        Assert.Equal(Costs.Climb, link.ApCost);
    }

    [Fact]
    public void SmokeAndHedgesBlockSightWithoutSlowingAnyoneDown()
    {
        var map = Corridor(0, 1);
        map.AddSideWall(new Hex(0, 0), HexDirection.NorthEast, 0, WallProfile.Screen);
        var graph = MovementGraph.Build(map);

        var link = Assert.Single(graph.LinksFrom(Node(0, 0)));
        Assert.Equal(TraversalKind.Walk, link.Kind);
        Assert.Equal(Costs.Walk, link.ApCost);
        Assert.True(WallProfile.Screen.BlocksSight);
    }

    [Fact]
    public void ASideWallIsSharedBySoBlocksBothNeighbours()
    {
        var map = Corridor(0, 1);
        map.AddSideWall(new Hex(0, 0), HexDirection.NorthEast, 0, WallProfile.Solid);

        // The same physical wall, named from the other side.
        Assert.NotNull(map.GetSideWall(new Hex(1, 0), HexDirection.SouthWest, 0));
        Assert.Equal(
            map.GetSideWall(new Hex(0, 0), HexDirection.NorthEast, 0),
            map.GetSideWall(new Hex(1, 0), HexDirection.SouthWest, 0));

        var graph = MovementGraph.Build(map);
        Assert.Empty(graph.LinksFrom(Node(1, 0)));
    }

    // ---- walls cutting through a hex -------------------------------------------

    [Fact]
    public void AWallBisectingAHexLetsUnitsCrossButNotStop()
    {
        var map = Corridor(-1, 0, 1);
        map.AddChord(new Hex(0, 0), 0, 3, 0, WallProfile.Low);
        var graph = MovementGraph.Build(map);

        // Neither half of the split hex is roomy enough to hold a unit.
        var halves = map.RegionsOf(new TileAddress(new Hex(0, 0), 0));
        Assert.Equal(2, halves.Count);
        Assert.All(halves, h => Assert.False(graph.CanEndTurn(new NodeId(new Hex(0, 0), 0, h.Index))));

        var reach = Pathfinder.Reachable(graph, Node(-1, 0), Costs.ActionPointsPerTurn);

        // You can still get to the far side: step in, vault the wall, step out.
        Assert.Equal(Costs.Walk + Costs.Vault + Costs.Walk, reach.CostTo(Node(1, 0)));

        // But the split hex never shows up as somewhere to end the move.
        Assert.Equal(
            [new Hex(-1, 0), new Hex(1, 0)],
            reach.Destinations.Select(d => d.Node.Hex).OrderBy(h => h.Q).ToList());
    }

    [Fact]
    public void AWallClippingACornerLeavesTheRestOfTheHexUsable()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 1);
        map.AddChord(new Hex(0, 0), 0, 2, 0, WallProfile.Low);
        var graph = MovementGraph.Build(map);

        var address = new TileAddress(new Hex(0, 0), 0);
        var major = map.RegionOnSide(address, HexDirection.South)!;
        var offcut = map.RegionOnSide(address, HexDirection.NorthEast)!;

        Assert.True(graph.CanEndTurn(new NodeId(address, major.Index)));
        Assert.False(graph.CanEndTurn(new NodeId(address, offcut.Index)));

        // The two pieces are joined by the wall between them, at vault price.
        var acrossTheWall = graph.LinksFrom(new NodeId(address, major.Index))
            .Single(l => l.To == new NodeId(address, offcut.Index));
        Assert.Equal(TraversalKind.Vault, acrossTheWall.Kind);
    }

    [Fact]
    public void ASolidWallAcrossAHexSealsTheTwoHalvesOffFromEachOther()
    {
        var map = Corridor(-1, 0, 1);
        map.AddChord(new Hex(0, 0), 0, 3, 0, WallProfile.Solid);
        var graph = MovementGraph.Build(map);

        Assert.False(Pathfinder.Reachable(graph, Node(-1, 0), int.MaxValue).CanReach(Node(1, 0)));
    }

    // ---- verticality -----------------------------------------------------------

    [Fact]
    public void AShortLedgeIsClimbedUpAndDroppedOffAtVeryDifferentPrices()
    {
        var map = new BattleMap();
        map.SetTile(new TileAddress(new Hex(0, 0), 0), 0);
        map.SetTile(new TileAddress(new Hex(1, 0), 0), 1.5);
        var graph = MovementGraph.Build(map);

        var up = Assert.Single(graph.LinksFrom(Node(0, 0)));
        Assert.Equal(TraversalKind.Climb, up.Kind);
        Assert.Equal(Costs.Climb, up.ApCost);
        Assert.Equal(1.5, up.HeightDelta, 9);

        var down = Assert.Single(graph.LinksFrom(Node(1, 0)));
        Assert.Equal(TraversalKind.Drop, down.Kind);
        Assert.Equal(Costs.Drop, down.ApCost);
    }

    [Fact]
    public void ACurbIsJustPartOfTheStride()
    {
        var map = new BattleMap();
        map.SetTile(new TileAddress(new Hex(0, 0), 0), 0);
        map.SetTile(new TileAddress(new Hex(1, 0), 0), Costs.StepHeight - 0.05);
        var graph = MovementGraph.Build(map);

        Assert.Equal(TraversalKind.Walk, Assert.Single(graph.LinksFrom(Node(0, 0))).Kind);
    }

    [Fact]
    public void TooHighToClimbMeansTheOnlyWayIsDown()
    {
        var map = new BattleMap();
        map.SetTile(new TileAddress(new Hex(0, 0), 0), 0);
        map.SetTile(new TileAddress(new Hex(1, 0), 0), 2.8); // above MaxClimb, within MaxSafeDrop
        var graph = MovementGraph.Build(map);

        Assert.Empty(graph.LinksFrom(Node(0, 0)));
        Assert.Equal(TraversalKind.Drop, Assert.Single(graph.LinksFrom(Node(1, 0))).Kind);
    }

    [Fact]
    public void AWallDoesNotMakeAnUnreachableHeightReachable()
    {
        // A railing on a rooftop is not a handhold for someone standing on the ground below.
        var map = new BattleMap();
        map.SetTile(new TileAddress(new Hex(0, 0), 0), 0);
        map.SetTile(new TileAddress(new Hex(1, 0), 1), 3.5);
        map.AddSideWall(new Hex(1, 0), HexDirection.SouthWest, 1, WallProfile.Railing);
        var graph = MovementGraph.Build(map);

        Assert.Empty(graph.LinksFrom(Node(0, 0)));
        Assert.Empty(graph.LinksFrom(Node(1, 0, layer: 1)));
    }

    [Fact]
    public void WhenBothAWallAndARiseAreInTheWayTheHarderOneSetsThePrice()
    {
        var map = new BattleMap();
        map.SetTile(new TileAddress(new Hex(0, 0), 0), 0);
        map.SetTile(new TileAddress(new Hex(1, 0), 0), 1.5); // a climb on its own
        map.AddSideWall(new Hex(0, 0), HexDirection.NorthEast, 0, WallProfile.Low); // a vault on its own
        var graph = MovementGraph.Build(map);

        var link = Assert.Single(graph.LinksFrom(Node(0, 0)));
        Assert.Equal(TraversalKind.Climb, link.Kind);
        Assert.Equal(Costs.Climb, link.ApCost);

        // Coming back down, the wall is the harder part.
        var back = Assert.Single(graph.LinksFrom(Node(1, 0)));
        Assert.Equal(TraversalKind.Vault, back.Kind);
        Assert.Equal(Costs.Vault, back.ApCost);
    }

    [Fact]
    public void ALadderEatsMostOfTheTurn()
    {
        var map = new BattleMap();
        map.SetTile(new TileAddress(new Hex(0, 0), 0), 0);
        for (var q = 0; q <= 6; q++)
            map.SetTile(new TileAddress(new Hex(q, 0), 1), 3.5); // too high to drop off

        map.AddLadder(new TileAddress(new Hex(0, 0), 0), new TileAddress(new Hex(0, 0), 1));
        var graph = MovementGraph.Build(map);

        var reach = Pathfinder.Reachable(graph, Node(0, 0), Costs.ActionPointsPerTurn);

        // Six of ten points just to get up there.
        Assert.Equal(Costs.Ladder, reach.CostTo(Node(0, 0, layer: 1)));

        // Which leaves four steps along the walkway, and no more.
        Assert.Equal(Costs.ActionPointsPerTurn, reach.CostTo(Node(4, 0, layer: 1)));
        Assert.False(reach.CanReach(Node(5, 0, layer: 1)));
    }

    [Fact]
    public void LaddersWorkBothWays()
    {
        var map = new BattleMap();
        map.SetTile(new TileAddress(new Hex(0, 0), 0), 0);
        map.SetTile(new TileAddress(new Hex(0, 0), 1), 3.5);
        map.AddLadder(new TileAddress(new Hex(0, 0), 0), new TileAddress(new Hex(0, 0), 1));
        var graph = MovementGraph.Build(map);

        Assert.Equal(Costs.Ladder, Pathfinder.Reachable(graph, Node(0, 0, 1), 10).CostTo(Node(0, 0)));
    }

    [Fact]
    public void SteppingOntoALowRoofWorksWithoutAnyAuthoredLink()
    {
        var map = new BattleMap();
        map.SetTile(new TileAddress(new Hex(0, 0), 0), 0);
        map.SetTile(new TileAddress(new Hex(1, 0), 1), 1.8); // a shed roof, one layer up
        var graph = MovementGraph.Build(map);

        var link = Assert.Single(graph.LinksFrom(Node(0, 0)));
        Assert.Equal(TraversalKind.Climb, link.Kind);
        Assert.Equal(Node(1, 0, layer: 1), link.To);
    }

    // ---- ground ----------------------------------------------------------------

    [Fact]
    public void BadFootingCostsExtraAndIsLabelledRough()
    {
        var map = Corridor(0);
        map.SetTile(new TileAddress(new Hex(1, 0), 0), 0, GroundType.Rubble);
        var graph = MovementGraph.Build(map);

        var link = Assert.Single(graph.LinksFrom(Node(0, 0)));
        Assert.Equal(TraversalKind.Rough, link.Kind);
        Assert.Equal(Costs.Walk + GroundType.Rubble.ExtraApCost, link.ApCost);
    }

    [Fact]
    public void ImpassableGroundIsNotEvenAPlace()
    {
        var map = Corridor(0);
        map.SetTile(new TileAddress(new Hex(1, 0), 0), 0, GroundType.Void);
        var graph = MovementGraph.Build(map);

        Assert.False(graph.Contains(Node(1, 0)));
        Assert.Empty(graph.LinksFrom(Node(0, 0)));
    }

    // ---- map bookkeeping -------------------------------------------------------

    [Fact]
    public void WallsCanOnlyJoinCornersOfACommonHex()
    {
        var map = new BattleMap();
        var far = new Hex(4, 4).Corner(0);

        Assert.Throws<ArgumentException>(
            () => map.AddWall(new Hex(0, 0).Corner(0), far, 0, WallProfile.Low));
    }

    [Fact]
    public void RemovingAWallRestoresTheHex()
    {
        var map = Corridor(-1, 0, 1);
        var hex = new Hex(0, 0);
        map.AddChord(hex, 0, 3, 0, WallProfile.Solid);
        Assert.Equal(2, map.RegionsOf(new TileAddress(hex, 0)).Count);

        Assert.True(map.RemoveWall(hex.Corner(0), hex.Corner(3), 0));
        Assert.Single(map.RegionsOf(new TileAddress(hex, 0)));

        var graph = MovementGraph.Build(map);
        Assert.Equal(2, Pathfinder.Reachable(graph, Node(-1, 0), 10).CostTo(Node(1, 0)));
    }

    [Fact]
    public void ChangingGeometryBumpsTheRevisionSoDerivedDataKnowsItIsStale()
    {
        var map = Corridor(0, 1);
        var before = map.Revision;
        map.AddSideWall(new Hex(0, 0), HexDirection.NorthEast, 0, WallProfile.Low);

        Assert.True(map.Revision > before);
        Assert.Equal(map.Revision, MovementGraph.Build(map).MapRevision);
    }
}
