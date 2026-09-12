# Shadow Tactics: Blades of the Shogun / Desperados III — reference

**What this game is the authority on, and what it is only an instance of.** Both are Mimimi
(Shadow Tactics: Blades of the Shogun, 2016, as Mimimi Productions; Desperados III, 2020, as
Mimimi Games), and `subprojects/interface.md` names exactly why they are in this set: the best
cone-drawing shipped anywhere in the reference list, and a planning mode — Shadow Mode in the
first game, Showdown Mode in the second — that is a UI answer to the problem of coordinating
several actors against one moment, which is this game's problem too. They are the authority on
both. They are only an **instance** of real-time input: movement, targeting and the camera all
run on one unbroken clock that the player can slow (automatically, on detection) or pause (by
choice, to plan), but never turns. Nothing about their key bindings, their absence of an action-
point economy, or their lack of a turn order transfers as a convention — those questions do not
apply to a game with no discrete turns. What transfers is *how a state, a plan, and a cone get
drawn*, independent of when control passes between two clocks.

**One file for the line, not two.** Desperados III is Shadow Tactics's own sequel and refines
almost everything below rather than replacing it: Shadow Mode became the paused, multi-step
Showdown Mode; the same cone, the same two badge icons, the same crouch-to-hide-in-bushes rule
carry over unchanged. Every heading says where the two agree and names the one where they differ.

## Tag key

| | |
|---|---|
| **observed** | read off a named shot in `shots/`. Pass two only — none in this file. |
| **verified** | a published source, with the link. |
| **remembered** | model knowledge, unchecked. Never load-bearing alone. |
| **inferred** | from something else in this file, which it names. |

## Sources

- [Game Design Deep Dive: Dynamic detection in Shadow Tactics](https://www.gamedeveloper.com/design/game-design-deep-dive-dynamic-detection-in-i-shadow-tactics-i-) — Game Developer
- [Interface and key shortcuts](https://www.gamepressure.com/shadowtactics/interface-and-key-shortcuts/z1941c) — gamepressure.com, Shadow Tactics
- [Controls](https://www.gamepressure.com/desperados-iii/controls/zad05a) — gamepressure.com, Desperados III
- [Exploration and sneaking](https://guides.gamepressure.com/desperados-iii/guide.asp?ID=53317) — gamepressure.com, Desperados III
- [Showdown Mode](https://www.gamepressure.com/desperados-iii/showdown-mode/zfe2ec) — gamepressure.com, Desperados III
- [Long Coat — how to eliminate?](https://www.gamepressure.com/desperados-iii/long-coat-how-to-eliminate/z9d050) — gamepressure.com
- [How to Kill Long Coats](https://culturedvultures.com/desperados-3-how-to-kill-long-coats/) — Cultured Vultures
- [Shadow Tactics: Blades of the Shogun Enemy Analysis](http://www.vigaroe.com/2024/11/shadow-tactics-blades-of-shogun-enemy.html) — vigaroe.com, on samurai
- [Shadow Tactics – Rendering Breakdown](https://kosmonautblog.wordpress.com/2017/01/09/shadow-tactics-rendering-breakdown/) — kosmonaut's blog
- [Desperados 3 Review — Revolvers And Redos](https://www.gamespot.com/reviews/desperados-3-review-revolvers-and-redos/1900-6417500/) — GameSpot
- [Desperados III version 1.2 update now available, adds four new 'Baron's Challenge' missions](https://www.gematsu.com/2020/07/desperados-iii-version-1-2-update-now-available-adds-four-new-barons-challenge-missions) — Gematsu
- [made easier (mod)](https://www.nexusmods.com/shadowtacticsbladesoftheshogun/mods/4) — Nexus Mods, Shadow Tactics
- Steam Community discussion threads, both games' hub pages (App 418240 and App 610370) — general play accounts on Shadow Mode's icons, the "?"/"!" badges, quicksave culture, and Showdown vs. Shadow Mode, none individually authoritative but converging on the same account across independent posters

## Nothing found

None of the ten headings came back empty. Headings 6 and 7 are the ones the genre note in
`interface.md` predicts will be thin, because this shelf is real-time and has no turn to hold a
strip or a bank on — and they are thin, but not empty: each names the mechanism the game
substitutes and says plainly that it is not the thing the heading asks about.

---

## 1. Screen furniture

**Both games.** A minimap with view-toggle buttons and a journal shortcut; a mission timer
counting time since the last quicksave, not time in mission; an objective tracker; a row of
character portraits along the bottom edge, each with a health bar, that doubles as the character-
select control (`1`–`5` in Desperados III select Cooper, McCoy, Hector, Kate, Isabelle by number,
`Tab` cycles). *verified* [gamepressure, Shadow Tactics interface](https://www.gamepressure.com/shadowtactics/interface-and-key-shortcuts/z1941c); [gamepressure, Desperados III controls](https://www.gamepressure.com/desperados-iii/controls/zad05a).

**The active character's action bar sits beside their portrait**, not in a separate panel: icons
for the abilities that character currently has, each with its bound key, plus a stance toggle and
a context-sensitive interact key (open a door, pick up a body). *verified*, same source.

**Two toggles exist for exactly the problem our own attention field solves differently: seeing
danger before committing to it.** Desperados III binds `Alt` to show every enemy's field of view
at once and `T` to show alarm zones; Shadow Tactics cycles a "viewcone mode" on backquote. Neither
is a persistent draw — both are held or toggled on demand, which is the opposite of our own
attention field, which paints permanently. *verified* [gamepressure, Desperados III controls](https://www.gamepressure.com/desperados-iii/controls/zad05a).

**A third toggle, `H`/`V`, highlights every interactive object on screen** — corpses, levers,
climbable ledges — because the isometric camera and dense scenery hide them otherwise. *verified*,
same sources.

**What a picture would settle.** Whether the timer, the objective tracker and the minimap are
always on screen together or whether any of them opens on a key, the way the instrument window
here is behind `O`. A single full-HUD screenshot from ordinary play, uncropped, settles it.

## 2. The soldier

**Actions are bound to letter keys beside the portrait** — `A`, `S`, `D`, `F`, `G` (Desperados
III adds `Y` for a fifth character), not a numbered `1`–`9` row — and hovering one shows a
tooltip with its cost and effect. *verified* [gamepressure, Desperados III controls](https://www.gamepressure.com/desperados-iii/controls/zad05a).

**`Ctrl` toggles a stance — crouch, for stealth and noise.** There is no third stance; height as
this game has it (standing, crouching, prone) does not exist here, only concealment-while-moving
versus not. *verified*, same source.

**Cancelling a whole plan has a key; cancelling one step of it may not.** `Shift`+the character's
number resets that character's queued Showdown Mode actions, `Shift`+`0` resets everyone.
*verified* [gamepressure, Showdown Mode](https://www.gamepressure.com/desperados-iii/showdown-mode/zfe2ec).
No source describes removing a single already-queued step without clearing the character's whole
plan — see the gap list.

**Shadow Mode/Showdown Mode is the genre-specific extension of "what an action costs and how it's
declared."** Press `Shift` (Shadow Tactics) or `Space` (Desperados III) to enter it, pick a
character, pick an ability, click a target or tile; the queued order is drawn on the target as a
small icon — a sword-in-a-circle for an attack, with a second, smaller crouch-icon badge attached
when the character will sneak rather than walk to reach it. Desperados III additionally shows a
run-or-walk icon on the queued move itself. `Enter` executes every character's queue at once.
*verified*, converging Steam Community accounts plus [gamepressure, Showdown Mode](https://www.gamepressure.com/desperados-iii/showdown-mode/zfe2ec).
Desperados III's version pauses the game for the whole planning phase; Shadow Tactics's does not
pause and exits back to real time after each single order, which is why coordinating more than
two characters in it is the thing every comparison between the two games singles out as improved
in the sequel. *verified*, Steam Community, "Showdown mode vs Shadow mode."

**What a picture would settle.** Whether removing one queued step from a multi-step Showdown Mode
plan is possible without resetting that character entirely — a player queuing two actions for one
character, then trying to undo only the second, with the result in frame.

## 3. The target

**There is no percentage anywhere.** Every outcome here is deterministic given position, facing
and detection state: a takedown either can be performed or it cannot, and the game shows which by
what the cursor or the target itself does, not by a number. This genre entry has nothing that
plays the role of a hit-chance line, a glancing factor, or an aimed-versus-snap choice — the
closest it comes is whether a queued approach is drawn walking or crouching, which changes noise
and visibility, not a chance to succeed. *verified*, converging sources above; no percentage
readout is described anywhere in the material surveyed.

**A target's own state is read off it directly, not off a panel line.** A knocked-out target
shows spinning stars and a body posture distinct from a standing one; an elite target — Long
Coat in Desperados III, Samurai in Shadow Tactics — carries a visibly different model and, once
engaged, a segmented health bar (three segments for a Long Coat) that most characters can only
partially deplete. *verified* [Long Coat — how to eliminate?](https://www.gamepressure.com/desperados-iii/long-coat-how-to-eliminate/z9d050); [How to Kill Long Coats](https://culturedvultures.com/desperados-3-how-to-kill-long-coats/); [Shadow Tactics Enemy Analysis, on samurai](http://www.vigaroe.com/2024/11/shadow-tactics-blades-of-shogun-enemy.html).

**How targets are switched is not documented anywhere found.** `Tab` in Shadow Tactics queues a
multi-point move path for the selected character, not a target cycle. *verified* [gamepressure, Shadow Tactics interface](https://www.gamepressure.com/shadowtactics/interface-and-key-shortcuts/z1941c).
No source describes a cycle-target key in either game — every target appears to be chosen by
pointing at it directly, which fits a genre where each character faces one specific enemy per
click rather than choosing among several in range. *inferred*, from the absence of any documented
key doing this job alongside a control scheme otherwise documented in full.

**What a picture would settle.** Whether there is any way to choose among two adjacent, both-
reachable targets other than moving the cursor between their models — a clip of a player queuing
an attack with two enemies standing close together, showing whatever they do (or don't) press.

## 4. The tile

**Movement is continuous, not banded.** Right-click moves, double right-click runs, and the path
previews continuously under the cursor before the click commits it — the genre convention
`conventions.md` already names ("hovering a reachable tile previews the path with its cost")
holds here for the preview-then-commit shape, but there is no discrete tile grid, no cost number,
and no reachable/unreachable band, because movement is not priced in points at all. *verified*
[gamepressure, Desperados III controls](https://www.gamepressure.com/desperados-iii/controls/zad05a).

**Cover and concealment are properties of the enemy's cone, not of the ground.** There is no
tile-level cover indicator independent of who is looking at it — a bush or tall-grass patch reads
as safe only because it renders any cone crossing it as striped rather than solid, and a crouching
character inside one is undetectable regardless of range. *verified* [Exploration and sneaking](https://guides.gamepressure.com/desperados-iii/guide.asp?ID=53317).
This is a real departure from the tactics canon's tile-based cover and from this game's own
per-tile attention field: here concealment is asked of the viewer, never stored on the ground.

**No detection ring exists on the tile the way Mutant Year Zero's does.** The whole of "what is
dangerous here" is answered by the cone, held or toggled into view, never a persistent radius
drawn at rest.

**What a picture would settle.** Whether a path preview ever changes appearance — colour, a
warning icon — when it crosses a tile a guard can see, independent of the cone's own rendering. A
screenshot of a queued or hovered path crossing partway through a cone, both inside and outside
it in the same frame, would settle whether the exposure warning lives on the path or purely on the
cone.

## 5. The enemy

**The cone is the whole of it, and it is genuinely the best in the set.** Each guard's field of
view renders as a cone with a solid region (100% detection) and a striped region — either a long-
range falloff or a segment a crouching character can cross unseen. Standing in a bush or tall
grass overrides the cone entirely. *verified* [Exploration and sneaking](https://guides.gamepressure.com/desperados-iii/guide.asp?ID=53317).

**Detection is a fill, not a switch, and the fill is drawn on the cone itself.** Walking into a
cone triggers a sound cue, the guard's cone snaps to face the intruding character, the game
briefly slows down, and the cone fills with yellow starting at the guard's eyes and spreading
toward the target; when the fill reaches them, detection is complete and the alarm follows.
*verified* [Game Design Deep Dive: Dynamic detection in Shadow Tactics](https://www.gamedeveloper.com/design/game-design-deep-dive-dynamic-detection-in-i-shadow-tactics-i-).
**This does not match `conventions.md`'s current description of "a meter over the head that fills
as you are noticed" — see What transfers, below.**

**Two badge icons carry the coarse states, and they are exactly Invisible, Inc.'s *noticed*
convention, independently arrived at.** A `?` over a guard's head means something has registered
— a noise, a body, a flicker of motion — and they are coming to check, without yet knowing what
for. A red `!` means a full alarm: the guard has confirmed a threat or found a body and will
raise nearby guards with it. *verified*, converging Steam Community and wiki accounts (Shadow
Tactics Fandom, Mission 1 page; multiple Steam Community threads independently describing the
same two icons the same way).

**Elite enemies are marked by model, not by icon**, and their three-segment health bar only
appears once a fight with them has started — there is no persistent tag naming them as an elite
before that. *verified*, sources under heading 3.

**What a picture would settle.** Whether the "meter that fills" language in `conventions.md`
refers to something drawn separately from the cone — a small gauge near the guard's head distinct
from the cone's own colour-fill — or is simply an imprecise description of the cone-fill mechanism
documented above. A screenshot or clip of a guard mid-detection with everything above and around
their head in frame, not just the cone, would settle it outright.

## 6. Turn order and time

**There is no turn, so there is nothing here to draw, and that is the finding.** Both games run
one continuous clock for every actor at once; nothing alternates and nothing is interleaved, so a
strip, a round mark, or a `whose go` question does not apply. Two things stand in for the
questions this heading is really asking:

- **The detection slow-motion (heading 5) is the closest thing to a *something just happened, look
  here* cue**, but it slows the shared clock rather than pausing anyone's turn, and it is a few
  seconds long by design, not a persistent state. *verified*, source under heading 5.
- **Showdown Mode's pause (heading 2) is a player-initiated stop of the whole clock for planning**,
  not a phase the game imposes — the inverse of an enemy-turn banner, since it is the player who
  freezes the world rather than the world freezing the player out of it.

**What a picture would settle.** Whether the detection slow-motion carries any UI beyond the time
dilation itself — a screen edge vignette, a word, a change to the cursor — and how long it lasts
before either resolving to full alarm or fading. A clip from just before a guard notices a
character to just after, at normal capture framerate so the slow-motion itself is visible in it.

## 7. Reactions

**Neither game has a held, scored, triggered-later action in the sense this game's overwatch is.**
There is no bank, no arc placed and left standing, no window that opens when something crosses it.
The nearest analogues, and how each falls short of the thing itself:

- **Hector's bear trap** (Desperados III) is placed and armed, then triggers on contact with
  anyone who walks over it — a declare-now, resolve-later object, which is the right shape, but
  it is bound to one tool on one character rather than a general stance any soldier can take.
  *verified* [Exploration and sneaking](https://guides.gamepressure.com/desperados-iii/guide.asp?ID=53317).
- **The whistle/lure** calls one or more guards to a location and they walk toward it over several
  seconds of real time the player still has to sit through and can act during — it is bait, not a
  trigger, since nothing fires automatically when they arrive; the player still has to act on them
  by hand. *verified*, same source.
- **A weakened elite** (heading 3) sits in a vulnerable window that any character can finish, which
  is a declare-then-later-resolve shape between two of the player's own actions rather than a
  reaction to the enemy's.

None of the three is drawn on the map the way a held arc is — a placed trap has no visible radius
until it fires, and neither source found describes one. *inferred*, from the absence of any
mention of a trap radius or marker in the sources on traps.

**What a picture would settle.** Whether a placed, armed trap shows any marker, radius, or icon
on the ground before it is triggered, or is visually indistinguishable from bare ground. A close
crop on a placed bear trap, from directly above if the camera allows it, with nothing else in
frame.

## 8. Camera and input

**Pitch is fixed; yaw is free by drag and steppable by key, in both games, differently bound.**
Desperados III: right-click-hold for free rotation (also `NumLock 4`/`6`), `Q`/`E` unclear on step
size from sources found. Shadow Tactics: `Q`/`E` step through what players describe as four fixed
views, `Left Alt`+mouse for free rotation in between. *verified* [gamepressure, Desperados III controls](https://www.gamepressure.com/desperados-iii/controls/zad05a);
Steam Community, Shadow Tactics camera-control threads (converging independent accounts).

**Panning is WASD or arrow keys, edge-scroll is on, and `Home`/similar resets the camera.**
*verified*, same sources.

**Zoom is mouse wheel, in both.** *verified*, same sources.

**There is no storey or level control.** Neither source describes a floor-cycling key, an X-ray or
transparency mode for roofs, or any camera behaviour tied to building height; the fixed, fairly
steep isometric pitch appears to be the entire answer to multi-storey buildings, and roof
underside geometry is reportedly left undetailed because the camera never gets under it to see it.
*verified*, weakly — [Shadow Tactics rendering breakdown](https://kosmonautblog.wordpress.com/2017/01/09/shadow-tactics-rendering-breakdown/)
confirms roof undersides are omitted for being unseen, but does not confirm what happens, if
anything, when a character (not the camera) passes under one. See the gap list.

**What a picture would settle.** Whether a roof or upper floor ever fades, cuts away, or is drawn
solid over a character who has walked beneath it. A screenshot of a character standing just inside
a roofed structure, camera at its normal pitch, is enough to answer whether this is a solved
problem or one the fixed pitch simply avoids asking.

## 9. Confirmation and refusal

**There is no confirmation dialogue anywhere documented, for anything, including a kill.** Every
action fires the instant it is clicked or a Showdown Mode plan is executed. This is the opposite
end of the genre from a confirm-before-firing convention, and it is deliberate: the actual safety
net both games supply is the quicksave/quickload cycle, which their own tutorials tell the player
to use often, and which most reviews and player discussions treat as the real undo mechanism in
place of any in-fiction one. *verified* [Desperados 3 Review — Revolvers And Redos](https://www.gamespot.com/reviews/desperados-3-review-revolvers-and-redos/1900-6417500/);
converging Steam Community accounts on both games' quicksave culture, including the developers'
own choice not to add a checkpoint alternative.

**What the game will not let a player do is enforced by blocking the action, not by warning about
it first.** Most characters cannot kill a Long Coat or Samurai outright — the attack lands, the
target drops to a distinct weakened posture instead of dying, and only specific characters or a
follow-up hit finishes it. The refusal is the outcome changing shape, not a dialogue appearing
before it. *verified*, sources under heading 3.

**No source describes an audible or visual refusal — a bark, a denial sound, a red flash — for an
action that simply cannot be attempted at all** (out of range, no line of sight). *inferred*, from
its absence across otherwise-detailed control and UI documentation for both games.

**What a picture would settle.** Whether attempting a genuinely impossible action (queuing an
attack on a target with no path to it, say) produces any feedback at all versus nothing happening.
A clip with sound of a player attempting one, framed so both the attempted click and whatever
does or doesn't follow are audible and visible.

## 10. What the game hides, and what its players added

**Neither game has Steam Workshop support.** *verified* [Nexus Mods, Shadow Tactics, "made easier"](https://www.nexusmods.com/shadowtacticsbladesoftheshogun/mods/4)
page and its surrounding Steam Community discussion confirm modding is off-platform, via Nexus,
not first-party.

**A player-authored mod exists specifically to soften Shadow Tactics's difficulty**, which is the
one documented case in this file of players patching something the shipped interface did not
expose as a setting — the base game offers three difficulty levels and no finer control.
*verified*, same source. What exactly the mod changes — numbers or warnings — was not confirmed;
see the gap list.

**Desperados III's first major post-launch update (1.2) added four free "Baron's Challenge"
missions and platform features players had asked for, including borderless fullscreen.**
*verified* [Gematsu, version 1.2 update](https://www.gematsu.com/2020/07/desperados-iii-version-1-2-update-now-available-adds-four-new-barons-challenge-missions).
This is bonus content and quality-of-life, not an interface rethink — nothing found suggests any
core HUD element shipped after launch in response to feedback, in contrast to the "highlight
interactive objects" and "show all cones" toggles, which read as day-one answers to the genre's
own visibility problem rather than a patched-in fix.

**What a picture would settle.** What the difficulty-easing Nexus mod for Shadow Tactics actually
changes — a changelog or its mod page's own description, read directly rather than through a
search snippet, would settle whether it is a numbers change (slower detection, wider "safe" cone
regions) or an interface change (an added warning), which decides whether this belongs under this
heading at all or is really a finding that belongs with heading 5.

---

## What transfers

- **The cone-fill-on-detection mechanism (heading 5) is strong, direct evidence for View's brief
  two, *the enemy's file, drawn*, and for `conventions.md`'s "What of the enemy is drawn" section**
  — but that section's line "a meter over the head that fills as you are noticed" does not match
  what this file found: the fill is on the cone, not a separate gauge. This is worth a look before
  the synthesis pass treats it as settled; it may be this game's own detection ring conflated with
  a different title, or a description imprecise enough that the fix is wording rather than
  substance.
- **The `?`/`!` badge pair (heading 5) independently corroborates the *noticed* borrowing
  `conventions.md` already proposes from Invisible, Inc.** — two unrelated stealth lineages
  reaching the same two-state answer is exactly the kind of convergence entry 058's rule treats as
  evidence for *convention* rather than *departure*.
- **The complete absence of any confirmation dialogue (heading 9), with quicksave/quickload as the
  substitute safety net, is a real precedent for brief three's no-undo-on-move stance** — but it
  also names the cost: both games are commonly discussed as leaning on save-scumming precisely
  because nothing in-fiction warns a player first. That is worth weighing against this game's own
  choice to show attention and earshot before a move commits, which is the safer version of the
  same bet.
- **Showdown Mode's pause-plan-execute shape (headings 2, 6, 7) is a genre precedent for "declare
  several actors' answers, then resolve them together" that is structurally close to brief six's
  reaction window**, solved by pausing the whole clock rather than by scoring and offering a
  default. It is not a reaction system — nothing in it responds to what the *enemy* does — but it
  is evidence that this genre has already built one answer to coordinating multiple actors against
  a single moment, in the one place the tactics canon has nothing to say (that canon never needs
  to coordinate more than one actor's turn at once).
- **Heading 7 found no genre precedent for drawing a held, not-yet-fired action on the map at all**
  — traps in this shelf are invisible until sprung. This means brief two and the reserve section of
  `conventions.md` are proposing something with no shipped analogue anywhere in the reference set
  so far, tactics canon or stealth shelf, which raises rather than lowers the stakes of getting the
  rung-on-the-body drawing right.

## The gap list

1. **Heading 5 — the cone-fill vs. "a meter over the head."** `conventions.md` currently credits
   this game with a detection meter drawn over the guard's head; this file found the fill is on
   the cone itself, with no separate gauge documented anywhere. **Picture:** a guard mid-detection,
   framed so the cone's colour state and the space directly above the guard's head are both
   visible in one shot. **Changes:** whether `conventions.md`'s citation needs correcting before
   the synthesis pass builds on it, and whether the borrowing for brief two is "the cone fills" or
   "a separate gauge fills," which are different things to draw.
2. **Heading 7 — whether a placed trap is ever visibly armed.** No source describes a radius or
   icon on a set trap before it fires. **Picture:** a close, top-down (or as steep an angle as the
   camera allows) crop of a placed, armed bear trap with nothing else in frame. **Changes:**
   whether this genre offers any precedent at all for drawing a declared-but-not-yet-triggered
   action on the ground, which bears directly on how much brief two's held-arc-on-a-hostile idea is
   inventing versus adapting.
3. **Heading 3 — how a target is chosen among several in range.** No cycle-target key was found;
   every target may simply be the one under the cursor. **Clip:** a player queuing an attack with
   two enemies standing close together, showing whether any key changes which one is selected.
   **Changes:** whether "Tab to cycle bodies," which `conventions.md` currently attributes to the
   tactics canon as a straightforward convention, has any support on the stealth shelf too, or
   whether target-cycling is a canon-only idea this game would be inventing rather than following.
4. **Heading 8 — whether a roof or upper floor ever occludes a character from the fixed-pitch
   camera.** Rendering sources confirm roof undersides are undetailed but not what happens to a
   character standing beneath one. **Picture:** a character walking from open ground under a roof,
   camera unmoved, both before and after the threshold in frame. **Changes:** whether "storey
   control" is a solved genre problem worth citing for View's height handling, or a non-problem
   this shelf never has to solve because its pitch is steep enough to always see under a roofline.
5. **Heading 9 — whether an impossible action gets any feedback at all.** No bark, flash, or sound
   was found for a flatly-impossible click. **Clip, with sound:** a player attempting an action
   with no valid target or path, showing whatever does or doesn't happen next. **Changes:** whether
   "silence is the refusal" is itself this genre's convention (which would support this game's own
   quiet handling of an impossible order) or whether a small missed cue is worth adding on top of
   it.
6. **Heading 2 — cancelling one step of a queued plan.** Only a whole-character reset (`Shift`+
   number) is documented. **Clip:** a player queuing two Showdown Mode steps for one character,
   then attempting to remove only the later one. **Changes:** whether the genre has an answer to
   "undo one order without losing the rest of the plan" that brief three's gesture set could use,
   or whether all-or-nothing is the honest precedent.
7. **Heading 6 — what, if anything, accompanies the detection slow-motion besides the time
   dilation.** **Clip:** from just before a guard notices someone to just after, at a framerate
   that keeps the slow-motion itself visible. **Changes:** whether this is pure game-feel or a
   genre precedent for the *their go* banner brief five specifies — both are answers to "something
   just happened here, look."
8. **Heading 1 — whether the timer, objective tracker and minimap are always simultaneously on
   screen.** **Picture:** one full, uncropped HUD screenshot from ordinary play. **Changes:** how
   much of the top-left-panel problem this genre actually avoids by placement versus merely
   shrinks by tucking things at the edges instead of stacking them in one block.
9. **Heading 10 — what the Shadow Tactics difficulty mod changes mechanically.** **Text or
   screenshot:** the mod's own changelog, read directly. **Changes:** whether this is a numbers
   fix (belongs nowhere near this file) or an interface fix players had to add themselves (belongs
   under heading 5's detection cues, not heading 10).
10. **Heading 4 — whether a path preview itself ever warns independent of the cone it crosses.**
    **Picture:** a hovered or queued path crossing partway through a guard's cone, both the covered
    and exposed portions in frame. **Changes:** whether exposure-while-moving is drawn only on the
    cone (as documented) or has a second, path-level cue this game's own destination-tile attention
    figure could be compared against.
