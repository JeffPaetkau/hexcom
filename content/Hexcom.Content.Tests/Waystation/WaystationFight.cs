using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;

namespace Hexcom.Content.Tests.Waystation;

/// <summary>
/// The fight over the waystation, as the sandbox deploys it: three of ours on the west road, a
/// garrison of four holding the crossroads.
/// </summary>
/// <remarks>
/// The deployments are the sandbox's, copied rather than referenced, because <c>game/</c> is a
/// Godot assembly and a headless test cannot load it. The header of
/// <c>content/maps/waystation.hexmap</c> is the third copy and the one written for people. All
/// three have to agree, and until there is a scenario file for them to agree <i>in</i>, this
/// comment is the only thing that says so. Entry 024 in <c>docs/decisions.md</c> is why the map
/// format holds none of it; entry 036 is why the file waits on Core saying what an objective is.
/// </remarks>
public static class WaystationFight
{
    public const string MapName = "waystation";

    /// <summary>One hex is one metre of radius — entry 007.</summary>
    public static readonly HexLayout Layout = new(size: 1.0);

    public static Battle Start(int seed)
    {
        var battle = new Battle(MapLibrary.Load(MapName), Layout, seed: seed);
        Deploy(battle);
        battle.Start();
        return battle;
    }

    /// <summary>Everybody, where the sandbox puts them, before <c>Start</c>.</summary>
    public static void Deploy(Battle battle)
    {
        // Ours, on the west road about twenty hexes out, facing the crossroads.
        battle.Deploy("Vance", Side.Player, At(-21, 3), UnitStats.Scout, HexDirection.SouthEast, Loadout.Infiltrator);
        battle.Deploy("Orsini", Side.Player, At(-20, 0), UnitStats.Trooper, HexDirection.NorthEast, Loadout.Heavy);
        battle.Deploy("Bekker", Side.Player, At(-19, -3), null, HexDirection.NorthEast, Loadout.Rifleman);

        // Theirs. The sentry watches the road we are coming up; the spotter has the roof and the
        // radio; the tower and the barn hold the east half and hear about us from the roof.
        battle.Deploy("Sentry", Side.Hostile, At(-5, 0), null, HexDirection.SouthWest, Loadout.Beamer);
        battle.Deploy("Spotter", Side.Hostile, At(0, 1, 1), UnitStats.Signaller, HexDirection.NorthWest, Loadout.Beamer);
        battle.Deploy("Watchman", Side.Hostile, At(16, -14, 1), null, HexDirection.NorthWest, Loadout.Rifleman);
        battle.Deploy("Hollis", Side.Hostile, At(14, -6), null, HexDirection.SouthWest, Loadout.Beamer);
    }

    private static NodeId At(int q, int r, int layer = 0) => new(new Hex(q, r), layer);
}
