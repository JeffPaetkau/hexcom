# Hexcom — working notes

Turn-based sci-fi squad tactics on a hex grid. Stealth-first: the fight is decided by who saw
whom first.

## The one rule

`src/Hexcom.Core` is plain .NET and **never references a game engine**. Every rule lives there;
Godot only draws and reads input. If a file under `src/` needs `using Godot;`, the design is
wrong. This is what makes the rules testable headless and the engine choice reversible.

## Commands

```bash
dotnet test                 # 221 tests, ~0.7s
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
- **Balance numbers are never inline.** They live in `MovementCosts`, `AwarenessModel`, and the
  threshold properties on `SightSolver`. If a magic number appears in a method, it belongs in a
  config record.
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
- `dotnet test -v q` hides assertion messages. Use
  `--logger "console;verbosity=detailed"` and grep for `Error Message`.
- Bash heredocs in this environment break on apostrophes in the body. Use the Write/Edit tools
  for prose-heavy files rather than `cat <<EOF`.

## Working rhythm

Each increment: build the rules with tests → wire enough of the sandbox to see it → update
`README.md` and `docs/design.html` → republish the artifact → commit and push.

Keeping the doc current is not bookkeeping. It is what lets a fresh session pick the project up
from `CLAUDE.md`, the README, the design doc and `git log` without needing the conversation.
