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
/// together — entry 038. The file is the one copy now, and this is what is left: a name, and the
/// one line that turns it into a battle.
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
}
