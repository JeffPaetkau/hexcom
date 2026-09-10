# View — presentation and interface

The Godot layer: drawing what Core answers, and taking input. Currently the greybox — a 3D
blockout of the battle with no art in it — which opens as the game a person plays, drives either
side by hand, or hands the hostile side to the AI.

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
  the one layout `Battle` is given and owns the mapping from the rules' plane into the scene;
  the camera moves itself and cannot reach it. See `../decisions.md` entries 002 and 005.

---

## The job — the first play-through's findings, built

Branch `view/playable`. **This is the brief for a fresh session**, and it is written so that this
file, `../map.md`, and entries 049, 053 and 057 are the whole of what it reads before it starts.

**What it is.** The first person has played the greybox — the user, against `Commander`, from
`build/Hexcom.exe` — and entry 057 is what they said. Six things, all of them interface, none of
them a rule, and the user's instruction with them: *make what we have playable*. This job builds
the six. A territory for interface research now exists (`subprojects/interface.md`) and will
write later briefs against what the genre does; **do not wait for it** — these six are concrete
and the person who asked for them is the person who will test them.

1. **The instruments go in a second window.** The legend and the tester's readouts — the orders
   block, the mode line, whatever else a player of a shipped game would never see — move to a
   separate `Window` the user can drag to another monitor. What stays in the main view is the
   player's HUD: mission, turn order, the soldier's situation, the cursor, the shot and its worth,
   reactions. **The test for which side of the line a readout is on**: would a player who never
   presses `O` want it. Captures still take the main viewport; decide whether `--shot` also
   captures the second window, or a flag does, and say so in **Seeing it**.
2. **The camera turns smoothly, not sixty degrees at a time.** Entry 053 chose snapping so arcs
   stay legible from a bearing; the user has overruled it and the arcs will have to stay legible
   anyway. `Q`/`E` animate to the next bearing rather than jumping, and the mouse turns freely.
   **Nothing animates in a capture**: `--yaw N` lands on the frame it names, and a run with
   `--shot` on it settles every animation before the picture, or the harness stops being
   deterministic and entry 053's fifth decision is undone.
3. **The mouse drives the camera as well as the keyboard.** Wheel zoom exists; add drag-to-orbit,
   drag-to-pan, and edge-pan. Right-click currently fires, so orbit is not a plain right-drag —
   settle the gesture set first, against what `conventions.md` will eventually say, and write
   the table in **Seeing it** beside the keys.
4. **It opens as the mission against the AI.** Today the keys open with both sides by hand and
   the user has to press `H` and `K` first. The default is the user playing the waystation
   mission against `Commander` with windows handed out and the other side hidden until found.
   Every other mode stays — AI against AI, both sides by hand, omniscient — behind the keys and
   the script settings, because the harness and the balance runs need them. **Every capture
   command in this file assumed the old defaults**; re-run them and re-pin the scene.
5. **Our units do not read against the terrain.** Contrast, first — a hue the ground never uses,
   an outline or a ground ring at a weight that survives the ghosted-storey tint, and a check
   at `--fit` distance as well as close in. The figures-not-names rule (entry 049) is about
   walls and ground and does not stop a soldier having a colour of its own.
6. **A move walks the route.** Not instant, not slow: the soldier moves along the path the
   rules already hand back, at a pace that reads as a walk at the default zoom. Entry 040 says
   the mover has not stepped until the window resolves, so the walk is the *resolution* drawn
   over time — draw the ticks the reaction line quotes as the soldier passes them. **Off for
   captures and headless runs**, by the same settle-before-shot rule as item 2, and a script
   setting so a person can turn it off too.

**Settle before writing much.** Two things, and they are the same thing. Every animation
introduced here — camera, movement — has to have a *settled* state the capture can wait for,
or `--shot` has to force it instantly; pick one mechanism and use it for all of them. And the
second window changes what a *frame* is: `SandboxFrame` is one moment's answers read by both
halves, and a HUD split across two windows still reads one frame, or it will show two moments.

**Record before fixing.** Entry 057 is the user's words; when the six are built, append an entry
saying what each cost and what it changed about the pinned scene, so the next play-through has a
baseline. Anything found on the way that is a rule, or a query Core does not expose, is an entry
for Core and not a fix here (contract 2).

**Still open from the greybox, and not this job's.** Whether an unfound hostile should hold a
`?` slot in the turn order, whether a hostile's held arc is drawn when the hostile is, whether
the fixed pitch is enough — Open questions below. And entry 012's second item, the shot line
saying who a shot would wake, half a day whenever it fits. The research territory will have a
view on all four.

**Out of scope.** Art, audio. Every rule. A second map or mission. The strategy layer.

---

## What landed on `view/camera-keys`

The user asked for standard camera controls before the play-through, and the brief above named
the five keys that had to move. What was decided while doing it, since the brief left the
destinations open:

- **The storey pair did not have to be invented.** `PageUp` and `PageDown` already changed storey
  — they were an undocumented alias beside `Q`/`E` — so the remap is a deletion there rather than
  a new binding, and the pair the brief wanted to keep as a pair was already one. It is now the
  only binding, and it is in both tables where it never was before.
- **The three singletons went to `J`, `K` and `L`, next to `H`.** `H` hands the hostile side to
  the AI and did not move, so `J` gives it one turn, `K` turns on answering windows by hand, and
  `L` calls a contact in. Four adjacent keys under the right hand, and all four are *who is
  deciding, and who gets told* — which is a group a person can learn as a group. `L` for **c-a-l-l
  it in** is the only one of the four with a mnemonic and it is the one that needed it least.
- **`,` and `.` still turn the camera.** They cost one `or` in a switch and they are what anybody
  who has used the sandbox already has in their hands. The tables name `Q`/`E`.

**The legend was already broken and this is what found it.** One line of keys along the bottom
edge ran off the right of a 1600-wide viewport, and had been doing so for long enough that it is
in every capture in the repository. Nobody noticed because the keys that fall off the end are the
ones nobody has learned — which is the failure mode of a legend, and the reason it is worth saying
out loud. It is three lines now, split into where you are looking, what the soldier does, and what
the run is set to, and `LegendLines` is the one figure the stack above it reads so the two cannot
drift apart. Splitting by purpose rather than by width also means each line is complete on its own.

**No script step moved.** `--layer`, `--ai-turn`, `--shout`, `--windows` and `--yaw` are the
surface the keys call (entry 049), so every capture command in this file still means what it
said. Two files changed: `HexSandbox.cs` for the switch and `BattleHud.cs` for the legend.

**The pinned scene does change, and only along the bottom edge.** A legend two lines taller is
drawn in every capture, so the zero-changed-pixel comparison in **Seeing it** has to be re-pinned
against a picture taken after this — the world above it is untouched.

---

## What landed on `view/export`

Entry 055 asked for it and entry 056 records what it cost. **Shipping it** above is the whole of
the result — the command, the two files it produces, the differences between the exported harness
and the editor one, and how to put the environment back on a machine that has never had it. Three
things about the shape of the change, which the section itself does not stop to say:

- **The repository gained one tracked file and lost a line from `.gitignore`.**
  `game/export_presets.cfg` is committed on purpose, which is why `game/export_presets.cfg` is no
  longer ignored: Master runs the export with no View session awake, and a preset it would have to
  recreate by hand is not a job it can run. `build/` took the ignored line's place.
- **`game/project.godot` gained `dotnet/project/solution_directory`.** That is the one edit to a
  file that was not new, and it is load-bearing rather than tidy — without it the export writes an
  executable with no .NET assemblies in it and exits 0. **Shipping it** says how that failure
  looks, because the way it looks is the trap.
- **Nothing in `game/scripts/` changed at all.** The capture harness, the script steps and the
  scale contract were exported as they stood and came out identical to the byte. The export is a
  packaging job, and it stayed one.

---

## What landed on `view/greybox`

Entry 053 is the reasoning; this is the shape, and the five decisions the brief asked to be
settled before writing much.

- **The picture shows our side's knowledge and nothing else, and opens that way.** A hostile is a
  body while somebody of ours has eyes on it, a see-through standing body at its marker with its
  credence otherwise, and nothing at all before anybody has heard a thing. `SandboxFrame.Knowledge`
  is the list — `Tactician.Known` for each of ours, merged by keeping the best any of them holds —
  and `SandboxFrame.Sees` is the one question the view, the HUD and the cursor ask, so there is no
  second place a hostile can leak through. What the enemy holds on *us* is drawn in both modes,
  because section 07 of the design doc names it as the one thing of theirs a player sees. `O` or
  `--omniscient` puts everything back, the status line says which is on, and the orders readout
  prints only when it is: it is the enemy's mind, and entry 023 says why it stays as an instrument.
- **One engine unit is one metre, and `SandboxScale` is one static layout and two axis
  conversions.** The pixels layout is gone. The class stays because entry 005 is the argument for
  the place existing: the layout the battle is given is built there from a constant and nothing
  that knows about the camera can build one. It also owns the sign of Z, so a mirror-image map
  cannot be introduced from a call site.
- **Storeys above the one being looked at are ghosted, not cut away.** Solid at or below, drawn at
  sixteen per cent above, so a roof says there is a roof without hiding the room. Cutting away
  loses the tower and the ridge from every picture of the ground; the flat view drew nothing and
  lost the soldiers standing on them. PgUp/PgDn and `--layer` still choose the storey, and it is the
  storey the cursor picks on and the sight sweep runs over.
- **The camera is pitched at 55 degrees and its yaw snaps to the six hex bearings.** `Q` and `E`
  turn it, `--yaw N` sets it, and it opens looking north so up the screen is up the map the way the
  flat view had it. Distance is the zoom — `--zoom N` is metres back, `LegibleAt` is 70 of them —
  and the camera never animates, because a capture has to land on the same frame every run.
- **A 3D capture is byte-deterministic on this machine**, with 3D antialiasing and shadows on. Two
  runs of `--fit` on the first day produced identical files, and every capture since has. So the
  zero-changed-pixel refactor test survives the move; **the pinned scene changes** — see Seeing it.

**Readouts on the ground are tinted hexes, not shapes.** The attention field asks `AttentionOn`
per tile and scales it by the range term the look-gain uses; the held arc asks `AngleOffDegrees`
per tile out to `MaxRange`, brighter inside `OptimalRange`. A flat disc vanishes under a ridge and
floats over a hollow; a tint follows the ground, and it is the rules' own answer per place. The
soldiers are cylinders — a slab, prone — at `StanceProfile`'s heights, with a bar at eye height for
the facing and a ring on the ground for whoever is up. Walls run from `WallBaseHeight` to
`WallTopHeight`, the two figures the sight trace uses, with entry 049's hue and a thickness in
place of the weight. Text is projected: every label the map carries is painted on a flat canvas
over the picture at a fixed point size, which is the lesson about labels in hex radii kept.

**What survived exactly as the brief said it would.** The named actions on `HexSandbox`, the
script, the capture, the frame, the HUD, the scenario, and the figures-not-names rule. `BattleHud`
needed a line saying the mode, the cursor going through the frame, `?` slots in the turn order, and
*somebody unseen* on the exposure line; nothing else.

**The territory question, answered for Master.** Presentation is `BattleView.cs` and
`MeshBuilder.cs`, 1,032 lines. Interface is `BattleHud.cs`, 974. The middle — the node, the camera,
the geometry, the scale, the frame, the palette, the capture, the script, the scenario, the canvas
— is 2,420, and `HexSandbox.cs` alone is the largest file in the directory. The middle grew; it did
not shrink or acquire an owner. The paths divide no better than they did at entry 014.

---

## What landed on `view/mission-file`

Entry 052 is the reasoning; this is the shape.

- **`SandboxScenario` is a name.** `MissionLibrary.Load` reads the file, `Mission.Begin` hands
  back a battle deployed, objectives set and started, and nothing in `game/` knows where anybody
  stands on the waystation. The compound stays as a bare map with hand-placed soldiers, because
  it is the fixture captures are diffed against and the case that keeps a map with no mission
  legal.
- **One of the six briefing parts is on screen and five are behind `M`.** The task is the only
  one that is a sentence about what to do next. The other five are what the squad was told before
  it went, which is a page and not a status line.
- **The sandbox applies the mission's clock and says so** — `round 31/30    out of time`. The
  rules have no clock (entry 047), so this is a view enforcing a content figure; it stops the
  turns and deliberately invents no verdict, because a made-up `Abandoned` would be a rule in
  `game/`.
- **Named ground is labelled on the map**, from `Mission.Places`. Same argument as the exit: a
  place a briefing names and a player cannot find is a name and not a place.

**One row of the audit below is a gap rather than blocked, and it is the last one.** Entry 012's
second item: the scorer charges a shot for what it announces, so the player sees the price and
not the bill. `AwarenessTracker.WouldAnnounce(shooter, from, weapon, at)` exists (entry 033) and
hands back an `Announcement` per enemy, in the same shape as `WouldHear` — which the cursor line
already prints for a route. It is the shot line growing the clause the cursor line has, it is
half a day, and **the names go on screen and the figures do not**, for the reason
`BattleHud.NoiseLine` gives. Do it before the greybox or during it; it is the same readout either
way.


---

## What landed on `view/scripted-capture`, so nobody re-derives it

Entry 049 is the reasoning; this is the shape.

- **The command line is a list of things a person could have done**, in the order typed.
  `SandboxScript` parses, `HexSandbox.Perform` dispatches, and **every step calls the same method
  the matching key calls**. That is the constraint worth keeping: a script that could reach
  `Battle` directly would be a way for a picture to show a state the keyboard cannot reach.
  Adding an action means adding a method, a key and a case — three places, on purpose.
- **A reaction window can be answered by hand**, from either side of it. `K` or `--windows` turns
  it on; a move then becomes `Commit`, a pause, and `Resolve`, and a hostile turn goes to a
  `Commander` built with `WindowAnswer.HandedOut`. `HexSandbox.Open` is the one question the rest
  of the code asks, because from the interface's side the two cases are identical.
- **Windows with no offers are skipped**, in `SkipEmptyWindows`. Core stops at every window when
  it is handing them out and is right to; a screen that stopped to ask a question with no answers
  in it would stop twice a turn on this map.
- **The committed route is drawn** while a window is open, with the tick each step lands on,
  because the mover has paid for a walk it has not taken and the map is otherwise lying.
- **Walls and ground take their look from their figures, never from their id.** Entry 038 asked
  for the decision and entry 049 made it. All six built-in wall profiles come out at the colour
  and weight the old table gave them.
- **The sandbox has an objective**, so a battle on the waystation can end. `Withdrawal` to the
  cottages, nobody above `Searching`, which is the map header as rules.

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
| how much is still left to learn about a contact | own `Detection` against `Threshold(Engaged)` | seen line, per contact, exactly | shown |
| the shot a new facing would open | `Tactician.BestShot` from an untaken pose | posture lines — it is the *prospect* term, scaled by attention and by what is left to learn | shown |
| who would hear you call it in | `Awareness.Earshot` | reserve line, by name — and `L` calls it in | shown |
| how much survives being passed on | `AwarenessModel.RelayFraction` | reserve line, beside the names | shown |

The attention row was worth closing on its own. The watch cone on the map used to answer this
question as a yes or a no; the model does not — a place is attended to fully, at the corner of
the eye, or barely, and the gap between the last two is the entire reason flanking works. The
cone's *range* was a lie as well, and blocked by entry 006 where its *resolution* never had been;
nobody had noticed the two were separate problems. Both are closed now: the cone is a graded
field out to the sight range, and entry 035 says how.

The second row was open the longest and the question was never how to format it. Your own
soldier's certainty about an enemy is neither of the two cases contract 3 originally named — it
is not your exposure and it is not the enemy's alarm. **Entry 042 settled it**: the split is
*whose knowledge it is* rather than what it is about, so your side's knowledge is yours in both
directions, and blurring what your own soldier has worked out would be fog about yourself, which
contract 3 already rejects for exposure in as many words. The seen line quotes it against
`Threshold(Engaged)` — and it can read over 100, because certainty banks margin up to `Ceiling`
and that margin is what a contact survives decay on.

Shouting was the odd row and is closed. `Tactician.AppraiseWord` scored it and
`ReactionAction.Shout` used it in a window, but no `Battle` action let anybody do it on their own
turn — so the interface could not offer it and `Commander` could not generate it, which is entry
012's first item. `Battle.Shout` exists now; `L` calls a contact in and the reserve line says who
would hear it. **Item 2 of entry 012 is still open**: the scorer charges a shot for what it
announces, and there is no preview of *who* a shot would wake, so the player sees the price and
not the bill.

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

## Two territories, one doc — and one territory, settled twice

Presentation and interface are different problems:

- **Presentation** is drawing, cameras, input plumbing, and eventually animation. It consumes
  Core. It lives in `BattleView.cs`, with `MeshBuilder.cs` under it.
- **Interface** is what the player is allowed to know and how they ask for it. It *constrains*
  Core — the design doc's build order puts it plainly: if the AI needs information the interface
  cannot show, the interface is wrong. Section 06 ("What it hands the interface") and section 07
  ("Asymmetric information, deliberately") are interface design as much as rules design. It lives
  in `BattleHud.cs`.

They shared this doc because they once shared a single 705-line file. They no longer do:

| | |
|---|---|
| `HexSandbox.cs` | the Godot node — lifecycle, the scene furniture, the actions, input, handing turns to the AI, gathering what our side knows, and assembling a frame |
| `SandboxScenario.cs` | which mission, by name — or, for the compound fixture, which map and who is on it |
| `SandboxScript.cs` | the command line as a list of things a person could have done, in order |
| `SandboxScale.cs` | the one layout the rules are given, and the axis mapping into the scene |
| `SandboxCamera.cs` | where the map is looked at from: a focus, a distance, one of six bearings |
| `SandboxGeometry.cs` | where things sit in the scene — outlines at floor height, node centres, picking by ray |
| `SandboxFrame.cs` | one moment's answers, assembled once and read by both halves — including what our side knows of the other |
| `MeshBuilder.cs` | coloured triangles into one mesh: prisms, slabs, cylinders, ribbons |
| `SandboxCanvas.cs` | a flat surface over the picture that draws what it is handed; there are two, one per half |
| `BattleView.cs` | **presentation** — ground, walls, links, the route, the fields and arcs, ghosts, bodies, and the map's labels |
| `BattleHud.cs` | **interface** — turn order, the soldier's situation, the shot under the cursor, reactions, the AI's orders |
| `SandboxPalette.cs` | colours and the two materials, shared because a side is one colour in both halves |
| `SandboxCapture.cs` | render some frames, write a PNG, quit |

`BattleView` and `BattleHud` are separate classes rather than partials of the node deliberately:
partials would have kept every private field reachable from both, which is a path boundary with
no boundary behind it. Each takes a `SandboxFrame` and its own surface and can reach nothing
else — the view has a `Node3D` and a canvas for labels, the HUD a canvas of its own.

**Whether that boundary makes two territories was asked in entry 013, answered in entry 014, and
looked at again by the greybox as `../map.md` said it would be.** It does not, and the second look
made it plainer: the middle is 2,420 lines against 1,032 and 974 for the halves, and the node is
the largest file in the directory. A territory is defined by paths, and the paths do not divide.
Entry 053 records the count.

---

## Gotchas

- **Godot defines its own `Side` enum, and its own `Environment`.** `game/` files need
  `using Side = Hexcom.Core.Units.Side;`. `Environment` resolves to Godot's while `using Godot;`
  is in scope, which is what the world environment wants and not what `System.Environment` is.
- **The sandbox needs Godot 4.7 .NET edition**, not the plain build. If your Godot is a different
  4.x, change the `Godot.NET.Sdk` version in `game/Hexcom.Game.csproj` to match.
- **Nothing on this machine is called `godot`.** See **Seeing it**. A session that types the
  short name, gets *command not found* and concludes the engine is missing has been misled by a
  shell, not by the install.
- **`.uid` files are tracked, and Godot writes them for you — but only the editor does.** Running
  the scene does not. Adding a script under `game/scripts/` leaves the tree one file short until
  somebody opens the project; a session with no editor open can make Godot write them with
  `--editor --headless --quit-after 200`, which is how the greybox's two arrived. Commit them with
  the script.
- **Build before you run.** Godot loads the assembly from `game/.godot/mono/temp/bin/Debug/`, and
  a scene launched before `dotnet build Hexcom.sln` fails with *"Cannot instantiate C# script"* —
  which reads like a broken scene file and is not one.
- **A picture is not proof of a rules change.** Sight and cover are scale-invariant (entry 005),
  so the opening frame is byte-identical before and after the world-scale fix. What changed was
  detection, which no still image shows. When a change is about distance, measure it; when it is
  about layout, capture it.
- **A picture is exactly the proof of a drawing change, and the 3D render is deterministic.** Two
  runs of the same command produce the same file, with MSAA and shadows on, so a refactor of
  drawing code can still be held to *zero* changed pixels against the commit before it. The flat
  view's history of catching a 546-pixel arc that way is why this was checked on the first day.
  **Diff the capture against the previous commit whenever you move drawing code, and pin the
  scene when you do.** The pinned scene is now
  `--scenario compound --omniscient --zoom 30 --look 0,0 --yaw 1`: omniscient because the fixture
  is checked with every soldier drawn, and the yaw said because a default is a thing that moves.
  Nothing captured before the greybox diffs against anything captured after it, and nothing
  captured before the key remap diffs against anything after it either — the legend along the
  bottom edge grew from one line to three, and it is in every picture.
- **The readouts are drawn over the map, not beside it.** All three HUD blocks sit on a panel for
  that reason, and anything added to them has to assume there is a tile-cost label underneath —
  because there is. The top block is the active soldier's situation and the bottom block is what
  happened while it was not your go; they are separate so that a busy enemy round does not push
  the situation down onto the roof.
- **The bottom block is *since you last acted*, not a log.** It is replaced whenever the enemy
  gets a go after something you did, so if two of yours are adjacent in the initiative order, the
  second one's pass leaves the block untouched — nothing hostile happened in between. Read it as
  "what they did about that", never as a history. And it prints only when the picture is
  omniscient: it is the enemy's mind.
- **`Battle` does not stop when a side is gone.** The survivors keep taking turns, so anything
  that loops on the hostile side being up has to check `IsDecided` or it never returns.
  `HexSandbox.Settle` does.
- **There is one layout and the camera cannot reach it.** `SandboxScale.World` is a static built
  from a constant; `SandboxCamera` owns a distance and a bearing and rewrites a `Camera3D`. The
  day a zoom factor gets multiplied into a layout is entry 002 again, and the shape of the code is
  what makes that a thing somebody has to do on purpose.
- **Text is projected, everything else is built.** A label is `Camera3D.UnprojectPosition` of a
  scene point, painted on the label canvas at a point size, so it stays legible at any distance
  and has to be redrawn on every camera move. Meshes are rebuilt on every action and never on a
  camera move. If a label and a shape disagree, the frame they were drawn from does not — look at
  which of the two redraws was missed.
- **Transparent meshes are sorted by distance, and all of ours are at the origin.** The ghosted
  storeys and the readouts would draw in whichever order the engine picked, and sometimes a
  readout vanished under a ghosted roof. `SandboxPalette.ClearBehind` carries a render priority so
  the ghosts go first, whatever the distance. Within one mesh, triangles draw in the order they
  were added, which is what lets several tints on one hex composite — so add the unseen wash
  before the fields and the outlines after them.
- **The cursor picks on the storey being looked at and nothing else.** The ray is met with each
  floor height on that storey; a roof above is transparent to it and a floor below is not
  reached. So on the ground storey you cannot click the roof, and on the roof you cannot click the
  room under it. That is what PgUp/PgDn are for.
- **Attention is a tint per tile and costs a query per tile.** Seven soldiers within 45 metres
  of most of the waystation is about eight thousand `AttentionOn` calls a rebuild, which is
  cheap, and eight thousand quads, which is cheap. It would stop being cheap at a hundred
  soldiers, at which point the field should sample rings again.
- **A switch over somebody else's enum wants its default to be a sentence, not a guess.**
  `BattleHud.Describe(Order)` ended in a catch-all that read the stance, which was true of the
  only kind left over when it was written; three kinds landed with grenades and the first one the
  AI threw brought the whole frame down. Entry 049. There are two more switches over Core enums
  in that file, and neither of them is Core's problem.
- **An action lives in three places and that is on purpose.** A method on `HexSandbox`, a key in
  `HandleKey`, a case in `Perform`. The script is an argument list rather than a second input
  system, so nothing but those methods may touch `Battle` — otherwise a capture can show a state
  the keyboard cannot reach, which is the opposite of what a harness is for.
- **A window is modal, and the camera keys are the exception.** While one is open the battle is
  held still around a question, so only the answers and the camera do anything. Looking is not
  answering, and the reactor being chosen for is usually somewhere else on the map.
- **Counting `--pass` is a guess.** Initiative is rolled per round, so a script that passes four
  times lands on a different soldier the day anybody's roll changes. `--until NAME` is what the
  hand does anyway.

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
a capture that read it would not reproduce. Flags put back what that took away:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot out.png --omniscient --hover 2,0 --pass 6 --ai
```

- `--hover q,r[,layer[,region]]` parks the cursor on a node, axial, the way the maps are
  authored. Everything cursor-driven — the path preview, the sight readout, the range band, the
  shot under the cursor and what it is worth — is invisible to a capture without it.
- `--pass N` hands the turn on N times before the picture. Whose turn it is decides most of the
  HUD, and the demo's first soldier carries a **power blade**, so no capture of the opening frame
  can show a rifle's readout. Without `--ai`, nobody acts during the passes — this reaches later
  soldiers, not later situations.
- `--ai` hands every hostile turn to `Commander` during the passes, so each pass is one of ours
  standing still while the other side does what it decides to. Interactively the same thing is
  `H`, and `J` gives one turn — anybody's — to the AI.
- `--omniscient` draws every soldier in play and prints the AI's orders. **Without it the
  picture is the game**: hostiles nobody of ours has found are not in it, and neither is the
  orders readout. A capture checking the AI wants this flag; a capture checking what a player
  would see does not. Interactively it is `O`.

**A map 85 metres across needs the camera told about, so five flags do that.**

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot map.png --fit
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot old.png --scenario compound --omniscient --zoom 30 --look 0,0 --yaw 1
```

- `--fit` pulls back until the whole map is in one picture, working the figure out rather than
  being told it. This is the flag to reach for for a picture of the shape of a map.
- `--zoom N` puts the camera N metres back from the ground it is looking at. Past 70 the tile
  detail switches off, which is deliberate and is what the status line means by *zoomed out*;
  36 is where a battle opens.
- `--look q,r` centres on a hex instead of on whoever is up, at the floor height of the storey
  being looked at.
- `--yaw N` turns the camera to look along hex bearing N, 0 to 5; 1 is north and is the default.
- `--scenario name` picks from `SandboxScenario.All` — `waystation`, the default, or `compound`.
  A name that matches nothing gets you the default and says so in the status line, rather than a
  scene that fails to load.

Interactively it is `W` `A` `S` `D` or a middle-drag to pan, `Q` and `E` to turn, the wheel or
`+`/`-` to zoom, `F` for the whole map and `G` for whoever is up. The camera never re-asks the
rules anything, so none of it can change what is true — only what is on screen.

**The keys, in the three groups the on-screen legend uses.** The legend is
`BattleHud.DrawLegend` and this table is the same content; they are two copies of one list and
changing one without the other is how a legend starts lying.

| Where you are looking | |
|---|---|
| `W` `A` `S` `D` | pan, in screen terms — `W` moves the view up the screen whichever bearing you are on |
| `Q` / `E` | turn the camera to the previous or next hex bearing; `,` and `.` still do the same |
| wheel, `+` / `-` | zoom |
| `F` / `G` | the whole map / whoever is up |
| PgUp / PgDn | change storey |

| What the soldier does | |
|---|---|
| left-click · right-click · space | move · fire · end the turn |
| `C` · `Z`/`X` · `V` · `B` · `T` | stance · turn on the spot · overwatch arc · arm or spring an ambush · leave the field |
| `L` | call a contact in |
| tab, `1`–`9`, space | while a window is open: whose answer, which answer, and run it |

| What the run is set to | |
|---|---|
| `H` · `J` | hand the hostile side to the AI · give it this one turn |
| `K` | answer reaction windows by hand |
| `O` · `M` · `R` | see everything · the briefing · a new battle |

A middle-drag and the arrow keys pan as well, which is the one place two bindings survive the
remap on purpose: a person who has a hand on the mouse should not have to move it.

**And a capture can act.** Everything on the line that is not one of the six settings —
`--shot`, `--shot-after`, `--scenario`, `--ai`, `--windows`, `--omniscient` — is a step, run in
the order it was typed, and each one prints what it did. They are the keys under another name:

| | |
|---|---|
| `--pass [N]` · `--until NAME` | hand the turn on; or hand it on until a named soldier is up |
| `--move q,r[,l[,g]]` · `--fire NAME` | the active soldier moves or shoots — at a soldier the picture shows |
| `--stance NAME` · `--face DIR` · `--overwatch NAME\|none` | posture, facing, the arc being held |
| `--arm` · `--spring NAME` · `--shout NAME` · `--extract` | ambush, call it in, walk off the field |
| `--ai-turn` · `--hostiles ai\|hand` | give this turn to the search; give the side to it or take it back |
| `--place NAME:N` · `--resolve` | answer an open reaction window, and run it |
| `--brief` | the whole briefing on screen |
| `--hover node` · `--look q,r` · `--zoom N` · `--yaw N` · `--fit` · `--layer N` | the cursor, the camera, the storey |

`--until` rather than a count of passes, because initiative is rolled per round. Camera steps go
last, since anything a soldier does afterwards may pull the view to whoever is up next.

The test this was built for, and what it prints — the same line in three dimensions as in two:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot out.png --scenario compound --omniscient   --ai --pass 3 --hostiles hand --until Watchman --overwatch narrow --until Orsini   --move 1,0 --zoom 24
```

*reactions — t15 Watchman (overwatch) snap at (0,1)@0: hit Front for 0.* One of ours moved, a
sentry holding an arc answered it, and the reaction line says what it did.

With `--windows`, a move stops at its reaction window instead and the picture can be taken with
the question still on screen. `--windows --ai --omniscient --pass 30 --zoom 40` on the waystation
stops in round 4 with the sentry committed to a 15-tick walk it has not taken, Vance offered three
answers and their scores, and the route drawn out of the sentry with the tick each step lands on.
`--ai --pass 16 --zoom 60` without `--omniscient` is the game's own view of the same fight two
rounds on: two hostiles as bodies with their rungs, two as `?` in the turn order and nowhere on
the map.

---

## Shipping it

**One command, from the repository root, and what comes out is a game the user double-clicks.**
Master runs this after every round of merges with no View session awake — entry 055 — so it is
written to be pasted rather than adapted.

```bash
mkdir -p build && Godot_v4.7.2-stable_mono_win64_console --headless --path game --export-release "Windows Desktop" ../build/Hexcom.exe
```

PowerShell has no `&&`, so there it is two statements on one line:

```
New-Item -ItemType Directory -Force build > $null; Godot_v4.7.2-stable_mono_win64_console --headless --path game --export-release "Windows Desktop" ../build/Hexcom.exe
```

**What `build/` holds afterwards, and nothing else.**

| | |
|---|---|
| `Hexcom.exe` | 190 MB. The game. This is the one to double-click |
| `Hexcom.console.exe` | 50 KB. A launcher that starts the same game with stdout on the terminal — the exported twin of `Godot_v4.7.2-stable_mono_win64_console`, and the one to script with |

There is no `.pck` and no `data_Hexcom_windows_x86_64/`, because the preset sets both
`binary_format/embed_pck` and `dotnet/embed_build_outputs`. The test the brief set was a thing a
person can copy to another folder and double-click, and one file passes it outright. `build/` is
in `.gitignore`: a built game is derived exactly as a test result is, and nothing checked in is a
claim about whether the tree builds.

**Four things about that command that are findings and not guesses**, each of them checked here
rather than assumed:

- **`--headless` is right, and the export does not need the solution built first.** The exporter
  runs `dotnet publish` itself, as a step it prints. It was run against a tree with every `bin/`,
  `obj/` and `game/.godot/mono` deleted and produced a working executable. This is the opposite
  of the interactive run, which *does* need `dotnet build Hexcom.sln` first and hangs on a dialog
  without it.
- **The export path is taken relative to `game/`, not to the working directory.** `--path game`
  sets it. Hence `../build/Hexcom.exe` for a `build/` at the repository root.
- **`build/` has to exist first.** The exporter will not create it; it stops with *The given
  export path doesn't exist* and writes nothing. That is the whole reason for the `mkdir`.
- **The preset is release, and nothing wants debug.** Everything the HUD prints is drawn by the
  HUD, and everything the script steps print reaches the terminal through the console wrapper in
  a release build — the capture below reports where it wrote to, in release. A debug export would
  buy the .NET debugger and the remote-debug hook, and neither is any use to a person playing.

### The exported game is a second harness

**It honours everything after `--` exactly as the editor run does, and it draws the same
picture to the byte.** `--fit` from the executable and `--fit` from the editor produced the same
SHA-256, so the zero-changed-pixel refactor test in **Seeing it** can be run either way and a
capture taken from a build is comparable with one taken from the tree.

```bash
build/Hexcom.console.exe -- --shot out.png --fit
```

**One difference, and it will bite.** A relative `--shot` path is resolved against the
executable's own directory, not the working directory — so the line above writes
`build/out.png`, and `--shot build/out.png` from the repository root fails with *FileNotFound*
because it is looking for `build/build/out.png`. The editor run resolves the same relative path
against `game/`. Pass an absolute path to either and the question goes away.

### The three checks the build has to pass, and what they said

- **It runs from outside the repository.** `build/` was copied to a temporary directory with no
  checkout anywhere near it and started there. It opens.
- **It opens on the waystation from the mission file.** The status line reads *waystation — a
  garrison holding the crossroads, approached from the west*, the mission line reads *Enter the
  compound, confirm what is stored in the house, and come out — UNDECIDED*, and the turn order
  has Bekker and Orsini against four `?` slots. `H`, `K` and `M` are the three keys of the
  play-through and all three work: their script forms `--ai`/`--hostiles ai`, `--windows` and
  `--brief` were driven through the executable and each reported what it did, `--pass 30`
  stopping at a reaction window in round 4 the way it does in the editor.
- **The capture and script flags survive the export.** They do, byte for byte, which is why
  there is a section about it above rather than a line in **Seeing it** saying the harness is
  editor-only.

### Setting this up on a machine that has never done it

Two things beyond a Godot install, and neither is in the repository.

**1. The export templates, matching the editor exactly.** The editor here is
`4.7.2.stable.mono.official.ed1daf0bf`, and it wants the **mono** templates, not the plain ones.
The route taken was the release asset rather than the editor's *Manage Export Templates* dialog,
because it scripts:

```bash
curl -L -o templates.tpz https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_mono_export_templates.tpz
```

1.20 GB — 1,202,598,411 bytes. It is a zip: unpack it and copy the contents of its `templates/`
directory into `%APPDATA%\Godot\export_templates\4.7.2.stable.mono\`, which on this machine is
`C:\Users\<user>\AppData\Roaming\Godot\export_templates\4.7.2.stable.mono\`. Godot creates the
`export_templates` directory empty on first run, so its existing is not evidence of anything.

**How to tell they are there**: 27 files in that directory, `version.txt` reading exactly
`4.7.2.stable.mono`, and `windows_release_x86_64.exe` among them at about 110 MB. If they are
missing the export stops early and says so by name.

**2. `dotnet/project/solution_directory` in `game/project.godot`, pointing at the repository
root.** This one is not obvious and it costs an afternoon to rediscover. Godot's .NET exporter
insists on a solution file beside the C# project, and it names the one it wants after the
assembly — with the setting absent it looks for `game/Hexcom.Game.sln`, does not find one, and
**fails in a way that still writes an executable**: the run exits 0, `Hexcom.exe` appears at
109 MB rather than 190, the `dotnet publish` step never runs, and the .NET assemblies are simply
not in it. The errors scroll past in the middle of the pack listing. Read the size.

Pointing the setting at the root is what fixes it:

```
[dotnet]

project/assembly_name="Hexcom.Game"
project/solution_directory="res://.."
```

The repository's one solution is `Hexcom.sln` at the root and that satisfies it, even though the
error message names `Hexcom.Game.sln` — checked by moving `Hexcom.sln` aside, which brings the
failure straight back. The alternative was a second solution file inside `game/`, which is a
duplicate of `Hexcom.sln` that has to be kept in step with it, and `game/*.sln` is in
`.gitignore` for the reason that duplicate is unwelcome. The setting also points the editor's own
build button at the real solution, which it should have been pointing at all along.

**Out of scope, deliberately**: an icon, an installer, code signing, and a Linux or Mac export.
Desktop-only is the design and Windows is the machine.

---

## Open questions

- **Whether an unfound hostile should hold a slot in the turn order at all.** It holds a `?` now:
  that somebody acts at that point is known, because turns are taken in the open, but the count
  of the enemy is a thing a stealth game might want to keep. The alternative is to drop the slot
  and let the strip show only what is found, which loses the interleaving the strip exists to
  show. The first play-through is the way to decide.
- **Whether a hostile's held arc should be drawn when the hostile is.** It is not, now: a body
  shows where a soldier is and which way it faces, and the attention field shows where it is
  looking, but what it would shoot at is its intent. Omniscient draws every arc. A player who
  walks into an arc they could see the soldier holding may reasonably say the picture lied.
- **Whether a fixed 55-degree pitch is enough.** It keeps a hex a hex and a wall a wall from every
  bearing, and it cannot look along a wall. Nothing so far has wanted to.
- **Whether a player should be answering the enemy's reactions.** The sandbox drives both sides
  by hand, so an open window offers every reactor in it whichever side they are on — which is
  right for a thing built to try both sides and is not what a shipped interface would do. The
  window readout says whose each offer is; nothing stops you answering for the other lot. Same
  family as the orders readout, which is the opponent's mind and is shown only when omniscient.
- **Whether the mission line belongs to a player at all, or only to a tester.** It shows the
  verdict, which is the scoreboard, and the reading each departed soldier left with, which is
  how the mission is judged. Both are ours by contract 3, so there is no leak; the question is
  whether being told *you have currently failed* mid-battle is the game or a debug readout.
- **Whether the sandbox should keep applying the mission clock once Core has one.** It does now
  because the rules have none and entry 047 says whatever runs the battle applies it, so the
  harness in `content/` and this both do — two implementations of one figure, which is the shape
  entry 038 was about. When the clock lands in the rules this should become a deletion and not a
  second opinion.

Three questions here are answered rather than open. The scenario belongs in `content/` and lives
there. What our own soldiers did during the enemy's turn is no longer invisible: `Act` carries the
outcome (entry 040) and a handed-out window is answerable by hand (entry 049). And the camera is a
`Camera3D`, which is what the old question about a `Camera2D` was really asking for.

## Recent work

```bash
git log --oneline -20 -- game
```
