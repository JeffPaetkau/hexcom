# Phantom Brigade — reference file (pass one, documentary)

Brace Yourself Games' mech tactics game, in Early Access from 2022 and past 1.0 by the time of
its free "2.0" content update (2026). This file is written from published material only — no
screenshots exist yet — per the pass described in
[../../subprojects/interface.md](../../subprojects/interface.md).

**What this game is the authority on.** The only shipped game in the set that plans a shared
slice of *time* rather than a shared *turn count* — five seconds, scrubbable, both sides' actions
laid on one timeline before either resolves. It is the nearest thing in the genre to Phantom
Brigade's own name for the pattern: **"We-Go."** It is only an instance, and a distant one, of
everything this project's stealth is about: once an engagement starts, both sides are fully
visible to each other with exact statistics, so it has no contact file, no alarm ladder, and
(within a single engagement) no fog of war at all. Read it for the timeline and the ghost-preview,
not for anything about hiding.

## Tag key

| | |
|---|---|
| **verified** | a published source, linked at the point of use. |
| **remembered** | model knowledge, unchecked against a primary source. Every one is a gap-list candidate. |
| **inferred** | derived from another claim in this file, which it names. |

| **observed** | read off a named shot in `shots/phantom-brigade/`, captured from the user's own copy in pass two. |

Pass one had no **observed** tags, by design. Pass two captured C9 (a still and a clip) and C11 (a
still). Neither shows what it was asked for in full, and the file says so where each lands.

## Sources

- [Console Creatures review](https://www.consolecreatures.com/review-phantom-brigade/) — turn
  length, the video-editor framing of the timeline.
- [Kotaku, "Phantom Brigade, A New Turn-Based Tactics Game, Rules"](https://kotaku.com/phantom-brigade-a-new-turn-based-tactics-game-rules-1845710612)
  — early hands-on, the prediction pitch.
- [Steam Community Guide — Comprehensive FAQ & Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2942917777)
  — the most detailed single source used here: timeline mechanics, the optimal-range ring, heat
  display, camera-centre button, order editing before commit.
- [Steam discussion — "Interface lacking of visualising information"](https://steamcommunity.com/app/553540/discussions/0/3765608282428596436/)
  — a moderator's own account of what the HUD shows and where it fails to be seen: heat bars,
  optimal-range halos, dashed incoming-fire lines.
- [Steam discussion — "Where is the enemy health bar and other questions"](https://steamcommunity.com/app/553540/discussions/0/684112727828914062/)
  — the health-bar stack (core/torso vs pilot) and the damage-prediction line's exact format.
- [Steam discussion — "aiming and pray"](https://steamcommunity.com/app/553540/discussions/0/3787002282777197600/)
  — the accuracy/damage-effectiveness split behind the targeting widget's single number, and the
  Ctrl-held breakdown.
- [Steam discussion — "Multiple predictions for higher difficulty units"](https://steamcommunity.com/app/553540/discussions/0/3782499316885125180/)
  — the prediction system's scope and its limits.
- [Steam discussion — "No ability to stop and then move again?"](https://steamcommunity.com/app/553540/discussions/0/3777994452125744142/)
  — a developer (Addie) on rough edges in movement planning, ahead of 1.0.
- [Steam discussion — "How does cover work?"](https://steamcommunity.com/app/553540/discussions/0/3787002719314053366/)
  and the destructibility threads linked from it — cover as geometry, not a tile state.
- [Adelaide Jenkins, "Simultaneous Turn Combat System"](https://www.adelaidejenkins.com/simultaneous-turn-combat-system)
  — a design postmortem on the timeline's origin in video-editor UI, the two-track layout, and the
  draggable path-ghost.
- [Brace Yourself Games — Phantom Brigade "2.0" free content update](https://braceyourselfgames.com/2026/06/25/phantom-brigade-free-content-update/)
  — controller support, camera customisation (presets, FOV, orbit), font-size and dialog-duration
  fixes shipped on community request.
- [Steam discussion — reinforcement patrols](https://steamcommunity.com/app/553540/discussions/0/3782499316871043836/)
  and the overworld stealth/detection material reached from it — detection radius and jamming
  belong to the strategic layer, not to a running engagement.

## Nothing found

**Heading 6 (turn order)** has no strip and no initiative to draw, and that is the finding, not a
hole: the game has no turns to order, only a five-second window both sides fill and then resolve
together. **Heading 7 (reactions)** is likewise near-empty by design — nothing in the resolve
phase hands control back mid-execution — and what little content the heading has is about what
*doesn't* exist rather than what does.

---

## 1. Screen furniture

- Each unit's health is not one number but a small stack: a white bar for the core/torso, which is
  the kill condition, and a red bar above it for pilot health, which concusses and disables the
  unit if depleted first — a moderator's own count put it at "about 5 different health bars" per
  enemy once armour and subsystem readouts are included, which the thread's original poster had
  not been able to parse unaided. **verified**, [health bar
  thread](https://steamcommunity.com/app/553540/discussions/0/684112727828914062/).
- A heat bar tracks each unit's current heat at whatever moment the timeline scrubber is parked
  on; the timeline's own background shifts lighter as a unit's projected heat rises, so the
  warning is temporal (painted at the point on the scrubber where it will happen) rather than a
  static readout of the present. **verified**, [FAQ
  guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2942917777); [interface
  thread](https://steamcommunity.com/app/553540/discussions/0/3765608282428596436/).
- An icon reading roughly "!0" marks a unit that has been assigned no actions for the coming five
  seconds, and attempting to execute a plan with one or more idle units produces a further
  warning before it is allowed to proceed. **remembered**.
- Objective-relevant units carry a highlight in both the timeline UI and in-world, described as a
  yellow targeting bracket. **remembered**.
- No minimap surfaced in any source read for this file, and one Steam thread title ("Is there a
  way to show Building info?") suggests at least one player went looking for map-level readouts
  that were not there. **remembered**, weak.

**What a picture would settle.** A full battle screenshot with the HUD intact, so the persistent
elements can be enumerated exhaustively rather than assembled from fragments of separate threads —
this heading is built from four different discussions each describing one corner of the same
screen, and none shows the whole of it.

## 2. The soldier

- There is no fixed action bar. Bindable actions run to roughly six slots (Wait, Run, Dash,
  Primary, Pilot Skill, and further slots keyed 1–6), and which action a given key produces is
  read off the mech's current loadout — so the same key means a different thing on two different
  mechs, and means a different thing again on the same mech after it loses a part. **verified**,
  from a shortcut-keys discussion surfaced in search but not independently fetched — treat as
  **remembered** pending a primary read.
- Orders are not committed the instant they are placed. An order already on the timeline can be
  dragged to a new time, and a double right-click deletes it outright — both before the plan is
  executed. **verified**, [FAQ guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2942917777).
- A developer describes movement's placement as one of the roughest edges in the interface ahead
  of 1.0 — clunky compared to firing, and the subject of an explicit "always listening" response —
  which is a finding about the game's own priorities more than about its shipped state.
  **verified**, [developer reply](https://steamcommunity.com/app/553540/discussions/0/3777994452125744142/).
- No source read for this file describes a hover tooltip over an ability showing its terms before
  it is placed, distinct from the targeting widget in section 3. Possibly folded into the same
  interaction; possibly absent. **remembered**, weak, and a genuine gap.

**What a picture would settle.** A single soldier selected, mid-plan, with the action-key row
visible and at least one order already sitting on the timeline — which would show whether the
"keys change meaning per loadout" claim above is a redraw of the row's labels or a fixed row the
player has to remember against.

## 3. The target

- The number shown on the targeting widget while planning a shot is **not** a hit chance. Machines
  and pilots are stated to be perfectly accurate; the only things that can make a shot miss are
  the weapon's scatter value and the target's position at the moment the projectile arrives, which
  a physics simulation resolves rather than a die roll. What the widget's single percentage
  actually shows is **damage effectiveness** — how much of a hit's damage would land given range,
  scatter and the target's exposed cross-section — folding accuracy and damage together for
  planning speed. **verified**, [aiming and pray
  thread](https://steamcommunity.com/app/553540/discussions/0/3787002282777197600/).
- **This is misread by the game's own players as a hit chance, repeatedly and confidently**, to
  the point of open forum arguments about "realistic ballistics" versus "arbitrary restrictions"
  that dissolve the moment somebody points out the number was never chance-to-hit at all. One
  player's complaint — "100% hit chance, my shotgun literally up against their mech... 65% hit" —
  is not a bug report, it is the conflation in a single sentence. **verified**, same thread.
- Holding Ctrl on the targeting widget splits the folded number back into its two components —
  the more accurate breakdown of accuracy versus damage the headline number was built from.
  **verified**, same thread.
- A damage-prediction line accompanies the shot, in the form `damage-about-to-deal /
  target's-current-combined-integrity`, and is trusted only loosely by experienced players — one
  recommends firing twice on a target that "should" die from the predicted number, because the
  prediction and physics outcome can diverge. **verified**, [health bar
  thread](https://steamcommunity.com/app/553540/discussions/0/684112727828914062/).
- No called-shot mode exists. Which part of an enemy takes damage falls out of firing angle and
  approach rather than a target selector: shooting the back tends to hit legs and can crash the
  unit, a flank tends to hit an arm, and a shot at a mech actively firing a weapon tends to catch
  the arm operating it. Players describe working this by manoeuvre — circling to a weak side,
  firing from above or below — as "a bit of an art" rather than a designed interaction.
  **remembered**, from search synthesis rather than a single fetched primary source; a genuine gap.
- Targets are switched with Ctrl+click rather than a cycle key. **remembered**.

**Pass two, and it did not catch the split.** *(observed.)*

- **Without Ctrl, the target already carries more than one number.** Taken with Ctrl not held (the
  capturer could not hold it and screenshot at once), the targeted unit shows a large **`100%`**
  headline under its reticle. To its left is `Optimal` in green over `2X Crit - 15%`. To its right
  is `Predicted damage` over `Unit damage ×1.5 2927/11358`, which is the damage-prediction line
  above in its shipped form. Under it is the unit's badge (`⊥10`, three bars, two weapon glyphs).
  [`shot-c9-headline-and-damage-prediction-without-ctrl.png`](shots/phantom-brigade/shot-c9-headline-and-damage-prediction-without-ctrl.png)
- **The key is labelled `Show details`**, bound to `Left Ctrl`, in the controls legend at the
  bottom right. [`shot-c9-show-details-bound-to-left-ctrl.png`](shots/phantom-brigade/shot-c9-show-details-bound-to-left-ctrl.png)
- **In the clip the capturer toggled Ctrl.** The only change in its frames that fits a toggle is at
  about 9.8 s. Every unit on the map, blue and red, gains its badge at once, where before only the
  targeted unit had one
  ([`shot-c9-ctrl-toggle-reveals-every-unit-badge.jpg`](shots/phantom-brigade/shot-c9-ctrl-toggle-reveals-every-unit-badge.jpg),
  before and after). That is *show me everything for a moment*, the job the held `Alt` does in
  Shadow Tactics. The headline splitting into accuracy and damage effectiveness **is not in any
  frame**, and neither is a scatter cone. The clip's picture stops at about 10.6 s of its 17.4, so
  whatever followed was not recorded.
- **Also in the clip**: while choosing a target, the cursor carries a distance in metres (`25 m`),
  and the weapon card on the right gives `Optimal range 4 – 37 m` and `Beam width 4 m` as numbers.

The claim that holding Ctrl splits the folded number stays **verified**, neither observed nor
contradicted. What pass two adds is that the headline is not alone at the target without Ctrl,
and that the one Ctrl effect on film is a map-wide reveal.

**What a picture would settle.** The Ctrl-held breakdown screen, in full, with a labelled
scatter cone and the two split numbers both visible — this file has the claim that the headline
number is damage-effectiveness rather than hit chance from a good source, but not a look at the
breakdown that is supposed to make that legible, and the fact that players still misread the
headline number suggests the breakdown either isn't reached often or doesn't fix the conflation
once seen.

## 4. The tile

- Movement and firing live on two separate timeline tracks rather than one — described by the
  system's own designer as "a track for movement and spatial actions, and a track for secondary
  actions that depended on position, such as firing" — so a tile's cost is not a single number the
  way a hex's is here; it is a placement on a track with a start time and a duration.
  **verified**, [Adelaide Jenkins,
  postmortem](https://www.adelaidejenkins.com/simultaneous-turn-combat-system).
- A **path-ghost** can be dragged along the planned movement path to preview the unit's position
  at any point in the turn — named by the same postmortem as "critical for target decision
  making," because where you will be when you fire is exactly what a target's effective range
  depends on. **verified**, same source.
- Holding Ctrl over a placed shot draws a grey ring for the weapon's "optimal" range: lighter grey
  shows full damage potential, a darker outer band shows scatter-wasted potential, and a separate
  bar graph shows damage falloff by distance. This is the tile-and-target version of the split
  described in section 3, drawn in world space rather than as a widget. **verified**, [FAQ
  guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2942917777).
- Incoming fire is shown as a dashed line to its target, and a moderator's own troubleshooting
  post treats this as an existing but under-noticed feature rather than a missing one — the
  reporting player had not seen it despite it being on screen. **verified**, [interface
  thread](https://steamcommunity.com/app/553540/discussions/0/3765608282428596436/).
- **Cover has no tile icon.** Hills and rock are stated to be indestructible cover, buildings are
  destructible cover, trees are cosmetic only, and certain weapons (railguns) ignore cover
  entirely — but whether a tile currently offers cover is read from the 3D geometry and the
  projectile's actual path, not from a badge on the tile. A closer piece of cover can block more
  than a farther one even though closing the distance exposes a unit to more and more accurate
  fire, which several threads treat as counter-intuitive on first encounter. **verified**, [cover
  thread and links from it](https://steamcommunity.com/app/553540/discussions/0/3787002719314053366/).
- Terrain and structures are broadly destructible — "every square meter... can be eroded or
  obliterated" — so a tile's cover value is not even fixed for the engagement; a wall a shot
  reasoned about a moment ago may not be there when it fires. **remembered**, from search
  synthesis; corroborated by multiple independent threads on building destructibility but not
  independently fetched.

**Pass two did not settle this.** *(observed — C11.)* The frame is the `SET DESTINATION` mode for a
unit: a hex badge over the planned destination reads `-6%` and `-2%` beside two unlabelled glyphs,
over the unit's own badge (`⊥6`, bars, weapon glyphs). **Incoming fire is drawn as red striped
wedges on the ground from each enemy toward its target.** A large faint ring surrounds the area, and
nothing in the frame labels it. Neither the optimal-range ring as described above nor a falloff bar
graph is in it.
[`shot-c11-set-destination-readout-and-enemy-fire-cones.jpg`](shots/phantom-brigade/shot-c11-set-destination-readout-and-enemy-fire-cones.jpg),
[`shot-c11-destination-badge-percentages.png`](shots/phantom-brigade/shot-c11-destination-badge-percentages.png)

**What a picture would settle.** The optimal-range ring and the falloff bar graph, both on screen
at once against a partially-destroyed piece of cover — this file has each piece from a different
source and has not seen them composed, and composition is exactly where a spatial readout either
holds together or turns into clutter.

## 5. The enemy

- **There is no contact file and no fog of war within a running engagement.** Once a battle
  starts, "Combat Clairvoyance" shows both sides' next five seconds in full — positions, planned
  fire, planned movement — which is the opposite pole from this project's rules: total certainty
  about what is about to happen, in exchange for a five-second horizon and near-total inability to
  undo a plan once it starts resolving. **verified**, multiple sources including [Kotaku's
  hands-on](https://kotaku.com/phantom-brigade-a-new-turn-based-tactics-game-rules-1845710612).
- The prediction is not advertised as infallible: one thread on higher difficulties reports
  enemies that can react to the player's own plan within the same window, meaning the five-second
  preview is a forecast of the enemy's *current* intent rather than a locked script. **verified**,
  [prediction-limits thread](https://steamcommunity.com/app/553540/discussions/0/3782499316885125180/).
- Detection radii, jamming, and "approach before being seen" belong to the **overworld** layer —
  closing on a hostile site or convoy before combat begins — not to anything inside a fight.
  Attacking a patrol from the front is recommended because it spends less time inside the patrol's
  detection bubble before the engagement starts, which is a pre-battle stealth mechanic distinct
  from anything drawn once mechs are exchanging fire. **remembered**, from search synthesis across
  several overworld-focused threads; treat as a claim about the strategic layer only.
  **inferred**, from the same material: reinforcement patrols already engaged nearby can join a
  running fight as a wave, which is the one way an unaccounted-for hostile can still appear mid-
  engagement even though nothing inside combat itself is hidden.
- No source read for this file shows how (or whether) an arriving reinforcement wave is
  telegraphed before it appears on the map — whether it is announced ahead of the five-second
  window it joins, or simply present at the next window with no warning. **remembered**, weak,
  and a genuine gap.

**What a picture would settle.** A frame from the moment a reinforcement wave enters an ongoing
fight — whether anything on screen marks the arrival as imminent before it happens, or whether the
next five-second preview simply includes new units with no transition drawn. This is the one
seam in an otherwise fully-visible combat model, and nothing read here says what it looks like.

## 6. Turn order and time

**This heading is empty by design, and the emptiness is the finding.** Phantom Brigade is
"We-Go": both sides plan a five-second window at the same time, then both plans resolve
together, continuously, with no interleaving and therefore nothing to put a strip in order of.
**verified**, [Adelaide Jenkins postmortem](https://www.adelaidejenkins.com/simultaneous-turn-combat-system)
and corroborated across the review and hands-on sources above.

- The round boundary that does exist is the edge between the planning phase and the resolve
  ("activation") phase — a cut the player controls by pressing execute, not a clock running down.
- The two-track timeline (movement above, secondary actions such as firing below) is itself the
  closest thing to a turn-order readout the game has, and it is a **planning** instrument, not a
  status display: once execution starts the timeline is what is being played back, not what is
  still being decided.
- Colour is reportedly used to separate whose plan is whose on the timeline — blue for friendly
  paths, red for enemy — which is the one piece of "whose go" information the game needs to
  convey, and it conveys it by colour-coding a shared object rather than by two separate turns.
  **remembered**, from the FAQ guide's description; not independently corroborated by a second
  source.

**What a picture would settle.** A frame of the activation phase itself, mid-resolve, to see
whether anything distinguishes "this bullet is mine" from "this bullet is theirs" once playback
has started and the timeline is no longer being edited — the blue/red split above is described
for the planning view, and this file found nothing about the resolve view's own colour language.

## 7. Reactions

**Also close to empty, and for a related reason: nothing hands control back mid-resolve.** Once
execution begins, "mechs and enemies act according to their queued commands without pauses for
reactive adjustment" — there is no overwatch-style held action, no interrupt, and no window that
opens for the player once the five seconds start running. **verified**, synthesis across the
We-Go sources above; the specific "without pauses" framing is search-synthesized rather than a
single fetched quote and should be treated as **remembered** pending a primary check.

- What substitutes for a reaction is entirely pre-planned: a defensive stance (a "shield" raise)
  or a dash placed on the timeline *before* execution, timed against the enemy's five-second
  forecast so that it is already active when the enemy's shot or melee attack would otherwise
  land. This is the payoff of total foresight — a player reacts to what they were shown, before
  the fact, rather than to what happens, during it. **remembered**.
- Friendly fire is not blocked or confirmed against; the closest thing to a warning is that an
  incoming or outgoing fire line, drawn through a mech that would be caught in it, is visible on
  the timeline the same way any other shot line is. At least one thread argues this is not enough
  and asks for an explicit warning, which the base game does not have as of the sources read here.
  **verified**, [friendly-fire discussion surfaced in
  search](https://steamcommunity.com/app/553540/discussions/0/3782499316871982333) — not
  independently fetched; treat the request-for-a-warning claim as **remembered**.

**What a picture would settle.** Whether "no pause for reactive adjustment" is completely true —
a clip of the activation phase from start to end, to confirm no control (not even a global pause)
is exposed to the player once execution has begun, since every source read here describes the
intent rather than the absence directly.

## 8. Camera and input

**The thinnest heading in this file, and it should not be padded to look otherwise.** Almost
everything found here is about a camera in the mech customisation/hangar screen, not the tactical
battle camera, and the two may not share controls.

- The 2.0 update's patch material advertises a "fully customisable" camera with variable field of
  view, damping, offsets and an orbit mode, plus presets including an over-the-shoulder view and a
  weapon-mounted view — but this is described in the context of cinematic replay/screenshot
  tooling, and it is not clear from the source whether any of it is live during battle planning.
  **verified**, [2.0 update
  post](https://braceyourselfgames.com/2026/06/25/phantom-brigade-free-content-update/).
- Controller support was added as part of the same update, alongside an inverted-zoom toggle under
  a Controller options tab — implying the tactical camera does have a zoom axis exposed to
  rebinding, which is the one concrete fact this file has about the in-battle camera specifically.
  **remembered**, from search synthesis; the primary patch notes were not independently fetched.
- No source read for this file states the tactical camera's rotation gesture (drag button, step
  key, or both), its pitch range, or whether it is free or snapped to any grid. This is a genuine
  and total gap, not a thin finding.
- Keyboard and mouse bindings are fully remappable via an in-game options tab, per multiple
  secondary guide sites, none of which were fetchable directly (403s from this file's session) to
  confirm the exact default bindings for the tactical camera. **remembered**, weak.

**What a picture would settle.** A short clip of a player rotating and zooming the camera during
the planning phase of a battle (not the hangar), with the keys or mouse gesture visible or
narrated — this heading currently cannot say whether Phantom Brigade's battle camera resembles
anything else in this reference set at all.

## 9. Confirmation and refusal

- Executing a plan that leaves one or more units with no orders for the coming five seconds is
  flagged — the idle-unit icon from section 1 — and a further warning appears if the player tries
  to execute anyway, though nothing read here says the warning is a hard block versus a
  dismissable prompt. **remembered**.
- Individual queued orders (Wait, Run, and by extension others placed on the timeline) can be
  edited or deleted freely up until the plan is executed — dragged to retime, or removed with a
  double right-click. This is real, sourced editing capability, not merely an absence of
  commitment. **verified**, [FAQ guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2942917777).
- **There is no undo once a plan has resolved.** The clearest statement of this found in search is
  a developer explanation citing the volume of dynamic state a turn touches — "thousands of
  dynamic objects, dozens of animated characters" — as the reason a full undo is not planned given
  the team's size. This claim could not be traced to a single fetchable primary page in this
  session (the likely source, the official FAQ, returned a 403), so it is downgraded to
  **remembered** here despite reading as a direct quote, and is a priority item for the gap list.
- Overheat is a graded consequence rather than a hard refusal: a unit can be pushed into
  overheating and will shut down for a period (with a further restart delay of about four
  seconds) rather than the game preventing the order that caused it. Deliberately overheating to
  force a dash or dodge is described by players as a known, sanctioned trade-off, not an exploit.
  **verified**, [overheat
  thread](https://steamcommunity.com/app/553540/discussions/0/684112727828865219/).

**What a picture would settle.** The execute-confirmation prompt itself, idle units included —
this file infers its existence and rough trigger from a search-level description, not from a
primary source, and cannot currently say whether it is a modal dialogue, an inline icon flash, or
something else.

## 10. What the game hides, and what its players added

- The single most persistent player request found across multiple threads, spanning the game's
  Early Access life and still unresolved as of the sources read here, is an explicit called-shot
  or part-targeting mode — players have built an informal practice of aiming by angle and position
  instead (section 3), and more than one thread frames this as a wish rather than a discovered
  technique. **remembered**, from search synthesis across several distinct threads.
- The 2.0 free update shipped several fixes explicitly framed as answers to community feedback:
  larger fonts across multiple screens, and a longer on-screen duration for combat dialogue —
  both readability fixes rather than new mechanics, which is itself a finding about where the
  interface's rough edges were being felt. **verified**, [2.0 update
  post](https://braceyourselfgames.com/2026/06/25/phantom-brigade-free-content-update/).
- A minus-key HUD-hide existed in earlier builds for clean screenshots and was reportedly not
  carried forward without comment, per one Steam thread asking where it went — a small but
  concrete case of a capture-friendly feature regressing. **remembered**, single thread, not
  independently corroborated.
- 76 mods were listed on Nexus Mods for the game as of this file's research (page itself not
  independently fetchable — 403), which was not explored further for content; whether any of them
  touch the HUD specifically is unknown from the sources read here. **remembered**, weak, and a
  gap.
- One long-running thread argues the damage-effectiveness number (section 3) should either be
  relabelled or accompanied by an explicit hit-chance figure, precisely because players keep
  reading it as one; this is a community diagnosis of the same conflation this file found
  independently in the same thread. **verified**, [aiming and pray
  thread](https://steamcommunity.com/app/553540/discussions/0/3787002282777197600/).

**What a picture would settle.** Nothing here needs a picture particularly — this heading is
about what published discussion already says was missing or added, and the more useful next step
for it is simply reading the top few Nexus mods directly rather than through a blocked listing
page, which is a research task rather than a photography one.

---

## What transfers

- **The damage-effectiveness number that plays a hit-chance number in public** bears on brief One
  (`view/readouts-in-place`) and the Readouts section of `conventions.md`: this game's own
  `GunneryModel` computes a real probability, and the risk this file surfaces is a naming and
  framing one — a folded, single headline number invites exactly the misreading Phantom Brigade's
  players demonstrate, independent of whether the underlying number is honest.
- **The draggable path-ghost, sliding a preview along a committed route to show position at any
  point in a time window,** is close kin to what the reaction window already draws — the mover's
  committed route with the tick each step lands on, described under entry 049 and Reactions in
  `conventions.md`. Phantom Brigade generalises the same idea (a scrubbable preview of a plan
  already laid down) to the entire turn rather than to a single interrupted move.
- **Total transparency once an engagement starts, purchased with a short horizon and near-zero
  ability to undo a resolving plan,** is the far pole from Invisible, Inc.'s coarse rungs in the
  What of the enemy is drawn section of `conventions.md`. It is not a source of borrowings — this
  project's fog is the point — but it is a useful boundary case for the synthesis pass to cite
  when it says which of the ten headings the reference set was unanimous on: this file is the one
  entry that has nothing to contribute to that heading's convention, on purpose.
- **Cover as pure geometry, with no tile badge**, contrasts directly with the shield-icon
  convention `conventions.md`'s Readouts section takes as the genre standard. Whether that is a
  point in Phantom Brigade's favour or against it is for the synthesis to weigh; this file only
  notes that a shipped, well-reviewed tactics game gets by without one.
- **No confirmed keybinding or gesture for the tactical camera** means this file cannot support or
  contradict anything in the Camera section of `conventions.md` or its entry-058 resolution — it
  is a blank rather than a data point, and should be read as such rather than silently dropped.

## The gap list

1. **Heading 8, the tactical battle camera's rotation and zoom gesture.** A short clip of a player
   rotating and zooming during the planning phase of an actual battle, not the hangar/customisation
   screen, with the input visible or narrated. This is the largest gap in the file — the Camera
   section of `conventions.md` cannot cite this game for anything until it exists, and right now
   the file cannot even say whether the battle camera is free, stepped, or fixed.
2. **Heading 9, the exact wording and source of the "no full undo" claim.** The developer
   explanation this file quotes could not be traced to a fetchable primary page in this session.
   A screenshot or archived copy of the official FAQ page (braceyourselfgames.com/phantom-
   brigade/faq/, which returned 403 here) would let this move from remembered to verified, or
   correct it if the memory is wrong.
3. **Heading 3, the Ctrl-held accuracy/damage breakdown, in full.** A screenshot of the targeting
   widget with Ctrl held, showing both split numbers and the scatter cone at once. This would
   settle whether the breakdown actually resolves the hit-chance/damage-effectiveness confusion
   this file documents, or whether it exists but players don't reach it either — which changes how
   much weight the "the number needs a name that can't be misread" finding above can bear.
   *Still open after C9.* The capture shows what sits at the target without Ctrl and a map-wide
   badge reveal with it, but not the split. See heading 3.
4. **Heading 1, a full HUD screenshot to enumerate screen furniture exhaustively.** This file
   assembled its list from four separate threads each describing a different fragment of the same
   screen. A single annotated shot of a battle in progress, panel by panel, would very likely add
   items this file does not know to ask about.
5. **Heading 5, whether a reinforcement wave is telegraphed before it joins a fight.** A clip
   spanning the moment reinforcements arrive: is there any warning in the preceding five-second
   window, or does the next window simply contain new units with no transition? This is the one
   possible crack in an otherwise fully-visible combat model and no source read here says which it
   is.
6. **Heading 4, the optimal-range ring and the damage-falloff graph composed together.** A frame
   showing both at once against a tile with cover, since this file has each from a different
   source and has not seen how they read together, which is exactly where a spatial readout either
   holds up or turns to clutter. *Still open after C11*, which caught the destination mode and the
   enemy fire wedges instead. See heading 4.
7. **Heading 6, whether the resolve phase distinguishes whose action is whose.** The blue/red path
   colouring described here is for the planning view; a frame from mid-playback would show whether
   that colour language survives into the phase the player is actually watching rather than
   editing.
8. **Heading 2, whether an ability has a hover state at all**, distinct from the targeting widget.
   No source read here describes one; a clip of a player hovering (not clicking) an action key
   would settle whether this is an absent convention or one this file simply failed to find
   evidence for.
9. **Heading 10, the top Nexus mods' actual content.** The mod listing page returned a 403 in this
   session. A direct read of the top ten or so mods — not a picture, a research task — would say
   whether any address the HUD, the camera, or the called-shot gap named above, which changes
   whether "players wanted a called-shot mode and didn't get one" or "players wanted it and built
   it themselves" is the true shape of that finding.
