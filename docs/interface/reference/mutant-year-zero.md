# Mutant Year Zero: Road to Eden

Job 6 of the reference set. See [../../subprojects/interface.md](../../subprojects/interface.md)
for the template this file follows and the rules for running it in parallel with the other nine.

**What this game is the authority on, and what it is only an instance of.** Press and players both
call it "DuX-Com" without much affection lost in the joke: the camera angle, the two-action-point
economy, the cover tiers and the overwatch reaction are XCOM's, borrowed openly. Where it earns its
place in this set is narrower and sharper than its silhouette suggests. It is the only shipped game
found that draws a detection ring **only in the mode that needs it** — reconnaissance, before a shot
is fired — and lets the player **shrink that ring with an action**, the flashlight, rather than a
mutation or a piece of gear. It also inherits, undisguised, a tabletop dice mechanic: hit chance
only ever reads 25%, 50%, 75% or 100%, because the source material rolled six-sided dice in fixed
steps and the digital game never smoothed the curve. Everything else here — the ability bar, the
cover math, the two-AP turn — is the genre's answer with the serial numbers still visible.

## Tag key

| | |
|---|---|
| **observed** | read off a named shot in `shots/`. Pass two only. |
| **verified** | a published source, with the link. |
| **remembered** | model knowledge, unchecked. Never load-bearing alone. |
| **inferred** | from something else in this file, which it names. |

No `observed` tags appear below — this is pass one. Where a claim rests on a search-engine
synthesis rather than a page this session actually opened, it is marked **remembered** and carries
a gap-list entry, even though a real thread sits behind the search result.

## Sources

- [How to Play Mutant Year Zero: Road to Eden](https://mutantyearzero.fandom.com/wiki/How_to_Play_Mutant_Year_Zero:_Road_to_Eden) — Fandom wiki
- [Mutation](https://mutantyearzero.fandom.com/wiki/Mutation) — Fandom wiki
- [Fighting](https://guides.gamepressure.com/mutant-year-zero-road-to-eden/guide.asp?ID=47933) — gamepressure.com guide
- [Controls](https://www.gamepressure.com/mutant-year-zero-road-to-eden/controls/z3ba97) — gamepressure.com guide
- [Starting tips](https://guides.gamepressure.com/mutant-year-zero-road-to-eden/guide.asp?ID=47741) — gamepressure.com guide
- [Guide and Walkthrough (PS4) by clandestine47](https://gamefaqs.gamespot.com/ps4/233878-mutant-year-zero-road-to-eden/faqs/78793) — GameFAQs
- [What do the red eye symbols and red shields mean](https://gamefaqs.gamespot.com/boards/233878-mutant-year-zero-road-to-eden/77272392) — GameFAQs board
- [Can you explain stealth/ambushing in the game?](https://steamcommunity.com/app/760060/discussions/0/3315110799623435119/) — Steam Community
- [Overwatch](https://steamcommunity.com/app/760060/discussions/0/1745605598720162561/) — Steam Community
- [Can't see the detection radius](https://steamcommunity.com/app/760060/discussions/0/5965578747674503401/) — Steam Community
- [Please, please, please mark last enemy on map](https://steamcommunity.com/app/760060/discussions/0/1745605598715653777/) — Steam Community
- [Camera rotation buttons in combat](https://steamcommunity.com/app/760060/discussions/0/4078523564603220382/) — Steam Community
- [Can I really not zoom in and out?](https://steamcommunity.com/app/760060/discussions/0/1744479064010091919/) — Steam Community
- [I am geniunley enjoying this game](https://steamcommunity.com/app/760060/discussions/0/3315110799617366871/?ctp=2) — Steam Community
- [The algorithm for hit chance is really weird...](https://steamcommunity.com/app/760060/discussions/0/3398435622565008380/) — Steam Community
- [Iron Mutant Play through?](https://steamcommunity.com/app/760060/discussions/0/4078523564609256655/) — Steam Community
- [Master the Stealthy Approach](https://www.mutantyearzero.com/news/master-the-stealthy-approach/) — official dev blog
- [New Game Plus](https://www.nexusmods.com/mutantyearzeroroadtoeden/mods/1) and [Quick save](https://www.nexusmods.com/mutantyearzeroroadtoeden/mods/5) — Nexus Mods
- [Mutant Year Zero ultrawide and wider fix](https://community.pcgamingwiki.com/files/file/1362-mutant-year-zero-ultrawide-double-monitor-patcher) — PCGamingWiki

## Nothing-found list

None outright. Every one of the ten headings below returned at least one documented observation,
and several of the strongest ones are explicit absences — no drawn overwatch zone, no minimap, no
turn-order strip, no camera zoom — which are findings about the game, not blanks in this file.

---

## 1. Screen furniture

- Action points are large dash marks above each character's ability bar, left side of that
  character's own UI, not gathered into one shared panel. **verified**
  ([How to Play](https://mutantyearzero.fandom.com/wiki/How_to_Play_Mutant_Year_Zero:_Road_to_Eden))
- The ability bar carries exactly three slots regardless of level: one passive (round icon), one
  minor (square icon), one major (hexagon icon). A Stalker can carry more mutations than that in
  the inventory but only one of each shape is equipped at a time. **verified**
  ([Mutation](https://mutantyearzero.fandom.com/wiki/Mutation))
- There is no minimap. One player calls it "a huge oversight" in a thread otherwise positive about
  the game; nobody in the replies disputes the claim. **verified**
  ([I am geniunley enjoying this game](https://steamcommunity.com/app/760060/discussions/0/3315110799617366871/?ctp=2))
- In its place, a real-time-only "Zone Summary" button, held rather than tapped, lights up the
  zone's exits temporarily and then stops. It is not available once tactical mode starts.
  **verified** ([Controls](https://www.gamepressure.com/mutant-year-zero-road-to-eden/controls/z3ba97))
- An "Exit Combat" control sits in the lower right corner during the ambush-setup phase, before the
  first shot: pressing it cancels the encounter and returns to real-time exploration. Once anyone
  has fired or been noticed, the option is gone. **verified**
  ([How to Play](https://mutantyearzero.fandom.com/wiki/How_to_Play_Mutant_Year_Zero:_Road_to_Eden))
- Resource counts (scrap, medkits, artifacts) are reported by secondary sources as living in the
  top right of the screen during exploration. **remembered** — no primary page opened for this
  specific claim; see gap list.

**What a picture would settle.** A full-HUD screenshot taken outside combat, with at least one of
scrap/medkits/artifacts nonzero, settles where those counters actually sit and whether Screen
furniture item 3 above is real or an artefact of an AI-summarised search result.

## 2. The soldier

- Two action points per Stalker; some mutations (Run 'N' Gun) raise this to three. Movement,
  shooting, throwing and sprinting each end the turn if they consume the character's last point;
  reloading and a short move do not. **verified**
  ([How to Play](https://mutantyearzero.fandom.com/wiki/How_to_Play_Mutant_Year_Zero:_Road_to_Eden);
  [Fighting](https://guides.gamepressure.com/mutant-year-zero-road-to-eden/guide.asp?ID=47933))
- Switching to a secondary weapon or to a grenade costs nothing, and can be done purely to preview
  its hit chance or throw range before deciding whether to commit an action to it. **verified**
  ([Fighting](https://guides.gamepressure.com/mutant-year-zero-road-to-eden/guide.asp?ID=47933))
- A held-button rotates the camera and a separate key changes the viewed storey — see heading 8 —
  but nothing in the sources describes what a *hover* over an ability in the bar reveals beyond the
  flavour-text summaries guides give for each mutation's cost, recharge and effect. Whether that
  text appears as an in-game tooltip or is guide-authors' paraphrase is not established here.
  **remembered**
- "Cancel an action" exists as its own bound control on console, distinct from movement and firing.
  What it undoes — the current selection, a partial move, or the whole turn — is not stated by any
  source found. **remembered**

**What a picture would settle.** A hover over an ability icon with the tooltip on screen, and a
short clip of pressing cancel mid-move (before and after the character has stepped), would settle
both open items above — the shape of the hover reveal, and how far back cancel reaches.

## 3. The target

- Hit chance only ever displays as 25%, 50%, 75% or 100% — never a value between — inherited
  directly from the tabletop original's six-sided-dice-in-fixed-steps resolution. One long-time
  player states it as flatly as a rule: "never seen anything in between." **verified**
  ([Guide and Walkthrough](https://gamefaqs.gamespot.com/ps4/233878-mutant-year-zero-road-to-eden/faqs/78793))
- Flanking removes the target's cover bonus outright rather than reducing it. High ground and being
  in a lit area (+25%) each raise the shooter's own hit chance. Damage shown before firing does not
  include a critical roll, which is a separate stat carried per weapon. **verified**
  ([Fighting](https://guides.gamepressure.com/mutant-year-zero-road-to-eden/guide.asp?ID=47933);
  [Guide and Walkthrough](https://gamefaqs.gamespot.com/ps4/233878-mutant-year-zero-road-to-eden/faqs/78793))
- The game exposes the hit-chance number at two separate moments — hovering a destination tile
  while choosing where to shoot from, and the dedicated "fire weapon" screen once a target is
  locked — and players report the two numbers disagreeing for the identical shot, close range,
  point-blank, no intervening choice. **verified**
  ([The algorithm for hit chance is really weird...](https://steamcommunity.com/app/760060/discussions/0/3398435622565008380/))
- What terms make up that second number — is cover broken out on its own line, is the light bonus
  named, is there a running total — is not established by any source found; guides describe the
  *inputs* to the roll, never the panel that lists them. **remembered**

**What a picture would settle.** The exact frame from the discrepancy report — the movement-preview
overlay's hit-chance figure and the "fire weapon" confirmation screen's figure, for the same target
and the same tile, in the same turn — would settle whether the mismatch is a real second readout
with different inputs (worth citing) or a stale number that failed to refresh (a bug, not a
convention). Either finding is useful to Brief One.

## 4. The tile

- Movement is shown as a coloured grid: white tiles cost one action point, orange cost two, red are
  unreachable (blocked, or on an inaccessible level). **verified**
  ([How to Play](https://mutantyearzero.fandom.com/wiki/How_to_Play_Mutant_Year_Zero:_Road_to_Eden))
- Cover comes in two tiers only — low cover blocks 25% of incoming hit chance, high cover blocks
  75% — shown as a shield icon that is reported to turn red when the character currently holding it
  is flanked or otherwise exposed. **verified**
  ([How to Play](https://mutantyearzero.fandom.com/wiki/How_to_Play_Mutant_Year_Zero:_Road_to_Eden);
  [red eye symbols and red shields](https://gamefaqs.gamespot.com/boards/233878-mutant-year-zero-road-to-eden/77272392))
- Enemy fields of view are drawn as a red circle with a pink border — but **only while the party is
  in stealth mode** (flashlight off), and its radius shrinks compared to flashlight-on. Turning the
  flashlight back on does not merely fail to help; it removes the ring from the screen entirely,
  which several players read as a rendering bug before learning it is the intended gate.
  **verified** ([Can't see the detection radius](https://steamcommunity.com/app/760060/discussions/0/5965578747674503401/))
- The stealth-break warning is drawn on the *destination tile itself*, before the move is
  committed: hovering a tile to move to shows the same hidden-mask icon with a red line through it
  if moving there would put the character in an enemy's vision. **verified**
  ([red eye symbols and red shields](https://gamefaqs.gamespot.com/boards/233878-mutant-year-zero-road-to-eden/77272392))
- A separate "Hide" state (context action near cover, distinct from the flashlight's stealth mode)
  shows the same burglar-mask icon and grants +15% critical chance plus access to Silent Assassin
  while it holds; it breaks the instant an enemy's patrol brings them close enough regardless of
  the vision-circle geometry. **verified**
  ([Can you explain stealth/ambushing?](https://steamcommunity.com/app/760060/discussions/0/3315110799623435119/))

**What a picture would settle.** A single screenshot capturing all three states in one frame — the
movement-range overlay, the shield icon in its exposed (red) state, and the vision-circle ring — is
probably not obtainable in one shot, since the ring only appears in stealth and the shield-flanked
state is a firefight state; two frames, one per mode, would do it instead.

## 5. The enemy

- Enemies too high level to fight are marked with a red skull icon during reconnaissance —
  informational, not a threat state that changes over the fight. **verified**
  ([How to Play](https://mutantyearzero.fandom.com/wiki/How_to_Play_Mutant_Year_Zero:_Road_to_Eden))
- There is no ambient alert ladder described anywhere in the sources found — no "suspicious, then
  searching, then alarmed" progression of the kind Invisible, Inc. or Mutant Year Zero's own
  tabletop cousin might suggest. An enemy is either unaware (the player is outside its vision
  circle or hidden), or the fight has started. **remembered** — an absence inferred from the
  consistent silence of every guide on the subject, not a positive statement found anywhere that
  the ladder doesn't exist; see gap list.
- Once combat starts, a directional marker exists to point the player at a remaining, unseen enemy
  — but it fails often enough, and has since launch, that a recurring thread topic is "where is the
  last enemy," with replies confirming the marker can point at an already-dead enemy's corpse or
  off the edge of the map entirely. **verified**
  ([mark last enemy on map](https://steamcommunity.com/app/760060/discussions/0/1745605598715653777/))
- There is no persistent map-position memory for an enemy once it leaves the player's sight beyond
  that one directional marker — contact, once lost, is not drawn as a last-known position or a
  decaying belief of any kind. **inferred**, from the marker thread above combined with the
  established absence of a minimap (heading 1) to hold such a marker on.

**What a picture would settle.** The directional marker itself, captured in a state where it is
known (from the thread) to be wrong — pointing at a corpse or off-map — settles its actual visual
form, which no source describes beyond "a red marker" and "an indicator."

## 6. Turn order and time

- Combat is phase-based, not initiative-based: the player moves any or all of the active squad in
  any order they choose during "the player's turn," then the AI moves every active enemy during
  "the enemy's turn," and the two phases repeat. This is stated directly and matches every
  walkthrough's description of "playing the first turn." **verified**
  ([How to Play](https://mutantyearzero.fandom.com/wiki/How_to_Play_Mutant_Year_Zero:_Road_to_Eden);
  [Fighting](https://guides.gamepressure.com/mutant-year-zero-road-to-eden/guide.asp?ID=47933))
- No source found describes a turn-order strip, an initiative value, or any UI naming who acts
  next beyond "the player" and "the enemy" as two undifferentiated blocks. A PC control exists to
  fast-forward through the enemy's phase, which only makes sense if that phase is otherwise a
  passive wait with nothing for the player to do but watch. **verified**
  ([Controls](https://www.gamepressure.com/mutant-year-zero-road-to-eden/controls/z3ba97))
- This is a real absence to record, not a gap: a squad-phase game with two undifferentiated blocks
  has no obvious place to put a strip, and none of the sources searched for one — official or
  player — treat its absence as a complaint. Compare heading 5's minimap and heading 7's overwatch
  zone, which are both absences players actively asked for.

**What a picture would settle.** Nothing further — this heading's answer is a structural fact about
the turn model (two-phase, not initiative-ordered), not a rendering choice a screenshot could
contradict.

## 7. Reactions

- Overwatch is the reaction: one action point, held into the opponent's phase, spent automatically
  by the game to fire at the first valid target that becomes exposed. Enemies use the identical
  mechanic against the player. **verified**
  ([How to Play](https://mutantyearzero.fandom.com/wiki/How_to_Play_Mutant_Year_Zero:_Road_to_Eden))
- **No zone, arc or highlighted tile set is ever drawn for an enemy's overwatch coverage.** Asked
  directly whether a player can anticipate which of their moves will trigger one, the only answer
  on record is: no, and "an indicator for the area the enemies can see would be nice, but is not
  implemented." A player only learns an overwatch existed at the moment it fires. **verified**
  ([Overwatch](https://steamcommunity.com/app/760060/discussions/0/1745605598720162561/))
- The listed counters to a triggered or anticipated overwatch are all indirect — a smoke grenade to
  break line of sight, or specific mutations (Dodge Dash, Puppeteer) — never a direct "this move is
  safe" readout. **verified** (same thread)
- What the moment of firing looks like — camera behaviour, whether the turn pauses to show it, any
  distinct sound or animation cue separating an overwatch shot from a normal one — is not described
  by any source found. **remembered**

**What a picture would settle.** This is the heading where a still cannot do the job: the entire
finding is that nothing is drawn *before* the trigger, so the only informative capture is a clip
spanning a move that is known in advance (from a save made just before) to trigger an enemy's
overwatch — showing the full HUD in the moment leading up to, during, and immediately after the
shot fires.

## 8. Camera and input

- Rotation is a held key plus mouse-drag on PC ("Rotating the camera - you need to hold the button
  and use the mouse to rotate"), not a stepped snap-to-bearing key of the kind XCOM 2 uses.
  **verified** ([Controls](https://www.gamepressure.com/mutant-year-zero-road-to-eden/controls/z3ba97))
- There is no zoom control at all. Players have tried the scroll wheel and keyboard +/- and report
  neither does anything; this appears to be a genuine absence rather than an undiscovered bind.
  **remembered** — found via a search-engine summary of the thread rather than the thread's own
  text; see gap list.
- Storey/level is changed with its own dedicated key ("Change level"), separate from camera pitch,
  used both to move a character to a roof and to look at an enemy standing on a different level
  from the current camera. **verified**
  ([Controls](https://www.gamepressure.com/mutant-year-zero-road-to-eden/controls/z3ba97))
- A long-standing, unresolved bug: holding the camera-pan key (W or S) during the player's own turn
  for more than roughly a second and a half can cause the active character's action points to
  disappear and the turn to lock up, with no official response recorded. This means camera input
  and turn-commit state are not as separated as the control scheme implies. **verified**
  ([Camera rotation buttons in combat](https://steamcommunity.com/app/760060/discussions/0/4078523564603220382/))

**What a picture would settle.** A clip reproducing the pan-lockup bug — holding the pan key through
the moment the AP dashes (heading 1) vanish — would settle whether anything on screen warns the
player before the lockup happens, which the forum thread doesn't say either way.

## 9. Confirmation and refusal

- Exiting an ambush setup before the first shot is a single confirmed, silent, reversible action —
  no warning, because nothing has happened yet to warn about (heading 1). **verified**
- The one genuine confirmation dialogue on record: at the start of each of a hidden character's
  turns, the game asks whether to bring them out of hiding, and answering no defers that character
  without penalty. This is the sole interrupt-and-ask moment found in any source. **verified**
  ([Fighting](https://guides.gamepressure.com/mutant-year-zero-road-to-eden/guide.asp?ID=47933))
- Movement and firing themselves take no confirmation step beyond the single click that commits
  them — no second click, no "are you sure," even for a shot the game itself displays at 25%.
- The game's actual answer to "what happens if I take a bad shot" is not a warning at all: guides
  recommend saving before every fight and after every turn — "there are 99 slots in the PC version"
  — precisely so a bad roll can be undone by reloading rather than played through. **verified**
  ([Starting tips](https://guides.gamepressure.com/mutant-year-zero-road-to-eden/guide.asp?ID=47741))
- The optional "Iron Mutant" difficulty modifier exists specifically to remove that safety net: it
  autosaves after every turn, permits no manual save, and deletes the save file on a wipe. Its
  existence as an opt-in extra mode is itself evidence that the base game's default undo mechanism
  is understood, in the community and seemingly by the developers, to be the reload. **verified**
  ([Iron Mutant Play through?](https://steamcommunity.com/app/760060/discussions/0/4078523564609256655/))

**What a picture would settle.** The hidden-character wake-up prompt, captured with its exact
wording and button layout on screen, is the one true confirmation dialogue this game has; nothing
else in this heading needs a picture, since the finding is an absence of prompts everywhere else.

## 10. What the game hides, and what its players added

- The mod scene is small — four titles found total, against the decade-long weight of job 1's
  archive: a Quick Save/Quick Load hotkey mod (F5/F9), a New Game Plus starter-save pack, a pause
  menu HUD toggle for clean screenshots, and a community ultrawide/multi-monitor patch the base
  game doesn't support natively. **verified**
  ([New Game Plus](https://www.nexusmods.com/mutantyearzeroroadtoeden/mods/1);
  [Quick save](https://www.nexusmods.com/mutantyearzeroroadtoeden/mods/5);
  [ultrawide and wider fix](https://community.pcgamingwiki.com/files/file/1362-mutant-year-zero-ultrawide-double-monitor-patcher))
- None of the four mods touch combat information — no cone-visibility mod, no overwatch-zone mod,
  answering heading 7's gap. Whatever players wanted fixed about detection and reactions, they
  asked for it in the forums (headings 4, 5 and 7 above) rather than patching it in themselves,
  which the small mod scene may simply not have had the tooling to attempt.
- The single most persistent, never-patched community complaint across five years of threads is
  the same one from heading 5: the last-enemy locator pointing at nothing. It is raised at launch
  in 2018 and still being asked about in 2023, which is itself the finding — not that the bug
  exists, but that nobody, official or modder, ever closed it. **verified**
  ([mark last enemy on map](https://steamcommunity.com/app/760060/discussions/0/1745605598715653777/))
- The Quick Save mod's existence is a quiet admission about the base game's save flow: if reloading
  before a risky shot is the community's accepted play pattern (heading 9), a mod that shaves that
  down to two keystrokes is filling a gap the base UI left for guides to paper over instead.
  **inferred**, from the Quick Save mod's description plus the Starting Tips guide's "save
  constantly, 99 slots" advice above.

**What a picture would settle.** Nothing here needs a picture; this heading is about absence and
pattern across years of public record, which text sources establish about as well as they ever
will.

---

## What transfers

- No zone or arc is ever drawn for an enemy's overwatch, and the player has no way to tell in
  advance whether a move will trigger one — direct evidence for **Reactions** in `conventions.md`
  and for Brief Four's concern with who a shot wakes.
- The stealth-break warning is drawn on the destination tile itself, before the move commits, not
  as an after-the-fact message — evidence for Brief One's "readouts go on the things they describe"
  and for **What of the enemy is drawn**.
- Detection rings exist only in the mode that needs them and shrink under a player-taken action
  (the flashlight) rather than a piece of gear or a levelled skill — the strongest single data point
  in the set for **What of the enemy is drawn**, and for the asymmetry question every convention
  here has to answer under contract 3.
- There is no per-unit turn order or initiative strip; combat alternates squad-phase to squad-phase
  with nothing in between — evidence for **Turn order and whose go it is**.
- The ability bar is capped at exactly one passive, one minor and one major slot regardless of
  level, rather than growing into a longer list — evidence for **Selecting and ordering**.
- The camera neither zooms nor free-rotates, only a held-drag rotation and a separate storey-cycle
  key — a further data point for **The camera**, alongside the case already closed by entry 058.

## The gap list

1. **Heading 7 (Reactions).** Whether anything at all telegraphs an enemy's overwatch coverage
   before a move is committed, beyond the forum answer of "not implemented." *What would settle
   it:* a clip spanning a move known in advance (from a save made just before) to trigger a
   specific enemy's overwatch, with the full HUD visible through the moment it fires — a still
   cannot do this, since the finding is about what happens over time. *Changes:* whether MYZ can be
   cited as the set's zero-telegraph extreme for Brief Four, or whether some unlogged indicator
   exists that no source happened to mention.

2. **Heading 3 (The target).** The exact line-by-line layout of the "fire weapon" confirmation
   screen — is cover broken out on its own line, is the light bonus named, is there a running
   total — versus the movement-preview overlay's single number, which players report disagreeing
   with it for an identical shot. *What would settle it:* a still of the fire-weapon screen open on
   a target with cover, at range, in partial light, beside a still of the movement overlay for the
   same shot. *Changes:* whether the mismatch is a second, more detailed readout (useful evidence
   for Brief One) or a stale number that failed to refresh (a bug, not a convention).

3. **Heading 1 (Screen furniture).** Where the resource counters (scrap, medkits, artifacts)
   actually sit — reported as top-right by a search summary this session did not verify against a
   primary source. *What would settle it:* a full-HUD still taken outside combat with a nonzero
   resource count. *Changes:* whether this game is a counter-example to "the one finding that
   outranks the other nine" in `conventions.md`, or confirms it by keeping resources out of the
   tactical HUD entirely (resource counts may only appear in real-time exploration, never in
   combat, which the sources don't distinguish).

4. **Heading 4 (The tile).** The two movement-cost bands (white/orange) and the cover-shield icon
   in its exposed (red) state, side by side in one frame — described separately by different
   sources but never confirmed together. *What would settle it:* the movement-range overlay active
   on a unit that is simultaneously flagged as flanked. *Changes:* nothing structural, but confirms
   or corrects how the two overlays compose when both are live at once, which a brief describing
   the tile would otherwise have to guess at.

5. **Heading 2 (The soldier).** What a hover over an ability actually reveals — an in-game tooltip
   with numbers, or nothing beyond the icon, with guides' cost/recharge/effect text being the
   guide-writers' own research rather than an on-screen readout. *What would settle it:* a still of
   an ability icon mid-hover, tooltip visible, cursor in frame. *Changes:* whether Brief One's
   "figures move onto the things they describe" already has a precedent here or a counter-example.

6. **Heading 2 (The soldier), second item.** How far "cancel" unwinds — the current selection, a
   partial move already taken, or the whole turn. *What would settle it:* a clip of pressing cancel
   immediately after a character has moved partway, then again after they have fired.
   *Changes:* whether this game offers anything resembling Tactical Breach Wizards' undo (job 10)
   or nothing past an unstarted selection.

7. **Heading 6 (Turn order).** Whether anything at all — colour wash, banner text, a change to the
   ambient sound — marks the exact instant control passes from the player's phase to the enemy's,
   beyond input simply stopping working. *What would settle it:* a clip of that transition moment.
   *Changes:* little for this game's own brief, since the heading's answer (no strip, phase-based)
   is already settled by text sources, but it sharpens what "nothing" means for the synthesis pass
   comparing across all ten games.

8. **Heading 8 (Camera).** Whether the camera-pan lockup bug (holding W/S mid-turn until AP dashes
   vanish) still reproduces, and whether anything visible warns the player before the lockup lands.
   *What would settle it:* a clip holding the pan key through the moment of failure. *Changes:*
   whether this belongs in the synthesis as a live cautionary case about coupling camera input to
   turn-commit state, or as dead history from a version several patches gone.

9. **Heading 5 (The enemy).** The directional last-enemy marker's actual visual form — colour,
   shape, whether it points or just glows — which no source describes beyond "red" and
   "indicator," plus a case of it visibly failing (pointing at a corpse or off-map).
   *What would settle it:* a still of the marker in a known-broken state, ideally with the
   surrounding HUD visible to also confirm or deny heading 1's minimap claim in the same frame.
   *Changes:* gives the synthesis pass an actual described object instead of a secondhand adjective.

10. **Heading 9 (Confirmation).** The exact wording and button layout of the "come out of hiding?"
    prompt — the one confirmation dialogue this file found evidence for. *What would settle it:* a
    still of that prompt on screen, mid-battle, with a hidden character selected. *Changes:*
    whether it reads as a real choice with stakes stated, or as a formality guides only mention
    because it exists, not because it matters.
