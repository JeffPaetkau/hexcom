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

**Two passes and a synthesis between them, and all three have run.** Pass two's findings are entry
089 and *What landed on `interface/captures`* below.

| | |
|---|---|
| **Pass one — documentary** | Published material only. **No file carries a single `observed` tag**, which is correct rather than a shortfall. Each ends with a numbered list of what a picture would settle, and those 89 questions are the pass's second deliverable. |
| **The synthesis** | Reads all ten at once and draws the conclusions each file was forbidden to draw. Its output is the *What ten games said* section of `conventions.md`, an amendment block per brief in `briefs.md`, and the ranked list in `captures.md` that replaces the 89. Entry 077 has what it found. |
| **Pass two — observed** | The user captures against the ranked list, drops the results in the inbox, and the gaps are filled in place. Five of the ten files now carry `observed` tags, each naming a crop in `shots/<game>/`. |

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

## The job — how a mission ends, and what the player is told

Branch `interface/mission-end`. Missions stop now, and nothing in this territory says what the genre
shows when one does.

**What exists.** A battle can end in more ways than everybody down on one side (entry 041). A
mission stops at its round limit, and it can stop on the alarm (entry 082). A withdrawal is judged
on the highest rung any enemy held on each soldier at the moment that soldier left, sampled then,
because asking afterwards reads Unaware for everybody. A reconnaissance is judged on a look taken
and on getting off the ground (entry 061). All of it reaches the player as one status line —
`mission: <task> <VERDICT>` — plus an *off the field* line per soldier, in `BattleHud.MissionLines`.
Its remarks call the sampled rung *the load-bearing part*.

**What it is.** The moment a player most needs to know which rule decided things is the moment the
interface says least. And a player replaying the waystation who fails and cannot say why will replay
it the same way.

**Where to look.** The ten files' headings 1, 9 and 10 for what each game draws at the end of a
mission. Then published screenshots of each game's end-of-mission or debrief screen, read the way
the options job read its settings: PCGamingWiki's page API for the wikitext and its image list, and
the images themselves opened. Patch notes and forum threads for what players said the screen left
out.

**The questions.**

- **What the genre puts on the end-of-mission screen**, and in what order: outcome, objectives,
  casualties, what was gained, statistics.
- **Whether a failure says which rule ended it.** Here there are several — out of time, the alarm,
  a soldier registered and kept, everybody down — and the objective already knows which one.
  Phoenix Point's missed popup is the failure to avoid.
- **What may be revealed of the enemy once it is over.** Contract 3 withholds his positions and his
  knowledge during the battle. Does the genre reveal them after, and does a reveal here make
  reconnaissance free on a map a player replays? That is the no-undo law's question again, one step
  later, and it is the heart of this job.
- **The verdict's words.** Entry 082 separates abandoning a mission from failing it, and the enum is
  not the words, the same lesson entry 098 learned for the rungs.
- **What a player can do next** when there are no saves and no mission select (milestone 3): the
  genre's *retry*, and whether a retry keeps the seed.

**Where the output goes.** A new section in `docs/interface/conventions.md`, *When it ends*, in the
usual shape, and one brief appended to `docs/interface/briefs.md`.

**Also re-prime the queue**, as the last two jobs did.

**One question routed by Master from entry 101, not this job's but small — answer it in passing.**
*Whether a screen's light cover should read as cover at all on the shield*, when the rules also make
the man behind it invisible: a player who sees *light* may conclude *seen*. The shield draws the rules'
answer; the question is what the word and the glyph should promise.

**Out of scope.** Building anything. Rules: a verdict a player needs that the objective cannot give
is a proposal for Core in `../decisions.md`. The campaign's debrief across missions, which is the
strategy layer's and has no rules yet. Saves.

**How to know it worked.** A View session pointed at the brief needs nothing else. A player who has
just failed the waystation can say, from the screen alone, which rule ended it and what they would
do differently.

---

## What landed on `interface/options`

Entry 102 has the findings. What exists:

- **`conventions.md` has a new section, *What a player may change***, placed before the debug
  overlays section, which is its counterpart: what an option may not be. It has a settings table
  for the ten games with sources, six findings with their denominators, the palette measured under
  colour-blindness, the line the asymmetry draws, and the recommendation.
- **`briefs.md` is re-primed and has brief ten, `view/options`.** Two is out, its text at
  `0bde77d:docs/interface/briefs.md`, and the landed table has a column saying where each brief's
  text lives.
- **`../decisions.md` entry 102**, with one drawing finding for View: the cover grades need a second
  channel.

Four things worth not re-deriving:

- **PCGamingWiki is the source for settings, and it has to be read through its API.** Its pages
  refuse a plain fetch. `api.php?action=parse&prop=wikitext` returns the input and video tables,
  `prop=imageinfo` resolves the settings screenshots, and the images can be opened. Five screenshots
  of binding and accessibility screens were read that way, and they corrected two claims in the
  first draft.
- **The screenshots overturned the obvious conflict rule.** *One key, one action per context* was
  the first draft. Phantom Brigade binds `1` twice in one list, to actions never live together. The
  rule is *no two live at once*, and it is this game's bar and window exactly.
- **The palette was measured, not argued.** A colour-blindness simulation over `SandboxPalette`'s
  own hex values found the one reading that carries a rule in hue alone and fails: the cover grades.
  It also showed that entry 098's glyph-first rung already survives any palette. The method is named
  in the section, so it can be re-run whenever a colour changes.
- **Every recommendation stays inside 094's ruling.** One pace scales every wait, so no dwell becomes
  a dial. One multiplier scales the HUD, so no layout constant becomes a setting. A palette mode is a
  mode, not colours a player picks. The narrow scope the user settled survived the evidence intact.

---

## What landed on `interface/onboarding`

The queue's last job. Entry 099 has the findings. What exists:

- **`conventions.md` has a new section, *Teaching it***, placed first among the sections because
  it is the first thing a player meets. It has the standard, with a table of eight games' first
  missions and their tags, what is built here, the three lessons, the asymmetry, and the
  recommendation.
- **The fog section's fact 2 is corrected in place**: the crossing look goes only to a soldier
  holding a reserve.
- **`briefs.md` is re-primed.** The six landed briefs are out, with a table naming each one's
  branch and entry and a pointer to their full text at `45e9829:docs/interface/briefs.md`. Two stays
  word for word with its amendment, and three new briefs follow it: seven `view/turn-end`, eight
  `view/briefing-first`, nine `content/first-mission`.
- **`../decisions.md` entry 099.**

Five things worth not re-deriving:

- **The brief's taxonomy was wrong, and checking it was worth more than answering it.** Into the
  Breach has a tutorial, and Invisible, Inc.'s is the most scripted in the set. The real split is not
  *tutorial or none*: eight of eight games with a source teach in a first mission, and they differ
  on how scripted it is. A genre claim in a brief is a thing to check against a source, the same
  lesson the synthesis learned about four of the queue's briefs.
- **Teach the departures; the conventions teach themselves.** Klei's finding about expectations
  carried in from other stealth games is the reason. It turns *what must a player be taught* into a
  list this document already had, the **departure** tags, and three lessons cover all of them.
- **The reserve is alertness, and the interface docs had missed it.** `ReactionWindow.BuildOffers`
  gives no look to a soldier with nothing banked. The design doc says so, and entry 097 did not. It
  makes the End turn slot the one place where a costly silence was left.
- **Nothing a player reads before turn one is about mechanics.** An explanation read before the
  thing it explains does not stick, which is Into the Breach's playtesters. The briefing is the
  only thing before turn one, and it carries lesson 2 for free, because the told marks are its
  *presence* paragraph said as rules.
- **Shaped, not scripted, is forced by contract 2 rather than chosen for taste.** A scripted guard
  is not `Commander`, and a script that holds one needs a rule. The rules already make the lessons
  happen if the ground and the posts are placed for it. That is also why the one hard rule in brief
  nine is about the file: the stop sits above every rung the mission teaches.

---

## What landed on `interface/fog`

Entry 094's item 15, answered ahead of the onboarding brief because View's ground-and-camera brief
was waiting on it. Entry 097 has the findings and the one question for Core. What exists:

- **`conventions.md` has a new section, *What the squad can see***, placed before *What of the
  enemy is drawn*, since the ground is what the enemy is drawn on. It gives the standard with its
  count, what the rules mean by *seen*, the asymmetry, and the recommendation in the usual shape.
  It also has a paragraph on the cover outlines against the shield, and four checks a capture can
  run.
- **`../decisions.md` entry 097.**

Four things worth not re-deriving:

- **The source settled it, not the reference set.** The set could say only that a fog is two
  games' answer out of four. What decided every sub-question — squad or soldier, which height,
  range, zoom — came from reading `SightSolver`, `AwarenessTracker.Observe`, `Tactician.Known` and
  `BattleView` together. The standing-height test is the rules' own test for having looked at a
  place, and the invariant *no drawn body on dark ground* follows from how the trace hides a
  silhouette. Neither was visible from the genre.
- **The largest finding is that lit ground cannot mean empty here.** Being drawn needs a rung as
  well as a line, and looks happen only at a turn's end and at a crossing. Every genre fog promises
  the opposite. The section is written so that the drawing never makes that promise.
- **Two layers, one reading.** The fill is the sight half and the tint the awareness half of what
  `LookGain` multiplies, and Core already keeps those in two homes. Clipping the tint to the fill
  turns two overlays into one reading with a binary edge and a grade inside it. It came from a
  remark in `AttentionOn` rather than from any game.
- **One convention was checked against the frames already in hand, and it came out thinner.**
  Entry 094 called a darkened ground *the convention*. The C12 frame, which was captured for a
  different question, is exactly where a fog would have to show, and there is none. It is worth
  going back through the existing shots before asking for new ones.

---

## What landed on `interface/captures`

Entry 089 has the findings and what each reaches. What exists:

- **Thirty-one crops in `docs/interface/reference/shots/<game>/`** across five games, named for
  what they show. Small interface crops are PNG, and whole scenes are JPG at 1,400 to 1,600 pixels,
  which kept the set near 7 MB.
- **`observed` tags in five reference files**, each naming its crop. Where a shot contradicted a
  claim, the claim is corrected in place and says so; answered gap entries are struck, not
  deleted.
- **`captures.md`** — each of the twelve entries above the line opens with what came back, and a
  struck heading means answered or ruled out.
- **`conventions.md`** — the held-key recommendation is struck and replaced, the C10 mark is gone,
  and heading 5, the banner and the reaction-firing rows are corrected in place.
- **`briefs.md`** — *Settling One*, after *Amending One*. No brief text rewritten.

Five things worth not re-deriving:

- **The held-key recommendation failed on its denominator, not its count.** Four games used a held
  key, and all four used it for *everything at once*, never for one shot's terms. 077 warned that
  reading the denominator is most of the method, and the synthesis still missed this one. A
  convention borrowed for a job has to be counted among games doing that job.
- **Guides describe mechanics; only a picture describes a readout.** Warhounds' per-bullet
  percentages were real sentences in real guides about how the burst resolves, and the shipped
  preview shows one figure. The same gap produced FWT's "graded tints": a reviewer's adjective read
  as a drawing.
- **The most important finding came from a game the set nearly dismissed.** Future War Tactics'
  file said it was an authority on one thing "and on very little else". Its last-seen beacon is the
  only persisted enemy marker in ten games, and no review mentions it. That is the case for
  photographing a thin file's emptiest heading rather than skipping it.
- **The user's notes outrank the frames only on what the frames cannot show.** C1's notes said the
  fold hid `FLANKING TARGET`. The frame showed the damage column still open, and asking settled it:
  a chevron per column. Where an account and a picture disagree on something visible, ask; do not
  pick.
- **A clip was found on a contact sheet and read at full resolution.** Thumbnails at a fixed rate
  located the moments, and every claim cites a full-resolution frame pulled at a named time. Banner
  dwell was measured on the banner's own pixels, frame by frame, which a person watching could not
  have done.

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
