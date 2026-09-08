# View — presentation and interface

The Godot layer: drawing what Core answers, and taking input. Currently one flat 2D sandbox that
drives both sides by hand.

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

## The job — work the interface fix list

Branch `view/interface-readouts`. Read **The interface audit** below first: it is the list this
job works from, and every item in it says what to do and what is stopping it.

The audit is finished. Four rows of it were closed while it was being written, because the fix
was a line of text once the question had been asked; the rest are still open and are ordered here
by what they cost against what they buy.

1. **Show what the active soldier can see, and what can see it.** `Tactician.Seen` is the list
   the AI's whole defensive half is computed over and the interface shows none of it. Nearest
   thing on screen is the alarm rung floating over each hostile, which is the *other* direction.
2. **Show what a posture would cost and what it would buy** — `Tactics.AppraisePosture` against
   `MovementCosts.ChangeStance` and `TurnInPlace`. This is the single largest hole: `Spared` and
   `Prospect` are two of the four terms in an `Appraisal` and neither has ever appeared on this
   screen. **Half of it is blocked** — see entry 010 in `../decisions.md`, and do not close that
   row by quietly rendering a score with an enemy's exact detection folded into it.
3. **Show the weapon's range bands.** The refusal line says *out of range at 14 m* only once the
   shot is already impossible. Which band a target sits in is what decides whether to close.
4. **Show what a move would announce** — its noise, and who would hear it. Blocked: no query
   exists, for the interface or the AI. Entry 011.
5. **The attention cone still lies about range.** Entry 006, still gated. The metres-per-hex
   figure is settled now (entry 007) but the map is not — 007 says the ranges are right and the
   demo compound is too small, so an honest cone still fills the viewport. Wait for content's
   larger map rather than drawing a cone against this one.

**How to know it worked.** Same standard as the audit: every row either closed with a readout you
can point at in a capture, or annotated with what is blocking it and where that is written down.

---

## The interface audit

*Done on `view/interface-audit`. Contract 2 says the view and the AI read one query surface, and
the build order's rule is sharper: **if the AI needs information the interface cannot show, the
interface is wrong**. This is that check, run against `Tactician` — the scorer the AI ranks every
action by.*

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
| vitality it actually takes off | `Gunnery.Expect().Vitality` | worth line | **closed by this job** |
| plate worn through | `Expect().PlateStripped` | worth line | **closed by this job** |
| shield soaked | `Expect().ShieldStripped` | worth line | **closed by this job** |
| chance it puts them down | `Expect().DownChance` | worth line | **closed by this job** |
| how much soldier is there to remove | `Target.Stats.Vitality` | map label gives current, never the maximum | gap |
| distance, cover, exposure | `SightResult` | cursor line, in metres and per cent | shown |
| where in the weapon's range that falls | `WeaponProfile.OptimalRange` / `MaxRange` | nowhere until the shot is refused | gap |
| the bonus for having the arc already held | `OverwatchArc.AimBonus` | reserve line | shown |

The four closed rows are one change and it was the audit's clearest single finding. Everything
the shot line said was true and none of it was what the AI ranks by: `ShotPlan.ExpectedDamage` is
damage arriving at the plate, and a beam landing squarely on a full shield reads well there and
achieves nothing. The player was being shown the trap the core doc calls the easiest mistake in
the codebase, and being left to do the arithmetic that avoids it.

### Spared — what a posture keeps off you

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| who this soldier is taking seriously | `Tactician.Seen` | nowhere | gap |
| the worst one shot each could do to you | `PlanThreat` per threat and mode | nowhere | gap |
| how likely they are to shoot at all | `Awareness.Of(them, you).Detection` | alarm line, as a rung | coarse — **but see below** |
| the bar they act from | `Model.Threshold(UtilityModel.ActsOn)` | alarm line, named | **closed by this job** |
| what a stance or a turn costs | `MovementCosts.ChangeStance` / `TurnInPlace` | nowhere | gap |
| what the whole trade comes to | `Tactics.AppraisePosture` | nowhere | **blocked** |

**The audit's real find is in this table.** `Tactician.Aimed` reads how much the enemy has
detected you as a raw certainty, and contract 3 says that number is blurred to a rung on purpose.
So the appraisal of a posture cannot be displayed without leaking it — and, worse the other way
round, the AI is reading a figure its own soldier has no way of knowing, which is the one thing
`Tactician`'s own doc comment promises it never does. That is Core's to resolve and it is written
up as entry 010 in `../decisions.md`.

It is worth being clear about which of the two problems matters. The display leak is small — you
would have to invert an aggregate to recover the number. The AI reading it is not small: it is a
soldier who knows exactly how spotted they are, in a game whose whole subject is not knowing.

### Prospect — what an action sets up

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| how much attention a place has | `Awareness.AttentionOn(pose, node)` | cursor line, exactly | **closed by this job** |
| how much is still left to learn about a contact | own `Detection` against `Threshold(Engaged)` | nowhere | gap |
| the shot a new facing would open | `Tactician.BestShot` from an untaken pose | nowhere | gap |
| who would hear you call it in | `Awareness.Earshot` | nowhere — and there is no way to shout | gap, and a Core gap with it |
| how much survives being passed on | `AwarenessModel.RelayFraction` | nowhere | gap |

The attention row was worth closing on its own. The watch cone on the map answers this question
as a yes or a no; the model does not — a place is attended to fully, at the corner of the eye, or
barely, and the gap between the last two is the entire reason flanking works. The cone's *range*
is still a lie and is still blocked by entry 006; its *resolution* never was, and nobody had
noticed the two were separate problems.

Shouting is the odd row. `Tactician.AppraiseWord` scores it, `ReactionAction.Shout` uses it in a
window, and there is no `Battle` action that lets anybody do it on their own turn — so the
interface cannot offer it and the turn planner being built now cannot generate it. Entry 011.

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
different matter and belong on screen, which is what the worth line now does.

### What is not in the scorer yet, and is missing from both

`core.md` names two omissions the turn planner will hit first. Both are also interface gaps, and
saying so is the point of the exercise:

- **Firing gives you away and nothing prices it.** `Battle.AnnounceFire` raises every enemy in
  earshot or facing your way. There is no preview of it, so neither the AI nor the player can see
  what a shot would cost in attention before taking it.
- **A move's noise is computed and thrown away.** `Battle.LoudnessOf` is private and runs inside
  `Move`, after the decision. In a stealth-first game the loudness of a route is one of the two
  or three things worth knowing about it.

Both are Core queries that do not exist. Entry 011.

---

## Two territories, one doc — now with a boundary

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
| `HexSandbox.cs` | the Godot node — lifecycle, the demo scenario, input, and assembling a frame |
| `SandboxScale.cs` | metres against pixels, and the only place that knows the difference |
| `SandboxGeometry.cs` | where things sit on the canvas — centroids, region polygons, hit tests |
| `SandboxFrame.cs` | one moment's answers, assembled once and read by both halves |
| `BattleView.cs` | **presentation** — ground, walls, links, path, beliefs, soldiers |
| `BattleHud.cs` | **interface** — turn order, exposure, the shot under the cursor, reactions |
| `SandboxPalette.cs` | colours, shared because a side is one colour in both halves |
| `SandboxCapture.cs` | render some frames, write a PNG, quit |

`BattleView` and `BattleHud` are separate classes rather than partials of the node deliberately:
partials would have kept every private field reachable from both, which is a path boundary with
no boundary behind it. They each take a `SandboxFrame` and a `CanvasItem` and can reach nothing
else. Two sessions can now work one on each.

This doc still covers both, because one of them has no brief yet. Splitting the doc is a decision
for whoever picks up interface work in earnest.

---

## Gotchas

- **Godot defines its own `Side` enum.** `game/` files need
  `using Side = Hexcom.Core.Units.Side;`.
- **The sandbox needs Godot 4.7 .NET edition**, not the plain build. If your Godot is a different
  4.x, change the `Godot.NET.Sdk` version in `game/Hexcom.Game.csproj` to match.
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
  came out byte-identical. That is how a change to the interface half proves it left the
  presentation half alone.
- **The readouts are drawn over the map, not beside it.** Both HUD blocks sit on a panel for that
  reason, and anything added to them has to assume there is a tile-cost label underneath —
  because there is. The help line and the top row of the map were mutually illegible in every
  capture taken before the panels existed.
- **Drawing scale and world scale are different variables and must stay that way.** `HexSize` is
  pixels and is exported; `SandboxScale.MetresPerHexSize` is metres and is a constant. That
  asymmetry is the contract, not an oversight.

---

## Seeing it

Godot 4.7.2 .NET is installed on this machine and the scene wiring runs — that is no longer an
open question. `winget install GodotEngine.GodotEngine.Mono` puts it under
`%LOCALAPPDATA%\Microsoft\WinGet\Packages`.

```bash
dotnet build Hexcom.sln && godot --path game
```

To capture the sandbox without anyone at the keyboard — which is how a session with no human
watching can check its own work:

```bash
godot --path game -- --shot out.png
```

`--shot-after N` waits N frames first, default 4; the first frame is drawn before the font atlas
is resident and loses every label. **Not with `--headless`** — the headless driver does not
rasterise and the capture comes back blank. `--headless --quit-after 30` is still the cheapest
way to check that the scene loads and `_Ready` survives, which catches most wiring breaks.

**A capture is deaf, so anything it is to show has to be an argument.** The run ignores the mouse
and the keyboard on purpose — the window opens under whatever the pointer was already doing, and
a capture that read it would not reproduce. Two flags put back what that took away:

```bash
godot --path game -- --shot out.png --hover 4,0,1 --pass 2
```

- `--hover q,r[,layer[,region]]` parks the cursor on a node, axial, the way the maps are
  authored. Everything cursor-driven — the path preview, the sight readout, the shot under the
  cursor and what it is worth — was invisible to every capture ever taken before this existed.
- `--pass N` hands the turn on N times before the picture. Whose turn it is decides most of the
  HUD, and the demo's first soldier carries a **power blade**, so no capture of the opening frame
  can show a shot readout at all. One pass brings up somebody with a rifle. Nobody acts during
  the passes — this reaches later soldiers, not later situations.

---

## Open questions

- **The greybox.** Build order puts a 3D blockout after the AI and after grenades — *only once
  the rules are settled*. The flat sandbox stays the working view until then.
- **Whether the demo scenario belongs in `game/`.** `HexSandbox.NewBattle` hard-codes five
  deployments. That is content wearing a view extension, the same way `DemoMaps.cs` is content
  wearing a `.cs` one, and it should probably move when there is a scenario format to move it to.
- **Splitting this doc, and the condition for it is now met.** `map.md` says interface earns its
  own doc when it has a brief of its own. It has one: the audit above and the fix list at the
  top are both entirely interface, and presentation has had no brief at all since the scale
  split. The reason it has not been done here is that `map.md` names `subprojects/view.md` as
  View's doc and `map.md` belongs to master, so the split is two files changing in two
  territories. Raised as entry 012 in `../decisions.md`; do not do it unilaterally.

## Recent work

```bash
git log --oneline -20 -- game
```
