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

## The job — the sandbox loads the mission file

Branch `view/mission-file`. Row 5 of entry 045's road, and **it is unblocked**: entry 047 landed
the file, and its *For View* paragraph is the whole API —
`MissionLibrary.Load(name)`, `Mission.Begin(seed, layout, map)`, `Mission.Deploy(battle)` for a
caller that builds its own `Battle`, `Mission.Brief` as six strings fit to show, and
`Mission.Places` as named ground a readout can label. The sandbox builds its own `Battle`,
because it wants its own layout, so `Deploy` is the one it wants.

**It is a deletion, which is what gathering the scenario in one place was for.**
`SandboxScenario` holds four things the file now holds: which map, who starts where with what
facing, where our side may leave from, and the bar we may not be noticed above. Entry 038 counted
three copies of the waystation mission and entry 049 knowingly added a fourth; 047 collapsed the
first three, so this is the last one. **The compound stays**, and not out of sentiment: it is the
fixture every capture from before the waystation was taken against, and entry 047 makes it the
case that keeps a map with no mission legal. So the type does not go — its waystation deployment
list does, and a scenario becomes either a mission name or a bare map.

**Two things to get right rather than to discover.** `Mission.Brief` is six strings and the
mission line currently prints `Objective.Brief`, which is one; deciding which of the six a player
sees mid-battle, and where the other five go, is interface work and not formatting. And the file
carries a round limit that nothing in the rules reads — entry 047 says whatever runs the battle
applies it — so the sandbox either applies it and says so on screen, or does not and says that
instead. Silently ignoring it is the one option that is wrong.

**Read entry 048 before touching the objective.** Fought from the file, twelve seeds all settle
and in none of them does anybody go near the compound: only the leaving half of the mission is
in the rules, so walking straight out is the best available play. That is Core's to fix and the
sandbox will show it happening; do not read it as the loader being wrong.

**How to know it worked.** `--scenario waystation` deploys from `content/` with nothing about the
waystation left in `game/`, and the mission line still reads the same words.

**Two lines while the file is open.** Entry 047 says the remarks on `SandboxScenario` and
`SandboxCapture` still describe `DemoMaps.cs` as present; it is deleted. And entry 046 names the
three hostile posts — Sentry is Cobb, Spotter is Teague, Watchman is Marek — but the names live
in the mission file now, so that is Content's line and not this job's; if any string literal
survives the deletion, it should be a name.

**One audit row is now a gap rather than blocked**, and it is the sibling of the one 049 closed:
`Battle.WouldAnnounce(ShotPlan)` exists (entry 033), so who a *shot* would wake can go on the
shot line the way who would hear a route already goes on the cursor line. Not this job; noted so
it is not re-found.

**After that, the greybox** — the section below is its brief, written in full so that it can be
promoted to `## The job` the day this one is merged. It rewrites `game/` substantially, so nothing
here should be built as though it will survive untouched.

---

## The job after this — the greybox (build order 06)

Branch `view/greybox`. **This is the brief for a fresh session**, and it is written so that this
file, `../map.md`, and the entries it cites are the whole of what that session reads before it
starts. The design doc is 120 KB; read sections 01, 06 (*What it hands the interface*) and 07
(*Asymmetric information, deliberately*) and no more of it unless a question sends you there.

**What it is.** A 3D blockout of the sandbox with no art in it: every hex a flat prism at its
floor height, every wall a box at the band height contract 6 fixes, every soldier a body at its
stance height with its facing marked, and every readout the flat sandbox has learned to draw,
drawn again in the space the rules already describe. *Playable* means what entry 050 says:
a person drives one side against `Commander` on the waystation from its mission file, answers
reaction windows by hand, and wins by withdrawing. It is the first view anyone will play rather
than test, and that is the whole of what changes — the rules have not moved since entry 041 and
every query this draws already exists.

**Why now, against the build order's *only once the rules are settled*.** The rules that shape
a view are settled: nothing added since 040 has changed a signature the sandbox reads, the
audit's rows are all shown, coarse or gap, and the one thing Core still owes the mission (entry
048, the task half) changes what the AI does and nothing about what is drawn. Balance dials will
move for a year and none of them change a shape. Entry 051 records that judgement and it is
Master's; if building this finds a query missing, that is an entry and not a reason to stop.

**Where the seam is, by what survives and what does not.** The flat sandbox was built in
eleven files against the day it would be rewritten, and the division was made for this:

| Survives as it is | Why |
|---|---|
| `HexSandbox`'s named actions — `MoveTo`, `FireAt`, `SetStance`, `PlaceReaction`, `ResolveOpenWindow` and the rest | the one surface both the keys and the script call; entry 049 says why it must stay the only thing that touches `Battle` |
| `SandboxScript`, `SandboxCapture`, and every flag in **Seeing it** | a session with no human watching checks its drawing with these, and a greybox nobody can photograph is a greybox nobody can check |
| `SandboxFrame` | one moment's answers, assembled once — the 3D view reads the same frame the HUD reads, which is contract 2 as a class |
| `BattleHud` | the interface is 2D text over the picture and stays so; it draws to a `CanvasLayer` and should need nothing but a new place to hang |
| `SandboxScenario`, as a mission name or a bare map | what the job above leaves of it |
| the figures-not-names rule of entry 049 | a wall's look comes from what it stops and what it costs; a material is a colour with a third dimension |

| Rewritten | Into |
|---|---|
| `BattleView` | meshes in a `Node3D` tree instead of `_Draw` calls — ground, walls, links, the route, the attention field, the held arc, the soldiers |
| `SandboxGeometry` | world positions from `HexLayout` and floor heights, and picking by ray rather than by polygon |
| `SandboxCamera` | a `Camera3D`, which the open question below has been asking for |
| `SandboxPalette` | materials; the same six colours, one per side and per cover grade |
| `SandboxScale` | see the first decision — it may become a single line, and the line must stay |
| `Sandbox.tscn` | a 3D scene; keep the node name so the capture path does not change |

**Settle before writing much.** Five decisions, and the first is the one that makes this a game.

1. **What a player is allowed to see of the other side.** The flat sandbox draws every hostile in
   play, and the beliefs it draws are the *enemy's* markers on us — right for a tool that drives
   both sides and the opposite of a game whose subject is who saw whom first. A playable view
   draws **your side's knowledge and nothing else**: a hostile as a body only while somebody of
   yours holds `EyesOn` on it, as a ghost at its marker with its credence otherwise
   (`Tactician.Known` is the list, and entry 042 says your own certainty is shown exactly), and
   not at all before anybody has heard a thing. Contract 3 permits exactly this and forbids
   nothing else. **Keep the see-everything mode as a switch** — `--omniscient`, or whatever
   name — because the capture harness and the orders readout are test instruments and 023 says
   so. Decide which mode the keys open in, and make the status line say which is on.
2. **World units.** In 3D one engine unit can be one metre, and `SandboxScale`'s whole reason —
   pixels against metres — collapses to a conversion of one. Contract 5 still stands: rendering
   scale is never fed into `Battle`. Keep one place that owns the layout the battle is given,
   however small it gets; the decisions log (entries 002, 005) is the argument for why that
   place exists at all, and it is the first thing a future session will delete as dead code.
3. **Storeys.** `--layer N` shows one floor of a flat map. In 3D a roof is above a room, and the
   waystation has a house roof, a tower and a ridge. Decide whether the active soldier's storey
   is shown by cutting away what is above it, by ghosting it, or by nothing — and know that the
   attention field and the held arc are drawn on the *ground* of a storey, so a roof that hides
   the floor hides the readout too. This is the one thing 3D makes harder rather than easier.
4. **The camera.** Facing is a rule here — six body faces, arcs measured from `Unit.Facing` —
   and an arc is legible only from a camera that agrees with the grid. A pitched camera whose
   yaw snaps to the six hex bearings keeps every wedge readable at every angle; a free orbit
   does not. Pan, zoom, `--fit`, `--look` and `--zoom` keep their meaning; `--zoom` becomes a
   distance rather than a hex radius, and the status line's *zoomed out* threshold moves with it.
5. **What a capture proves in 3D.** The flat render is byte-deterministic and the doc above
   relies on it for zero-changed-pixel refactors. A 3D render with MSAA and a depth buffer may or
   may not be, on this machine. **Find out on the first day**, with two captures of the same
   command, and write the answer into **Seeing it** before building anything that would rely on
   either answer.

**What to draw, in the order it earns its keep.** Ground and walls first, at the heights in
contract 6, and a capture with `--fit` of the waystation that a person can read as the same map
the flat one shows. Then soldiers as bodies with facing. Then the six things the flat sandbox
draws that nothing else shows — the attention field, the held arc, the committed route with its
ticks, the reach set with its costs, the cover outlines, and the markers — each one checked
against the flat capture of the same command. Then the mission: the exit as a named place on the
ground, because a place that is not visible does not exist (entry 049). The HUD reads the same
frame throughout and should not need to change to be right.

**The territory question, which is Master's and which this job is asked to inform.** Entry 014
settled that presentation and interface are one territory because the paths did not divide, and
`../map.md` says the greybox is the moment to look again. When the rewrite is done, say in
`../decisions.md` whether they divide now — whether `game/` has fallen into a 3D-view half and a
HUD half with a small shared middle, or has not. That is a finding about paths, not a request to
split, and it is the only thing about the breakdown this brief asks for.

**Out of scope.** Art, animation, audio, and anything under `assets/` — a blockout is boxes on
purpose, and the visual register in `docs/setting.md` is for whoever comes after. Every rule.
The task half of a mission — the AI will walk to the exit in round 2 on the waystation and
entry 048 says why; a picture of it doing so is correct. The map editor. A second mission or
map. Suppression, saves, the strategy layer.

**How to know it worked.** Three things, and the last is the one that matters:

- A capture from one pasted command, on the waystation from its mission file, in which the
  ground, the walls, the soldiers and every readout in the table above are in the picture and
  match the flat capture of the same command in what they say.
- The scripted test from entry 049 — a sentry holding an arc answers a move — reproduces in 3D
  with the reaction line saying the same thing.
- **A person plays the waystation mission to a verdict against `Commander` with windows handed
  out and the other side hidden until found**, and says afterwards what read wrong. That is the
  first measurement of the interface rather than of the rules, and it belongs in
  `../decisions.md` beside the balance findings.

---

## What landed on `view/scripted-capture`, so nobody re-derives it

Entry 049 is the reasoning; this is the shape.

- **The command line is a list of things a person could have done**, in the order typed.
  `SandboxScript` parses, `HexSandbox.Perform` dispatches, and **every step calls the same method
  the matching key calls**. That is the constraint worth keeping: a script that could reach
  `Battle` directly would be a way for a picture to show a state the keyboard cannot reach.
  Adding an action means adding a method, a key and a case — three places, on purpose.
- **A reaction window can be answered by hand**, from either side of it. `W` or `--windows` turns
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
| who would hear you call it in | `Awareness.Earshot` | reserve line, by name — and `S` calls it in | shown |
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
012's first item. `Battle.Shout` exists now; `S` calls a contact in and the reserve line says who
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
| `HexSandbox.cs` | the Godot node — lifecycle, the actions, input, handing turns to the AI, and assembling a frame |
| `SandboxScenario.cs` | which map, who is standing on it, and what winning is. Content wearing a view extension, gathered in one place against the day there is a mission file |
| `SandboxScript.cs` | the command line as a list of things a person could have done, in order |
| `SandboxScale.cs` | metres against pixels, and the only place that knows the difference |
| `SandboxCamera.cs` | where the map is looked at from and how close. Owns the scale, because zooming rebuilds it |
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
  **Diff the capture against the previous commit whenever you move drawing code.** Pin the scene
  when you do — `--scenario compound --zoom 44 --look 0,0` is the frame every capture taken
  before the waystation was taken at, and the default is now a different map at a different zoom
  centred on a different thing. A diff against an unpinned default is a diff of the deployment.
  It cuts the
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
  asymmetry is the contract, not an oversight. The camera moves the first one on every wheel
  notch and must never move the second — which is why zooming rebuilds a whole `SandboxScale`
  rather than assigning to a field: an immutable pair of layouts cannot drift apart.
- **Anything drawn in hex radii vanishes when you zoom out, and text does not.** A label set at
  11 points stays 11 points at any zoom, so an offset quoted in hex radii puts the name on top of
  the dot; a box width quoted in hex radii clips the last characters off every label on the map
  at once. Offsets and text boxes are therefore in pixels, footprints and wedges in hex radii,
  and anything the rules quote in metres goes through `SandboxScale.MetresToPixels`. Three units
  in one file is not a mess, it is three different questions.
- **A map that brings its own kit brings no colour with it.** `BattleView.StyleFor` switches on
  well-known wall ids, so a profile a `.hexmap` declares for itself — the waystation's `hedge`,
  say — draws in the default grey until somebody adds a case. Entry 035.
- **The sandbox draws one storey and the units on the others are still there.** They come out as
  hollow rings labelled *above* or *below*, with their attention field drawn all the same, since
  a soldier four metres up is watching this ground and not some other ground. Leaving the field
  out was tried and it hid the most interesting fact on the waystation.
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
  readout in a picture. The command above is the one that proved that branch: by the sixth pass
  the Spotter has crawled along the roof, put an aimed shot into the scout at 95 % and gone prone,
  and the bottom block says so with every term. Interactively the same thing is `H`, and `A`
  gives one turn — anybody's — to the AI.

**A map 85 metres across needs the camera told about, so four more flags do that.**

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot map.png --fit
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot old.png --scenario compound --zoom 44
```

- `--fit` pulls back until the whole map is in one picture, working the figure out rather than
  being told it. This is the flag to reach for: the waystation at the 44-pixel hex the compound
  was drawn with is nearly four screens wide, so without it every picture is of one corner.
- `--zoom N` sets the hex radius in pixels directly. Below 22 the tile detail switches off, which
  is deliberate and is what the status line means by *zoomed out*.
- `--look q,r` centres on a hex instead of on whoever is up.
- `--scenario name` picks from `SandboxScenario.All` — `waystation`, the default, or `compound`.
  A name that matches nothing gets you the default and says so in the status line, rather than a
  scene that fails to load.

Interactively it is the wheel or `+`/`-` to zoom, a middle-drag or the arrows to pan, `F` for the
whole map and `G` for whoever is up. The camera never re-asks the rules anything, so none of it
can change what is true — only what is on screen.

**And a capture can act.** Everything on the line that is not one of the five settings —
`--shot`, `--shot-after`, `--scenario`, `--ai`, `--windows` — is a step, run in the order it was
typed, and each one prints what it did. They are the keys under another name:

| | |
|---|---|
| `--pass [N]` · `--until NAME` | hand the turn on; or hand it on until a named soldier is up |
| `--move q,r[,l[,g]]` · `--fire NAME` | the active soldier moves or shoots |
| `--stance NAME` · `--face DIR` · `--overwatch NAME\|none` | posture, facing, the arc being held |
| `--arm` · `--spring NAME` · `--shout NAME` · `--extract` | ambush, call it in, walk off the field |
| `--ai-turn` · `--hostiles ai\|hand` | give this turn to the search; give the side to it or take it back |
| `--place NAME:N` · `--resolve` | answer an open reaction window, and run it |
| `--hover node` · `--look q,r` · `--zoom N` · `--fit` · `--layer N` | the cursor, the camera, the storey |

`--until` rather than a count of passes, because initiative is rolled per round. Camera steps go
last, since anything a soldier does afterwards may pull the view to whoever is up next.

The test this was built for, and what it prints:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot out.png --scenario compound   --ai --pass 3 --hostiles hand --until Watchman --overwatch narrow --until Orsini   --move 1,0 --zoom 44
```

*reactions — t15 Watchman (overwatch) snap at (0,1)@0: hit Front for 0.* One of ours moved, a
sentry holding an arc answered it, and the reaction line says what it did — which was checkable
only with a hand on the keyboard until this existed.

With `--windows`, a move stops at its reaction window instead and the picture can be taken with
the question still on screen. `--windows --ai --pass 30` on the waystation stops in round 4 with
the sentry committed to a 15-tick walk it has not taken, Vance offered three answers and their
scores, and the route drawn out of the sentry with the tick each step lands on.

---

## Open questions

- **The greybox.** Build order puts a 3D blockout after the AI and after grenades — *only once
  the rules are settled*. The flat sandbox stays the working view until then.
- **Whether the camera should be a `Camera2D`.** It is an offset on the node, which is what the
  one line it replaced already was, and it costs nothing while there is a single flat view. A
  real camera node would give smoothing, limits and a viewport for free, and the greybox will
  want all three.
- **Whether a player should be answering the enemy's reactions.** The sandbox drives both sides
  by hand, so an open window offers every reactor in it whichever side they are on — which is
  right for a thing built to try both sides and is not what a shipped interface would do. The
  window readout says whose each offer is; nothing stops you answering for the other lot. Same
  family as the orders readout, which is the opponent's mind and is shown anyway.
- **Whether the mission line belongs to a player at all, or only to a tester.** It shows the
  verdict, which is the scoreboard, and the reading each departed soldier left with, which is
  how the mission is judged. Both are ours by contract 3, so there is no leak; the question is
  whether being told *you have currently failed* mid-battle is the game or a debug readout.

The scenario question is answered rather than open: it is a `## The job` above, waiting on
Content. And what our own soldiers did during the enemy's turn is no longer invisible — `Act`
carries the outcome (entry 040) and a handed-out window is answerable by hand (entry 049).

## Recent work

```bash
git log --oneline -20 -- game
```
