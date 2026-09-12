# Invisible, Inc. — reference file

Klei, 2015. The authority on the entire left column of this genre: a turn-based stealth tactics
game where the enemy is drawn by what is known about it rather than by what it is, an alarm ladder
whose sub-levels are hidden on purpose, and a *noticed* state short of *seen*. It is only an
instance, not an authority, on combat — its guns are a last resort with no readout to speak of —
and on turn order, which it does not interleave at all. `conventions.md` already leans on it
harder than any other game in the set; this file is the evidence underneath that reliance.

## Tags

| | |
|---|---|
| **verified** | a published source, linked at the point of use. |
| **remembered** | model knowledge, unchecked against a source. Flagged for the gap list below. |
| **inferred** | derived from another claim in this file, which it names. |

Pass one. No **observed** tag appears in this file, and that is not a shortfall — see
`../../subprojects/interface.md`.

## Sources

- [Game Design Deep Dive: Alarm systems in Klei's Invisible, Inc.](https://www.gamedeveloper.com/design/game-design-deep-dive-alarm-systems-in-klei-s-i-invisible-inc-i-) — the technical designer, on the record, on the alarm meter's design history.
- [`vision` — Invisible, Inc. community wiki](https://iiwiki.werp.site/vision) — vision cone geometry and the watched/noticed/hidden labels.
- [`guard_behaviour` — Invisible, Inc. community wiki](https://iiwiki.werp.site/guard_behaviour) — the full state machine: stationary, patrolling, investigating, alerted, overwatch, tracking.
- [`alarm_tracker` — Invisible, Inc. community wiki](https://iiwiki.werp.site/alarm_tracker) — where the meter sits and what it stops showing at the top of its range.
- [Invisible, Inc. — Any Key To Start](https://anykeytostart.wordpress.com/2015/05/27/invisible-inc/) — an interface critique written by another designer: contextual action buttons, the AP readout's position, the augment-slot ambiguity, cone-shading clutter.
- [Invisible Inc. Beginners Guide — Steam Community](https://steamcommunity.com/sharedfiles/filedetails/?id=455743741) — portrait panel, AP display, the Incognita access button and its device labels.
- [What Works And Why: Invisible Inc — Tom Francis](https://www.pentadact.com/2014-12-29-what-works-and-why-invisible-inc/) — turn structure, the reliability of the vision readout as a design choice, and the *Abort Mission* naming flaw.
- [Invisible, Inc. — TV Tropes, "Game Mechanics"](https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/InvisibleInc) — the no-hit-points, no-accuracy claim for combat.
- [UI Tweaks (Mod) — Invisible, Inc. Wiki, Fandom](https://invisibleinc.fandom.com/wiki/UI_Tweaks_(Mod)) and [its source](https://github.com/osheroff/ui_tweaks) — the community's own list of what the shipped HUD leaves out.
- Steam discussion threads on camera rotation (`Q`/`E`, no free rotation) and the `Alt` map-reveal key, found by search and not independently re-fetched — flagged **verified** where a thread is quoted directly, with the caveat in the gap list.

## Nothing found

Heading 3, **the target**, is empty by design and that is this file's largest finding — see the
heading itself. Heading 6, **turn order and time**, has no strip or interleaving to describe,
because the game does not interleave. Neither is a gap in the research; both are reported as
findings under their own headings.

---

### 1. Screen furniture

- **Alarm tracker, top right.** Current level and the number of steps to the next one.
  *(verified — [alarm_tracker](https://iiwiki.werp.site/alarm_tracker))*
- **Agent portraits, bottom left**, one per living agent, click to select; clicking a portrait a
  second way opens a panel of that agent's augments, inventory and stats. *(verified —
  [Beginners Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=455743741))*
- **Max AP, top left**, near the portraits: what the selected agent will have at the start of its
  *next* turn, not what it has now. *(verified — same source)*
- **The Incognita button, top left**, reading "Access Incognita >". Pressing it swaps the whole
  screen into the hacking layer: hackable devices are boxed in red with a firewall number, daemons
  get a red circuit-board texture around the number, and PWR-cost programs list down the left edge
  under the button. It is a mode, not a panel — the tactical HUD is not visible while it is open.
  *(verified — same source)*
- **PWR counter.** Starts at 10 by default and is spent to enter Incognita mode and to run
  programs; some augments and events add to it. Screen position not confirmed independently — see
  the gap list. *(remembered)*
- **Nothing is drawn at the top centre or bottom centre of the frame in any source consulted.**
  The furniture is a left column (agents, AP, Incognita, PWR) and a right corner (alarm); the
  centre is the map and nothing else, which given `conventions.md`'s finding about this game's own
  panel-heavy HUD is worth having named precisely rather than gestured at. *(inferred, from the
  absence of any source placing anything else)*

**What a picture would settle.** A full, unscaled capture of the tactical screen with at least one
agent selected, showing every corner at once — the sources above describe pieces from different
years of patches and none gives one authoritative screenshot of the whole frame together.

### 2. The soldier

- **No action bar.** Abilities are triggered from **context buttons that appear on the world
  object itself** — a door, a console, a guard's body — rather than from a row of icons on the
  soldier. Klei's own choice, and the critique praising it is explicit: "your mouse never leaves
  the area you're focusing on." *(verified — [Any Key To Start](https://anykeytostart.wordpress.com/2015/05/27/invisible-inc/))*
- **Hover on a destination tile** changes the AP readout above the agent's head to the AP
  remaining *after* the move, not the cost of the move. The critique flags this as a minor cost
  rather than a benefit: the number sits above the agent, not at the cursor, so a player planning
  a long path must look away from where they are pointing to read it. *(verified — same source)*
- **No confirm step and no undo on a move.** Clicking a destination tile commits the move at once.
  Steam's own discussion threads asking for an undo or a confirm-before-commit option are asking
  for something the shipped game does not have; there is no official response offering one.
  *(verified — [Steam Community Discussions, "Undo last move?"](https://steamcommunity.com/app/243970/discussions/0/616187203942781866/))*
- **Cancel exists at the level of a declared action, not a spent point.** Right-click, or `Esc`,
  backs out of a context-button prompt before it is taken; it cannot back out of a move already
  clicked. *(remembered — see gap list)*
- **Disabled-state icons.** An ability whose cost or condition cannot currently be met — the
  critique's example is a taser with no charge — is shown greyed out on its context button rather
  than hidden, so the player learns the constraint by seeing the refusal. *(verified — [What Works
  And Why](https://www.pentadact.com/2014-12-29-what-works-and-why-invisible-inc/))*

**What a picture would settle.** One frame with an agent mid-path-preview and the AP readout
visible above its head, and a second showing a context-button prompt open on a guard's body with
at least one action disabled — confirming the disabled-icon treatment described only in prose
above.

### 3. The target

**This game has no shot readout, because it has nothing for one to break down.** Guns and melee
takedowns in Invisible, Inc. do not roll to hit: every attack that can be attempted connects.
*(verified — [TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/InvisibleInc): "agents no
longer have the stats of hit points or accuracy... all hits will kill their targets")* What stands
in for a readout is a binary the game checks before the attack is even offered: **armour piercing
against armour class**. A weapon's Pierce value is compared to a guard's armour, and an attack
that cannot get through is not merely a bad idea — the game will not let the player attempt it at
all, so there is no wasted click and no failed roll to explain. *(verified — [Steam guide, "Items,
Augments and Enemies"](https://steamcommunity.com/sharedfiles/filedetails/?id=470340865))*

Targets are switched by clicking a different body directly; there is no cycling key, because there
is no mode to cycle within — a shot is one click on one guard, exactly as a move is one click on
one tile.

**Why this is the heading's most valuable row rather than its thinnest.** A genre convention this
game's own author-list treats as load-bearing — a headline number with a breakdown behind a hover
— has nothing to attach to here, because the design removed the quantity the number would have
described. Combat is not the information game; avoiding it is. The absence is the finding, and it
argues for `briefs.md`'s target-readout brief by counter-example: a hit-chance line is a genre
convention for games where combat is the content, and this game's nearest stealth relative
confirms that by not having one either.

**What a picture would settle.** Nothing — this is a claim about absence, and a screenshot cannot
prove a negative more convincingly than the sourced claim above already does. What would help
instead is a clip of an attempted attack against over-armoured cover being refused, to confirm the
game blocks the click rather than allowing it and rolling a miss.

### 4. The tile

- **Reachable tiles are shown on hover** as the agent moves the mouse; the AP-remaining figure
  above the agent's head updates live rather than the tile itself carrying a number.
  *(verified — [Any Key To Start](https://anykeytostart.wordpress.com/2015/05/27/invisible-inc/))*
- **Vision is drawn as striped shading on the tile itself**, in three bands: dark red for
  **watched** (primary vision — stepping in is seen at once), light red for **noticed**
  (peripheral vision — the tile *looks* watched but is not, the game's answer to `conventions.md`'s
  cited *peripheral* distinction), and yellow for **hidden**, meaning the tile is behind cover from
  every observer who could otherwise see it. No shading at all means no corporate entity has vision
  on the tile. *(verified — [vision](https://iiwiki.werp.site/vision), corroborated by [Beginners
  Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=455743741))*
- **Tiles once seen and now out of sight are shaded darker and less saturated** rather than reset
  to unknown — a fog-of-war memory layer distinct from the live vision layer above it.
  *(verified — [vision](https://iiwiki.werp.site/vision))*
- **The striping itself was criticised as ambiguous** by another interface designer: "it's not
  very clear what happens on squares with partial shading," with a suggested fix of full shading
  for seen tiles and none for unseen rather than a stripe pattern in between. The game also ships
  an alternate "reduced walls" display mode that trades geometric fidelity for legibility — evidence
  that Klei itself treated the default rendering as a readability compromise rather than a settled
  answer. *(verified — [Any Key To Start](https://anykeytostart.wordpress.com/2015/05/27/invisible-inc/))*
- **No cover icon separate from the vision shading.** Cover is not drawn as its own indicator on a
  tile; it is expressed entirely through which vision band the tile falls into, which is a
  narrower answer than `conventions.md`'s target genre gives (a shield icon distinct from the hit
  chance). Whether cover has any effect once a fight actually starts — as opposed to only gating
  whether a tile is seen — was not settled in what this pass read; see the gap list.

**What a picture would settle.** A single frame showing all three vision bands at once around one
guard, ideally with the fog-of-war (seen-but-not-visible) shading also present somewhere in frame,
to check the four visual states against each other directly rather than against four separate
descriptions.

### 5. The enemy

- **A guard not currently seen is not drawn at all**, full stop — no silhouette, no last-known
  marker, while the corporate side has no vision on the tile it last occupied.
- **The instant a guard leaves the player's vision, a "red ghost" is left at its last known
  position for the remainder of that turn only**, then it too disappears. *(verified —
  [vision](https://iiwiki.werp.site/vision))* This is a strictly shorter memory than
  `conventions.md`'s recommended ghost-marker-with-a-line-to-the-truth: it does not persist across
  turns and it carries no belief about where the guard went next, only where it was.
- **Five behavioural states, each with its own icon:** stationary (no icon), patrolling (an icon
  the source names but does not describe further), **investigating** — a yellow triangle with a
  question mark, plus a separate floating `?` marking the interest point the guard is walking
  toward — **alerted/hunting** — a red triangle with an exclamation mark, permanent for the rest of
  the mission — and **overwatch**, drawn as its own state, in which an armed guard who currently
  sees a non-incapacitated agent turns to face it, shouts (alerting nearby guards), and will shoot
  any agent who takes an action that keeps it visible or who is still visible at the start of the
  next corporate turn. A sixth, **tracking**, rides along with overwatch: the guard turns to keep
  facing a moving target within its vision, including peripheral vision, but will not turn for a
  target that merely *ends* a move in peripheral — one safe tile of drift is built in.
  *(verified — [guard_behaviour](https://iiwiki.werp.site/guard_behaviour))*
- **Escalation is automatic and irreversible in one direction**: seeing an agent, a knocked-out or
  dead body, a rescued NPC, or a destroyed drone moves a guard straight to alerted with no
  intermediate step, and alerted has no way back down for that guard for the rest of the mission.
  Investigating, by contrast, is fully reversible — a guard that finds nothing at the interest point
  returns to its previous state and forgets it was ever suspicious. *(verified — same source)*
- **The alarm ladder is six steps, each five sub-steps wide, and the sub-steps are invisible by
  design.** It rises by one step at the end of every corporate turn and on certain events (a guard
  going alerted among them); every fifth step is a full level and triggers a scripted, named
  consequence — more cameras active, firewalls raised, another patrol, an elite enforcer, a
  pinpointed agent location. Above level 6 the tracker stops visibly updating on screen even though
  the underlying value keeps rising. *(verified — [Game Design Deep
  Dive](https://www.gamedeveloper.com/design/game-design-deep-dive-alarm-systems-in-klei-s-i-invisible-inc-i-)
  and [alarm_tracker](https://iiwiki.werp.site/alarm_tracker))* The designers renamed the mechanic
  from "ALARM" to "SECURITY LEVEL" specifically because playtesters read the original naming and
  numbering as more informative than it was meant to be. *(verified — Game Design Deep Dive)*

**What a picture would settle.** One frame each of investigating and alerted, close enough to read
the triangle icon clearly, and — harder — a frame or short clip catching the exact moment a guard
flips from investigating back to stationary with nothing found, since every source describes that
transition in prose and none shows it.

### 6. Turn order and time

**There is no strip, because there is no interleaving to strip.** The game runs whole-side turns:
the player moves every agent it chooses to, in any order, spending each agent's own AP pool, for as
long as it wants, then ends the turn; the corporation then moves every active guard once, in an
order the game does not expose to the player, and hands control back. *(verified —
[pentadact](https://www.pentadact.com/2014-12-29-what-works-and-why-invisible-inc/), corroborated
generally by every other source read)* There is consequently no *whose go is it* question within a
side's turn at all — the player's own agents are not in any order relative to each other, contrary
to an interleaving strip, and are not shown as being in one.

**What the player sees during the corporate turn** is not documented in any source this pass read
in enough detail to describe precisely — whether the camera follows guards as they act, whether
there is a banner naming the phase, or whether it is silent until something the player would
notice happens. This is a genuine gap rather than a considered absence; see the gap list.

**What a picture would settle.** A clip spanning one full corporate turn end to end, to see what,
if anything, marks the hand-off and what the camera does while the player has no input.

### 7. Reactions

**The player holds nothing analogous to overwatch.** There is no declared stance, arc or ability
that a player's agent banks for the corporation's turn; every player action is spent immediately on
the player's own turn. The genre's *reaction* question, as `conventions.md` frames it, has no
player-side answer here at all.

**The enemy's overwatch is the only held-and-triggered behaviour in the game**, and it is described
fully under heading 5 above rather than repeated here: a guard declares it by seeing a visible,
non-incapacitated hostile, the trigger is drawn as the guard turning to face and shouting, and it
fires either on a later action of the target's that keeps it visible or automatically at the start
of the next corporate turn if the target is still in view. *(verified —
[guard_behaviour](https://iiwiki.werp.site/guard_behaviour))* Nothing found describes the moment of
firing itself — whether there is a camera cut, a distinct sound, or any warning between the guard
turning and the shot landing. See the gap list.

**What a picture would settle.** A clip of a guard entering overwatch through to firing on a target,
to see whether the moment of the shot is marked any differently from an ordinary guard action.

### 8. Camera and input

- **Rotation is stepped, on `Q`/`E`, in 90-degree turns, and there is no free rotation** — a
  Steam Community discussion confirms players asking for free rotation are told the game does not
  offer it. *(verified — [Steam Community
  Discussions](https://steamcommunity.com/app/243970/discussions/0/620712999975654334/), found by
  search and not independently re-fetched — see the gap list caveat on this source)*
- **Rotation is cosmetic rather than informative**, because only the walls are modelled with any
  depth; agents and props are flat sprites that do not change silhouette with the turn, which
  another discussion describes plainly as "really just a trick of the eye." *(verified — same
  caveat)*
- **`Alt` (held) reveals the full map layout** regardless of current fog of war, for route planning
  around objects and doors the current view might be hiding. *(verified — same caveat)*
- **The tutorial locks rotation off**; it unlocks only once the tutorial ends. *(verified — same
  caveat)* This is a small, concrete instance of teaching a reduced interface first, worth a note
  toward the onboarding brief's own questions even though this pass is explicitly not that brief.
- **No storey or level control was found described anywhere in this pass**, and it may simply not
  exist: nothing read confirms whether a single mission's map can span more than one floor. Flagged
  as a gap rather than asserted either way.
- **No cycle-target key**, consistent with heading 3: there is no targeting mode to cycle within.

**What a picture would settle.** Nothing here needs a still; it needs the manual or options screen,
which no source quoted gives in full — see the gap list for the keybind reference this heading is
really missing.

### 9. Confirmation and refusal

- **A move commits on one click, with no confirmation and no undo**, as established under heading
  2. This is the genre's convention taken at its strictest: not even the shot gets a second click
  here, because there is no separate shot-targeting mode to hang one on.
- **The game will not let a player attempt an attack it knows cannot connect** — an
  under-pierced weapon against armour is refused at the point of trying to select the target,
  rather than offered and then failing. *(verified — [Steam guide, "Items, Augments and
  Enemies"](https://steamcommunity.com/sharedfiles/filedetails/?id=470340865))* This is the
  strongest instance in the file of the template's own ninth question — *what does the game simply
  not let a player do* — and it is a refusal with no dialogue at all, just an action that never
  becomes available.
- **Disabled abilities are shown greyed out rather than hidden**, so a refusal is legible before
  the player tries it — see heading 2.
- **One warning the game does draw**: the watched/noticed/hidden shading under heading 4 is itself
  a warning drawn on the tile before commitment, in the same family `conventions.md` recommends for
  this project's own concealment ring.
- **One naming failure, reported directly by a source otherwise praising the game's interface**:
  "Abort Mission" ends the entire campaign rather than merely the current mission, and nothing in
  the label or its placement distinguishes it from a lower-stakes cancel. *(verified —
  [pentadact](https://www.pentadact.com/2014-12-29-what-works-and-why-invisible-inc/))* Worth
  keeping precisely because it is the one piece of evidence in this file about the genre's *bad*
  interface habits rather than its good ones — a confirmation the genre would have caught, on an
  action severe enough that skipping one is a real cost.

**What a picture would settle.** A frame of the Abort Mission control itself, in its menu context,
to see whether anything on screen at the point of the click hints at the stakes that the label
alone does not.

### 10. What the game hides, and what its players added

- **The community's own UI Tweaks mod is a direct list of gaps its author judged worth closing**:
  AP shown to the nearest half-point rather than rounded, so a diagonal move's true cost is
  checkable before committing; unique path colours per tracked or observed guard, specifically to
  disambiguate crossing patrol routes the base game draws in one colour; inventory reordering by
  drag-and-drop; item-level numbers stamped on stacked-item icons; and doors made operable mid
  body-drag. *(verified — [UI Tweaks (Mod),
  Fandom](https://invisibleinc.fandom.com/wiki/UI_Tweaks_(Mod)) and [source](https://github.com/osheroff/ui_tweaks))*
  Every one of these is a precision or disambiguation fix rather than a new capability — the mod's
  own description is explicit that it does not touch balance — which is itself a finding: the
  shipped HUD's gaps that players bothered to patch were legibility gaps, not missing features.
- **The interface critique cited throughout this file was written by a working designer specifically
  to find what the shipped HUD does not do well**, and three of its four substantive complaints —
  cone-shading ambiguity, the AP readout's distance from the cursor, and the augment-slot fill
  direction — are about exactly the kind of precision problem the community mod also targeted from
  a different angle. Two independent critics converging on legibility rather than missing systems
  is worth more than either alone. *(inferred, from the UI Tweaks list above and [Any Key To
  Start](https://anykeytostart.wordpress.com/2015/05/27/invisible-inc/))*
- **The alternate "reduced walls" display mode**, mentioned under heading 4, is the developer's own
  admission of the same class of problem, shipped rather than patched in.

**What a picture would settle.** Nothing further — this heading is built from written sources
describing a fix and the problem it answers, which is exactly the form the heading asks for, and a
screenshot of a mod adds nothing a description of its changelog does not already give.

---

## What transfers

- **Heading 3's absence bears on `briefs.md`'s target-readout brief directly**: a hit-chance
  breakdown is a convention for games where combat is the content, and this game's closest stealth
  relative not having one at all is evidence for how little of that convention should survive into
  a game where combat is the thing being avoided, not won.
- **Heading 5's ghost marker is a narrower mechanic than `conventions.md`'s own recommendation**
  for the *enemy* section — a same-turn-only fade with no belief carried forward — and the gap
  between the two is worth the synthesis pass weighing explicitly rather than assuming Invisible,
  Inc. already does what is being proposed.
- **Heading 5's investigating/alerted pair is the clearest shipped precedent for the *noticed*
  state `conventions.md` already borrows**, and the one-way escalation (investigating resolves
  either way; alerted never resolves) is a detail the conventions doc does not currently carry and
  the synthesis pass may want to.
- **Heading 9's armour-piercing refusal is a second shipped instance of *silent refusal at the
  point of attempt*, alongside the `conventions.md` recommendation for the concealment ring — both
  are refusals drawn on the world rather than in a dialogue, which is the pattern worth generalising
  rather than treating as two separate borrowings.
- **Heading 7's finding that this game has no player-side reaction at all is a genuine data point
  for the Reactions section of `conventions.md`**, which currently draws its convention entirely
  from the alternating-side genre (overwatch as a stance) and the interrupt line (Jagged Alliance,
  Silent Storm); the closest turn-based stealth relative offering *neither* is worth knowing before
  calling either the convention.

## The gap list

1. **Heading 6 — what the corporate turn shows on screen.** No source read describes camera
   behaviour, phase framing, or pacing during the enemy's turn in Invisible, Inc. with any
   precision. *Picture:* a clip spanning one full corporate turn end to end. *Changes:* whether
   this project's own "one indicator per contiguous stretch of hostile activity" (entry 065) has
   any shipped precedent to check against, or is genuinely unprecedented in the genre as
   `conventions.md` already suspects for the strip question generally.
2. **Heading 7 — the moment overwatch fires.** Every source describes the trigger and the
   consequence; none describes the presentation of the shot itself — camera cut, sound, delay.
   *Picture:* a clip from a guard entering overwatch through to firing. *Changes:* whether this
   project's own reaction window (entry 049) has anything to borrow for the moment of resolution,
   as opposed to only for the declaration.
3. **Heading 8 — storeys.** Not established either way whether a mission map can span more than
   one floor, or what a level-change control would look like if so. *Picture or source:* the
   official manual's control reference, or a clip of a mission with a visible floor change.
   *Changes:* whether this heading is legitimately empty (no such thing exists) or only
   under-researched, which changes how much weight `conventions.md`'s synthesis pass can put on
   its silence.
4. **Heading 4 — whether cover matters once an attack is actually attempted.** The vision bands
   clearly gate detection; whether the same cover also reduces or blocks damage in the rare case
   combat happens was not settled. *Picture or clip:* an attack attempted against a target in
   cover versus in the open, if the numbers differ. *Changes:* whether heading 3's "no readout"
   finding needs a footnote for a hidden cover effect the UI still doesn't surface, which would be
   a sharper version of the same finding rather than a contradiction of it.
5. **Heading 1 — PWR's on-screen position**, asserted from general knowledge and not from a
   source that shows it in place. *Picture:* the full-frame capture already wanted for heading 1
   would settle this at no extra cost.
6. **The Steam Community Discussions cited for heading 8 (camera rotation, `Alt` reveal, tutorial
   lock) came back as search-engine summaries of forum threads rather than pages this pass fetched
   and read directly.** They are plausible and specific enough to keep, but they carry a weaker
   chain of custody than every other **verified** tag in this file, which cites a source this pass
   opened itself. *Resolution:* re-fetch the three threads directly, or replace the claims with
   ones drawn from the official manual. *Changes:* nothing about the claims' content, only their
   confidence — worth flagging precisely because the tag key does not otherwise distinguish
   "verified by reading" from "verified by trusting a summary of reading."
7. **Heading 2 — how far back cancel goes.** Confirmed that a context-button prompt can be backed
   out of before being taken; not confirmed whether *any* action, once its prompt is committed,
   can be cancelled by a further keystroke, or whether commitment is uniformly immediate and final
   across every ability the way it is for movement. *Picture or clip:* a cancelled non-move action
   mid-prompt, and a failed attempt to cancel one already taken. *Changes:* whether heading 2's
   "cancel exists at the level of a declared action" line generalises past the one case it was
   checked against.
