using System.Linq;
using Hexcom.Core.Hexes;
using Xunit;

namespace Hexcom.Core.Tests;

public class HexTests
{
    [Fact]
    public void CubeConstraintHolds()
    {
        foreach (var hex in Hex.Zero.WithinRange(4))
            Assert.Equal(0, hex.Q + hex.R + hex.S);
    }

    [Fact]
    public void DistanceIsSymmetricAndZeroOnSelf()
    {
        var a = new Hex(2, -3);
        var b = new Hex(-1, 4);

        Assert.Equal(0, a.DistanceTo(a));
        Assert.Equal(a.DistanceTo(b), b.DistanceTo(a));
        Assert.Equal(7, a.DistanceTo(b));
    }

    [Fact]
    public void EveryNeighbourIsExactlyOneStepAway()
    {
        var hex = new Hex(3, -2);
        var neighbours = hex.Neighbors().ToList();

        Assert.Equal(6, neighbours.Count);
        Assert.Equal(6, neighbours.Distinct().Count());
        Assert.All(neighbours, n => Assert.Equal(1, hex.DistanceTo(n)));
    }

    [Fact]
    public void SteppingBackWithTheOppositeDirectionReturnsHome()
    {
        var hex = new Hex(-4, 1);
        foreach (var direction in HexDirectionExtensions.All)
            Assert.Equal(hex, hex.Neighbor(direction).Neighbor(direction.Opposite()));
    }

    [Fact]
    public void DirectionToRecoversTheStepTaken()
    {
        var hex = new Hex(1, 1);
        foreach (var direction in HexDirectionExtensions.All)
            Assert.Equal(direction, hex.DirectionTo(hex.Neighbor(direction)));

        Assert.Null(hex.DirectionTo(hex));
        Assert.Null(hex.DirectionTo(new Hex(5, 5)));
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(5)]
    public void RingHasSixTimesRadiusHexesAllAtThatDistance(int radius)
    {
        var center = new Hex(2, 2);
        var ring = center.Ring(radius).ToList();

        Assert.Equal(6 * radius, ring.Count);
        Assert.Equal(6 * radius, ring.Distinct().Count());
        Assert.All(ring, h => Assert.Equal(radius, center.DistanceTo(h)));
    }

    [Fact]
    public void RingStepsAreContiguous()
    {
        var ring = new Hex(0, 0).Ring(3).ToList();
        for (var i = 0; i < ring.Count; i++)
            Assert.Equal(1, ring[i].DistanceTo(ring[(i + 1) % ring.Count]));
    }

    [Theory]
    [InlineData(0, 1)]
    [InlineData(1, 7)]
    [InlineData(2, 19)]
    [InlineData(3, 37)]
    public void WithinRangeCountsTheCenteredHexNumber(int radius, int expected)
    {
        var hexes = Hex.Zero.WithinRange(radius).ToList();

        Assert.Equal(expected, hexes.Count);
        Assert.Equal(expected, hexes.Distinct().Count());
        Assert.All(hexes, h => Assert.True(Hex.Zero.DistanceTo(h) <= radius));
    }

    [Fact]
    public void LineRunsFromStartToEndOneStepAtATime()
    {
        var a = new Hex(-3, 1);
        var b = new Hex(2, -4);
        var line = a.LineTo(b);

        Assert.Equal(a.DistanceTo(b) + 1, line.Count);
        Assert.Equal(a, line[0]);
        Assert.Equal(b, line[^1]);

        for (var i = 0; i < line.Count - 1; i++)
            Assert.Equal(1, line[i].DistanceTo(line[i + 1]));
    }

    [Fact]
    public void LineToSelfIsJustSelf()
    {
        var hex = new Hex(4, 4);
        Assert.Equal([hex], hex.LineTo(hex));
    }

    [Fact]
    public void RotatingSixTimesReturnsTheSameDirection()
    {
        foreach (var direction in HexDirectionExtensions.All)
        {
            Assert.Equal(direction, direction.Rotate(6));
            Assert.Equal(direction, direction.Rotate(-6));
            Assert.Equal(direction.Opposite(), direction.Rotate(3));
        }
    }
}
