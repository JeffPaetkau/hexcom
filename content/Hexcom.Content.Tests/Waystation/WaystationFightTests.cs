using System.Linq;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Xunit.Abstractions;

namespace Hexcom.Content.Tests.Waystation;

/// <summary>
/// The waystation, fought over by the AI on both sides. The report these print is the
/// instrument the first battlefield brief asks for: not who won, but where the fighting was.
/// </summary>
/// <remarks>
/// The deployments, the exit and the round cap all come from
/// <c>content/missions/waystation.hexmission</c> now, which is the one copy of them there is.
/// <para>
/// The first twelve matches fought here reached no decision at all, and entry 038 is the reason:
/// there was nothing to want, so a search one step deep found nothing better than where it was
/// standing. There is something to want now, and what these tests assert is that it is enough to
/// end a match — the rest of what they check is what the map was redrawn to guarantee.
/// </para>
/// </remarks>
public class WaystationFightTests(ITestOutputHelper output)
{
    /// <summary>
    /// How many seeds to fight. One by default so the suite stays quick; set
    /// <c>HEXCOM_SEEDS</c> to a dozen when the point is to read the routes rather than to
    /// check the harness.
    /// </summary>
    private static int Seeds => Env("HEXCOM_SEEDS", 1);

    /// <summary>The first seed to fight, so a dozen can be split across two processes.</summary>
    private static int FirstSeed => Env("HEXCOM_SEED_FROM", 1);

    /// <summary>
    /// The round cap, which the mission carries: it is the sixth row of the briefing, not a knob
    /// on the harness. Sixty is what the first dozen were run to, and what to set
    /// <c>HEXCOM_ROUNDS</c> to when comparing against them.
    /// </summary>
    private static int Rounds => Env("HEXCOM_ROUNDS", WaystationFight.Rounds);

    private static int Env(string name, int fallback)
        => int.TryParse(Environment.GetEnvironmentVariable(name), out var n) && n > 0 ? n : fallback;

    [Fact]
    public void TheFightIsRecordedSeedBySeed()
    {
        var map = MapLibrary.Load(WaystationFight.MapName);

        foreach (var seed in Enumerable.Range(FirstSeed, Seeds))
        {
            var battle = WaystationFight.Start(seed);
            var report = MatchRecorder.Play(battle, seed, Rounds);
            output.WriteLine(MatchRecorder.Describe(report, WaystationFight.Landmarks(map)));
            if (Environment.GetEnvironmentVariable("HEXCOM_TRANSCRIPT") == seed.ToString())
                output.WriteLine(MatchRecorder.Transcript(report));

            // It comes to something, which is what entry 038 measured that it did not.
            // What is deliberately no longer asserted is that anybody fired: a withdrawal
            // achieved without a shot is the best outcome this game has, and the line that used
            // to demand one was written when the only way to end a battle was to win a fight.
            Assert.True(report.Settled, $"seed {seed}: ran to the round cap with no verdict");
        }
    }

    // ---- what the redraw was for ------------------------------------------------------

    [Fact]
    public void TheTreeLineHidesTheFieldsAndLeavesTheRoadAQueue()
    {
        var battle = WaystationFight.Start(seed: 1);
        var bekker = battle.Units.Single(u => u.Name == "Bekker");
        var orsini = battle.Units.Single(u => u.Name == "Orsini");
        var cobb = battle.Units.Single(u => u.Name == "Cobb");

        // From the field, the man at the gate is behind the trees.
        Assert.False(battle.CanSee(bekker, cobb), "the rifleman in the field can see the gate");
        Assert.False(battle.CanSee(cobb, bekker), "the sentry can see into the field");

        // From the road, through the gap, he is not — the road is still the way everybody uses.
        Assert.True(battle.CanSee(orsini, cobb), "the road should look straight at the gate");
    }

    [Fact]
    public void TheStreamIsCrossedAtTheBridgeAndTheFordAndNowhereElse()
    {
        var map = MapLibrary.Load(WaystationFight.MapName);
        var graph = MovementGraph.Build(map);

        var west = new NodeId(new Hex(-19, -3), 0);
        var drain = new NodeId(new Hex(-1, -4), 0);
        var reach = Pathfinder.Reachable(graph, west, int.MaxValue);
        Assert.True(reach.CanReach(drain), "the drain is cut off from the west bank");

        // Every link that steps from one bank to the other does so on the bridge or the ford.
        var stream = map.Tiles.Where(t => t.Ground.Id == "deep").Select(t => t.Address.Hex).ToHashSet();
        Assert.NotEmpty(stream);
        foreach (var hex in stream) Assert.False(graph.Contains(new NodeId(hex, 0)), $"{hex} is deep water and has a node");

        var crossings = new[] { new Hex(-8, 0), new Hex(-6, -4) };
        Assert.All(crossings, hex => Assert.True(graph.Contains(new NodeId(hex, 0)), $"{hex} should be a crossing"));
    }

    [Fact]
    public void ARifleShotAtTheWestGateIsHeardInTheCompoundAndNowhereFurther()
    {
        // The figure the fight turns on, measured rather than worked out from the model:
        // WeaponProfile.SlugRifle.Loudness is 45 and AwarenessModel.NoiseMetresPerPoint 0.4.
        var battle = WaystationFight.Start(seed: 1);
        var bekker = battle.Units.Single(u => u.Name == "Bekker");
        var gate = new NodeId(new Hex(-5, 0), 0);

        var heard = battle.Awareness.WouldHear(bekker, gate, bekker.Weapon.Loudness)
            .Select(a => a.Learner.Name)
            .Order()
            .ToList();
        output.WriteLine($"a slug rifle fired at the west gate is heard by: {string.Join(", ", heard)}");

        // Cobb at the gate and Teague on the roof; not the barn, not the tower.
        Assert.Contains("Teague", heard);
        Assert.DoesNotContain("Hollis", heard);
        Assert.DoesNotContain("Marek", heard);
    }

    [Fact]
    public void AWalkDownTheRoadIsHeardFurtherThanARifleShot()
    {
        // Loudness is the listed cost of the whole route times the noisiest ground on it, so a
        // turn's walk on gravel outdoes one round from the loudest gun on the map. Entry 037.
        var battle = WaystationFight.Start(seed: 1);
        var orsini = battle.Units.Single(u => u.Name == "Orsini");

        var road = new System.Collections.Generic.List<TraversalLink>();
        for (var q = -20; q < -11; q++)
        {
            var from = new NodeId(new Hex(q, 0), 0);
            var to = new NodeId(new Hex(q + 1, 0), 0);
            road.Add(battle.Graph.LinksFrom(from).Single(l => l.To == to));
        }

        var walk = battle.Loudness(orsini, road);
        var rifle = battle.Units.Single(u => u.Name == "Bekker").Weapon.Loudness;
        output.WriteLine($"nine strides down the road: loudness {walk:0}, heard at {walk * battle.Awareness.Model.NoiseMetresPerPoint:0.0} m; a slug rifle: {rifle:0}, heard at {rifle * battle.Awareness.Model.NoiseMetresPerPoint:0.0} m");

        Assert.True(walk > rifle, $"the walk ({walk:0}) should be louder than the rifle ({rifle:0})");
    }
}
