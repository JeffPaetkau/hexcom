using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;

namespace Hexcom.Content.Tests;

/// <summary>One soldier's turn, as the recorder saw it.</summary>
public sealed record TurnRecord(int Round, string Unit, Side Side, NodeId From, NodeId To, IReadOnlyList<Order> Orders);

/// <summary>Somebody going down: who, when, where, and who was shooting at the time.</summary>
public sealed record Casualty(int Round, string Unit, Side Side, NodeId Where, string By);

/// <summary>The job in the middle of a sortie: where it was, whether it was done, and by whom.</summary>
/// <param name="Where">The node the objective points at, or null for a sortie with no job.</param>
/// <param name="By">Who did it and in which round, or null if nobody did.</param>
public sealed record TaskRecord(string Brief, NodeId? Where, bool Done, (string Unit, int Round)? By)
{
    public override string ToString()
        => By is { } who ? $"done by {who.Unit} in round {who.Round}"
            : Done ? "done"
            : Where is { } at ? $"not done; the job was at {at}"
            : "nothing to do but leave";
}

/// <summary>
/// What one match came to. Everything a reader needs to say where the fighting happened,
/// which is the question the first battlefield brief asks and the win check does not answer.
/// </summary>
/// <param name="Verdict">
/// How it came out for the side that had orders, or <c>Undecided</c> for a match that ran out of
/// rounds. Entry 041: a battle settles on its objective now, and a mission that ends because
/// somebody walked off the field looks nothing like one that ends because a side was wiped out.
/// </param>
/// <param name="Departures">How each soldier left the field, and what the enemy held on them as they went.</param>
/// <param name="Task">
/// What the thing in the middle of the mission came to, or null for an objective with nothing in
/// the middle of it. A verdict alone cannot tell a squad that never got near the job from one that
/// did it and was seen walking home, and those are opposite findings about the same map — so
/// since entry 061 put something in the middle, the recorder writes down whether it was done.
/// </param>
public sealed record MatchReport(
    int Seed,
    bool Decided,
    Side? Winner,
    Verdict Verdict,
    int Rounds,
    int Turns,
    double Seconds,
    IReadOnlyList<TurnRecord> TurnLog,
    IReadOnlyList<Casualty> Casualties,
    IReadOnlyDictionary<string, AwarenessState> AlarmPeaks,
    IReadOnlyDictionary<string, int> Standing,
    IReadOnlyDictionary<string, Departure> Departures,
    TaskRecord? Task)
{
    /// <summary>Whether it settled on the objective rather than on the round cap.</summary>
    public bool Settled => Verdict != Verdict.Undecided;

    public int Shots => TurnLog.Sum(t => t.Orders.Count(o => o.Kind == OrderKind.Fire));
    public int Throws => TurnLog.Sum(t => t.Orders.Count(o => o.Kind == OrderKind.Throw));
    public TurnRecord? FirstShot => TurnLog.FirstOrDefault(t => t.Orders.Any(o => o.Kind is OrderKind.Fire or OrderKind.Throw));

    /// <summary>The last round in which anybody fired or threw; after it the match is a stalemate.</summary>
    public int LastFire => TurnLog.Where(t => t.Orders.Any(o => o.Kind is OrderKind.Fire or OrderKind.Throw)).Select(t => t.Round).DefaultIfEmpty(0).Max();

    /// <summary>Every charge thrown: who, when, and at what piece of ground.</summary>
    public IEnumerable<(int Round, string Unit, NodeId At)> ThrowsMade
        => TurnLog.SelectMany(t => t.Orders.Where(o => o.Kind == OrderKind.Throw).Select(o => (t.Round, t.Unit, o.Throw!.Aimed)));

    /// <summary>
    /// Turns spent pacing: four or more moves and nothing fired. A soldier ranked on the shot a
    /// move would open, who then finds a better move back, walks between two tiles all turn.
    /// </summary>
    public IEnumerable<TurnRecord> PacingTurns
        => TurnLog.Where(t => t.Orders.Count(o => o.Kind == OrderKind.Move) >= 4 && !t.Orders.Any(o => o.Kind is OrderKind.Fire or OrderKind.Throw));

    /// <summary>Every node a soldier stood on at the end of a turn, in order.</summary>
    public IEnumerable<NodeId> RouteOf(string unit)
        => TurnLog.Where(t => t.Unit == unit).Select(t => t.To);
}

/// <summary>
/// Runs a match with <see cref="Commander"/> on both sides and writes down what happened.
/// </summary>
/// <remarks>
/// A skirmish test asserts a decision; this records the road to one. The two things it keeps
/// that the battle itself throws away are where everybody was at the end of each turn — the
/// route — and the highest rung each hostile ever reached about each of ours, sampled every turn
/// because <c>Battle.Withdraw</c> forgets a contact the moment its holder goes down (entry 030).
/// The round cap is an instrument, not a rule: a match that hits it is reported as undecided,
/// which is a finding about the AI and the map rather than a failure of the recorder.
/// </remarks>
public static class MatchRecorder
{
    public static MatchReport Play(Battle battle, int seed, int roundCap = 60, Side orders = Side.Player)
    {
        var commander = new Commander(battle);
        var log = new List<TurnRecord>();
        var casualties = new List<Casualty>();
        var peaks = new Dictionary<string, AwarenessState>();
        var watch = Stopwatch.StartNew();
        var turns = 0;

        var everyone = battle.Units.ToList();
        var ours = everyone.Where(u => u.Side == Side.Player).ToList();
        var theirs = everyone.Where(u => u.Side == Side.Hostile).ToList();

        while (battle.IsRunning && !battle.IsDecided && battle.Round <= roundCap)
        {
            var mover = battle.Active!;
            var from = mover.Position;
            var round = battle.Round;
            var standingBefore = everyone.Where(u => u.InPlay).ToList();

            // Core change, kept to one line: TakeTurn hands back an Act per order now, with the
            // outcome beside it. The record still wants only the orders; see decisions.md entry
            // 040, and note that Act carries what each one did if this recorder ever wants it.
            var acts = commander.TakeTurn();
            turns++;

            log.Add(new TurnRecord(
                round, mover.Name, mover.Side, from, mover.Position, [.. acts.Select(a => a.Order)]));

            // Left is what tells a body from a soldier who walked off, and until objectives
            // existed nothing had to — InPlay is false for both. Entry 030.
            foreach (var fallen in standingBefore.Where(u => u.Left?.Kind == DepartureKind.Down))
                casualties.Add(new Casualty(round, fallen.Name, fallen.Side, fallen.Position, mover.Name));

            foreach (var hostile in theirs.Where(h => h.InPlay))
            foreach (var mine in ours)
            {
                var state = battle.Awareness.ReadoutFor(hostile.Id, mine.Id).State;
                var key = $"{hostile.Name}>{mine.Name}";
                if (!peaks.TryGetValue(key, out var best) || state > best) peaks[key] = state;
            }
        }

        watch.Stop();

        var sides = battle.SidesInPlay.ToList();
        return new MatchReport(
            seed,
            battle.IsDecided,
            sides.Count == 1 ? sides[0] : null,
            battle.VerdictFor(orders),
            battle.Round,
            turns,
            watch.Elapsed.TotalSeconds,
            log,
            casualties,
            peaks,
            everyone.ToDictionary(u => u.Name, u => u.InPlay ? u.Vitality : 0),
            everyone.Where(u => u.Left is not null).ToDictionary(u => u.Name, u => u.Left!),
            TaskOf(battle, orders));
    }

    /// <summary>What the side with orders was asked to do besides leave, and whether it did it.</summary>
    private static TaskRecord? TaskOf(Battle battle, Side side)
    {
        if (battle.ObjectiveOf(side) is not Sortie sortie) return null;

        var by = sortie is Reconnaissance { Confirmed: { } seen } ? (seen.By.Name, seen.Round) : ((string, int)?)null;
        return new TaskRecord(sortie.Brief, sortie.Place, sortie.Done, by);
    }

    /// <summary>A named piece of ground, so a route can be read as a story.</summary>
    public sealed record Landmark(string Name, Func<NodeId, bool> Holds);

    /// <summary>
    /// Every place a mission names, as a landmark.
    /// </summary>
    /// <remarks>
    /// A <c>place</c> is most of what a landmark is: a name a briefing can say and a set of tiles
    /// on a storey. The recorder used to carry the waystation's as a hand-written list of hexes,
    /// which was the one thing in it that would not fight a second map. What a mission does not
    /// name — a drain, a ford — a harness adds beside these.
    /// </remarks>
    public static IReadOnlyList<Landmark> PlacesOf(Mission mission)
        => [.. mission.Places.Select(p => new Landmark(p.Key, n => p.Value.Contains(n.Tile)))];

    /// <summary>One match, as a few lines a person can read.</summary>
    public static string Describe(MatchReport r, IReadOnlyList<Landmark> landmarks)
    {
        var sb = new StringBuilder();
        var outcome = r.Settled ? r.Verdict.ToString().ToLowerInvariant() : r.Decided ? $"decided for {r.Winner}" : "UNDECIDED";
        sb.AppendLine($"seed {r.Seed}: {outcome} at round {r.Rounds} after {r.Turns} turns, {r.Seconds:F1} s; {r.Shots} shots, {r.Throws} throws, last fire round {r.LastFire}");

        // Before the routes, because it is the question the routes are read to answer: an
        // abandoned match where the look was taken and an abandoned match where nobody went near
        // the house are opposite findings and the verdict calls them the same thing.
        if (r.Task is { } task) sb.AppendLine($"  task: {task}");

        if (r.FirstShot is { } first)
        {
            var order = first.Orders.First(o => o.Kind is OrderKind.Fire or OrderKind.Throw);
            sb.AppendLine($"  first fire: round {first.Round}, {first.Unit} at {first.To} — {order}");
        }

        var throws = r.ThrowsMade.Select(t => $"r{t.Round} {t.Unit} at {t.At}");
        if (throws.Any()) sb.AppendLine($"  throws: {string.Join(", ", throws)}");

        var pacing = r.PacingTurns.GroupBy(t => t.Unit).Select(g => $"{g.Key} {g.Count()} turns");
        if (pacing.Any()) sb.AppendLine($"  pacing: {string.Join(", ", pacing)}");

        foreach (var (name, left) in r.Departures.Where(d => d.Value.Kind == DepartureKind.Extracted))
            sb.AppendLine($"  off: {name} in round {left.Round}, with the other side at {left.Noticed}");

        foreach (var c in r.Casualties)
            sb.AppendLine($"  down: {c.Unit} ({c.Side}) round {c.Round} at {c.Where}, on {c.By}'s turn");

        var standing = string.Join(", ", r.Standing.Where(kv => kv.Value > 0).Select(kv => $"{kv.Key} {kv.Value}"));
        sb.AppendLine($"  standing: {standing}");

        var peaks = r.AlarmPeaks.Where(kv => kv.Value > AwarenessState.Unaware)
            .OrderByDescending(kv => kv.Value)
            .Select(kv => $"{kv.Key} {kv.Value}");
        sb.AppendLine($"  alarm peaks: {string.Join(", ", peaks)}");

        foreach (var unit in r.TurnLog.Select(t => t.Unit).Distinct())
        {
            var route = r.RouteOf(unit).ToList();
            var visited = landmarks.Where(l => route.Any(l.Holds)).Select(l => l.Name);
            var moved = r.TurnLog.Count(t => t.Unit == unit && t.From != t.To);
            sb.AppendLine($"  {unit}: {moved} moves, ended at {route.Last()}; {(visited.Any() ? string.Join(", ", visited) : "nowhere named")}");
        }

        return sb.ToString();
    }

    /// <summary>The whole turn log, for reading one match closely.</summary>
    public static string Transcript(MatchReport r)
    {
        var sb = new StringBuilder();
        foreach (var t in r.TurnLog)
        {
            var did = t.Orders.Count == 0 ? "held" : string.Join("; ", t.Orders.Select(o => o.ToString()));
            sb.AppendLine($"r{t.Round} {t.Unit} {t.From}->{t.To}: {did}");
        }
        return sb.ToString();
    }
}
