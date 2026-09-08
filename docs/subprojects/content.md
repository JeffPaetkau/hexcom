# Content — maps, kit, and the tools to author them

Maps, missions, loadouts, unit rosters, and the balance values that make a soldier a scout rather
than a gunner. The territory with the least in it and the most to define.

Read [../map.md](../map.md) first.

## Owns

```
src/Hexcom.Core/Maps/DemoMaps.cs      content wearing a .cs extension
content/**                            when it exists
```

That is the whole of it today, and it is the point: **this territory's first job is to create its
own territory.** A map is currently C# built by hand against the corner graph. Level design is
not a thing anyone can do until there is a format and something to author it with.

## Must not touch

Everything else under `src/`, all of `tests/`, `game/`, and `docs/design.html`.

### The awkward case: balance numbers

The dials that make a scout a scout live inside Core's config records — `CostProfile`,
`AwarenessModel`, `GunneryModel`, `ReactionModel`, `StanceProfile`, `MovementCosts`,
`OverwatchArc`, `WeaponProfile`. Those are Core's files.

**The rule while that is true: Core owns the shape, and Core owns the file.** A content session
proposing a different value writes it up in `../decisions.md` with the argument, and Core makes
the edit. This is clumsy, and it is clumsy because the numbers are in the wrong place for the way
the project now works — which is itself an open question below.

## Depends on

- **The corner graph and wall chord model** — a wall joins any two corners of a hex; six sides,
  six minor chords, three bisectors, fifteen segments per hex. Any map format has to express
  that, not a tile grid.
- **Region partition and the transit rule** — a region below 60% of a hex is crossable but not
  standable. A map author needs to know this or they will author tiles nobody can stand in.
- **Authored versus generated links** — climbs, ledges and drops are generated from floor
  heights; ladders and stairs are authored. Only the second kind is a content decision.
- **`WallProfile` as data, not an enum** — deliberately, so content can add wall kinds without
  touching the rules. This is the one place the split already works as intended.

---

## The job — decide how big a hex is, then what a map file is

Branch `content/map-format`. Two pieces of work, in this order, because the first is small and
several other people are waiting on it.

### 1. ~~How big is a hex?~~ Settled: `size: 1.0`

Answered in `../decisions.md` entry 007 — 2.00 m corner to corner, 1.73 m between centres,
because a hex is one soldier's standing space and walls sit on its edges. Nothing had to move:
every test already used it. The art spec is unblocked.

**Read 007 before starting the map format, because it lands a requirement on it.** The figure
resolved the long-standing tension against the *map* rather than against the ranges: every range
in the game overshoots `DemoMaps.Compound` several times over, and a map on which they
discriminate is radius 20 to 30 — 70 to 105 m, some two thousand tiles. That is now a hard
constraint on part 2 rather than a nice-to-have.

### 2. What is a map file?

The territory's real founding act, and now the only thing in this brief. Today a map is C# built
by hand against the corner graph, and level design is not something a person can do.

**Size is the constraint that decides it.** Hand-authoring twenty tiles in C# is tedious; hand-
authoring two thousand is not a thing anybody will do, and entry 007 says two thousand is the
real target. Weigh both candidates below against that number, not against the demo map.

Two candidates, and the choice decides whether level design is a programming task forever:

- **Serialise the corner graph directly.** Honest, loses nothing, unpleasant to hand-author.
- **A friendlier authored form that compiles down to one.** Needs a compiler nobody has written,
  and every simplification risks making some legal map inexpressible.

Whichever way it goes, the format has to express the things Depends on lists above: chords rather
than tile edges, authored ladders and stairs as distinct from generated climbs and drops, and
`WallProfile` as open data rather than a closed enum. `DemoMaps.Compound()` is the test — if the
format cannot express the existing demo map, it is not finished.

Record the choice and the rejected alternative in `../decisions.md`.

---

## Open questions

**How big is a map?** Settled downwards from entry 007 rather than chosen: if the ranges are
right and the hex is one soldier wide, a map that lets a rifle's 55 m and a sentry's 45 m mean
anything is 70 to 105 m across — radius 20 to 30, one to three thousand tiles. Nothing that size
exists, and `DemoMaps.Compound` at radius 6 is a tenth of it. Whether that is one map size or a
range of them, and what a mission needs beyond ground, is open.

**What is a map file?** The two candidates: serialise the corner graph directly, which is honest
and unpleasant to hand-author; or a friendlier authored form that compiles down to one, which
needs a compiler nobody has written. The answer decides whether level design is a programming
task forever.

**Where do balance numbers live?** They are in Core config records, which was right when there
was one territory and is awkward now — see above. Moving values (not shapes) out to data would
give Content real ownership and make AI-vs-AI balance runs configurable without a rebuild. It
would also weaken the "seven homes" rule that currently keeps magic numbers out of method
bodies, so it is not obviously correct.

**Nothing has been measured.** Every number in the game is set by reasoning, because there is
nobody to play against yet. The AI is what turns these arguments into findings, so most balance
work is properly blocked on Core, not merely waiting for someone to do it.

## Recent work

```bash
git log --oneline -20 -- src/Hexcom.Core/Maps
```
