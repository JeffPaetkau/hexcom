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

        // Teague has the roof, which is a layer and not a coordinate.
        var teague = mission.Deployments.Single(d => d.Name == "Teague");
        Assert.Equal(new TileAddress(new Hex(0, 1), 1), teague.Where);
        Assert.Same(UnitStats.Signaller, teague.Stats);

        // Bekker names no role, which is the default soldier rather than an omission.
        Assert.Null(mission.Deployments.Single(d => d.Name == "Bekker").Stats);
    }

    [Fact]
    public void TheWaystationCarriesABriefingInAllSixParts()
    {
        var brief = MissionLibrary.Load("waystation").Brief;

        Assert.All(Briefing.Order, part => Assert.NotEmpty(brief.Part(part)));
        Assert.Contains("Instrument 4-11", brief.Instrument);
        Assert.Contains("what is stored in the house", brief.Task);
        Assert.Contains("will not fire", brief.Restraint);

        // The briefing names posts and the deployments name people, which is the split the
        // roster asked for: the Commission does not know the man at the gate is called Cobb.
        Assert.Contains("outside the west gate", brief.Presence);
        Assert.DoesNotContain("Cobb", brief.Presence);
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
    public void TheGroundTheBriefingTalksAboutIsNamedSoTheObjectiveCanPointAtIt()
    {
        var mission = MissionLibrary.Load("waystation");

        // The task is a look at the house, inside the compound, and out by the cottages. All
        // three are places, because an objective at a place cannot refer to a coordinate.
        Assert.Equal(["compound", "cottages", "house"], mission.Places.Keys.Order().ToList());
        Assert.Equal(61, mission.Places["compound"].Count);
        Assert.Equal(7, mission.Places["house"].Count);
    }

    [Fact]
    public void TheMissionCarriesItsOwnClockAndTheObjectiveReadsIt()
    {
        var mission = MissionLibrary.Load("waystation");
        Assert.Equal(30, mission.Rounds);

        // Entry 082 put the clock on the objective. The file's thirty rounds used to be applied by
        // whatever ran the battle; now it is the objective's own deadline, and the alarm half is
        // left unwritten because the waystation's grace is the playtest's to set.
        var objective = mission.Begin(seed: 1).ObjectiveOf(Side.Player)!;
        Assert.Equal(new Deadline(Round: 30), objective.Stop);
    }

    [Fact]
    public void TheSquadIsToldWhatItsBriefingSaysAboutThePostsAndNoMore()
    {
        var battle = MissionLibrary.Load("waystation").Begin(seed: 1);
        var held = (string ours, string theirs)
            => battle.Awareness.ReadoutFor(Unit(battle, ours).Id, Unit(battle, theirs).Id).State;

        // Three posts stated flat, and the barn after "the last two reports disagree".
        foreach (var soldier in new[] { "Vance", "Orsini", "Bekker" })
        {
            Assert.Equal(AwarenessState.Searching, held(soldier, "Cobb"));
            Assert.Equal(AwarenessState.Searching, held(soldier, "Teague"));
            Assert.Equal(AwarenessState.Searching, held(soldier, "Marek"));
            Assert.Equal(AwarenessState.Suspicious, held(soldier, "Hollis"));
        }

        // A briefing is one way: nobody told the garrison anything.
        Assert.Equal(AwarenessState.Unaware, held("Cobb", "Vance"));
    }

    [Fact]
    public void WhatASideIsToldIsAMarkerAtThePostTheSoldierIsActuallyStandingOn()
    {
        var battle = Parse(
            "deploy Cobb hostile -5,0 facing sw kit beamer",
            "told player alerted Cobb").Begin();

        var contact = battle.Awareness.ReadoutFor(Unit(battle, "Vance").Id, Unit(battle, "Cobb").Id);
        Assert.Equal(AwarenessState.Alerted, contact.State);
        Assert.Equal(new NodeId(new Hex(-5, 0), 0), contact.LastKnownPosition);
    }

    [Fact]
    public void ToldAboutSomebodyNotYetDeployedIsRefusedAtTheLine()
    {
        var error = Assert.Throws<MissionFormatException>(
            () => Parse("told player searching Cobb", "deploy Cobb hostile -5,0"));
        Assert.Contains("Nobody called Cobb has been deployed yet", error.Message);
    }

    [Fact]
    public void ASideCannotBeToldAboutItsOwnOrToldNothing()
    {
        var own = Assert.Throws<MissionFormatException>(() => Parse("deploy Bekker player -19,-3", "told player searching Bekker"));
        Assert.Contains("told about the other side", own.Message);

        var nothing = Assert.Throws<MissionFormatException>(() => Parse("deploy Cobb hostile -5,0", "told player unaware Cobb"));
        Assert.Contains("Leave the soldier off", nothing.Message);
    }

    [Fact]
    public void TheClockCanStopAMissionWhenTheAlarmGoesOut()
    {
        var both = Parse("rounds 20 after-alarm 2");
        Assert.Equal(new Deadline(Round: 20, AfterAlarm: 2), both.Stop);

        var alarmOnly = Parse("rounds after-alarm 0");
        Assert.Equal(new Deadline(AfterAlarm: 0), alarmOnly.Stop);
        Assert.Contains("rounds after-alarm 0", MissionWriter.Write(alarmOnly));

        var twice = Assert.Throws<MissionFormatException>(() => Parse("rounds 20", "rounds after-alarm 2"));
        Assert.Contains("one 'rounds' line", twice.Message);
    }

    private static Unit Unit(Battle battle, string name) => battle.Units.Single(u => u.Name == name);

    // ---- what a mission becomes ------------------------------------------------------

    [Fact]
    public void BeginningAMissionDeploysItAndGivesTheSideItsOrders()
    {
        var battle = MissionLibrary.Load("waystation").Begin(seed: 1);

        Assert.Equal(7, battle.Units.Count);
        Assert.Equal(1, battle.Round);

        var objective = Assert.IsType<Reconnaissance>(battle.ObjectiveOf(Side.Player));
        Assert.Equal(AwarenessState.Suspicious, objective.Unnoticed);
        Assert.True(objective.IsExit(new NodeId(new Hex(-14, 6), 0)));
        Assert.False(objective.IsExit(new NodeId(new Hex(0, 0), 0)));

        // Two places, and the one to be looked at is a point: the middle of the house, from
        // within the rule's own twelve metres, because the file says nothing about the distance.
        Assert.Equal(new NodeId(new Hex(0, 1), 0), objective.Place);
        Assert.Equal(12.0, objective.Within);
        Assert.False(objective.Done);

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
        Assert.Contains("objective reconnaissance player at house exit cottages unnoticed suspicious", lowered);
        Assert.DoesNotContain(" disc ", lowered);

        // The one silence lowering leaves alone. 'within' is the rules' default and not the
        // format's, so Content has no name to print for it and prints nothing rather than a
        // second copy of a number that lives in Reconnaissance.
        Assert.DoesNotContain(" within ", lowered);
    }

    [Fact]
    public void APlaceCanBeDrawnWithAnyShapeTheMapFormatKnows()
    {
        var mission = Parse("place yard disc 0,0 r 1", "objective withdrawal player exit yard");

        Assert.Equal(7, mission.Places["yard"].Count);
        Assert.Contains(new TileAddress(Hex.Zero, 0), mission.Places["yard"]);
    }

    // ---- two places and something in the middle --------------------------------------

    [Fact]
    public void AReconnaissanceAimsAtTheMiddleOfThePlaceRatherThanTheCornerItWasWrittenFrom()
    {
        // The same seven hexes listed in two orders. A place is ground and Reconnaissance wants a
        // point, so the reader has to choose one, and the choice cannot depend on the writing.
        var drawn = Parse(
            "place vault disc 0,1 r 1",
            "place gate hex -4,0",
            "objective reconnaissance player at vault exit gate");
        var listed = Parse(
            "place vault hexes 1,1 0,2 -1,2 -1,1 0,0 1,0 0,1",
            "place gate hex -4,0",
            "objective reconnaissance player at vault exit gate");

        var graph = MovementGraph.Build(MapLibrary.Load("waystation"));

        Assert.Equal(new NodeId(new Hex(0, 1), 0), drawn.NodeOf("vault", graph));
        Assert.Equal(drawn.NodeOf("vault", graph), listed.NodeOf("vault", graph));
    }

    [Fact]
    public void AReconnaissanceCanSayHowCloseTheLookHasToBeTakenFrom()
    {
        var mission = Parse(
            "place vault disc 0,1 r 1",
            "place gate hex -4,0",
            "objective reconnaissance player at vault exit gate within 4.5 unnoticed unaware");

        var order = Assert.IsType<ReconnaissanceOrder>(mission.Objectives.Single());
        Assert.Equal("vault", order.Place);
        Assert.Equal("gate", order.Exit);
        Assert.Equal(4.5, order.Within);
        Assert.Equal(AwarenessState.Unaware, order.Unnoticed);

        // And a distance written down is a distance written back out, unlike the default.
        Assert.Contains("within 4.5", MissionWriter.Write(mission));
    }

    [Fact]
    public void ASabotageIsTheSameTwoPlacesWithThePricedJob()
    {
        var mission = Parse(
            "place mast hex 0,1",
            "place gate hex -4,0",
            "objective sabotage player at mast exit gate effort 25");

        var order = Assert.IsType<SabotageOrder>(mission.Objectives.Single());
        Assert.Equal(25, order.Effort);

        var sabotage = Assert.IsType<Sabotage>(mission.Begin().ObjectiveOf(Side.Player));
        Assert.Equal(25, sabotage.Effort);
        Assert.Equal(25, sabotage.Owing);
    }

    [Fact]
    public void ASortieWithNothingToLookAtIsRefusedAndSaysWhatIsMissing()
    {
        var error = Assert.Throws<MissionFormatException>(
            () => Parse("place gate hex -4,0", "objective reconnaissance player exit gate"));
        Assert.Contains("something to look at", error.Message);
    }

    [Fact]
    public void EverySortieSpellsTheExitTheSameWay()
    {
        // One grammar, one word. The line entry 059 left commented in the waystation said
        // 'out cottages', and this is the test that there is no second spelling of it.
        var error = Assert.Throws<MissionFormatException>(
            () => Parse("place gate hex -4,0", "objective reconnaissance player at gate out gate"));
        Assert.Contains("Unknown reconnaissance option 'out'", error.Message);
        Assert.Contains("exit", error.Message);
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
        // Three of the six can be built now; the other three are still names the grammar knows
        // and the rules do not, which is a true and useful thing to be told.
        var error = Assert.Throws<MissionFormatException>(() => Parse("objective capture player"));
        Assert.Contains("one of the six mission shapes", error.Message);
        Assert.Contains("entries 041 and 061", error.Message);
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
