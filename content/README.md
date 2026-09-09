# Content — maps, and the `.hexmap` format

What is here:

```
maps/*.hexmap              the maps, as text
Hexcom.Content/            reads and writes that text; ships every map as an embedded resource
Hexcom.Content.Tests/      xUnit
```

`MapLibrary.Load("compound")` gives you a `BattleMap` from anywhere, with no working directory
to get right. `MapFile.Load(path)` reads a file; `MapFile.Parse(text)` reads a string;
`MapWriter.Write(map)` turns any `BattleMap` back into text, primitives only.

The rest of this file is the format. It is short because the format is: a map is the corner
graph written down, plus shorthand that expands to it.

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
used — the tests hold `DemoMaps.Compound()` and both shipped maps to this. It is how a map
built in code gets onto disk, and it is the proof that the shorthand adds convenience and
nothing else.
