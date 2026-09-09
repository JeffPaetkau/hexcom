# Hexcom — project map

The constitution for working on this repository across several Claude sessions at once. It says
who owns what, what may not change quietly, and where to find out what everybody else has done.

**Read this file and every sub-project doc. Write only your own.** A session is told which
territory it is working in; that grants it the paths listed under that territory and nothing
else. The one exception is `decisions.md`, which anybody may append to and nobody may edit.

---

## The territories

Seven, five with docs. A doc is created when there is a brief to put in it — an empty one rots
and, worse, looks maintained while doing it.

| Territory | Doc | Owns | Gated by |
|---|---|---|---|
| **Core** | [subprojects/core.md](subprojects/core.md) | `src/Hexcom.Core/**` (except `Maps/DemoMaps.cs`), `tests/**`, `docs/design.html` | nothing — it is the trunk |
| **View** | [subprojects/view.md](subprojects/view.md) | `game/**` | nothing — its current job reads `Tactics`, which has landed, and the hex figure it wanted is settled |
| **Content** | [subprojects/content.md](subprojects/content.md) | `src/Hexcom.Core/Maps/DemoMaps.cs`, `content/**` when it exists | nothing — Core's AI has landed, so balance work is unblocked too |
| **Setting & campaign** | [subprojects/setting.md](subprojects/setting.md) | `docs/setting.md` and `docs/setting/**` | nothing |
| **Art & audio** | — this file | `assets/**` when it exists | the setting's visual register, and an asset spec nobody has written. The hex figure it was waiting on is settled — see entry 007 |
| **Strategy layer** | — this file | undecided | the campaign shape, which belongs to Setting |
| **Master** | [subprojects/master.md](subprojects/master.md) | `CLAUDE.md`, `docs/map.md`, `docs/decisions.md`, and the doc *set* — each territory owns its own doc's contents | nothing — but it writes no code, ever |

**Each territory doc with work in it opens with a `## The job` section** — the current brief,
written so that a session can be pointed at that one file and need nothing else. When a job is
finished, the session that finished it replaces that section with the next one. A brief is a work
order, not a status line: it says what to do, not how far along somebody got.

Note the carve-out: Core owns all of `src/Hexcom.Core` **except** `Maps/DemoMaps.cs`, which is
content wearing a `.cs` extension until there is a map format to put it in.

**View is two territories sharing one doc.** Presentation (drawing, cameras, input plumbing) and
interface (what the player is allowed to know, and how they ask) are different problems, and the
second one constrains the rules rather than consuming them. They no longer share a file:
presentation is `game/scripts/BattleView.cs` and interface is `game/scripts/BattleHud.cs`,
separate classes rather than partials so that neither can reach into the other's state.

**They stay one territory anyway, and that is settled — see [decisions.md](decisions.md) entry
014.** An earlier version of this file said interface earns its own doc once it has a brief of
its own. That test was wrong. Having a brief is what earns a *doc*; having **paths** is what
earns a *territory*, and only the second was ever the question. The paths do not divide: the two
classes are 648 lines of `game/`, and the entry point, input handling, scenario setup, scale
contract and capture harness are 726 lines belonging to both and to neither. Two territories
sharing over half a directory is the ambiguity path ownership exists to remove.

The greybox (build order 06) rewrites `game/` substantially and is the moment to look again.

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

**4. Balance numbers live in exactly eight homes.** `MovementCosts`, `AwarenessModel`,
`GunneryModel`, `ReactionModel`, `CostProfile`, `StanceProfile`, `OverwatchArc`, `UtilityModel`,
plus `Loadout` / `WeaponProfile` / `FireMode` as content. A magic number in a method body is a
bug. Float epsilons are not balance numbers.

The eighth is newer than the rest and different in kind: the other seven say what the world does,
`UtilityModel` says what any of it is *worth to somebody deciding*. See
[decisions.md](decisions.md) entry 003.

**5. One horizontal world unit is one metre.** `SightSolver` builds a `Vec3` from a
`HexLayout` position (X, Y) and a floor height (Z, metres) and takes distances across it, so the
layout's units *are* metres, necessarily. Rendering scale is a separate concern and must not be
fed into `Battle`. The view keeps the two apart in `SandboxScale`, which owns both layouts and
hands out only the metres one — see [decisions.md](decisions.md), entries 002 and 005.

What 005 also establishes, because the obvious guess is wrong: breaking this contract does *not*
disturb sight or cover, which are scale-free by construction. It breaks everything priced in
metres — detection, noise, voice, weapon range. A violation therefore shows up as a stealth game
where nobody is ever detected, and not as a game where cover looks weak.

**6. The physical constants art must match.** Verified against the source, not remembered:

| | |
|---|---|
| Stance heights (eye / body) | standing 1.65 / 1.80 m · crouching 1.10 / 1.25 m · prone 0.35 / 0.45 m |
| Wall bands | low 1.0 m · railing 1.2 m · high 2.0 m · screen 2.0 m · solid 3.0 m |
| Body faces | six — front, two shoulders, two flanks, back |
| Hex size | `HexLayout(size: 1.0)` — 2.00 m corner to corner, 1.73 m flat to flat and between centres |

All six rows are now facts. The hex size was the one open question here and it was settled by
[decisions.md](decisions.md) entry 007: a hex is one soldier's standing space, because a soldier
occupies exactly one and walls sit on its edges. **The art spec is no longer gated.**

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
2. **`decisions.md` is append-only, with one exception: the `Status` field.** Never edit or
   reorder an entry's text; supersede it with a new one. But an entry's Status may be flipped in
   place, naming the entry that resolved it — otherwise the log grows, everything reads as open,
   and the one instrument for seeing what is outstanding stops working. Two branches that both
   appended will conflict on merge — that is expected, and the resolution is always to keep both
   hunks and renumber a collision. Nothing there is ever lost, because nothing but a Status is
   ever changed in place.
3. **A finding outside your territory goes in `decisions.md`, not in the neighbour's code.**
   This is the pressure valve, and it is the whole point of the scheme. A view session *will*
   learn something about the rules. Write it down and let Core pick it up.
4. **Only Core republishes the artifact.** One URL, one publisher; see the design doc rules in
   `CLAUDE.md`. Other territories update their own doc and leave `design.html` alone.
5. **A session that writes code works in a worktree** — standard, and set out in `CLAUDE.md`.
   These docs stop sessions colliding *semantically*; they do nothing about two sessions writing
   the same file in the same directory. Only a worktree does that. Master sessions editing this
   file stay on `master`.
6. **Mind your own worktree and no one else's**, and remove it once your branch is merged. Do not
   list, inspect, reference or reason about another territory's worktree or branch — refer to
   work by what it produced, never by who is producing it. Anything else is status about somebody
   else, stale before it is read. Master is the exception and worries about all of them.
7. **Say when it is a good moment to start a new session.** The rhythm in `CLAUDE.md` applies per
   territory: a territory is at a clean point when its own doc, its tests and its commits agree,
   and nothing decided in conversation is still only in the conversation.

---

## Master session

One session at a time acts as master: it keeps this file true, curates `docs/decisions.md`,
writes the briefs other territories are pointed at, and is where the breakdown itself gets argued
about. It writes no code, ever, and it works on `master` rather than in a worktree — which is
also what makes it the session that can merge branches.

Its own brief is [subprojects/master.md](subprojects/master.md), including how to derive status
without reading it out of a file. **Point a new session at that one file to pick the role up.**

If you are not the master session, you may still append to `decisions.md` — that is what it is
for, and routing those entries into briefs is most of what Master does with them.

Whether a master session is currently live is not recorded here, because that would be status.
