using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// What an action is worth, and what gets chosen because of it. These read as judgements: two
/// men in front of you and only one of them worth shooting, a beam that will be soaked whatever
/// you do about it, a shout that is worth something only because of who can hear it.
/// </summary>
public class TacticsTests
{
    private static NodeId Node(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    private static readonly UtilityModel Rates = UtilityModel.Default;

    /// <summary>Always goes first, so a posture is declared before anyone runs across it.</summary>
    private static readonly UnitStats Watchful = UnitStats.Default with { Initiative = 30 };

    /// <summary>Always goes last.</summary>
    private static readonly UnitStats Tardy = UnitStats.Default with { Initiative = 1 };

    private static Battle Field(BattleMap? map = null, int seed = 1)
        => new(map ?? new BattleMap().FillDisc(Hex.Zero, 14), new HexLayout(size: 1.0), seed: seed);

    // ---- what a shot is actually expected to do ---------------------------------

    [Fact]
    public void ABeamThatLandsSquarelyOnAFullForceShieldIsWorthNothingAtAll()
    {
        var battle = Field();
        var beamer = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast, Loadout.Beamer);
        var shielded = battle.Deploy("Vance", Side.Player, Node(4, 0), Tardy, HexDirection.SouthWest, Loadout.Beamer);
        battle.Start();

        var plan = battle.PlanShot(beamer, shielded);

        // The shot connects and delivers everything the weapon has. Ten points of shield soak
        // eight points of beam without noticing, and the soldier behind it feels nothing.
        Assert.True(plan.CanFire);
        Assert.True(plan.ExpectedDamage > 0);
        Assert.Equal(0, battle.Gunnery.Expect(plan).Vitality);
    }

    [Fact]
    public void AGunnerPrefersTheManWhoseShieldsHaveGoneToTheOneStillCarryingThem()
    {
        var battle = Field();
        var beamer = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast, Loadout.Beamer);
        var fresh = battle.Deploy("Vance", Side.Player, Node(4, 0), Tardy, HexDirection.SouthWest, Loadout.Beamer);
        var bare = battle.Deploy("Idris", Side.Player, Node(4, -1), Tardy, HexDirection.SouthWest, Loadout.Beamer);
        battle.Start();

        // Somebody has already been at the second one, and the face they will be shot on has
        // nothing left on it.
        foreach (var face in BodyFaces.All) bare.Protection.Absorb(face, DamageKind.Beam, 40);

        var atFresh = battle.Tactics.Worth(battle.PlanShot(beamer, fresh));
        var atBare = battle.Tactics.Worth(battle.PlanShot(beamer, bare));

        Assert.True(atBare > atFresh * 4, $"bare {atBare:0.00} should dwarf shielded {atFresh:0.00}");
    }

    [Fact]
    public void TheSecondRoundOfABurstWalksThroughTheHoleTheFirstMade()
    {
        // A repeater round is six points and a fresh face stops all of it: one into the shield,
        // five into the plate. The plate is only eight thick, so it is gone by the second round.
        var armoured = new Protection(Loadout.Rifleman);
        var run = armoured.Preview(BodyFace.Front, DamageKind.Kinetic, damage: 6, rounds: 3);

        Assert.Equal(0, run[0].ToVitality);
        Assert.True(run[1].ToVitality > 0);
        Assert.True(run[2].ToVitality > run[1].ToVitality);

        // And nothing was actually taken off the soldier working that out.
        Assert.Equal(Loadout.Rifleman.ArmourPerFace, armoured.ArmourOn(BodyFace.Front));
    }

    [Fact]
    public void WearingThePlateOffCountsForSomethingEvenWhenNothingGetsThrough()
    {
        var battle = Field();
        var rifleman = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful);
        var target = battle.Deploy("Vance", Side.Player, Node(3, 0), Tardy, HexDirection.SouthWest);
        battle.Start();

        var plan = battle.PlanShot(rifleman, target, FireMode.Snap);
        var expected = battle.Gunnery.Expect(plan);

        // Most of a slug goes into the armour rather than the man, and armour does not come back.
        Assert.True(expected.PlateStripped > expected.Vitality);
        Assert.True(battle.Tactics.Worth(plan) > expected.Vitality);
    }

    [Fact]
    public void AShotThatMightFinishSomebodyIsWorthFarMoreThanTheVitalityItTakesOff()
    {
        var battle = Field();
        var rifleman = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful);
        var slight = battle.Deploy(
            "Vance", Side.Player, Node(3, 0),
            UnitStats.Default with { Initiative = 1, Vitality = 8 },
            HexDirection.SouthWest);
        battle.Start();

        // Nothing left to stop it, and a slug does more than they have.
        foreach (var face in BodyFaces.All) slight.Protection.Absorb(face, DamageKind.Kinetic, 40);

        var plan = battle.PlanShot(rifleman, slight);
        var expected = battle.Gunnery.Expect(plan);

        Assert.True(expected.DownChance > 0.5);

        // Everything they would have done for the rest of the fight goes with them, and that is
        // worth at least what it took to get them there.
        Assert.True(
            battle.Tactics.Worth(plan) > expected.Vitality * 1.9,
            $"{battle.Tactics.Worth(plan):0.00} should roughly double {expected.Vitality:0.00}");
    }

    // ---- how you are left standing ----------------------------------------------

    [Fact]
    public void TurningRoundIsWorthTheShotItOpensAndNothingElse()
    {
        var battle = Field();
        var sentry = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast);
        var behind = battle.Deploy("Vance", Side.Player, Node(-4, 0), Tardy, HexDirection.NorthEast);
        battle.Start();

        var round = battle.Awareness.AttentionOn(sentry, behind.Position);
        Assert.True(round < 1.0, "the point of the setup is that they are not being watched");

        var turned = UnitPose.Of(sentry) with { Facing = battle.HeadingTo(sentry.Position, behind.Position) };
        var appraisal = battle.Tactics.AppraisePosture(
            sentry, turned, battle.Costs.TurnInPlace, [Threat.At(behind)]);

        // Every face still carries the same plate and the same shield, and the glancing average
        // is flattened, so which way round the sentry stands changes nothing about the round it
        // catches. What turning buys is seeing them at all.
        Assert.Equal(0, appraisal.Spared, 6);
        Assert.True(appraisal.Prospect > 0);
        Assert.True(appraisal.WorthDoing);
    }

    [Fact]
    public void TurningTowardsSomebodyYouAlreadyHaveDeadToRightsBuysNothing()
    {
        var battle = Field();
        var sentry = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast);
        var behind = battle.Deploy("Vance", Side.Player, Node(-4, 0), Tardy, HexDirection.NorthEast);
        battle.Start();

        // Look at them until there is nothing further to learn. Over the shoulder is a slow way
        // to learn anything, which is the whole reason turning is on the table at all.
        for (var i = 0; i < 60 && battle.Awareness.Of(sentry.Id, behind.Id).State < AwarenessState.Engaged; i++)
            battle.Awareness.Notice(sentry, behind, UnitPose.Of(behind), battle.Round);

        Assert.Equal(AwarenessState.Engaged, battle.Awareness.Of(sentry.Id, behind.Id).State);

        var turned = UnitPose.Of(sentry) with { Facing = battle.HeadingTo(sentry.Position, behind.Position) };
        var appraisal = battle.Tactics.AppraisePosture(
            sentry, turned, battle.Costs.TurnInPlace, [Threat.At(behind)]);

        Assert.Equal(0, appraisal.Prospect, 6);
        Assert.False(appraisal.WorthDoing);
    }

    [Fact]
    public void GettingLowerIsWorthWhateverItTakesOffTheirShot()
    {
        var battle = Field();
        var sentry = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast);
        var threat = battle.Deploy("Vance", Side.Player, Node(4, 0), Tardy, HexDirection.SouthWest);
        battle.Start();

        var flat = UnitPose.Of(sentry) with { Stance = Stance.Prone };
        var appraisal = battle.Tactics.AppraisePosture(
            sentry, flat, battle.Costs.ChangeStance, [Threat.At(threat)]);

        // Flat is a smaller thing to hit, and the sight trace says so, so the shot coming back is
        // worth less. Nothing about the facing changed, so there is nothing further to see.
        Assert.True(appraisal.Spared > 0);
        Assert.Equal(0, appraisal.Prospect, 6);
    }

    // ---- passing it on -----------------------------------------------------------

    [Fact]
    public void CallingItInIsWorthWhatTheManWhoHearsItCanDoAboutIt()
    {
        var (battle, spotter, mate, runner) = Pair();

        // The spotter has a good look at the runner; the mate is standing right beside it with a
        // clear line on the same man and no idea he is there.
        for (var i = 0; i < 3; i++) battle.Awareness.Notice(spotter, runner, UnitPose.Of(runner), battle.Round);
        Assert.True(battle.CanSee(mate, runner));
        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(mate.Id, runner.Id).State);

        var word = battle.Tactics.AppraiseWord(
            spotter, runner, UnitPose.Of(runner), battle.Reactions.ShoutCost);

        Assert.True(word.Prospect > 0);
        Assert.True(word.WorthDoing);
    }

    [Fact]
    public void ShoutingAtSomebodyWhoAlreadyKnowsIsWorthNothing()
    {
        var (battle, spotter, mate, runner) = Pair();

        foreach (var watcher in new[] { spotter, mate })
            for (var i = 0; i < 3; i++)
                battle.Awareness.Notice(watcher, runner, UnitPose.Of(runner), battle.Round);

        var word = battle.Tactics.AppraiseWord(
            spotter, runner, UnitPose.Of(runner), battle.Reactions.ShoutCost);

        Assert.Equal(0, word.Prospect, 6);
        Assert.False(word.WorthDoing);
    }

    // ---- and what gets chosen because of it --------------------------------------

    [Fact]
    public void AShotThatWillBeSoakedEntirelyIsNotWorthThePointsItCosts()
    {
        // A beam sentry startled by somebody carrying a full set of shields. The shot is there,
        // it is affordable, and it will do nothing whatever — which is a judgement the old policy
        // could not make, because it ranked shots on damage arriving rather than on damage
        // arriving anywhere.
        var (battle, _, _) = Unready(sentryKit: Loadout.Beamer, runnerKit: Loadout.Beamer);

        var window = battle.Move(IntoTheOpen).Reactions!;
        var shot = window.Offers.Single().Options.Single(o => o.Action == ReactionAction.Fire);

        Assert.True(shot.Forecast!.ExpectedDamage > 0, "the shot connects; it simply does not land");
        Assert.Equal(0, battle.Gunnery.Expect(shot.Forecast).Vitality);
        Assert.False(window.Appraise(shot).WorthDoing);
    }

    [Fact]
    public void TheSameShotIsWorthTakingOnceHisShieldsAreGone()
    {
        // The other half of the pair. Same sentry, same weapon, same ground, same distance — the
        // only thing that changed is that somebody has already been at the runner.
        var (battle, _, runner) = Unready(sentryKit: Loadout.Beamer, runnerKit: Loadout.Beamer);
        foreach (var face in BodyFaces.All) runner.Protection.Absorb(face, DamageKind.Beam, 40);

        var window = battle.Move(IntoTheOpen).Reactions!;
        var offer = window.Offers.Single();

        Assert.True(window.Appraise(offer.Options.Single(o => o.Action == ReactionAction.Fire)).WorthDoing);
        Assert.Equal(ReactionAction.Fire, offer.Recommended.Action);
    }

    [Fact]
    public void DivingBehindTheSandbagsCostsYouYourOwnShotAsWellAsTheirs()
    {
        var battle = Field(BehindABuilding(sandbags: true));
        var sentry = battle.Deploy(
            "Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast, Loadout.Beamer);
        var runner = battle.Deploy(
            "Vance", Side.Player, Node(3, 2), Tardy, HexDirection.SouthWest, Loadout.Beamer);
        battle.Start();

        var flat = UnitPose.Of(sentry) with { Stance = Stance.Prone };

        Assert.False(
            battle.Sight.Trace(runner.Vantage, new Vantage(sentry.Position, Stance.Prone)).CanSee,
            "flat behind a knee-high wall is the whole point of the setup");

        var appraisal = battle.Tactics.AppraisePosture(
            sentry, flat, battle.Costs.ChangeStance, [Threat.At(runner)]);

        // Cover works in both directions and the scoring says so without being told. Nothing can
        // be shot at a soldier who cannot be seen, and nothing can be shot by one either.
        Assert.True(appraisal.Spared > 0, "there is no longer a shot coming");
        Assert.True(appraisal.Prospect < 0, "and no longer a shot going the other way");
    }

    // ---- scaffolding --------------------------------------------------------------

    /// <summary>Two hostiles side by side, and a player unit in plain view of both of them.</summary>
    private static (Battle Battle, Unit Spotter, Unit Mate, Unit Runner) Pair()
    {
        var battle = Field();
        var spotter = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast);
        var mate = battle.Deploy("Roan", Side.Hostile, Node(0, -1), Watchful, HexDirection.NorthEast);
        var runner = battle.Deploy("Vance", Side.Player, Node(4, 0), Tardy, HexDirection.SouthWest);
        battle.Start();

        return (battle, spotter, mate, runner);
    }

    /// <summary>
    /// A blank wall across the front of the hex a runner starts in, so the sentry at the origin
    /// has never laid eyes on them. Stepping one hex sideways comes out from behind it.
    /// </summary>
    /// <param name="sandbags">
    /// A knee-high wall across the sentry's own north-east face as well. Standing, it is half
    /// cover and half the silhouette; flat behind it, the sentry cannot be seen at all.
    /// </param>
    private static BattleMap BehindABuilding(bool sandbags = false)
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 14);
        map.AddSideWall(new Hex(3, 0), HexDirection.SouthWest, 0, WallProfile.Solid);
        if (sandbags) map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Low);
        return map;
    }

    /// <summary>Out from behind the wall, into the open ground north-east of the sentry.</summary>
    private static NodeId IntoTheOpen => Node(3, 2);

    /// <summary>A sentry with points banked and nothing declared, about to be walked in front of.</summary>
    private static (Battle Battle, Unit Sentry, Unit Runner) Unready(
        Loadout? sentryKit = null,
        Loadout? runnerKit = null,
        bool sandbags = false)
    {
        var battle = Field(BehindABuilding(sandbags));
        var sentry = battle.Deploy(
            "Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast, sentryKit);
        var runner = battle.Deploy(
            "Vance", Side.Player, Node(3, 0), Tardy, HexDirection.North, runnerKit);

        battle.Start();
        Assert.Same(sentry, battle.Active);
        battle.EndTurn();

        Assert.False(battle.CanSee(sentry, runner), "the wall was supposed to hide them");

        return (battle, sentry, runner);
    }
}
