# Core — the rules

Everything the game is, as plain .NET. Hex geometry, cover, movement, sight, detection,
initiative, damage, reactions, the AI, and the things that go off.

Read [../map.md](../map.md) first, then this. `../design.html` is the source of truth for *why*
any of it is the way it is; this file is how to work on it without breaking something.

## Owns

```
src/Hexcom.Core/**      except Maps/DemoMaps.cs, which belongs to content
tests/**
docs/design.html        and it is the only territory that republishes the artifact
```

## Must not touch

`game/**` — if a rule change needs the view updated, say so in `../decisions.md` and let View do
it. The temptation is strongest when a signature changes and the sandbox stops compiling; resist
it anyway, or note in your commit exactly what you changed there and why it could not wait.

## Depends on

Nothing. Core is the trunk. Everything else depends on it, which is why the contracts in
[../map.md](../map.md) are mostly about not moving the ground under other territories:
no engine references, one query surface for the view and the AI alike, information asymmetric on
purpose, balance numbers in their homes — nine of them since `BlastModel`, see
[../decisions.md](../decisions.md) entry 032 — and one horizontal unit is one metre.

---

## The job — a squad that is not seen

Branch `core/unnoticed`. Read the rest of this file before starting; the turn loop below and the
gotchas after it are the things that will bite, and the ones about objectives, the clock and the
batch are the three most likely to.

**What exists.** Every system the design doc describes bar suppression; three of the six mission
shapes; a mission that stops at an hour or so many rounds after the garrison's word is out
(`../decisions.md` entry 079); and a batch of headless matches, checked in, that anybody can run
again with the same seeds (entry 080).

**What the batch said, in one line: nothing wins the waystation, and the reason is not a dial.**
Across every arm the squad got eyes on the house, usually by round two, and some hostile held it
at `Engaged` in every match — so every verdict is `Abandoned` on the departure reading. The
objective is scored as a race because nothing in the scorer prices the mission's own win condition.
`ObjectiveValue × Progress` pays for getting there and getting home; **nothing pays for getting
there unseen**. Entry 080 has the tables; read its headline and the section on the clock.

**The job is the missing term, and then the measurement again.**

- **Price being noticed against the mission, not only against the fight.** `Sortie.Unnoticed` is a
  rung, and a squad member held above it has already cost the mission — so the thing to price is
  *what this action does to the highest rung any enemy will hold on this soldier*, in the same
  vitality every other term is in, scaled by what the objective is worth. The raw material exists:
  `AwarenessTracker.WouldAnnounce` and `WouldHear` already say who learns what from an act, and
  `Tactician.Aimed` already reads an enemy's detection as a rung. What is missing is the step from
  *he will be Searching* to *and that is most of the mission gone*. Settle deliberately whether it
  is a cliff at the rung or a slope up to it: a cliff is what the win condition is, a slope is what
  a one-step search can climb, and entry 044's argument for gradients over flags applies here too.
- **The clock, as something the scorer can see.** Entry 080 measured a three-round grace ending
  most matches before round six with fewer than half the squad home — against a squad that does
  not know it has three rounds. Once the alarm is out, what is left of the journey against what is
  left of the night is a number the objective already has (`Remaining`, in points) and one the
  deadline now has (`LastRound`). A squad with the job done and the hour closing should go.
- **Run the batch again, and record the difference.** `ObjectiveValue` above 60 is saturated on this
  ground and 30 to 60 is the live range — but choosing inside it before this term exists is tuning a
  race. `ObjectiveHorizon` is the same dial on this ground, so the term should not be tuned against
  either one alone. With the term in, the value question and the clock question are the two to rerun. The test
  that the term works is simple and has never once been true: **a reconnaissance on the waystation
  achieved in more than a handful of matches in a hundred.**

**If that goes quickly, the two faults a one-step search shows on real ground** — entry 039, both
still open, both invisible on a disc:

1. **Every charge in a match lands on one empty hex.** The crater rule marks the thrower at the
   burst, so the next throw is aimed at the crater. The rule is right and its interaction with a
   one-step search is not.
2. **A soldier paces between two tiles on a shot it never takes.** `Order.Opens` credits a move
   with a shot, and from the new tile the best option is the move back, credited with the same
   shot.

**Two things the batch settled that are not this brief's to act on.** `RemovalBonus` is a *finish
him* dial and cannot say *that one first* at any setting — a signaller worth more wants a per-soldier
term derived from what the soldier does for its side, and on the waystation the alarm is out before
anybody could act on it anyway. The two cost archetypes are a large live change, halving what the
squad kills at value 30; keep them. And entry 048's quiet scout was the mission, not the man: with
something to look at, the scout is the one who goes in and he is seen every time from either post.

**Content is waiting on nothing from Core.** Entry 079 tells it to uncomment the reconnaissance line
— `within` is inert on the waystation and can stay unwritten — and that `rounds` and the briefing's
stop have somewhere to go. When that lands, delete `tests/Hexcom.Core.Tests/Measured/Waystation.cs`'s
hand-built objective and read the file's.

**A garrison that does not move is still Core's, and still not this brief's.** Three of the
waystation's four hostiles never act. It wants a notion of what a soldier is *doing* rather than
where it is, which is also what *the mission is lost, get out* wants; neither should be built
piecemeal, and milestone 2 on `../map.md` is where they go together.

**Out of scope.** `game/**` as ever. Extraction and capture, dropped from the last brief and still
unneeded. Suppression.

**The test that it worked:** entry 080's value table rerun with the term in, and a row in it where
the waystation is achieved.

---

## How a turn runs

Worth knowing before touching anything, because most of the surprises are in the order.

```
Battle.Start()      roll initiative, book everyone, hand the first turn out
  └ Advance()       refill AP · recharge shields · clear Reserve and Overwatch
                    (NOT Ambush) · rebook for next round
  the active unit acts
      Move (= Commit · PlaceRecommended · Resolve) · Fire · Throw · LayMine · Shout
      Face · ChangeStance · SetOverwatch · Arm · SpringAmbush · Work · Extract
  Battle.EndTurn()  Awareness.Observe  ← the only moment a unit looks around
                    Objective.Looked   ← and therefore the only moment a look-at-it job completes
                    Bank               ← leftover AP becomes Reserve, AP zeroed
                    Advance
```

**A reaction window is the only thing that acts out of turn**, and there are exactly two ways one
opens:

- `Battle.Move` opens one on the committed route. Overwatch, surprise, a trap somebody walked
  into, and any mine on the route all answer into it.
- `Battle.SpringAmbush` opens one deliberately, on a `CommittedMove` of zero length.

Either way: offers are built in the constructor and `Resolve` walks the subject along the
timeline firing at each landing tick.

**`Battle.Move` is `Commit` then `PlaceRecommended` then `Resolve`**, and the middle one is the
seam. `Commit` prices the route, spends the points and hands back a `MoveCommitment` — the window
with its offers made and nothing placed. **The mover has not stepped**: it stands at the start
until `Resolve` walks it along, so anything reading the field while a window is open sees a
soldier who has paid for a walk it has not taken. Place what you like in the gap, or nothing at
all, which means everybody held their fire.

**A mine is on that timeline and is not an offer**, because there is nobody to offer it to.
`Mines` and `Detonations` sit beside `Offers` and `Resolutions`; `Resolve` merges the two lists
and the terrain goes first where a mine and a placement land on the same tick.

`ReactionWindow.Best` hands the whole list to `Tactician.Best`, which scores each option in
vitality. Nothing about the ordering is written down as a ladder any more, which means a change to
`UtilityModel` can silently change which reaction a unit takes — that is the point, and it is also
the thing to suspect when a reaction test starts failing for no reason you can see.

---

## Gotchas

- **Geometry needs epsilons at boundaries.** Two bugs so far came from exact-equality cases: a
  silhouette exactly as tall as the wall hiding it produced `0.9999999999999999`, and a parapet
  3.5 m overhead was vaultable because the wall profile decided the traversal before the height
  was checked. Suspect float boundaries first when a geometric test fails oddly.
- **A real behaviour change should break tests that assumed the old behaviour.** Adding facing
  broke nine awareness tests whose sentries faced the default direction. The fix was pointing the
  sentries at the approach, not weakening the model. Don't soften a model to keep a stale test
  green.
- **Two pockets, never mixed.** `Unit.ActionPoints` is the turn allowance; `Unit.Reserve` is what
  banked for reacting. `PlanShot` and `Resolve` take an `ApSource` saying which is being spent.
  Zeroing the allowance at `EndTurn` is deliberate: points are spent or banked, never left lying
  on a unit whose turn is over.
- **A reaction moves the mover.** `ReactionWindow.Resolve` walks the unit along its committed
  route and fires from each landing tick, so the mover is genuinely standing there. That is why
  sight, cover and which face a round hits need no special case inside a window — but it does
  mean anything reading a unit's position mid-window sees an intermediate one.
- **`BodyFace` is not `HexDirection`.** Armour faces are the soldier's own sides, so `BodyFace`
  is an offset from `Unit.Facing`, not a compass point. `Battle.FacesPresentedTo` returns a
  *distribution* — a body is a hexagon, so a shot can always reach two or three plates — and the
  round is rolled against it in `Resolve`. Anything that wants one answer takes `Aspects[0]` or
  `ShotPlan.LikeliestFace`.
- **Nothing may assume a particular turn size.** A turn is 50 and a stride is 5, but the
  allowance is expected to vary per soldier, and the whole list was already rescaled once (10 → 50
  so the cheapest action stopped setting the resolution of everything else). Express test
  expectations against `MovementCosts` / `FireMode.ApCost`, never as literals.
- **Loudness is priced off the listed cost of the ground, not what the mover paid.** Crawling
  costs 3× so a crawler spending 3× the points would come out as loud as somebody strolling —
  the stance cancelling itself out. `Battle.Loudness` sums `link.ApCost`, deliberately — and it
  is public so a route can be priced before it is taken; `AwarenessTracker.WouldHear` says who
  would hear it, and `Tactician.AppraiseMove` puts the two into a move's score.
- **The price list is not what a soldier pays.** `MovementCosts` and `FireMode.ApCost` describe
  the world; `UnitStats.Costs` says what this soldier spends on it. Never read `FireMode.ApCost`
  or `TraversalLink.ApCost` directly in a rule — go through `CostProfile`. Movement pricing is a
  `Func` handed to `Pathfinder.Reachable`, never baked into the graph, which is built once per
  map. `CommittedMove` must be given the same profile the route was costed with or the reaction
  clock stops matching the points actually spent.
- **Surprise fires on a crossing, not a rise.** `seen.Before < bar && seen.After >= bar`. "Rose"
  would re-trigger all the way up the awareness ladder; "is above" would trigger every move.
  Reactors also get their mid-window look *only if they have reserve banked* — the reserve is
  doubling as alertness, and removing that gate hands every hostile a free extra look per move.
- **`Unit.Ambush` survives `Advance`; `Unit.Overwatch` does not.** An overwatch is a posture held
  for a round; an ambush is a plan that stands until sprung, which is what lets the member who
  chooses the moment still be armed on its own turn. `Unit.Held` is whichever one is set. An
  ambush window is a `CommittedMove` of *zero* length — same timeline, one instant.
- **Arc edges are exclusive, on purpose.** Hex bearings are exact multiples of 60°, so a place
  sitting precisely on the edge of a 120° arc is the common case. Comparisons add
  `Geometry2D.AngleEpsilonDegrees` so the edge falls to the *wider* arc deterministically — one
  spoke over is the corner of the eye, not full attention. Two tests pin this; don't "fix" them.
- **`ShotPlan.ExpectedDamage` is damage arriving at the plate, not damage done.** It ignores
  shields and armour entirely, so a beam landing squarely on a full force shield reads well and
  achieves nothing. Anything *choosing* between shots wants `Gunnery.Expect`, which puts the
  rounds through the layers they will actually meet. This is the single easiest mistake to make
  in this codebase and the old reaction policy made it.
- **A window's scores are only true before it resolves.** `Appraise` reads live state — the
  target's remaining vitality, who has noticed whom — so appraising an option after `Resolve` has
  run gives a different number than the one it was recommended on. A unit that fired has been
  noticed for firing. See entry 004 in `../decisions.md`.
- **Cover works in both directions and the scorer knows it.** Going flat behind a knee-high wall
  takes you out of sight of the man in front of you, and takes him out of yours: `Spared` goes up
  and `Prospect` goes *negative* in the same appraisal. A posture score that only ever improves
  is a posture score with a bug in it.
- **`Order.Worth` is not what the order was picked on.** `Order.Score` is, and it adds
  `Order.Opens` — the shot a move sets up. A move's own `Worth` is almost always negative, because
  walking costs points and buys nothing; ranking on it means never taking a firing position.
  Anything reading an order for display wants both halves.
- **A three-a-side match costs a second or two.** Measured, on a radius-sixteen disc with both
  sides driven by `Commander`: the two skirmish tests run one and two matches respectively, at
  about two seconds each, while every other test in the file is under a fifth of a second. So a
  thousand headless matches is twenty to thirty-five minutes rather than the *seconds* section 01
  of the design doc claims the engine-free split buys. Nothing needs doing about it until
  somebody actually runs a batch, which is what the overwatch gate is waiting for; the figure is
  here so that whoever does is not surprised.
  <br>**Where the time goes has not been profiled.** The shape of the search says it should be
  the sight traces — a decision crosses the reachable set with every known threat and every fire
  mode, and a full allowance reaches a few hundred nodes on open ground — but that is arithmetic
  about the code rather than a measurement of it, and the obvious fix (cache the trace per
  destination and threat within one decision) is a guess at the right one. Profile before
  optimising.
- **A blade carrier will not walk across open ground to reach you.** Greedy with one step of
  lookahead cannot see a knife going in two turns from now, so it correctly works out that this
  turn's walk into rifle range is worse than standing still, and stands still forever. Not a bug
  in the scoring; a limit of the search, and the first thing a deeper one would fix. It would at
  least stab somebody when it arrived, which it would not have before entry 031.
- **A threat is a belief, and `Tactician.Known` is the only place one is made.** `Threat` carries
  `Credence` and `EyesOn`. A contact the soldier looked at last and can still see stands where
  it really is; anything else stands at the marker, upright, with a placeholder facing, and is
  worth `Credence(roundsSince)` of a sighting — one for two rounds, then halving. Never build a
  `Threat` from the field for the AI; `Threat.At(unit)` exists for tests and for the mover inside
  a reaction window, which really is standing there.
- **The Commander never fires at a marker.** `Options` offers shots only at threats with
  `EyesOn`. The forecast of a shot at a marker is what a move toward it is *ranked* on
  (`Order.Opens`, scaled by credence), but `Battle.Fire` resolves against where the target really
  is, and carrying that shot out would have the battle correcting the soldier's guess for free.
  So a unit walks to where it can see the marker, looks at the end of its turn like everybody
  else, and shoots next turn — which also means a soldier who is shot from somewhere it has not
  looked at cannot shoot straight back. It turns to look first. That is the ladder working, not
  a bug.
- **What the enemy holds on you is read as a rung.** `Tactician.Aimed` quantises the enemy's
  detection to `Threshold(ReadoutFor(...).State)` before it enters the arithmetic. Two certainty
  figures on the same rung give identical posture scores, and a test pins it. This is entry 011
  in `../decisions.md`, and it is what lets `Appraisal.Spared` go on screen.
- **Against a marker, the look he would get is averaged over six facings.** Assuming the man you
  cannot see is looking straight at where you would arrive was measured, and it prices going
  round a corner above the shot it opens on every geometry tried, so nobody ever goes. An
  expected look is how the scorer treats the plates a round might find, too.
- **Hunting reaches one move, and not further.** A soldier walks to a spot with a line on a fresh
  marker when that spot is within about five hexes; further than that the walk costs more than
  the one discounted shot it might open, and a search one step deep cannot see the turn of
  shooting beyond it. Measured on a solid wall: five hexes long and the far side gets found,
  eleven and nobody moves. The same limit means two survivors who lose contact out of reach of
  each other are a stalemate — markers decay, nobody walks — which is why the acceptance test for
  beliefs asserts a fight and not a decision. This is the blade-carrier limit again, and it is
  the argument for either a deeper search or an objective system; it is not a beliefs problem.

---

- **A charge is aimed at a place, and that is what makes it different to score.** A shot resolves
  against where the target really is, so the Commander never fires at a marker; a throw resolves
  against a piece of ground, so it may be thrown at one. The forecast is built from
  `BlastCandidate`s the caller supplies — believed enemies at their markers, your own squad where
  it stands — and never from the field, because reading the field would let a commander discover
  that a marker has gone stale by noticing that the grenade would catch nobody. `PlanThrow` with
  no candidates reads the field and is what `Throw` uses; anything *deciding* must pass a list.
- **A charge is the only thing in the game that runs out**, and `UtilityModel.ChargeValue` is what
  stops the scorer leading with grenades. Without it a commander threw both at the first soldier
  it saw, measurably: four Commander tests changed behaviour and that is how it was found. It is
  set at about one clean rifle shot, which is what makes a grenade the answer to the shot you
  cannot take rather than a better version of the one you can. If grenade behaviour ever looks
  wrong, suspect this before suspecting the blast model.
- **Four Commander tests deploy a rifleman with an empty pouch**, through `Barehanded`. Given a
  charge and a man behind a wall, a commander throws it — correctly — and a test named after
  flanking or after going to look stops exercising either. One mechanism per situation; the
  grenade behaviour is asserted in `OrdnanceTests`, where it belongs.
- **The arc gets harder the closer you stand to the wall.** `4·s·(1-s)` collapses toward both
  ends of the throw, so hugging a three metre wall and throwing seventeen metres wants seven and a
  half metres of arc and fails, where the same wall halfway along wants about two. That is
  arithmetic rather than a rule and it is the right behaviour, but it is the first thing that
  looks like a bug when a throw refuses from what seems like an easy position.
- **A throw that clips lands at the thrower feet**, or on the near side of the wall it caught.
  `LobResult` carries which wall and how much arc was wanted, so a preview can say why — and a
  preview that does not show a clipped throw is a preview that lets a player grenade themselves.
- **A blast traces outward from the burst, not inward from a shooter.** `SightSolver.TraceFrom`
  takes a point rather than a vantage for exactly this. It is why a wall shelters you from a
  charge on its far side and does nothing about one lobbed over, with no rule written down about
  explosions and cover — and it is why the burst height on `BlastModel` is load-bearing rather
  than flavour.
- **Nothing glances in a blast.** Obliquity models a solid object skipping off a plate it met
  edge-on. A blast is not one object along one line, and crediting it with deflection off a
  shoulder would be borrowing arithmetic that is about something else.
- **A mine does not go off under the side that laid it**, and that is a simplification standing in
  for the awareness ladder having no opinion about objects. See [../decisions.md](../decisions.md)
  entry 034, item 2 — and item 1, which is the same hole from the other side: a noise has to be
  about a person, so a mine whose layer has gone down is heard by nobody.
- **`Battle.Mines` is the ground and `Battle.MinesOf` is what one side may see.** Contract 3
  lives in the second. An interface drawing the first shows a player where the enemy mined.

- **A committed move has been paid for and not taken.** `Battle.Commit` spends the points and
  builds the window; the mover stands at the start until `Resolve` walks it along. So anything
  reading the field between the two — an interface drawing the choices, a test asserting mid-window
  — sees a soldier whose allowance is gone and whose feet have not moved. That is the state the
  whole seam exists to make available, and it is the one nothing before this could produce.
- **`Commander` only ever ends the turn of the soldier it set out to drive.** Three things hand
  the turn on without the loop asking: being dropped mid-move, having an ambush sprung on you, and
  walking off the field. Ending it again banks somebody else's allowance and passes it on before
  they have done anything with it, which was a live bug until entry 040. If a soldier ever seems
  to silently lose a turn, suspect this shape first.
- **An objective slopes and a marker does not.** `Objective.Progress` is a gradient measured in
  action points along the graph, which is what lets a search one step deep set off toward
  something three turns away. A marker is a point, so hunting still reaches about one move — the
  same limit as ever. Do not be tempted to slope a marker: soldiers would walk at ghosts from
  across the map, which is what `MarkerDecay` exists to prevent.
- **The approach field is priced off the listed cost of the ground**, not off what any particular
  soldier pays for it, and it is cached per map revision. It describes the ground, like
  `Battle.Loudness` does; how quickly a given soldier crosses it is about them. One backward
  search over the whole graph, not one per candidate destination — which is the difference between
  an objective a commander can afford to want and one it cannot.
- **The departure reading is sampled, never polled.** `Battle.Withdraw` takes it before
  `Awareness.Forget` runs, because after that there is nothing to read: a condition of the form
  *leave with nobody above a suspicion*, asked afterwards, answers Unaware for everybody, always.
  It is a sample per departure rather than a mark held across the battle, deliberately — a
  monotone mark would forbid silencing a witness, which is the best move in the game and works
  today with no rule saying so.
- **A battle with no objective behaves exactly as it always did.** `VerdictFor` falls back on last
  side standing and `TowardObjective` returns nothing, so every scenario and every test that
  predates objectives is untouched. That is what made this safe to add to every appraisal rather
  than to a special path, and it is worth preserving.

- **The clock is two halves and they live in different files on purpose.** `Deadline` is on the
  objective, because a round limit is a property of a mission; `Alarm` is on `AwarenessTracker`,
  because *the word got out* is a fact about what a side knows and would be true of that ground
  with no mission on it. Anything that wants to know whether a squad is out of time asks
  `Objective.Stop`; anything that wants to know whether the garrison has been told asks
  `Awareness.AlarmOf` or `AlarmAgainst`. Do not derive either from the other.
- **Only a set raises an alarm**, and the gate is in `Relay` — the one place word leaves the
  person holding it. A shout and a comrade's reaction go through the same method and neither
  counts, which is load-bearing on real ground rather than pedantic: the waystation's barn and
  tower are outside earshot of the compound, so who has the radio decides whether a sighting is an
  incident or a mission.
- **`Forget` wipes contacts and never the alarm.** Word sent cannot be unsent, so silencing the
  signaller one round late buys nothing back. That is the asymmetry that makes the set worth
  killing *first*, and it is the counter-part to the rule that makes the quiet kill work at all —
  if a test ever shows an alarm disappearing when somebody goes down, this is what broke.
- **The clock running out is `Abandoned`, not `Failed`.** A squad still in the field at first light
  has lost the mission and has not lost the squad, which is the whole reason there are three
  endings. `Failed` stays for there being nobody left who could have brought it home.

- **A mission is one journey, measured in action points, and the task is part of it.**
  `Objective.Remaining` is what is still owed from where you stand: the walking there, the points
  the job itself wants, and the walking home. So a stride toward the charge and a stride spent on
  the charge are worth exactly the same, and the score is continuous across the moment the task
  completes — finishing it does not jolt anything, it shortens what is left. Anything added to
  this model should be expressible in action points or it does not belong in `Remaining`.
- **The exit is not the far end of the journey.** Progress at the exit with the job undone is
  *lower* than progress at the place, because the way home runs by way of the thing you came for.
  That is the whole of what entry 048 asked for, and it is the first thing to check if a squad
  ever walks out early again.
- **The horizon stretches to the length of the job, once, at `Start`.** It decides how steep the
  slope is and never how far it reaches, so a mission longer than `ObjectiveHorizon` still slopes
  all the way back to the deployment. Measured off where the squad actually stands, because the
  map's diameter is not the mission's length — on a large map that would flatten every objective
  to nothing.
- **A commander will not walk out with the job undone**, and the rules will. `Battle.Extract`
  permits it and settles to `Verdict.Abandoned`; `Commander` is simply not offered it, because
  weighing cutting your losses against pressing on needs a notion of how the battle is going that
  the scorer has not got. So a squad being cut to pieces stands and takes it.
- **`Objective` is a class, not a record.** It holds how far along the mission is. A record that
  changes is a record in name only, and this is the one entity in the rules that is not a unit.

- **The batch is checked in and off by default.** `tests/Hexcom.Core.Tests/Measured/` is an
  instrument, not a suite: `[BatchFact]` skips unless `HEXCOM_BATCH=1`, and `HEXCOM_SEEDS` says
  how many matches an arm runs. It asserts nothing on purpose — a batch prints what happened and a
  person reads it, and an assertion there would pin today's balance in place, which is the
  opposite of what a measurement is for.

  ```bash
  HEXCOM_BATCH=1 HEXCOM_SEEDS=100 dotnet test tests/Hexcom.Core.Tests --filter "FullyQualifiedName~Measured" --logger "console;verbosity=detailed"
  ```

  **One question per class**, because xUnit runs classes in parallel and a batch is over an hour
  otherwise. Outcomes are decided by the seed and never by the clock, so nothing about running six
  at once moves a figure.
- **The batch builds the mission the file describes rather than the objective it can say.**
  `waystation.hexmission` still carries a withdrawal, and measuring an objective dial against a
  withdrawal on that ground measures the wrong thing — it is achieved by turning round and going
  home. `Measured/Waystation.cs` builds the reconnaissance off the same places the file declares
  and takes everything else from the file unchanged, so there is still one copy of the waystation.
  Delete that when Content uncomments the line.
- **A commander per side, never one for both.** A dial turned on both sides at once measures
  nothing: the two halves move together and the match comes out where it started.

## Open questions

Owned here. The design doc carries more, marked *Open* in the section they belong to; these are
the ones that block or shape what Core does next.

- **Nothing tells a commander how the battle is going.** It cannot weigh cutting its losses
  against pressing on, so it is not offered the choice: leaving with the job undone is a decision
  the rules allow and the scorer never takes. Everything it ranks is one action against another at
  one moment, and *the mission is lost, get out* is a judgement about the whole thing. This is the
  sharpest thing the search cannot do, and it arrived with objectives rather than being fixed by
  them.
- **Nothing prices getting there unseen**, and entry 080 measured what that costs: no
  reconnaissance on the waystation achieved in any arm, every squad held at `Engaged`. The
  objective pays for reaching the place and coming home, and the rung `Sortie.Unnoticed` judges on
  appears nowhere in the arithmetic. It is the job at the head of this file.
- **`ObjectiveValue` is saturated, measured.** 60, 120 and 240 are indistinguishable on the
  waystation; 15 stands and fights until the night runs out. Entry 080 says leave it at 120 until
  the term above exists, because tuning it now is tuning a race.
- **`ObjectiveHorizon` and `ObjectiveValue` are one dial, measured.** Below the journey the horizon
  is stretched and inert; above it the scorer answers to value per point of ground, so horizon 16
  at 120 plays exactly like horizon 4 at 30. Do not tune the two separately.
- **Being come looking for costs the shooter nothing.** `GivenAway` prices what a listener could
  do from where they stand, and from behind a wall that is nothing — the pinned test
  `SomebodyWhoHearsTheShotAndCannotReachYouCostsYouNothingYet` still holds. A unit now does come
  looking, so the figure is wrong, and the right one is the best shot the listener could reach in
  a turn: their reachable set and a trace per node, inside every shot appraisal, per destination.
  A search inside a score. `AppraiseWord` has the same gap from the other side. Profile before
  attempting it; the obvious fix is caching the reachable set per unit per decision.
- **A shot that kills its target still gives you away to the target.** `GivenAway` counts the man
  being shot at among the people who now know where you are, and if he goes down he is not
  anybody. That is the entire argument for the quiet kill and the model does not make it. Fixing
  it means the announcement preview knowing which enemies survive the shot it is previewing,
  which is a small change to `WouldAnnounce` and a fiddly one to get right.
- **`MarkerDecay` is the second dial to watch.** At a half per round past the fresh two, a marker
  three rounds old is worth a quarter of a sighting, and the trace of the acceptance test shows
  it fading to nothing in five. Whether that is too quick to hunt with or too slow to stop
  chasing ghosts is a question only a batch of matches can answer, and the batch can run now.
- **A startled soldier still cannot decline.** Holding fire is offered to overwatch and to an
  ambush and not to surprise, on the argument in `../decisions.md` entry 040: surprise is the
  involuntary one and offering it the chance to do nothing is offering it the chance not to
  flinch. Measured, it takes the offer — a dive costs two points and buys a discounted share of
  one shot, which on open ground comes out just under nothing. That is a defensible line and it
  is not obviously the right one for a *player*, who may want their own startled soldier to keep
  its points. It is one line if View asks.
- **`ShieldValue` is the dial to watch first.** At 0.15 a fully soaked eight point beam scores
  0.72 against a snap shot costing 0.75 — near enough break-even that the ordering between firing
  pointlessly and doing something else is decided by noise. Either the shield term is too generous
  or a point of reserve is too cheap, and only matches will say which.
- **The overwatch awareness gate can now be re-examined.** Flagged in the doc and in
  `ReactionModel`, with the two dials named. It was gated on having an AI to run matches with;
  there is one, so this is the first thing to point a batch of headless matches at.
- **`UtilityModel.ChargeValue` prices a charge at a flat figure however much fight is left.**
  The last one should be dearer than the first, and one carried out of the battle was worth
  nothing at all — both are real and both need a notion of how far through the fight this is,
  which nothing in the rules has. It is also the one new dial that a batch of matches would
  settle quickly, because a commander that spends its grenades badly loses and says so.
- **Nothing spots a mine, and nothing lays one but a player.** Both are the same hole seen twice:
  the awareness ladder holds beliefs about soldiers and has no way to hold one about a place, and
  a soldier with nothing to want cannot pick ground to deny. See [../decisions.md](../decisions.md)
  entry 034, items 1 to 3. The first wants a contact about a place — which an explosion, a door
  and a falling body all are; the third waits on objectives rather than on a deeper search.
- **A throw is only ever aimed at the tile under somebody.** Offsetting to catch two at once, or
  to keep one of your own out of the radius, is a search — every node in range crossed with
  everybody in the blast, per candidate, per decision. What is built will decline a grenade that
  catches its own and will not go looking for the one that avoids them. Entry 034, item 4.
- **Most balance numbers are still set by reasoning.** `ObjectiveValue`, `ObjectiveHorizon`, the two `CostProfile`
  archetypes and `RemovalBonus` have been measured (entry 080); everything else is an argument, and
  the design doc says why each one is what it is. The batch in `Measured/` is how to turn another
  into a finding — and a question about anything a reaction scores has to build the battle with its
  model, because windows rank with `battle.Tactics` and not with the commander's.

## Recent work

```bash
git log --oneline -20 -- src/Hexcom.Core tests
```
