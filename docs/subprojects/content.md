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
`docs/decisions.md` entries 024 and 047 and the `<remarks>` on `MapFile` and `MissionFile`. In one
sentence each: a map is the corner graph written down — `tile`, `chord`, `link` — plus shorthand
that expands to it; a mission names a map and adds the four things ground cannot carry — a
deployment with a facing, a named place, an objective, and a clock — plus the squads, what each
side is told about the other, and a six-part briefing. Both have a writer that lowers a file to
primitives to prove the shorthand adds nothing.

`MapLibrary.Load("kestrel")` and `MissionLibrary.Load("waystation")` are how anybody gets
either, from any working directory, because both are embedded in the assembly.
`Mission.Begin(seed)` hands back a battle deployed, briefed, ordered and started.

Three maps. **The waystation** (radius 24, open country at a crossroads) and **Kestrel Yard**
(radius 14, a freight yard in a works town) each carry a reconnaissance. **The compound** is a
fixture: too small to fight on, and the ground Core's sight tests and View's captures are built on.

Two harnesses, one shape: `content/Hexcom.Content.Tests/Waystation` and `.../Kestrel`, each a
`*Fight` class that names the mission and the ground its places do not, `*FightTests` driven by
`HEXCOM_SEEDS`, `HEXCOM_SEED_FROM`, `HEXCOM_ROUNDS` and `HEXCOM_TRANSCRIPT`, and `*GroundTests`
measuring the map against its own briefing. `MatchRecorder` is shared and reads a mission's
places as landmarks; `MapSketch` draws any map in characters, a storey at a time.

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
  `Battle.Extract()` as the free turn action, and `Battle.VerdictFor(side)` for how it came out.
  Entry 041. A mission file's `objective` statement lowers to one of these, and a new shape in
  Core is a new `ObjectiveOrder` here and no change to the grammar.
- **`Sortie` as the shape all three buildable objectives share** — go out, do something, come
  back, with the task and the walking priced in one currency. `Withdrawal(side, exits,
  unnoticed)`, `Reconnaissance(side, place, exits, within, unnoticed)` and `Sabotage(side, place,
  exits, effort, unnoticed)`. Entry 061. The exit is a collection of nodes and the place is one
  node, which is why the grammar's `exit` keeps a whole place and its `at` takes the middle of
  one — entry 081.
- **`Battle.Brief(side, unit, rung)`** — a marker on an enemy at his post, before `Start`. What a
  `told` line lowers to. Entry 087.
- **`Objective.Stop`, a `Deadline(Round, AfterAlarm)`** — the clock, on the objective rather than
  the battle. What a `rounds` line lowers to. Entry 082.
- **`Unit.Left`** — a `Departure` saying whether a soldier walked off or was put down, and what
  the other side held on them as they went. It is what lets the harness tell a mission achieved
  from a squad wiped out, which before objectives were the same state.

---

## The job — a sabotage, and the one number in the mission book worth arguing

Branch `content/sabotage`. Both missions in the library are reconnaissances, on purpose: the second
map was argued against the first with the objective held still. The rules have three shapes and
the library uses one. `Sabotage(side, place, exits, effort, unnoticed)` is built (entry 061), the
grammar reads it (`objective sabotage ... effort N`), and no file says it.

**Read the mission book's section 5 first** (`docs/setting/missions.md`). Two sentences in it are
the brief. *The price is paid in turns and not in an action*, and *the figure itself is Content's,
and it is the one number in this book worth arguing about, because a sabotage that can be done in
a single turn is a door and not a mission.* The effort is the only balance-shaped number a mission
file writes, and nobody has measured one.

**Then entry 092**, which is what fighting the second map found. Three things from it bear on
this: the look is taken every match on both maps and nothing is achieved on either, and the reason
is the search rather than the ground; a briefed squad's followers fight markers (entry 087's item
for Master, which is not yours); and a floor is not a ceiling, so *cover at the place* — which the
mission book says a sabotage needs more than an approach — is walls and only walls.

**What to do.**

- **Put a sabotage on ground that exists before drawing any.** The mission book's test for this
  shape is *a thing at a place, and cover at that place rather than on the way to it* — four or
  five turns of standing still. Measure the three maps against that, the way `*GroundTests` measure
  a look: where on each can a soldier stand for five turns with nothing of theirs in view? If one
  of them carries it, the mission is a file and not a map. If none does, say why in a line and
  draw the smallest thing that does — and a relay mast in a field is the mission book's own
  example.
- **Give the briefing its restraint and its stop.** Section 5's are *leave the housing shut* and
  *if it turns into a fight, break it and go*. The second is a real stop, and whether the format
  can say it — an objective that changes shape when it goes loud — is a finding about the format
  or about the rules, and yours to tell apart.
- **Argue the effort with the harness, not the prose.** Fight a dozen seeds at three or four
  values bracketing *four or five turns of one soldier* — the mission book's arithmetic is 50
  points a turn — and read, per value, whether the job gets finished, by how many hands, and how
  many rounds the squad stood at the place. `MatchRecorder`'s task line already says whether the
  job was done and by whom; how long it took is the line to add. Write the value into the file and
  the measurement into `../decisions.md`.

**Out of scope.** Anything that makes the garrison move (entry 059) or changes how the search
weighs being seen (entries 083 and 087) is Core's, and the effort will look wrong while those
stand — say so rather than setting the figure to suit them. The sandbox offering a third mission
is View's.

**How to know it worked.** A `.hexmission` with `objective sabotage` in it, fought to a verdict by a
harness of the same shape as the other two, the ground measured against the mission book's test
for the shape, and an effort figure in the file with a batch behind it.

**Queued behind this: brief nine, `content/first-mission`** — `../interface/briefs.md` *Nine*,
written in full and sufficient as it stands; `../decisions.md` entry 099 has what shaped it. A short
mission on the real rules whose ground and posts make the three lessons of *Teaching it* happen on
their own. It is behind the sabotage and not ahead of it because its test is a stranger playing once
View's briefs seven and eight have landed, and those are behind two View briefs. **Brief nine's
*whether the build opens on it* is not this job's to settle** (entry 100): the waystation stays the
default, and the question is Master's when the game can be played well enough for a default to
matter. Build the mission; do not change `SandboxScenario`'s order.

---

## Open questions

**~~How big is a map?~~ A range, and the ranges do not set it.** Entry 007 reasoned radius 20 to
30 from the weapons and the sight range. The waystation is 24 and a rifle engages at 35 to 38 m
there. Kestrel Yard is 14 and entry 092 measured what that does: no post has a line longer than
33 m, every line any post has is inside the 45 m sight range, and the posts see between a sixth and
a half of the standable ground where on the waystation two of them see almost nine tenths. **In a
town the walls bind before the ranges do**, so the radius is not set by how far anybody can see.
What it does set is how many decisions the approach is: on Kestrel the loading floor is 115 action
points from where the squad starts and the footbridge about 200 — two turns in and two more out,
where the waystation's approach alone was two turns of road. So the sharpened question is not how
big but how many routes, and how much dearer the quiet one may be before nobody takes it — on
Kestrel the duct is 35 points dearer than the gate, and nobody took it in.

**~~What is a scenario file?~~** Answered: a file of its own that names a map, `.hexmission`,
entry 047. The clock it carried is read by a rule now — `rounds` is the `Deadline` on every
objective, entry 082 — and what a side is told is a statement, `told`, entry 087. What is still
open is that it **names** roles and kits and cannot declare them, which is the balance-numbers
question below wearing a different hat.

**A place nobody can stand in cannot be the thing a mission points at.** `at <place>` picks the
middle of the standable ground in it, so a sealed vault is not nameable as a target (entry 081).
The second map was where it would bite, and it did not: the loading floor is a building interior
with a door, and every other thing the waystation could not test — a place inside another place,
an exit upstairs, a deployment on a storey — needed no change to the format. A sabotage at a mast
or a housing may be where it bites next.

**Can a mission say anything about behaviour?** Everything the format holds is a fact about the
opening frame — who is where, facing which way, with what, and what the other side is told.
Nothing in it, and nothing in the rules, can say what a soldier is *doing*: the roster gives the
Cadre one honest patrol and neither a mission file nor `Commander` can express her, so a fifth
deployment is a fifth soldier standing still (entry 059). A standing order in the file and a
behaviour in the search are different answers with the same effect, and only one of them is
Content's. It is the largest single thing between either map and a site that reads as inhabited.

**A map editor.** Text is enough to author with and not enough to see with. `MapSketch` draws any
map in characters a storey at a time and is kept now, because the second map needed the thing the
first one threw away; the greybox draws them properly but only the missions `SandboxScenario`
names. So the cheap answer — *the game is the map view* — is true for a map the sandbox offers, and
a sketch is the view for one it does not yet. Whether editing wants a tool of its own is still the
live question.

**Where do balance numbers live?** They are in Core config records, which was right when there
was one territory and is awkward now — see above. Moving values (not shapes) out to data would
give Content real ownership and make AI-vs-AI balance runs configurable without a rebuild. It
would also weaken the nine-homes rule (entry 032) that currently keeps magic numbers out of
method bodies, so it is not obviously correct. Both formats show the shape the answer would take:
`profile` and `ground` are content declaring kit against a shape Core owns, and `role` and `kit`
in a mission are content *naming* one where declaring it would be the balance change. The effort
on a sabotage is the first number a mission file writes that is balance-shaped, and the job above
is where that line gets tested.

**Almost nothing has been measured, and here is what has.** Every number in the game was set by
reasoning; the harnesses are the first thing to check any of them against a match, and what they
found is in entries 037 to 039, 048, 081 and 092: a rifle is heard at 18 m against a design that
says a hundred, a turn's walk on gravel is heard further than a shot, the AI throws every charge at
the first crater and paces between two tiles on a shot it never takes, and a turn is thirteen
hexes of road, which makes a radius-24 approach two decisions long and a radius-14 one a single
decision.

Two things have been measured *right*. An objective ends a battle, every match on both maps. And
an objective with a job in the middle of it is gone after: the look is taken in twenty-four matches
of twenty-four on Kestrel, in rounds three to five. What stands between that and a mission achieved
is Core's on both maps — the squad marches the way everybody uses and fights the markers it was
told about — and a dozen seeds of Kestrel is four minutes.

**And what was measured about the ground rather than the numbers.** Entry 059 asked the mission
book's question of the waystation — is there anywhere to look at the house *from* — and got an
answer the drawing never advertised, which entry 081 narrowed to four places on the door axis, all
under the roof. Entry 092 asked it of Kestrel before the map was called drawn: within twelve metres
the loading floor is seen from inside the shed, from the yard through the roller door, and from
the office's window and roof edge, every one of them in some post's view; the one line no post can
see is through the side door, a stride and a half too far to count; and the duct lands behind the
racking one stride from a look, which is the waystation's drain again and was not drawn to be.
**Measure a map against its own briefing before calling it drawn**, because a map can be wrong
about what it offers for a long time without anybody noticing — and fight it, because Kestrel's
first drawing had a side door you could only reach through the gate, and nothing but twelve routes
said so.

## Recent work

```bash
git log --oneline -20 -- content
```
