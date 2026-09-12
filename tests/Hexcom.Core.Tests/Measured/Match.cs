using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;

namespace Hexcom.Core.Tests.Measured;

/// <summary>
/// What one headless match came to, in the quantities a dial is argued about in.
/// </summary>
/// <remarks>
/// Deliberately not a turn log. A batch is hundreds of matches and the questions it answers are
/// all counts — how often the job got done, how much shooting there was on the way, how far the
/// squad got before it stopped. Keeping every order of every turn for four hundred matches is
/// tens of megabytes of detail nobody reads, and the one existing recorder that does keep it is
/// for reading a single match closely. Both exist because they are different instruments.
/// </remarks>
/// <param name="Confirmed">
/// The round the look landed, or null if it never did. The one reading that says whether the
/// squad went and did the job at all, as against fighting near where it started.
/// </param>
/// <param name="Alarm">The round the hostile side's word got out, or null if it never did.</param>
/// <param name="Closest">
/// How near the nearest of ours ever got to the thing they came to look at, in hexes. A squad that
/// never sets off reads twenty here; one that walks into the compound reads nought.
/// </param>
/// <param name="FirstAimedAt">
/// The first hostile ours shot or threw at, by name, or null if they never fired. What the scorer
/// preferred, which is the only way to ask what removing a signaller is worth to it: the garrison
/// has one man with a set and three without, standing on the same ground.
/// </param>
/// <param name="FirstDown">The first hostile put down, by name, or null if none were.</param>
/// <param name="Noticed">The highest rung any hostile ever held on any of ours, sampled per turn.</param>
/// <param name="Peaks">
/// The same reading per soldier, by name. Entry 048 read the scout as the one nobody notices and
/// the trooper as the one everybody does, and nobody established whether that is the man or the
/// post he was given — which is a question only a per-soldier reading can answer.
/// </param>
public sealed record MatchOutcome(
    int Seed,
    Verdict Verdict,
    int Rounds,
    int Turns,
    double Seconds,
    int? Confirmed,
    int? Alarm,
    int OurShots,
    int TheirShots,
    int OurThrows,
    int TheirThrows,
    int OurLosses,
    int TheirLosses,
    int Extracted,
    int Closest,
    string? FirstAimedAt,
    string? FirstDown,
    AwarenessState Noticed,
    IReadOnlyDictionary<string, AwarenessState> Peaks)
{
    /// <summary>Whether it settled on the objective rather than running out of rounds.</summary>
    public bool Settled => Verdict != Verdict.Undecided;

    /// <summary>Whether anybody at all fired or threw anything.</summary>
    public bool Quiet => OurShots + TheirShots + OurThrows + TheirThrows == 0;
}

/// <summary>
/// Plays a battle out with a <see cref="Commander"/> on each side and writes down the totals.
/// </summary>
/// <remarks>
/// A commander per side rather than one for both, which is the whole reason this exists beside
/// the recorder in <c>content/</c>. Every question in this brief is of the form <em>what does
/// this dial do</em>, and a dial turned on both sides at once measures nothing: the two halves
/// move together and the match comes out where it started. So the side under test gets the model
/// being tried and the other side keeps the shipped one.
/// <para>
/// The turn loop is the one <see cref="Commander"/> already imposes — it drives whoever is active
/// and ends that soldier's turn — so all this does is pick which of the two commanders is asked.
/// </para>
/// </remarks>
public static class Match
{
    /// <summary>
    /// Fight it out and report the totals. Stops when the battle is decided, when nobody is left
    /// to act, or at <paramref name="roundCap"/>.
    /// </summary>
    /// <param name="roundCap">
    /// A backstop, not the mission clock. A mission with a <see cref="Deadline"/> ends itself and
    /// never reaches this; one without it would otherwise run until a stalemate ran out of
    /// patience, and a batch cannot afford to wait.
    /// </param>
    public static MatchOutcome Play(
        Battle battle,
        int seed,
        UtilityModel? ours = null,
        UtilityModel? theirs = null,
        int roundCap = 60)
    {
        var commanders = new Dictionary<Side, Commander>
        {
            [Side.Player] = new Commander(battle, ours),
            [Side.Hostile] = new Commander(battle, theirs),
        };

        var watch = Stopwatch.StartNew();
        var everyone = battle.Units.ToList();
        var mine = everyone.Where(u => u.Side == Side.Player).ToList();
        var yours = everyone.Where(u => u.Side == Side.Hostile).ToList();

        var counts = new Dictionary<(Side, OrderKind), int>();
        var peaks = mine.ToDictionary(u => u.Name, _ => AwarenessState.Unaware);
        var noticed = AwarenessState.Unaware;
        var closest = int.MaxValue;
        string? firstDown = null;
        string? firstAimedAt = null;
        var turns = 0;

        var place = (battle.ObjectiveOf(Side.Player) as Sortie)?.Place;

        while (battle.IsRunning && !battle.IsDecided && battle.Round <= roundCap)
        {
            var mover = battle.Active!;
            var standing = yours.Where(u => u.InPlay).ToList();

            foreach (var act in commanders[mover.Side].TakeTurn())
            {
                var key = (mover.Side, act.Kind);
                counts[key] = counts.GetValueOrDefault(key) + 1;

                if (mover.Side != Side.Player || firstAimedAt is not null) continue;

                firstAimedAt = act.Order.Shot?.Target.Name
                    ?? (act.Kind == OrderKind.Throw ? Nearest(yours, act.Order.Throw!.Aimed) : null);
            }

            turns++;

            // Sampled per turn, because Withdraw makes the tracker forget everything about a unit
            // the moment it leaves — so the peak cannot be read at the end. Entry 030.
            foreach (var hostile in yours.Where(u => u.InPlay))
                foreach (var friend in mine)
                {
                    var state = battle.Awareness.ReadoutFor(hostile.Id, friend.Id).State;
                    if (state > noticed) noticed = state;
                    if (state > peaks[friend.Name]) peaks[friend.Name] = state;
                }

            if (place is { } target)
                foreach (var friend in mine.Where(u => u.InPlay))
                    closest = Math.Min(closest, friend.Position.Hex.DistanceTo(target.Hex));

            firstDown ??= standing
                .FirstOrDefault(u => u.Left?.Kind == DepartureKind.Down)?.Name;
        }

        watch.Stop();

        var recce = battle.ObjectiveOf(Side.Player) as Reconnaissance;

        return new MatchOutcome(
            seed,
            battle.VerdictFor(Side.Player),
            battle.Round,
            turns,
            watch.Elapsed.TotalSeconds,
            recce?.Confirmed?.Round,
            battle.Awareness.AlarmOf(Side.Hostile)?.Round,
            counts.GetValueOrDefault((Side.Player, OrderKind.Fire)),
            counts.GetValueOrDefault((Side.Hostile, OrderKind.Fire)),
            counts.GetValueOrDefault((Side.Player, OrderKind.Throw)),
            counts.GetValueOrDefault((Side.Hostile, OrderKind.Throw)),
            mine.Count(u => u.Left?.Kind == DepartureKind.Down),
            yours.Count(u => u.Left?.Kind == DepartureKind.Down),
            mine.Count(u => u.Left?.Kind == DepartureKind.Extracted),
            closest == int.MaxValue ? -1 : closest,
            firstAimedAt,
            firstDown,
            noticed,
            peaks);
    }

    /// <summary>
    /// Who a charge was meant for: the nearest of them to the ground it was aimed at.
    /// </summary>
    /// <remarks>
    /// A throw is aimed at a place and not a person, so which enemy it was <em>for</em> has to be
    /// inferred. The commander only ever aims at the tile under a believed threat, so the nearest
    /// is the one it meant — and if the marker is stale and nobody is near it any more, that is
    /// still the enemy whose marker it was.
    /// </remarks>
    private static string? Nearest(IEnumerable<Unit> among, NodeId at) => among
        .OrderBy(u => u.Position.Hex.DistanceTo(at.Hex))
        .FirstOrDefault()?.Name;
}
