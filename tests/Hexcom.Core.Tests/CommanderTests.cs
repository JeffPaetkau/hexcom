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
/// A soldier taking its own turn. These read as decisions: what was on the table, what got picked
/// out of it, and why the one that got picked was the one that was worth most.
/// </summary>
public class CommanderTests
{
    private static NodeId Node(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    private static readonly UnitStats Quick = UnitStats.Default with { Initiative = 30 };
    private static readonly UnitStats Slow = UnitStats.Default with { Initiative = 1 };

    /// <summary>
    /// The standard rifleman with an empty grenade pouch.
    /// </summary>
    /// <remarks>
    /// Used wherever the situation is one a grenade answers — somebody behind cover, somebody
    /// heard round a corner — and the behaviour under test is not the grenade. A commander given
    /// a charge and a man behind a wall throws it, which is correct and is asserted in
    /// <see cref="OrdnanceTests"/>; here it would mean a test named after flanking that quietly
    /// stopped exercising the flank. One mechanism per situation.
    /// </remarks>
    private static readonly Loadout Barehanded = Loadout.Rifleman with { Charges = 0 };

    private static Battle Field(BattleMap? map = null, int seed = 1)
        => new(map ?? new BattleMap().FillDisc(Hex.Zero, 16), new HexLayout(size: 1.0), seed: seed);

    // ---- knowing nothing ---------------------------------------------------------

    [Fact]
    public void ASoldierWhoKnowsAboutNobodyDoesNothingAtAll()
    {
        var battle = Field();
        var alone = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast);
        battle.Deploy("Vance", Side.Player, Node(12, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        Assert.Same(alone, battle.Active);
        Assert.Empty(new Commander(battle).TakeTurn());

        // Standing still is not nothing: the whole turn goes into the reserve, which is what a
        // soldier with no idea where anybody is ought to be doing with it.
        Assert.Equal(battle.Reactions.Banked(alone.Stats.ActionPoints), alone.Reserve);
    }

    /// <summary>
    /// A turn taken one decision at a time is the same turn, and it ends when the caller says
    /// so rather than when the commander runs out of things to do — which is what lets an
    /// instrument stand between two decisions and ask what the second was chosen over.
    /// </summary>
    [Fact]
    public void ATurnCanBeTakenOneDecisionAtATimeAndEndsWhenTheCallerSaysSo()
    {
        var (battle, gunner, target) = Contact(Node(4, 0));

        var commander = new Commander(battle);
        var expected = commander.Next();
        Assert.NotNull(expected);

        var first = commander.Step();
        Assert.NotNull(first);
        Assert.Equal(expected!.Kind, first!.Kind);
        Assert.Same(gunner, battle.Active);

        var taken = new List<Act> { first };
        while (commander.Step() is { } more) taken.Add(more);

        Assert.Same(gunner, battle.Active);
        Assert.Equal(taken, commander.Taken);
        Assert.Null(commander.Next());

        battle.EndTurn();
        Assert.Same(target, battle.Active);
    }

    // ---- knowing something -------------------------------------------------------

    [Fact]
    public void ASoldierWithAClearShotTakesIt()
    {
        var (battle, gunner, target) = Contact(Node(4, 0));

        var orders = new Commander(battle).TakeTurn();

        Assert.Contains(orders, o => o.Kind == OrderKind.Fire);
        Assert.True(target.Vitality < target.Stats.Vitality || gunner.ActionPoints == 0);
    }

    [Fact]
    public void ASoldierWhoseTargetIsInCoverGoesRoundItRatherThanShootingThroughIt()
    {
        var (battle, gunner, target) = Screened();
        var commander = new Commander(battle);

        Assert.NotEqual(CoverGrade.None, battle.Sight.Trace(gunner.Vantage, target.Vantage).Cover);

        var threats = commander.Judge.Known(gunner).ToList();
        var options = commander.Options(gunner, threats).ToList();

        var here = options.Where(o => o.Kind == OrderKind.Fire).Max(o => o.Worth.Harm);
        var flank = options.Where(o => o.Kind == OrderKind.Move).MaxBy(o => o.Score)!;

        // Nobody wrote down that flanking beats firing through a wall. The sight trace reports
        // less of the target behind the sandbags and the arithmetic does the rest.
        Assert.True(flank.Opens!.Value.Harm > here, $"{flank.Opens.Value.Harm:0.00} should beat {here:0.00}");

        var orders = commander.TakeTurn();
        Assert.Equal(OrderKind.Move, orders[0].Kind);
        Assert.Contains(orders, o => o.Kind == OrderKind.Fire);
    }

    [Fact]
    public void AMoveIsRankedOnTheShotItOpensRatherThanOnTheWalk()
    {
        var (battle, gunner, _) = Screened();
        var commander = new Commander(battle);

        var moves = commander
            .Options(gunner, commander.Judge.Known(gunner).ToList())
            .Where(o => o.Kind == OrderKind.Move)
            .ToList();

        Assert.NotEmpty(moves);

        var taken = moves.MaxBy(o => o.Score)!;

        // Walking is not an achievement. The step costs points and leaves the gunner standing
        // somewhere marginally worse; all of what makes it worth doing is at the other end of it.
        Assert.True(taken.Worth.Score < 0, $"the step itself is a cost, not {taken.Worth}");
        Assert.True(taken.Opens!.Value.Harm > 0, "and it is taken for the shot it opens");
        Assert.True(taken.Score > 0);
    }

    [Fact]
    public void SomebodyWithNothingWorthDoingHoldsTheGroundAndTheirPoints()
    {
        // A blade carrier twenty-two metres from a runner it cannot reach this turn, whose
        // slug rifle can reach it perfectly well. Walking into that is worse than standing still.
        var (battle, blade, _) = Contact(Node(13, 0), kit: Loadout.Infiltrator);

        var orders = new Commander(battle).TakeTurn();

        Assert.DoesNotContain(orders, o => o.Kind == OrderKind.Fire);
        Assert.Equal(battle.Reactions.Banked(blade.Stats.ActionPoints), blade.Reserve);
    }

    // ---- going to look -------------------------------------------------------------

    [Fact]
    public void ASoldierWhoHeardSomethingGoesToLookWhereItCameFrom()
    {
        var (battle, kessel, vance) = RoundTheCorner();
        var commander = new Commander(battle);

        var marker = battle.Awareness.Of(kessel.Id, vance.Id);
        Assert.Equal(AwarenessState.Searching, marker.State);
        Assert.False(marker.EyesOn);
        Assert.Equal(vance.Position, marker.LastKnownPosition);

        var orders = commander.TakeTurn();

        // Round the corner to somewhere the place the noise came from can be seen — and not a
        // shot fired, because there is nothing to shoot at yet, only somewhere to look.
        Assert.Equal(OrderKind.Move, orders[0].Kind);
        Assert.DoesNotContain(orders, o => o.Kind == OrderKind.Fire);
        Assert.True(
            battle.Sight.CanSee(kessel.Vantage, new Vantage(marker.LastKnownPosition!.Value, Stance.Standing)),
            $"{kessel.Position} cannot see the marker at {marker.LastKnownPosition}");

        // The look at the end of the turn found him where the noise said, and the next turn is
        // an ordinary one against somebody in plain view.
        Assert.True(battle.Awareness.Of(kessel.Id, vance.Id).EyesOn);

        while (battle.Active != kessel) battle.EndTurn();
        Assert.Contains(commander.TakeTurn(), o => o.Kind == OrderKind.Fire);
    }

    [Fact]
    public void NobodyShootsAtAPlaceTheyHaveNotLookedAt()
    {
        // A marker in the open, and the man it belongs to standing exactly there in plain view.
        // The gunner has not looked since, and until it does the marker is all it holds.
        var battle = Field();
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast);
        var target = battle.Deploy("Vance", Side.Player, Node(4, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        for (var i = 0; i < 2; i++) battle.Awareness.Hear(target, 200, battle.Round);

        Assert.True(battle.CanSee(gunner, target), "the setup wants him in view and unlooked-at");
        Assert.False(battle.Awareness.Of(gunner.Id, target.Id).EyesOn);

        var commander = new Commander(battle);
        var threats = commander.Judge.Known(gunner).ToList();
        var threat = Assert.Single(threats);
        Assert.False(threat.EyesOn);

        // The shot is there for the taking, geometrically. Taking it would mean the battle
        // resolving the gunner's guess against where the man really is, which is the battle
        // aiming for him.
        Assert.True(battle.PlanShot(gunner, target).CanFire);
        Assert.DoesNotContain(commander.Options(gunner, threats), o => o.Kind == OrderKind.Fire);

        // One look later it is a target rather than a marker, and the shot is on the table.
        commander.TakeTurn();
        while (battle.Active != gunner) battle.EndTurn();

        Assert.True(commander.Judge.Known(gunner).Single().EyesOn);
        Assert.Contains(commander.Options(gunner, commander.Judge.Known(gunner).ToList()), o => o.Kind == OrderKind.Fire);
    }

    [Fact]
    public void AMarkerIsFreshForTwoRoundsAndHalvesEveryRoundAfter()
    {
        var judge = Field().Tactics;

        // The subject may not have had a turn yet at one round; from two it certainly has.
        Assert.Equal(1.0, judge.Credence(0));
        Assert.Equal(1.0, judge.Credence(1));
        Assert.Equal(judge.Model.MarkerDecay, judge.Credence(2));
        Assert.Equal(judge.Model.MarkerDecay * judge.Model.MarkerDecay, judge.Credence(3), 9);
    }

    [Fact]
    public void AStaleMarkerIsWorthGoingToLookAtInProportionToTheChanceHeIsStillThere()
    {
        var (battle, kessel, vance) = RoundTheCorner();
        var fresh = battle.Tactics.Known(kessel).Single();

        // The same belief, older: every reason to go there scales with the credence, so the
        // shot the position would open and the look it would buy both come down together.
        var stale = fresh with { Credence = 0.25 };
        var vantage = Node(3, -2);
        var arriving = new UnitPose(vantage, kessel.Stance, battle.HeadingTo(vantage, vance.Position));

        Assert.True(battle.Sight.CanSee(arriving.Vantage, fresh.Where.Vantage));
        Assert.Equal(0.25 * battle.Tactics.BestShot(kessel, arriving, fresh), battle.Tactics.BestShot(kessel, arriving, stale), 9);

        var freshWalk = battle.Tactics.AppraisePosture(kessel, arriving, 15, [fresh]);
        var staleWalk = battle.Tactics.AppraisePosture(kessel, arriving, 15, [stale]);
        Assert.True(staleWalk.Prospect < freshWalk.Prospect, $"{staleWalk} should promise less than {freshWalk}");
        Assert.True(staleWalk.Spared > freshWalk.Spared, "and a man who is probably gone is less to fear");
    }

    [Fact]
    public void TwoSidesThatStartOutOfContactFindEachOtherAndFight()
    {
        // Three a side either side of a wall, nobody in view of anybody. Something loud happens
        // on the far side — a dropped crate, a slammed door — and that is all either side is
        // ever told.
        //
        // The wall is five hexes long, and that is not incidental: the far end of it is about as
        // far as a soldier will walk to look at a fresh marker. Past five hexes or so the walk
        // costs more than the one discounted shot the look might open, and a search one step
        // deep cannot see the turn of shooting beyond that — the same limit that keeps a blade
        // carrier from crossing open ground. A longer wall here is a stalemate, and it is a
        // limit of the search rather than of the beliefs.
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        Barrier(map, 3, -2, 2);
        var battle = Field(map);

        // Nobody carries a charge, because the thing under test is the hunt. Given one, the side
        // that heard something lobs it over the barrier at the noise instead of walking round —
        // which is right, and is asserted where it belongs, in OrdnanceTests.
        for (var i = 0; i < 3; i++)
        {
            battle.Deploy($"Red {i}", Side.Hostile, Node(0, i - 1), UnitStats.Default, HexDirection.NorthEast, Barehanded);
            battle.Deploy($"Blue {i}", Side.Player, Node(5, i - 1), UnitStats.Default, HexDirection.SouthWest, Barehanded);
        }

        battle.Start();

        var reds = battle.InPlay.Where(u => u.Side == Side.Hostile).ToList();
        var blues = battle.InPlay.Where(u => u.Side == Side.Player).ToList();
        Assert.All(reds, red => Assert.All(blues, blue => Assert.False(battle.CanSee(red, blue))));

        for (var i = 0; i < 2; i++) battle.Awareness.Hear(blues[0], 200, battle.Round);

        var commander = new Commander(battle);
        var walkedBeforeTheFirstShot = new System.Collections.Generic.HashSet<Unit>();
        var shots = 0;
        var turns = 0;

        while (battle.IsRunning && !battle.IsDecided && turns++ < 400)
        {
            var mover = battle.Active!;
            var orders = commander.TakeTurn();

            var fired = orders.Count(o => o.Kind == OrderKind.Fire);
            if (shots == 0 && fired == 0 && orders.Any(o => o.Kind == OrderKind.Move)) walkedBeforeTheFirstShot.Add(mover);
            shots += fired;
        }

        // The side that heard something went and looked before a shot was fired by anybody.
        // Who fires first is then a matter of turn order: the looker looks at the end of its
        // turn, and so does the man it found, and whichever of them comes round first shoots.
        // Going to look costs a turn, and that turn is the window the found soldier is owed.
        Assert.True(shots > 0, "nobody ever fired");
        Assert.Contains(reds, walkedBeforeTheFirstShot.Contains);
        Assert.DoesNotContain(blues, walkedBeforeTheFirstShot.Contains);

        // And it was a fight rather than an ambush: both sides took losses.
        Assert.Contains(reds, red => !red.InPlay);
        Assert.Contains(blues, blue => !blue.InPlay);

        // What is deliberately not asserted is that it was decided. Traced with this seed, the
        // last two standing lose contact eight hexes apart, their markers decay, and neither will
        // walk that far to old news — a search one step deep cannot value an approach that takes
        // two turns, so a fight that loses contact is a stalemate. That is the search's limit,
        // recorded in core.md, and the reason the objective system is the next thing an AI needs.
    }

    // ---- what the arithmetic says about arcs --------------------------------------

    [Fact]
    public void DeclaringAnArcIsOfferedAndPricedOnTheShotItBuys()
    {
        var (battle, gunner, _) = Contact(Node(4, 0));
        var commander = new Commander(battle);

        var arcs = commander
            .Options(gunner, commander.Judge.Known(gunner).ToList())
            .Where(o => o.Kind == OrderKind.Overwatch)
            .ToList();

        Assert.NotEmpty(arcs);

        // Declaring costs points and does nothing this turn. All of its value is in the reserve
        // it leaves and the bonus that reserve now shoots at.
        Assert.All(arcs, o => Assert.True(o.Worth.Score < 0));
        Assert.Contains(arcs, o => o.Opens!.Value.Prospect > 0);

        var narrow = arcs.Where(o => o.Arc == OverwatchArc.Narrow).MaxBy(o => o.Score)!;
        var wide = arcs.Where(o => o.Arc == OverwatchArc.Wide).MaxBy(o => o.Score)!;
        Assert.True(narrow.Score > wide.Score, "a narrow arc shoots better down the ground it covers");
    }

    // ---- both sides at once -------------------------------------------------------

    [Fact]
    public void TwoSidesRunByTheSameJudgementFightToADecision()
    {
        var battle = Skirmish();
        var commander = new Commander(battle);

        var turns = 0;
        while (battle.IsRunning && !battle.IsDecided && turns++ < 400) commander.TakeTurn();

        Assert.True(battle.IsDecided, $"still undecided after {turns} turns");
        Assert.True(turns < 400, "it should not have needed the cap");

        // Somebody won it, and they did it by shooting rather than by the clock running out.
        var standing = battle.InPlay.ToList();
        Assert.NotEmpty(standing);
        Assert.Single(standing.Select(u => u.Side).Distinct());
    }

    [Fact]
    public void TheSameSeedFightsTheSameFightTwice()
    {
        static string Play()
        {
            var battle = Skirmish(seed: 7);
            var commander = new Commander(battle);

            var log = new System.Text.StringBuilder();
            var turns = 0;

            while (battle.IsRunning && !battle.IsDecided && turns++ < 400)
                foreach (var order in commander.TakeTurn())
                    log.Append(order).Append('\n');

            return log.ToString();
        }

        // The whole point of one seeded generator. If a match cannot be replayed there is no
        // such thing as running thousands of them and comparing the results.
        Assert.Equal(Play(), Play());
    }

    // ---- scaffolding ---------------------------------------------------------------

    /// <summary>
    /// A hostile who has already had a look round, and a player unit it now knows about. The
    /// hostile is up, with a full turn in hand.
    /// </summary>
    private static (Battle Battle, Unit Gunner, Unit Target) Contact(NodeId at, Loadout? kit = null)
    {
        var battle = Field();
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, kit);
        var target = battle.Deploy("Vance", Side.Player, at, Slow, HexDirection.SouthWest);
        battle.Start();

        // Looking is what a turn ends with, so it takes a round to come back round to the
        // hostile with a contact in hand and its allowance refilled — and more than one round if
        // they are far enough off that a single look does not settle it.
        for (var i = 0; i < 12 && battle.Awareness.Of(gunner.Id, target.Id).State < AwarenessState.Searching; i++)
            battle.EndTurn();

        while (battle.Active != gunner) battle.EndTurn();

        Assert.Same(gunner, battle.Active);
        Assert.Equal(gunner.Stats.ActionPoints, gunner.ActionPoints);
        Assert.True(
            battle.Awareness.Of(gunner.Id, target.Id).State >= AwarenessState.Searching,
            "the setup depends on the gunner having noticed them");

        return (battle, gunner, target);
    }

    /// <summary>
    /// A gunner with a sight screen across the front of its own hex, and a target it knows about
    /// on the far side of it. One step clear of the screen opens the shot.
    /// </summary>
    /// <remarks>
    /// A screen rather than a wall because it has to block the line without blocking the walk —
    /// otherwise the setup tests whether the gunner can path round a building rather than whether
    /// it will take a step for a shot. Knowing about somebody you cannot see is ordinary: the
    /// contact is built up before the screen goes between them.
    /// </remarks>
    private static (Battle Battle, Unit Gunner, Unit Target) Screened()
    {
        // A knee-high wall across the face the gunner is looking at, so the target is in cover
        // from straight ahead and in the open from anywhere off the line.
        var facing = new Hex(4, 0).DirectionTo(new Hex(3, 0))!.Value;
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        map.AddSideWall(new Hex(4, 0), facing, 0, WallProfile.Low);

        var battle = Field(map);
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Barehanded);
        var target = battle.Deploy("Vance", Side.Player, Node(4, 0), Slow, HexDirection.SouthWest, Barehanded);
        battle.Start();

        for (var i = 0; i < 12 && battle.Awareness.Of(gunner.Id, target.Id).State < AwarenessState.Searching; i++)
            battle.EndTurn();

        while (battle.Active != gunner) battle.EndTurn();

        return (battle, gunner, target);
    }

    /// <summary>
    /// A solid wall along one flank of the hexes at <paramref name="q"/>, from one row to
    /// another: two sides per hex, so the line has no gaps in it.
    /// </summary>
    private static void Barrier(BattleMap map, int q, int rFrom, int rTo)
    {
        for (var r = rFrom; r <= rTo; r++)
        {
            var hex = new Hex(q, r);
            foreach (var beyond in new[] { new Hex(q - 1, r), new Hex(q - 1, r + 1) })
                map.AddSideWall(hex, hex.DirectionTo(beyond)!.Value, 0, WallProfile.Solid);
        }
    }

    /// <summary>
    /// A hostile with a wall between it and a player unit it has never seen, and a noise from
    /// the far side loud enough to be worth investigating. The hostile is up, with a full turn.
    /// </summary>
    private static (Battle Battle, Unit Kessel, Unit Vance) RoundTheCorner()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 16);
        Barrier(map, 3, -2, 2);

        var battle = Field(map);
        var kessel = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast, Barehanded);
        var vance = battle.Deploy("Vance", Side.Player, Node(5, 0), Slow, HexDirection.SouthWest, Barehanded);
        battle.Start();

        Assert.Same(kessel, battle.Active);
        Assert.False(battle.CanSee(kessel, vance), "the wall was supposed to hide them");

        // One noise makes a sentry suspicious; it takes a second to send him looking.
        for (var i = 0; i < 2; i++) battle.Awareness.Hear(vance, 200, battle.Round);

        return (battle, kessel, vance);
    }

    /// <summary>Three a side in the open, everybody in view of everybody, nobody in cover.</summary>
    private static Battle Skirmish(int seed = 1)
    {
        var battle = Field(seed: seed);

        for (var i = 0; i < 3; i++)
        {
            battle.Deploy($"Red {i}", Side.Hostile, Node(-5, i - 1), UnitStats.Default, HexDirection.NorthEast);
            battle.Deploy($"Blue {i}", Side.Player, Node(5, i - 1), UnitStats.Default, HexDirection.SouthWest);
        }

        battle.Start();
        return battle;
    }
}
