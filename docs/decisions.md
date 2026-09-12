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
**2026-09-07** · **Raised by** core · **For** core (with view to say what it needs) · **Status** resolved by 040

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
**2026-09-08** · **Raised by** view · **For** core · **Status** resolved by 040

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
**2026-09-08** · **Raised by** view · **For** core, and master for the statuses · **Status** resolved — View's half by this entry, Core's by 042

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
**2026-09-08** · **Raised by** content · **For** view, core and master · **Status** resolved — core's half by 043;
the decision itself was always made, master's half by 029 and view's by 035

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
**2026-09-08** · **Raised by** setting · **For** core and content · **Status** resolved by 041 for core; content's half open

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
**2026-09-08** · **Raised by** setting · **For** core and content · **Status** resolved by 041 for core; content's half open

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
**2026-09-08** · **Raised by** core · **For** master, view, content · **Status** resolved for
master by 036, which updated contract 4; open for view and content until they read it

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
**2026-09-08** · **Raised by** core · **For** core, master · **Status** open for core — items 1, 2 and 4 are in `core.md`'s open questions; master routed item 3 to build order 05b in 036

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

## 036 — After three more merges: nine homes, Content's brief caught up, and the road to the greybox shortened
**2026-09-08** · **Raised by** master · **For** all · **Status** resolved

Three branches merged since 029 — `setting/missions`, `core/grenades`, `view/waystation` — and
the fourth territory, Content, has not started the brief 029 gave it. This entry records what
Master did about the entries they left, and restates the road, since three rows of 029's table
are done and one has split.

**Contract 4 is nine homes.** `BlastModel` and `ThrownProfile` are in the map and in
`CLAUDE.md`, as entry 032 asked. The pattern 032 named — a figure derived from a physical
constant rather than dialled — is in the contract's text now, so the next person adding a home
sees it before choosing.

**Content's brief was stale without anybody touching it**, which is the rot 029 did not predict:
a brief written before three neighbours merged said the sandbox hard-coded five deployments (it
gathers them in `SandboxScenario` now, and there are six), said loading the map was View's to
offer (035 did it), and said the scenario file waited on the campaign shape (027 settled it).
Fixed, and entry 030's four things a mission needs and entry 035's two authoring notes are in it.
The scenario file now waits on one thing only: Core saying what an objective is, build order
05b.

**Two Core debts had no brief**: the `DemoMaps` deletion from 024, and the contract 3 question
from 023 about a soldier's own certainty. Both are a paragraph in `core/open-window`. Entry
034's third item — the AI laying mines waits on an approach to deny, which is an objective seen
from the other side — is 05b's by construction and needs no separate routing.

**The road from here.** What 029 listed as nine rows is now six, because rows 1, 4 and half of
7 are done and rows 2 and 3 became one Core brief:

| | Territory | What it produces | Waits on |
|---|---|---|---|
| 1 | Core | the open window and a battle that ends on an objective — 05a and 05b, one brief | nothing |
| 2 | Content | the waystation fought over, and the first measured balance findings | nothing |
| 3 | Setting | the roster, so deployments have names on both sides | nothing |
| 4 | View | a capture that can act | nothing |
| 5 | Content | a mission file: start with facing, a named end, a thing to do, when it stops | 1 for what an objective is, 3 for who |
| 6 | View | placing your own reactions, then the greybox | 1, then everything |

Four sessions can start today, one per territory, and none of them collides. The critical path
is still Core, and it is now one increment long rather than two.

**One thing to watch that nobody owns yet.** Entry 030 names a mission clock as the one
genuinely new thing the six mission shapes want — a record of the moment a hostile with a set
has registered somebody and had a turn to use it. Core's brief leaves it to the judgement of
whoever picks the brief up. If it is left out of 05b, it becomes the item after, and the denial
and extraction missions wait on it; the withdrawal mission does not.

---

## 037 — A rifle shot is heard at 18 metres, and the design doc says a hundred
**2026-09-08** · **Raised by** content · **For** core · **Status** open

Measured on the waystation, not worked out from the model: a slug rifle fired at the west gate,
`(-5,0)`, is heard by the sentry standing there and by the spotter on the house roof ten metres
away, and by nobody else. Not by the barn at 24 m, not by the tower at 28 m. The test
`ARifleShotAtTheWestGateIsHeardInTheCompoundAndNowhereFurther` in
`content/Hexcom.Content.Tests/Waystation` pins it, through `AwarenessTracker.WouldHear`.

**The arithmetic behind it.** `WeaponProfile.SlugRifle.Loudness` is 45 and
`AwarenessModel.NoiseMetresPerPoint` is 0.4, so a rifle carries 18 m; the repeater at 65 carries
26 m. A shout (`VoiceRangeMetres`) carries 15. So the loudest weapon in the game is heard about
as far as a man calling out, and the design doc — section 07, and entry 007 quoting it — talks
about *gunfire heard at a hundred*. Two figures, one of them wrong by a factor of five.

**What it does to a fight, seen twelve times.** The garrison at the waystation is split exactly
as the mission book says a detail should be (entry 030): the compound, the barn and the tower are
all outside each other's earshot. So a firefight at the west gate — and in twelve matches out of
twelve there was one, by round 3 — is *silent* in the barn and the tower. Hollis and the Watchman
learn of it only from the roof's radio at `RelayFraction` 0.6, and in the seeds where the spotter
went down early they learned of it not at all: seed 6, Sentry down round 3, Spotter round 10,
Hollis never above Alerted and never moved. That is the radio doing exactly what the bible wants
it to, and it is also a rifle fight at fifty paces that nobody heard.

**Which figure is right is Core's to say, and it is a design question rather than a typo.**
Eighteen metres makes a slug rifle nearly a silent weapon on a map this size, which flattens the
beam-against-slug trade the weapons table is built on: the one cost the design gives a rifle over
a carbine is that it is heard, and at 18 m it is heard by people who could already see the
muzzle flash. A hundred metres makes every shot on an 85 m map heard by everybody, which is the
compound problem entry 030 describes, at scale. Somewhere between — forty to sixty metres, a
loudness of 100 to 150 at the current 0.4, or a `NoiseMetresPerPoint` of 1.0 — is where a shot
at the gate wakes the barn and not the tower, and the *split detail depends on its set* claim in
entry 030 stays true because the set is faster, not because it is the only channel. Content has
no dial to turn here; the number is in `WeaponProfile` and `AwarenessModel`, both Core's.

**One more thing the same factor does, measured the same way.** A move's loudness is the listed
cost of the whole route times the noisiest ground on it (`Battle.Loudness`), through the same
0.4. So nine strides along the gravel road — 45 AP at `noise 1.6` — come to 72, and are heard at
29 m: a soldier *walking down the road* is heard further than a soldier *firing a rifle* on it.
`AWalkDownTheRoadIsHeardFurtherThanARifleShot` pins that. It is not obviously wrong — a turn's
walk is a long noise and a shot is a short one — but it is the kind of thing that should be true
on purpose, and the weapons table reads as though the shot were the louder of the two.

---

## 038 — The waystation has been fought over: twelve matches, none decided, and a map redrawn from the routes
**2026-09-08** · **Raised by** content · **For** core, view and master · **Status** open (core's half, routed into `core/objectives`); view's half answered by 049, master's by 045; the map is redrawn and the brief is done

Row 2 of entry 036's road. `Commander` on both sides, the sandbox's deployments (entry 035),
sixty rounds or a decision, whichever first. The recorder is
`content/Hexcom.Content.Tests/Waystation/MatchRecorder`; `HEXCOM_SEEDS=12 dotnet test` reruns
what follows and prints the routes.

**Twelve of twelve were undecided at round 60, and every one of them was over by round 21.**
The last shot or throw in any match fell between rounds 3 and 21; after that, the survivors
stood where they were for forty rounds. `core.md` predicts this — a search one step deep with
nothing to want is a stalemate once contact is lost — and this is it happening on real ground,
with buildings, at scale. **So the answer to the brief's question, what a match on this map
ends on, is: nothing.** A round cap would be theatre; a cap at 25 would have caught every fight
seen and decided none of them. The ending is the objective, which is Core's 05b, and this entry
is the measurement that says it is not optional.

**What it cost.** A sixty-round match with seven soldiers on 1801 tiles took 11 to 80 seconds,
43 on average, over 270 to 420 turns — call it 130 ms a turn, five to ten times `core.md`'s
figure for three a side on a radius-sixteen disc. A dozen seeds is nine minutes on this machine.
Usable for reading routes; not for a thousand matches, which at this rate is half a day. Nothing
was profiled, per `core.md`'s advice; the number is here so whoever does is not surprised.

**What the routes said about the map, and what was done about it.**

- **The west road was a firing lane.** In twelve matches out of twelve the first shot was
  Bekker's, on round 2 or 3, at the sentry standing outside the west gate 35 m down the open
  road, at a score of +4.35, with every hostile still `Unaware` — the rifle's 55 m outreaches
  the 45 m sight range, and at 35 m a slug rifle announces itself to nobody but the man it is
  fired at (entry 037). *Redrawn:* a tree line along the field boundary at `q = -12` with the
  road through a gap in it, and a sandbag line across the road at the gate. Rerun on six seeds:
  first fire moved from round 2 to round 4 in six of six, and its target moved from the sentry
  at the gate, now hidden, to the spotter *standing on the house roof*, which is visible over
  two-metre trees from 38 m. That is correct — a signaller upright on a roof is a target — and
  it is the roof's problem now, not the road's.
- **The stream was a decoration.** It was one hex of `shallow_water` everywhere, so in every
  match where anybody crossed, they waded — the bridge was used once in twelve. *Redrawn:* the
  stream is `deep`, impassable, and has two crossings: the bridge on the road, in full view of
  the gate, and a ford five hexes from the drain. The cottages, it turned out, stood in the
  stream, and have moved to the west bank.
- **Nobody used the drain, the ridge, the woods or the bridge**, and after the redraw nobody
  uses the ford either. Not a map finding: a commander with no objective has no reason to go
  anywhere it cannot shoot from, and the drain is a route to somewhere, not a firing position.
  Entry 034 item 3 and `core.md`'s first open question, from the map's side.
- **The tower and the barn never move.** Hollis, in the barn, made 0 moves in eleven of twelve
  and the Watchman 0 in twelve of twelve, on the first map; on the redrawn one the Watchman
  came down the ladder in three of six to get a shot at Vance. Both are the *nothing to want*
  hole again, and the only cure the map has is putting a target in their view.
- **Vance never advances.** The blade carrier: 0 to 5 moves a match, all of them dithering at
  the west edge. `core.md` records why; the map cannot help.

**Two things about the AI that the transcripts show and the summaries did not**, each with the
match it was seen in, are entry 039.

**The mission is in the map.** The header of `waystation.hexmap` now carries it in the six-part
shape `docs/setting/missions.md` gives a briefing: an inspection of the compound; a detail of
four, one with a set; enter, confirm what is in the house, come out; not seen, not fired;
starting on the west road with facing, leaving by the cottages, over when somebody properly
registers you and lives to keep it. The deployments are the sandbox's to the hex and the
facing, and the harness deploys the same. **Three copies of one fact, and this entry is the
only thing that says they must agree** until there is a mission file (entry 036, row 5).

**For View.** The map changed under the sandbox: the cottages moved, the stream is impassable
except at `(-8,0)` and `(-6,-4)`, there is a tree line at `q = -12` from `r = -2` to `5`, and
sandbags across the road at `(-5,-1)`, `(-5,0)`, `(-5,1)`. The deployments did not change. The
`deep` ground and `hedge` profile are map-declared kit, and entry 035 says a declared profile is
drawn grey; `deep` is a ground, and whether the view colours grounds by id or by figure is
yours.

**For Core.** Entry 037 and entry 039. And a figure for the brief you have: whatever ends a
battle on an objective, the fights on this map are done by round 21 and would need to be judged
by then.

**For Master.** Row 2 of 036's road is done, and its finding routes to Core rather than back to
Content: the map can be redrawn any number of times and no match on it will end until 05b lands.
Content's next brief is a second battlefield of a different shape, so that the mission file has
two maps to be argued from rather than one — `content.md` says so.

---

## 039 — Two things a search one step deep does on real ground: throws at the crater, and paces
**2026-09-08** · **Raised by** content · **For** core · **Status** open

Both from the transcript of seed 1 on the first map, both visible in the counts across all
twelve, both reproducible with `HEXCOM_TRANSCRIPT=1 dotnet test` in `content/`.

**1. Every charge in the match lands on one empty hex.** Round 3: the sentry steps back from
the gate at `(-5,0)` to `(0,-1)` after Bekker's look. Round 4: Bekker throws a frag at `(-5,0)`,
the marker, and so does Orsini — correct per entry 033, a throw is aimed at a belief. Round 5:
the *spotter* throws a plasma charge at `(-5,0)`, and so does the *sentry*, from five hexes
away, at a hex nobody of ours had ever stood on. They could only have a contact there through
`AwarenessTracker.Hear`'s crater rule: everybody in earshot marks the thrower at the crater
(entry 033, *wrong and meant to be*). Then round 5 again: Bekker's second frag, at `(-5,0)`.
Five charges, one hex, nobody on it after round 3; and *five throws* is the count in nine of
the twelve matches, three or four in the rest, because five is what the two sides carry within
throwing range of that hex. The crater rule was built so that a charge could make noise
somewhere you are not; on this ground it makes each side's charges bait for the other side's,
and a garrison that empties its pouch at a crater on round 5 has nothing left when Bekker walks
through the gate on round 8. On the redrawn map the pattern broke — one to four throws a match,
at places where somebody actually was — because the tree line meant the first grenade was
thrown at a soldier in view rather than at a marker at a gate. Which is to say the map fixed it
by accident, and it is waiting on the next map to come back.

**2. A soldier paces between two tiles on a shot it never takes.** Seed 1, rounds 13 to 18,
Bekker at `(-1,1)` and `(-1,2)` inside the compound: seven moves a turn, alternating between
the two, scored +25, +12, +22, +9, +17, +4 and falling — every move ranked on the shot at the
spotter it would open, and from the new tile the best option is the move back, ranked on the
same shot. No shot fired in six rounds. Orsini did the same at `(-8,-2)` and `(-9,-2)` in the
same match, rounds 13 to 15, while the Watchman shot him from the tower every round until he
went down. `Order.Opens` is the lookahead crediting a move with a shot; what is missing is the
move *costing* the shot it displaces, or the shot being taken when it is the thing the last move
was chosen for. The recorder counts these as *pacing* turns — four or more moves and nothing
fired — and on the redrawn map they nearly vanished (two turns in six matches), which says the
geometry that produces them is specific and not that the search is fixed.

Neither is a balance number. Both are the search's, and both were invisible on a disc.
---

## 040 — The window is a state the battle sits in, and holding fire is an action
**2026-09-09** · **Raised by** core · **For** view, master · **Status** resolved

Entry 004 asked which shape the interface wanted and 022 answered: the split, not the callback.
Built as asked, with two things settled that 022 left to whoever picked it up.

**`Battle.Commit` and `Battle.Resolve`, with `Move` as the two in sequence.** Committing prices
the route, spends the points and builds the window with its offers made and nothing placed. The
mover has **not stepped** — it stands at the start until the window resolves and walks it along —
so anything reading the field while a window is open sees a soldier who has paid for a walk it
has not taken. `Move` is the two with `PlaceRecommended` between them, so every existing caller,
including the turn loop and every headless match, is where it was.

**It returns a `MoveCommitment` rather than the bare `ReactionWindow` 022 named**, and that is the
one deviation from what View asked for. Two reasons, both practical: a refusal has to come back
from somewhere, and `null` loses the sentence a player should be shown; and `Resolve` needs the
route and the price to build the `MoveOutcome`, which the window does not carry. The commitment is
the window plus the receipt, and `commitment.Window` is the thing the HUD draws. **If View would
rather have the window itself, say so and it is a small change** — but a `Commit` that cannot say
*out of reach this turn* did not look like an improvement.

**Declining is an explicit `ReactionAction.Nothing`, not a nullable `Recommended`.** 022 offered
either and `core.md` asked for the choice to be made deliberately. The action wins on three
counts: it is a thing the interface can draw beside the other options rather than a hole in the
list; a player can pick it on purpose; and the scorer prices it at exactly nothing, so *hold fire*
beats every option that scores below zero **by arithmetic**, with no rule anywhere saying it
should. That closes the open question `core.md` carried — a reactor no longer takes a bad answer
because it had to take one. `Recommended` stays non-null, because with holding fire on the list
there is always something to recommend.

**And it is offered only to the deliberate reactions.** An overwatch and an ambush are held shots:
somebody chose to hold them and may choose to keep them, which is exactly the case entry 004
named. Surprise is the involuntary one, and the whole of what it models is that a soldier caught
out does *something* rather than nothing — offering it the chance to do nothing is offering it the
chance not to flinch. Measured rather than assumed: with declining on the surprise list, a
startled sentry stands still, because a dive costs two points and buys a discounted share of one
shot, which on open ground comes out just under nothing. Two existing tests pin the old behaviour
and both were right to.

**The seam reaches through `Commander`, which is what 022 said it had to.** A commander built with
`WindowAnswer.HandedOut` stops its turn with the window open, exposes it as `Commander.Waiting`,
and carries on from `Resume()`. The default is unchanged. `TakeTurn` now returns an `Act` per
order — the order it was chosen on, plus the `MoveOutcome`, `ShotOutcome` or `BlastOutcome` it
produced — which is 022's last item, the one about the sandbox being unable to narrate the
enemy's turn.

**One line changed in `game/`**, at the single call site that reads `TakeTurn`, so the solution
still builds; it maps the acts back to their orders and says why in a comment. Nothing else under
`game/` was touched.

**And a bug that predates all of this, found by building it.** `Commander.TakeTurn` ended the turn
unconditionally when its loop stopped. Three things hand the turn on without the loop asking —
being dropped mid-move, having an ambush sprung on you, and now walking off the field — and in
every one of those the call ended **somebody else's** turn, banking their allowance and passing it
on before they had done anything with it. It went unseen because the only thing driving whole
turns was a headless match, where a soldier that silently loses a turn looks like a soldier that
decided to do nothing. Ending the turn is now conditional on the soldier the commander set out to
drive still being the one whose turn it is, and a test pins it.

---

## 041 — A battle can end three ways, and an objective is a gradient
**2026-09-09** · **Raised by** core · **For** content, setting, view, master · **Status** resolved

Build order 05b. Entry 026 asked whether a battle could end any way but elimination and entry 030
said what the answer had to account for. Both are built, with the withdrawal shape as the one
concrete mission.

**Three endings, and casualties are not a term in any of them.** `Verdict` is `Undecided`,
`Achieved`, `Failed` or `Abandoned` — done, settled against you, or out of reach with everybody
home. The third is the one entry 030 argued for and it is the commonest honest outcome of quiet
work: a squad that is seen has lost the mission and has not lost the squad, and a win-or-die model
reports those identically. Nothing weighs a dead rifleman, because the campaign holds the roster
and already has that measurement.

**Both of entry 030's warnings were real and both are handled.** `Unit.Left` is a `Departure`
carrying how the soldier went — `Down` or `Extracted` — the round, and the reading. Leaving and
dying are no longer the same state. And the reading is **sampled at the moment of departure**
inside `Battle.Withdraw`, before the forgetting, because a condition asked afterwards reads
Unaware for everybody, trivially and always. It is a sample per departure rather than a mark held
across the battle, which is what keeps the counter-play 030 asked to preserve: silencing a witness
takes his contact out of the world, and a test pins that too.

**What an objective is.** An abstract `Objective` with a side, a `Judge` that returns a verdict,
and a `Progress` that says how much of it a place represents. It is the only polymorphism in these
rules and it earns it: the shapes are open, entry 026 lists six, and a record with a field per
kind would rot while a switch over a kind enum would put every future mission type inside
`Battle`. `Withdrawal(side, exit, unnoticed)` is the one concrete kind.

**What it deliberately does not do is put a price on anything.** An objective is a win condition,
not a scoring model — 030's words — so the one exchange rate lives in `UtilityModel` with every
other: `ObjectiveValue`, what doing what you came for is worth, and `ObjectiveHorizon`, how far
away still counts as being on the way. Nothing about which mission it is reaches the arithmetic.

**Progress is a gradient and that is the load-bearing part.** A flag is worth everything from
inside the exit and nothing a pace outside it, and a search one step deep cannot see a place three
turns away, so nobody would ever set off. Sloped over the approach, every stride toward it scores
— the same trick that makes a move to a firing position worth taking. It is measured in action
points along the movement graph rather than in metres across the map, so the far side of a river
reads as far away where the water is narrow, and it is **one backward search from the exit** over
the whole graph rather than one per candidate destination. That needed `MovementGraph.LinksTo` and
`Pathfinder.CostToReach`, both new, both general.

**For Content.** `Battle.SetObjective` before `Start`, and `Withdrawal` takes a collection of exit
nodes — a named place rather than a map edge, as 030 asked. `Battle.Extract()` is the turn action
and it is free: the price of leaving is having walked there. A battle with no objective behaves
exactly as it always did, so nothing existing changed. The scenario file entry 036 says waits on
*what an objective is* is unblocked.

**For Setting.** Of the six shapes, withdrawal is done. Reconnaissance and sabotage want an
objective at a node; extraction wants something carried; denial and capture want the clock and
subdual. The clock is still the one genuinely new thing and is still nobody's — see below.

**For View.** `Battle.VerdictFor(side)`, `Battle.ObjectiveOf(side)`, `Objective.Brief` for words
to show, and `Unit.Left` for why somebody is off the field. `IsDecided` is now true when an
objective settles, however many soldiers are still standing, and falls back on the last-side-
standing rule for a battle nobody gave an objective to.

---

## 042 — Contract 3 has a third case, and it reads exactly
**2026-09-09** · **Raised by** core · **For** view, master · **Status** resolved — contract 3 in `map.md` says so since 045

Entry 023 asked, and it is in section 07 of the design doc now. Contract 3 named two cases: your
own exposure, exact; the enemy's alarm, a rung. **What your own soldier holds on an enemy is a
third, and it is read exactly.**

The principle underneath the split is not what the number is *about*, it is **whose knowledge it
is**. Your side's knowledge is yours, in both directions, and blurring what your own soldier has
worked out would be fog about yourself — which contract 3 already rejects in as many words for
exposure. The other side's knowledge stays coarse in both directions, and the marker they hold on
you is the one thing of theirs you see at all.

So View may draw *how much is still left to learn about this contact* as a figure. `map.md`'s
contract 3 is a sentence short of saying this and Master may want to add it.

---

## 043 — `DemoMaps` has no callers in `tests/` and Content may delete it
**2026-09-09** · **Raised by** core · **For** content · **Status** resolved for core

Entry 024's half for Core. `DemoMapTests` and the three tests in `SightTests` now read
`MapLibrary.Load("compound")`, so `tests/Hexcom.Core.Tests` references `Hexcom.Content` and
nothing in `tests/` calls `DemoMaps` any more.

**The choice between the two offers.** Entry 024 offered either this or keeping a hand-built map
in Core with the two held equal by test. Loading won on a reason beyond tidiness: the pipeline
`DemoMapTests` checks end to end now starts at the text a person actually writes, which is a
strictly better fixture. The test *assembly* referencing Content does not touch *Core is the
trunk*, which is a statement about the library.

**Content's move.** `src/Hexcom.Core/Maps/DemoMaps.cs` is untouched here, because deleting it
would also break the Content test that holds the two maps equal, and both of those are yours. Both
can go together whenever you like.

**Also from 024:** the masthead in `design.html` counted one test assembly and now names both.

---

## 044 — Two things this branch found and did not build
**2026-09-09** · **Raised by** core · **For** core · **Status** open

**1. An objective is worth more than any fight, and that is set by argument.**
`UtilityModel.ObjectiveValue` is a whole squad's worth of vitality, deliberately larger than
anything a shot can score, so a squad told to get out walks out through fire rather than stopping
to trade. That is the behaviour the complaint about elimination was asking for, and it is also the
first number in this game that can make a soldier ignore what is happening in front of it.
`ObjectiveHorizon` decides how far the pull reaches. Neither has been measured, both are exactly
the sort a batch of headless matches settles, and the failure modes are legible: a squad that
walks past a firefight to reach an exit means the value is too high, and one that stands in a
firefight ignoring the exit means the horizon is too short.

**2. Nothing between an objective and the marker.** The gradient fixes *reaching* for a soldier
with somewhere to be; it does nothing for one hunting a contact, which still reaches about one
move because a marker is a point and not a slope. The two are the same shape of problem seen from
either end, and the fix for the second is a deeper search rather than another gradient — a marker
that sloped would send soldiers walking at ghosts from across the map, which is the thing
`MarkerDecay` exists to prevent.

## 045 — Build order 05 is done end to end, the reading rule has changed, and sessions now say what they were
**2026-09-09** · **Raised by** master · **For** all · **Status** resolved

Three branches merged since 036 — `content/first-battlefield`, `core/open-window` carrying both
05a and 05b — and the road to the greybox is now View's and Content's rather than Core's. This
entry records the routine, and two changes to the scheme that are not routine.

**Routine.** Contract 3 in `map.md` names the third case entry 042 found. Entry 004 is closed by
040, the oldest open entry in the log and the first API designed for an interface that did not
yet exist. View's brief no longer
says reaction placement waits on Core: 040 built the seam, and the brief names `MoveCommitment`,
`ReactionAction.Nothing`, `WindowAnswer.HandedOut` and `Act` so View reads one file. Content's
brief inverted: it said the mission file waited on 05b and a second map could go first; 05b
landed, so the mission file is the job and the second map is after it, and the two sentences
that said `DemoMaps` still served Core's tests now say 043 let it go. The `deep` ground and the
`hedge` profile from 038 are in View's brief.

**Not routine, one: the reading rule.** `CLAUDE.md` and `map.md` said read every doc. The docs
are now 460 KB, the log alone is 135 KB and 44 entries of which five are open, and every new
session was paying to read the resolved thirty-nine. The rule is now: the map and your own doc in
full; of the others, `## Owns` and `## The job`; of the log, the open entries and any your brief
cites; of the design doc, the section the job touches. The briefs were already written to be
sufficient prompts — `master.md` says so in as many words — so this is the scheme being used as
designed rather than a change to it. What it costs: a session may miss a neighbour's gotcha that
would have saved it an hour. The cure is the existing one, an entry, and the brief-writer's job
of naming what the job depends on gets slightly more important.

**Not routine, two: a `Session:` trailer.** The user asked that each session record, for Master,
whether it was fresh or continued and what model it ran on, so that the next job can be pointed
at the cheaper of the two. The model was already in every commit — the harness adds
`Co-Authored-By: Claude Opus 5` or `Claude Fable 5.1` — and continuity was not recorded
anywhere. It is now a trailer on the last commit of a branch, `Session: new` or
`Session: continued, job 3`, and `master.md` has the `git log` format that reads both. A
trailer rather than a line in a doc because *status is derived*: it cannot go stale, it cannot
be forgotten to be deleted, and it sits beside the thing it describes.

**The recommendation this round**, so it is written down once and can be checked against the
next set of trailers. Core has run two jobs on Opus in one session and its next brief continues
on the same files; keep it. Content has run two on Fable, and its next job is a file format with
a sufficient brief; start fresh on Opus, because a continued Fable session pays the dearer rate
on a large context every turn, and a cold start on Opus pays once. View has run one job on Opus
and its next is in the same files; keep it. Setting is prose with a sufficient brief; Opus,
fresh or continued as it stands. The greybox, when it comes, is a fresh session on Fable: it
rewrites `game/` and re-asks the View split.

**The road, restated.** Four rows, and Core is off the critical path for the first time.

| | Territory | What it produces | Waits on |
|---|---|---|---|
| 1 | Content | the mission file, and `DemoMaps` deleted | nothing |
| 2 | View | a capture that can act, and placing your own reactions | nothing |
| 3 | Setting | the roster | nothing |
| 4 | Core | the rest of the mission shapes, the clock, and the first measured numbers | nothing, and nothing waits on it for the greybox |
| 5 | View | the sandbox loads the mission file | 1 |
| 6 | View | the greybox, build order 06 | 2 and 5 |

Rows 1 to 4 can all start today. The greybox is two View increments away, and the second of them
is the one that rewrites the directory.

---

## 046 — The roster exists, the posts are not names, and the two cost profiles have no soldiers

**2026-09-09** · **Raised by** setting · **For** view, content, core · **Status** open — routed by 050: the names to Content's brief, items 3 and 4 to Core's, and View's line to its brief

[setting/roster.md](setting/roster.md) is written: twelve people a side, each of them a
`UnitStats`, a `CostProfile`, a `Loadout` and three sentences, with nothing invented and nothing
proposed. Four things came out of writing it that belong to somebody else.

**1. Three of the seven strings the sandbox deploys are posts rather than names, and the split
runs along the side line.** Vance, Orsini, Bekker and Hollis are people; Sentry, Spotter and
Watchman are the road outside the west gate, the roof with the set, and the tower. That is the
asymmetry section 4 of the bible spends a page denying — same armoury, eleven years apart — and
it is the one thing in the project that makes the hostile side read as obstacles.

The roster **adopts every name already in the code and changes none of them**, because adopting
is cheap and a name has no properties to get wrong. What it adds is who stands each post:
**Sentry is Cobb, Spotter is Teague, Watchman is Marek.** Section 6 of the roster is the table,
with the numbers each is already carrying beside it.

Nothing depends on this and nothing breaks until somebody does it. It is three string literals in
`game/scripts/SandboxScenario.cs` and the matching four in the header of `waystation.hexmap`, and
the right moment is whenever either file is open for another reason. The post words stay useful
either way: *the sentry outside the west gate* is how you describe a place you have not been to.

**2. A mission file that lists a squad can take it out of the roster whole.** Sections 4 and 5
are twenty-four soldiers written in exactly the form `Battle.Deploy` takes — a name, an
archetype, a loadout — and section 6 maps every soldier the sandbox currently fields onto one of
them. There is no format question here for Content to answer; the names are simply available.

**3. `CostProfile.Scout` and `CostProfile.Gunner` have no soldiers.** Verified across `src`,
`tests`, `game` and `content`: `CostProfile.Gunner` appears once, in `ReactionTests`, and
`CostProfile.Scout` appears nowhere at all. `UnitStats.Scout` and `UnitStats.Trooper` both run on
`CostProfile.Default`, so no unit the game deploys pays anything but list price for moving or
firing, and the record's own remarks — *this is what lets a scout and a heavy trooper spend the
same ten points on different things* — describe something that has never happened in a battle.

The roster writes Vance as `UnitStats.Scout with { Costs = CostProfile.Scout }` and Orsini as
`UnitStats.Trooper with { Costs = CostProfile.Gunner }`, because those two soldiers are plainly
what the two profiles were written for. **That is a suggestion and not a request**, it changes no
file this territory owns, and everything reads correctly with it ignored. Whether the archetypes
should carry the profiles by default is a balance question and therefore Core's.

**4. The fiction has put its money down on what the signaller is worth**, which
`UtilityModel.RemovalBonus` lists as open and values at a soldier's own vitality. The roster's
answer, in its section 3, is not a number:

- **The set goes to the worst-armed observer on the detail**, never to the best-protected
  soldier. `UnitStats.Signaller` is Perception 12, Encumbrance 1 and not one point of action or
  initiative above ordinary, which describes an observer carrying an awkward thing and describes
  nobody else. `Radio` is settable on any archetype and the roster deliberately never does it.
- **The order to use it comes from somebody else**, so the commander and the set are two people
  who must stay inside line of sight or the fifteen metres of shouting
  `AwarenessTracker.CanReach` allows. That tether is the shape of every position either side
  takes, and it is why splitting a detail across the waystation — the barn at 24 m, the tower at
  28 — costs something real.
- **What a quiet kill buys is measured and already built.** Before anything reaches `AlertedAt`,
  killing the set removes the channel outright, and `Battle.Withdraw` calls `Forget`, so what he
  knew goes with him. After it, his side already holds 0.6 of what he had, and 0.6 of 75 is 45,
  under Searching at 50. Either way the detail must close up to within a shout of itself, which
  is a garrison giving up most of its ground voluntarily.

None of that asks for a rule. It is the argument for why removing one particular soldier is worth
more than removing the rifleman beside him, stated in quantities that already exist, so that
whoever eventually weights `RemovalBonus` has something to weigh rather than an assertion.

---

## 047 — A mission is a file of its own, and the waystation is now written down once
**2026-09-09** · **Raised by** content · **For** view, core, setting, master · **Status** resolved

Row 1 of entry 045's road. `content/missions/waystation.hexmission` exists, `MissionFile` reads
it, `MissionWriter` lowers it, `MissionLibrary.Load("waystation")` ships it, and `Mission.Begin`
hands back a battle deployed, ordered and started. `DemoMaps.cs` is gone.

**It is a separate file, not a block in the `.hexmap`, and here is the case.** Entry 024 kept the
map to ground on purpose and called a separate file plausible; the brief said the deciding case
was one map carrying two missions. That case does not need waiting for, because two weaker ones
are already here and point the same way. **A map with no mission has to stay legal** —
`compound.hexmap` has none and never will, since it is the fixture the view diffs its captures
against, and a mission-in-map format makes every such map look like one with something missing.
**Ground outlives missions**: a map is drawn once and edited rarely, a mission is per-run and, in
a campaign, generated. And the original case stands on its own: the waystation is a crossroads
and all six shapes in the mission book could be fought over it.

**What is shared is the lexer and not the reader.** One statement per line, `#` to end of line,
`q,r` and `q,r@layer`, `ne n nw sw s se`, and an error that names the file and the line — those
are in one place now (`TextFormat.cs`), and `MapFile` was moved onto it. The statements are
disjoint and the two readers are separate, because a shared reader would need a statement table
keyed on which kind of file it was halfway through. The rejected alternative was copying the
cursor, which would have left two tokenisers to drift apart in exactly the way this entry is
about.

**What the file holds** is entry 030's four things plus the squads: `deploy` with a facing,
`place` for named ground, `objective` for the thing to do, `rounds` for the clock, and `brief` in
the mission book's six parts. All six briefing parts are **required**, which is the whole moral of
entry 038 turned into a rule — three copies of one mission drifted, and what let them was that
none of them had to be complete.

**All six mission shapes are names the grammar knows and only withdrawal builds.** The other five
are refused with *this is one of the six shapes and the rules only have withdrawal so far*, which
is a true and useful thing to be told where "unknown statement" is neither. So the format needs no
change when Core adds one — only a new `ObjectiveOrder`.

**Roles and kits are named, never declared.** `scout`, `trooper`, `signaller`; `rifleman`,
`beamer`, `heavy`, `infiltrator`, `sidearm`. A file that could write out its own action points
and plate would be a balance change hiding in content — the same line that lets a map declare a
hedge and not redefine what `low` means. `content.md`'s open question about where balance numbers
live is unchanged by this and not answered by it.

**The three copies are one.** The prose header in `waystation.hexmap` is gone, replaced by what
is genuinely about the ground; `WaystationFight` in the harness is now a name and one call. The
third copy is `SandboxScenario` in `game/`, and it is View's — see below.

**Two stale references this leaves, both outside Content and both one line.** The remarks on
`DemoMapTests` in `tests/` and on `SandboxScenario` and `SandboxCapture` in `game/` describe
`DemoMaps.cs` as still present or as the thing a map is held equal to. Nothing breaks; the
sentences are just no longer true.

**For View.** `MissionLibrary.Load(name)` and `Mission.Begin(seed, layout, map)` are the whole
API, and `Mission.Deploy(battle)` is there for a caller that builds its own `Battle` — which the
sandbox does, because it wants its own layout. `Mission.Brief` is six strings fit to show, and
`Mission.Places` is named ground a readout can label. Row 5 of entry 045's road is unblocked and
is a deletion of `SandboxScenario`'s deployment lists rather than surgery.

**For Setting.** The names in the file are the sandbox's — Vance, Orsini, Bekker, Sentry,
Spotter, Watchman, Hollis. If the roster renames anybody, it is one file now.

**For Core.** The round limit is in the file and nothing in the rules reads it; whatever runs the
battle applies it. That is still the missing clock of entry 030 and it has not moved. And see 048,
which is what fighting from the file turned up.

**For Master.** `content/missions/**` is Content's, on the same terms as `content/maps/**`.
`src/Hexcom.Core/Maps/DemoMaps.cs` is deleted, so the carve-out in `map.md`'s Owns column for Core
— *except `Maps/DemoMaps.cs`* — has nothing left to except and can go.

---

## 048 — A withdrawal is achieved by walking away, because the task half of a mission is not in the rules
**2026-09-09** · **Raised by** content · **For** core · **Status** resolved by 061

Twelve seeds on the waystation, fought from the mission file, `Commander` on both sides. **Every
one of them settles**, which is the finding entry 038 asked for: it measured twelve matches
reaching no decision in sixty rounds, and an objective closes that completely. Three achieved,
nine abandoned, all in round 2 or 3, and the twelve together take two seconds where they used to
take nine minutes.

**And in none of them does anybody go near the compound.** The brief says *enter the compound,
confirm what is stored in the house, and come out*. `Withdrawal` judges the coming out. So the
best available play is to walk to the exit immediately, and the AI plays it — correctly, given
what it was told.

**The diagnosis is not that `ObjectiveValue` is too high.** That is entry 044's first item and it
is a real question, but it is not this one: with the value at nothing, the squad would do what
entry 038 measured, which is nothing at all. What is missing is that **every shape in the mission
book has something to do before the leaving**, and only the leaving is modelled. The book's own
withdrawal is *go, be there, come back*; entry 041 quotes that as `Withdrawal`'s summary and then
builds the last third of it.

**What the numbers say about the shape of the fix.** Measured off the map, in hexes at 1.73 m
between centres:

| | Vance | Orsini | Bekker |
|---|---|---|---|
| start to the nearest cottage | 10 | 12 | 14 |
| start to the compound centre | 21 | 20 | 22 |
| by way of the compound | 34 | 33 | 35 |

A turn is about ten hexes. So the exit is one turn away and the thing to look at is two turns
past it in the opposite direction, which is why round 2 is when everybody leaves. Any fix has to
make the mission worth thirty-four hexes rather than ten, and `ObjectiveHorizon` is measured in
turns of action points — so a two-stage objective whose first stage is out of horizon has the
same problem the gradient was invented to solve. That is the interesting part, and it is Core's.

**One more reading, offered as an observation rather than a measurement.** Vance, the scout on
foot with the blade, is `Unaware` to everybody in all twelve. Orsini, the trooper carrying the
repeater at encumbrance 3, is `Searching` in nine. Bekker sits between them. Nobody fired a shot
in nine of the twelve and the only ordnance in any of them was the sentry throwing a plasma
charge at open ground. Whether that split is the noise of the walk (entry 037: a turn's walk on
gravel is heard further than a slug rifle) or simply who is nearer the road is not something these
runs separate, and it is worth separating, because the first answer would mean the thing that
loses a stealth mission is already footsteps rather than eyes.

**Reproduce it:**

```bash
HEXCOM_SEEDS=12 dotnet test content/Hexcom.Content.Tests --filter "FullyQualifiedName~TheFightIsRecordedSeedBySeed" --logger "console;verbosity=detailed"
```

---

## 049 — The capture can act, the window can be answered by hand, and a wall is drawn by what it does
**2026-09-09** · **Raised by** view · **For** view, core, content and master · **Status** resolved; row 2 of 045's road

Two jobs that turned out to be one. A scripted capture is how a picture proves a window was
answered by hand, and a window that can be answered by hand is the only interesting thing a
scripted capture had left to photograph.

**The command line is a list of things a person could have done, in the order they typed them.**
`SandboxScript` splits the user arguments into steps and `HexSandbox` walks them. Order is the
whole of it — `--move` then `--pass` is a different battle from `--pass` then `--move`, and a
parser that asks *was `--move` given* cannot tell them apart — so this is a sequence and not a
bag of flags. Five things stayed settings, on the test of whether somebody at the keyboard could
do them: `--shot`, `--shot-after`, `--scenario`, `--ai`, `--windows`. Everything else is a step,
including the camera, which means `--fit` goes last.

**Every step calls the method the matching key calls, and nothing else touches `Battle`.** That
was the constraint the brief set and it is the one worth keeping: a script that could reach the
rules directly would be a way for a picture to show a state the keyboard cannot reach, which is
the opposite of what a harness is for. So the actions came out of the input handler into named
methods — `MoveTo`, `FireAt`, `SetStance`, `HoldArc`, `ShoutAbout`, `LeaveTheField`, `EndTurn`,
`PlaceReaction`, `ResolveOpenWindow` — and the keys and the script are two callers of one
surface. Each step prints what it did, because a deaf run's worst failure is silence: a misspelt
unit name would otherwise produce a perfectly good picture of the wrong moment.

**`--until NAME` earned its place immediately.** Initiative is rolled per round, so counting
passes is a guess that goes wrong the moment a roll changes — three attempts at the brief's own
test landed on the wrong soldier before this existed. It is what the hand does anyway: press
space until my man is up.

**The window.** `_byHand`, the `W` key, `--windows`: with it on a move is `Commit`, a pause and a
later `Resolve` rather than `Battle.Move`, and a hostile turn goes to a `Commander` built with
`WindowAnswer.HandedOut`. Both arrive at the same place, and the readout does not care which —
from the interface's side they are one question: somebody is part way through a move that is
already paid for, and the people who can answer it have not yet. Tab picks whose answer, a
number picks it, space resolves with recommendations standing in for anybody left. The options
are scored with `ReactionWindow.Appraise`, the same call the recommendation is made with, so a
player is choosing between exactly what the AI would have ranked — which is contract 2 at its
narrowest, and it is why *hold fire* reads as `+0.00` rather than as an absence.

**Two things about that state had to be drawn or it is unreadable.** The mover has paid for a
walk it has not taken, so the committed route is drawn out of it with the tick each step lands
on — the same clock the options are quoted against. Without it a player sees a soldier who has
apparently done nothing being shot at for it.

**The brief's own test, from one pasted command:**

```
--scenario compound --ai --pass 3 --hostiles hand --until Watchman --overwatch narrow
--until Orsini --move 1,0 --zoom 44
```

*reactions — t15 Watchman (overwatch) snap at (0,1)@0: hit Front for 0.* One of ours moved, a
sentry holding an arc answered it, and the reaction line says what it did. On the waystation,
`--windows --ai --pass 30` stops in round 4 with the sentry committed from `(-5,0)` to `(-6,-2)`
over 15 ticks and Vance offered three answers with their scores; `--place Vance:2 --resolve`
takes the second and reports what the window then did.

**A decision entry 038 asked View for: colour and weight come from the figures, never from the
name.** `StyleFor` switched on six well-known wall ids, so the waystation's `hedge` drew in the
fallback grey along with every profile any future map invents, and entry 035 wrote that down as
a gotcha rather than fixing it. A map may declare its own kit — that is the point of the format —
so a table of names is a table that is wrong about every map written after it, and silently.
Walls now take their hue from what they are worth to a plan (walk through it, a building wall,
or the colour of the cover they give) and their weight from how much of a body they stop. Ground
takes its fill from `Passable` and `ExtraApCost`. **All six built-in wall profiles come out at
exactly the colour and weight the hand-written table gave them**, which is the check worth
having: the figures were what the names had been standing in for, and nobody had noticed because
there had never been a seventh profile to disagree.

**Three readouts that Core made possible and nothing was showing.**

- **The mission.** `Objective.Brief`, `VerdictFor(Player)`, and `Unit.Left` for who is off the
  field and what the other side held on them as they went. Ours only; what the enemy came to do
  is theirs to know.
- **What our own soldier holds on a contact, exactly** — entry 042's third case of contract 3.
  It reads `74/100` against `Threshold(Engaged)`, and it can read `130/100`, because certainty
  banks margin up to `Ceiling`. That is not a formatting slip: the margin is what a contact
  survives decay on.
- **Who would hear you call it in, and at what fraction.** Two audit rows at once, both gaps
  since the audit was written, and both unblocked by Core rather than here: `Battle.Shout`
  exists now, so entry 012's odd row is closed on the interface side — `S`, or `--shout NAME`.

**And the sandbox now has something to win.** `SandboxScenario` sets the waystation's
`Withdrawal(Player, the three cottage tiles, Searching)` — the mission written in that map's own
header, as rules. Entry 038 measured twelve matches on this map and not one of them ended, and
this is the first time the sandbox can be played to a verdict. It is knowingly a **fourth** copy
of a fact 038 counted three of; when the mission file lands (045's row 1) this scenario is one of
the things it deletes, and until then the header is the thing to change first and this the thing
to change with it.

**One bug, in `game/`, found by the AI throwing a grenade in front of the readout.**
`BattleHud.Describe(Order)` ended in a catch-all that read `order.Stance!.Value`, which was true
of the only kind left over when it was written. Three kinds have landed since — `Throw`,
`Shout`, `Leave` — and the first grenade brought the whole frame down. Every kind is named now
and the default is a sentence. **A switch over somebody else's enum wants its default to be a
sentence, not a guess**, and this file has two more of them.

**For Core, one thing, and the workaround is three lines so it is a note rather than a request.**
A `Commander` handing its windows out stops at *every* window, including the ones nobody was
offered anything in — which is right for Core, since it cannot know whether the thing answering
wants to see an empty list. It is wrong for a screen: stopping to ask a question with no answers
in it is a worse interface than not stopping, and on a map this size it is the common case rather
than the corner. The sandbox resumes past those itself (`SkipEmptyWindows`). If a second
interface ever wants the same thing, it belongs behind the flag rather than in both of them.

**For Content.** Nothing is asked. Worth knowing that the sandbox now deploys the waystation
mission as an objective as well as the deployments, so the mission file has four things to
absorb from `game/` rather than two, and that the exit is drawn on the map — a named place has to
be visible or it does not exist.

**Written before 047 and 048 landed, and both of them are merged into the same master as this.**
The fourth copy of the waystation mission described above is now the *last* copy: 047 collapsed
the other three into `content/missions/waystation.hexmission`, and View's next brief is deleting
this one. Nothing here needs changing for that — the objective the sandbox sets is the same
`Withdrawal` the file sets, which is the point — and it means the sandbox will reproduce what
048 measured: with only the leaving half of the mission in the rules, walking straight out is the
best available play, and a picture of the AI doing exactly that is now one command away.

**For Master.** Row 2 of 045's road is done. Entry 038's half for View is answered above; entry
012's first item is closed and its second — a preview of who a *shot* would wake — is still open.

## 050 — The mission is a file, the sandbox can be played to a verdict, and the first trailers have been read
**2026-09-09** · **Raised by** master · **For** all · **Status** resolved

Three branches merged since 045 — `setting/roster`, `content/mission-file`,
`view/scripted-capture` — and Core did not run. This entry records the routine, the first reading
of the `Session:` trailers, and where the road now stands.

**Routine.** The carve-out in `map.md` for `DemoMaps.cs` is gone with the file (047), and
`content/missions/**` is in Content's Owns column and in `CLAUDE.md`. Entry 048 is in Core's brief
as the measurement that reshapes its first item: with only the leaving half of a mission in the
rules, a squad told to inspect a compound walks to the exit in round 2, and the fix has to make
the mission worth thirty-four hexes rather than ten against a horizon measured in turns. Entry
046's four items are routed — the post names to Content, since the names live in the mission
file now; the unused cost profiles and the signaller argument to Core; the stale remarks to
whoever has each file open. Entry 049's note about empty windows is in Core's brief as a note.

**The trailers, first reading.** View ran on Opus, continued, job 2 — as recommended in 045.
Content ran on Opus, new — as recommended. Setting's commit carries no trailer: the rule landed
in 045 and its branch was cut from the same master, so it is the one that missed it, and the
model is in the `Co-Authored-By` line anyway. Core did not run. So the instrument works, and the
recommendations for this round can be checked against it next time:

| Territory | Last | Next job | Session | Model |
|---|---|---|---|---|
| View | Opus, continued, job 2 | the sandbox loads the mission file — a deletion in files it just edited | keep, job 3 | Opus |
| View, after that | — | the greybox, build order 06 — rewrites `game/`, re-asks the split | fresh | Fable |
| Content | Opus, new | a second battlefield — same harness, same formats | keep, job 2 | Opus |
| Setting | Opus | the sites of Calder — prose against a checklist | either | Opus |
| Core | Opus, two jobs, idle a round | the task half of a mission — a design question with a table to settle it against | keep if it still holds context, else fresh | Opus, and Fable if the *one kind or two* question stalls |
| Master | Fable, job 5 | the next round | keep while it holds the picture | Fable |

**The road.** Playable and greybox have come apart, and it is worth saying which is which.
The greybox is two View increments away and waits on nothing else. *Playable* — a mission that
is a mission rather than a walk to the exit — waits on Core's task half, and nothing in the
greybox waits on that in turn, so the two proceed side by side.

| | Territory | What it produces | Waits on |
|---|---|---|---|
| 1 | View | the sandbox loads the mission file | nothing |
| 2 | View | the greybox | 1 |
| 3 | Core | an objective at a place, so the mission has a task before the leaving | nothing |
| 4 | Content | a second battlefield, tight and built-up, with its own mission | nothing |
| 5 | Setting | the sites of Calder | nothing |

Rows 1, 3, 4 and 5 can all start today. The first greybox somebody plays will have a walk-out
mission on it unless row 3 lands first, and that is fine: it is a blockout, and 048 says the
walk-out is one command away to see.

## 051 — The greybox is briefed, and the rules are settled enough for it
**2026-09-09** · **Raised by** master · **For** view, core · **Status** resolved

`subprojects/view.md` carries the brief for build order 06 in full, under *The job after this*,
written to be promoted the day `view/mission-file` merges. Two judgements in it cross a boundary
and are recorded here so they can be argued with.

**The build order says *only once the rules are settled*, and this says they are — for a view.**
Nothing since entry 040 has changed a signature the sandbox reads; every row of the interface
audit is shown, coarse, or a gap with its query named; and what Core still owes the mission —
the task half, entry 048 — changes what the AI does and nothing about what is drawn. Balance
dials will move for a long time and none of them changes a shape. If the greybox finds a query
missing, that is an entry for Core and not a reason to stop. Core: the greybox does not wait on
`core/objectives`, and `core/objectives` should not wait on the greybox.

**The one decision that makes it a game is in the brief and not in any rule.** The flat sandbox
draws every hostile in play and the enemy's beliefs about us, because it was built to drive both
sides. A playable view draws your side's knowledge and nothing else — a body while somebody
holds eyes on it, a ghost at its marker with its credence, nothing before anyone has heard a
thing. Contract 3 permits exactly that and no rule requires it, which is why it is a view
decision and why the brief puts it first. The see-everything mode stays as a switch, because
the capture harness and the orders readout are instruments (entry 023).

**What the user decided this round, for the record.** Everything but the road to a playable
greybox waits, to conserve the token budget: Core's task half, Content's second battlefield and
Setting's sites all have briefs and none of them is to be started. That is a scheduling decision
and it is not written into any brief, because a brief is a work order and not a status line.

---

## 052 — The sandbox fights the mission file, and the fourth copy is gone
**2026-09-09** · **Raised by** view · **For** view, core and master · **Status** resolved

The last copy of the waystation mission has left `game/`. `SandboxScenario` was a map name, seven
deployments, three exit tiles and a threshold; it is now a mission name and a line for the status
bar. `MissionLibrary.Load` reads the file, `Mission.Begin` hands back a battle deployed,
objectives set and started, and the sandbox passes it the metres layout because it owns two and
only one of them may reach `Battle`.

**The drift entry 038 warned about was real and this is the measurement of it.** The copy just
deleted let a soldier leave at `Searching`. The file says `unnoticed suspicious`, one rung lower.
Two of the four things that decide whether the mission is won disagreed, in the same repository,
and nothing but a person reading both files could have noticed — which is the argument for one
copy, made after the fact by the copy that was wrong.

**Three interface decisions, because a mission file asks three questions a map never did.**

- **Which of the six briefing parts is on screen.** The task, and only the task. It is the one
  part that is a sentence about what to do next; the other five are what the squad was told
  before it went, and they are a page, not a status line. So `M` — or `--brief` — puts the whole
  briefing up, in the file's own words, with the clock noted underneath. The status line keeps
  saying `Objective.Brief` where there is no file, which is the compound.
- **What to do with the round limit.** Apply it, and say so. The file carries thirty rounds and
  nothing in the rules reads it (entry 047), so the sandbox stops the turns at 31 and the status
  line reads `round 31/30    out of time`. **It invents no verdict.** `Withdrawal.Judge` says
  `Undecided` while anybody is still standing on the field, and that is the honest answer: the
  squad did not get out and the rules have not settled it. A sandbox that made up an `Abandoned`
  would be putting a rule in `game/`.
- **Whether named ground is drawn.** Yes, from `Mission.Places`. Same argument that had the exit
  drawn: a briefing that says *off by the cottages* and a map on which the cottages are not
  labelled leaves the player to work out which three buildings those were.

**The sandbox now plays a mission to a verdict, and the first thing it showed was entry 048.**
Both sides on the AI, eight turns, one command: Vance and Orsini extract in round 3 and Bekker in
round 5, all three at `UNAWARE` or `SUSPICIOUS`, **ACHIEVED** — and nobody goes within twenty
hexes of the compound the task is about. That is 048's finding reproduced on screen rather than in
a test summary, which is worth having because the next person to look at `ObjectiveValue` can now
watch the thing they are arguing about.

**One readout problem recurred and got the fix it should have had the first time.** The mission
line ran under the turn-order strip the first time anybody won — three departures joined onto one
line is the same shape of bug the seen line had with three contacts. Both are now one line per
item. **A readout that grows with how many soldiers are involved cannot be a line**, and this
file has had that lesson twice; the third time it should be a rule.

**For Core.** Nothing needed, one thing worth knowing. Two things now apply the mission clock —
the harness in `content/` and this — because the rules have none, so a figure that lives in one
file is enforced by two implementations. That is precisely the shape entry 038 was about, at one
remove. When the clock of entry 030 lands, both should become deletions rather than second
opinions, and the sandbox's is written to be one.

**For Master.** Row 1 of entry 050's road is done, which leaves the greybox as View's only
outstanding row and entry 051's brief as the thing to promote. Nothing in `game/` names a map, a
soldier or a threshold on the waystation any more; the only hand-placed deployment left is the
compound fixture, which entry 047 made the case for keeping.

## 053 — The greybox is built, it opens as the game, and the paths still do not divide
**2026-09-09** · **Raised by** view · **For** view, core and master · **Status** resolved for what landed; the play-through it needs is View's next brief

Build order 06. `game/` is a 3D blockout of the battle with no art in it: every tile a prism at
its floor height, every wall a box from `WallBaseHeight` to `WallTopHeight`, every soldier a body
at `StanceProfile`'s height with its facing marked, and every readout the flat sandbox drew, drawn
again in the space the rules describe. The named actions, the script, the capture, the frame, the
HUD and the scenario survived as the brief said they would; the view, the geometry, the camera,
the scale, the palette and the scene were rewritten. Two files are new — a mesh builder and a
canvas — and the two `.uid` files beside them are in the commit. `subprojects/view.md` has the
shape; this is the reasoning, and the five decisions the brief asked for.

**1. What a player sees of the other side: their own side's knowledge, and the keys open on
that.** A hostile is a body while somebody of ours has eyes on it, a see-through body at its marker
with its credence otherwise, and nothing before anybody has heard a thing. The list is
`Tactician.Known` for each of ours, merged by keeping the best any of them holds, which is the list
the scorer weighs — contract 2 as a dictionary — and one question, `SandboxFrame.Sees`, is what
the view, the HUD and the cursor ask, so there is no second place a hostile leaks through. Four
things in the HUD followed from it: a line saying which mode is on; an unfound hostile's slot in
the turn order reads `?` with no name, roll or reserve; the exposure line names an unfound watcher
*somebody unseen*, because that a line exists is geometry and ours, but who is at the far end of
it is theirs; and the orders readout prints only when omniscient, since it is the enemy's mind.
The marker the enemy holds on us is drawn in both modes: section 07 names it as the one thing of
theirs a player sees, and it is the payoff. `O` and `--omniscient` put everything back, because the
capture harness and the orders readout are instruments (entry 023).

**2. World units: one engine unit is one metre, and `SandboxScale` is a static with one layout in
it.** The pixels layout is gone and nothing converts. The class stays for the reason entry 005 is:
the layout the battle is given is built there from a constant, nothing that knows about the
camera can build one, and the sign of Z lives in one place. It is 68 lines, and the next session
to want to inline it should read 005 first.

**3. Storeys: ghosted above, solid at and below.** A roof over the storey being looked at is drawn
at sixteen per cent, so it says there is a roof without hiding the room. Cutting away loses the
tower and the ridge from every picture of the ground; drawing nothing, which the flat view did,
lost the soldiers standing on them. The attention field and the held arc are tinted onto the tiles
of the storey being looked at, so a sentry in the tower tints the ground it watches rather than
the air at its own height — which is what the flat view drew and was right to.

**4. The camera: pitched at 55 degrees, yaw snapped to the six hex bearings.** An arc is legible
only from a camera that agrees with the grid, and from a bearing the hexes tile the screen the
same way at every step of the turn. It opens looking north so a capture of the same command shows
the same map the same way up as before. Zoom is distance; `--zoom N` is metres back; the tile
detail threshold moved from 22 pixels to 70 metres, which is the same hex size. The camera never
animates, because a capture has to land on the same frame every run.

**5. A 3D capture is byte-deterministic on this machine**, with 3D antialiasing and shadows on —
two runs of `--fit` on the first day, identical files, and every capture since. The
zero-changed-pixel refactor test survives. The pinned scene is new and is in `view.md`.

**One drawing decision the brief did not ask for and is worth the entry: readouts on the ground
are tinted hexes, not shapes.** The flat view drew the attention field as nested sectors and the
held arc as a wedge. Here both are painted per tile at the value the rules give for that tile —
`AttentionOn` scaled by the look-gain's range term, and `AngleOffDegrees` against the arc out to
`MaxRange`. A disc at one height vanishes under a ridge; a tint follows the ground; and it is the
rules' own answer per place rather than an illustration of the rule, so when a dial moves the
picture moves with it and nothing in `game/` needs to know. Eight thousand queries a rebuild on
the waystation, and cheap.

**What was checked, and what was not.** Three tests were set. The fitted waystation reads as the
same map the flat one showed, and a close capture has the ground, the walls, the soldiers with
facing, the reach with its costs, the cover outlines, the attention field, the exit, the named
place and the route preview in it. The scripted test from entry 049 reproduces in three
dimensions and prints the same line: *t15 Watchman (overwatch) snap at (0,1)@0: hit Front for 0*.
An open window on the waystation shows the sentry's committed route with its ticks and Vance's
three answers. **The third test — a person plays the waystation to a verdict against `Commander`
with windows handed out and the other side hidden until found, and says what read wrong — has
not been run, because a session cannot run it.** It is View's next brief, and its finding will be
its own entry.

**For Master: the territory question, as a count.** Presentation is `BattleView.cs` and
`MeshBuilder.cs`, 1,032 lines. Interface is `BattleHud.cs`, 974. The middle — `HexSandbox.cs` and
the nine files it uses — is 2,420, and the node is the largest file in the directory. The
greybox grew the middle and did not give it an owner. The paths divide no better than they did at
entry 014, and this is a finding about paths and not a request.

**For Core, two things, neither a request.** The build order in `design.html` has row 06 as the
next thing and it is built; the row is Core's to flip, since only Core republishes. And nothing
about the greybox needed a query Core does not expose — entry 051's judgement that the rules
were settled enough for a view held.

**Three questions the greybox opens are in `view.md` under Open questions**: whether an unfound
hostile should hold a slot in the turn order at all, whether a hostile's held arc should be drawn
when the hostile is, and whether the fixed pitch is enough. All three are the play-through's to
settle and none should be settled from what seems tidy.

## 054 — The greybox is on master, the split was re-asked and stays settled, and the next measurement is a person
**2026-09-09** · **Raised by** master · **For** all · **Status** resolved

Two View branches merged since 051 — `view/mission-file` on Opus, continued, job 3; and
`view/greybox` on Fable, fresh, as 050 recommended — and build order 06 is built. Nothing else
ran, by the user's decision recorded in 051. This entry closes the round.

**The split, for the third time.** Entry 014 said presentation and interface stay one territory
because the paths do not divide, and `map.md` said the greybox was the moment to look again.
Entry 053 looked, with a count, and the middle both halves use is larger than either half. So
`map.md` now says the question was asked and answered, and stops inviting it. It can be asked a
fourth time when somebody has a path that would divide it, and not before.

**What the road to a playable greybox has left in it: one row, and it is not a session's.**
Entry 053's third success test is a person playing the waystation mission to a verdict against
`Commander`, with windows handed out and the other side hidden until found, and saying what read
wrong. View's brief is written for the session that records that. The user is the person.

**How it is played, for the record and because the question was asked.** There is no exported
executable, and building one is a View job that has not been asked for: it needs Godot's export
templates, which the WinGet package does not install, and a preset in `game/`. The game runs
through the editor binary against the project directory, after a build:

```bash
dotnet build Hexcom.sln
Godot_v4.7.2-stable_mono_win64_console --path game
```

`H` hands the hostile side to the AI, `W` makes reaction windows stop for an answer, `M` puts
the briefing up. `O` shows everything and is the one key the play-through is asked not to
press, because what it hides is the game.

**What waits, still.** Core's task half (048), Content's second battlefield, Setting's sites,
and the export. All briefed but the last; none started. The order in which they resume is the
user's, and the first play-through is the thing most likely to change it.

## 055 — The game is tested by playing it, so every round ends with a build, and Master runs it
**2026-09-09** · **Raised by** master · **For** view, master · **Status** closed by 056

The user's decision, recorded because it gives Master a power it did not have and View a job the
build order does not list.

**The decision.** From now on each round of sessions ends with a rebuilt Windows executable for
the user to test, and Master produces it. Master writes no code and that has not changed: it
pastes one command that View owns, after everything is merged and pushed, and reports where the
output went. `subprojects/master.md` has it as a standing item.

**What View owes for that, in its current brief.** The export templates installed on this machine
and written down as if for the next machine; a committed `export_presets.cfg`; `build/` at the
root and in `.gitignore`; and one pasteable command under `## Shipping it`, verified rather than
expected — including whether the built game still takes the capture and script flags, because if
it does the export is a second harness and if it does not the doc has to say the harness is
editor-only.

**Why the build is not committed.** It is derived, exactly as a test result is. The doctrine
that status lives nowhere in the repository applies to it: a checked-in `.exe` is a claim about
whether the tree builds, made by whoever last remembered to update it.

**What it costs.** One command's worth of tokens per round for Master, and a View increment once.
Against that, the user plays every round instead of asking whether it runs, and the play-through
findings — the first measurement of the interface rather than of the rules — start arriving one
round earlier than they otherwise would.

## 056 — The export works, and the exported game is a second capture harness

**2026-09-09** · **Raised by** view · **For** master, core, content · **Status** closed — this is what entry 055 was waiting on

`view/export` is done and `## Shipping it` in `subprojects/view.md` is the command. Master can
paste it after a round with no View session awake, which is what entry 055 asked for. Four things
here rather than in that doc, because each of them is somebody else's business too.

**The exported game answers the capture and script flags, and draws the same picture to the
byte.** `--fit` run from `build/Hexcom.console.exe` and `--fit` run from the editor against
`game/` produced the same SHA-256. So the zero-changed-pixel refactor test survives into the
build, and a picture taken from a shipped executable is comparable with one taken from a
checkout. This was the open half of entry 055 — whether the export would be a second harness or
whether the harness would have to be called editor-only. It is a second harness.

One difference and it is worth knowing before it wastes an hour: a relative `--shot` path is
resolved against the executable's own directory in the build, and against `game/` in the editor
run. An absolute path behaves the same in both.

**Godot's .NET exporter fails silently in a way that produces a plausible executable.** With no
solution file where it expects one it prints errors in the middle of the pack listing, **exits
0**, and writes an `Hexcom.exe` that is missing every .NET assembly. The only cheap tell is the
size: 109 MB wrong against 190 MB right. The fix is one line of `game/project.godot` and it is
written down. This is recorded for whoever hits the same shape elsewhere — a zero exit code from
a Godot tool is not evidence that it did the thing.

**The export builds the C# itself and needs no `dotnet build` first.** It runs `dotnet publish`
as a step it prints, and it was verified against a tree with every `bin/`, `obj/` and
`game/.godot/mono` deleted. The interactive editor run is the opposite and still needs a build
first, so the two commands in `README.md` are different on purpose and not by neglect.

**One tracked file was added and it is not code.** `game/export_presets.cfg` is committed, and
`game/export_presets.cfg` came out of `.gitignore` to allow it, because Master runs the export
and cannot recreate a preset by hand. `build/` took its place in the ignore list: a built game is
derived exactly as a test result is, and nothing checked in is a claim about whether the tree
builds.

**What it does not settle.** Nothing about art, installers, signing, or any platform but Windows,
all of which were out of scope. And it is a packaging job only — no file under `game/scripts/`
changed, which is why the pictures are identical rather than merely similar.

## 057 — The first play-through: six findings, a change of focus, and a territory for the interface
**2026-09-09** · **Raised by** master, for the user · **For** view, content, core, interface · **Status** the six are built — entry 066; the mission's content half and the objective scope routed to Content and Core remain open

The user played `build/Hexcom.exe` — the waystation against `Commander`, the first person to —
and said this, recorded here in their words as nearly as a list allows, because entry 053 said the
play-through's finding would be its own entry.

**The six findings.** All interface, none a rule.

1. Move the debugging readouts and the legend to a separate window that can sit on a different
   monitor.
2. Moving the camera should be smooth, not sixty degrees at a time.
3. The mouse should control the camera as well as the keyboard.
4. Opening it as a user should go straight into the mission against the AI. Keep the other
   settings controllable for AI-against-AI work, but the default is me playing the mission.
5. My units lack contrast against the terrain.
6. When units move, move them along the path — not slow, but not instant. With the animation off
   for headless runs.

And the verdict on the whole: *it's a start*.

**The change of focus.** From here the work is making what exists playable: Content finishing
the mission material, View developing the interface. Everything else waits. Two consequences
that are not obvious from the sentence:

- **Half of "finishing the mission" is Core's.** Entry 048 measured the waystation mission
  achieving itself in round 2, because the rules have an objective for leaving and none for the
  task. Content can name the places, take the squads from the roster and write the briefing, and
  the mission still walks out until Core has an objective at a place. So `core/objectives` runs,
  scoped to that one item, and its brief says so.
- **Item 2 overrules a greybox decision.** Entry 053 snapped the camera to hex bearings so that
  arcs stay legible from any angle. The user wants it free and smooth; the arcs have to stay
  legible anyway, and the harness has to stay deterministic — the brief says how.

**A new territory: Interface design**, `subprojects/interface.md`, owning `docs/interface/**`.
The interface so far was designed by the sessions that built the rules, against the audit of what
the AI reads, and never against what a player of this genre expects under their hands. The
territory researches what is standard in turn-based squad tactics, says what the asymmetry of
contract 3 does to each convention, and writes a queue of View briefs against it. It writes no
code and no other territory's doc; Master promotes its briefs into `view.md`, so one file is
never two territories' `## The job`. The six findings above go to View **now**, without waiting
for the research: they are concrete, and the person who asked is the person who tests.

**Routed.** The six into View's brief, `view/playable`. The mission's content half into
Content's brief, `content/waystation-mission`, with the second map after it. The scope onto
Core's brief. The territory's first brief in its own doc.

**Sessions.** View: fresh, and Opus — six well-specified items, and the Opus session that did
the keys has run three jobs. Content: keep on Opus if the session holds, else fresh. Core:
its idle Opus session if it still holds context, else fresh on Opus. Interface: fresh on Opus;
it reads and writes.

## 058 — Two things the user settled after the play-through: the camera stays free, and convention is the default
**2026-09-09** · **Raised by** master, for the user · **For** view, interface · **Status** resolved

Recorded because both were argued, so that neither is re-argued.

**The smooth camera stands over the snapped one.** Master put the case for entry 053's decision
— arcs and facing wedges are legible from a hex bearing and smear between them — and the user
held: smooth is more important, trade-off noted. So View's brief asks for a free camera *and*
arcs that survive any angle, and if the second proves hard the answer is a better arc, never a
snapped camera again.

**The genre's convention is the starting point, and a departure argues its case.** For the
interface territory: every recommendation is either the convention as it stands or a departure
with the reason this game needs it, and the default in doubt is the convention. This game will
modify conventions to suit its subject; it will not invent where a player already knows what to
expect.

---

---

## 059 — The waystation mission is finished but for the rule it needs, and the ground already says what the mission is
**2026-09-09** · **Raised by** content · **For** core, view, setting · **Status** open for content — Core landed the objective in 061; the one-line uncomment is the head of Content's brief, see 068

Content's half of entry 057's *make what we have playable*. Everything about
`waystation.hexmission` that is content is now written, so that when Core has an objective at a
place the file changes one line.

**The names are out of the roster.** Cobb has the gate, Teague has the roof and the set, Marek is
in the tower. That is item 1 of entry 046 done for the waystation, and it took three words because
the mission is one file. The **briefing still says posts** — *one stands on the road outside the
west gate* — and only the deployments say names, which is the split section 6 of the roster asked
for and the right one: the Commission does not know the man at the gate is called Cobb. `game/`'s
compound fixture still fields the three posts and that is View's to change or keep.

**The ground the briefing talks about is named ground.** `compound`, `house` and `cottages`, so an
objective can point at them and the view can label them (entry 052).

**The briefing is rewritten in the mission book's assessment register**, because the task is a
look and not a walk. Six parts, about 250 words, the longest of them *what is there* at 121 —
which is the right shape, since entry 030 says the uncertainty in that row is the campaign.

### The measurement, which is the interesting half

The mission book's test for a reconnaissance is whether the ground gives you somewhere to look at
the place *from*: a place with no standoff on it is a burglary and not an assessment. Asked of the
house, on the map as drawn:

| | |
|---|---|
| standable places outside the wall | 1693 |
| of those, with a line into the house | **0** |
| standable places in the yard | 54 |
| of those, with a line into the house | **14**, all south of the door |
| of those fourteen, overlooked by the roof | **14** |
| where the drain under the south wall opens | `-1,-3`, which is one of the fourteen |

**So the ground already states the mission, and nobody drew it that way on purpose.** The house
cannot be looked into from the road at any range, so the task is necessarily inside the wall. The
drain — the way in nobody watches — lands you on the shot. And there is nowhere to take it from
that Teague cannot see, so the man on the roof is not an obstacle on the way to the mission, he
*is* the mission. Three tests in `content/Hexcom.Content.Tests/Waystation/WaystationGroundTests.cs`
hold all of it, and they are the first tests in the project that check a map against what a
briefing claims about it.

**What is thin about it is that it is one decision.** Deal with the roof or accept being seen.
Whether that is enough is measurable the day the objective lands and is guesswork before it, so
the map has not been redrawn — but the two levers are known and both are content: a second
opening on the far side of the house, or a lower section of compound wall so the ridge at 1.5 m
buys standoff from outside.

### For Core

**1. The objective, and one question about its shape that Content cannot answer.** The
reconnaissance line is written into the file and commented out, one statement, so landing the rule
is an uncomment and a deletion:

```
objective reconnaissance player at house out cottages unnoticed suspicious
```

Note what it names: a place to get eyes on **and** a place to leave by. That is not this mission
being unusual — **all six shapes in the mission book end with getting off the ground**, so either
every objective grows an exit and a threshold, or objectives compose and a mission carries two.
The grammar can express either and it cannot guess; whichever Core builds, Content writes an
`ObjectiveOrder` for it and the format does not change (entry 047).

**2. A garrison that does not move is most of what makes this read as a diorama**, and it is not
content's to fix. Three of the four hostiles never act: Marek cannot notice the west road at 54 m
against a sight range of 45, Hollis has no line to it at all, and Teague sits still. The fiction
already has the answer and the map already has the route — the roster's section 5 gives the Cadre
one honest patrol, Ilves, *out past the bridge and back at hours nobody can predict*. **Nothing can
say that.** A mission file has no way to give a soldier a route, and nothing in `Commander`
patrols; a fifth deployment would just be a fifth soldier standing still. Whether a patrol is a
standing order in the file or a behaviour in the search is Core's call, and until one of them
exists a garrison is four sentries.

**3. Twelve seeds are unchanged from entry 048**, as they should be, since the objective did not
change: three achieved, nine abandoned, all in round 2 or 3, nobody within twenty hexes of the
house. The finding stands and the fix is item 1.

### For View

`Mission.Places` now holds three rather than one, and two of them are concentric: `compound` is 61
tiles centred on `0,0` and `house` is 7 centred on `0,1`. `DrawPlaceLabels` puts one label at the
centroid of each, so **this entry was going to report that the two would collide**, and a capture
says they do not — 1.73 m of separation is about sixty pixels at a normal working zoom and both
read cleanly, at the compound and from across the map. Recorded because it was checked rather than
reasoned about, and the reasoning was wrong: a place inside another place is a case the
one-label-per-place rule did not have until now and it turns out to handle.

Two small things the same captures did show.

- **The briefing panel prints `wayoff` where the file says `way-off`.** The five other parts are
  single words so nothing else shows it. `MissionFile.PartName` is the file's spelling of a
  `BriefingPart` and is public for exactly this.
- **The task is on the status line and it is 21 words**, which fits at 1600 wide with a little to
  spare. The mission book says a task is one sentence and *if it takes two it is two missions*, so
  the constraint is the fiction's rather than the readout's — but a longer one would run out of
  line, and Content now knows it.

### For Setting

The roster's names are in and they read well in a match report. What the roster wrote that nothing
can yet use is Ilves — see Core item 2 above. Also unused: `CostProfile.Scout` and
`CostProfile.Gunner` are still attached to nobody, which is item 3 of entry 046 and still Core's.

## 060 — The genre's conventions are written down, and the biggest gap is where the numbers are drawn
**2026-09-09** · **Raised by** interface · **For** view, master · **Status** resolved — the queue is promoted through View's own brief, which points at it since 066

`docs/interface/conventions.md` and `docs/interface/briefs.md` exist. The first is one section per
question a player meets — camera, selecting and ordering, turn order, what of the enemy is drawn,
reactions, animation, readouts, developer overlays — each saying what is standard with the games
it comes from, what this game already does, what contract 3's asymmetry changes, and a
recommendation tagged **convention** or **departure** per entry 058. The second is a queue of six
View briefs, with an amendment sheet at its head for the six findings 057 already routed.

**The finding that outranks the other nine, and it is not a missing feature.** Every figure in
this interface is a line of text in a panel at the top left; `BattleHud.DrawLines` assembles about
twenty of them and several carry six or eight facts each. The only numbers drawn at the thing they
describe are the AP costs on tiles. The genre's interface is spatial — hit chance on the target,
cover on the tile, points on the soldier — and the panel holds only what has nowhere better to be.
The interface audit checked *whether* everything the AI weighs is visible and it passed; nobody
asked *where*, and a game whose subject is information cannot teach a player to read a
battlefield with a readout that requires looking away from it. First brief in the queue.

**The brief's list of games is the right shelf for half the questions and the wrong one for the
half that matters most.** The tactics canon — the XCOM pair, Phoenix Point, Jagged Alliance 3,
Battle Brothers, Into the Breach, the older line — sets the camera, the action bar, the turn
order and the animation, and the conventions doc leans on it there. But every game on it draws
the enemy the moment a unit sees one, and none has a rung, a marker or a contact file. The
conventions that transfer to *what of the enemy is drawn* come from turn-based and real-time
stealth instead: **Invisible, Inc.**, whose alarm runs on six rungs with five sub-levels each
that are deliberately given no effect and no display so that a player only ever reads a
transition — which is contract 3's coarse rung, designed independently by somebody else and
shipped; **Mutant Year Zero**, which draws detection radii only in the mode where they matter;
and the Commandos line, which draws a cone per guard and a meter that fills as you are noticed.

**Three View open questions are answered with a genre reason rather than a tidiness one**, and
the briefs carry the reasoning:

- **A hostile's held arc is drawn whenever the hostile is.** The stealth shelf draws what a guard
  will do, because beating it is the game. A player who walks into an arc held by a soldier they
  could see holding it will say the picture lied, and they will be right.
- **An unfound hostile keeps its slot in the turn order and loses its shape.** Dropping the slot
  loses the interleaving a strip exists to show. A portrait-shaped slot with a `?` in it claims
  more than the rules do; an anonymous narrow tick says *somebody acts here*, which is true
  because turns are taken in the open. Whether the *count* of ticks is itself too much has no
  precedent in the genre, because every interleaving game in it starts with everybody visible.
- **A player answers reaction windows only for their own side, by default.** Offering every
  reactor whichever side they are on is the same family as the orders readout: an instrument, and
  it belongs behind the same switch.

**Two things a session building the six should read before it starts.** Right-click fires here
and cancels in every game in the genre, which puts the most irreversible action in the game on
the button a player presses to back out of something *and* spends the gesture the genre uses for
orbit — so the mouse camera and the gesture set settle together. And a walk should be priced in
**metres per second** rather than seconds per move, because one world unit is one metre by
contract 5 and a fixed duration makes a two-hex step and an eight-hex step look equally urgent.

**Nothing here is a proposal for Core.** Every recommendation is answerable from a query that
exists — `ReadoutFor` for the rung, `Contact.LastKnownPosition` for the marker, `Appraise` for
the window's default. The one thing the interface cannot show is already open rather than new:
entry 012's second item, who a shot would wake, which is the fourth brief in the queue.

**Every figure in the research is an argument and not a measurement**, and the doc says so where
it gives one. Degrees per second for a camera step, degrees per pixel for a drag, metres per
second for a walk: all reasoned from what the genre looks like, none timed. The person at the
keyboard settles them.

**For Master.** The queue is written to be promoted one at a time into `view.md`, so that one
file is never two territories' `## The job`. The amendment sheet at the head of it is deliberately
*not* a brief: entry 057's six are routed already and re-issuing them would put one job in two
files, so the sheet is what belongs beside them, and a review list if they have landed.
---

---

## 061 — An objective at a place: one shape, three tasks, and a mission measured in one currency
**2026-09-09** · **Raised by** core · **For** content, view, master · **Status** resolved

Entry 048 measured the waystation mission achieving itself in round 2, because the rules had an
objective for the leaving and none for the task. They have one now.

**The choice the brief asked to be made deliberately — one kind or two — is: one shape and three
tasks.** `Sortie` is *go out, do something, come back*, and it holds the exit, the reading taken
as each soldier leaves, the three endings and the journey. `Withdrawal`, `Reconnaissance` and
`Sabotage` differ in one question: has the thing been done. Looking at a place is a geometric fact
checked when somebody looks; spending points on a charge is an action with a verb and a price.
Those are different enough that a predicate on one shared record would have to be a delegate,
which content written as a text file cannot hold — so they are subclasses over a base that carries
the other nine tenths.

**The interesting part is that the task and the walking are priced in the same currency.**
`Remaining` is the action points still owed: getting there, doing what is there, and getting to
the exit. Twenty points spent walking and twenty spent on the charge move it by the same amount,
so a two-stage mission needs no second scale and **no seam** — completing the task does not jolt
the score, it changes what is left. That is what the brief's *two-stage objective whose first
stage is out of horizon* worry was really about, and it dissolves: there are no stages, only a
journey with something in the middle of it.

**And the horizon is stretched to the length of the job.** `ObjectiveHorizon` said how many turns
of walking still counted as being on the way; a mission longer than that would have read as
nothing worth starting, which is a flag again with extra steps. So the horizon is now the larger
of the configured one and the actual journey, measured off the deployment at `Start` — it decides
how *steep* the slope is on a short mission and never how far it reaches. Measured off where the
squad stands rather than off the map, because a map's diameter is not a mission's length.

**Two consequences for the AI, and the first is the fix.**

- **Leaving is not offered until the job is done.** A commander with the task outstanding has no
  Leave order to pick, so it cannot achieve the mission by walking out of the gate. The *rules*
  still allow it — abandoning is a real decision and `Verdict.Abandoned` is what it settles to —
  but the scorer is not offered it, because weighing *cut our losses* against *press on* needs to
  know how the rest of the battle is going and it does not. That is now the sharpest thing the
  search cannot do.
- **Working is an order**, ranked at the same rate per point as walking toward the place, which
  falls straight out of the shared currency rather than being asserted.

**For Content, and this answers the question entry 059 asks.** Every sortie carries its own exit
and threshold; objectives do not compose and a mission carries one. So
`objective reconnaissance player at house out cottages unnoticed suspicious` maps straight onto
the constructor, and the only thing the statement does not name is `within` — how close a look has
to be taken from, in metres, defaulting to twelve. Entry 059's own measurement says the house can
be seen from fourteen places, all inside the yard, so the default is very likely right; the
parameter is there if it is not.

`Reconnaissance(side, place, exit, within, unnoticed)` and
`Sabotage(side, place, exit, effort, unnoticed)`, both set with `Battle.SetObjective` before
`Start` like `Withdrawal`. `within` is how close a look has to be taken from, in metres, default
twelve — a line to a building from eighty metres is a line and not a report. `effort` is action
points, from however many soldiers, default forty. `Battle.Work()` is the turn action and spends
everything the soldier can spare rather than a fixed chunk. The waystation mission changes one
statement, as the brief said it would.

**For View.** `Objective.Brief` is words to show. `Sortie.Done` says whether the task is done,
`Reconnaissance.Confirmed` says who confirmed it and in which round, and `Sabotage.Spent`,
`Effort` and `Owing` are a progress bar. `OrderKind.Work` is new and comes back in an `Act` like
any other.

**One structural change worth naming.** `Objective` is a class rather than a record now. It holds
how far along the mission is, and a record that changes is a record in name only.

---

## 062 — The two archetypes now pay their own prices, and nothing noticed
**2026-09-09** · **Raised by** core · **For** master · **Status** open — the measurement is the first item of `core/measured`

Entry 046's item for Core, taken up. `UnitStats.Scout` carries `CostProfile.Scout` and
`UnitStats.Trooper` carries `CostProfile.Gunner`, so a scout is quick over ground and slow on the
trigger and a trooper is the other way round — which is what both profiles were written to
describe, and what the design doc has claimed for three increments while no soldier the game ever
deployed carried one.

**The whole suite passed unchanged**, and that is the finding rather than the reassurance. Nothing
depended on the archetypes paying list price, and equally **nothing tested that they did not**: a
scout that moved at four fifths and fired at seven fifths would have been indistinguishable from
one that did neither, in 391 tests. So this is a live behaviour change to every match on the
waystation with no measurement behind it, and it lands in the same increment that asks for the
first measured numbers in the project. Whoever runs that batch should run it both ways.

**What it does, on paper.** A scout crosses ten hexes for forty points instead of fifty and pays
thirty-five for a standard shot instead of twenty-five, so it banks more from a walk and shoots
worse and later — cost is time inside a reaction window, so it also answers a move further along
the route. A trooper is the mirror. Entry 048 already reads the scout as the one nobody notices
and the trooper as the one everybody does; this widens the gap in one direction and narrows it in
the other, and which way it lands is exactly what a batch would say.

**Also from 046, and not done:** what a signaller is worth to remove. Section 3 of
`docs/setting/roster.md` is the fiction's argument in quantities that exist, and `RemovalBonus`
values every soldier at their own vitality and nothing else. It wants the same batch.

**Also from 049, and not Core's:** a commander handing its windows out stops at windows with no
offers. That is right for these rules — an empty window is still a window — and the sandbox skips
them itself. If a second interface wants the same, the place for it is a flag here rather than
the same code written twice.

## 063 — Windows a session opens go on the left monitor
**2026-09-09** · **Raised by** master, for the user · **For** view · **Status** open until the flag is in Seeing it

The user has three monitors and works on the centre one. Every Godot window a session opens — a
capture, a scene-load check, a run to look at something — lands on it, and with four sessions
running that is a window every few minutes in the middle of whatever they are reading. The rule:
**a window a session opens goes on the left monitor**, and it is in `CLAUDE.md` as a gotcha for
everybody.

**The mechanism is View's, and it is the harness.** A setting on the command line — a setting,
not a step, in the sense entry 049 draws — call it `--aside`, that moves the window to the
leftmost screen before the first frame. Leftmost by position, not by index: Godot's `--screen N`
takes an index, and which index is the left monitor is a fact about this machine that would be
wrong on the next one, whereas `DisplayServer.ScreenGetPosition` over every screen and the one
with the smallest X is true everywhere. `--shot` implies it, since a capture is always a
session's. Every command in **Seeing it** carries it. The exported game with no flags opens where
Windows puts it, which is the user's monitor and correct.

**One thing to check rather than assume.** A capture has to rasterise, and entry 053's harness
notes say a window off-screen or headless does not. A window on another monitor is on-screen;
a window moved before the display server has settled may not be. Verify with two captures of
the same command after the move, as entry 053 did on day one.

**Priority.** Ahead of anything in the interface queue and behind nothing: it costs an hour and
it is paid for the first time a session takes a capture without the user noticing.

## 064 — The turn order strip draws only what the player knows
**2026-09-09** · **Raised by** interface, for the user · **Status** resolved — and it closes the View open question about the `?` slot

The user read the turn-order section of `docs/interface/conventions.md` and overruled its
recommendation. **An enemy the player has not found holds no slot in the strip at all** — not a
portrait with a `?` in it, which is what the greybox draws, and not the anonymous tick the
conventions doc proposed instead. From the player's side their own soldiers act in sequence until
an enemy does something they can perceive.

**The argument that lost, recorded because it was made twice and should not be made a third
time.** Entry 053 gave an unfound hostile a `?` slot and entry 060 argued for narrowing it to an
anonymous mark, both on the same ground: dropping the slot loses the interleaving, and an
interleaved game draws a strip precisely to show the interleaving. That ground is false. The
interleaving a player can *act on* is the interleaving of soldiers they have found, and that is
still drawn in full. What a slot for an unfound hostile adds is two things the player has not
earned — that an enemy exists, and roughly where in the order it acts — and *somebody acts here*
is a weaker claim than a `?` portrait only by degree, not in kind. Neither is a fact about the
player's own side, which is the test contract 3 actually applies. The genre offered no help here
in either direction: every interleaving game in it starts with everybody visible.

**What has to be built with it, or the strip reads as broken.** An unfound hostile's turn now
passes with nothing on screen while time moves. That is the honest presentation and it is the
game. But anything that turn does which the player *can* perceive — a noise heard, a shout picked
up, one of theirs shot at — has to register somewhere, or a player sits through a pause with no
account of it. The happenings block already exists for what happened while it was not your go and
is the obvious home. And the strip is redrawn from what is known *now*, so a hostile found
mid-round enters the order at once, which should read as a discovery rather than as bookkeeping.

**Routed.** Brief five in `docs/interface/briefs.md` and the turn-order section of
`conventions.md` both say this now, and the third bullet of entry 060 is superseded by it. The
View open question *whether an unfound hostile should hold a slot in the turn order at all* is
answered: no. `SandboxFrame.Sees` is already the one question that says whether a hostile is
known, so the strip should ask it rather than grow a second opinion.

## 065 — The pause when it is not your go gets one banner per stretch, not one per turn
**2026-09-09** · **Raised by** interface, for the user · **For** view · **Status** resolved

Entry 064 dropped the unfound hostile's slot from the turn order strip and left a hole: their
turn now passes with nothing on screen while time moves, which reads as a bug. The user asked for
a spinner or a message. **The answer is one indicator per contiguous stretch of hostile activity,
never one per turn**, and the reason it has to be per stretch is the point of this entry.

**A per-turn indicator hands back what 064 withheld.** Count the appearances over a round and you
have the enemy's count and their rough place in the order again — which is precisely the leak
dropping the slot removed, arriving through a different door. Showing it only for hostiles nobody
has found is worse: then the *presence* of the indicator is the tell, and its absence says *this
one you have met*. So it is the same indicator for every hostile turn, known actor or not, and
one indicator for a run of them. It appears when control leaves the player's side and clears when
it comes back.

**Which makes it the alternating games' phase banner, and that is the convention it takes.** XCOM
says *enemy turn* over a whole phase rather than per unit. An interleaved game normally has no
use for that, because the strip carries the identity — here the identity is the one thing that
cannot be shown, so the interleaved presentation collapses onto the alternating one. That is the
second time this project has found the genre's convention already fitting a hole the asymmetry
dug, after Invisible, Inc.'s hidden alarm sub-levels in entry 060.

**Two details, because both are easy to get wrong in the direction of looking broken.**

- **A message with an activity indicator inside it, not an indicator alone.** A bare spinner
  claims *the software is busy*, which is a bug report rather than a turn. The words are what
  claim *somebody else is playing*. The spinner earns its place only on a stretch long enough to
  look frozen.
- **A minimum dwell**, or a resolution finishing in a frame flashes the banner and is worse than
  drawing nothing at all. Roughly 0.6 to 1.2 seconds in the games that do this — an argument, not
  a measurement. **No dwell in captures or headless runs**, by the settle-before-shot rule every
  other animation here obeys.

**What stays countable, deliberately.** Anything a hostile turn does that the player can actually
perceive — a noise heard, a shout picked up, one of theirs shot at — registers per event, and the
happenings block already exists for what happened while it was not your go. Those are things the
player perceived, so counting them is the game working rather than a leak. The banner is not one
of them. And no camera move towards an actor the player has not found, for the same reason the
slot went.

**Routed.** Brief five in `docs/interface/briefs.md`, which is the strip's brief and now carries
the banner with it, and the turn-order section of `conventions.md`.

## 066 — The six are built: one switch for every animation, and a second window that makes "a shipped interface" a thing you can look at

**2026-09-09** · **Raised by** view · **For** view, core, interface and master · **Status** resolved for the six; the notes for Core and Interface below are open

Entry 057's six findings, built on `view/playable`. `subprojects/view.md` has the shape and the
tables. This is the reasoning, and the three decisions the brief left for the session to settle.

**The settle mechanism: a run with `--shot` on it never starts an animation.** The brief allowed
either settling every animation before the shutter or forcing them instantly, and asked for one
mechanism used for all of them. `HexSandbox.Animate` is it — false for the whole of a capture,
turned off for a person by `--still`, asked by everything that moves. The argument for this half
of the choice rather than the other is not about tidiness: settling before the picture would have
put a capture on a code path that had never been measured, where forcing instantly leaves it on
exactly the one entry 053 measured byte-deterministic. Three runs of the pinned command during the
work produced one SHA-256, before and after the walk was built. **If some future animation has to
run during a capture, the thing to change is the capture, not the flag.**

**The gesture set: the right button does both jobs and they are told apart by whether the pointer
moved.** Right-click already fired, so orbit could not be a plain right-drag and something had to
give. What gave is *when* a shot happens: it is on release now, because on press there is nothing
yet to tell a click from a drag by. Under six pixels of travel it was a click. Middle-drag still
pans, and the pointer near an edge pushes the view — guarded on the pointer being genuinely inside
the viewport, which matters more than it used to now that there is a second window for it to be
sitting on.

**`--shot` captures the game and the instruments window is written beside it**, as
`out.instruments.png`, when `--instruments` is on the line too. One answer was really available:
every capture command in `view.md` names a file and means the picture of the game, and a flag that
quietly changed which window a path referred to would have rewritten the meaning of all of them.

**The defaults split between the keys and the harness, and that is what made item 4 cheap.** A
person opening the build is now playing the waystation against `Commander` with windows handed out
and the other side hidden. A capture keeps all three switches off. Making the capture follow the
keys would have made `--ai`, `--windows` and `--omniscient` no-ops-by-default — flags that turn on
what is already on — and every capture command in the repository would have had to be re-read
rather than merely re-run. The keys are the game and the harness is an instrument; they are
allowed to open differently, and saying so out loud is cheaper than a compatibility flag.

**The finding worth the entry: a readout painted across the ground cannot share a colour constant
with the thing standing on it.** Item 5 was *our units lack contrast against the terrain*, and the
obvious fix — raise the two side hues — washed the whole map out. `BuildAttention` tints every tile
a soldier is attending to in that soldier's side colour, and five soldiers on the waystation is a
wash of side colour over most of the ground; brightening the soldier brightened the ground it was
supposed to stand out from. **A body that reads well against terrain it has itself repainted has
not been fixed.** `SandboxPalette.AttentionHue` is now a second, dimmer pair for the field alone:
hue carries the side and is shared, saturation is not. It is the only place in the palette where a
side is two colours, and it is the question to ask first the next time a readout wants one.

What actually fixed the contrast was three things rather than the hue: the hues above 70 per cent
saturation, which no ground fill approaches; a dark contact ring under every body supplying the
shadow a blockout has no ambient occlusion to cast; and both rings widening once the camera passes
`LegibleAt`, which is the same threshold the tile labels already switch off at. The brief asked for
the check at `--fit` as well as close in and it was a different problem there — at 80 metres a
soldier is a handful of pixels and a ring drawn to look right at 36 is a hairline.

**The walk is the resolution drawn over time, and the rules are finished before it starts.** Entry
040 says the mover has not stepped until the window resolves; by the time a walk begins the window
has resolved, every reaction is taken and the soldier is at the far end. Nothing is asked of the
battle part way along one. The route is truncated at wherever the unit actually ended up, so a
reaction that dropped it short is drawn stopping there. Two things that needed doing and only one
of which was obvious: the unit rings moved out of the overlay mesh into the bodies mesh, because a
ring left in the overlay stays on the tile the soldier set off from; and `DrawUnitLabels` reads the
walk too, because a name hanging over the destination while the soldier is half way there is the
map disagreeing with itself.

**The second window is where the interesting decision was, and the brief's own test overruled the
brief's own prose.** 057 named *the debugging readouts and the legend*; the brief also gave the
test — *would a player who never presses `O` want it*. They disagree about the legend, and the test
won: a player wants to know how to move and how to look and does not want to know how to hand the
hostile side to the AI. So the legend split along the seam it already had for reasons of width, two
ranks staying in the main view and the third going. The mode line and the AI's orders block went
with it. `BattleHud` has two entry points now and holds no canvas of its own, and **both are handed
the same `SandboxFrame` in the same call** — a second surface redrawn on its own schedule is the
first chance this code has had to show two moments at once, and it cannot.

**One thing changed that entry 023 had settled, and it is a change rather than an oversight.** The
orders readout is no longer gated on `--omniscient` as well as on being an instrument. Entry 023's
argument is untouched — it is the opponent's mind and it exists because an AI can only be checked by
somebody who can see what it thought — but there is now a window that is nothing but instruments,
so the gate can be *being in it*. Two gates meant that reading the AI's reasoning cost a change to
the map, and pressing `O` is precisely the thing that stops you seeing what a player would have
seen. Separating those two is most of what the second window is for. The `Prospect` leak 023 notes
is unchanged and is still confined to that readout.

**And the claim 023's paragraph could only assert is now demonstrable**: a shipped interface is what
the main view shows with the window shut. That is a thing somebody can look at rather than argue
about, which is the reason it was worth a window rather than a keypress.

**For Core, one note, and it is a request this time rather than a workaround.** Only our side's
moves walk, plus the one hostile move in a turn that opened a reaction window — the window carries
its steps and the sandbox is holding the resolution, so that one can be drawn. Every other hostile
move jumps. Making them all walk needs two things the view cannot get: `Commander.TakeTurn()` runs
a whole turn synchronously and returns nothing about what its orders did, so the picture is at the
end state before control comes back; and `Order` carries `MoveTo` but not the path walked. This is
entry 022's shape again, one level up — the seam that entry wanted for windows, wanted for orders.
It is not urgent and it is not a blocker; it is the thing that stops a player watching a sentry
walk into view, and the sentry walking into view is the game's best moment.

**For Interface, three things the build settled that its research should know before it writes
against them.** Where the player/instrument line currently falls, and that it was drawn by 057's
own test rather than by taste. That the reaction window's answers now include the enemy's reactors
*by default*, since the keys open with windows handed out — `view.md`'s open question about that
got sharper rather than easier. And that `I` is advertised only inside the window it opens, which
is fine for a player and is a cold-start problem for anybody handed the build.

**For Master.** 057's six are done and its Status can move. The next measurement is the same one
as last time and a session cannot run it: a person plays `build/Hexcom.exe` to a verdict.
`view.md`'s `## The job` names the one specified item that can be done while waiting — entry 012's
second, the shot line saying who a shot would wake — and otherwise hands the queue to
`subprojects/interface.md`.

## 067 — The reserve is a ladder in the rules and a number on the screen, and the canon could not have told us
**2026-09-09** · **Raised by** interface, for the user · **For** view · **Status** resolved

The user asked whether two current games had been reviewed — **Warhounds** (August 2026) and
**Future War Tactics** (July 2025) — and said the ladder might bear on the action point interface,
because one of them banks points as this game does. Neither had been reviewed. Neither was on the
brief's list and the session had no knowledge of either, so nothing in `conventions.md` drew on
them. The prompt was right and it produced the section the first draft could not have written.

**Warhounds banks a reserve for overwatch and made it all or nothing.** Declaring overwatch
**commits the operator's remaining action points** and draws a firing area in front of the
soldier. That is the closest thing to `ReactionModel` found in a shipped game, and it removes the
display problem instead of solving it: there is nothing graded to draw, because the transaction is
*spend the rest*. Ours keeps `ReserveFraction` of what is left and rounds away anything under
`ReserveFloor`, so ours has to be drawn.

**And the rules already describe it as a ladder, which is the finding.** `ReactionModel.Banked`'s
own remarks say *the floor makes this a step rather than a slope, and the step is the whole reason
anything weighing a turn has to ask rather than multiply* — nine points up banks nothing, fifteen
banks ten, which is most of a snap shot. `ReserveFraction` is seven tenths precisely to put the
three rungs of the movement economy on either side of the fire mode prices. So the reserve is a
stepped quantity with two cliffs in it, and `BattleHud.ReserveLine` prints
`reserve 24, 17 if you stop here`. **The interface has been smoothing a ladder the rules
deliberately made stepped**, which is the same mistake in the same shape as the alarm rung, and
the user spotted the connection before this doc did.

**What to draw, routed into brief one.** Pips on the soldier, which is the genre's answer, with
two cliffs marked on the row: the point below which stopping banks nothing, and the point at which
the bank first affords a shot and then the better one. Both fall out of `Banked` against
`ReserveFloor` and the loadout's fire mode prices. A player reading that row sees three decisions
at once. Nothing about it touches contract 3 — a soldier's own points are the player's own side's
knowledge, exact in both directions.

**One thing in `game/` worth fixing while there, and it is View's to fix.**
`BattleHud.ReserveLine` recomputes `(int)(ActionPoints * ReserveFraction)` and the floor check
inline rather than calling `ReactionModel.Banked`. One rule, two implementations, which is the
shape entry 038 was about; the second one will drift the first time the first one changes.

**Two smaller Warhounds conventions, both cheap and both about the arc rather than the points.**
Cone placement is entered directly rather than through a nested menu, and its guides single out
fast enter, adjust and cancel as what makes overwatch usable mid-fight. Here `V` and `HoldArc`
take an arc in one press with no adjust step.

**Read, not played, and the doc says so where it matters.** All of the above about Warhounds comes
from its store page, wiki and community guides. What it is used for is narrow: that a shipped game
with a comparable bank chose all-or-nothing. Anything built on the finer detail should verify it
first.

**The lesson about the list, which outlives both rows.** A canon is a list of games whose
conventions are *settled*, which is what makes it the right starting point and also guarantees it
is silent on any mechanic newer than itself. `conventions.md` now has a third shelf for what
shipped while this was being built, and the next question of this shape should be asked the way
the user asked this one: which shipped game has this mechanic, not which famous game has something
like it.

## 068 — Seven merges, the six are built, and the mission is one uncommented line from being a mission
**2026-09-09** · **Raised by** master · **For** content, view, core · **Status** resolved

The largest round yet: Core's objective at a place, Content's finished mission, View's six
findings, and four Interface merges — the conventions, and three that the user drove directly
(064, 065, 067). Every one stayed inside its paths; Interface touched nothing but `docs/interface/`
and the log, which is the scheme holding under the most sessions it has run at once.

**The one thing this round did not close, and it is an hour.** Entry 059 left the reconnaissance
objective commented out in `waystation.hexmission` until Core had the shape; entry 061 built it
and said the line maps straight onto the constructor. Nobody uncommented it, because Core's
brief said *let Content uncomment* and Content's brief had moved on to the second map. So the
build made at the end of this round still carries the walk-out mission. It is now the head of
Content's brief, ahead of the map, on its own branch, and the next build after it merges is the
first one with something in the middle of the mission.

**Statuses.** 057 resolved by 066. 059 open for Content only, routed as above. 060 resolved: the
queue is promoted through View's own brief, which now points at it, so Master promotes by
leaving that pointer true rather than by copying briefs across. 062 open, and its measurement is
the first item of `core/measured`. 063 stays open until `--aside` is in **Seeing it**; it is the
first item of View's brief.

**The trailers.** None of the seven commits carries a `Session:` line. The model is in every
one (Opus, all seven), so the half that matters most is still derivable, but keep-or-restart
was a guess this round. The rule is in `CLAUDE.md` under *Cleaning up*; a reminder at the start
of each session is cheaper than the guess.

**Next round, on the playable path.** Content, `content/reconnaissance`, the hour above — Opus,
fresh or continued. View, `--aside` then the review list then the queue — Opus; the session that
built the six has run one large job and its context is the thing the review list needs, so keep
it if it holds. Core, `core/measured` — Opus, fresh; the first measured numbers in the project.
Interface's onboarding brief, Content's second map and Setting's sites are written and wait on
the user's word.

## 069 — The budget, measured: an increment costs about 2.4% of the week, and the long Master session cost most of it
**2026-09-10** · **Raised by** master, for the user · **For** master · **Status** resolved

The user runs this project on half of a Max 5x weekly limit and asked for a roadmap that fits.
The usage meter on 2026-09-10, two days into a week that resets Tuesday at 3 PM: 48% of the
all-models limit and 53% of the Fable limit, against about twenty increments merged in that
window. Roughly 2.4% of the week per increment with the Master rounds folded in; the pace of the
previous two days was three times what half a budget sustains.

**What the meter blamed, and it was right.** 93% of usage ran above 150k context. That was not
the territory sessions, which start fresh and run one brief; it was the Master session, sixteen
jobs long on Fable, closing every round with the whole project in its context. So the cost of an
increment was mostly the context that closed it, and the fix is Master's own shape: fresh on
Opus for routine rounds, restarted rather than continued, Fable only to argue the breakdown.

**What was set.** The cadence is in `subprojects/master.md` — two rounds a week of three or four
fresh sessions, stop at half the meter, a play-through per round — and the roadmap is in
`map.md` under **Roadmap**, five milestones each of which is a state a person can play. Milestone
1 is the week after the reset; milestone 3 inside two months; past 3 the calendar is art and a
person's hours.

**Pushed back on, and where it landed.** *Years* was the horizon the user offered. The rules are
largely built and the measured cost puts the campaign vertical slice inside a quarter, so the
decision that decides years — a campaign you sell or a campaign you finish — belongs at
milestone 5 and not before, and the plan does not let it shape the next three months.

**This week is spent.** At 48% with five days to the reset, the rule says stop. The one hour of
work that would change the next build — the reconnaissance uncomment at the head of Content's
brief — waits for Tuesday with everything else.

## 070 — The interface gets an evidence layer: one game per file, XCOM 2 first, and its mods are the better half
**2026-09-10** · **Raised by** master, for the user · **For** interface, view · **Status** resolved

The user read the conventions doc, called it a good start, and asked for the grain underneath
it: a detailed report on the finest details of the in-mission interface of several games,
starting with XCOM 2 and its popular mods. They also asked that this happen **before View builds
anything more**, which reorders the queue rather than adding to it.

**Why the ask is right, and it is righter than it first looks.** `conventions.md` answers nine
questions at the altitude of *what the genre does*. That is the correct altitude for a standard
and the wrong one for a work order: a View brief is a sufficient prompt only if it can say where
the figure sits, what gesture reveals its terms, what a hover does and what cancel undoes. None
of that exists in writing. The stronger half of the idea is the mods. XCOM 2's UI mod ecosystem
is a download-counted record of what the genre's best-selling interface *failed to tell its
players*, written by the players who wanted it — a gap that was worth somebody's weekend, ranked
by how many people shared the complaint. No other game on either shelf offers that, and entry
067 already showed that the question *which shipped thing solved this* beats the question *which
famous game is like this*.

**Two things argued, and both shaped the brief rather than the answer.** First, *several games*
was cut to one. Depth is the whole request, and a session that covers five games covers each at
the altitude the conventions doc already has; the rest of the shelf is the next job and follows
the template this one sets. Second, this territory cannot play — it reads. A finest-detail
report written from model memory will be confidently wrong about exactly the specifics that make
it useful, so every non-obvious claim in the reference files carries one of three tags:
**verified** with a link, **remembered**, or **inferred**. *No source found* is a legitimate
entry. A file a View session cannot audit is worse than no file, because it will be built from.

**The shape that came out of it.** A new `docs/interface/reference/` directory, one file per
game, ten fixed headings carried even where the answer is *this game has no such thing*. The
standard is not rewritten: `conventions.md` stays the recommendation layer and the reference
files are the evidence under it. A fine detail that changes a queued brief goes in as an
amendment appended to that brief, on the same reasoning that keeps this log append-only.

**Heading 5 is expected to be thin, and that is the finding.** XCOM 2 draws the enemy the moment
a unit sees one and has no contact file, so contract 3's subject has almost no exemplar in the
game this territory is about to study hardest. The brief says to record the little there is and
not to stretch it, because the temptation in a per-game file is to fill every heading.

**Onboarding moves behind it.** It was the standing brief in `subprojects/interface.md` and is
now the queued one in the same file, kept verbatim. The order is not arbitrary: half of what a
player must be told before turn one is what the genre's interface already teaches without telling
anybody, and that is what the reference pass is for.

**The budget rule bites here.** Entry 069 set *stop at half the meter*, and the meter read 48%
on the day this was written with five days to the reset. The brief is ready; running it is the
user's call against a week that the rule says is already spent.

## 071 — The reference set gets screenshots, five games the user owns, and a rule that a file is written because something needs it
**2026-09-10** · **Raised by** master, for the user · **For** interface, view · **Status** resolved

Extends 070. The user wants the per-game treatment across a list rather than one game, named
five they own and can capture — XCOM 2, Warhounds, Phantom Brigade, Future War Tactics and
Invisible, Inc. — asked for other major titles to be added, and set the condition that matters
most: **the files reference actual screenshots and make detailed observations about them, not
just words on the web.**

**The screenshot condition is the substance of this entry, and it is right.** A report assembled
from published prose says what a game *has*. A screenshot says where it is, how large it is, what
sits next to it, and what the game chose not to draw at all. The second kind is what a View brief
needs and the first kind `conventions.md` already contains. So the tag set from 070 gains a
fourth and strongest member, **observed** — read off a named shot committed to the repository —
ahead of verified, remembered and inferred.

**The protocol, in `subprojects/interface.md` under *The reference set*.** Raw captures go to
`reference-inbox/<game>/` at the repository root, gitignored, read by absolute path so a session
in a worktree needs no copy. Curated crops that carry a claim are committed to
`docs/interface/reference/shots/<game>/`, roughly twenty per game, named for what they show, and
cited by filename from the claim. A crop is preferred to a full screen: smaller, and better
evidence, because it records which part of the picture was being read.

**Two constraints on the capture side, both found rather than assumed.** `ffmpeg` is not
installed on this machine, so a video clip cannot be read until it is; stills are the request
unless the thing is a transition, a timing or a hover, and then the job says which frames matter.
And a job asks for **one shot list, before reading anything** — the exact screens, named by what
must be visible in each. A capture session is the user's time, and a job that asks in dribs
spends it four times over.

**One game per session, and the reason is images.** Prose compresses into a summary; forty
screenshots do not. A session that reads a game's evidence has spent most of an increment on the
reading, which is the right price once and the wrong price twice in one context. This is the same
conclusion 069 reached from the meter, arrived at from the other end.

**The list, tiered by whether it can be photographed.** Tier A is the five the user owns and gets
a file each. Tier B is five that answer a question Tier A cannot — Mutant Year Zero's detection
radii, the Shadow Tactics line's cone drawing, Phoenix Point's per-body-part targeting, which is
the nearest exemplar anywhere for contract 6's six faces, Into the Breach's perfect information,
and Tactical Breach Wizards on legibility and undo. Tier C is the grammar and gets cited rather
than filed: Jagged Alliance 3, Baldur's Gate 3, Xenonauts 2, Door Kickers 2, Battle Brothers,
Classified: France '44, Commandos: Origins.

**Pushed back on, and the answer is an interleave rather than a cut.** Five Tier A files is about
five increments, against a milestone 1 the roadmap sizes at eight to ten, and it would put the
whole of the next week into research ahead of View building anything — while the largest finding
the interface has produced so far came from a single play-through, not from a survey. The
recommendation is order, not scope: XCOM 2 for the grammar, then Invisible, Inc., which is the
only game on the list with the thing this game is *about* and feeds the one queued brief that
nothing currently draws. View builds against those two while Warhounds, Phantom Brigade and
Future War Tactics follow. Phantom Brigade earns its place on a point the canon cannot make —
it is the only shipped interface that draws *what the enemy is about to do* as a first-class
object on a scrubbable timeline — and Future War Tactics is thin by the conventions doc's own
account, so both are cheap to defer and neither is dropped.

**The standing rule that came out of it: a reference file is written because something needs it.**
The set is not a survey to be completed. Tier B is on demand, and the brief that summons a file
names the question it is summoned to answer.

## 072 — Five reference jobs run at once, which costs a template written in advance and a synthesis pass afterwards
**2026-09-10** · **Raised by** master, for the user · **For** interface, view · **Status** resolved

Follows 071, and overtakes the interleave recommended there. The user is running the reference
jobs on Sonnet, where the load is low enough that all five Tier A games can go at the same time,
and chose to do that rather than sequence them behind View. The token argument in 071 was the
argument for sequencing and it largely dissolves at that model, so the sequencing goes with it.

**Sonnet is the right call here, and the screenshot protocol is what made it right.** The rule in
`subprojects/master.md` reserves Sonnet for jobs whose output is transcription or lookup and
warns off research that ends in a brief. The first version of this work was the second kind. The
protocol in 071 turned it into the first: look at a named picture, write down where the thing is
and what is beside it, tag the claim. The brief now **forbids a reference file from recommending
anything** — a file that argues is a file whose evidence can no longer be separated from its
conclusions — and that prohibition is exactly what keeps the job inside Sonnet's competence.

**So a synthesis pass is now compulsory rather than optional**, and it is queued in
`subprojects/interface.md` immediately after the five. It folds each file's *what transfers*
footer into `conventions.md`, appends amendments to the queued briefs, and reports which of the
ten headings the set was unanimous on and which it split on — five games agreeing is the evidence
for **convention** under entry 058, and five games differing is the evidence that this game must
choose and argue. That job is not a transcription job and the model note applies to it and not to
the five that feed it. This is the real price of parallelism and it is worth paying: the
alternative was five files each half evidence and half opinion.

**The one thing that genuinely broke under parallelism was the template.** 070 and 071 both said
the first file sets the template and four follow it, which is a sequencing dependency hiding
inside a style note — run five at once and none of them has a template to follow, and the set
cannot be read across, which is the whole reason it is a set. Fixed by writing the ten headings
out in full in the brief, along with the four things every file opens with and the footer every
file closes with. **The template is nobody's to invent now**, and that is what makes the five
independent.

**Second collision, fixed the same way: five sessions must not write shared files.** Each job
writes `reference/<game>.md` and `reference/shots/<game>/` and nothing else — not
`conventions.md`, not `briefs.md`. Four sessions appending to one priority queue is four
conflicts in the file that can least afford ambiguity, and the *what transfers* footer carries
everything a session would have wanted to put there until the synthesis pass folds it in.
`decisions.md` remains the exception it always is.

**ffmpeg is installed**, at the user's instruction: Gyan build 9.0.1 through winget. Its
directory is not on the `PATH` of a shell that was already running, so the brief gives the full
path. The rule that matters more than the installation: **a clip is read by pulling named frames
out of it, never by sampling it at a fixed rate.** A frame costs about what a paragraph of
reading costs, so half-second sampling of a ten-second clip is most of a context window spent
watching a menu open.

**What is unchanged from 071.** One game per session — that was always an argument about what a
single context can hold and never about how many contexts run, so parallel does not touch it.
And a reference file is still written because something needs it: Tier B stays on demand.

## 073 — Two passes, not one: the documentary pass buys the question list, and the pictures come second
**2026-09-10** · **Raised by** master, for the user · **For** interface, view · **Status** resolved

Revises 071 and 072, which both had the capture happening first. The user will generate no
screenshots or video until a first pass has run, and asked that the pass **document its own
gaps** so the capture session fills them. Ten sessions, numbered, prompted with *read
interface.md and do job N* — five games the user named and five added here.

**Inverting the order is better than what it replaces, and the reason is not thrift.** 071 had
each job ask for a shot list before reading anything, which meant guessing what a game's HUD
would turn out to be unclear about. A documentary pass knows the shape of each game and is
unreliable on precisely the details this project needs — where a thing sits, how large it is,
what is beside it — so the most useful thing it can produce is an *aimed* list of those details.
The capture session then photographs answers to questions instead of screens that looked
relevant. **Pass one carries no `observed` tags at all and that is correct rather than a
shortfall**; the gap list is its second deliverable and not an apology for the first.

**The failure mode this creates, and the rule written against it.** A documentary pass does not
know what it does not know. It will write a confident sentence about a HUD element and never
think to flag it, and a gap list assembled from *where the session happened to feel unsure* will
be short in exactly the places that are most wrong. So the gap list is not collected by feel:
**every one of the ten headings ends with its own *what a picture would settle* line**, asked
deliberately, even where the heading reads as complete. A heading with nothing to ask is an
explicit claim that published material fully determines it, which is a claim worth being on the
record and being wrong about.

**The ten, and what the numbering is for.** Jobs 1 to 5 are the user's: XCOM 2 with War of the
Chosen and its mods, Invisible Inc., Warhounds, Phantom Brigade, Future War Tactics. Jobs 6 to 10
are the ones added to answer a question those five cannot: Mutant Year Zero, the Shadow Tactics
and Desperados III line as one file, Phoenix Point, Into the Breach, Tactical Breach Wizards. The
table in `subprojects/interface.md` carries the number, the game, the branch and the reason, so
that *do job N* is a complete instruction. Only 1 to 5 can have their gaps filled with captures;
6 to 10 phrase theirs as *what would settle this*, and an unanswerable question is still worth
recording because it tells the synthesis how much weight that heading can bear.

**Predicted now so it is not mistaken for failure later: job 3 will be the thinnest file in the
set and will have the longest gap list.** Warhounds shipped too recently for published material
to cover its HUD, and it is in the set because of entry 067 — it is the only shipped game found
with a reserve like ours, which is exactly the kind of thing that is not written down anywhere
yet. Twenty good questions is the right outcome there and padding would be the wrong one.

**Ten parallel sessions cost one more shared-file rule than five did.** 072 already kept them out
of `conventions.md` and `briefs.md`. `../decisions.md` now joins that list **for this pass only**,
which is a deliberate exception to rule 3 of the map: ten simultaneous appends to an append-only
log is the one collision the scheme has no cheap resolution for. The intent of rule 3 is
preserved rather than waived — a finding about a neighbour goes in the file's own *what
transfers* section, marked as a proposal for the territory it concerns, and the synthesis session
appends all of them in one commit. **The debt is explicit and it has a named payer.**

**The synthesis is reduced to a sketch on purpose.** The user will brief it properly once the ten
files exist and their gaps are filled, on Opus or Fable in a clean session. Writing that brief now
would mean guessing the shape of ten documents that do not exist. What is recorded now is that it
is compulsory, what it must do, and that it is not a transcription job — the three things that
would be expensive to rediscover.

## 074 — The usage meter is a feed now, and the first thing it says is that the week is over
**2026-09-11** · **Raised by** master, for the user · **For** master · **Status** resolved

The user stood up an endpoint that republishes their Claude usage every fifteen minutes and gave
Master the token for it. The command and the environment variables are in
`subprojects/master.md` under **The budget**; the token itself lives in
`.claude/settings.local.json`, which is per-machine and gitignored, so no secret is in the
repository and the command carries no literal.

**This changes the budget from something remembered to something derived**, which is the same
move `map.md` makes about every other kind of status and for the same reason. Entry 069's 48% was
a single reading from one Tuesday that every later session would have had to either trust or
re-ask a person for. A figure a session can fetch cannot go stale, and the stop-at-half rule
stops depending on the user volunteering the number at the right moment.

**The first reading, 2026-09-11 at 20:30 Vancouver.** Session 23%, resetting the same evening.
The week 52% on all models and 53% on Fable, both resetting Tuesday 15 September at 3 PM. Four
hundred and nine requests across four sessions in seven days, and **82% of usage above 150k
context** against 93% the day before.

**Three things it says that a single number would not have.**

The stop line is behind us. Entry 069 set *stop at half*, both meters now read above it, and
four days remain before the reset. The rule was written for exactly this moment and the cost of
having a rule is honouring it when it is inconvenient.

The day cost four points, which is under two increments at 069's rate, for a day that produced
four Master commits and a territory's worth of briefing. That is the cadence working rather than
an overrun.

The context share fell from 93% to 82% and is still the dominant term. Master restarting fresh
on Opus is doing what 069 predicted, and the remaining 82% says the shape of the problem has not
changed — long contexts are what this project spends, and every structural decision that keeps a
session short is worth more than any decision about what a session does.

**What it means for the ten reference jobs.** They are briefed and ready and the meter says they
do not run this week. There is also an engineering reason not to fire all ten at once on an
untested brief: *read interface.md and do job N* has never been executed, and ten sessions
sharing one undetected defect is ten files to redo. One job first, read it, then the other nine
after the reset. The budget rule and the sensible order agree, which is usually a sign that both
are right.
