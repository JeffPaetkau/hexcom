# Decisions and cross-boundary findings

**Append-only.** Add entries at the bottom. Never edit or reorder one — if an entry turns out to
be wrong, write a new entry that supersedes it and say so in both directions.

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
**2026-09-06** · **Raised by** master · **For** view (with core to confirm) · **Status** open

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
**2026-09-07** · **Raised by** core · **For** core (with view to say what it needs) · **Status** open

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
**2026-09-07** · **Raised by** view · **For** core and content · **Status** resolved (view's half)

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
**2026-09-07** · **Raised by** view · **For** view (later), gated on content · **Status** open

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
**2026-09-07** · **Raised by** content · **For** core · **Status** open

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

## 009 — The interface has been audited against the scorer, and the list lives in view.md
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

**Two rows could not be closed and are entries 010 and 011 below.** Two more are blocked on
things already recorded here: the attention cone still misreports range (006, still gated — 007
settled the hex but says the demo map is too small, so an honest cone still fills the viewport),
and the entire posture half of the model is blocked by 010.

**The finding worth carrying whatever else happens:** the exercise works. Contract 2 was written
on the theory that making the AI and the interface read one surface would expose gaps in both,
and it did — the largest thing the audit found is a place the *AI* reads something it should not,
and it was found by asking whether a player could be shown it. Nobody was looking for that.

---

## 010 — `Tactician.Aimed` reads how much the enemy has detected you, exactly
**2026-09-07** · **Raised by** view · **For** core · **Status** open

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

## 011 — Three things the AI will want that no query exposes, so the interface cannot show them either
**2026-09-07** · **Raised by** view · **For** core · **Status** open

Found by the audit in entry 009. All three are contract 2 in the ordinary direction: a query
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

## 012 — Interface has earned its own doc, and cannot give itself one
**2026-09-07** · **Raised by** view · **For** master · **Status** open

[map.md](map.md) says View is two territories sharing one doc, and that interface earns a doc of
its own once it has a brief of its own. It now has one: the audit in entry 009 and the fix list
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
