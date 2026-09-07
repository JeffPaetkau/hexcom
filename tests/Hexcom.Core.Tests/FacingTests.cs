using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// Facing decides how readily something is noticed, never whether it could be seen at all.
/// Line of sight stays pure geometry; attention is a question about people.
/// </summary>
public class FacingTests
{
    private static NodeId Node(int q, int r) => new(new Hex(q, r), 0);

    private static Battle Field(int seed = 1)
        => new(new BattleMap().FillDisc(Hex.Zero, 14), new HexLayout(size: 1.0), seed: seed);

    /// <summary>
    /// One sentry at the origin looking whichever way, one intruder four hexes north-east.
    /// </summary>
    private static (Battle Battle, Unit Sentry, Unit Intruder) Watch(HexDirection facing)
    {
        var battle = Field();
        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(0, 0), facing: facing);
        var intruder = battle.Deploy("Intruder", Side.Player, Node(4, 0));
        battle.Start();
        return (battle, sentry, intruder);
    }

    // ---- the arcs --------------------------------------------------------------

    [Fact]
    public void SomethingDeadAheadHasTheSentryFullAttention()
    {
        var (battle, sentry, intruder) = Watch(HexDirection.NorthEast);
        Assert.Equal(1.0, battle.Awareness.AttentionOn(sentry, intruder.Position), 6);
        Assert.True(battle.Awareness.IsWatching(sentry, intruder.Position));
    }

    [Fact]
    public void OneSpokeRoundIsStillTheCornerOfAnEye()
    {
        // Neighbouring spokes are sixty degrees apart, right on the edge of a hundred and
        // twenty degree front arc, so a target one spoke over sits just outside it.
        var (battle, sentry, intruder) = Watch(HexDirection.North);
        var attention = battle.Awareness.AttentionOn(sentry, intruder.Position);

        // The arithmetic that gets here lands on 60.00000000000001, not 60, so which side of the
        // edge this falls is a decision the model has to make rather than one the floating point
        // makes for it. The edge belongs to the wider arc, and this is where that is pinned.
        Assert.Equal(60.0, battle.AngleOffDegrees(sentry.Position, sentry.Facing, intruder.Position), 6);
        Assert.Equal(battle.Awareness.Model.PeripheralAcuity, attention, 6);
        Assert.False(battle.Awareness.IsWatching(sentry, intruder.Position));
    }

    [Fact]
    public void JustInsideTheEdgeOfTheFrontArcHasFullAttention()
    {
        // Forty degrees off, which is inside the cone by any reading. The pair of these says the
        // boundary is decided deliberately rather than by whichever way the rounding fell.
        var battle = Field();
        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(0, 0), facing: HexDirection.NorthEast);
        battle.Start();

        var justInside = Node(1, 2);
        Assert.InRange(battle.AngleOffDegrees(sentry.Position, sentry.Facing, justInside), 40, 42);
        Assert.Equal(1.0, battle.Awareness.AttentionOn(sentry, justInside), 6);
    }

    [Fact]
    public void TurningYourBackNearlyBlindsYouToIt()
    {
        var (battle, sentry, intruder) = Watch(HexDirection.SouthWest);
        Assert.Equal(battle.Awareness.Model.RearAcuity, battle.Awareness.AttentionOn(sentry, intruder.Position), 6);
    }

    [Fact]
    public void AttentionNeverDependsOnLineOfSight()
    {
        // A building wall between them changes what can be seen, not where they are looking.
        var map = new BattleMap().FillDisc(Hex.Zero, 14);
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Solid);
        var battle = new Battle(map, new HexLayout(size: 1.0));

        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(0, 0), facing: HexDirection.NorthEast);
        var intruder = battle.Deploy("Intruder", Side.Player, Node(4, 0));
        battle.Start();

        Assert.False(battle.CanSee(sentry, intruder));
        Assert.Equal(1.0, battle.Awareness.AttentionOn(sentry, intruder.Position), 6);
    }

    // ---- what it does to detection ---------------------------------------------

    [Fact]
    public void ComingAtASentryFromBehindBuysYouAgesLongerUnnoticed()
    {
        static double AfterOneLook(HexDirection facing)
        {
            var (battle, sentry, intruder) = Watch(facing);
            battle.Awareness.Observe(sentry, battle.Round);
            return battle.Awareness.Of(sentry.Id, intruder.Id).Detection;
        }

        var ahead = AfterOneLook(HexDirection.NorthEast);
        var corner = AfterOneLook(HexDirection.North);
        var behind = AfterOneLook(HexDirection.SouthWest);

        Assert.True(ahead > corner);
        Assert.True(corner > behind);

        // The whole point of the walk round the back: an order of magnitude, not a rounding.
        Assert.True(ahead / Math.Max(behind, 0.001) > 8, $"ahead {ahead:0.0} against behind {behind:0.0}");
    }

    [Fact]
    public void WalkingInFrontOfASentryGetsYouFoundWhileTheSameWalkBehindDoesNot()
    {
        static AwarenessState AfterThreeLooks(HexDirection facing)
        {
            var (battle, sentry, intruder) = Watch(facing);
            for (var i = 0; i < 3; i++) battle.Awareness.Observe(sentry, battle.Round);
            return battle.Awareness.Of(sentry.Id, intruder.Id).State;
        }

        Assert.True(AfterThreeLooks(HexDirection.NorthEast) >= AwarenessState.Alerted);
        Assert.Equal(AwarenessState.Unaware, AfterThreeLooks(HexDirection.SouthWest));
    }

    [Fact]
    public void APositionIsOnlyFlankableBecauseAUnitCanLookOneWay()
    {
        // Two intruders on opposite spokes. Whichever the sentry watches, the other is safe.
        var battle = Field();
        var sentry = battle.Deploy("Sentry", Side.Hostile, Node(0, 0), facing: HexDirection.NorthEast);
        var infront = battle.Deploy("InFront", Side.Player, Node(4, 0));
        var behind = battle.Deploy("Behind", Side.Player, Node(-4, 0));
        battle.Start();

        battle.Awareness.Observe(sentry, battle.Round);
        battle.Awareness.Observe(sentry, battle.Round);

        Assert.True(battle.Awareness.Of(sentry.Id, infront.Id).State >= AwarenessState.Searching);
        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(sentry.Id, behind.Id).State);
    }

    // ---- setting it ------------------------------------------------------------

    [Fact]
    public void MovingLeavesYouLookingWhereYouWereGoing()
    {
        var battle = Field();
        var unit = battle.Deploy("Runner", Side.Player, Node(0, 0), facing: HexDirection.South);
        battle.Start();

        Assert.True(battle.Move(Node(0, 3)).Moved);
        Assert.Equal(HexDirection.North, unit.Facing);

        battle.EndTurn();
        while (battle.Active != unit) battle.EndTurn();

        Assert.True(battle.Move(Node(3, 3)).Moved);
        Assert.Equal(HexDirection.NorthEast, unit.Facing);
    }

    [Fact]
    public void TurningOnTheSpotCostsAPointAndSticksUntilYouMove()
    {
        var battle = Field();
        var unit = battle.Deploy("Watcher", Side.Player, Node(0, 0), facing: HexDirection.NorthEast);
        battle.Start();

        Assert.True(battle.Face(HexDirection.SouthWest));
        Assert.Equal(HexDirection.SouthWest, unit.Facing);
        Assert.Equal(unit.Stats.ActionPoints - battle.Costs.TurnInPlace, unit.ActionPoints);

        // Already looking that way, so nothing to do and nothing to pay.
        Assert.False(battle.Face(HexDirection.SouthWest));

        battle.EndTurn();
        Assert.Equal(HexDirection.SouthWest, unit.Facing);
    }

    [Fact]
    public void YouCannotTurnWithNothingLeft()
    {
        var battle = Field();
        var unit = battle.Deploy("Runner", Side.Player, Node(0, 0), UnitStats.Default);
        battle.Start();

        battle.Move(Node(10, 0)); // spends all ten
        Assert.Equal(0, unit.ActionPoints);
        Assert.False(battle.Face(HexDirection.South));
    }

    [Fact]
    public void VaultingWithinOneHexDoesNotSpinYouRound()
    {
        // Two tiles, the second split by a barricade, so the last step of the route stays put.
        var map = new BattleMap();
        for (var q = -1; q <= 1; q++) map.SetTile(new TileAddress(new Hex(q, 0), 0), 0);
        map.AddChord(new Hex(0, 0), 0, 3, 0, WallProfile.Low);

        var battle = new Battle(map, new HexLayout(size: 1.0));
        var unit = battle.Deploy("Vaulter", Side.Player, Node(-1, 0), facing: HexDirection.South);
        battle.Start();

        Assert.True(battle.Move(Node(1, 0)).Moved);

        // The route crossed the barricade inside the middle hex, but the heading comes from the
        // last step that actually changed hex.
        Assert.Equal(HexDirection.NorthEast, unit.Facing);
    }

    [Fact]
    public void FacingSurvivesTheGridBeingDrawnRotated()
    {
        // Rendering pointy-top rotates the whole plane; the logic must not notice.
        static double Attention(double rotation)
        {
            var battle = new Battle(
                new BattleMap().FillDisc(Hex.Zero, 8),
                new HexLayout(size: 1.0, rotationRadians: rotation));

            var sentry = battle.Deploy("Sentry", Side.Hostile, Node(0, 0), facing: HexDirection.NorthEast);
            var intruder = battle.Deploy("Intruder", Side.Player, Node(4, 0));
            battle.Start();

            return battle.Awareness.AttentionOn(sentry, intruder.Position);
        }

        Assert.Equal(Attention(0), Attention(Math.PI / 6), 6);
    }

    [Fact]
    public void EveryDirectionIsWatchedByExactlyTheSpokeItNames()
    {
        foreach (var direction in HexDirectionExtensions.All)
        {
            var battle = Field();
            var sentry = battle.Deploy("Sentry", Side.Hostile, Node(0, 0), facing: direction);
            battle.Start();

            var ahead = new NodeId(direction.Offset() * 3, 0);
            var behind = new NodeId(direction.Opposite().Offset() * 3, 0);

            Assert.True(battle.Awareness.IsWatching(sentry, ahead), $"{direction} did not watch ahead");
            Assert.False(battle.Awareness.IsWatching(sentry, behind), $"{direction} watched its own back");
        }
    }
}
