# Core — the rules

Everything the game is, as plain .NET. Hex geometry, cover, movement, sight, detection,
initiative, damage, reactions, and — next — the AI.

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
purpose, balance numbers in their eight homes, and one horizontal unit is one metre.

---

## The job — grenades and mines (build order 05)

Branch `core/grenades`. Read the rest of this file before starting; the turn loop below and the
gotchas after it are the things that will bite, and the reaction timeline is the thing a mine
has to fit into.

**What exists.** The AI is complete for what the game can currently express: `Tactician` scores
one action in vitality over the same queries the interface shows, `Commander` takes a turn with
it, and a soldier that hears something goes round the corner to look — `Tactician.Known` builds
threats from a marker as well as from a sighting, discounted by `Tactician.Credence` for how
long the marker has gone unconfirmed. Two sides that start out of contact find each other and
fight. What it cannot do is priced in the gotchas and open questions below, and none of it is
blocking.

**The job is the two items the design doc's weapons table (section 10) leaves for later.** Its
own words on each are the brief:

- **Grenades — an arcing trace.** *Every trace so far has asked whether a straight line gets
  through, and an arc explicitly does not: the whole point of throwing one is to put it
  somewhere you cannot shoot.* A second query beside `SightSolver`, answering whether a lobbed
  object clears the intervening walls and where it lands if it clips one. Damage is an area, so
  it wants a shape of its own rather than a `ShotPlan`; the layers it meets per face are what
  `Protection` already does. A grenade is the loudest thing after a slug rifle, and
  `AwarenessTracker.Hear` is public precisely so it can raise the noise.
- **Mines — a reaction owned by the terrain.** *A mine is an overwatch that a unit is not
  standing behind: a trigger on a tile, resolved at the tick the mover enters it. Same clock,
  same resolution order.* `ReactionWindow` already walks the mover along a `CommittedMove` and
  fires at landing ticks; a mine is an offer with no reactor, placed by the map.

**Settle before writing much.** Whether a grenade is a `FireMode` on a `WeaponProfile` or a thing
of its own. The weapon table makes it a weapon; `Gunnery.HitChance` and the reaction timeline
assume a shooter, a target and a face, and a grenade has a landing point and a radius instead.
Whichever way it goes, the AI has to be able to weigh one — `Tactician` scores what
`Gunnery.Expect` returns, so a grenade wants an `Expect` of its own — and the interface has to
be able to show the arc. Contract 2 applies as ever.

**Out of scope.** `game/**`. The open questions below are real and none of them are this job;
the one most likely to tempt is the search depth, because a soldier that will not walk two turns
toward a marker will not walk two turns toward a grenade target either. Record, do not build.

**The test that it worked:** a soldier behind a wall it cannot be shot through is dug out by a
grenade lobbed over it, and a mine on the approach fires on the mover at the tick it steps on
the tile, out of nobody's reserve.

After this: the Godot greybox (build order 06), which is View's.

---

## How a turn runs

Worth knowing before touching anything, because most of the surprises are in the order.

```
Battle.Start()      roll initiative, book everyone, hand the first turn out
  └ Advance()       refill AP · recharge shields · clear Reserve and Overwatch
                    (NOT Ambush) · rebook for next round
  the active unit acts
      Move · Fire · Face · ChangeStance · SetOverwatch · Arm · SpringAmbush
  Battle.EndTurn()  Awareness.Observe  ← the only moment a unit looks around
                    Bank               ← leftover AP becomes Reserve, AP zeroed
                    Advance
```

**A reaction window is the only thing that acts out of turn**, and there are exactly two ways one
opens:

- `Battle.Move` opens one on the committed route. Overwatch, surprise, and a trap somebody walked
  into all answer into it.
- `Battle.SpringAmbush` opens one deliberately, on a `CommittedMove` of zero length.

Either way: offers are built in the constructor, `Run()` = `PlaceRecommended()` + `Resolve()`,
and `Resolve` walks the subject along the timeline firing at each landing tick. An interface or
an AI plugs in by placing its own choices between those two calls instead of calling `Run`.

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
  in the scoring; a limit of the search, and the first thing a deeper one would fix. Note that it
  would still not stab anybody when it arrived — see entry 008 in `../decisions.md`.
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

## Open questions

Owned here. The design doc carries more, marked *Open* in the section they belong to; these are
the ones that block or shape what Core does next.

- **Nothing draws a soldier who knows about nobody.** A unit with no contact at or above
  `UtilityModel.ActsOn` scores every option at nothing and banks its turn, and a lost contact
  decays back to that state. Correct, and the reason a fight that loses contact is a stalemate.
  An objective system — ground to hold, a route to patrol, a place to reach — is what gives such
  a unit something to want, and it is the largest thing between this AI and one a player would
  call an enemy. Not a search-depth problem: a deeper search would still have nothing to search
  for.
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
- **Nothing may decline a reaction.** `ReactionOffer.Recommended` is not nullable, so a reactor
  always takes its best option even when every option scores below zero — which happens: a beam
  that will be soaked entirely is worth about what it costs, and the model correctly says all the
  answers are bad and then picks one anyway. Making it nullable is a handful of lines and a real
  behaviour change, so it wants doing deliberately rather than in passing.
- **`ShieldValue` is the dial to watch first.** At 0.15 a fully soaked eight point beam scores
  0.72 against a snap shot costing 0.75 — near enough break-even that the ordering between firing
  pointlessly and doing something else is decided by noise. Either the shield term is too generous
  or a point of reserve is too cheap, and only matches will say which.
- **Melee does not reach.** `../decisions.md` entry 008, addressed here and open: `PowerBlade`
  carries a 2.0 m range and `Gunnery` measures eye to centre of mass in three dimensions, so at
  the hex size settled in entry 007 two adjacent soldiers are further apart than a blade can
  cover. Nothing special-cases melee and something has to — either a reach measured along the
  ground, or an adjacency test, and which one is a design question rather than a number.
- **The overwatch awareness gate can now be re-examined.** Flagged in the doc and in
  `ReactionModel`, with the two dials named. It was gated on having an AI to run matches with;
  there is one, so this is the first thing to point a batch of headless matches at.
- **Every balance number is set by reasoning, not measurement.** Treat the figures as arguments
  rather than findings, and check the design doc for why one is what it is before changing it —
  several are load-bearing in ways their size does not advertise. This is now *testable* rather
  than merely true, which is the whole reason the AI came before grenades.

## Recent work

```bash
git log --oneline -20 -- src/Hexcom.Core tests
```
