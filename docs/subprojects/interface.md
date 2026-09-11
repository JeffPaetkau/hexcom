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
the answer is *this game has no such thing*. The first file sets the template and the rest follow
it, because a set whose files do not line up cannot be read across.

**One game per session.** Not thrift — the evidence is images, and images do not compress into a
summary the way prose does. A session that reads forty screenshots has spent most of a normal
increment on the reading alone, which is the correct price for the thing being bought and the
wrong price to pay twice in one context.

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
is five files and about five increments; Tier B is on-demand, and the question that summons one
is named in the brief that asks. A reference file nobody is building from is the most expensive
kind of prose this project can produce.

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
what a key does. Ask for a short clip only for those, and say which frames matter. Note that
`ffmpeg` is not installed on this machine — a clip cannot be read until it is, and one still per
named moment is usually the cheaper request.

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

## The job — XCOM 2 in detail, and what its mods say it got wrong

Branch `interface/reference-xcom2`. Take a worktree; the rule has no exception for prose.

**What it is.** `conventions.md` answers nine questions at the altitude of *what the genre does*,
and the user has called that a good start and asked for the grain underneath it. View is about to
build six briefs against that standard. A brief is only a sufficient prompt if it can say what
the thing looks like and how it behaves — where the figure sits, what gesture reveals its terms,
what happens on hover, what happens on cancel. That evidence does not exist yet. This job builds
the first file of it.

**One game, in depth, not five in outline.** Depth is the whole request; breadth is what makes a
report like this read as a summary of things everybody already knew. XCOM 2 and War of the Chosen
only. The rest of the shelf is the next job in this territory and follows the template this one
sets.

**Why XCOM 2 first, and why the mods are the better half of the idea.** The base game is the
genre's best-selling exemplar and sets the action bar, the shot HUD, the cover pips and the
ability hotkeys that a player arrives already knowing. But its UI mod ecosystem is something
rarer: a decade-long, download-counted record of *what a tactics interface failed to tell its
players*, written by the players who wanted it. A mod with hundreds of thousands of subscribers
is a gap in the genre's best interface that was worth somebody's weekend. That is a stronger
signal than anything the shipped game does, and no other game on either shelf offers it.

**Where the output goes.** `docs/interface/reference/xcom2.md`, a new directory. Its head says
what the template is and why, in a paragraph, because four more games follow it. `conventions.md`
is not rewritten — the standard stands, and this is the evidence underneath it. Add one line to
`conventions.md` pointing at the reference set, and nothing else.

**What "finest detail" means here.** Ten headings, and the file carries all ten even where the
answer is *this game has no such thing*:

1. **Screen furniture** — every persistent element of the tactical HUD, where on the screen it
   sits, what it shows, and when it appears or disappears.
2. **The soldier** — how actions are shown and spent, the ability bar, the hotkeys, what a hover
   over an ability does, what cancel does and how far back it goes.
3. **The target** — the shot HUD line by line: every term in the hit-chance breakdown, whether
   the terms are shown by default or behind a key, the target-switch gesture and the cycle order.
4. **The tile** — movement range and the dash band, the path preview, cover pips, the
   concealment ring, and which of those are drawn on hover versus after a commitment.
5. **The enemy** — how a suspected or unseen enemy is drawn if at all, the alert states and their
   icons, the pod-activation moment, the scamper.
6. **Turn order and time** — whether there is a strip, what an interruption looks like, what the
   player is shown during the other side's go.
7. **Reactions** — how overwatch is declared, whether its arc is drawn, and what the trigger
   looks like at the moment it fires.
8. **Camera and input** — default binds, drag gestures, rotation steps and their speed, the
   storey control, tab targeting.
9. **Confirmation and refusal** — what takes a second click, what warns, and what the game lets a
   player do irreversibly in silence.
10. **What the game hides, and the mod that reveals it** — the heading the other nine exist to
    reach.

**The mods.** In-mission only. Each row says what gap it fills, what it draws, and roughly how
many people installed it, because the count is an ordinal reading of how badly it was missed.
The ones worth starting from, not a closed list: Gotcha Again, Free Camera Rotation, True
Concealment, Peek From Concealment, Overwatch All/Others, Stop Wasting My Time, Show Health
Values and its numeric-display relatives, Target Preview and the perfect-information family,
Evac All, and whichever tactical-HUD replacement is currently the most subscribed. Skip anything
that touches the Avenger, the geoscape or character creation — this territory is the mission.

**The shots are the point, and the rules for them are in *The reference set* above.** Read that
section before starting: the inbox, the four tags, the curated `shots/` directory, and the rule
that the first thing this job produces is **one shot list** covering everything it will need. The
user owns XCOM 2 and can capture it. A claim about where a figure sits, how big it is and what is
beside it should be tagged **observed** and name the shot — that is what this job is buying, and
a file of **remembered** claims is the report we could already have written.

**A short verified file beats a long remembered one**, so do not pad to fill a heading.

**Settle before writing much.**

- **The template**, because four games follow it and a reference set whose files do not line up
  cannot be read across.
- **Which headings this game is the authority on, and which it is merely an instance of.** One
  game is not the genre. Where XCOM 2 is idiosyncratic, say so and leave the convention call to
  the pass that has more than one game in it.
- **Heading 5 will be thin, and that is the finding.** XCOM 2 draws the enemy the moment a unit
  sees one and has no contact file, so contract 3's subject has almost no exemplar here. Record
  what little there is — the concealment ring, the last-known-position marker on a lost target if
  any — and do not stretch the rest into a convention it never was.

**What to do with what it finds.** Two destinations and no third. A fine detail that changes a
brief already in `briefs.md` goes in as an **amendment appended to that brief**, naming it — the
briefs themselves are not rewritten, on the same reasoning the log is append-only. A detail that
would need a query Core does not expose is a proposal in `../decisions.md`.

**Out of scope.** Building anything. The strategy layer's interface. Rewriting the nine sections
of `conventions.md`. Onboarding, which is the brief below and stays queued behind this.

**How to know it worked.** A View session building brief one can answer, from this file alone and
without opening a browser: where XCOM 2 puts the hit chance, what terms are on it, what gesture
shows the arithmetic, and what its players added because that was not enough.

---

## Next in this territory — the first five minutes, and what has to be taught

Queued behind the reference job above, and deliberately: onboarding decides what a player must be
told before turn one, and half of that answer is what the genre's interface already teaches
without telling anybody. Branch `interface/onboarding` when it comes up.

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
