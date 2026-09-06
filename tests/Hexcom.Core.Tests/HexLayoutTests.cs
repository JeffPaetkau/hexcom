using System.Linq;
using Hexcom.Core.Geometry;
using Hexcom.Core.Hexes;
using Xunit;

namespace Hexcom.Core.Tests;

public class HexLayoutTests
{
    [Fact]
    public void WorldPositionRoundTripsBackToTheSameHex()
    {
        var layout = new HexLayout(size: 1.5, origin: new Vec2(10, -4));

        foreach (var hex in Hex.Zero.WithinRange(6))
            Assert.Equal(hex, layout.HexAt(layout.Center(hex)));
    }

    [Fact]
    public void PointsNearAHexCentreResolveToThatHex()
    {
        var layout = new HexLayout(size: 1.0);
        var hex = new Hex(2, -1);
        var center = layout.Center(hex);

        // Anywhere within the inradius is unambiguously inside the hex.
        var inradius = layout.Height / 2;
        for (var i = 0; i < 12; i++)
        {
            var angle = Math.PI / 6 * i;
            var probe = center + new Vec2(Math.Cos(angle), Math.Sin(angle)) * (inradius * 0.9);
            Assert.Equal(hex, layout.HexAt(probe));
        }
    }

    [Fact]
    public void NeighbouringCentresAreOnePitchApart()
    {
        var layout = new HexLayout(size: 1.25);
        var hex = new Hex(1, 1);

        foreach (var neighbour in hex.Neighbors())
            Assert.Equal(layout.Pitch, Vec2.Distance(layout.Center(hex), layout.Center(neighbour)), 9);
    }

    [Fact]
    public void FlatTopHexIsWiderThanItIsTall()
    {
        var layout = new HexLayout(size: 1.0);
        Assert.Equal(2.0, layout.Width, 9);
        Assert.Equal(Math.Sqrt(3), layout.Height, 9);
        Assert.True(layout.Width > layout.Height);
    }

    [Fact]
    public void SideMidpointSitsBetweenTheHexAndItsNeighbour()
    {
        var layout = new HexLayout(size: 1.0);
        var hex = new Hex(0, 0);

        foreach (var direction in HexDirectionExtensions.All)
        {
            var expected = (layout.Center(hex) + layout.Center(hex.Neighbor(direction))) * 0.5;
            Assert.True(Vec2.Distance(expected, layout.SideMidpoint(hex, direction)) < 1e-9);
        }
    }

    [Fact]
    public void RotatingThirtyDegreesRendersPointyTopWithoutChangingTheLogic()
    {
        var flat = new HexLayout(size: 1.0);
        var pointy = new HexLayout(size: 1.0, rotationRadians: Math.PI / 6);
        var hex = new Hex(2, -1);

        // The grid is the same shape, just turned: distances are preserved...
        foreach (var neighbour in hex.Neighbors())
            Assert.Equal(
                Vec2.Distance(flat.Center(hex), flat.Center(neighbour)),
                Vec2.Distance(pointy.Center(hex), pointy.Center(neighbour)),
                9);

        // ...and the hexes now point up rather than sideways.
        var top = pointy.Corners(hex).OrderByDescending(c => c.Y).First();
        var center = pointy.Center(hex);
        Assert.Equal(0.0, top.X - center.X, 9);

        // Round tripping still works in the rotated frame.
        Assert.Equal(hex, pointy.HexAt(pointy.Center(hex)));
    }

    [Fact]
    public void SizeMustBePositive()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new HexLayout(0));
        Assert.Throws<ArgumentOutOfRangeException>(() => new HexLayout(-1));
    }
}
