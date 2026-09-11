# Interface design — what the genre does, and the briefs that follow from it

Research and brief-writing for the player's interface. This territory plays other games, reads,
and writes; it draws nothing and touches no code. Its output is a standard the View territory
builds to, and a queue of View briefs written to that standard.

Read [../map.md](../map.md) first.

## Owns

```
docs/interface/**      the conventions doc, the per-game reference files, and the queue of briefs
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

## What landed on `interface/reference-xcom2`

`docs/interface/reference/xcom2.md` exists: the first file of the evidence set, ten headings deep
against XCOM 2 and War of the Chosen, in-mission only, each claim tagged **verified**,
**remembered** or **inferred**. `conventions.md` gained the one line the brief allowed, pointing
at `reference/`, and nothing else in it changed.

The first pass leaned on a page-fetch tool that Nexus, Steam and StrategyWiki all returned HTTP 403
to, so it read search excerpts rather than pages. Asked directly whether it had used screenshots,
the honest answer was no — so a second pass opened a real browser instead, which none of those
sites blocked, and read the pages and one screenshot directly. Three things worth not re-deriving:

- **Heading 5 was thin, exactly as the brief predicted.** XCOM 2 draws a found enemy fully and
  permanently once seen and has no contact file, no rung and no marker on a lost target. There was
  nothing to stretch it with, so the heading names that and moves on — the turn-based stealth
  shelf already in `conventions.md` is where this heading's real answer lives.
- **One screenshot overturned a remembered claim, and it is the one amendment this job produced.**
  A real capture of the targeting screen shows the hit-chance breakdown as a docked list at the
  bottom of the screen, not a hover tooltip on the target's card — the opposite of what the file
  first said from memory, and of what `../briefs.md`'s Brief One cites as "XCOM's hover" to copy
  the gesture from. Recorded as an amendment on Brief One rather than a silent fix, per the job's
  own rule about routing findings.
- **The mods themselves still needed no `decisions.md` entry.** Every one found, now with exact
  current counts read from its own page rather than a search excerpt, is a prosthetic for a single
  missing preview or shortcut — a warning before a click, a number instead of a bar, one click
  instead of many — never a request for a different game, and none named a query this project's
  briefs don't already cover or a rule Core doesn't already expose.
- **One row is still explicitly unresolved.** Which tactical-HUD replacement is currently most
  subscribed was not settled even with a working browser — the Nexus "most endorsed" listing was
  not filtered and read before the session's time on this ran out. Recorded as a gap, not guessed.

---

## The job — the first five minutes, and what has to be taught

Branch `interface/onboarding`. Take a worktree; the rule has no exception for prose.

Onboarding decides what a player must be told before turn one, and half of that answer is what
the genre's interface already teaches without telling anybody.

**What it is.** The conventions are written and the queue is written (entry 060), and both assume
a player who already knows what a hit chance and an action point are. Neither says how anybody
learns *this* game. That is the next interface question and it is the one the second play-through
will run into hardest, because the model a player has to hold here is not the genre's: a soldier
has two pockets of points rather than one, spending everything means answering nothing, a contact
is a file that decays rather than a unit that is spotted, and the marker on the map is somebody
else's belief and not a fact.

**Where to look.** The genre teaches in four ways and this game can afford at most two of them.
XCOM 2 ships a scripted tutorial mission that takes control away. Into the Breach teaches by
showing every enemy's next action, so the rules are legible from the first turn and there is no
tutorial at all. Invisible, Inc. teaches by making the first level's single guard unmissable, and
by drawing the cone that everything else in the game is about. Jagged Alliance 3 and Battle
Brothers teach by tooltip and let the player lose. Say which of those this game is, and why —
Into the Breach's answer is the one that costs no content, and this game already draws a graded
attention field per tile, which is the same move.

**The questions.**

- **What a player must know before turn one, and what can wait.** The reserve is the candidate
  for *before*: a player who spends all their points is holding no reaction and will not find out
  why until it costs them.
- **How a rung is taught.** A five-step ladder means nothing until a player has watched one move.
  What action makes it move visibly and cheaply, in the first minute?
- **What the game should refuse to let a player do silently.** Not a confirmation dialogue, which
  the genre has decided against for moves. A warning drawn on the thing — the genre's concealment
  ring is exactly this and it is brief four in the queue already.
- **Tooltips, and where the arithmetic lives.** Brief one moves the figures onto the things they
  describe and picks one gesture for *show me the terms*. Onboarding is the other half of that
  decision, and it should not be settled twice.
- **What the mission briefing is for.** `Objective.Brief` exists, the mission file carries a
  briefing, and the only way to read it is a key a tester presses. The genre puts it on a screen
  before the battle.

**Where the output goes.** A new section in `docs/interface/conventions.md` — *Teaching it* — in
the same shape as the others: standard with its games, what this game does, what the asymmetry
changes, a recommendation tagged **convention** or **departure**. Plus briefs appended to
`docs/interface/briefs.md`, after the six that are there.

**Also re-prime the queue.** Read `git log --oneline -- game docs/interface` and
`../decisions.md` for entries appended since 060. A brief whose subject has landed comes out of
the queue; a brief the play-through contradicted gets rewritten. Do not record what is in flight
and do not name a branch that is not merged — the queue is a work order, never a status board.

**Settle before writing much.** Entry 058's rule still holds and applies here twice over: the
convention is the starting point and a departure argues its case. The temptation in onboarding is
to invent, because the model is unusual. It is also the place where inventing costs most, since a
player who does not recognise the *teaching* cannot tell whether they are confused by the lesson
or by the game.

**Out of scope.** Building anything. Writing the tutorial's words, which is `docs/setting.md`'s
register and Setting's job once there is a shape to fill. Rules, which go to Core through
`../decisions.md` — and a tutorial that needs a rule is a strong signal the lesson is wrong.
The strategy layer's interface, which still has no rules to show.

**How to know it worked.** A View session can be pointed at one of the new briefs and need
nothing else; and somebody who has never played this game can be handed the recommendation and
say what they would understand about the enemy after one turn.

---

## What landed on `interface/conventions`

Entry 060 has the reasoning. What exists:

- `docs/interface/conventions.md` — nine sections, one per question a player meets, each with the
  standard and its games, what this game does, what contract 3's asymmetry changes, and a
  recommendation tagged **convention** or **departure** per entry 058.
- `docs/interface/briefs.md` — six View briefs in priority order, with an amendment sheet at the
  head for entry 057's six findings, which are routed already and are deliberately not re-issued
  as briefs here.

Three things worth not re-deriving:

- **The largest finding is placement, not content.** The interface audit asked whether everything
  the AI weighs is visible and it passed; nobody asked *where*, and the answer is a panel of
  about twenty text lines at the top left.
- **Half the genre list is the wrong shelf.** The tactics canon sets the camera, the action bar,
  the turn order and the animation. It has nothing on a contact file, because no game on it has
  one. Invisible, Inc., Mutant Year Zero and the Commandos line are where those conventions come
  from, and Invisible, Inc.'s hidden alarm sub-levels are contract 3's coarse rung shipped by
  somebody else.
- **Nothing in the research needed a query Core does not expose.** The one gap that does is
  entry 012's second item, which was already open.

## Recent work

```bash
git log --oneline -20 -- docs/interface docs/subprojects/interface.md
```
