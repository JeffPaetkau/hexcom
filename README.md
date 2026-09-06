# Hexcom

Turn-based squad tactics on a hex grid. Stealth-first, action-point movement, individual
initiative. Desktop only.

## The one architectural rule

`Hexcom.Core` is plain .NET and **never references a game engine**. Every rule — hex geometry,
cover, movement, line of sight, detection, initiative, damage, AI — lives there. Godot is a
presentation and input layer that queries the core and draws the answer.

That buys three things: the rules are unit-testable headless, balance can be tuned by running
thousands of AI-vs-AI matches in seconds, and if the art pipeline ever forces a move off Godot,
only the view layer is lost.

If you ever find yourself adding `using Godot;` to a file under `src/`, stop.

```
src/Hexcom.Core/        the rules — no engine references, ever
tests/Hexcom.Core.Tests/  xUnit
game/                   the Godot 4 project (view + input only)
```

## Running it

Tests, and the fastest way to see whether anything is broken:

```bash
dotnet test
```

The sandbox needs **Godot 4.7 .NET edition** ([godotengine.org](https://godotengine.org/download)
— the build labelled ".NET", not the plain one). Open `game/project.godot` in the editor and
press F5. If your Godot is a different 4.x, change the `Godot.NET.Sdk` version in
`game/Hexcom.Game.csproj` to match.

The sandbox loads `DemoMaps.Compound` and draws the movement graph flat:

| | |
|---|---|
| click | move the unit somewhere it can stand |
| hover | show the route, the cost of each awkward step, and what cover the cursor has |
| `Q` / `E` | change layer (the roof is layer 1) |
| `C` | cycle stance: standing, crouching, prone |
| `[` / `]` | change the action point budget |
| `R` | reset |

Green tiles are in reach and show their cost. Dull red tiles can be crossed but not stood in.
Blacked-out tiles are dead ground the unit has no eyes on, and outlined tiles have cover from
where it is standing — blue light, yellow half, orange full. Wall colours: white solid, orange
high, yellow low, blue railing, green sight-screen.

Go prone on the ground floor and watch the visible area collapse; climb the ladder and watch it
open up.

## What is built

- **Hex geometry** — axial coordinates, flat-top layout, distance, rings, lines. `HexLayout`
  converts to world space; rotating it 30° renders pointy-top without touching the logic.
- **Corner graph** — every grid corner has one canonical name shared by the three hexes that
  meet at it, so walls live on a global corner graph rather than per-tile.
- **Cover as chords** — a wall joins any two corners of a hex. Six sides, six minor chords, three
  bisectors: fifteen segments per hex, one uniform representation for building faces, sandbag
  lines and barricades cutting diagonally across a tile.
- **Region partition** — chords cut a hex into regions by planar face traversal. Regions below
  60% of a hex are crossable but not standable, so a bisected tile can be vaulted through but
  never occupied.
- **Movement graph** — typed, individually priced links (walk, vault, climb, ladder, drop,
  stairs, door, crawl) instead of uniform grid steps. Climbs, ledges and drops are generated
  from floor heights; ladders and stairs are authored.
- **Pathfinding** — Dijkstra over action points, returning the whole reachable set. Transit
  regions are pathed through but excluded from valid destinations.
- **Sight and cover** — one trace answers both, because they are the same question. The top of
  each wall the line crosses is projected back onto the target as a waterline; cover is graded
  by how much of the silhouette falls below it, and the target is invisible when an opaque wall
  submerges all of it. Stance, elevation and range are not special cases — a prone soldier
  behind sandbags vanishes, and a shooter on a roof negates that same cover, purely from the
  geometry.

## What is not built yet

The detection and awareness model, initiative, units, weapons, damage, AI, saves, and the
strategy layer. See the design doc for where these are heading.
