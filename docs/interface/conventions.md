# What the genre does, and which of it applies here

Turn-based squad tactics has a settled interface grammar. This says what it is, what this game
already does, what the asymmetry of contract 3 changes, and what to build. One section per
question a player meets, in the order they meet it.

Read [../map.md](../map.md) and [../subprojects/interface.md](../subprojects/interface.md) first.
The queue of jobs that follow from this is [briefs.md](briefs.md).

## What a standard is for

A convention is worth following because **the player arrives already knowing it**. That is the
whole of its value, and it means a convention is cheap to follow and expensive to break for no
reason.

**The user settled the rule in entry 058: the convention is the starting point, and a departure
has to argue its case.** The default in doubt is the convention. This game will modify
conventions to suit its subject; it will not invent where a player already knows what to expect.
So every recommendation below is one of two things and says which:

| | |
|---|---|
| **convention** | The genre's answer, taken as it stands. No case to make; the case is that a player has met it before. |
| **departure** | Not the genre's answer, and the reason this game needs it is given. |

A handful of sections have no convention to depart from, because no game in the genre had the
thing to show. Those carry the departure's burden anyway — a recommendation with nothing behind
it but reasoning is exactly the kind that has to argue — and each says what the nearest relative
is and what it lends.

**The one finding that outranks the other nine.** Every figure in this game is a line of text in
a panel at the top left. `BattleHud.DrawLines` assembles about twenty of them, several carrying
six or eight facts separated by whitespace, and the only numbers drawn at the thing they describe
are the AP costs on the tiles. The genre's interface is *spatial*: the hit chance sits on the
target, cover sits on the tile, action points sit on the soldier, and the panel holds only what
has nowhere better to be. This is not decoration. A game whose subject is information cannot
teach a player to read a battlefield with a readout that requires them to look away from it. It
is the first brief, and it is a **convention** the game has not yet adopted rather than one it
chose to leave.

---

## The camera

**Standard.** Split, and the split is historical rather than considered. XCOM 2 turns the camera
in ninety-degree steps on `Q` and `E`, animated, with two pitch levels and no free rotation —
and the most-installed interface mod on its Nexus page is Free Camera Rotation, which adds
hold-to-turn and configurable step angles. Jagged Alliance 3 turns freely while the middle mouse
button is held and steps on `Q`/`E`, plus three view presets. Battle Brothers and Into the Breach
do not rotate at all. Silent Storm rotated freely in 2003.

**What the stepped camera was ever for.** Sprites. The older line drew each unit for a fixed
number of facings, so the camera could only stand where the art existed. Nothing in a 3D game
inherits that constraint, and what survives of the convention is two real benefits: a grid reads
the same way from a bearing it agrees with, and a step is bindable to a controller.

**Here.** Entry 053 snapped yaw to the six hex bearings so held arcs stay legible; entry 057
overruled it. Pitch is fixed at 55 degrees, zoom is distance in metres, and the camera never
animates because a capture has to land on the same frame every run.

**The asymmetry.** None. The camera is the one part of this interface the enemy's knowledge does
not touch.

**Recommendation** — **convention**, in the shape the genre's better half has it. Free yaw on a
drag, as Jagged Alliance 3 and Silent Storm do and as the most-installed XCOM 2 interface mod
adds. Keep `Q`/`E` as an animated *snap to the next bearing*: on a free camera a stepped key
stops being a limitation and becomes the affordance the genre's step was actually providing,
which is *put the grid square with the screen*. Allow pitch within a clamp that keeps a wall a
wall. Make edge-pan a setting, default off — at close zoom under a pitched camera an accidental
edge-pan loses the soldier you were looking at.

**Entry 058 closed the argument underneath this and it should not be reopened.** The case for the
snapped camera was that arcs and facing wedges smear between bearings; the user held that smooth
matters more. So if an arc proves illegible from an odd angle, **the answer is a better arc**,
never a snapped camera again.

**What *smooth* means, as an argument and not a measurement.** The genre's keyed step is a single
beat: on the order of 300 to 450 degrees per second, so a sixty-degree turn lands in about a
sixth of a second and reads as a turn rather than a cut. A drag is one to one with the hand,
around 0.2 to 0.4 degrees per pixel. Neither figure has been measured here and both are the
person-at-the-keyboard's to settle.

**One thing no convention covers:** every camera animation needs a settled state the capture can
wait for, or `--shot` forces it instantly. Entry 053's fifth decision is byte-determinism, and it is
worth more than a smooth transition in a screenshot.

## Selecting and ordering

**Standard, and unusually uniform.** Left-click selects one of yours. Hovering a reachable tile
previews the path with its cost. **One** click commits, and no game in the list offers an undo —
the points already spent are the game, and the genre decided long ago that a move you can take
back is not a decision. Attacks are different: they are a *mode*, entered from an action bar or a
key, with target cycling on Tab and an explicit confirm. So confirmation sits on the shot and not
on the move, because the shot is the one that announces you.

**Right-click cancels.** In XCOM 2 and Jagged Alliance 3 it backs out of a mode or clears a
selection. It does not fire in any game in the list.

**The action bar** is a row of icons along the bottom, bound to `1`–`9`, each showing its cost and
a tooltip of what it does.

**Here.** Left-click moves, **right-click fires**, and every other action is a letter — `C`, `Z`,
`X`, `V`, `B`, `T`, `L`. There is no action bar and no targeting mode, so a shot is committed by
one right-click with the cursor over a body, and the numbers `1`–`9` are bound to reaction-window
answers instead.

**The asymmetry.** It bites once. A move commits, and in a game where the enemy is drawn only
when found, a committed move can walk into an arc the player had no way to see. The genre's
no-undo rule was written for a game where everything relevant was on screen. Softening it is
tempting and wrong: the fog *is* the game, and a rewind would make reconnaissance free. What is
owed instead is the shown-before-committing figure — attention on the destination tile is already
there, and who would hear you is already there. See Readouts.

**Recommendation** — **convention**, and it is not cosmetic. Right-click becomes cancel. Firing
becomes a targeting mode: an action bar entry and a key, Tab to cycle bodies, a confirm to
commit. This also unblocks the mouse camera, since a plain right-drag is the gesture the genre
uses for orbit or pan and it is currently spent on the most irreversible action in the game.

## Turn order and whose go it is

**Standard, and here the genre really is split in two.** XCOM, Phoenix Point, Mutant Year Zero
and Into the Breach alternate whole sides, so there is no order to show — a banner says whose go
it is and each soldier carries its own points. Battle Brothers and the older line interleave by
initiative, and every interleaving game draws the same thing: a strip of portraits in order along
the top edge, the current actor picked out, and the round boundary marked. Battle Brothers
recalculates initiative every round from fatigue and armour, which is why its strip needs a
slider and why the round mark matters — the order you are reading is only good until the round
ends.

**Here.** Interleaved, initiative rolled per round, and there is a strip: `DrawOrderStrip`. A
hostile nobody has found holds a slot reading `?`, with no name, roll or reserve.

**The asymmetry.** This is the one place in the interface where the *count* of the enemy leaks,
and the genre has nothing to say about it, because every interleaving game in it starts with
everybody visible.

**Recommendation** — **convention** on the round boundary, **departure** on the slot, and the
departure is the user's decision in entry 064: **the strip draws only what the player knows.** A
hostile nobody has found holds no slot at all, not even an anonymous one. From the player's side
their own soldiers simply act in sequence until an enemy does something they can perceive.

This was argued the other way first and the argument was wrong. It ran: dropping the slot loses
the interleaving the strip exists to show. It does not, because the interleaving a player can act
on is the interleaving of soldiers they have found, and that is still drawn. What a slot for an
unfound hostile adds is two things the player has not earned — that an enemy exists, and roughly
where in the order it acts — and a mark that says *somebody acts here* is a weaker claim than a
`?` portrait only by degree. Neither is a fact about the player's own side, which is the test
contract 3 actually applies.

**What follows from it, and it has to be built or the strip reads as broken.** An unfound
hostile's turn passes with nothing on screen and time moving. That is the honest presentation and
it is the game, but it means anything that turn does which the player *can* perceive — a noise
heard, a shout picked up, a soldier of theirs shot at — has to register somewhere, or a player
sits through a pause with no account of it. And the strip is redrawn from what is known *now*, so
a hostile found mid-round appears in the order at once, which reads as a discovery rather than as
bookkeeping.

**The pause itself needs an indicator, and its shape is not obvious — the user settled it in
entry 065.** *One indicator per contiguous stretch of hostile activity, never one per turn.* It
appears when control leaves the player's side and clears when it returns.

The reason it cannot be per turn is that a per-turn mark hands back exactly what dropping the
slot withheld: a player who counts the appearances has the enemy's count and their rough place in
the order again. Showing it only for hostiles nobody has found is worse still, because then its
*presence* is the tell. So it is the same indicator for every hostile turn, known actor or not,
and it is one indicator for a run of them.

**This is the alternating games' phase banner, and that is the convention it takes.** XCOM says
*enemy turn* over the whole phase rather than per unit. An interleaved game would normally have
no use for that, because its strip carries the identity; here the identity is the one thing that
cannot be shown, so the presentation collapses onto the banner. Two details it needs:

- **A message, with an activity indicator inside it — not an indicator alone.** A spinner on its
  own claims *the software is busy*, which is a bug report. The words are what claim *somebody
  else is playing*. The spinner earns its place only on a stretch long enough to look frozen.
- **A minimum dwell**, or a resolution that finishes in a frame flashes the banner and is worse
  than drawing nothing. The games that do this hold it for roughly 0.6 to 1.2 seconds, which is
  an argument rather than a measurement. Captures and headless runs skip the dwell entirely, by
  the same settle-before-shot rule every other animation here obeys.

Mark the round boundary, which is a plain **convention** borrowed from Battle Brothers and is
missing.

## What of the enemy is drawn

**Standard, modern tactics: binary, and generous.** XCOM hides a pod completely until it
activates, then draws it permanently with full statistics *even out of line of sight*. There is
no fog on a known enemy and no last-known-position marker anywhere in the modern pair. Mutant
Year Zero draws each enemy's detection radius, but only while the squad is in stealth mode, and
shrinks the circles when you switch the torches off.

**Standard, turn-based stealth — a different shelf, and the one that transfers.** Invisible Inc
draws every guard's vision cone with striped shading, and it distinguishes three things this
game's rules also distinguish: seen, *peripheral* — tiles that look watched and are not — and
*noticed*, a state short of seen in which the guard will come and look next turn. Its alarm runs
on a ladder of six, and each rung has five sub-levels that are deliberately given no effect and
no display, so that the only thing a player ever reads is a transition. The Commandos line —
Shadow Tactics, Desperados III — draws a cone per guard plus a meter over the head that fills as
you are noticed.

**Here.** Three states already, chosen in entry 053: a body while one of ours has eyes on it, a
see-through body at its marker with the credence beside it otherwise, and nothing at all before
anybody has heard a thing. The attention field is painted per tile at the value the rules give
that tile, which is finer than any cone in the genre. And the marker the enemy holds on *us* is
drawn in both modes — section 07 names it as the one thing of theirs a player sees.

**The asymmetry.** Total, and this is where the game has no ancestor. The genre draws what you
know about them. This game additionally draws what they know about you, and the rules carry a
five-rung ladder — `Unaware`, `Suspicious`, `Searching`, `Alerted`, `Engaged` — that the HUD
currently prints as a word inside a text line.

**Recommendation** — **departure**, and the only one in this document that is a departure from
nothing: the genre has no convention here, because no game in it has a contact file. So each of
the four below names what it borrows and from where, which is the closest thing to a convention
available.

- **Put the rung on the body.** A five-step ladder drawn at the enemy it belongs to, with
  Invisible Inc's discipline: the certainty behind it is never shown, only the transitions, which
  is exactly what contract 3 already requires and what `ReadoutFor` already returns. A rung that
  moves while you watch is the most informative single thing this game can draw.
- **Draw their marker as a ghost of your own soldier.** They believe you are at a place you have
  left. Drawing that as a translucent copy of the soldier it is wrong about, with a line to where
  the soldier actually is, is the picture the game is about, and nothing in the genre draws it
  because nothing in the genre has it.
- **Borrow *noticed* explicitly.** `Suspicious` is the rung a player will misread as *seen*, and
  Invisible Inc's answer — a distinct mark meaning *coming to look, does not know what for* — is
  a convention that already exists for exactly this state.

**And it answers a View open question.** Draw a hostile's held arc whenever the hostile itself is
drawn. The stealth shelf draws what a guard will do, because beating it is the game; the tactics
shelf hides it, because there the enemy shoots on its turn anyway. This game is on the first
shelf. A player who walks into an arc held by a soldier they could see holding it will say the
picture lied, and they will be right.

## Reactions

**Standard: overwatch is a state, not an interaction.** You set it, and it resolves during the
other side's turn with a camera cut to the shooter and no input from you. The one line in the
genre that hands control back mid-turn is the older one — Jagged Alliance 2 and Silent Storm
*interrupt*: your soldier is handed to you part way through the enemy's move with a few points,
and famously without any explanation of why, whose initiative won, or how long you have. Into
the Breach sits at the other extreme and shows every enemy's exact next action before you commit
to anything.

**Here.** A window: the reactors by name, their options scored with `ReactionWindow.Appraise` —
the same call the recommendation is made with — a tick clock, the committed route drawn out of
the mover with the tick each step lands on, and Tab / number / space to answer. Entry 049 built
it and it is already better than the interrupt it descends from, because the clock and the scores
are visible.

**The asymmetry.** Mild here and worth naming anyway: the window offers every reactor in it
whichever side they are on, which is right for a harness that drives both sides and is not what a
player should be handed.

**Recommendation** — **convention** where the genre has one, **departure** where it does not.

- Keep the window. Take Into the Breach's lesson: the clock is the thing to draw, on the map, on
  the route, which View already does.
- Give it a **default answer and one key**. Every option is already scored by the same call that
  makes the recommendation, so the common case — take the recommendation — should be one press,
  not a Tab, a number and a space. This is the genre's *state, not interaction* convention
  recovered as a default rather than as a limitation.
- **By default a player answers only their own side.** Answering for the other lot is the same
  family as the orders readout: an instrument, and it belongs behind the same switch. That
  settles the View open question with a genre reason rather than a tidiness one.

## Movement and shooting animation

**Standard.** The soldier walks the path, the camera follows only if the mover would otherwise
leave the screen, and every game in the list ships a speed setting — XCOM 2's is Zip Mode, which
exists because the animation is the part of a long campaign a returning player wants shortened.
The camera cut to a reaction shooter is the single most complained-about behaviour in the genre,
and the lesson from the complaint is narrow: cut to the thing that surprised you, and cut back.

**Here.** Movement is instant. Entry 040 says the mover has not stepped until the window
resolves, so the walk is the *resolution* drawn over time.

**The asymmetry.** One consequence, and it is a gift rather than a problem. A walk that takes
time is a walk a reaction can interrupt visibly, so the ticks the reaction line quotes can be
drawn as the soldier passes them. The animation stops being decoration and becomes the readout
for a rule.

**Recommendation** — **convention**, with one **departure** in how the pace is set.

- **Price the walk in metres per second, not in seconds per move.** One horizontal world unit is
  one metre by contract 5, so a pace is available for free and a fixed duration per move would
  make a two-hex step and an eight-hex step look equally urgent. A tactical walk is about 1.4
  metres per second and a hustle about 2.5. Both are arguments, not measurements.
- Ship the instant setting, on Zip Mode's precedent, and force it in captures and headless runs.
- Camera follows the mover only when it would otherwise leave the frame; cut to a reactor and
  back.

## Readouts

**Standard: one number, at the thing, expandable.** XCOM 2 puts a single hit chance on the target
card and hides the modifier arithmetic behind a hover; cover is a shield icon on the tile; points
are pips on the soldier. Battle Brothers is the exception that proves it — it shows every modifier
in a long tooltip, and it is also the game in the list with a reputation for opacity.

**Here.** The audit in `../subprojects/view.md` shows that almost everything the AI weighs is on
screen, exactly, which was the right thing to check and it passed. What was never asked is
*where*. Twenty-odd lines, top left, several of them carrying six or eight facts.

**The asymmetry.** It is a trap in this direction. A game about information invites the
conclusion that more readout is more information, and the genre's answer is that quantity is not
information — **placement** is. There is also a real constraint the genre does not have: an
exposure figure is exact because it is about you, an alarm is a rung because it is not, and a
panel of similar-looking lines makes those two look like the same kind of fact. Putting each at
the thing it is about makes the difference visible without a word of explanation.

**Recommendation** — **convention**, and it is brief one.

- Hit chance and expected worth on the target. Cover and cost on the tile. Points, reserve and
  held arc on the soldier. The alarm rung on the enemy. Attention on the ground, where it already
  is.
- The panel keeps only what has no place on the map: the mission, the clock, the weapon.
- Headline at the thing, breakdown on demand. That is XCOM's hover, and it answers *how much
  arithmetic to show* without having to choose between the audit and the genre — the audit's
  figures all stay reachable, they just stop being simultaneous.

**One gap the genre would not have tolerated.** Firing is the loudest thing a soldier can do,
the scorer charges the shot for what it announces, and there is no preview of who it would wake.
XCOM tells you before you break concealment; this game does not, and it is the game where it
matters most. Entry 012's second item, still open, and it is brief four.

## Points, and the reserve

*Added after the first draft, on the user's prompt — entry 067. It is the section the original
game list could not have produced; see the shelves below for why.*

**Standard.** Points are pips on the soldier and the count is small. XCOM 2 gives two actions and
draws two; Battle Brothers and the older line carry a number and a bar. Overwatch costs a fixed
action, so no game in the brief's list has to draw *what is left to react with* — spending your
last action on overwatch is the whole transaction and there is nothing graded about it.

**The one shipped game with our mechanic removed the problem rather than drawing it.**
Warhounds (2026), which is XCOM- and Jagged Alliance-inspired, banks a reserve for overwatch:
declaring it **commits the operator's remaining action points** and draws a firing area in front
of them. So the bank exists and it is all or nothing. Ours is graded, and that is the difference
that puts this section here.

**Here, and the rules already call it a ladder.** `ReactionModel.Banked` takes what a soldier did
not spend, keeps `ReserveFraction` of it, and returns nothing at all below `ReserveFloor`. Its own
remarks say why that shape was chosen: *the floor makes this a step rather than a slope, and the
step is the whole reason anything weighing a turn has to ask rather than multiply* — ending a turn
nine points up banks nothing, fifteen banks ten, which is most of a snap shot. `ReserveFraction`
is set at seven tenths specifically to put the three rungs of the movement economy — hold
everything, spend about half, spend it all — on either side of the fire mode prices. The reserve
line prints `reserve 24, 17 if you stop here`.

**The asymmetry.** None. This is the player's own soldier's own points, exact in both directions
by contract 3, which is why it can be drawn as precisely as the rules compute it.

**Recommendation** — **convention** in its form, **departure** in what the form carries. Pips on
the soldier, which is the genre's answer. But the row carries **two cliffs marked on it**, which
no game in the genre needs:

- the point below which stopping banks **nothing** — `ReserveFloor` against `Banked`;
- the point at which the bank first affords a **shot**, and then the better one — `Banked` against
  the loadout's fire mode prices, which is the second cliff `Banked`'s own remarks name.

A player reading that row sees *spend down to here and I can still snap, to here and I can still
take an aimed shot, past here and I am holding nothing*. That is three decisions in one glance,
and it is the same object as the alarm ladder: discrete steps with a threshold on them, which is
why a number is the wrong drawing for either. It is also why the ladder was the right instinct
here and not merely an analogy — the rules are already stepped, and the interface is what has
been smoothing them.

**Two things Warhounds does with the arc rather than the points**, both **convention** and both
cheap: overwatch enters cone placement directly rather than through a nested menu, and its guides
single out fast enter, adjust and cancel as what makes it usable mid-fight. Here `V` and
`HoldArc` take an arc in one press with no adjust step.

**Read, not played.** Everything about Warhounds above comes from its store page, wiki and
community guides rather than from the controller, and it should be checked before anything is
built on the detail. What it is used for here is narrow and safe: that a shipped game with a
comparable bank chose all-or-nothing, which is a design fact its own store page states.

## Debug and developer overlays

**Standard: shipped games ship none.** What exists is behind a console — XCOM's requires a launch
flag — and the second-window pattern is not from this genre at all. It is a development-tool
pattern, and it is the right one to borrow, because the alternative on offer is a keyboard toggle
that a player will find.

**Here.** The orders readout prints every turn the AI has taken with each term of its appraisal,
and `BattleHud.TurnLines` says in its own remarks that any interface built for a player drops it.
It is drawn only when omniscient. The legend and the mode line are a tester's and are drawn
always.

**The asymmetry.** It is the reason the line is easy to draw here. Anything that is the enemy's
knowledge is an instrument by construction. Anything that is ours can be a player's.

**Recommendation** — **departure**, and a small one: the genre has no overlay convention to keep,
so this follows the development-tool pattern instead. Entry 057's item 1 is right. The instrument
window takes the orders readout, the appraisal terms, the mode line, the
legend and the seed. The game window keeps the mission, the turn order, the soldier's situation,
the cursor, the shot and its worth, and reactions. View's brief already has the test for which
side a readout falls on — *would a player who never presses `O` want it* — and it is a good one.

---

## The games, and the two shelves

The brief's list is the tactics canon: the modern XCOM pair, Phoenix Point, Jagged Alliance 3,
Battle Brothers, Into the Breach, and the older line behind them. It is the right list for
cameras, action bars, turn order and animation, and those sections above lean on it.

It is the wrong shelf for the thing this game is *about*. Every game on it draws the enemy the
moment a unit sees one, and none of them has a rung, a marker, or a contact file. The conventions
that transfer to the sections that matter most here come from turn-based and real-time stealth:

| | |
|---|---|
| **Invisible, Inc.** | The closest relative in existence. Vision cones with peripheral tiles distinguished, a *noticed* state short of seen, and an alarm ladder whose sub-levels are hidden on purpose so that only transitions are ever read. That last is contract 3's coarse rung, designed deliberately by somebody else and shipped. |
| **Mutant Year Zero** | Detection radii drawn only in the mode where they matter, and shrunk by an action the player takes. Stealth as a non-twitch tactical decision, which is this game exactly. |
| **Shadow Tactics / Desperados III / Commandos** | Real-time, so the input conventions do not transfer, but the drawing does: a cone per guard, and a meter over the head that fills as you are noticed. |

**A third shelf, and the first draft did not know it existed: what shipped while this was being
built.** The canon list stops at games old enough to have a settled reputation, which is exactly
what makes it a canon and exactly what makes it blind to the two games in the genre closest in
time. Both were added on the user's prompt.

| | |
|---|---|
| **Warhounds** (2026) | XCOM- and Jagged Alliance-inspired, and the only shipped game found with a reserve like ours: declaring overwatch commits the operator's remaining action points. It is all or nothing where ours is graded, which is the whole of the *Points, and the reserve* section above. Also: cone placement entered directly rather than through a nested menu, with fast adjust and cancel. |
| **Future War Tactics** (2025) | Colour-coded zones for movement and attack radius, which is the thing this game already does with graded tints rather than bands. Little else here that the canon does not say better. |

**The lesson about the list itself is worth more than either row.** The reserve section exists
because somebody asked whether a game outside the list had solved a problem we had, and one had —
by removing it. A canon is a list of games whose conventions are *settled*, which is what makes it
the right starting point and also guarantees it is silent on any mechanic newer than the canon.
The next question of this shape should be asked the same way: which shipped game has this
mechanic, rather than which famous game has something like it.

**Nothing here is a proposal for Core.** Every recommendation above is answerable from a query
that exists — `ReadoutFor` for the rung, `Contact.LastKnownPosition` for the marker, `Reachable`
and `CostTo` for the tile, `Appraise` for the window's default. The one thing the interface
cannot show is already an open entry rather than a new one: entry 012's second item, who a shot
would wake.

**Where this came from.** Play, plus the interface documentation and community threads for
[XCOM 2's Free Camera Rotation mod](https://www.nexusmods.com/xcom2/mods/1),
[Jagged Alliance 3's camera controls](https://steamcommunity.com/app/1084160/discussions/0/3807280781155752599/),
[Klei's design deep dive on the alarm system in Invisible, Inc.](https://www.gamedeveloper.com/design/game-design-deep-dive-alarm-systems-in-klei-s-i-invisible-inc-i-),
[Battle Brothers on initiative and turn order](https://battlebrothersgame.com/tactical-combat-mechanics/),
and [Mutant Year Zero on stealth and detection](https://www.mutantyearzero.com/news/master-the-stealthy-approach/).
