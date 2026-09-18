using System.Linq;
using Hexcom.Rules;

namespace Hexcom.Rules.Tests;

public class FacingTests
{
    private static readonly Hex Origin = new(0, 0);

    [Fact]
    public void Facing_a_neighbour_is_facing_its_direction()
    {
        for (var d = 0; d < Facing.Count; d++)
        {
            Assert.Equal(d, Facing.Toward(Origin, Origin.Neighbour(d)));
        }
    }

    [Fact]
    public void Facing_a_far_hex_picks_the_nearest_of_the_six_directions()
    {
        // Three columns east and a shade south: eleven degrees below +X, nearer the thirty
        // degree direction than the three hundred and thirty.
        Assert.Equal(0, Facing.Toward(Origin, new Hex(3, -1)));

        // Straight north up -Z is direction four, and straight south direction one.
        Assert.Equal(4, Facing.Toward(Origin, new Hex(0, -7)));
        Assert.Equal(1, Facing.Toward(Origin, new Hex(0, 7)));
    }

    [Fact]
    public void A_hex_faces_no_way_towards_itself()
    {
        Assert.Null(Facing.Toward(Origin, Origin));
    }

    [Fact]
    public void Direction_four_is_north_and_the_names_go_round_from_the_south_east()
    {
        Assert.Equal("N", Facing.Name(4));
        Assert.Equal(270, Facing.BearingDegrees(4));
        Assert.Equal(new[] { "SE", "S", "SW", "NW", "N", "NE" }, new[] { 0, 1, 2, 3, 4, 5 }.Select(Facing.Name));
    }

    [Fact]
    public void The_fewest_sixths_between_directions_go_either_way_round()
    {
        Assert.Equal(0, Facing.Steps(2, 2));
        Assert.Equal(1, Facing.Steps(0, 1));
        Assert.Equal(1, Facing.Steps(0, 5));
        Assert.Equal(2, Facing.Steps(1, 5));
        Assert.Equal(3, Facing.Steps(0, 3));
    }

    [Fact]
    public void Turning_costs_four_a_sixth_and_an_about_face_twelve()
    {
        var movement = new Movement(DrawnGround.Flat);

        Assert.Equal(0, movement.TurnCost(2, 2));
        Assert.Equal(4, movement.TurnCost(2, 3));
        Assert.Equal(8, movement.TurnCost(0, 4));
        Assert.Equal(12, movement.TurnCost(0, 3));
    }

    [Fact]
    public void Turning_on_the_spot_pays_and_faces_or_is_refused_with_nothing_spent()
    {
        var movement = new Movement(DrawnGround.Flat);
        var unit = new Unit(Origin, facing: 0);

        Assert.Equal(12, movement.Turn(unit, 3));
        Assert.Equal(3, unit.Facing);
        Assert.Equal(Unit.MaxAp - 12, unit.Ap);

        unit.Spend(unit.Ap - 3);
        Assert.Null(movement.Turn(unit, 4));
        Assert.Equal(3, unit.Facing);
        Assert.Equal(3, unit.Ap);

        Assert.Equal(0, movement.Turn(unit, 3));
        Assert.Equal(3, unit.Ap);
    }

    [Fact]
    public void A_shot_turns_the_shooter_to_face_the_target_for_nothing_extra()
    {
        var shooter = new Unit(Origin, Side.Player, facing: 1);
        var target = new Unit(new Hex(0, -7), Side.Hostile);

        Assert.NotNull(Shooting.Fire(shooter, target, roll: 0.5));
        Assert.Equal(4, shooter.Facing);
        Assert.Equal(Unit.MaxAp - Weapon.Rifle.ShotCost, shooter.Ap);
    }
}
