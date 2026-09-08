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
docs/                   design doc, and the project map the work is divided by
```

Work is split into territories with path-based ownership so that several sessions can run at
once without colliding. [`docs/map.md`](docs/map.md) is the constitution;
[`docs/decisions.md`](docs/decisions.md) is the append-only log of anything that crosses a
boundary.

## Running it

Tests, and the fastest way to see whether anything is broken:

```bash
dotnet test
```

The sandbox needs **Godot 4.7 .NET edition** ([godotengine.org](https://godotengine.org/download)
— the build labelled ".NET", not the plain one; `winget install GodotEngine.GodotEngine.Mono` on
Windows). Open `game/project.godot` in the editor and press F5, or from a shell:

```bash
dotnet build Hexcom.sln && godot --path game
```

Build first — Godot loads the C# assembly from `game/.godot/mono/temp/bin/`, and a scene launched
before it exists fails with a message about not being able to instantiate the script. If your
Godot is a different 4.x, change the `Godot.NET.Sdk` version in `game/Hexcom.Game.csproj` to
match.

To render a frame and write it to a file rather than watch it — useful in CI, and the only way an
automated session can check its own drawing:

```bash
godot --path game -- --shot out.png
```

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
| `B` | arm an ambush, or spring it on whoever is under the cursor |
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
one of yours to be; they stop moving when you do. A brighter, outlined wedge is an arc being held
— yellow for an overwatch, pink for an armed ambush — and the figure beside it in the turn order
is what that unit has banked to answer with.

Go prone and watch the visible area collapse. Pass a few turns and watch the order interleave
rather than alternate. Walk round behind a sentry's wedge and watch it stay unaware while the
same walk in front of it does not. The spotter on the roof sees most of the map and carries the
radio, so it is the one worth reaching first — and the ladder costs thirty of fifty points, so
whoever wants that position gives up their turn to take it.

You drive both sides, so the three reactions are all easy to try. The HUD reports which tick each
shot went off on and where the target was standing when it landed.

- **Overwatch** — give a sentry a narrow arc with `V`, end its turn, then run one of yours across
  it. Run the same route again with the arc set wide and watch the same weapon shoot worse.
- **Surprise** — walk one of yours across the front of a sentry that declared nothing. It answers
  anyway, out of half a bank and a beat late. Do it again with the same sentry and nothing
  happens: you cannot startle somebody twice with the same soldier.
- **Ambush** — press `B` on two or three of theirs in a row to arm them, then walk one of yours
  into the arc. All of them fire in one window, before you get to answer. Or hover a target and
  press `B` again with an armed unit active to spring it deliberately.

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
  from floor heights; ladders and stairs are authored. A stride costs five of fifty points, so
  ten hexes of open ground is a whole turn — and how you carry yourself is priced too: a crouch
  costs half again per hex and a crawl three times, so going flat buys its concealment with
  ground rather than for nothing.
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
  costs a fraction of a stride.
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
  gunner the other way round spend the same fifty points on very different turns, and gear that
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
- **Surprise** — the involuntary one, that nobody sets up and everybody has. It fires on the
  single moment a contact crosses into being noticed, so you cannot startle somebody who was
  already tracking you and a firefight does not generate one per move. Half the reserve, no
  aiming bonus, and it starts a beat after registering rather than at the top of the window —
  which is where "the weapon was already pointed" stops being a claim about overwatch and starts
  being arithmetic. Two bars, not one: something at the edge of what you can make out is enough
  to duck or spin round and nowhere near enough to shoot at, so a crawler at forty metres makes a
  sentry twitch without drawing fire. Behind is still behind.
- **Ambush** — a squad arms against an agreed arc and waits; when one of them says now, every
  armed member fires in the same window, before the target does anything about any of it. That is
  what makes an alpha strike survive interleaved initiative. Structurally it is a committed move
  of *zero* length — the same timeline, one instant — so the cheap shots still land before the
  expensive ones and a squad stops spending reserves on somebody already down. Springing calls
  the contact in first, so an ambusher has to be reachable by radio, shout or line of sight to
  join in, and one who got bored and spent its turn moving is still armed and out of the trap.

- **Judgement, in vitality** — every action a soldier could take is scored in the only currency
  that ends a fight: points of soldier. What a shot is worth is what gets through the shields and
  the plate it will actually meet, so a beam landing squarely on a full force shield reads as the
  nothing it is, and wearing eight points off a plate that never comes back reads as the progress
  it is. What a *posture* is worth is worked out by asking the ordinary questions twice, once
  about the soldier as they are and once about the soldier as they would be: turning earns its
  keep by buying a look rather than by presenting a better plate, going flat earns its keep by
  being harder to find as much as by being harder to hit, and diving behind a knee-high wall
  scores the shot it costs you as well as the shot it saves you. What calling a contact in is
  worth is whatever the people who can hear it could then do about it — nothing if they already
  knew, a great deal if one of them was a rung short of being allowed to fire down the arc they
  are already holding. Action points are priced in the same currency, which is what lets a cheap
  bad option be compared with an expensive good one at all.

  Nothing in it is a ladder. The old policy for picking a reaction was one — shoot if you can,
  otherwise turn, otherwise get low, otherwise call it in — and it could not tell a shot that
  would be soaked from one that would not, because it ranked shots on damage arriving rather than
  damage arriving anywhere. That is gone. The AI and the interface rank by the same call, and it
  returns its terms separately so a player can be told *why* rather than shown a number.

## What is not built yet

Grenades and mines, suppression, saves, and the strategy layer. See the design doc for where these
are heading.

The setting is science fiction — Star Trek, Star Wars, Babylon 5 in register.

The judgement is built; the thing that uses it on its own turn is not. A hostile unit ranks its
reactions properly and still does nothing whatever when its own turn comes round, so the sandbox
drives both sides by hand. What is missing is the search — over where a unit could go, what it
could shoot from there, and what it should hold back — with the same scorer at the bottom of it.
That, and the fact that firing gives you away and nothing prices that yet, is what stands between
here and a headless AI-versus-AI match.
