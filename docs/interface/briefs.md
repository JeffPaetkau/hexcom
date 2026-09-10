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
version that works. If the six have already landed, it is a review list.

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

**Out of scope.** The alarm rung on the body, which is brief two and depends on this landing
first. The instrument window's contents, which are entry 057's item 1. Any new figure — this
moves what exists and adds nothing.

**How to know it worked.** With the cursor on a hostile at default zoom, the hit chance, the
expected worth and the cost of getting there are all readable without the eye leaving the target,
and the panel is short enough to read in one glance. A capture at `--fit` has no text over the
map that is not attached to something on it.

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

## Five — the strip says what it knows

**Branch** `view/order-strip`. **The genre's answer on the round mark; a departure on the
anonymous slot**, which the genre never needed because its strips draw everybody.

**What it is.** Initiative is rolled per round and the strip shows the interleave, which is why
an interleaving game draws a strip at all. Two things are missing and one is wrong. Missing: the
round boundary, without which the order a player is reading looks more durable than it is —
Battle Brothers marks it for the same reason, and recalculates initiative every round as this
does. Wrong: an unfound hostile holds a portrait-shaped slot with a `?` in it, which reads as *a
soldier you have failed to identify* and claims more than the rules do.

**The seam.** `BattleHud.DrawOrderStrip`.

**Settle first.** The View open question, and the answer the conventions give is *keep the slot,
change its shape*. Dropping it loses the interleaving. An anonymous narrow tick reads as
*somebody acts here*, which is true — turns are taken in the open. Whether the count of ticks is
itself too much to give away is the part with no precedent, because every interleaving game in
the genre starts with everybody visible; decide it, and say which way in the entry.

**Out of scope.** What is drawn on the map, which is brief two.

**How to know it worked.** A player can say whose go is next, when the round turns over, and that
somebody they have not found acts between two of theirs — without being able to count a squad.

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
