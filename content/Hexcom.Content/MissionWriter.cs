using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using Hexcom.Core.Maps;

namespace Hexcom.Content;

/// <summary>
/// Writes a <see cref="Mission"/> back out as <c>.hexmission</c> text with nothing left implicit:
/// every place an explicit list of tiles, every facing, role, kit and threshold spelled out.
/// </summary>
/// <remarks>
/// The same instrument <see cref="MapWriter"/> is, for a much smaller claim. A mission has one
/// piece of shorthand — <c>place</c> takes the map format's shapes — and one set of defaults, and
/// this is what proves neither hides anything: a mission written this way reads back to the same
/// mission, and writing it again produces the same text. Where the map writer earns its keep on
/// eighteen hundred tiles, this earns it on the defaults, which are the part of any format that
/// quietly stops meaning what the reader thinks.
/// </remarks>
public static class MissionWriter
{
    public static string Write(Mission mission)
    {
        var sb = new StringBuilder();
        sb.AppendLine("# Lowered by MissionWriter. Nothing here is shorthand and nothing is left to a default.");

        if (mission.Name is not null) sb.Append("mission ").AppendLine(mission.Name);
        sb.Append("map ").AppendLine(mission.MapName);
        if (mission.Rounds is { } rounds) sb.Append("rounds ").AppendLine(rounds.ToString(CultureInfo.InvariantCulture));

        WriteBriefing(mission, sb);
        WritePlaces(mission, sb);
        WriteDeployments(mission, sb);
        WriteObjectives(mission, sb);

        return sb.ToString();
    }

    private static void WriteBriefing(Mission mission, StringBuilder sb)
    {
        sb.AppendLine();
        foreach (var part in Briefing.Order)
            sb.Append("brief ").Append(MissionFile.PartName(part)).Append(' ').AppendLine(mission.Brief.Part(part));
    }

    private static void WritePlaces(Mission mission, StringBuilder sb)
    {
        if (mission.Places.Count == 0) return;
        sb.AppendLine();

        foreach (var (name, tiles) in mission.Places.OrderBy(p => p.Key, StringComparer.Ordinal))
        {
            var layers = tiles.Select(t => t.Layer).Distinct().ToList();
            if (layers.Count > 1)
                throw new InvalidOperationException($"'{name}' spans layers {string.Join(" and ", layers)}, which no 'place' statement can say.");

            sb.Append("place ").Append(name).Append(" hexes");
            foreach (var tile in tiles) sb.Append(' ').Append(Coordinate(tile));
            if (layers[0] != 0) sb.Append(" layer ").Append(layers[0].ToString(CultureInfo.InvariantCulture));
            sb.AppendLine();
        }
    }

    private static void WriteDeployments(Mission mission, StringBuilder sb)
    {
        sb.AppendLine();
        foreach (var d in mission.Deployments)
        {
            sb.Append("deploy ").Append(d.Name)
                .Append(' ').Append(Lower(d.Side))
                .Append(' ').Append(Address(d.Where))
                .Append(" facing ").Append(MapFile.DirectionName(d.Facing));
            if (d.Role is not null) sb.Append(" role ").Append(d.Role);
            if (d.Kit is not null) sb.Append(" kit ").Append(d.Kit);
            sb.AppendLine();
        }
    }

    private static void WriteObjectives(Mission mission, StringBuilder sb)
    {
        if (mission.Objectives.Count == 0) return;
        sb.AppendLine();

        foreach (var order in mission.Objectives)
        {
            sb.Append("objective ").Append(Lower(order.Kind)).Append(' ').Append(Lower(order.Side));

            // The shape's own half first, then the half every sortie shares, so a written line
            // reads in the order the grammar in content/README.md gives it.
            var at = order switch
            {
                ReconnaissanceOrder r => r.Place,
                SabotageOrder s => s.Place,
                _ => null,
            };

            if (at is not null) sb.Append(" at ").Append(at);
            if (order is SortieOrder sortie) sb.Append(" exit ").Append(sortie.Exit);

            // The one thing lowering deliberately does not spell out. Everywhere else a silence in
            // the file is the format's default and gets written back as a value; these two are
            // the rules' defaults, they live on Reconnaissance and Sabotage as optional
            // parameters, and Content has no name to print for them. Printing a copy would be a
            // balance number in two places, which is the thing the format exists to prevent.
            switch (order)
            {
                case ReconnaissanceOrder { Within: { } within }:
                    sb.Append(" within ").Append(within.ToString("0.###", CultureInfo.InvariantCulture));
                    break;
                case SabotageOrder { Effort: { } effort }:
                    sb.Append(" effort ").Append(effort.ToString(CultureInfo.InvariantCulture));
                    break;
            }

            if (order is SortieOrder ending) sb.Append(" unnoticed ").Append(Lower(ending.Unnoticed));

            sb.AppendLine();
        }
    }

    private static string Lower<T>(T value) where T : struct, Enum
        => value.ToString()!.ToLowerInvariant();

    private static string Coordinate(TileAddress tile)
        => $"{tile.Hex.Q.ToString(CultureInfo.InvariantCulture)},{tile.Hex.R.ToString(CultureInfo.InvariantCulture)}";

    private static string Address(TileAddress tile)
        => tile.Layer == 0 ? Coordinate(tile) : $"{Coordinate(tile)}@{tile.Layer.ToString(CultureInfo.InvariantCulture)}";
}
