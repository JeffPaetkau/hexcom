# Content — maps, kit, and the tools to author them

Maps, missions, loadouts, unit rosters, and the balance values that make a soldier a scout rather
than a gunner. The territory with the least in it and the most to define.

Read [../map.md](../map.md) first.

## Owns

```
content/maps/*.hexmap                 the maps, as text
content/Hexcom.Content/               reads and writes that text; ships every map by name
content/Hexcom.Content.Tests/         xUnit — this territory's tests live here, not in tests/
content/README.md                     the format reference, for whoever authors a map
src/Hexcom.Core/Maps/DemoMaps.cs      content wearing a .cs extension, kept until nobody calls it
```

The format itself is in [`content/README.md`](../../content/README.md); the reasoning for it is
`docs/decisions.md` entry 024 and the `<remarks>` on `MapFile`. In one sentence: a map is the
corner graph written down — `tile`, `chord`, `link` — plus shorthand that expands to it, and
`MapWriter` can lower any map back to the primitives to prove the shorthand adds nothing.

`MapLibrary.Load("compound")` is how anybody gets a map. It works from any working directory
because the maps are embedded in the assembly, and the test that holds it identical to
`DemoMaps.Compound()` is what lets the two coexist.

## Must not touch

Everything else under `src/`, all of `tests/`, `game/`, and `docs/design.html`.

`Hexcom.sln` is shared, like `README.md`: this territory added its two projects to it and
touches nothing else in it.

### The awkward case: balance numbers

The dials that make a scout a scout live inside Core's config records — `CostProfile`,
`AwarenessModel`, `GunneryModel`, `ReactionModel`, `StanceProfile`, `MovementCosts`,
`OverwatchArc`, `WeaponProfile`. Those are Core's files.

**The rule while that is true: Core owns the shape, and Core owns the file.** A content session
proposing a different value writes it up in `../decisions.md` with the argument, and Core makes
the edit. This is clumsy, and it is clumsy because the numbers are in the wrong place for the way
the project now works — which is itself an open question below.

The one exception already works the way the rest should: `WallProfile` and `GroundType` are
open data, and a map file declares its own with `profile` and `ground`. The built-in five and
seven cannot be redefined from a file, deliberately — that would be a balance change hiding in
content.

## Depends on

- **The corner graph and wall chord model** — a wall joins any two corners of a hex; six sides,
  six minor chords, three bisectors, fifteen segments per hex. The `chord` statement is exactly
  that, which is why it is the primitive and `wall` is sugar over it.
- **Region partition and the transit rule** — a region below 60% of a hex is crossable but not
  standable. A bisector (`chord low 0,-3 0-3`) makes a tile nobody can stop in; the reader
  checks every tile's partition when it finishes so that two chords crossing inside one hex are
  refused at the line rather than when the graph is first built.
- **Authored versus generated links** — climbs, ledges and drops are generated from floor
  heights; ladders, stairs, doors and crawls are authored with `link` and its three shorthands.
  Only the second kind is a content decision, and only the second kind is in the file.
- **`WallProfile` as data, not an enum** — the reason `profile hedge ...` is a line in a map
  rather than a pull request against the rules.

---

## The job — a battlefield to fight over, and the numbers it tests

Branch `content/first-battlefield`. The format exists and the first map at the right size exists;
neither has had a shot fired on it. This job is the first use of both.

**Where the seam is.** `content/maps/waystation.hexmap` is radius 24 — 85 m across, 1801 ground
tiles — which is the size entry 007 asked for so that a rifle's 55 m and a sentry's 45 m have
room to differ. It was drawn to show the format scales, not to be fought over, and it shows: a
crossroads with a compound, a barn, cottages, a ridge, a tower and two woods, laid out by
eye. `Commander` (entry 009) drives both sides headless, and `tests/` already shows the shape of
a skirmish test on a disc. Nothing has ever been run on ground with buildings in it.

**What to do.**

1. **Give the waystation a reason.** Two deployments and an objective, in prose in the file's
   header for now — where each side starts, which way they face, what they are there for. A
   scenario format is an open question below and is *not* this job; the sandbox hard-codes five
   deployments and `view.md` says so. Argue for the rewrite when there is a second map that
   needs it.
2. **Run the AI over it, and look at the routes.** Both sides `Commander`, a dozen seeds. The
   thing to read off is not who wins but *where the fighting happens*: whether anybody uses the
   drain, whether the ridge is worth the climb, whether the woods hide anything at 45 m. A
   headless match is a second or two on a radius-16 disc (`core.md`); measure it here, because
   this is five times the ground and the search is over reachable sets. If it is unusable that
   is an entry for Core, with the number.
3. **Redraw the map from what the routes say.** This is the level design the format was built to
   make possible. The map is forty statements; changing it is meant to be cheaper than arguing
   about it.
4. **Then, and only then, write down the first balance findings** — as entries in
   `../decisions.md`, one number each, with the match that showed it. Every figure in the game is
   an argument rather than a measurement; this is the first place a measurement can come from,
   and the whole of the balance-numbers question below turns on there being some.

**Decide before writing much:** what a match on this map *ends* on. The rules end when one side is
down, which on 85 m of ground with an AI that only fights what it can see may take a very long
time or never. A turn cap is the obvious answer and it is a balance number, so if you need one it
goes in `../decisions.md` for Core, not in a test.

**Out of scope.** Loading the map in the sandbox is View's (entry 024 offers it); deleting
`DemoMaps.cs` waits on Core's tests not calling it (same entry); a deployment format is open
below.

**How to know it worked.** A map file with a header that says what the fight is, a test that runs
a match on it to a decision, and at least one entry in `../decisions.md` that says a number was
*measured* to be wrong — or measured to be right, which counts.

---

## Open questions

**How big is a map?** Entry 007 settled the *scale*: radius 20 to 30, 70 to 105 m, one to three
thousand tiles, if the ranges are right. The waystation is radius 24 and the format takes it in
forty statements, so size is no longer a cost. What is still open is whether that is one map size or
a range of them, and what a mission needs beyond ground — deployment zones, objectives, an edge
to leave by. Nothing has been played at this size.

**What is a scenario file?** The map format deliberately holds ground and walls and nothing
else. Who starts where, facing which way, with what, and what winning means are not in it, and
today they are hard-coded in `game/scripts/HexSandbox.cs` — content wearing a view extension,
as `view.md` puts it. A deployment block in the map file, a separate scenario file that names a
map, or something the campaign layer owns are all plausible; the answer depends on the campaign
shape, which is Setting's to decide first.

**A map editor.** Text is enough to author with and it is not enough to *see* with: the
waystation was checked by rendering it as characters. Whether the sandbox grows a map view, or
an editor is a tool of its own, is a question for after the greybox (build order 06) changes
what the view is.

**Where do balance numbers live?** They are in Core config records, which was right when there
was one territory and is awkward now — see above. Moving values (not shapes) out to data would
give Content real ownership and make AI-vs-AI balance runs configurable without a rebuild. It
would also weaken the "eight homes" rule that currently keeps magic numbers out of method
bodies, so it is not obviously correct. The map format shows the shape the answer would take:
`profile` and `ground` are content declaring kit against a shape Core owns.

**Nothing has been measured.** Every number in the game is set by reasoning, because there is
nobody to play against yet. The AI is what turns these arguments into findings, and the job
above is the first time it is pointed at ground this territory drew.

## Recent work

```bash
git log --oneline -20 -- content src/Hexcom.Core/Maps/DemoMaps.cs
```
