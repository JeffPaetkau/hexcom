using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;

namespace Hexcom.Content.Tests;

/// <summary>
/// A mission file holds the four things a map deliberately cannot, and it is the only copy of
/// them. These tests are that sentence, and the last of them is the one that matters: what the
/// file says is what a battle built from it does.
/// </summary>
public class MissionFileTests
{
    // ---- the waystation, which used to be written down three times -------------------

    [Fact]
    public void TheWaystationMissionPutsEverybodyWhereTheProseUsedTo()
    {
        var mission = MissionLibrary.Load("waystation");

        Assert.Equal("waystation", mission.MapName);
        Assert.Equal(7, mission.Deployments.Count);

        var vance = mission.Deployments.Single(d => d.Name == "Vance");
        Assert.Equal(Side.Player, vance.Side);
        Assert.Equal(new TileAddress(new Hex(-21, 3), 0), vance.Where);
        Assert.Equal(HexDirection.SouthEast, vance.Facing);
        Assert.Same(UnitStats.Scout, vance.Stats);
        Assert.Same(Loadout.Infiltrator, vance.Loadout);

        // The spotter is on the house roof, which is a layer and not a coordinate.
        var spotter = mission.Deployments.Single(d => d.Name == "Spotter");
        Assert.Equal(new TileAddress(new Hex(0, 1), 1), spotter.Where);
        Assert.Same(UnitStats.Signaller, spotter.Stats);

        // Bekker names no role, which is the default soldier rather than an omission.
        Assert.Null(mission.Deployments.Single(d => d.Name == "Bekker").Stats);
    }

    [Fact]
    public void TheWaystationCarriesABriefingInAllSixParts()
    {
        var brief = MissionLibrary.Load("waystation").Brief;

        Assert.All(Briefing.Order, part => Assert.NotEmpty(brief.Part(part)));
        Assert.Contains("Instrument 4-11", brief.Instrument);
        Assert.Contains("confirm what is stored", brief.Task);
        Assert.Contains("will not fire", brief.Restraint);
    }

    [Fact]
    public void TheWayOffIsAPlaceAnybodyCanStandInAndWalkTo()
    {
        var mission = MissionLibrary.Load("waystation");
        var map = mission.LoadMap();
        var graph = MovementGraph.Build(map);

        var exit = mission.NodesOf("cottages", graph);
        Assert.Equal(3, exit.Count);

        // And it is on our side of the stream, which is the whole reason it is not the road.
        var bekker = new NodeId(new Hex(-19, -3), 0);
        var reach = Pathfinder.Reachable(graph, bekker, int.MaxValue);
        Assert.All(exit, node => Assert.True(reach.CanReach(node), $"{node} cannot be walked to"));
    }

    [Fact]
    public void TheMissionCarriesItsOwnClock()
    {
        Assert.Equal(30, MissionLibrary.Load("waystation").Rounds);
    }

    // ---- what a mission becomes ------------------------------------------------------

    [Fact]
    public void BeginningAMissionDeploysItAndGivesTheSideItsOrders()
    {
        var battle = MissionLibrary.Load("waystation").Begin(seed: 1);

        Assert.Equal(7, battle.Units.Count);
        Assert.Equal(1, battle.Round);

        var objective = Assert.IsType<Withdrawal>(battle.ObjectiveOf(Side.Player));
        Assert.Equal(AwarenessState.Suspicious, objective.Unnoticed);
        Assert.True(objective.IsExit(new NodeId(new Hex(-14, 6), 0)));
        Assert.False(objective.IsExit(new NodeId(new Hex(0, 0), 0)));

        // The other side is holding the place, not withdrawing from it.
        Assert.Null(battle.ObjectiveOf(Side.Hostile));
    }

    [Theory]
    [MemberData(nameof(ShippedMissions))]
    public void EveryShippedMissionBuildsABattleThatStarts(string name)
    {
        var battle = MissionLibrary.Load(name).Begin(seed: 1);
        Assert.True(battle.IsRunning);
        Assert.NotEmpty(battle.Units);
    }

    public static TheoryData<string> ShippedMissions()
    {
        var data = new TheoryData<string>();
        foreach (var name in MissionLibrary.Names) data.Add(name);
        return data;
    }

    // ---- the shorthand adds nothing --------------------------------------------------

    [Fact]
    public void LoweringAMissionToPrimitivesLosesNothing()
    {
        var original = MissionLibrary.Load("waystation");
        var lowered = MissionWriter.Write(original);
        var reread = MissionFile.Parse(lowered, "lowered");

        // Writing what was read gives the same text back, so nothing was left in the shorthand.
        Assert.Equal(lowered, MissionWriter.Write(reread));

        // And it really is lowered: no shapes, and every default spelled out.
        Assert.Contains("place cottages hexes -14,6 -14,7 -13,6", lowered);
        Assert.Contains("objective withdrawal player exit cottages unnoticed suspicious", lowered);
        Assert.DoesNotContain(" disc ", lowered);
    }

    [Fact]
    public void APlaceCanBeDrawnWithAnyShapeTheMapFormatKnows()
    {
        var mission = Parse("place yard disc 0,0 r 1", "objective withdrawal player exit yard");

        Assert.Equal(7, mission.Places["yard"].Count);
        Assert.Contains(new TileAddress(Hex.Zero, 0), mission.Places["yard"]);
    }

    [Fact]
    public void APlaceCanBeUpstairs()
    {
        var mission = Parse("place roof hex 0,1 layer 1");
        Assert.Equal(new TileAddress(new Hex(0, 1), 1), mission.Places["roof"].Single());
    }

    // ---- what it refuses -------------------------------------------------------------

    [Fact]
    public void AMissionWithoutAMapIsRefused()
    {
        var error = Assert.Throws<MissionFormatException>(() => MissionFile.Parse("mission Nowhere", "test.hexmission"));
        Assert.Contains("which map", error.Message);
    }

    [Fact]
    public void AHalfWrittenBriefingIsRefusedAndSaysWhichHalf()
    {
        var text = "map waystation\ndeploy Vance player 0,0\nbrief task Walk in and walk out.\n";
        var error = Assert.Throws<MissionFormatException>(() => MissionFile.Parse(text, "test.hexmission"));
        Assert.Contains("'instrument'", error.Message);
        Assert.Contains("all six parts", error.Message);
    }

    [Fact]
    public void KitTheRulesDoNotHaveIsRefusedAtTheLineWithTheListOfWhatThereIs()
    {
        var error = Assert.Throws<MissionFormatException>(() => Parse("deploy Nolan player 3,0 kit railgun"));
        Assert.Contains("Unknown kit 'railgun'", error.Message);
        Assert.Contains("infiltrator", error.Message);
    }

    [Fact]
    public void AMissionShapeTheRulesDoNotHaveYetIsRefusedByNameRatherThanAsAMisspelling()
    {
        var error = Assert.Throws<MissionFormatException>(() => Parse("objective sabotage player"));
        Assert.Contains("one of the six mission shapes", error.Message);
        Assert.Contains("entry 041", error.Message);
    }

    [Fact]
    public void AnExitNobodyDeclaredIsRefusedWhereItIsWrittenRatherThanWhenTheBattleStarts()
    {
        var error = Assert.Throws<MissionFormatException>(() => Parse("objective withdrawal player exit orchard"));
        Assert.Contains("orchard", error.Message);
    }

    [Fact]
    public void ASoldierDeployedWhereNobodyCanStandIsRefusedByLine()
    {
        // The stream, which is too deep to wade and therefore has no node to stand on. Caught
        // when the battle is built rather than when the file is read, because the file has not
        // met the map yet — but it still says which line the soldier was written on.
        var stream = MapLibrary.Load("waystation").Tiles.First(t => t.Ground.Id == "deep").Address.Hex;
        var mission = Parse($"deploy Nolan player {stream.Q},{stream.R}");

        var error = Assert.Throws<MissionFormatException>(() => mission.Begin());
        Assert.Contains("Nolan", error.Message);
        Assert.Equal(10, error.Line);
    }

    /// <summary>
    /// A minimal mission on the waystation, plus whatever the test is about. Six briefing lines
    /// are the price of the rule that a briefing is whole, and this is where it is paid.
    /// </summary>
    private static Mission Parse(params string[] statements)
    {
        var text = string.Join('\n',
            [
                "mission Test",
                "map waystation",
                "deploy Vance player -21,3 facing se role scout kit infiltrator",
                .. Briefing.Order.Select(p => $"brief {MissionFile.PartName(p)} Something about the {p}."),
                .. statements,
            ]);

        return MissionFile.Parse(text, "test.hexmission");
    }
}
