using System.Collections.Generic;
using System.Linq;
using System.Text;
using Hexcom.Core.Maps;

namespace Hexcom.Content.Tests;

/// <summary>
/// A map drawn in characters, one storey at a time, so a session with no picture can read what it
/// drew before fighting on it.
/// </summary>
/// <remarks>
/// The waystation was checked this way and the helper was thrown away afterwards; the second map
/// needed it again, which is the argument for keeping it. It is a reading aid rather than a view —
/// the greybox is the view — and it prints nothing the rules would not: every tile's ground at its
/// centre, every wall at its midpoint by profile, and whoever a mission puts on the storey.
/// <para>
/// North is up. A hex centre is four characters from its neighbour across and four lines from the
/// one above it, which stretches the picture about one and a half times upwards and keeps every
/// side's midpoint on a whole character.
/// </para>
/// </remarks>
public static class MapSketch
{
    private const double MetresAcross = 0.375;
    private const double MetresUp = 0.433;

    public static string Draw(BattleMap map, int layer = 0, Mission? mission = null)
    {
        var layout = Mission.Metres;
        var cells = new Dictionary<(int Col, int Row), char>();

        void Put(Hexcom.Core.Geometry.Vec2 at, char c, bool over)
        {
            var key = ((int)Math.Round(at.X / MetresAcross), (int)Math.Round(-at.Y / MetresUp));
            if (over || !cells.ContainsKey(key)) cells[key] = c;
        }

        foreach (var tile in map.Tiles.Where(t => t.Address.Layer == layer))
            Put(layout.Center(tile.Address.Hex), GroundChar(tile), over: false);

        foreach (var wall in map.Walls.Where(w => w.Layer == layer))
            Put((layout.Position(wall.A) + layout.Position(wall.B)) * 0.5, WallChar(wall.Profile), over: true);

        foreach (var link in map.Links.Where(l => l.From.Layer == layer || l.To.Layer == layer))
        {
            var here = link.From.Layer == layer ? link.From : link.To;
            if (link.From.Layer != link.To.Layer) Put(layout.Center(here.Hex), '^', over: true);
        }

        foreach (var d in mission?.Deployments.Where(d => d.Where.Layer == layer) ?? [])
            Put(layout.Center(d.Where.Hex), d.Side == Hexcom.Core.Units.Side.Player ? char.ToLowerInvariant(d.Name[0]) : char.ToUpperInvariant(d.Name[0]), over: true);

        if (cells.Count == 0) return $"(nothing on layer {layer})";

        var (colLow, colHigh) = (cells.Keys.Min(k => k.Col), cells.Keys.Max(k => k.Col));
        var (rowLow, rowHigh) = (cells.Keys.Min(k => k.Row), cells.Keys.Max(k => k.Row));

        var sb = new StringBuilder();
        for (var row = rowLow; row <= rowHigh; row++)
        {
            var line = new StringBuilder();
            for (var col = colLow; col <= colHigh; col++)
                line.Append(cells.TryGetValue((col, row), out var c) ? c : ' ');
            sb.AppendLine(line.ToString().TrimEnd());
        }
        return sb.ToString();
    }

    private static char GroundChar(Tile tile) => tile.Ground.Id switch
    {
        "floor" => tile.FloorHeight > 0.4 && tile.Address.Layer == 0 ? 'o' : '.',
        "grass" => ',',
        "gravel" => ':',
        "rubble" => '%',
        "mud" => 'm',
        "shallow_water" => 'w',
        _ when !tile.Ground.Passable => '~',
        var id => id[0],
    };

    private static char WallChar(WallProfile profile) => profile.Id switch
    {
        "solid" => '#',
        "high" => 'H',
        "low" => '=',
        "railing" => '+',
        "screen" => '"',
        var id => char.ToUpperInvariant(id[0]),
    };
}
