using System.Collections.Generic;
using System.Linq;
using Hexcom.Content;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>One soldier put on the map before the battle starts.</summary>
/// <param name="Name">What the readouts call them.</param>
/// <param name="Side">Ours or theirs.</param>
/// <param name="Where">The node they stand on — checked by <c>Battle.Deploy</c>, which throws if it is not standable.</param>
/// <param name="Stats">Their build, or null for the default soldier.</param>
/// <param name="Facing">Which way they are looking, which is most of what a stealth game turns on.</param>
/// <param name="Kit">Weapon, shield and plate.</param>
public sealed record SandboxDeployment(
    string Name,
    Side Side,
    NodeId Where,
    UnitStats? Stats,
    HexDirection Facing,
    Loadout Kit);

/// <summary>
/// A map and the people standing on it: what the sandbox opens with.
/// </summary>
/// <remarks>
/// <para>
/// The ground comes from <c>content/</c> now — <see cref="MapLibrary"/> reads the
/// <c>.hexmap</c> files embedded in <c>Hexcom.Content</c>, so the sandbox asks for a map by name
/// and does not care where the repository is on disk. Entry 024 in <c>docs/decisions.md</c> is
/// the format; entry 007 is why the waystation exists at all, which is that every range in the
/// game overshot the only map in the game by a factor of three.
/// </para>
/// <para>
/// The deployments do <b>not</b> come from content, because there is nowhere yet to put them:
/// entry 024 says plainly that who starts where and what winning means are the two things the
/// map format deliberately does not hold, and entry 029 makes the mission file Content's job
/// once Core has said what an objective is. Until then they are hard-coded, which
/// <c>docs/subprojects/view.md</c> has an open question about. Gathering them here rather than
/// leaving them inside <c>HexSandbox.NewBattle</c> does not answer that question; it just means
/// the answer, when it comes, is a deletion of one file rather than surgery on the node.
/// </para>
/// </remarks>
/// <param name="Name">What to type after <c>--scenario</c>.</param>
/// <param name="MapName">The <c>.hexmap</c> to load it on.</param>
/// <param name="Situation">One line for the readouts, so the picture says what it is a picture of.</param>
/// <param name="Deployments">Everybody, in no particular order — initiative decides who goes first.</param>
/// <param name="Exit">
/// Where our side may walk off the field, or empty for a fight with nothing to win.
/// </param>
public sealed record SandboxScenario(
    string Name,
    string MapName,
    string Situation,
    IReadOnlyList<SandboxDeployment> Deployments,
    IReadOnlyList<NodeId>? Exit = null)
{
    private static NodeId At(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    /// <summary>
    /// The fight over the waystation: a garrison holding a crossroads, approached from the west.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Drawn against the map rather than dropped onto it. Ours start about 20 hexes out on the
    /// west road, which at the 1.73 m pitch entry 007 fixed is 35 metres — far enough that the
    /// distances discriminate, which was the entire complaint entry 007 made about the compound.
    /// Measured on the opening frame, seed 7:
    /// </para>
    /// <list type="bullet">
    /// <item>the sentry outside the west gate is 25 to 27 m off, and one look at any of ours is
    /// worth 35 to 37 certainty against a <c>Searching</c> bar of 50 — so the first decision of
    /// the battle is whether to keep walking;</item>
    /// <item>the rifleman in the watchtower can see all three of ours and one look is worth
    /// <b>nought</b>, because 54 to 56 m is past <c>AwarenessModel.SightRangeMetres</c> of 45.
    /// Six metres closer and it wakes up. That gap is what the honest attention field in
    /// <see cref="BattleView"/> draws, and it is the first thing on this project that has ever
    /// made a picture of entry 006;</item>
    /// <item>the ridge is 1.5 m up and on our side of the stream, and the step onto it is a
    /// climb: -14,-4 is five hexes from Bekker and costs 50 AP of 50, the whole turn. The crest
    /// at -12,-6 is another turn again. From either the tower is 43 to 46 m and everything else
    /// is closer, which is the trade — a firing position that costs the approach;</item>
    /// <item>the bridge at -8,0 is the other way through. It is 5 m from the sentry, out of
    /// sight of both the roof and the barn, and the planking is the loudest ground on the map.</item>
    /// </list>
    /// <para>
    /// A turn is about ten hexes. On the opening frame Vance can reach 210 places, Bekker 159
    /// and Orsini 148 — measured, seed 7 — so the compound is two turns away at a walk and more
    /// than that if anybody is being careful about it.
    /// </para>
    /// <para>
    /// The shape of the thing: the spotter on the house roof is the <see cref="UnitStats.Signaller"/>,
    /// and <c>AwarenessTracker.CanReach</c> gives a radio the whole side. Whatever it works out,
    /// everyone knows — including the tower, which cannot see that far itself. Vance carries the
    /// power blade, the only weapon in the game that kills without telling anybody. So there is a
    /// quiet way to take this place and a loud one, and which it turns out to be is decided on the
    /// roof.
    /// </para>
    /// <para>
    /// Vance also has the highest initiative, so the sandbox opens on a soldier holding a blade
    /// and no capture of the opening frame can show a shot readout. That is the same trap the
    /// compound had and a <c>--pass</c> is still the way past it.
    /// </para>
    /// <para>
    /// <b>And there is now something to win.</b> The mission is the one written in the header of
    /// <c>waystation.hexmap</c>: go in, look at what is in the house, come out by the cottages,
    /// and do not be properly registered on the way. As rules that is
    /// <c>Withdrawal(Player, the three cottage tiles, Searching)</c> — entry 041 — and it is the
    /// difference between a sandbox and a game, because entry 038 measured twelve matches on this
    /// map and not one of them ended: a commander with nothing to want stands still once contact
    /// is lost.
    /// </para>
    /// <para>
    /// It is also a <b>fourth</b> copy of a fact entry 038 already counted three of, and that is
    /// deliberate and temporary. The map header holds the mission in prose, the harness in
    /// <c>content/</c> deploys it, and this file does both — so when the mission file lands
    /// (entry 036, row 5) this scenario is one of the things it deletes, and until then the
    /// header is the thing to change first and this the thing to change with it.
    /// </para>
    /// </remarks>
    public static readonly SandboxScenario Waystation = new(
        "waystation",
        "waystation",
        "three of ours on the west road, a garrison holding the crossroads",
        [
            new("Vance", Side.Player, At(-21, 3), UnitStats.Scout, HexDirection.SouthEast, Loadout.Infiltrator),
            new("Orsini", Side.Player, At(-20, 0), UnitStats.Trooper, HexDirection.NorthEast, Loadout.Heavy),
            new("Bekker", Side.Player, At(-19, -3), null, HexDirection.NorthEast, Loadout.Rifleman),

            // The sentry stands on the road outside the west gate and watches the way we are
            // coming. The spotter has the roof and the radio. The other two hold the east half
            // of the crossroads and can do nothing about us until somebody tells them.
            new("Sentry", Side.Hostile, At(-5, 0), null, HexDirection.SouthWest, Loadout.Beamer),
            new("Spotter", Side.Hostile, At(0, 1, 1), UnitStats.Signaller, HexDirection.NorthWest, Loadout.Beamer),
            new("Watchman", Side.Hostile, At(16, -14, 1), null, HexDirection.NorthWest, Loadout.Rifleman),
            new("Hollis", Side.Hostile, At(14, -6), null, HexDirection.SouthWest, Loadout.Beamer),
        ],

        // The cottages on the west bank: a named place and not a map edge, because whoever is
        // meeting you there has to be able to find it.
        [At(-14, 6), At(-14, 7), At(-13, 6)]);

    /// <summary>
    /// The old demo: two of ours outside the compound, three of theirs inside it, one on the roof.
    /// </summary>
    /// <remarks>
    /// Kept because every capture taken before the waystation existed was taken on it, and a
    /// drawing change is checked by diffing a picture against the commit before it — which needs
    /// the same scene to be reachable. It is also, since entry 047, the fixture that keeps a map
    /// with no mission legal: <c>compound.hexmap</c> has none and never will, and a format that
    /// made every such map look like one with something missing would have been the wrong format.
    /// <para>
    /// It is radius 6 — 21 m across, against a sight range of 45 and a rifle that reaches 55.
    /// Everything on it is inside everything else's everything, which is the complaint entry 007
    /// made and the reason it is no longer the scenario the sandbox opens with.
    /// </para>
    /// </remarks>
    public static readonly SandboxScenario Compound = new(
        "compound",
        "compound",
        "two of ours outside the wall, three of theirs holding it",
        [
            new("Vance", Side.Player, At(-4, 0), UnitStats.Scout, HexDirection.NorthEast, Loadout.Infiltrator),
            new("Orsini", Side.Player, At(-3, 2), UnitStats.Trooper, HexDirection.NorthEast, Loadout.Heavy),
            new("Sentry", Side.Hostile, At(4, 2), null, HexDirection.SouthWest, Loadout.Beamer),
            new("Watchman", Side.Hostile, At(4, -2), null, HexDirection.NorthWest, Loadout.Rifleman),
            new("Spotter", Side.Hostile, At(4, 0, 1), UnitStats.Signaller, HexDirection.SouthWest, Loadout.Beamer),
        ]);

    /// <summary>Everything the sandbox can open with. First is the default.</summary>
    public static readonly IReadOnlyList<SandboxScenario> All = [Waystation, Compound];

    /// <summary>By name, case-insensitively, falling back to the default rather than throwing.</summary>
    /// <remarks>
    /// A typo on the command line should get you a sandbox and a look at the name you meant,
    /// not a scene that fails to load. The name is printed in the readouts, so a wrong one is
    /// visible in the picture it spoiled.
    /// </remarks>
    public static SandboxScenario ByName(string? name)
        => All.FirstOrDefault(s => string.Equals(s.Name, name, System.StringComparison.OrdinalIgnoreCase))
           ?? All[0];

    /// <summary>The ground, read from <c>content/</c>.</summary>
    public BattleMap LoadMap() => MapLibrary.Load(MapName);

    /// <summary>
    /// Put everybody on a battle that has not started yet, and give it something to be about.
    /// </summary>
    /// <remarks>
    /// The objective goes on before <c>Start</c>, which is what entry 041 asks for. A scenario
    /// with no exit gets none, and a battle with no objective behaves exactly as it always did —
    /// which is why the compound is unchanged and every capture ever taken on it still means the
    /// same thing.
    /// <para>
    /// <c>Searching</c> rather than the <c>Suspicious</c> default, because the header says so in
    /// as many words: <em>Searching, not a dog barking</em>. It is a real difference — half the
    /// certainty ladder — and it is what makes the mission winnable by people who were noticed
    /// and not identified.
    /// </para>
    /// </remarks>
    public void DeployInto(Battle battle)
    {
        foreach (var d in Deployments)
            battle.Deploy(d.Name, d.Side, d.Where, d.Stats, d.Facing, d.Kit);

        if (Exit is { Count: > 0 } exit)
            battle.SetObjective(new Withdrawal(Side.Player, exit, AwarenessState.Searching));
    }
}
