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
