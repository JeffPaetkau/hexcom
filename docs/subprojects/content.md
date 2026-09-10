# Content — maps, kit, and the tools to author them

Maps, missions, loadouts, unit rosters, and the balance values that make a soldier a scout rather
than a gunner. The territory with the least in it and the most to define.

Read [../map.md](../map.md) first.

## Owns

```
content/maps/*.hexmap                 the ground, as text
content/missions/*.hexmission         who is standing on it and what they came to do
content/Hexcom.Content/               reads and writes both; ships every file by name
content/Hexcom.Content.Tests/         xUnit — this territory's tests live here, not in tests/
content/README.md                     the format reference, for whoever authors either
```

Both formats are in [`content/README.md`](../../content/README.md); the reasoning is
`docs/decisions.md` entries 024 and 046 and the `<remarks>` on `MapFile` and `MissionFile`. In one
sentence each: a map is the corner graph written down — `tile`, `chord`, `link` — plus shorthand
that expands to it; a mission names a map and adds the four things ground cannot carry — a
deployment with a facing, a named place, an objective, and a clock — plus the squads and a
six-part briefing. Both have a writer that lowers a file to primitives to prove the shorthand
adds nothing.

`MapLibrary.Load("compound")` and `MissionLibrary.Load("waystation")` are how anybody gets
either, from any working directory, because both are embedded in the assembly.
`Mission.Begin(seed)` hands back a battle deployed, ordered and started.

## Must not touch

All of `src/`, all of `tests/`, `game/`, and `docs/design.html`. The one carve-out this territory
used to have — `src/Hexcom.Core/Maps/DemoMaps.cs`, content wearing a `.cs` extension — is gone,
because the file is (entry 043).

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

A mission file sits on the other side of the same line and shows where it currently is. It
**names** a role and a kit — `role scout`, `kit infiltrator` — and cannot declare either, because
a file that could write out its own action points and plate would be the balance change. So the
composition is content and the numbers are not, which is exactly the split `profile` makes for a
wall except that nobody has yet written the mission-file equivalent of `profile`.

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
- **`Objective` as a polymorphic strategy** — `Battle.SetObjective` before `Start`,
  `Withdrawal(side, exits, unnoticed)` over a collection of nodes, `Battle.Extract()` as the free
  turn action, and `Battle.VerdictFor(side)` for how it came out. Entry 041. A mission file's
  `objective` statement lowers to one of these, and a new shape in Core is a new
  `ObjectiveOrder` here and no change to the grammar.
- **`Unit.Left`** — a `Departure` saying whether a soldier walked off or was put down, and what
  the other side held on them as they went. It is what lets the harness tell a mission achieved
  from a squad wiped out, which before objectives were the same state.

---

## The job — a second battlefield, of a different shape

Branch `content/second-battlefield`. Row 6 of entry 045's road, and the last thing Content owes
the greybox. The waystation has been fought over twice now — once with nothing to want (entry 038)
and once from a mission file (entry 047) — and both times on one shape of ground. A second map,
so that the mission format is argued from two shapes rather than one, and the *one size or a
range* question below gets a second data point.

**Where the seam is.** `content/README.md` is both formats. `waystation.hexmap` is the worked
example, forty-five statements of ground; `waystation.hexmission` is the mission on it, and
`content/Hexcom.Content.Tests/Waystation` is the harness — `WaystationFight` is now a name and one
call, `MatchRecorder` runs `Commander` against itself and writes down routes, throws, casualties,
alarm peaks, departures, verdict and pacing, and `HEXCOM_SEEDS`, `HEXCOM_SEED_FROM`,
`HEXCOM_ROUNDS` and `HEXCOM_TRANSCRIPT` steer it. Copy the shape for the new map; the recorder is
not waystation-specific except for its landmarks, which want generalising now that a second map
needs them — and a `place` in a mission file is most of what a landmark is.

**What to draw.** The waystation is open ground with things on it, and the mission book's six
shapes want the other kind too: somewhere built-up and tight, where sight lines are short, every
wall is a building face, and the way in that is not the way everybody uses is a roof or a duct
rather than a ford. Radius 12 to 16 rather than 24 — that is the size question being asked on
purpose, since entry 007's figure was reasoned from the ranges and a town blocks the ranges.
Reuse the built-in profiles; if it needs a new one, remember entry 035 — a map that brings its
own kit brings no colour with it, and the view wants a line in `../decisions.md`.

**Give it a mission file of its own**, not a header. That is what the format is for now, and the
new map is the second data point on whether it is the right shape. Watch for what the waystation
could not test: a `place` that is a building interior rather than three hexes of floor, an exit
that is upstairs, a deployment that has to name a layer. If any of those is awkward, that is a
finding about the format and it is yours to fix.

**Fight it before calling it done.** A dozen seeds through the harness, and read the routes the
way entry 038 did. Expect entry 047 — a squad told to leave leaves, immediately, because the task
half of a mission is not in the rules — and **do not draw around it**. It is Core's, a map cannot
fix a search, and a second map that hides it would cost the measurement. Setting the exit
somewhere the squad has to cross the map to reach would be exactly that mistake. Do redraw around
anything that is the map's: a firing lane where a street was meant, a crossing nobody uses
because there is an easier one.

**Settle before drawing much.** Whether the compound goes. It is the demo map, radius 6,
everything in earshot of everything (entry 030), and `DemoMaps.cs` is gone (entry 043). A second
map at the right size that carries a mission would make the compound the third map and the only
one too small to fight on. Do not delete it — the view's captures diff against it — but say in
`../decisions.md` whether it is a map or a fixture.

**Out of scope.** New objective kinds and the missing task term (entry 047) are Core's. Anything
in `game/`: the sandbox reads whatever `SandboxScenario` names, and pointing it at the mission
file is View's, raised in entry 046.

**How to know it worked.** A second `.hexmap` and a second `.hexmission`, a harness that fights
it to a verdict, a note in `../decisions.md` on what its size did to the ranges that the
waystation's did not, and the *one size or a range* question below either answered or sharpened.

---

## Open questions

**How big is a map?** Entry 007 settled the *scale*: radius 20 to 30, 70 to 105 m, one to three
thousand tiles, if the ranges are right. The waystation is radius 24 and the format takes it in
under fifty statements, so size is no longer a cost, and it has now been fought on (entry 038):
at that size a rifle engages at 35 to 38 m before anybody on the other side is past `Unaware`,
a firefight at the gate is silent in the barn 24 m away (entry 037), and the far half of the map
is never visited because nothing sends anybody there. What is still open is whether that is one
map size or a range of them — the brief above asks for a tight one on purpose. What a mission
needs beyond ground is no longer open: entry 030 answered it in prose and
`waystation.hexmission` holds it.

**~~What is a scenario file?~~** Answered: a file of its own that names a map, `.hexmission`,
entry 046. What is still open is the two things it deliberately does not do. It **names** roles
and kits and cannot declare them, which is the balance-numbers question below wearing a different
hat. And it carries a round limit that no rule reads, because the clock of entry 030 is still
nobody's — so the file states the mission's own answer to *when it stops* and whatever runs the
battle applies it.

**A map editor.** Text is enough to author with and it is not enough to *see* with: the
waystation was checked by rendering it as characters. Whether the sandbox grows a map view, or
an editor is a tool of its own, is a question for after the greybox (build order 06) changes
what the view is.

**Where do balance numbers live?** They are in Core config records, which was right when there
was one territory and is awkward now — see above. Moving values (not shapes) out to data would
give Content real ownership and make AI-vs-AI balance runs configurable without a rebuild. It
would also weaken the nine-homes rule (entry 032) that currently keeps magic numbers out of
method bodies, so it is not obviously correct. Both formats show the shape the answer would take:
`profile` and `ground` are content declaring kit against a shape Core owns, and `role` and `kit`
in a mission are content *naming* one where declaring it would be the balance change.

**Almost nothing has been measured, and here is what has.** Every number in the game was set by
reasoning; the waystation harness is the first thing to check any of them against a match, and
what it found is in entries 037 to 039 and 047: a rifle is heard at 18 m against a design that
says a hundred, a turn's walk on gravel is heard further than a shot, the AI throws every charge
at the first crater and paces between two tiles on a shot it never takes, and a squad told to
leave leaves in round 2 without doing what it came for. The one thing that has been measured
*right* is that an objective ends a battle: twelve matches out of twelve, where twelve out of
twelve used to run out of rounds. A dozen seeds is two seconds now rather than nine minutes,
which makes the harness cheap enough to be the first thing anybody with a number to test
reaches for.

## Recent work

```bash
git log --oneline -20 -- content
```
