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

    [Fact]
    public void HowSpottedYouAreIsWeighedAsARungAndNeverAsTheNumberBehindIt()
    {
        // A sentry behind sandbags, so that going flat takes it out of view altogether and what
        // that saves is the whole of the shot, weighed by how likely the shot is to come. And a
        // dim-sighted watcher, so each look moves the certainty by a little and several looks fit
        // inside one rung of the ladder.
        var battle = Field(BehindABuilding(sandbags: true));
        var sentry = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast);
        var watcher = battle.Deploy(
            "Vance", Side.Player, Node(3, 2),
            UnitStats.Default with { Initiative = 1, Perception = 2 },
            HexDirection.SouthWest);
        battle.Start();

        var flat = UnitPose.Of(sentry) with { Stance = Stance.Prone };
        Assert.False(battle.Sight.Trace(watcher.Vantage, flat.Vantage).CanSee, "flat behind the wall is the point");

        double Spared() => battle.Tactics.AppraisePosture(sentry, flat, battle.Costs.ChangeStance, [Threat.At(watcher)]).Spared;

        void LookUntil(AwarenessState state)
        {
            for (var i = 0; i < 40 && battle.Awareness.Of(watcher.Id, sentry.Id).State < state; i++)
                battle.Awareness.Notice(watcher, sentry, UnitPose.Of(sentry), battle.Round);
            Assert.Equal(state, battle.Awareness.Of(watcher.Id, sentry.Id).State);
        }

        var unaware = Spared();

        LookUntil(AwarenessState.Suspicious);
        var barely = Spared();
        var before = battle.Awareness.Of(watcher.Id, sentry.Id).Detection;

        battle.Awareness.Notice(watcher, sentry, UnitPose.Of(sentry), battle.Round);
        Assert.Equal(AwarenessState.Suspicious, battle.Awareness.Of(watcher.Id, sentry.Id).State);
        Assert.True(battle.Awareness.Of(watcher.Id, sentry.Id).Detection > before, "the look was supposed to count");

        // One more look, same rung: the sentry cannot tell the difference, so neither may the
        // scorer. The player is shown the rung and nothing behind it, and a soldier who could
        // read the number would break cover at exactly the right moment every time.
        Assert.Equal(barely, Spared(), 9);
        Assert.True(barely > unaware, "but a new rung is a real change in how much there is to fear");
    }

    // ---- what a walk tells everybody ---------------------------------------------

    [Fact]
    public void ALoudRouteIsPricedOnWhoWouldHearItBeforeAnybodyTakesIt()
    {
        var (battle, sneak, listener) = Overheard(Loadout.Rifleman) is var (b, gunner, _, hidden)
            ? (b, gunner, hidden)
            : throw new System.InvalidOperationException();

        // A short walk and a long one to the same place: the route decides the racket, and the
        // man in the shed cannot see the sneak but can hear both.
        var quiet = new UnitPose(Node(0, 1), sneak.Stance, HexDirection.North);
        var reach = battle.Reachable(sneak);
        Assert.True(reach.TryGetPath(quiet.Position, out var path));

        var soft = battle.Loudness(sneak, path!);
        Assert.True(soft > 0);

        var whisper = battle.Tactics.AppraiseMove(sneak, quiet, reach.CostTo(quiet.Position)!.Value, 0, []);
        var stamping = battle.Tactics.AppraiseMove(sneak, quiet, reach.CostTo(quiet.Position)!.Value, soft * 40, []);

        Assert.Contains(battle.Awareness.WouldHear(sneak, quiet.Position, soft * 40), a => a.Learner == listener);
        Assert.True(whisper.Spared > stamping.Spared, $"{stamping} should cost more than {whisper}");
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
            spotter, runner, UnitPose.Of(runner), battle.Costs.Shout);

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
            spotter, runner, UnitPose.Of(runner), battle.Costs.Shout);

        Assert.Equal(0, word.Prospect, 6);
        Assert.False(word.WorthDoing);
    }

    // ---- what firing tells everybody ---------------------------------------------

    [Fact]
    public void ASlugRifleIsHeardThroughAWallAndABeamIsNotHeardAtAll()
    {
        var (battle, gunner, watched, hidden) = Overheard(Loadout.Rifleman);

        var told = battle.Awareness
            .WouldAnnounce(gunner, UnitPose.Of(gunner), gunner.Weapon, watched)
            .ToList();

        // Forty-five points of noise carries eighteen metres and does not care about the
        // building in the way.
        Assert.False(battle.CanSee(gunner, hidden), "the wall was supposed to hide them");
        Assert.Contains(told, t => t.Learner == hidden);
        Assert.Contains(told, t => t.Learner == watched);
    }

    [Fact]
    public void ABeamTellsOnlyThePeopleWhoCanSeeWhereItCameFrom()
    {
        var (battle, beamer, watched, hidden) = Overheard(Loadout.Beamer);

        var told = battle.Awareness
            .WouldAnnounce(beamer, UnitPose.Of(beamer), beamer.Weapon, watched)
            .ToList();

        // Silent, so the man behind the building learns nothing. The one with a line on the
        // shooter gets a bright arrow pointing straight back down it.
        Assert.DoesNotContain(told, t => t.Learner == hidden);
        Assert.Contains(told, t => t.Learner == watched);
    }

    [Fact]
    public void AShotIsWorthLessWhenItBringsHisMateDownOnYouAsWell()
    {
        var (battle, gunner, target, _) = Pairing();
        var alone = Alone(Loadout.Rifleman);

        var seen = battle.Tactics.Appraise(battle.PlanShot(gunner, target));
        var quiet = alone.Battle.Tactics.Appraise(alone.Battle.PlanShot(alone.Gunner, alone.Target));

        // The same soldier, the same weapon, the same target at the same range. The only
        // difference is that somebody who can shoot back is watching.
        Assert.Equal(quiet.Harm, seen.Harm, 6);
        Assert.True(seen.Score < quiet.Score);

        // Shooting a man who did not know you were there tells him, whoever else is about, so
        // even the shot taken in private costs something.
        Assert.True(quiet.Spared < 0, $"the target learns, so {quiet.Spared:0.00} should be negative");
        Assert.True(seen.Spared < quiet.Spared, $"{seen.Spared:0.00} should be worse than {quiet.Spared:0.00}");
    }

    [Fact]
    public void SomebodyWhoHearsTheShotAndCannotReachYouCostsYouNothingYet()
    {
        var (battle, gunner, watched, hidden) = Overheard(Loadout.Rifleman);

        // He hears it, and it tells him roughly where you are.
        Assert.Contains(
            battle.Awareness.WouldAnnounce(gunner, UnitPose.Of(gunner), gunner.Weapon, watched),
            t => t.Learner == hidden);

        // And it costs the gunner nothing, because what being given away is worth is measured by
        // what the person you gave yourself away to could do about it — and from inside a shed
        // that is nothing. He will come looking now, a unit acts on a marker; but what that is
        // worth is the best shot he could reach in a turn, and pricing it means a search inside
        // every shot the scorer weighs. This test exists to pin the gap rather than to approve
        // of it.
        var told = battle.Tactics.GivenAway(battle.PlanShot(gunner, watched));
        var alone = Alone(Loadout.Rifleman);

        Assert.Equal(alone.Battle.Tactics.GivenAway(alone.Battle.PlanShot(alone.Gunner, alone.Target)), told, 6);
    }

    [Fact]
    public void TellingPeopleWhatTheyAlreadyKnowCostsNothing()
    {
        var (battle, gunner, watched, hidden) = Overheard(Loadout.Rifleman);

        // Both of them already have a live fix on the gunner, so the shot settles nothing.
        foreach (var knower in new[] { watched, hidden })
            for (var i = 0; i < 60 && battle.Awareness.Of(knower.Id, gunner.Id).Detection < 100; i++)
                battle.Awareness.Notice(knower, gunner, UnitPose.Of(gunner), battle.Round);

        Assert.Equal(0, battle.Tactics.GivenAway(battle.PlanShot(gunner, watched)), 6);
    }

    // ---- what holding back is worth ----------------------------------------------

    [Fact]
    public void NothingBanksBelowTheFloorAndTheFloorIsAStep()
    {
        var rules = ReactionModel.Default;

        Assert.Equal(0, rules.Banked(rules.ReserveFloor));
        Assert.True(rules.Banked(15) >= rules.ReserveFloor);
        Assert.Equal(35, rules.Banked(UnitStats.Default.ActionPoints));
    }

    [Fact]
    public void PointsHeldBackAreWorthWhateverTheyCouldAnswerWith()
    {
        var (battle, sentry, runner) = Facing();
        var threats = new[] { Threat.At(runner) };

        var whole = battle.Tactics.AppraiseHolding(sentry, sentry.Stats.ActionPoints, threats);
        var scraps = battle.Tactics.AppraiseHolding(sentry, battle.Reactions.ReserveFloor, threats);

        Assert.True(whole.Prospect > 0);
        Assert.Equal(0, scraps.Prospect, 6);
    }

    [Fact]
    public void AReserveIsWorthNothingWhenThereIsNobodyToAnswer()
    {
        var (battle, sentry, _) = Facing();

        Assert.Equal(Appraisal.Nothing, battle.Tactics.AppraiseHolding(sentry, sentry.Stats.ActionPoints, []));
    }

    [Fact]
    public void HoldingAnArcIsWorthMoreThanHoldingThePointsAlone()
    {
        var (battle, sentry, runner) = Facing();
        var threats = new[] { Threat.At(runner) };

        var loose = battle.Tactics.AppraiseHolding(sentry, 40, threats);
        var narrow = battle.Tactics.AppraiseHolding(sentry, 40, threats, OverwatchArc.Narrow.AimBonus);
        var wide = battle.Tactics.AppraiseHolding(sentry, 40, threats, OverwatchArc.Wide.AimBonus);

        // The whole decision an arc offers, and it comes out of the arithmetic rather than off a
        // preference list: narrow shoots best, wide barely beats not declaring at all.
        Assert.True(narrow.Prospect > wide.Prospect);
        Assert.True(wide.Prospect > loose.Prospect);
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

    /// <summary>
    /// A gunner with somebody in plain sight and somebody else round the back of a building —
    /// close enough to hear a shot, with no line on where it came from.
    /// </summary>
    private static (Battle Battle, Unit Gunner, Unit Watched, Unit Hidden) Overheard(Loadout kit)
    {
        // Four walls of a shed, so there is no line into it from anywhere the gunner might be.
        var map = new BattleMap().FillDisc(Hex.Zero, 14);
        foreach (var side in System.Enum.GetValues<HexDirection>())
            map.AddSideWall(new Hex(0, 4), side, 0, WallProfile.Solid);

        var battle = Field(map);
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast, kit);
        var watched = battle.Deploy("Vance", Side.Player, Node(4, 0), Tardy, HexDirection.SouthWest);
        var hidden = battle.Deploy("Idris", Side.Player, Node(0, 4), Tardy, HexDirection.North);
        battle.Start();

        return (battle, gunner, watched, hidden);
    }

    /// <summary>A gunner, a target, and the target's mate standing in the open beside him.</summary>
    private static (Battle Battle, Unit Gunner, Unit Target, Unit Mate) Pairing()
    {
        var battle = Field();
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast);
        var target = battle.Deploy("Vance", Side.Player, Node(4, 0), Tardy, HexDirection.SouthWest);
        var mate = battle.Deploy("Idris", Side.Player, Node(4, -1), Tardy, HexDirection.SouthWest);
        battle.Start();

        return (battle, gunner, target, mate);
    }

    /// <summary>The same gunner and target, with nobody else on the field to overhear it.</summary>
    private static (Battle Battle, Unit Gunner, Unit Target) Alone(Loadout kit)
    {
        var battle = Field();
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast, kit);
        var target = battle.Deploy("Vance", Side.Player, Node(4, 0), Tardy, HexDirection.SouthWest);
        battle.Start();

        return (battle, gunner, target);
    }

    /// <summary>A sentry looking straight at a runner four hexes off, in the open.</summary>
    private static (Battle Battle, Unit Sentry, Unit Runner) Facing()
    {
        var battle = Field();
        var sentry = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Watchful, HexDirection.NorthEast);
        var runner = battle.Deploy("Vance", Side.Player, Node(4, 0), Tardy, HexDirection.SouthWest);
        battle.Start();

        return (battle, sentry, runner);
    }

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
