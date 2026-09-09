using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Maps;

namespace Hexcom.Content.Tests;

/// <summary>
/// Says whether two maps hold the same tiles, walls and links, and if not, what differs. The
/// tests lean on this rather than on a map's own equality because <see cref="BattleMap"/> is an
/// entity with caches, and what matters here is only what was authored.
/// </summary>
internal static class MapEquality
{
    public static IReadOnlyList<string> Differences(BattleMap expected, BattleMap actual)
    {
        var diffs = new List<string>();

        var expectedTiles = expected.Tiles.ToDictionary(t => t.Address);
        var actualTiles = actual.Tiles.ToDictionary(t => t.Address);
        foreach (var (address, tile) in expectedTiles)
        {
            if (!actualTiles.TryGetValue(address, out var other)) diffs.Add($"missing tile {address}");
            else if (other != tile) diffs.Add($"tile {address}: expected {tile}, got {other}");
        }
        foreach (var address in actualTiles.Keys.Except(expectedTiles.Keys)) diffs.Add($"extra tile {address}");

        var expectedWalls = expected.Walls.ToDictionary(w => (w.A, w.B, w.Layer));
        var actualWalls = actual.Walls.ToDictionary(w => (w.A, w.B, w.Layer));
        foreach (var (key, wall) in expectedWalls)
        {
            if (!actualWalls.TryGetValue(key, out var other)) diffs.Add($"missing wall {wall}");
            else if (other.Profile != wall.Profile) diffs.Add($"wall {wall}: got profile {other.Profile.Id}");
        }
        foreach (var key in actualWalls.Keys.Except(expectedWalls.Keys)) diffs.Add($"extra wall {actualWalls[key]}");

        var expectedLinks = expected.Links.ToList();
        var actualLinks = actual.Links.ToList();
        foreach (var link in expectedLinks.Where(l => !actualLinks.Remove(l))) diffs.Add($"missing link {link}");
        foreach (var link in actualLinks) diffs.Add($"extra link {link}");

        if (expected.OccupancyThreshold != actual.OccupancyThreshold) diffs.Add("occupancy threshold differs");
        if (expected.LayerHeight != actual.LayerHeight) diffs.Add("layer height differs");

        return diffs;
    }

    public static void AssertSame(BattleMap expected, BattleMap actual)
    {
        var diffs = Differences(expected, actual);
        Assert.True(diffs.Count == 0, string.Join("\n", diffs.Take(20)));
    }
}
