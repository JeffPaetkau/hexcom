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
