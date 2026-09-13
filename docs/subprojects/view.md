# View — presentation and interface

The Godot layer: drawing what Core answers, and taking input. Currently the greybox — a 3D
blockout of the battle with no art in it — which opens as the game a person plays, drives either
side by hand, or hands the hostile side to the AI.

Read [../map.md](../map.md) first.

## Owns

```
game/**
```

## Must not touch

```
src/**      tests/**      docs/design.html
```

If the view needs a query Core does not expose, that is a Core change — and by contract 2 in
[../map.md](../map.md) it is one the AI gets too. Raise it in `../decisions.md` rather than
reaching into `src/`.

## Depends on

- **Core's public API**, which is the same surface the AI reads. No private back door for
  drawing.
- **Information asymmetry** (contract 3). Your own soldier's exposure is reported exactly,
  because that is information about yourself. An enemy's alarm is coarse on purpose. Do not
  render a number Core deliberately blurred, even when you can compute it.
- **One horizontal world unit is one metre** (contract 5). Held by `SandboxScale`, which builds
  the one layout `Battle` is given and owns the mapping from the rules' plane into the scene;
  the camera moves itself and cannot reach it. See `../decisions.md` entries 002 and 005.

---

## The job — the action bar

Branch `view/action-bar`. **Read `../decisions.md` entry 094 first**: it is the second play-through,
and four of its fifteen findings are this brief — 6, 9, 10 and 11. They are one missing thing.

**What is wrong, in the player's words.** *I press V and nothing seems to happen other than lose AP.*
*Have a shot on an enemy but only have 9 AP. How do I take a snap shot?* *Fire and End turn should be
different keys.* *Both keyboard and mouse should work for all actions.*

**What it is.** The bar `../interface/conventions.md` recommends under *Selecting and ordering*: a
row along the bottom, a slot per action, each showing its key and its price, each usable by click
and by key. Firing becomes a mode entered from a slot and confirmed on the target. End turn gets its
own slot and its own key.

**Where the seams already are.**

- `HexSandbox.HandleKey` — `Key.Key1` is commented as *an action bar with one slot in it*, and
  `Key.Space or Key.Enter` fires an aim or, with none, ends the turn. The second half of that case
  goes.
- `Battle.PlanShot(shooter, target, mode)` **already takes a mode**; `AimAt` and `ConfirmShot` never
  pass one, so every shot a player takes is `WeaponProfile.DefaultMode`. The modes are
  `unit.Weapon.Modes`, and the price is `Stats.Costs.Fire(mode.ApCost)` — the price the reserve
  ladder already uses, so the bar and the ladder cannot disagree.
- The staged shot's headline, bill and worth (`BattleHud.DrawShotHeadline`, the docked terms,
  `Tactician.Appraise`) must price **the mode chosen**, not the default. Check every caller that
  builds a plan for the staged aim.
- The other slots already have one method each: `SetStance`, `FaceTo`, `HoldArc` / `NextArc`,
  `ArmAmbush` / `SpringAmbushOn`, `ShoutAbout`, `LeaveTheField`, `EndTurn`.
- **The arc that is not drawn.** `BattleView.BuildHeldArcs` skips a unit whose
  `Overwatch is not null && Reserve <= 0`, and entry 093 found the active soldier's reserve reads
  nought on its own turn. Confirm with a capture (`--arc` on the active soldier, before and after)
  before touching it. If the skip is right for a reserve that has been spent, draw a *declared* arc
  on the active soldier some other way rather than deleting the condition; ask `Battle`, not the HUD,
  what the reserve will be.
- `SandboxScript` — a capture must be able to pick a mode (`--aim NAME` with a mode) and press a slot,
  or the bar is untestable headless.

**Settle before writing much.**

- **Where the bar goes.** Convention is bottom centre, and entry 093 found bottom centre is under the
  legend. The legend is a tester's thing and the bar is the player's, so the bar has the better
  claim; say where the legend goes instead.
- **Mode first, or target first.** The genre is ability first: pick *snap*, then the target, then
  confirm. Clicking a hostile with no mode chosen currently aims at the default; decide whether it
  still does (probably yes, as *standard*, the slot lit) so the one-click habit survives.
- **The arcs as slots.** Three widths plus none. One slot that cycles repeats `V`'s fault — four
  states at a point each with nothing saying which one landed. Three slots, or one slot that opens
  three, and the held one lit either way.
- **A slot that cannot be afforded** is shown, dimmed, with its price — *snap 15 AP* at 9 AP answers
  item 9 without a word of help text. A slot refused for another reason says the reason.
- **End turn's key.** XCOM 2 uses `Backspace`; `Space` and `Enter` confirm and do nothing else. Say
  what happens to `Space` with nothing to confirm (nothing, is the recommendation).
- **The number keys.** Outside a window `1`–`9` are the bar's; inside one they stay the window's
  answers, as now. Never both at once.
- **What hovering a slot shows.** Entry 093 ruled out a hover card per *figure*. A slot's name and
  what it does is not a figure; one line is allowed, and nothing that repeats the docked terms.

**Out of scope.** Rebinding keys and the options screen — `view/options`, below. The camera, the
ground's labels, cover shields and fog — `view/ground-and-camera`. How the enemy is drawn — brief two.
The price of a shot, which is Core's (entry 094, item 14). Every rule.

**How to know it worked.**

- A rifleman with 20 AP and a hostile in sight takes a **snap** shot with the mouse alone, and again
  with the keyboard alone; the headline and bill show the snap's price and odds before the confirm.
- The same soldier at 9 AP sees every fire slot dimmed with its price.
- `Space` with no aim does not end the turn. The End turn slot and its key do.
- Holding a narrow arc on the active soldier draws it on the ground in the same frame, and the bar
  says which arc is held — captured before and after.
- The pinned scene changes by the bar and nothing else; two runs hash the same.

**Queued behind this, in order, so a session finishing it knows the next.** Each is Master's to write
out in full when it is next; the items are entry 094's.

1. **Brief two, `view/enemy-file`** (`../interface/briefs.md`, as amended by 089 below), now also
   carrying 094's items 5 and 8 — a ghost from the briefing must not read as sight on turn one, and a
   rung under a hostile must say whose it is.
2. **`view/ground-and-camera`** — hold `Q`/`E` to turn and a tap still lands on a bearing (item 2);
   **middle-drag pan does not work in the build** though the code reads right, then a mouse pan the
   player can find (item 3); pitch within a clamp (item 4, and `conventions.md` *The camera*);
   readouts that do not cover bodies (item 12); a cover shield at the cursor saying what cover *you*
   would have, kept apart from the outlines that say what cover a tile has *from* you (items 7, 13);
   the reach and reserve edges labelled, and weapon range drawn somewhere (item 14); **the
   waystation's house and exit drawn at all** — `BuildExit` draws only a `Withdrawal`, and a
   `Reconnaissance` is not one; and the fog, once Interface has said what it becomes (item 15).
3. **`view/options`** — an input map and a preferences file loaded at start, and an options screen
   over them (item 1, settled narrow with the user). `--edge-pan`, `--pace` and `--still` move in
   first.

Small things owed and not briefs: the bill's last clause becomes names when Core lands entry 086's
relay; **the map still draws whoever is up, whichever side**, which is brief two's ground and entry
090's finding; and entry 092's *For View* — `HexSandbox.OutOfTime` can go now both mission files
write their clock onto the objective.

**Owed to later briefs, routed from entry 089 so it is not lost.**

- **Brief two.** Heading 5 is no longer empty: Future War Tactics leaves a red beacon where each lost
  enemy was last seen, still up next turn (C12), and Invisible, Inc.'s interest-point `?` is a glyph
  on a bracketed tile (C3). So *building the thing ten games did without* is nine, and the one shipped
  persisted marker is **a glyph at a place, not a ghost of a body**. The brief's substance stands;
  its framing and that choice move. Also entry 090: the map still draws whoever is up, whichever side.
- **Brief six, already built.** A reaction firing is on film for the first time (C4). Warhounds plays
  the shot in the overhead view it was already in, puts the result as floating text at the target,
  marks no trigger point on the ground, and tints its idle overwatch area on the grid's own tiles
  rather than drawing a wedge. Worth reading against what six built the next time anybody touches
  the moment a reaction fires; not a job on its own.

**What the next View brief inherits from three, six, four, five and one, so it is not re-argued.**

- **Keys.** Outside a window `1` aims, `Tab` cycles targets and space confirms a shot or ends the
  turn — **the last half of which the action bar undoes, entry 094**; inside one `1`–`9` change an answer, `Tab` picks whose, and space runs it. Right-click and
  `Esc` back out and never spend a point. **Held `Ctrl` is every figure's terms at once and `P`
  folds the shot's docked terms**; `Alt` is still unbound.
- **A figure hangs from the thing it describes.** One headline at the thing; its terms docked while
  aiming, or under held `Ctrl`, and no third way — no hover card per figure. Offsets are pixels from
  `BattleView.Crown`, which reads the walk; a tag whose thing is off screen is not drawn. The panel
  keeps the mission, the clock, the weapon and the storey, and nothing else goes back into it.
- **The reserve is a ladder.** `SandboxFrame.Ladder` asks `Banked`; the ground and the bar use its
  steps and its colours, and nothing multiplies by the fraction.
- **Whose knowledge is on screen.** A window offers our own side's reactors; the other side's are
  behind the instruments window, the same switch as the AI's orders. A hostile nobody of ours has
  eyes on is *somebody unseen* in any list of names, said once however many there are —
  `SandboxFrame.Names`.
- **A hostile up under the AI is withheld.** `SandboxFrame.Withheld` — a hostile active, the side on
  the AI, the instruments shut — blanks the situation block to the clock and *their go* and nulls the
  staged shot. Anything else that describes the active unit asks it first.
- **Their go is one banner, never one per turn,** and what our side perceived of it is a line per
  event under *WHILE IT WAS THEIR GO*. The banner is not countable and the lines are, on purpose —
  entry 065.

---

**Standing, behind the brief.**

**The measurement a session cannot take.** A person plays `build/Hexcom.exe` to a verdict and
says what read wrong. The first was entry 057 and the second entry 094; the next is the same
measurement again, and a session finishing a brief should expect its work to be played rather than
only captured. The walking pace was the other one and it has been taken: **ten metres a second,
watched rather than argued** — entry 080, and it is the first interface figure in the project
settled that way.

**The options screen is scheduled now** — `view/options`, third in the queue above. `--edge-pan`,
`--pace` and `--still` are three player preferences a double-click cannot reach, and the user
settled the scope in 094: keybindings and preferences, not every constant.

**Out of scope, and unchanged.** Art, audio. Every rule. A second map or mission. The strategy
layer.

---

## What landed on `view/readouts-in-place`

Brief one, to *Settling One*. `../decisions.md` entry 093 is the reasoning, the tests and the two
findings; this is the shape.

**Two ways to the terms, and only two.** Each thing on the map carries one figure. The shot's terms
open for as long as the player is aiming, docked at the right edge above the legend — `DrawTerms` —
with a fold that is a preference, not a gesture per shot: `P` or a click on the switch, kept for the
run in `_termsFolded`. Folded, the `AIMING` lines and the headline stay, because the `AIMING` line is
what tells a player space fires. Holding `Ctrl` sets `SandboxFrame.Details` and every thing shows its
terms together. Both are `--details` and `--fold` to a capture.

**What hangs where** — `BattleHud.DrawInPlace`, nothing of it while `Withheld`:

| | headline | terms, under `Ctrl` |
|---|---|---|
| the soldier up — `DrawSoldier` | above the name: the points bar cut at the reserve's steps, each step as a spend, exposure and the highest rung on it | the bar they act from, the arc held, who a shout reaches, who has a line on it, the posture keys scored |
| a contact — `DrawContacts` | its name and rung, as the view draws them | under the rung, or under the ghost at a marker: distance, *you hold*, worst shot on us, *sees you* |
| the staged shot — `DrawShotHeadline` | over the target's name: `HIT`, and cost and worth under it; or *no shot* and why | docked while aiming |
| the cursor's tile — `DrawCursorTag` | beside the tile: cost, what stopping there banks in the band's colour, who hears the walk | cover, exposure, distance and band, attention, loudness |

The cursor's tag is drawn last so it is on top; it is not drawn while aiming, since a click on the
ground then backs out and moves nobody, nor over a soldier the picture shows.

**The HUD is handed a camera and a function.** `BattleHud(font, camera, crown)`: the camera to
project tiles, and `BattleView.Crown` — public now, and walk-aware — so a readout hangs from the body
the name hangs from. The HUD learns nothing else about the walk. That makes **three** things that read
the walk, and the gotcha below says so.

**The ladder** is `ReserveLadder` in `SandboxFrame.cs`: a rung per step, found by asking `Banked` for
the fewest leftover points that reach it, priced at `Costs.Fire` — what `AppraiseHolding` checks. Its
`Floor`, `Cheapest` and `Better` are the three the ground draws; `Better` is the first mode dearer than
the cheapest, and one colour covers it and everything above. **`BuildReachBands`** replaces the reach
fill: a pale edge at reach, and violet edges at the floor, the cheapest shot and the dearest shot a
move can keep, each inset a little further so nested edges do not sit on each other, and a band that
encloses what the band outside it does, or only the soldier's own tile, is skipped.
`SandboxPalette.BandHue` and `ReachEdge` are the colours; `ReachFill` is gone.

**Two things changed that were not the brief's and were in its way.** `SandboxCamera.Fit` looks past
the map's middle and stands further back, because at `--fit` the near rim was under the legend and the
brief's test is that nothing unattached lies over the map. And the worth line's terms: it printed
*harm less spent*, and the score has had two more terms since Core priced a shot's give-away — `Terms`
now, as everywhere else.

**`TheirGoDwell` is 1.4 seconds, and measured** — capture C7, entry 089.

**What was measured, from captures.** The target's headline at default zoom on the compound (`--until
Orsini --aim Spotter`) and the waystation (`--ai --pass 16 --until Bekker --aim Teague`); `--details` on
both, and on `--until Bekker --hover -16,-3 --zoom 26`; `--fit` on the waystation and the compound; a
refused shot's headline and dock (`--aim Cobb` from Orsini). The pinned scene, twice, one hash.
**Not measured**: a hand on `Ctrl`, the fold switch clicked, the focus-out release, the dwell.

---

## What landed on `view/order-strip`

Brief five. `../decisions.md` entry 090 is the reasoning, the measurement and the finding; this is the
shape.

**The strip is the first six bookings `Sees` allows.** An unfound hostile holds no slot, no roll and
no reserve — entry 064 — and because the six are counted *after* the filter, the strip is the same
picture whether an unfound hostile is booked among them or not. The genre is silent here, not
departed from: none of the ten reference games draws a per-unit strip.

**The round mark** is a rule and *round N* before the first booking in a later round than
`Battle.Round`, from `ActAt / Battle.TicksPerRound`. **A hostile found since our last order is
outlined** in its hostile hue — `SandboxFrame.Found`, kept in `Recalculate` by comparing who our side
had eyes on before the gather with after, cleared by the next order, and cleared after the opening
gather so a deployment is not a discovery.

**The banner — `DrawTheirGo`.** *THEIR GO* and three dots, a band across the full width a third of the
way down, because the camera puts our own soldier in the middle. It goes up in `Settle` when a hostile
turn is handed to the AI — once, however many turns follow — and comes down in `LowerBanner` when
nothing is holding it (a hostile window of ours to answer, a hostile being walked) and
`TheirGoDwell` has run. **It is not drawn while a window is open**, and resolving a hostile window
restarts the dwell. `_theirGo` counts seconds only while `Animated`, so a capture has no dwell and
never shows the banner.

**`TheirGoDwell` shipped at 0.9 seconds and provisional** against captures C7 and C17. A floor, not a
length. **It is 1.4 and measured since brief one** — C7, entry 089.

**The account — `BattleHud.Perceived`.** When control leaves our side `Settle` takes a snapshot of our
side's merged knowledge; `Perceive`, after every `AfterAction`, compares it with now and freezes the
lines, and drops the snapshot when the stretch is over rather than paused. Found, lost sight of, lost
track of, *somebody unseen, marked at*; and a shot or a blast at one of ours, read off the turn's
`Act`s, since `TakenTurn` carries those now and `Orders` is derived. Cleared by our next order.
**The reset is keyed on the snapshot, not on `keepRecord`**, because a turn of ours handed to the AI
sets `keepRecord` too and would otherwise keep a stale account; the one call that comes through
`AfterAction` mid-stretch is a hostile window being run, and that is exactly when a snapshot is held.

**Two leaks in the pause the brief did not name, closed.** `SandboxFrame.Withheld` blanks the top block
to the clock and *their go* while the AI's hostile is up and nulls `StagedShot`; it used to read
*you hold 63/100* on each of ours during a hostile's window. And the window's mover and springer go
through `Names`.

**What was measured.**

- **The strip, with and without an unfound hostile's turn**: `--until Cobb` against `--until Cobb
  --pass` on the waystation, hostiles by hand — identical strips above the ground; master's pair
  moves a `?`.
- **The pinned scene changes in the strip only**: the diff is x 1410–1580, y 142–182, which is the
  round mark pushing Vance down a row.
- **The window stop in the game's view** — `--windows --ai --pass 30 --zoom 40` — reads *round 4/30
  their go* where it read Cobb's whole situation.
- **The account across a mission**, one `--pass` or `--ai-turn` a step: shots at Vance by name, then
  by *somebody unseen* once Vance was down; a blast catching Vance; *found Cobb*, *found Teague*,
  *lost sight of Cobb*. Stretches in which nothing was perceived printed nothing. No marker line came
  up in those runs.
- **The found outline**: `--ai` and five `--ai-turn` on the waystation stop on Orsini with *found
  Cobb* in the account and Cobb's slot outlined; Teague, already in sight, is not.
- **Not measured**: the dwell on a screen. A capture cannot show it by construction and a person at
  the keyboard is the check.

---

## What landed on `view/shot-bill`

Brief four. `../decisions.md` entry 086 is the reasoning and the finding for Core; this is the shape.

**Under the shot line, a bill line names who taking the shot would tell.** *The shot tells: Teague
(shot at), somebody unseen — and whoever Teague passes it on to.* Names and never figures, the move
line's rung discipline. The target first and marked, because being shot at tells the target outright
whether or not a round lands. On the map, `((( ! )))` under the target's rung whenever the shot would
tell anybody else, and a `!` over each of those the picture shows.

**One call on Core, and not the one the brief's promotion named.** The job said the shot's half uses
`AwarenessTracker.WouldHear` against the weapon's `Loudness`. Reading `Battle.Fire` first, as the job
also said to, a shot announces itself three ways — the target's certainty settled outright, the bang
heard at `Loudness`, the flash seen at `Flash` — and `WouldHear` previews one of them. A beam is
silent and bright, so a beam shot would have read *tells nobody* while telling everybody facing it.
`Battle.WouldAnnounce(ShotPlan)` previews all three and is the call the AI's scorer prices `GivenAway`
by, so the player's bill and the AI's charge are one answer. `SandboxFrame.Giveaway` is that call,
and `SandboxFrame.StagedShot` — moved out of the HUD — is the shot both halves ask it about.

**Measured, headless, and it found the hole.** `--aim` now reports who Core's preview would tell, and
a shot reports who it actually told, read off the enemy's contact files either side of `Battle.Fire`
and before anybody else acts. On the waystation from round 7, Bekker's three possible shots:

| shot at | the bill named | the shot told |
|---|---|---|
| Teague | Hollis, Marek, Teague | **Cobb**, Hollis, Marek, Teague |
| Marek | Hollis, Marek, Teague | **Cobb**, Hollis, Marek, Teague |
| Hollis | Hollis, Marek, Teague | Hollis, Marek, Teague |

In all three every name the preview gave was told, and reading `WouldAnnounce` against `AnnounceFire`
says it cannot name somebody the shot does not tell: the three channels are applied in sequence and
previewed side by side, and each only raises. What it misses is the relay:
`TakeFireFrom` has the target pass what it now knows to whoever it can reach, and Teague and Marek
reach Cobb while Hollis does not. Core's preview omits the relay on purpose — its remarks say a
relayed contact arrives below the rung anybody acts on — but *below the rung* is still *told*, and a
shot at a signaller is exactly where it stops being small: the relay is also where the side's alarm
is raised. Making the two one call needs Core, so it is entry 086 and not a computation here. Until
then the line ends *and whoever Teague passes it on to*, which is true and names nobody it cannot.

**The move's noise line was leaking, and brief four found it by copying it.** It printed every
listener in earshot by name, found or not — on the waystation, most of the garrison's names on the
first hover. Both lines now go through `SandboxFrame.Names`: a hostile nobody of ours has eyes on is
*somebody unseen*, said once however many there are, since a count of unfound listeners is a count of
the other side's soldiers. That is one step stricter than the exposure line, which says *somebody
unseen* once per watcher; the exposure line was left alone.

**The glyphs are provisional, as the job said to treat them.** Capture C8 — the Gotcha Again mod's
vocabulary on a hovered tile — has not been taken, and these are text in the label font because that
is what the greybox draws. They are placed in pixels from the point the name label hangs from, not in
metres: the first attempt put them in metres and at rifle distance they landed on the names.

**Not done.** The amendment's placement for a *move* — the mark on the destination tile — is not
drawn; the move has its names on the cursor line and nothing on the map. Brief four is the shot.

---

## What landed on `view/window-default`

Brief six. `../decisions.md` entry 085 is the reasoning; this is the shape.

**A window offers our own side's reactors, and the other side's only while the instruments window
is open.** That was the brief's *settle first*, and its default. `SandboxFrame.Answerable` is the
list and `SandboxFrame.AnswerableIn` asks it of a window before it is the open one; the chooser, the
number keys, `Tab`, `--place` and the readout all go through it, so there is no second place a
hostile's offer can reach the screen. The count in the readout goes through it too — *1 of 3
answered* would have said how many of the other side have a line on the mover.

**A window with nothing of ours in it does not stop.** The other side takes its recommendations and
the move goes through, in both places a window is born: `MoveTo` for a move made here, and
`SkipUnanswerableWindows` — which was `SkipEmptyWindows` — for a turn a `Commander` is taking. **The
recommendations are placed before resuming, and that is the one thing in this branch that would
have been easy to get wrong**: `Commander.Resume` reads a window with nothing placed as everybody
holding fire, so skipping one the way an empty window is skipped would have switched the other side's
reactions off without a trace.

**The default is drawn as a state, not a suggestion.** Every one of ours not being chosen for reads
*will: Vance goes Prone at t15*; the one being chosen for lists its options with *← will, unless
changed*; one already answered reads *CHANGED TO*. The header says what space does in words —
*run it, every answer not changed stands* — so the common case is one key, and the brief's own
framing is what the words say: overwatch is a state the soldier is in, and the window is where you
may overrule it. Before this the readout said *recommended*, which is advice, and space's clause was
at the far end of a long line.

**Why a scored window rather than the alternative the amendment names.** Tactical Breach Wizards'
reactions are named abilities a soldier owns. A scored window is what makes a default answer possible
at all — `ReactionWindow.Appraise` ranks arbitrary soldiers and options — and a per-ability reaction
has nothing to default to.

**Closing or opening the instruments mid-window** re-points the chooser from the top, and a window
left with nothing of ours in it stays open and says *nothing here is yours to answer — space: run
it*. Closing a window of instruments is not an answer to anything.

**What was measured.**

- **The recorded scripts run unchanged**: `--windows --ai --omniscient --pass 30 --place Vance:1
  --resolve --pass 2` prints the same steps as on master.
- **Skipping a hostile-only window is the same battle as windows off.** The reaction script on the
  compound with `--windows` added — Orsini across Watchman's narrow arc — now moves straight through
  (*nobody of ours could answer*) and the capture is **byte-identical** to the same script without
  `--windows`. With `--instruments` it stops, and offers Watchman.
- **A whole waystation mission, both sides on the AI, one step per window.** Ninety `--ai-turn
  --resolve` pairs with `--windows --ai`, run on brief three's code and on this. Three's stopped at
  two windows, both of them asking the player to answer *the enemy's* reaction to one of our moves;
  this stopped at none. The mission ends *abandoned* in round 3 on both, with the same reaction line,
  strip and readouts — the pictures differ by 38 pixels along one ghosted wall edge and in nothing a
  label or a body carries.

**One thing lost, and it is small.** A move that stopped at its window used to be walked along its
route when the window resolved. A skipped window's move jumps, which is what an empty window's move
has always done. The moves affected are our own soldiers' turns handed to the AI with `J`, an
instrument, and the walk for an AI turn is already partial — entry 066.

**The amendment's arc adjust step was not built.** Both shipped precedents give a held arc an adjust
step before confirming, and `V` takes an arc in one press and charges for each. The amendment itself
calls it arguably another brief's; it is an open question below, and it belongs with brief two's
drawing of the arc if it is taken.

---

## What landed on `view/gestures`

Brief three. `../decisions.md` entry 084 is the reasoning and the two findings; this is the shape.

**Right-click never fires. Firing is a mode, and a shot is two gestures.** Point the mode at a
hostile — `1` (the one under the cursor, else the nearest), `Tab` (the next in sight, nearest
first), or a left-click on the body — read the terms, and confirm with space, enter, or a second
click on the same body. Right-click and `Esc` back out, spending nothing. The mode is `_aim` on the
node and `SandboxFrame.Aim` in the frame, and the frame is where it is checked: an aim is dropped
the moment it stops being a shot worth describing, so a window opening, the target leaving sight or
`O` being turned off cannot leave a line of fire on the map pointing at somebody it is not drawing.

**The two things the brief asked to be settled first.**

- **One confirmation in the game, and it is on the shot.** A move is still one click, there is
  still no undo, and nothing was added to soften the fog. Entry 077's law is the reason — a game
  lets a player take something back exactly as far as it told them the truth — and the shot carries
  the confirm because the shot is what announces you.
- **The number keys are an action bar with one slot, live only outside a window.** `1` aims. The
  window keeps `1`–`9`. Every action already refuses while a window is open and `AnswerKey` takes
  the numbers first, so a number never has two live meanings; moving the window's numbers would have
  broken the match between the readout, the keys and `--place NAME:N` for nothing. The letter keys
  for the other actions stay letters — none of them has a target to stage, so none needs a mode.

**What a click does now depends on two things, and the table is short.**

| | not aiming | aiming |
|---|---|---|
| left-click a hostile | aim at it | aim at it — or fire, if it is the one aimed at |
| left-click anywhere else | move | back out, **and do not move** |
| right-click | back out of the briefing, if it is up | back out |
| space / enter | end the turn | fire |

The ground click while aiming was the one real decision the brief left: a player who clicks the
ground mid-aim has changed their mind about the shot, and a cancel that also walked the soldier off
and spent the points would be a strange cancel. The path preview is not drawn while aiming, for the
same reason — it would be promising a move the click will not make.

**An aim survives the orders taken on the spot and nothing else.** Stance, facing, an arc, a shout:
the aim stays and the shot line re-plans, because crouching to see whether the shot improves is part
of deciding to take it. A move, a shot, a pass, or a turn handed to the AI all go through
`AfterAction`, which drops it. A refused confirm stays aimed and says why — out of range, no line —
because what a player wants after *no* is to change something and try again.

**`ClickSlop` and `_orbitTravel` were meant to be a deletion and are not.** The section on
`view/playable` below says so and was wrong in one respect: it assumed the right button would be
free once firing left it, and the brief gives it to cancel. Cancel on the press would make every
orbit throw the aim away — at exactly the moment a player most wants to look round. So the slop
stays, and what changed is its stakes: a drag misread as a click used to be a shot nobody meant,
and is now an aim dropped.

**`Tab` is built for this game's reason, and the amendment's reason turned out to be the wrong
one.** It said a hostile can be a see-through body at a marker. A ghost is not a target — `Sees`
needs eyes on, and so does `FireAt` — so the cycle never offers one. The reason that holds is the
cursor: it picks only on the storey being looked at, so a hostile on a roof cannot be clicked from
the ground at all. On the compound, Spotter is up the ladder and Orsini's `Tab` reaches it with a
45 per cent shot that no click from storey 0 could have asked for. Entry 084.

**What is drawn.** A white line from the shooter's eye to the target's chest and a white ring outside
the target's own rings, both in the cursor mesh because pointing the mode elsewhere changes nothing
true and must not cost a sight sweep. White because hostile red on a line would read as a shot
coming the other way and yellow already means a walk that is paid for. The line is drawn whether or
not the shot is possible; the shot line says why not. In the HUD, an `AIMING` line in capitals above
the shot line says at whom, which of how many, and the ways out in words — space ends the turn when
that line is absent and fires when it is present, which is only fair if nobody can miss which. The
shot and worth lines quote the aim rather than the cursor while one is up, so the pointer can go and
orbit without the terms being swapped for somebody else's.

**Every new interaction has a script step.** `--aim [NAME]` is `1` bare and a left-click on NAME
named; `--next-target` is `Tab`; `--confirm` is space while aiming; `--back-out` is right-click and
`Esc`. `--fire NAME` is unchanged, and for a shot the rules allow it is exactly `--aim NAME
--confirm` — the two captures hash the same. For one they refuse the two part company on purpose:
`--fire` spends the step and reports *no shot*, `--confirm` stays aimed and says why. `Ctrl` and
`Alt` are unbound, as brief one's amendment asked.

**What was measured, and what could not be.**

- Master's `game/` and this branch's, the same commands: `--place Vance:1 --resolve` on the
  waystation and the reaction script with a `--fire` added on the compound print identical steps.
  The pinned scene differs only in rows 822 to 892, which is the legend; the two scripted captures
  differ from row 788 down, which is the legend and the block stacked above it moving up a line.
  Nothing above that changed by a pixel.
- **The mouse and the keys were not driven.** A capture is deaf, so `LeftClick`, the right release
  and the key bindings are checked by reading and by their script twins, not by a hand. The
  play-through is where they get measured.
- **The exported build hung** when run with `--shot` from this session and wrote nothing; the
  editor harness was used instead. Not investigated — it is master's build and not this branch's.

**The pinned scene changes along the bottom edge.** The player's legend is three lines — looking,
orders, posture — because the shot's four gestures would have run the old second line towards the
right edge.

---

## What landed on `view/aside`

Entry 063's flag and brief Zero's three riders. `../decisions.md` entry 079 is the reasoning; this
is the shape.

**`SandboxAside` is one method and the whole of the mechanism.** It takes the smallest X over
`DisplayServer.ScreenGetPosition`, reads the usable rect of that screen so a centred window does
not sit under the taskbar, and centres the window in it. Both windows go through it: the main one
in `_EnterTree`, the instruments one when it opens, since a hidden window has no position worth
setting and `I` can open it long after `_Ready`. It says where it put things, for the same reason
every script step says what it did — a run that asked to be put aside and silently was not is a
window in the user's face with nothing in the log about it.

**The window appears before it moves, and no script can prevent that.** The user watched it happen:
Godot creates and maps the window while bringing the display server up, and the C# assembly is not
loaded until the scene layer initialises, which is after. `_EnterTree` is the earliest hook there
is and it shortens the flash rather than removing it — the world building, the mission load and the
opening sight sweep now all happen on the monitor the window is going to stay on. **The placement
that has nothing to see is Godot's own `--screen N`**, before the `--`, using the index `--aside`
prints; it is not the default because an index is a fact about one machine and the smallest X is
true everywhere. Entry 080.

**The check entry 063 asked for came back stronger than it asked.** Moving the window costs no
pixels at all: the pinned command on the left monitor and the same command where Windows put it
hash to one SHA-256, and so do two runs on the left monitor. Nothing hashed before this diffs
against anything hashed after it.

**And it found that the instruments window was not a window.** Godot embeds `Window` nodes in the
parent viewport by default, so the second window was a panel in the corner of the first: it could
not be dragged to another monitor, which is the only reason entry 066 built it, and a capture taken
with `--instruments` had it painted over the map. `project.godot` now says otherwise. The gotchas
carry the general shape, which is that photographing the second window is not a check that it *is*
one.

**The three riders.** Edge-pan is off and `--edge-pan` is the switch. `WalkLongest` is gone,
because a cap on a walk's duration is seconds-a-move wearing a metres-a-second coat and reinstates
exactly what pricing the walk in metres exists to prevent. **The pace is ten metres a second, and
it is measured** — the sheet says 1.4 to 2.5, this branch reasoned its way to 3.5, and the user
watched it and said ten. A hex goes by in about a sixth of a second and the longest walk the rules
can buy is under two. `--pace N` stays so the next person to disagree can show it rather than argue
it. Entry 080 has what the gap says about taking a figure from the genre: those figures describe
how fast a soldier moves, and this one describes how long a player watches a transition.

---

## What landed on `view/playable`

Entry 057 is what the user said after the first play-through; entry 066 is what building the six
cost. This is the shape, and the decisions the brief left open.

**One switch settles every animation, and it is off rather than waited for.** The brief allowed
two mechanisms — settle before the picture, or never start one — and `HexSandbox.Animate` is the
second. It is false for the whole of any run with `--shot` on it, `--still` turns it off for a
person, and everything that animates asks it and lands on its end state within the call when the
answer is no. Waiting would have put a capture on a code path nobody had measured; this leaves it
on exactly the one that was byte-deterministic before, and the pinned scene proves it — three
runs of the pinned command, one SHA-256.

**The camera turns freely and rests on the six bearings.** `SandboxCamera.YawRadians` is
continuous now and `Yaw` is derived from it, which is the only form anything outside the class
ever wanted. `Q`/`E` head for the next bearing and ease into it in about a fifth of a second,
counted from where the camera is *heading* rather than where it has got to, so three quick
presses turn three bearings. A right-drag turns it to anywhere in between and there is no snap
when it is released — a mouse that tidied itself up would be taking the view off the person
holding it. `--yaw N` still arrives within the call, animated or not, because a script step that
took frames would put the same command in a different place depending on how many it was given.

**The gesture set, settled.** Right-click had to keep firing, so the right button does both and
they are told apart by whether the pointer moved: under six pixels between press and release it
was a click and the shot goes off, over it and it was an orbit. **The shot therefore happens on
release**, which is the only moment at which the two are distinguishable. Middle-drag still pans,
the wheel still zooms, and the pointer within 24 pixels of an edge pushes the view at a rate
proportional to how far in it has gone — guarded on the pointer actually being inside the
viewport, because the whole point of the second window is that the pointer spends time elsewhere.

**That disambiguation is an interim and `../interface/briefs.md` brief Three retires it.** The
brief's finding, which landed while this was being built, is that right-click firing is itself the
departure: the genre spends that button on cancel, and this game has the most irreversible action
in it bound to the button a player presses to back out of something. When firing becomes a mode,
the right button is free, the orbit takes the whole of it and `ClickSlop` and `_orbitTravel` are a
deletion. Nothing here should be built on the assumption that they stay.

**It opens as the mission against the AI, and a capture does not.** The keys now open with the
hostile side on `Commander`, reaction windows handed out, and the other side hidden until found.
The capture harness keeps every default it had. That split is deliberate and it is what stops the
change being expensive: `--ai` and `--windows` would stop meaning anything the day they became
the default of the thing they switch on, and every capture command in this file would have had to
be re-read rather than merely re-run.

**Our soldiers read against the terrain, and the fix was three changes rather than one.** The
hues went up past 70 per cent saturation, which no ground fill approaches; every body stands on a
dark contact ring supplying the shadow a blockout does not cast, and a side-coloured ring outside
that which is what carries at distance; and both rings widen once the camera is far enough back
to have switched tile detail off, which is the same threshold the tile labels already use.

**The trap in that, and it is worth the paragraph.** Raising the two side hues washed the whole
map out, because `BuildAttention` tints every tile a soldier is attending to in its own side's
colour — five soldiers on the waystation is a wash of side colour over most of the ground, and
brightening the soldier brightened the ground it was meant to stand out from. `AttentionHue` is
now a second, dimmer pair for the field alone: hue carries the side and is shared, saturation is
not. **A readout painted across the ground cannot share a constant with the thing standing on
it**, and this is the only place in the palette where a side is two colours.

**A move walks its route, and the walk is the resolution drawn over time.** Entry 040 says the
mover has not stepped until the window resolves, so by the time a walk starts the rules have
finished: every reaction is taken, the soldier is at the far end, and what moves is the picture
catching up. The route is truncated at wherever the unit actually ended up, so a reaction that
dropped it part way is drawn stopping there rather than walking on. The remaining route is drawn
ahead of it in the committed colour with its tick labels — the same line the reaction options were
quoted against, running out from under the soldier's feet. Seven metres a second, capped at 1.6
seconds — both superseded on `view/aside`, which is ten and no cap.

**Two things the walk needed that were not obvious.** The unit rings moved out of the overlay mesh
into the bodies mesh, because a ring left in the overlay stays on the tile the soldier set off
from; and `DrawUnitLabels` reads the walk as well, because a name hanging over the destination
while the soldier is half way there is the map disagreeing with itself. `BattleView.RebuildBodies`
exists so a walking frame costs seven bodies and not a sight sweep.

**Only our side's moves walk, and one of theirs.** A hostile move that opened a reaction window is
walked, because the window carries its steps and the sandbox is holding the resolution. A hostile
move nobody could have reacted to opens no window, is resumed past by `SkipEmptyWindows`, and
jumps. Making all of them walk needs two things from Core and neither is available here — a turn
that yields per order, and the path each move walked. Written up for Core in entry 066 rather than
worked around.

**The instruments are in a `Window` of their own**, built closed, opened by `I` or
`--instruments`, hidden rather than freed when it is closed so the split between the two halves of
the HUD is decided in one place. `BattleHud` now has two entry points and holds no canvas of its
own; **both are handed the same `SandboxFrame` in the same call**, which is the condition the brief
attached to splitting the HUD at all — a second surface redrawn on its own schedule is the first
chance this code has ever had to show two moments at once, and it cannot.

**Where the line fell, and it is not where the brief's prose put it.** The brief named the legend
as moving and also gave the test — *would a player who never presses `O` want it*. The two
disagree, and the test wins: a player wants to know how to move and how to look and does not want
to know how to hand the hostile side to the AI. So the legend splits along the seam it already had
for reasons of width, two ranks staying and the third going. What else moved is the mode line, and
the AI's orders block.

**The orders readout is no longer gated on `--omniscient` as well.** Entry 023 made it an
instrument and it still is; what changed is that there is now a window which is nothing but
instruments, so the gate can be *being in it*. Two gates would have meant that reading the AI's
reasoning cost a change to the map — pressing `O` is exactly the thing that stops you seeing what
a player would have seen — and separating those two is most of what the second window is for.

**`--shot` captures the game, and the second window is written beside it.** The decision the brief
asked for, and there was one answer available: every capture command in this file names a file and
means the picture of the game, so a flag that quietly changed which window a path referred to
would rewrite the meaning of all of them. With `--instruments` on the line as well, the instruments
window goes to the same name with `.instruments` before the extension.

**One bug found and not introduced by this work.** The instruments window's mode line ran off its
right edge on the first attempt, which is the legend's failure from the key remap happening again
in a narrower box. It is two lines now — which battle, and which switches — and the window opens
at 1120 by 620 because the widest orders line is about 880 pixels and a window sized to fit
exactly is a window that is already broken.

**The pinned scene did not change.** The bottom edge lost a legend line and the top block lost the
mode line, so `--scenario compound --omniscient --zoom 30 --look 0,0 --yaw 1` has to be re-pinned
against a picture taken after this — but nothing captured after the key remap and before this
differs in the world above the readouts, and three runs of the pinned command during this work
produced one hash.

---

## What landed on `view/camera-keys`

The user asked for standard camera controls before the play-through, and the brief above named
the five keys that had to move. What was decided while doing it, since the brief left the
destinations open:

- **The storey pair did not have to be invented.** `PageUp` and `PageDown` already changed storey
  — they were an undocumented alias beside `Q`/`E` — so the remap is a deletion there rather than
  a new binding, and the pair the brief wanted to keep as a pair was already one. It is now the
  only binding, and it is in both tables where it never was before.
- **The three singletons went to `J`, `K` and `L`, next to `H`.** `H` hands the hostile side to
  the AI and did not move, so `J` gives it one turn, `K` turns on answering windows by hand, and
  `L` calls a contact in. Four adjacent keys under the right hand, and all four are *who is
  deciding, and who gets told* — which is a group a person can learn as a group. `L` for **c-a-l-l
  it in** is the only one of the four with a mnemonic and it is the one that needed it least.
- **`,` and `.` still turn the camera.** They cost one `or` in a switch and they are what anybody
  who has used the sandbox already has in their hands. The tables name `Q`/`E`.

**The legend was already broken and this is what found it.** One line of keys along the bottom
edge ran off the right of a 1600-wide viewport, and had been doing so for long enough that it is
in every capture in the repository. Nobody noticed because the keys that fall off the end are the
ones nobody has learned — which is the failure mode of a legend, and the reason it is worth saying
out loud. It is three lines now, split into where you are looking, what the soldier does, and what
the run is set to, and `LegendLines` is the one figure the stack above it reads so the two cannot
drift apart. Splitting by purpose rather than by width also means each line is complete on its own.

**No script step moved.** `--layer`, `--ai-turn`, `--shout`, `--windows` and `--yaw` are the
surface the keys call (entry 049), so every capture command in this file still means what it
said. Two files changed: `HexSandbox.cs` for the switch and `BattleHud.cs` for the legend.

**The pinned scene does change, and only along the bottom edge.** A legend two lines taller is
drawn in every capture, so the zero-changed-pixel comparison in **Seeing it** has to be re-pinned
against a picture taken after this — the world above it is untouched.

---

## What landed on `view/export`

Entry 055 asked for it and entry 056 records what it cost. **Shipping it** above is the whole of
the result — the command, the two files it produces, the differences between the exported harness
and the editor one, and how to put the environment back on a machine that has never had it. Three
things about the shape of the change, which the section itself does not stop to say:

- **The repository gained one tracked file and lost a line from `.gitignore`.**
  `game/export_presets.cfg` is committed on purpose, which is why `game/export_presets.cfg` is no
  longer ignored: Master runs the export with no View session awake, and a preset it would have to
  recreate by hand is not a job it can run. `build/` took the ignored line's place.
- **`game/project.godot` gained `dotnet/project/solution_directory`.** That is the one edit to a
  file that was not new, and it is load-bearing rather than tidy — without it the export writes an
  executable with no .NET assemblies in it and exits 0. **Shipping it** says how that failure
  looks, because the way it looks is the trap.
- **Nothing in `game/scripts/` changed at all.** The capture harness, the script steps and the
  scale contract were exported as they stood and came out identical to the byte. The export is a
  packaging job, and it stayed one.

---

## What landed on `view/greybox`

Entry 053 is the reasoning; this is the shape, and the five decisions the brief asked to be
settled before writing much.

- **The picture shows our side's knowledge and nothing else, and opens that way.** A hostile is a
  body while somebody of ours has eyes on it, a see-through standing body at its marker with its
  credence otherwise, and nothing at all before anybody has heard a thing. `SandboxFrame.Knowledge`
  is the list — `Tactician.Known` for each of ours, merged by keeping the best any of them holds —
  and `SandboxFrame.Sees` is the one question the view, the HUD and the cursor ask, so there is no
  second place a hostile can leak through. What the enemy holds on *us* is drawn in both modes,
  because section 07 of the design doc names it as the one thing of theirs a player sees. `O` or
  `--omniscient` puts everything back, the status line says which is on, and the orders readout
  prints only when it is: it is the enemy's mind, and entry 023 says why it stays as an instrument.
- **One engine unit is one metre, and `SandboxScale` is one static layout and two axis
  conversions.** The pixels layout is gone. The class stays because entry 005 is the argument for
  the place existing: the layout the battle is given is built there from a constant and nothing
  that knows about the camera can build one. It also owns the sign of Z, so a mirror-image map
  cannot be introduced from a call site.
- **Storeys above the one being looked at are ghosted, not cut away.** Solid at or below, drawn at
  sixteen per cent above, so a roof says there is a roof without hiding the room. Cutting away
  loses the tower and the ridge from every picture of the ground; the flat view drew nothing and
  lost the soldiers standing on them. PgUp/PgDn and `--layer` still choose the storey, and it is the
  storey the cursor picks on and the sight sweep runs over.
- **The camera is pitched at 55 degrees and its yaw snaps to the six hex bearings.** `Q` and `E`
  turn it, `--yaw N` sets it, and it opens looking north so up the screen is up the map the way the
  flat view had it. Distance is the zoom — `--zoom N` is metres back, `LegibleAt` is 70 of them —
  and the camera never animates, because a capture has to land on the same frame every run.
  **Two halves of this were overruled by the first play-through** and the section on
  `view/playable` above is what stands: the yaw is free and rests on the bearings rather than
  snapping to them, and turning is animated. The determinism the clause was protecting is intact
  and is now kept by a switch instead — a capture starts no animation at all.
- **A 3D capture is byte-deterministic on this machine**, with 3D antialiasing and shadows on. Two
  runs of `--fit` on the first day produced identical files, and every capture since has. So the
  zero-changed-pixel refactor test survives the move; **the pinned scene changes** — see Seeing it.

**Readouts on the ground are tinted hexes, not shapes.** The attention field asks `AttentionOn`
per tile and scales it by the range term the look-gain uses; the held arc asks `AngleOffDegrees`
per tile out to `MaxRange`, brighter inside `OptimalRange`. A flat disc vanishes under a ridge and
floats over a hollow; a tint follows the ground, and it is the rules' own answer per place. The
soldiers are cylinders — a slab, prone — at `StanceProfile`'s heights, with a bar at eye height for
the facing and a ring on the ground for whoever is up. Walls run from `WallBaseHeight` to
`WallTopHeight`, the two figures the sight trace uses, with entry 049's hue and a thickness in
place of the weight. Text is projected: every label the map carries is painted on a flat canvas
over the picture at a fixed point size, which is the lesson about labels in hex radii kept.

**What survived exactly as the brief said it would.** The named actions on `HexSandbox`, the
script, the capture, the frame, the HUD, the scenario, and the figures-not-names rule. `BattleHud`
needed a line saying the mode, the cursor going through the frame, `?` slots in the turn order, and
*somebody unseen* on the exposure line; nothing else.

**The territory question, answered for Master.** Presentation is `BattleView.cs` and
`MeshBuilder.cs`, 1,032 lines. Interface is `BattleHud.cs`, 974. The middle — the node, the camera,
the geometry, the scale, the frame, the palette, the capture, the script, the scenario, the canvas
— is 2,420, and `HexSandbox.cs` alone is the largest file in the directory. The middle grew; it did
not shrink or acquire an owner. The paths divide no better than they did at entry 014.

---

## What landed on `view/mission-file`

Entry 052 is the reasoning; this is the shape.

- **`SandboxScenario` is a name.** `MissionLibrary.Load` reads the file, `Mission.Begin` hands
  back a battle deployed, objectives set and started, and nothing in `game/` knows where anybody
  stands on the waystation. The compound stays as a bare map with hand-placed soldiers, because
  it is the fixture captures are diffed against and the case that keeps a map with no mission
  legal.
- **One of the six briefing parts is on screen and five are behind `M`.** The task is the only
  one that is a sentence about what to do next. The other five are what the squad was told before
  it went, which is a page and not a status line.
- **The sandbox applies the mission's clock and says so** — `round 31/30    out of time`. The
  rules have no clock (entry 047), so this is a view enforcing a content figure; it stops the
  turns and deliberately invents no verdict, because a made-up `Abandoned` would be a rule in
  `game/`.
- **Named ground is labelled on the map**, from `Mission.Places`. Same argument as the exit: a
  place a briefing names and a player cannot find is a name and not a place.

**One row of the audit below is a gap rather than blocked, and it is the last one.** Entry 012's
second item: the scorer charges a shot for what it announces, so the player sees the price and
not the bill. `AwarenessTracker.WouldAnnounce(shooter, from, weapon, at)` exists (entry 033) and
hands back an `Announcement` per enemy, in the same shape as `WouldHear` — which the cursor line
already prints for a route. It is the shot line growing the clause the cursor line has, it is
half a day, and **the names go on screen and the figures do not**, for the reason
`BattleHud.NoiseLine` gives. Do it before the greybox or during it; it is the same readout either
way.


---

## What landed on `view/scripted-capture`, so nobody re-derives it

Entry 049 is the reasoning; this is the shape.

- **The command line is a list of things a person could have done**, in the order typed.
  `SandboxScript` parses, `HexSandbox.Perform` dispatches, and **every step calls the same method
  the matching key calls**. That is the constraint worth keeping: a script that could reach
  `Battle` directly would be a way for a picture to show a state the keyboard cannot reach.
  Adding an action means adding a method, a key and a case — three places, on purpose.
- **A reaction window can be answered by hand**, from either side of it. `K` or `--windows` turns
  it on; a move then becomes `Commit`, a pause, and `Resolve`, and a hostile turn goes to a
  `Commander` built with `WindowAnswer.HandedOut`. `HexSandbox.Open` is the one question the rest
  of the code asks, because from the interface's side the two cases are identical.
- **Windows with no offers are skipped**, in `SkipEmptyWindows` — `SkipUnanswerableWindows` since
  brief six, which skips windows with no offers *of ours* too. Core stops at every window when
  it is handing them out and is right to; a screen that stopped to ask a question with no answers
  in it would stop twice a turn on this map.
- **The committed route is drawn** while a window is open, with the tick each step lands on,
  because the mover has paid for a walk it has not taken and the map is otherwise lying.
- **Walls and ground take their look from their figures, never from their id.** Entry 038 asked
  for the decision and entry 049 made it. All six built-in wall profiles come out at the colour
  and weight the old table gave them.
- **The sandbox has an objective**, so a battle on the waystation can end. `Withdrawal` to the
  cottages, nobody above `Searching`, which is the map header as rules.

---

## The interface audit

*Done on `view/interface-audit`, and closed against on `view/interface-readouts`. Contract 2 says
the view and the AI read one query surface, and the build order's rule is sharper: **if the AI
needs information the interface cannot show, the interface is wrong**. This is that check, run
against `Tactician` — the scorer the AI ranks every action by.*

**Since brief one the lines the tables name are places, not lines.** Nothing was dropped and every
verdict stands; read the third column through this: the **shot line** and **worth line** are the
target's `HIT` headline and the terms docked while aiming, the **bill line** is in that dock too; the
**seen line** is each contact's tag under held `Ctrl`; the **alarm line** is under the soldier's
points bar, with the bar they act from under `Ctrl`; the **reserve line** is the bar itself and the
ground's band edges, with the arc and the shout under `Ctrl`; the **posture line** is under `Ctrl` at
the soldier; and the **cursor line** is the tag beside the tile. Entry 093.

The tables below are organised by the four terms of an `Appraisal`, because that is how the AI
reasons and therefore what the interface has to be able to explain. Verdicts:

| | |
|---|---|
| **shown** | on screen, exactly, and the player can act on it |
| **coarse** | on screen as a rung rather than a number, deliberately, per contract 3 |
| **gap** | the AI weighs it, the player cannot see it, and nothing prevents fixing it |
| **blocked** | ditto, but something does — the blocker is named |

### Harm — what a shot achieves

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| whether the shot is possible at all | `ShotPlan.CanFire` / `Refusal` | shot line, with the reason | shown |
| chance to hit | `ShotPlan.HitChance` | shot line | shown |
| what it costs this soldier | `ShotPlan.ApCost` | shot line, with the list price when they differ | shown |
| how much survives the angle | `ShotPlan.GlancingFactor` | shot line | shown |
| which plates it can reach | `ShotPlan.Aspects` + `Protection` | shot line, share and stock per face | shown |
| vitality it actually takes off | `Gunnery.Expect().Vitality` | worth line | shown |
| plate worn through | `Expect().PlateStripped` | worth line | shown |
| shield soaked | `Expect().ShieldStripped` | worth line | shown |
| chance it puts them down | `Expect().DownChance` | worth line | shown |
| how much soldier is there to remove | `Target.Stats.Vitality` | map label, current over maximum | shown |
| distance, cover, exposure | `SightResult` | cursor line, in metres and per cent | shown |
| where in the weapon's range that falls | `WeaponProfile.OptimalRange` / `MaxRange` | cursor line names the band and the long-range factor; status line carries the bands | shown |
| the bonus for having the arc already held | `OverwatchArc.AimBonus` | reserve line | shown |
| who the shot gives you away to | `Battle.WouldAnnounce(plan)` | bill line, by name; the unfound as *somebody unseen*; marks on the map | shown, less the target's relay — entry 086 |

The four `Expect` rows were the audit's clearest single finding and were closed while it was
being written. Everything the shot line said was true and none of it was what the AI ranks by:
`ShotPlan.ExpectedDamage` is damage arriving at the plate, and a beam landing squarely on a full
shield reads well there and achieves nothing. The player was being shown the trap the core doc
calls the easiest mistake in the codebase, and being left to do the arithmetic that avoids it.

The maximum-vitality row looked cosmetic and was not. The scorer's removal bonus is priced
against the *maximum* — a kill shot on a soldier with seven points left scores a whole soldier of
twenty — so the first time the AI's orders were printed, a shot worth 22.5 sat beside a label
that said 7, and the arithmetic could not be checked from the screen.

### Spared — what a posture keeps off you

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| who this soldier is taking seriously | `Tactician.Known` | seen line — in view with distance, or believed at a marker with credence | shown |
| the worst one shot each could do to you | `PlanThreat` per threat and mode | seen line, worth, mode and hit chance | shown |
| how likely they are to shoot at all | `Awareness.ReadoutFor(them, you).State` | alarm line, as a rung — and since entry 021 the scorer reads the same rung | coarse, on both sides |
| the bar they act from | `Model.Threshold(UtilityModel.ActsOn)` | alarm line, named | shown |
| what a stance or a turn costs | `MovementCosts.ChangeStance` / `TurnInPlace` | posture line, for each of the three keys | shown |
| what the whole trade comes to | `Tactics.AppraisePosture` | posture line, score and every term | shown |

**The audit's real find was in this table.** `Tactician.Aimed` read how much the enemy had
detected you as a raw certainty, and contract 3 says that number is blurred to a rung on purpose.
So the appraisal of a posture could not be displayed without leaking it — and, worse the other
way round, the AI was reading a figure its own soldier had no way of knowing, which is the one
thing `Tactician`'s own doc comment promises it never does. Written up as entry 011 and resolved
by entry 021: the scorer now reads the rung the interface shows, a test pins that two certainties
on one rung score the same, and the posture line prints the whole appraisal.

It is worth keeping clear which of the two problems mattered. The display leak was small — you
would have to invert an aggregate to recover the number. The AI reading it was not small: it was
a soldier who knew exactly how spotted they were, in a game whose whole subject is not knowing.
The interface audit found it and Core did not, which is contract 2 paying for itself.

### Prospect — what an action sets up

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| how much attention a place has | `Awareness.AttentionOn(pose, node)` | cursor line, exactly | shown |
| how much is still left to learn about a contact | own `Detection` against `Threshold(Engaged)` | seen line, per contact, exactly | shown |
| the shot a new facing would open | `Tactician.BestShot` from an untaken pose | posture lines — it is the *prospect* term, scaled by attention and by what is left to learn | shown |
| who would hear you call it in | `Awareness.Earshot` | reserve line, by name — and `L` calls it in | shown |
| how much survives being passed on | `AwarenessModel.RelayFraction` | reserve line, beside the names | shown |

The attention row was worth closing on its own. The watch cone on the map used to answer this
question as a yes or a no; the model does not — a place is attended to fully, at the corner of
the eye, or barely, and the gap between the last two is the entire reason flanking works. The
cone's *range* was a lie as well, and blocked by entry 006 where its *resolution* never had been;
nobody had noticed the two were separate problems. Both are closed now: the cone is a graded
field out to the sight range, and entry 035 says how.

The second row was open the longest and the question was never how to format it. Your own
soldier's certainty about an enemy is neither of the two cases contract 3 originally named — it
is not your exposure and it is not the enemy's alarm. **Entry 042 settled it**: the split is
*whose knowledge it is* rather than what it is about, so your side's knowledge is yours in both
directions, and blurring what your own soldier has worked out would be fog about yourself, which
contract 3 already rejects for exposure in as many words. The seen line quotes it against
`Threshold(Engaged)` — and it can read over 100, because certainty banks margin up to `Ceiling`
and that margin is what a contact survives decay on.

Shouting was the odd row and is closed. `Tactician.AppraiseWord` scored it and
`ReactionAction.Shout` used it in a window, but no `Battle` action let anybody do it on their own
turn — so the interface could not offer it and `Commander` could not generate it, which is entry
012's first item. `Battle.Shout` exists now; `L` calls a contact in and the reserve line says who
would hear it. **Item 2 of entry 012 is closed by brief four**, with one hole in it: the bill line
under the shot names who taking it would tell, through `Battle.WouldAnnounce` — the call the scorer
charges `GivenAway` by — and the target's relay to its own side is not in that preview. Entry 086.

### Spent — what it costs

| The AI weighs | The query | Where the interface shows it | |
|---|---|---|---|
| what a move costs from here | `Reachable` / `CostTo` | tile labels and the cursor line | shown |
| what is left to react with | `Unit.Reserve`, `ReserveFraction`, `ReserveFloor` | reserve line, including what stopping now would bank | shown |
| what arc is being held | `Unit.Held`, `HeldArc` | reserve line and the wedge on the map | shown |
| a point of anything, in vitality | `UtilityModel` | nowhere | deliberate — see below |

`UtilityModel`'s dials are the only things in this audit that are *right* to withhold on grounds
other than contract 3. They are not facts about the world; they are what one side's judgement
happens to prefer, and showing a player the exchange rates their opponent scores by is showing
them the opponent's mind rather than the battlefield. The scores those dials produce are a
different matter and belong on screen, which is what the worth line does.

### The orders readout is the opponent's mind, and is shown anyway

The block prints every turn `Commander` has taken since the player last acted, one line per
`Order`, with `Worth` and `Opens` each broken into their terms and the `Score` beside them. That
is exactly what entry 009 asked for and exactly what the paragraph above says a shipped interface
must not do. Both are right: the sandbox exists to check the AI, an AI can only be checked by
somebody who can see what it thought, and the readout is an instrument in the same sense the seed
on the command line is. `BattleHud.TurnLines` says so in its remarks, and any interface built for
a player rather than for a tester drops it.

**It is in the instruments window now, and dropping it is a thing you can do by closing that
window.** The audit above was written when the readout was a block along the bottom of the same
screen as the map, gated on `--omniscient`; `view/playable` moved it and took the second gate
away, because reading the AI's reasoning should not cost a change to the picture. What the
paragraph above argued for is unchanged and is now demonstrable rather than asserted: a shipped
interface is what the main view shows with the window shut.

One of its terms could not be shown to a player even in principle. A hostile's `Prospect` is
scaled by how much that hostile has already worked out about the soldier it is turning towards —
its own contact file, which is fine for the AI and is the number contract 3 blurs for us. Noted
in entry 023 so that nobody later mistakes the readout for a precedent.

### What is not in the scorer yet, and is missing from both

The audit named two omissions the turn planner would hit first. Both were also interface gaps,
and saying so was the point of the exercise:

- **Firing gives you away and nothing prices it for the player.** No longer, mostly: the bill line
  names who the shot would tell, from `Battle.WouldAnnounce(plan)`, which is the call the scorer's
  `GivenAway` is priced by — so what the player reads and what the AI charges are one answer. The
  hole is the same on both sides of contract 2: neither includes what the target passes on to its
  own side, and measured on the waystation that relay tells somebody the preview did not name.
  Brief four, and entry 086 for Core.
- **A move's noise was computed and thrown away.** No longer: `Battle.Loudness` is public and is
  the figure `Move` then charges, `AwarenessTracker.WouldHear` says who would hear it, and the
  cursor line prints both — the loudness and the names — for any route the active soldier could
  take. Closed by entry 021. Only the names are printed; the figures behind them are movements in
  the enemy's contact file, and `BattleHud.NoiseLine` says why that stays a rung.

---

## Two territories, one doc — and one territory, settled twice

Presentation and interface are different problems:

- **Presentation** is drawing, cameras, input plumbing, and eventually animation. It consumes
  Core. It lives in `BattleView.cs`, with `MeshBuilder.cs` under it.
- **Interface** is what the player is allowed to know and how they ask for it. It *constrains*
  Core — the design doc's build order puts it plainly: if the AI needs information the interface
  cannot show, the interface is wrong. Section 06 ("What it hands the interface") and section 07
  ("Asymmetric information, deliberately") are interface design as much as rules design. It lives
  in `BattleHud.cs`.

They shared this doc because they once shared a single 705-line file. They no longer do:

| | |
|---|---|
| `HexSandbox.cs` | the Godot node — lifecycle, the scene furniture, the actions, input, handing turns to the AI, gathering what our side knows, and assembling a frame |
| `SandboxScenario.cs` | which mission, by name — or, for the compound fixture, which map and who is on it |
| `SandboxScript.cs` | the command line as a list of things a person could have done, in order |
| `SandboxScale.cs` | the one layout the rules are given, and the axis mapping into the scene |
| `SandboxCamera.cs` | where the map is looked at from: a focus, a distance, one of six bearings |
| `SandboxGeometry.cs` | where things sit in the scene — outlines at floor height, node centres, picking by ray |
| `SandboxFrame.cs` | one moment's answers, assembled once and read by both halves — including what our side knows of the other |
| `MeshBuilder.cs` | coloured triangles into one mesh: prisms, slabs, cylinders, ribbons |
| `SandboxCanvas.cs` | a flat surface that draws what it is handed; there are three — the map's labels, the player's readouts, and the instruments window's |
| `BattleView.cs` | **presentation** — ground, walls, links, the route, the fields and arcs, ghosts, bodies, and the map's labels |
| `BattleHud.cs` | **interface** — two surfaces from one frame: the player's readouts over the map, and the instruments in their own window |
| `SandboxPalette.cs` | colours and the two materials, shared because a side is one colour in both halves |
| `SandboxCapture.cs` | render some frames, write a PNG, quit |

`BattleView` and `BattleHud` are separate classes rather than partials of the node deliberately:
partials would have kept every private field reachable from both, which is a path boundary with
no boundary behind it. Each takes a `SandboxFrame` and its own surface and can reach nothing
else — the view has a `Node3D` and a canvas for labels, the HUD a canvas of its own.

**Whether that boundary makes two territories was asked in entry 013, answered in entry 014, and
looked at again by the greybox as `../map.md` said it would be.** It does not, and the second look
made it plainer: the middle is 2,420 lines against 1,032 and 974 for the halves, and the node is
the largest file in the directory. A territory is defined by paths, and the paths do not divide.
Entry 053 records the count.

---

## Gotchas

- **Godot defines its own `Side` enum, and its own `Environment`.** `game/` files need
  `using Side = Hexcom.Core.Units.Side;`. `Environment` resolves to Godot's while `using Godot;`
  is in scope, which is what the world environment wants and not what `System.Environment` is.
- **The sandbox needs Godot 4.7 .NET edition**, not the plain build. If your Godot is a different
  4.x, change the `Godot.NET.Sdk` version in `game/Hexcom.Game.csproj` to match.
- **Nothing on this machine is called `godot`.** See **Seeing it**. A session that types the
  short name, gets *command not found* and concludes the engine is missing has been misled by a
  shell, not by the install.
- **`.uid` files are tracked, and Godot writes them for you — but only the editor does.** Running
  the scene does not. Adding a script under `game/scripts/` leaves the tree one file short until
  somebody opens the project; a session with no editor open can make Godot write them with
  `--editor --headless --quit-after 200`, which is how the greybox's two arrived. Commit them with
  the script.
- **Build before you run.** Godot loads the assembly from `game/.godot/mono/temp/bin/Debug/`, and
  a scene launched before `dotnet build Hexcom.sln` fails with *"Cannot instantiate C# script"* —
  which reads like a broken scene file and is not one.
- **A picture is not proof of a rules change.** Sight and cover are scale-invariant (entry 005),
  so the opening frame is byte-identical before and after the world-scale fix. What changed was
  detection, which no still image shows. When a change is about distance, measure it; when it is
  about layout, capture it.
- **A picture is exactly the proof of a drawing change, and the 3D render is deterministic.** Two
  runs of the same command produce the same file, with MSAA and shadows on, so a refactor of
  drawing code can still be held to *zero* changed pixels against the commit before it. The flat
  view's history of catching a 546-pixel arc that way is why this was checked on the first day.
  **Diff the capture against the previous commit whenever you move drawing code, and pin the
  scene when you do.** The pinned scene is now
  `--scenario compound --omniscient --zoom 30 --look 0,0 --yaw 1`: omniscient because the fixture
  is checked with every soldier drawn, and the yaw said because a default is a thing that moves.
  Nothing captured before the greybox diffs against anything captured after it, nothing captured
  before the key remap diffs against anything after it — the legend grew from one line to three —
  and nothing captured before `view/playable` diffs against anything after it either: the legend
  went back down to two, the mode line left the top block, and every soldier gained two rings.
  **`view/gestures` breaks it along the bottom edge only**: the legend is three lines again, and
  measured against master everything above row 822 of the pinned scene is unchanged by a pixel.
  **`view/order-strip` breaks it in the strip only**: the round mark pushes Vance down a row, and
  the whole diff is x 1410–1580, y 142–182.
  **`view/readouts-in-place` breaks it everywhere**: the reach is an edge rather than a fill, so
  the ground changes under the whole move range, and the panel, the soldier's bar and the legend all
  moved. Nothing captured before it diffs against anything after it; two runs of the pinned command
  after it hash the same. **And `--fit` frames differently**: `SandboxCamera.Fit` looks past the map's
  middle and stands further back.
  **`--aside` breaks none of this and that was measured, not assumed** — a capture on the left
  monitor and the same one where Windows put it are byte-identical. The one break is narrower than
  it looks: a capture taken with `--instruments` before the subwindow fix has the instruments panel
  drawn over the map and diffs against every one taken after it. A capture without that flag does
  not.
- **Animation cannot break the determinism, and the reason is worth keeping straight.** It is not
  that the animations settle quickly. It is that a run with `--shot` on it never starts one — see
  `HexSandbox.Animate`. A change that made any animation conditional on something other than that
  flag would put the whole harness back in play, so if a walk or a turn ever has to run during a
  capture, the thing to change is the capture and not the flag.
- **A readout painted across the ground may not share a colour constant with the thing standing
  on it.** The attention field tints every tile a soldier attends to in that soldier's side
  colour, so on the waystation it is a wash over most of the map. Raising the side hues to make
  the bodies read washed the terrain out with them, and a body that reads well against ground it
  has itself repainted has not been fixed. `SandboxPalette.AttentionHue` is the second, dimmer
  pair; hue carries the side and is shared, saturation is not. It is the only place in the palette
  where a side is two colours, and the day a third readout wants a side colour it is the question
  to ask first.
- **The bodies mesh is rebuilt on its own, and the unit rings live in it rather than the
  overlay.** A walk redraws the soldiers every frame it runs for and the full rebuild is a sight
  sweep behind it, so `BattleView.RebuildBodies` exists. The rings had to move for it: a ring left
  in the overlay stays on the tile the soldier set off from while the soldier walks away. Anything
  else that belongs to a body rather than to a place belongs in that mesh for the same reason.
- **Three things read the walk and all three have to.** `BuildBodies` draws the body at it,
  `DrawUnitLabels` puts the name over it, and the HUD hangs the soldier's readouts from the same
  point. Only the first is obvious, and with only the first done the name hangs over the destination
  while the soldier is half way there — the map disagreeing with itself, which is exactly what a
  single frame is supposed to prevent. The last two go through `BattleView.Crown`, which is the one
  place that reads it; anything else that hangs from a soldier asks it too.
- **A readout on the map is placed in pixels from `Crown`, never in metres.** The name sits just
  above that point and a hostile's rung just below it; the soldier's bar stacks upwards over the name,
  a contact's terms downwards under the rung — further when the bill's mark is there — and the shot's
  headline over the target's name. Placed in metres, a tag lands on the name at any distance a rifle
  shot is taken from, which is what the bill's glyphs found first. A tag whose point is off the
  screen is not drawn rather than pulled in to an edge, where it would be attached to nothing.
- **Nothing multiplies by `ReserveFraction`.** The ladder asks `ReactionModel.Banked`, once per
  leftover, because the floor makes the reserve a step and a product smooths it. The panel did the
  multiplication inline for months (entry 067).
- **A `Window` node is not an operating-system window until the project says so.** Godot 4 defaults
  `display/window/subwindows/embed_subwindows` to true, which draws a `Window` *inside* the parent
  viewport. The instruments window shipped like that and nobody noticed for a whole increment: it
  could not be dragged to another monitor, which is the only reason it is a window, and every
  capture taken with `--instruments` had it painted over the map. `project.godot` sets the setting
  false. **A capture of the second window is not a check that it is a window** — an embedded one
  has its own viewport texture and photographs perfectly.
- **Godot's screen coordinates are not Windows'.** `ScreenGetPosition` reports unscaled physical
  pixels with the origin moved to the leftmost screen, so this machine's left monitor is at X
  −1920 in Windows and at X 0 in Godot. The *ordering* survives, which is all `--aside` needs, but
  a position printed by one and a position printed by the other are different numbers for the same
  window. `SandboxAside` prints the one Godot believes.
- **A window sized to fit its widest line is already broken.** The instruments window's mode line
  ran off its right edge on the first attempt, which is the legend's failure of the key remap in a
  narrower box. Anything added to that window has to be checked against `InstrumentsSize`, and the
  fix when it does not fit is to split the line by purpose rather than to widen the window again.
- **The readouts are drawn over the map, not beside it.** Every HUD block and tag sits on a plate
  for that reason, and anything added has to assume there is a tile-cost label underneath — because
  there is. The top block is only what has no place on the map — the mission, the clock, the weapon,
  the storey — and **nothing goes back into it**: a figure about a thing hangs from the thing (brief
  one, entry 093). The bottom-left block is what happened while it was not your go, and the
  right-edge dock is the shot's terms while aiming.
- **The bottom block is *since you last acted*, not a log.** It is replaced whenever the enemy
  gets a go after something you did, so if two of yours are adjacent in the initiative order, the
  second one's pass leaves the block untouched — nothing hostile happened in between. Read it as
  "what they did about that", never as a history. And it prints only when the picture is
  omniscient: it is the enemy's mind.
- **`Battle` does not stop when a side is gone.** The survivors keep taking turns, so anything
  that loops on the hostile side being up has to check `IsDecided` or it never returns.
  `HexSandbox.Settle` does.
- **There is one layout and the camera cannot reach it.** `SandboxScale.World` is a static built
  from a constant; `SandboxCamera` owns a distance and a bearing and rewrites a `Camera3D`. The
  day a zoom factor gets multiplied into a layout is entry 002 again, and the shape of the code is
  what makes that a thing somebody has to do on purpose.
- **Text is projected, everything else is built.** A label is `Camera3D.UnprojectPosition` of a
  scene point, painted on the label canvas at a point size, so it stays legible at any distance
  and has to be redrawn on every camera move. Meshes are rebuilt on every action and never on a
  camera move. If a label and a shape disagree, the frame they were drawn from does not — look at
  which of the two redraws was missed.
- **Transparent meshes are sorted by distance, and all of ours are at the origin.** The ghosted
  storeys and the readouts would draw in whichever order the engine picked, and sometimes a
  readout vanished under a ghosted roof. `SandboxPalette.ClearBehind` carries a render priority so
  the ghosts go first, whatever the distance. Within one mesh, triangles draw in the order they
  were added, which is what lets several tints on one hex composite — so add the unseen wash
  before the fields and the outlines after them.
- **The cursor picks on the storey being looked at and nothing else.** The ray is met with each
  floor height on that storey; a roof above is transparent to it and a floor below is not
  reached. So on the ground storey you cannot click the roof, and on the roof you cannot click the
  room under it. That is what PgUp/PgDn are for.
- **Attention is a tint per tile and costs a query per tile.** Seven soldiers within 45 metres
  of most of the waystation is about eight thousand `AttentionOn` calls a rebuild, which is
  cheap, and eight thousand quads, which is cheap. It would stop being cheap at a hundred
  soldiers, at which point the field should sample rings again.
- **A switch over somebody else's enum wants its default to be a sentence, not a guess.**
  `BattleHud.Describe(Order)` ended in a catch-all that read the stance, which was true of the
  only kind left over when it was written; three kinds landed with grenades and the first one the
  AI threw brought the whole frame down. Entry 049. There are two more switches over Core enums
  in that file, and neither of them is Core's problem.
- **An action lives in three places and that is on purpose.** A method on `HexSandbox`, a key in
  `HandleKey`, a case in `Perform`. The script is an argument list rather than a second input
  system, so nothing but those methods may touch `Battle` — otherwise a capture can show a state
  the keyboard cannot reach, which is the opposite of what a harness is for.
- **Space means two things, and the `AIMING` line is the only thing telling a player which.** It
  fires while an aim is up and ends the turn while one is not. That is the window's convention —
  space commits whatever is open — and it is fair only because the mode cannot be missed. Anything
  that hides or moves the `AIMING` line, or keeps an aim alive where the line is not drawn, puts a
  shot on the key a player presses to pass. It heads the docked terms now, and **the fold does not
  fold it** — `DrawTerms` keeps it and the headline whatever the fold says.
- **An aim is checked in the frame, not tidied up wherever the moment changes.** `_aim` is only a
  unit; `SandboxFrame.Aim` is that unit if the mode still makes sense — a window shut, somebody up,
  the target hostile, in play and in sight. Read `Aim`, never `AimedAt`, or an aim can outlive the
  stance change or the `O` press that made it a leak. The one place `_aim` *is* cleared on purpose
  is `AfterAction`, which is how a move or a pass drops it.
- **The right button still has a slop, and changing it costs nothing now.** `ClickSlop` tells a
  back-out from an orbit. Before brief three a misread drag was a shot nobody meant; now it is an
  aim dropped. If it ever becomes a shot again — any binding that spends points on a right *click* —
  the slop is back to being the only thing between a camera turn and an irreversible action.
- **A preview of what the enemy learns iterates every enemy, found or not.** `WouldHear`,
  `WouldAnnounce` and `Earshot` of a hostile are all about the whole other side, which is right for
  the AI and a leak on a screen. Anything that prints their learners goes through
  `SandboxFrame.Names`. The move line did not, for as long as it existed.
- **The shot's bill is checked against the contact files, and that read is an instrument.**
  `HexSandbox.HeldOn` reads each enemy's exact certainty on the shooter, which contract 3 keeps off
  the picture. It exists so a script step can report who a shot told; it must never feed a readout.
- **Skipping a window is placing its recommendations and then resuming, never just resuming.**
  `Commander.Resume` and `Battle.Resolve` both treat what was placed as the whole answer, so a window
  resumed with nothing in it is everybody in it holding fire. That was harmless while only empty
  windows were skipped and is not now that windows the other side could answer are. Anything new
  that runs past a window — a fast-forward, a second skip — places first.
- **Every list of a window's offers goes through `Answerable`, including counts.** The readout, the
  chooser, the number keys, `Tab` and `--place` all read the filtered list; `window.Offers` is read
  directly only to decide whether a window did anything at all. A readout that counted the raw list
  would say how many hostiles have a line on the mover, named or not.
- **A window is modal, and the camera keys are the exception.** While one is open the battle is
  held still around a question, so only the answers and the camera do anything. Looking is not
  answering, and the reactor being chosen for is usually somewhere else on the map.
- **The strip counts after it filters.** `Take(6)` before `Sees` would give six bookings with the
  unfound ones blank, and the number of visible slots would say how many were hidden. Anything else
  that lists bookings filters first.
- **The account of their go is a snapshot comparison, and the snapshot is the stretch's clock.**
  `_heldBefore` is taken when control leaves our side and dropped when the stretch ends rather than
  pauses; while it is held, `AfterAction` is mid-stretch and must not clear the account or the
  banner. Keying that on `keepRecord` was the first attempt and was wrong — a turn of ours handed to
  the AI sets it too.
- **The banner never appears in a capture**, by the dwell rule, and not in a window either. Checking
  its drawing needs a change to one of those two, made and reverted — do not leave either in.
- **Counting `--pass` is a guess.** Initiative is rolled per round, so a script that passes four
  times lands on a different soldier the day anybody's roll changes. `--until NAME` is what the
  hand does anyway.

---

## Seeing it

Godot 4.7.2 .NET is installed on this machine and the scene wiring runs — that is no longer an
open question. `winget install GodotEngine.GodotEngine.Mono` puts it under
`%LOCALAPPDATA%\Microsoft\WinGet\Packages`, adds that directory to the PATH, and **makes no
`godot` alias** — the only executables there are `Godot_v4.7.2-stable_mono_win64.exe` and its
`_console` twin (entries 017 and 019). So the commands below name the executable in full, and
they run as pasted from either `bash` or PowerShell. Use the `_console` one when scripting: it
keeps stdout on the terminal, which is where the capture reports where it wrote to.

```bash
dotnet build Hexcom.sln && Godot_v4.7.2-stable_mono_win64_console --path game -- --aside
```

To capture the sandbox without anyone at the keyboard — which is how a session with no human
watching can check its own work:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --aside --shot out.png
```

`--shot-after N` waits N frames first, default 4; the first frame is drawn before the font atlas
is resident and loses every label. **Not with `--headless`** — the headless driver does not
rasterise and the capture comes back blank. `--headless --quit-after 30` is still the cheapest
way to check that the scene loads and `_Ready` survives, which catches most wiring breaks.

**A capture is deaf, so anything it is to show has to be an argument.** The run ignores the mouse
and the keyboard on purpose — the window opens under whatever the pointer was already doing, and
a capture that read it would not reproduce. Flags put back what that took away:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --aside --shot out.png --omniscient --hover 2,0 --pass 6 --ai
```

- `--hover q,r[,layer[,region]]` parks the cursor on a node, axial, the way the maps are
  authored. Everything cursor-driven — the path preview, the sight readout, the range band, the
  shot under the cursor and what it is worth — is invisible to a capture without it.
- `--pass N` hands the turn on N times before the picture. Whose turn it is decides most of the
  HUD, and the demo's first soldier carries a **power blade**, so no capture of the opening frame
  can show a rifle's readout. Without `--ai`, nobody acts during the passes — this reaches later
  soldiers, not later situations.
- `--ai` hands every hostile turn to `Commander` during the passes, so each pass is one of ours
  standing still while the other side does what it decides to. Interactively the same thing is
  `H`, and `J` gives one turn — anybody's — to the AI.
- `--omniscient` draws every soldier in play. **Without it the picture is the game**: hostiles
  nobody of ours has found are not in it. A capture checking where everybody is wants this flag;
  a capture checking what a player would see does not. Interactively it is `O`. It no longer
  governs the AI's orders readout — that moved to the instruments window and is gated on the
  window being open, which is the next flag.
- `--instruments` opens the second window and, with `--shot`, writes it beside the picture:
  `--shot out.png --instruments` produces `out.png` and `out.instruments.png`. **`--shot` always
  means the game**, so every command in this file still names the file it always named.
  Interactively it is `I`.
- `--still` turns off the camera turn and the walk for a person at the keyboard. A capture does
  not need it — nothing animates while a picture is being taken, by construction — so it is here
  for somebody watching rather than capturing.
- `--pace N` sets the walking pace in metres a second, ten by default. The default is measured
  rather than argued — `../decisions.md` entry 080 — and the flag stays so the next person to
  disagree can show it instead.
- `--edge-pan` turns on the pointer-at-the-edge push, which is **off**. Brief Zero's rider, and
  the reason is that it is the only camera gesture that runs while the hand is doing nothing.

**`--aside` puts this run's windows on the leftmost monitor, and every command above carries it.**
The user works on the centre screen of three and a window landing on it mid-thought is the most
distracting thing a session does; `../decisions.md` entry 063 is the rule and 079 is the build.
Leftmost is by position rather than by index, so it is right on any machine. **`--shot` implies
it** — a capture is always a session's — and the flag is written out anyway so that a command
without it can be read as one meant for a person. It places the instruments window too, whenever
that is opened. The exported game with no flags opens where Windows puts it, which is the user's
own screen and is correct.

**The window appears on the usual monitor for an instant before it moves.** Godot maps it while the
display server comes up, before any script is loaded, so a placement from inside the process is
always a correction. It happens in `_EnterTree`, ahead of everything else this run does, which is
as early as a script can be. **To place it with nothing to see, add Godot's own `--screen N`**
before the `--`, taking N from the index `--aside` printed — that is applied at creation. It is not
the default because an index is a fact about one machine, which is the whole reason `--aside`
measures instead. Entry 080.

**Moving the window changes no pixels, which was worth checking rather than assuming.** The pinned
command captured on the left monitor and the same command captured where Windows put it produce one
SHA-256, and so do two runs on the left monitor. So every hash in this file survives the flag, and
a capture on another screen rasterises in full rather than coming back blank the way a headless one
does.

**A capture is still, and that is a switch rather than a wait.** `HexSandbox.Animate` is false
for the whole of any run with `--shot` on it, so `--yaw N` lands on the frame it names, a
`--move` puts the soldier at the far end within the call, and two runs of one command still make
one file. The alternative — settling every animation before the shutter — would have put a
capture on a code path that had never been measured. Do not make animation conditional on
anything else; this is the one flag and everything that moves asks it.

**A map 85 metres across needs the camera told about, so five flags do that.**

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --aside --shot map.png --fit
Godot_v4.7.2-stable_mono_win64_console --path game -- --aside --shot old.png --scenario compound --omniscient --zoom 30 --look 0,0 --yaw 1
```

- `--fit` pulls back until the whole map is in one picture, working the figure out rather than
  being told it. This is the flag to reach for for a picture of the shape of a map.
- `--zoom N` puts the camera N metres back from the ground it is looking at. Past 70 the tile
  detail switches off, which is deliberate and is what the status line means by *zoomed out*;
  36 is where a battle opens.
- `--look q,r` centres on a hex instead of on whoever is up, at the floor height of the storey
  being looked at.
- `--yaw N` turns the camera to look along hex bearing N, 0 to 5; 1 is north and is the default.
- `--scenario name` picks from `SandboxScenario.All` — `waystation`, the default, or `compound`.
  A name that matches nothing gets you the default and says so in the status line, rather than a
  scene that fails to load.

Interactively it is `W` `A` `S` `D` or a middle-drag to pan, `Q` and `E` or a right-drag to turn,
the wheel or `+`/`-` to zoom, `F` for the whole map and `G` for whoever is up. The camera never
re-asks the rules anything, so none of it can change what is true — only what is on screen.

**The mouse, settled.** Right-click never fires — brief three, and *What landed on
`view/gestures`* above:

| | |
|---|---|
| middle-drag | pan |
| right-drag | turn the camera freely, to anywhere between the six bearings; no snap on release |
| right-click | back out — **on release**, and only if the pointer moved under `ClickSlop` pixels since the press; never spends a point |
| pointer near an edge | push the view that way, faster the further into the margin it goes — **off unless `--edge-pan`** |
| wheel | zoom |
| left-click | move whoever is up; on a hostile, aim; on the hostile already aimed at, fire; while aiming, the fold switch in the docked terms folds them, and anywhere else backs out and moves nobody |

A right press starts a candidate orbit either way; which of the two it turns out to have been is
not knowable until the button comes back up, which is why the back-out waits for the release —
so that turning the camera to look at a target does not drop the aim at it.

**Edge-pan is off unless it is asked for**, which is brief Zero's rider and the genre's answer: it
is the one camera gesture that fires while the hand is doing nothing, so a pointer parked near an
edge while a player reads the panel moves the map out from under what they are reading. `--edge-pan`
turns it on. When it is on it runs only while the pointer is genuinely inside the viewport — with a
second window in play the pointer spends time on another monitor, and a view that crept while
nobody was looking at it would be the worst kind of bug to find.

**The keys, in the groups the two legends use.** The player's legend is `BattleHud.PlayerKeys`
and the instruments window's is `InstrumentKeys`; this table is the same content, and they are
two copies of one list — changing one without the other is how a legend starts lying.

The first three are on screen in the main view; the last is in the instruments window, which is
where the split falls and why. The test is *would a player who never presses `O` want it* — a
player wants to know how to move and how to look, and does not want to know how to hand the
hostile side to the AI.

| Where you are looking — **player's legend** | |
|---|---|
| `W` `A` `S` `D` | pan, in screen terms — `W` moves the view up the screen whichever bearing you are on |
| `Q` / `E` | head for the previous or next hex bearing, animated; `,` and `.` still do the same |
| right-drag | turn freely, between bearings |
| wheel, `+` / `-` | zoom |
| `F` / `G` | the whole map / whoever is up |
| PgUp / PgDn | change storey |

| Orders — **player's legend** | |
|---|---|
| left-click | move, or aim at a hostile; on the one aimed at, fire |
| `1` · tab | aim at the hostile under the cursor or else the nearest · aim at the next in sight |
| space, enter | fire while aiming; end the turn while not |
| right-click, `Esc` | back out: the aim, or else the briefing |
| `P` | fold the shot's docked terms, or open them; it stays as it is left |
| tab, `1`–`9`, space | while a window is open: whose answer, change it, and run it — every answer not changed stands; only our side's reactors are offered unless the instruments window is open |

| Posture — **player's legend** | |
|---|---|
| `C` · `Z`/`X` · `V` · `B` · `T` | stance · turn on the spot · overwatch arc · arm or spring an ambush · leave the field |
| `L` | call a contact in |
| hold `Ctrl` | every figure's terms on the map at once, for as long as it is held |

`Alt` is unbound. `Ctrl` went to *everything at once*, which is the job the reference set uses a held
key for; the shot's terms needed no key, because they open while aiming (entry 089).

| What the run is set to — **instruments window** | |
|---|---|
| `H` · `J` | hand the hostile side to the AI · give it this one turn |
| `K` | answer reaction windows by hand |
| `O` · `M` · `R` | see everything · the briefing · a new battle |
| `I` | the instruments window itself — which is also how it is closed from the keyboard |

**`I` is in the window it opens, which reads like a mistake and is not.** A key that shuts a
window is discoverable from inside it; a key that opens one has to be discoverable from
somewhere, and it is here, in the README, and on the window's own close button. Whether the main
view should advertise it is one for the interface territory.

A middle-drag and the arrow keys pan as well, which is the one place two bindings survive the
remap on purpose: a person who has a hand on the mouse should not have to move it.

**The keys open on the game and a capture opens on the harness.** Interactively the hostile side
is on `Commander`, reaction windows are handed out, and the other side is hidden until found;
`H`, `K` and `O` turn each of those the other way. A capture keeps the old defaults — all three
off — so `--ai`, `--windows` and `--omniscient` still mean what they meant and every command in
this file still opens the run it was written against.

**And a capture can act.** Everything on the line that is not one of the eleven settings —
`--shot`, `--shot-after`, `--scenario`, `--ai`, `--windows`, `--omniscient`, `--instruments`,
`--still`, `--aside`, `--edge-pan`, `--pace` — is a step, run in the order it was typed, and each
one prints what it did. They are the keys under another name:

| | |
|---|---|
| `--pass [N]` · `--until NAME` | hand the turn on; or hand it on until a named soldier is up |
| `--move q,r[,l[,g]]` · `--fire NAME` | the active soldier moves or shoots — at a soldier the picture shows |
| `--aim [NAME]` · `--next-target` · `--confirm` · `--back-out` | the firing mode: `1` or a click on NAME · `Tab` · space · right-click. `--fire NAME` is `--aim NAME --confirm` for any shot the rules allow. `--aim` reports who the shot *would tell*; a shot reports who it *told*, read off the contact files, so the bill can be checked headless |
| `--stance NAME` · `--face DIR` · `--overwatch NAME\|none` | posture, facing, the arc being held |
| `--arm` · `--spring NAME` · `--shout NAME` · `--extract` | ambush, call it in, walk off the field |
| `--ai-turn` · `--hostiles ai\|hand` | give this turn to the search; give the side to it or take it back |
| `--place NAME:N` · `--resolve` | answer an open reaction window, and run it |
| `--brief` | the whole briefing on screen |
| `--details` · `--fold` | `Ctrl` held down for the rest of the run · `P` |
| `--hover node` · `--look q,r` · `--zoom N` · `--yaw N` · `--fit` · `--layer N` | the cursor, the camera, the storey |

`--until` rather than a count of passes, because initiative is rolled per round. Camera steps go
last, since anything a soldier does afterwards may pull the view to whoever is up next.

The test this was built for, and what it prints — the same line in three dimensions as in two:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --aside --shot out.png --scenario compound --omniscient   --ai --pass 3 --hostiles hand --until Watchman --overwatch narrow --until Orsini   --move 1,0 --zoom 24
```

*reactions — t15 Watchman (overwatch) snap at (0,1)@0: hit Front for 0.* One of ours moved, a
sentry holding an arc answered it, and the reaction line says what it did.

With `--windows`, a move stops at its reaction window instead and the picture can be taken with
the question still on screen — **if one of ours is offered an answer in it.** A window only the
other side could answer runs at once on its recommendations, since brief six; add `--instruments`
to stop at those too and answer for both sides. So the command above with `--windows` added moves
Orsini straight through, byte-identical to the command without it, and with `--instruments` as
well it stops with Watchman offered. `--windows --ai --omniscient --pass 30 --zoom 40` on the waystation
stopped in round 4 with the sentry committed to a 15-tick walk it has not taken, Vance offered three
answers and their scores, and the route drawn out of the sentry with the tick each step lands on.
**It no longer stops**: on brief one's base it passes all thirty with Vance down in round 8, most
likely because the mission's *told* lines (entry 092) changed what the AI does — nothing brief one
touched moves the battle. A command that stops at a window of ours wants finding again; entry 093.
`--ai --pass 16 --zoom 60` without `--omniscient` is the game's own view of the same fight two
rounds on: two hostiles as bodies with their rungs, and two nowhere at all — not on the map and,
since brief five, not in the turn order either.

---

## Shipping it

**One command, from the repository root, and what comes out is a game the user double-clicks.**
Master runs this after every round of merges with no View session awake — entry 055 — so it is
written to be pasted rather than adapted.

```bash
mkdir -p build && Godot_v4.7.2-stable_mono_win64_console --headless --path game --export-release "Windows Desktop" ../build/Hexcom.exe
```

PowerShell has no `&&`, so there it is two statements on one line:

```
New-Item -ItemType Directory -Force build > $null; Godot_v4.7.2-stable_mono_win64_console --headless --path game --export-release "Windows Desktop" ../build/Hexcom.exe
```

**What `build/` holds afterwards, and nothing else.**

| | |
|---|---|
| `Hexcom.exe` | 190 MB. The game. This is the one to double-click |
| `Hexcom.console.exe` | 50 KB. A launcher that starts the same game with stdout on the terminal — the exported twin of `Godot_v4.7.2-stable_mono_win64_console`, and the one to script with |

There is no `.pck` and no `data_Hexcom_windows_x86_64/`, because the preset sets both
`binary_format/embed_pck` and `dotnet/embed_build_outputs`. The test the brief set was a thing a
person can copy to another folder and double-click, and one file passes it outright. `build/` is
in `.gitignore`: a built game is derived exactly as a test result is, and nothing checked in is a
claim about whether the tree builds.

**Four things about that command that are findings and not guesses**, each of them checked here
rather than assumed:

- **`--headless` is right, and the export does not need the solution built first.** The exporter
  runs `dotnet publish` itself, as a step it prints. It was run against a tree with every `bin/`,
  `obj/` and `game/.godot/mono` deleted and produced a working executable. This is the opposite
  of the interactive run, which *does* need `dotnet build Hexcom.sln` first and hangs on a dialog
  without it.
- **The export path is taken relative to `game/`, not to the working directory.** `--path game`
  sets it. Hence `../build/Hexcom.exe` for a `build/` at the repository root.
- **`build/` has to exist first.** The exporter will not create it; it stops with *The given
  export path doesn't exist* and writes nothing. That is the whole reason for the `mkdir`.
- **The preset is release, and nothing wants debug.** Everything the HUD prints is drawn by the
  HUD, and everything the script steps print reaches the terminal through the console wrapper in
  a release build — the capture below reports where it wrote to, in release. A debug export would
  buy the .NET debugger and the remote-debug hook, and neither is any use to a person playing.

### The exported game is a second harness

**It honours everything after `--` exactly as the editor run does, and it draws the same
picture to the byte.** `--fit` from the executable and `--fit` from the editor produced the same
SHA-256, so the zero-changed-pixel refactor test in **Seeing it** can be run either way and a
capture taken from a build is comparable with one taken from the tree.

```bash
build/Hexcom.console.exe -- --shot out.png --fit
```

**One difference, and it will bite.** A relative `--shot` path is resolved against the
executable's own directory, not the working directory — so the line above writes
`build/out.png`, and `--shot build/out.png` from the repository root fails with *FileNotFound*
because it is looking for `build/build/out.png`. The editor run resolves the same relative path
against `game/`. Pass an absolute path to either and the question goes away.

### The three checks the build has to pass, and what they said

- **It runs from outside the repository.** `build/` was copied to a temporary directory with no
  checkout anywhere near it and started there. It opens.
- **It opens on the waystation from the mission file.** The status line reads *waystation — a
  garrison holding the crossroads, approached from the west*, the mission line reads *Enter the
  compound, confirm what is stored in the house, and come out — UNDECIDED*, and the turn order
  has Bekker and Orsini against four `?` slots. `H`, `K` and `M` are the three keys of the
  play-through and all three work: their script forms `--ai`/`--hostiles ai`, `--windows` and
  `--brief` were driven through the executable and each reported what it did, `--pass 30`
  stopping at a reaction window in round 4 the way it does in the editor.
- **The capture and script flags survive the export.** They do, byte for byte, which is why
  there is a section about it above rather than a line in **Seeing it** saying the harness is
  editor-only. **Re-checked after `view/playable`**, because that branch added a second `Window`
  to the scene and two settings: the export honours `--instruments` and `--still`, writes both
  PNGs, and the pinned scene from the executable has the same SHA-256 as the pinned scene from
  the editor. **Re-checked again after `view/aside`**, because that branch moves the windows and
  un-embeds one of them: the export honours `--aside` and places both, and the pinned scene still
  hashes the same from the executable as from the editor. It now also hashes the same *with*
  `--instruments` as without, which is the subwindow fix visible as a number — the panel is no
  longer painted over the map.

### Setting this up on a machine that has never done it

Two things beyond a Godot install, and neither is in the repository.

**1. The export templates, matching the editor exactly.** The editor here is
`4.7.2.stable.mono.official.ed1daf0bf`, and it wants the **mono** templates, not the plain ones.
The route taken was the release asset rather than the editor's *Manage Export Templates* dialog,
because it scripts:

```bash
curl -L -o templates.tpz https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_mono_export_templates.tpz
```

1.20 GB — 1,202,598,411 bytes. It is a zip: unpack it and copy the contents of its `templates/`
directory into `%APPDATA%\Godot\export_templates\4.7.2.stable.mono\`, which on this machine is
`C:\Users\<user>\AppData\Roaming\Godot\export_templates\4.7.2.stable.mono\`. Godot creates the
`export_templates` directory empty on first run, so its existing is not evidence of anything.

**How to tell they are there**: 27 files in that directory, `version.txt` reading exactly
`4.7.2.stable.mono`, and `windows_release_x86_64.exe` among them at about 110 MB. If they are
missing the export stops early and says so by name.

**2. `dotnet/project/solution_directory` in `game/project.godot`, pointing at the repository
root.** This one is not obvious and it costs an afternoon to rediscover. Godot's .NET exporter
insists on a solution file beside the C# project, and it names the one it wants after the
assembly — with the setting absent it looks for `game/Hexcom.Game.sln`, does not find one, and
**fails in a way that still writes an executable**: the run exits 0, `Hexcom.exe` appears at
109 MB rather than 190, the `dotnet publish` step never runs, and the .NET assemblies are simply
not in it. The errors scroll past in the middle of the pack listing. Read the size.

Pointing the setting at the root is what fixes it:

```
[dotnet]

project/assembly_name="Hexcom.Game"
project/solution_directory="res://.."
```

The repository's one solution is `Hexcom.sln` at the root and that satisfies it, even though the
error message names `Hexcom.Game.sln` — checked by moving `Hexcom.sln` aside, which brings the
failure straight back. The alternative was a second solution file inside `game/`, which is a
duplicate of `Hexcom.sln` that has to be kept in step with it, and `game/*.sln` is in
`.gitignore` for the reason that duplicate is unwelcome. The setting also points the editor's own
build button at the real solution, which it should have been pointing at all along.

**Out of scope, deliberately**: an icon, an installer, code signing, and a Linux or Mac export.
Desktop-only is the design and Windows is the machine.

---

## Open questions

- ~~**Whether an unfound hostile should hold a slot in the turn order at all.**~~ Answered by
  `../decisions.md` entry 064, and the answer is no. Built by brief five, entry 090.
- **Whether the map should stop describing a hostile who is up.** Reach fill and costs, the path
  preview, the active attention peak and ring are all drawn from `battle.Active` whatever its side, so
  a hostile stopped at a window has its reach drawn — inside a house nobody of ours can see into, on
  the waystation. Brief five's out of scope was the map; `SandboxFrame.Withheld` is the gate. Entry
  090.
- **Whether the banner should stand aside for a window.** It does: a window of ours is a question to
  us, and a band reading *their go* over it contradicts it. The other reading is that it is still
  their go and the band is 46 pixels. The play-through's to say.
- **Whether the found outline should last longer than until our next order.** It marks a discovery
  for one decision. A player who crouches first and looks at the strip second still sees it; one who
  moves first does not.
- **Whether springing an ambush belongs in the firing mode.** `B` with an armed soldier up springs
  on whoever is under the cursor, at once — the same irreversible, announcing action on the same
  kind of gesture brief three took off the right button, just on a letter. It was left alone as out
  of scope. The argument for folding it in is that the confirm is meant to live on everything that
  announces you; the argument against is that arming is already a deliberate first step, which is
  the half of a mode that `B` has had all along.
- **Whether the action bar should be drawn.** `1` aims, and nothing on screen is a bar with a slot
  in it; the legend names the key and a click on a body does the same. A player of the genre looks
  for icons along the bottom, and whether that is worth the pixels over the map is the play-through's
  to say.
- **Whether a hostile's held arc should be drawn when the hostile is.** It is not, now: a body
  shows where a soldier is and which way it faces, and the attention field shows where it is
  looking, but what it would shoot at is its intent. Omniscient draws every arc. A player who
  walks into an arc they could see the soldier holding may reasonably say the picture lied.
- **Whether a fixed 55-degree pitch is enough.** It keeps a hex a hex and a wall a wall from every
  bearing, and it cannot look along a wall. Nothing so far has wanted to. The free yaw makes this
  more pressing rather than less: a person who can now turn the camera to anywhere will try to
  tilt it, and the right-drag's vertical axis is unused and sitting there.
- **Whether the main view should say anything about the instruments window.** The legend split by
  the brief's own test and the third rank went with the instruments, so `I` is advertised only
  inside the window it opens, in the README, and in this file. A player never wants it; a tester
  opening the build cold has to be told once. Deliberately not solved by putting one line back on
  the player's legend, which is the fix that would undo the split.
- **Whether an unfound hostile's *walk* should be drawn.** A hostile move that opens a reaction
  window is walked along its committed route, and the route is drawn whether or not our side can
  see the mover — which is what `BuildCommitted` already did while the window was open, so it
  leaks nothing the window did not. But the two together now draw a moving line out of a soldier
  the picture is not showing, which is a stronger claim than a static one, and nobody has watched
  it happen yet.
- ~~**Whether a player should be answering the enemy's reactions.**~~ Answered by brief six and
  entry 085: no. A window offers our side's reactors, and the other side's are behind the
  instruments window, the same switch as the orders readout.
- **Which glyphs the shot's bill should use.** `((( ! )))` under the target and `!` over each
  listener are placeholders in the label font, waiting on capture C8. Among the labels on the
  waystation house roof — a name, a rung, `LADDER`, `HOUSE` — the target's mark is hard to pick out,
  which is the case for a mesh glyph rather than more text.
- **Whether a move's destination tile carries the same mark.** Brief four's amendment finds the
  warning drawn on the destination tile in every stealth game that draws it. The move has its
  listeners on the cursor line and nothing on the map.
- **Whether a held arc gets an adjust step.** Brief six's amendment: Phoenix Point adjusts the cone
  before confirming and Warhounds' guides single out enter, adjust and cancel as what makes
  overwatch usable. `V` takes the next arc in one press and charges for each, so finding the one you
  want can cost three declarations. Cheap, and it would be a second mode beside the firing mode — it
  should take the same keys (space confirms, right-click backs out) if it is built. The amendment
  calls it arguably brief two's or a job of its own.
- **Whether `Ctrl`'s soldier terms are too big to be a moment.** Held, the posture keys' three
  appraisals and the rest make a block several hundred pixels wide over the soldier. A held key is
  *for a moment*, which is the argument it can be large; a player who holds it to read one contact
  and gets a wall of text at their own soldier is the argument against. Splitting it — contacts on
  `Ctrl`, the soldier's own terms on hovering the soldier — would be the second gesture the brief
  warned against.
- **Whether the ground should carry every fire mode, or two.** It carries the cheapest shot and the
  dearest one a move can keep, and a rifle has a third mode between them that only the bar names.
  Five nested edges stop reading as bands; three may be one too many as well, and the play-through
  is where that is found.
- **Whether a hovered target should name who the shot tells.** Pointing at a hostile gives the
  headline and the bill's marks on the map; the names are in the dock, once aiming. Before brief one
  the names were on the panel on hover too.
- **Whether the violet edges read at all against busy ground.** They are legible in every capture
  taken at 26 to 50 metres; at `--fit` the bands are a few pixels and the pale reach edge is what
  survives, which may be right — a player at that distance is not choosing a move.
- ~~**Whether the top block should describe a hostile who is up.**~~ No — it read the enemy's
  contact file as a number. `SandboxFrame.Withheld`, brief five, entry 090.
- **Whether the mission line belongs to a player at all, or only to a tester.** It shows the
  verdict, which is the scoreboard, and the reading each departed soldier left with, which is
  how the mission is judged. Both are ours by contract 3, so there is no leak; the question is
  whether being told *you have currently failed* mid-battle is the game or a debug readout.
- **Whether the sandbox should keep applying the mission clock once Core has one.** It does now
  because the rules have none and entry 047 says whatever runs the battle applies it, so the
  harness in `content/` and this both do — two implementations of one figure, which is the shape
  entry 038 was about. When the clock lands in the rules this should become a deletion and not a
  second opinion.

Three questions here are answered rather than open. The scenario belongs in `content/` and lives
there. What our own soldiers did during the enemy's turn is no longer invisible: `Act` carries the
outcome (entry 040) and a handed-out window is answerable by hand (entry 049). And the camera is a
`Camera3D`, which is what the old question about a `Camera2D` was really asking for.

## Recent work

```bash
git log --oneline -20 -- game
```
