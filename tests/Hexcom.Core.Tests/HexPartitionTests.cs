using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// A hex has fifteen possible wall segments: six sides, six minor chords and three bisectors.
/// These tests pin down what each does to the space inside the tile.
/// </summary>
public class HexPartitionTests
{
    private static HexRegion RegionWithSide(IReadOnlyList<HexRegion> regions, HexDirection side)
        => Assert.Single(regions.Where(r => r.BoundsSide(side)));

    [Fact]
    public void AnEmptyHexIsOneWholeStandableRegion()
    {
        var regions = HexPartition.Compute([]);

        var region = Assert.Single(regions);
        Assert.Equal(1.0, region.AreaFraction, 9);
        Assert.Equal(6, region.Sides.Count);
        Assert.Empty(region.Chords);
        Assert.True(region.Occupiable);
    }

    [Fact]
    public void AWallAlongASideDoesNotDivideTheHex()
    {
        // Sides bound the tile rather than cutting it, so they leave one region.
        var regions = HexPartition.Compute([(0, 1), (3, 4)]);
        Assert.Single(regions);
        Assert.Equal(1.0, regions[0].AreaFraction, 9);
    }

    [Fact]
    public void AMinorChordClipsASixthOffAndLeavesTheRestStandable()
    {
        var regions = HexPartition.Compute([(0, 2)]);

        Assert.Equal(2, regions.Count);

        var major = regions[0];
        Assert.Equal(5.0 / 6.0, major.AreaFraction, 9);
        Assert.True(major.Occupiable);
        Assert.Equal(
            [HexDirection.NorthWest, HexDirection.SouthWest, HexDirection.South, HexDirection.SouthEast],
            major.Sides);

        var offcut = regions[1];
        Assert.Equal(1.0 / 6.0, offcut.AreaFraction, 9);
        Assert.False(offcut.Occupiable);
        Assert.Equal([HexDirection.NorthEast, HexDirection.North], offcut.Sides);
    }

    [Fact]
    public void ABisectorSplitsTheHexInHalfAndNeitherHalfIsStandable()
    {
        var regions = HexPartition.Compute([(0, 3)]);

        Assert.Equal(2, regions.Count);
        Assert.All(regions, r => Assert.Equal(0.5, r.AreaFraction, 9));

        // Half a hex is room to pass through, not room to fight from.
        Assert.All(regions, r => Assert.False(r.Occupiable));

        Assert.Equal(
            [HexDirection.NorthEast, HexDirection.North, HexDirection.NorthWest],
            RegionWithSide(regions, HexDirection.North).Sides);
        Assert.Equal(
            [HexDirection.SouthWest, HexDirection.South, HexDirection.SouthEast],
            RegionWithSide(regions, HexDirection.South).Sides);
    }

    [Fact]
    public void TwoMinorChordsLeaveATwoThirdsRegionBetweenThem()
    {
        var regions = HexPartition.Compute([(0, 2), (2, 4)]);

        Assert.Equal(3, regions.Count);
        Assert.Equal(4.0 / 6.0, regions[0].AreaFraction, 9);
        Assert.True(regions[0].Occupiable);
        Assert.Equal(2, regions.Count(r => Math.Abs(r.AreaFraction - 1.0 / 6.0) < 1e-9));
        Assert.Equal(2, regions.Count(r => !r.Occupiable));
    }

    [Theory]
    [InlineData(new[] { 0, 2 })]
    [InlineData(new[] { 0, 3 })]
    [InlineData(new[] { 1, 4 })]
    [InlineData(new[] { 0, 2, 2, 4 })]
    [InlineData(new[] { 0, 2, 3, 5 })]
    [InlineData(new[] { 0, 2, 2, 4, 4, 0 })]
    public void RegionAreasAlwaysSumToTheWholeHex(int[] flatChords)
    {
        var chords = Enumerable.Range(0, flatChords.Length / 2)
            .Select(i => (flatChords[i * 2], flatChords[i * 2 + 1]));

        var regions = HexPartition.Compute(chords);
        Assert.Equal(1.0, regions.Sum(r => r.AreaFraction), 9);
    }

    [Theory]
    [InlineData(new[] { 0, 2 })]
    [InlineData(new[] { 0, 3 })]
    [InlineData(new[] { 0, 2, 2, 4 })]
    [InlineData(new[] { 0, 2, 3, 5 })]
    public void EverySideBelongsToExactlyOneRegion(int[] flatChords)
    {
        var chords = Enumerable.Range(0, flatChords.Length / 2)
            .Select(i => (flatChords[i * 2], flatChords[i * 2 + 1]));

        var sides = HexPartition.Compute(chords).SelectMany(r => r.Sides).ToList();

        Assert.Equal(6, sides.Count);
        Assert.Equal(6, sides.Distinct().Count());
    }

    [Fact]
    public void ThreeMinorChordsLeaveATriangleInTheMiddle()
    {
        // Clipping all three alternating corners leaves half the hex as a central triangle.
        var regions = HexPartition.Compute([(0, 2), (2, 4), (4, 0)]);

        Assert.Equal(4, regions.Count);
        Assert.Equal(0.5, regions[0].AreaFraction, 9);
        Assert.Empty(regions[0].Sides); // walled in on every side
        Assert.All(regions, r => Assert.False(r.Occupiable));
    }

    [Fact]
    public void EachRegionsCentroidFallsInsideTheHex()
    {
        foreach (var region in HexPartition.Compute([(0, 2)]))
            Assert.True(region.LocalCentroid.Length < 1.0);
    }

    [Fact]
    public void CrossingWallsInsideOneHexAreRejected()
    {
        // Two bisectors meeting at the centre. Model that shape across neighbouring hexes.
        var error = Assert.Throws<HexPartitionException>(() => HexPartition.Compute([(0, 3), (1, 4)]));
        Assert.Contains("cross", error.Message);
    }

    [Fact]
    public void ChordsAreClassifiedByHowFarApartTheirCornersAre()
    {
        Assert.Equal(ChordClass.Side, WallSegment.Classify(0, 1));
        Assert.Equal(ChordClass.Side, WallSegment.Classify(5, 0));
        Assert.Equal(ChordClass.Minor, WallSegment.Classify(0, 2));
        Assert.Equal(ChordClass.Minor, WallSegment.Classify(4, 0));
        Assert.Equal(ChordClass.Bisector, WallSegment.Classify(0, 3));
        Assert.Equal(ChordClass.Bisector, WallSegment.Classify(5, 2));
    }

    [Fact]
    public void OccupancyThresholdIsTunable()
    {
        // Loosen it and the halves of a bisected hex become standable after all.
        var loose = HexPartition.Compute([(0, 3)], occupancyThreshold: 0.4);
        Assert.All(loose, r => Assert.True(r.Occupiable));
    }
}
