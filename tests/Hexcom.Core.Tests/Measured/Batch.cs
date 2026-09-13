using System.Collections.Generic;
using System.Linq;
using System.Text;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Tactics;

namespace Hexcom.Core.Tests.Measured;

/// <summary>
/// What a run of matches said, as the handful of numbers a dial is argued about in.
/// </summary>
/// <remarks>
/// Every figure here is a count or a mean over the same seeds, so two readings taken with one
/// dial moved between them are paired: the maps, the deployments and the initiative rolls are
/// identical and the only difference is the thing under test. That is what makes a difference of
/// a few percent worth reporting at all.
/// </remarks>
public sealed record Reading(string Arm, IReadOnlyList<MatchOutcome> Matches)
{
    public int Count => Matches.Count;

    public int Verdicts(Verdict verdict) => Matches.Count(m => m.Verdict == verdict);

    /// <summary>How often the squad got eyes on the thing it came for, at all.</summary>
    public int Confirmed => Matches.Count(m => m.Confirmed is not null);

    /// <summary>How often the garrison's word got out.</summary>
    public int Alarms => Matches.Count(m => m.Alarm is not null);

    /// <summary>How often nobody fired a shot or threw anything, on either side.</summary>
    public int Quiet => Matches.Count(m => m.Quiet);

    public double Mean(Func<MatchOutcome, double> of) => Matches.Count == 0 ? 0 : Matches.Average(of);

    /// <summary>The middle value, which is the honest average for a round number.</summary>
    public double Median(Func<MatchOutcome, double?> of)
    {
        var values = Matches.Select(of).Where(v => v is not null).Select(v => v!.Value).OrderBy(v => v).ToList();
        if (values.Count == 0) return double.NaN;
        return values.Count % 2 == 1
            ? values[values.Count / 2]
            : (values[values.Count / 2 - 1] + values[values.Count / 2]) / 2.0;
    }

    /// <summary>Who goes down first, by name, most often first.</summary>
    public IEnumerable<(string Name, int Times)> FirstDown => Tally(m => m.FirstDown);

    /// <summary>Who the first shot of the match was aimed at, by name.</summary>
    public IEnumerable<(string Name, int Times)> FirstAimedAt => Tally(m => m.FirstAimedAt);

    private IEnumerable<(string Name, int Times)> Tally(Func<MatchOutcome, string?> of) => Matches
        .Select(of)
        .Where(name => name is not null)
        .GroupBy(name => name!)
        .Select(g => (g.Key, g.Count()))
        .OrderByDescending(p => p.Item2);

    public double Seconds => Matches.Sum(m => m.Seconds);

    /// <summary>Two lines a person can read, and the same two for every arm so they line up.</summary>
    public string Lines()
    {
        var sb = new StringBuilder();
        var verdicts = string.Join(" ", Enum.GetValues<Verdict>().Select(v => $"{v.ToString()[..4].ToLowerInvariant()} {Verdicts(v),3}"));

        sb.AppendLine($"{Arm,-28} n={Count,4}  {verdicts}");
        sb.AppendLine(
            $"{"",-28} looked {Confirmed,3} (r{Median(m => m.Confirmed):0.#})  " +
            $"alarm {Alarms,3} (r{Median(m => m.Alarm):0.#})  quiet {Quiet,3}  " +
            $"closest {Mean(m => m.Closest):0.0}  " +
            $"shots {Mean(m => m.OurShots):0.0}/{Mean(m => m.TheirShots):0.0}  " +
            $"down {Mean(m => m.OurLosses):0.00}/{Mean(m => m.TheirLosses):0.00}  " +
            $"out {Mean(m => m.Extracted):0.00}  " +
            $"rounds {Mean(m => m.Rounds):0.0}");

        var aimed = FirstAimedAt.Select(p => $"{p.Name} {p.Times}").ToList();
        if (aimed.Count > 0) sb.AppendLine($"{"",-28} first aimed at: {string.Join(", ", aimed)}");

        var first = FirstDown.Select(p => $"{p.Name} {p.Times}").ToList();
        if (first.Count > 0) sb.AppendLine($"{"",-28} first down: {string.Join(", ", first)}");

        var seen = Matches.GroupBy(m => m.Noticed).OrderBy(g => g.Key)
            .Select(g => $"{g.Key.ToString().ToLowerInvariant()} {g.Count()}");
        sb.AppendLine($"{"",-28} worst rung held on us: {string.Join(", ", seen)}");

        foreach (var soldier in Matches.SelectMany(m => m.Peaks.Keys).Distinct())
        {
            var rungs = Matches
                .Select(m => m.Peaks[soldier])
                .GroupBy(rung => rung)
                .OrderBy(g => g.Key)
                .Select(g => $"{g.Key.ToString().ToLowerInvariant()} {g.Count()}");

            sb.AppendLine($"{"",-28}   {soldier,-8} {string.Join(", ", rungs)}");
        }

        return sb.ToString();
    }
}

/// <summary>Runs one arm of a measurement over a fixed set of seeds.</summary>
public static class Batch
{
    /// <summary>
    /// Play the same seeds with one thing changed, and hand back the totals.
    /// </summary>
    /// <remarks>
    /// Seeds are the first <paramref name="matches"/> integers rather than anything drawn, so a
    /// figure in <c>docs/decisions.md</c> can be reproduced exactly by anybody who runs this
    /// again. A measurement nobody else can repeat is an argument with numbers in it.
    /// </remarks>
    public static Reading Run(string arm, int matches, Func<int, Battle> begin, UtilityModel? ours = null, UtilityModel? theirs = null)
    {
        var outcomes = new List<MatchOutcome>(matches);
        var elapsed = 0.0;

        for (var seed = 1; seed <= matches; seed++)
        {
            var outcome = Match.Play(begin(seed), seed, ours, theirs);
            outcomes.Add(outcome);
            elapsed += outcome.Seconds;

            if (Measurement.Progress is { } path)
                File.AppendAllText(
                    path,
                    $"{arm}: {seed}/{matches} in {outcome.Seconds:0.0} s, {elapsed:0} s so far; " +
                    $"{outcome.Verdict.ToString().ToLowerInvariant()} r{outcome.Rounds}, looked {(outcome.Confirmed is { } c ? $"r{c}" : "never")}, " +
                    $"alarm {(outcome.Alarm is { } a ? $"r{a}" : "never")}, shots {outcome.OurShots}/{outcome.TheirShots}{Environment.NewLine}");
        }

        return new Reading(arm, outcomes);
    }
}
