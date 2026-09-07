using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Xunit;

namespace Hexcom.Core.Tests;

public class CombatTests
{
    private static NodeId Node(int q, int r) => new(new Hex(q, r), 0);

    private static Battle Field(int seed = 1, BattleMap? map = null)
        => new(map ?? new BattleMap().FillDisc(Hex.Zero, 20), new HexLayout(size: 1.0), seed: seed);

    /// <summary>A shooter at the origin and a target a few hexes north-east, both facing each other.</summary>
    private static (Battle Battle, Unit Shooter, Unit Target) Duel(
        Loadout shooterKit,
        Loadout targetKit,
        int range = 4,
        int seed = 1,
        BattleMap? map = null)
    {
        var battle = Field(seed, map);
        var shooter = battle.Deploy("Shooter", Side.Player, Node(0, 0), facing: HexDirection.NorthEast, loadout: shooterKit);
        var target = battle.Deploy("Target", Side.Hostile, Node(range, 0), facing: HexDirection.SouthWest, loadout: targetKit);
        battle.Start();

        while (battle.Active != shooter) battle.EndTurn();
        return (battle, shooter, target);
    }

    // ---- working out the odds --------------------------------------------------

    [Fact]
    public void AClearShotAtOptimalRangeIsAGoodOne()
    {
        var (battle, shooter, target) = Duel(Loadout.Rifleman, Loadout.Rifleman);
        var plan = battle.PlanShot(shooter, target);

        Assert.True(plan.CanFire);
        Assert.Null(plan.Refusal);
        Assert.InRange(plan.HitChance, 0.7, 0.95);
        Assert.Equal(FireMode.Standard, plan.Mode);
    }

    [Fact]
    public void PlanningAShotChangesNothing()
    {
        var (battle, shooter, target) = Duel(Loadout.Rifleman, Loadout.Rifleman);
        var before = shooter.ActionPoints;

        battle.PlanShot(shooter, target, FireMode.Aimed);
        battle.PlanShot(shooter, target, FireMode.Snap);

        Assert.Equal(before, shooter.ActionPoints);
        Assert.Equal(target.Stats.Vitality, target.Vitality);
    }

    [Fact]
    public void TakingYourTimeShootsBetterAndSnappingShootsWorse()
    {
        var (battle, shooter, target) = Duel(Loadout.Rifleman, Loadout.Rifleman);

        var snap = battle.PlanShot(shooter, target, FireMode.Snap);
        var standard = battle.PlanShot(shooter, target, FireMode.Standard);
        var aimed = battle.PlanShot(shooter, target, FireMode.Aimed);

        Assert.True(snap.HitChance < standard.HitChance);
        Assert.True(standard.HitChance < aimed.HitChance);

        // And the better shot is the slower one, which is the whole trade in a reaction window.
        Assert.True(snap.ApCost < standard.ApCost);
        Assert.True(standard.ApCost < aimed.ApCost);
    }

    [Fact]
    public void AccuracyHoldsToOptimalRangeThenFallsAway()
    {
        var gunnery = new Gunnery();
        var weapon = WeaponProfile.SlugRifle;

        Assert.Equal(1.0, gunnery.RangeFactor(weapon, 5), 6);
        Assert.Equal(1.0, gunnery.RangeFactor(weapon, weapon.OptimalRange), 6);
        Assert.True(gunnery.RangeFactor(weapon, 35) < 1.0);
        Assert.Equal(gunnery.Model.LongRangeFloor, gunnery.RangeFactor(weapon, weapon.MaxRange), 6);
        Assert.Equal(gunnery.Model.LongRangeFloor, gunnery.RangeFactor(weapon, 500), 6);
    }

    [Fact]
    public void CoverMakesYouHarderToHitTwiceOver()
    {
        var open = Duel(Loadout.Rifleman, Loadout.Rifleman);

        var walled = new BattleMap().FillDisc(Hex.Zero, 20);
        walled.AddSideWall(new Hex(4, 0), HexDirection.SouthWest, 0, WallProfile.Low);
        var behind = Duel(Loadout.Rifleman, Loadout.Rifleman, map: walled);

        var exposed = open.Battle.PlanShot(open.Shooter, open.Target);
        var covered = behind.Battle.PlanShot(behind.Shooter, behind.Target);

        // Less of them is showing, and what is showing is being used well.
        Assert.True(covered.Sight.Exposure < exposed.Sight.Exposure);
        Assert.Equal(CoverGrade.Half, covered.Sight.Cover);
        Assert.True(covered.HitChance < exposed.HitChance * 0.7);
    }

    [Fact]
    public void GoingProneSteadiesYourAim()
    {
        var (battle, shooter, target) = Duel(Loadout.Rifleman, Loadout.Rifleman);
        var standing = battle.PlanShot(shooter, target).HitChance;

        Assert.True(battle.ChangeStance(Stance.Prone));
        Assert.True(battle.PlanShot(shooter, target).HitChance > standing);
    }

    [Fact]
    public void ShotsAreRefusedWithAReasonRatherThanSilently()
    {
        var walled = new BattleMap().FillDisc(Hex.Zero, 20);
        walled.AddSideWall(new Hex(4, 0), HexDirection.SouthWest, 0, WallProfile.Solid);

        var hidden = Duel(Loadout.Rifleman, Loadout.Rifleman, map: walled);
        Assert.Contains("No line", hidden.Battle.PlanShot(hidden.Shooter, hidden.Target).Refusal);

        var faraway = Duel(Loadout.Sidearm, Loadout.Rifleman, range: 18);
        Assert.Contains("Out of range", faraway.Battle.PlanShot(faraway.Shooter, faraway.Target).Refusal);

        var battle = Field();
        var shooter = battle.Deploy("Shooter", Side.Player, Node(0, 0), facing: HexDirection.NorthEast);
        var mate = battle.Deploy("Mate", Side.Player, Node(2, 0));
        var enemy = battle.Deploy("Enemy", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        battle.Start();
        while (battle.Active != shooter) battle.EndTurn();

        Assert.Contains("Pick somebody else", battle.PlanShot(shooter, shooter).Refusal);
        Assert.Contains("one of ours", battle.PlanShot(shooter, mate).Refusal);

        battle.Move(Node(0, 8)); // spends most of the turn
        Assert.Contains("Needs", battle.PlanShot(shooter, enemy, FireMode.Aimed).Refusal);
    }

    [Fact]
    public void AWeaponWillNotFireAModeItDoesNotHave()
    {
        var (battle, shooter, target) = Duel(Loadout.Infiltrator, Loadout.Rifleman, range: 1);
        Assert.Contains("cannot fire", battle.PlanShot(shooter, target, FireMode.Aimed).Refusal);
        Assert.True(battle.PlanShot(shooter, target, FireMode.Strike).CanFire);
    }

    // ---- what stops what -------------------------------------------------------

    [Fact]
    public void ShieldsStopBeamsAndBarelyNoticeSlugs()
    {
        var shieldOnly = new Loadout(WeaponProfile.Sidearm, ShieldPerFace: 20, ArmourPerFace: 0);

        var beam = new Protection(shieldOnly).Absorb(BodyFace.Front, DamageKind.Beam, 10);
        Assert.Equal(10, beam.StoppedByShield);
        Assert.Equal(0, beam.ToVitality);

        var slug = new Protection(shieldOnly).Absorb(BodyFace.Front, DamageKind.Kinetic, 10);
        Assert.Equal(2, slug.StoppedByShield); // fifteen per cent, rounded
        Assert.Equal(8, slug.ToVitality);
    }

    [Fact]
    public void PlateStopsSlugsAndCooksUnderABeam()
    {
        var plateOnly = new Loadout(WeaponProfile.Sidearm, ShieldPerFace: 0, ArmourPerFace: 20);

        var slug = new Protection(plateOnly).Absorb(BodyFace.Front, DamageKind.Kinetic, 10);
        Assert.Equal(10, slug.StoppedByArmour);
        Assert.Equal(0, slug.ToVitality);

        var beam = new Protection(plateOnly).Absorb(BodyFace.Front, DamageKind.Beam, 10);
        Assert.Equal(3, beam.StoppedByArmour); // a quarter, rounded
        Assert.Equal(7, beam.ToVitality);
    }

    [Fact]
    public void PlateAblatesAndShieldsComeBack()
    {
        var protection = new Protection(new Loadout(WeaponProfile.Sidearm, ShieldPerFace: 6, ArmourPerFace: 10, ShieldRecharge: 2));
        var face = BodyFace.FrontLeft;

        protection.Absorb(face, DamageKind.Kinetic, 12);
        var armourAfter = protection.ArmourOn(face);
        var shieldAfter = protection.ShieldOn(face);

        Assert.True(armourAfter < 10, "plate did not ablate");
        Assert.True(shieldAfter < 6);

        protection.Recharge();
        Assert.Equal(shieldAfter + 2, protection.ShieldOn(face));
        Assert.Equal(armourAfter, protection.ArmourOn(face)); // plate does not come back
    }

    [Fact]
    public void EachFaceIsProtectedSeparately()
    {
        var protection = new Protection(Loadout.Beamer);
        protection.Absorb(BodyFace.Front, DamageKind.Beam, 40);

        Assert.Equal(0, protection.ShieldOn(BodyFace.Front));
        Assert.Equal(Loadout.Beamer.ShieldPerFace, protection.ShieldOn(BodyFace.Rear));
        Assert.Single(protection.BareFaces);
    }

    [Fact]
    public void WalkingRoundASoldierNamesEachSideOfThemInTurn()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Hostile, Node(0, 0), facing: HexDirection.NorthEast);
        battle.Start();

        // The target is looking north-east, so a shooter out along that spoke is dead in front
        // and the rest fall away to either side of it.
        var expected = new[]
        {
            (HexDirection.NorthEast, BodyFace.Front),
            (HexDirection.North, BodyFace.FrontLeft),
            (HexDirection.NorthWest, BodyFace.RearLeft),
            (HexDirection.SouthWest, BodyFace.Rear),
            (HexDirection.South, BodyFace.RearRight),
            (HexDirection.SouthEast, BodyFace.FrontRight),
        };

        foreach (var (direction, face) in expected)
        {
            var shooter = new Unit(new UnitId(99), "Ghost", Side.Player, new NodeId(direction.Offset() * 4, 0));
            Assert.Equal(face, battle.FaceToward(target, shooter));
        }
    }

    [Fact]
    public void TurningRoundPresentsADifferentPlateToTheSameShooter()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Hostile, Node(0, 0), facing: HexDirection.NorthEast);
        var shooter = battle.Deploy("Shooter", Side.Player, Node(4, 0), facing: HexDirection.SouthWest);
        battle.Start();

        // Faces are the soldier's own sides, not compass points. Nobody moves here; the target
        // simply looks somewhere else, and a different plate is now the one in the way.
        var pose = UnitPose.Of(target);

        Assert.Equal(BodyFace.Front, Squarest(pose));
        Assert.Equal(BodyFace.FrontRight, Squarest(pose with { Facing = HexDirection.North }));
        Assert.Equal(BodyFace.Rear, Squarest(pose with { Facing = HexDirection.SouthWest }));

        BodyFace Squarest(UnitPose looking) => battle.FacesPresentedTo(looking, shooter.Position)[0].Face;
    }

    [Fact]
    public void WalkingRoundTheBackFindsTheSpentSide()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Hostile, Node(0, 0), facing: HexDirection.NorthEast, loadout: Loadout.Beamer);
        var front = battle.Deploy("Front", Side.Player, Node(4, 0), facing: HexDirection.SouthWest, loadout: Loadout.Beamer);
        var behind = battle.Deploy("Behind", Side.Player, Node(-4, 0), facing: HexDirection.NorthEast, loadout: Loadout.Beamer);
        battle.Start();

        // Burn the shield off the side they are looking over.
        target.Protection.Absorb(BodyFace.Front, DamageKind.Beam, 40);

        Assert.Equal(BodyFace.Front, battle.FaceToward(target, front));
        Assert.Equal(BodyFace.Rear, battle.FaceToward(target, behind));

        Assert.Equal(0, target.Protection.ShieldOn(battle.FaceToward(target, front)));
        Assert.True(target.Protection.ShieldOn(battle.FaceToward(target, behind)) > 0);

        // And the payoff of tracking sides by body: turning about swaps which of them is exposed,
        // so a soldier whose front is gone can put a fresh plate between itself and the threat.
        var turned = UnitPose.Of(target) with { Facing = HexDirection.SouthWest };

        Assert.True(target.Protection.ShieldOn(Squarest(turned, front.Position)) > 0);
        Assert.Equal(0, target.Protection.ShieldOn(Squarest(turned, behind.Position)));

        BodyFace Squarest(UnitPose looking, NodeId from) => battle.FacesPresentedTo(looking, from)[0].Face;
    }

    // ---- which of the six a round actually finds -------------------------------

    [Fact]
    public void StandingInFrontOfSomebodyShowsYouThreeOfTheirSides()
    {
        var aspects = BodyFaces.Presented(0);

        // A hexagon met head-on is one full face and a shoulder either side, foreshortened to
        // half the width each. Half the rounds find the front plate, a quarter each shoulder.
        Assert.Equal(3, aspects.Count);
        Assert.Equal(BodyFace.Front, aspects[0].Face);
        Assert.Equal(0.50, aspects[0].Share, 6);
        Assert.Equal(0.0, aspects[0].ObliquityDegrees, 6);

        Assert.Equal(
            new[] { BodyFace.FrontLeft, BodyFace.FrontRight },
            aspects.Skip(1).Select(a => a.Face).ToArray());
        Assert.All(aspects.Skip(1), a => Assert.Equal(0.25, a.Share, 6));
        Assert.All(aspects.Skip(1), a => Assert.Equal(60.0, a.ObliquityDegrees, 6));
    }

    [Fact]
    public void StandingTowardsACornerShowsYouTwoSidesEqually()
    {
        var aspects = BodyFaces.Presented(30);

        // Thirty degrees off is a corner, so the two faces meeting at it are equally awkward and
        // the other four are edge-on or hidden. This is the boundary case: cos of ninety degrees
        // is not quite zero in floating point, and without slack it becomes a sliver you can hit.
        Assert.Equal(2, aspects.Count);
        Assert.Equal(
            new[] { BodyFace.Front, BodyFace.FrontLeft },
            aspects.Select(a => a.Face).ToArray());
        Assert.All(aspects, a => Assert.Equal(0.5, a.Share, 6));
        Assert.All(aspects, a => Assert.Equal(30.0, a.ObliquityDegrees, 6));
    }

    [Fact]
    public void WhicheverWayYouComeAtThemTheSharesAddUp()
    {
        for (var angle = -180; angle <= 180; angle += 7)
        {
            var aspects = BodyFaces.Presented(angle);

            Assert.InRange(aspects.Count, 2, 3);
            Assert.Equal(1.0, aspects.Sum(a => a.Share), 6);
            Assert.All(aspects, a => Assert.InRange(a.ObliquityDegrees, 0, 90));
        }
    }

    [Fact]
    public void ASlugSkipsOffAPlateItMeetsAtAnAngleAndABeamDoesNot()
    {
        var gunnery = new Gunnery();

        Assert.Equal(1.0, gunnery.GlancingFactor(DamageKind.Kinetic, 0), 6);
        Assert.True(gunnery.GlancingFactor(DamageKind.Kinetic, 60) < 1.0);
        Assert.True(gunnery.GlancingFactor(DamageKind.Kinetic, 90)
                    < gunnery.GlancingFactor(DamageKind.Kinetic, 60));

        // A beam lands wherever it lands and burns. The angle of the surface is not its problem.
        Assert.All(
            new[] { 0.0, 30.0, 60.0, 90.0 },
            a => Assert.Equal(1.0, gunnery.GlancingFactor(DamageKind.Beam, a), 6));
    }

    [Fact]
    public void WhichBearingYouComeFromDecidesWhichPlateWearsAndNotHowMuchGetsThrough()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Hostile, Node(0, 0), facing: HexDirection.NorthEast);

        // Both sit the same distance from the target and carry the same rifle. The only
        // difference is the bearing: (4,0) is straight down the way the target is looking, and
        // (2,2) is sixty degrees round from it, which puts a corner in the way.
        var square = battle.Deploy("Square", Side.Player, Node(4, 0), facing: HexDirection.SouthWest);
        var oblique = battle.Deploy("Oblique", Side.Player, Node(2, 2), facing: HexDirection.SouthWest);
        battle.Start();

        var headOn = battle.PlanShot(square, target);
        var cornerOn = battle.PlanShot(oblique, target);

        // The geometry still differs, and that is the part worth having: one shot can find three
        // plates and the other only two, so where you stand decides which sides get worn.
        Assert.Equal(3, headOn.Aspects.Count);
        Assert.Equal(2, cornerOn.Aspects.Count);
        Assert.NotEqual(
            headOn.Aspects.Select(a => a.Face).ToArray(),
            cornerOn.Aspects.Select(a => a.Face).ToArray());

        // What must not differ is how much damage you expect to do. A hexagon is bookkeeping for
        // which plate wears, not a claim that soldiers are hexagonal, so the bearing you happen
        // to approach the abstraction from is worth nothing either way.
        Assert.Equal(headOn.GlancingFactor, cornerOn.GlancingFactor, 6);
        Assert.Equal(headOn.ExpectedDamage, cornerOn.ExpectedDamage, 6);
    }

    [Fact]
    public void ARoundStillSkipsOffAShoulderEvenThoughTheAverageIsFlat()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Hostile, Node(0, 0), facing: HexDirection.NorthEast);
        var shooter = battle.Deploy("Shooter", Side.Player, Node(4, 0), facing: HexDirection.SouthWest);
        battle.Start();

        var plan = battle.PlanShot(shooter, target);
        var weapon = plan.Weapon;

        // Flattening the average does not flatten the individual hits. Catch them square in the
        // chest and the round arrives whole; clip a shoulder and it skips.
        var square = battle.Gunnery.DamageAt(weapon, 0, plan.GlancingScale);
        var shoulder = battle.Gunnery.DamageAt(weapon, 60, plan.GlancingScale);

        Assert.Equal(DamageKind.Kinetic, weapon.Kind);
        Assert.True(shoulder < square, $"shoulder {shoulder} should be under square {square}");
    }

    // ---- placing a round deliberately ------------------------------------------

    /// <summary>Someone who has learned to put a round where they mean to.</summary>
    private static readonly UnitStats Marksman = UnitStats.Default with { CanCallShots = true };

    [Fact]
    public void AnOrdinarySoldierShootsAtAManAndNotAtAPlate()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        var shooter = battle.Deploy("Shooter", Side.Player, Node(0, 0), facing: HexDirection.NorthEast);
        battle.Start();
        while (battle.Active != shooter) battle.EndTurn();

        var plan = battle.PlanShot(shooter, target, FireMode.Standard, BodyFace.FrontLeft);

        Assert.False(plan.CanFire);
        Assert.Contains("cannot place a round", plan.Refusal);
    }

    [Fact]
    public void AMarksmanPicksThePlateAndPaysForItInAccuracy()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        var shooter = battle.Deploy("Shooter", Side.Player, Node(0, 0), Marksman, HexDirection.NorthEast);
        battle.Start();
        while (battle.Active != shooter) battle.EndTurn();

        var loose = battle.PlanShot(shooter, target, FireMode.Standard);
        var called = battle.PlanShot(shooter, target, FireMode.Standard, BodyFace.FrontLeft);

        Assert.True(called.CanFire);
        Assert.True(called.IsCalledShot);
        Assert.Equal(BodyFace.FrontLeft, called.LikeliestFace);
        Assert.True(called.HitChance < loose.HitChance);

        // And the round goes where it was sent rather than where the geometry would have put it.
        var outcome = battle.Fire(target, FireMode.Standard, BodyFace.FrontLeft);
        Assert.All(
            outcome.Shots.Where(s => s.Hit),
            s => Assert.Equal(BodyFace.FrontLeft, s.Damage!.Face));
    }

    [Fact]
    public void YouCannotCallAPlateThatIsNotInView()
    {
        var battle = Field();
        var target = battle.Deploy("Target", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
        var shooter = battle.Deploy("Shooter", Side.Player, Node(0, 0), Marksman, HexDirection.NorthEast);
        battle.Start();
        while (battle.Active != shooter) battle.EndTurn();

        // They are facing the shooter, so their back is not something anyone out front can name.
        var plan = battle.PlanShot(shooter, target, FireMode.Standard, BodyFace.Rear);

        Assert.False(plan.CanFire);
        Assert.Contains("not in view", plan.Refusal);
    }

    // ---- pulling the trigger ---------------------------------------------------

    [Fact]
    public void FiringSpendsThePointsAndRollsAgainstThePlan()
    {
        var (battle, shooter, target) = Duel(Loadout.Rifleman, Loadout.Rifleman);
        var before = shooter.ActionPoints;

        var outcome = battle.Fire(target, FireMode.Standard);

        Assert.True(outcome.Fired);
        Assert.Equal(FireMode.Standard.ApCost, outcome.ApSpent);
        Assert.Equal(before - FireMode.Standard.ApCost, shooter.ActionPoints);
        Assert.Single(outcome.Shots);
    }

    [Fact]
    public void ABurstSendsSeveralRoundsAndResolvesEachOne()
    {
        var (battle, shooter, target) = Duel(Loadout.Heavy, Loadout.Rifleman, range: 3);
        var outcome = battle.Fire(target, FireMode.Burst);

        Assert.True(outcome.Fired);
        Assert.True(outcome.Shots.Count is >= 1 and <= 3);
        Assert.All(outcome.Shots, s => Assert.InRange(s.Roll, 0, 1));
    }

    [Fact]
    public void ARefusedShotCostsNothing()
    {
        var walled = new BattleMap().FillDisc(Hex.Zero, 20);
        walled.AddSideWall(new Hex(4, 0), HexDirection.SouthWest, 0, WallProfile.Solid);
        var (battle, shooter, target) = Duel(Loadout.Rifleman, Loadout.Rifleman, map: walled);

        var before = shooter.ActionPoints;
        var outcome = battle.Fire(target);

        Assert.False(outcome.Fired);
        Assert.Equal(before, shooter.ActionPoints);
        Assert.Equal(target.Stats.Vitality, target.Vitality);
    }

    [Fact]
    public void EnoughHitsTakeSomebodyOutOfTheFight()
    {
        // No protection at all, so every round tells.
        var naked = new Loadout(WeaponProfile.SlugRifle, ShieldPerFace: 0, ArmourPerFace: 0);
        var battle = Field(seed: 4);
        var shooter = battle.Deploy("Shooter", Side.Player, Node(0, 0), facing: HexDirection.NorthEast, loadout: naked);
        var target = battle.Deploy("Target", Side.Hostile, Node(2, 0), facing: HexDirection.SouthWest, loadout: naked);
        battle.Start();

        for (var round = 0; round < 20 && target.InPlay; round++)
        {
            while (battle.Active != shooter && battle.IsRunning) battle.EndTurn();
            if (!battle.IsRunning) break;

            while (shooter.ActionPoints >= FireMode.Snap.ApCost && target.InPlay)
                battle.Fire(target, FireMode.Snap);

            if (target.InPlay) battle.EndTurn();
        }

        Assert.False(target.InPlay);
        Assert.True(target.IsDown);
        Assert.Null(battle.UnitAt(Node(2, 0)));
    }

    [Fact]
    public void TheSameSeedFightsTheSameFight()
    {
        static int DamageDone(int seed)
        {
            var (battle, _, target) = Duel(Loadout.Heavy, Loadout.Rifleman, range: 3, seed: seed);
            var start = target.Vitality;
            battle.Fire(target, FireMode.Burst);
            return start - target.Vitality;
        }

        Assert.Equal(DamageDone(11), DamageDone(11));
    }

    // ---- what firing tells everyone --------------------------------------------

    [Fact]
    public void BeingShotAtSettlesTheQuestionOfWhetherAnybodyIsOutThere()
    {
        var (battle, shooter, target) = Duel(Loadout.Rifleman, Loadout.Rifleman, range: 8);
        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(target.Id, shooter.Id).State);

        battle.Fire(target, FireMode.Snap);

        Assert.True(battle.Awareness.Of(target.Id, shooter.Id).State >= AwarenessState.Alerted);
        Assert.Equal(shooter.Position, battle.Awareness.Of(target.Id, shooter.Id).LastKnownPosition);
    }

    [Fact]
    public void ASlugthrowerIsHeardThroughAWallAndABeamIsNot()
    {
        // A third party round the corner: no sight of either combatant, and far enough from the
        // one being shot at that no shout reaches them either. So the only channel left open is
        // the weapon's own signature, which is the thing under test.
        static double NoticedBy(Loadout kit)
        {
            var map = new BattleMap().FillDisc(Hex.Zero, 20);
            map.AddSideWall(new Hex(-2, 0), HexDirection.SouthWest, 0, WallProfile.Solid);

            var battle = new Battle(map, new HexLayout(size: 1.0), seed: 2);
            var shooter = battle.Deploy("Shooter", Side.Player, Node(0, 0), facing: HexDirection.NorthEast, loadout: kit);
            var target = battle.Deploy("Target", Side.Hostile, Node(4, 0), facing: HexDirection.SouthWest);
            var listener = battle.Deploy("Listener", Side.Hostile, Node(-9, 0), facing: HexDirection.SouthWest);
            battle.Start();

            Assert.False(battle.CanSee(listener, shooter), "the listener should be round the corner from the shooter");
            Assert.False(battle.CanSee(listener, target), "the listener should be round the corner from the target");

            var apart = Hexcom.Core.Geometry.Vec3.GroundDistance(
                battle.Sight.Ground(listener.Position), battle.Sight.Ground(target.Position));
            Assert.True(apart > battle.Awareness.Model.VoiceRangeMetres, "the target could shout to the listener");

            while (battle.Active != shooter) battle.EndTurn();
            battle.Fire(target, FireMode.Snap);

            return battle.Awareness.Of(listener.Id, shooter.Id).Detection;
        }

        Assert.True(NoticedBy(Loadout.Rifleman) > 0, "a slug rifle went unheard through a wall");
        Assert.Equal(0, NoticedBy(Loadout.Beamer));
    }

    [Fact]
    public void ABeamGivesYouAwayToWhoeverIsLookingYourWay()
    {
        // The flash channel on its own, with nobody being shot at to shout about it. Two
        // onlookers the same distance away, one facing the shooter and one turned away.
        var battle = Field(seed: 3);
        var shooter = battle.Deploy("Shooter", Side.Player, Node(0, 0), facing: HexDirection.NorthEast, loadout: Loadout.Beamer);
        var watching = battle.Deploy("Watching", Side.Hostile, Node(0, 5), facing: HexDirection.South);
        var turnedAway = battle.Deploy("TurnedAway", Side.Hostile, Node(0, -5), facing: HexDirection.South);
        battle.Start();

        battle.Awareness.Reveal(shooter, WeaponProfile.PulseCarbine.Flash, battle.Round);

        var seen = battle.Awareness.Of(watching.Id, shooter.Id).Detection;
        var missed = battle.Awareness.Of(turnedAway.Id, shooter.Id).Detection;

        Assert.True(seen > 0, "the flash was not noticed by somebody looking straight at it");
        Assert.True(seen > missed * 4, $"facing barely mattered: {seen:0.0} against {missed:0.0}");
    }

    [Fact]
    public void ABladeLeavesNothingForABystanderToNotice()
    {
        // A bystander round the corner and out of shouting range of the victim, so the only way
        // they could learn anything is from the weapon itself.
        var map = new BattleMap().FillDisc(Hex.Zero, 20);
        map.AddSideWall(new Hex(-2, 0), HexDirection.SouthWest, 0, WallProfile.Solid);

        var battle = new Battle(map, new HexLayout(size: 1.0), seed: 6);
        var killer = battle.Deploy("Killer", Side.Player, Node(0, 0), facing: HexDirection.NorthEast, loadout: Loadout.Infiltrator);
        var victim = battle.Deploy("Victim", Side.Hostile, Node(1, 0), facing: HexDirection.NorthEast);
        var bystander = battle.Deploy("Bystander", Side.Hostile, Node(-9, 0), facing: HexDirection.SouthWest);
        battle.Start();

        Assert.False(battle.CanSee(bystander, killer));

        while (battle.Active != killer) battle.EndTurn();
        var outcome = battle.Fire(victim, FireMode.Strike);

        Assert.True(outcome.Fired);
        Assert.Equal(0, WeaponProfile.PowerBlade.Loudness);
        Assert.Equal(0, battle.Awareness.Of(bystander.Id, killer.Id).Detection);

        // The victim, on the other hand, is in no doubt about it.
        Assert.True(battle.Awareness.Of(victim.Id, killer.Id).State >= AwarenessState.Alerted);
    }
}
