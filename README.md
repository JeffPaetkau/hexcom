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

The sandbox runs a five-unit skirmish on `DemoMaps.Compound`, drawn flat — two of yours outside
the compound against three inside it, one of them holding the roof:

| | |
|---|---|
| click | move whoever is up |
| hover | show the route, the cost of each awkward step, and what cover the cursor has |
| space | end the turn |
| `C` | cycle stance: standing, crouching, prone |
| `Q` / `E` | change layer (the roof is layer 1) |
| `R` | new battle |

Green tiles are in reach and show their cost. Dull red tiles can be crossed but not stood in.
Blacked-out tiles are dead ground the active unit has no eyes on, and outlined tiles have cover
from where it is standing — blue light, yellow half, orange full. Wall colours: white solid,
orange high, yellow low, blue railing, green sight-screen. The strip on the right is the turn
order with each unit's initiative roll.

Go prone and watch the visible area collapse. Pass a few turns and watch the order interleave
rather than alternate. The spotter on the roof sees most of the map; getting up there costs six
of ten points, so whoever wants that position gives up their turn to take it.

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
- **Units and the turn loop** — a `Battle` owns the map, the units and whose turn it is. Turn
  order is a queue over a battle clock rather than sides alternating, so play interleaves: one
  of yours, two of theirs, one of yours. Initiative is a rating plus a d10, less the weight of
  your kit. Every roll comes from one seeded generator, so a whole fight replays identically
  from a seed and a list of commands — which is what makes headless balance runs possible.

## What is not built yet

The detection and awareness model, the ambush action, weapons, damage, AI, saves, and the
strategy layer. See the design doc for where these are heading.
