# Content — the `.hexmap` and `.hexmission` formats

What is here:

```
maps/*.hexmap              the ground, as text
missions/*.hexmission      who is standing on it and what they came to do
Hexcom.Content/            reads and writes both; ships every file as an embedded resource
Hexcom.Content.Tests/      xUnit
```

`MapLibrary.Load("compound")` gives you a `BattleMap` from anywhere, with no working directory
to get right, and `MissionLibrary.Load("waystation")` gives you a `Mission`. `MapFile.Load(path)`
reads a file; `MapFile.Parse(text)` reads a string; `MapWriter.Write(map)` turns any `BattleMap`
back into text, primitives only. `MissionFile` and `MissionWriter` are the same three for a
mission, and `Mission.Begin(seed)` hands back a battle deployed, ordered and started.

Most of this file is the map format. It is short because the format is: a map is the corner
graph written down, plus shorthand that expands to it. The mission format is at the end.

## The shape of a file

One statement per line. `#` starts a comment. Blank lines are ignored. Keywords are lowercase.
Numbers use a dot for the decimal point.

```
# The compound
map Compound

fill disc 0,0 r 6 floor

wall solid line 2,-3 to 2,2 nw sw
breach 2,0 sw

fill hexes 4,-1 4,0 4,1 5,-1 5,0 layer 1 h 3.5
ladder 4,0@0 4,0@1
```

That is most of `maps/compound.hexmap`, and it is the whole of the demo map that used to be
ninety lines of C#.

**Order matters twice.** Declarations — `profile`, `ground`, `occupancy`, `layer-height` —
have to come before the first tile, wall or link. And later statements act on what earlier
ones built: a second `fill` paints over the first, and `breach` removes a wall that has to be
there already.

## Naming things

| | written as | meaning |
|---|---|---|
| a hex | `q,r` | axial coordinates, flat-top, the way every test and `DemoMaps` names them |
| a tile | `q,r@layer` or `q,r` | a hex at a storey; layer 0 when the `@` is left off |
| a side | `ne` `n` `nw` `sw` `s` `se` | the six faces of a hex, and `all` for every one |
| a corner pair | `0-2` | two of the six corners, 0 due east and counting counter-clockwise |
| a shape | see below | a set of hexes |

A hex's corners and sides are indexed the same way `Hex.Corner` and `HexDirection` are: side
`i` is bounded by corners `i` and `i+1`, so `ne` is the side from corner 0 to corner 1. Corner
pairs one apart are sides, two apart clip a sixth off the hex, three apart cut it in half —
and the rules say a half is somewhere you can cross but not stand. Fifteen pairs per hex, and
that is the entire cover vocabulary.

### Shapes

| | |
|---|---|
| `hex q,r` | one hex |
| `hexes q,r q,r ...` | a list |
| `line q,r to q,r` | every hex on the straight line between two, inclusive |
| `disc q,r r N` | every hex within N steps of a centre |
| `ring q,r r N` | every hex exactly N steps from a centre |

## Statements

### Ground

```
tile q,r@L [h metres] [ground]
fill <shape> [layer L] [h metres] [ground]
```

`tile` is the primitive: one hex at one layer. `fill` is the same thing for every hex in a
shape. Both *paint*: anything not mentioned is kept if the tile already exists, so
`fill hex 3,4 rubble` changes the ground and leaves the height alone. A new tile with no `h`
sits at `layer × layer-height`, which is 0 on the ground.

Built-in grounds: `floor` `grass` `gravel` `rubble` `mud` `shallow_water` `void`.

### Walls

```
chord <profile> q,r@L a-b
wall  <profile> <shape> <side...> [layer L]
enclose <profile> <shape> [layer L]
breach q,r@L <side or a-b ...>
```

`chord` is the primitive: a wall between two corners of one hex. Since a side is the chord
between adjacent corners, every wall in the game is a `chord` of some hex. The others are
loops over it:

- `wall` puts the named sides on every hex in the shape. `wall solid line 2,-3 to 2,2 nw sw`
  is a straight wall — which on a hex grid is a zigzag, each hex contributing two faces.
- `enclose` walls every side of the shape that faces *out* of it. A building is one line.
- `breach` removes walls. It is an error if there is nothing there to remove, because that is
  almost always a typo in the coordinate.

Built-in profiles: `low` `high` `solid` `railing` `screen`. A side is one wall shared by the
two hexes on either side of it, so naming it through either hex finds the same wall.

### Links

```
link <kind> from to [cost N] [one-way] [regions a b]
ladder from to
stairs from to
door   from to
```

The connections the rules cannot work out from the floor heights: climbs, ledges and drops
are generated, these are authored. `kind` is any `TraversalKind` — `walk` `rough` `vault`
`climb` `ladder` `stairs` `drop` `jump` `door` `crawl`. Cost defaults to the price list for
that kind. `regions` names which region of a divided hex each end is in; you will almost never
need it.

### Declaring kit

```
profile <id> height metres cover none|light|half|full [blocks|passable] [opaque|clear] [vault|novault] [climb|noclimb] [destructible|permanent]
ground  <id> [cost N] [noise factor] [impassable]
```

`WallProfile` and `GroundType` are open data rather than enums precisely so a map can bring
its own. Defaults are `blocks opaque novault noclimb permanent` and `cost 0 noise 1.0`. The
built-in names cannot be redefined; balance changes to those go through Core, as
`docs/subprojects/content.md` says.

### Settings

```
map <name>
occupancy 0.6
layer-height 3.0
```

The `BattleMap` init properties. Leave them alone unless you know why the transit rule sits at
60%.

## Errors

Every refusal names the file and the line, `test.hexmap:14: Unknown wall profile 'hegde'.
Known: high, low, railing, screen, solid.` Two chords crossing inside one hex — which the
partition rejects — are caught when the file is read rather than when the movement graph is
first built, and blamed on the last line that put a chord in that hex.

## Lowering

`MapWriter.Write` emits only `tile`, `chord` and `link` lines, plus declarations for any kit
the map brought with it. Reading that back gives the same map, whatever shorthand the original
used — the tests hold both shipped maps to this. It is how a map built in code gets onto disk,
and it is the proof that the shorthand adds convenience and nothing else.

---

# Missions

A map holds ground and nothing else, deliberately. The four things a mission needs that ground
cannot carry — where each side starts *with facing*, a named place to end at, the thing to do,
and when it stops — live in a `.hexmission` file that names a map.

## Why a separate file and not a block in the map

Three reasons, and the first is the one that decided it.

**One battlefield carries several missions.** The waystation is a crossroads, and the mission
book lists six shapes that could all be fought over it. A block in the map file means either one
map to one mission, or several mission blocks inside a file that is otherwise entirely about
ground — and the second is a separate file with extra steps.

**A map with no mission has to stay legal.** `compound.hexmap` has none and never will: it is
the fixture the view diffs its captures against. If the mission lived in the map, every map
without one would be a map with something missing.

**Ground outlives missions.** A map is drawn once and edited rarely. A mission is per-run and, in
a campaign, generated. Keeping them in one file would put a stable thing and a disposable one
behind the same round trip.

What is shared is the *lexer*, not the reader: one statement per line, `#` to end of line,
`q,r` and `q,r@layer`, `ne n nw sw s se`, and errors that name the file and the line. Two readers
over one tokeniser, because a person carries those conventions from one file to the other and
would be furious to find them subtly different.

## The shape of a file

```
mission Instrument 4-11: the waystation
map waystation
rounds 30
```

`map` is required and names a `.hexmap` by library name. `mission` is the title, and falls back
to the file name.

## The clock

```
rounds 30
rounds after-alarm 3
rounds 30 after-alarm 3
```

When the mission stops. A number is the last round it runs to; `after-alarm N` is how many rounds
it outlives the alarm going out — the first moment somebody with a set passes on a contact at
Alerted. Whichever comes first wins, and a squad still on the field after it has *abandoned* the
mission rather than failed it. Both halves go on one line, because they are one clock.

It is written onto every objective the file builds, as `Objective.Stop` — entry 082 put the clock
on the objective rather than the battle, since the same ground carries a different hour under a
different briefing.

## The briefing

```
brief instrument  Instrument 4-11 continues in force and this is an inspection of the waystation
brief instrument  on the north road, filed accordingly. A walk.
brief task        Enter the compound, confirm what is stored in the house, and come out.
```

Six parts, all required: `instrument`, `presence`, `task`, `restraint`, `way-off`, `stop`. They
are the six of [`docs/setting/missions.md`](../docs/setting/missions.md), and requiring all of
them is the point — this file exists because the same mission was written down three times and
what let the copies drift was that none of them had to be complete.

Repeating a part adds a line to it, which is how prose wraps without a continuation character.

## Named ground

```
place cottages hexes -14,6 -14,7 -13,6
place yard disc 0,0 r 4
place roof hex 0,1 layer 1
```

Any shape the map format knows, plus an optional `layer`. A place is authored as tiles and used
as *nodes*: when something asks which of them a soldier could stand in, the movement graph
answers, so a hex cut by a chord contributes the half anybody can stop in and not the offcut.

Places are named rather than numbered because a briefing has to be able to say one.

## Deployments

```
deploy Vance  player -21,3  facing se role scout   kit infiltrator
deploy Teague hostile 0,1@1 facing nw role signaller kit beamer
deploy Bekker player -19,-3 facing ne              kit rifleman
```

`deploy <name> <side> <tile>`, then any of `facing`, `role` and `kit`. Sides are `player`,
`hostile` and `neutral`. Facing defaults to `ne` and is never decoration: a soldier's front cone
reads at acuity 1.0 and the corner of his eye at 0.45, so a garrison deployed facing the wrong
way has made a decision on the player's behalf.

Roles name a `UnitStats` preset — `scout`, `trooper`, `signaller`, or omitted for the default
soldier. Kits name a `Loadout` — `rifleman`, `beamer`, `heavy`, `infiltrator`, `sidearm`.

**Both are named, never declared.** A file that could write out its own action points, shields
and plate would be a balance change hiding in content, which is the same line that lets a map
declare a hedge but not redefine what `low` means. Whether that line is in the right place is an
open question in [`../docs/subprojects/content.md`](../docs/subprojects/content.md).

## What a side is told

```
told player searching  Cobb Teague Marek
told player suspicious Hollis
```

`told <side> <rung> <name...>` — the side that is told, how firmly, and who about, by deployed
name. Each becomes a marker in every contact file on that side before the first turn, at the post
the soldier is really standing on, through `Battle.Brief`. It decays like any other contact the
moment somebody looks and does not find him: a briefing is trusted until the ground says
otherwise.

This is the presence part of the briefing handed to the rules, and without it a squad plays blind
— entry 087 watched the scout walk its first turn into the view of a sentry the prose describes.
The briefing names **posts** and this names **people**, for the same reason `deploy` does: a
marker has to be on somebody.

- **One line per rung**, because that is how a briefing states its certainty: three posts stated
  flat, and the fourth the reports disagree about.
- **A post not told is not known.** That is how a file says the reports missed somebody. It cannot
  say somebody is where he is not, because a marker is put where the soldier stands — being wrong
  about a post would be a different mission.
- **A soldier is deployed before anybody is told about him**, and a side is told about the other
  side. `unaware` is refused: telling a side nothing is leaving the name off.

It is a statement of its own rather than an option on `deploy` because a deployment is a fact
about the garrison and this is a belief the squad holds; putting it on the garrison's line would
put both sides' knowledge in one statement, and would have to guess which side is told once there
are three.

## Objectives

```
objective reconnaissance player at house exit cottages unnoticed suspicious
```

`objective <shape> <side>`, then options belonging to the shape. One per side, and a side with
none behaves as it always did.

All six shapes of the mission book are names the grammar knows — `withdrawal`,
`reconnaissance`, `sabotage`, `extraction`, `denial`, `capture` — and three of them can be built,
because three of them are what the rules have. The other three are refused with a message saying
so rather than as a misspelling, which is a true and useful thing to be told.

The three that build are one shape with different things in the middle of it, so they share two
options and spell them the same way:

| | |
|---|---|
| `exit <place>` | where this side may walk off the field. Required, in all three |
| `unnoticed <rung>` | the highest rung any enemy may hold on a departing soldier and still have it count |

Rungs are `unaware`, `suspicious`, `searching`, `alerted`, `engaged`; the default is
`suspicious`, which is a dog barking rather than a sentry walking towards where he thinks you
were.

Then each shape adds its own:

| | |
|---|---|
| `withdrawal` | nothing. Be there, leave, and be nobody's problem |
| `reconnaissance` | `at <place>`, required, and `within <metres>` — how close the look has to be taken from |
| `sabotage` | `at <place>`, required, and `effort <points>` — action points the job takes, from however many soldiers |

**An exit is a place and the thing in the middle is a point.** Any node in the exit will do, so
`exit` keeps all of them; a look is a line traced to one node, so `at` takes the place's *middle*
— the node with the least total distance to the rest of it. That is the room rather than the
doorway, and it is the same answer whichever order the file listed the ground in. It also means a
place nobody can stand in cannot be looked at, which is a real limit: a sealed vault is a fair
thing to photograph and this cannot yet name one.

**`within` and `effort` are the two silences the writer leaves alone.** Everywhere else a default
is the format's and gets spelled out when lowered. These two belong to the rules, on
`Reconnaissance` and `Sabotage`, and a file that omits one inherits it rather than copying it —
so the writer prints nothing rather than a second home for a balance number.

## Lowering

`MissionWriter.Write` spells everything out: every place an explicit list of tiles, every facing,
role, kit and threshold, and one `told` line per soldier. There are only two pieces of shorthand in
the format — `place` takes the map's shapes and `told` takes several names — so the claim this proves is mostly about the *defaults*, which are the part of any
format that quietly stops meaning what the reader thinks. The two exceptions are `within` and
`effort`, for the reason given above: they are the rules' defaults, not the format's.
