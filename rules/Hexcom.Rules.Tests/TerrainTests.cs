using Hexcom.Rules;

namespace Hexcom.Rules.Tests;

public class TerrainTests
{
    [Fact]
    public void The_same_seed_gives_the_same_ground()
    {
        var a = new Terrain(7);
        var b = new Terrain(7);

        for (var i = 0; i < 50; i++)
        {
            double x = i * 37.3 - 400, z = i * -23.9 + 300;
            Assert.Equal(a.Height(x, z), b.Height(x, z));
            Assert.Equal(a.SurfaceAt(x, z), b.SurfaceAt(x, z));
        }
    }

    [Fact]
    public void A_road_is_paved_on_its_centreline_and_a_field_is_open()
    {
        var terrain = new Terrain(7);

        // The highway and the north road both pass through this control point.
        Assert.Equal(Surface.Paved, terrain.SurfaceAt(0, -40));

        // Halfway along the quarry track's first span, on its centreline.
        Assert.Equal(Surface.Track, terrain.SurfaceAt(362.5, 140.6));

        Assert.Equal(Surface.Open, terrain.SurfaceAt(500, -500));
    }

    [Fact]
    public void The_bluff_is_walked_up_at_its_gentle_end_and_refused_at_its_cliff()
    {
        var terrain = new Terrain(7);
        var movement = new Movement(terrain);

        Assert.True(terrain.Height(128, 49) - terrain.Height(128, 28) > 2.5, "the table should stand about three metres up");
        Assert.NotNull(ClimbSouth(movement, 128));
        Assert.Null(ClimbSouth(movement, 172));

        // Nor can the cliff be reached by sidling along its face from the gentle end: no hex
        // on the steep half of the face is in reach from anywhere.
        var reach = movement.Reachable(Hex.At(148, 20), Unit.MaxAp);
        Assert.All(reach.Hexes, hex => Assert.True(movement.CanStand(hex), $"{hex} is on ground of grade {movement.GradeAt(hex):F2}"));
    }

    /// <summary>The cost of walking due south across the bluff's face at an x, or null if a step is refused.</summary>
    private static int? ClimbSouth(Movement movement, double x)
    {
        var hex = Hex.At(x, 26);
        var total = 0;
        while (hex.Centre.Z < 50)
        {
            var next = hex.Neighbour(1);
            if (movement.StepCost(hex, next) is not { } step) return null;
            total += step;
            hex = next;
        }

        return total;
    }

    [Fact]
    public void A_road_lies_on_its_own_profile()
    {
        var terrain = new Terrain(7);
        var highway = terrain.Roads[0];

        for (var i = 50; i < highway.Points.Count; i += 97)
        {
            var (x, z) = highway.Points[i];
            Assert.Equal(highway.Profile[i], terrain.Height(x, z), 2);
        }
    }
}
