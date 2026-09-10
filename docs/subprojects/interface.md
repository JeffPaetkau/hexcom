# Interface design — what the genre does, and the briefs that follow from it

Research and brief-writing for the player's interface. This territory plays other games, reads,
and writes; it draws nothing and touches no code. Its output is a standard the View territory
builds to, and a queue of View briefs written to that standard.

Read [../map.md](../map.md) first.

## Owns

```
docs/interface/**      the conventions doc, and the queue of interface briefs
```

## Must not touch

All code, all tests, `game/**`, `docs/design.html`, and the other territory docs. If a
convention wants a rule that does not exist — a query the HUD would need, a thing the AI would
have to expose — that is a proposal for Core in `../decisions.md`, not a request.

**View builds; this territory says what to build and why.** A brief written here becomes View's
job only when Master promotes it into `subprojects/view.md`, so two territories never write the
same `## The job`. Write briefs in the shape `master.md` describes: the seam by name, the
decisions to settle first, what is out of scope, and how to know it worked.

## Depends on

- **Contract 3 in `../map.md`** — information is asymmetric on purpose, and a convention from a
  game where the enemy is always drawn does not transfer unexamined. Every convention this
  territory recommends has to say what the asymmetry does to it.
- **The interface audit in `subprojects/view.md`** — what the AI weighs and where the HUD shows
  it. That is the list of what a player here has to be able to read; the genre says how.
- **Entry 049 in `../decisions.md`** — the keys and the script steps are two callers of one
  surface on `HexSandbox`, and every capture is deaf. A brief that adds an interaction adds a
  step, or says why it cannot.

---

## The job — the conventions, and the first queue

Branch `interface/conventions`. Take a worktree; the rule has no exception for prose.

**What it is.** The greybox is built and the first person has played it (entry 057). The
interface was designed by the sessions that built the rules, against the audit of what the AI
reads, and never against what a player of this genre expects to find under their hands. This
job supplies that: what is standard in turn-based squad tactics, what of it applies here, and
a queue of briefs for View in priority order.

**Where to look.** The genre has a settled grammar and a handful of games that set it: the
modern XCOM pair, Phoenix Point, Jagged Alliance 3, Battle Brothers, Into the Breach, and the
older line — X-COM, Silent Storm, Xenonauts — whose conventions the modern ones simplified.
Read their interfaces, not their rules. The questions, roughly in the order a player meets them:

- **The camera** — orbit, pan, zoom, edge-scroll, what the mouse does versus the keyboard, and
  whether rotation is free or stepped. Entry 057 already says the user wants it free and smooth
  and mouse-driven; the research says what *smooth* means in this genre in degrees per second
  and what a stepped camera was ever for.
- **Selecting and ordering** — how a unit is chosen, how a move is previewed and committed, how
  an action bar is laid out, what a right-click means, and where confirmation sits.
- **Turn order and whose go it is** — the strip, the timeline, the initiative bar, and how the
  games that interleave (this one does) show it against the ones that alternate.
- **What of the enemy is drawn** — fog, last-known-position ghosts, detection meters, alert
  states. This is where contract 3 bites: the genre draws the enemy the moment a unit sees it,
  and this game additionally draws what the enemy holds on *you*. Say what the convention is
  and what this game does that has no convention.
- **Reactions** — overwatch cones, the interrupt prompt, how the games that let a player answer
  mid-move (few do) present the choice and the clock.
- **Movement and shooting animation** — how long a move takes on screen, whether it can be
  skipped, and what the camera does during it. Entry 057 asks for movement along the path; the
  research says how fast.
- **Readouts** — hit chance, cover, exposure, and how much arithmetic is shown against how much
  is hidden behind a number. The audit shows everything the AI weighs; the genre shows less, on
  purpose, and the question is which of those is right for a game whose subject is information.
- **Debug and developer overlays** — what ships and what is a tester's, and how the games that
  keep both separate them. Entry 057 asks for the legend and the instruments in a second window.

**Where the output goes.** Two files.

- `docs/interface/conventions.md` — one section per question above: what is standard, with the
  games it comes from; what this game already does; what the asymmetry changes; and a
  recommendation. Short. A convention is a sentence and a source, not a survey.
- `docs/interface/briefs.md` — the queue, in priority order, each brief complete in the shape
  Master writes them. The first entries are the six findings in entry 057, rewritten against
  the conventions so that View builds the genre's answer and not the first one that works.
  After those, whatever the conventions doc found that the audit missed.

**Settle before writing much.** What the standard is *for*. **The user's rule, entry 058: the
convention is the starting point, and a departure from it is a proposal that has to argue its
case.** A convention is worth following because a player arrives already knowing it, and worth
breaking only where this game's subject — who saw whom first — needs something the genre never
had to show. So every recommendation is one of two things, and says which: *the convention, as
is*, or *a departure, and here is why this game needs it*. View does not have to guess which
conventions are load-bearing, and the default when in doubt is the convention.

**Out of scope.** Building anything. Art direction, which is `docs/setting.md`'s register and
Art's job. Rules, which go to Core through `../decisions.md`. The strategy layer's interface,
which has no rules to show yet.

**How to know it worked.** A View session can be pointed at the first brief in
`docs/interface/briefs.md` and need nothing else; and a reader of `conventions.md` who has
played XCOM can say in one sentence what will feel familiar here and what will not, and why.

## Recent work

```bash
git log --oneline -20 -- docs/interface docs/subprojects/interface.md
```
