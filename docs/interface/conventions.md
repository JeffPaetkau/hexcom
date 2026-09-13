# What the genre does, and which of it applies here

Turn-based squad tactics has a settled interface grammar. This says what it is, what this game
already does, what the asymmetry of contract 3 changes, and what to build. One section per
question a player meets, in the order they meet it.

Read [../map.md](../map.md) and [../subprojects/interface.md](../subprojects/interface.md) first.
The queue of jobs that follow from this is [briefs.md](briefs.md). The evidence underneath it is
ten files under [reference/](reference/), one game each; what a picture would still change is
ranked in [captures.md](captures.md), cited below as **C1**, **C2** and so on.

**Most recommendations here rest on published material; the ones pass two reached rest on
pictures.** The documentary pass ran first and carried no `observed` tag, by design. Pass two
captured eleven of the twelve entries above the line in `captures.md` from the user's own copies
of five games. Where a picture settled a recommendation, the section says so and names the capture,
and the shot itself is in `reference/shots/<game>/`. A recommendation still resting on a
`remembered` claim is marked **provisional**, says so, and names the capture-list entry that would
settle it. A recommendation with no such mark rests on a `verified` source, on several files
agreeing, or on an `observed` shot.

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

## What ten games said, heading by heading

*Written by the synthesis pass, which is the only session that could: a convention is a thing a
player arrives already knowing, so the unit of evidence is the set agreeing, and no single
reference file can see that. Ten files under [reference/](reference/), one game each, against the
same ten headings. The ranked list of what a picture would still change is
[captures.md](captures.md), and entries below cite it as **C1**, **C2** and so on.*

**Read the counts with the right denominator.** *The set agrees* means the games that have the
mechanic agree, not that ten out of ten said the same thing. Eight games with no alarm ladder are
silent on how to draw one; they are not eight votes against it. Where the denominator is small
this section says so, because a two-for-two is a different kind of evidence from a nine-for-ten
and the difference decides how much weight a recommendation can carry.

| # | Heading | Verdict | The count |
|---|---|---|---|
| 1 | Screen furniture | **unanimous** | every game puts its furniture at the edges and leaves the centre to the map; every game scopes a soldier's own facts to that soldier's card |
| 2 | The soldier | **unanimous on cancel, empty on hover** | ten of ten cancel a mode and never a commitment; what a hover reveals is verified in **one** game of ten |
| 3 | The target | **split, and against the assumption** | three of ten show a hit chance as a percentage; five show none at all; two show a number that is not one or is not established as one |
| 4 | The tile | **unanimous where it counts** | four of the six grid games band the move range by *which point pays*; drawing the warning to be seen on the destination tile is two of the three games that need one, and the third's absence is the set's most-subscribed mod |
| 5 | The enemy | **nearly empty — one of ten, found by a picture** | *pass one said zero; C12 found one.* **One** of ten leaves a marker at a lost enemy's last-seen place that survives into the next turn (Future War Tactics); none is shown to decay or move. A state short of seen is two of ten, but two of *two* among games that have one |
| 6 | Turn order and time | **empty on the strip, and the banner is now four** | **zero of ten** draw a per-unit initiative strip. The phase banner is the only turn-order element with positive evidence anywhere: verified in two, observed in two more (C4, C7) |
| 7 | Reactions | **split, and the split is by whose arc it is** | two of ten draw the player's *own* held arc on the ground; **zero** draw a hostile's, and one game's players asked and were refused. *One* game now has the moment one fires on film (C4): no camera cut |
| 8 | Camera and input | **split by year, and both directions get asked for** | stepped in the four oldest, free-drag in the four newest; XCOM 2's players modded free rotation in, Tactical Breach Wizards' players are asking for the step back |
| 9 | Confirmation and refusal | **unanimous** | one modal confirmation for a tactical action in ten games. Refusal is a disabled affordance or a rule drawn on the world, never a dialogue |
| 10 | What players added | **unanimous** | every counted community fix in the set is a legibility fix. Nobody modded a new turn order, cover system or hit formula into any of these games |

### The one law the set obeys without exception

**A game in this set lets a player take something back exactly as far as it told them the
truth.** Seven of the ten hide something — a pod, a guard, a patrol, a contact — and not one of
them permits an undo of a committed action; the safety net is a quicksave, an Ironman toggle, or
nothing. The three that hide nothing inside a battle all permit free revision right up to
resolution: Into the Breach's unlimited pre-fire move undo plus one turn reset, Tactical Breach
Wizards' unlimited rewind, Phantom Brigade's draggable and deletable orders, which stop being
editable at exactly the moment its five-second certainty window starts running. Warhounds is the
tenth and does not break it — it has no undo either, and **C6** confirmed its fog: first contact
is announced as `Enemy squad detected`, so it hid a squad until then.

**This is entry 058's no-undo ruling arrived at by mechanism rather than assertion, and it is
worth more than the ruling.** A rewind is cheap in a game where nothing was hidden when the
choice was made, and expensive in one where it makes reconnaissance free. Tactical Breach
Wizards is the case a future session will be tempted to cite as a counter-example; its rewind is
*enabled by* its lack of fog, not independent of it. Do not soften the rule here, and do not
re-argue it — but do notice what the law implies in the other direction: **this game owes its
player the figures before the click precisely because it will not give them the click back.**
That is not a nicety. It is the other half of the same bargain every game in the set has struck.

### Heading by heading, and what moved

**1. Screen furniture — unanimous, and this game is the outlier.** Every layout in the set is a
set of edges: a left column and a right corner (Invisible, Inc.), a top-left stack and a
bottom-left card (Into the Breach), portraits down one side and an item panel in a corner (Future
War Tactics, Shadow Tactics, XCOM 2). Nothing sits in the middle in any of them. Second and
sharper: **a soldier's own facts live on that soldier's card**, not in a shared panel — Mutant
Year Zero draws each character's action points above that character's own ability bar rather than
gathering them, Into the Breach puts each mech's weapons inside that mech's roster row, Phoenix
Point's whole bar is soldier-scoped and appears only on selection. The twenty-line panel at the
top left is not a variation on this; it is the thing the whole set avoids, and the avoidance is
structural rather than stylistic.

**2. The soldier — unanimous on cancel, empty on hover.** Cancel backs out of a mode, a prompt or
an aim preview, and never out of a spent point: XCOM 2, Invisible, Inc., Phoenix Point, Warhounds
and Shadow Tactics all say so in the same words, and the two apparent exceptions are the
undo-games from the law above. **But what a hover over an ability actually reveals is verified in
exactly one game of the ten** — Shadow Tactics, a tooltip with cost and effect. Phoenix Point's
own developers say hovering rebuilds the ability bar's canvas and no source says what appears in
it; XCOM 2's is remembered; Phantom Brigade's, Tactical Breach Wizards' and Warhounds' are
unknown; Into the Breach replaces hover with two held keys, `Ctrl` and `Alt`. **Brief one is
about to pick one gesture for *show me the terms* and the reference set does not contain a
verified example of the gesture it was told to copy.** See the Readouts section below and
**C1** — which, with **C5**, has since settled it: in both games photographed aiming, the terms
need no gesture at all, because they are open the moment the aim is.

**3. The target — split, and it flips the section that cited it.** Three games show a hit chance
as a percentage (XCOM 2, Mutant Year Zero, Warhounds); five show none at all, three of those five
because nothing is rolled (Invisible, Inc., Shadow Tactics, Into the Breach, Tactical Breach
Wizards) and one because it draws dispersion as two concentric circles instead (Phoenix Point);
and two show a number that is not a hit chance (Phantom Brigade's damage effectiveness) or is not
established as one (Future War Tactics). **A hit-chance percentage is the tactics canon's answer,
not the genre's**, and the two newest games in the set removed it on purpose. This game keeps
one, and should — `GunneryModel` computes a real probability and contract 3 makes it the player's
own side's knowledge, exact by right. What does not survive is the claim that *one number with
the breakdown on demand* is a convention. It is one game's answer, and see Readouts for the
failure mode the set records twice. *Pass two sharpened this rather than reversed it:* the two
games photographed aiming (**C1**, **C5**) both show one figure at the target and its terms open
beside the action, not on demand. *One figure, terms open while aiming* is two of two among games
that show a hit chance and were captured.

**Target cycling is one game of ten.** `Tab` cycles in XCOM 2. Nowhere else in the set is a
cycle-target key documented at all: Phoenix Point offers a list of visible enemies at the foot of
the screen, Phantom Brigade uses `Ctrl`+click, and the other seven appear to expect the player to
point at the body. Brief three carries *Tab to cycle bodies* as though it were the genre's
answer; it is XCOM's.

**4. The tile — unanimous where it counts, and it hands the reserve a better drawing.** Four of
the six grid games with a point economy band the reachable area by **which point pays for it** —
XCOM 2 and Phoenix Point and Warhounds all in blue and yellow, Mutant Year Zero in white and
orange — and in three of those four the band falls exactly at *can I still act when I arrive*.
That is the same cliff the reserve has, drawn on the ground instead of on the soldier. See
**Points, and the reserve**, which is where it changes a recommendation. **C10 made it five of
six:** Future War Tactics, which the set carried as its one candidate for a graded field, draws its
movement zone as two nested outlines on square tiles with no tint at all.

The other tile finding is the set's strongest single piece of quantitative evidence. Among the
games where being seen is the thing that matters, **the warning is drawn on the destination tile
before the click**: Mutant Year Zero puts a struck-through mask icon on the tile that would
expose you, Invisible, Inc. shades every tile watched, peripheral or hidden. Shadow Tactics puts
it on the cone rather than the ground, on a held key. XCOM 2 draws nothing at all — and **Gotcha
Again**, the mod that draws it, has 272,071 subscribers, more than any other community fix in the
set by an order of magnitude. That is brief four's case, made by somebody else's players.

**5. The enemy — nearly empty, and corrected by a picture.** *The synthesis wrote that no game in
the set carries a belief about an enemy that persists and can be wrong. **C12 contradicts it.**
Future War Tactics leaves a red beacon standing where each lost enemy was last seen, and it is
still there on the next turn — a claim about where the enemy is that can be wrong, persisted past
the turn it was made. It is drawn as an abstract spike of light, not as a ghost of the body. One
still cannot say how long it lasts, whether it decays or moves, or whether it clears on a fresh
sighting, and the reviews of the game never mention it, which is why pass one found nothing.* So
the heading is one of ten, not zero, and the one is thin. Invisible, Inc.'s red ghost lasts
the remainder of one turn and carries no belief about where the guard went. Mutant Year Zero has
a directional last-enemy marker that has pointed at corpses and off the map since 2018 and was
never fixed. Phoenix Point draws nothing at all and announces a state change in a popup its own
players describe as impossible to recover once missed — with a mod built solely to draw a
persistent icon instead. **Brief two is not adapting a convention. It is building the thing nine
games did without and one drew as a bare beacon, and the two games that tried a cheaper version
still shipped the two failures above.** Future War Tactics is the precedent for *a mark at a place
that outlives the sighting*. It is not a precedent for a file that decays or for a marker that
says how sure anybody is, and nothing in the set is. One requirement follows directly and is not
negotiable: **persistent, not announced** — which the one game with a persisted marker also obeys.

*A state short of seen* is the one borrowing available and it is a good one: Invisible, Inc.'s
investigating (a yellow `?` triangle, plus a floating `?` at the point being walked to) and
Shadow Tactics' `?` badge are two unrelated lineages reaching the same answer, and both draw it
as a glyph on the body rather than as a position on a scale. Two of ten looks thin until the
denominator is read properly: of the games in the set that have a state between unaware and
engaged, it is two of two. Under entry 058 that is about as strong as evidence for **convention**
gets.

**6. Turn order and time — empty, and emptier than anyone thought.** The brief that ordered this
synthesis said three of the ten have no initiative strip. The true count is **zero of ten**.
XCOM 2, Into the Breach, Mutant Year Zero and Warhounds alternate whole sides; Phoenix Point runs
a faction phase in whatever order the player picks; Invisible, Inc. does the same; Phantom Brigade
resolves both sides at once; Shadow Tactics has no turns; Future War Tactics has a
rounds-remaining dial and nothing else; Tactical Breach Wizards shows the enemies' order only
while the cursor rests on the end-turn button. The strip in `conventions.md` was attributed to
Battle Brothers, which is Tier C and has no file. **So this game's turn structure has exactly one
precedent and it is outside the evidence set.**

What *is* evidenced is the phase banner: XCOM 2's over the whole enemy phase and Into the
Breach's full-width `ENEMY TURN` bar, verified, contradicted by nothing, unknown in the rest.
Entry 065 chose a banner for the pause; the set says the banner is not a fallback for a strip
that cannot be drawn, it is the only thing the genre reliably does here. **Pass two photographed
two more.** Warhounds puts an `ENEMY TURN` box at the top centre for the whole phase (**C4**).
Invisible, Inc. — the closest relative, and the only one of the four that hides its enemies the
way this game does — runs `ENEMY ACTIVITY` across the screen, keeps the phase in a red backdrop
tint after the words go, moves no camera, shows nothing for a guard the player cannot perceive,
and hands back with `AGENT ACTIVITY` (**C7**). That is entry 065's *one indicator per contiguous
stretch*, shipped.

**7. Reactions — split, and the split is between your arc and theirs.** A correction first,
because the skim that briefed this session had it the wrong way round: **two games in the set do
draw a held, not-yet-fired action on the map.** Phoenix Point draws the overwatch arc on the
ground from the soldier's eye position, adjustable with `Ctrl`+scroll before confirming, with its
maximum width set by weapon class — which is `OverwatchArc`'s shape, arrived at independently.
Warhounds draws a firing area in front of the operator and its guides single out fast enter,
adjust and cancel as what makes it usable. XCOM 2 has no cone at all, and the stealth shelf's
traps are invisible until sprung, which is where the *no shipped analogue* reading came from — it
is true of that shelf and false of the set.

**What has no analogue is drawing a *hostile's* held arc, and there is a refusal on the record.**
Asked directly whether a player can tell which move will spring an enemy's overwatch, Mutant Year
Zero's answer was no, and "an indicator for the area the enemies can see would be nice, but is
not implemented." Brief two proposes exactly that indicator and argues it from the stealth shelf
— but what the stealth shelf draws is a *vision* cone, not a reaction arc, so the borrowing is
thinner than it reads. The case still holds and it holds on its own terms: a player who walks
into an arc held by a soldier they could see holding it will say the picture lied. It is a
departure, it is the right one, and it should stop citing a precedent it does not have.

**And nobody in ten games documents what a reaction looks like at the moment it fires.** Every
one of the ten gap lists asks for the same clip and none of them has it. This game's reaction
window is the one place it is unambiguously ahead of the genre, and the genre cannot tell it
anything about the half it has not built. *Pass two filmed one* (**C4**, Warhounds). The camera
does not cut to the shooter. It holds the overhead view with shooter and target both in frame, the
result arrives as floating text at the target, and nothing on the ground marks where the trigger
was. That is one game, and it is the one whose bank is most like ours, so it is worth having. It
is still a long way short of a convention.

**8. Camera and input — split by year, and the split argues the recommendation from both ends.**
Stepped yaw in the four oldest entries (XCOM 2 at 45 degrees, Invisible, Inc. and Phoenix Point at
90, Into the Breach with no camera control found at all); free drag in the newer ones (Warhounds'
full 360 in 2026, Mutant Year Zero, Desperados III, Tactical Breach Wizards). The two complaints
are mirror images: XCOM 2's most-endorsed interface mod adds free rotation, and Tactical Breach
Wizards' players are on the forum asking for `Q`/`E` steps it never shipped. **That is both halves
of this document's existing recommendation evidenced separately** — free yaw on a drag, with the
keyed step kept as a snap — and it is now a finding rather than a compromise.

Right-click is where brief three needs correcting. It is not true that the genre binds right-click
to cancel: Desperados III and Future War Tactics bind it to *move*, and Phoenix Point binds it to
both move and cancel at once. What *is* true, and is the stronger argument, is that **every game
in the set that puts a committing action on right-click produced a documented player complaint
about it** — Phoenix Point's is a mod that disables right-click-to-move so the button can only
cancel, Future War Tactics' is a forum post asking to swap it in a game that cannot rebind
anything. This game has the most committing action there is on that button. *Pass two weakens the
count and not the conclusion:* Invisible, Inc. also moves on right-click — its cursor hint reads
`MOVE: [ RIGHT CLICK ]` (**C3**) — and no complaint about it turned up in its file. So it is two
documented complaints among three games that commit on right-click, not every one. Nothing in the
set fires on right-click, which was the stronger half of the argument and still stands.

**9. Confirmation and refusal — unanimous.** One modal confirmation for a tactical action in ten
games: Mutant Year Zero asks whether to bring a hidden character out of hiding. Phantom Brigade
warns before executing a plan with an idle unit, which is a plan-level check rather than an
action-level one. Everything else commits silently on the click. **Refusal is drawn as a disabled
affordance or as the world saying no** — Invisible, Inc. refuses an under-pierced attack by never
offering the target and greys a taser with no charge rather than hiding it; Shadow Tactics refuses
an over-armoured kill by having the outcome change shape rather than by warning first. This is the
pattern to generalise, and it is the same family as the concealment ring: **a refusal belongs on
the thing being refused.**

**10. What players added — unanimous, and it is how to read the queue.** Every counted community
fix in the set is a legibility fix. XCOM 2's mods are a missing preview, a number instead of a
bar, or one click instead of many; Invisible, Inc.'s UI Tweaks is precision and disambiguation and
says outright it changes no balance; Phoenix Point's three are all *a state the game tracks and
does not show*; Phantom Brigade's community-requested 2.0 fixes were font size and dialogue
duration. Nobody in ten games modded in a new turn order, a new cover system or a new hit-chance
formula. Two of them — Into the Breach's undo sitting close enough to end-turn to mis-click, and
Invisible, Inc.'s action-point figure sitting above the agent rather than at the cursor — are
complaints about **distance**, which is the sharpest available statement of what brief one is for:
a figure belongs where the cursor already is.

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

**The reference set evidences both halves of that separately, which it could not do before.** The
split runs by year rather than by taste: stepped yaw in the four oldest entries — XCOM 2 at 45
degrees, Invisible, Inc. and Phoenix Point at 90, Into the Breach with no camera control found at
all — and free drag in the newer ones, Warhounds' full 360 in 2026, Mutant Year Zero, Desperados
III, Tactical Breach Wizards. And the two complaints are mirror images: XCOM 2's most-endorsed
interface mod exists to add free rotation, while Tactical Breach Wizards' players are on the forum
asking for the `Q`/`E` step their game never shipped, for the reason the older games had one. Both
directions get asked for, so *free drag plus a keyed snap* is the recommendation the set actually
supports rather than a compromise between two camps.

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

**The no-undo rule is the strongest finding the reference set produced, and it comes with its
reason.** All ten games obey one law: *a game lets a player take something back exactly as far as
it told them the truth.* The seven that hide something permit no undo at all and offer a quicksave
or an Ironman toggle instead; the three that hide nothing inside a battle all permit free revision
up to resolution — Into the Breach's unlimited pre-fire move undo plus one turn reset, Tactical
Breach Wizards' unlimited rewind, Phantom Brigade's draggable and deletable orders, which stop
being editable at exactly the moment its five-second certainty window begins. Tactical Breach
Wizards is the case a future session will cite as a counter-example; its rewind is *enabled by*
its lack of fog, not independent of it.

**The other half of that bargain is owed, and it is the reason brief four exists.** A game that
will not give the click back has to give the figures before it. Every game in the set that both
hides something and matters about being seen draws the warning before the commit — Mutant Year
Zero on the destination tile, Invisible, Inc. as shading on every tile, Shadow Tactics on a
held-key cone. The one that draws nothing is XCOM 2, and Gotcha Again, the mod that draws it, has
272,071 subscribers.

**Right-click is not reliably cancel, and the real finding is better than the one this section
claimed.** In XCOM 2 and Jagged Alliance 3 it backs out of a mode or clears a selection, and in
Invisible, Inc. it backs out of a prompt. But Desperados III and Future War Tactics bind it to
*move*, and Phoenix Point binds it to move and cancel at once. What holds across all of them is
this: **every game in the set that puts a committing action on right-click produced a documented
complaint about it.** Phoenix Point's is a mod that disables right-click-to-move so the button can
only cancel; Future War Tactics' is a forum post asking to swap it, in a game that cannot rebind
anything at all. Nothing in the set fires on right-click. This game does. *Corrected by **C3**:
Invisible, Inc. moves on right-click too, and no complaint about it was found, so it is two in
three, not every one. The last two sentences are untouched, and they were the argument.*

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
becomes a targeting mode: an action bar entry and a key, a confirm to commit. This also unblocks
the mouse camera, since a plain right-drag is the gesture the genre uses for orbit or pan and it
is currently spent on the most irreversible action in the game.

**Target cycling is XCOM's, not the genre's, and this section over-claimed it.** `Tab` cycles in
XCOM 2 and in no other game in the set: Phoenix Point offers a list of visible enemies along the
foot of the screen, Phantom Brigade uses `Ctrl`+click, and the remaining seven appear to expect
the player to point at the body. Invisible, Inc. says why in one line — there is no targeting mode
to cycle within, because a shot is one click on one guard exactly as a move is one click on one
tile. So a cycle key is worth building here for the reason this game has and XCOM does not — a
hostile can be a see-through body at a marker, which is harder to point at than a lit silhouette —
and not because a player arrives expecting it. **Departure**, mildly, and cheap either way.

## Turn order and whose go it is

**Standard — and the reference set says there is barely a standard to have.** XCOM 2, Phoenix
Point, Mutant Year Zero, Warhounds and Into the Breach alternate whole sides, so there is no order
to show; a banner says whose go it is and each soldier carries its own points. Battle Brothers and
the older line interleave by initiative, and every interleaving game draws the same thing: a strip
of portraits in order along the top edge, the current actor picked out, and the round boundary
marked. Battle Brothers recalculates initiative every round from fatigue and armour, which is why
its strip needs a slider and why the round mark matters — the order you are reading is only good
until the round ends.

**But zero of the ten reference games draw a per-unit initiative strip**, and that is a correction
to this section rather than a detail. Five alternate sides, two run a faction phase in whatever
order the player picks, one resolves both sides simultaneously, one has no turns at all, and
Tactical Breach Wizards shows the enemies' order only while the cursor rests on the end-turn
button. Battle Brothers is Tier C and has no file. **So the strip this game already draws has
exactly one precedent and it is outside the evidence set**, and the burden entry 058 puts on a
departure cannot be discharged here by pointing at the genre in either direction.

What *is* evidenced is the banner. XCOM 2 says *enemy turn* over the whole phase; Into the Breach
draws a full-width `ENEMY TURN` bar across the middle of the screen with the mech roster still
visible beside it. Verified in two, contradicted by none, unknown in the rest. That makes entry
065's choice better supported than it looked when it was made: the banner is not a consolation for
a strip that cannot be drawn, it is the one turn-order element the genre reliably has. *Pass two
added two observed:* Warhounds' `ENEMY TURN` (**C4**) and Invisible, Inc.'s `ENEMY ACTIVITY` /
`AGENT ACTIVITY` pair (**C7**). The second has the details this section asks for. It hides the
player's HUD for the whole phase, keeps the phase in an ambient red tint once the banner is gone,
moves no camera, and draws nothing for a guard the player cannot perceive.

**And there is a third answer worth naming even though this game cannot take it.** Tactical Breach
Wizards' order preview on the end-turn hover withholds nothing and shouts nothing — a cheaper way
to be honest than a permanent strip, and a good fit for a game where the player replans constantly.
It is unavailable here for the reason entry 064 gives: a preview of the full order would hand back
the count of hostiles nobody has found. Worth recording so a future session does not rediscover it
and assume it was missed.

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
  the same settle-before-shot rule every other animation here obeys. **Now one measurement
  (C7):** Invisible, Inc.'s `ENEMY ACTIVITY` banner is up for at least 1.43 s. It was already
  showing on the clip's first frame, so that is a floor. The `AGENT ACTIVITY` banner handing back
  is up for about 1.4 s. The argued range sits below the one shipped figure, so its top end is the
  safer half.
- **What fills the stretch between banner in and banner out.** Invisible, Inc. keeps a tint on the
  world's backdrop for the phase once the words have gone, about two seconds in the clip. That is
  a second, quieter indicator, and it says *still their go* without a word. It is one game's
  answer, recorded rather than recommended.

Mark the round boundary, which is a plain **convention** borrowed from Battle Brothers and is
missing.

## What the squad can see

*Added for `../decisions.md` entry 094, item 15, from the second play-through: "It's not obvious
what I'm seeing versus what is in the fog of war." View's ground-and-camera brief waits on it.
Entry 095 has the reasoning in short and the one question it leaves for Core.*

**Standard — split two and two, and split by year, the way the camera is.** Take only the games
in the set that hide an enemy on the map, because the others have nothing for a fog to say. Two of
them darken the ground outside the squad's sight. Two draw no fog at all.

- **XCOM 2 greys out what the squad cannot see**, squad-wide. *Verified*: its players describe
  soldiers standing in "a completely blacked out area" until the squad's sight updates
  ([Steam discussion](https://steamcommunity.com/app/268500/discussions/0/412446890546610495/)).
- **Invisible, Inc. dims and desaturates every room no agent can see now**, and keeps what was
  seen before dim rather than black. *Observed* at whole-level zoom in the C3 frame, where the
  agent's room is lit and the rest are not
  ([`shot-c3-move-range-outline-path-and-cursor-hint.jpg`](reference/shots/invisible-inc/shot-c3-move-range-outline-path-and-cursor-hint.jpg)).
- **Future War Tactics hides its enemies and draws no fog.** *Observed* in the one frame where a
  fog would have to show. C12 is the turn after contact was lost, and the two last-seen beacons
  stand on ground lit exactly like the squad's own
  ([`shot-c12-turn-after-contact-lost-full-frame.jpg`](reference/shots/future-war-tactics/shot-c12-turn-after-contact-lost-full-frame.jpg)).
- **Warhounds hides its squads until first contact and draws no fog** in any of its photographed
  frames (C4, C6).

Phoenix Point hides its enemies too, and its file says nothing about its ground either way.
Into the Breach, Tactical Breach Wizards and Phantom Brigade hide nothing inside a battle, and
Shadow Tactics draws every guard. So *a darkened ground outside squad sight*, as entry 094 put
it, is the older half's convention and not the genre's.

**Two things decide it here, and one of them is the complaint.** A convention is worth following
because the player arrives expecting it (entry 058). The user arrived looking for a fog and said
so, which is the evidence that clause asks for, as direct as it gets. The other is that the newer
two can do without a fog because they draw almost nothing of an unseen enemy: one bare beacon in
Future War Tactics, nothing in Warhounds. Their ground has nothing on it that needs telling apart.
This game's ground carries told ghosts, markers and an attention field, and not one of them can be
read without knowing whether the ground under it is ground anybody of ours can see.

**And the game that draws fog best still never answers the question a move asks.** A 2017
critique of XCOM 2 says its interface "does nothing to show you what tiles you will be able to
see", whether at the end of a move or during it
([Gile, Game Developer](https://www.gamedeveloper.com/design/xcom-2-and-vision-the-cost-of-an-illusion)).
A fog shows what the squad sees now. What it would see from somewhere else is a separate
question, and the genre has left it open.

**Here.** `BattleView.BuildUnseen` darkens, in `SandboxPalette.Unseen`, every tile on the storey
being looked at where the **active soldier**, in their current stance, has no line to a standing
body. That is `Battle.Sight.Trace(active.Vantage, new Vantage(node))`, and `Vantage` stands the
target up by default. It draws only when zoomed in past `SandboxCamera.LegibleAt`. Nothing draws
the squad's sight. Over the ground, every drawn soldier's attention field is tinted in its side's
colour: `AttentionOn` times the range falloff, **through walls**. `AttentionOn`'s own remark says
why: *line of sight stays pure geometry in the sight solver; who is paying attention is a question
about people.* The cover outlines sit on the active soldier's seen tiles, and the ghosts stand at
their markers.

**It already contradicts itself once.** A hostile that a teammate has eyes on, standing where the
active soldier cannot see, is drawn as a body on dark ground.

**What *seen* means in the rules — and it is not what the genre's fog promises.** Three facts,
read from the source:

1. **Seeing is geometry; noticing is a rate.** `SightResult.CanSee` is true if any sliver of the
   silhouette is in view. A hostile is drawn as a body only when some soldier of ours has eyes on
   it **and** a contact at `Searching` or above (`UtilityModel.ActsOn`, through `Tactician.Known`),
   and each look adds `LookGain` toward that. So at list figures:
   - a man standing in the open, dead ahead at 10 m, is registered in one look (about 52 against
     `Searching`'s 50);
   - the same man at 30 m takes two looks, and four if he is in the corner of the eye;
   - lie him flat at 30 m in the corner of the eye with a wall hiding 40% of him, and one look adds
     about 3, so seventeen turns of looking.
2. **A look happens at a moment.** Ending a turn is *the only moment a unit looks around*
   (`../subprojects/core.md`, *How a turn runs*). The one other look is the one a stationary
   soldier gets at a mover crossing ground that is not behind it (`ReactionWindow.OfferFor`). **A
   soldier who is walking takes no look.** Ground that a soldier has just walked into view of has
   not been looked across yet.
3. **Whether a place can be seen depends on the height of what stands there.** A place can be in a
   line to a standing man and not to a crouched one behind a 1.0 m wall, and the body of a man on a
   roof can show while the roof under him does not.

So **lit ground in XCOM means everything on it is drawn, and lit ground here can hold a man in
plain view whom nobody has registered.** The fog cannot promise an empty tile, and it must not be
drawn in a way that looks like that promise.

**The asymmetry.** It permits exactness and forbids one shortcut. The ground is our side's own
sight, so contract 3 lets it be drawn exactly. The shortcut is to test each tile against whoever
is actually standing on it, at their stance. Then one dark hex among lit ones would tell the player
that a man is lying flat there. **The fill must be a question about the place, never about its
occupant**, and that is the second reason for the standing test below.

**Recommendation** — **convention** in the fill, **departure** in what the fill is allowed to
claim.

- **Darken the ground that no soldier of ours has a line to. The squad's sight, not the
  soldier's.** Take the union over our soldiers in play, each at their current vantage, of
  `CanSee` to a standing body at the node. This is the convention, taken from the half of the genre
  the player came from. It is squad-wide because everything drawn on the ground is squad
  knowledge: `HexSandbox.GatherKnowledge` merges every soldier's `Known`. One soldier's fill under
  the squad's bodies is today's contradiction.
- **Test at standing height, never at the height of whoever is there.** There is no genre
  precedent to depart from, since the genre's sight has no height. Three reasons:
  - **It is the rules' own test for having looked at a place.** `Tactician.Known` stands a marker
    upright *because the question a marker answers is can I see the place*, and
    `AwarenessTracker.Checked` tests a briefing against a standing body. So the edge of the fog is
    exactly where a told ghost gets tested, which is contract 2 drawn on the ground.
  - **It keeps a promise a capture can check: a drawn body never stands on dark ground.** The
    trace hides a silhouette from the waterline up, and the hidden share only grows as the body
    gets shorter. So a man who can be seen crouched or prone can also be seen standing, and a
    lower test would put bodies on the dark behind every low wall and on every roof.
  - **It closes the leak named under the asymmetry.**

  What it costs is fact 1 again: lit ground behind a low wall may still hide a crouched man. The
  ground says *a man standing here would be in view* and never *nobody is here*.
- **Do not cut the fill at a range. Range belongs to the tint.** A line has no range limit, while
  `LookGain` is zero past `SightRangeMetres`, 45 m. A body already registered that walks out past
  45 m keeps its eyes-on and stays drawn, so a fill cut at range would put it on the dark. Keep the
  fill pure geometry and let the attention field, which fades to nothing at 45 m, carry range.
  **Lit with no tint** then reads correctly: in a line, with nobody watching that far, so nothing
  new will be registered there.
- **Draw our side's attention field only where that soldier has a line to a standing body.** The
  fill is the sight half and the tint the awareness half of the one product `LookGain` multiplies.
  Core keeps them in two homes, and the drawing stacks them as two layers in that order. **The
  convention is that a cone knows what blocks it.** Invisible, Inc.'s stripes run up the face of a
  glass wall and change to a separate band in the lee of a sofa or a desk (**C2**, observed). Today's tint runs through
  walls, onto ground where no look can land. For our own soldiers the clip costs nothing, because
  it reuses the traces the fill already takes.

  **A drawn hostile's field takes the same clip**, from his line to a standing man of ours. That
  is still our knowledge: we see him, so his lines are geometry anybody could work out. The price
  is a sweep of traces per drawn hostile, which is View's to measure. If it is too dear, clip ours
  first and leave theirs unclipped, and say so. Testing at standing errs toward danger for a
  crouched soldier of ours behind a low wall, which is the safe way to be wrong; the exact figure
  for a stance is the destination readout's job, not the ground's.

  The result is one reading, not two overlays. **Dark** means no look of ours can land here.
  **Tinted** says how hard we are looking. **Lit and bare** means in a line but watched by nobody.
  The edge is binary and the grade sits inside it, which is the fix a published critique of
  Invisible, Inc.'s partial shading asked for: shade seen fully and unseen not at all, and carry
  the grade in a tint that was already there, not in a third band.
- **The look still to come belongs to the active soldier, and it is told on the soldier, not on
  the ground.** Fact 2 means a soldier who has just walked into view lights up ground that nobody
  has looked across yet. **A third ground state was considered and rejected**: *will be looked
  across when you stop*.
  - The rules keep no set of looked-at places. Looks are taken per subject, at a turn's end and at
    a crossing, so a view that kept one would be modelling something the AI never reads, against
    contract 2.
  - A reaction can change a watchman's stance after it has looked, and a record kept by the view
    would silently get that wrong.
  - It is also the three-band problem again.

  **What is left is a known cost, recorded here so it is not discovered.** A player can see a lit,
  empty courtyard and walk into a man they would have registered by stopping. Two things carry
  the lesson instead. That a soldier looks when they stop is a teaching question, and it is the
  first thing *Teaching it* has to settle. And the End turn control on the action bar is the look,
  so it is worth a word saying so. Whether a mover should take a look at all is Core's question,
  filed in entry 095, and nothing in this section depends on the answer.
- **The told ghosts stand on the fill, and the fill never clears one.** A ghost on dark ground is
  a belief about a place nobody can look at, and it reads correctly with no help. A ghost on lit
  ground stands on a place about to be tested: the next look from the soldier whose line lights it
  either confirms it as a body or starts it decaying (`AwarenessTracker.Observe`). **What the fog
  cannot do is item 5's job.** On turn one a told marker is exactly where its hostile stands, and
  on lit ground the only difference between *told* and *seen* is a see-through body against a
  solid one. That difference belongs to the ghost's own drawing, which is brief two, and not to
  the ground. The fill's part is never to lie about which kind of ground a ghost is on.
- **Draw it at every zoom.** Convention: Invisible, Inc.'s dim rooms are photographed at
  whole-level zoom. `BuildUnseen`'s reason for dropping it was one soldier's sight covering one tile
  in ten, and the squad's sight is wider. The deeper reason is the sandbox's own rule that *the
  camera changes what is drawn and never what is true*. Labels leaving at a distance is a choice
  about legibility. A fog that leaves at a distance says the squad sees everything from far away.
  The fill tints tile tops and not walls, so the shape of the place should survive. If a capture
  shows it does not, lighten the fill with distance and never remove it.

**Considered and rejected: drawing the fog as fog.** A haze or drifting cloud over unseen ground
was put forward by the user and argued against, and the user agreed.

- **Smoke is already a rule, and it would look the same.** `WallProfile` carries a sight-blocker you
  can walk through — smoke, a hedge, a curtain of hanging plastic — which hides everybody from
  everybody. Fog of war hides nothing from the enemy; it is our side's ignorance. Draw both as
  haze and a player seeing fog near a hostile will conclude the hostile cannot see through it
  either. That is contract 3's *whose knowledge it is*, broken by a picture.
- **The edge has to be crisp** enough to say which hex a ghost stands on, and a haze softens exactly
  that.
- **A volume has height, and the ghosts stand inside it.** Kept below prone body height so as not
  to bury them, it is a tint with a texture.
- **It moves**, and a capture needs a still frame.

Neither game in the set that draws a fog draws haze: XCOM 2's is blacked out and Invisible, Inc.'s
is dimmed and desaturated. **So the art pass renders this fill as unlit — dimmed and desaturated,
Invisible, Inc.'s treatment — and never as obscured.** Desaturation reads as *not seen*, survives
zooming out, keeps ghosts and tints legible on top, and cannot be mistaken for smoke. The
greybox's dark tint stands until then.

**Where the stance grade goes, if it is drawn anywhere.** Two games in the set draw a band for
*seen standing, not crouched*: Shadow Tactics' striped segment of a cone, which a crouching
character can cross unseen (verified), and Invisible, Inc.'s yellow hidden band. Both put it on
**the enemy's** cone, because *where can I get past them low* is the question a stealth player
actually asks. That makes it a later refinement of a drawn hostile's clipped field, at the price of
a second trace per tile, and not a feature of our fog. Item 15 does not need it. The C2 crop also
says what it would cost: in a full frame, Invisible, Inc.'s yellow read as the shadow of the
furniture that cast it.

**The cover outlines and the shield — items 7 and 13 of entry 094.** They answer opposite questions:

- **The outlines** say where a target would be safe from the soldier who is up — `SightResult.Cover`,
  seen from the active soldier.
- **The genre's shield** says what cover *you* would have on a tile.

The genre answers the shield's question at the tile under the cursor, and the outlines' question
only while aiming, as a term of the shot: XCOM 2's `LOW COVER −20%` (*Readouts*). No game in the
set paints enemy's-eye cover on every tile at rest. **Convention, both ways:**

- **The shield** goes under the cursor, as a glyph standing at the edge of the tile toward whatever
  gives the cover, in the grade colours, against the threats our side holds. `Sight.Trace` from each
  of `Known`'s poses already answers it.
- **The outlines** move into the firing mode, where the shooter's question is asked, and leave the
  ground at rest.

Then the two are never on the ground at the same time, which is the cheapest way to make sure
they never look alike. It also puts the one per-soldier view a player needs, the shooter's, in the
one mode that needs it. The ground at rest shows the squad's sight, and the firing mode shows the
shooter's.

**What a capture should show before this is called built.** Four checks, each one a picture:

- No body stands on dark ground, at any zoom, in any pinned capture that is not omniscient.
- None of our soldiers' tint lies on dark ground.
- On the waystation's turn one, which of the four told ghosts stand on the dark. If any stands on
  lit ground, item 5 is brief two's to finish and not this section's.
- A zoomed-out capture in which the buildings still read as buildings.

**Nothing here needs a query Core does not have.** `Sight.Trace`, `Tactician.Known` and
`AttentionOn` answer all of it.

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
Shadow Tactics, Desperados III — draws a cone per guard, and **the detection fill is on the cone
itself**: it starts at the guard's eyes and spreads toward the intruder, and detection completes
when it arrives.

*Corrected by the synthesis. An earlier draft said the fill was a meter over the guard's head.
The reference file found no separate gauge in either game and no source describing one — the fill
is the cone's own colour, and the nearest head-mounted thing in that line is the `?`/`!` badge
pair, which is a state glyph and not a meter. That pair is a real borrowing and the enemy section
below takes it separately. **Provisional**, on a `verified` claim rather than an `observed` one;
**C13** would settle it outright by framing one guard's head and cone in the same shot.*

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
  a convention that already exists for exactly this state. It is two of ten across the set and two
  of *two* among games that have such a state, reached independently by Invisible, Inc.'s yellow
  `?` triangle and Shadow Tactics' `?` badge, and drawn in both as a glyph on the body rather than
  as a position on a scale. *Observed for Invisible, Inc. (**C3**):* a yellow downward triangle
  with a `?` over the head, and at the place being walked to a matching yellow shield-shaped `?` on
  a tile marked with corner brackets. The glyph on the body and the glyph at the place are one
  colour and one symbol, and that pairing is the detail worth copying for a marker.

**Three things the reference set added to this section, all of them requirements rather than
suggestions.**

- **Persistent, not announced.** Phoenix Point tracks alert state and surfaces it as a brief
  orange popup that its own players describe as impossible to recover once missed; a mod exists
  solely to draw a persistent icon instead. That is the failure mode nearest this game's, proven
  by somebody else's players, and it rules out any design where a rung change is a transient
  message.
- **The name of the ladder sets how precisely it is read.** Klei renamed Invisible, Inc.'s alarm
  to `SECURITY LEVEL` because playtesters read the original naming and numbering as more
  informative than it was meant to be. This game's rungs are `Unaware`, `Suspicious`, `Searching`,
  `Alerted`, `Engaged` in the rules, and `Searching` and `Alerted` are exactly the pair a player
  will read as a measured scale rather than as two words. What the rungs are *called on screen* is
  therefore an interface decision with a shipped precedent behind it, not a passthrough of the
  enum.
- **A rung that goes back down has no analogue anywhere.** Invisible, Inc.'s escalation is one-way
  at the top: investigating resolves either way, alerted never resolves for the rest of the
  mission. This game's contact file decays, so a rung can fall. A player borrowing the genre's
  only ladder will assume it cannot, and the drawing has to make the fall as visible as the rise
  or the rules will be read wrong in the one direction that costs a player a soldier.

**And it answers a View open question, with a correction to how it is argued.** Draw a hostile's
held arc whenever the hostile itself is drawn. A player who walks into an arc held by a soldier
they could see holding it will say the picture lied, and they will be right. **But it is a
departure from nothing and should stop citing the stealth shelf as though it were a precedent** —
what that shelf draws is a *vision* cone, not a held reaction arc, and no game in the set draws a
hostile's reaction zone at all. Mutant Year Zero's players asked for exactly this indicator and
were told it is not implemented. The recommendation stands on its own reasoning, which is enough;
it does not need a borrowing it does not have.

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

**Two things the reference set changed here.** First, **drawing your own held arc on the ground is
a convention after all**, which an earlier reading of the set denied. Phoenix Point draws the
overwatch arc from the soldier's eye position, adjustable with `Ctrl`+scroll before confirming,
with its maximum width set by weapon class — `OverwatchArc`'s own shape, reached independently.
Warhounds draws a firing area in front of the operator and its guides single out fast enter,
adjust and cancel as what makes overwatch usable mid-fight. Here `V` and `HoldArc` take an arc in
one press with no adjust step, which is faster than both and gives up the thing both shipped
games thought worth building. An adjust step is **convention**, and it is cheap. *What Warhounds'
area looks like, observed (**C4**):* not a wedge but the grid's own tiles tinted yellow, drawn
while it waits. While it is being placed, a `Brings out of cover` warning sits at the cursor, a
refusal-family mark drawn on the thing. Once declared, an `OVERWATCH` label sits on the soldier's
name plate.

Second, **nobody in ten games documents what a reaction looks like at the moment it fires.** All
ten gap lists ask for the same clip and none of them has it. *Pass two filmed one (**C4**):
Warhounds does not cut to the shooter, draws nothing at the trigger point, and reports the result
as floating text at the target.* One game, so the rest of this paragraph stands. The window this game already has —
the reactors named, the options scored, a tick clock, the route drawn with the tick each step
lands on — is the one place in this interface that is unambiguously ahead of the genre, and the
genre has nothing to tell it about the resolution half. That is a reason to build the resolution
carefully rather than by analogy, and it is why **C7** and **C16** are on the capture list at all.

## Movement and shooting animation

**Standard.** The soldier walks the path, the camera follows only if the mover would otherwise
leave the screen, and every game in the list ships a speed setting — XCOM 2's is Zip Mode, which
exists because the animation is the part of a long campaign a returning player wants shortened.
The camera cut to a reaction shooter is the single most complained-about behaviour in the genre,
and the lesson from the complaint is narrow: cut to the thing that surprised you, and cut back.
Warhounds, the newest game in the set, does not cut at all: its reaction shot plays out in the
overhead view it was already in (**C4**).

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

**Standard: one number, at the thing — and the *expandable* half did not survive the evidence.**
XCOM 2 puts a single hit chance over the target's head; cover is a shield icon on the tile; points
are pips on the soldier. Battle Brothers is the exception that proves it — it shows every modifier
in a long tooltip, and it is also the game in the list with a reputation for opacity.

**Two corrections from the reference set, and the first one matters because brief one was built on
it.** The arithmetic behind XCOM 2's number is **not** a hover card on the target. A guide
screenshot opened at full resolution shows a stacked list docked at the bottom left of the screen,
beside the ability name, under a bold `HIT 64%` headline: `AIM +92%`, `HEIGHT ADVANT +20%`,
`DEFENSE −40%`, `SQUADSIGHT −8%`, `LOW COVER −20%`, with a mirrored damage column to its right.
The target itself carries only the floating `64%` and a health bar. **So *XCOM's hover* names a
gesture that does not exist**, and whether that docked list is shown by default or sits behind a
collapsed headline could not be settled from a still — small chevron glyphs suggest it is
collapsible. That question is **C1**, the highest-ranked entry in the capture list, precisely
because brief one has to choose a gesture and this is the game it was told to copy.

**C1 settled it, and C5 said the same thing from the game this section called the counter-case.**
In XCOM 2, choosing Fire Weapon on a target opens the breakdown at once, with no further click:
`HIT 68%`, `AIM +65%`, `WEAPON RANGE +3%` in one column and `DAMAGE 3-5`, `CRIT 40%`, `FLANKING
TARGET +40%` in the other, docked at the bottom centre either side of the ability panel. Each
column has a chevron that folds it, and the fold is **sticky** — a new target stays folded. The
target carries a reticle, the red `68%` and a health bar. In Warhounds the attack mode opens a
panel at the right edge reading `PRECISION 17%` over `Precision +85`, `Range -18`, `Cover -50` and
`DAMAGE 4-8`, again with no further input, while `17%` sits beside the reticle, over the health bar
and on a `[TAB]` target card. **Neither game puts the terms behind a gesture. Both put one figure
at the target and the terms in the HUD, open for as long as the player is aiming.** The shots are
in `reference/shots/xcom2/` and `reference/shots/warhounds/`.

**The second correction is that a hit chance is not the genre's answer at all.** Three of ten show
one as a percentage; five show none; two show a number that is not one. This game keeps its
percentage and should — `GunneryModel` computes a real probability, and contract 3 makes a figure
about your own shot exact by right. But *one number, breakdown on demand* is one game's habit, not
a convention, and it has a **documented failure mode recorded twice in the set**. Phantom Brigade
folds accuracy and damage into a single percentage that its own players argue about in public as
though it were a hit chance, which it is not. XCOM 2's single number silently omits a flat 20%
graze band that applies to almost every shot it draws. In both cases the failure is the same: **a
folded number invites a wrong model of what it means, and the breakdown behind it does not undo
the first impression.** ~~Warhounds is the counter-case and it is worth weighing — it shows a
percentage per bullet in a burst, several numbers at once by design, on a deliberate transparency
pitch.~~ *Corrected by **C5**: Warhounds is not a counter-case. Its shipped preview for a burst is
one figure with its terms beneath it, and no per-bullet percentage is on screen. The per-bullet
figures came from guides describing the mechanic, not the readout. It is a second instance of
XCOM's shape, and it adds a naming warning of its own: its headline `PRECISION` shares its name with
one of the terms under it.*

**What the set says a figure's *place* is worth, which is the rule brief one actually needs.**
Invisible, Inc.'s own designers put its abilities on context buttons that appear on the world
object, and the interface critique that praises it gives the reason in one line: your mouse never
leaves the area you are focusing on. The same critique's complaint about the same game is that its
action-point figure sits above the agent rather than at the cursor, so a player planning a long
path has to look away from where they are pointing. Into the Breach's players have twice asked for
its undo button to be moved further from end-turn. Three independent complaints, three games, one
rule: **a figure belongs where the cursor already is.** That is a sharper test than *on the thing
it describes*, and it decides several of brief one's placements on its own.

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
- ~~Headline at the thing, breakdown on demand — but **pick the gesture on this game's own terms,
  because the set does not supply one.** A hover's contents are verified in exactly one of the ten
  games. XCOM 2 docks a list; Into the Breach uses two held keys, `Ctrl` for a unit's detail and
  `Alt` for the turn's resolution order; Phantom Brigade splits its folded number on a held
  `Ctrl`; Shadow Tactics and Desperados III hold `Alt` to show every cone at once. **Held-key
  disclosure is the pattern with the most support in the set** — four games, three of them for
  exactly the *show me everything for a moment* job — and it has the property a hover card lacks:
  it is one gesture for every figure at once rather than one card per figure, which is how this
  ends up worse than the panel. Take that, one key, everywhere. **Provisional until C1.**~~
- **Headline at the thing; the shot's terms open while aiming, with a fold the player can close
  and the game remembers.** **Convention**, and no longer provisional: settled by **C1** and
  **C5**. *This replaces the held-key recommendation above, which the pictures contradicted.* The
  two games photographed aiming both open the terms the moment the aim starts, dock them in the
  HUD rather than on the target, and keep one figure at the target. XCOM 2 lets the player fold
  them, per column, and remembers the fold. Firing here is already a mode (entry 084), so the
  convention has the thing it hangs on. **What the held key keeps** is the job the set actually
  uses it for, *everything at once for a moment*: Shadow Tactics' and Desperados III's `Alt` for
  every cone, Into the Breach's `Ctrl` and `Alt`, and Phantom Brigade's `Left Ctrl`, labelled
  `Show details`, which on film reveals every unit's badge on the map together (**C9**). Pass two
  did not catch Phantom Brigade's split of its folded number, so that claim stays verified and
  unobserved. The pictures take the held key away from the shot's terms. They say nothing about
  whether this game wants one for anything else.
- **Name the headline so it cannot be read as something else.** Phantom Brigade's number is the
  set's warning and it cost its players years of public argument. Whatever a single figure folds
  together, the label says which quantity it is, and a term that is the whole reason the number
  has the shape it does is not one of the things folded away.

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

**The reference set moved this recommendation, and it is the largest single change the synthesis
made.** The genre already draws this cliff — **on the ground, not on the soldier.** Four of the
six grid games in the set band the reachable area by which point pays for it, and in three of the
four the band falls exactly at *can I still act when I arrive*: XCOM 2's blue is a move you can
still fire after and its yellow is a dash that leaves nothing, Phoenix Point's blue keeps an
action in reserve and its yellow spends everything, Warhounds' blue is the first action and its
yellow the second. That is not a different mechanic from the reserve. It is the same question —
*what will I still be holding when I get there* — asked at the place where the player is actually
asking it, which is the tile under the cursor.

**So the cliffs belong on the move range as well as on the pips, and the ground is the stronger
of the two.** The pip row says what a soldier holds now; the banded range says what they will hold
*there*, which is the decision being taken. This game's move overlay is a graded tint where the
genre's is a small number of bands, and a graded field cannot show a cliff — it is the smoothing
problem again, in the one place it costs most. Recommendation: **convention**, adopted as the
genre has it, with the bands cut at the reserve's own thresholds rather than at whole action
points. A player hovering a tile should be able to see, without reading a figure, whether arriving
there still leaves an aimed shot in hand. ~~**Provisional on C10** as to whether any shipped game
bands a graded field rather than a discrete one, which is the one thing Future War Tactics is in
the set for and the one thing no screenshot of it caught.~~ **Settled by C10, and the mark is
gone.** Future War Tactics, the set's only candidate for a graded field, is not one. Its movement
zone is **two nested outlines, amber inside green, stepped along the tile edges, with no tint on
the ground at all**
([`shot-c10-move-range-two-nested-outlines.jpg`](reference/shots/future-war-tactics/shot-c10-move-range-two-nested-outlines.jpg)).
No shipped game in the set draws reach as a graded field, so banding it is the convention without
an exception. Invisible, Inc. draws its reachable area the same way, as a cyan outline with no fill
(**C3**). That answers this section's worry about a second overlay competing with the attention
tint: **both games that were photographed draw the band as an edge, not a fill, and an edge lies
over a tint without fighting it.**

**One thing this does not license.** The bands stay a property of the tile under consideration.
Nothing here argues for painting the whole map in more colour; the set's own lesson from Invisible,
Inc.'s striped vision shading is that a second overlay competing with an existing one is where
legibility goes, and this game already paints attention per tile.

**Two things Warhounds does with the arc rather than the points**, both **convention** and both
cheap: overwatch enters cone placement directly rather than through a nested menu, and its guides
single out fast enter, adjust and cancel as what makes it usable mid-fight. Here `V` and
`HoldArc` take an arc in one press with no adjust step.

**Read, not played — and then played, in part.** Everything about Warhounds above comes from its store page, wiki and
community guides rather than from the controller, and it should be checked before anything is
built on the detail. *Pass two checked three things (C4, C5, C6).* Overwatch is entered from the
action bar, and its area is drawn as tinted grid tiles. The attack preview is one figure with its
terms, not per-bullet figures. First contact is a banner. The all-or-nothing bank was not
exercised on film and stays as its store page states it. What it is used for here is narrow and safe: that a shipped game with a
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
| **Shadow Tactics / Desperados III / Commandos** | Real-time, so the input conventions do not transfer, but the drawing does: a cone per guard, with the detection fill on the cone itself rather than on a gauge, and a `?`/`!` badge pair over the head carrying the coarse state. |

**A third shelf, and the first draft did not know it existed: what shipped while this was being
built.** The canon list stops at games old enough to have a settled reputation, which is exactly
what makes it a canon and exactly what makes it blind to the two games in the genre closest in
time. Both were added on the user's prompt.

| | |
|---|---|
| **Warhounds** (2026) | XCOM- and Jagged Alliance-inspired, and the only shipped game found with a reserve like ours: declaring overwatch commits the operator's remaining action points. It is all or nothing where ours is graded, which is the whole of the *Points, and the reserve* section above. Also: cone placement entered directly rather than through a nested menu, with fast adjust and cancel. |
| **Future War Tactics** (2025) | Colour-coded zones for movement and attack radius — *not* graded tints as this row once said, but two nested outlines on the tile edges (C10). And, found only by a picture, a red beacon left where a lost enemy was last seen (C12), the one persisted enemy marker in the set. |

**A fourth lineage, found by the reference set rather than reasoned to: breach and clear.** XCOM:
Chimera Squad and, after it, Tactical Breach Wizards answer the enemy question a third way that is
neither the canon's nor the stealth shelf's — a room's occupants are established the moment the
door goes in, so nobody is hidden and nothing is remembered. It matters here because Tactical
Breach Wizards is the newest game in the whole set, released 2024, and it still has no contact
file. **The two shelves have not converged**, and the thing this game is about has no ancestor on
any of the three as of the last game anyone has shipped.

**The lesson about the list itself is worth more than either row.** The reserve section exists
because somebody asked whether a game outside the list had solved a problem we had, and one had —
by removing it. A canon is a list of games whose conventions are *settled*, which is what makes it
the right starting point and also guarantees it is silent on any mechanic newer than the canon.
The next question of this shape should be asked the same way: which shipped game has this
mechanic, rather than which famous game has something like it.

**Nothing here needs a query Core does not have**, and that has survived the reference set: the
synthesis filed three findings for Core in `../decisions.md` and not one of them asks for a new
surface. Every recommendation above is answerable from a query that exists — `ReadoutFor` for the rung, `Contact.LastKnownPosition` for the marker, `Reachable`
and `CostTo` for the tile, `Appraise` for the window's default. The one thing the interface
cannot show is already an open entry rather than a new one: entry 012's second item, who a shot
would wake.

**Where this came from.** The ten reference files under [reference/](reference/) carry the
evidence and its sources file by file, and every count in *What ten games said* is drawn from
them. The first draft of this document predates them and came from play plus the interface
documentation and community threads for
[XCOM 2's Free Camera Rotation mod](https://www.nexusmods.com/xcom2/mods/1),
[Jagged Alliance 3's camera controls](https://steamcommunity.com/app/1084160/discussions/0/3807280781155752599/),
[Klei's design deep dive on the alarm system in Invisible, Inc.](https://www.gamedeveloper.com/design/game-design-deep-dive-alarm-systems-in-klei-s-i-invisible-inc-i-),
[Battle Brothers on initiative and turn order](https://battlebrothersgame.com/tactical-combat-mechanics/),
and [Mutant Year Zero on stealth and detection](https://www.mutantyearzero.com/news/master-the-stealthy-approach/).
