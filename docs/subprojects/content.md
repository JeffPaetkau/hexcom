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

## Open questions

**How big is a hex, in metres?** Nothing states it. Tests use `new HexLayout(size: 1.0)`
throughout, which makes a hex 2 m across and 1.73 m between centres — small for a soldier to
occupy, and hard to square with an awareness model that talks about crawlers at forty metres and
shots heard at a hundred. Because `SightSolver` mixes layout units with metre heights in one
`Vec3`, this is not a free parameter: it sets the scale of cover, sight and detection together.
**This blocks the art spec**, which cannot size a model against an unknown hex. See
`../decisions.md` entry 002.

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
