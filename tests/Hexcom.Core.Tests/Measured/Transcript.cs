using System.Collections.Generic;
using System.Linq;
using System.Text;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Xunit;
using Xunit.Abstractions;

namespace Hexcom.Core.Tests.Measured;

/// <summary>A test that only runs when somebody asked to read one match closely.</summary>
public sealed class TranscriptFactAttribute : FactAttribute
{
    public TranscriptFactAttribute()
    {
        if (Transcript.Seed is not null) return;

        Skip = "Set HEXCOM_TRANSCRIPT=<seed> to read one match closely.";
    }
}

/// <summary>
/// One match, every decision, and what each was chosen over.
/// </summary>
/// <remarks>
/// The batch answers <em>how often</em>; this answers <em>why</em>. A turn log — the content
/// harness keeps one — says what a soldier did, and it cannot say what the second move was
/// chosen over, which is where both search faults of entry 039 live and where entry 087's
/// followers went wrong. So this stands between decisions, through <see cref="Commander.Step"/>,
/// and prints the table each was ranked from: the top few options with their terms, and for a
/// move the two halves a reader cannot recover from the total — what the pose keeps of the
/// mission and what the ground is worth toward it.
/// <para>
/// It reads certainty figures the interface may not, because it is an instrument and not a
/// screen. <c>HEXCOM_TRANSCRIPT</c> is the seed; <c>HEXCOM_BLIND=1</c> plays it without the
/// briefing; <c>HEXCOM_VALUE</c> sets what the objective is worth to our side, as the batch does.
/// </para>
/// </remarks>
public static class Transcript
{
    public static int? Seed
        => int.TryParse(Environment.GetEnvironmentVariable("HEXCOM_TRANSCRIPT"), out var n) && n > 0 ? n : null;

    public static bool Blind => Environment.GetEnvironmentVariable("HEXCOM_BLIND") is not (null or "" or "0");

    public static double? Value
        => double.TryParse(Environment.GetEnvironmentVariable("HEXCOM_VALUE"), out var v) && v > 0 ? v : null;

    /// <summary>How many of the options each decision prints. The rest were beaten by these.</summary>
    public const int Shown = 6;

    /// <summary>Play it out and write down every decision the side being read made.</summary>
    public static string Of(Battle battle, UtilityModel? ours = null, Side read = Side.Player, int roundCap = 60)
    {
        var sb = new StringBuilder();
        var commanders = new Dictionary<Side, Commander>
        {
            [Side.Player] = new Commander(battle, read == Side.Player ? ours : null),
            [Side.Hostile] = new Commander(battle, read == Side.Hostile ? ours : null),
        };

        var everyone = battle.Units.ToList();
        var round = 0;

        while (battle.IsRunning && !battle.IsDecided && battle.Round <= roundCap)
        {
            if (battle.Round != round)
            {
                round = battle.Round;
                sb.AppendLine();
                sb.AppendLine($"== round {round} ==");
            }

            var mover = battle.Active!;
            var commander = commanders[mover.Side];

            if (mover.Side != read)
            {
                var from = mover.Position;
                var acts = commander.TakeTurn();
                var did = acts.Count == 0 ? "held" : string.Join("; ", acts.Select(a => a.ToString()));
                sb.AppendLine($"r{round} {mover.Name} {from}->{mover.Position}: {did}");
                continue;
            }

            Turn(sb, battle, commander, mover, everyone);
        }

        sb.AppendLine();
        var recce = battle.ObjectiveOf(read) as Reconnaissance;
        var alarm = battle.Awareness.AlarmOf(read == Side.Player ? Side.Hostile : Side.Player);
        sb.AppendLine(
            $"{battle.VerdictFor(read).ToString().ToLowerInvariant()} at round {battle.Round}; " +
            $"looked {(recce?.Confirmed is { } c ? $"r{c.Round} by {c.By.Name}" : "never")}; " +
            $"alarm {(alarm is { } a ? $"r{a.Round} by {battle.GetUnit(a.Raised)?.Name}" : "never")}; " +
            $"standing {string.Join(", ", everyone.Where(u => u.InPlay).Select(u => $"{u.Name} {u.Vitality}"))}; " +
            $"left {string.Join(", ", everyone.Where(u => u.Left is not null).Select(u => $"{u.Name} {u.Left}"))}");

        return sb.ToString();
    }

    private static void Turn(StringBuilder sb, Battle battle, Commander commander, Unit mover, IReadOnlyList<Unit> everyone)
    {
        var judge = commander.Judge;
        var enemies = everyone.Where(u => u.InPlay && u.IsHostileTo(mover)).ToList();

        sb.AppendLine($"r{battle.Round} {mover.Name} at {mover.Position} {mover.Stance.ToString().ToLowerInvariant()} facing {mover.Facing}, {mover.ActionPoints} AP, {mover.Vitality} vit");

        var held = enemies.Select(e =>
        {
            var contact = battle.Awareness.Of(e.Id, mover.Id);
            return $"{e.Name} {contact.State.ToString().ToLowerInvariant()} {contact.Detection:0}{(contact.EyesOn ? " eyes on" : "")}";
        });
        sb.AppendLine($"    held on him: {string.Join(", ", held)}");

        var known = judge.Known(mover).ToList();
        var sensed = judge.Sensed(mover).Where(t => known.All(k => k.Unit != t.Unit)).ToList();
        sb.AppendLine($"    knows: {(known.Count == 0 ? "nobody" : string.Join(", ", known))}");
        if (sensed.Count > 0) sb.AppendLine($"    senses too: {string.Join(", ", sensed)}");

        // What each registered enemy would make of him standing where he stands, per look.
        var here = UnitPose.Of(mover);
        var eyes = judge.Sensed(mover).Select(t => (t.Unit.Name, Look: t.EyesOn || t.FacingKnown
                ? battle.Awareness.WouldNotice(t.Unit, t.Where, here)
                : battle.Awareness.WouldNoticeFacingAnyWay(t.Unit, t.Where, here)))
            .Where(e => e.Look > 0)
            .Select(e => $"{e.Name} {e.Look:0.0}");
        sb.AppendLine($"    a look at him here is worth: {(eyes.Any() ? string.Join(", ", eyes) : "nothing to anybody")}; quiet {judge.Quiet(mover, here, judge.Sensed(mover)):0.00}");

        while (battle.Active == mover)
        {
            var threats = judge.Known(mover).ToList();
            var holding = judge.AppraiseHolding(mover, mover.ActionPoints, threats);
            var all = commander.Options(mover, threats).OrderByDescending(o => o.Score).ToList();
            var options = all.Take(Shown).ToList();

            // The best move is always worth seeing, because a squad that will not go anywhere is
            // the finding most worth reading the reasons for — and so are the two moves that
            // would have taken it furthest toward the job, whatever they cost.
            if (options.All(o => o.Kind != OrderKind.Move) && all.FirstOrDefault(o => o.Kind == OrderKind.Move) is { } bestMove)
                options.Add(bestMove);

            foreach (var forward in all
                         .Where(o => o.Kind == OrderKind.Move && !options.Contains(o))
                         .OrderByDescending(o => judge.TowardObjective(mover, o.MoveTo!.Value))
                         .Take(2))
                options.Add(forward);

            if (options.Count > 0)
            {
                sb.AppendLine($"    holding is worth {holding.Score:+0.00;-0.00}; on the table ({all.Count}):");
                var reach = battle.Reachable(mover);
                foreach (var option in options) sb.AppendLine($"      {Describe(battle, judge, mover, reach, option)}");
            }

            var act = commander.Step();
            if (act is null)
            {
                sb.AppendLine("    -> holds");
                break;
            }

            var outcome = act.Fired is { } shot ? $" [{shot}]"
                : act.Threw is { } blast ? $" [{blast}]"
                : act.Moved is { } moved && moved.Reactions is { } window && window.Resolutions.Count > 0
                    ? $" [{string.Join("; ", window.Resolutions)}]"
                    : "";
            sb.AppendLine($"    -> {act}{outcome}");

            if (!act.Carried) break;
        }

        if (battle.Active == mover && battle.IsRunning) battle.EndTurn();
    }

    /// <summary>
    /// One option with its terms, and for a move the two halves that are otherwise lost in
    /// <c>Prospect</c>: what the pose keeps of the mission and what the ground is worth.
    /// </summary>
    private static string Describe(Battle battle, Tactician judge, Unit mover, ReachabilityResult reach, Order option)
    {
        var line = $"{option,-40} worth {option.Worth}";
        if (option.Opens is { } opens && opens.Score != 0) line += $" opens {opens}";

        if (option.Kind != OrderKind.Move || option.MoveTo is not { } to) return line;

        if (!reach.TryGetPath(to, out var path)) return line;

        var timeline = new CommittedMove(mover.Position, path, mover.Facing, mover.Stance);
        var route = timeline.ArrivalTicks.Select(timeline.PoseAt).ToList();
        var arriving = route[^1];
        var heard = battle.Awareness.WouldHear(mover, to, battle.Loudness(mover, path)).ToList();

        var before = UnitPose.Of(mover);
        var keep = judge.Keeping(mover, before, arriving, heard, route);
        var arrivalOnly = judge.Keeping(mover, before, arriving, heard);
        var toward = judge.TowardObjective(mover, to) - judge.TowardObjective(mover, mover.Position);

        var worst = judge.Foreseen(mover, arriving, judge.Sensed(mover), heard, route)
            .OrderByDescending(kv => kv.Value)
            .Select(kv => $"{battle.GetUnit(kv.Key)?.Name} {kv.Value:0}")
            .FirstOrDefault() ?? "nobody";

        return line + $" | keep {keep:+0.0;-0.0} (crossing {keep - arrivalOnly:+0.0;-0.0}) toward {toward:+0.0;-0.0} heard by {heard.Count}; worst {worst}";
    }
}

/// <summary>
/// The waystation, one seed, read closely — briefed unless told otherwise.
/// </summary>
/// <remarks>
/// Entry 087 found that a briefed squad's scout goes in unseen and its followers start a war, and
/// asked for a transcript of a briefed match before anything was changed about it. The content
/// harness's transcript does not brief; this one runs the instrument arm.
/// </remarks>
public class OneWaystationMatchReadClosely(ITestOutputHelper output)
{
    [TranscriptFact]
    public void Read()
    {
        var seed = Transcript.Seed!.Value;
        var ours = Transcript.Value is { } value ? UtilityModel.Default with { ObjectiveValue = value } : null;
        var battle = Waystation.Begin(seed, briefed: !Transcript.Blind);

        output.WriteLine($"seed {seed}, {(Transcript.Blind ? "blind" : "briefed")}, objective worth {ours?.ObjectiveValue ?? UtilityModel.Default.ObjectiveValue:0}");
        output.WriteLine(Transcript.Of(battle, ours));
    }
}
