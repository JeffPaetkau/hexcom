# Interface design — what the genre does, and the briefs that follow from it

Research and brief-writing for the player's interface. This territory plays other games, reads,
and writes; it draws nothing and touches no code. Its output is a standard the View territory
builds to, and a queue of View briefs written to that standard.

Read [../map.md](../map.md) first.

## Owns

```
docs/interface/**      the conventions doc, the per-game reference files, the ranked capture
                       list, and the queue of briefs
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

**Two passes. The first has run, the synthesis between them has run, and the second is the job
below.**

| | |
|---|---|
| **Pass one — documentary** | Published material only. **No file carries a single `observed` tag**, which is correct rather than a shortfall. Each ends with a numbered list of what a picture would settle, and those 89 questions are the pass's second deliverable. |
| **The synthesis** | Reads all ten at once and draws the conclusions each file was forbidden to draw. Its output is the *What ten games said* section of `conventions.md`, an amendment block per brief in `briefs.md`, and the ranked list in `captures.md` that replaces the 89. Entry 077 has what it found. |
| **Pass two — observed** | The user captures against the ranked list, drops the results in the inbox, and the gaps are filled in place. |

**The ranking had to wait for the synthesis and could not have been done earlier.** A question's
importance is only visible once all ten files are read together: what outranks what is *would a
picture change a recommendation or only confirm it*, and no single file can see which of its own
questions does that.

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

## The job — pass two: the pictures, against a list that is already ranked

Branch `interface/captures`. Take a worktree. **One session, on Opus, for all eleven.**

**The captures are in, and three things about them override what follows.** Entry 088 has why.

- **Eleven of the twelve above the line, and C8 is not coming.** The user's XCOM 2 is the GOG
  build, which cannot load Workshop mods, so Gotcha Again's tile icons cannot be photographed.
  Strike C8 as *not capturable from the user's copy* rather than answered. What it would have
  settled is the glyph vocabulary for brief four's tile warning, which is built and marked
  provisional, and stays that way. Do not substitute published screenshots for it and tag them
  observed.
- **One session, not one per game.** The rule below was written for twenty to forty shots a game.
  The inbox holds sixteen files across five games, one to four each, and five parallel sessions
  would each have to edit `conventions.md` and `captures.md` — the shared-file collision entry 072
  barred. Read all five folders in one context.
- **Four of the sixteen are clips** — `invisible-inc/C7.mp4`, `phantom-brigade/C9.mp4`,
  `warhounds/C4a.mp4`, and whatever the XCOM 2 notes point at. Pull the frames each entry in
  `captures.md` names with `ffmpeg`, by the full path in *The inbox and the shots*, and never
  sample a clip at a fixed rate. Read `xcom2/C1-notes.md` first: it is the user's own account of
  what they saw, and it outranks any reading of the frames that disagrees with it.

**Why Opus and not Sonnet, which the documentary pass ran on.** That pass was forbidden to
recommend. This one is permitted to change a recommendation, and the first it changes is the
gesture brief one is built around — the next thing View builds. A weak call here costs more in the
View session that follows than the model saved.

**What it is.** The ten reference files were written from published material and carry no
`observed` tag. [../interface/captures.md](../interface/captures.md) ranks the 89 gap questions
into one list of twenty, twelve above a cut line, ranked by what a picture would *change* rather
than confirm. This job turns the answers into evidence in place: `remembered` and `inferred`
claims become **observed** where a shot settles them, gap entries are struck as they are
answered, and the recommendations in `conventions.md` that are marked **provisional** against a
capture entry either lose the mark or get corrected.

**Eleven of the twelve above the line are about a game the user can play** — XCOM 2, Invisible,
Inc., Warhounds, Phantom Brigade, Future War Tactics. The other five games probably cannot be
photographed at all, which is why their questions sit below the line and are phrased as *what
would settle this*.

**The seam.** `docs/interface/reference/<game>.md` for the claims and the gap lists,
`docs/interface/reference/shots/<game>/` for the crops, `docs/interface/captures.md` for the
list, and `conventions.md` for the recommendations that cited a capture entry by number. The
inbox and the crop mechanism are in *The inbox and the shots* above, and they are set up already.

**Settle before writing much.**

- **A reference file's evidence is immutable the way the log is, with exactly one exception: a
  claim's tag.** Upgrading `remembered` to **observed** and naming the shot is the whole job.
  Rewriting a heading's prose because a picture suggested a better sentence is not, and neither is
  adding a finding a shot did not produce.
- **One session for this round, overriding the old one-game rule** — see the head of this job.
- **A shot that contradicts a claim is the best outcome and needs saying loudly.** Correct the
  claim in place, tag it **observed**, and append an entry to `../decisions.md` if the correction
  reaches a brief or a recommendation. Two such corrections came out of the documentary pass and
  both were worth more than the pass's agreements.
- **Roughly twenty crops per game, named for what they show**, and prefer a labelled crop to a
  full screen: it is smaller and it is better evidence, because it records which part of the
  picture was being read.

**Settling brief one is in scope, narrowly.** Two provisional marks stand between brief one and
View: C1, on the gesture for *show me the terms*, in both `conventions.md` and *Amending One*; and
C10, on whether the reserve's cliff belongs on the move range. Where a capture settles one, drop
or correct the mark in `conventions.md` and **append** a short *Settling One* block after *Amending
One* in `briefs.md` saying what the picture showed and what the brief now builds. Appended, never
rewritten, on the same reasoning as the amendments. The mark on C15 is below the line and stays.

**Out of scope.** Recommending anything a capture did not settle. Rewriting a brief's text, which
is the amendment block's shape.
Capturing a game nobody owns. Researching a question a browser settles — the mod changelogs,
subscriber counts and patch notes that captures.md deliberately excluded stay in their own files'
gap lists.

**How to know it worked.** Brief one can be promoted to View with no provisional mark left on its
gesture or its move range. A recommendation in `conventions.md` that said **provisional** now
either says nothing or says something different, and names the shot. A gap entry that was answered
is struck rather than deleted. And somebody reading one reference file can tell, per claim,
whether it came from a page or from a picture.

---
## Then — the first five minutes, and what has to be taught

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

## What landed on `interface/synthesis`

Entry 077 has the reasoning and entry 078 the findings routed to Core. What exists:

- **`conventions.md` has a new section near the top, *What ten games said*** — each of the ten
  headings ruled unanimous, split or empty, with the count behind the ruling. It is the thing to
  read first, and it opens with the rule for reading the counts: *the set agrees* means the games
  that have the mechanic agree, not that ten of ten said the same thing.
- **Six of the nine sections moved**, each saying in a clause what moved it, and the two factual
  errors are corrected in place.
- **`briefs.md` carries an amendment block**, one entry per brief, appended rather than folded in
  so that a brief a View session has already read does not change under it.
- **`captures.md`** — twenty entries, twelve above a cut line, ranked by what a picture would
  change. It is what the user works from in one sitting.

Five things worth not re-deriving:

- **The set obeys one law about undo and it explains entry 058 rather than merely agreeing with
  it.** A game lets a player take something back exactly as far as it told them the truth. Ten for
  ten. The half that matters here is the converse: this game owes the figures before the click
  because it will not give the click back.
- **Four things the briefs said about the genre were wrong**, and three of the four are in briefs
  View builds first. They are listed in entry 077 and amended in `briefs.md`; the shortest version
  is that XCOM has no hover, nobody has a strip, two games do draw a held arc, and `Tab` is one
  game's habit.
- **The largest recommendation change came from reading two headings together** — the genre draws
  the reserve's cliff on the ground, as the move-range band, and three of the four games that band
  it cut the band exactly at *can I still act when I arrive*. Neither heading alone says that.
- **Reading the denominator correctly is most of the method.** Two of ten looks thin for the
  *noticed* state and is two of two among games that have one; ten of ten alternate-side games
  having no strip says nothing about a strip, because none of them interleaves.
- **A skim of the transfer sections got two of its five starting points wrong**, in both cases by
  generalising one shelf's finding to the whole set. The brief said to check each against the file
  it came from, and that instruction earned its place twice.

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
