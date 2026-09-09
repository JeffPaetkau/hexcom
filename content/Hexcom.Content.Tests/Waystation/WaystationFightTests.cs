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
/// Nothing here asserts a decision, because none of the first twelve matches reached one and
/// the reason is Core's, recorded in <c>docs/decisions.md</c> entry 038: the fighting is over by
/// round 21 and the rest is the stalemate <c>core.md</c> predicts for a search one step deep
/// with nothing to want. What is asserted is what the map was redrawn to guarantee.
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
    /// The round cap. Thirty covers every fight seen so far with room to spare; sixty is what
    /// the first dozen were run to, and what to use when comparing against them.
    /// </summary>
    private static int Rounds => Env("HEXCOM_ROUNDS", 30);

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
            output.WriteLine(MatchRecorder.Describe(report, map));
            if (Environment.GetEnvironmentVariable("HEXCOM_TRANSCRIPT") == seed.ToString())
                output.WriteLine(MatchRecorder.Transcript(report));

            // It is a fight, whatever else it is.
            Assert.True(report.Shots + report.Throws > 0, $"seed {seed}: nobody fired");
        }
    }

    // ---- what the redraw was for ------------------------------------------------------

    [Fact]
    public void TheTreeLineHidesTheFieldsAndLeavesTheRoadAQueue()
    {
        var battle = WaystationFight.Start(seed: 1);
        var bekker = battle.Units.Single(u => u.Name == "Bekker");
        var orsini = battle.Units.Single(u => u.Name == "Orsini");
        var sentry = battle.Units.Single(u => u.Name == "Sentry");

        // From the field, the sentry at the gate is behind the trees.
        Assert.False(battle.CanSee(bekker, sentry), "the rifleman in the field can see the gate");
        Assert.False(battle.CanSee(sentry, bekker), "the sentry can see into the field");

        // From the road, through the gap, he is not — the road is still the way everybody uses.
        Assert.True(battle.CanSee(orsini, sentry), "the road should look straight at the gate");
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

        // The sentry at the gate and the spotter on the roof; not the barn, not the tower.
        Assert.Contains("Spotter", heard);
        Assert.DoesNotContain("Hollis", heard);
        Assert.DoesNotContain("Watchman", heard);
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
