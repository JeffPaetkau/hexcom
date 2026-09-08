# Hexcom — working notes

Turn-based sci-fi squad tactics on a hex grid. Stealth-first: the fight is decided by who saw
whom first.

## Start here

The project is worked on by several sessions at once, split into territories with path-based
ownership. **Read [docs/map.md](docs/map.md) before touching anything** — it says who owns what,
which contracts may not change quietly, and how to find out what everyone else has done.

Then read the doc for the territory you have been told you are working in:

| | |
|---|---|
| [docs/subprojects/core.md](docs/subprojects/core.md) | the rules and the AI — `src/Hexcom.Core`, `tests/` |
| [docs/subprojects/view.md](docs/subprojects/view.md) | Godot presentation and interface — `game/` |
| [docs/subprojects/content.md](docs/subprojects/content.md) | maps, kit, and the tools to author them |

**Read all of them, write only yours.** The one exception is
[docs/decisions.md](docs/decisions.md), which any session may append to and none may edit — that
is where a finding about somebody else's territory goes instead of into their code.

If you have not been told which territory you are in, ask before editing.

## Work in a worktree

**Any session that is going to write code starts a worktree, first thing.** Use `EnterWorktree`
and name it for the branch you are about to work on — `core/utility-scoring`, `view/hud-rework`.
Territory docs and `docs/decisions.md` prevent sessions colliding *semantically*; only a worktree
stops two of them writing the same file in the same directory.

Sessions that are only reading, or that are editing `docs/map.md` and `docs/decisions.md` as the
master session, stay on `master` in the main directory. A worktree for a doc edit is friction
with nothing to show for it.

Three things about how it behaves here:

- **It branches from `origin/master`, not your local HEAD.** So push `master` before starting a
  worktree, or the new one will not contain your last commit.
- **Merging happens in the main working directory.** A branch can only be checked out in one
  worktree at a time, which is precisely what makes "one territory, one branch" true rather than
  merely agreed — but it also means the worktree holding `core/x` cannot be the one that merges
  it into `master`.
- **Each worktree builds from scratch.** `bin/` and `obj/` are per-directory, so the first
  `dotnet test` in a new worktree is slow and the rest are normal. Packages come from the global
  cache, so nothing is re-downloaded.

**Cleaning up.** Finish the increment as usual — tests green, docs updated, committed — then push
the branch and say it is ready to merge. **Do not remove a worktree yourself.** Removing one with
commits that are not on `master` throws work away, so exiting and removing is the user's call:
offer it once the branch is merged, and leave it alone otherwise.

## The one rule

`src/Hexcom.Core` is plain .NET and **never references a game engine**. Every rule lives there;
Godot only draws and reads input. If a file under `src/` needs `using Godot;`, the design is
wrong. This is what makes the rules testable headless and the engine choice reversible.

## Commands

```bash
dotnet test                 # 289 tests, ~6s (the AI search is most of it)
dotnet build Hexcom.sln     # includes the Godot project, which typechecks against Godot 4.7.2
```

The sandbox needs Godot 4.7 **.NET edition**; open `game/project.godot`, press F5. Godot is not
installed on this machine, so the scene wiring has never been verified — only the C#.

## Where things live

| | |
|---|---|
| `src/Hexcom.Core/` | all rules: Hexes, Geometry, Maps, Movement, Vision, Units, Battles, Awareness, Combat, Reactions, Tactics |
| `tests/Hexcom.Core.Tests/` | xUnit |
| `game/` | Godot view layer, one script: `HexSandbox.cs` |
| `docs/map.md` | territories, ownership, frozen contracts |
| `docs/decisions.md` | append-only log of cross-boundary decisions and findings |
| `docs/subprojects/` | one doc per active territory |
| `docs/design.html` | **the design source of truth** — decisions, rationale, open questions |

The design doc is published as an Artifact at
https://claude.ai/code/artifact/f7a71d6e-e493-43d7-88f7-bd569d06e201 and is republished from
`docs/design.html` after each increment. Read it before proposing design changes; it records why
things are the way they are, and which questions are still open.

**Only the core territory republishes it.** One URL and several sessions is a conflict waiting to
happen.

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
  | `UtilityModel` | what an action is worth — the exchange rates the AI ranks by |

  Float epsilons are not balance numbers: `Geometry2D.Epsilon` and `AngleEpsilonDegrees`.
- Entity state that only the battle may change uses `internal set` (see `Unit`). Tests go
  through the public API deliberately — this has already caught a bad test.
- **Branch naming is `<territory>/<slug>`** — `core/utility-scoring`, `view/hud-rework`. A branch
  is how another session sees that work is in flight, so the name is not cosmetic.

## Gotchas

Territory-specific ones live in the territory docs — the turn loop, the two AP pockets, the
epsilon boundaries and the reaction timeline are all in
[docs/subprojects/core.md](docs/subprojects/core.md); Godot's `Side` collision and the scale
problem are in [docs/subprojects/view.md](docs/subprojects/view.md). These two are everyone's:

- `dotnet test -v q` hides assertion messages. Use
  `--logger "console;verbosity=detailed"` and grep for `Error Message`.
- Bash heredocs in this environment break on apostrophes in the body. Use the Write/Edit tools
  for prose-heavy files rather than `cat <<EOF`.

## Where it stands

Sections 01–11 of the design doc are built. Next on the build order is **going to look** — an AI
that acts on a remembered position and not only on what it can currently see — then grenades and
mines, then the Godot greybox.

**Every balance number in the game is set by reasoning, not by play.** Nothing has been measured,
because there is nobody to play against yet — the sandbox drives both sides by hand. So treat the
figures as arguments rather than findings, and when one looks wrong, check the doc for why it is
what it is before changing it; several are load-bearing in ways their size does not advertise.

Do not record status in any of these files. It is derived — `git log`, `git branch -a`,
`dotnet test`. A status line written by hand outlives the session that wrote it and then lies to
the next one.

## Working rhythm

Each increment: build the rules with tests → wire enough of the sandbox to see it → update
`README.md`, your territory doc and `docs/design.html` → republish the artifact → commit and push.

Keeping the docs current is not bookkeeping. It is what lets a fresh session pick the project up
from `CLAUDE.md`, `docs/map.md`, the territory docs and `git log` without needing the
conversation.

### Say when it is a good moment to start a new session

**At the end of each increment, tell the user that this is a clean point to start a new session
if it is.** One line, no preamble, then stop — it is a note, not a ritual, and it should not turn
into a nag or a sales pitch for ending the conversation.

A point is clean when all of these hold:

- `dotnet test` green and `dotnet build Hexcom.sln` succeeds
- `README.md`, your territory doc and `docs/design.html` describe what now exists, not what used
  to
- the artifact is republished, if you are the core territory
- the work is committed and pushed
- **nothing decided in conversation is still only in the conversation**

The last one is the whole reason the rhythm exists and the only one that is easy to get wrong.
A number argued down from one value to another, an alternative considered and rejected, a bug
found and the reasoning that found it — if it shaped the code, it belongs in a `<remarks>` block,
the design doc, or `docs/decisions.md` before the session ends. A fresh session inherits the
files and `git log`. It inherits none of the argument.

Mid-increment is **not** a clean point however tidy the tree looks: a half-built system with
green tests is exactly the state the docs cannot describe. Neither is a point where a design
question has been raised and not yet answered or recorded as Open.
