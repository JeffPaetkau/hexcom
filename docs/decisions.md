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

## 003 — The scale split is done, and 002 was wrong about what it broke
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

## 004 — The interface cannot show the range the rules judge by
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

**What to do, and when.** Not yet. The right cone depends on the metres-per-hex figure (003), and
drawing a truthful cone at the wrong scale is not progress. When that figure is settled, revisit
this with the option of a graded falloff or a marked band at the range threshold rather than a
hard-edged wedge — the model does not have a hard edge either.
