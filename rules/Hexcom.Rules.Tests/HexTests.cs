using Hexcom.Rules;

namespace Hexcom.Rules.Tests;

public class HexTests
{
    [Fact]
    public void The_hex_at_a_centre_is_that_hex()
    {
        for (var q = -8; q <= 8; q++)
        for (var r = -8; r <= 8; r++)
        {
            var hex = new Hex(q, r);
            var (x, z) = hex.Centre;
            Assert.Equal(hex, Hex.At(x, z));
        }
    }

    [Fact]
    public void Neighbours_are_one_apart_and_a_stride_between_centres()
    {
        var hex = new Hex(3, -5);
        for (var d = 0; d < 6; d++)
        {
            var n = hex.Neighbour(d);
            Assert.Equal(1, hex.DistanceTo(n));

            var (x0, z0) = hex.Centre;
            var (x1, z1) = n.Centre;
            var run = System.Math.Sqrt((x1 - x0) * (x1 - x0) + (z1 - z0) * (z1 - z0));
            Assert.Equal(Movement.Stride, run, 6);
        }
    }

    [Fact]
    public void The_edge_between_corners_faces_the_neighbour_in_that_direction()
    {
        var hex = new Hex(0, 0);
        for (var d = 0; d < 6; d++)
        {
            var (ax, az) = hex.Corner(d);
            var (bx, bz) = hex.Corner(d + 1);
            var (nx, nz) = hex.Neighbour(d).Centre;

            // The edge's midpoint lies halfway to the neighbour's centre.
            Assert.Equal(nx / 2, (ax + bx) / 2, 6);
            Assert.Equal(nz / 2, (az + bz) / 2, 6);
        }
    }
}
