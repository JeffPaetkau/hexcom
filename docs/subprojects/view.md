# View — presentation and interface

The Godot layer: drawing what Core answers, and taking input. Currently one flat 2D sandbox that
drives either side by hand, or hands the hostile side to the AI.

Read [../map.md](../map.md) first.

## Owns

```
game/**
```

## Must not touch

```
src/**      tests/**      docs/design.html
```

If the view needs a query Core does not expose, that is a Core change — and by contract 2 in
[../map.md](../map.md) it is one the AI gets too. Raise it in `../decisions.md` rather than
reaching into `src/`.

## Depends on

- **Core's public API**, which is the same surface the AI reads. No private back door for
  drawing.
- **Information asymmetry** (contract 3). Your own soldier's exposure is reported exactly,
  because that is information about yourself. An enemy's alarm is coarse on purpose. Do not
  render a number Core deliberately blurred, even when you can compute it.
- **One horizontal world unit is one metre** (contract 5). Held by `SandboxScale`, which builds
  the metres layout `Battle` is given and the pixels layout everything is drawn with. See
  `../decisions.md` entries 002 and 005.

---

## The job — a capture that can act

Branch `view/scripted-capture`. Read **Seeing it** below first; the job is to extend it.

A capture can now show a situation the *AI* made — `--ai` hands the hostile side to `Commander`
during the passes, and the picture that proved `view/interface-readouts` was one where the
Spotter had crawled along the roof and shot the scout twice. It still cannot show a situation a
*person* made: nothing in a capture moves one of ours, fires, or changes a stance, so every
readout that depends on the player having done something — the reaction line most of all — is
still checkable only with a hand on the keyboard.

Give the capture a small script. Flags in the shape the existing ones already have, applied in
order before `--pass` and the picture — something like `--move q,r[,layer]` for the active unit,
`--fire name`, `--stance prone`, `--face NE`, `--end` — is enough. The test of it: a single
pasted command that walks Orsini across the front of a sentry that is holding an arc and captures
the reaction line saying what the sentry did about it. Keep it deaf and reproducible, which is
the whole bargain the harness rests on, and keep `HexSandbox` the only thing that calls `Battle`
— the script is an argument list, not a second input system.

**Two other jobs are waiting on other territories, and whichever gate lifts first jumps the
queue.** Each has its readout already designed in the audit below; what is missing is the query.

- **Placing your own reactions**, when Core lands the seam asked for in entry 004 and answered in
  entry 022: an open `ReactionWindow` whose offers the HUD can list, appraise and let the player
  pick from before it resolves.
- **The attention cone at its true reach**, when content's larger map lands — entry 006, gated
  on 007's finding that the demo compound is too small for any honest range figure.

**Two things watched on `view/interface-readouts` are for Core and are written up in entry 023.**
Do not re-find them: a stance change is scored on what it spares and never on the shot it
costs, because postures carry no `Opens` and `Prospect` is nought against a contact already held
`Engaged`; and a hostile's own `Prospect` term is built from the one number contract 3 blurs,
which is fine for the AI and makes the orders readout an instrument rather than an entitlement.

**Since beliefs landed (entry 021) the AI hunts.** A hostile that has heard enough walks to where
it can see the marker, looks, and shoots next turn. A capture with `--ai` will show a soldier
arrive somewhere and stand there: that is a look, not a stall, and the seen line on its next
turn will say what it was walking towards.

**How to know it worked.** A capture, from one pasted command, in which one of ours has acted
and the reaction line reports what the other side did about it.

---

## The interface audit

*Done on `view/interface-audit`, and closed against on `view/interface-readouts`. Contract 2 says
the view and the AI read one query surface, and the build order's rule is sharper: **if the AI
needs information the interface cannot show, the interface is wrong**. This is that check, run
against `Tactician` — the scorer the AI ranks every action by.*

The tables below are organised by the four terms of an `Appraisal`, because that is how the AI
reasons and therefore what the interface has to be able to explain. Verdicts:

| | |
|---|---|
| **shown** | on screen, exactly, and the player can act on it |
| **coarse** | on screen as a rung rather than a number, deliberately, per contract 3 |
| **gap** | the AI weighs it, the player cannot see it, and nothing prevents fixing it |
| **blocked** | ditto, but something does — the blocker is named |

### Harm — what a shot achieves

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| whether the shot is possible at all | `ShotPlan.CanFire` / `Refusal` | shot line, with the reason | shown |
| chance to hit | `ShotPlan.HitChance` | shot line | shown |
| what it costs this soldier | `ShotPlan.ApCost` | shot line, with the list price when they differ | shown |
| how much survives the angle | `ShotPlan.GlancingFactor` | shot line | shown |
| which plates it can reach | `ShotPlan.Aspects` + `Protection` | shot line, share and stock per face | shown |
| vitality it actually takes off | `Gunnery.Expect().Vitality` | worth line | shown |
| plate worn through | `Expect().PlateStripped` | worth line | shown |
| shield soaked | `Expect().ShieldStripped` | worth line | shown |
| chance it puts them down | `Expect().DownChance` | worth line | shown |
| how much soldier is there to remove | `Target.Stats.Vitality` | map label, current over maximum | shown |
| distance, cover, exposure | `SightResult` | cursor line, in metres and per cent | shown |
| where in the weapon's range that falls | `WeaponProfile.OptimalRange` / `MaxRange` | cursor line names the band and the long-range factor; status line carries the bands | shown |
| the bonus for having the arc already held | `OverwatchArc.AimBonus` | reserve line | shown |

The four `Expect` rows were the audit's clearest single finding and were closed while it was
being written. Everything the shot line said was true and none of it was what the AI ranks by:
`ShotPlan.ExpectedDamage` is damage arriving at the plate, and a beam landing squarely on a full
shield reads well there and achieves nothing. The player was being shown the trap the core doc
calls the easiest mistake in the codebase, and being left to do the arithmetic that avoids it.

The maximum-vitality row looked cosmetic and was not. The scorer's removal bonus is priced
against the *maximum* — a kill shot on a soldier with seven points left scores a whole soldier of
twenty — so the first time the AI's orders were printed, a shot worth 22.5 sat beside a label
that said 7, and the arithmetic could not be checked from the screen.

### Spared — what a posture keeps off you

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| who this soldier is taking seriously | `Tactician.Known` | seen line — in view with distance, or believed at a marker with credence | shown |
| the worst one shot each could do to you | `PlanThreat` per threat and mode | seen line, worth, mode and hit chance | shown |
| how likely they are to shoot at all | `Awareness.ReadoutFor(them, you).State` | alarm line, as a rung — and since entry 021 the scorer reads the same rung | coarse, on both sides |
| the bar they act from | `Model.Threshold(UtilityModel.ActsOn)` | alarm line, named | shown |
| what a stance or a turn costs | `MovementCosts.ChangeStance` / `TurnInPlace` | posture line, for each of the three keys | shown |
| what the whole trade comes to | `Tactics.AppraisePosture` | posture line, score and every term | shown |

**The audit's real find was in this table.** `Tactician.Aimed` read how much the enemy had
detected you as a raw certainty, and contract 3 says that number is blurred to a rung on purpose.
So the appraisal of a posture could not be displayed without leaking it — and, worse the other
way round, the AI was reading a figure its own soldier had no way of knowing, which is the one
thing `Tactician`'s own doc comment promises it never does. Written up as entry 011 and resolved
by entry 021: the scorer now reads the rung the interface shows, a test pins that two certainties
on one rung score the same, and the posture line prints the whole appraisal.

It is worth keeping clear which of the two problems mattered. The display leak was small — you
would have to invert an aggregate to recover the number. The AI reading it was not small: it was
a soldier who knew exactly how spotted they were, in a game whose whole subject is not knowing.
The interface audit found it and Core did not, which is contract 2 paying for itself.

### Prospect — what an action sets up

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| how much attention a place has | `Awareness.AttentionOn(pose, node)` | cursor line, exactly | shown |
| how much is still left to learn about a contact | own `Detection` against `Threshold(Engaged)` | nowhere | gap — **and a question**, below |
| the shot a new facing would open | `Tactician.BestShot` from an untaken pose | posture lines — it is the *prospect* term, scaled by attention and by what is left to learn | shown |
| who would hear you call it in | `Awareness.Earshot` | nowhere — and there is no way to shout | gap, and a Core gap with it |
| how much survives being passed on | `AwarenessModel.RelayFraction` | nowhere | gap |

The attention row was worth closing on its own. The watch cone on the map answers this question
as a yes or a no; the model does not — a place is attended to fully, at the corner of the eye, or
barely, and the gap between the last two is the entire reason flanking works. The cone's *range*
is still a lie and is still blocked by entry 006; its *resolution* never was, and nobody had
noticed the two were separate problems.

The second row is left open on purpose. Your own soldier's certainty about an enemy is neither of
the two cases contract 3 names — it is not your exposure and it is not the enemy's alarm — and
nobody has said whether a player reads it exactly or as a rung. The seen line already applies it
as a filter (`Known` is contacts past `ActsOn`) without quoting it, and quotes the *credence* of
a marker, which is a different thing: how much a remembered position is trusted, not how sure the
soldier is that the enemy exists. Quoting the certainty is a design decision about entitlement,
not a formatting one, and it is raised in entry 023.

Shouting is the odd row. `Tactician.AppraiseWord` scores it, `ReactionAction.Shout` uses it in a
window, and there is no `Battle` action that lets anybody do it on their own turn — so the
interface cannot offer it and `Commander` cannot generate it. Entry 012.

### Spent — what it costs

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| what a move costs from here | `Reachable` / `CostTo` | tile labels and the cursor line | shown |
| what is left to react with | `Unit.Reserve`, `ReserveFraction`, `ReserveFloor` | reserve line, including what stopping now would bank | shown |
| what arc is being held | `Unit.Held`, `HeldArc` | reserve line and the wedge on the map | shown |
| a point of anything, in vitality | `UtilityModel` | nowhere | deliberate — see below |

`UtilityModel`'s dials are the only things in this audit that are *right* to withhold on grounds
other than contract 3. They are not facts about the world; they are what one side's judgement
happens to prefer, and showing a player the exchange rates their opponent scores by is showing
them the opponent's mind rather than the battlefield. The scores those dials produce are a
different matter and belong on screen, which is what the worth line does.

### The orders readout is the opponent's mind, and is shown anyway

The block at the bottom of the screen prints every turn `Commander` has taken since the player
last acted, one line per `Order`, with `Worth` and `Opens` each broken into their terms and the
`Score` beside them. That is exactly what entry 009 asked for and exactly what the paragraph
above says a shipped interface must not do. Both are right: the sandbox exists to check the AI,
an AI can only be checked by somebody who can see what it thought, and the readout is an
instrument in the same sense the seed on the command line is. `BattleHud.TurnLines` says so in
its remarks, and any interface built for a player rather than for a tester drops it.

One of its terms could not be shown to a player even in principle. A hostile's `Prospect` is
scaled by how much that hostile has already worked out about the soldier it is turning towards —
its own contact file, which is fine for the AI and is the number contract 3 blurs for us. Noted
in entry 023 so that nobody later mistakes the readout for a precedent.

### What is not in the scorer yet, and is missing from both

The audit named two omissions the turn planner would hit first. Both were also interface gaps,
and saying so was the point of the exercise:

- **Firing gives you away and nothing prices it for the player.** The scorer charges a shot for
  what it announces (`GivenAway`, shown inside the worth line's spared term), but there is no
  preview of *who* a shot would wake and by how much, so the player sees the price and not the
  bill. Still open — entry 012, item 2.
- **A move's noise was computed and thrown away.** No longer: `Battle.Loudness` is public and is
  the figure `Move` then charges, `AwarenessTracker.WouldHear` says who would hear it, and the
  cursor line prints both — the loudness and the names — for any route the active soldier could
  take. Closed by entry 021. Only the names are printed; the figures behind them are movements in
  the enemy's contact file, and `BattleHud.NoiseLine` says why that stays a rung.

---

## Two territories, one doc — and one territory, settled

Presentation and interface are different problems:

- **Presentation** is drawing, cameras, input plumbing, and eventually animation. It consumes
  Core. It lives in `BattleView.cs`.
- **Interface** is what the player is allowed to know and how they ask for it. It *constrains*
  Core — the design doc's build order puts it plainly: if the AI needs information the interface
  cannot show, the interface is wrong. Section 06 ("What it hands the interface") and section 07
  ("Asymmetric information, deliberately") are interface design as much as rules design. It lives
  in `BattleHud.cs`.

They shared this doc because they shared a single 705-line file. They no longer do:

| | |
|---|---|
| `HexSandbox.cs` | the Godot node — lifecycle, the demo scenario, input, handing turns to the AI, and assembling a frame |
| `SandboxScale.cs` | metres against pixels, and the only place that knows the difference |
| `SandboxGeometry.cs` | where things sit on the canvas — centroids, region polygons, hit tests |
| `SandboxFrame.cs` | one moment's answers, assembled once and read by both halves |
| `BattleView.cs` | **presentation** — ground, walls, links, path, beliefs, soldiers |
| `BattleHud.cs` | **interface** — turn order, the soldier's situation, the shot under the cursor, reactions, the AI's orders |
| `SandboxPalette.cs` | colours, shared because a side is one colour in both halves |
| `SandboxCapture.cs` | render some frames, write a PNG, quit |

`BattleView` and `BattleHud` are separate classes rather than partials of the node deliberately:
partials would have kept every private field reachable from both, which is a path boundary with
no boundary behind it. They each take a `SandboxFrame` and a `CanvasItem` and can reach nothing
else. Two sessions can now work one on each.

**Whether that boundary makes two territories was asked in entry 013 and answered in entry 014:
it does not, and the question is settled.** A territory is defined by paths, and the paths do not
divide — the entry point, the input handling, the scenario, the scale contract and the capture
harness are over half of `game/` and belong to both halves and to neither. One territory whose
brief happens to be interface work is an accurate description rather than a compromise. The
greybox (build order 06) rewrites `game/` substantially and is the moment to look again.

---

## Gotchas

- **Godot defines its own `Side` enum.** `game/` files need
  `using Side = Hexcom.Core.Units.Side;`.
- **The sandbox needs Godot 4.7 .NET edition**, not the plain build. If your Godot is a different
  4.x, change the `Godot.NET.Sdk` version in `game/Hexcom.Game.csproj` to match.
- **Nothing on this machine is called `godot`.** See **Seeing it**. A session that types the
  short name, gets *command not found* and concludes the engine is missing has been misled by a
  shell, not by the install.
- **`.uid` files are tracked, and Godot writes them for you.** Adding a script under
  `game/scripts/` leaves the tree dirty the first time anyone opens the project, because Godot
  generates a `.uid` beside each one. They belong in the repository — commit them with the script
  rather than wondering, later, whether the untracked files in your status are yours.
- **Build before you run.** Godot loads the assembly from `game/.godot/mono/temp/bin/Debug/`, and
  a scene launched before `dotnet build Hexcom.sln` fails with *"Cannot instantiate C# script"* —
  which reads like a broken scene file and is not one.
- **A picture is not proof of a rules change.** Sight and cover are scale-invariant (entry 005),
  so the opening frame is byte-identical before and after the world-scale fix. What changed was
  detection, which no still image shows. When a change is about distance, measure it; when it is
  about layout, capture it.
- **A picture is exactly the proof of a drawing change, and the render is deterministic.** The
  same build captures byte-identically across runs and across frame counts, so a refactor of
  drawing code can be held to *zero* changed pixels against the commit before it. The split that
  created these files was checked that way and it earned its keep immediately: the vision wedge
  came out of the move with `steps = 14` where the original had `18`, a coarser arc that nothing
  else would have caught — it is a translucent overlay whose silhouette nobody has memorised, the
  build was clean and all 259 tests passed. 546 pixels on one arc were the entire evidence.
  **Diff the capture against the previous commit whenever you move drawing code.** It cuts the
  other way too: the HUD rework on `view/interface-audit` changed 78,110 pixels in exactly two
  horizontal bands — rows 14–112 and 862–891, the two panels — and every row of map between them
  came out byte-identical. `view/interface-readouts` was held to the same test before it touched
  a map label: rows 14–143 and 862–891, nothing between. That is how a change to the interface
  half proves it left the presentation half alone.
- **The readouts are drawn over the map, not beside it.** All three HUD blocks sit on a panel for
  that reason, and anything added to them has to assume there is a tile-cost label underneath —
  because there is. The help line and the top row of the map were mutually illegible in every
  capture taken before the panels existed. The top block is the active soldier's situation and
  the bottom block is what happened while it was not your go; they are separate so that a busy
  enemy round does not push the situation down onto the roof.
- **The bottom block is *since you last acted*, not a log.** It is replaced whenever the enemy
  gets a go after something you did, so if two of yours are adjacent in the initiative order, the
  second one's pass leaves the block untouched — nothing hostile happened in between. Read it as
  "what they did about that", never as a history.
- **`Battle` does not stop when a side is gone.** The survivors keep taking turns, so anything
  that loops on the hostile side being up has to check `IsDecided` or it never returns.
  `HexSandbox.Settle` does.
- **Drawing scale and world scale are different variables and must stay that way.** `HexSize` is
  pixels and is exported; `SandboxScale.MetresPerHexSize` is metres and is a constant. That
  asymmetry is the contract, not an oversight.

---

## Seeing it

Godot 4.7.2 .NET is installed on this machine and the scene wiring runs — that is no longer an
open question. `winget install GodotEngine.GodotEngine.Mono` puts it under
`%LOCALAPPDATA%\Microsoft\WinGet\Packages`, adds that directory to the PATH, and **makes no
`godot` alias** — the only executables there are `Godot_v4.7.2-stable_mono_win64.exe` and its
`_console` twin (entries 017 and 019). So the commands below name the executable in full, and
they run as pasted from either `bash` or PowerShell. Use the `_console` one when scripting: it
keeps stdout on the terminal, which is where the capture reports where it wrote to.

```bash
dotnet build Hexcom.sln && Godot_v4.7.2-stable_mono_win64_console --path game
```

To capture the sandbox without anyone at the keyboard — which is how a session with no human
watching can check its own work:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot out.png
```

`--shot-after N` waits N frames first, default 4; the first frame is drawn before the font atlas
is resident and loses every label. **Not with `--headless`** — the headless driver does not
rasterise and the capture comes back blank. `--headless --quit-after 30` is still the cheapest
way to check that the scene loads and `_Ready` survives, which catches most wiring breaks.

**A capture is deaf, so anything it is to show has to be an argument.** The run ignores the mouse
and the keyboard on purpose — the window opens under whatever the pointer was already doing, and
a capture that read it would not reproduce. Three flags put back what that took away:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot out.png --hover 2,0 --pass 6 --ai
```

- `--hover q,r[,layer[,region]]` parks the cursor on a node, axial, the way the maps are
  authored. Everything cursor-driven — the path preview, the sight readout, the range band, the
  shot under the cursor and what it is worth — was invisible to every capture ever taken before
  this existed.
- `--pass N` hands the turn on N times before the picture. Whose turn it is decides most of the
  HUD, and the demo's first soldier carries a **power blade**, so no capture of the opening frame
  can show a rifle's readout. Without `--ai`, nobody acts during the passes — this reaches later
  soldiers, not later situations.
- `--ai` hands every hostile turn to `Commander` during the passes, so each pass is one of ours
  standing still while the other side does what it decides to. This is the first way a capture
  has had of showing a situation rather than a starting position, and it is what puts the orders
  readout in a picture. The command above is the one that proved this branch: by the sixth pass
  the Spotter has crawled along the roof, put an aimed shot into the scout at 95 % and gone prone,
  and the bottom block says so with every term. Interactively the same thing is `H`, and `A`
  gives one turn — anybody's — to the AI.

---

## Open questions

- **The greybox.** Build order puts a 3D blockout after the AI and after grenades — *only once
  the rules are settled*. The flat sandbox stays the working view until then.
- **Whether the demo scenario belongs in `game/`.** `HexSandbox.NewBattle` hard-codes five
  deployments. That is content wearing a view extension, the same way `DemoMaps.cs` is content
  wearing a `.cs` one, and it should probably move when there is a scenario format to move it to.
- **What the player's own soldiers did during the enemy's turn is invisible.** A hostile move
  opens a window in which our units react automatically, and the sandbox cannot report it:
  `Commander.TakeTurn` returns orders with their appraisals and not what carrying them out did,
  so the reaction line only ever describes a move a person made. Asked of Core in entry 022,
  alongside the seam for placing reactions by hand, since an interface that drives the enemy
  through `Commander` needs both to reach through it.

## Recent work

```bash
git log --oneline -20 -- game
```
