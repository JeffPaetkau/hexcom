using System.Collections.Generic;
using Hexcom.Rules;

namespace Hexcom.Rules.Tests;

public class ShootingTests
{
    private static readonly Hex Origin = new(0, 0);

    /// <summary>A hex about that many metres east of the origin: the grid is 1.5 hex sizes a column.</summary>
    private static Hex EastBy(double metres) => Hex.At(metres, 0);

    private static Unit Ours(Hex at) => new(at, Side.Player, "UNIT 1");

    private static Unit Theirs(Hex at) => new(at, Side.Hostile, "HOSTILE 1");

    [Fact]
    public void Neighbouring_hexes_are_a_metre_apart()
    {
        Assert.Equal(1.0, Shooting.Range(Origin, Origin.Neighbour(0)), precision: 6);
    }

    [Fact]
    public void The_rifle_cannot_miss_the_next_hex_and_is_at_its_accuracy_at_its_optimal_range()
    {
        Assert.Equal(1.0, Weapon.Rifle.HitChance(1));
        Assert.Equal(1.0, Weapon.Rifle.HitChance(0.5));
        Assert.Equal(0.8 + 0.2 * 10 / 19, Weapon.Rifle.HitChance(10), precision: 6);
        Assert.Equal(0.80, Weapon.Rifle.HitChance(20), precision: 6);
    }

    [Fact]
    public void A_shot_at_the_next_hex_always_lands_whatever_the_dice_say()
    {
        var target = Theirs(Origin.Neighbour(0));
        Assert.True(Shooting.Fire(Ours(Origin), target, roll: 0.999)!.Value.Hit);
    }

    [Fact]
    public void The_rifle_falls_to_two_fifths_of_its_accuracy_at_its_maximum_range_and_nothing_past_it()
    {
        Assert.Equal(0.32, Weapon.Rifle.HitChance(55), precision: 6);
        Assert.Equal(0.56, Weapon.Rifle.HitChance(37.5), precision: 6);
        Assert.Equal(0.0, Weapon.Rifle.HitChance(55.01));
    }

    [Fact]
    public void A_shot_at_a_target_beyond_the_rifle_is_refused_as_out_of_range()
    {
        var shot = Shooting.Plan(Ours(Origin), Theirs(EastBy(60)));

        Assert.Equal("OUT OF RANGE", shot.Refusal);
        Assert.False(shot.CanFire);
        Assert.Null(Shooting.Fire(Ours(Origin), Theirs(EastBy(60)), roll: 0));
    }

    [Fact]
    public void A_hit_costs_the_shot_and_a_round_and_takes_the_damage_off_the_target()
    {
        var shooter = Ours(Origin);
        var target = Theirs(EastBy(10));

        var result = Shooting.Fire(shooter, target, roll: 0.5);

        Assert.True(result!.Value.Hit);
        Assert.Equal(10, result.Value.Damage);
        Assert.Equal(Unit.MaxAp - 35, shooter.Ap);
        Assert.Equal(11, shooter.Rounds);
        Assert.Equal(20, target.HitPoints);
        Assert.False(result.Value.TargetDown);
    }

    [Fact]
    public void A_miss_costs_the_same_and_hurts_nobody()
    {
        var shooter = Ours(Origin);
        var target = Theirs(EastBy(10));

        var result = Shooting.Fire(shooter, target, roll: 0.95);

        Assert.False(result!.Value.Hit);
        Assert.Equal(0, result.Value.Damage);
        Assert.Equal(Unit.MaxAp - 35, shooter.Ap);
        Assert.Equal(11, shooter.Rounds);
        Assert.Equal(Unit.MaxHitPoints, target.HitPoints);
    }

    [Fact]
    public void Three_hits_put_a_soldier_down_and_a_fourth_is_refused()
    {
        var target = Theirs(EastBy(5));

        for (var i = 0; i < 3; i++) Shooting.Fire(Ours(Origin), target, roll: 0);

        Assert.True(target.IsDown);
        Assert.Equal(0, target.HitPoints);
        Assert.Equal("TARGET DOWN", Shooting.Plan(Ours(Origin), target).Refusal);
    }

    [Fact]
    public void Two_shots_fit_a_turn_and_a_third_does_not()
    {
        var shooter = Ours(Origin);
        var target = Theirs(EastBy(5));

        Shooting.Fire(shooter, target, roll: 1);
        Shooting.Fire(shooter, target, roll: 1);

        Assert.Equal("NOT ENOUGH POINTS", Shooting.Plan(shooter, target).Refusal);
        shooter.Refresh();
        Assert.True(Shooting.Plan(shooter, target).CanFire);
    }

    [Fact]
    public void An_empty_rifle_is_refused_before_the_points_are()
    {
        var shooter = Ours(Origin);
        var target = Theirs(EastBy(5));

        for (var i = 0; i < Weapon.Rifle.Rounds; i++)
        {
            shooter.Refresh();
            Shooting.Fire(shooter, target, roll: 1);
        }

        Assert.Equal(0, shooter.Rounds);
        Assert.Equal("NO ROUNDS", Shooting.Plan(shooter, target).Refusal);
    }

    [Fact]
    public void A_soldier_on_the_same_side_is_not_a_target()
    {
        Assert.Equal("FRIENDLY", Shooting.Plan(Ours(Origin), Ours(EastBy(5))).Refusal);
    }

    [Fact]
    public void A_hex_another_soldier_stands_on_is_neither_reached_nor_walked_through()
    {
        var blocked = new HashSet<Hex> { Origin.Neighbour(0) };
        var reach = new Movement(DrawnGround.Flat).Reachable(Origin, 15, blocked: blocked);

        Assert.False(reach.Contains(Origin.Neighbour(0)));

        // Two strides straight on would land beyond the blocked hex; the way round it is three.
        var beyond = Origin.Neighbour(0).Neighbour(0);
        Assert.True(reach.Contains(beyond));
        Assert.Equal(15, reach.CostTo(beyond));
        Assert.DoesNotContain(Origin.Neighbour(0), reach.PathTo(beyond));
    }
}
