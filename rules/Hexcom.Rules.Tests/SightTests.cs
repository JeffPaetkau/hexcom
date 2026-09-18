using System;
using System.Diagnostics;
using Hexcom.Rules;

namespace Hexcom.Rules.Tests;

public class SightTests
{
    private static readonly Hex Origin = new(0, 0);

    /// <summary>Metres along direction 0 from the origin, as the ground sees them: the axis the drawn banks are laid across.</summary>
    private static double Along(double x, double z) => x * 0.8660254 + z * 0.5;

    /// <summary>The hex that many strides out along direction 0.</summary>
    private static Hex Out(int strides) => new(strides, 0);

    // Facing direction 0 (south-east on the compass), so Out is straight ahead.
    private const int Ahead = 0;

    [Fact]
    public void On_the_flat_a_man_ahead_is_clear_close_by_half_made_out_at_the_weather_distance_and_gone_by_three_times_it()
    {
        var sight = new Sight(DrawnGround.Flat);

        Assert.Equal(1, sight.Clarity(Origin, Ahead, Out(1)), precision: 3);
        Assert.Equal(0.5, sight.Clarity(Origin, Ahead, Out(40)), precision: 3);
        Assert.Equal(0, sight.Clarity(Origin, Ahead, Out(120)), precision: 3);
    }

    [Fact]
    public void The_same_man_behind_is_barely_made_out_and_to_the_side_partly()
    {
        var sight = new Sight(DrawnGround.Flat);
        var behind = Origin.Neighbour(3);
        var beside = new Hex(-1, 2); // Ninety degrees off: past the front arc, inside the peripheral one.

        Assert.Equal(SightModel.Default.RearAcuity, sight.Clarity(Origin, Ahead, behind), precision: 2);
        Assert.Equal(SightModel.Default.PeripheralAcuity, sight.Clarity(Origin, Ahead, beside), precision: 2);
        Assert.False(sight.Survey(Origin, Ahead).Sees(behind));
        Assert.True(sight.Survey(Origin, Ahead).Sees(beside));
    }

    [Fact]
    public void The_bands_blend_rather_than_step()
    {
        var sight = new Sight(DrawnGround.Flat);

        Assert.Equal(1, sight.ArcFactor(60));
        Assert.True(sight.ArcFactor(75) is > 0.45 and < 1);
        Assert.Equal(0.45, sight.ArcFactor(90), precision: 6);
        Assert.Equal(0.45, sight.ArcFactor(100), precision: 6);
        Assert.True(sight.ArcFactor(115) is > 0.08 and < 0.45);
        Assert.Equal(0.08, sight.ArcFactor(130), precision: 6);
        Assert.Equal(0.08, sight.ArcFactor(180), precision: 6);
    }

    [Fact]
    public void A_bank_hides_a_man_from_the_feet_up_by_the_share_of_him_below_its_waterline()
    {
        // A metre-high bank five strides out, a stride wide; the man stands two strides past it.
        var bank = new DrawnGround(height: (x, z) => Along(x, z) is >= 4.5 and < 5.5 ? 1.0 : 0.0);
        var sight = new Sight(bank);

        // From an eye at 1.65 the bank top projects to 1.65 + (1 - 1.65) * 7 / 5 = 0.74 on the
        // man: two fifths of his 1.8 hidden, three fifths showing.
        Assert.Equal(1 - 0.74 / 1.8, sight.Exposure(Origin, Out(7)), precision: 2);

        // The eye is above the bank, so the line over it descends: right behind it he is more
        // hidden, and far behind it not at all, since the waterline has dropped below his feet.
        Assert.True(sight.Exposure(Origin, Out(6)) < sight.Exposure(Origin, Out(7)));
        Assert.Equal(1, sight.Exposure(Origin, Out(40)), precision: 3);
    }

    [Fact]
    public void A_table_hides_what_stands_back_from_its_edge_from_below_and_hides_the_ground_below_from_what_stands_back()
    {
        // A three-metre table from ten strides out: the bluff, drawn by hand.
        var table = new DrawnGround(height: (x, z) => Along(x, z) >= 9.5 ? 3.0 : 0.0);
        var sight = new Sight(table);

        // Just past the edge the waterline is 1.65 + 1.35 * 12 / 10 = 3.27: a sliver hidden.
        Assert.Equal(1 - 0.27 / 1.8, sight.Exposure(Origin, Out(12)), precision: 2);

        // Ten strides back from the edge only head and shoulders show, and forty back nothing.
        Assert.Equal(0.25, sight.Exposure(Origin, Out(20)), precision: 2);
        Assert.Equal(0, sight.Exposure(Origin, Out(50)), precision: 3);

        // From the edge the ground below is all in view; ten strides back from it the edge is
        // in the way and only a head shows at the foot, and a man five strides from the foot
        // is hidden entirely. You have to go to the edge to look down.
        Assert.Equal(1, sight.Exposure(Out(10), Origin), precision: 3);
        Assert.Equal(0.25, sight.Exposure(Out(20), Origin), precision: 2);
        Assert.Equal(0, sight.Exposure(Out(20), Out(5)), precision: 3);
    }

    [Fact]
    public void A_survey_has_the_soldiers_own_hex_clear_and_reaches_only_as_far_as_the_air_does()
    {
        var sight = new Sight(DrawnGround.Flat);
        var view = sight.Survey(Origin, Ahead);

        Assert.Equal(1, view.ClarityAt(Origin));
        Assert.True(view.Sees(Out(60)));
        Assert.False(view.Sees(Out(80)));
        Assert.Equal(0, view.ClarityAt(Out(150)));
        Assert.True(view.Count > 3 * 40 * 40);
    }

    [Fact]
    public void A_foggy_dawn_is_the_same_rule_with_a_shorter_distance()
    {
        var dawn = new Sight(DrawnGround.Flat, new SightModel { HalfSightMetres = 8 });

        Assert.Equal(0.5, dawn.Clarity(Origin, Ahead, Out(8)), precision: 3);
        Assert.False(dawn.Survey(Origin, Ahead).Sees(Out(16)));
    }

    [Fact]
    public void A_shot_at_a_target_out_of_sight_is_refused()
    {
        var shooter = new Unit(Origin, Side.Player);
        var target = new Unit(Out(5), Side.Hostile);

        Assert.Equal("NOT IN SIGHT", Shooting.Plan(shooter, target, seen: false).Refusal);
        Assert.Null(Shooting.Fire(shooter, target, 0.5, seen: false));
        Assert.True(Shooting.Plan(shooter, target).CanFire);
    }

    [Fact]
    public void A_survey_of_the_real_landscape_is_quick_enough_to_take_at_every_turn()
    {
        var sight = new Sight(new Terrain(7));
        var watch = Stopwatch.StartNew();
        var view = sight.Survey(new Hex(171, -66), 5);
        watch.Stop();

        Assert.True(view.Count > 10_000);
        Assert.True(watch.ElapsedMilliseconds < 1500, $"survey took {watch.ElapsedMilliseconds} ms");
    }
}
