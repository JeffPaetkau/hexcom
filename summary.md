# Hexcom — project summary

## Where take 2 is (updated 2026-09-16, evening)

**The approach.** Take 2 builds the interface first, piece by piece, and pulls the rules in to
match it, because the interface is the user's only view into how things are going. V1 (below)
is reference only, not binding; check with the user when unsure. The v1 rules were reviewed on
2026-09-15 and the user confirmed **"that is where we are going"**: costed movement graph
(walk 5, rough 10, vault 15, climb and ladder 30, some tiles crossable but not standable),
per-soldier cost profiles, stances (crouch 1.6, prone 3.0, change 2), facing (turn in place 2),
a reaction reserve banked from unspent points, refusals with reasons, initiative rather than
side alternation. Recommended order: costed reach and paths, then stance, then facing.

**What exists.** [README.md](README.md) is the current description: build, test and run
commands, controls, and the capture flags. In short: a Godot 4.7.2 .NET project under `game/`,
built in code, and an engine-free rules library under `rules/Hexcom.Rules/` with xUnit tests
beside it. The library holds the procedural landscape (hills, roads, tracks, grass and dirt)
from one height function, the hex maths (**one metre centre to centre**, decided 2026-09-16:
the stride is the base and the corner distance is derived; a standing or crouching soldier takes
one hex), the unit (**100 AP**, doubled with the smaller hex so a paved road, a scout and a gunner
still land on distinct prices; **a turn stands for ten seconds**, `Units.TurnSeconds`, so every
price is a share of that and the animations are timed to it, then played at `Board.PlaybackSpeed`,
default 2), the movement price list
(`MovementCosts`: stride 5, paved 4, climb 10 and descent 3 per unit grade, banks over 0.7
refused, and a hex whose own ground is steeper than 0.7 is unstandable however level the step
onto it, `Movement.CanStand`, added 2026-09-16 when the user found the unit sidling along the
bluff's contour onto its cliff; twenty metres a turn at two metres a second, a fast walk, since
the default move is a walk and running will be a choice that buys distance with noise; **hurried
descents**, added 2026-09-16 at the user's design: a descent of grade 0.25 or more can be taken
at a run for 3 points less per unit grade instead of 3 more, with a fall chance per step of
`TripPerGrade` 0.1 times the grade compounding along the way (raise it to 1.0 to see falls
often when testing), a fall costing the rest of the turn, later also prone
and damage; the board shows hexes reachable only by hurrying in orange and the fall risk on
the card, clicking one accepts it, falls are rolled from `new Random(7)` in `Board` until the
rules own their dice), per-soldier
`CostProfile` multipliers, and Dijkstra reach over the implicit hex graph. The game has a
tactical camera; one unit in a cyan ring, a hover ring, a see-through dark grey disc on every
hex in reach (the same size as the cursor ring; the user replaced the reach outline with per-hex
marks on 2026-09-16 because one shape in different colours is more versatile: grey for
movement, orange for warning, red for danger, the last two reserved in `SciFi`; the marks are
painted by the terrain shader from a per-hex texture, `HexMarks`, after draped disc meshes let
the ground poke through them on banks), animated
paid-for moves along the cheapest path timed to the turn, and End Turn; a sci-fi HUD with a
unit card. The hex grid is never drawn in play (`--grid` for checking; it is faint, 0.25, so the
marks read through it). Committed on `master` on 2026-09-16 evening, not pushed since the
landscape commit.

**The game, in the user's words (2026-09-16): a tactics combat game in which stealth is an
important element, a servant of combat and the other objectives, not the main point.** V1's
"stealth-first" below is the old framing.

**Next, in the agreed order: stance (crouch 1.6, prone 3.0, change about 4 at the doubled
scale), then facing (turn in place about 4).** Two loose ends from the fall rule to pick up when
they fit: a fall should also put the soldier prone and hurt them (the user said "implement
later"), and falls are rolled from `new Random(7)` in `Board` until the rules own a seeded source
of chance; `--trip` forces every hurried step to fall for pictures. An open question to settle when stance arrives,
not before: whether a prone soldier occupies two hexes (a body is 1.8 m long on a 1 m hex; the
user leans that way) or one hex with the model overhanging. Two-hex occupancy touches every
query that asks who is in a hex, so it is a decision, not a default. Things a fresh session
should know: the natural landscape on seed 7 never refuses a step (the steepest ground beside a
road is a grade of 0.40), so a **bluff** was added south of the highway cutting on 2026-09-16
(`Terrain.Bluff`: a 3 m table, north face from x 126 to 174 at z 30, grade 0.15 at the west end
rising geometrically to 6 at the east, refused from about x 146 on) to have every slope from
ramp to cliff within one turn of the standard picture; the standard picture of priced reach is
the unit beside the highway cutting, `--unit 171,-66 --focus 148,20 --pitch 50 --zoom 40
--yaw 20`, with the bluff at the bottom of the frame (hex 171,-66 is also where the game starts
the unit, `World.Home`, with the camera over it); the picture of hurried descents is the unit on
the bluff table, `--unit 157,-33 --focus 136,34 --pitch 50 --zoom 30 --yaw 0 --hover 136,25.5`;
the rings drape onto the drawn mesh (`TerrainView.MeshHeight`), not the raw height function, so
they can be depth tested, while the hex marks are painted by the terrain shader and need no
draping.

**How the work is checked.** Every visual change gets a picture, not a claim: run the game with
`-- --shot out.png` plus camera, hover, move, sun or drag flags (see README), read the PNG, and
send the user the pictures. Scripted state checks print to the console (unit hex and AP, ground
under a probe point). `--heights` prints the ground along a line when a picture cannot explain
something. The user runs the game themselves on the left monitor and reports what they see.

**Conventions kept.** British spelling; doc comments say why; commit only when the user says
"commit", push when they say "push"; no branches unless asked. Godot's window opens fullscreen
on screen 0 (the left monitor); captures force a 1600 by 900 window.

---

A summary of the first approach to this project, written at the fresh start on 2026-09-14. All of
that work is preserved on the branch **`archive/v1-territories`** (also tagged **`v1-final`**) on
`origin` (https://github.com/JeffPaetkau/hexcom). Anything here can be checked against it:

```bash
git show v1-final:README.md
```

```bash
git checkout archive/v1-territories -- docs/design.html
```

---

## What the game is

Turn-based sci-fi squad tactics on a hex grid, desktop only. **Stealth-first: the fight is
decided by who saw whom first.** Action-point movement, individual initiative (not side
alternation), no aggro radius — every enemy that knows about you learned it through a channel
you can see and cut.

**Setting, in brief.**  General Sci-Fi: Star Trek / Star Wars / Babylon 5. Beams
and slugs both survive because each defeats what the other's protection cannot, so nobody wins a
frontal exchange and the game is about seeing first.

---

## Technical decisions (v1)

### Stack
- **C# / .NET 8** throughout. **Godot 4.7.2 .NET (mono)** for presentation only.
- **xUnit** tests.
- Solution `Hexcom.sln`: `src/Hexcom.Core` (rules), `tests/Hexcom.Core.Tests`,
  `content/Hexcom.Content` + tests (map/mission file parser), `game/Hexcom.Game.csproj` (Godot).
- Godot binary on this machine is `Godot_v4.7.2-stable_mono_win64_console` (WinGet
  `GodotEngine.GodotEngine.Mono`; there is no `godot` alias on PATH). Exporting needs the mono
  export templates (~1.2 GB).

### The one architectural rule
**The rules library never references a game engine.** Every rule — geometry, cover, movement,
sight, detection, initiative, damage, AI — lived in plain .NET; Godot only drew and read input.
This made the rules testable headless, let AI-vs-AI balance batches run with no window (a 3v3
match on a radius-16 map in ~2 s), and kept the engine choice reversible.

### Other contracts that held up
- **One query surface**: what the view draws and what the AI reads are the same public API. If the
  AI needs information the interface cannot show, the interface is wrong.
- **Asymmetric information on purpose**: your own side's knowledge is reported exactly; the
  enemy's alarm is reported coarsely. The view never renders a number the core blurred.
- **Balance numbers are never inline** — they live in config records (`MovementCosts`,
  `AwarenessModel`, `GunneryModel`, `ReactionModel`, `BlastModel`, `CostProfile`, `StanceProfile`,
  `OverwatchArc`, `UtilityModel`, plus `Loadout`/`WeaponProfile`/`FireMode`/`ThrownProfile` as
  content). Every number was set by reasoning; only a handful were ever measured.
- **One world unit = one metre.** Rendering scale kept separate. Breaking it silently breaks
  detection, noise and range (not sight/cover, which are scale-free).
- **Deterministic**: one seeded RNG, so a battle replays exactly from seed + command list.

### Physical constants (art must match)
| | |
|---|---|
| Stance heights (eye / body) | standing 1.65/1.80 m · crouching 1.10/1.25 m · prone 0.35/0.45 m |
| Wall bands | low 1.0 · railing 1.2 · high 2.0 · screen 2.0 · solid 3.0 m |
| Body faces | six — front, two shoulders, two flanks, back |
| Hex | `HexLayout(size: 1.0)` — 2.00 m corner to corner, 1.73 m between centres; one soldier per hex |

### Systems that were built
- **Hex geometry**: axial coords, flat-top layout; a global **corner graph** so walls live on
  shared corners, not per tile.
- **Cover as chords**: a wall joins any two corners of a hex (15 segments per hex). Chords cut a
  hex into regions; regions under 60% of a hex are crossable but not standable.
- **Movement graph**: typed, priced links (walk, vault, climb, ladder, drop, stairs, door, crawl);
  50 AP a turn, 5 per stride; crouch and crawl cost more. Dijkstra returns the reachable set.
- **Sight and cover are one trace**: wall tops project onto the target as a waterline; cover is
  how much silhouette is below it. Stance, elevation and range fall out of the geometry.
- **Turn loop**: queue over a battle clock; initiative = rating + d10 − kit weight.
- **Awareness**: per-enemy belief states; detection accumulates by looking (on their turn),
  hearing (immediate, gives a place), or being told (radio reaches the side, shouting is local).
  Facing and vision cones (120° full, 200° peripheral) make positions flankable.
- **Combat**: beam vs kinetic; shields vs ablative plate, tracked **per body face**; the body is a
  hexagon so a shot finds plates by angle-based shares; glancing slugs; firing gives you away via
  your weapon's channel; melee is adjacency on the movement graph.
- **Reactions**: overwatch, surprise and ambush windows, with anti-cascade rules.
- **Grenades and mines** (a second trace for blasts).
- **AI (`Commander`/`Tactician`)**: a utility scorer measured in vitality; greedy search with one
  step of lookahead; hunts from last-known markers rather than true positions (no cheating);
  objectives, "not being seen" priced, briefings.
- **Missions**: objectives, a clock, three endings. Maps as `.hexmap` text, missions as
  `.hexmission` text (waystation, kestrel, compound).
- **Godot sandbox**: 3D greybox, fog of your side's knowledge, HUD readouts, camera, headless
  capture harness (`--shot out.png --hover q,r --pass N --ai --omniscient --aside`), and a
  one-file Windows export.

### Known gaps when v1 stopped
No patrols or standing intent; a one-step-deep search that cannot plan routes around a sentry;
the commander cannot weigh cutting its losses; three of six mission shapes unbuilt; no saves,
strategy layer, art, audio or suppression; most balance numbers unmeasured. Headless batches
showed the waystation recon was never won briefed and won ~15% blind.

### Build and test gotchas
- `dotnet test -v q` hides assertion messages; use `--logger "console;verbosity=detailed"`.
- A long-running `HEXCOM_BATCH=1` testhost locks the test DLLs, so no other build/test in that
  directory works until it exits (`taskkill //IM testhost.exe //F` to abandon one).
- Build before launching Godot — it loads the C# assembly from `game/.godot/mono/temp/bin/`.
  Export needs `dotnet/project/solution_directory` set in `project.godot`, or it silently ships an
  exe with no assemblies.
- Bash heredocs in this environment break on apostrophes; use Write/Edit for prose files.
- Inside a worktree the Bash tool refuses `cd`, `-C` and shell variables in compound commands.

---

## How v1 was worked on (and what it cost)

- **Territories with path ownership**: Core (rules + tests + design doc), View (Godot), Content
  (maps/missions), Setting (fiction), Interface (genre research and briefs, no code), and a
  **Master** session that wrote no code and kept `docs/map.md`, an append-only
  `docs/decisions.md` (~100 entries), and the briefs.
- Each coding session worked in its own **git worktree** on a `<territory>/<slug>` branch, and
  Master merged in the main directory.
- Docs were heavy: README ~780 lines, design doc ~2,500, decisions log ~6,200, View's doc ~2,000.
  **The docs became the most expensive thing to read**, and long Master contexts were most of the
  token spend (see below).
- Design doc was published as an Artifact:
  https://claude.ai/code/artifact/f7a71d6e-e493-43d7-88f7-bd569d06e201 (source
  `docs/design.html` on the archive branch).
- A research layer of per-game interface reference files (XCOM 2, Invisible Inc., Shadow
  Tactics, Phoenix Point, Mutant Year Zero, Into the Breach, …) lives under `docs/interface/`. The raw
  screenshots and capture notes behind them are committed under `reference-inbox/` on the archive
  branch (after the `v1-final` tag).
- User preferences carried forward: **Windows a session opens go on the left monitor** (the user
  works on the centre one of three); British spelling in prose; test names as sentences about
  behaviour; doc comments explain why; **push back on doubtful ideas with reasoning** before
  doing them.

---

## Checking and managing account token usage

This project shares Jeff's **Claude Max 5x** weekly limit with their own work.

### Reading the meter
A private endpoint republishes the account's usage every 15 minutes. The URL and token are in
`.claude/settings.local.json` under `env` (`HEXCOM_USAGE_URL`, `HEXCOM_USAGE_TOKEN`). That file is
per-machine and gitignored — **never commit the token or paste it into a tracked file.** Command:

```bash
curl -sS -m 20 -H "Authorization: Bearer $HEXCOM_USAGE_TOKEN" "$HEXCOM_USAGE_URL"
```

It reports the current 5-hour session %, the week on all models, the week on Fable (each with
reset time), and a local breakdown (request count, sessions, share of usage above 150k context).

- **The percentages and reset times are authoritative** and include all devices and claude.ai.
- **The breakdown is local to this machine only and approximate.** Never subtract it from the
  headline to guess what the user spent elsewhere.
- Ask the feed rather than trusting a remembered figure.

Reading at the fresh start (2026-09-14 18:00 Vancouver): session 20%, week (all models) 84%, week
(Fable) 85%, both resetting **Tuesday 15 Sep, 3 PM**; 82% of local usage above 150k context.

### The budget rule
- **The week resets Tuesday 3 PM (America/Vancouver).**
- The ceiling is the whole meter; the constraint is **a floor at a moment**: leave enough for the
  user's own workdays before the reset — about **20% remaining on Monday morning** (i.e. 80% used
  or less). The old "stop at 50%" rule was a misreading and is dead.
- **Weekends are the project's window; the workweek is the user's.**
- The all-models meter carries the floor. The Fable meter constrains only Fable work. Check both.

### What was learned about cost
- **Long contexts are what costs.** 82–93% of usage ran above 150k context, almost entirely from
  one long-lived coordinating session. Short fresh sessions are far cheaper per unit of work.
- Measured: ~20 increments in two days cost 48% of a week (~2.4% each, dominated by long Fable
  sessions); ten short parallel Sonnet research jobs cost about 1% of the week together.
- **Budget by measuring one job, not estimating ten**: read the meter, run one session, read it
  again.
- Restart sessions rather than continuing them past a few jobs; use Opus for routine work and
  Fable only where the judgement is worth it; never restart to change model a turn from done.
- Keep docs short enough that a fresh session does not burn its budget reading them.
