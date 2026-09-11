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

## The reference set — the games, the shots, and the rules for both

`conventions.md` is the recommendation layer. Underneath it sits one file per game in
`docs/interface/reference/`, at the grain a View brief needs: where the figure sits, what gesture
shows its terms, what a hover does, what cancel undoes. Ten fixed headings, carried even where
the answer is *this game has no such thing*. **The template is written out in full in the job
below and is not any file's to invent**, precisely so that the five files can be written at the
same time without waiting on each other; a set whose files do not line up cannot be read across,
and that is the only thing about running them together that was ever at risk.

**One game per session, and the five may run at once.** The evidence is images, and images do not
compress into a summary the way prose does — a session that reads forty screenshots has spent
most of its context on the reading, which is the right price for the thing being bought and the
wrong price to pay twice in one context. That is an argument about what one session holds, not
about how many run, so parallel is free and the rules that keep five out of each other's way are
at the foot of the job.

### The games, in the order they earn a file

**Tier A — the user owns these and can capture them**, so they get the deep treatment, the
screenshots, and a file each.

| | |
|---|---|
| **XCOM 2** + War of the Chosen, and its in-mission mods | the grammar every player arrives already knowing, plus a download-counted record of what it failed to tell them |
| **Invisible, Inc.** | the closest relative in existence — cones with peripheral tiles distinguished, a *noticed* state short of seen, and an alarm ladder whose rungs are hidden on purpose |
| **Warhounds** | the only shipped game found with a reserve like ours, and cone placement entered directly rather than through a nested menu |
| **Phantom Brigade** | the only shipped interface built around *what the enemy is about to do*, drawn on a timeline the player scrubs. Nothing else on either shelf draws prediction as a first-class object |
| **Future War Tactics** | colour-coded zones for movement and attack, and a recent small-team answer to the whole HUD at once |

**Tier B — not owned**, so published material and video only, and each earns its file by answering
a question Tier A cannot.

| | |
|---|---|
| **Mutant Year Zero** | detection radii drawn only in the mode that needs them, and shrunk by an action the player takes |
| **Shadow Tactics / Desperados III** | the best cone drawing shipped, and a planning mode that is a UI answer to a timing problem |
| **Phoenix Point** | per-body-part targeting, which is the nearest exemplar anywhere for contract 6's six faces, plus a ballistic preview |
| **Into the Breach** | perfect information and enemy intent — the answer the onboarding brief below has to argue with rather than around |
| **Tactical Breach Wizards** | the most recent word on making a tactical turn legible: undo, and consequence shown before commitment |

**Tier C — the grammar.** One line each in whichever file has cause to cite them, and a file of
their own only when a brief needs one: Jagged Alliance 3 (interrupts, tooltips, free camera),
Baldur's Gate 3 (reaction prompts, and the most polished readout set shipped at any budget),
Xenonauts 2 (time units, a second model of what a soldier spends), Door Kickers 2 (a planning
phase and cones in real time), Battle Brothers (the initiative strip), Classified: France '44 and
Commandos: Origins (recent stealth).

**A file is written because something needs it.** The set is not a survey to be completed. Tier A
is five files, written once and then owned by their game; Tier B is on demand, and the question
that summons one is named in the brief that asks. A reference file nobody is building from is the
most expensive kind of prose this project can produce — and the cost that matters is not the
tokens, it is that the next session reads it.

### The shots, and why they are the point

A report assembled from words on the web says what a game has. Only a screenshot says where it
is, how big it is, what is next to it, and what the game chose not to draw. The second kind is
what a View session needs and the first kind it already has.

**The inbox is `reference-inbox/<game>/` at the repository root**, gitignored. The user drops raw
captures there. Any session reads them by absolute path — `E:/hexcom/reference-inbox/<game>/...`
— which works from inside a worktree, so the inbox is never copied and never diverges.

**Ask for the shots in one list, before reading any of them.** The first thing a per-game job
produces is a **shot list**: the exact screens needed, named by what has to be visible in each —
*a soldier selected with the ability bar and a target under the cursor*, not *a combat screen*.
A capture session is the user's time, and a job that asks in dribs spends it four times over.

**What a still cannot show**, so the list says when it needs something else: a hover state unless
the cursor and its tooltip are in the frame, any transition, any timing, anything audible, and
what a key does. Ask for a short clip only for those, and say which frames matter.

**A clip is read by pulling frames out of it, never by watching it.** `ffmpeg` 9.0.1 is installed
on this machine. Its directory is not on the `PATH` of an already-running shell, so call it by
its full path:

```bash
"$LOCALAPPDATA/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe" -ss 4.5 -i clip.mp4 -frames:v 1 moment.png
```

Pull the named moment and its neighbours, not a whole sequence at a fixed rate: a frame costs
about what a paragraph of reading costs, and a clip sampled every half-second is most of a
context window spent watching a menu open.

**The committed evidence is curated, not the inbox.** A shot that carries a claim goes to
`docs/interface/reference/shots/<game>/`, named for what it shows —
`shot-hit-chance-breakdown-expanded.png`, not `screenshot_04.png` — and the claim in the file
names the file. Roughly twenty per game, and **prefer a labelled crop to a full screen**: the
crop is smaller, and it is also better evidence, because it says which part of the picture was
being read. Pillow is available and ImageMagick is not:

```bash
python -c "from PIL import Image; im=Image.open('in.png'); im.crop((x0,y0,x1,y1)).save('out.png')"
```

### The four tags

Every non-obvious claim in a reference file carries one, and the first is the one this exercise
exists to buy:

| | |
|---|---|
| **observed** | read off a named shot in `shots/`. The strongest, and the reason for the whole protocol. |
| **verified** | a published source, with the link. |
| **remembered** | model knowledge, unchecked. Legitimate, and never load-bearing on its own. |
| **inferred** | from something else in the file, which it names. |

*No source found* is a legitimate entry and an honest one. A fine-detail file a View session
cannot audit is worse than no file, because it will be built from regardless.

---

## The job — one game, observed in detail. You will be told which.

Branch `interface/reference-<game>`, one per game. Take a worktree; the rule has no exception for
prose. **The five Tier A jobs are written to run at the same time**, so the rules that keep them
from colliding are part of the job and not housekeeping — they are the last section here.

**What it is.** `conventions.md` answers nine questions at the altitude of *what the genre does*,
and the user has called that a good start and asked for the grain underneath it. View builds six
briefs against that standard. A brief is a sufficient prompt only if it can say where the figure
sits, what gesture reveals its terms, what a hover does and what cancel undoes. That evidence
does not exist yet, and it cannot be had from published prose — which is why the shots are the
job and not an illustration of it. Read *The reference set* above first: the inbox, the shot
list, the curated `shots/` directory and the four tags.

**Where the output goes.** `docs/interface/reference/<game>.md`, and the crops that carry its
claims in `docs/interface/reference/shots/<game>/`. Nothing else. `conventions.md` is not
rewritten — the standard stands and this is the evidence underneath it.

### The template, which is fixed so that nobody has to invent it

Ten headings, in this order, in every file, carried **even where the answer is *this game has no
such thing*** — an empty heading is a finding about the game and the most valuable rows in the
set will be the empty ones. Under each, the observations; beside each observation, its tag.

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
on and what it is only an instance of; the tag key; the shot list as it was actually captured;
and a *nothing found* list, which is the headings that came back empty and why.

**Close each file with a short *what transfers* section** — three to six lines, each naming the
brief in `briefs.md` or the section of `conventions.md` it bears on. Do not write the
recommendation itself: this file is evidence, the recommendation is the pass that has all five
files in front of it.

### Per game, what to expect before you look

- **XCOM 2** (with War of the Chosen) is the grammar everyone arrives knowing, and its mods are
  the better half of the job: a decade-long, download-counted record of what the genre's
  best-selling interface failed to tell its players. A mod with a hundred thousand subscribers is
  a gap that was worth somebody's weekend, and the count is an ordinal reading of how badly it
  was missed. In-mission only — skip anything touching the Avenger, the geoscape or character
  creation. Heading 5 will be thin and that is the finding: this game draws a unit the moment it
  is seen and has no contact file at all.
- **Invisible, Inc.** is the closest relative in existence and the only Tier A game whose
  headings 4 and 5 are the point rather than an afterthought. Cones with peripheral tiles
  distinguished, a *noticed* state short of seen, and an alarm ladder whose rungs are hidden on
  purpose — which is contract 3's coarse rung, shipped by somebody else. Expect this file to be
  the one brief two is built from.
- **Warhounds** is the only shipped game found with a reserve like ours (entry 067), so heading 7
  is its reason for being here. Also worth heading 8: cone placement entered directly rather than
  through a nested menu, with fast adjust and cancel.
- **Phantom Brigade** is the only shipped interface that draws *what is about to happen* as a
  first-class object on a timeline the player scrubs. Heading 6 is where that goes and it will
  not fit the shape the other four use — say so rather than forcing it. Its planning model is not
  ours and the file should not pretend otherwise; what transfers is how prediction is *drawn*.
- **Future War Tactics** is the thin one by `conventions.md`'s own account: colour-coded zones
  for movement and attack, where this game uses graded tints. A short honest file is the right
  outcome and padding it is the wrong one.

### Running five at once, and the three rules that make it safe

1. **Write your own two paths and nothing else** — `reference/<game>.md` and
   `reference/shots/<game>/`. Not `conventions.md`, not `briefs.md`, not another game's file.
   Four sessions appending to one queue is four conflicts in the file that can least afford
   ambiguity, and the *what transfers* section at the foot of your own file carries everything
   you would have wanted to put there. One later pass, with all five files in front of it, folds
   them in.
2. **`../decisions.md` is the exception, as always** — append if you find something a neighbour
   owes an answer on. A merge conflict there is expected and the resolution is to keep both
   hunks and renumber.
3. **Ask for your shots in one list and read the inbox, never another game's.**
   `E:/hexcom/reference-inbox/<game>/`, by absolute path.

**Out of scope.** Building anything. The strategy layer's interface. Rewriting `conventions.md`.
Recommending what this game should do — that is the synthesis pass, and a file that argues is a
file whose evidence can no longer be separated from its conclusions.

**How to know it worked.** A View session can answer, from your file alone and without opening a
browser or a game: where this game puts the figure it is about to move, what is written on it,
what gesture shows the arithmetic behind it, and what the players added because that was not
enough. And every claim of that kind names a shot.

---

## Next in this territory — the synthesis, which is what the five files are for

Queued behind the reference jobs and **required by them**: each of those files is forbidden to
recommend anything, so that its evidence can be separated from its conclusions. Somebody has to
draw the conclusions, and that somebody has all five files open at once. Branch
`interface/synthesis`.

It does three things and no fourth. It folds each file's *what transfers* footer into the nine
sections of `conventions.md`, which is where a recommendation is allowed to live. It appends
amendments to the queued briefs in `briefs.md` where an observation changes one — appended and
naming the brief, never rewriting it. And it says, once, **which of the ten headings the set
turned out to be unanimous on and which it split on**: a convention is a thing a player arrives
already knowing, so five games agreeing is the evidence for *convention* and five games differing
is the evidence that this game must choose and argue, per entry 058.

Expect heading 5 to be the interesting one. Four of the five Tier A games have little to say
about how a remembered or suspected enemy is drawn, and the fifth has almost all of it.

**This job is not a transcription job**, and the model note in `master.md` applies to it and not
to the five that feed it.

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
