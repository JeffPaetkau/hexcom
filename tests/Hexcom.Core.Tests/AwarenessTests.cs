using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// Detection is the system the game is about, so these read as approaches rather than as unit
/// tests: who walked where, how loudly, and what the other side made of it.
/// </summary>
public class AwarenessTests
{
    private static NodeId Node(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    private static Battle Field(BattleMap? map = null, int seed = 1)
        => new(map ?? new BattleMap().FillDisc(Hex.Zero, 14), new HexLayout(size: 1.0), seed: seed);

    /// <summary>Give one unit a turn, and only that unit, whoever the clock says is up.</summary>
    private static void TakeTurn(Battle battle, Unit unit)
    {
        for (var guard = 0; guard < 20; guard++)
        {
            if (battle.Active == unit) { battle.EndTurn(); return; }
            battle.EndTurn();
        }

        Assert.Fail($"{unit.Name} never came round");
    }

    /// <summary>Let one observer look, without anyone else acting in between.</summary>
    private static void Look(Battle battle, Unit observer) => battle.Awareness.Observe(observer, battle.Round);

    // ---- starting out ----------------------------------------------------------

    [Fact]
    public void NobodyKnowsAnythingBeforeTheFirstLook()
    {
        var battle = Field();
        var sneak = battle.Deploy("Sneak", Side.Player, Node(-2, 0));
        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(2, 0), facing: HexDirection.SouthWest);
        battle.Start();

        // Deployment alone tells nobody anything, which is what leaves room for an approach.
        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(sentry.Id, sneak.Id).State);
        Assert.True(battle.Awareness.IsUndetected(sneak.Id));
    }

    [Fact]
    public void StandingInTheOpenNearbyGetsYouFoundInACoupleOfLooks()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Player, Node(0, 0));
        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(3, 0), facing: HexDirection.SouthWest);
        battle.Start();

        Look(battle, sentry);
        Assert.True(battle.Awareness.Of(sentry.Id, target.Id).State >= AwarenessState.Searching);

        Look(battle, sentry);
        Assert.True(battle.Awareness.Of(sentry.Id, target.Id).State >= AwarenessState.Alerted);
    }

    [Fact]
    public void ProneBehindSandbagsAtDistanceIsAsGoodAsInvisible()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 14);
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Low);
        var battle = Field(map);

        var sneak = battle.Deploy("Sneak", Side.Player, Node(0, 0));
        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(8, 0), facing: HexDirection.SouthWest);
        battle.Start();

        TakeTurn(battle, sneak);
        while (battle.Active != sneak) battle.EndTurn();
        Assert.True(battle.ChangeStance(Stance.Prone));
        battle.EndTurn();

        for (var i = 0; i < 6; i++) Look(battle, sentry);

        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(sentry.Id, sneak.Id).State);
    }

    [Fact]
    public void CoverBuysYouTimeRatherThanSafety()
    {
        var open = Field();
        var exposed = open.Deploy("Exposed", Side.Player, Node(0, 0));
        var watcher = open.Deploy("Watcher", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        open.Start();
        Look(open, watcher);

        var walled = new BattleMap().FillDisc(Hex.Zero, 14);
        walled.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Low);
        var covered = Field(walled);
        var hiding = covered.Deploy("Hiding", Side.Player, Node(0, 0));
        var other = covered.Deploy("Watcher", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        covered.Start();
        Look(covered, other);

        Assert.True(
            covered.Awareness.Of(other.Id, hiding.Id).Detection
            < open.Awareness.Of(watcher.Id, exposed.Id).Detection);
    }

    // ---- losing them again -----------------------------------------------------

    [Fact]
    public void BreakingContactBleedsCertaintyAwayUntilTheyGiveUp()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 14);
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Solid);
        var battle = Field(map);

        var quarry = battle.Deploy("Quarry", Side.Player, Node(1, 0));
        var hunter = battle.Deploy("Hunter", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        battle.Start();

        // Seen out in the open first.
        Look(battle, hunter);
        Look(battle, hunter);
        var contact = battle.Awareness.Of(hunter.Id, quarry.Id);
        Assert.True(contact.State >= AwarenessState.Alerted);
        var lastSeen = contact.LastKnownPosition;

        // Then behind the building wall, out of sight.
        while (battle.Active != quarry) battle.EndTurn();
        Assert.True(battle.Move(Node(0, 0)).Moved);
        battle.EndTurn();

        for (var i = 0; i < 10; i++) Look(battle, hunter);

        Assert.Equal(AwarenessState.Unaware, contact.State);
        Assert.False(contact.EyesOn);

        // But the belief about where you were is kept, stale and wrong.
        Assert.Equal(lastSeen, contact.LastKnownPosition);
        Assert.NotEqual(quarry.Position, contact.LastKnownPosition);
    }

    [Fact]
    public void LosingSightDropsYouOffEngagedWithoutForgettingAnything()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 14);
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Solid);
        var battle = Field(map);

        var quarry = battle.Deploy("Quarry", Side.Player, Node(1, 0));
        var hunter = battle.Deploy("Hunter", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        battle.Start();

        for (var i = 0; i < 4; i++) Look(battle, hunter);
        var contact = battle.Awareness.Of(hunter.Id, quarry.Id);
        Assert.Equal(AwarenessState.Engaged, contact.State);

        while (battle.Active != quarry) battle.EndTurn();
        battle.Move(Node(0, 0));
        battle.EndTurn();
        Look(battle, hunter);

        // Still hunting, no longer shooting.
        Assert.Equal(AwarenessState.Alerted, contact.State);
    }

    // ---- noise -----------------------------------------------------------------

    [Fact]
    public void SprintingOverGravelIsHeardThroughAWall()
    {
        // A building wall between the two of them, so nothing can be seen either way.
        var map = new BattleMap().FillDisc(Hex.Zero, 14, ground: GroundType.Gravel);
        map.AddSideWall(new Hex(5, 0), HexDirection.NorthEast, 0, WallProfile.Solid);
        var battle = Field(map);

        var sneak = battle.Deploy("Sneak", Side.Player, Node(0, 0));
        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(8, 0), facing: HexDirection.SouthWest);
        battle.Start();

        Assert.False(battle.CanSee(sentry, sneak), "the wall was supposed to hide them");

        while (battle.Active != sneak) battle.EndTurn();
        Assert.True(battle.Move(Node(4, 0)).Moved); // four hexes of gravel at a run

        var contact = battle.Awareness.Of(sentry.Id, sneak.Id);
        Assert.True(contact.Detection > 0, "a noisy dash went unheard");
        Assert.Equal(sneak.Position, contact.LastKnownPosition);
    }

    [Fact]
    public void ASoundNeverMakesAnybodyCertain()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 14, ground: GroundType.Gravel);
        map.AddSideWall(new Hex(1, 0), HexDirection.NorthEast, 0, WallProfile.Solid);
        var battle = Field(map);

        var sneak = battle.Deploy("Sneak", Side.Player, Node(0, 0));
        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(2, 0), facing: HexDirection.SouthWest);
        battle.Start();

        // Bang about right next to them, repeatedly.
        for (var round = 0; round < 6; round++)
        {
            while (battle.Active != sneak) battle.EndTurn();
            battle.Move(battle.Active!.Position == Node(0, 0) ? Node(0, 1) : Node(0, 0));
            battle.EndTurn();
        }

        // They will come and look, but a noise alone can never tell them what they are dealing with.
        var contact = battle.Awareness.Of(sentry.Id, sneak.Id);
        Assert.True(contact.State <= AwarenessState.Searching, $"noise reached {contact.State}");
    }

    [Fact]
    public void CrawlingOverGrassIsMuchQuieterThanRunningOverGravel()
    {
        // Same four hex approach, ending the same short distance from the same listener.
        static double NoiseMade(GroundType ground, Stance stance)
        {
            var battle = Field(new BattleMap().FillDisc(Hex.Zero, 14, ground: ground));
            var sneak = battle.Deploy("Sneak", Side.Player, Node(-6, 0));
            var sentry = battle.Deploy("Sentry", Side.Hostile, Node(0, 0), facing: HexDirection.SouthWest);
            battle.Start();

            while (battle.Active != sneak) battle.EndTurn();
            if (stance != Stance.Standing) battle.ChangeStance(stance);
            battle.Move(Node(-2, 0));

            return battle.Awareness.Of(sentry.Id, sneak.Id).Detection;
        }

        var loud = NoiseMade(GroundType.Gravel, Stance.Standing);
        var quiet = NoiseMade(GroundType.Grass, Stance.Prone);

        Assert.True(loud > 0, "running over gravel two hexes away went unheard");
        Assert.Equal(0, quiet); // crawling over grass simply does not carry that far
        Assert.True(quiet < loud);
    }

    // ---- passing the word ------------------------------------------------------

    [Fact]
    public void AShoutOnlyCarriesAsFarAsAShout()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Player, Node(0, 0));
        var spotter = battle.Deploy("Spotter", Side.Hostile, Node(3, 0), facing: HexDirection.SouthWest);
        var nearby = battle.Deploy("Nearby", Side.Hostile, Node(3, 3), facing: HexDirection.SouthWest);
        var faraway = battle.Deploy("Faraway", Side.Hostile, Node(13, 0), facing: HexDirection.SouthWest);
        battle.Start();

        // Put a wall between the far one and everyone, so it cannot simply watch them react.
        Look(battle, spotter);
        Look(battle, spotter);
        Assert.True(battle.Awareness.Of(spotter.Id, target.Id).Detection >= battle.Awareness.Model.AlertedAt);

        Assert.True(battle.Awareness.Of(nearby.Id, target.Id).Detection > 0, "the shout did not carry next door");
        Assert.True(
            battle.Awareness.Of(nearby.Id, target.Id).Detection
            < battle.Awareness.Of(spotter.Id, target.Id).Detection,
            "second-hand word was worth as much as seeing it");
    }

    [Fact]
    public void ARadioReachesTheWholeSideAndKillingItCutsTheNet()
    {
        static double WordReaching(bool signallerAlive)
        {
            var map = new BattleMap().FillDisc(Hex.Zero, 30);
            var battle = new Battle(map, new HexLayout(size: 1.0), seed: 5);

            var target = battle.Deploy("Target", Side.Player, Node(0, 0));
            var signaller = battle.Deploy("Signaller", Side.Hostile, Node(3, 0), UnitStats.Signaller, facing: HexDirection.SouthWest);
            var distant = battle.Deploy("Distant", Side.Hostile, Node(26, 0), facing: HexDirection.SouthWest);
            battle.Start();

            if (!signallerAlive) battle.Withdraw(signaller);

            // Everybody looks. Only the signaller is close enough to see anything.
            foreach (var watcher in battle.InPlay.Where(u => u.Side == Side.Hostile).ToList())
            {
                battle.Awareness.Observe(watcher, battle.Round);
                battle.Awareness.Observe(watcher, battle.Round);
            }

            return battle.Awareness.Of(distant.Id, target.Id).Detection;
        }

        Assert.True(WordReaching(signallerAlive: true) > 0, "the radio did not reach across the map");
        Assert.Equal(0, WordReaching(signallerAlive: false));
    }

    [Fact]
    public void WatchingAComradeReactTellsYouSomething()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Player, Node(0, 0));
        var spotter = battle.Deploy("Spotter", Side.Hostile, Node(3, 0), facing: HexDirection.SouthWest);

        // Out of shouting range, no radio, but in plain view of the spotter.
        var distant = battle.Deploy("Distant", Side.Hostile, Node(14, 0), facing: HexDirection.SouthWest);
        battle.Start();

        Assert.True(
            battle.Sight.Ground(distant.Position).Plane is var _
            && Hexcom.Core.Geometry.Vec3.GroundDistance(
                battle.Sight.Ground(spotter.Position),
                battle.Sight.Ground(distant.Position)) > battle.Awareness.Model.VoiceRangeMetres,
            "the two were close enough to shout, so this proves nothing");

        Look(battle, spotter);
        Look(battle, spotter);

        Assert.True(battle.Awareness.Of(distant.Id, target.Id).Detection > 0);
    }

    // ---- what the player gets to see -------------------------------------------

    [Fact]
    public void ThePlayerReadsEnemyAwarenessCoarselyAndTheirOwnExposureExactly()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 14);
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Low);
        var battle = Field(map);

        var mine = battle.Deploy("Mine", Side.Player, Node(0, 0));
        var theirs = battle.Deploy("Theirs", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        battle.Start();
        Look(battle, theirs);

        // Coarse about them: a rung on a ladder and a stale marker, no number.
        var readout = battle.Awareness.ReadoutFor(theirs.Id, mine.Id);
        Assert.True(readout.State >= AwarenessState.Suspicious);
        Assert.Equal(mine.Position, readout.LastKnownPosition);
        Assert.True(readout.EyesOn);
        Assert.False(readout.IsStale);

        // Exact about my own soldier: a real fraction, because it is information about me.
        var exposure = battle.ExposureOf(mine);
        Assert.InRange(exposure, 0.3, 0.7); // half a body over waist-high sandbags
    }

    [Fact]
    public void AReadoutForSomebodyNobodyHasNoticedIsEmpty()
    {
        var battle = Field();
        var mine = battle.Deploy("Mine", Side.Player, Node(0, 0));
        var theirs = battle.Deploy("Theirs", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        battle.Start();

        var readout = battle.Awareness.ReadoutFor(theirs.Id, mine.Id);
        Assert.Equal(AwarenessState.Unaware, readout.State);
        Assert.Null(readout.LastKnownPosition);
    }

    [Fact]
    public void HighestAwarenessReportsTheWorstOfIt()
    {
        var battle = Field();
        var mine = battle.Deploy("Mine", Side.Player, Node(0, 0));
        var near = battle.Deploy("Near", Side.Hostile, Node(2, 0), facing: HexDirection.SouthWest);
        battle.Deploy("Far", Side.Hostile, Node(13, 0), facing: HexDirection.SouthWest);
        battle.Start();

        Assert.Equal(AwarenessState.Unaware, battle.HighestAwarenessOf(mine));

        Look(battle, near);
        Assert.True(battle.HighestAwarenessOf(mine) >= AwarenessState.Searching);
        Assert.False(battle.Awareness.IsUndetected(mine.Id));
    }

    [Fact]
    public void KillingSomebodyErasesWhatTheyKnewAndWhatWasKnownOfThem()
    {
        var battle = Field();
        var mine = battle.Deploy("Mine", Side.Player, Node(0, 0));
        var theirs = battle.Deploy("Theirs", Side.Hostile, Node(3, 0), facing: HexDirection.SouthWest);
        battle.Start();

        Look(battle, theirs);
        Assert.NotEmpty(battle.Awareness.ContactsFor(theirs.Id));

        battle.Withdraw(theirs);

        Assert.Empty(battle.Awareness.ContactsFor(theirs.Id));
        Assert.Empty(battle.Awareness.ContactsOn(theirs.Id));
        Assert.True(battle.Awareness.IsUndetected(mine.Id));
    }

    // ---- the window ------------------------------------------------------------

    [Fact]
    public void ASentryThatHasAlreadyActedThisRoundWillNotNoticeYouUntilItComesRound()
    {
        var battle = Field();
        var sneak = battle.Deploy("Sneak", Side.Player, Node(-6, 0), UnitStats.Scout);
        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(6, 0), UnitStats.Trooper, facing: HexDirection.SouthWest);
        battle.Start();

        // The scout out-rolls the trooper handily, so it moves before the sentry looks.
        Assert.Equal(sneak, battle.Active);

        battle.Move(Node(0, 0));
        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(sentry.Id, sneak.Id).State);

        // Only when the sentry gets its turn does the walk into the open cost anything.
        battle.EndTurn();
        Assert.Equal(sentry, battle.Active);
        battle.EndTurn();

        Assert.True(battle.Awareness.Of(sentry.Id, sneak.Id).State >= AwarenessState.Suspicious);
    }
}
