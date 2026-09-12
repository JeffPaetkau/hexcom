using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Battles;
using Hexcom.Core.Tactics;
using Xunit.Abstractions;

namespace Hexcom.Core.Tests.Measured;

/// <summary>
/// The first measurements in this project's history.
/// </summary>
/// <remarks>
/// Every balance number in this game was set by reasoning, and four of them are load-bearing in
/// ways their size does not advertise: what an objective is worth, how far its pull reaches, what
/// the two cost archetypes do, and what removing a signaller is worth. All four are testable now
/// because a commander drives both sides and a mission fights itself.
/// <para>
/// <b>These assert nothing.</b> They are instruments and not tests: a batch prints what happened
/// and a person reads it. An assertion here would pin today's balance in place, which is the
/// opposite of what a measurement is for — the figures go into <c>docs/decisions.md</c>, and what
/// gets pinned afterwards is whatever behaviour the argument settles on.
/// </para>
/// <para>
/// <b>One question per class, because xUnit runs classes in parallel and a batch is minutes.</b>
/// Outcomes are decided by the seed and not by the clock, so nothing about running four of them
/// at once changes a single figure — only the <c>s of matches</c> line, which is a note about
/// what the run cost rather than a finding.
/// </para>
/// </remarks>
public abstract class Measured(ITestOutputHelper output)
{
    /// <summary>
    /// An objective low enough that the squad still weighs what is in front of it.
    /// </summary>
    /// <remarks>
    /// Not a proposal for the shipped figure. It is the setting three of these questions need in
    /// order to be asked at all: at the shipped value the squad runs straight in, never fires a
    /// shot and is off the field by round four, and a match like that answers nothing about
    /// shooting, about how far a pull reaches, or about how long a clock has to be.
    /// </remarks>
    protected const double Fighting = 30.0;

    /// <summary>What the squad brings, with one thing moved.</summary>
    protected static UtilityModel Ours(double value) => UtilityModel.Default with { ObjectiveValue = value };

    protected void Report(string question, IEnumerable<Reading> arms)
    {
        output.WriteLine(question);
        output.WriteLine(new string('-', question.Length));

        var total = 0.0;
        foreach (var arm in arms)
        {
            output.WriteLine(arm.Lines());
            total += arm.Seconds;
        }

        output.WriteLine($"{total:0} s of matches, {Measurement.Seeds} paired seeds an arm.");
    }
}

/// <summary>
/// What an objective is worth against everything happening in front of it.
/// </summary>
/// <remarks>
/// Entry 044 names both failure modes and they are opposite: a squad that walks past a firefight
/// to reach an exit means the value is too high, and one that stands in a firefight ignoring the
/// exit means it is too low. Read <c>looked</c> and <c>closest</c> for whether the squad went at
/// all, and <c>shots</c> against <c>down</c> for what it did on the way.
/// </remarks>
public class TheValueOfAnObjective(ITestOutputHelper output) : Measured(output)
{
    [BatchFact]
    public void Measure()
    {
        var arms = new[] { 15.0, 30.0, 60.0, 120.0, 240.0 }
            .Select(value => Batch.Run(
                Name(value), Measurement.Seeds, seed => Waystation.Begin(seed), ours: Ours(value)));

        Report("What an objective is worth", arms);
    }

    private static string Name(double value)
        => $"value {value:0}{(value == UtilityModel.Default.ObjectiveValue ? " (shipped)" : "")}";
}

/// <summary>
/// How far the pull of an objective reaches.
/// </summary>
/// <remarks>
/// The slope rather than the size, and the two are easy to confuse. The horizon decides how steep
/// the gradient is and never how far it reaches, because a mission longer than the horizon is
/// stretched to its own length when the fight starts — so on a journey this long every setting
/// below four turns is the same setting.
/// <para>
/// Measured both at the shipped value and at one the pull does not swamp. What it found, in
/// <c>docs/decisions.md</c> entry 083, is that above the journey the horizon and the value are one
/// dial: the scorer answers to value per point of ground, and horizon sixteen at 120 plays like
/// horizon four at 30. An earlier version of this remark predicted the opposite, off a run that
/// had handed the horizon only to the commander.
/// </para>
/// </remarks>
public abstract class Horizons(ITestOutputHelper output) : Measured(output)
{
    /// <summary>
    /// The horizon goes on the battle, not only on the commander. <see cref="Objective"/> reads it
    /// once at <c>Start</c> off <see cref="Battle.Tactics"/>, so a horizon handed only to a
    /// commander is silently ignored, which is what the first run of this question did.
    /// </summary>
    protected Reading Arm(double value, double turns)
    {
        var model = Ours(value) with { ObjectiveHorizon = turns };
        return Batch.Run(
            $"horizon {turns:0} at {value:0}", Measurement.Seeds,
            seed => Waystation.Begin(seed, slope: model), ours: model);
    }
}

public class HowFarAnObjectivePulls(ITestOutputHelper output) : Horizons(output)
{
    [BatchFact]
    public void Measure() => Report(
        "How far an objective pulls, at the shipped value",
        new[] { 2.0, 16.0 }.Select(t => Arm(UtilityModel.Default.ObjectiveValue, t)));
}

/// <summary>The same question at a value the pull does not swamp, split so the arms run at once.</summary>
public class HowFarAShortPullReaches(ITestOutputHelper output) : Horizons(output)
{
    [BatchFact]
    public void Measure() => Report(
        $"How far an objective pulls, at {Fighting:0}",
        new[] { 1.0, 2.0 }.Select(t => Arm(Fighting, t)));
}

/// <inheritdoc cref="HowFarAShortPullReaches"/>
public class HowFarALongPullReaches(ITestOutputHelper output) : Horizons(output)
{
    [BatchFact]
    public void Measure() => Report(
        $"How far an objective pulls, at {Fighting:0}",
        new[] { 8.0, 16.0 }.Select(t => Arm(Fighting, t)));
}

/// <summary>
/// What the two cost archetypes do, which nothing has ever asked.
/// </summary>
/// <remarks>
/// Entry 062 gave the scout and the trooper the profiles the design doc had claimed for three
/// increments, and the whole suite passed unchanged — 391 tests, none of which could tell a
/// soldier that moved at four fifths and fired at seven fifths from one that did neither. This is
/// the same change asked of a batch instead of a suite.
/// </remarks>
public class WhatTheArchetypesDo(ITestOutputHelper output) : Measured(output)
{
    [BatchFact]
    public void Measure()
    {
        var arms = new[] { false, true }.SelectMany(flat => new[]
        {
            Batch.Run(
                $"{(flat ? "list price" : "the posts")} at the shipped value",
                Measurement.Seeds,
                seed => Waystation.Begin(seed, listPrice: flat)),
            Batch.Run(
                $"{(flat ? "list price" : "the posts")} at {Fighting:0}",
                Measurement.Seeds,
                seed => Waystation.Begin(seed, listPrice: flat),
                ours: Ours(Fighting)),
        });

        Report("What the two cost archetypes do", arms);
    }
}

/// <summary>
/// What a signaller is worth to remove.
/// </summary>
/// <remarks>
/// <see cref="UtilityModel.RemovalBonus"/> values every soldier at their own vitality and nothing
/// else, so the man carrying the set is worth exactly what the rifleman beside him is. Read
/// <c>first aimed at</c> and <c>first down</c>: the garrison is four men, one of whom holds the
/// whole side's net, and if the scorer has no opinion about which then the shots go where the
/// geometry sends them.
/// </remarks>
public class WhatASignallerIsWorth(ITestOutputHelper output) : Measured(output)
{
    [BatchFact]
    public void Measure()
    {
        var arms = new[] { 0.0, 1.0, 4.0 }
            .Select(bonus => Batch.Run(
                $"removal {bonus:0}{(bonus == UtilityModel.Default.RemovalBonus ? " (shipped)" : "")}",
                Measurement.Seeds,
                seed => Waystation.Begin(seed),
                ours: Ours(Fighting) with { RemovalBonus = bonus }));

        Report($"What a signaller is worth to remove, at an objective worth {Fighting:0}", arms);
    }
}

/// <summary>
/// Whether the quiet one is the man or the post.
/// </summary>
/// <remarks>
/// Entry 048 read the scout as <c>Unaware</c> to everybody across twelve matches and the trooper
/// as <c>Searching</c> across nine, and left open whether that is the noise of the walk — a scout
/// is quick over ground and a trooper is ponderous — or simply who was deployed nearer the road.
/// The two readings are confounded in the shipped mission and there is exactly one way to
/// separate them: put each man in the other's place and see which reading moves.
/// <para>
/// Entry 037 is what makes this worth the run: a turn's walk on gravel carries further than a slug
/// rifle, which would mean the thing that loses a stealth mission is already footsteps rather than
/// eyes.
/// </para>
/// </remarks>
public class WhetherTheQuietOneIsTheMan(ITestOutputHelper output) : Measured(output)
{
    [BatchFact]
    public void Measure()
    {
        var arms = new[] { false, true }.Select(swap => Batch.Run(
            swap ? "the two ours, posts swapped" : "the posts as written",
            Measurement.Seeds,
            seed => Waystation.Begin(seed, swapPosts: swap),
            ours: Ours(Fighting)));

        Report("Whether the quiet one is the man or the post", arms);
    }
}

/// <summary>
/// The mission clock, end to end, on the ground it was written for.
/// </summary>
/// <remarks>
/// Not a dial: a check that the two halves meet. The alarm is raised by the awareness model when
/// the man with the set works it out, the deadline is a property of the mission, and what a batch
/// says is how often the second one bites — which is the only way to know whether a grace of
/// three rounds is generous or fatal on this ground.
/// </remarks>
public class HowLongThreeRoundsIs(ITestOutputHelper output) : Measured(output)
{
    [BatchFact]
    public void Measure()
    {
        var arms = new int?[] { null, 5, 3, 1 }
            .Select(grace => Batch.Run(
                grace is null ? "the round limit alone" : $"{grace} rounds once they know",
                Measurement.Seeds,
                seed => Waystation.Begin(seed, clock: new Deadline(Waystation.Mission.Rounds, grace)),
                ours: Ours(Fighting)));

        Report("How long three rounds is", arms);
    }
}
