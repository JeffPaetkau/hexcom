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

        var threats = commander.Judge.Seen(gunner).ToList();
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
            .Options(gunner, commander.Judge.Seen(gunner).ToList())
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

    // ---- what the arithmetic says about arcs --------------------------------------

    [Fact]
    public void DeclaringAnArcIsOfferedAndPricedOnTheShotItBuys()
    {
        var (battle, gunner, _) = Contact(Node(4, 0));
        var commander = new Commander(battle);

        var arcs = commander
            .Options(gunner, commander.Judge.Seen(gunner).ToList())
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
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast);
        var target = battle.Deploy("Vance", Side.Player, Node(4, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        for (var i = 0; i < 12 && battle.Awareness.Of(gunner.Id, target.Id).State < AwarenessState.Searching; i++)
            battle.EndTurn();

        while (battle.Active != gunner) battle.EndTurn();

        return (battle, gunner, target);
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
