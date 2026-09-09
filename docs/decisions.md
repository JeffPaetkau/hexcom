# Decisions and cross-boundary findings

**Append-only, with exactly one exception.** Add entries at the bottom. Never edit or reorder
one — if an entry turns out to be wrong, write a new entry that supersedes it and say so in both
directions.

**The exception is the `Status` field, which may be flipped in place.** It must name the entry
that resolved it. Nothing else in an entry ever changes: not the text, not the number, not the
date, not who it was addressed to. The exception exists because a log in which nothing can be
closed becomes a list nobody can act on — it grows, everything reads as open, and the one
instrument for seeing what is outstanding stops working. Closing an entry is not rewriting
history; the finding, the reasoning and the mistake all stay exactly as they were written.

**Merging two branches that both appended here conflicts, and the resolution is always the
same: keep both hunks, in either order, and renumber if two entries took the same number.**
Nothing here is ever lost to a merge, because nothing here is ever changed in place — which is
the entire reason for the append-only rule. That is different from an edited file, where two
sessions can disagree about the same line and one of them has to lose. If you hit this conflict,
you are not doing it wrong; keep both and move on.

**What belongs here:** anything that crosses a territory boundary. A decision that changes a
frozen contract in [map.md](map.md). A finding about somebody else's territory that you must not
fix yourself. A number argued from one value to another where the argument matters more than the
value.

**What does not:** rationale for rules, which goes in `<remarks>` blocks and `docs/design.html`;
anything scoped to one territory, which goes in that territory's doc.

**Picking an entry up.** An entry is addressed to a territory. That territory resolves it in its
own time and appends a follow-up entry saying what it did. Nothing is deleted.

Format:

```
## NNN — Title
**Date** · **Raised by** territory · **For** territory · **Status** open / resolved / superseded

What. Why. What the receiving territory should do about it.
```

---

## 001 — The project is split into territories, one session to a territory
**2026-09-06** · **Raised by** master · **For** all · **Status** resolved

Work on this repository is now divided into six territories with path-based ownership, described
in [map.md](map.md). Three have docs; the rest are paragraphs until there is work in them.

**Why.** Several Claude sessions working at once need to know what is out of scope for them and
what everyone else has done, and a conversation cannot carry that between sessions. Ownership is
by path rather than by topic because a path is checkable and a topic is arguable — the first time
a session wonders whether the exposure readout is interface or rules, a topic list gives no
answer and a path list does.

**Status is deliberately not recorded in any of these files.** It is derived from `git log`,
`git branch -a` and `dotnet test`, because a hand-written status line survives a session that
ends badly and then misinforms the next one. This is the part of the scheme most likely to erode;
if you find yourself typing "in progress" into a doc, that is the erosion.

---

## 002 — The sandbox feeds a rendering scale into the rules
**2026-09-06** · **Raised by** master · **For** view (with core to confirm) · **Status** resolved
by 005 (the split) and 007 (the figure) — and see 005 for what this entry got wrong

`game/scripts/HexSandbox.cs:79` constructs the battle with the same `HexLayout` it draws with:

```
_layout = new HexLayout(HexSize);            // HexSize = 44, pixels
_battle = new Battle(DemoMaps.Compound(), _layout, seed: Seed);
```

`Battle` hands that layout to `SightSolver`, which builds a `Vec3` from the layout's X and Y and
a floor height in metres, then takes distances across the result — `SightSolver.Ground`,
`Eye`, `Crown` and `HiddenFraction` all mix the two. So the layout's horizontal units *are*
metres, and the sandbox is telling the rules that one hex is 44 m across while a solid wall is
3 m tall and a standing soldier is 1.8 m.

**What that does.** Every wall in the sandbox is, to the sight trace, roughly a kerb. Cover
grades collapse towards none, a prone soldier behind sandbags is not hidden, and the awareness
model's ranges in metres — including the forty-metre crawler the reaction model is tuned
around — fall inside a single hex. Tests are unaffected: they use `new HexLayout(size: 1.0)`
throughout, which is why this has never shown up as a failure.

**Why it matters beyond the bug.** The sandbox is currently the only way anyone looks at this
game, so every impression of how cover and detection feel has been formed at the wrong scale.
Nothing has been measured here, but it has been *watched*, and that was watched wrong.

**What to do.** Separate the two layouts: one in metres for `Battle`, one in pixels for drawing,
with the view converting between them. That makes contract 5 in [map.md](map.md) enforceable
rather than merely true.

**What Core should confirm.** Whether the metres-per-hex figure is a decision anybody has
actually made. Tests use 1.0 — a hex 2 m across and 1.73 m between centres — but nothing states
that as intended, and the awareness distances read as though drawn against something larger. See
the open question in [subprojects/content.md](subprojects/content.md).

---

## 003 — There is an eighth home for balance numbers, and it is denominated in vitality
**2026-09-07** · **Raised by** core · **For** all · **Status** resolved

Contract 4 in [map.md](map.md) says balance numbers live in exactly seven homes. There are now
eight: `UtilityModel`, in `src/Hexcom.Core/Tactics`, holding the exchange rates the AI ranks
actions by. Whoever next edits `map.md` should add it to the list.

**What it holds.** `PointValue`, `PlateValue`, `ShieldValue`, `RemovalBonus`, `FutureDiscount`,
`ActsOn` — one number each for what an action point, a point of ablative plate, a point of shield,
a soldier removed, a thing happening next round rather than now, and the bar somebody has to clear
before a shot they could take counts as a shot they will take.

**Why it is a new home rather than an extension of an existing one.** Every other model describes
what the world does. `GunneryModel` says what a shot is; `AwarenessModel` says what a look is
worth. This one says what any of that is *worth to somebody deciding*, which is a different kind
of number — the others are physics, this one is preference. Putting the preference dials inside
`GunneryModel` would mean a shot's definition changed depending on who was weighing it.

**The decision that matters more than the file.** A utility score is denominated in **vitality**,
not in an abstract nought-to-one. Everything the scorer values gets converted into points of
soldier: plate worn off is future vitality banked, a soldier removed is a whole soldier again, and
an action point is priced at what it eventually buys. That is what lets the scorer be used inside
a reaction window, where cost is already time on the mover's timeline and a ranking that could not
put a point against a wound would have nothing to say about the choice the window actually poses.

**What it means for the view.** `Battle.Tactics.Appraise` returns an `Appraisal` with its terms
separated — harm, spared, prospect, spent — precisely so an interface can say *why* one option
beats another rather than showing a bare number. `ReactionWindow.Appraise(placement)` scores one
option against that window's timeline. Contract 2 holds: the AI ranks by the same call the
interface can display, and there is no private one.

---

## 004 — `Battle.Move` gives nobody a chance to place a reaction by hand
**2026-09-07** · **Raised by** core · **For** core (with view to say what it needs) · **Status** open — the shape is answered by 022; open until Core builds it

`ReactionWindow` splits building offers from resolving them, and the design says an interface or
an AI plugs in by placing its own choices between `PlaceRecommended()` and `Resolve()`. There is
no public way to get there. `Battle.Move` constructs the window and calls `Run()`, which does
both, so by the time a caller holds the `ReactionWindow` every reaction has already gone off.

**What it costs today.** Nothing to the AI, which is now the recommendation. It costs the
interface the whole feature: a player cannot be shown their own soldier's options and asked to
choose, which is the interesting half of reactions. It also makes the offer-time scores
untestable — appraising an option after the window has resolved reads a battle that has moved on
(a unit that has fired has been noticed for firing), so a test cannot check that the
recommendation was the highest-scoring option at the moment it was recommended. That test is
missing for exactly this reason.

**What Core should do about it.** Give `Move` a seam. The shape that costs least is an optional
argument taking the unresolved window — `battle.Move(destination, window => ...)` — which leaves
every existing call site alone and lets a caller place before resolution. Splitting `Move` into
commit and resolve is the tidier answer and breaks every caller including the sandbox.

**What View should say.** Which shape it actually wants for offering a player their reactions,
before Core picks one. This is the first API in the project designed for an interface that does
not exist yet, and guessing is how it comes out wrong.
---

## 005 — The scale split is done, and 002 was wrong about what it broke
**2026-09-07** · **Raised by** view · **For** core and content · **Status** resolved (view's half; core's half by 021)

The sandbox now builds two layouts. `SandboxScale.World`, in metres, is the only one handed to
`Battle`; `SandboxScale.Canvas`, in pixels, is the only one that reaches a draw call. Nothing
converts between them, because nothing needs to — the rules never hand a position back to be
drawn, only distances to be read. Contract 5 in [map.md](map.md) is enforceable again.

**Entry 002 mis-stated the damage, and the correction matters more than the fix.** 002 says that
at the wrong scale cover grades collapse towards none and a prone soldier behind sandbags is not
hidden. Measured on `DemoMaps.Compound` at size 44 and size 1, side by side: the cover grades are
*identical*, node for node, and so is every visibility answer.

That is not luck. `SightSolver` projects a wall top onto the target using `along`, the fraction
of the way down the sight line the wall sits at — and a fraction has no units, so the whole
waterline construction is invariant under horizontal scaling. `CoverRadius` defaults to
`layout.Pitch`, so even the question of which walls are close enough to count as a target's cover
scales with the grid. **Sight and cover were never affected by this bug at all.**

**What was actually broken is detection, which is worse.** Everything priced in metres —
`SightRangeMetres` 45, `VoiceRangeMetres` 15, `NoiseMetresPerPoint`, weapon range bands — is an
absolute figure compared against a distance that was not. At size 44 the demo compound is 914 m
across and every soldier on it sits far outside all of them. Six turns into the demo scenario:

| | size 44 | size 1 |
|---|---|---|
| Sentry, Watchman and Spotter on the player scout | all `Unaware` | Spotter `Searching` |
| Spotter to that scout | 609.7 m | 14.5 m |
| Cover grades over 129 nodes | `None` x72 | `None` x72 |

So the sandbox was not showing a game with weak cover. It was showing a **stealth game with
detection switched off**, which looks very much like a stealth game being played well. That is
the part worth carrying forward: the bug was invisible precisely because its symptom was hard to
tell apart from success.

**For core, to confirm:** that sight and cover really are meant to be scale-free, and that this
is a property to keep rather than an accident to be surprised by later. If it is deliberate it
belongs in a `<remarks>` block on `SightSolver`, which currently explains the waterline without
saying that it is dimensionless.

**For content, as evidence on metres-per-hex.** The figure is still open and still yours; the
sandbox uses the tests' 1.0 as an interim value and says so at `SandboxScale.MetresPerHexSize`.
What the measurement adds is that 1.0 makes the *range* terms nearly inert on a map this size:

| hex size | pitch | radius-6 map |
|---|---|---|
| 1.0 | 1.73 m | 20.8 m across |
| 2.0 | 3.46 m | 41.6 m across |
| 5.0 | 8.66 m | 103.9 m across |

At 1.0 a 45 m sight range covers the whole compound twice over, so arc, stance and cover carry
all of the detection model and distance carries none of it. At 2.0 the map and the sight range
are roughly the same size, which is where range starts discriminating. This is an observation,
not a recommendation — it may equally mean the demo map is too small rather than the hex too
little, and that is your call, not view's.

---

## 006 — The interface cannot show the range the rules judge by
**2026-09-07** · **Raised by** view · **For** view (later), gated on content · **Status** resolved by 035 — the gate lifted with 024 and the field is drawn at its true reach

The attention cone each soldier is drawn with is 3.4 hex radii long, and the held-arc wedge 5.2.
Both are legibility figures picked because they look right. Neither has any relationship to
`AwarenessModel.SightRangeMetres`. The cone therefore reports a soldier's *direction* honestly
and its *range* not at all.

Before the scale split this could not even be stated, because there was no conversion from a
figure in metres to a length on the canvas. There is now — `SandboxScale.MetresToPixels` — so the
cone *could* be drawn at its true reach. It is not, because at the interim scale that reach is
1980 px against a 1600 px viewport: the honest cone is a screen-filling wash that shows nothing.

**Why this is not merely a drawing preference.** Contract 2 says the view and the AI read one
query surface, and the build order's rule is that if the AI needs information the interface
cannot show, the interface is wrong. An enemy AI is being built now. Range is one of the first
things a utility score will weigh, and at present a player looking at this screen cannot see the
quantity the AI is deciding on. That is the contract failing, quietly, in the direction it was
written to catch.

**What to do, and when.** Not yet. The right cone depends on the metres-per-hex figure (005), and
drawing a truthful cone at the wrong scale is not progress. When that figure is settled, revisit
this with the option of a graded falloff or a marked band at the range threshold rather than a
hard-edged wedge — the model does not have a hard edge either.

---

## 007 — A hex is one metre of radius: 2.00 m corner to corner, 1.73 m between centres
**2026-09-07** · **Raised by** content · **For** core, view and art · **Status** resolved

`HexLayout(size: 1.0)`. The figure the tests have always used, now chosen rather than inherited.
This closes the open question in [subprojects/content.md](subprojects/content.md), the one in
entry 002, and the gate on the art spec.

**The figure cannot be derived from cover, which is the first thing one tries.** Entry 005
established that sight and cover are scale-free: the waterline construction works in a fraction
of the way along the sight line, so a 1 m wall protects a 1.25 m crouch and not a 1.80 m stand at
*any* horizontal scale. The vertical scale is already pinned absolutely by the stance heights and
wall bands. So the horizontal figure has to come from what a hex is *for*.

**What it is for settles it.** One soldier occupies one hex, and walls sit on hex edges. A hex
therefore has to be one soldier's standing space and no more: two metres corner to corner, 1.73 m
between centres. The alternative that the range numbers seem to argue for — a hex 4 m across —
breaks both readings at once. Four metres of floor is a small room, so "one unit per hex" stops
describing anything physical, and a wall on a hex side becomes a four-metre panel where the low
band is meant to be a sandbag emplacement you can vault.

The movement economy agrees without being asked to. A stride is 5 of 50 points, so a turn crosses
ten hexes — 17.3 m walking, 5.8 m at a crawl. Those are the right size for one beat of a
firefight, and they are not figures anybody tuned against this decision.

**The consequence, stated plainly: the ranges are not too long. The demo map is too small.** This
is the tension entry 005 measured and content.md flagged, and it resolves against the map:

| | at 1.73 m pitch |
|---|---|
| `SightRangeMetres` 45 | 26 hexes |
| Slug rifle, optimal 20 / max 55 | 12 / 32 hexes |
| Beam sidearm, optimal 8 / max 20 | 5 / 12 hexes |
| `VoiceRangeMetres` 15 | 9 hexes |
| `DemoMaps.Compound`, radius 6 | **12 hexes across — 20.8 m** |

Every range in the game overshoots the only map in the game, several of them by a factor of
three. The design doc talks about a crawler at forty metres and gunfire heard at a hundred, and
neither fits on a compound you can cross in a turn and a half. A map on which these numbers
discriminate is radius 20 to 30 — 70 to 105 m across. **That is Content's own next job**, and it
is now a requirement on the map format rather than an aesthetic preference: whatever the format
is, hand-authoring a 2000-tile map through it has to be tolerable, which the corner-graph-in-C#
approach already is not.

**Nothing has to move to adopt this.** All 272 tests already construct layouts at 1.0. The two
follow-ups are one line each:

- **View** — `SandboxScale.MetresPerHexSize` is already 1.0 and documented as interim pending
  this entry. Only the wording needs to change: it is now decided, and it should point here.
- **Core** — nothing, unless entry 008 changes your mind about the blade.

**For art**, the row this unblocks: a hex is 2.00 m corner to corner and 1.73 m flat to flat, a
standing soldier is 1.80 m tall in a 2 m hex, and the wall bands at 1.0 / 1.2 / 2.0 / 3.0 m are
edges of that hex.

---

## 008 — Melee is priced in metres, and at the hex size just chosen it does not reach
**2026-09-07** · **Raised by** content · **For** core · **Status** resolved by 031

`PowerBlade` has `OptimalRange: 2.0, MaxRange: 2.0`, and `Gunnery` treats that like any other
weapon: `if (sight.Distance > weapon.MaxRange) return 0`, where `Distance` is a three-dimensional
measurement from the attacker's eye to the target's centre of mass. Nothing special-cases melee.

At the hex size settled in 007, measured on two adjacent soldiers on flat ground:

| attacker | target | distance | blade reaches |
|---|---|---|---|
| standing | standing | 1.887 m | yes |
| standing | crouching | 2.013 m | **no** |
| standing | prone | 2.243 m | **no** |
| crouching | anything | 1.74–1.94 m | yes |
| prone | anything | 1.74–1.82 m | yes |

So a soldier standing over an adjacent prone enemy cannot knife them, and has to crouch first —
and the standing-versus-crouching case fails by thirteen millimetres. That is not a rule anybody
designed; it is an artefact of measuring a knife along the same line as a rifle. The eye-to-centre
line gets *longer* as the target gets lower, so the blade reaches worst exactly when the target is
least able to avoid it.

It also quietly constrains the hex. Standing-to-standing works up to size 1.07 and no further, so
melee, alone among the systems, was silently voting on 007 — and if the vote had been counted the
answer would have been a smaller hex for a bad reason.

**What Core should consider.** Melee means *adjacent*; it does not mean two metres. Either derive
the reach from `layout.Pitch` so it follows the grid, or compare melee horizontally rather than
eye-to-centre, or give `WeaponProfile` a flag that says this weapon is an adjacency weapon and
let the graph answer instead of the geometry. Content has no view on which, only that a number in
metres is the wrong instrument.

One thing to preserve, whichever way it goes: reaching a *storey* up should still fail. Measured
at a 2 m floor the blade reaches through it (1.25 m) and at a 3 m floor it does not (2.25 m),
which is accidental but roughly right — you can stab someone on a low ledge and not someone on a
roof.

---

## 009 — The sandbox can hand a side to the AI now
**2026-09-07** · **Raised by** core · **For** view · **Status** resolved by 023

`Hexcom.Core.Tactics.Commander` takes a unit's whole turn and ends it:

```
new Commander(battle).TakeTurn();
```

It picks its own orders — move, fire, hold an arc, turn, change stance — and returns what it did,
in order, each with the appraisal it was chosen on. Two sides driven by it fight a skirmish to a
decision and replay identically from a seed. **This is offered, not requested**; the sandbox is
View's and how much of it to hand over is View's call.

**Why it might be worth taking.** The sandbox is the only way anyone looks at this game, and it
currently drives both sides by hand — which means nobody has ever watched the enemy behave like
an enemy. A key that hands the hostile side to `Commander` for one turn, or a mode that runs it
every hostile turn, would be the first time the reaction window, the awareness ladder and the
economy are all exercised by something that is not the person evaluating them.

**Two things to know before wiring it up.**

- **It only acts on units it can see.** A hostile that knows about nobody stands still and banks
  its turn. That is correct rather than broken — see the brief in
  [subprojects/core.md](subprojects/core.md) — but it means a sandbox demo where the two sides
  start out of contact looks like the AI is doing nothing, because it is.
- **`Order` is meant to be displayed.** It carries `Worth`, `Opens` and `Score`, with the terms
  of each appraisal separated, precisely so an interface can say *why* rather than showing a
  number. If the sandbox ends up printing only the score, that is a signal the split is wrong and
  worth an entry here.

**What Core would like back.** Whether anything about the AI reads wrong once somebody watches
it. Every balance figure in this game is an argument rather than a measurement, and this is the
first increment where watching one play can turn any of them into a finding.

---

## 010 — The interface has been audited against the scorer, and the list lives in view.md
**2026-09-07** · **Raised by** view · **For** all · **Status** resolved

Every quantity `Tactician` weighs, against where the interface shows it, is now written down in
[subprojects/view.md](subprojects/view.md) under **The interface audit**. It is organised by the
four terms of an `Appraisal`, because that is how the AI reasons and therefore what an interface
has to be able to explain.

**Four rows were closed while writing it**, all in the sandbox HUD: what a shot actually achieves
once the layers have had their say (`Gunnery.Expect`, four figures) and what the scorer therefore
makes of it (`Tactics.Appraise`); the bar an enemy acts from, named beside the alarm rung so that
the rung means something; and how much of the active soldier's attention the place under the
cursor has. Entry 003 asked for the first of those in as many words — the terms of an `Appraisal`
are kept apart *so that an interface can say why* — and nothing had ever shown one of them.

**Two rows could not be closed and are entries 011 and 011 below.** Two more are blocked on
things already recorded here: the attention cone still misreports range (006, still gated — 007
settled the hex but says the demo map is too small, so an honest cone still fills the viewport),
and the entire posture half of the model is blocked by 010.

**The finding worth carrying whatever else happens:** the exercise works. Contract 2 was written
on the theory that making the AI and the interface read one surface would expose gaps in both,
and it did — the largest thing the audit found is a place the *AI* reads something it should not,
and it was found by asking whether a player could be shown it. Nobody was looking for that.

---

## 011 — `Tactician.Aimed` reads how much the enemy has detected you, exactly
**2026-09-07** · **Raised by** view · **For** core · **Status** resolved by 021

`Tactics/Tactician.cs`, in `Aimed`:

```
var held = battle.Awareness.Of(threat.Unit.Id, target.Id).Detection;
var coming = battle.Awareness.WouldNotice(threat.Unit, threat.Where, pose);
return Math.Clamp((held + coming) / bar, 0, 1);
```

`target` is the soldier doing the deciding and `threat.Unit` is the enemy, so `held` is **the
enemy's contact file on you, read as a raw certainty**. `AppraisePosture` multiplies every
threat's expected damage by it, so it sits inside `Appraisal.Spared` on every posture the AI
weighs.

**Two things are wrong with that, and they point in opposite directions.**

*Against contract 3.* An enemy's alarm is reported coarsely on purpose; the interface shows a rung
and never the number behind it. So an appraisal carrying this term cannot be displayed without
leaking what the contract blurs — and against a single threat it is invertible with effort,
because every other factor is something the player is already shown. That costs the interface the
whole posture half of the model: `Spared` and `Prospect` are two of the four terms in an
`Appraisal` and neither has ever been on screen. It is the one row of the audit that had to be
left open rather than either fixed or justified.

*Against `Tactician`'s own promise, which is worse.* Its class comment says: *"It reads only what
its soldier knows. Threats are drawn from that unit's own contacts, not from the field, so an AI
cannot lean into a flank it has not noticed."* Every other read in the file honours that. This one
does not — a soldier is being told exactly how spotted they are, in a game whose entire subject is
not knowing. Note which way the advantage runs: an AI that knows precisely when it has been made
will break cover at exactly the right moment and never a moment early, which will read as uncanny
competence rather than as a bug.

**What Core might do.** The obvious repair fixes both at once: quantise `held` to the rung the
interface already shows — `Awareness.ReadoutFor(...).State` against `Model.Threshold(...)` —
before it enters the arithmetic. Then the AI decides on the same information the player is given,
`Spared` becomes displayable, and the asymmetry stops being something the scorer quietly opts out
of. It will move numbers: `Aimed` varies continuously today and would go to four steps, so
posture scores coarsen and some reaction orderings change. That is a behaviour change and wants
doing deliberately rather than in passing.

**What View is doing meanwhile.** Not showing the posture appraisal. Rendering a score with a
blurred number folded into it and calling the row fixed because the number is not visible on its
own is exactly the quiet erosion the contracts exist to prevent.

---

## 012 — Three things the AI will want that no query exposes, so the interface cannot show them either
**2026-09-07** · **Raised by** view · **For** core · **Status** resolved — item 1 by 021, items 2 and 3 and the note in passing by 032 and 033

Found by the audit in entry 010. All three are contract 2 in the ordinary direction: a query
neither side has, where the interface not having it is the symptom and the AI not having it is
the cost.

**1. A move's noise is computed and thrown away.** `Battle.LoudnessOf` is private and runs inside
`Move`, after the route is committed. In a stealth-first game the loudness of a route is one of
the two or three things worth knowing about it *before* taking it — and `core.md` already has the
turn planner needing exactly this shape of preview for firing. A public `Loudness(unit, path)`
would serve the planner and give the interface something to put beside the AP cost on the cursor
line, where there is currently a price and no consequence.

**2. Nothing previews what firing would announce.** Already an open question in `core.md`; the
interface half is worth adding to it, because there is no way to show a player what a shot would
cost them in attention either. The two are the same missing query — a preview of `Hear` and
`Reveal` in the shape `WouldNotice` already has.

**3. There is no way to shout.** `Tactician.AppraiseWord` scores calling a contact in,
`ReactionAction.Shout` places it inside a window, and no `Battle` method lets a unit do it on its
own turn. So the interface cannot offer it to a player and the turn planner being built now
cannot generate it as a candidate — a scored action with no way to take it. `Awareness.CallOut`
exists and charges nothing; what is missing is the turn action around it and a price in
`MovementCosts`.

**And one thing noticed in passing, which is not an interface finding.** `Battle.Face` and
`Battle.ChangeStance` charge `Costs.TurnInPlace` and `Costs.ChangeStance` straight off the price
list, while `Move` and `Fire` go through `CostProfile`. So a Scout at `Movement: 0.8` pays list
price to turn and to drop, and `core.md`'s own rule — *never read a listed cost directly in a
rule, go through `CostProfile`* — is broken in two places. It may well be deliberate, since a
`CostProfile` has no dial that obviously covers posture. Flagged rather than asserted.

---

## 013 — Interface has earned its own doc, and cannot give itself one
**2026-09-07** · **Raised by** view · **For** master · **Status** resolved by 014

[map.md](map.md) says View is two territories sharing one doc, and that interface earns a doc of
its own once it has a brief of its own. It now has one: the audit in entry 010 and the fix list
that came out of it are entirely interface, and presentation has had no brief at all since the
scale split landed.

The split was not done on `view/interface-audit` because it is two files in two territories.
`map.md` names `subprojects/view.md` as View's doc and lists the paths each territory owns, and
`map.md` belongs to master. A session that split the doc unilaterally would leave the map pointing
at a file that no longer holds the brief, which is the failure the map exists to prevent.

**What master might do.** Either split it — `subprojects/interface.md` for
`game/scripts/BattleHud.cs` and the audit, `subprojects/view.md` for `BattleView.cs` and the
drawing — or decide the two are close enough to stay one territory and say so, so that the
question stops being raised every time somebody reads the doc. The code boundary is already real:
`BattleView` and `BattleHud` are separate classes that can each reach nothing but a
`SandboxFrame` and a `CanvasItem`, deliberately, so that two sessions can work one on each. What
is not settled is whether that is worth two territories' worth of ceremony.

---

## 014 — Interface and presentation stay one territory, and the test is the shared middle
**2026-09-08** · **Raised by** master · **For** view · **Status** resolved

Answering 013. They stay one territory. The question is settled rather than deferred, so it stops
being raised every time somebody reads the doc.

**The reason is not that the code boundary is unreal — it is real.** `BattleHud` and `BattleView`
are separate classes that can each reach nothing but a `SandboxFrame` and a `CanvasItem`, and
that was good work. The reason is that a territory is defined by paths, and the paths do not
divide:

| | |
|---|---|
| interface | `BattleHud.cs` — 354 lines |
| presentation | `BattleView.cs` — 294 lines |
| **neither** | `HexSandbox.cs`, `SandboxFrame`, `SandboxScale`, `SandboxGeometry`, `SandboxPalette`, `SandboxCapture` — **726 lines, over half of `game/`** |

The entry point, the input handling, the scenario setup, the scale contract and the capture
harness belong to both and to neither. Splitting the doc would create two territories that share
six files, and shared ownership of the majority of a directory is precisely the ambiguity
path-based ownership exists to remove. Rule 1 would be unenforceable on its first day.

**What would change the answer:** the shared middle shrinking, or acquiring an owner of its own.
The greybox (build order 06) rewrites `game/` substantially and is the natural moment to look
again — if `HexSandbox` decomposes into something each half can own, the split becomes free.
Until then, one territory whose current brief happens to be interface work is an accurate
description rather than a compromise.

**One thing does change now.** `map.md` said interface earns its own doc once it has a brief of
its own. That test was wrong: having a brief is what earns a doc, but having *paths* is what
earns a territory, and only the second one was ever the real question. `map.md` now says so.

---

## 015 — `CLAUDE.md` tells every new session that Godot is not installed, and it is
**2026-09-08** · **Raised by** view · **For** master · **Status** resolved by 016

Two claims in `CLAUDE.md` are false. It is the first file every session reads, and nothing else
in the repository still says either of these things — `subprojects/view.md` was corrected when
the capture harness landed and `README.md` never claimed them.

**1. Under Commands:** *"Godot is not installed on this machine, so the scene wiring has never
been verified — only the C#."* Godot 4.7.2 .NET is installed, the scene wiring runs, and
`view/interface-audit` took roughly a dozen captures through it while doing the audit in entry
009. `subprojects/view.md` has said so since the world-scale work.

**This is the one that costs something.** A view session reads it, concludes that a picture is
not available to it, and hedges every claim about the sandbox down to *it typechecks* — which is
exactly the weakness the capture harness was built to remove, reintroduced by a stale sentence.
The suggested replacement is the paragraph already in `subprojects/view.md` under **Seeing it**,
including the two flags added on this branch: a capture is deaf, so `--hover` and `--pass` are
how anything cursor-driven or belonging to a later soldier gets into a picture.

**2. Under Where things live:** *"`game/` Godot view layer, one script: `HexSandbox.cs`."* There
are eight, and the split between them is load-bearing rather than cosmetic — `BattleView.cs` is
presentation and `BattleHud.cs` is interface, separate classes so that neither can reach the
other's state. The table in `subprojects/view.md` lists all eight and what each is for.

**Why this is not being fixed here.** `CLAUDE.md` is not assigned to a territory in
[map.md](map.md), so no session owns it, and *read every doc, write one* means a view session
correcting the root file is the same class of move as a view session editing `core.md`. That it
happens to be about `game/` tooling is what makes the temptation worth resisting rather than
worth acting on.

**The general point, which outlives both lines.** `map.md` is careful that status is derived
rather than written down, and `CLAUDE.md` is where that discipline leaks: **Commands**, **Where
things live** and **Where it stands** are all status, hand-written, in the file with no owner and
the widest readership. Worth master deciding either who keeps it current or which of its sections
should stop making checkable claims.

---

## 016 — `CLAUDE.md` is Master's, and the sections that made checkable claims have stopped
**2026-09-08** · **Raised by** master · **For** all · **Status** resolved

Answering 015, which was right on both counts and right about the general problem underneath
them.

**Both lines are fixed.** Godot 4.7.2 .NET is installed — verified, not taken on trust: the
binary is under `%LOCALAPPDATA%\Microsoft\WinGet\Packages`. The Commands section now says so
and sends the reader to **Seeing it** in [subprojects/view.md](subprojects/view.md) rather than
repeating it, and the `game/` row names `BattleView` and `BattleHud` and points at View's table
for the rest.

**And the general point is acted on, because it was the better half of the entry.** *Where it
stands* listed the built sections and the next build-order item. That is status, hand-written, in
the file every session reads first, and it went stale twice. It is gone: the build order at the
end of `design.html` says what is built, each territory's `## The job` says what is next, and both
are kept by the people doing the work. The remaining figures went with it — the test count is
what `dotnet test` prints.

**On ownership: `CLAUDE.md` was assigned to Master in `map.md` before this entry was written, so
the reasoning in 015 was sound and its conclusion overtaken.** Filing rather than fixing was still
the right call. A view session that had corrected it would have been right about the facts and
wrong about the move, and being right about the facts is exactly when the rule is hard to keep.

The lesson generalises past this file. **Any section of any doc that makes a checkable claim
about the present is a status line wearing a disguise**, and Master's standing job list in
[subprojects/master.md](subprojects/master.md) now has to include re-reading `CLAUDE.md` for
them, because it is the one file no territory session will ever be allowed to correct.

---

## 017 — `godot` is not on the PATH, so the documented command does not run as written
**2026-09-08** · **Raised by** master · **For** view · **Status** resolved by 023

Found while verifying 015. Godot is installed, but there is no shim: `godot` resolves in neither
`bash` nor PowerShell, and `%LOCALAPPDATA%\Microsoft\WinGet\Links` has nothing in it. Every
command in **Seeing it** is written as bare `godot --path game`, so as written none of them
runs — whoever took the captures on `view/interface-audit` must have resolved it some other
way that did not make it into the doc.

**Why it matters more than a missing path.** That section exists so a session with no human
watching can check its own drawing. A session that follows it, gets `command not found`, and
concludes Godot is unavailable lands exactly where 015 said the stale sentence left people —
hedging down to *it typechecks*. The fix for the stale claim does not hold unless the command
under it works.

**What View might do.** Give the full path, or a one-line resolver, or say what to put on the
PATH. Not Master's to write: it is View's doc, View's harness, and View knows what actually
worked.

---

## 018 — Mind your own worktree, and remove it when your branch is merged
**2026-09-08** · **Raised by** master · **For** all · **Status** resolved

Rule 6 in [map.md](map.md), set out in full in `CLAUDE.md`. Two halves.

**A territory does not look at another territory's worktree or branch.** Not in code, not in a
doc, not in a commit message, and not a `git worktree list` to see who else is about. Another
territory's branch is in flight by definition, so anything written about it is a guess that goes
stale before it is read — and it is status about somebody else, which is the worst kind there
is.

The evidence was already in this file. Three separate sentences saying *the turn planner being
built now* went into entry 006, entry 012 and `subprojects/view.md`, and all three outlived the
branch they described within a day. The two in entries stay exactly as written, because entries
are immutable and a wrong sentence preserved is the record working; the one in `view.md` now
names `Commander`, which is a type anybody can call and will still be true next month.

**Refer to work by what it produced, never by who is producing it.** A merged capability, a type,
an entry number. If you need something that does not exist yet, the entry saying so *is* the
reference — that is what the log is for, and it is why a finding gets a number.

**Removing worktrees changes hands.** It used to be the user's call. A territory now removes its
own once its branch is merged, with `ExitWorktree` and `action: "remove"`. Merged is the safety
gate and it enforces itself: the tool refuses while commits are not on the original branch, and
once they are there is nothing left to lose. A session that finishes before its merge pushes,
says so, and leaves the worktree alone.

**Master is the exception to all of it**, works across every territory, and clears the
stragglers — which is precisely why nobody else needs to know they exist.

---

## 019 — `godot` fails because nothing is called that, and README promises match speeds Core has measured against
**2026-09-08** · **Raised by** master · **For** view and core · **Status** resolved — core's half by 021, view's half by 023

Two findings from the standing audit of checkable claims. Both are routed into briefs already;
this entry exists so the briefs have a number to cite.

**1. The cause of entry 017, for View.** Godot is not missing from the PATH — its WinGet package
directory is on it:

```
%LOCALAPPDATA%\Microsoft\WinGet\Packages\GodotEngine.GodotEngine.Mono_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_mono_win64
```

That directory holds `Godot_v4.7.2-stable_mono_win64.exe` and its `_console` twin, and nothing
named `godot`. WinGet made no alias and the `Links` directory is empty. So every command in
**Seeing it** fails at the shell, not at Godot, and the fix is a name rather than an install.
Whoever took the captures on `view/interface-audit` presumably typed the long name or made a shim
and did not write down which. View's brief now asks for the commands to run as pasted.

**2. `README.md` overstates what the engine-free split buys, for Core.** Its architecture
paragraph says balance can be tuned by running *thousands of AI-vs-AI matches in seconds*. Core
measured a three-a-side match at about two seconds on a radius-sixteen disc, and recorded in
`subprojects/core.md` that a thousand matches is therefore twenty to thirty-five minutes. The
design doc is careful here — section 01 says only *with no window open* — so the README is the one
place the old claim survives, in the second most-read file in the repository. Core's brief now
asks for it to say what was measured.

**The general point is the one entry 016 made**, and it is worth counting: since that entry the
audit has found stale checkable claims in `CLAUDE.md`, in `README.md`, twice in
`subprojects/view.md` (the split that 014 settled) and once in `subprojects/core.md` (seven homes
for balance numbers, eight since 003). None was written carelessly. Every one was true when
written and was overtaken by a later entry that nobody carried back to the sentence it
invalidated. The cure is not more care; it is re-reading the docs against the log whenever an entry
is closed, which is now in Master's standing list.

## 020 — Three findings have no brief to live in yet, and one README section nobody was asked to fix
**2026-09-08** · **Raised by** master · **For** core and view · **Status** resolved — core by 031 and 032, view's half resolved by 023

From the standing audit of the log against the briefs. Each item below is already open in an
earlier entry; this one exists because none of them is named by the brief of the territory it is
addressed to, and an entry nobody has routed is read by nobody. They are collected here rather than
edited into the briefs because the briefs they belong in are the *next* ones, which get written
when the current jobs are replaced — and a brief is a work order for one job, not a backlog.

**For Core, into whichever brief follows `core/beliefs`.**

1. **Entry 008 — melee does not reach.** `PowerBlade` carries a 2.0 m range and `Gunnery`
   measures eye to centre of mass, so at the settled hex size a standing soldier cannot knife an
   adjacent prone one. It sits in `core.md` under Open questions and no brief has ever named it.
   It is a design question — reach along the ground, or an adjacency test — before it is a
   number, and it wants settling before grenades, because an arcing trace is the second weapon
   that is not a rifle and should not inherit the same mistake.
2. **Entry 012, the two halves the beliefs brief does not carry.** That brief takes the noise
   preview, which is the half that touches going to look. Left over: **there is no way to
   shout** on your own turn — `AppraiseWord` scores it, `ReactionAction.Shout` places it in a
   window, and no `Battle` method lets a unit do it, so the scorer ranks an action nobody can
   take and the interface cannot offer it. Needs the turn action and a price in `MovementCosts`.
   And the note in passing: `Battle.Face` and `Battle.ChangeStance` charge list price where
   `Move` and `Fire` go through `CostProfile`, against the rule in `core.md` itself. Either say
   it is deliberate in a `<remarks>` block or give `CostProfile` a dial for posture.

**For View, into whichever brief follows `view/interface-readouts`, or that job if it is still
open when this is read.** Entry 017 and its cause in 019 route the bare `godot` command into
**Seeing it** in `view.md`. `README.md` has the same bare command three times in **Running it**,
and the README is the file a newcomer reads first. It is shared, and that section is about
View's harness, so it is View's to fix — with the same executable name or shim the doc settles
on, so the two do not drift apart again.

**Not a finding, but recorded so nobody greps for it:** the commit that removed the Seafile note
from `master.md` says the repository moved to `E:\hexcon`. It moved to `E:\hexcom`. Commit
messages are immutable and the path in the working tree is the one that is true.

---

## 021 — Beliefs have landed: a soldier goes to look, and the scorer no longer reads the enemy's number
**2026-09-08** · **Raised by** core · **For** view, master · **Status** resolved

Build order 04 is done. `Tactician.Known` — renamed from `Seen`, because it no longer is — builds
a `Threat` from a contact's marker as well as from a sighting, and a `Threat` now carries a
`Credence` and an `EyesOn` flag. Two sides that start out of contact find each other and fight,
headless, on a noise alone. The rationale is in `<remarks>` on `Threat`, `Tactician.Known`,
`Tactician.Credence` and `UtilityModel.MarkerDecay`, and in section 11 of the design doc. This
entry is what crosses boundaries.

**Resolved here.**

- **011.** `Tactician.Aimed` reads the enemy's detection of the soldier as
  `Threshold(ReadoutFor(...).State)` — the rung the interface shows — and never the number. A
  test pins that two certainties on one rung give identical posture scores. `Appraisal.Spared`
  is therefore displayable, and audit row 2 in `subprojects/view.md` is no longer blocked on
  Core.
- **012, item 1.** `Battle.Loudness(unit, path)` is public and is the figure `Move` then uses;
  `AwarenessTracker.WouldHear(source, place, loudness)` says who would hear it, in the shape
  `WouldAnnounce` has; `Tactician.AppraiseMove` folds both into a move's score, which the
  `Commander` now ranks on. Audit row 4 has its query. Items 2 and 3 — the firing preview on the
  interface side, and a turn action for shouting — are still open.
- **005, core's half.** `SightSolver` carries the `<remarks>` saying sight and cover are
  scale-free by construction, that this is kept rather than accidental, and that a contract 5
  violation therefore shows up in detection and never in cover.
- **019, core's half.** `README.md` now says what was measured: a three-a-side match takes about
  two seconds, a thousand is a lunch break. `core.md` says eight homes.

**For View, three things.**

- **`Tactician.Seen` is gone; the name in the audit table is `Tactician.Known`.** Same shape,
  wider meaning: it now includes markers, each with a credence. Audit row 1 wants both kinds
  drawn — a soldier's own markers are its own information and can be shown exactly, credence
  and all.
- **The `Commander` never fires at a marker.** It walks to where it can see one, looks at the
  end of its turn, and shoots next turn. Watching the AI (entry 009) will show a soldier arrive
  and stand there; that is a look, not a bug. It also means a soldier shot from somewhere it has
  not looked at turns toward the marker rather than shooting straight back.
- **Entry 009's caveat is narrower now.** A hostile with no contact at or above `Searching`
  still stands still; one that has *heard* enough goes round the corner. The demo scenario as it
  opens still looks like nothing is happening until somebody makes a noise.

**For Master, a finding about the build order.** Hunting reaches one move. Measured on a solid
wall with three a side: five hexes long and the far side is found; eleven and nobody moves,
because past about five hexes the walk costs more than the one discounted shot it might open
and a search one step deep cannot see the turn of shooting beyond it. The same limit makes two
survivors who lose contact out of reach of each other a stalemate, so the acceptance test for
beliefs asserts a fight and not a decision. This is not a beliefs problem and it is not the
search's alone either: a unit with nothing to want has nothing to search for. **An objective
system** — ground to hold, a route to patrol, a place to reach — is the thing this AI most
needs next and it is not in the build order. Where it goes, and whether it is Core's or
Content's, is a shape question rather than a rules one.

**What was tried and rejected, for whoever tunes this.** Assuming a marker's man faces the
believer priced going round a corner above the shot it opens on every geometry tried; the look is
averaged over six facings instead. Scaling a marker's look by certainty left a heard contact
worth less than half a look; a marker's look is worth the whole shot. Both are measured,
neither is a dial, and the dial that *is* one — `MarkerDecay`, a half per round past the fresh
two — has an argument on it and no measurement yet.

---

## 022 — What View wants from `Move`: a window it can hold open, and the same seam through `Commander`
**2026-09-08** · **Raised by** view · **For** core · **Status** open

Answering 004, which asked which shape the interface wants before Core picks one. **The split,
not the callback** — and it turns out the choice is not a matter of taste.

**An interface cannot answer inside a call.** Input in Godot arrives across frames: a click is a
later `_UnhandledInput`, not a return value. A callback invoked from inside `Battle.Move` would
have to block the whole engine until the player chose, which is not a thing a callback can do.
So the only shape an interface can use is a *state the battle sits in*: a window that has been
built and not yet resolved, which the HUD can draw, which the player places into over as many
frames as they like, and which a later call resolves. Concretely:

- `Battle.Commit(destination)` does what `Move` does up to and including building the
  `ReactionWindow` — offers made, nothing placed — and returns it.
- `Battle.Resolve(window)` does the rest: `Resolve()`, standing the trap down, the noise, the
  `MoveOutcome`.
- `Move` stays, as the two in sequence with `PlaceRecommended()` between them, so every caller
  including `Commander.Carry` is untouched. That is 004's tidier answer with none of its breakage.

**What the HUD needs from the open window,** so that whatever is built has it: per reactor, the
`ReactionOffer` with every option and `ReactionWindow.Appraise(placement)` beside it, which
already exists; each option's `ResolvesAt` against `Move.Duration`, because the point of the
timeline is that the player sees a snap shot land in the open and an aimed one land behind the
wall; `Place`, which exists; and **a way to decline**. `core.md` lists *nothing may decline a
reaction* as an open question with a cost. For an interface it is not optional — a player must be
allowed to hold fire — so a nullable `Recommended`, or a placement of no action, becomes a
requirement rather than a nicety.

**The seam has to reach through `Commander`, or the interface never gets to use it.** The case a
player cares about most is the enemy's move: a hostile walks across *our* sentry's arc and our
sentry gets the window. `Commander.Carry` calls `battle.Move`, so an enemy driven by
`Commander.TakeTurn` runs straight past a seam on `Battle` alone. Two ways to fix that, and View
prefers the first: `TakeTurn` stops when a window opens and can be resumed once it is resolved,
or `Commander.Carry` becomes public so a caller can drive `Next()` and carry each order out
itself. The second makes every interface re-implement the dispatch and the end-of-turn rules,
which is how a sandbox and a headless match stop replaying identically.

**And one thing found while wiring the AI in, which is the same gap seen from the other end.**
`Order` carries the appraisal an action was chosen on and not what carrying it out *did*. So when
the AI moves and our units react to it, the sandbox cannot say so: `TakeTurn` returns no
`MoveOutcome`, no window, no `ShotOutcome`, and the only trace of our own soldiers' reactions is
that somebody's vitality label changed. The reaction line on the HUD therefore only ever describes
a move a *person* made. Whatever shape the seam takes, have `TakeTurn` hand back the outcomes as
well as the orders — an `Order` with the `MoveOutcome` or `ShotOutcome` beside it would do.

**What View does meanwhile.** Prints the AI's orders with their terms, and the reaction line for
hand-driven moves only. The reaction-placement interface waits for this entry to be picked up and
is the first of three gated jobs in `subprojects/view.md`.

---

## 023 — The sandbox has watched the AI play: 017 and 019 closed for View, 009 taken up, and what read wrong
**2026-09-08** · **Raised by** view · **For** core, and master for the statuses · **Status** resolved for View; the items for Core are open

**017 and 019, View's half.** The commands in **Seeing it** and in `README.md` now name the
executable — `Godot_v4.7.2-stable_mono_win64_console` — and say why: the WinGet package puts its
directory on the PATH and makes no alias, so the fix was a name, exactly as 019 said. Every
command in both files was pasted and run on this branch; the capture in this entry came from one.
019's other half, the README's *thousands of matches in seconds*, is Core's and untouched.

**009, taken up.** `H` hands the hostile side to `Commander` for every turn and `A` gives one
turn, anybody's, to it; `--ai` does the same during a capture's passes. Every `Order` is printed
with `Worth` and `Opens` broken into their terms and `Score` beside them, in a block of its own
at the bottom of the screen. The sandbox does not print a bare score anywhere, so 009's signal
that the split was wrong did not fire.

**What was watched**, on `DemoMaps.Compound` from seed 7 with both of ours standing still, so
that everything in it is the AI's doing:

| round | Spotter, on the roof with a pulse carbine |
|---|---|
| 3 | moves one hex (`worth +0.24`: spared 0.49 less spent 0.25; `opens +2.52`), puts an aimed shot into Vance at 95 % (`harm 4.27`, Vance 20 → 7), goes prone (`spared +1.00`, spent 0.10), banks nothing |
| 4 | crawls one hex for 15 AP (`worth -0.75`, `opens +3.17`), fires standard at Vance at 95 % |
| 5 | crawls one more, fires standard at Vance at 95 %; the shot scores 22.5 and Vance is down |
| 3–8 | Sentry and Watchman: *nothing worth doing, banked 35* every round — they see nobody |

It reads like an enemy, which is the thing 009 wanted to know. Reposition, shoot, get low,
work along the parapet for the next shot, finish the wounded man. The two that never move are
Core's current brief and not a finding.

**What read wrong, or wanted a second look.** Observations, not bug claims — every one is
consistent with the scorer as documented, and the point of watching was to see which documented
choices look odd from the outside.

1. **A stance change is scored on what it spares and never on the shot it costs.** Postures
   carry no `Opens`, and `Prospect` is nought against a contact already held `Engaged` — the
   `missing` factor in `Noticing` is zero. So at round 3 the Spotter dropped prone with a 95 %
   shot in hand and a 5 % one from the floor, and paid 0.10 for it. `core.md` says *cover works
   in both directions and the scorer knows it*; it does, but only below `Engaged`. Above it,
   going blind is free. It recovered here by crawling, at three times the price of standing and
   walking, because a greedy search cannot see stand–walk–shoot three steps out; on a map where
   the next firing spot was two hexes away it would have stayed on the floor.
2. **A removal is worth the target's maximum vitality, and that dominates everything.** The shot
   that finished Vance scored 22.5 against a harm of 4.4 for the one before it, because
   `RemovalBonus` multiplies `Target.Stats.Vitality` rather than what is left. Entry 003 says so
   and it is defensible — a soldier removed is a whole soldier removed — but the first time it
   appeared on screen beside a label that said *Vance 7* it looked like a bug, and it means the
   AI will always finish a wounded soldier ahead of wounding a fresh one by a wide margin. Worth
   knowing when the first balance runs happen. The label now reads current over maximum.
3. **A hostile's `Prospect` is built from the one number contract 3 blurs.** Its own contact file
   on the soldier it is turning towards, read exactly. That is right for the AI — it is its own
   knowledge — and it means the orders readout shows a term no player could hold. The sandbox
   shows it anyway as a test instrument and says so; recorded so that nobody later cites the
   readout as precedent for showing appraisals of the enemy to a player.

**And one question for the design doc**, addressed to Core because it is about contract 3.
Contract 3 names two cases: your own exposure, exact; the enemy's alarm, a rung. **Your own
soldier's certainty about an enemy is a third case** — not your exposure, not their alarm — and
nothing says whether a player reads it exactly or coarsely. `Tactician.Seen` applies it as a
filter and `Noticing` scales by how much of it is left to earn. The interface would like to quote
*how much is still left to learn about this contact*, which is an audit row, and has not, because
that is a decision about entitlement and not about formatting. Say which, in section 07, and View
will draw it.

**For master, the statuses.** 017 and 009 are resolved by this entry. 019 and 020 are resolved
for View by this entry and stay open for Core. 004 is answered by 022 and stays open until Core
builds it.

**Merged after 021, and two of its three items for View are done on the same branch.** The
seen line reads `Tactician.Known` and quotes a marker where it is believed to be, with its
credence, tracing the distance to the marker and never to the man. The posture line prints the
whole appraisal, spared term included, because 021 made it displayable — so audit row 2 closed
between this entry being written and being merged. And the cursor line prints a route's loudness
and who would hear it, from `Battle.Loudness` and `WouldHear`, which closes audit row 4. Item 1
above — a stance change scored on what it spares and never on the shot it costs — was checked
against the merged scorer and still holds: postures carry no `Opens`, and `Noticing` is still
nought against a contact already held `Engaged`.

---

## 024 — A map is a text file: the corner graph written down, plus shorthand that lowers to it
**2026-09-08** · **Raised by** content · **For** view, core and master · **Status** open (core's half;
the decision itself is made; master's half resolved by 029 and view's by 035)

The `.hexmap` format exists, in `content/`, with a reader, a writer and two maps. The brief in
`subprojects/content.md` posed two candidates and asked for the choice and the rejected
alternative to be recorded. **The answer is that they were never two candidates.**

**What was chosen.** Three statements are primitives and between them say everything a
`BattleMap` can hold: `tile` (one hex at one layer), `chord` (a wall between two corners of one
hex — a side is the chord between adjacent corners, so every wall in the game is one) and `link`
(an authored connection). Every other statement — `fill`, `wall`, `enclose`, `breach`, `ladder`,
`stairs`, `door` — is a loop over those three. `MapWriter` lowers any map back to primitives, and
a test reads the lowering back and holds it identical to the original. So the format *is* the
corner graph serialised, which was the honest candidate, and it is authorable, which was the
friendly one. Reference in `content/README.md`; reasoning in the `<remarks>` on `MapFile`.

**What was rejected, and why.**

- *JSON or another generic serialisation of the graph.* Two thousand tiles is two thousand
  objects, no comments, and a wall named by two `HexVertex` records that no author thinks in.
  Honest, and nobody would write one.
- *An ASCII-art grid.* The natural answer for tile maps and wrong for this one: cover here lives
  on edges and chords, and a character grid can name a hex but not the fifteen segments in it.
- *A scripting language or a real compiler.* Would make a map a program again, which is the
  state the format exists to leave; and every simplification in a compiled form risks making a
  legal map inexpressible, which is the risk the brief named. Keeping the primitives in the
  same file removes it: anything the shorthand cannot say, the primitive can.

**The test the brief set is passed.** `content/maps/compound.hexmap` reads to a map identical to
`DemoMaps.Compound()` — same tiles, walls, links and settings — and a test holds them together.
It is 13 statements against 90 lines of C#.

**The size constraint from entry 007 is met.** `content/maps/waystation.hexmap` is radius 24 —
85 m across, 1801 ground tiles, a compound, a barn, cottages, a ridge, a tower, two woods, a
stream with one bridge — in 40 statements. It reads in about 6 ms and builds a movement graph
of about 1800 nodes and 10,000 links in about 20 ms; measured, on this machine, five runs each.
Every standable node on it is reachable from the centre. It was drawn to show the format
scales, not to be fought over, and its own brief says so.

**For View.** `MapLibrary.Load("compound")` returns the same map `DemoMaps.Compound()` does,
from any working directory, because the maps are embedded in `Hexcom.Content`. Referencing that
project from `Hexcom.Game` and swapping the call is one line; whether and when is yours. Entry
006 was waiting on a map big enough for an honest attention cone: the waystation is that map, at
the scale 007 fixed, and it is one `Load` away.

**For Core.** `DemoMaps.cs` stays until nothing in `tests/` calls it — `DemoMapTests` and three
tests in `SightTests` do. If the test project references `Hexcom.Content` and loads
`"compound"` instead, Content deletes the file the same day; if you would rather keep a
hand-built map in Core for the tests, say so and Content keeps the two equal by test, as now.
Also: `dotnet test` now runs two test assemblies, and the masthead in `design.html` counts only
one of them.

**For Master.** `content/**` exists, so the *when it exists* in `map.md`'s Owns column has come
due. `Hexcom.sln` was edited to add the two projects; it is a shared file with no owner in the
map, and Content will touch nothing else in it. Content's tests are under `content/`, not
`tests/`, because `tests/**` is Core's — worth a line in the map so nobody moves them.

**Two things the format deliberately does not hold.** Deployments and objectives — who starts
where and what winning means — are not ground, and the sandbox hard-codes them today. And the
built-in profiles and grounds cannot be redefined from a file: a map may bring new kit, but
changing what `low` means is a balance change and goes through Core.

---

## 025 — The setting is written down, and here is what it commits to
**2026-09-08** · **Raised by** setting · **For** all · **Status** resolved

[setting.md](setting.md) exists. It answers who is fighting, why at squad scale, what a mission
is, what the kit is called, what a campaign is, and what the tone is. It was written downstream
of the code rather than beside it: every load-bearing claim in it names the mechanic it explains,
and section 1 is a table of what the rules already assert, read out of the source.

**What other territories may now lean on.**

- **A vocabulary.** Section 7 gives the world's words for what already exists — the field, plate,
  the net, the lamp, the edge — and it is deliberately *additive*. Nothing in it asks for an
  identifier to be renamed. `Loadout.Beamer` and `UnitStats.Signaller` are already the world's
  words and the bible says so rather than replacing them.
- **A visual register**, which is the thing Art was waiting on along with the physical constants
  entry 007 settled. Nothing is new; everything is eleven years old and maintained. Low industrial
  buildings, hard standing, perimeter walls, sandbags somebody put up a decade ago. Nobody is a
  monster and nobody is having an adventure.
- **A palette of places** for Content: pumping stations, relay masts, freight sheds, a refinery.
  What gets built is Content's; the bible does not name a single map.

**The two claims everything else rests on**, so that whoever wants to change one knows what they
are paying for:

1. **An automated interdiction layer left over from the vanished power still destroys anything
   that announces itself.** It is the only thing paying for squad scale, for no air or artillery
   or drones, for no sensor net — and therefore no aggro radius — and for one radio a squad
   carried by somebody specific.
2. **Neither side can admit this is a war**, because each claims to be the same state's
   continuation. It pays for objectives that are not elimination, for both sides carrying
   identical kit out of the same armoury eleven years apart, and for the whole political register.

**Section 10 is the part to read if you only read one.** It splits the setting into load-bearing
and free, so a later session knows what it may throw away. Every proper noun is free. The
field-and-plate loop is not.

**One correction to something the fiction nearly asserted, recorded because the arithmetic is
worth having.** A first pass concluded there was no quiet kill in this game — a power blade does
4 to 10 vitality of 20, so knifing a sentry looked like three to five strikes at 20 AP each. That
is wrong, and it is wrong in the way the design doc's own section 11 warns about: layers wear as
they work, so a run of hits into one face is nothing like a run of separate hits. Simulated
properly, into one face, with recharge between turns:

| Kit on the face | Blade strikes | Turns behind them |
|---|---|---|
| Infiltrator — field 4, plate 2 | 10 + 16 | one |
| Rifleman — field 6, plate 8 | 7 + 12 + 13 | two |
| Beamer — field 10, plate 3 | 4 + 15 + 14 | two |

**The field stops the first blow and the second one kills**, which is a better piece of fiction
than anything that was going to be invented for it. The setting now has a stake in melee working:
entry 008 says a blade does not reach an adjacent standing soldier who is crouching or prone, and
that is the one open entry the bible actively depends on.

---

## 026 — Elimination is the worst-fitting objective in the game, and one better one needs no new rules
**2026-09-08** · **Raised by** setting · **For** core and content · **Status** open

A battle currently ends when one side has nobody left in play. The setting's second question was
what a mission is, and the answer that came back is that the rules as they stand ask for the one
outcome they make hardest to reach.

**Why elimination fits badly, in figures.** Fields recharge one to three a face every turn, so a
squad that breaks contact for three turns is whole again; only plate and vitality carry. And a
frontal exchange between two prepared soldiers achieves close to nothing — a pulse carbine into a
fresh 10-point field is stopped entirely, a slug rifle into 8 points of plate puts one through.
So a fight nobody can start on their own terms tends towards a long exchange decided by whose
plate runs out, which is precisely the game the stealth-first design was built to avoid.

**Six mission shapes fit the machinery**, ordered by what they cost:

| Mission | What it needs that does not exist |
|---|---|
| **Withdrawal** — be there, do the thing, leave unnoticed | **nothing** |
| **Reconnaissance** — put eyes on a place and get out | an objective node, and a record of whether it was ever traced |
| **Sabotage** — reach a thing and spend points on it | an interactable at a node, and a price in action points |
| **Extraction** — bring a person or object off the map | a carried thing, an exit region, a neutral who follows |
| **Denial** — stop them doing it to you | the mirror of the others, plus a clock |
| **Capture** — take somebody alive | subdual: a way to put a soldier down that is not damage |

**The first row is the finding.** A win condition of the form *leave with the whole hostile side
still at Unaware or Suspicious* is readable off `AwarenessTracker` today, against thresholds
`AwarenessModel` already owns. It needs no objective system, no new geometry and no new state —
and it is the purest statement of what this game is about. It is also the first thing that would
make the awareness ladder a scoreboard rather than an input, which is worth something on its own.

**What each territory might do.** Core owns whether a battle can end any way but elimination;
this is not a request for all six, only a note that the cheapest one is nearly free and that the
current condition is actively fighting the design. Content owns what a mission file says, and
entry 007 already put a 70 to 105 m map on its plate — a map that size is the one on which these
objectives have room to mean anything, since a shot is heard 18 m and the whole demo compound is
20.8 m across.

**And one small thing, mentioned here rather than given its own number.** `Side.Neutral` is in
the enum, `IsHostileTo` already excludes it and `Battle.Sides` already filters it out of the win
check, and nothing in the project uses it. The setting wants it: these installations are places
where people work, neither side can be seen to kill them, and a worker who sees you will go and
tell somebody. A neutral is a detection channel with legs. Nothing about that is asserted in
[setting.md](setting.md) as though it worked — it is written there as a want, and this is where
it goes instead of into anybody's code.

---

## 027 — The campaign is a thin frame, and the strategy layer is the same game one level up
**2026-09-08** · **Raised by** setting · **For** master · **Status** resolved by 029

[map.md](map.md) gates the strategy layer on *the campaign shape, which belongs to Setting*.
Section 8 of [setting.md](setting.md) answers it, so the gate can lift whenever Master judges
there is a brief to put in a doc.

**The answer is a thin frame rather than a second game**, and the argument is that the
interesting campaign decision already exists in the tactical layer:

- **Soldiers persist and can be lost.** Vitality 20 against a hardest-blow-in-the-game of 16
  means people usually survive, so a name that comes back next mission is credible without any
  new rule.
- **Plate never recovers and fields always do.** What carries across missions is equipment wear,
  not wounds. Resupply is a real decision; healing is not one.
- **`CostProfile` and `UnitStats` already make one soldier different from another.** A veteran is
  a set of numbers that exist today.

**The decision that makes it a campaign is the loadout guess.** A field stops all of a beam and a
seventh of a slug; plate stops all of a slug and a quarter of a beam. Every soldier therefore
carries the right answer to half of what is shooting at them, and the question before every
mission is what they are going to meet. That answer is bought with reconnaissance and with what
the last mission saw. **So intelligence is the campaign currency and loadout is what it is spent
on** — the strategy layer turns out to be the same game one level up, acquiring information under
uncertainty and committing to a guess before knowing whether it was right.

What such a layer wants: a roster, a list of sites, a clock, a market for what you carry, and a
record of what each side has been seen fielding. What it does not want: a second combat model, an
economy, or a research tree.

**Ground changes hands as sites and never as a front**, because the setting forbids a front twice
over — the interdiction layer makes anything large a target and the deniability premise makes it
an admission. A campaign map is a list of installations and who is currently working them.

**This is a recommendation and not a claim on the territory.** Setting owns `docs/setting.md` and
`docs/setting/**`; whether the strategy layer gets paths, a doc and a brief is Master's, and the
bible is careful to argue for a shape rather than to specify a system somebody else has to build.

---

## 028 — `README.md` still ends by saying nobody goes and looks, and entry 021 says they do
**2026-09-08** · **Raised by** setting · **For** core · **Status** resolved by 033

Found while merging `setting/bible`, which touched the section above this one and could not help
reading it.

The last paragraph of `README.md`, under **What is not built yet**, opens *"Nobody goes and
looks"* and closes *"That is next."* It then describes the three-faced hole in full: a unit that
knows about nobody stands still all battle, no unit can move to gain a line of sight, and being
heard costs the shooter nothing when the listener is behind a wall.

Entry 021 says all three are fixed. `Tactician.Known` builds a threat from a marker as well as
from a sighting, two sides that start out of contact find each other and fight on a noise alone,
and `Battle.Loudness` with `AwarenessTracker.WouldHear` closed the third. Build order 04 is done.

**Why it is worth an entry rather than a quiet fix.** The paragraph is Core's — it describes the
AI, it was written by whoever built the AI, and a setting session correcting it is the same class
of move entry 015 declined to make about `CLAUDE.md`. It is also not a typo: something has to
replace it, and what the README should now say about beliefs is a judgement only Core can make.
It is the second most-read file in the repository and it currently tells a newcomer that the
headline capability of the project does not exist.

**This is the pattern entry 019 counted and 016 named**, and it has now caught the territory that
closed the entry rather than a bystander. Every stale claim found so far was true when written and
was overtaken by a later entry that nobody carried back to the sentence it invalidated — and here
the invalidating entry and the stale sentence are the same increment, which is the tightest the
loop has ever been and still did not close. Nothing to conclude from that except that the
re-read has to happen when the entry is flipped, not later.

**One thing the same paragraph gets right and should keep.** The reason the hole was deliberate —
*acting on the real position of a unit you have lost track of is exactly the cheating the whole
scheme exists to prevent* — is still true, and is now the argument for why threats are built from
a marker with a credence rather than from the field. It is worth keeping the sentence and changing
its tense.

## 029 — After four merges: the map caught up, and what stands between here and a playable greybox
**2026-09-08** · **Raised by** master · **For** all · **Status** resolved

Four branches merged on one day — `core/beliefs`, `view/interface-readouts`,
`content/map-format`, `setting/bible` — and each left something for Master. This entry records
what was done about them, and one shape decision the build order did not have.

**The map, brought up to date.** Content's Owns column now lists what exists under `content/`,
and says its tests live there rather than in `tests/` (entry 024). `README.md` and `Hexcom.sln`
are named as the two shared files. Art's gate is down to the asset spec alone, since 025 gave it
the visual register. Strategy's gate is no longer the campaign shape, which 027 answered, but the
two things a campaign frame needs underneath it: a battle that can end some way other than
elimination, and a mission file. No strategy doc yet, because there is no brief to put in one.

**Statuses.** 004 stays open with its shape answered by 022. 006 stays open with its gate
lifted by 024. 024 and 027 are resolved for Master here. The rest were flipped by the sessions
that closed them, which is the scheme working.

**Routed.** 028 into Core's brief, first thing on the branch. 022 and 026 into the paragraph
after Core's brief, so they are the next Core job rather than the greybox. 006 in View's brief now
says the map has landed and loading it is the first half.

**The shape decision: objectives go in the build order between 05 and 06.** Entry 021 found that
the AI has nothing to search for once it can see nobody, and named an objective system as the
thing it most needs next. Entry 026 found the current end condition — elimination — is the
one the design makes hardest to reach, and that the withdrawal condition needs no new rules.
Those are the same finding from two sides, and the build order has no item for it. A greybox
with no way to win in it is a blockout of a sandbox, not of a game. So: **what an objective is,
and how a battle ends, is Core's, as rules. Which objective a mission carries, and where, is
Content's, as content, and the mission file is the second thing the `.hexmap` format
deliberately left out.** Core owns `design.html` and should add the item; this entry is the
argument for it.

**The road to a playable greybox, written down once so the briefs can cite it.** Playable means:
a person drives one side against `Commander`, on a map loaded from `content/`, with somewhere to
start and something to win, placing their own reactions, with the whole weapons table in play.
In dependency order:

| | Territory | What it produces | Entry |
|---|---|---|---|
| 1 | Core | grenades and mines, melee reach, the shout action | 008, 012, 020 |
| 2 | Core | the open window: `Commit` / `Resolve`, declining, `TakeTurn` handing back outcomes | 004, 022 |
| 3 | Core | a battle that ends on an objective, withdrawal first | 021, 026 |
| 4 | Setting | the mission book, so the mission file is written from fiction | 026 |
| 5 | Content | the waystation fought over, and the first measured balance findings | 007, 024 |
| 6 | Content | a mission file: deployments, facing, objective, exit | 024, 026 |
| 7 | View | a capture that can act; the waystation loaded; the cone at its true reach | 006, 024 |
| 8 | View | placing your own reactions, once 2 lands | 022 |
| 9 | View | the greybox, build order 06 | — |

Rows 1 to 3 are sequential on Core. Rows 4 to 6 run beside them; 6 waits on 4 and on 3 for what
an objective is. Rows 7 and 8 run beside everything; 8 waits on 2. Row 9 waits on all of it, and
`view.md` already says the greybox rewrites `game/` substantially, which is why nothing in rows 7
and 8 should be built as though it will survive that rewrite untouched.

---

## 030 — The mission book is written, and the withdrawal condition needs two things entry 026 did not see
**2026-09-08** · **Raised by** setting · **For** core and content · **Status** open

[setting/missions.md](setting/missions.md) exists: the six shapes of entry 026 turned into what
a soldier is actually told, what winning is in quantities the rules already have, and what the
ground has to offer. Row 4 of entry 029's road to a greybox.

**The bible's last open question is closed, and the answer relocates it rather than building
anything.** *Can a mission be failed without the squad being destroyed?* Yes, and the failure is
the objective becoming unreachable, never the casualty count. A battle wants three endings rather
than two — achieved, settled against you, and stopped being reachable and everybody came home —
and the third is the commonest honest outcome of quiet work. **Casualties are the campaign's to
grade and it already has the data**, since entry 027 records that soldiers persist and plate never
recovers, so the roster is the measurement. Nothing tactical should weigh a dead rifleman against
a records core, and specifically it should not be made to, because the only thing in the code that
prices a soldier is `UtilityModel` valuing them at their own vitality — the figure the bible
already records the fiction as disagreeing with. So the six shapes are win conditions and not
scoring models.

**Two things about the withdrawal condition, checked against the source rather than assumed.**
Entry 026 said it needs no new rules at all. The awareness *measurement* needs none, and that
holds. The *ending* needs two small things, and both are the kind that is cheaper to know about
before the code is written than after.

1. **Today, leaving is indistinguishable from being wiped out.** `Battle.Withdraw` sets
   `InPlay` false, `SidesInPlay` filters on `InPlay`, and `IsDecided` is true when at most one
   side is left. So a squad that successfully walks off the map ends the battle in exactly the
   state a squad that was killed to the last man ends it. Whatever ends a battle on an objective
   has to tell the two apart.

2. **`Withdraw` calls `Awareness.Forget`, so the evidence is gone by the time anybody could poll
   for it.** A condition of the form *leave with the whole hostile side still at Unaware or
   Suspicious*, evaluated after the squad has left, reads Unaware for everybody, trivially and
   always. The reading has to be sampled per soldier at the moment of departure, and the worst
   sample kept.

   **And it should be sampled that way rather than kept as a global high-water mark**, because
   `Forget` is also what makes the best move in the game work. A unit going down is put through
   `Withdraw` by `Battle.Fire`, so silencing a witness really does take his contact out of the
   world — with no new rules, today. A monotone global mark would forbid that. A per-departure
   sample keeps it, and keeps its counter-play too: if he relayed before he died, his side holds
   0.6 of what he had and that survives him.

**Two costings in entry 026 come down.** Reconnaissance was costed at *an objective node, and a
record of whether it was ever traced*; the record is two calls that exist —
`SightSolver.Trace` from the soldier's vantage to a vantage at the place, and
`AwarenessTracker.IsWatching(observer, place)` for the front cone at acuity 1.0 rather than the
corner of the eye at 0.45. Denial was costed at *the mirror of the others, plus a clock*; the
clock is `Battle.Round`, which counts already, so what is wanted is a round limit that ends a
battle rather than a clock to read.

**For Content, the four things a mission needs that a map deliberately cannot hold** — entry 024
left this open on purpose and the fiction now has an answer. Somewhere to start, *with facing*,
because 1.0 against 0.45 means a deployment that faces the wrong way has made a decision on the
player's behalf. Somewhere to end, which is **a named place and not an edge**, because the person
meeting you there has to be able to find it. Something to do. And when it stops.

**And one measurement, off `waystation.hexmap`, at 1.73 m between centres.** The barn is 14 hexes
from the compound centre and the watchtower 16 — 24.2 m and 27.7 m, both outside the 15 m a shout
carries and the 18 m a slug rifle is heard at. So a detail split across that map genuinely depends
on its set, and `AwarenessTracker.CanReach` is what makes the signaller worth killing rather than
anything in the fiction. The compound, at 20.8 m across, has every point within earshot of every
other: it can carry the withdrawal win condition today, and it cannot make an alarm or a clock
mean anything.

**The mission clock is the one genuinely new thing the six shapes want**, and there is no channel
that leaves the map for it to hang on. `Relay` fires at `AlertedAt` and `CanReach` sends it
side-wide only for a unit with a set; a relayed contact arrives at 0.6, so 75 becomes 45 and lands
below Searching, which is the bible's *a bearing, not a target* as arithmetic. What is missing is
anything that records the moment a hostile with a set has registered somebody and had a turn in
which to use it. Everything in that sentence but the record is a query that exists.
---

## 031 — Melee means adjacent, and the movement graph is the instrument
**2026-09-08** · **Raised by** core · **For** all · **Status** resolved

Entry 008 asked for one of three things — reach measured along the ground, an adjacency test, or
a flag on `WeaponProfile` letting the graph answer — and said content had no view on which. It is
the third, and it is the third because entry 008 itself made the argument against the first two:
*a number in metres is the wrong instrument*.

`WeaponProfile` now carries a `Reach`, either `Ranged` or `Adjacent`. A ranged weapon is measured
as it always was. An adjacency weapon is not measured at all: `Battle.InReach` asks
`Battle.Adjacent`, which asks the movement graph whether the two nodes are one traversal apart.
`PowerBlade` is the only adjacency weapon so far; its two range figures stay on the profile as a
description of an arm and nothing reads them.

**Why the graph rather than the grid.** Because the graph already knows everything the answer
needs, and knows it for the same reasons melee should care about it. There is no link through a
building face, so a blade does not reach through one. There is no link up a three metre face,
because `MaxClimb` is 2.2, so a blade does not reach a man on a roof. There *is* a link up a two
metre ledge and over a waist-high wall you could vault, so a blade reaches both. That is exactly
the behaviour entry 008 asked to preserve — *you can stab someone on a low ledge and not someone
on a roof* — arrived at on purpose rather than by accident, and it is pinned by a theory at 2.0 m
and 3.0 m in `OrdnanceTests`.

**What this closes.** Entry 008, and the first of the three items entry 020 routed to Core. The
figures in 008's table are no longer reachable states: the standing-versus-crouching case that
failed by thirteen millimetres is now a question with no millimetres in it. It also removes the
quiet constraint 008 found, where melee alone was voting on the hex size settled by 007 — nothing
about a blade now changes if the hex changes.

**What it costs.** `Gunnery.HitChance` takes an optional `inReach` so that the verdict can be
supplied by somebody with a map, and `Gunnery.RangeFactor` returns one flat for an adjacency
weapon. Both default to the old behaviour, so anything calling `Gunnery` directly about a rifle is
unaffected and anything calling it directly about a blade is asking the wrong question — which is
said in as many words on both.

---

## 032 — There is a ninth home for balance numbers, and four of the eight have moved
**2026-09-08** · **Raised by** core · **For** master, view, content · **Status** open — needs
[map.md](map.md) contract 4 updating

Frozen contract 4 names eight homes plus the kit records. Building grenades and mines changed
five things about that list, and a contract change needs an entry saying what and why. This is it.
Master owns `map.md`; Core owns `design.html` and has updated the section there.

**1. `BlastModel` is new, and is the ninth home.** It holds two numbers: how high above the floor
a charge goes off, and how much of one somebody with no line to the burst still catches. Folding
them into `GunneryModel` was considered and rejected — nothing about a blast is a hit chance, a
range band or a cover penalty, and a record called *the dials on shooting* holding the burst
height of a grenade is a record whose name has stopped describing it.

It is deliberately short, and two things a reader will go looking for are not in it. **Falloff is
not a dial**: a blast runs from full at the centre to nothing at the radius in a straight line,
because the radius is a ring on a map and a player has to be able to read the consequence of
standing inside it off that ring. **What a stance is worth against a blast is not a dial either**:
it is derived from the silhouette heights in contract 6, as `BodyHeight` over the standing one, so
a prone soldier catches a quarter of the wave and the figure moves if the stance heights ever do.
That is the second number in this project derived from a physical constant rather than argued
into place, and it is the pattern to prefer.

**2. `ThrownProfile` joins `Loadout` / `WeaponProfile` / `FireMode` as kit.** A charge is content:
damage, radius, how far it throws, how high it lofts, what it costs, how loud it is. There are
three — a frag grenade, a plasma charge and a claymore — and `Loadout` now carries one kind and a
count of them.

**3. `UtilityModel` gains two.** `ChargeValue`, what it is worth to still have a charge, and
`FriendlyHarm`, what a point of damage done to your own side is worth against a point done to
theirs. The first is not optional decoration: a charge is the first thing in this game that runs
out, and a scorer pricing only the action points threw both grenades at the first soldier it saw.
It measurably did — four commander tests changed behaviour, which is how it was found. Set at
about one clean rifle shot, which is the figure that makes a grenade the answer to the shot you
*cannot* take rather than a better version of the one you can.

**4. `ReactionModel.ShoutCost` has moved to `MovementCosts.Shout`.** Its own remarks said it lived
on the reaction model only while shouting was only ever a reaction, and that it would move across
the moment somebody could do it on their own turn. `Battle.Shout` exists, so it has. There is
still exactly one of it, and `ReactionWindow` reads the new one. This is the second half of entry
012 item 3.

**5. `CostProfile` gains `Posture`.** The note in passing at the end of entry 012 was right and it
was a bug rather than a decision: `Battle.Face` and `Battle.ChangeStance` charged list price while
`Move` and `Fire` went through the profile, so a scout at four fifths movement paid full price to
turn and to drop, against the one rule `core.md` states plainly about prices. Both now go through
`CostProfile.Posturing`, and so does every posture option inside a reaction window — where it
matters most, because what a reactor pays is also how long it takes. The multiplier is one on
every archetype, deliberately: the point is that posture *can* now be priced per soldier, not that
anybody currently is.

**What Master might do.** Update contract 4 in [map.md](map.md) to nine homes and name
`ThrownProfile` alongside the other kit records. Nothing else in the map is affected; no path
ownership changed.

---

## 033 — Grenades and mines have landed, and a charge is aimed at a place
**2026-09-08** · **Raised by** core · **For** view, content, master · **Status** resolved

Build order 05 is done. Two new queries, two new turn actions, one new thing on the reaction
timeline, and the AI takes all of it. What follows is what the other territories can now draw,
author and rely on.

**The arc is a second trace, and it lives beside the first.** `LobSolver` shares
`SightSolver.Crossings` — now public, and a public `WallCrossing` record with it — and parts
company immediately after: sight asks whether the top of each wall is above the *line*, an arc
asks whether it is above the *parabola*. The free parameter is the apex above the straight line
between hand and landing point, and a soldier throws as flat as the obstacles allow, so the solver
takes the lowest apex that clears everything and the thing fails only when that exceeds
`ThrownProfile.MaxArc`. On open ground the apex is nought and the arc degenerates into the sight
line, which is a useful thing to be able to check.

The consequence worth knowing before drawing it: **the closer you are standing to the wall, the
higher you have to throw**, because the divisor collapses toward the ends of the throw. Hugging a
three metre wall and throwing seventeen metres needs seven and a half metres of arc and fails; the
same wall halfway along the same throw needs about two. A throw that fails drops on the near side
of the wall it clipped, which is usually at the thrower's own feet, and `LobResult` says which
wall and how much arc was wanted. **View wants both**: the arc is worth drawing, and a preview
that does not show a clipped throw is a preview that lets a player grenade themselves.

**A blast is not a shot and does not pretend to be.** `BlastPlan` has a landing point and a list of
everybody caught rather than a target and a hit chance. It cannot miss. Underneath, it goes
through `Protection.Preview` face by face like everything else and reports a `ShotExpectation` per
soldier, so the scorer weighs a grenade against a snap shot in one currency. Nothing glances:
obliquity models a solid object skipping off a plate it met edge-on, and crediting a blast with
that would be borrowing arithmetic about something else.

Three things fall out of geometry already in the game rather than out of new rules. The burst
traces *outward* to each victim, so a wall shelters you from a charge on its far side and does
nothing at all about one lobbed over. Fragmentation is kinetic and a shaped charge is beam, so
which one to throw depends entirely on what they are wearing — the ordering flips between a
shielded target and an armoured one, and a test pins both directions. And going flat quarters what
you catch, off the silhouette heights.

**A mine is an overwatch nobody is standing behind, and that is the implementation.** It resolves
inside the same `ReactionWindow`, at the tick the mover's foot lands on its tile, on the same clock
and in the same order — the terrain goes first where a mine and a placement land together, because
a mine is the mover's own foot arriving and everybody else had to decide. It needed no mechanism,
only an owner: `ReactionWindow.Mines` and `.Detonations` sit beside `Offers` and `Resolutions`
because there is nobody to offer a mine to. A move across one fires with no reserve anywhere on
the field, which is the thing an overwatch cannot do.

**For Content.** `Battle.LayMine` places one under the active unit and `Battle.MinesOf(side)` is
the query that respects contract 3 — `Battle.Mines` reports the ground, `MinesOf` reports what one
side is entitled to see, and the interface must use the second. Mines are laid during a battle
rather than authored on a map, so nothing in the `.hexmap` format is affected; whether a mission
can start with a minefield in place is a mission-file question and this entry does not answer it.

**For View.** Three new orders can come back from `Commander`: `Throw`, `Shout`, and — through
`Battle.LayMine` — nothing, because the AI deliberately does not lay mines. Also new and squarely
interface: `Battle.WouldAnnounce(ShotPlan)` and `WouldAnnounce(BlastPlan)`, which is entry 012
item 2 closed. The preview existed on the tracker and nothing said so; there is now one call for
what a shot or a burst would tell the other side, in the shape the scorer already prices it in.

**Two behaviour changes worth expecting.** A commander given a charge and an enemy behind a wall
throws it rather than walking round, which is right and changed four existing tests — they now
deploy a rifleman with an empty pouch, so that a test named after flanking goes on exercising the
flank. And **a commander will throw at a marker**, unlike a shot, which it never takes at one. The
asymmetry is not an oversight: `Battle.Fire` resolves against where the target really is, so
carrying out a shot at a marker would have the battle correcting the guess for free, whereas a
throw is aimed at a piece of ground, the ground does not move, and if he left then the grenade is
simply wasted. The decision is made on the belief and the world answers it.

**And an explosion is heard from where it went off.** `AwarenessTracker.Hear` has an overload
taking the place separately from the source, because until something made a noise at a distance
the two were the same. Everybody in earshot marks the *thrower* at the crater, which is wrong and
is meant to be: it is the one way in this game to make a great deal of noise somewhere you are
not standing, and the scorer can see that it is cheap. Being blown up does not tell you who did
it, unlike being shot at.

---

## 034 — Four things found building grenades that are nobody's job yet
**2026-09-08** · **Raised by** core · **For** core, master · **Status** open

Recorded rather than built, per the brief. None of them blocks anything.

**1. A noise has to be about a person, and a mine's may not be.** The detection model holds
contacts per observer and subject, so `Hear` needs a `Unit` for the bang to be attributed to. A
mine carries the id of whoever laid it for exactly this reason — and a mine laid by somebody who
has since gone down is therefore heard by nobody at all. That is a real hole and the patch for it
is not in `Mine`: it wants a noise channel with no subject, which is a contact about a *place*
rather than about a soldier. That is also what an explosion, a door and a falling body all
actually are.

**2. Nothing spots a mine.** They do not trigger on the side that laid them, which is a
simplification standing in for the awareness ladder having no opinion about objects. A minefield
you laid and had to retreat through is a good situation and this throws it away, and the reason it
is here is that the alternative — a squad walking into its own charges with no way to be told
about them — is worse. Spotting one wants a contact about a place, which is item 1 again.

**3. The AI does not lay mines, on purpose.** `Commander` generates throws and not mine-laying.
Laying is a bet on ground somebody will cross later, and choosing the tile is exactly the question
a unit that knows about nobody cannot answer — the same hole entry 021 named and entry 029 routed
into the objective work. A mine wants an approach to deny, and an approach is an objective seen
from the other side. So it waits on objectives rather than on a search.

**4. A throw is only ever aimed at the tile under somebody.** Offsetting the landing point to
catch two enemies at once, or to keep one of your own out of the radius, is a real decision and a
real search: every node within throwing range crossed with everybody in the blast, per candidate,
per decision. What is built counts allies inside the radius at what they are worth, so a commander
will *decline* a grenade that would catch its own; it will not go looking for the throw that
avoids them. Same shape as every other limit of a one-step search, and the same profile-first
advice applies.

---

## 035 — The waystation is loaded and the attention cone is drawn at its true reach, because the view learned to move
**2026-09-08** · **Raised by** view · **For** view, content and core · **Status** resolved; closes 006, and 024's half for View

Entry 006 said the attention cone reported a soldier's direction honestly and its range not at
all — 3.4 hex radii, picked because it looked right, against an `AwarenessModel.SightRangeMetres`
of 45 metres it had no relation to. It said the honest version could not be drawn, because at the
viewing distance of the day 45 metres was 1980 pixels against a 1600 pixel viewport, a
screen-filling wash showing nothing. It said to come back when the metres-per-hex figure was
settled. Entry 007 settled it and entry 024 supplied a map big enough for it to matter.

**Both were necessary and neither was sufficient. The missing half was a camera.** 45 metres is
only a wash if you insist on standing four metres from the map, and the sandbox did, because it
had never needed to do otherwise — the demo compound is radius 6 and fits on a screen twice over.
Seen at the zoom the whole waystation fits in, the honest field is about half the width of the
map, which is what it is. The cone was never too long. The view was too close.

**What is drawn now.** Not a wedge with a different number in it. `AwarenessTracker` says two
things the old shape said neither of:

- **Attention is graded.** `AttentionOn` gives the front arc its full rate, the peripheral band
  `PeripheralAcuity` of 0.45, and everything behind `RearAcuity` of 0.08 — not nought, because
  people do turn round. The gap between the last two is the entire reason flanking works.
- **Range tells against you gently and then sharply.** `LookGain` scales by `1 - (d/range)²`.

So the field is the product of those two terms, in six rings across four arcs, out to the sight
range, with a circle marking where a look stops being worth anything at all. Nested sectors
rather than annuli, outermost first, each filled at the alpha that brings the composite to the
model's value for that ring — sectors are convex and Godot fills them exactly, and the
arithmetic is one line. The held arc gets the same treatment against a different number: an
overwatch has no range of its own, it just needs a shot, so it is drawn to
`WeaponProfile.MaxRange` with the optimal band marked inside it. A slug rifle holds an arc 55 m
deep and a pulse carbine 42. On the compound both reached clean off the map.

**The camera is `SandboxCamera`, and it holds the scale.** Zoom is `SandboxScale.HexPixels` and
is rebuilt on every notch; `MetresPerHexSize` is a constant and is never touched, which is
contract 5 restated as a class boundary. The node's own `Position` is the pan, which is what the
single `Position = viewport / 2` in `_Ready` already was for a map whose middle was the origin.
Wheel, middle-drag, arrows, `+`/`-`, `F` for the whole map, `G` for whoever is up. The camera
changes what is drawn and never what is true, so moving it queues a redraw and re-asks the rules
nothing.

**Two legibility judgements are in here and they are judgements, not physics.** Eighteen hundred
tiles cannot all carry a cost label at a size anybody can read, so below 22 pixels to the hex the
tile detail goes — labels, the grid, the dead-ground wash — and the ground, the walls, the cover
outlines and the soldiers stay. And every soldier attends to everything within 45 m at some rate,
so seven fields at one weight is a wash whatever the falloff does: the active soldier and every
hostile are drawn at full weight, our own idle soldiers faintly. Both are about which of several
true things a reader is being asked to read, which is interface work. Neither changes a number.

**The waystation is what the sandbox opens with.** `Hexcom.Game` references `Hexcom.Content` and
the map is `MapLibrary.Load`, so `DemoMaps` is no longer called from `game/` at all — the
compound is still there, still reachable as `--scenario compound`, and now loaded by name from
`content/maps/compound.hexmap` rather than built in C#. That is 024's *For View* paragraph done.
The deployments are still hard-coded, because 024 says the map format deliberately does not hold
them and 029 makes the mission file Content's once Core has said what an objective is. They are
gathered into `SandboxScenario` so that when there is a file to move them to, the move is a
deletion rather than surgery on the node.

**The fight, measured on the opening frame at seed 7.** Three of ours on the west road about 20
hexes out, a garrison holding the crossroads:

| | |
|---|---|
| sentry outside the west gate | 25–27 m; one look at any of ours is worth 35–37 against a `Searching` bar of 50 |
| signaller on the house roof | 35–37 m, and it has the radio, so `CanReach` gives whatever it works out to the whole side |
| rifleman in the watchtower | sees all three of ours and one look is worth **nought** — 54–56 m is past the 45 m sight range |
| the ridge, 1.5 m up | the step onto it is a climb: five hexes and 50 AP of 50, a whole turn, for a firing position that sees the tower at 46 m |
| the bridge | 5 m from the sentry, out of sight of both the roof and the barn, and the loudest ground on the map |

The third row is the one worth keeping. A capture shows the tower's 45-metre circle stopping six
metres short of three soldiers it can see perfectly well; eight passes of `--ai` later the sentry
has gone `ALERTED` and the man in the barn `SUSPICIOUS` off the radio, while the bottom block
says *Watchman (AI): nothing worth doing, banked 35*. What made the tower sit still has not been
traced through the scorer and is not claimed here — the measured fact is the range, and the
readout is what a reader sees beside it. Either way it is a detection model doing something a
smaller map could not have shown, which is what entry 006 was asking for.

**For Content.** Row 5 of 029's table is the waystation fought over. This is a fight on it, and
the figures above are the first taken from one — but they are opening-frame geometry, who can see
whom and what it costs to get somewhere, and not balance findings. Two things did come out of
drawing it that belong to whoever authors the next map. The ridge is reachable in one turn only
at its eastern foot, because the 1.5 m step is a climb everywhere else and the one cut path at
`-8,-6` is well forward; that is a good shape and it is not obvious from the file. And a profile
a map declares for itself gets the default grey wall style, because `BattleView.StyleFor`
switches on well-known ids — the waystation's `hedge` now has a case, and the next map to invent
a profile will be grey until somebody adds one. **A map that brings its own kit brings no colour
with it.**

**For Core.** Nothing needed, one figure recorded. A sight sweep over the waystation's ground
floor is 1804 traces; four consecutive sweeps in one process took 192, 141, 40 and 25 ms, so call
it 25 ms warm and most of the rest jitting. Loading the map is about 140 ms and building the
battle about 50. All of that is comfortable for something that runs on an action rather than on a
redraw, and it is why the sandbox still asks about every tile on the storey rather than only
about the ones on screen.

**What this does not do.** It does not make the capture able to act — that is still the job
`view.md` had, and a picture of one of ours mid-approach with a sentry reacting to it still needs
a hand on the keyboard. It does not touch the greybox, which rewrites `game/` and will want a
camera that is a `Camera2D` rather than an offset on a node.
