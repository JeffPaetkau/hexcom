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

**The order, in one line each.** Two first, because a stranger cannot read the first mission's marks
until they are drawn. Then seven, the turn's end, the cheapest of the three and one that helps every
mission, the waystation included. Then eight, the briefing before turn one. Then nine, the first
mission, which is written against all three and can be built beside them.

---

## Landed, and out of the queue

Re-primed by the onboarding pass. A brief whose subject has landed comes out, so that the queue
stays a work order. The six below landed with the entries named, and **their full text, with the
amendment and settling blocks that went with them, is at `45e9829:docs/interface/briefs.md`.**
Code comments and entries that cite them by number resolve there. What each built is under *What
landed on* in `../subprojects/view.md`.

| | Brief | Branch | Entry |
|---|---|---|---|
| Zero | the first play-through's six, as the genre answers them | `view/playable` | 066 |
| One | the readouts go on the things they describe | `view/readouts-in-place` | 093 |
| Three | the gesture set | `view/gestures` | 084 |
| Four | who a shot would wake | `view/shot-bill` | 086 |
| Five | the strip, and the pause, say only what the player knows | `view/order-strip` | 090 |
| Six | the window has a default | `view/window-default` | 085 |

Two things from those blocks were never built, and they are carried in `../subprojects/view.md`
rather than here: the arc's adjust step (*Amending Six*), and the relay missing from the shot's
bill (entry 086, Core's half).

**Two stays below, word for word with its amendment,** because View's job reads it by name. It
comes out the same way once it lands.

---

## Two — the enemy's file, drawn

**Branch** `view/enemy-file`. **A departure from nothing**: the genre has no convention here, so
this borrows from the nearest relative and the borrowings are named.

**What it is.** The rules carry a five-rung ladder — `Unaware`, `Suspicious`, `Searching`,
`Alerted`, `Engaged` — and a marker each hostile holds on each of ours. Both are drawn today as
words in a text line. They are the subject of the game and no other game in the genre has them,
so there is no convention to inherit and one close relative to borrow from: Invisible, Inc.

**The seam.** `AwarenessTracker.ReadoutFor(them, us).State` is the rung, already coarse by
contract 3, and already what the scorer reads since entry 021. `Contact.LastKnownPosition` is the
marker. `SandboxFrame.Sees` is the one question the view, the HUD and the cursor all ask about a
hostile, so there is no second place for anything to leak. `BattleHud.AlarmLine` and `Held` are
what this replaces.

**Settle first.**

- *The ladder shows transitions only.* Invisible, Inc. gives its alarm six rungs with five
  sub-levels each that have no effect and no display, so a player only ever reads a change. That
  is contract 3's coarse rung arrived at independently and shipped. The certainty behind the rung
  is never drawn, and `ReadoutFor` already makes that hard to get wrong.
- *`Suspicious` needs its own mark.* A player will read it as *seen* and it is not — it is
  *something registered, coming to look, does not know what for*. The genre has a convention for
  exactly this state and calls it noticed.
- *Their marker is a ghost of our own soldier.* They believe one of ours is somewhere they have
  left. Draw it as a translucent copy of the soldier it is wrong about, with a line to where that
  soldier actually is. That is the one thing of theirs a player sees, and section 07 says it is
  the payoff.
- *A hostile's held arc is drawn whenever the hostile is.* This settles a View open question with
  a genre reason: the stealth shelf draws what a guard will do because beating it is the game. A
  player who walks into an arc held by a soldier they could see holding it will say the picture
  lied.

**Out of scope.** The rules. Anything that would need a query that does not exist — and nothing
here does. Whether an unfound hostile holds a slot in the turn order, which is brief five.

**How to know it worked.** Walking one soldier along a sentry's flank moves a rung on that
sentry's body while the player watches, and the ghost of that soldier stays behind at the place
the sentry still believes in. Neither reads as a number. A player who has never seen the panel
can say which hostile is about to act on them and why.

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

# Amendments from the reference set

*Appended by the synthesis pass, and appended rather than folded in so that a brief a View session
has already read does not change under it silently. Only the amendment to the brief still in the
queue is kept here; the rest, with the settling block that followed them, are at
`45e9829:docs/interface/briefs.md`. The evidence is the ten files under
[reference/](reference/), and **C1**–**C20** are entries in [captures.md](captures.md).*

## Amending Two — the enemy's file, drawn

**Correction to how the held arc is argued, not to the recommendation.** The brief settles a View
open question by drawing a hostile's held arc whenever the hostile is drawn, and argues it from the
stealth shelf: *the stealth shelf draws what a guard will do because beating it is the game.* What
that shelf draws is a **vision cone**, not a held reaction arc, and the two are different objects.
**No game in ten draws a hostile's reaction zone at all**, and Mutant Year Zero's players asked for
exactly this indicator and were told it is not implemented. The recommendation stands and is right
— a player who walks into an arc held by a soldier they could see holding it will say the picture
lied. But it is a departure from nothing, it carries a departure's burden, and it should stop citing
a borrowing it does not have.

**And the complementary correction, which points the other way.** Drawing *your own* held arc on
the ground is a **convention** with two shipped precedents, which an earlier reading of the set
denied. Phoenix Point draws the overwatch arc from the soldier's eye position with its maximum width
set by weapon class — `OverwatchArc`'s own shape, reached independently — and Warhounds draws a
firing area in front of the operator. So the arc is not unprecedented; only the hostile's is.
**C4** and **C14** are the two captures that would settle the drawing.

**Three requirements the set added, all with a shipped failure or a shipped precedent behind them.**

- **Persistent, not announced.** Phoenix Point tracks alert state and surfaces it as a brief orange
  popup that its own players describe as impossible to recover once missed; a mod exists solely to
  draw a persistent icon instead. That is the failure mode nearest this game's, and it rules out any
  design where a rung change is a transient message. **Provisional on C15** only as to whether the
  popup is a sub-second miss or an attention problem; the requirement holds either way.
- **What the rungs are called on screen is this brief's decision, not a passthrough of the enum.**
  Klei renamed Invisible, Inc.'s alarm from `ALARM` to `SECURITY LEVEL` because playtesters read the
  original naming and numbering as more informative than it was meant to be. `Searching` and
  `Alerted` are exactly the pair a player will read as a measured scale rather than as two words,
  and contract 3 says that scale is not theirs to have.
- **A rung that falls has no analogue anywhere in the set.** Invisible, Inc.'s escalation is one-way
  at the top: investigating resolves either way, alerted never resolves for the rest of the mission.
  A contact file here decays, so a rung can come back down. A player borrowing the genre's only
  ladder will assume it cannot, and the drawing has to make the fall as visible as the rise — or the
  rules get read wrong in the one direction that costs a soldier.

**One refinement on the *noticed* mark.** The convergence the brief rests on is real and the
denominator is better than it looks: two of ten across the set, but two of *two* among games that
have a state between unaware and engaged, and both drew it as a glyph on the body rather than as a
position on a scale. The detail worth copying is one the brief does not have: Invisible, Inc. draws
a **second** `?` at the interest point the guard is walking toward, separate from the badge on the
guard. That is the same object as this game's marker — a glyph at a place somebody believes in — and
it is the only instance of one in ten games. **C3** is the capture.
