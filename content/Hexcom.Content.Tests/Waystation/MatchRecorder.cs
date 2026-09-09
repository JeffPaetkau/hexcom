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

namespace Hexcom.Content.Tests.Waystation;

/// <summary>One soldier's turn, as the recorder saw it.</summary>
public sealed record TurnRecord(int Round, string Unit, Side Side, NodeId From, NodeId To, IReadOnlyList<Order> Orders);

/// <summary>Somebody going down: who, when, where, and who was shooting at the time.</summary>
public sealed record Casualty(int Round, string Unit, Side Side, NodeId Where, string By);

/// <summary>
/// What one match came to. Everything a reader needs to say where the fighting happened,
/// which is the question the first battlefield brief asks and the win check does not answer.
/// </summary>
public sealed record MatchReport(
    int Seed,
    bool Decided,
    Side? Winner,
    int Rounds,
    int Turns,
    double Seconds,
    IReadOnlyList<TurnRecord> TurnLog,
    IReadOnlyList<Casualty> Casualties,
    IReadOnlyDictionary<string, AwarenessState> AlarmPeaks,
    IReadOnlyDictionary<string, int> Standing)
{
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
    public static MatchReport Play(Battle battle, int seed, int roundCap = 60)
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

            var orders = commander.TakeTurn();
            turns++;

            log.Add(new TurnRecord(round, mover.Name, mover.Side, from, mover.Position, orders));

            foreach (var fallen in standingBefore.Where(u => !u.InPlay))
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
            battle.Round,
            turns,
            watch.Elapsed.TotalSeconds,
            log,
            casualties,
            peaks,
            everyone.ToDictionary(u => u.Name, u => u.InPlay ? u.Vitality : 0));
    }

    /// <summary>A named place on the waystation, so a route can be read as a story.</summary>
    public sealed record Landmark(string Name, Func<NodeId, bool> Holds);

    /// <summary>The places the brief asked about, and a few more the map has.</summary>
    public static IReadOnlyList<Landmark> WaystationLandmarks(BattleMap map) =>
    [
        new("the drain", n => n.Layer == 0 && (n.Hex == new Hex(-1, -3) || n.Hex == new Hex(-1, -4))),
        new("the bridge", n => n.Layer == 0 && n.Hex == new Hex(-8, 0)),
        new("the ridge", n => n.Layer == 0 && map.GetTile(n.Tile)?.FloorHeight > 1.0),
        new("the west wood", n => n.Layer == 0 && n.Hex.DistanceTo(new Hex(-6, -14)) <= 1),
        new("the east wood", n => n.Layer == 0 && n.Hex.DistanceTo(new Hex(14, 6)) <= 2),
        new("inside the compound", n => n.Layer == 0 && n.Hex.DistanceTo(Hex.Zero) <= 4),
        new("the house roof", n => n.Layer == 1 && n.Hex.DistanceTo(new Hex(0, 1)) <= 1),
        new("the barn", n => n.Layer == 0 && n.Hex.DistanceTo(new Hex(14, -6)) <= 2),
        new("the cottages", n => n.Layer == 0 && (n.Hex == new Hex(-14, 6) || n.Hex == new Hex(-14, 7) || n.Hex == new Hex(-13, 6))),
        new("the tower", n => n.Layer == 1 && n.Hex == new Hex(16, -14)),
        new("the ford", n => n.Layer == 0 && n.Hex == new Hex(-6, -4)),
        new("the pond", n => n.Layer == 0 && n.Hex.DistanceTo(new Hex(6, -16)) <= 2 && map.GetTile(n.Tile)?.Ground == GroundType.ShallowWater),
        new("the tree line", n => n.Layer == 0 && n.Hex.Q == -12 && n.Hex.R is >= -2 and <= 5),
    ];

    /// <summary>One match, as a few lines a person can read.</summary>
    public static string Describe(MatchReport r, BattleMap map)
    {
        var sb = new StringBuilder();
        var outcome = r.Decided ? $"decided for {r.Winner}" : "UNDECIDED";
        sb.AppendLine($"seed {r.Seed}: {outcome} at round {r.Rounds} after {r.Turns} turns, {r.Seconds:F1} s; {r.Shots} shots, {r.Throws} throws, last fire round {r.LastFire}");

        if (r.FirstShot is { } first)
        {
            var order = first.Orders.First(o => o.Kind is OrderKind.Fire or OrderKind.Throw);
            sb.AppendLine($"  first fire: round {first.Round}, {first.Unit} at {first.To} — {order}");
        }

        var throws = r.ThrowsMade.Select(t => $"r{t.Round} {t.Unit} at {t.At}");
        if (throws.Any()) sb.AppendLine($"  throws: {string.Join(", ", throws)}");

        var pacing = r.PacingTurns.GroupBy(t => t.Unit).Select(g => $"{g.Key} {g.Count()} turns");
        if (pacing.Any()) sb.AppendLine($"  pacing: {string.Join(", ", pacing)}");

        foreach (var c in r.Casualties)
            sb.AppendLine($"  down: {c.Unit} ({c.Side}) round {c.Round} at {c.Where}, on {c.By}'s turn");

        var standing = string.Join(", ", r.Standing.Where(kv => kv.Value > 0).Select(kv => $"{kv.Key} {kv.Value}"));
        sb.AppendLine($"  standing: {standing}");

        var peaks = r.AlarmPeaks.Where(kv => kv.Value > AwarenessState.Unaware)
            .OrderByDescending(kv => kv.Value)
            .Select(kv => $"{kv.Key} {kv.Value}");
        sb.AppendLine($"  alarm peaks: {string.Join(", ", peaks)}");

        var landmarks = WaystationLandmarks(map);
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
