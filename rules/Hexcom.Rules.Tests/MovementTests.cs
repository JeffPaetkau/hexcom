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

    // The neighbour in direction 0 sits at x = 0.87, z = 0.5: a step with a run along +X.
    private static readonly Hex East = Origin.Neighbour(0);

    // The neighbour in direction 1 sits at x = 0, z = 1: a step with no run along X at all.
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
    public void Twenty_strides_on_the_flat_spend_a_turn_exactly()
    {
        var reach = new Movement(DrawnGround.Flat).Reachable(Origin, Unit.MaxAp);

        Assert.Equal(WithinStrides(20), reach.Count);
        Assert.Equal(100, reach.CostTo(new Hex(20, 0)));
        Assert.False(reach.Contains(new Hex(21, 0)));
    }

    [Fact]
    public void A_paved_road_is_a_cheaper_stride_and_twenty_five_of_them_are_a_turn()
    {
        var paved = new DrawnGround(surface: (_, _) => Surface.Paved);
        var movement = new Movement(paved);

        Assert.Equal(4, movement.StepCost(Origin, East));
        Assert.Equal(WithinStrides(25), movement.Reachable(Origin, Unit.MaxAp).Count);
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
        // Rise of half the run between the two centres, reached at the eastern neighbour's x.
        var steep = new DrawnGround(height: (x, _) => x / (1.5 * Units.HexSize) * Movement.Stride / 2);
        Assert.Equal(10, new Movement(steep).StepCost(Origin, East));
    }

    [Fact]
    public void A_bank_too_steep_to_walk_is_refused_and_the_reach_stops_at_it()
    {
        var bank = new DrawnGround(height: (x, _) => x > 0.5 ? 3 : 0);
        var movement = new Movement(bank);

        Assert.Null(movement.StepCost(Origin, East));
        Assert.Null(movement.StepCost(East, Origin));

        var reach = movement.Reachable(Origin, Unit.MaxAp);
        Assert.Contains(South, reach.Hexes);
        Assert.DoesNotContain(East, reach.Hexes);
    }

    [Fact]
    public void Ground_too_steep_to_stand_on_is_refused_even_by_a_level_step_along_it()
    {
        // A one-in-one slope along +X: a step due south along the contour has no rise at all.
        var face = new DrawnGround(height: (x, _) => x);
        var movement = new Movement(face);

        Assert.False(movement.CanStand(South));
        Assert.Null(movement.StepCost(Origin, South));
        Assert.Equal(1, movement.Reachable(Origin, Unit.MaxAp).Count);
    }

    [Fact]
    public void A_steep_descent_can_be_hurried_for_less_at_the_risk_of_a_fall()
    {
        // Ground falling 0.52 along +Z, a shade past one in two so no price sits on a rounding
        // midpoint: the step south is a descent of that grade.
        var slope = new DrawnGround(height: (_, z) => -0.52 * z);
        var movement = new Movement(slope);

        Assert.Equal(7, movement.StepCost(Origin, South));
        Assert.Equal(3, movement.HurriedStepCost(Origin, South));
        Assert.Equal(0.052, movement.TripChance(Origin, South), 6);

        // No hurrying uphill.
        Assert.Null(movement.HurriedStepCost(South, Origin));
    }

    [Fact]
    public void A_gentle_descent_has_no_hurried_way()
    {
        var gentle = new DrawnGround(height: (_, z) => -0.2 * z);
        Assert.Null(new Movement(gentle).HurriedStepCost(Origin, South));
    }

    [Fact]
    public void Hurrying_reaches_further_down_a_slope_and_the_risk_compounds_along_the_way()
    {
        var slope = new DrawnGround(height: (_, z) => -0.52 * z);
        var movement = new Movement(slope);
        var careful = movement.Reachable(Origin, Unit.MaxAp);
        var hurried = movement.Reachable(Origin, Unit.MaxAp, hurrying: true);

        // Twenty steps straight down the slope: 140 carefully, 60 at a run.
        var far = new Hex(0, 20);
        Assert.False(careful.Contains(far));
        Assert.True(hurried.Contains(far));
        Assert.Equal(60, hurried.CostTo(far));
        Assert.True(hurried.HurriedInto(far));
        Assert.Equal(1 - Math.Pow(1 - 0.052, 20), hurried.RiskTo(far)!.Value, 6);

        // Everything the careful reach has, the hurrying one has too, and a step uphill is safe.
        Assert.All(careful.Hexes, hex => Assert.True(hurried.Contains(hex)));
        Assert.Equal(0.0, hurried.RiskTo(Origin.Neighbour(5)));
        Assert.False(hurried.HurriedInto(Origin.Neighbour(5)));
    }

    [Fact]
    public void The_cheapest_way_goes_round_a_bank_rather_than_over_it()
    {
        // A bank three metres high across the way east, four hexes wide, with ground either side.
        var bank = new DrawnGround(height: (x, z) => x is > 1.2 and < 2.3 && Math.Abs(z) < 2.3 ? 3 : 0);
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

        // Every hex in reach, plus the ring just outside it that was priced and refused, each
        // asked for its centre and the four points its slope is read from.
        Assert.Equal((reach.Count + 6 * 21) * Movement.HeightsPerHex, asked);
        Assert.All(reach.Hexes, hex => Assert.NotNull(reach.CostTo(hex)));
    }
}
