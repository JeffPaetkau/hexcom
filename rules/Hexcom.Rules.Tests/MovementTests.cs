using System;
using System.Linq;
using Hexcom.Rules;

namespace Hexcom.Rules.Tests;

/// <summary>Ground drawn by hand: a height function and a surface function, for pricing steps without a landscape.</summary>
internal sealed class DrawnGround : IGround
{
    private readonly Func<double, double, double> _height;
    private readonly Func<double, double, Surface> _surface;

    public DrawnGround(Func<double, double, double>? height = null, Func<double, double, Surface>? surface = null)
    {
        _height = height ?? ((_, _) => 0);
        _surface = surface ?? ((_, _) => Surface.Open);
    }

    public static DrawnGround Flat { get; } = new();

    public double Height(double x, double z) => _height(x, z);

    public Surface SurfaceAt(double x, double z) => _surface(x, z);
}

public class MovementTests
{
    private static readonly Hex Origin = new(0, 0);

    // The neighbour in direction 0 sits at x = 1.5, z = 0.87: a step with a run along +X.
    private static readonly Hex East = Origin.Neighbour(0);

    // The neighbour in direction 1 sits at x = 0, z = 1.73: a step with no run along X at all.
    private static readonly Hex South = Origin.Neighbour(1);

    /// <summary>How many hexes lie within a number of strides of one, on open ground.</summary>
    private static int WithinStrides(int n) => 1 + 3 * n * (n + 1);

    [Fact]
    public void A_stride_on_open_flat_ground_costs_five()
    {
        var movement = new Movement(DrawnGround.Flat);
        Assert.Equal(5, movement.StepCost(Origin, East));
    }

    [Fact]
    public void Ten_strides_on_the_flat_spend_a_turn()
    {
        var reach = new Movement(DrawnGround.Flat).Reachable(Origin, Unit.MaxAp);

        Assert.Equal(WithinStrides(10), reach.Count);
        Assert.Equal(50, reach.CostTo(new Hex(10, 0)));
        Assert.False(reach.Contains(new Hex(11, 0)));
    }

    [Fact]
    public void A_paved_road_is_a_cheaper_stride()
    {
        var paved = new DrawnGround(surface: (_, _) => Surface.Paved);
        var movement = new Movement(paved);

        Assert.Equal(4, movement.StepCost(Origin, East));
        Assert.Equal(WithinStrides(12), movement.Reachable(Origin, Unit.MaxAp).Count);
    }

    [Fact]
    public void A_dirt_track_is_no_faster_than_the_field()
    {
        var track = new DrawnGround(surface: (_, _) => Surface.Track);
        Assert.Equal(5, new Movement(track).StepCost(Origin, East));
    }

    [Fact]
    public void Uphill_costs_more_than_downhill_on_the_same_slope_and_both_more_than_the_flat()
    {
        // A one-in-four grade along +X: fourteen degrees, ordinary hillside.
        var hillside = new DrawnGround(height: (x, _) => x * 0.25);
        var movement = new Movement(hillside);

        var up = movement.StepCost(Origin, East)!.Value;
        var down = movement.StepCost(East, Origin)!.Value;
        var along = movement.StepCost(Origin, South)!.Value;

        Assert.True(up > down, $"up {up} should cost more than down {down}");
        Assert.True(down > along, $"down {down} should cost more than along {along}");
        Assert.Equal(5, along);
    }

    [Fact]
    public void A_climb_of_one_in_two_adds_a_whole_stride()
    {
        // Rise of half the run between the two centres.
        var steep = new DrawnGround(height: (x, _) => x / 1.5 * Movement.Stride / 2);
        Assert.Equal(10, new Movement(steep).StepCost(Origin, East));
    }

    [Fact]
    public void A_bank_too_steep_to_walk_is_refused_and_the_reach_stops_at_it()
    {
        var bank = new DrawnGround(height: (x, _) => x > 1 ? 3 : 0);
        var movement = new Movement(bank);

        Assert.Null(movement.StepCost(Origin, East));
        Assert.Null(movement.StepCost(East, Origin));

        var reach = movement.Reachable(Origin, Unit.MaxAp);
        Assert.Contains(South, reach.Hexes);
        Assert.DoesNotContain(East, reach.Hexes);
    }

    [Fact]
    public void The_cheapest_way_goes_round_a_bank_rather_than_over_it()
    {
        // A bank three metres high across the way east, four hexes wide, with ground either side.
        var bank = new DrawnGround(height: (x, z) => x is > 2 and < 4 && Math.Abs(z) < 4 ? 3 : 0);
        var reach = new Movement(bank).Reachable(Origin, Unit.MaxAp);

        var beyond = new Hex(4, -2);
        var path = reach.PathTo(beyond);

        Assert.Equal(Origin, path[0]);
        Assert.Equal(beyond, path[^1]);
        Assert.DoesNotContain(path, hex => bank.Height(hex.Centre.X, hex.Centre.Z) > 0);
        Assert.True(path.Count - 1 > Origin.DistanceTo(beyond), "the way round is longer than the line");
        Assert.Equal((path.Count - 1) * 5, reach.CostTo(beyond));
    }

    [Fact]
    public void The_cost_of_a_path_is_the_sum_of_its_steps()
    {
        var rolling = new DrawnGround(height: (x, z) => 2 * Math.Sin(x / 4) * Math.Cos(z / 5));
        var movement = new Movement(rolling);
        var reach = movement.Reachable(Origin, Unit.MaxAp);

        foreach (var hex in reach.Hexes)
        {
            var path = reach.PathTo(hex);
            var summed = 0;
            for (var i = 1; i < path.Count; i++) summed += movement.StepCost(path[i - 1], path[i])!.Value;
            Assert.Equal(summed, reach.CostTo(hex));
        }
    }

    [Fact]
    public void The_path_to_where_the_unit_stands_is_just_that_hex_and_out_of_reach_is_empty()
    {
        var reach = new Movement(DrawnGround.Flat).Reachable(Origin, 5);

        Assert.Equal(new[] { Origin }, reach.PathTo(Origin));
        Assert.Equal(new[] { Origin, East }, reach.PathTo(East));
        Assert.Empty(reach.PathTo(new Hex(2, 0)));
        Assert.Null(reach.CostTo(new Hex(2, 0)));
    }

    [Fact]
    public void A_scout_pays_four_fifths_and_a_gunner_half_again()
    {
        var movement = new Movement(DrawnGround.Flat);

        Assert.Equal(4, movement.StepCost(Origin, East, CostProfile.Scout));
        Assert.Equal(8, movement.StepCost(Origin, East, CostProfile.Gunner));
    }

    [Fact]
    public void No_step_is_ever_free()
    {
        var weightless = new CostProfile { Movement = 0.01 };
        Assert.Equal(1, new Movement(DrawnGround.Flat).StepCost(Origin, East, weightless));
    }

    [Fact]
    public void The_ground_is_asked_about_each_hex_once()
    {
        var asked = 0;
        var counting = new DrawnGround(height: (_, _) => { asked++; return 0; });
        var reach = new Movement(counting).Reachable(Origin, Unit.MaxAp);

        // Every hex in reach, plus the ring just outside it that was priced and refused.
        Assert.Equal(reach.Count + 6 * 11, asked);
        Assert.All(reach.Hexes, hex => Assert.NotNull(reach.CostTo(hex)));
    }
}
