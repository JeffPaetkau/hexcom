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

## The reference set — ten games, two passes, and one fixed shape

`conventions.md` is the recommendation layer. Underneath it sits one file per game in
`docs/interface/reference/`, at the grain a View brief needs: where the figure sits, what gesture
shows its terms, what a hover does, what cancel undoes.

**There are two passes and you are in the first one.**

| | |
|---|---|
| **Pass one — documentary** | Published material only. No screenshots exist yet. Every file ends with a numbered list of **what a picture would settle**, and that list is the pass's second deliverable, not an apology for the first. |
| **Pass two — observed** | The user captures against those lists, drops them in the inbox, and the gaps are filled in place. Only then does a file carry the **observed** tag at all. |

**Pass one has no `observed` tags in it and that is correct, not a shortfall.** What it is buying
is the question list. A survey written from published material knows the shape of each game and
is unreliable on exactly the details that matter here — where a thing sits, how big it is, what
is beside it — so its job is to find out precisely which details those are, per heading, and name
the picture that would settle each. That is cheaper to do from prose than from photographs, and
it means the capture session is aimed rather than speculative.

**The trap, and the one rule that avoids it.** A documentary pass does not know what it does not
know: it will write a confident sentence about a HUD element and never think to flag it. So the
gap list is **not** a record of where the session happened to feel unsure. Every one of the ten
headings ends with its own *what a picture would settle* line, asked and answered deliberately,
even when the heading reads as complete. A heading with nothing to ask is a claim that the game's
published material fully determines it, and that claim is worth making explicitly.

### The ten jobs

**You were given a number. It is here.** Each job is one game, one file, one branch, one
worktree, and they are written to run all at once. The prompt *read this file and do job N* is
meant to be sufficient; if it is not, that is a defect in this file and worth an entry.

| # | Game | Branch | Why it is in the set |
|---|---|---|---|
| 1 | **XCOM 2**, with War of the Chosen and its in-mission mods | `interface/reference-xcom2` | the grammar every player arrives already knowing, plus a download-counted record of what it failed to tell them |
| 2 | **Invisible, Inc.** | `interface/reference-invisible-inc` | the closest relative in existence — cones with peripheral tiles distinguished, a *noticed* state short of seen, and an alarm ladder whose rungs are hidden on purpose |
| 3 | **Warhounds** | `interface/reference-warhounds` | the only shipped game found with a reserve like ours, and cone placement entered directly rather than through a nested menu |
| 4 | **Phantom Brigade** | `interface/reference-phantom-brigade` | the only shipped interface that draws *what is about to happen* as a first-class object, on a timeline the player scrubs |
| 5 | **Future War Tactics** | `interface/reference-future-war-tactics` | colour-coded zones for movement and attack, and a recent small-team answer to the whole HUD at once |
| 6 | **Mutant Year Zero** | `interface/reference-mutant-year-zero` | detection radii drawn only in the mode that needs them, and shrunk by an action the player takes |
| 7 | **Shadow Tactics and Desperados III** | `interface/reference-shadow-tactics` | the best cone drawing shipped, and a planning mode that is a UI answer to a timing problem. One file for the line, not one each |
| 8 | **Phoenix Point** | `interface/reference-phoenix-point` | per-body-part targeting, the nearest exemplar anywhere for contract 6's six faces, plus a ballistic preview |
| 9 | **Into the Breach** | `interface/reference-into-the-breach` | perfect information and enemy intent — the answer the onboarding brief has to argue with rather than around |
| 10 | **Tactical Breach Wizards** | `interface/reference-tactical-breach-wizards` | the most recent word on making a tactical turn legible: undo, and consequence shown before commitment |

**Jobs 1 to 5 can have their gaps filled; jobs 6 to 10 probably cannot.** The user owns the first
five and can photograph them. For the rest, pass two is published video at best, so a gap list
there should say *what would settle this* rather than *please capture this* — and a question that
can never be answered is still worth writing down, because it tells the synthesis how much weight
that heading can bear.

**What to expect before you look, per game.** Job 1's mods are the better half of it: a
decade-long, download-counted record of what the genre's best-selling interface failed to tell
its players, and the subscriber count is an ordinal reading of how badly each gap was missed. In-
mission only, so skip the Avenger, the geoscape and character creation. Job 1's heading 5 will be
thin, because the game draws a unit the moment it is seen and has no contact file at all — that
is the finding, not a hole. Job 2 is the opposite and is the file brief two will be built from.
**Job 3 will be the thinnest in the set and its gap list the longest**: Warhounds is new enough
that published material barely covers its HUD, and an honest short file with twenty good
questions is exactly the right outcome there. Job 4 will not fit heading 6's shape and should say
so rather than forcing it; its planning model is not ours and what transfers is how prediction is
*drawn*. Job 5 is thin by `conventions.md`'s own account, and padding it is the wrong instinct.
Job 7 is real-time, so its input conventions do not transfer and its drawing does.

**Tier C, for citation only and not a job:** Jagged Alliance 3 (interrupts, tooltips, free
camera), Baldur's Gate 3 (reaction prompts, and the most polished readout set shipped at any
budget), Xenonauts 2 (time units, a second model of what a soldier spends), Door Kickers 2 (a
planning phase and cones in real time), Battle Brothers (the initiative strip), Classified:
France '44 and Commandos: Origins (recent stealth). A file of their own only if a later brief
names the question it wants answered.

### The four tags

Every non-obvious claim carries one. In pass one only three of them are available:

| | |
|---|---|
| **observed** | read off a named shot in `shots/`. Pass two only. The strongest, and what the exercise is ultimately for. |
| **verified** | a published source, with the link. The best pass one can do, and most of a good file. |
| **remembered** | model knowledge, unchecked. Legitimate, never load-bearing alone, and every one of these is a candidate for the gap list. |
| **inferred** | from something else in the file, which it names. |

*No source found* is a legitimate entry and an honest one. A file a View session cannot audit is
worse than no file, because it will be built from regardless.

### The inbox and the shots, for pass two

The mechanism is set up already so that pass two is a fill rather than a redesign.

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

A frame costs about what a paragraph of reading costs, so pull the named moment and its
neighbours rather than sampling a clip at a fixed rate.

---

## The job — one game, documented in detail, and the questions a picture would settle

Branch as the table above gives it. **Take a worktree; the rule has no exception for prose.**

**What it is.** `conventions.md` answers nine questions at the altitude of *what the genre does*.
View builds six briefs against that standard, and a brief is a sufficient prompt only if it can
say where the figure sits, what gesture reveals its terms, what a hover does and what cancel
undoes. This job builds the evidence layer underneath, for one game, and names what it could not
settle without a picture.

**Where the output goes.** `docs/interface/reference/<game>.md`. **Nothing else.** Not
`conventions.md`, not `briefs.md`, not another game's file, and in this pass not
`../decisions.md` either — see the rules at the foot.

### The template, which is fixed so that nobody has to invent it

Ten headings, in this order, in every file, carried **even where the answer is *this game has no
such thing*** — an empty heading is a finding about the game, and some of the most valuable rows
in the set will be the empty ones. Under each: the observations, each with its tag, and then that
heading's *what a picture would settle* line.

1. **Screen furniture** — every persistent element of the tactical HUD: where on the screen it
   sits, what it shows, when it appears and when it goes away.
2. **The soldier** — how actions are shown and spent, the ability bar, the hotkeys, what a hover
   over an ability reveals, what cancel does and how far back it goes.
3. **The target** — the shot readout line by line: every term in the breakdown, whether the terms
   are shown by default or behind a gesture, how targets are switched and in what order.
4. **The tile** — movement range and its bands, the path preview, cover indicators, any
   concealment or detection ring, and which of those are drawn on hover versus after a commitment.
5. **The enemy** — how a suspected, remembered or unseen enemy is drawn if at all; the alert
   states and their icons; the moment the game admits a contact.
6. **Turn order and time** — whether there is a strip, what an interruption looks like, and what
   the player is shown while it is not their go.
7. **Reactions** — how a held action is declared, whether its arc or zone is drawn, and what the
   trigger looks like at the moment it fires.
8. **Camera and input** — default binds, drag gestures, rotation steps and their speed, the
   storey or level control, cycle-target keys.
9. **Confirmation and refusal** — what takes a second click, what warns, what the game lets a
   player do irreversibly in silence, and what it simply will not let them do.
10. **What the game hides, and what its players added** — mods, community fixes, options buried
    in a menu. The heading the other nine exist to reach.

**Each file opens with the same four things**: one paragraph on what this game is the authority
on and what it is only an instance of; the tag key; the sources, listed; and a *nothing found*
list, which is the headings that came back empty and why.

**Each file closes with two sections and no third.**

- ***What transfers*** — three to six lines, each naming the brief in `briefs.md` or the section
  of `conventions.md` it bears on. Do **not** write the recommendation itself. This file is
  evidence; the recommendation is the synthesis pass, which will have all ten files in front of
  it. A file that argues is a file whose evidence can no longer be separated from its conclusions.
- ***The gap list*** — numbered, and the second deliverable of this pass. Each entry: which
  heading, what is unsettled, **the exact picture or clip that would settle it** named by what
  must be visible in the frame (*a soldier selected with the ability bar and a target under the
  cursor*, not *a combat screen*), and what the answer would change. Order it by what it would
  change, not by heading. Say when a still cannot do it — a hover state without the cursor and
  tooltip in frame, a transition, a timing, anything audible — and then name the moment in a clip.

### Running ten at once, and the rules that make it safe

1. **Write your own one path and nothing else.** `docs/interface/reference/<game>.md`. Ten
   sessions appending to one shared queue is ten conflicts in the files that can least afford
   ambiguity, and your *what transfers* and gap-list sections carry everything you would have
   wanted to put there.
2. **Not `../decisions.md` either, in this pass, and that is a deliberate exception to rule 3 of
   the map.** The rule exists so a finding about somebody else's territory gets written down
   instead of acted on, and that intent is preserved: put it in *What transfers*, clearly marked
   as a proposal for the territory it concerns. One later session appends the entries. Ten
   parallel appends to an append-only log is the one collision the scheme has no cheap answer to.
3. **Read your own game only.** Do not read another job's file, and do not wait on one.
4. **Nothing here is a status board.** Do not write what is in flight, and do not name a branch
   that is not merged.

**Out of scope.** Building anything. The strategy layer's interface. Rewriting `conventions.md`.
Recommending what this game should do.

**How to know it worked.** Two tests, and the second is the one this pass is really for. A View
session can answer from your file alone: where this game puts the figure it is about to move,
what is written on it, what gesture shows the arithmetic behind it, and what its players added
because that was not enough. And the user can sit down with your gap list, play the game once
with a capture key, and come back with every picture the file needs — without having to work out
what to photograph.

---

## Next in this territory — the synthesis, which is what the ten files are for

**A sketch, not a brief.** It is written properly once the ten files and their filled gaps exist,
because a brief for reading ten documents that do not exist yet would be guessing at their shape.
What is fixed now is that the job is **required**, and why: every reference file is forbidden to
recommend anything so that its evidence stays separable from its conclusions, which means
somebody has to draw the conclusions with all ten open at once. Branch `interface/synthesis`, a
clean session, and not a transcription job — the model note in `master.md` applies to this one
and not to the ten that feed it.

The shape it will have. It folds each file's *what transfers* footer into the nine sections of
`conventions.md`, which is where a recommendation is allowed to live. It appends amendments to
the queued briefs in `briefs.md` where an observation changes one — appended and naming the
brief, never rewriting it. It appends to `../decisions.md` the findings the ten files were told
to hold rather than file, which is the whole of that debt paid by one session in one commit. And
it says, once, **which of the ten headings the set was unanimous on and which it split on**: a
convention is a thing a player arrives already knowing, so ten games agreeing is the evidence for
*convention* under entry 058, and ten games differing is the evidence that this game must choose
and argue its case.

Expect heading 5 to be the interesting one, and expect it to split hard. Most of the set draws
the enemy the moment it is seen and has nothing to say about a remembered contact; two of the ten
have almost all of it.

---

## Then — the first five minutes, and what has to be taught

Queued behind the reference jobs and the synthesis, and deliberately: onboarding decides what a
player must be told before turn one, and half of that answer is what the genre's interface
already teaches without telling anybody. Branch `interface/onboarding` when it comes up.

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
