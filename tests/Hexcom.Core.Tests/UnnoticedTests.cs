using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// A squad that is not seen. These read as the judgements a soldier makes on a mission whose
/// win condition is a rung on the awareness ladder: what stepping into a sentry's eye costs,
/// what a shot costs once he has you anyway, and what the hour closing does to the walk home.
/// </summary>
/// <remarks>
/// Entry 083 measured what this scorer did before any of it existed: a hundred paired seeds on
/// the waystation in every arm, the squad held at Engaged in every match, the mission achieved
/// twice in two thousand four hundred. The objective paid for getting there and getting home,
/// and nothing paid for getting there unseen.
/// </remarks>
public class UnnoticedTests
{
    private static NodeId Node(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    private static NodeId Along(HexDirection direction, int steps) => new(Hex.Zero + direction.Offset() * steps, 0);

    /// <summary>Always goes first.</summary>
    private static readonly UnitStats Quick = UnitStats.Default with { Initiative = 30 };

    /// <summary>Always goes last, and never looks before the test has had its say.</summary>
    private static readonly UnitStats Slow = UnitStats.Default with { Initiative = 1 };

    private static Battle Field(int seed = 1)
        => new(new BattleMap().FillDisc(Hex.Zero, 16), new HexLayout(size: 1.0), seed: seed);

    private static double Objective => UtilityModel.Default.ObjectiveValue;

    // ---- stepping into an eye ----------------------------------------------------

    /// <summary>
    /// The term itself. A sentry looking north, and a scout weighing two hexes at the same
    /// distance from him: one straight in front, one straight behind. The first hands him most
    /// of a look and costs most of the mission; the second hands him the corner of an eye.
    /// </summary>
    [Fact]
    public void SteppingIntoASentrysEyeCostsTheMissionAndSteppingBehindHimBarelyDoes()
    {
        var (battle, sentry, scout) = Posted(AwarenessState.Suspicious);
        var before = UnitPose.Of(scout);

        var inFront = before with { Position = Along(HexDirection.North, 3) };
        var behind = before with { Position = Along(HexDirection.South, 3) };

        Assert.Equal(1.0, battle.Awareness.AttentionOn(sentry, inFront.Position));
        Assert.Equal(battle.Awareness.Model.RearAcuity, battle.Awareness.AttentionOn(sentry, behind.Position));

        var front = battle.Tactics.Keeping(scout, before, inFront);
        var rear = battle.Tactics.Keeping(scout, before, behind);

        Assert.True(front < -Objective / 2, $"in front should cost most of the mission, not {front:0.0}");
        Assert.True(rear > -Objective / 10, $"behind should cost a sliver of it, not {rear:0.0}");
        Assert.True(front < rear);

        // And a walk is a posture with a noise attached, so the same ordering comes out of the
        // move appraisal the search actually ranks on.
        var reach = battle.Reachable(scout);
        Assert.True(
            battle.Tactics.AppraiseMove(scout, inFront, reach.CostTo(inFront.Position)!.Value, 0, []).Prospect
            < battle.Tactics.AppraiseMove(scout, behind, reach.CostTo(behind.Position)!.Value, 0, []).Prospect);
    }

    /// <summary>
    /// What the term is scaled by is the rung the mission tolerates, and a mission that tolerates
    /// the top of the ladder cannot be lost by being seen. Nor can a side with nothing to do.
    /// </summary>
    [Fact]
    public void AMissionThatCannotBeLostByBeingSeenPricesBeingSeenAtNothing()
    {
        var (battle, _, scout) = Posted(AwarenessState.Engaged);
        var before = UnitPose.Of(scout);
        var inFront = before with { Position = Along(HexDirection.North, 3) };

        Assert.Equal(0, battle.Tactics.Bar(scout));
        Assert.Equal(0, battle.Tactics.Keeping(scout, before, inFront));

        var loose = Field();
        var sentry = loose.Deploy("Kessel", Side.Hostile, Node(0, 0), Slow, HexDirection.North);
        var free = loose.Deploy("Vance", Side.Player, Along(HexDirection.South, 6), Quick, HexDirection.North);
        loose.Start();

        Assert.Equal(0, loose.Tactics.Bar(free));
        Assert.Equal(0, loose.Tactics.Keeping(free, UnitPose.Of(free), UnitPose.Of(free) with { Position = Along(HexDirection.North, 3) }));
        Assert.Equal(1.0, loose.Tactics.Quiet(free, UnitPose.Of(free), [Threat.At(sentry)]));
    }

    /// <summary>
    /// The briefing's own line: if the shift sees you the task is over. Once the sentry holds a
    /// soldier at the rung, there is nothing left of the mission for that soldier to keep, and
    /// the term says so — walking into his eye and firing both cost nothing more.
    /// </summary>
    [Fact]
    public void OnceTheSentryHasYouGoingLoudCostsTheMissionNothingMore()
    {
        var (battle, sentry, scout) = Posted(AwarenessState.Suspicious, Loadout.Rifleman);

        // By the one channel that settles it outright: he has been shot at from there.
        battle.Awareness.TakeFireFrom(sentry, scout, battle.Round);
        Assert.True(battle.Awareness.Of(sentry.Id, scout.Id).State >= AwarenessState.Searching);

        var before = UnitPose.Of(scout);
        var inFront = before with { Position = Along(HexDirection.North, 3) };

        Assert.Equal(0, battle.Tactics.Quiet(scout, before, battle.Tactics.Sensed(scout)));
        Assert.Equal(0, battle.Tactics.Keeping(scout, before, inFront), 9);

        var plan = battle.PlanShot(scout, sentry);
        Assert.True(plan.CanFire);
        Assert.Equal(0, battle.Tactics.Blowing(plan), 9);
    }

    /// <summary>
    /// A shot settles it for the man being shot at, so it hands the mission away — unless it
    /// drops him, in which case whatever he learned goes with him. That is the whole argument
    /// for the quiet kill, and a shot at somebody who will not survive it is priced accordingly.
    /// </summary>
    [Fact]
    public void AShotHandsTheMissionAwayUnlessItDropsTheOnlyManWhoHeardIt()
    {
        double Costs(UnitStats target)
        {
            var battle = Field();
            var gunner = battle.Deploy("Vance", Side.Player, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Rifleman);
            var sentry = battle.Deploy("Kessel", Side.Hostile, Node(3, 0), target, HexDirection.SouthWest);
            battle.SetObjective(new Withdrawal(Side.Player, [Node(-6, 0)]));
            battle.Start();

            var plan = battle.PlanShot(gunner, sentry);
            Assert.True(plan.CanFire);
            Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(sentry.Id, gunner.Id).State);

            var blowing = battle.Tactics.Blowing(plan);
            Assert.Equal(blowing, battle.Tactics.Appraise(plan).Prospect, 9);
            return blowing;
        }

        var sturdy = Costs(Slow);
        var fragile = Costs(Slow with { Vitality = 1 });

        Assert.True(sturdy <= -Objective * 0.99, $"a shot he survives settles it: {sturdy:0.0}");
        Assert.True(fragile > sturdy, $"a shot that drops him should cost less than {sturdy:0.0}, not {fragile:0.0}");
        Assert.True(fragile < 0, "but the round is not certain, so it is not free");
    }

    // ---- what the search does with it ----------------------------------------------

    /// <summary>
    /// The acceptance test, in miniature. A sentry looking south with the thing to look at
    /// behind him, and a scout coming up from behind who has registered him. Told not to be
    /// seen, the scout stays out of his eye; told nothing of the sort, the same scout on the
    /// same ground walks straight past him into it.
    /// </summary>
    [Fact]
    public void AScoutToldNotToBeSeenKeepsOutOfTheSentrysEyeWhereOneToldNothingWalksIntoIt()
    {
        UnitPose Ends(AwarenessState unnoticed, out Battle battle, out Unit sentry)
        {
            battle = Field();
            sentry = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Slow, HexDirection.South);
            var scout = battle.Deploy(
                "Vance", Side.Player, Along(HexDirection.North, 9), UnitStats.Scout with { Initiative = 30 }, HexDirection.South);

            battle.SetObjective(new Reconnaissance(
                Side.Player, Along(HexDirection.South, 9), [Along(HexDirection.North, 12)], unnoticed: unnoticed));
            battle.Start();

            // The scout has had a look at him and knows where he is standing.
            battle.Awareness.Notice(scout, sentry, UnitPose.Of(sentry), battle.Round);
            Assert.True(battle.Awareness.Of(scout.Id, sentry.Id).State >= AwarenessState.Suspicious);
            Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(sentry.Id, scout.Id).State);

            Assert.Same(scout, battle.Active);
            var acts = new Commander(battle).TakeTurn();
            Assert.Contains(acts, a => a.Kind == OrderKind.Move);

            return UnitPose.Of(scout);
        }

        var careful = Ends(AwarenessState.Suspicious, out var quiet, out var watched);
        var careless = Ends(AwarenessState.Engaged, out var loud, out var walkedPast);

        var lookAtCareful = quiet.Awareness.WouldNotice(watched, UnitPose.Of(watched), careful);
        var lookAtCareless = loud.Awareness.WouldNotice(walkedPast, UnitPose.Of(walkedPast), careless);

        Assert.Equal(1.0, loud.Awareness.AttentionOn(walkedPast, careless.Position));
        Assert.True(quiet.Awareness.AttentionOn(watched, careful.Position) < 1.0, $"the careful scout ended in his eye at {careful.Position}");
        Assert.True(lookAtCareful < lookAtCareless, $"{lookAtCareful:0.0} should be less of a look than {lookAtCareless:0.0}");
        Assert.True(lookAtCareful < quiet.Awareness.Model.Threshold(AwarenessState.Searching), "and short of the rung the mission is lost at");
    }

    /// <summary>
    /// The briefing, as a contact. A squad told before the fight that a man stands at the gate
    /// holds him as a marker at that post: something to keep out of the eye of, and something a
    /// soldier will go and check, from the first turn rather than the second.
    /// </summary>
    [Fact]
    public void ASquadBriefedAboutASentryStartsOutKnowingWhereHeStands()
    {
        var battle = Field();
        var sentry = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Slow, HexDirection.South);
        var scout = battle.Deploy("Vance", Side.Player, Along(HexDirection.North, 9), Quick, HexDirection.South);
        var mate = battle.Deploy("Orsini", Side.Player, Along(HexDirection.North, 10), Slow, HexDirection.South);
        battle.SetObjective(new Reconnaissance(Side.Player, Along(HexDirection.South, 9), [Along(HexDirection.North, 12)]));

        // Nothing is handed to the sentry about himself.
        Assert.Throws<ArgumentException>(() => battle.Brief(Side.Hostile, sentry, AwarenessState.Searching));

        battle.Brief(Side.Player, sentry, AwarenessState.Searching);
        battle.Start();

        foreach (var ours in new[] { scout, mate })
        {
            var threat = Assert.Single(battle.Tactics.Known(ours));
            Assert.Same(sentry, threat.Unit);
            Assert.False(threat.EyesOn, "a briefing is a marker, not a sighting");
            Assert.Equal(sentry.Position, threat.Where.Position);
            Assert.Equal(1.0, threat.Credence);
        }

        // And nothing was handed the other way.
        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(sentry.Id, scout.Id).State);

        // Told less than it already knows, a soldier keeps what it has.
        battle.Awareness.Brief(scout, sentry, Node(3, 3), AwarenessState.Suspicious);
        Assert.Equal(sentry.Position, battle.Tactics.Known(scout).Single().Where.Position);

        // Once the fight is under way it is too late to brief anybody.
        Assert.Throws<InvalidOperationException>(() => battle.Brief(Side.Player, sentry, AwarenessState.Alerted));
    }

    // ---- the hour closing ------------------------------------------------------------

    /// <summary>
    /// The clock as the scorer sees it. The same stride home is worth twice as much with two
    /// rounds left as with all night, because the slope is stretched to the shorter of the
    /// mission and the night — and nothing changes while the night is the longer.
    /// </summary>
    [Fact]
    public void WithTheHourClosingAStrideHomeIsWorthMoreThanWithAllNight()
    {
        double Stride(Deadline? clock, out Objective objective)
        {
            var battle = Field();
            battle.Deploy("Vance", Side.Player, Node(0, 0), Quick, HexDirection.NorthEast);
            battle.Deploy("Kessel", Side.Hostile, Node(0, -14), Slow, HexDirection.North);
            battle.SetObjective(new Withdrawal(Side.Player, [Node(12, 0)]) { Stop = clock });
            battle.Start();

            objective = battle.ObjectiveOf(Side.Player)!;
            return objective.Progress(battle, Node(1, 0)) - objective.Progress(battle, Node(0, 0));
        }

        var allNight = Stride(null, out var unhurried);
        var lateOn = Stride(new Deadline(Round: 2), out var hurried);
        var longNight = Stride(new Deadline(Round: 30), out var easy);

        Assert.Equal(1.0, unhurried.Urgency(Field()));
        Assert.Equal(allNight, longNight, 9);
        Assert.Equal(2.0 * allNight, lateOn, 9);
        Assert.True(hurried.PerPoint > 0);
    }

    /// <summary>
    /// The clock steepens the slope and never flattens it. A soldier further from home than the
    /// night allows is still drawn home, because walking out late is better for the squad than
    /// standing in the compound, and the verdict is already lost either way.
    /// </summary>
    [Fact]
    public void ASoldierWhoCannotMakeItHomeInTimeStillWantsHome()
    {
        var battle = Field();
        battle.Deploy("Vance", Side.Player, Node(0, 0), Quick, HexDirection.NorthEast);
        battle.Deploy("Kessel", Side.Hostile, Node(0, -14), Slow, HexDirection.North);
        battle.SetObjective(new Withdrawal(Side.Player, [Node(12, 0)]) { Stop = new Deadline(Round: 1) });
        battle.Start();

        var objective = battle.ObjectiveOf(Side.Player)!;
        Assert.True(objective.Owed(battle, Node(0, 0)) > objective.NightLeft(battle), "the whole point is that he cannot make it");

        Assert.True(objective.Progress(battle, Node(1, 0)) > objective.Progress(battle, Node(0, 0)));
        Assert.True(objective.Urgency(battle) > 1);
    }

    /// <summary>
    /// A stride spent on the charge and a stride walked toward it earn the same, and that has to
    /// stay true once the night is short: the rate is not constant any more, so the work is
    /// priced through the same two readings the walk is.
    /// </summary>
    [Fact]
    public void WorkingOnTheChargeEarnsWhatWalkingTheSamePointsEarnsHoweverLateItIs()
    {
        var battle = Field();
        var sapper = battle.Deploy("Vance", Side.Player, Node(0, 0), Quick, HexDirection.NorthEast);
        battle.Deploy("Kessel", Side.Hostile, Node(0, -14), Slow, HexDirection.North);

        var job = new Sabotage(Side.Player, Node(4, 0), [Node(-4, 0)], effort: 40) { Stop = new Deadline(Round: 2) };
        battle.SetObjective(job);
        battle.Start();

        Assert.True(job.Urgency(battle) > 1, "the clock has to be biting for this to say anything");

        var stride = MovementCosts.Default.Walk;
        var walked = Objective * (job.Progress(battle, Node(1, 0)) - job.Progress(battle, Node(0, 0)));

        Assert.Equal(walked, battle.Tactics.WorkWorth(sapper, stride), 6);
        Assert.NotEqual(Objective * job.PerPoint * stride, walked, 6);
    }

    /// <summary>
    /// What entry 083 measured the clock doing to a squad that could not see it: three rounds of
    /// grace ending most matches with fewer than half the squad home. With the hour closing a
    /// soldier who could stand and trade walks instead.
    /// </summary>
    [Fact]
    public void ASoldierWithTheJobDoneAndTheHourClosingGoesRatherThanStandsAndTrades()
    {
        var battle = Field();
        var gunner = battle.Deploy("Vance", Side.Player, Node(0, 0), Quick, HexDirection.NorthEast, Loadout.Rifleman);
        var sentry = battle.Deploy("Kessel", Side.Hostile, Node(4, 0), Slow, HexDirection.SouthWest, Loadout.Rifleman);

        // A mission that being seen cannot cost, so that the only thing in the way of the shot
        // is the clock; and an exit a turn's walk the other way.
        battle.SetObjective(new Withdrawal(Side.Player, [Node(-8, 0)], unnoticed: AwarenessState.Engaged)
        {
            Stop = new Deadline(Round: 1),
        });
        battle.Start();

        for (var i = 0; i < 3; i++) battle.Awareness.Notice(gunner, sentry, UnitPose.Of(sentry), battle.Round);
        Assert.Contains(battle.Tactics.Known(gunner), t => t.Unit == sentry && t.EyesOn);

        // At a value where the squad still weighs what is in front of it, the shot is on the
        // table and would be taken with all night.
        var fighting = UtilityModel.Default with { ObjectiveValue = 30 };
        var commander = new Commander(battle, fighting);
        var shot = commander.Options(gunner, commander.Judge.Known(gunner).ToList()).Where(o => o.Kind == OrderKind.Fire).MaxBy(o => o.Score);
        Assert.NotNull(shot);
        Assert.True(shot!.Score > 0);

        var acts = commander.TakeTurn();

        Assert.DoesNotContain(acts, a => a.Kind == OrderKind.Fire);
        Assert.Contains(acts, a => a.Kind == OrderKind.Move);
        Assert.True(gunner.Position.Hex.DistanceTo(new Hex(-8, 0)) < 8, $"he should have walked toward the exit, not to {gunner.Position}");
    }

    // ---- setting up ------------------------------------------------------------------

    /// <summary>
    /// A sentry at the centre looking north, and a scout six hexes behind him who has had a look
    /// at him and knows where he is. The scout is out of his eye where it stands, so every pose
    /// the tests weigh is measured against a mission still whole.
    /// </summary>
    private static (Battle Battle, Unit Sentry, Unit Scout) Posted(AwarenessState unnoticed, Loadout? kit = null)
    {
        var battle = Field();
        var sentry = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Slow, HexDirection.North);
        var scout = battle.Deploy("Vance", Side.Player, Along(HexDirection.South, 6), Quick, HexDirection.North, kit);

        battle.SetObjective(new Reconnaissance(
            Side.Player, Along(HexDirection.North, 8), [Along(HexDirection.South, 10)], unnoticed: unnoticed));
        battle.Start();

        Assert.Same(scout, battle.Active);
        battle.Awareness.Notice(scout, sentry, UnitPose.Of(sentry), battle.Round);
        Assert.True(battle.Awareness.Of(scout.Id, sentry.Id).State >= AwarenessState.Suspicious, "the scout was supposed to have registered him");
        Assert.Equal(AwarenessState.Unaware, battle.Awareness.Of(sentry.Id, scout.Id).State);

        return (battle, sentry, scout);
    }
}
