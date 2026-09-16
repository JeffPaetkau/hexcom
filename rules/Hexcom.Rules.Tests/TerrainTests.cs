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
