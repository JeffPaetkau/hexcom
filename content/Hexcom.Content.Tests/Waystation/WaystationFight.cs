using System.Collections.Generic;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;

namespace Hexcom.Content.Tests.Waystation;

/// <summary>
/// The fight over the waystation, read from <c>content/missions/waystation.hexmission</c>.
/// </summary>
/// <remarks>
/// This class used to hold the deployments, copied out of the sandbox because <c>game/</c> is a
/// Godot assembly a headless test cannot load. That was the third of three copies of one set of
/// facts, and a comment asking whoever changed one to change the others was all that held them
/// together — entry 038. The file is the one copy now, and this is what is left: a name, the
/// one line that turns it into a battle, and the ground the mission does not name.
/// </remarks>
public static class WaystationFight
{
    public const string Name = "waystation";

    /// <summary>The mission, read once. Everything below comes off it.</summary>
    public static Mission Mission { get; } = MissionLibrary.Load(Name);

    /// <summary>The map it is fought on, by the name the mission gave.</summary>
    public static string MapName => Mission.MapName;

    /// <summary>One hex is one metre of radius — entry 007.</summary>
    public static HexLayout Layout => Hexcom.Content.Mission.Metres;

    /// <summary>How long to fight before calling it, as the mission's own clock says.</summary>
    public static int Rounds => Mission.Rounds ?? 60;

    /// <summary>The ground, freshly read. A <see cref="BattleMap"/> is mutable; matches do not share one.</summary>
    public static BattleMap LoadMap() => MapLibrary.Load(MapName);

    public static Battle Start(int seed) => Mission.Begin(seed);

    /// <summary>The mission's three places, and the ground a route is read against that it does not name.</summary>
    public static IReadOnlyList<MatchRecorder.Landmark> Landmarks(BattleMap map) =>
    [
        .. MatchRecorder.PlacesOf(Mission),
        new("the drain", n => n.Layer == 0 && (n.Hex == new Hex(-1, -3) || n.Hex == new Hex(-1, -4))),
        new("the bridge", n => n.Layer == 0 && n.Hex == new Hex(-8, 0)),
        new("the ridge", n => n.Layer == 0 && map.GetTile(n.Tile)?.FloorHeight > 1.0),
        new("the west wood", n => n.Layer == 0 && n.Hex.DistanceTo(new Hex(-6, -14)) <= 1),
        new("the east wood", n => n.Layer == 0 && n.Hex.DistanceTo(new Hex(14, 6)) <= 2),
        new("the house roof", n => n.Layer == 1 && n.Hex.DistanceTo(new Hex(0, 1)) <= 1),
        new("the barn", n => n.Layer == 0 && n.Hex.DistanceTo(new Hex(14, -6)) <= 2),
        new("the tower", n => n.Layer == 1 && n.Hex == new Hex(16, -14)),
        new("the ford", n => n.Layer == 0 && n.Hex == new Hex(-6, -4)),
        new("the pond", n => n.Layer == 0 && n.Hex.DistanceTo(new Hex(6, -16)) <= 2 && map.GetTile(n.Tile)?.Ground == GroundType.ShallowWater),
        new("the tree line", n => n.Layer == 0 && n.Hex.Q == -12 && n.Hex.R is >= -2 and <= 5),
    ];
}
