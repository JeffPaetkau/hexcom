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
  `../decisions.md` entries 002 and 003.

---

## The job — check the interface against what the AI is about to need

Branch `view/interface-audit`. Read `../decisions.md` entry 004 first; it is the first finding of
this job, written down before the job existed.

Contract 2 says the view and the AI read one query surface, and the build order's rule is
sharper than that: *if the AI needs information the interface cannot show, the interface is
wrong.* Nobody has ever checked the HUD against that standard, because until now there was no AI
to check it against. There is one being built on `core/utility-scoring` right now, which makes
this the moment the rule can actually be enforced rather than merely asserted.

**The work is an audit with a fix list, not a rework.** Go through what a utility score will
weigh — range to target, exposure, cover grade, arc coverage, reserve, what is known about whom,
what a move would cost — and for each one ask whether a player looking at this screen can see it.
Where they cannot, either add it or write down why it is deliberately withheld. Contract 3 makes
that second answer a real one: an enemy's alarm is coarse *on purpose*, and "the AI reads a number
the player is shown a rung of" is the intended asymmetry, not a gap. Distinguishing those two
cases is most of the job.

Two things are already known to be on the list:

- **Range is not shown at all.** Entry 004. Gated on the metres-per-hex figure — do not close it
  by drawing a truthful cone at an interim scale.
- **The top HUD lines collide with the map.** Visible in any capture: the help line runs
  underneath the tile-cost labels and both become unreadable. That one is unblocked, small, and
  worth doing first because every subsequent screenshot is easier to read afterwards.

**How to know it worked.** A written list, in this doc or in `../decisions.md`, of every query
the AI weighs and where the interface shows it. The deliverable is the list; the code changes
fall out of it.

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
- **Build before you run.** Godot loads the assembly from `game/.godot/mono/temp/bin/Debug/`, and
  a scene launched before `dotnet build Hexcom.sln` fails with *"Cannot instantiate C# script"* —
  which reads like a broken scene file and is not one.
- **A picture is not proof of a rules change.** Sight and cover are scale-invariant (entry 003),
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
  **Diff the capture against the previous commit whenever you move drawing code.**
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

---

## Open questions

- **The greybox.** Build order puts a 3D blockout after the AI and after grenades — *only once
  the rules are settled*. The flat sandbox stays the working view until then.
- **Whether the demo scenario belongs in `game/`.** `HexSandbox.NewBattle` hard-codes five
  deployments. That is content wearing a view extension, the same way `DemoMaps.cs` is content
  wearing a `.cs` one, and it should probably move when there is a scenario format to move it to.
- **Splitting this doc.** Presentation and interface now have a real boundary in the code; they
  still share one doc, because interface has no separate brief yet. Whoever takes interface work
  in earnest should split it.

## Recent work

```bash
git log --oneline -20 -- game
```
