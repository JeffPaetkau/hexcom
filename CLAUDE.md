# Hexcom — working notes

Turn-based sci-fi squad tactics on a hex grid. Stealth-first: the fight is decided by who saw
whom first.

## The one rule

`src/Hexcom.Core` is plain .NET and **never references a game engine**. Every rule lives there;
Godot only draws and reads input. If a file under `src/` needs `using Godot;`, the design is
wrong. This is what makes the rules testable headless and the engine choice reversible.

## Commands

```bash
dotnet test                 # 259 tests, ~1s
dotnet build Hexcom.sln     # includes the Godot project, which typechecks against Godot 4.7.2
```

The sandbox needs Godot 4.7 **.NET edition**; open `game/project.godot`, press F5. Godot is not
installed on this machine, so the scene wiring has never been verified — only the C#.

## Where things live

| | |
|---|---|
| `src/Hexcom.Core/` | all rules: Hexes, Geometry, Maps, Movement, Vision, Units, Battles, Awareness, Combat, Reactions |
| `tests/Hexcom.Core.Tests/` | xUnit |
| `game/` | Godot view layer, one script: `HexSandbox.cs` |
| `docs/design.html` | **the design source of truth** — decisions, rationale, open questions |

The design doc is published as an Artifact at
https://claude.ai/code/artifact/f7a71d6e-e493-43d7-88f7-bd569d06e201 and is republished from
`docs/design.html` after each increment. Read it before proposing design changes; it records why
things are the way they are, and which questions are still open.

**Republishing it from a session that did not publish it** — which is every new session — needs
that URL passed explicitly as the Artifact tool's `url` argument, and the artifact read once
first. Publishing without it silently creates a second, competing copy instead of updating this
one.

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

**A reaction window is the only thing that acts out of turn**, and there are exactly two ways
one opens:

- `Battle.Move` opens one on the committed route. Overwatch, surprise, and a trap somebody
  walked into all answer into it.
- `Battle.SpringAmbush` opens one deliberately, on a `CommittedMove` of zero length.

Either way: offers are built in the constructor, `Run()` = `PlaceRecommended()` + `Resolve()`,
and `Resolve` walks the subject along the timeline firing at each landing tick. An interface or
an AI plugs in by placing its own choices between those two calls instead of calling `Run`.

The reaction picking policy in `ReactionWindow.Best` is a **deliberate stand-in** — shoot if you
can, else turn, else get low, else call it in. Ranking a shot against a dive into cover is what
utility scoring is for; replacing it is the same job as building the AI.

## Conventions actually in use

- **Test names are sentences about behaviour**, not method names:
  `GoingProneBehindSandbagsTakesYouOutOfSightAltogether`. Tests read as situations — who is
  where, doing what, and what the other side made of it.
- **Doc comments explain why, not what.** `<summary>` says what it is; `<remarks>` carries the
  design rationale, including what was considered and rejected.
- **British spelling in prose and comments** (colour, metres, behaviour, centre). Identifiers
  follow .NET conventions, so `Color` and `Center` stay American where they name framework or
  Godot concepts.
- Records for values and config, classes for entities. Config types expose `init` properties with
  sensible defaults and a `Default` static.
- **Balance numbers are never inline.** If a magic number appears in a method, it belongs in a
  config record. The homes, and there are no others:

  | | |
  |---|---|
  | `MovementCosts` | action prices and the height thresholds that pick a traversal |
  | `AwarenessModel` | detection rates, arc widths, thresholds, how far word travels |
  | `GunneryModel` | hit chance, cover penalties, glancing, called shots |
  | `ReactionModel` | what banks, what springs a reaction, what each kind costs |
  | `CostProfile` | what one soldier pays against the price list — per unit |
  | `StanceProfile` | heights, concealment, noise and movement per stance |
  | `OverwatchArc` | arc widths and their aiming bonuses |
  | `Loadout` / `WeaponProfile` / `FireMode` | kit, as content |

  Float epsilons are not balance numbers: `Geometry2D.Epsilon` and `AngleEpsilonDegrees`.
- Entity state that only the battle may change uses `internal set` (see `Unit`). Tests go
  through the public API deliberately — this has already caught a bad test.

## Gotchas

- **Godot defines its own `Side` enum.** `game/` files need
  `using Side = Hexcom.Core.Units.Side;`.
- **Geometry needs epsilons at boundaries.** Two bugs so far came from exact-equality cases:
  a silhouette exactly as tall as the wall hiding it produced `0.9999999999999999`, and a
  parapet 3.5 m overhead was vaultable because the wall profile decided the traversal before the
  height was checked. Suspect float boundaries first when a geometric test fails oddly.
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
  chooses the moment still be armed on its own turn. `Unit.Held` is whichever one is set.
  An ambush window is a `CommittedMove` of *zero* length — same timeline, one instant.
- **Arc edges are exclusive, on purpose.** Hex bearings are exact multiples of 60°, so a place
  sitting precisely on the edge of a 120° arc is the common case. Comparisons add
  `Geometry2D.AngleEpsilonDegrees` so the edge falls to the *wider* arc deterministically — one
  spoke over is the corner of the eye, not full attention. Two tests pin this; don't "fix" them.
- `dotnet test -v q` hides assertion messages. Use
  `--logger "console;verbosity=detailed"` and grep for `Error Message`.
- Bash heredocs in this environment break on apostrophes in the body. Use the Write/Edit tools
  for prose-heavy files rather than `cat <<EOF`.

## Where it stands

Sections 01–10 of the design doc are built. Next on the build order is **enemy AI**, then
grenades and mines, then the Godot greybox.

**Every balance number in the game is set by reasoning, not by play.** Nothing has been measured,
because there is nobody to play against yet — the sandbox drives both sides by hand. So treat the
figures as arguments rather than findings, and when one looks wrong, check the doc for why it is
what it is before changing it; several are load-bearing in ways their size does not advertise.
The overwatch awareness gate is flagged in the doc and in `ReactionModel` as the first thing to
re-examine under real play, with the two dials named.

AI is what turns those arguments into measurements: it is also what unlocks the headless
AI-vs-AI balance runs the whole engine-free split was for.

## Working rhythm

Each increment: build the rules with tests → wire enough of the sandbox to see it → update
`README.md` and `docs/design.html` → republish the artifact → commit and push.

Keeping the doc current is not bookkeeping. It is what lets a fresh session pick the project up
from `CLAUDE.md`, the README, the design doc and `git log` without needing the conversation.

### Say when it is a good moment to start a new session

**At the end of each increment, tell the user that this is a clean point to start a new session
if it is.** One line, no preamble, then stop — it is a note, not a ritual, and it should not turn
into a nag or a sales pitch for ending the conversation.

A point is clean when all of these hold:

- `dotnet test` green and `dotnet build Hexcom.sln` succeeds
- `README.md` and `docs/design.html` describe what now exists, not what used to
- the artifact is republished
- the work is committed and pushed
- **nothing decided in conversation is still only in the conversation**

The last one is the whole reason the rhythm exists and the only one that is easy to get wrong.
A number argued down from one value to another, an alternative considered and rejected, a bug
found and the reasoning that found it — if it shaped the code, it belongs in a `<remarks>` block
or the design doc before the session ends. A fresh session inherits the files and `git log`. It
inherits none of the argument.

Mid-increment is **not** a clean point however tidy the tree looks: a half-built system with
green tests is exactly the state the docs cannot describe. Neither is a point where a design
question has been raised and not yet answered or recorded as Open.
