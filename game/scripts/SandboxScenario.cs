using System.Collections.Generic;
using System.Linq;
using Hexcom.Content;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>One soldier put on a bare map before the battle starts.</summary>
/// <remarks>
/// Only the fixture below uses this. A mission carries its own <c>Deployment</c>, with the role
/// and the kit named rather than referenced, which is the shape content settled on.
/// </remarks>
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
/// What the sandbox opens with: a mission from <c>content/</c>, or a bare map with people put on
/// it here.
/// </summary>
/// <remarks>
/// <para>
/// <b>This file used to hold the waystation and it does not any more.</b> Entry 038 counted three
/// copies of that mission drifting apart — a prose header on the map, a harness in
/// <c>content/</c>, and this — and entry 049 knowingly made a fourth by adding the objective
/// here. Entry 047 collapsed the other three into
/// <c>content/missions/waystation.hexmission</c> and this is the last of them going. What is left
/// is a name: <c>MissionLibrary.Load</c> reads the file, <c>Mission.Begin</c> hands back a battle
/// deployed, objectives set and started, and nothing in <c>game/</c> knows where anybody stands.
/// </para>
/// <para>
/// The drift was not hypothetical. The copy this replaces let a soldier leave at
/// <c>Searching</c>; the file says <c>unnoticed suspicious</c>, one rung lower, and the file is
/// the one the harness fights from. Two of the four things that decide whether the mission is
/// won disagreed, and nothing but a person reading both files could have noticed.
/// </para>
/// <para>
/// <b>The fixture stays</b>, and not out of sentiment. Every capture taken before the waystation
/// existed was taken on the compound, a drawing change is checked by diffing a picture against
/// the commit before it, and that needs the same scene to still be reachable. Entry 047 makes it
/// the other thing as well: a map with no mission has to stay legal, and the compound is the map
/// that proves it.
/// </para>
/// </remarks>
/// <param name="Name">What to type after <c>--scenario</c>.</param>
/// <param name="Situation">One line for the readouts, so the picture says what it is a picture of.</param>
/// <param name="MissionName">The <c>.hexmission</c> to fight, or null for a bare map.</param>
/// <param name="MapName">The <c>.hexmap</c>, for a bare map. Ignored when there is a mission.</param>
/// <param name="Deployments">Who stands where on a bare map. Ignored when there is a mission.</param>
public sealed record SandboxScenario(
    string Name,
    string Situation,
    string? MissionName = null,
    string? MapName = null,
    IReadOnlyList<SandboxDeployment>? Deployments = null)
{
    private static NodeId At(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    /// <summary>
    /// The fight over the waystation, read from <c>content/missions/waystation.hexmission</c>.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Everything that used to be written out here is in that file, including the four things a
    /// map deliberately cannot hold: who starts where with what facing, the named ground to leave
    /// by, the objective, and when it stops. What survives here is the name and a line for the
    /// status bar.
    /// </para>
    /// <para>
    /// What the ground is like, measured on the opening frame at seed 7, is still worth having in
    /// front of whoever is changing the drawing:
    /// </para>
    /// <list type="bullet">
    /// <item>the sentry outside the west gate is 25 to 27 m off, and one look at any of ours is
    /// worth 35 to 37 certainty against a <c>Searching</c> bar of 50 — so the first decision of
    /// the battle is whether to keep walking;</item>
    /// <item>the rifleman in the watchtower can see all three of ours and one look is worth
    /// <b>nought</b>, because 54 to 56 m is past <c>AwarenessModel.SightRangeMetres</c> of 45.
    /// Six metres closer and it wakes up, and that gap is what the attention field in
    /// <see cref="BattleView"/> draws;</item>
    /// <item>a turn is about ten hexes, the cottages are one turn from the start and the compound
    /// is two turns past them in the other direction — which is the measurement entry 048 is
    /// about, and the reason a squad told only to leave leaves immediately.</item>
    /// </list>
    /// </remarks>
    public static readonly SandboxScenario Waystation = new(
        "waystation",
        "a garrison holding the crossroads, approached from the west",
        MissionName: "waystation");

    /// <summary>
    /// The old demo: two of ours outside a walled compound, three of theirs holding it.
    /// </summary>
    /// <remarks>
    /// A fixture rather than a mission, deliberately, and the only place in <c>game/</c> where
    /// anybody is still deployed by hand. It is radius 6 — 21 m across, against a sight range of
    /// 45 and a rifle that reaches 55 — so everything on it is inside everything else's
    /// everything, which is the complaint entry 007 made and the reason it is not what the
    /// sandbox opens with. That is exactly what makes it a good fixture: small, fast, and
    /// unchanged since every capture anybody has diffed against was taken on it.
    /// </remarks>
    public static readonly SandboxScenario Compound = new(
        "compound",
        "two of ours outside the wall, three of theirs holding it",
        MapName: "compound",
        Deployments:
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

    /// <summary>The mission this is, or null for a bare map.</summary>
    public Mission? LoadMission() => MissionName is null ? null : MissionLibrary.Load(MissionName);

    /// <summary>
    /// Build the battle, deployed, objectives set and started.
    /// </summary>
    /// <remarks>
    /// The layout is handed in and is always the metres one. <c>Mission.Begin</c> takes it for
    /// exactly this reason — the sandbox owns two layouts and only one of them may reach
    /// <c>Battle</c>, which is frozen contract 5 and the single mistake this side of the project
    /// has actually made. See <see cref="SandboxScale"/>.
    /// </remarks>
    public Battle Open(Mission? mission, HexLayout metres, int seed)
    {
        if (mission is not null) return mission.Begin(seed, metres);

        var battle = new Battle(MapLibrary.Load(MapName!), metres, seed: seed);
        foreach (var d in Deployments!) battle.Deploy(d.Name, d.Side, d.Where, d.Stats, d.Facing, d.Kit);
        battle.Start();

        return battle;
    }
}
