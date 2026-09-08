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
- **One horizontal world unit is one metre** (contract 5) — *currently violated here*. See
  `../decisions.md` entry 002; this is the first thing for a View session to fix.

---

## The job — separate rendering scale from world scale

Branch `view/world-scale`. This is `../decisions.md` entry 002; read it first, it has the
evidence.

`HexSandbox.cs:79` hands the drawing layout straight to `Battle`:

```csharp
_layout = new HexLayout(HexSize);                              // 44 — pixels
_battle = new Battle(DemoMaps.Compound(), _layout, seed: Seed);
```

`SightSolver` builds a `Vec3` from that layout's X and Y and a floor height in **metres**, then
takes distances across it. So the sandbox is telling the rules a hex is 44 m across while a solid
wall is 3 m tall. Every wall is a kerb to the sight trace: cover collapses towards none, prone
behind sandbags does not hide, and the awareness ranges in metres fall inside a single hex. Tests
never caught it because they all pass `size: 1.0`.

**The fix is two layouts.** One in metres, constructed here and handed to `Battle`; one in pixels
for drawing. The view converts between them at the boundary — that is what a view layer is for.
Take care that everything currently reading `_layout` is sorted into the right one: `HexAt` for
input and `Position`/`Center` for drawing are pixel-side, and anything Core is given is
metres-side.

**Do not wait on the metres-per-hex figure.** Nobody has ever decided it, and Content owns the
question (see [content.md](content.md)). Use the tests' `1.0` as the interim value, leave a
comment saying it is interim and pointing at the open question, and get the *structure* right —
that is the part that makes contract 5 enforceable rather than merely true. When Content settles
the number, changing it becomes a one-line edit instead of an archaeology exercise.

**How to know it worked.** The sandbox should start behaving like the tests: go prone behind
sandbags and disappear, walk into a building's shadow and lose the watcher. If cover still does
nothing, the two layouts have not actually been separated.

**Then, and only if you have appetite:** the `HexSandbox.cs` split below. It is not urgent while
one person works here, and it is a precondition for two.

---

## Two territories, one doc

Presentation and interface are different problems:

- **Presentation** is drawing, cameras, input plumbing, and eventually animation. It consumes
  Core.
- **Interface** is what the player is allowed to know and how they ask for it. It *constrains*
  Core — the design doc's build order puts it plainly: if the AI needs information the interface
  cannot show, the interface is wrong. Section 06 ("What it hands the interface") and section 07
  ("Asymmetric information, deliberately") are interface design as much as rules design.

They share this doc because they share a single file, `game/scripts/HexSandbox.cs`, so there is
no path boundary to enforce. Splitting that file is what earns interface a doc of its own.

---

## Gotchas

- **Godot defines its own `Side` enum.** `game/` files need
  `using Side = Hexcom.Core.Units.Side;`.
- **Godot is not installed on this machine.** The scene wiring has never been verified — only the
  C#. `dotnet build Hexcom.sln` typechecks `game/` against Godot 4.7.2 and that is the whole of
  the assurance available here. Say so rather than implying a change was seen working.
- **The sandbox needs Godot 4.7 .NET edition**, not the plain build. If your Godot is a different
  4.x, change the `Godot.NET.Sdk` version in `game/Hexcom.Game.csproj` to match.
- **Drawing scale and world scale are the same variable today, and must not be.** `HexSize = 44`
  is a pixel figure and it is being handed to `Battle`. See above.

---

## Open questions

- **Splitting `HexSandbox.cs`.** It is presentation, interface, input handling and scenario setup
  in one file. The split is what makes the two territories separable; it is not urgent while one
  person is working here, and it is a precondition for two.
- **The greybox.** Build order puts a 3D blockout after the AI and after grenades — *only once
  the rules are settled*. The flat sandbox stays the working view until then.
- **What the interface owes the AI.** Every query the AI wants must be showable. Nobody has
  checked the existing HUD against that standard, and the AI does not exist yet to test it.

## Recent work

```bash
git log --oneline -20 -- game
```
