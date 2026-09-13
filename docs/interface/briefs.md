# The queue — interface briefs, in priority order

Written against [conventions.md](conventions.md). Each is complete in the shape
[../subprojects/master.md](../subprojects/master.md) describes: the branch, the seam by name, the
decisions to settle first, what is out of scope, and how to know it worked.

**Nothing here is anybody's job until Master promotes it** into `## The job` in the territory's
own doc. One file is never two territories' brief. Take them in order unless Master says
otherwise. Most are View's; brief nine is Content's, and says so.

**Entry 058's rule holds throughout: the convention is the starting point, and a departure argues
its case.** Each brief says at the top whether it is the genre's answer or a departure from it,
so a session knows which parts it may reshape while building and which parts are the point.

**The order, in one line each.** Seven first, the turn's end, the cheapest and one that helps every
mission, the waystation included. Then eight, the briefing before turn one. Nine, the first mission,
is written against both and can be built beside them. Ten, the options, is last. It helps every
player without teaching any of them anything, and a player who cannot read the game yet has
nothing to change.

---

## Landed, and out of the queue

A brief whose subject has landed comes out, so that the queue stays a work order. Code comments and
entries that cite a brief by number resolve through the pointer beside it. What each built is under
*What landed on* in `../subprojects/view.md`.

| | Brief | Branch | Entry | Full text |
|---|---|---|---|---|
| Zero | the first play-through's six, as the genre answers them | `view/playable` | 066 | `45e9829:docs/interface/briefs.md` |
| One | the readouts go on the things they describe | `view/readouts-in-place` | 093 | `45e9829:docs/interface/briefs.md` |
| Two | the enemy's file, drawn | `view/enemy-file` | 098 | `0bde77d:docs/interface/briefs.md` |
| Three | the gesture set | `view/gestures` | 084 | `45e9829:docs/interface/briefs.md` |
| Four | who a shot would wake | `view/shot-bill` | 086 | `45e9829:docs/interface/briefs.md` |
| Five | the strip, and the pause, say only what the player knows | `view/order-strip` | 090 | `45e9829:docs/interface/briefs.md` |
| Six | the window has a default | `view/window-default` | 085 | `45e9829:docs/interface/briefs.md` |

Each commit holds the brief together with the amendment and settling blocks that went with it.
Two things from those blocks were never built, and they are carried in `../subprojects/view.md`
rather than here: the arc's adjust step (*Amending Six*), and the relay missing from the shot's
bill (entry 086, Core's half). **Brief eight's `Ctrl` half no longer waits:** entry 098 drew the
three marks and settled what each is called, under *Told, lost, seen*, and the rung's words are
`SandboxRung.Words`.

---

## Seven — the turn's end says what it does

**Branch** `view/turn-end`. **The genre's answer in where it goes**: the figure goes where the
cursor already is. **A departure in what it says**, because no game in the set has a turn's end that
does anything.

**What it is.** Lesson 1 of `conventions.md` *Teaching it*. Ending a soldier's go does two things
and neither shows. It is the only moment that soldier looks around, and it banks what is left as a
reserve. A soldier who banks nothing holds no answer on the other side's go, and gets no look at
anybody who walks across their front either: `ReactionWindow.BuildOffers` skips a reactor with no
reserve before it asks anything else, and its remarks say why. A player learns the first by the
fog lying to them, which entry 097 chose to allow, and the second by a window that never opened,
which cannot be seen at all. Both need saying, at the control that does them and on the soldier
they happen to.

**The seam.**

- **The slot.** `ActionBar.Of` in `SandboxBar.cs` adds `"end"` with the name `end turn` and a hint
  saying leftover points bank for reacting. `BattleHud.DrawBar` draws it. The slot's caption is the
  place for the figure.
- **The figure.** `SandboxFrame.Ladder` asks `ReactionModel.Banked`, through `ReserveLadder.Of`,
  for what stopping now would bank, and its rungs are the fire modes that bank affords. Nothing
  multiplies by the fraction (`../subprojects/view.md`, *What the next View brief inherits*).
- **The mark on the body.** `Unit.CanReact` is `InPlay && Reserve > 0`, so a soldier of ours for
  whom it is false on a go that is not their own is head down. Marks hang from `BattleView.Crown`.
- **No new interaction**, so no new script step, per entry 049. The existing `--pass`, `--ai-turn`
  and `--until` steps reach every frame this needs.

**Settle first.**

- **The words.** Two facts, every turn, short enough for a slot: that the soldier will look, and
  what they will bank. Something like *look · bank 17* and *look · bank nothing*. Whether the
  caption also names the best fire mode the bank affords — *bank 17 · a snap* — is the reserve's
  own cliff (entry 067), and worth the room if it fits. Decide once, and keep the ground's band
  colours if a mode is named.
- **A declared arc.** A soldier ending with an arc held banks into it. Say whether the caption says
  so, or whether the arc slot's lit state already does.
- **When the mark shows.** From the end of that soldier's go until their next one starts, and never
  on their own go, because the reserve is cleared at `Advance` and reads nought all through it (the
  reason entry 093 took it off the readout). A soldier who spends the last of a reserve answering a
  window goes head down at once, which is correct, and the mark should follow.
- **What it looks like.** It sits on our own soldiers only, and it must not look like a stance
  glyph, like brief two's rung on a hostile, or like any ghost. The reserve of a hostile belongs to
  his side, and it is never drawn (contract 3).

**Out of scope.** The rules, and every figure in `ReactionModel`. A message or a popup of any kind:
the requirement is persistent, not announced, from Phoenix Point's failure. The arc's adjust step.
Whether a walking soldier should take a look, which is entry 097's question to Core and changes
nothing here.

**How to know it worked.**

- On a soldier with 24 points left, the End turn slot reads the figure `Banked` gives for 24. With
  9 left it reads that the soldier banks nothing. The two captures differ in the slot and nowhere
  else.
- Across a hostile go under `--ai-turn`, with one soldier of ours holding a reserve and one holding
  none, the mark is on the second and not the first. If the hostile crosses both fronts, the window
  offers only the soldier without the mark, and the capture shows that.
- The pinned scenes change by the slot's caption and the mark, and nothing else. Two runs hash the
  same.

---

## Eight — what the squad was told, before turn one and after

**Branch** `view/briefing-first`. **The genre's answer** for the briefing's place. **A small
departure** in drawing the told marks while it is read, argued below.

**What it is.** Lesson 2 of *Teaching it*, first case, and the one thing a player needs before turn
one. The mission file carries a six-part briefing, and the only way to read it is `M`, which no
legend names. The genre puts a briefing in front of the first move. What this game adds is that the
briefing is also where the told marks on the map come from. `told player searching Cobb Teague
Marek` is the *presence* part said as rules. So drawing those marks as the *presence* paragraph is
read, with its *we think*, teaches *a mark is what we were told* before anything moves. It is
entry 094's item 5, *I can see all the enemies*, answered from the moment the player is told.

Second half: every mark says what it is under held `Ctrl`. That is the gesture brief one chose for
*every figure's terms at once* (entry 093), applied to marks as well, so the question of a gesture
is not settled twice.

**The seam.**

- **The switch.** `HexSandbox._briefing` starts false. `Key.M` toggles it, a back-out puts it away,
  and `--brief` is the script step that turns it on.
- **The text.** `BattleHud.BriefingLines` prints `mission.Brief.Part(part)` for each of
  `Briefing.Order`, in the file's own words.
- **Who opens it.** Entry 066 split the defaults: a person double-clicking the build gets the game's
  defaults, and the capture harness gets its own, so every pinned capture still opens the run it was
  written against. The briefing opens for a person and not for a capture, the same way.
- **The legend.** `BattleHud.PlayerKeys` has no `M`.
- **The marks.** A told contact is `Contact.Briefed` (entry 091), drawn by `BattleView.BuildGhosts`
  today and by whatever brief two replaces it with.
- **`Ctrl`.** `HexSandbox.HoldDetails` and `SandboxFrame.Details`, with `--details` holding it down
  for a capture.

**Settle first.**

- **What dismisses it.** `M`, `Esc` and right-click are the back-out family and should all do it.
  Space and enter confirm a shot and do nothing else (entry 096), so they should not dismiss it.
  Give it its own button as well, so a mouse player finds a way out without being told.
- **What waits behind it.** If a hostile under the AI has the first go of the round, its turn must
  not run behind the briefing. Decide whether the battle holds until dismissal, and check that
  `--brief` in a script does not change what a script without it plays.
- **How the told marks are singled out while it is up.** All of them together while the *presence*
  part is on screen. The file does not link a sentence to a contact, and linking them is a format
  change for Content, not a drawing here. The camera does not move to them. `--fit` at the opening
  already frames the waystation.
- **The names under `Ctrl`.** One word or two per kind of mark, and three kinds: what we were told,
  what we saw and lost, and what he believes about us. They are brief two's three looks. If brief
  two has named them, use its words. If it has not landed, this half waits for it and the briefing
  half does not.

**Out of scope.** The briefing's words, which are the mission file's and, behind it, Setting's
register. A menu, a separate scene or a mission select, which is milestone 3. A prompt that speaks
during the mission: *Teaching it* considered it and deferred it. The fog, which is
`view/ground-and-camera`.

**How to know it worked.**

- The build opens with the briefing over the waystation's opening frame, and the four told posts
  singled out. Dismissed, the frame is today's frame.
- `M` brings it back mid-mission, and the legend names `M`.
- Every capture command in `../subprojects/view.md` opens as it did, and a `--brief` capture shows
  the briefing.
- A `--details` capture on the waystation's turn one names every mark on screen, and none of the
  four told posts reads as a body.

---

## Nine — the first mission teaches, and it is shaped, not scripted

**Branch** `content/first-mission`. **Content's, not View's** — Master routes it. **The genre's
answer** for the vehicle, eight games of eight. **A departure** in running it without a script,
argued in *Teaching it*: a scripted hostile teaches the script, a script needs a rule, and a
scripted tutorial stalls when one instruction is missing.

**What it is.** A short mission, fought on the real rules against `Commander`, whose ground and
posts are placed so that the three lessons of *Teaching it* happen on their own in the first few
turns. Mutant Year Zero's too-strong enemies make sneaking happen the same way. Nothing in it is
held in place and nothing tells the AI what to do. It is a mission file, and the format already
has everything it needs.

**The seam.** `content/missions/*.hexmission` — `deploy`, `told`, the six `brief` parts,
`objective … unnoticed <rung>`, and `rounds`. `MissionLibrary.Load`. A harness in the shape of
`content/Hexcom.Content.Tests/Waystation` and `.../Kestrel`: a `*Fight` naming the mission,
`*FightTests` over seeds, and `*GroundTests` measuring the map against its own briefing, with
`MatchRecorder` and `MapSketch` as they are. Which mission a person's build opens on is one name in
`SandboxScenario`, and that line is View's.

**Settle first.**

- **The stop sits above every rung the mission teaches.** The waystation's is `unnoticed
  suspicious`, so there a sentry reaching Searching ends the task, and that sentry is lesson 3. A
  lesson that ends the mission is teaching by losing. Set the stop no lower than Searching, and say
  in the file why.
- **The moments, each one measured by a ground or fight test rather than argued**, in the way the
  waystation's line into the house is held by a test:
  1. **Turn one shows a body beside a mark.** One hostile is in plain view of the deployment and
     drawn as a body, and at least one told post is out of view and drawn as a mark. Both are on
     screen at the opening zoom.
  2. **A move in the first minute is heard.** From the deployment, a route that one soldier can
     take on turn one ends where `WouldHear` names the hostile in view, through a wall and not in
     his sight. Taken, it raises his rung and does not reach the stop.
  3. **The rung comes back down.** With the squad quiet afterwards, that rung falls within a few
     rounds, across the seeds. If the decay dials cannot make that happen on a short mission,
     that is a finding for Core in `../decisions.md`, and no dial is changed here.
  4. **Stopping sees what walking did not.** A place reachable on turn one is in a standing man's
     line from where a soldier arrives, and it holds a hostile nobody has registered. He is
     registered when that soldier's go ends, and not before, and the mission survives it.
  5. **Wanted, measured, not required:** a Searching hostile's walk to his marker crosses a place
     where one of ours plausibly stopped holding a reserve, so the first window comes early. The AI
     scores that walk, and it cannot be placed, only made likely. Report how often it happens.
- **Size.** Short enough to replay in minutes: two or three hostiles and a clock well under the
  waystation's thirty. The ground can be an existing map or a small new one; that is Content's
  call, and so is the kit.
- **The words.** The briefing in the mission book's register (`docs/setting/missions.md`), as the
  waystation's is. The *restraint* and *stop* parts name the stop plainly, because that is the one
  rule of the mission that is not on the map.
- **Whether the build opens on it.** The recommendation is that a person's build opens on the first
  mission, with the waystation one flag away. A stranger is the audience for teaching, and the genre
  offers its tutorial first. But every play-through so far has measured the waystation, so **Master
  and the user decide**, and View changes the one line.

**Out of scope.** Rules. A mission that needs one goes to Core in `../decisions.md`, and needing it
means the lesson is wrong. Scripting of any kind. A prompt that speaks during the mission, which is
a format change *Teaching it* deferred. Every drawing, which is briefs two, seven and eight.

**How to know it worked.**

- The harness pins moments 1 to 4 on named seeds and reports moment 5 as a rate.
- **The stranger's test, once two, seven and eight have landed.** Somebody who has not played is
  handed the build, plays one turn, and is asked what they understand. *Teaching it* gives the four
  sentences a right answer contains. Where one is wrong, record which, and check it against its
  owner: *which is really there* is brief two's drawing on moment 1; *he hears me* is the cursor
  line on moment 2; *this soldier keeps seventeen* is brief seven; *a soldier looks when they stop* is moment 4's
  ground. Then decide whether the mission or the drawing failed, and do not guess.

---

## Ten — what a player may change

**Branch** `view/options`. **The genre's answer** in every setting that names games. **Two
departures**: colour is a second channel in the drawing before it is ever a mode, and there is no
briefing option. Both are argued in `conventions.md` *What a player may change*, and neither is
built here.

**What it is.** Entry 094's item 1, settled narrow with the user: an input map and a preferences
file, loaded at start, with an options screen over them, and the layout constants stay in code.
Today nothing can be changed except from the command line, and a double-click cannot pass a flag
(entry 100). The set says what goes on the screen: rebinding in eight games of ten, one map per
context in four of four, pace patched into two games and modded into a third, and text size wanted
by the players of both games that were asked.

**The seam.**

- **Keys.** `HexSandbox.HandleKey` is a switch over literal `Key` cases. Every order but a move goes
  through `HexSandbox.PressSlot`, by slot id. `ActionBar.Of` gives each `BarSlot` its key as a
  string, from `FireKeys` and `ArcKeys`. `BattleHud.PlayerKeys` is the legend, and
  `BattleHud.BriefingLines` writes `M` into the briefing's heading. The reaction window's keys are
  their own branch of the handler (entry 096). Held `Ctrl` is `HoldDetails`.
- **Preferences.** `--edge-pan` sets `EdgePanning`. `--pace` sets `WalkPace`, which defaults to ten
  metres a second, the one interface figure measured by watching (entry 080). `--still` clears
  `Animate`. `TheirGoDwell` holds the banner. `SandboxCamera` owns the turn, and
  `HexSandbox._UnhandledInput` reads the drags.
- **The split with the harness, already built.** `Animated` is `_capture is null && Animate`, so a
  capture already refuses to take time whatever a person has set. The preferences follow the same
  test.
- **Text.** `BattleHud` draws with `_canvas.DrawString` at literal sizes, `TagSize`, `LineHeight`
  and `TagStep` among them, at pixel offsets from `BattleView.Crown`. The bar is 86 pixels, and
  `SandboxCamera.Fit` was measured against it.
- **Godot's own mechanism**, if it fits: `InputMap` for the bindings and `ConfigFile` under `user://`
  for the file. That is View's call.

**Settle first.**

- **The map's names.** Bind to actions, not keys: the slot ids `PressSlot` takes, and a name for each
  of `HandleKey`'s other cases. Then every place a key is written — slot, legend, briefing, hint —
  reads it from the map. Settle whether the file carries every binding or only the ones a player
  changed.
- **The contexts, and what counts as live at once.** Battle, window and camera. A clash is refused
  only where both actions would be live at the same moment, and the refusal is drawn on the row. The
  bar is empty inside a window (entry 096), so the two `1`s never clash, and the camera's keys clash
  with everything. Write the rule down as a table before building the screen.
- **Two slots, an unbind, and a reset** per context and for all. A held binding says it is held, as
  Mutant Year Zero labels one.
- **The pace's steps.** Phoenix Point has four, and XCOM 2 has Zip Mode on or off. Pick steps, with
  today's default as one of them and *instant* as the top, the same as `--still`. One preference
  scales the walk, the camera's animated turn and the banner's dwell together, and none of them gets
  a dial of its own (entry 094).
- **The scale's range, and what it does not scale.** Text, tags, the bar and the panel scale. The
  world and the camera do not. At a larger scale `Fit`'s margins grow with the bar, so re-measure
  them rather than scaling them blind.
- **How the screen is reached.** `Esc` backs out and never spends a point (entry 084). Phoenix Point's
  bindings screen gives `Esc` both jobs as *Cancel / Open game menu*: it cancels while there is
  something to cancel, and opens the menu when there is not. Take that. The screen spends nothing
  and changes nothing in the battle.
- **What the screen is organised by.** Controls grouped by context, which is the one thing the set
  agrees on. Everything else is View's to lay out.

**Out of scope.** A colour-blind palette mode, which waits for the art pass. The second channel on
the cover grades, which is a drawing and not an option: entry 101 routes it.
Difficulty, which is Core's and balance. Any setting for a layout constant, a single colour or a
single dwell. Anything behind the instruments switch or on the harness's command line: omniscience,
the other side's windows, the AI's sides, the seed. Options for the briefing or the first mission.
Controller support. Audio, beyond leaving the screen room for it.

**How to know it worked.**

- A person rebinds End turn. The bar's slot, the legend and any hint show the new key, the old key
  does nothing, and a restart keeps it. Binding a key already live in the same context is refused
  on that row. Binding the window's `1` and the bar's `1` is allowed, as the defaults already are.
- With a preferences file that moves every setting away from its default, every capture command in
  `../subprojects/view.md` hashes as it does with no file at all.
- The pace's default reproduces today's run, and its top step reproduces `--still`.
- At the largest scale, a capture at `--fit` still passes brief one's test — no text over the map
  that is not attached to something on it — and the bar's slots are all readable.
- `Esc` with an aim open backs out of the aim; `Esc` with nothing open opens the screen.
- A deleted file gives the defaults. A malformed one gives the defaults and a line saying so, never
  a crash.
