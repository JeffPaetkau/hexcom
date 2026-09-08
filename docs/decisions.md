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
