using System.Linq;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;

namespace Hexcom.Content.Tests;

/// <summary>
/// The format is finished when it can say everything the corner graph can hold and the demo
/// map comes out of a file identical to the one built by hand. These tests are that sentence.
/// </summary>
public class MapFileTests
{
    // ---- the two candidates are one format ---------------------------------------

    [Fact]
    public void TheCompoundFromTheFileIsTheCompoundFromTheCode()
    {
        MapEquality.AssertSame(DemoMaps.Compound(), MapLibrary.Load("compound"));
    }

    [Fact]
    public void LoweringAMapBuiltInCodeToPrimitivesLosesNothing()
    {
        var original = DemoMaps.Compound();
        var text = MapWriter.Write(original, "Compound");
        var reread = MapFile.Parse(text, "lowered").Map;

        MapEquality.AssertSame(original, reread);

        // And it really is primitives: nothing in it needs the shorthand to be understood.
        var statements = text.Split('\n').Select(l => l.Split(' ')[0]).Where(k => k.Length > 0 && k[0] != '#');
        Assert.All(statements, k => Assert.Contains(k, new[] { "map", "tile", "chord", "link" }));
    }

    [Fact]
    public void LoweringAMapWrittenWithShorthandLosesNothing()
    {
        // The waystation uses every shorthand statement there is, and declares its own kit.
        var original = MapLibrary.Read("waystation");
        var reread = MapFile.Parse(MapWriter.Write(original.Map, original.Name), "lowered");

        MapEquality.AssertSame(original.Map, reread.Map);
        Assert.Contains("hedge", reread.Profiles.Keys);
        Assert.Contains("boardwalk", reread.Grounds.Keys);
    }

    [Theory]
    [MemberData(nameof(ShippedMaps))]
    public void EveryShippedMapReadsAndBuildsAGraph(string name)
    {
        var map = MapLibrary.Load(name);
        var graph = MovementGraph.Build(map);
        Assert.NotEmpty(graph.Nodes);
    }

    public static TheoryData<string> ShippedMaps()
    {
        var data = new TheoryData<string>();
        foreach (var name in MapLibrary.Names) data.Add(name);
        return data;
    }

    // ---- the size entry 007 asked for ----------------------------------------------

    [Fact]
    public void TheWaystationIsBigEnoughForTheRangesToMeanSomething()
    {
        var map = MapLibrary.Load("waystation");

        // Radius 20 to 30 is the figure; 24 is 1801 tiles of ground before the roofs.
        Assert.InRange(map.Tiles.Count(t => t.Address.Layer == 0), 1500, 3000);
        Assert.True(map.Tiles.Any(t => t.Address.Layer == 1), "nothing to climb onto");
    }

    [Fact]
    public void EverySpotOnTheWaystationCanBeReachedFromTheCrossroads()
    {
        var map = MapLibrary.Load("waystation");
        var graph = MovementGraph.Build(map);
        var reach = Pathfinder.Reachable(graph, new NodeId(Hex.Zero, 0), int.MaxValue);

        var cutOff = graph.Nodes.Where(n => n.CanEndTurn && !reach.CanReach(n.Id)).Select(n => n.Id.ToString()).ToList();
        Assert.True(cutOff.Count == 0, $"{cutOff.Count} nodes cut off: {string.Join(", ", cutOff.Take(10))}");
    }

    // ---- shorthand -------------------------------------------------------------------

    [Fact]
    public void AWallAlongALineOfHexesIsOneWallPerSidePerHex()
    {
        var map = Parse("fill disc 0,0 r 3\nwall solid line 0,-2 to 0,2 nw sw");

        Assert.Equal(10, map.Walls.Count);
        Assert.NotNull(map.GetSideWall(new Hex(0, 1), HexDirection.NorthWest, 0));
        Assert.NotNull(map.GetSideWall(new Hex(0, -2), HexDirection.SouthWest, 0));
        Assert.Null(map.GetSideWall(new Hex(0, 3), HexDirection.NorthWest, 0));
    }

    [Fact]
    public void ABreachRemovesOneFaceAndLeavesTheRestOfTheWallStanding()
    {
        var map = Parse("fill disc 0,0 r 3\nwall solid line 0,-2 to 0,2 nw\nbreach 0,0 nw");

        Assert.Null(map.GetSideWall(new Hex(0, 0), HexDirection.NorthWest, 0));
        Assert.NotNull(map.GetSideWall(new Hex(0, -1), HexDirection.NorthWest, 0));
        Assert.NotNull(map.GetSideWall(new Hex(0, 1), HexDirection.NorthWest, 0));
    }

    [Fact]
    public void EnclosingAShapeWallsOnlyTheSidesThatFaceOut()
    {
        var map = Parse("fill disc 0,0 r 3\nenclose solid disc 0,0 r 1");

        // Seven hexes have 42 sides between them; 24 of those are shared and interior.
        Assert.Equal(18, map.Walls.Count);
        Assert.Null(map.GetSideWall(Hex.Zero, HexDirection.North, 0));
        Assert.NotNull(map.GetSideWall(new Hex(0, 1), HexDirection.North, 0));

        // The graph agrees: the inside is sealed.
        var graph = MovementGraph.Build(map);
        var reach = Pathfinder.Reachable(graph, new NodeId(Hex.Zero, 0), int.MaxValue);
        Assert.Equal(7, reach.Destinations.Count());
    }

    [Fact]
    public void ASideIsTheSameWallFromEitherHex()
    {
        var map = Parse("fill disc 0,0 r 1\nwall low hex 0,0 ne");

        Assert.Single(map.Walls);
        Assert.NotNull(map.GetSideWall(new Hex(1, 0), HexDirection.SouthWest, 0));
    }

    [Fact]
    public void PaintingATileKeepsWhateverTheStatementDidNotMention()
    {
        var map = Parse("fill disc 0,0 r 1 h 1.5 gravel\nfill hex 0,0 rubble\nfill hex 1,0 h 0.2");

        var repainted = map.GetTile(new TileAddress(Hex.Zero, 0))!;
        Assert.Equal(1.5, repainted.FloorHeight);
        Assert.Equal(GroundType.Rubble, repainted.Ground);

        var lowered = map.GetTile(new TileAddress(new Hex(1, 0), 0))!;
        Assert.Equal(0.2, lowered.FloorHeight);
        Assert.Equal(GroundType.Gravel, lowered.Ground);
    }

    [Fact]
    public void ATileOnAnUpperLayerDefaultsToThatLayersHeight()
    {
        var map = Parse("layer-height 2.5\nfill hex 0,0\nfill hex 0,0 layer 2");

        Assert.Equal(0.0, map.GetTile(new TileAddress(Hex.Zero, 0))!.FloorHeight);
        Assert.Equal(5.0, map.GetTile(new TileAddress(Hex.Zero, 2))!.FloorHeight);
    }

    [Fact]
    public void ALadderIsAnAuthoredLinkAndADrainIsAOneWayCrawl()
    {
        var map = Parse("fill hex 0,0\nfill hex 0,0 layer 1 h 4\nladder 0,0 0,0@1\nlink crawl 0,0 1,0 one-way cost 20");

        Assert.Collection(map.Links,
            l => Assert.Equal(new AuthoredLink(new TileAddress(Hex.Zero, 0), new TileAddress(Hex.Zero, 1), TraversalKind.Ladder), l),
            l =>
            {
                Assert.Equal(TraversalKind.Crawl, l.Kind);
                Assert.False(l.Bidirectional);
                Assert.Equal(20, l.ApCost);
            });
    }

    // ---- open data -----------------------------------------------------------------

    [Fact]
    public void ADeclaredProfileIsNewKitWithoutARuleChange()
    {
        var map = Parse("profile hedge height 1.5 cover light passable opaque\nfill hex 0,0\nchord hedge 0,0 0-2");

        var wall = Assert.Single(map.Walls);
        Assert.Equal("hedge", wall.Profile.Id);
        Assert.Equal(1.5, wall.Profile.HeightMetres);
        Assert.False(wall.Profile.BlocksMovement);
        Assert.True(wall.Profile.Opaque);
        Assert.False(wall.Profile.Destructible);
    }

    [Fact]
    public void ADeclaredGroundIsNewFootingWithoutARuleChange()
    {
        var map = Parse("ground bog cost 3 noise 0.5\nfill hex 0,0 bog");

        var ground = Assert.Single(map.Tiles).Ground;
        Assert.Equal(("bog", 3, 0.5, true), (ground.Id, ground.ExtraApCost, ground.NoiseFactor, ground.Passable));
    }

    // ---- refusals name the line ----------------------------------------------------

    [Theory]
    [InlineData("fill hex 0,0\nchord hedge 0,0 0-2", 2, "hedge")]
    [InlineData("fill hex 0,0\n\n# comment\nwall solid hex 0,0 up", 4, "'up'")]
    [InlineData("fill hex 0,0\noccupancy 0.5", 2, "before the first tile")]
    [InlineData("profile low height 1 cover half", 1, "built-in")]
    [InlineData("fill hex 0,0\nbreach 0,0 n", 2, "no wall")]
    [InlineData("fill hex 0,0\nchord low 0,0 0-3\nchord low 0,0 1-4", 3, "cross")]
    [InlineData("fill hex 0,0\ntile 0,0 h", 2, "line ended")]
    [InlineData("fill hex 0,0 gravel extra", 1, "'extra'")]
    public void AMistakeIsRefusedWithItsLineNumber(string text, int line, string mentions)
    {
        var error = Assert.Throws<MapFormatException>(() => MapFile.Parse(text, "test.hexmap"));

        Assert.Equal(line, error.Line);
        Assert.Contains(mentions, error.Message);
        Assert.StartsWith("test.hexmap:", error.Message);
    }

    private static BattleMap Parse(string text) => MapFile.Parse(text).Map;
}
