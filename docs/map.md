# Hexcom — project map

The constitution for working on this repository across several Claude sessions at once. It says
who owns what, what may not change quietly, and where to find out what everybody else has done.

**Read this file and every sub-project doc. Write only your own.** A session is told which
territory it is working in; that grants it the paths listed under that territory and nothing
else. The one exception is `decisions.md`, which anybody may append to and nobody may edit.

---

## The territories

Six, but only three have docs. A doc is created when there is real work in the territory —
an empty one rots and, worse, looks maintained.

| Territory | Doc | Owns | State |
|---|---|---|---|
| **Core** | [subprojects/core.md](subprojects/core.md) | `src/Hexcom.Core/**` (except `Maps/DemoMaps.cs`), `tests/**`, `docs/design.html` | active — enemy AI is next |
| **View** | [subprojects/view.md](subprojects/view.md) | `game/**` | active — sandbox only |
| **Content** | [subprojects/content.md](subprojects/content.md) | `src/Hexcom.Core/Maps/DemoMaps.cs`, `content/**` when it exists | barely started; owns its own tooling |
| **Art & audio** | — this file | `assets/**` when it exists | not started, and gated on a spec that does not exist |
| **Setting & campaign** | — this file | `docs/setting.md` when it exists | not started; free to start any time |
| **Strategy layer** | — this file | undecided | not started; arguably a second game |

Note the carve-out: Core owns all of `src/Hexcom.Core` **except** `Maps/DemoMaps.cs`, which is
content wearing a `.cs` extension until there is a map format to put it in.

**View is two territories sharing one doc.** Presentation (drawing, cameras, input plumbing) and
interface (what the player is allowed to know, and how they ask) are different problems, and the
second one constrains the rules rather than consuming them. They share a doc because they share
a single file — `game/scripts/HexSandbox.cs` — so there is no path boundary to enforce yet.
Splitting that file is what earns interface its own doc.

### The two territories not yet given paths

**Art & audio** is last in the build order and should stay there, but its *contract* is
writeable today: the world already fixes stance heights, wall bands and six body faces, and every
one of those constrains a model before anyone makes one. See Frozen contracts below.

Audio is bundled with art for scheduling, not because it is decoration. Noise is a rule here —
`AwarenessTracker` hears through walls, `LoudnessOf` prices it off the ground, and a beam is
silent where a slug rifle is not. Whatever eventually makes a footstep sound has to agree with
numbers Core already owns.

**Setting & campaign** is the freest thing in the project. It needs nothing from anybody and
blocks nothing. Science fiction, Star Trek / Star Wars / Babylon 5 in register.

---

## Frozen contracts

Changing one of these is not a normal edit. It needs an entry in
[decisions.md](decisions.md) saying what changed and why, because somebody else's territory is
built on it.

**1. Core never references a game engine.** The oldest rule and the reason the rest works. If a
file under `src/` needs `using Godot;`, the design is wrong.

**2. One query surface.** What the view draws and what the AI reads are the same public API on
Core. From the design doc's build order: *if the AI needs information the interface cannot show,
the interface is wrong.* So a query added for one is available to the other by construction, and
neither gets a private back door.

**3. Information is asymmetric on purpose.** A unit's own exposure is reported exactly; an
enemy's alarm is reported coarsely. The view must not render a number Core deliberately blurred,
and Core must not blur a number about your own soldier.

**4. Balance numbers live in exactly seven homes.** `MovementCosts`, `AwarenessModel`,
`GunneryModel`, `ReactionModel`, `CostProfile`, `StanceProfile`, `OverwatchArc`, plus
`Loadout` / `WeaponProfile` / `FireMode` as content. A magic number in a method body is a bug.
Float epsilons are not balance numbers.

**5. One horizontal world unit is one metre.** `SightSolver` builds a `Vec3` from a
`HexLayout` position (X, Y) and a floor height (Z, metres) and takes distances across it, so the
layout's units *are* metres, necessarily. Rendering scale is a separate concern and must not be
fed into `Battle`. **This contract is currently violated** — see
[decisions.md](decisions.md), entry 002.

**6. The physical constants art must match.** Verified against the source, not remembered:

| | |
|---|---|
| Stance heights (eye / body) | standing 1.65 / 1.80 m · crouching 1.10 / 1.25 m · prone 0.35 / 0.45 m |
| Wall bands | low 1.0 m · railing 1.2 m · high 2.0 m · screen 2.0 m · solid 3.0 m |
| Body faces | six — front, two shoulders, two flanks, back |
| Hex size | **unpinned.** Tests use 1.0 (2 m across, 1.73 m between centres); nothing states the intended figure |

The last row is an open question, not a fact. It belongs to Content and it blocks the art spec.

---

## Where status actually lives

Nowhere in these files. Status written by hand is a lie the moment a session ends badly, and it
ends badly often enough to matter. Derive it:

```bash
git log --oneline -20
```

```bash
git branch -a
```

```bash
dotnet test
```

- **What has landed in a territory** — `git log --oneline -- <its paths>`
- **What is in flight** — branch names. A branch *is* the claim and merging *is* the release, so
  the claim cannot outlive the work.
- **Whether it works** — the test run, which is the only honest answer.

**Branch naming: `<territory>/<short-slug>`** — `core/utility-scoring`, `view/hud-rework`,
`content/map-format`. Master-session work on these docs goes on `master` directly.

---

## Rules of the scheme

1. **Read every doc, write one.** Plus `decisions.md`, which is everybody's.
2. **`decisions.md` is append-only.** Never edit or reorder an entry; supersede it with a new
   one. Append-only is the one file shape that survives several sessions writing on the same day.
3. **A finding outside your territory goes in `decisions.md`, not in the neighbour's code.**
   This is the pressure valve, and it is the whole point of the scheme. A view session *will*
   learn something about the rules. Write it down and let Core pick it up.
4. **Only Core republishes the artifact.** One URL, one publisher; see the design doc rules in
   `CLAUDE.md`. Other territories update their own doc and leave `design.html` alone.
5. **Concurrent sessions need separate worktrees.** These docs stop sessions colliding
   *semantically*. They do nothing about two sessions writing the same file in the same working
   tree — only a worktree or a branch does that.
6. **Say when it is a good moment to start a new session.** The rhythm in `CLAUDE.md` applies per
   territory: a territory is at a clean point when its own doc, its tests and its commits agree,
   and nothing decided in conversation is still only in the conversation.

---

## Master session

One session at a time acts as master: it owns `docs/map.md`, curates `docs/decisions.md`, and is
where the breakdown itself gets argued about. It does not own any code. If you are not the master
session, you may still append to `decisions.md` — that is what it is for.

Whether a master session is currently live is not recorded here, because that would be status.
