## C1 · heading 3 · is the shot breakdown open by default, or behind a click?

Captured by Jeff, described in chat, filed here for whoever runs the `interface/captures`
pass-two fill.

**Two frames, both against Jose Luis Soto's `Fire Weapon` targeting on the same target:**

1. `c1-breakdown-expanded-on-target-select.png` — directly after selecting the target, before
   any further click. Full breakdown showing: `HIT 68%`, `AIM +65%`, `WEAPON RANGE +3%` on the
   left, `DAMAGE 3-5`, `CRIT 40%`, `FLANKING TARGET +40%` on the right.
2. `c1-breakdown-collapsed-after-chevron.png` — after clicking the chevron beside the panel
   title. Collapses to just `HIT 68%`, `DAMAGE 3-5`, `CRIT 40%` — `AIM`, `WEAPON RANGE` and
   `FLANKING TARGET` drop out of frame.

**Finding, per Jeff:** the breakdown is open (expanded) by default on entering targeting mode.
The chevron toggles it closed, and the closed state is *sticky* — selecting a new target after
collapsing it stays collapsed, rather than resetting to expanded per-target.

This bears directly on `conventions.md`'s held-key-disclosure recommendation, marked
**provisional** against this entry: XCOM 2 defaults to full disclosure and only lets the player
fold it away, which is the opposite of a gated reveal.
