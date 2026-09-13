using System.Collections.Generic;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;

namespace Hexcom.Content.Tests.Kestrel;

/// <summary>
/// The fight over Kestrel Yard, read from <c>content/missions/kestrel.hexmission</c>.
/// </summary>
/// <remarks>
/// The waystation's harness, copied in shape: a name, the line that turns the file into a battle,
/// and the ground a route is read against that the mission does not name. Everything else — who,
/// where, what they are told, the objective and the clock — is the file's.
/// </remarks>
public static class KestrelFight
{
    public const string Name = "kestrel";

    public static Mission Mission { get; } = MissionLibrary.Load(Name);

    /// <summary>How long to fight before calling it, as the mission's own clock says.</summary>
    public static int Rounds => Mission.Rounds ?? 60;

    public static BattleMap LoadMap() => MapLibrary.Load(Mission.MapName);

    public static Battle Start(int seed) => Mission.Begin(seed);

    /// <summary>Hexes of a block, the same rectangle the map format draws.</summary>
    private static bool InBlock(Hex h, int qLow, int qHigh, int rowLow, int rowHigh)
        => h.Q >= qLow && h.Q <= qHigh && 2 * h.R + h.Q >= rowLow && 2 * h.R + h.Q <= rowHigh;

    /// <summary>The mission's four places, and the ground the routes are read against.</summary>
    public static IReadOnlyList<MatchRecorder.Landmark> Landmarks { get; } =
    [
        .. MatchRecorder.PlacesOf(Mission),
        new("the gate", n => n.Layer == 0 && (n.Hex == new Hex(0, -4) || n.Hex == new Hex(1, -4))),
        new("the main street", n => n.Layer == 0 && 2 * n.Hex.R + n.Hex.Q is >= -16 and <= -9 && n.Hex.Q is >= -8 and <= 11),
        new("the east lane", n => n.Layer == 0 && n.Hex.Q is >= 11 and <= 14),
        new("the lane by the wall", n => n.Layer == 0 && n.Hex.Q == 6),
        new("the towpath", n => n.Layer == 0 && n.Hex.Q == -9),
        new("the side-door alley", n => n.Layer == 0 && n.Hex.Q == -8 && 2 * n.Hex.R + n.Hex.Q is >= 4 and <= 19),
        new("the boiler house", n => n.Layer == 0 && InBlock(n.Hex, -5, -2, 21, 24)),
        new("the duct", n => n.Layer == 0 && n.Hex == new Hex(-5, 12)),
        new("the office downstairs", n => n.Layer == 0 && InBlock(n.Hex, 7, 11, -5, 9)),
        new("the office upstairs", n => n.Layer == 1 && InBlock(n.Hex, 7, 11, -5, 9)),
        new("the office roof", n => n.Layer == 2),
        new("the fire escape", n => n.Hex == new Hex(12, -4) && n.Layer == 1),
    ];
}
