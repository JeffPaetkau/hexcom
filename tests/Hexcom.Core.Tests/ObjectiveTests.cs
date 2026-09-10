using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// A window a person can answer, and a battle that ends because somebody did what they came to
/// do. These read as the two halves of the same want: the interesting half of reactions belongs
/// to whoever is playing, and a fight is not the thing anybody is on the field for.
/// </summary>
public class ObjectiveTests
{
    private static NodeId Node(int q, int r, int layer = 0) => new(new Hex(q, r), layer);

    private static readonly UnitStats Quick = UnitStats.Default with { Initiative = 30 };
    private static readonly UnitStats Slow = UnitStats.Default with { Initiative = 1 };

    private static Battle Field(BattleMap? map = null, int seed = 1)
        => new(map ?? new BattleMap().FillDisc(Hex.Zero, 16), new HexLayout(size: 1.0), seed: seed);

    private static void WaitFor(Battle battle, Unit unit)
    {
        while (battle.Active != unit) battle.EndTurn();
    }

    // ---- the window, held open ---------------------------------------------------

    /// <summary>
    /// The seam an interface cannot do without. A click arrives on a later frame, so the only
    /// shape a player can use is a state the battle sits in rather than a question asked inside a
    /// call.
    /// </summary>
    [Fact]
    public void ACommittedMoveCanBeLookedAtBeforeAnythingAnswersIt()
    {
        var (battle, watchman, runner) = Overwatched();

        var start = runner.Position;
        var points = runner.ActionPoints;

        var commitment = battle.Commit(Node(4, 2));

        Assert.True(commitment.Committed, commitment.Refusal);
        Assert.Equal(points - commitment.ApCost, runner.ActionPoints);

        var window = commitment.Window!;
        var offer = Assert.Single(window.Offers);

        Assert.Same(watchman, offer.Reactor);
        Assert.Empty(window.Placements);
        Assert.Empty(window.Resolutions);

        // Paid for and not yet taken. The route is committed, which is the whole reason both
        // sides can read the future for its duration, and the mover has not stepped.
        Assert.Equal(start, runner.Position);
        Assert.Equal(runner.Stats.Vitality, runner.Vitality);

        // And every option can be scored before any of it happens, which is what a player is
        // being shown. Appraising after the fact reads a battle that has moved on.
        Assert.All(offer.Options, o => window.Appraise(o));

        battle.Resolve(commitment);
        Assert.Equal(Node(4, 2), runner.Position);
    }

    [Fact]
    public void APlayerCanPlaceSomethingOtherThanWhatWasRecommended()
    {
        var (battle, watchman, _) = Overwatched();

        var commitment = battle.Commit(Node(4, 2));
        var offer = commitment.Window!.Offers.Single();

        var other = offer.Options.First(o => o != offer.Recommended && o.Action == ReactionAction.Fire);
        commitment.Window.Place(other);

        var outcome = battle.Resolve(commitment);
        var resolution = Assert.Single(outcome.Reactions!.Resolutions);

        Assert.Same(other, resolution.Placement);
        Assert.Equal(other.ApCost, watchman.Stats.Costs.Fire(other.Mode!.ApCost));
    }

    /// <summary>
    /// A held shot is one somebody chose to hold, so choosing not to spend it has to be on the
    /// list. Nothing could decline a reaction until now: a reactor took its best option even
    /// when every option scored below zero, which happens.
    /// </summary>
    [Fact]
    public void AWatchmanCanBeToldToHoldItsFire()
    {
        var (battle, watchman, _) = Overwatched();

        var reserve = watchman.Reserve;
        var commitment = battle.Commit(Node(4, 2));
        var offer = commitment.Window!.Offers.Single();

        var hold = Assert.Single(offer.Options, o => o.Action == ReactionAction.Nothing);
        Assert.Equal(Appraisal.Nothing, commitment.Window.Appraise(hold));

        commitment.Window.Place(hold);
        var outcome = battle.Resolve(commitment);

        Assert.Single(outcome.Reactions!.Resolutions);
        Assert.Null(outcome.Reactions.Resolutions[0].Outcome);
        Assert.Equal(reserve, watchman.Reserve);
    }

    /// <summary>Placing nothing at all is a real answer, and means nobody answered.</summary>
    [Fact]
    public void AWindowNobodyAnsweredResolvesWithNothingHappening()
    {
        var (battle, watchman, runner) = Overwatched();

        var reserve = watchman.Reserve;
        var outcome = battle.Resolve(battle.Commit(Node(4, 2)));

        Assert.True(outcome.Moved);
        Assert.Empty(outcome.Reactions!.Resolutions);
        Assert.Equal(reserve, watchman.Reserve);
        Assert.Equal(runner.Stats.Vitality, runner.Vitality);
        Assert.Equal(Node(4, 2), runner.Position);
    }

    /// <summary>
    /// The old call is the two halves with the recommendations between them, which is what keeps
    /// every caller that does not want to answer a window by hand exactly where it was.
    /// </summary>
    [Fact]
    public void MovingIsCommittingAndResolvingWithTheRecommendationsInBetween()
    {
        var byHand = Overwatched();
        var handCommit = byHand.Battle.Commit(Node(4, 2));
        handCommit.Window!.PlaceRecommended();
        var handOutcome = byHand.Battle.Resolve(handCommit);

        var whole = Overwatched();
        var wholeOutcome = whole.Battle.Move(Node(4, 2));

        Assert.Equal(handOutcome.ApSpent, wholeOutcome.ApSpent);
        Assert.Equal(handOutcome.Reactions!.Placements.Count, wholeOutcome.Reactions!.Placements.Count);
        Assert.Equal(byHand.Runner.Vitality, whole.Runner.Vitality);
        Assert.Equal(byHand.Runner.Position, whole.Runner.Position);
    }

    [Fact]
    public void ARefusedMoveCommitsNothingAndCostsNothing()
    {
        var (battle, _, runner) = Overwatched();

        var points = runner.ActionPoints;
        var commitment = battle.Commit(runner.Position);

        Assert.False(commitment.Committed);
        Assert.Null(commitment.Window);
        Assert.Equal(points, runner.ActionPoints);
        Assert.False(battle.Resolve(commitment).Moved);
    }

    // ---- the seam through the commander ------------------------------------------

    /// <summary>
    /// The case a player cares about most is the <em>enemy's</em> move, so the seam has to reach
    /// through the thing driving the enemy or the interface never gets to use it.
    /// </summary>
    [Fact]
    public void AnEnemyTurnStopsAtTheWindowOurSentryHasToAnswer()
    {
        var (battle, watchman, runner) = Overwatched(runnerHasSomewhereToBe: true);
        var commander = new Commander(battle, windows: WindowAnswer.HandedOut);

        var acts = commander.TakeTurn();

        var window = commander.Waiting;
        Assert.NotNull(window);
        Assert.Same(watchman, window!.Offers.Single().Reactor);
        Assert.Empty(window.Placements);
        Assert.Equal(OrderKind.Move, acts[^1].Kind);

        // Nothing has resolved, so the mover is still standing where it started.
        Assert.Equal(Node(4, -2), runner.Position);
        Assert.Null(acts[^1].Moved);

        window.Place(window.Offers.Single().Options.Single(o => o.Action == ReactionAction.Nothing));
        commander.Resume();

        // Held fire, so nothing was fired — read off the window rather than off the reserve,
        // which the sentry's own turn has since refilled.
        Assert.Null(commander.Waiting);
        Assert.Equal(ReactionAction.Nothing, Assert.Single(window.Resolutions).Placement.Action);
        Assert.Equal(runner.Stats.Vitality, runner.Vitality);

        // And the act now carries what the move did, which is the thing an order alone never said.
        Assert.True(commander.Taken[0].Moved!.Moved);
        Assert.NotEqual(Node(4, -2), runner.Position);
    }

    /// <summary>
    /// An order records what an action was chosen on and nothing about what it did, which was
    /// fine until an interface wanted to narrate the enemy's turn.
    /// </summary>
    [Fact]
    public void TakingATurnHandsBackWhatEachOrderDidAsWellAsWhyItWasPicked()
    {
        var battle = Field();
        var gunner = battle.Deploy("Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast);
        var target = battle.Deploy("Vance", Side.Player, Node(4, 0), Slow, HexDirection.SouthWest);
        battle.Start();

        // Looking is what a turn ends with, so it takes a round or two to come back round to the
        // gunner with a contact in hand and a full allowance.
        for (var i = 0; i < 12 && battle.Awareness.Of(gunner.Id, target.Id).State < AwarenessState.Searching; i++)
            battle.EndTurn();
        WaitFor(battle, gunner);

        var acts = new Commander(battle).TakeTurn();
        var shot = acts.First(a => a.Kind == OrderKind.Fire);

        Assert.True(shot.Carried);
        Assert.NotNull(shot.Fired);
        Assert.True(shot.Fired!.Fired);
        Assert.Same(target, shot.Order.Shot!.Target);

        // Every act carries whatever its own kind of order produces, and nothing else.
        Assert.All(acts, a => Assert.True(a.Kind == OrderKind.Fire || a.Fired is null));
    }

    /// <summary>
    /// A bug that predates objectives and that walking off the field would have hit every time.
    /// Three things hand the turn on without the loop asking; ending it again takes the next
    /// soldier's whole allowance away before they have done anything with it.
    /// </summary>
    [Fact]
    public void ACommanderOnlyEverEndsTheTurnOfTheSoldierItWasDriving()
    {
        var battle = Withdrawing(out var leaver, out var other, at: Node(2, 0));

        WaitFor(battle, leaver);
        new Commander(battle).TakeTurn();

        Assert.True(leaver.GotOut);
        Assert.Same(other, battle.Active);
        Assert.Equal(other.Stats.ActionPoints, other.ActionPoints);
    }

    // ---- leaving, and what it settles --------------------------------------------

    [Fact]
    public void WalkingOffTheFieldIsNotTheSameAsBeingCarriedOffIt()
    {
        var battle = Withdrawing(out var leaver, out _, at: Node(2, 0));

        WaitFor(battle, leaver);
        Assert.True(battle.Extract());

        Assert.False(leaver.InPlay);
        Assert.True(leaver.GotOut);
        Assert.Equal(DepartureKind.Extracted, leaver.Left!.Kind);
    }

    [Fact]
    public void NobodyLeavesFromSomewhereTheirSideCannotLeaveFrom()
    {
        var battle = Withdrawing(out var leaver, out _, at: Node(6, 0));

        WaitFor(battle, leaver);

        Assert.False(battle.Extract());
        Assert.True(leaver.InPlay);
    }

    /// <summary>
    /// The trap entry 030 found by reading the source rather than assuming. Leaving makes the
    /// tracker forget, so a condition asked afterwards reads Unaware for everybody, trivially and
    /// always. The reading has to be taken as the soldier goes.
    /// </summary>
    [Fact]
    public void TheReadingIsTakenAsTheSoldierLeavesRatherThanAfterwards()
    {
        var battle = Withdrawing(out var leaver, out _, at: Node(2, 0));

        // Make quite sure somebody has him, then walk him off.
        MakeNoise(battle, leaver);
        Assert.True(battle.HighestAwarenessOf(leaver) >= AwarenessState.Searching);

        WaitFor(battle, leaver);
        Assert.True(battle.Extract());

        // The tracker has forgotten him entirely, and the sample survives it.
        Assert.Equal(AwarenessState.Unaware, battle.HighestAwarenessOf(leaver));
        Assert.True(leaver.Left!.Noticed >= AwarenessState.Searching);
    }

    [Fact]
    public void ASquadThatGetsOutQuietlyHasDoneWhatItCameToDo()
    {
        var battle = Withdrawing(out var leaver, out _, at: Node(2, 0));

        Assert.Equal(Verdict.Undecided, battle.VerdictFor(Side.Player));

        WaitFor(battle, leaver);
        Assert.True(battle.Extract());

        Assert.Equal(AwarenessState.Unaware, leaver.Left!.Noticed);
        Assert.Equal(Verdict.Achieved, battle.VerdictFor(Side.Player));
        Assert.True(battle.IsDecided);
    }

    /// <summary>
    /// The third ending, and the reason two were not enough: a squad that is seen has lost the
    /// mission and has not lost the squad, and a win-or-die model reports those identically.
    /// </summary>
    [Fact]
    public void ASquadThatIsSeenComesHomeWithoutTheMission()
    {
        var battle = Withdrawing(out var leaver, out _, at: Node(2, 0));

        MakeNoise(battle, leaver);
        Assert.True(battle.HighestAwarenessOf(leaver) > AwarenessState.Suspicious);

        WaitFor(battle, leaver);
        Assert.True(battle.Extract());

        Assert.Equal(Verdict.Abandoned, battle.VerdictFor(Side.Player));
    }

    [Fact]
    public void ASquadWithNobodyLeftToGetOutHasLostIt()
    {
        var battle = Withdrawing(out var leaver, out _, at: Node(2, 0));

        battle.Withdraw(leaver);

        Assert.Equal(Verdict.Failed, battle.VerdictFor(Side.Player));
        Assert.True(battle.IsDecided);
    }

    /// <summary>
    /// The counter-play entry 030 asked to keep, and the reason the reading is a sample per
    /// departure rather than a mark held across the battle: silencing a witness really does take
    /// his contact out of the world, with no rule saying so.
    /// </summary>
    [Fact]
    public void SilencingAWitnessTakesWhatHeKnewWithHim()
    {
        var battle = Withdrawing(out var leaver, out var watcher, at: Node(2, 0));

        MakeNoise(battle, leaver);
        Assert.True(battle.HighestAwarenessOf(leaver) > AwarenessState.Suspicious);

        battle.Withdraw(watcher);
        Assert.Equal(AwarenessState.Unaware, battle.HighestAwarenessOf(leaver));

        WaitFor(battle, leaver);
        Assert.True(battle.Extract());

        Assert.Equal(Verdict.Achieved, battle.VerdictFor(Side.Player));
    }

    // ---- what an objective does to the search ------------------------------------

    /// <summary>
    /// The hole every open question named: a unit with no contact scored every option at nothing
    /// and banked its turn, because there was nothing in the game for it to want. There is now.
    /// </summary>
    [Fact]
    public void AnObjectiveDrawsASoldierWhoKnowsAboutNobody()
    {
        var battle = Field();
        var leaver = battle.Deploy("Vance", Side.Player, Node(-12, 0), Quick, HexDirection.NorthEast);
        battle.Deploy("Kessel", Side.Hostile, Node(14, 0), Slow, HexDirection.SouthWest);
        battle.SetObjective(new Withdrawal(Side.Player, [Node(-15, 0)]));
        battle.Start();

        Assert.Same(leaver, battle.Active);
        Assert.Empty(battle.Tactics.Known(leaver));

        var before = leaver.Position;
        var acts = new Commander(battle).TakeTurn();

        Assert.Contains(acts, a => a.Kind == OrderKind.Move);
        Assert.NotEqual(before, leaver.Position);

        // Nearer, measured the way the objective measures: along the ground, in action points.
        var objective = battle.ObjectiveOf(Side.Player)!;
        Assert.True(objective.Progress(battle, leaver.Position) > objective.Progress(battle, before));
    }

    /// <summary>
    /// The acceptance test the brief set. A battle that stops because a squad did the thing and
    /// left, rather than because everybody on one side was killed.
    /// </summary>
    [Fact]
    public void ASkirmishEndsBecauseOneSideWithdrewRatherThanBecauseItWasWipedOut()
    {
        var battle = Field(seed: 3);
        var exit = new[] { Node(-13, 0), Node(-13, 1) };

        for (var i = 0; i < 2; i++)
        {
            battle.Deploy($"Blue {i}", Side.Player, Node(-8, i), UnitStats.Default, HexDirection.SouthWest);
            battle.Deploy($"Red {i}", Side.Hostile, Node(8, i), UnitStats.Default, HexDirection.NorthEast);
        }

        battle.SetObjective(new Withdrawal(Side.Player, exit));
        battle.Start();

        var commander = new Commander(battle);
        var turns = 0;

        while (battle.IsRunning && !battle.IsDecided && turns++ < 200) commander.TakeTurn();

        Assert.NotEqual(Verdict.Undecided, battle.VerdictFor(Side.Player));

        var blues = battle.Units.Where(u => u.Side == Side.Player).ToList();
        Assert.All(blues, b => Assert.True(b.GotOut, $"{b.Name} did not walk out"));

        // And the other side is still standing, which is the whole point: nobody had to be
        // killed for this battle to have an answer.
        Assert.Contains(battle.InPlay, u => u.Side == Side.Hostile);
    }

    // ---- a mission with something in the middle of it ----------------------------

    /// <summary>
    /// What entry 048 measured, and the whole of what this is for. Twelve seeds settled in round
    /// two by walking to the exit, because the rules had an objective for the leaving and none
    /// for the task. Leaving is not on the table until the task is done.
    /// </summary>
    [Fact]
    public void AMissionIsNotAchievedByWalkingOutOfTheGate()
    {
        var battle = Sent(out var scout);
        var job = (Reconnaissance)battle.ObjectiveOf(Side.Player)!;
        var commander = new Commander(battle);

        // Standing on the exit with the job undone, and walking off it is not offered.
        while (battle.Active != scout) battle.EndTurn();
        Assert.True(battle.Move(Gate).Moved);

        Assert.True(job.IsExit(scout.Position));
        Assert.False(job.Done);
        Assert.DoesNotContain(
            commander.Options(scout, commander.Judge.Known(scout).ToList()),
            o => o.Kind == OrderKind.Leave);

        // The rules still permit it — abandoning is a real decision — and it settles as one.
        Assert.True(battle.Extract());
        Assert.Equal(Verdict.Abandoned, battle.VerdictFor(Side.Player));
    }

    /// <summary>
    /// The journey is out and back, so the exit is not the far end of it. Standing on the exit
    /// with the job undone is further from done than standing at the place.
    /// </summary>
    [Fact]
    public void TheWayHomeIsMeasuredByWayOfTheThingYouCameFor()
    {
        var battle = Sent(out _);
        var job = battle.ObjectiveOf(Side.Player)!;

        var atStart = job.Progress(battle, Node(0, 0));
        var atGate = job.Progress(battle, Gate);
        var atCompound = job.Progress(battle, Compound);

        Assert.True(atCompound > atStart, $"the compound {atCompound:0.00} should beat the start {atStart:0.00}");
        Assert.True(atGate < atCompound, $"the gate {atGate:0.00} should not beat the compound {atCompound:0.00}");

        // And walking to the gate is worse than standing still, because it is the wrong way.
        Assert.True(atGate < atStart);
    }

    /// <summary>
    /// Doing the thing does not jolt the score. It changes what is left, and the score is what is
    /// left — which is why the two stages need no seam between them.
    /// </summary>
    [Fact]
    public void ConfirmingItLeavesTheScoreWhereItWasAndTheRestOfTheJourneyShorter()
    {
        var battle = Field();
        var sapper = battle.Deploy("Vance", Side.Player, Compound, Quick, HexDirection.NorthEast);
        battle.Deploy("Kessel", Side.Hostile, Node(0, 14), Slow, HexDirection.NorthEast);

        var job = new Sabotage(Side.Player, Compound, [Gate], effort: 20);
        battle.SetObjective(job);
        battle.Start();

        var before = job.Progress(battle, Compound);

        while (battle.Active != sapper) battle.EndTurn();
        Assert.Equal(job.Effort, battle.Work());
        Assert.True(job.Done);

        // Standing in the same place, the score has moved by exactly the points that went in —
        // no more, and no jolt for the stage changing.
        Assert.Equal(before + job.Effort * job.PerPoint, job.Progress(battle, Compound), 6);
        Assert.True(job.Progress(battle, Gate) > job.Progress(battle, Compound));
    }

    [Fact]
    public void ALookFromTooFarOffConfirmsNothing()
    {
        var battle = Sent(out var scout, new Reconnaissance(Side.Player, Compound, [Gate], within: 4.0));
        var job = (Reconnaissance)battle.ObjectiveOf(Side.Player)!;

        // Two hexes short is three and a half metres, which is inside four; five hexes is not.
        while (battle.Active != scout) battle.EndTurn();
        Assert.True(battle.Move(Node(5, 0)).Moved);
        battle.EndTurn();

        Assert.False(job.Done, "five hexes off is not a confirmation");

        while (battle.Active != scout) battle.EndTurn();
        Assert.True(battle.Move(Node(9, 0)).Moved);
        battle.EndTurn();

        Assert.True(job.Done);
        Assert.Equal(scout, job.Confirmed!.Value.By);
    }

    [Fact]
    public void ConfirmingItMeansLookingAtIt()
    {
        var battle = Sent(out var scout);
        var job = (Reconnaissance)battle.ObjectiveOf(Side.Player)!;

        while (battle.Active != scout) battle.EndTurn();
        Assert.True(battle.Move(Node(9, 0)).Moved);

        // Facing the other way, so the place is behind him. A look he did not take is not a look.
        Assert.True(battle.Face(HexDirection.SouthWest));
        Assert.False(battle.Awareness.IsWatching(scout, Compound));
        battle.EndTurn();

        Assert.False(job.Done);

        while (battle.Active != scout) battle.EndTurn();
        Assert.True(battle.Face(HexDirection.NorthEast));
        battle.EndTurn();

        Assert.True(job.Done);
    }

    // ---- working at it -----------------------------------------------------------

    /// <summary>
    /// The job is so many points of somebody's turn, and a turn is not enough of them. It
    /// accumulates, and it only accumulates from somebody standing on it.
    /// </summary>
    [Fact]
    public void AChargeTakesMorePointsThanOneTurnHasAndRemembersWhatWentIn()
    {
        var battle = Field();
        var sapper = battle.Deploy("Vance", Side.Player, Compound, Quick, HexDirection.NorthEast);
        var mate = battle.Deploy("Orsini", Side.Player, Node(10, 1), Slow, HexDirection.NorthEast);
        battle.Deploy("Kessel", Side.Hostile, Node(0, 14), Slow, HexDirection.NorthEast);

        var job = new Sabotage(Side.Player, Compound, [Gate], effort: 70);
        battle.SetObjective(job);
        battle.Start();

        while (battle.Active != sapper) battle.EndTurn();
        var went = battle.Work();

        Assert.Equal(sapper.Stats.ActionPoints, went);
        Assert.Equal(0, sapper.ActionPoints);
        Assert.False(job.Done);
        Assert.Equal(70 - went, job.Owing);

        // Standing beside it is not standing on it.
        battle.EndTurn();
        while (battle.Active != mate) battle.EndTurn();
        Assert.Equal(0, battle.Work());

        // And the rest goes in on the next turn of somebody who is.
        battle.EndTurn();
        while (battle.Active != sapper) battle.EndTurn();

        Assert.Equal(70 - went, battle.Work());
        Assert.True(job.Done);
        Assert.Equal(0, job.Owing);
    }

    /// <summary>
    /// The whole reason the mission is measured in action points: a point spent on the charge and
    /// a point spent walking toward it are worth the same, so nothing has to say that working is
    /// better than shuffling.
    /// </summary>
    [Fact]
    public void PuttingPointsIntoTheJobPaysWhatWalkingTowardItPays()
    {
        var battle = Sent(out var scout, new Sabotage(Side.Player, Compound, [Gate], effort: 40));
        var job = (Sabotage)battle.ObjectiveOf(Side.Player)!;

        var walked = job.Progress(battle, Node(1, 0)) - job.Progress(battle, Node(0, 0));
        var stride = MovementCosts.Default.Walk;

        Assert.Equal(stride * job.PerPoint, walked, 6);
        Assert.Equal(walked, battle.Tactics.WorkWorth(scout, stride) / battle.Tactics.Model.ObjectiveValue, 6);
    }

    // ---- what it does to the search ----------------------------------------------

    /// <summary>
    /// The acceptance test. A squad sent out to look at something goes and looks at it, and only
    /// then comes home — where before it walked to the exit and called the mission done.
    /// </summary>
    [Fact]
    public void ASquadSentToLookAtSomethingGoesAndLooksBeforeItComesHome()
    {
        var battle = Sent(out var scout);
        var job = (Reconnaissance)battle.ObjectiveOf(Side.Player)!;
        var commander = new Commander(battle);

        var confirmedBefore = false;
        var turns = 0;

        while (battle.IsRunning && !battle.IsDecided && turns++ < 60)
        {
            var mover = battle.Active!;
            var acts = commander.TakeTurn();

            if (mover != scout) continue;
            if (acts.Any(a => a.Kind == OrderKind.Leave)) confirmedBefore = job.Done;
        }

        Assert.True(job.Done, "the scout never went and looked");
        Assert.True(confirmedBefore, "it walked off the field before confirming anything");
        Assert.True(scout.GotOut);
        Assert.Equal(Verdict.Achieved, battle.VerdictFor(Side.Player));
    }

    /// <summary>
    /// The trap the gradient was invented to solve, seen from the other side: a mission longer
    /// than the horizon would read as nothing worth starting, which is a flag again.
    /// </summary>
    [Fact]
    public void AMissionLongerThanTheHorizonStillSlopesAllTheWayBack()
    {
        var far = Node(15, 0);
        var battle = Field();
        var scout = battle.Deploy("Vance", Side.Player, Node(-15, 0), Quick, HexDirection.NorthEast);
        battle.Deploy("Kessel", Side.Hostile, Node(0, 14), Slow, HexDirection.NorthEast);

        var job = new Reconnaissance(Side.Player, far, [Node(-15, 1)]);
        battle.SetObjective(job);
        battle.Start();

        // Thirty hexes out and thirty back is three hundred points, past the four turns the
        // horizon is set at — and every stride of it still scores.
        var here = job.Progress(battle, scout.Position);
        var onward = job.Progress(battle, Node(-14, 0));

        Assert.True(job.PerPoint > 0);
        Assert.True(onward > here, $"{onward:0.000} should beat {here:0.000}");

        var acts = new Commander(battle).TakeTurn();
        Assert.Contains(acts, a => a.Kind == OrderKind.Move);
        Assert.True(job.Progress(battle, scout.Position) > here);
    }

    // ---- setting up --------------------------------------------------------------

    /// <summary>
    /// A watchman holding an arc across a runner's route, with the runner up and a full turn in
    /// hand. The window this opens is the one the interface work is all about.
    /// </summary>
    private static (Battle Battle, Unit Watchman, Unit Runner) Overwatched(bool runnerHasSomewhereToBe = false)
    {
        var battle = Field();
        var watchman = battle.Deploy(
            "Kessel", Side.Hostile, Node(0, 0), Quick, HexDirection.NorthEast);
        var runner = battle.Deploy(
            "Vance", Side.Player, Node(4, -2), UnitStats.Default with { Initiative = 1 }, HexDirection.North);

        // Somewhere on the far side of the watched ground, so a commander driving the runner
        // walks it across the arc rather than standing about.
        if (runnerHasSomewhereToBe) battle.SetObjective(new Withdrawal(Side.Player, [Node(4, 4)]));

        battle.Start();
        Assert.Same(watchman, battle.Active);

        Assert.True(battle.SetOverwatch(OverwatchArc.Standard));
        battle.EndTurn();

        WaitFor(battle, runner);
        Assert.True(watchman.Reserve > 0, "the watchman was supposed to bank something");

        return (battle, watchman, runner);
    }

    /// <summary>
    /// One soldier with somewhere to be and one hostile who may or may not be looking at them.
    /// </summary>
    private static Battle Withdrawing(out Unit leaver, out Unit other, NodeId at)
    {
        var battle = Field();

        // Far enough off, and looking the other way, that nobody drifts up the ladder by accident
        // while the turns are being handed round.
        leaver = battle.Deploy("Vance", Side.Player, at, Quick, HexDirection.SouthWest);
        other = battle.Deploy("Kessel", Side.Hostile, Node(15, 0), Slow, HexDirection.NorthEast);

        battle.SetObjective(new Withdrawal(Side.Player, [Node(2, 0), Node(2, 1)]));
        battle.Start();

        return battle;
    }

    /// <summary>Make quite sure one side has the other on the ladder, by the loudest channel.</summary>
    private static void MakeNoise(Battle battle, Unit about, int times = 3)
    {
        for (var i = 0; i < times; i++) battle.Awareness.Hear(about, 200, battle.Round);
    }

    /// <summary>
    /// The waystation shape, in miniature: a squad with the exit one way and the thing to look at
    /// twice as far the other, which is the geometry entry 048 measured walking away from.
    /// </summary>
    private static Battle Sent(out Unit scout, Objective? job = null)
    {
        var battle = Field();

        scout = battle.Deploy("Vance", Side.Player, Node(0, 0), Quick, HexDirection.NorthEast);
        battle.Deploy("Kessel", Side.Hostile, Node(0, 14), Slow, HexDirection.NorthEast);

        // The bar is Searching rather than Suspicious because these read the *sequence* — go,
        // look, come back — on an open disc where a lone hostile cannot help registering somebody
        // crossing it. What the bar should be for a real mission is content's to say.
        battle.SetObjective(
            job ?? new Reconnaissance(Side.Player, Compound, [Gate], unnoticed: AwarenessState.Searching));
        battle.Start();

        return battle;
    }

    /// <summary>The thing to look at, ten hexes out.</summary>
    private static NodeId Compound => Node(10, 0);

    /// <summary>The way home, four hexes back the other way.</summary>
    private static NodeId Gate => Node(-4, 0);
}
