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
| left-click | move whoever is up |
| hover | show the route, the cost of each awkward step, and what cover the cursor has |
| right-click | fire at whoever is under the cursor |
| space | end the turn |
| `C` | cycle stance: standing, crouching, prone |
| `V` | cycle the overwatch arc: none, narrow, standard, wide |
| `Z` / `X` | turn on the spot |
| `Q` / `E` | change layer (the roof is layer 1) |
| `R` | new battle |

Green tiles are in reach and show their cost. Dull red tiles can be crossed but not stood in.
Blacked-out tiles are dead ground the active unit has no eyes on, and outlined tiles have cover
from where it is standing — blue light, yellow half, orange full. Wall colours: white solid,
orange high, yellow low, blue railing, green sight-screen. The strip on the right is the turn
order with each unit's initiative roll.

The translucent wedge on each unit is the arc it is properly watching. Under each enemy is how
alarmed they are — coarse on purpose. Your own soldier's exposure is reported exactly, in the
HUD, because that is information about yourself. Faint red circles are where an enemy *believes*
one of yours to be; they stop moving when you do. A brighter, outlined wedge is an overwatch arc
being held, and the yellow figure in the turn order is what that unit has banked to answer with.

Go prone and watch the visible area collapse. Pass a few turns and watch the order interleave
rather than alternate. Walk round behind a sentry's wedge and watch it stay unaware while the
same walk in front of it does not. The spotter on the roof sees most of the map and carries the
radio, so it is the one worth reaching first — and getting up there costs six of ten points, so
whoever wants that position gives up their turn to take it.

You drive both sides, so overwatch is easy to try: give a sentry a narrow arc with `V`, end its
turn, then run one of yours across it. The HUD reports which tick the shot went off on and where
the runner was standing when it landed. Run the same route again with the arc set wide and watch
the same weapon shoot worse.

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
- **Detection and awareness** — no aggro radius anywhere. Every enemy that knows about you
  learned it through a channel you can see and cut: looking (on their own turn, so a sentry that
  has already acted leaves a window), hearing (immediate, and it reports a place rather than a
  person), or being told by radio, by shouting, or by watching a comrade react. Only a unit with
  a radio reaches the whole side. Each enemy holds a belief about where you are, and it goes
  stale the moment you move.
- **Facing and vision cones** — a unit looks one way: full attention across 120°, a corner of the
  eye out to 200°, a twelfth behind. Coming at a sentry from the rear is worth an order of
  magnitude, so a position is flankable rather than merely approachable. Facing changes how
  readily something is *noticed*, never whether it could be seen — line of sight stays geometry.
  Moving turns you to face your line of travel for free; watching one way while standing still
  costs a point.
- **Weapons, shooting and protection** — beam against kinetic, and each defeats what the other
  cannot. Shields soak beams and shrug at solid objects; ablative plate stops rounds and cooks
  under a beam. Both are tracked **per side of the body** — front, two shoulders, two flanks and
  the back — so the walk round the back that buys an unnoticed approach also buys the thin side
  of the armour, and a soldier whose front shield has collapsed can turn a fresh one to the
  threat for a point. Hit chance comes from the sight trace's exposure figure, weapon range
  bands, fire mode and stance. Firing gives you away through the channel your weapon uses: a slug
  rifle is heard through walls, a beam paints a line back to you for anyone facing your way, and
  a powered blade does neither.
- **A body is a hexagon too** — so a shot is never at one plate. Head-on you can reach half the
  front and a quarter of each shoulder; on the corner, two plates equally. Which one a round
  finds is rolled against those shares. A slug that arrives at an angle skips off and loses some
  of its damage; a beam lands where it lands and burns. The averages are flattened so the
  bearing you approach from decides *which side wears*, never how much gets through — a hexagon
  is bookkeeping, not a claim that soldiers are hexagonal. Ordinary soldiers do not choose where
  a round lands; placing one on a named plate is something a soldier earns, and costs accuracy.
- **Everyone pays their own prices** — the price list describes the world, but what a given
  soldier spends on it is about them. A scout quick over ground and slow on the trigger and a
  gunner the other way round spend the same ten points on very different turns, and gear that
  shaves a point off firing is a multiplier on the wearer. Inside a reaction window that is not
  only economy: cost is time, so the slow shooter's round lands later and catches the runner
  further along.
- **The reaction window, and overwatch** — a move is committed before anyone answers it, so for
  its duration both sides know the future. Inside the window **action points are time**: a
  reactor placing an action at tick *t* that costs *k* resolves at *t + k*, against wherever the
  mover will be by then. A three point snap shot catches a runner in the open; a slower, better
  shot arrives after the same runner is behind a wall. Reactions are paid for out of what was
  left at the end of your own turn, so sprinting somewhere leaves you nothing to answer with, and
  the choice to hold points back is made before you know whether it will pay. Overwatch is the
  first of the three kinds: a declared arc, an aiming bonus that sharpens as the arc narrows, and
  a shot cheap enough to land early in the window. A watchman only fires at somebody it has
  actually noticed — holding an arc buys it a look at the moment of the crossing, not certainty
  about what is there, so a careful enough approach still gets across.

## What is not built yet

Ambush and surprise, grenades and mines, suppression, AI, saves, and the strategy layer. See the
design doc for where these are heading.

The setting is science fiction — Star Trek, Star Wars, Babylon 5 in register.

Ambush and surprise fold into the machinery that is already there. Both place actions on the same
committed timeline out of the same reserve; what is new in each is only who is asked and when.
A `ReactionWindow` already separates offering choices from resolving them, which is where the
interface and the AI will plug in.
