using System.Linq;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Vision;
using Xunit.Abstractions;

namespace Hexcom.Content.Tests.Waystation;

/// <summary>
/// What the waystation offers the mission written on it, measured rather than asserted from the
/// drawing.
/// </summary>
/// <remarks>
/// The mission book's test for a reconnaissance is whether the ground gives you somewhere to
/// look at the place <em>from</em> — a place with no standoff on it is a burglary and not an
/// assessment. These are that question asked of the house, and the answer turns out to be the
/// mission: the house is sealed from outside the wall, the fourteen places inside it can be seen
/// from are all south of the door, the drain lands you on one of them, and every one of the
/// fourteen is overlooked by the roof. Nobody drew it that way on purpose. Entry 058.
/// </remarks>
public class WaystationGroundTests(ITestOutputHelper output)
{
    private static readonly Hex HouseCentre = new(0, 1);
    private static readonly Vantage Roof = new(new NodeId(HouseCentre, 1));

    private readonly MovementGraph _graph = MovementGraph.Build(MapLibrary.Load(WaystationFight.MapName));
    private readonly SightSolver _sight = new(MapLibrary.Load(WaystationFight.MapName), Mission.Metres);

    private System.Collections.Generic.List<NodeId> House
        => HouseCentre.WithinRange(1).Select(h => new NodeId(h, 0)).Where(_graph.CanEndTurn).ToList();

    private System.Collections.Generic.List<NodeId> Standable(System.Func<NodeId, bool> where)
        => _graph.Nodes.Where(n => n.CanEndTurn && n.Id.Layer == 0 && where(n.Id)).Select(n => n.Id).ToList();

    [Fact]
    public void TheHouseCannotBeSeenIntoFromAnywhereOutsideTheWall()
    {
        var house = House;
        var outside = Standable(n => n.Hex.DistanceTo(Hex.Zero) > 4);
        output.WriteLine($"{outside.Count} standable places outside the wall, {house.Count} inside the house");

        var seers = outside.Where(o => house.Any(h => _sight.CanSee(new Vantage(o), new Vantage(h)))).ToList();
        Assert.Empty(seers);
    }

    [Fact]
    public void TheHouseIsSeenIntoFromFourteenPlacesInTheYardAndTheRoofOverlooksEveryOneOfThem()
    {
        var house = House;
        var yard = Standable(n => n.Hex.DistanceTo(Hex.Zero) <= 4).Except(house).ToList();

        var canSeeIn = yard.Where(y => house.Any(h => _sight.CanSee(new Vantage(y), new Vantage(h)))).ToList();
        output.WriteLine($"{canSeeIn.Count} of {yard.Count} yard places have a line through the door: {string.Join(", ", canSeeIn.Select(n => n.Hex))}");

        Assert.Equal(14, canSeeIn.Count);

        // Which is the whole mission: there is nowhere to take the look from that the set cannot
        // see. Either the roof is dealt with or the answer is not worth carrying home.
        var hidden = canSeeIn.Where(y => !_sight.CanSee(Roof, new Vantage(y))).ToList();
        Assert.Empty(hidden);
    }

    [Fact]
    public void TheDrainPutsYouStraightOntoTheLookAndTheGatesDoNot()
    {
        var house = House;
        var drain = new NodeId(new Hex(-1, -3), 0);
        Assert.True(_graph.CanEndTurn(drain), "the drain does not open anywhere anybody can stand");
        Assert.True(house.Any(h => _sight.CanSee(new Vantage(drain), new Vantage(h))), "the drain should land on the look");

        // The two gates are on the road, and the road runs past the house rather than at its door.
        foreach (var gate in new[] { new NodeId(new Hex(4, 0), 0), new NodeId(new Hex(-4, 0), 0) })
            Assert.False(house.Any(h => _sight.CanSee(new Vantage(gate), new Vantage(h))), $"the gate at {gate} sees into the house");
    }
}
