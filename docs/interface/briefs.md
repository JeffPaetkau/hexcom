# The queue — interface briefs for View, in priority order

Written against [conventions.md](conventions.md). Each is complete in the shape
[../subprojects/master.md](../subprojects/master.md) describes: the branch, the seam by name, the
decisions to settle first, what is out of scope, and how to know it worked.

**Nothing here is View's job until Master promotes it** into `## The job` in
`../subprojects/view.md`. One file is never two territories' brief. Take them in order unless
Master says otherwise; the order is *what a player of this genre reaches for and does not find*,
not what is cheapest.

**Entry 058's rule holds throughout: the convention is the starting point, and a departure argues
its case.** Each brief says at the top whether it is the genre's answer or a departure from it,
so a session knows which parts it may reshape while building and which parts are the point.

Priority reasoning, in one line each: the six findings from the play-through are already routed
and come first; then the readouts, because the panel is what a returning player would notice
before anything else; then the enemy's file, because it is the game's subject and nothing draws
it; then the gestures, which block the mouse camera; then the two smaller gaps.

---

## Zero — the six, as the genre answers them

**Not a brief.** Entry 057's six findings are routed to View already, and re-issuing them here
would put one job in two files. This is the amendment sheet that belongs beside them: what
`conventions.md` says each one's answer is, so the genre's version gets built and not the first
version that works. **The six landed with entry 066**, so this is now a review list: each item
says what the genre's answer was, and what was built can be read against it.

1. **The instruments in a second window.** No genre precedent — shipped games ship no overlays
   and put what exists behind a console. Borrow the development-tool pattern instead. The
   instrument window takes the orders readout, the appraisal terms, the mode line, the legend and
   the seed; the game window keeps the mission, the turn order, the soldier, the cursor, the shot
   and its worth, and reactions. View's own test for the line is the right one.
2. **The camera turns smoothly.** Settled by entry 058 and not to be re-argued: if an arc proves
   illegible from an odd angle the answer is a better arc, never a snapped camera. Free yaw on a
   drag; keep `Q`/`E` as an *animated snap to the next bearing*, which on a free camera is an
   affordance rather than a limitation — it is how a player squares the grid with the screen. A
   keyed step in this genre is one beat, on the order of 300 to 450 degrees per second; a drag is
   one to one with the hand, around 0.2 to 0.4 degrees per pixel. Both are arguments and neither
   is measured.
3. **The mouse drives the camera.** Settle it *with* item 4 of this sheet, not before it. The
   genre's orbit gesture is a right-drag or a middle-drag and right-click is currently spent on
   firing, which is the most irreversible action in the game bound to the button the genre uses
   for cancel. Edge-pan a setting, default off.
4. **It opens as the mission against the AI.** No conventions bear on it. Build it as written.
5. **Contrast.** No conventions bear on the hue. One rider: whatever weight a soldier's outline
   gets has to survive the ghosted-storey tint *and* the alarm ladder that brief two puts on
   hostile bodies, so leave room above the body rather than filling it.
6. **A move walks the route.** Price the pace in **metres per second**, not seconds per move —
   one world unit is one metre by contract 5, and a fixed duration makes a two-hex step and an
   eight-hex step look equally urgent. A tactical walk is about 1.4 m/s, a hustle about 2.5, both
   arguments. Draw the ticks the reaction line quotes as the soldier passes them: the walk is the
   readout for the reaction rule, not decoration. Instant setting on Zip Mode's precedent, forced
   in captures.

---

## One — the readouts go on the things they describe

**Branch** `view/readouts-in-place`. **The genre's answer, adopted** — no departure in it.

**What it is.** Every figure in this interface is a line of text in a panel at the top left. The
genre's interface is spatial: the hit chance on the target, cover on the tile, points on the
soldier, and a panel for what has nowhere better to be. A game whose subject is information
cannot teach a player to read a battlefield with a readout that requires looking away from it.
This is the largest single difference between what is built and what a player of this genre
expects, and it is worth more than any missing feature.

**The seam.** `BattleHud.DrawLines` assembles the panel — about twenty lines from `MissionLines`,
`AlarmLine`, `SeenLines`, `ViewedLine`, `ReserveLine`, `PostureLines`, `ShotLine`, `WorthLine`
and the cursor line, several carrying six or eight facts each. `SandboxCanvas` is a flat surface
over the picture that draws what it is handed, and `SandboxGeometry` already converts a node and
a unit into a screen position for the map labels. Those two are the whole mechanism: a figure
becomes spatial by being drawn at a projected position instead of at a panel row.

**Settle first.** *Headline and breakdown.* The audit's figures all stay reachable and stop being
simultaneous — one number at the thing, its terms on demand, which is XCOM's hover. Pick the
gesture for *on demand* once and use it everywhere; a second modal readout per figure is how this
ends up worse than the panel. And pick what the panel keeps: the mission, the clock and the
weapon have no place on the map, and everything else does.

**The points are the one figure that changes shape rather than only place — entry 067.** Pips on
the soldier is the genre's answer, and the row carries two cliffs no game in the genre needs: the
point below which stopping banks nothing, and the point at which the bank first affords a snap
shot and then an aimed one. Both come out of `ReactionModel.Banked` against `ReserveFloor` and
the loadout's fire mode prices, and `Banked`'s own remarks name the second cliff. A player reading
that row should see *spend to here and I can still snap, to here and I can still take an aimed
shot, past here and I am holding nothing*. **Call `Banked` rather than re-deriving it**:
`BattleHud.ReserveLine` currently recomputes the fraction and the floor inline, which is one rule
with two implementations and is the shape entry 038 was about.

**Out of scope.** The alarm rung on the body, which is brief two and depends on this landing
first. The instrument window's contents, which were entry 057's item 1. Any new figure other than
the two cliffs above — this moves what exists, and those two are the one exception because the
rules already compute them and only the panel was flattening them.

**How to know it worked.** With the cursor on a hostile at default zoom, the hit chance, the
expected worth and the cost of getting there are all readable without the eye leaving the target,
and the panel is short enough to read in one glance. A capture at `--fit` has no text over the
map that is not attached to something on it. And a player who has spent no points can say, from
the soldier alone, how far they may move and still hold an aimed shot.

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

## Three — the gesture set

**Branch** `view/gestures`. **The genre's answer, adopted**, and the current binding is the
departure being undone.

**What it is.** Right-click fires. In every game in the genre right-click cancels or deselects,
and firing is a *mode* — entered from an action bar or a key, targets cycled on Tab, committed
with an explicit confirm. Two things follow: the most irreversible action in this game is on the
button a player will press to back out of something, and the gesture the genre uses for orbit is
unavailable.

**The seam.** Entry 049 pulled every action out of the input handler into named methods on
`HexSandbox` — `MoveTo`, `FireAt`, `SetStance`, `HoldArc`, `ShoutAbout`, `LeaveTheField`,
`EndTurn`, `PlaceReaction`, `ResolveOpenWindow` — and the keys and the script are two callers of
one surface. So this job rebinds callers and adds a mode; it does not touch what the actions do.
Every interaction added here needs a script step or a reason it cannot have one, per entry 049.

**Settle first.** *What confirmation the genre actually asks for*: one click commits a move, no
undo anywhere, and the confirm lives on the shot because the shot is what announces you. Do not
add a move confirmation to soften the fog — the fog is the game, and a rewind would make
reconnaissance free. What is owed instead is already on screen: attention on the destination and
who would hear you. And *where the letter keys go*: an action bar bound to `1`–`9` collides with
the reaction window's numbers, so decide whether the window's numbers move or the bar is only
live outside a window.

**Out of scope.** The camera gestures themselves, which are entry 057's item 3 and settle against
this. The reaction window's keys, except for the collision above.

**How to know it worked.** A player who has played XCOM can select a soldier, move, take a shot
and back out of a half-entered order without being told any keys. Pressing right-click over a
hostile does not kill it.

---

## Four — who a shot would wake

**Branch** `view/shot-bill`. **The genre's answer, adopted** — XCOM warns you before you break
concealment and this game does not.

**What it is.** Entry 012's second item, and the oldest open interface gap. Firing is the loudest
thing a soldier can do, the scorer charges the shot for what it announces — `GivenAway`, inside
the worth line's spared term — and there is no preview of *who* it would wake or by how much. The
player sees the price and not the bill. XCOM tells you before you break concealment; this is the
game where it matters most.

**The seam.** The move half is already built and is the pattern to copy:
`AwarenessTracker.WouldHear` against `Battle.Loudness`, printed by `BattleHud.NoiseLine` as names
without figures, because the figures are movements in the enemy's contact file and stay a rung.
`ShotLine` and `WorthLine` are where the shot's half goes.

**Settle first.** Whether the query exists. The noise a *move* makes is public; the noise a *shot*
makes may not be reachable without a new query on Core, and if it is not, that is an entry in
`../decisions.md` under contract 2 and not a computation in `game/`. Check before building. And
the same rung discipline as the move: names, not figures.

**Out of scope.** Any change to what a shot costs. The rules of earshot.

**How to know it worked.** Hovering a shot on the waystation names the sentries that would hear
it, and taking the shot wakes exactly those.

---

## Five — the strip, and the pause, say only what the player knows

**Branch** `view/order-strip`. **The genre's answer on the round mark; a departure on the unfound
hostile**, which the genre never needed because its strips draw everybody.

**What it is.** Initiative is rolled per round and the strip shows the interleave, which is why
an interleaving game draws a strip at all. One thing is missing and one is wrong. Missing: the
round boundary, without which the order a player is reading looks more durable than it is —
Battle Brothers marks it for the same reason, and recalculates initiative every round as this
does. Wrong: an unfound hostile holds a slot reading `?`, which tells a player that an enemy
exists and roughly when it acts. **Entry 064 settles it and the View open question with it: the
strip draws only what the player knows, and an unfound hostile holds no slot at all.**

**The seam.** `BattleHud.DrawOrderStrip`, and `SandboxFrame.Sees` is already the one question
that says whether a hostile is known — the same question the view, the HUD and the cursor ask, so
the strip must not grow a second opinion about it.

**Build with it: the *their go* banner, settled by entry 065.** An unfound hostile's turn passes
with nothing on screen and time moving, and the pause needs an account or it reads as a bug.
**One indicator per contiguous stretch of hostile activity, never one per turn** — it appears
when control leaves the player's side and clears when it returns. Per-turn hands back exactly
what dropping the slot withheld, because a player who counts the appearances has the enemy's
count and their place in the order again; and showing it only for unfound hostiles is worse,
because then its presence is the tell. So: the same indicator for every hostile turn, known actor
or not, and one for a run of them. A **message** with an activity indicator inside it, not an
indicator alone — a bare spinner claims the software is busy, which is a bug report. A **minimum
dwell** of roughly 0.6 to 1.2 seconds, an argument and not a measurement, so a resolution that
finishes in a frame does not flash it. **No dwell in captures or headless runs**, by the same
settle-before-shot rule as every other animation.

**Settle first.** *Where a perceptible event lands.* Anything a hostile turn does that the player
*can* perceive — a noise heard, a shout picked up, one of theirs shot at — has to register, and
the happenings block already exists for what happened while it was not your go. Those are per
event and are legitimately countable, because the player genuinely perceived them; the banner is
not. And *the strip is redrawn from what is known now*, so a hostile found mid-round enters the
order immediately, which should read as a discovery.

**Out of scope.** What is drawn on the map, which is brief two. Anything that would make an
unfound hostile's turn *visible* — that is the fog, and it stays. Any camera move towards an
actor the player has not found, for the same reason.

**How to know it worked.** A player can say whose go is next and when the round turns over, and
cannot count the enemy squad from the strip, from the banner, or from anywhere else. A round in
which a hostile they have not found takes a turn shows them the banner, leaves them something to
read about it if it made a sound, and nothing if it did not.

---

## Six — the window has a default

**Branch** `view/window-default`. **The genre's answer, recovered as a default** rather than as
the limitation it is elsewhere.

**What it is.** Every option in a reaction window is scored with `ReactionWindow.Appraise`, the
same call the recommendation is made with. Answering the common case — take the recommendation —
costs a Tab, a number and a space. The genre's convention is that overwatch is a *state* and not
an interaction; the right way to keep this window, which is better than the interrupt it descends
from, is to recover that convention as a default rather than as a limitation.

**The seam.** `ResolveOpenWindow` and `PlaceReaction` on `HexSandbox`, `BattleHud.WindowLines`,
and the `--place NAME:N` / `--resolve` steps that must keep working unchanged.

**Settle first.** Whose windows a player is offered. The window currently offers every reactor in
it whichever side they are on, which is right for a harness that drives both sides and is not
what a player should be handed — it is the same family as the orders readout, and belongs behind
the same switch. That settles a View open question. Default: your own side only.

**Out of scope.** The scoring. The tick clock and the committed route, which are built and are
what the window got right.

**How to know it worked.** A full waystation mission is playable with one key per reaction
window, the scripted steps from entry 049 still reproduce their line, and no window offers a
player an answer for a hostile unless the instruments are on.

---

# Amendments from the reference set

*Appended by the synthesis pass, and appended rather than folded in for the same reason the log is
append-only: a brief a View session has already read must not change under it silently. Nothing
above this line was rewritten. Each amendment names its brief, says what the evidence did to it,
and says whether it is a correction or a refinement.* The evidence is the ten files under
[reference/](reference/), the cross-file rulings are the *What ten games said* section of
[conventions.md](conventions.md), and **C1**–**C20** below are entries in [captures.md](captures.md).

**Four of these are corrections rather than refinements, and they are the most valuable output of
the whole exercise: brief one's central reference does not exist, brief three's cycle key is one
game's habit, brief five departs from something the set never showed, and brief two has been
citing a precedent it does not have.**

## Amending Zero — the six, as the genre answers them

- **Item 1, the instruments in a second window: confirmed, and now countable.** Not one of the ten
  games ships a developer overlay of any kind. XCOM 2's own file says plainly that what exists
  either always shows or shows only while a mode is active, and what debug there is sits behind a
  console with a launch flag. The development-tool pattern was the right borrowing and the set has
  no competing answer.
- **Item 2, the camera: both halves are now evidenced separately.** The set splits by year, stepped
  in the four oldest and free-drag in the four newest — and the two complaints are mirror images.
  XCOM 2's most-endorsed interface mod exists to add free rotation; Tactical Breach Wizards shipped
  free-drag with no step and its players are on the forum asking for `Q`/`E` back, for the reason
  the older games had it. *Free yaw plus a keyed snap* is what the set supports, not a compromise
  between two camps. Nothing to change; the rider is that if the snap is ever cut as redundant,
  this is the evidence that it is not.
- **Item 3, the mouse drives the camera: the argument for it got stronger and changed shape.** It
  is not true that the genre binds right-click to cancel — Desperados III and Future War Tactics
  bind it to *move*, and Phoenix Point to move and cancel at once. What is true across the set is
  that **every game that puts a committing action on right-click produced a documented complaint
  about it**: Phoenix Point's is a mod that disables right-click-to-move so the button can only
  cancel, Future War Tactics' is a forum post asking to swap it in a game that cannot rebind
  anything. Nothing in ten games fires on right-click. Cite that rather than a convention that is
  not uniform.
- **Item 5, contrast: one addition to the rider.** Brief two's alarm ladder now also has to show a
  rung *falling*, not only rising — see the amendment to brief two — so the room left above a
  hostile body has to carry a state that changes in both directions, not just a five-step climb.

## Amending One — the readouts go on the things they describe

**Correction, and it is the central one.** The brief names *XCOM's hover* as the model for *show me
the terms*. **There is no such hover.** A guide screenshot opened at full resolution shows a
stacked breakdown docked at the bottom left of the screen under a bold `HIT 64%` headline — `AIM
+92%`, `HEIGHT ADVANT +20%`, `DEFENSE −40%`, `SQUADSIGHT −8%`, `LOW COVER −20%`, with a mirrored
damage column beside it — while the target itself carries only the floating percentage and a health
bar. The brief's central reference is a gesture nobody shipped.

**What to build instead, and it is a better fit than the hover was.** What a hover reveals is
verified in exactly **one** of the ten games. What has real support is **held-key disclosure**:
Into the Breach holds `Ctrl` for a unit's detail and `Alt` for the turn's resolution order, Phantom
Brigade holds `Ctrl` to split its folded number, Shadow Tactics and Desperados III hold `Alt` to
show every cone at once. Four games, three of them for exactly the *show me everything for a
moment* job. It also has the property the brief was reaching for and a hover card cannot give: one
gesture for every figure at once, rather than one card per figure, which is how this ends up worse
than the panel it replaces. **Provisional until C1**, which settles whether XCOM's docked list is
open by default or gated, and **C5**, which is the same question with a different answer available.

**Refinement, and it gives the brief an actual test.** The set complains about *distance* three
times in three unrelated games: Invisible, Inc.'s action-point figure sits above the agent rather
than at the cursor, so a player planning a long path looks away from where they are pointing; Into
the Breach's players have twice asked for undo to be moved further from end-turn; and the same
critique that faults Invisible, Inc. praises its context buttons in one line — your mouse never
leaves the area you are focusing on. So the rule is not *on the thing it describes*, it is **where
the cursor already is**. Those coincide for the hit chance and the cover icon. They do not coincide
for a figure about the soldier while the cursor is on a distant tile, and that is the case to design
for rather than discover.

**A second refinement, and it changes what the two cliffs look like.** The brief puts the reserve's
two cliffs on the pip row, per entry 067. The genre draws that same cliff **on the ground**: four of
the six grid games in the set band the reachable area by which point pays for it, and in three of
the four the band falls exactly at *can I still act when I arrive* — XCOM 2's blue is a move you can
still fire after and its yellow a dash that leaves nothing, Phoenix Point's blue keeps an action in
reserve and its yellow spends everything, Warhounds' blue is the first action and its yellow the
second. That is not a different figure from the reserve; it is the same question asked at the place
the player is asking it. **So the cliffs go on the move range as well as on the pips, and the ground
is the stronger of the two** — the pip row says what a soldier holds now, the banded range says what
they will hold *there*, which is the decision being taken. This stays inside the brief's own scope:
its *out of scope* line admits the two cliffs as the one exception because the rules already compute
them, and this draws those same two cliffs in a second place rather than adding a third figure.

**One consequence worth naming before it bites.** The move overlay is a graded tint today and a
graded field cannot show a cliff. That is the same smoothing mistake entry 067 found on the reserve
line, in the one place it costs most. **Provisional on C10**, which is the set's only candidate for
a game that bands a graded field and the one thing Future War Tactics is in the set for.

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

## Amending Three — the gesture set

**Correction.** The brief says *targets cycled on Tab* as though it were the genre's answer.
`Tab` cycles in XCOM 2 and in **no other game in the set**: Phoenix Point offers a list of visible
enemies along the foot of the screen, Phantom Brigade uses `Ctrl`+click, and the remaining seven
appear to expect the player to point at the body. Invisible, Inc. says why in a line — there is no
targeting mode to cycle within, because a shot is one click on one guard exactly as a move is one
click on one tile.

**Build the cycle key anyway, for this game's reason rather than the genre's.** A hostile here can
be a see-through body at a marker, which is materially harder to point at than a lit silhouette, and
that is a reason XCOM never had. Say so in the commit rather than calling it a convention.

**Refinement: the cancel design the brief assumes is the one thing this heading is unanimous on.**
Ten of ten cancel a mode, a prompt or an aim preview and never a spent point — XCOM 2, Invisible,
Inc., Phoenix Point, Warhounds and Shadow Tactics in the same words, and the two apparent exceptions
are the two games that hide nothing (see the amendment to brief five's law). So *right-click becomes
cancel, firing becomes a mode* is as well supported as anything in this document.

**Refinement: the key collision the brief flags has a third option now.** The brief asks whether the
reaction window's numbers move or the action bar is live only outside a window. Held-key disclosure
from the amendment to brief one adds a constraint rather than an option — whichever key is chosen
for *show me the terms* has to be held, not tapped, and must not be `1`–`9` or a letter already
bound. `Ctrl` and `Alt` are what the set uses and both are free here.

## Amending Four — who a shot would wake

**Refinement, and the brief's case is now the best-evidenced thing in the queue.** Among the games
in the set where being seen is what matters, the warning is drawn **on the destination tile before
the click**: Mutant Year Zero puts a struck-through mask icon on a tile that would expose you,
Invisible, Inc. shades every tile watched, peripheral or hidden. Shadow Tactics puts it on the cone
instead, on a held key. XCOM 2 draws nothing — and **Gotcha Again**, the mod that draws it, has
272,071 Steam Workshop subscribers, an order of magnitude more than any other community fix in the
reference set. That is this brief's argument made by somebody else's players, at a size nothing else
in the queue can match.

**What to take from the mod, which is vocabulary rather than justification.** Its icons all sit on
the destination tile and each names one situation: a red reticle if the enemy becomes shootable,
yellow if also flanked, a reticle added to an enemy's own overwatch icon with a marker on the tile
that would spring it. **C8** is the capture, and its value is that a community has already found out
which glyphs read at a glance on a hovered tile and which do not.

**One caution from the far end of the same spectrum.** Mutant Year Zero is the set's zero-telegraph
extreme: asked directly whether a player can anticipate an overwatch, the answer on the record is no,
and the listed counters are all indirect. Future War Tactics is worse — its reaction fire is
described by a reviewer who tracked it across a playthrough as arbitrary, with no clear rules,
sometimes several shots and sometimes none. **A graded reserve that is not visibly earned and not
visibly watched will read exactly that way**, bug or not, and this brief plus brief two are together
what stops it.

## Amending Five — the strip, and the pause, say only what the player knows

**Correction, and it changes what this brief is departing from.** The brief treats the strip as the
genre's answer and the dropped slot as the departure. **Zero of the ten reference games draw a
per-unit initiative strip.** Five alternate whole sides, two run a faction phase in whatever order
the player picks, one resolves both sides at once, one has no turns, and Tactical Breach Wizards
shows the enemies' order only while the cursor rests on the end-turn button. The strip was
attributed to Battle Brothers, which is Tier C and has no file. **So this game's turn structure has
exactly one precedent and it is outside the evidence set**, and entry 058's burden cannot be
discharged here by pointing at the genre either way. Entry 064's decision stands — it was the user's
and it was argued on contract 3, not on convention — but this brief should stop describing the slot
as a departure from a standard and describe it as a choice in a place the genre is silent.

**Refinement, and it promotes the banner.** The banner is the one turn-order element with positive
evidence anywhere: XCOM 2 says *enemy turn* over the whole phase, Into the Breach draws a full-width
`ENEMY TURN` bar across the middle of the screen with the mech roster still visible beside it.
Verified in two, contradicted by none, unknown in the rest. Entry 065's choice is better supported
than it looked when it was made — the banner is not a consolation for a strip that cannot be drawn,
it is what the genre reliably does here. **C7** and **C17** are the captures, and C17 would replace
the argued 0.6-to-1.2-second dwell with a measured one.

**One third answer, named so nobody rediscovers it and assumes it was missed.** Tactical Breach
Wizards' order preview on the end-turn hover withholds nothing and shouts nothing, which is a
cheaper way to be honest than a permanent strip. It is unavailable here for entry 064's own reason:
a preview of the full order hands back the count of hostiles nobody has found.

## Amending Six — the window has a default

**Refinement: the alternative this project is not taking, and why.** Tactical Breach Wizards'
reactions — if the two reported examples are real — are not a state any soldier can enter but named
abilities specific soldiers own and must have equipped. That is a real design and it is the opposite
of this game's, where `ReactionWindow.Appraise` has to score arbitrary combinations of soldiers and
options. The reason not to take it is particular to this project rather than obviously superior, and
it is worth one line in the commit: a scored window is what makes a *default answer* possible at all,
and a per-ability reaction has nothing to default to.

**Refinement: give the arc an adjust step.** Both shipped precedents for drawing your own held arc
have one — Phoenix Point adjusts the cone's angle with `Ctrl`+scroll before confirming, and
Warhounds' own guides single out fast enter, adjust and cancel as what makes overwatch usable
mid-fight. Here `V` and `HoldArc` take an arc in one press with no adjust, which is faster than both
and gives up the thing both games thought worth building. **Convention**, and cheap. This is
arguably brief two's or a job of its own rather than this one's; it is recorded here because this is
the brief that touches reactions.

**One thing the genre cannot help with, stated so a session does not go looking.** **Nobody in ten
games documents what a reaction looks like at the moment it fires.** All ten gap lists ask for the
same clip and not one has it. The window this game already has — reactors named, options scored, a
tick clock, the route drawn with the tick each step lands on — is the one place this interface is
unambiguously ahead of the genre, and there is no precedent to copy for the resolution half. Build it
on this game's own reasoning and expect to be the reference.
