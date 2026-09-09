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

## The job — a second battlefield, of a different shape

Branch `content/second-battlefield`. The waystation has been fought over (entry 038) and the
mission file waits on Core saying what an objective is (entry 036, row 5). What Content can do
without waiting is the thing the mission file will need when it comes: a second map, so that
the file is argued from two shapes rather than one, and the *one size or a range* question
below gets a second data point.

**Where the seam is.** `content/README.md` is the format; `waystation.hexmap` is the worked
example, forty-five statements plus a header that carries a mission in the mission book's six parts.
`content/Hexcom.Content.Tests/Waystation` is the harness: `WaystationFight` deploys, `MatchRecorder`
runs `Commander` against itself and writes down routes, throws, casualties, alarm peaks and
pacing, and `HEXCOM_SEEDS`, `HEXCOM_SEED_FROM`, `HEXCOM_ROUNDS` and `HEXCOM_TRANSCRIPT` steer it.
Copy the shape for the new map; the recorder is not waystation-specific except for its
landmarks, which want generalising when a second map needs them.

**What to draw.** The waystation is open ground with things on it, and the mission book's six
shapes want the other kind too: somewhere built-up and tight, where sight lines are short,
every wall is a building face, and the way in that is not the way everybody uses is a roof or a
duct rather than a ford. Radius 12 to 16 rather than 24 — that is the size question being asked
on purpose, since entry 007's figure was reasoned from the ranges and a town blocks the ranges.
Give it the four things a mission needs in its header, the way the waystation has them. Reuse
the built-in profiles; if it needs a new one, remember entry 035 — a map that brings its own
kit brings no colour with it, and the view wants a line in `../decisions.md`.

**Fight it before calling it done.** A dozen seeds through the harness, and read the routes
the way entry 038 did. Expect the same two findings — nothing decided, the tower-and-barn
stillness wherever a soldier starts out of view — and do not redraw around them, because they
are Core's (entries 038 and 039) and a map cannot fix a search. Do redraw around anything that
is the map's: a firing lane where a street was meant, a crossing nobody uses because there is an
easier one.

**Settle before drawing much.** Whether the compound goes. It is the demo map, radius 6,
everything in earshot of everything (entry 030), and `DemoMaps.cs` still mirrors it for Core's
tests (entry 024). A second map at the right size that carries the withdrawal mission would make
the compound the third map and the only one too small to fight on. Do not delete it — the view's
captures diff against it — but say in `../decisions.md` whether it is a map or a fixture.

**Out of scope.** The mission file itself, until 05b. Balance findings that need a match to end
— there is no ending yet. Anything in `game/`: the sandbox opens whatever `SandboxScenario` names,
and offering it the new map is an entry for View, with the deployments written out the way
entry 038 wrote the waystation's.

**How to know it worked.** A second `.hexmap` with a mission header, a harness that fights it,
a note in `../decisions.md` on what its size did to the ranges that the waystation's did not,
and the *one size or a range* question below either answered or sharpened.

---

## Open questions

**How big is a map?** Entry 007 settled the *scale*: radius 20 to 30, 70 to 105 m, one to three
thousand tiles, if the ranges are right. The waystation is radius 24 and the format takes it in
under fifty statements, so size is no longer a cost, and it has now been fought on (entry 038):
at that size a rifle engages at 35 to 38 m before anybody on the other side is past `Unaware`,
a firefight at the gate is silent in the barn 24 m away (entry 037), and the far half of the map
is never visited because nothing sends anybody there. What is still open is whether that is one
map size or a range of them — the brief above asks for a tight one on purpose — and what a
mission needs beyond ground, which entry 030 has answered in prose and no file yet holds.

**What is a scenario file?** The map format deliberately holds ground and walls and nothing
else. Who starts where, facing which way, with what, and what winning means are not in it, and
today they are hard-coded in `game/scripts/SandboxScenario.cs` — content wearing a view
extension, as `view.md` puts it. A deployment block in the map file, a separate scenario file
that names a map, or something the campaign layer owns are all plausible. The campaign shape is
settled — a thin frame, entry 027 — and the fiction's answer to what a mission needs is entry
030; what is still missing is what an objective *is* in the rules, which is Core's build order
05b. The file is written after that, not before.

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

**Almost nothing has been measured, and here is what has.** Every number in the game was set by
reasoning; the waystation harness is the first thing to check any of them against a match, and
what it found is in entries 037 to 039: a rifle is heard at 18 m against a design that says a
hundred, a turn's walk on gravel is heard further than a shot, no match ends, the AI throws
every charge at the first crater and paces between two tiles on a shot it never takes. Nothing
was measured to be *right* yet, which is the more interesting half and needs a match that can
end. A dozen seeds is nine minutes; the harness is there for whoever has a number to test.

## Recent work

```bash
git log --oneline -20 -- content src/Hexcom.Core/Maps/DemoMaps.cs
```
