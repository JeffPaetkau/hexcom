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
purpose, balance numbers in their seven homes, and one horizontal unit is one metre.

---

## The job — the AI takes a turn (build order 04, second half)

Branch `core/turn-planner`. Read the rest of this file before starting; the turn loop below and
the gotchas after it are the things that will bite.

**What exists.** `Tactician` scores one action, in vitality, and `ReactionWindow` now ranks by it
instead of by a ladder. What does not exist is anything that generates candidates for an ordinary
turn. A hostile unit still does nothing whatever when its turn comes round; the sandbox drives
both sides by hand.

**The decision already taken, so do not retake it.** One scorer, two searches. `Tactician`
appraises a single action and knows nothing about where the candidates came from; what differs
between picking a reaction and taking a turn is which options get generated and how they chain,
not what any one of them is worth. So this job is a *search* over `Battle.Destinations`,
`PlanShot`, `SetOverwatch` and `Arm`, calling `Appraise` — not a second scoring model. If you find
yourself adding terms to `Appraisal`, ask first whether the reaction window would want them too;
if it would not, the split is being drawn in the wrong place.

**Two things the scorer is missing that a turn planner will feel immediately.**

1. **Firing gives you away, and nothing prices that.** `Battle.AnnounceFire` raises every enemy
   in earshot or facing your way; `Worth` counts none of it. In a stealth-first game that is the
   biggest single hole in the model — an AI scored this way blazes away and blows its own
   approach. The derivation is the inverse of `AppraiseWord`: for each enemy the shot would carry
   over the bar, subtract what they would then do about you. It needs a preview of `Hear` and
   `Reveal` in the way `WouldNotice` previews a look, which is the same shape and about as much
   work.
2. **Chaining.** Two actions in one turn are not worth the sum of their scores — moving somewhere
   changes what the shot from there is worth, and the reaction reserve is what is left at the end.
   `ReserveFraction` means the last unspent points are worth more than `PointValue` says, because
   they are what the unit answers the next move with.

**The hard constraint — contract 2 in [../map.md](../map.md).** The AI reads the same public
queries the interface shows. If the AI wants information the interface cannot show, that is a
finding about the interface, to be written up in `../decisions.md` — not a licence to reach into
internals for convenience. This held through the scorer and it is worth saying that it *paid*:
`Gunnery.Expect`, `AwarenessTracker.WouldNotice` and `Battle.PlanThreat` were all added because
the AI needed them, and every one of them is a figure a player should have been able to see and
could not.

**Out of scope.** `game/**`. Entry 004 in `../decisions.md` is a Core API gap the interface needs
and the AI does not; it is not this job. Entry 002 is an open sandbox bug; leave it alone.

**The test that it worked:** a hostile side, given nothing but `Battle` and a seed, plays a
skirmish to a decision without being told anything about the map. That is what unlocks the
headless AI-versus-AI runs the engine-free split was built for, and turns every balance number in
this game from an argument into a finding — starting with the overwatch awareness gate that
`ReactionModel` already names as first for re-examination.

After this: grenades and mines (build order 05).

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
  the stance cancelling itself out. `LoudnessOf` sums `link.ApCost`, deliberately.
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

---

## Open questions

Owned here. The design doc carries more, marked *Open* in the section they belong to; these are
the ones that block or shape what Core does next.

- **Firing gives you away and the scorer does not price it.** Named in the brief above because a
  turn planner hits it first, but it is a hole in the model as it stands: a soaked beam and a slug
  rifle that tells the whole compound are scored on what they do to the target and nothing else.
  The first of the two omissions that will make an AI play badly in a way anyone can see.
- **Nothing may decline a reaction.** `ReactionOffer.Recommended` is not nullable, so a reactor
  always takes its best option even when every option scores below zero — which happens: a beam
  that will be soaked entirely is worth about what it costs, and the model correctly says all the
  answers are bad and then picks one anyway. Making it nullable is a handful of lines and a real
  behaviour change, so it wants doing deliberately rather than in passing.
- **`ShieldValue` is the dial to watch first.** At 0.15 a fully soaked eight point beam scores
  0.72 against a snap shot costing 0.75 — near enough break-even that the ordering between firing
  pointlessly and doing something else is decided by noise. Either the shield term is too generous
  or a point of reserve is too cheap, and only matches will say which.
- **The overwatch awareness gate is the first thing to re-examine under real play.** Flagged in
  the doc and in `ReactionModel`, with the two dials named. It cannot be settled until there is
  an AI to run matches with, which is the argument for doing the AI first.
- **Every balance number is set by reasoning, not measurement.** Nothing has been played, because
  there is nobody to play against. Treat the figures as arguments rather than findings, and check
  the design doc for why one is what it is before changing it — several are load-bearing in ways
  their size does not advertise.
- **Whether the metres-per-hex figure was ever decided.** Tests use 1.0 throughout; nothing
  states it as intended, and the awareness distances read as though drawn against something
  larger. Raised in `../decisions.md` entry 002.

## Recent work

```bash
git log --oneline -20 -- src/Hexcom.Core tests
```
