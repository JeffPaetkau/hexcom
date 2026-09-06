using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Xunit;

namespace Hexcom.Core.Tests;

public class BattleTests
{
    private static NodeId Node(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    private static Battle OpenField(int seed = 1, int radius = 10)
        => new(new BattleMap().FillDisc(Hex.Zero, radius), new HexLayout(size: 1.0), seed: seed);

    /// <summary>Two against two, far enough apart to have to walk at each other.</summary>
    private static Battle Skirmish(int seed = 1)
    {
        var battle = OpenField(seed);
        battle.Deploy("Vance", Side.Player, Node(-4, 0), UnitStats.Scout);
        battle.Deploy("Orsini", Side.Player, Node(-4, 1), UnitStats.Trooper);
        battle.Deploy("Sentry", Side.Hostile, Node(4, 0));
        battle.Deploy("Watchman", Side.Hostile, Node(4, -1));
        battle.Start();
        return battle;
    }

    // ---- deployment ------------------------------------------------------------

    [Fact]
    public void UnitsStartWithAFullTurnOfPoints()
    {
        var battle = OpenField();
        var unit = battle.Deploy("Vance", Side.Player, Node(0, 0), UnitStats.Scout);

        Assert.Equal(UnitStats.Scout.ActionPoints, unit.ActionPoints);
        Assert.Equal(Stance.Standing, unit.Stance);
        Assert.True(unit.InPlay);
        Assert.Equal(unit, battle.UnitAt(Node(0, 0)));
    }

    [Fact]
    public void TwoUnitsCannotBeDeployedToTheSamePlace()
    {
        var battle = OpenField();
        battle.Deploy("Vance", Side.Player, Node(0, 0));

        Assert.Throws<ArgumentException>(() => battle.Deploy("Orsini", Side.Player, Node(0, 0)));
    }

    [Fact]
    public void UnitsCannotBeDeployedWhereNobodyCanStand()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 3);
        map.AddChord(Hex.Zero, 0, 3, 0, WallProfile.Low); // bisected: crossable, not standable
        var battle = new Battle(map, new HexLayout(size: 1.0));

        Assert.Throws<ArgumentException>(() => battle.Deploy("Vance", Side.Player, Node(0, 0)));
    }

    [Fact]
    public void SidesKnowWhoTheyAreFightting()
    {
        var battle = Skirmish();
        var vance = battle.Units.First(u => u.Name == "Vance");

        Assert.Equal(2, battle.Enemies(vance).Count());
        Assert.Single(battle.Allies(vance));
        Assert.All(battle.Enemies(vance), e => Assert.Equal(Side.Hostile, e.Side));
    }

    // ---- turn order ------------------------------------------------------------

    [Fact]
    public void StartingTheBattleGivesSomebodyTheFirstTurn()
    {
        var battle = Skirmish();

        Assert.Equal(1, battle.Round);
        Assert.NotNull(battle.Active);
        Assert.True(battle.IsRunning);
    }

    [Fact]
    public void EveryoneActsOnceARoundBeforeAnyoneActsTwice()
    {
        var battle = Skirmish();
        var seen = new List<UnitId>();

        while (battle.Round == 1 && battle.Active is { } active)
        {
            seen.Add(active.Id);
            battle.EndTurn();
        }

        Assert.Equal(4, seen.Count);
        Assert.Equal(4, seen.Distinct().Count());
        Assert.Equal(2, battle.Round);
    }

    [Fact]
    public void TheOrderInterleavesTheSidesRatherThanAlternatingWholeTeams()
    {
        // Over several rounds a clock-driven order has to produce at least one run where the
        // same side acts twice running. Sides taking it in strict turns never would.
        var battle = Skirmish(seed: 7);
        var order = new List<Side>();

        for (var i = 0; i < 16 && battle.Active is { } active; i++)
        {
            order.Add(active.Side);
            battle.EndTurn();
        }

        var runs = Enumerable.Range(1, order.Count - 1).Count(i => order[i] == order[i - 1]);
        Assert.True(runs > 0, "the order never let one side act twice in a row");
        Assert.Contains(Side.Player, order);
        Assert.Contains(Side.Hostile, order);
    }

    [Fact]
    public void HeavyKitCostsYouYourPlaceInTheOrder()
    {
        // Same rolls either way, so the only difference is the rating and the encumbrance.
        var firstTurns = new List<string>();

        for (var seed = 0; seed < 40; seed++)
        {
            var battle = OpenField(seed);
            battle.Deploy("Scout", Side.Player, Node(-2, 0), UnitStats.Scout);
            battle.Deploy("Trooper", Side.Hostile, Node(2, 0), UnitStats.Trooper);
            battle.Start();
            firstTurns.Add(battle.Active!.Name);
        }

        // Scout is 14 initiative with no encumbrance against 8 less 3, so it should nearly
        // always go first, but a ten-sided roll means never say always.
        Assert.True(firstTurns.Count(n => n == "Scout") > 35, $"scout led {firstTurns.Count(n => n == "Scout")} of 40");
    }

    [Fact]
    public void TheOrderStripLooksAhead()
    {
        var battle = Skirmish();

        // Three others still to act this round, plus the active unit already booked for next.
        Assert.Equal(4, battle.TurnOrder.Count);

        var times = battle.TurnOrder.Select(s => s.ActAt).ToList();
        Assert.Equal(times.OrderBy(t => t), times);
    }

    [Fact]
    public void ASeedReplaysTheSameFight()
    {
        static List<string> Run(int seed)
        {
            var battle = Skirmish(seed);
            var names = new List<string>();
            for (var i = 0; i < 12 && battle.Active is { } active; i++)
            {
                names.Add(active.Name);
                battle.EndTurn();
            }
            return names;
        }

        Assert.Equal(Run(99), Run(99));
        Assert.NotEqual(Run(99), Run(4));
    }

    [Fact]
    public void WithdrawingCancelsABookedTurn()
    {
        var battle = Skirmish();
        var doomed = battle.Active!;

        battle.Withdraw(doomed);

        Assert.False(doomed.InPlay);
        Assert.NotEqual(doomed, battle.Active);
        Assert.DoesNotContain(battle.TurnOrder, s => s.Unit == doomed.Id);
        Assert.Equal(3, battle.InPlay.Count());
    }

    [Fact]
    public void AFightIsDecidedWhenOnlyOneSideIsLeft()
    {
        var battle = Skirmish();
        Assert.False(battle.IsDecided);

        foreach (var hostile in battle.InPlay.Where(u => u.Side == Side.Hostile).ToList())
            battle.Withdraw(hostile);

        Assert.True(battle.IsDecided);
        Assert.Equal([Side.Player], battle.SidesInPlay);
    }

    [Fact]
    public void ActingOutOfTurnIsAnError()
    {
        var battle = OpenField();
        battle.Deploy("Vance", Side.Player, Node(0, 0));

        Assert.Throws<InvalidOperationException>(() => battle.Move(Node(1, 0)));
        Assert.Throws<InvalidOperationException>(() => battle.EndTurn());
    }

    [Fact]
    public void ABattleCannotBeStartedTwice()
    {
        var battle = Skirmish();
        Assert.Throws<InvalidOperationException>(battle.Start);
    }

    // ---- moving ----------------------------------------------------------------

    [Fact]
    public void MovingSpendsExactlyWhatTheRouteCosts()
    {
        var battle = OpenField();
        var unit = battle.Deploy("Vance", Side.Player, Node(0, 0));
        battle.Start();

        var before = unit.ActionPoints;
        var outcome = battle.Move(Node(3, 0));

        Assert.True(outcome.Moved);
        Assert.Equal(3, outcome.ApSpent);
        Assert.Equal(before - 3, unit.ActionPoints);
        Assert.Equal(Node(3, 0), unit.Position);
        Assert.Equal(3, outcome.Path.Count);
    }

    [Fact]
    public void PointsRefillAtTheStartOfEachTurn()
    {
        var battle = OpenField();
        var unit = battle.Deploy("Vance", Side.Player, Node(0, 0));
        battle.Start();

        battle.Move(Node(4, 0));
        Assert.Equal(unit.Stats.ActionPoints - 4, unit.ActionPoints);

        battle.EndTurn();
        Assert.Equal(unit.Stats.ActionPoints, unit.ActionPoints);
    }

    [Fact]
    public void YouCannotWalkFurtherThanYourPointsCarryYou()
    {
        var battle = OpenField(radius: 14);
        var unit = battle.Deploy("Vance", Side.Player, Node(0, 0), UnitStats.Default);
        battle.Start();

        // Eleven hexes of open ground on ten points is one stride too many, and costs nothing
        // to be told so.
        var tooFar = battle.Move(Node(11, 0));
        Assert.False(tooFar.Moved);
        Assert.Equal("Out of reach this turn.", tooFar.Refusal);
        Assert.Equal(unit.Stats.ActionPoints, unit.ActionPoints);

        // Ten is exactly enough, and leaves nothing over.
        Assert.True(battle.Move(Node(10, 0)).Moved);
        Assert.Equal(0, unit.ActionPoints);
    }

    [Fact]
    public void YouCannotStandWhereSomebodyElseIsStanding()
    {
        var battle = OpenField();
        battle.Deploy("Vance", Side.Player, Node(0, 0));
        battle.Deploy("Orsini", Side.Player, Node(2, 0));
        battle.Start();

        var mover = battle.Active!;
        var target = mover.Name == "Vance" ? Node(2, 0) : Node(0, 0);
        var outcome = battle.Move(target);

        Assert.False(outcome.Moved);
        Assert.Contains("standing there", outcome.Refusal);
    }

    [Fact]
    public void YouCanSqueezePastAnAllyButNotThroughAnEnemy()
    {
        // A one hex wide corridor with somebody in the middle of it.
        static Battle Corridor(Side blockerSide)
        {
            var map = new BattleMap();
            for (var q = 0; q <= 4; q++) map.SetTile(new TileAddress(new Hex(q, 0), 0), 0);

            var battle = new Battle(map, new HexLayout(size: 1.0));
            battle.Deploy("Mover", Side.Player, new NodeId(new Hex(0, 0), 0));
            battle.Deploy("Blocker", blockerSide, new NodeId(new Hex(2, 0), 0));
            battle.Start();
            return battle;
        }

        var pastAlly = Corridor(Side.Player);
        var mover = pastAlly.Units.First(u => u.Name == "Mover");
        Assert.Contains(pastAlly.Destinations(mover), d => d.Node == new NodeId(new Hex(4, 0), 0));

        var pastEnemy = Corridor(Side.Hostile);
        mover = pastEnemy.Units.First(u => u.Name == "Mover");
        Assert.DoesNotContain(pastEnemy.Destinations(mover), d => d.Node == new NodeId(new Hex(4, 0), 0));
    }

    [Fact]
    public void DestinationsNeverIncludeSomewhereYouCannotStand()
    {
        var battle = Skirmish();
        var unit = battle.Active!;

        Assert.All(
            battle.Destinations(unit),
            d => Assert.True(battle.CanStopAt(unit, d.Node), $"{d.Node} is not standable"));
    }

    [Fact]
    public void MovingNowhereIsRefusedRatherThanCharged()
    {
        var battle = OpenField();
        var unit = battle.Deploy("Vance", Side.Player, Node(0, 0));
        battle.Start();

        Assert.False(battle.Move(Node(0, 0)).Moved);
        Assert.False(battle.Move(Node(50, 0)).Moved);
        Assert.Equal(unit.Stats.ActionPoints, unit.ActionPoints);
    }

    // ---- stance ----------------------------------------------------------------

    [Fact]
    public void ChangingStanceCostsAPointAndSticks()
    {
        var battle = OpenField();
        var unit = battle.Deploy("Vance", Side.Player, Node(0, 0));
        battle.Start();

        Assert.True(battle.ChangeStance(Stance.Prone));
        Assert.Equal(Stance.Prone, unit.Stance);
        Assert.Equal(unit.Stats.ActionPoints - battle.Costs.ChangeStance, unit.ActionPoints);

        // Already prone, so nothing to do and nothing to pay.
        Assert.False(battle.ChangeStance(Stance.Prone));

        // And it survives the turn ending: getting up is its own decision.
        battle.EndTurn();
        Assert.Equal(Stance.Prone, unit.Stance);
    }

    [Fact]
    public void YouCannotChangeStanceWithNothingLeft()
    {
        var battle = OpenField();
        var unit = battle.Deploy("Vance", Side.Player, Node(0, 0), UnitStats.Default);
        battle.Start();

        battle.Move(Node(10, 0)); // spends all ten
        Assert.Equal(0, unit.ActionPoints);
        Assert.False(battle.ChangeStance(Stance.Crouching));
    }

    // ---- seeing each other -----------------------------------------------------

    [Fact]
    public void UnitsSeeEachOtherAcrossOpenGround()
    {
        var battle = Skirmish();
        var vance = battle.Units.First(u => u.Name == "Vance");

        Assert.Equal(3, battle.VisibleTo(vance).Count());
        Assert.DoesNotContain(vance, battle.VisibleTo(vance));
    }

    [Fact]
    public void AWallBetweenThemHidesTheEnemy()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 6);
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Solid);
        var battle = new Battle(map, new HexLayout(size: 1.0));

        var hider = battle.Deploy("Hider", Side.Player, Node(0, 0));
        var seeker = battle.Deploy("Seeker", Side.Hostile, Node(3, 0));
        battle.Start();

        Assert.False(battle.CanSee(seeker, hider));
        Assert.Empty(battle.VisibleTo(seeker).Where(u => u == hider));
        Assert.NotNull(battle.Look(seeker, hider).Blocker);
    }

    [Fact]
    public void GoingProneBehindCoverBreaksContact()
    {
        var map = new BattleMap().FillDisc(Hex.Zero, 6);
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Low);
        var battle = new Battle(map, new HexLayout(size: 1.0));

        var hider = battle.Deploy("Hider", Side.Player, Node(0, 0));
        var seeker = battle.Deploy("Seeker", Side.Hostile, Node(3, 0));
        battle.Start();

        // Standing behind sandbags: covered, but in plain view.
        Assert.True(battle.CanSee(seeker, hider));
        Assert.Equal(CoverGrade.Half, battle.Look(seeker, hider).Cover);

        // Going prone is an action, so it has to happen on the hider's own turn.
        if (battle.Active != hider) battle.EndTurn();
        Assert.Equal(hider, battle.Active);
        Assert.True(battle.ChangeStance(Stance.Prone));

        Assert.False(battle.CanSee(seeker, hider));
    }

    [Fact]
    public void WithdrawnUnitsAreInvisibleAndUnfindable()
    {
        var battle = Skirmish();
        var vance = battle.Units.First(u => u.Name == "Vance");
        var sentry = battle.Units.First(u => u.Name == "Sentry");
        var post = sentry.Position;

        battle.Withdraw(sentry);

        Assert.DoesNotContain(sentry, battle.VisibleTo(vance));
        Assert.DoesNotContain(sentry, battle.Enemies(vance));
        Assert.Null(battle.UnitAt(post));
    }

    // ---- a whole fight ---------------------------------------------------------

    [Fact]
    public void TwoSquadsCanPlayOutSeveralRoundsWithoutTheLoopSeizingUp()
    {
        var battle = Skirmish(seed: 3);
        var turns = 0;

        while (battle.Round <= 5 && battle.Active is { } active)
        {
            // Walk at the nearest enemy, or hold if there is nobody left to walk at.
            var quarry = battle.Enemies(active)
                .OrderBy(e => active.Position.Hex.DistanceTo(e.Position.Hex))
                .FirstOrDefault();

            if (quarry is not null)
            {
                var step = battle.Destinations(active)
                    .OrderBy(d => d.Node.Hex.DistanceTo(quarry.Position.Hex))
                    .FirstOrDefault();

                if (step is not null) battle.Move(step.Node);
            }

            battle.EndTurn();
            turns++;
        }

        Assert.Equal(20, turns); // four units, five rounds
        Assert.All(battle.InPlay, u => Assert.True(battle.Graph.CanEndTurn(u.Position)));

        // Nobody ended up sharing a tile.
        Assert.Equal(battle.InPlay.Count(), battle.InPlay.Select(u => u.Position).Distinct().Count());

        // And they closed the distance rather than milling about.
        var players = battle.InPlay.Where(u => u.Side == Side.Player);
        var hostiles = battle.InPlay.Where(u => u.Side == Side.Hostile).ToList();
        Assert.All(players, p => Assert.True(
            hostiles.Min(h => p.Position.Hex.DistanceTo(h.Position.Hex)) <= 2));
    }
}
