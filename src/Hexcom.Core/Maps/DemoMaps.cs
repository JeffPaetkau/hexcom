using Hexcom.Core.Hexes;

namespace Hexcom.Core.Maps;

/// <summary>
/// Hand-built maps for greyboxing and tests. Content, not rules.
/// </summary>
/// <remarks>
/// There is a real map format now, and this map lives in it as <c>content/maps/compound.hexmap</c>,
/// where <c>MapLibrary.Load("compound")</c> returns the same tiles, walls and links this method
/// builds. A test in <c>content/Hexcom.Content.Tests</c> holds the two identical. This copy stays
/// only because the core tests and the sandbox still call it; once they load the file instead
/// it goes — see <c>docs/decisions.md</c> entry 020. Until then, a change here is a change to
/// the file too, or that test will say so.
/// </remarks>
public static class DemoMaps
{
    /// <summary>
    /// A walled compound with a breach, sandbags, a smoke screen, broken ground, a barricade
    /// running across one tile, and a rooftop reachable only by ladder. Exercises every
    /// traversal kind the graph builder knows how to generate.
    /// </summary>
    public static BattleMap Compound()
    {
        var map = new BattleMap();
        map.FillDisc(Hex.Zero, radius: 6, layer: 0, floorHeight: 0);

        BuildCompoundWall(map);
        BuildSandbags(map);
        BuildBrokenGround(map);
        BuildBarricades(map);
        BuildRooftop(map);

        return map;
    }

    /// <summary>
    /// A north-south perimeter wall, one hex column wide. A "straight" wall on a hex grid is a
    /// zigzag: each hex contributes its north-west and south-west faces.
    /// </summary>
    private static void BuildCompoundWall(BattleMap map)
    {
        for (var r = -3; r <= 2; r++)
        {
            var hex = new Hex(2, r);
            map.AddSideWall(hex, HexDirection.NorthWest, 0, WallProfile.Solid);

            // Leave one face open: the breach everyone will funnel through.
            if (r != 0) map.AddSideWall(hex, HexDirection.SouthWest, 0, WallProfile.Solid);
        }
    }

    private static void BuildSandbags(BattleMap map)
    {
        map.AddSideWall(new Hex(-2, 2), HexDirection.SouthEast, 0, WallProfile.Low);
        map.AddSideWall(new Hex(-2, 2), HexDirection.South, 0, WallProfile.Low);
        map.AddSideWall(new Hex(-1, 1), HexDirection.South, 0, WallProfile.Low);

        // A hedge you cannot see through but can walk straight past.
        map.AddSideWall(new Hex(-1, -2), HexDirection.NorthEast, 0, WallProfile.Screen);
    }

    private static void BuildBrokenGround(BattleMap map)
    {
        foreach (var hex in new[] { new Hex(-4, 1), new Hex(-4, 2), new Hex(-3, 1) })
            map.SetTile(new TileAddress(hex, 0), 0, GroundType.Rubble);
    }

    private static void BuildBarricades(BattleMap map)
    {
        // Clips a corner off the tile: most of it is still standable.
        map.AddChord(new Hex(0, 3), 0, 2, 0, WallProfile.Low);

        // Splits the tile in half: crossable, but there is nowhere in it to stand.
        map.AddChord(new Hex(0, -3), 0, 3, 0, WallProfile.Low);
    }

    private static void BuildRooftop(BattleMap map)
    {
        const double roofHeight = 3.5;
        Hex[] roof = [new(4, -1), new(4, 0), new(4, 1), new(5, -1), new(5, 0)];

        foreach (var hex in roof)
            map.SetTile(new TileAddress(hex, 1), roofHeight);

        // Too high to jump down from, so the ladder is the only way up or off.
        map.AddLadder(new TileAddress(new Hex(4, 0), 0), new TileAddress(new Hex(4, 0), 1));

        // A parapet along the north edge: cover for whoever holds the roof.
        map.AddSideWall(new Hex(4, 1), HexDirection.North, 1, WallProfile.Railing);
        map.AddSideWall(new Hex(4, 1), HexDirection.NorthWest, 1, WallProfile.Railing);
    }
}
