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

## The reference set — what it is and the rules that built it

`conventions.md` is the recommendation layer. Underneath it sits one file per game in
`docs/interface/reference/`, at the grain a View brief needs: where the figure sits, what gesture
shows its terms, what a hover does, what cancel undoes. Ten files, about 3,700 lines, built in
one parallel round.

**Two passes, and only the first has run.**

| | |
|---|---|
| **Pass one — documentary** | Published material only. **No file carries a single `observed` tag**, which is correct rather than a shortfall. Each ends with a numbered list of what a picture would settle, and those 89 questions are the pass's second deliverable. |
| **Pass two — observed** | The user captures against a *ranked* list, drops the results in the inbox, and the gaps are filled in place. The ranking is the synthesis's job, because a question's importance is only visible once all ten files are read together. |

### The ten files, and what each was brought in to answer

| # | File | Why it is in the set |
|---|---|---|
| 1 | `xcom2.md` | the grammar every player arrives already knowing, plus a download-counted record of what it failed to tell them |
| 2 | `invisible-inc.md` | the closest relative in existence — cones, a *noticed* state short of seen, an alarm ladder whose rungs are hidden on purpose |
| 3 | `warhounds.md` | the only shipped game found with a reserve like ours, and a 2026 free camera |
| 4 | `phantom-brigade.md` | the only shipped interface that draws what is about to happen as a first-class object on a scrubbable timeline |
| 5 | `future-war-tactics.md` | colour-coded zones for movement and attack, and a recent small-team answer to the whole HUD |
| 6 | `mutant-year-zero.md` | detection radii drawn only in the mode that needs them, and shrunk by an action the player takes |
| 7 | `shadow-tactics.md` | the best cone drawing shipped, and a pause-plan-execute mode. Covers Desperados III too |
| 8 | `phoenix-point.md` | per-body-part targeting, the nearest exemplar anywhere for contract 6's six faces, and a dispersion reticle instead of a percentage |
| 9 | `into-the-breach.md` | perfect information and enemy intent, with contract 3's asymmetry switched off |
| 10 | `tactical-breach-wizards.md` | the newest game in the set: no hit chance at all, binary cover, and rewind as confirmation |

**Jobs 1 to 5 can have their gaps filled from play; 6 to 10 probably cannot**, so a question
about those is phrased as *what would settle this* rather than *please capture this*. An
unanswerable question still earns its place: it says how much weight a heading can bear.

**Tier C, cited but not filed:** Jagged Alliance 3, Baldur's Gate 3, Xenonauts 2, Door Kickers 2,
Battle Brothers, Classified: France '44, Commandos: Origins. A file of their own only when a
brief names the question it wants answered.

### The template, which is fixed and is nobody's to invent

Ten headings, in this order, in every file, carried **even where the answer is *this game has no
such thing*** — an empty heading is a finding about the game, and several of the most valuable
rows in the set turned out to be the empty ones. Under each: the observations with their tags,
then that heading's *what a picture would settle* line.

1. **Screen furniture** — every persistent element of the tactical HUD: where it sits, what it
   shows, when it appears and when it goes away.
2. **The soldier** — how actions are shown and spent, the ability bar, the hotkeys, what a hover
   over an ability reveals, what cancel does and how far back it goes.
3. **The target** — the shot readout line by line: every term in the breakdown, whether the terms
   are shown by default or behind a gesture, how targets are switched and in what order.
4. **The tile** — movement range and its bands, the path preview, cover indicators, any
   concealment or detection ring, and which are drawn on hover versus after a commitment.
5. **The enemy** — how a suspected, remembered or unseen enemy is drawn if at all; the alert
   states and their icons; the moment the game admits a contact.
6. **Turn order and time** — whether there is a strip, what an interruption looks like, and what
   the player is shown while it is not their go.
7. **Reactions** — how a held action is declared, whether its arc or zone is drawn, and what the
   trigger looks like at the moment it fires.
8. **Camera and input** — default binds, drag gestures, rotation steps and their speed, the
   storey or level control, cycle-target keys.
9. **Confirmation and refusal** — what takes a second click, what warns, what the game lets a
   player do irreversibly in silence, and what it will not let them do at all.
10. **What the game hides, and what its players added** — mods, community fixes, options buried
    in a menu.

**Each file opens with** a paragraph on what this game is the authority on and what it is only an
instance of; the tag key; the sources; and a *nothing found* list. **Each file closes with** *What
transfers* — naming the brief or conventions section each line bears on, without writing the
recommendation itself — and *The gap list*.

### The four tags

| | |
|---|---|
| **observed** | read off a named shot in `shots/`. Pass two only. The strongest. |
| **verified** | a published source, with the link. The best pass one can do, and most of a good file. |
| **remembered** | model knowledge, unchecked. Never load-bearing alone, and every one is a candidate for the gap list. |
| **inferred** | from something else in the file, which it names. |

*No source found* is a legitimate entry and an honest one.

### The inbox and the shots, for pass two

**The inbox is `reference-inbox/<game>/` at the repository root**, gitignored, read by absolute
path — `E:/hexcom/reference-inbox/<game>/...` — which works from inside a worktree, so it is
never copied and never diverges.

**Curated crops go to `docs/interface/reference/shots/<game>/`**, named for what they show —
`shot-hit-chance-breakdown-expanded.png`, not `screenshot_04.png` — and the claim names the file.
Roughly twenty per game, and prefer a labelled crop to a full screen: smaller, and better
evidence, because it records which part of the picture was being read. Pillow is available and
ImageMagick is not:

```bash
python -c "from PIL import Image; im=Image.open('in.png'); im.crop((x0,y0,x1,y1)).save('out.png')"
```

**A clip is read by pulling named frames out of it, never by watching it.** `ffmpeg` 9.0.1 is
installed; its directory is not on the `PATH` of an already-running shell, so call it in full:

```bash
"$LOCALAPPDATA/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe" -ss 4.5 -i clip.mp4 -frames:v 1 moment.png
```

A frame costs about what a paragraph costs, so pull the named moment and its neighbours rather
than sampling at a fixed rate.

---

## The job — the synthesis: what ten games agree on, and what View builds next

Branch `interface/synthesis`. Take a worktree. A clean session, and **not a transcription job** —
the model note in `master.md` applies to this one and not to the ten that fed it.

**What it is.** Every reference file was forbidden to recommend anything, so that its evidence
stayed separable from its conclusions. This is the session that draws the conclusions, with all
ten open at once. It is the only session that can: a convention is a thing a player arrives
already knowing, so the unit of evidence is *the set agreeing*, and no single file can see that.

**Read the ten files and `conventions.md`.** You do not need to re-read the games.

### The four deliverables

**1. Fold each file's *What transfers* into `conventions.md`.** That doc is where a recommendation
is allowed to live, and it has nine sections. Each of the 53 transfer lines names the section or
brief it bears on, so the routing is done; what is not done is the weighing. Update a section's
recommendation where the evidence moved it, and say in one clause what moved it.

**2. Rule on each of the ten headings: unanimous, split, or empty across the set.** This is the
heart of the job and the reason entry 058's rule needs it. Ten games agreeing is the evidence for
**convention**; ten games differing is the evidence that this game must choose and argue its
case; and a heading the whole set leaves empty is the strongest possible finding — it means this
project is building something with no shipped analogue, and the stakes of getting it right are
higher than anyone assumed. Put this in `conventions.md` as a new section near the top, because
it is the thing a future session will want first.

**3. Amend the queued briefs in `briefs.md`.** Appended, naming the brief, never rewriting it —
same reasoning that keeps the log append-only. Some of these are corrections rather than
refinements and they are the most valuable output of the whole exercise.

**4. Produce *the* capture list**, replacing 89 per-game questions with one ranked cross-file
list. Rank by **what a picture would change**, not by heading and not by game. A question whose
answer would flip a recommendation outranks one that would merely confirm it, and a question
about a game the user owns outranks an equally important one about a game nobody can photograph.
This goes at the foot of `conventions.md` or in a file of its own; it is what the user works from
in a single sitting, and it is the reason the synthesis runs *before* pass two rather than after.

### Five things already visible, so the session does not have to rediscover them

These came out of a skim of the transfer sections. They are starting points, not conclusions, and
each needs checking against the file it came from.

- **A factual error in `conventions.md`.** Its stealth-shelf table says Shadow Tactics and
  Desperados III draw "a meter over the head that fills as you are noticed". The reference file
  found the fill is on the **cone**, not a separate gauge. Fix the wording, and check whether the
  original claim was another game's detection ring conflated in.
- **Brief one names a gesture that does not exist.** It cites "XCOM's hover" as the model for
  *show me the terms*. The XCOM 2 file found a docked breakdown list, not a hover card. Brief one
  is the first thing View builds and its central reference is wrong.
- **Nothing in the set draws a held, not-yet-fired action on the map.** Traps are invisible until
  sprung across the whole stealth shelf, and no tactics game in the set draws a reserve either.
  Brief two and the reserve section are proposing something with **no shipped analogue anywhere**.
  That raises the stakes on the drawing rather than lowering them, and it deserves saying loudly.
- **Two unrelated lineages reached the same two-state answer.** Invisible, Inc.'s
  investigating/alerted pair and Shadow Tactics' `?`/`!` badges converge on *noticed* short of
  *seen*. Under entry 058 that convergence is about as strong as evidence for **convention** gets.
- **Three of the ten have no initiative strip at all**, and a fourth shows turn order only on
  request. The conventions section on turn order was written as though a strip is the genre
  standard; faction-phase-with-free-order is at least as live.

### Settle before writing much

- **Every recommendation carries its evidence grade.** The set has no `observed` tags in it.
  A recommendation resting on a `remembered` claim is **provisional**, says so, and names the
  capture-list entry that would settle it. This is the whole reason the tags exist and the point
  at which they either pay for themselves or do not.
- **Do not re-argue what entry 058 settled.** Convention is the default; a departure argues its
  case. Where the set is unanimous and this game wants to differ, the burden is on this game.
- **The transfer lines are other sessions' readings, not ground truth.** Where one says something
  surprising, open the file and check the heading it came from before building on it.

### What to do with the debt the ten files are carrying

`../decisions.md` was closed to the ten parallel jobs, because ten simultaneous appends to an
append-only log is the one collision the scheme has no cheap answer for. **This session is the
named payer.** Sweep the ten files for findings addressed to another territory, and file them as
entries — one commit, correctly numbered. There is at least one, in `phoenix-point.md`.

**Out of scope.** Building anything. Editing a reference file's evidence, which is immutable the
way the log is; a correction goes in the synthesis, naming the file and the heading. The strategy
layer's interface. Onboarding, which is queued below and is a separate job deliberately.

**How to know it worked.** Three tests. A View session can be pointed at any brief in `briefs.md`
and find its amendments beside it. The user can sit down with the capture list, play for an hour,
and fill the gaps that matter without choosing between 89 questions. And somebody reading
`conventions.md` can see, for each of the ten headings, whether this game is following the genre
or leaving it — and on what evidence.

---

## Then — pass two, the captures

Not yet a brief, and deliberately: it is written against the synthesis's ranked capture list,
which does not exist yet. What is fixed is the mechanism, which is set up already and is in *The
inbox and the shots* above. The work is a fill rather than a redesign: the same ten files, the
same ten headings, `remembered` and `inferred` claims upgraded to **observed** where a shot
settles them, and the gap entries struck as they are answered. One game per session, and only the
five the user owns can be done from play.

---
## After that — the first five minutes, and what has to be taught

Last of the queue, and deliberately: onboarding decides what a player must be told before turn
one, and half of that answer is what the genre's interface already teaches without telling
anybody — which is exactly what the synthesis is about to write down. Branch
`interface/onboarding` when it comes up. The ten reference files give it something the earlier
version of this brief did not have: Into the Breach's total disclosure is now documented in
detail rather than cited, and it is the argument this job has to answer rather than route
around.

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
