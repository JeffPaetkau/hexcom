# Hexcom — project summary

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
