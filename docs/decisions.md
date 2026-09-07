# Decisions and cross-boundary findings

**Append-only.** Add entries at the bottom. Never edit or reorder one — if an entry turns out to
be wrong, write a new entry that supersedes it and say so in both directions. Append-only is what
lets several sessions write here on the same day without conflicting.

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
