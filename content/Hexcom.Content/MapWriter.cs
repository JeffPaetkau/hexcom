using System.Globalization;
using System.Linq;
using System.Text;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;

namespace Hexcom.Content;

/// <summary>
/// Writes a <see cref="BattleMap"/> out as <c>.hexmap</c> text using primitives only: one
/// <c>tile</c> per tile, one <c>chord</c> per wall, one <c>link</c> per authored link.
/// </summary>
/// <remarks>
/// This is the honest half of the format made concrete. A map lowered this way reads back to
/// the same tiles, walls and links, whichever shorthand it was originally written with, and the
/// round trip is what the tests use to show that the shorthand adds nothing the primitives
/// cannot say. It is also how a map built in code — by an editor, one day — gets onto disk in
/// the first place. The output is sorted, so two maps that differ diff sensibly.
/// </remarks>
public static class MapWriter
{
    public static string Write(BattleMap map, string? name = null)
    {
        var sb = new StringBuilder();
        sb.AppendLine("# Lowered to primitives by MapWriter. Every line here is a tile, a chord or a link.");
        if (name is not null) sb.Append("map ").AppendLine(name);
        if (map.OccupancyThreshold != HexPartition.DefaultOccupancyThreshold)
            sb.Append("occupancy ").AppendLine(Number(map.OccupancyThreshold));
        if (map.LayerHeight != 3.0)
            sb.Append("layer-height ").AppendLine(Number(map.LayerHeight));

        WriteDeclarations(map, sb);
        WriteTiles(map, sb);
        WriteWalls(map, sb);
        WriteLinks(map, sb);

        return sb.ToString();
    }

    private static void WriteDeclarations(BattleMap map, StringBuilder sb)
    {
        var profiles = map.Walls.Select(w => w.Profile).Distinct()
            .Where(p => !IsBuiltIn(p))
            .OrderBy(p => p.Id, StringComparer.Ordinal);

        foreach (var p in profiles)
        {
            sb.Append("profile ").Append(p.Id)
              .Append(" height ").Append(Number(p.HeightMetres))
              .Append(" cover ").Append(p.Cover.ToString().ToLowerInvariant())
              .Append(p.BlocksMovement ? " blocks" : " passable")
              .Append(p.Opaque ? " opaque" : " clear")
              .Append(p.Vaultable ? " vault" : " novault")
              .Append(p.Climbable ? " climb" : " noclimb")
              .AppendLine(p.Destructible ? " destructible" : " permanent");
        }

        var grounds = map.Tiles.Select(t => t.Ground).Distinct()
            .Where(g => !IsBuiltIn(g))
            .OrderBy(g => g.Id, StringComparer.Ordinal);

        foreach (var g in grounds)
        {
            sb.Append("ground ").Append(g.Id)
              .Append(" cost ").Append(g.ExtraApCost.ToString(CultureInfo.InvariantCulture))
              .Append(" noise ").Append(Number(g.NoiseFactor))
              .AppendLine(g.Passable ? "" : " impassable");
        }
    }

    private static void WriteTiles(BattleMap map, StringBuilder sb)
    {
        foreach (var tile in map.Tiles.OrderBy(t => t.Address.Layer).ThenBy(t => t.Address.Hex.Q).ThenBy(t => t.Address.Hex.R))
        {
            sb.Append("tile ").Append(Address(tile.Address))
              .Append(" h ").Append(Number(tile.FloorHeight))
              .Append(' ').AppendLine(tile.Ground.Id);
        }
    }

    private static void WriteWalls(BattleMap map, StringBuilder sb)
    {
        var chords = map.Walls.Select(wall =>
        {
            // A side belongs to two hexes; name it through the lower one so the output is stable.
            var host = wall.A.SharedHexesWith(wall.B).OrderBy(h => h.Q).ThenBy(h => h.R).First();
            var a = host.CornerIndexOf(wall.A);
            var b = host.CornerIndexOf(wall.B);
            return (Address: new TileAddress(host, wall.Layer), A: Math.Min(a, b), B: Math.Max(a, b), wall.Profile);
        });

        foreach (var c in chords.OrderBy(c => c.Address.Layer).ThenBy(c => c.Address.Hex.Q).ThenBy(c => c.Address.Hex.R).ThenBy(c => c.A).ThenBy(c => c.B))
        {
            sb.Append("chord ").Append(c.Profile.Id)
              .Append(' ').Append(Address(c.Address))
              .Append(' ').Append(c.A).Append('-').Append(c.B)
              .AppendLine();
        }
    }

    private static void WriteLinks(BattleMap map, StringBuilder sb)
    {
        foreach (var link in map.Links)
        {
            sb.Append("link ").Append(link.Kind.ToString().ToLowerInvariant())
              .Append(' ').Append(Address(link.From))
              .Append(' ').Append(Address(link.To));
            if (link.ApCost is { } cost) sb.Append(" cost ").Append(cost.ToString(CultureInfo.InvariantCulture));
            if (!link.Bidirectional) sb.Append(" one-way");
            if (link.FromRegion != 0 || link.ToRegion != 0)
                sb.Append(" regions ").Append(link.FromRegion).Append(' ').Append(link.ToRegion);
            sb.AppendLine();
        }
    }

    private static bool IsBuiltIn(WallProfile profile)
    {
        if (!MapFile.BuiltInProfiles.TryGetValue(profile.Id, out var builtIn)) return false;
        if (builtIn == profile) return true;
        throw new InvalidOperationException(
            $"Wall profile '{profile.Id}' has the name of a built-in profile but different values, so a map file cannot express it.");
    }

    private static bool IsBuiltIn(GroundType ground)
    {
        if (!MapFile.BuiltInGrounds.TryGetValue(ground.Id, out var builtIn)) return false;
        if (builtIn == ground) return true;
        throw new InvalidOperationException(
            $"Ground '{ground.Id}' has the name of a built-in ground but different values, so a map file cannot express it.");
    }

    private static string Address(TileAddress address)
        => $"{address.Hex.Q},{address.Hex.R}@{address.Layer}";

    private static string Number(double value) => value.ToString("R", CultureInfo.InvariantCulture);
}
