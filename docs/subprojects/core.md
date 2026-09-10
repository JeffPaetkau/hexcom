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

## The job — measure the numbers, and the clock

Branch `core/measured`. Read the rest of this file before starting; the turn loop below and the
gotchas after it are the things that will bite, and the two about objectives are the two most
likely to.

**What exists.** Every system the design doc describes bar suppression, and every mission shape in
the book bar three. A reaction window a person can answer, a battle that ends because a squad did
what it came for, and an objective at a place that a squad will actually walk to.
`docs/decisions.md` entries 061 and 062 are the argument for the last of those.

**The job is the first measurement in this project's history, and then the clock.** In that
order, because the first one is overdue and the second is small.

- **Run the matches and write down what they said.** `Commander` drives both sides headless, the
  waystation mission fights itself in about two seconds for twelve seeds, and *every balance
  number in this game is still an argument*. Four are load-bearing and none has been measured:
  `UtilityModel.ObjectiveValue` and `ObjectiveHorizon`, which decide whether a squad walks past a
  firefight to reach an exit or stands in one ignoring it; the two `CostProfile` archetypes, which
  entry 062 turned on for the first time in a live behaviour change nothing tested; and
  `RemovalBonus`, which values a signaller at a rifleman. **Run each of them both ways over a few
  hundred seeds and record the figures in `../decisions.md`.** It would be the first entry in this
  project to say a number *was measured* rather than argued, which is worth more than any of the
  numbers it settles.

  Two of the readings entry 048 already offers are worth separating while you are there: the scout
  is `Unaware` to everybody in twelve matches and the trooper is `Searching` in nine, and nobody
  has established whether that is the noise of the walk or simply who is nearer the road. Entry
  037 says a turn's walk on gravel is heard further than a slug rifle, which would mean the thing
  that loses a stealth mission is already footsteps rather than eyes.

- **The mission clock.** Entry 030 named it as the one genuinely new thing the six shapes want and
  it has been nobody's for four increments. What is missing is a record of the moment a hostile
  **with a set** has registered somebody and then had a turn in which to use it; everything else
  in that sentence is a query that exists. A round limit that ends a battle is `Battle.Round` and
  a comparison. Settle where it lives: a round limit is a property of the mission, but *the alarm
  went out* is a fact about the awareness model, and putting it in the wrong one makes the other
  awkward for good.

- **Extraction and capture, if the two above go quickly.** A thing that can be carried, and a way
  to put a soldier down that is not damage. Both are real new state, neither is needed for a
  playable greybox, and they are the half of this brief to drop.

**Content is waiting on one line, and it is already written.** Entry 059 says
`waystation.hexmission` carries its objective statement commented out, and that landing the rule
is an uncomment and a deletion:

```
objective reconnaissance player at house out cottages unnoticed suspicious
```

That is the shape entry 061 built — every sortie carries its own exit and threshold, rather than
objectives composing and a mission carrying two — so the statement maps straight onto
`Reconnaissance(side, place, exit, within, unnoticed)`. **What it does not name is `within`**, the
distance a look has to be taken from, which defaults to twelve metres; entry 059's own measurement
says the house can only be seen from fourteen places inside the yard, so the default is probably
right and the parameter exists if it is not. Whoever picks this up should say so in
`../decisions.md` and let Content uncomment.

**A garrison that does not move is Core's, and it is not this brief's.** Entry 059 measures three
of the waystation's four hostiles never acting at all, and names the cause: nothing in the game
patrols, so a standing order in a mission file has nothing in the search to hand it to. That is a
real hole and it is bigger than a brief — it wants a notion of what a soldier is *doing* rather
than where it is, which is the same missing thing as *the mission is lost, get out*. Both are
about a soldier having a standing intent, and neither should be built piecemeal.

**Two findings from real ground that are still open and still Core's.** Both are entry 039, both
were invisible on a disc, and both nearly vanished when the map changed — which says the geometry
that produces them is specific rather than that they are fixed.

1. **Every charge in a match lands on one empty hex.** The crater rule marks the thrower at the
   burst, so the next throw is aimed at the crater, and five charges went into a hex nobody had
   stood on since round 3. The rule is right — a grenade should be able to make noise somewhere
   you are not — and its interaction with a one-step search is not.
2. **A soldier paces between two tiles on a shot it never takes.** `Order.Opens` credits a move
   with a shot, and from the new tile the best option is the move back, credited with the same
   shot. What is missing is either the move costing the shot it displaces, or the shot being taken
   when it is the thing the last move was chosen for.

**And one thing this increment made sharper rather than better.** A commander will not walk out
with the job undone, because weighing *cut our losses* against *press on* needs to know how the
rest of the battle is going. That is the right call for now and it means a squad being cut to
pieces stands and takes it. Entry 058 says so; whoever gives the scorer a notion of how a battle
is going should look here first.

**Out of scope.** `game/**` as ever. Which objective a mission carries and where — Content's, and
entry 061 unblocked it. Suppression, still: nothing depends on it.

**The test that it worked:** an entry in `../decisions.md` that says a figure was measured, with
the seeds and the counts under it — and a mission that ends because the alarm has been out for
three rounds.

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

## Open questions

Owned here. The design doc carries more, marked *Open* in the section they belong to; these are
the ones that block or shape what Core does next.

- **Nothing tells a commander how the battle is going.** It cannot weigh cutting its losses
  against pressing on, so it is not offered the choice: leaving with the job undone is a decision
  the rules allow and the scorer never takes. Everything it ranks is one action against another at
  one moment, and *the mission is lost, get out* is a judgement about the whole thing. This is the
  sharpest thing the search cannot do, and it arrived with objectives rather than being fixed by
  them.
- **An objective is worth more than any fight, and nobody has measured that.**
  `UtilityModel.ObjectiveValue` is a whole squad's worth of vitality, deliberately larger than
  anything a shot can score, so a squad told to get out walks out through fire rather than
  stopping to trade — which is the behaviour the complaint about elimination was asking for, and
  is also the first number in this game that can make a soldier ignore what is in front of it.
  `ObjectiveHorizon` decides from how far away it pulls. The failure modes are legible and named
  in `../decisions.md` entry 044: walking past a firefight to reach an exit means the value is
  too high, standing in one ignoring the exit means the horizon is too short. Both are exactly
  what a batch of matches settles.
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
- **Every balance number is set by reasoning, not measurement.** Treat the figures as arguments
  rather than findings, and check the design doc for why one is what it is before changing it —
  several are load-bearing in ways their size does not advertise. This is now *testable* rather
  than merely true, which is the whole reason the AI came before grenades.

## Recent work

```bash
git log --oneline -20 -- src/Hexcom.Core tests
```
