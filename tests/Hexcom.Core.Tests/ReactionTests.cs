using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// Reacting out of turn, and the clock it happens on. These read as approaches watched and
/// answered: who was holding what arc, which way the runner went, and what the watchman could
/// still do about it by the time the round arrived.
/// </summary>
public class ReactionTests
{
    private static NodeId Node(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    /// <summary>Always goes first, so the arc is declared before anyone runs across it.</summary>
    private static readonly UnitStats Watchful = UnitStats.Default with { Initiative = 30 };

    /// <summary>Always goes last.</summary>
    private static readonly UnitStats Tardy = UnitStats.Default with { Initiative = 1 };

    private static Battle Field(BattleMap? map = null, int seed = 1, ReactionModel? reactions = null)
        => new(
            map ?? new BattleMap().FillDisc(Hex.Zero, 14),
            new HexLayout(size: 1.0),
            seed: seed,
            reactions: reactions);

    /// <summary>The route a unit would take, read as a timeline.</summary>
    private static CommittedMove Route(Battle battle, Unit unit, NodeId destination)
    {
        var reach = battle.Reachable(unit);
        Assert.True(reach.TryGetPath(destination, out var path), $"{destination} is out of {unit.Name}'s reach.");
        return new CommittedMove(unit.Position, path, unit.Facing, unit.Stance);
    }

    /// <summary>
    /// A watchman at the origin and a runner somewhere in front of it, with the watchman up
    /// first. Nothing has been declared yet.
    /// </summary>
    private static (Battle Battle, Unit Watchman, Unit Runner) Standoff(
        NodeId runnerStart,
        BattleMap? map = null,
        HexDirection facing = HexDirection.NorthEast,
        int seed = 1,
        ReactionModel? reactions = null,
        UnitStats? runnerStats = null,
        CostProfile? watchmanCosts = null)
    {
        var battle = Field(map, seed, reactions);
        var watchman = battle.Deploy(
            "Kessel", Side.Hostile, Node(0, 0),
            Watchful with { Costs = watchmanCosts ?? CostProfile.Default },
            facing);
        var runner = battle.Deploy(
            "Vance", Side.Player, runnerStart, (runnerStats ?? UnitStats.Default) with { Initiative = 1 },
            HexDirection.North);

        battle.Start();
        Assert.Same(watchman, battle.Active);

        return (battle, watchman, runner);
    }

    /// <summary>The same, with the arc declared and the turn handed to the runner.</summary>
    private static (Battle Battle, Unit Watchman, Unit Runner) Overwatched(
        OverwatchArc arc,
        NodeId runnerStart,
        BattleMap? map = null,
        HexDirection facing = HexDirection.NorthEast,
        int seed = 1,
        ReactionModel? reactions = null,
        UnitStats? runnerStats = null,
        CostProfile? watchmanCosts = null)
    {
        var field = Standoff(runnerStart, map, facing, seed, reactions, runnerStats, watchmanCosts);

        Assert.True(field.Battle.SetOverwatch(arc));
        field.Battle.EndTurn();
        Assert.Same(field.Runner, field.Battle.Active);

        return field;
    }

    /// <summary>
    /// Open ground with a knee-high wall on the far side of one hex, so a runner who reaches it
    /// is behind cover from the origin without having had to cross the wall to get there.
    /// </summary>
    private static BattleMap CoverAtTheEnd()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 14);
        map.AddSideWall(new Hex(4, 2), HexDirection.SouthWest, 0, WallProfile.Low);
        return map;
    }

    /// <summary>
    /// A four hex corridor with a knee-high wall across the middle of it. No way round, so the
    /// only route from one end to the other has a three point vault in the middle of it.
    /// </summary>
    private static (Battle Battle, Unit Walker) Barricaded()
    {
        var map = new BattleMap();
        for (var q = 0; q <= 3; q++) map.SetTile(new TileAddress(new Hex(q, 0), 0), floorHeight: 0);
        map.AddSideWall(new Hex(1, 0), HexDirection.NorthEast, 0, WallProfile.Low);

        var battle = Field(map);
        var walker = battle.Deploy("Vance", Side.Player, Node(0, 0));
        battle.Start();

        return (battle, walker);
    }

    // ---- the timeline ----------------------------------------------------------

    [Fact]
    public void AFourPointRunPutsTheMoverThreePointsAlongAtTickThree()
    {
        var (battle, _, runner) = Standoff(Node(4, -2));
        var move = Route(battle, runner, Node(4, 2));

        Assert.Equal(4, move.Duration);
        Assert.Equal(Node(4, -2), move.PositionAt(0));
        Assert.Equal(Node(4, -1), move.PositionAt(1));
        Assert.Equal(Node(4, 1), move.PositionAt(3));
        Assert.Equal(Node(4, 2), move.PositionAt(4));
    }

    [Fact]
    public void AnActionThatLandsAfterTheRunIsOverFindsThemStandingAtTheDestination()
    {
        var (battle, _, runner) = Standoff(Node(4, -2));
        var move = Route(battle, runner, Node(4, 2));

        // Seven points of aiming against a four point run: the shot goes off three ticks after
        // they have arrived, which is exactly the penalty for taking too long over it.
        Assert.Equal(move.Destination, move.PositionAt(7));
        Assert.Equal(move.Start, move.PositionAt(-3));
    }

    [Fact]
    public void VaultingAWallLeavesYouSittingOnTheNearSideOfItForTheWholePrice()
    {
        var (battle, walker) = Barricaded();
        var move = Route(battle, walker, Node(3, 0));

        // Walk one, vault three, walk one. The vault is a single link with a single arrival, so
        // for three ticks the runner is still standing at the foot of the wall.
        Assert.Equal(5, move.Duration);
        Assert.Equal(Node(1, 0), move.PositionAt(1));
        Assert.Equal(Node(1, 0), move.PositionAt(2));
        Assert.Equal(Node(1, 0), move.PositionAt(3));
        Assert.Equal(Node(2, 0), move.PositionAt(4));
        Assert.Equal(Node(3, 0), move.PositionAt(5));
    }

    [Fact]
    public void TheMoverIsFacingWhereverItWasHeadedAtEveryPointAlongTheRoute()
    {
        var (battle, _, runner) = Standoff(Node(4, -2), facing: HexDirection.South);
        var move = Route(battle, runner, Node(4, 2));

        Assert.Equal(HexDirection.North, move.FacingAt(1));
        Assert.Equal(HexDirection.North, move.FacingAt(move.Duration));
    }

    [Fact]
    public void OnlyTheTicksTheMoverArrivesSomewhereAreWorthConsidering()
    {
        var (battle, walker) = Barricaded();
        var move = Route(battle, walker, Node(3, 0));

        Assert.Equal([0, 1, 4, 5], move.ArrivalTicks.ToArray());
    }

    // ---- what banks ------------------------------------------------------------

    [Fact]
    public void AWholeTurnSpentStandingStillBanksAnAimedShot()
    {
        var (battle, watchman, _) = Standoff(Node(4, -2));
        battle.EndTurn();

        Assert.Equal(7, watchman.Reserve);
        Assert.Equal(FireMode.Aimed.ApCost, watchman.Reserve);
        Assert.True(watchman.CanReact);
    }

    [Fact]
    public void HalfATurnOfMovementStillBanksASnapShot()
    {
        var (battle, watchman, _) = Standoff(Node(4, -2));
        battle.Move(Node(5, 0));
        Assert.Equal(5, watchman.ActionPoints);

        battle.EndTurn();

        Assert.Equal(3, watchman.Reserve);
        Assert.Equal(FireMode.Snap.ApCost, watchman.Reserve);
    }

    [Fact]
    public void SprintingTheWholeTurnLeavesNothingToAnswerWith()
    {
        var (battle, watchman, _) = Standoff(Node(4, -2));
        battle.Move(Node(0, 10));
        Assert.Equal(0, watchman.ActionPoints);

        battle.EndTurn();

        Assert.Equal(0, watchman.Reserve);
        Assert.False(watchman.CanReact);
    }

    [Fact]
    public void ScrapsOfATurnAreRoundedAwayRatherThanBanked()
    {
        var (battle, watchman, _) = Standoff(Node(4, -2));
        battle.Move(Node(0, 8));
        Assert.Equal(2, watchman.ActionPoints);

        battle.EndTurn();

        Assert.Equal(0, watchman.Reserve);
    }

    [Fact]
    public void TurningTheDifficultyUpLeavesEverybodyWithMoreToAnswerWith()
    {
        var twitchy = Standoff(Node(4, -2), reactions: ReactionModel.Twitchy);
        twitchy.Battle.Move(Node(3, 0));
        twitchy.Battle.EndTurn();

        var deliberate = Standoff(Node(4, -2), reactions: ReactionModel.Deliberate);
        deliberate.Battle.Move(Node(3, 0));
        deliberate.Battle.EndTurn();

        Assert.Equal(7, twitchy.Watchman.Reserve);
        Assert.Equal(2, deliberate.Watchman.Reserve);
    }

    [Fact]
    public void TheReserveAndTheArcBothExpireWhenTheWatchmanComesRoundAgain()
    {
        var (battle, watchman, runner) = Overwatched(OverwatchArc.Standard, Node(4, -2));
        Assert.Equal(6, watchman.Reserve);
        Assert.NotNull(watchman.Overwatch);

        battle.EndTurn();
        while (battle.Active != watchman) battle.EndTurn();

        Assert.Equal(0, watchman.Reserve);
        Assert.Null(watchman.Overwatch);
        Assert.Equal(watchman.Stats.ActionPoints, watchman.ActionPoints);
        Assert.NotNull(runner);
    }

    // ---- declaring an arc ------------------------------------------------------

    [Fact]
    public void DeclaringAnArcCostsAPointAndPointsTheWeaponThatWay()
    {
        var (battle, watchman, _) = Standoff(Node(4, -2));

        Assert.True(battle.SetOverwatch(OverwatchArc.Narrow, HexDirection.North));

        Assert.Equal(8, watchman.ActionPoints); // one to declare, one to turn on the spot
        Assert.Equal(HexDirection.North, watchman.Facing);
        Assert.Equal(OverwatchArc.Narrow, watchman.Overwatch!.Value.Arc);
        Assert.Equal(HexDirection.North, watchman.Overwatch!.Value.Centre);
    }

    [Fact]
    public void HoldingTheArcYouAreAlreadyFacingCostsNothingExtra()
    {
        var (battle, watchman, _) = Standoff(Node(4, -2));

        Assert.True(battle.SetOverwatch(OverwatchArc.Narrow));

        Assert.Equal(9, watchman.ActionPoints);
        Assert.Equal(HexDirection.NorthEast, watchman.Overwatch!.Value.Centre);
    }

    [Fact]
    public void AWatchmanWithNothingLeftCannotDeclareAnything()
    {
        var (battle, watchman, _) = Standoff(Node(4, -2));
        battle.Move(Node(0, 10));

        Assert.Equal(0, watchman.ActionPoints);
        Assert.False(battle.SetOverwatch(OverwatchArc.Narrow));
        Assert.Null(watchman.Overwatch);
    }

    // ---- being caught by one ---------------------------------------------------

    [Fact]
    public void WalkingAcrossAWatchedArcGetsYouShotAt()
    {
        var (battle, watchman, runner) = Overwatched(OverwatchArc.Standard, Node(4, -2));

        var outcome = battle.Move(Node(4, 2));

        Assert.True(outcome.Moved);
        var window = Assert.IsType<ReactionWindow>(outcome.Reactions);
        var offer = Assert.Single(window.Offers);
        Assert.Same(watchman, offer.Reactor);
        Assert.Equal(ReactionKind.Overwatch, offer.Kind);

        var resolution = Assert.Single(window.Resolutions);
        Assert.True(resolution.Outcome.Fired);
        Assert.Equal(runner, resolution.Shot.Target);
    }

    [Fact]
    public void WalkingRoundBehindTheWatchmanGetsYouNothingAtAll()
    {
        var (battle, _, _) = Overwatched(OverwatchArc.Standard, Node(-4, 0));

        var outcome = battle.Move(Node(-4, 3));

        Assert.Empty(outcome.Reactions!.Offers);
        Assert.Empty(outcome.Reactions!.Resolutions);
    }

    [Fact]
    public void AnEnemyHoldingNoArcAtAllIsNeverEvenAsked()
    {
        var (battle, watchman, _) = Standoff(Node(4, -2));
        battle.EndTurn();

        Assert.Equal(7, watchman.Reserve);

        var outcome = battle.Move(Node(4, 2));

        // Points in hand are not the same thing as a weapon already pointed at the ground you
        // are crossing. Answering a move you were not watching for is a surprise reaction.
        Assert.Empty(outcome.Reactions!.Offers);
    }

    [Fact]
    public void AWatchmanWhoBankedOnlyScrapsHoldsAnEmptyArc()
    {
        var (battle, watchman, _) = Overwatched(
            OverwatchArc.Standard, Node(4, -2), reactions: ReactionModel.Deliberate);

        Assert.Equal(2, watchman.Reserve);

        var outcome = battle.Move(Node(4, 2));

        // Two points is not a shot in any weapon, so there is nothing to offer.
        Assert.Empty(outcome.Reactions!.Offers);
    }

    [Fact]
    public void ANarrowArcShootsBetterDownItThanAWideOneDoes()
    {
        var narrow = Overwatched(OverwatchArc.Narrow, Node(2, 0));
        var wide = Overwatched(OverwatchArc.Wide, Node(2, 0));

        var down = narrow.Battle.Move(Node(6, 0));
        var across = wide.Battle.Move(Node(6, 0));

        var keen = down.Reactions!.Offers.Single().Recommended;
        var casual = across.Reactions!.Offers.Single().Recommended;

        Assert.Equal(keen.Mode, casual.Mode);
        Assert.True(keen.Forecast.HitChance > casual.Forecast.HitChance);
    }

    [Fact]
    public void AWiderArcCoversGroundANarrowOneNeverSees()
    {
        // A run out along a bearing forty degrees off where the watchman is looking: outside a
        // sixty degree arc, inside a hundred and twenty, and well inside the cone it is actually
        // paying attention to, so noticing it is not what is in question here.
        var narrow = Overwatched(OverwatchArc.Narrow, Node(1, 2));
        var standard = Overwatched(OverwatchArc.Standard, Node(1, 2));

        var ignored = narrow.Battle.Move(Node(2, 4));
        var caught = standard.Battle.Move(Node(2, 4));

        Assert.Empty(ignored.Reactions!.Offers);
        Assert.Single(caught.Reactions!.Offers);
    }

    [Fact]
    public void AnApproachExactlyOnTheEdgeOfTheArcFallsOutsideIt()
    {
        // Hex bearings are exact multiples of sixty degrees, so a run due north of a watchman
        // facing north-east sits precisely on the edge of a hundred and twenty degree arc. The
        // edge belongs to the wider arc, here and in the attention cones — and it is decided
        // that way rather than by whatever 60.00000000000001 compares as.
        var (battle, watchman, _) = Overwatched(OverwatchArc.Standard, Node(0, 3));

        Assert.Equal(60.0, battle.AngleOffDegrees(watchman.Position, HexDirection.NorthEast, Node(0, 4)), 6);

        var outcome = battle.Move(Node(0, 6));

        // Cover that ground and you have to declare a wider arc, and shoot worse down all of it.
        Assert.Empty(outcome.Reactions!.Offers);
    }

    // ---- noticing before shooting ----------------------------------------------

    /// <summary>
    /// A blank wall across the front of the hex a runner starts in, so the watchman at the
    /// origin has never laid eyes on them. Stepping one hex sideways comes out from behind it.
    /// </summary>
    private static BattleMap BehindABuilding()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 14);
        map.AddSideWall(new Hex(3, 0), HexDirection.SouthWest, 0, WallProfile.Solid);
        return map;
    }

    [Fact]
    public void SteppingOutFromCoverIntoAWatchedArcIsNoticedAndShotAt()
    {
        var (battle, watchman, runner) = Overwatched(OverwatchArc.Standard, Node(3, 0), BehindABuilding());

        // The watchman could not see the runner when it last looked, so it knows nothing about
        // them. Holding an arc is looking down it, so the crossing itself is what gets noticed.
        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(watchman.Id, runner.Id).State);

        var outcome = battle.Move(Node(3, 2));

        Assert.Single(outcome.Reactions!.Offers);
        Assert.True(battle.Awareness.Of(watchman.Id, runner.Id).State >= AwarenessState.Searching);
    }

    [Fact]
    public void AWatchmanWhoOnlyGoesOnWhatItAlreadyKnewLetsThatCrossingThrough()
    {
        // The same run against a watchman that does not get to look outside its own turn. This
        // is what gating purely on prior awareness costs: the canonical overwatch situation —
        // somebody breaking cover across a held arc — goes entirely unanswered, because looking
        // happens on your turn and the watchman has already had it.
        var rules = ReactionModel.Default with { OverwatchLooks = false };
        var (battle, _, _) = Overwatched(OverwatchArc.Standard, Node(3, 0), BehindABuilding(), reactions: rules);

        var outcome = battle.Move(Node(3, 2));

        Assert.Empty(outcome.Reactions!.Offers);
    }

    [Fact]
    public void ACarefulEnoughApproachCrossesAWatchedArcUntouched()
    {
        // Wider hexes, so the runner can be most of forty metres out and still on the map. It is
        // inside the arc, inside weapon range, and in plain line of sight the whole way.
        var battle = new Battle(new BattleMap().FillDisc(Hex.Zero, 14), new HexLayout(size: 4.0), seed: 1);
        var watchman = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast);
        var runner = battle.Deploy("Vance", Side.Player, Node(6, -3), Tardy, HexDirection.North);
        battle.Start();

        Assert.True(battle.SetOverwatch(OverwatchArc.Standard));
        battle.EndTurn();

        battle.ChangeStance(Stance.Prone);
        var outcome = battle.Move(Node(6, -1));

        // Prone at that range is simply not noticed, and what is not noticed is not shot at.
        // Nothing here is special to overwatch — it is the ordinary detection model deciding.
        Assert.Equal(Stance.Prone, runner.Stance);
        Assert.True(battle.CanSee(watchman, runner));
        Assert.True(battle.Awareness.Of(watchman.Id, runner.Id).State < AwarenessState.Searching);
        Assert.Empty(outcome.Reactions!.Offers);
    }

    // ---- paying your own prices ------------------------------------------------

    [Fact]
    public void ASlowShotLandsLaterInTheWindowThanTheSameModeFiredQuickly()
    {
        // A long enough run that neither shot is still in the air when it ends.
        var quick = Overwatched(OverwatchArc.Standard, Node(4, -2));
        var slow = Overwatched(
            OverwatchArc.Standard, Node(4, -2),
            watchmanCosts: new CostProfile { Firing = 1.6 });

        var early = Snap(quick.Battle.Move(Node(4, 6)));
        var late = Snap(slow.Battle.Move(Node(4, 6)));

        // Cost is time inside a window, so a watchman that is slow on the trigger pays for it in
        // ticks and catches the runner further along the route. Same weapon, same mode.
        Assert.Equal(FireMode.Snap.ApCost, early.Forecast.ApCost);
        Assert.True(late.Forecast.ApCost > early.Forecast.ApCost);
        Assert.True(late.ResolvesAt > early.ResolvesAt);

        static ReactionShot Snap(MoveOutcome outcome)
            => outcome.Reactions!.Offers.Single().Options.Single(o => o.Mode == FireMode.Snap);
    }

    [Fact]
    public void GearThatSpeedsUpTheTriggerBuysAnExtraShotOutOfTheSameReserve()
    {
        var (battle, watchman, _) = Overwatched(
            OverwatchArc.Standard, Node(4, -2),
            watchmanCosts: new CostProfile { Firing = 0.8 });

        var offer = battle.Move(Node(4, 2)).Reactions!.Offers.Single();

        // Six banked points buy a snap and a standard shot at list price. Knock a fifth off and
        // the aimed shot comes into reach as well, which is the whole point of the mount.
        Assert.Equal(6, offer.Reserve);
        Assert.Contains(offer.Options, o => o.Mode == FireMode.Aimed);
        Assert.All(offer.Options, o => Assert.True(o.Forecast.ApCost < o.Mode.ApCost));
    }

    [Fact]
    public void AHeavyTrooperCoversLessGroundOnTheSamePoints()
    {
        var battle = Field();
        var scout = battle.Deploy("Scout", Side.Player, Node(0, 0), UnitStats.Default with { Initiative = 30 });
        var gunner = battle.Deploy(
            "Gunner", Side.Player, Node(0, 6),
            UnitStats.Default with { Initiative = 1, Costs = CostProfile.Gunner });
        battle.Start();

        // One graph, describing the same ground. What each of them pays to cross it differs.
        var quick = battle.Destinations(scout).Count();
        var slow = battle.Destinations(gunner).Count();

        Assert.True(slow < quick, $"gunner reached {slow}, scout reached {quick}");
    }

    // ---- action points are time ------------------------------------------------

    [Fact]
    public void ASnapShotCatchesThemInTheOpenWhereAnAimedOneArrivesAfterTheyReachCover()
    {
        var (battle, watchman, runner) = Standoff(Node(4, -2), CoverAtTheEnd());
        var move = Route(battle, runner, Node(4, 2));

        var snap = battle.PlanShot(
            watchman, runner, FireMode.Snap, 1.0, move.PoseAt(FireMode.Snap.ApCost), ApSource.Turn);
        var aimed = battle.PlanShot(
            watchman, runner, FireMode.Aimed, 1.0, move.PoseAt(FireMode.Aimed.ApCost), ApSource.Turn);

        Assert.True(snap.CanFire);
        Assert.True(aimed.CanFire);

        // The aimed shot is the better shot and it misses the moment: it goes off after the
        // runner has arrived, and arrives at a target behind a wall.
        Assert.Equal(Node(4, 1), snap.TargetPose!.Value.Position);
        Assert.Equal(move.Destination, aimed.TargetPose!.Value.Position);
        Assert.Equal(CoverGrade.None, snap.Sight.Cover);
        Assert.True(aimed.Sight.Cover > CoverGrade.None);

        Assert.True(snap.HitChance > aimed.HitChance);
    }

    [Fact]
    public void TheWatchmanTakesTheShotThatConnectsRatherThanTheBetterOne()
    {
        var (battle, _, _) = Overwatched(OverwatchArc.Standard, Node(4, -2), CoverAtTheEnd());

        var outcome = battle.Move(Node(4, 2));
        var offer = outcome.Reactions!.Offers.Single();

        // Both are affordable out of six banked points, and the slower one shoots better in the
        // abstract. It still loses, because it lands after the runner is behind the wall.
        Assert.Contains(offer.Options, o => o.Mode == FireMode.Standard);
        Assert.Equal(FireMode.Snap, offer.Recommended.Mode);
        Assert.Equal(FireMode.Snap.ApCost, offer.Recommended.ResolvesAt);
    }

    [Fact]
    public void AReactionResolvesAgainstWhereTheRunnerWillBeNotWhereItStarted()
    {
        var (battle, _, runner) = Overwatched(OverwatchArc.Standard, Node(4, -2));
        var start = runner.Position;

        var outcome = battle.Move(Node(4, 2));
        var resolution = outcome.Reactions!.Resolutions.Single();

        Assert.NotEqual(start, resolution.Caught);
        Assert.Equal(outcome.Reactions!.Move.PositionAt(resolution.At), resolution.Caught);
        Assert.Equal(resolution.Shot.Forecast.TargetPose!.Value.Position, resolution.Caught);
    }

    [Fact]
    public void ARunnerCrossingAWatchedArcIsShotInWhicheverSideItHasSwungRound()
    {
        // A run across the watchman's front rather than towards it, so the bearing between the
        // two swings a long way over the four ticks it takes.
        var (battle, watchman, runner) = Overwatched(OverwatchArc.Standard, Node(4, -3));

        var faceNow = battle.FaceToward(runner, watchman);
        var outcome = battle.Move(Node(4, 1));
        var faceHit = outcome.Reactions!.Resolutions.Single().Shot.Forecast.LikeliestFace;

        // Which plate the round arrives at is worked out where it lands, not where the runner
        // was standing when the window opened. Nothing special-cases this: the runner is
        // genuinely standing there by the time the shot goes off, showing whichever side the
        // run has swung round by then.
        Assert.Equal(BodyFace.FrontLeft, faceNow);
        Assert.Equal(BodyFace.RearLeft, faceHit);
    }

    // ---- spending the reserve --------------------------------------------------

    [Fact]
    public void AnOverwatchShotComesOutOfTheReserveAndNotOutOfNextTurn()
    {
        var (battle, watchman, _) = Overwatched(OverwatchArc.Standard, Node(4, -2));
        Assert.Equal(6, watchman.Reserve);

        var shot = battle.Move(Node(4, 2)).Reactions!.Resolutions.Single().Shot;

        Assert.Equal(6 - shot.Mode.ApCost, watchman.Reserve);
        Assert.Equal(0, watchman.ActionPoints);
    }

    [Fact]
    public void AWatchmanThatHasSpentItsReserveHoldsItsFire()
    {
        var (battle, watchman, runner) = Overwatched(OverwatchArc.Standard, Node(4, -2));

        var first = battle.Move(Node(4, 2));
        Assert.Single(first.Reactions!.Resolutions);
        Assert.True(watchman.Reserve < FireMode.Snap.ApCost);

        // A reserve is spent, not refreshed, so the second run across the same arc in the same
        // round is not answered at all — and will not be until the watchman gets a turn back.
        var second = battle.Move(Node(4, 4));
        Assert.Empty(second.Reactions!.Offers);
        Assert.NotNull(watchman.Overwatch); // still holding the arc, just with nothing to hold it with
        Assert.True(runner.InPlay);
    }

    [Fact]
    public void TakingAnOverwatchShotTellsTheRunnerExactlyWhereYouAre()
    {
        var (battle, watchman, runner) = Overwatched(OverwatchArc.Standard, Node(4, -2));
        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(runner.Id, watchman.Id).State);

        battle.Move(Node(4, 2));

        Assert.True(runner.InPlay);
        Assert.True(battle.Awareness.Of(runner.Id, watchman.Id).State >= AwarenessState.Alerted);
        Assert.Equal(watchman.Position, battle.Awareness.Of(runner.Id, watchman.Id).LastKnownPosition);
    }

    // ---- being stopped ---------------------------------------------------------

    [Fact]
    public void BeingDroppedHalfWayAcrossLeavesYouWhereYouFell()
    {
        var (battle, _, runner) = Overwatched(
            OverwatchArc.Standard,
            Node(4, -2),
            CoverAtTheEnd(),
            runnerStats: UnitStats.Default with { Vitality = 1 });

        var outcome = battle.Move(Node(4, 2));
        var window = outcome.Reactions!;

        Assert.True(window.Resolutions.Single().Outcome.TargetDown);
        Assert.True(window.Interrupted);
        Assert.Equal(FireMode.Snap.ApCost, window.StoppedAt);
        Assert.False(runner.InPlay);

        // Three ticks into a four tick run, so one hex short of the cover being run for.
        Assert.Equal(Node(4, 1), runner.Position);
        Assert.NotEqual(Node(4, 2), runner.Position);
    }

    [Fact]
    public void AnUnansweredRunEndsWhereItMeantTo()
    {
        var (battle, _, runner) = Overwatched(OverwatchArc.Standard, Node(-4, 0));

        var outcome = battle.Move(Node(-4, 3));

        Assert.False(outcome.Interrupted);
        Assert.Equal(outcome.Reactions!.Move.Duration, outcome.Reactions!.StoppedAt);
        Assert.Equal(Node(-4, 3), runner.Position);
        Assert.Equal(HexDirection.North, runner.Facing);
    }

    // ---- the interface the player will drive -----------------------------------

    [Fact]
    public void AWindowOffersOneChoicePerWayOfFiringAndRecommendsOneOfThem()
    {
        var (battle, _, _) = Overwatched(OverwatchArc.Standard, Node(4, -2), CoverAtTheEnd());

        var offer = battle.Move(Node(4, 2)).Reactions!.Offers.Single();

        Assert.Equal(offer.Options.Count, offer.Options.Select(o => o.Mode).Distinct().Count());
        Assert.Contains(offer.Recommended, offer.Options);
        Assert.All(offer.Options, o => Assert.True(o.Mode.ApCost <= offer.Reserve));
        Assert.All(offer.Options, o => Assert.True(o.Forecast.CanFire));
    }

    [Fact]
    public void AWindowCannotBeResolvedTwice()
    {
        var (battle, _, runner) = Overwatched(OverwatchArc.Standard, Node(4, -2));
        var window = battle.Move(Node(4, 2)).Reactions!;

        Assert.Throws<InvalidOperationException>(() => window.Resolve());
        Assert.Throws<InvalidOperationException>(() => window.Place(window.Placements[0]));
        Assert.NotNull(runner);
    }
}
