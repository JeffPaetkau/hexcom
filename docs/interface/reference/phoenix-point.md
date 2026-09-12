# Phoenix Point — reference file (pass one, documentary)

Snapshot Games, 2019, PC/console. **What this game is the authority on**: per-body-part
targeting against six anatomical parts, a free-aim reticle that shows dispersion rather than a
percentage, and physically simulated projectiles — the nearest shipped exemplar for contract 6's
six body faces and the ballistic-preview half of brief three. **What it is only an instance
of**: everything else. It has no contact file, no coarse alarm ladder, and (see heading 6) no
initiative strip at all — a faction-phase turn structure with one reaction (overwatch) rather
than a bank of reserved ones. Where the set splits on those questions, this file is one data
point among ten, not the strong one.

## Tag key

- **verified** — a published source, linked below.
- **remembered** — model knowledge, unchecked, and a candidate for the gap list.
- **inferred** — derived from another claim in this file, which it names.
- No **observed** tags: pass one, no screenshots exist yet.

## Sources

- [Combat](https://phoenixpoint.wiki.fextralife.com/Combat) — FextraLife wiki
- [Overwatch](https://phoenixpoint.wiki.fextralife.com/Overwatch) — FextraLife wiki
- [Controls](https://phoenixpoint.wiki.fextralife.com/Controls) — FextraLife wiki
- [Free Aim and Part Damage guide](https://se7en.ws/phoenix-point-free-aim-and-part-damage-guide-how-to-use-the-free-aiming-system-for-more-precise-shots/?lang=en)
- [Perception](https://phoenixpoint.fandom.com/wiki/Perception) — Fandom wiki
- [Status Effects](https://phoenixpoint.fandom.com/wiki/Status_Effects) — Fandom wiki
- [Will Points](https://phoenixpoint.fandom.com/wiki/Will_Points) — Fandom wiki
- [Behind the Scenes: Optimizing Phoenix Point's UI](https://phoenixpoint.info/blog/2020/5/14/behind-the-scenes-optimizing-phoenix-points-ui) — dev blog
- [\[MOD\] Enemy Alert Indicators](https://forums.snapshotgames.com/t/mod-enemy-alert-indicators/7435) — Snapshot forums
- [Way to tell who's alerted?](https://steamcommunity.com/app/839770/discussions/0/3432327866254034500/) — Steam discussion
- [Disable "right-click to move"](https://steamcommunity.com/app/839770/discussions/3/2992044576642383860/) — Steam discussion, feedback board
- [Assorted Adjustments](https://github.com/Mad-Mods-Phoenix-Point/AssortedAdjustments) — mod, GitHub
- [Action Points, Movement, FREE Aim, Vehicle combat, Cover and more](https://steamcommunity.com/sharedfiles/filedetails/?id=2331577913) — Steam Community guide
- [Silly Accuracy Question](https://steamcommunity.com/app/839770/discussions/0/601893317626600700/) — Steam discussion
- [Phoenix Point tips and guide](https://www.pcgamer.com/phoenix-point-tips-guide/) — PC Gamer
- [Clarifying the aiming system](https://forums.snapshotgames.com/t/clarifying-the-aiming-system/4236) — Snapshot forums

## Nothing found

- **Heading 6, an initiative strip**: none exists to find. Confirmed absent (see heading 6), not
  a research gap.
- **Heading 8, a storey/level control**: no dedicated key or gesture surfaced anywhere in the
  published material. Either it doesn't exist and the camera pitch is enough, or it exists and
  nobody wrote it down — the gap list carries this rather than guessing which.
- **Heading 9, an explicit confirmation dialogue**: no source describes one, for anything —
  ending a turn, throwing a grenade near a teammate, firing through fog at an unconfirmed target.
  Several player threads (heading 10) exist *because* nothing warns them.

---

## 1. Screen furniture

Thin, and thin for a documentary reason: nobody writing about this game's UI describes it as a
static layout, only as pieces that appear when something is selected. What's confirmed:

- A per-soldier ability bar appears along the bottom when a unit is selected, built from several
  Unity canvases kept separate so that hovering or pressing a button only rebuilds the ability
  bar's own canvas — a performance detail, but it **verified** the bar is bottom-of-screen and
  soldier-scoped rather than a fixed always-on strip (Behind the Scenes devblog).
- A list of visible enemies is shown at the bottom of screen alongside the ability bar — both the
  enemies the selected soldier can currently engage and every enemy the squad as a whole can see
  — **verified** (Action Points/Movement/Free Aim guide). This is the closest thing to a target
  switcher (heading 3) that surfaced.
- Cover is read off small shield icons rather than a persistent readout: full shield for full
  cover, half shield for 50%, none for exposed — **verified** (Combat wiki). Whether these sit on
  the tile, on the soldier, or in a side panel did not surface.
- Character info panels showing per-soldier stats and combat status were added to the tactical
  layer at some point in development, and portraits on the tactical layer went through community
  feedback as a separate change — **verified**, but neither source pins a screen position (August
  2019 dev update; Snapshot forums thread on tactical-layer portraits).

*What a picture would settle.* Nothing above says where the ability bar, the enemy list, and any
portrait strip sit relative to each other, or whether anything persists on screen with no unit
selected at all.

## 2. The soldier

Four action points per turn, standard, adjustable by status (tired, exhausted, paralysed, dazed
and panicked reduce it; Onslaught and Rapid Clearance increase it) — **verified** (Combat wiki).
Cost is a fraction of the bar rather than a flat number: inventory actions and pistol shots cost
a quarter, assault rifles and grenades a half, sniper rifles and machine guns three quarters —
**verified**, same source. The ability bar shows this consumption directly on the bar rather than
as a separate number, though no source confirms whether the fraction is drawn as a filled
segment, a fading icon, or something else.

Some abilities cost Will Points instead of or alongside Action Points — Overwatch spends both,
Gunslinger spends Will only — and the ability icon carries a number for the Will cost —
**verified** (Combat wiki; Will Points wiki). Hovering an ability updates the UI, per the same
devblog that describes the canvas split, but what the hover reveals — range, cost breakdown, a
description — is not said.

Cancel is `Right Click` / `Esc`, both bound to the same action ("Move soldier/Cancel Action") —
**verified** (Controls wiki). How far back cancel goes — one step, the whole move, back to full
Action Points — did not surface, and it matters: a Steam feedback thread exists specifically
because right-click doubles as "move here" and players hit it trying to cancel and instead
committed a move (heading 10).

*What a picture would settle.* A soldier selected with the ability bar and the cursor hovering
one ability, showing what the tooltip contains and whether the AP-fraction is drawn on the bar
itself or elsewhere.

## 3. The target

This is the game's reason for being in the set, and it is the most precisely documented heading
in the file.

**Two aiming modes.** By default a shot auto-targets the enemy's centre of mass. Scrolling the
mouse wheel while a weapon is readied enters Free Aim, where the reticle is placed by hand —
**verified** (Free Aim guide; Combat wiki). Free Aim is a gesture on top of the default, not a
separate menu: nothing describes a click to *enter* aiming mode other than starting to scroll.

**The reticle is two concentric circles, not a percentage.** All shots land inside the outer
circle; 50% of shots are expected to land inside the inner one — described consistently across
three independent sources as a blue/red or blue/inner pair depending on which is being cited
(Combat wiki calls them "blue" and "red"; the Free Aim guide calls them outer/inner without
colour; the Steam "Silly Accuracy" thread frames the same two circles as *Effective Range*, the
distance at which a human-sized target fits inside the 50% circle) — **verified**, terminology
inconsistent across sources, which the gap list should not paper over. A more accurate weapon
draws smaller circles; a less accurate one draws bigger ones — **verified** (Free Aim guide).
Fine adjustment is a click-drag on screen, not a separate control — **verified** (Combat wiki).

**Targeting is per anatomical body part, not per facing.** In Free Aim, hovering a part shows an
information box: the part or held-equipment's name, its armour rating, its hit points, and what
disabling it does — a headshot lowers max HP and causes bleeding, a leg hit impairs movement, a
weapon-arm hit destroys that weapon — **verified** (Free Aim guide; Combat wiki). Armour is
per-part and subtracted before damage: the guide's own worked example is 30 damage against 10
armour landing as 20 — **verified**. This is anatomical (head / torso / arms / legs / held
equipment), not directional. **It is not contract 6's six faces, and the two should not be
conflated in synthesis**: Phoenix Point earns its place on *granular per-part targeting existing
and being read from a hover*, not on facing being one of the parts.

**No hit-chance number is shown anywhere in any source.** Every description of "how good is this
shot" is the circle geometry itself — smaller inner circle relative to the target silhouette
reads as a better shot. Whether a number exists elsewhere in the UI and simply wasn't mentioned,
or whether the circles really are the entire readout, is exactly the kind of claim the gap list
exists to unresolve rather than guess at.

Switching targets: the bottom-of-screen enemy list (heading 1) is the only mechanism that
surfaced. No dedicated cycle-target key appears in the controls list.

*What a picture would settle.* A shot lined up in Free Aim with a body part highlighted and its
information box open — settles the box's exact wording and whether a hit-chance figure sits
anywhere near it. Second: the enemy list at the bottom of screen with more than one target in it,
to see whether clicking a list entry re-aims the reticle or only recentres the camera.

## 4. The tile

Selecting a soldier draws two lines on the ground: blue for the range reachable while still
keeping an action in reserve, yellow for the maximum range that spends everything —
**verified** (Combat wiki). This is a threshold band, not a gradient, and it is drawn on
selection rather than on hover.

Cover is the shield icons from heading 1, read per-tile as the soldier considers moving there.
Cover in this game is binary at the tile — full or half — not the graded exposure contract 4's
concealment model uses; whether it can be partial per body part (a leg exposed, a torso covered)
is exactly what the free-aim body-part armour system in heading 3 would suggest, but no source
draws that connection explicitly for the *movement* preview rather than the *shot* preview.

There is no concealment ring drawn on the player's own tile. The nearest thing is the reverse:
hovering an already-spotted enemy draws an orange circle showing the range at which *it* can
detect the currently selected soldier — **verified** (perception/LoS discussion, Steam). That is
a detection-range preview belonging to the enemy, read by the player, not a stealth indicator the
player's own soldier carries.

*What a picture would settle.* A soldier mid-move with both the blue and yellow lines visible and
at least one tile inside them showing a shield icon — settles whether the shield is drawn on the
tile itself or in a side panel, and whether it updates live as the cursor moves along the path.

## 5. The enemy

Weak, and weak in a way that is itself the finding. Perception is a stat (1 perception ≈ 1 tile
of detection range; default 30, many hostiles at 60) and an enemy is "Alerted" the instant a
soldier enters its perception range and line of sight, or the instant that enemy is fired on, or
the instant a nearby ally alerts it — **verified** (Perception wiki). There is no coarse rung
between unaware and alerted; the transition is binary and immediate, matching the pattern
`interface.md` already expects most of the set to show for this heading.

**What happens on screen at that transition is the actual gap, and it is well documented as a
complaint rather than a feature.** A brief orange "Alerted [class icon]" message pops up and
disappears; several independent player threads describe it as easy to miss and impossible to
recover once missed, and one names the base game's information panel directly: it does not show
whether an enemy is currently aware of the player at all, only the transient popup at the moment
it changes — **verified** (Steam "Way to tell who's alerted?" thread). A mod exists solely to
draw a persistent icon over alerted (or, in its inverted variant, unalerted) enemies —
**verified** ([MOD] Enemy Alert Indicators). Fog thickens around some enemy types and can hide
them further; grenades disperse fog and can force a reveal — **remembered**, not independently
verified here.

There is no marker at all for a *remembered but currently unseen* contact — nothing in any source
describes a persisted last-known-position after an enemy breaks line of sight. Read together with
heading 10, this looks like an omission players noticed rather than a considered design.

*What a picture would settle.* The moment the "Alerted" popup fires — a clip, not a still, since
its duration is exactly the complaint — and a still of the enemy information panel with an
alerted unit selected, to see directly whether alert state is anywhere in it as the Steam thread
claims.

## 6. Turn order and time

**Confirmed absent, not merely undocumented.** The turn structure is faction-phase: the player's
whole side acts in an order the player picks freely, soldier by soldier, then the enemy side gets
its whole phase — **verified** (multiple sources agree; none describes a unit-level initiative
queue or a strip showing upcoming actors). There is nothing here resembling XCOM 2's alien-turn
banner or a Persona-style order rail, because there is no ordering to show: any of the player's
un-acted soldiers can go next, by the player's own choice.

The one exception to strict phase separation is Overwatch (heading 7) and a documented
"interrupt": moving a soldier into new sight of an enemy can truncate that move and return the
soldier to the last square from which the reveal was survivable, mid-animation, functioning as an
interruption of the player's own turn rather than the enemy's — **verified**, loosely (a Steam
thread describes the mechanic; no source names it precisely). What the player is shown while this
happens — a full stop, a camera cut, a warning icon — did not surface.

*What a picture would settle.* This is one of the headings pass two probably cannot answer for
games 6–10 generally, but it can here: a clip of the reveal-interrupt actually firing, framed
before, during and after, is the only way to know what "the player is shown while it is not their
turn" even means for a game with no enemy-turn HUD state at all.

## 7. Reactions

Overwatch is the only reservable reaction found. It is a status effect placed on a soldier,
costing Action Points (and, per heading 2, apparently sometimes Will) that stays active through
both the enemy's phase and the player's own next phase — **verified** (Combat wiki; Overwatch
wiki, though the Overwatch wiki page itself is otherwise a stub). It fires once, at the first
enemy to enter the covered area, not on every entrant — **verified** (Combat wiki).

**The arc is drawn on the ground from the soldier's eye position**, lighting the area that will
trigger it, and its angle is adjustable before confirming with `Ctrl` + scroll-wheel — **verified**
(forum thread on overwatch cone mechanics). Maximum angle is weapon-dependent: assault rifles and
handguns get wide cones, sniper rifles and heavy weapons narrow ones, and the cone's height cutoff
is the soldier's own perception — **verified**, same source. This is close kin to `OverwatchArc`'s
arc-widths-per-weapon-class shape, and probably this file's second-strongest transfer candidate
after body-part targeting.

No source describes what the trigger moment looks like on screen beyond "it fires" — no flash on
the cone, no distinct sound cue mentioned, nothing about whether the arc stays drawn afterward or
vanishes the instant it resolves.

*What a picture would settle.* The cone being drawn and adjusted before confirming Overwatch —
settles whether the angle-adjust gesture (`Ctrl`+scroll) shows a live preview or a stepped one.
Second, ideally a clip: the instant an enemy crosses the cone and the reaction fires, to see
whether the game marks that moment visually at all or only via the shot itself.

## 8. Camera and input

From the Controls wiki, verbatim: `WASD`/arrows pan, `Q`/`E` rotate 90°, `T`/`G` zoom in/out, and
holding middle-mouse forces maximum zoom-out — **verified**. `Left Click` selects/confirms,
`Right Click` moves the selected soldier or cancels, `Tab` moves to the next character, `X` cycles
the weapon selector, `1`–`4` pick a weapon directly, `F` fires, `Y` sets Overwatch, `Space` selects
the "End Action" ability, double-`Space` ends that soldier's turn, `Backspace`/`End` ends the
faction's turn, `I` opens inventory, `Esc` cancels — **verified**, same source.

Rotation is stepped (90° per press), not a free drag, which the source states outright rather
than leaving to inference. No source names a level/storey key; buildings are multi-floor by
several accounts, and camera pitch alone may be doing that job, or a control exists that nobody
documented — carried to the gap list rather than guessed.

*What a picture would settle.* A multi-storey building with the camera at two different pitches or
heights, to settle whether storeys are read by pitching the camera or by a dedicated control this
research did not find.

## 9. Confirmation and refusal

**No source, anywhere searched, describes a confirmation dialogue for anything** — not ending a
turn with soldiers unacted, not throwing a grenade near a teammate, not firing through fog at an
unconfirmed silhouette. That absence is corroborated indirectly by heading 10: the "right-click to
cancel is also right-click to move" complaint and the modded fix for it are exactly the kind of
friction a confirmation step would normally exist to prevent, and nobody describes the game
offering one instead.

Nothing found describes the game refusing an action outright either — no greyed-out button
tied to a specific rule, beyond the ordinary running-out-of-Action-Points case implicit in
heading 2's cost fractions.

*What a picture would settle.* This heading may simply be empty in the shipped game, which is
itself the finding contract 6's asymmetry-aware conventions should weigh against — a still cannot
prove a negative, but a played session reaching for "are you sure" and not finding it would.

## 10. What the game hides, and what its players added

Three separate, independently-sourced player fixes, all aimed at the same kind of gap — the base
game tracks a state internally and does not surface it, or surfaces it too briefly to use:

1. **Alert state.** Covered in heading 5: a transient popup, no persistent indicator, and a mod
   (Enemy Alert Indicators) built specifically to draw one — **verified**.
2. **Accidental commits from the overloaded right-click.** Right-click means both *move here* and
   *cancel*, and a Steam feedback thread exists asking for it to be split; the *Assorted
   Adjustments* mod includes an option to disable right-click-to-move in tactical missions
   entirely so the key can only cancel — **verified** (Steam feedback thread; Assorted
   Adjustments mod page).
3. **Enemy-turn pacing.** Multiple Steam threads, separate from the two above, describe long or
   apparently-infinite enemy turns with no way to speed them up or see what's happening — not a
   HUD gap exactly, but adjacent: a turn-structure legibility problem serious enough to generate
   its own recurring complaint thread — **verified**, though this is a performance/AI complaint
   more than an interface one and the gap list should not overweight it.

The pattern across all three: the interface's failures in the published record are omissions
(a state that exists and isn't shown) rather than bad drawings of something that is shown. That
is a different shape of lesson than most of the set is expected to offer, and worth flagging to
synthesis as such rather than folding into "cone drawing" or "readout clarity" categories that
don't fit it.

---

## What transfers

- **Heading 3's body-part hover box** is the strongest single finding in the file for brief three
  (the shot readout) and for contract 6's six faces — with the caveat, stated once and worth
  repeating in synthesis, that Phoenix Point's parts are anatomical and contract 6's are
  directional. The transfer is *a hover reveals a named part with its own armour/HP/effect*, not
  the part taxonomy itself.
- **Heading 3's two-circle dispersion reticle** bears on brief three's aiming-mode question
  directly: a percentage is not the only legible way to show a shot's spread, and a circle-based
  readout is the only alternative any game in the set (so far) uses instead of a number.
- **Heading 7's per-weapon-class arc width, adjusted live before confirming**, bears on
  `OverwatchArc` and on whichever brief covers declaring a reaction — this game answers *how wide*
  with the same shape our config already uses (arc by weapon class), which is evidence for
  convention rather than departure on that specific point.
- **Heading 5's alert-state omission and its modded fix** is a proposal for the interface
  territory's own conventions doc, not for Core: whatever brief covers the alarm ladder or a
  contact's UI should treat "persistently visible, not transiently announced" as a requirement
  this game's own players proved necessary by building it themselves.
- **Heading 6's confirmed absence of any initiative strip** bears on whichever brief assumes one
  exists across the genre; this file is evidence that faction-phase-with-free-order is also a
  live convention, not just older games' choice.
- **Heading 9's apparent absence of any confirmation gesture, read together with heading 10's
  right-click complaints**, bears on brief nine's silent-vs-warned question from the opposite
  direction most of the set will argue it from: this is a data point for what happens when a
  genre entry has *no* warnings rather than the genre's usual mix of some.

## The gap list

1. **Heading 1 — the persistent layout.** No source draws the whole HUD with nothing selected, or
   says whether the ability bar and enemy list are the only things that ever appear at the bottom
   of screen. *Picture:* a plain tactical view, nothing selected, full screen, to see what's on it
   by default. *Changes:* whether this file's "thin because nothing is persistent" reading is
   correct or an artefact of what happens to get screenshotted.

2. **Heading 5 — the "Alerted" popup's actual duration and position.** Multiple sources agree it
   is brief and easy to miss but none gives a duration or an on-screen location. *Clip:* a soldier
   spotted by a previously-unaware enemy, framed a second before and several seconds after, full
   screen. *Changes:* whether "brief" means sub-second (a genuine miss risk) or a few seconds (an
   attention problem, not a rendering one) — these want different fixes if this game's failure
   mode is one worth avoiding.

3. **Heading 3 — whether a hit-chance number exists anywhere near the reticle.** Every source
   describes the circles and none mentions a percentage, but "no source mentions it" is weaker
   than "no source shows the full screen while aiming." *Picture:* a shot lined up in Free Aim,
   full screen including any side panel, corner readout, or tooltip — not a crop of the reticle
   alone. *Changes:* whether this game is evidence that a probability display can be dropped
   entirely in favour of geometry, which is a live question for brief three.

4. **Heading 2 — what an ability's hover tooltip actually contains.** The devblog confirms hovering
   triggers a UI update; nothing says what appears. *Picture:* an ability icon hovered, with
   whatever tooltip or panel that produces, full screen. *Changes:* whether this game has anything
   to say about brief one's "where do the figures live" question, or is silent on it too.

5. **Heading 8 — the storey/level control, if one exists.** *Picture, ideally a short clip:*
   a multi-floor building, the camera changing height or pitch, with whatever key or scroll
   gesture is doing it visible in an overlay if the capture tool can show one. *Changes:* whether
   this game has an answer to a control question our own interface will also need, or whether
   camera pitch alone is standing in for it here too.

6. **Heading 9 — whether any confirmation exists that this research simply didn't surface.**
   *Clip:* ending a turn with an un-acted soldier, and separately, throwing a grenade with a
   teammate near the blast radius. *Changes:* whether heading 9's "confirmed absent" claim in this
   file should be softened to "not found" — a real difference for how much weight synthesis can
   put on it.

7. **Heading 4 — whether the shield cover icon is drawn on the tile or in a side panel, and
   whether it updates live while dragging the move preview.** *Picture:* mid-drag of a movement
   path, cursor on a half-cover tile, full screen. *Changes:* whether "cover read at a glance
   during planning" is a convention this game actually offers or one this file over-credited it
   with from prose alone.

8. **Heading 6 — what the screen shows during the reveal-interrupt.** Named in one imprecise
   source; no still can settle a truncated, resumed action. *Clip:* a soldier's move interrupted
   by a new enemy sighting, several seconds either side. *Changes:* whether this counts as this
   game's answer to "what does the player see while control is briefly taken away," which every
   other game in the set answers differently.
