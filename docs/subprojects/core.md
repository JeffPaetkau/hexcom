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

## The job — enemy AI (build order 04)

Branch `core/utility-scoring`. Read the rest of this file before starting; the turn loop below
and the gotchas after it are the things that will bite.

**The seam already exists.** `ReactionWindow` separates building offers from resolving them, and
`ReactionWindow.Best` is a deliberate stand-in — shoot if you can, else turn, else get low, else
call it in. Replacing that with utility scoring *is* the AI job, so start there rather than with
a full turn planner. It is bounded, it has an obvious test story, and the rest grows out of it.

**Settle these two before writing much, and record the answer in `<remarks>` or the design doc.**
They are the decisions most likely to get made implicitly and then be expensive:

1. Does one scorer serve both the reaction window and the ordinary turn, or are those different
   problems? Build order 04 implies one — same queries, same ranking — but that is an implication
   and not yet a decision.
2. What is a utility score denominated in? The game already has one currency, and inside a
   window cost is literally time. An abstract 0–1 score that does not talk to action points will
   not survive contact with `ReactionWindow.Resolve`.

**The hard constraint — contract 2 in [../map.md](../map.md).** The AI reads the same public
queries the interface shows. If the AI wants information the interface cannot show, that is a
finding about the interface, to be written up in `../decisions.md` — not a licence to reach into
internals for convenience. This is the constraint an AI implementation is most likely to breach,
and breaching it quietly is how the "one query surface" contract dies.

**Out of scope.** `game/**`. If the sandbox needs a way to hand a side to the AI, append it to
`../decisions.md` for View. Entry 002 there is an open sandbox bug; it does not affect headless
work, so leave it alone.

**Why it is first.** Every balance number in this game is an argument rather than a measurement,
because there is nobody to play against. The AI is what unlocks the headless AI-vs-AI runs the
engine-free split was built for, and turns those arguments into findings — starting with the
overwatch awareness gate that `ReactionModel` already names as first for re-examination.

**The test that it worked:** the ranking is *derived* from something — expected damage, exposure,
points spent — rather than enumerated. A slightly better hard-coded ladder satisfies the letter
of "replace the stand-in" and none of its point.

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

The reaction picking policy in `ReactionWindow.Best` is a **deliberate stand-in** — shoot if you
can, else turn, else get low, else call it in. Ranking a shot against a dive into cover is what
utility scoring is for; replacing it is the same job as building the AI.

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

---

## Open questions

Owned here. The design doc carries more, marked *Open* in the section they belong to; these are
the ones that block or shape what Core does next.

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
