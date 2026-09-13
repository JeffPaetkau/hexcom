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

## The job — the quiet way round

Branch `core/quiet-way`. Read the rest of this file before starting; the gotchas about the term,
the crossing, the rounds ahead, the briefing and the transcript are the ones that will bite.

**What exists.** Every system the design doc describes bar suppression; three of the six mission
shapes; a mission that stops (`../decisions.md` entry 082); a batch anybody can run again with the
same seeds (083); a term that prices being seen — on the crossing as a reaction window takes it,
on the arrival as a rate, on the recovery past the rung — and a briefing that holds until the
ground says otherwise and carries the way a post watches (087, 091); and a transcript instrument
that prints every decision of a match with what it was chosen over (091).

**What the batch said, in one line: briefed, nobody fights and nobody goes in; blind, the squad
wins one match in seven by being seen and waiting to be forgotten.** Entry 091 has the tables
and the transcript. The followers are fixed: the three faults that set them fighting were the
crossing the term did not price, the clamp that went dead at the rung, and a briefing that faded
like a sighting, and none of them was the hunt entry 087 guessed at. Briefed, the squad is never
seen, never fires and never takes the look: from the hidden ground at the bridge every move
toward the house crosses the gate sentry's front or is heard by four men, and the route that does
neither goes away from the house before it comes back. A search one step deep cannot see it.
That is the blade-carrier limit for the third time, and this time it is the mission. The
acceptance test of the last two briefs — *achieved in more than a handful of matches in a
hundred* — is met at last, by the blind arm, at fifteen: the squad walks in, is seen, hides until
the contacts decay and walks out under Suspicious. That is the rules working and a decay dial
nobody has measured, both at once; entry 091 says so and it is Master's to weigh.

**The job is the route.** `Objective.Progress` is a gradient in action points along the movement
graph, priced off the listed cost of the ground and cached per map revision. Price it, per
soldier, through what that soldier believes is watched: a link into a hex that hands a sensed
enemy a look costs that look in the same points, as `Tactician.Startled` prices a crossing and
`Coming` prices an arrival. Then the slope runs along the quiet way, the one-step search follows
it hop by hop, and a route that leaves the direct line is worth taking from the first hop because
each hop is nearer along the field. Things to settle deliberately:

- **Whose field.** The listed field describes the ground; this one describes what one soldier
  knows, so it is per soldier and per decision, and `Sensed` changes as contacts do. One backward
  search over the graph per decision is what an objective costs today; the exposure per node per
  sensed enemy is a trace each, which is the same order as a decision already spends on the
  arrival looks. Profile before caching, and cache per soldier per contact file if it is needed.
- **What a look costs in points.** The exchange rate between a look-point and an action point is
  what the term already says: a share of the objective per share of the bar. Derive it from
  `ObjectiveValue`, `Bar` and the journey rather than adding a dial; if a dial is needed anyway
  it goes in `UtilityModel` with the argument beside it.
- **Whether `Remaining` changes or only `Progress`.** The way home has to be quiet too, and
  `Urgency` reads the journey against the night; a watched route is longer, and whether the clock
  should see that is a question to answer in the `<remarks>`.
- **Run the briefed question again, and record the difference.** Twelve seeds first, with
  `HEXCOM_PROGRESS`, and the transcript on a seed that still hides; a hundred seeds of the briefed
  question is most of an hour.

**If that goes quickly, the two faults a one-step search shows on real ground** — entry 039, both
still open, both invisible on a disc:

1. **Every charge in a match lands on one empty hex.** The crater rule marks the thrower at the
   burst, so the next throw is aimed at the crater. The rule is right and its interaction with a
   one-step search is not.
2. **A soldier paces between two tiles on a shot it never takes.** `Order.Opens` credits a move
   with a shot, and from the new tile the best option is the move back, credited with the same
   shot.

**Two things settled that are not this brief's to act on.** `ObjectiveValue` is saturated at 60
with the term in as it was without, and for a reason that is now understood: the term is a share
of the objective, so the value moves both sides of the trade at once. Leave it at 120. And entry
086's relay hole is now inherited by `Tactician.Blowing` as well as `GivenAway`; the preview with
the relay in it fixes three things at once and is worth doing, but it is not what stands between
the waystation and a win.

**Content is waiting on one thing from Core, and has it.** `Battle.Brief(side, unit, rung)` is
the call, and it hands on the facing the deploy line states, so the grammar for the briefing's
presence part (087, *For Content*) needs no facing of its own. Until it lands,
`Measured/Waystation.cs` briefs all four posts by hand in its `briefed` arm and the file plays
blind. `Waystation.cs` also still builds the objective itself, for the clock the file cannot yet
write (082); delete both stand-ins when the file can say them. **And one question is Content's
to answer on the ground**, 091 *For Content*: whether a route from the west road to the drain
exists that never enters the gate sentry's front arc and is not heard from the gate, and how long
it is.

**A garrison that does not move is still Core's, and still not this brief's.** Three of the
waystation's four hostiles never act; milestone 2 on `../map.md`.

**The two questions from the second play-through are answered** (entry 095), and neither changes a
rule. The shot's price stays. 25% dearer takes the surprise snap out of every purse and the
waystation goes from fifteen achieved to one. Cheaper changes the mode the garrison fires and not
the mission. `SEARCHING` beside a hostile is the rules: one move cannot take a fresh sentry past it.

**Out of scope.** `game/**` as ever. Extraction and capture. Suppression.

**The test that it worked:** entry 091's briefed table rerun, and a row in it where the look is
taken in most matches of a hundred with the alarm out in few — and then, still, the waystation
achieved in more than a handful.

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
- **One move cannot take a sentry who held nothing past Searching, however close it ends.** A
  window gives a reactor with reserve one look, at the first step it can see, and hearing the walk
  stops at one short of `AlertedAt`. The best look in the game is `LookGain` times perception
  over ten, 71 for a scout's eyes, which are the sharpest there are, so a man walked right up to reads Searching until his own turn
  ends and then Engaged. Searching beside a body is therefore the sign he *did* see the walk: from
  behind he gets no look and the footsteps alone leave him Suspicious. Entry 095, and
  `WalkingStraightUpToASentrySFaceLeavesHimSearchingUntilHisOwnTurnComesRound` pins it.
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
  <br>**Where the time goes is the sight traces, and the solver now remembers them.** Pricing the
  crossing made a decision trace every step of every route against every sensed enemy, and a
  briefed waystation match went to two hundred seconds; the routes share their hexes, so
  `SightSolver.Trace` keeps every pair of vantages it has answered until the map's revision
  changes, and the same match is about ten. Nothing about a trace depends on anything but the map
  and the layout, which is what makes that safe, and a wall going up empties it. Bounded at a
  quarter of a million entries, which is memory and not balance.
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
  at once moves a figure. `HEXCOM_PROGRESS=<path>` appends a line per match — arm, seed, seconds,
  verdict, when the look and the alarm came — that can be tailed while the runner holds the rest.
- **The batch builds the mission the file describes rather than the objective it can say.**
  `waystation.hexmission` still carries a withdrawal, and measuring an objective dial against a
  withdrawal on that ground measures the wrong thing — it is achieved by turning round and going
  home. `Measured/Waystation.cs` builds the reconnaissance off the same places the file declares
  and takes everything else from the file unchanged, so there is still one copy of the waystation.
  Delete that when Content uncomments the line.
- **A commander per side, never one for both.** A dial turned on both sides at once measures
  nothing: the two halves move together and the match comes out where it started.

- **Being seen is priced as a difference between two poses, never as a reading of one.**
  `Tactician.Keeping` is `Quiet(after) - Quiet(before)`, both against the same list of sensed
  enemies, for the reason the posture score is: a soldier standing in a sentry's eye has to see
  that stepping out of it is worth something. A reading of the pose after alone would score
  staying put at nothing and moving at the cost of the walk. If a unit ever stands in plain view
  of a sentry it knows about with a mission that forbids it, check that both halves are being
  asked the same question.
- **`Quiet` takes the worst enemy, not the sum, and the slope runs to the ceiling, not to the
  bar.** One enemy over the bar loses the mission and a second loses nothing more. Past the bar
  the share keeps climbing, because the mission is judged at departure and a contact decays: a
  soldier predicted at Searching is one round of hiding from whole, one at the ceiling is five,
  and the term can tell them apart. The first version clamped at the bar, and a soldier anybody
  held at the rung read every pose as the same nought — staying in the eye, stepping out of it
  and firing all cost nothing more, which is how the followers walked to the gate the turn they
  were noticed. Entry 091 has the transcript. The fight consequence is still priced elsewhere,
  by `Aimed` and `Spared`.
- **A move is priced on the crossing, not only the arrival.** `Quiet` takes a `route` — every
  pose the walk passes through, off the same `CommittedMove` timeline the window will read — and
  for each sensed enemy prices the one look the window would give it at the first step it can see
  that is not behind it, exactly as `ReactionWindow` picks the tick. Anything appraising a move
  through the Tactician must pass the route; `AppraiseMove` with none prices the arrival alone,
  which is what a test of the arrival wants and what a commander must never do. Before this the
  followers on the waystation were tagged in transit by the gate sentry on the way to ground the
  term had priced as hidden, and the surprise look that tagged them is a Searching contact in one
  look at twelve metres.
- **The rounds ahead are counted, and `Ahead` is where.** A look at the arrival is a rate — a
  look a round for as long as the pose is held — and a hidden arrival is a round of forgetting per
  round, so both are multiplied by a geometric count of the rounds until the job is done or the
  night is out, at `FutureDiscount`. That is what nets a one-off crossing under the bar against
  the hiding that follows it; without it a single look at Suspicious cost a quarter of the
  mission, and the squad stopped at the edge of the watched ground and never went in. `Ahead`
  reads `Objective.Owed` and `NightLeft` at the list allowance, never a particular soldier's.
- **A marker carries a facing when it has one.** `Contact.LastKnownFacing` is set by a look, a
  flash and a briefing, copied by a relay, and cleared by a sound and by being shot at.
  `Threat.FacingKnown` says which, and `Coming` and `Crossing` price a known facing exactly and an
  unknown one averaged over six. On the waystation the average priced the road past the gate at
  half a look and the ground behind the sentry at the same half; with the facing the briefing
  states it is a full look and nearly nothing, which is the whole of an approach.
- **The term reads `Sensed`, not `Known`.** `Known` stops at `ActsOn` because a soldier does not
  shoot at something it has half-glimpsed; `Sensed` goes down to Suspicious because a careful one
  does not walk into the view of a place it registered something in. The Commander still passes
  `Known` to everything else, so a stance change to get out of a merely-suspected sentry's eye is
  not offered — `Postures` yields nothing with no known threat — while a move is, because moves
  are offered whenever there is an objective to move toward.
- **Nothing prices an eye the soldier has not registered**, and a briefing is how it registers
  one before anybody has looked. On the waystation the squad deploys on the road the gate sentry
  watches and he takes his first look before the scout has taken any; blind, the scout's first
  turn is walked at full stride into the view of a man it will only know about at the end of it.
  That is entry 087's finding and it is not a fault in the term.
- **A briefing is a contact that holds.** `Contact.Briefed` marks one, and `Observe` will not
  decay it until the observer has had a line to the place it names or some other channel has
  reported the man — every site that sets `LastContactRound` clears the flag. The first version
  decayed a briefing like a sighting, and the four posts were out of every contact file by round
  three, before anybody had a line to any of them; the scout then walked up to a gate it had been
  told was manned. A briefed marker also reads as fresh for as long as it holds, because it has
  no contact round to be stale from, and that is deliberate: a post is more reliable as a place
  than a sighting is, and the fight terms priced against it are held in check by the quiet term
  rather than by a discount on the marker.
- **`Commander.Step` is one decision; `TakeTurn` is `Step` until nothing, then `EndTurn`.** An
  instrument that steps must end the turn itself, and `Taken` starts afresh with each soldier
  stepped. `Measured/Transcript.cs` is the instrument: `HEXCOM_TRANSCRIPT=<seed>` prints every
  decision of a waystation match with the options it was chosen from, the two moves that would
  have gone furthest toward the job whatever they cost, and for each move the crossing, the
  progress and whose eye it ends in — `HEXCOM_BLIND=1` for the unbriefed arm, `HEXCOM_VALUE` for
  the objective's worth. It reads certainty figures the interface may not, because it is an
  instrument and not a screen. About fifteen seconds a match.
- **`Urgency` moves the level of `Progress`, not only the slope.** Above one, `Progress` can read
  more than one; anything comparing it to a whole — a display, an assertion — has to expect that.
  Only differences rank, so nothing in the search cares, and `Finishing` still pays exactly
  `ObjectiveValue`. `PerPoint` is the all-night rate and is wrong once the night is short; price a
  shortening through two `Toward` readings, which is what `WorkWorth` does.

## Open questions

Owned here. The design doc carries more, marked *Open* in the section they belong to; these are
the ones that block or shape what Core does next.

- **Nothing tells a commander how the battle is going.** It cannot weigh cutting its losses
  against pressing on, so it is not offered the choice: leaving with the job undone is a decision
  the rules allow and the scorer never takes. Everything it ranks is one action against another at
  one moment, and *the mission is lost, get out* is a judgement about the whole thing. This is the
  sharpest thing the search cannot do, and it arrived with objectives rather than being fixed by
  them.
- **A briefed squad stops at the edge of the watched ground, measured.** With the crossing and
  the recovery priced and the briefing holding, nobody fights and nobody goes in: from the bridge
  every move toward the house crosses the gate sentry's front or is heard by four, and the route
  that does neither leaves the direct line before it comes back, which a search one step deep
  cannot see — entry 091, and the job at the head of this file. Whether such a route exists on
  the waystation at all is Content's question, in the same entry.
- **Being forgotten is the second best move in the game, measured.** Blind on the waystation the
  squad is seen in every match and now achieves fifteen in a hundred by hiding until the contacts
  decay — `DecayPerTurn` at fifteen takes a soldier from Alerted to under Suspicious in four
  quiet rounds, and a garrison that does not move never goes to look. Entry 091. The dial has
  never been measured and is now load-bearing for the mission.
- **The crossing assumes every sensed enemy has reserve.** A reactor gets its mid-window look
  only with points banked, and the walker cannot know who has; on the waystation every sentry
  banks the lot, so the assumption is exact there and conservative elsewhere. A garrison that
  moves (milestone 2) will spend its reserve, and the term will then price crossings that never
  happen. Nothing to do until then.
- **`ObjectiveValue` is saturated, measured twice.** 60, 120 and 240 are one row with the quiet
  term in as they were without it, because the term is a share of the objective and the value
  moves both sides of the trade at once. Leave it at 120; the live range is still 30 to 60 and
  nothing in it is a win.
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
- **A shot that kills its target still gives you away to the target, in `GivenAway`.**
  `Tactician.Blowing` now counts him only at the chance he survives, which is the quiet kill
  priced for the mission; `GivenAway` still counts him in full for the fight. The same
  announcement preview also leaves out the target's relay to his friends — entry 086, View's
  finding, now with the mission term as a second consumer.
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
- **The surprise snap fits its purse by two points.** `⌊50 × ReserveFraction × SurpriseFraction⌋`
  is 17 and a snap is 15. Measured on the waystation (entry 095), 25% dearer firing puts it out
  of reach, and the mission collapses in the same arm. The collapse is not yet traced to it; a
  transcript at that price would settle it. Check the sum before moving the turn size, the bank,
  the purse or the snap.
- **The reaction window's price has never been measured where the window matters.** On the
  waystation, across eight hundred matches at four firing prices, overwatch fires a tenth of a shot
  a match and a surprise shot never kills. Every kill is a turn shot. Asking whether half a turn is
  the right shot for the window needs an overwatched approach and a Commander that sets arcs
  (entry 095, *For Master*).
- **Most balance numbers are still set by reasoning.** `ObjectiveValue`, `ObjectiveHorizon`, the two `CostProfile`
  archetypes and `RemovalBonus` have been measured (entry 083), and the firing prices as a whole on
  the waystation (095); everything else is an argument, and
  the design doc says why each one is what it is. The batch in `Measured/` is how to turn another
  into a finding — and a question about anything a reaction scores has to build the battle with its
  model, because windows rank with `battle.Tactics` and not with the commander's.

## Recent work

```bash
git log --oneline -20 -- src/Hexcom.Core tests
```
