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
/// Things that go off, and the blade that had to be settled before them. These read as the two
/// situations the straight line could never describe: something lobbed over a wall it cannot be
/// shot through, and something left on the ground with nobody standing behind it.
/// </summary>
public class OrdnanceTests
{
    private static NodeId Node(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    private static readonly UnitStats Quick = UnitStats.Default with { Initiative = 30 };
    private static readonly UnitStats Slow = UnitStats.Default with { Initiative = 1 };

    /// <summary>The price list, so these read against the economy rather than against literals.</summary>
    private static readonly MovementCosts Prices = MovementCosts.Default;

    private static Battle Field(BattleMap? map = null, int seed = 1)
        => new(map ?? new BattleMap().FillDisc(Hex.Zero, 16), new HexLayout(size: 1.0), seed: seed);

    /// <summary>A solid building face along the side of <paramref name="hex"/> facing a neighbour.</summary>
    private static void WallBetween(BattleMap map, Hex hex, Hex beyond, WallProfile? profile = null)
        => map.AddSideWall(hex, hex.DirectionTo(beyond)!.Value, 0, profile ?? WallProfile.Solid);

    /// <summary>
    /// Put a unit flat, the long way round: wait for its turn and have it drop.
    /// </summary>
    /// <remarks>
    /// Through the public API on purpose. Reaching into the unit would set a stance no soldier
    /// ever paid for, and doing it the honest way has already caught one bad test in this project.
    /// </remarks>
    private static void GoProne(Battle battle, Unit unit)
    {
        while (battle.Active != unit) battle.EndTurn();
        Assert.True(battle.ChangeStance(Stance.Prone));
        battle.EndTurn();
    }

    /// <summary>Hand turns on until it is this unit again, with a full allowance.</summary>
    private static void WaitFor(Battle battle, Unit unit)
    {
        while (battle.Active != unit) battle.EndTurn();
    }

    // ---- the blade, which had to be settled first --------------------------------

    /// <summary>
    /// Entry 008, pinned from the failing side. A two metre reach measured eye to centre of mass
    /// gets <em>longer</em> as the target gets lower, so the blade used to reach worst exactly
    /// when the target was least able to avoid it.
    /// </summary>
    [Fact]
    public void AStandingSoldierCanKnifeTheProneOneAtItsFeet()
    {
        var battle = Field();
        var knife = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Infiltrator);
        var target = battle.Deploy("Vance", Side.Player, Node(1, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        GoProne(battle, target);
        WaitFor(battle, knife);
        battle.Awareness.Observe(knife, battle.Round);

        var plan = battle.PlanShot(knife, target);

        // The measurement that used to decide this still says no, and it is no longer asked.
        Assert.True(plan.Sight.Distance > knife.Weapon.MaxRange, "the old instrument still refuses");
        Assert.True(plan.CanFire, plan.Refusal);
    }

    [Fact]
    public void ABladeReachesNothingItCannotStepTo()
    {
        var battle = Field();
        var knife = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Infiltrator);
        var far = battle.Deploy("Vance", Side.Player, Node(2, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        var plan = battle.PlanShot(knife, far);

        Assert.False(plan.CanFire);
        Assert.Equal("Not close enough to reach them.", plan.Refusal);
    }

    [Fact]
    public void ABladeDoesNotReachThroughABuildingWall()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        WallBetween(map, new Hex(0, 0), new Hex(1, 0));

        var battle = Field(map);
        var knife = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Infiltrator);
        var target = battle.Deploy("Vance", Side.Player, Node(1, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        Assert.False(battle.Adjacent(knife.Position, target.Position), "nothing crosses a building face");
        Assert.False(battle.PlanShot(knife, target).CanFire);
    }

    /// <summary>
    /// The one thing entry 008 asked to keep. You can knife somebody on a low ledge and not
    /// somebody on a roof, and now that is the graph saying so rather than an accident of metres.
    /// </summary>
    [Theory]
    [InlineData(2.0, true)]
    [InlineData(3.0, false)]
    public void ABladeReachesUpALedgeAndNotUpAStorey(double floor, bool reaches)
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        map.SetTile(new TileAddress(new Hex(1, 0), 1), floor);

        var battle = Field(map);
        var knife = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Infiltrator);
        var above = battle.Deploy("Vance", Side.Player, Node(1, 0, layer: 1), Slow, HexDirection.SouthWest);
        battle.Start();
        battle.Awareness.Observe(knife, battle.Round);

        Assert.Equal(reaches, battle.PlanShot(knife, above).CanFire);
    }

    // ---- the arc -----------------------------------------------------------------

    [Fact]
    public void WithNothingInTheWayAThrowIsFlat()
    {
        var battle = Field();
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick);
        battle.Start();

        var lob = battle.Lob.Trace(thrower.Vantage, Node(5, 0), ThrownProfile.FragGrenade.MaxArc);

        Assert.True(lob.Clears);
        Assert.Equal(0, lob.Apex);
        Assert.Equal(Node(5, 0), lob.Landing);
    }

    [Fact]
    public void AThrowOverAWallItCannotBeSeenThroughLandsWhereItWasAimed()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        WallBetween(map, new Hex(2, 0), new Hex(1, 0));

        var battle = Field(map);
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick);
        battle.Start();

        var target = Node(4, 0);
        Assert.False(battle.Sight.CanSee(thrower.Vantage, new Vantage(target)), "the wall was supposed to hide it");

        var lob = battle.Lob.Trace(thrower.Vantage, target, ThrownProfile.FragGrenade.MaxArc);

        Assert.True(lob.Clears, $"needed {lob.Required:0.0} m of arc");
        Assert.True(lob.Apex > 0, "a wall in the way has to be thrown over");
        Assert.Equal(target, lob.Landing);
    }

    /// <summary>
    /// Hugging the thing you are trying to lob over is the hard version, and it is arithmetic
    /// rather than a rule: the divisor collapses toward the ends of the throw.
    /// </summary>
    [Fact]
    public void TheSameWallCostsMoreArcTheCloserYouAreStandingToIt()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        WallBetween(map, new Hex(0, 0), new Hex(1, 0));
        WallBetween(map, new Hex(5, 0), new Hex(4, 0));

        var battle = Field(map);
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick);
        battle.Start();

        var underfoot = battle.Lob.Trace(thrower.Vantage, Node(10, 0), maxApex: 100);
        var halfway = battle.Lob.Trace(thrower.Vantage, Node(10, 0), maxApex: 100);

        // Both walls are on the same line, so the throw at the far one is the same throw with the
        // near one taken away. Compared through the shared arithmetic rather than two setups.
        var line = new Hexcom.Core.Geometry.Segment2(
            battle.Lob.Hand(thrower.Vantage).Plane, battle.Sight.Ground(Node(10, 0)).Plane);
        var crossings = battle.Sight.Crossings(line).OrderBy(c => c.Along).ToList();

        Assert.Equal(2, crossings.Count);

        var near = LobSolver.ApexToClear(crossings[0], battle.Lob.Hand(thrower.Vantage).Z, 0);
        var far = LobSolver.ApexToClear(crossings[1], battle.Lob.Hand(thrower.Vantage).Z, 0);

        Assert.True(near > far, $"{near:0.0} m against the near wall should beat {far:0.0} m against the far one");
        Assert.Equal(near, underfoot.Required, 6);
        Assert.Equal(near, halfway.Required, 6);
    }

    /// <summary>
    /// The bad outcome, and the reason a throw is worth previewing: a wall you cannot get over
    /// puts the thing on the ground at your own feet.
    /// </summary>
    [Fact]
    public void AWallTooHighForTheArmDropsTheChargeShort()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        WallBetween(map, new Hex(0, 0), new Hex(1, 0));

        var battle = Field(map);
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick);
        battle.Start();

        var lob = battle.Lob.Trace(thrower.Vantage, Node(10, 0), ThrownProfile.FragGrenade.MaxArc);

        Assert.False(lob.Clears);
        Assert.True(lob.Required > ThrownProfile.FragGrenade.MaxArc);
        Assert.Equal(WallProfile.Solid, lob.Clipped?.Profile);
        Assert.Equal(thrower.Position, lob.Landing);
    }

    // ---- the blast ---------------------------------------------------------------

    /// <summary>
    /// The whole point of the increment. A wall that stops every round stops nothing that goes
    /// over the top of it.
    /// </summary>
    [Fact]
    public void ASoldierBehindAWallThatCannotBeShotThroughIsDugOutByAGrenade()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        WallBetween(map, new Hex(2, 0), new Hex(1, 0));

        var battle = Field(map);
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Rifleman);
        var target = battle.Deploy("Vance", Side.Player, Node(4, 0), Slow, HexDirection.SouthWest, Loadout.Rifleman);
        battle.Start();

        Assert.False(battle.PlanShot(thrower, target).CanFire, "there was supposed to be no shot");

        var plan = battle.PlanThrow(thrower, target.Position);
        Assert.True(plan.CanThrow, plan.Refusal);
        Assert.True(plan.Clears);
        Assert.Contains(plan.Caught, e => e.Caught == target);

        var before = target.Vitality;
        var outcome = battle.Throw(target.Position);

        Assert.True(outcome.Went, outcome.Refusal);
        Assert.Equal(target.Position, outcome.Landing);
        Assert.True(target.Vitality < before, "the grenade was supposed to reach him");
    }

    /// <summary>
    /// The same wall, the other way round. A charge on the far side of it is a charge that did
    /// not happen to you, which is what makes lobbing one over worth the trouble.
    /// </summary>
    [Fact]
    public void AWallBetweenYouAndTheBurstTakesAllOfIt()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        WallBetween(map, new Hex(2, 0), new Hex(1, 0));

        var battle = Field(map);
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick);
        var target = battle.Deploy("Vance", Side.Player, Node(3, 0), Slow);
        battle.Start();

        // Aimed short, on the thrower side of the wall, and within the four metre radius of him.
        var short_ = Node(1, 0);
        var plan = battle.PlanThrow(thrower, short_);

        Assert.True(plan.CanThrow, plan.Refusal);
        Assert.DoesNotContain(plan.Caught, e => e.Caught == target);
    }

    /// <summary>
    /// Derived from the silhouette heights rather than dialled. A blast catches as much of a
    /// soldier as stands up into it, so a prone one — a quarter the height of a standing one —
    /// catches a quarter of the wave, and the figure moves if the stance heights ever do.
    /// </summary>
    [Fact]
    public void GoingFlatQuartersWhatAChargeDoesToYou()
    {
        Assert.Equal(
            StanceProfile.Prone.BodyHeight / StanceProfile.Standing.BodyHeight,
            Ordnance.StanceShare(Stance.Prone),
            6);

        var battle = Field();
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick);
        var target = battle.Deploy("Vance", Side.Player, Node(2, 0), Slow);
        battle.Start();

        var upright = battle.PlanThrow(thrower, target.Position).Caught.Single(e => e.Caught == target);

        GoProne(battle, target);
        WaitFor(battle, thrower);

        var flat = battle.PlanThrow(thrower, target.Position).Caught.Single(e => e.Caught == target);

        // Near a quarter rather than exactly one: a man on his face has his centre of mass nearer
        // the ground, so he is fractionally nearer a charge lying on it, and the falloff notices.
        Assert.InRange(flat.Share / upright.Share, 0.2, 0.35);
        Assert.True(flat.Arriving < upright.Arriving);
    }

    /// <summary>
    /// The two families again, and the ordering flips exactly where it should. Fragmentation is
    /// kinetic, so a force shield barely notices it and plate eats it; a shaped charge is beam,
    /// so the shield eats it and plate does not. Which one to carry is a question about the enemy.
    /// </summary>
    [Fact]
    public void WhichChargeToThrowDependsEntirelyOnWhatTheyAreWearing()
    {
        var battle = Field();
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Rifleman);
        var shielded = battle.Deploy("Vance", Side.Player, Node(2, 0), Slow, HexDirection.SouthWest, Loadout.Beamer);
        var armoured = battle.Deploy("Rusk", Side.Player, Node(-2, 0), Slow, HexDirection.NorthEast, Loadout.Heavy);
        battle.Start();

        double Against(Unit victim, ThrownProfile charge)
            => battle
                .PlanThrow(thrower, victim.Position, charge, [BlastCandidate.At(victim)])
                .Caught.Single()
                .Expectation.Vitality;

        // Ten points of shield and three of plate: the fragments walk straight through.
        Assert.True(
            Against(shielded, ThrownProfile.FragGrenade) > Against(shielded, ThrownProfile.PlasmaCharge),
            "fragments beat a shield");

        // Fourteen points of plate and eight of shield: the fragments stop dead and the beam does not.
        Assert.True(
            Against(armoured, ThrownProfile.PlasmaCharge) > Against(armoured, ThrownProfile.FragGrenade),
            "a shaped charge beats plate");
    }

    /// <summary>
    /// Heard from the crater, not from the hand. A grenade is the one way in this game to make a
    /// great deal of noise somewhere you are not standing.
    /// </summary>
    [Fact]
    public void TheBangIsHeardWhereItLandedRatherThanWhereItWasThrownFrom()
    {
        var battle = Field();
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Rifleman);
        var listener = battle.Deploy("Vance", Side.Player, Node(10, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        var crater = Node(6, 0);
        Assert.True(battle.Throw(crater).Went);

        var contact = battle.Awareness.Of(listener.Id, thrower.Id);

        Assert.True(contact.Detection > 0, "an explosion is not quiet");

        // And what he learned is wrong, deliberately. He marks the man who threw it at the crater,
        // which is ten metres from where the man is standing.
        Assert.Equal(crater, contact.LastKnownPosition);
        Assert.NotEqual(thrower.Position, contact.LastKnownPosition);
    }

    [Fact]
    public void AChargeThrownIsAChargeGone()
    {
        var battle = Field();
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Rifleman);
        battle.Deploy("Vance", Side.Player, Node(6, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        var carried = thrower.ThrownLeft;
        Assert.True(carried > 0);

        for (var i = 0; i < carried; i++) Assert.True(battle.Throw(Node(3, 0)).Went);

        Assert.Equal(0, thrower.ThrownLeft);

        var empty = battle.PlanThrow(thrower, Node(3, 0));
        Assert.False(empty.CanThrow);
    }

    // ---- what the scorer makes of one --------------------------------------------

    /// <summary>
    /// The only action in the game that can be worth a negative number because of who else was
    /// standing there.
    /// </summary>
    [Fact]
    public void AChargeThatWouldCatchYourOwnSquadScoresAgainstYou()
    {
        var battle = Field();
        var thrower = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Rifleman);
        var mate = battle.Deploy("Ordell", Side.Hostile, Node(5, 0), Slow, HexDirection.NorthEast, Loadout.Rifleman);
        var target = battle.Deploy("Vance", Side.Player, Node(6, 0), Slow, HexDirection.SouthWest, Loadout.Rifleman);
        battle.Start();

        var alone = battle.PlanThrow(thrower, target.Position, against: [BlastCandidate.At(target)]);
        var together = battle.PlanThrow(thrower, target.Position);

        Assert.Contains(together.Caught, e => e.Caught == mate && e.Friendly);
        Assert.True(
            battle.Tactics.Worth(together) < battle.Tactics.Worth(alone),
            "catching one of your own is a cost, not a rounding error");
    }

    /// <summary>
    /// A charge is the first thing in this game that runs out, so spending one has to cost
    /// something the points cannot express.
    /// </summary>
    [Fact]
    public void NobodyThrowsAChargeAtSomebodyTheyCouldSimplyShoot()
    {
        var battle = Field();
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Rifleman);
        battle.Deploy("Vance", Side.Player, Node(4, 0), Slow, HexDirection.SouthWest, Loadout.Rifleman);
        battle.Start();
        battle.Awareness.Observe(gunner, battle.Round);

        var commander = new Commander(battle);
        var threats = commander.Judge.Known(gunner).ToList();
        var options = commander.Options(gunner, threats).ToList();

        var throws = options.Where(o => o.Kind == OrderKind.Throw).ToList();
        var shots = options.Where(o => o.Kind == OrderKind.Fire).ToList();

        Assert.NotEmpty(throws);
        Assert.NotEmpty(shots);

        // The grenade does more, and the rifle does nearly as much for nothing. Take the rifle.
        Assert.True(throws.Max(o => o.Worth.Harm) > shots.Max(o => o.Worth.Harm));
        Assert.True(shots.Max(o => o.Score) > throws.Max(o => o.Score));
    }

    /// <summary>
    /// And the other half of the same figure: with no shot to be had, the charge comes off the
    /// belt. Aimed at a place, so it may be aimed at a remembered one.
    /// </summary>
    [Fact]
    public void AChargeIsWorthSpendingOnSomebodyWhoCannotBeShotAtAll()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        WallBetween(map, new Hex(2, 0), new Hex(1, 0));

        var battle = Field(map);
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Rifleman);
        var hidden = battle.Deploy("Vance", Side.Player, Node(4, 0), Slow, HexDirection.SouthWest, Loadout.Rifleman);
        battle.Start();

        // Two noises put him on the map without putting him in view.
        for (var i = 0; i < 2; i++) battle.Awareness.Hear(hidden, 200, battle.Round);

        var commander = new Commander(battle);
        var threats = commander.Judge.Known(gunner).ToList();

        Assert.Contains(threats, t => t.Unit == hidden && !t.EyesOn);

        var best = commander.Next();

        Assert.NotNull(best);
        Assert.Equal(OrderKind.Throw, best!.Kind);
        Assert.Equal(hidden.Position, best.Throw!.Aimed);
    }

    // ---- mines -------------------------------------------------------------------

    /// <summary>
    /// A mine is an overwatch nobody is standing behind: same window, same clock, and it fires at
    /// the tick the foot lands rather than at the end of the move.
    /// </summary>
    [Fact]
    public void AMineFiresOnTheMoverAtTheTickItStepsOnTheTile()
    {
        var (battle, mover, mine) = Mined(Node(2, 0));

        var before = mover.Vitality;
        var outcome = battle.Move(Node(4, 0));

        Assert.True(outcome.Moved, outcome.Refusal);

        var went = Assert.Single(outcome.Reactions!.Detonations);

        Assert.Same(mine, went.Mine);
        Assert.Equal(mine.Node, went.Caught);

        // Two strides in, priced off the list rather than off a literal.
        Assert.Equal(2 * Prices.Walk, went.At);
        Assert.True(mover.Vitality < before, "the mine was supposed to catch him");
    }

    /// <summary>
    /// The thing an overwatch cannot do. Nobody is watching, nobody has a reserve, and the ground
    /// answers anyway.
    /// </summary>
    [Fact]
    public void AMineAnswersAMoveOutOfNobodyReserve()
    {
        var (battle, mover, _) = Mined(Node(2, 0), removeLayer: true);

        var outcome = battle.Move(Node(4, 0));

        Assert.Empty(outcome.Reactions!.Offers);
        Assert.Single(outcome.Reactions.Detonations);
        Assert.True(mover.Vitality < mover.Stats.Vitality);
    }

    [Fact]
    public void AMineDoesNotGoOffUnderTheSideThatLaidIt()
    {
        var battle = Field();
        var sapper = battle.Deploy("Kessel", Side.Hostile, Node(2, 0), Quick, HexDirection.NorthEast, Loadout.Infiltrator);
        var mate = battle.Deploy("Ordell", Side.Hostile, Node(0, 0), Slow, HexDirection.NorthEast, Loadout.Infiltrator);
        battle.Deploy("Vance", Side.Player, Node(12, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        Assert.Same(sapper, battle.Active);
        Assert.True(battle.LayMine());
        Assert.True(battle.Move(Node(3, 0)).Moved);
        battle.EndTurn();

        WaitFor(battle, mate);

        var outcome = battle.Move(Node(2, 0));

        Assert.True(outcome.Moved, outcome.Refusal);
        Assert.Empty(outcome.Reactions!.Detonations);
        Assert.Equal(mate.Stats.Vitality, mate.Vitality);
    }

    [Fact]
    public void AMineWorksOnce()
    {
        var (battle, first, mine) = Mined(Node(2, 0));

        Assert.True(battle.Move(Node(4, 0)).Moved);
        Assert.True(mine.Spent);
        Assert.DoesNotContain(mine, battle.Mines);

        battle.EndTurn();
        WaitFor(battle, first);

        var again = battle.Move(Node(2, 0));

        Assert.True(again.Moved, again.Refusal);
        Assert.Empty(again.Reactions!.Detonations);
    }

    /// <summary>The interface half of contract 3: your own charges, and nobody else.</summary>
    [Fact]
    public void EachSideIsOnlyEverShownTheChargesItLaidItself()
    {
        var (battle, _, mine) = Mined(Node(2, 0));

        Assert.Contains(mine, battle.MinesOf(Side.Hostile));
        Assert.Empty(battle.MinesOf(Side.Player));
    }

    // ---- shouting, which the scorer could price and nobody could do ---------------

    [Fact]
    public void AUnitCanCallAContactInOnItsOwnTurn()
    {
        var battle = Field();
        var spotter = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast);
        var mate = battle.Deploy("Ordell", Side.Hostile, Node(1, 0), Slow, HexDirection.NorthEast);
        var seen = battle.Deploy("Vance", Side.Player, Node(4, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        battle.Awareness.Observe(spotter, battle.Round);

        var held = battle.Awareness.Of(spotter.Id, seen.Id);
        Assert.True(held.State >= AwarenessState.Searching, "the spotter was supposed to have him");

        var theirs = battle.Awareness.Of(mate.Id, seen.Id).Detection;
        var points = spotter.ActionPoints;

        Assert.True(battle.Shout(seen));

        Assert.Equal(spotter.Stats.Costs.Posturing(Prices.Shout), points - spotter.ActionPoints);
        Assert.True(battle.Awareness.Of(mate.Id, seen.Id).Detection > theirs, "word was supposed to travel");
    }

    [Fact]
    public void ThereIsNothingToCallInAboutSomebodyYouHaveNotNoticed()
    {
        var battle = Field();
        var spotter = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick);
        var stranger = battle.Deploy("Vance", Side.Player, Node(14, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(spotter.Id, stranger.Id).State);
        Assert.False(battle.Shout(stranger));
        Assert.Equal(spotter.Stats.ActionPoints, spotter.ActionPoints);
    }

    // ---- setting up --------------------------------------------------------------

    /// <summary>
    /// A hostile sapper lays a charge, steps off it, and a player unit is up with a full turn and
    /// a route across it.
    /// </summary>
    /// <param name="removeLayer">
    /// Take the sapper out of the fight afterwards, so that nobody on that side has a reserve, an
    /// arc or a line — which is how a mine gets tested as a thing the terrain does rather than a
    /// thing a soldier does.
    /// </param>
    private static (Battle Battle, Unit Mover, Mine Mine) Mined(NodeId at, bool removeLayer = false)
    {
        var battle = Field();
        var sapper = battle.Deploy("Kessel", Side.Hostile, at, Quick, HexDirection.NorthEast, Loadout.Infiltrator);
        var mover = battle.Deploy("Vance", Side.Player, Node(0, 0), Slow, HexDirection.NorthEast);
        battle.Start();

        Assert.Same(sapper, battle.Active);
        Assert.True(battle.LayMine());

        var mine = Assert.Single(battle.Mines);

        // Off the charge, so there is somewhere for the mover to step.
        Assert.True(battle.Move(new NodeId(at.Hex.Neighbor(HexDirection.North), at.Layer)).Moved);

        battle.EndTurn();
        WaitFor(battle, mover);

        if (removeLayer) battle.Withdraw(sapper);

        Assert.Equal(mover.Stats.ActionPoints, mover.ActionPoints);
        return (battle, mover, mine);
    }
}
