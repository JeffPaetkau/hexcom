# Into the Breach — reference file (pass one, documentary)

Job 9 of the ten in [../../subprojects/interface.md](../../subprojects/interface.md). Read that
file's job description before reading this one; it is not repeated here.

**What this game is the authority on, and what it is only an instance of.** Into the Breach is
the authority on total, standing disclosure of enemy intent: every attack a Vek will make is
drawn, in full, one turn before it lands, and there is no fog, no suspicion state and no alert
ladder anywhere in it — every unit, friendly or hostile, is fully known the instant it exists on
the board. That makes it the extreme opposite pole from contract 3's asymmetric knowledge, and
exactly why interface.md calls this job "the answer the onboarding brief has to argue with rather
than around": it is not evidence for what this game's HUD should draw about a hostile, it is the
boundary case that shows what disclosure looks like with the asymmetry switched off entirely. It
is only an instance of the rest: a small, alternating-turn action bar, a movement-range highlight,
and a two-tier undo, none of which are unusual for the genre.

**Tag key.**

| | |
|---|---|
| **verified** | a published source, with the link |
| **remembered** | model knowledge, unchecked — a candidate for the gap list |
| **inferred** | from something else in this file, which it names |

Pass one carries no **observed** tags; see interface.md's *The reference set* for why.

**Sources.**

- [interfaceingame.com — Combat screenshot](https://interfaceingame.com/wp-content/uploads/into-the-breach/into-the-breach-combat.png), full-resolution capture of the tactical HUD mid-battle
- [interfaceingame.com — Enemy Turn screenshot](https://interfaceingame.com/wp-content/uploads/into-the-breach/into-the-breach-enemy-turn.png)
- [interfaceingame.com — Pilot/hangar screenshot](https://interfaceingame.com/wp-content/uploads/into-the-breach/into-the-breach-pilot.png), out-of-mission mech management, cited only where noted
- [Into the Breach Wiki — How To Play Guide](https://intothebreach.fandom.com/wiki/How_To_Play_Guide_For_Into_The_Breach)
- [Into the Breach Wiki — Attacks](https://intothebreach.fandom.com/wiki/Attacks)
- [gamepressure.com — Interface: Battle Map](https://www.gamepressure.com/into-the-breach/interface-battle-map/zcaa73)
- [PCGamingWiki — Into the Breach](https://www.pcgamingwiki.com/wiki/Into_the_Breach)
- Steam Community discussions: [move the Undo Move button](https://steamcommunity.com/app/590380/discussions/0/1694914735994678222/), [a second thread asking the same](https://steamcommunity.com/app/590380/discussions/0/1697167355212699840/), [undo weapon actions, not just moves](https://steamcommunity.com/app/590380/discussions/0/1697167355222689214/), [general PC controls thread](https://steamcommunity.com/app/590380/discussions/0/3391786047381352814/)
- [thoughtsabout.games — Combining Mechanics I Dislike into a Game I Adore](https://thoughtsabout.games/blog/posts/into-the-breach-combining-mechanics-i-dislike-into-a-game-i-adore/)
- [Atomic Bob-Omb — Into the Breach & Enemy Intentions](https://atomicbobomb.home.blog/2020/05/17/into-the-breach-enemy-intentions/)

**Nothing found.** Heading 7, *Reactions*, came back fully empty — no source describes anything
resembling an interrupt, an overwatch state, or a reserved action of any kind, and heading 5 below
explains why one would be redundant here.

---

## 1. Screen furniture

Top-left, stacked: a settings gear; **Power Grid** — a lightning-bolt icon beside an eight-segment
pip bar, partially filled, showing the campaign-wide grid health this mission's damage draws down
(**verified**, combat screenshot); beside it, **Grid Defense NN%**, "the chance of a building
resisting damage," shown to the right of the Power Grid meter (**verified**, How To Play Guide and
matching the screenshot's "18%" reading). Below that: **Reset Turn**, greyed once spent
(**verified**, screenshot; "a single turn per battle to be reset," **verified**, thoughtsabout.games).
Below that, a large **End Turn** button beside a smaller **Undo Move** button (**verified**,
screenshot).

Left edge below the buttons: a vertical list of the squad's mechs, one row each, portrait
thumbnail plus a second small icon and a row of green square health pips; a collapse arrow at the
list's foot (**verified**, screenshot). Selecting a mech expands a separate card, bottom-left, with
the pilot's portrait and name, a health count, and each weapon or ability as its own icon slot
with a small pip beneath it (**verified**, screenshot showing pilot "Ralph Karlsson").

Top centre: an **Attack Order** button, a circular-arrow icon; holding it (or `Alt`) shows the
turn's full resolution order including environmental hazards (**verified**, How To Play Guide).
Top right: a **Victory in N turns** countdown, and beneath it a **Bonus Objectives** panel listing
each objective with a status icon — a filled star for one currently biting, an outlined star for
one not yet live, a warning triangle for one at immediate risk (**verified**, screenshot; the icon
meanings are **inferred** from which objectives they sit beside).

A tile-info card appears bottom-right reading, in the captured frame, "Ground Tile — No special
effect" (**verified**, screenshot). Whether this card is always present and blank when nothing is
hovered, or only spawns on hover, is not settled by a still — see the gap list.

During the hostile phase, a full-width dark bar reading **ENEMY TURN** in large caps crosses
roughly the screen's vertical middle; the mech roster list stays visible at the left, and the
screenshot's bottom two corners render as plain black (**verified**, enemy-turn screenshot). Given
the discipline that a picture would settle this: whether the blacked corners are deliberate
letterboxing that hides HUD elements meaningless mid-hostile-phase, or an artefact of that one
capture, is unresolved — see the gap list.

## 2. The soldier

No bottom action bar. Each mech's weapon or ability icons live inside that mech's own entry in the
roster list and, once selected, in its expanded card (**verified**, screenshot). Number keys are a
shortcut to the same weapons a click selects (**verified**, How To Play Guide: "Click on a weapon
to use it. The number keys will also work as a shortcut"). Movement is not gated behind an ability
icon at all — a highlighted tile is clicked directly (**verified**, How To Play Guide).

Firing locks a mech out of moving for the rest of that turn: "You may not move after you've shot a
weapon" (**verified**, How To Play Guide). Whether this is drawn — a disabled move-highlight, a
struck-through icon — or simply produces no highlighted tiles if tried, is not settled by any
source found; see the gap list.

Two tiers of hover disclosure exist, each behind a different held key rather than a plain hover:
holding `Ctrl` over a unit or ability "shows additional information about its abilities and
status" (**verified**, How To Play Guide); holding `Alt` (or hovering the Attack Order button)
shows the turn's resolution order (**verified**, same source). Cancel is right-click, per one
community summary of the controls (**remembered**, cross-checked loosely against the Steam
controls thread but not confirmed word-for-word — see the gap list under heading 8 for the
button conflict this sits inside).

## 3. The target

There is no hit-chance term to show, because Into the Breach's attacks are not rolled — an attack
that is telegraphed and not disrupted lands for its stated value (**remembered**; consistent with
every source found describing damage as a fixed number rather than a percentage, but no source
states the absence of a roll in so many words, so it is not tagged verified). This is a structural
difference from the rest of the reference set worth naming plainly: a "shot readout" here has
nothing probabilistic in it at all, only a damage number and whatever secondary effect the attack
carries.

Attacks are typed — Melee, Beam, Projectile, Artillery, Dash, Fly Over, Free Aim — each with its
own targeting shape, and each may additionally push, pull, throw, swap, or apply Fire, Freeze,
A.C.I.D., Smoke or Shield (**verified**, Wiki: Attacks). The damage-and-effect preview appears on
hover once a weapon is selected, with no key required (**verified**, How To Play Guide: "Hover an
enemy to highlight its forewarned attack" — this describes previewing the *enemy's* telegraphed
attack, and the same hover-to-preview pattern is described for the player's own weapons via the
attack-order and Ctrl layers above). No source names a dedicated key for cycling between multiple
valid targets in range; see the gap list.

## 4. The tile

A selected mech's reachable tiles are shown as a green-tinted, green-bordered overlay across the
grid (**verified**, screenshot). Whether the highlighted range is banded by terrain cost or is a
flat pool of tiles with some terrain simply impassable is not settled by any source found — see
the gap list.

Tiles an enemy currently intends to hit are marked with a red diagonal-stripe pattern; a tile about
to have a Vek emerge from underground carries a yellow chevron icon instead, visually distinct
from an already-present enemy (**verified**, screenshot). There is no concealment or detection
ring of any kind, because there is no concealment mechanic in this game at all — everything on the
board is visible to the player the instant it exists (**inferred**, from heading 5). There is
correspondingly no cover system either: buildings and mountains block a Beam or Projectile's line
by their type, per heading 3's attack types, but grant no percentile defensive bonus, because
nothing here is rolled (**inferred**, from heading 3).

## 5. The enemy

Nothing is ever suspected, remembered-but-unseen, or hidden — a Vek is either not yet on the
board, marked for emergence next turn by the chevron in heading 4, or fully drawn with its
telegraphed attack shown on hover (**verified**, screenshot and How To Play Guide, combined).
There is no alert ladder, no noticed-short-of-seen state, and no contact file of any kind, because
nothing is ever in a state short of fully known. The moment the game "admits a contact" is
therefore not a moment at all in the sense the rest of this reference set means it — it is the
turn the emergence marker appears, one full turn ahead of the Vek itself, which is earlier and
more generous than any disclosure a stealth game in the set offers (**inferred**, from the
emergence-marker finding in heading 4 and the two-phase turn structure in heading 6).

## 6. Turn order and time

Whole sides alternate — no interleaved initiative strip of any kind (**verified**, enemy-turn
screenshot showing a full-width phase banner rather than a per-unit order). The wrinkle specific
to this game: Vek take two separate phases bracketing the player's one, advancing into position
and telegraphing on the first, then executing the telegraphed attack on the second, with the
player's own turn always sandwiched between a telegraph and its resolution ("the enemies take two
turns and the player acting in between them," **verified**, Atomic Bob-Omb). This is the mechanical
reason the phase-banner convention costs this game nothing: there is no interleave to lose track
of, because nothing a Vek does on its own phase was ever secret — it was shown a full turn earlier.

The **Victory in N turns** counter in heading 1 doubles as the round-boundary marker, ticking down
once per round and serving as both the game's clock and its only order-adjacent readout
(**inferred**, from heading 1). Whether the **ENEMY TURN** banner carries a minimum dwell time, an
entry or exit animation, or resolves instantly when a phase has nothing perceptible in it, is not
settled by a still image; see the gap list.

## 7. Reactions

Nothing found. No source describes anything resembling an interrupt, a held or reserved action, or
any way for the player to answer something mid-enemy-phase. This is a genuine absence rather than
an oversight in the research: heading 5 and 6 together are the reason — nothing a Vek does was
ever hidden, so there is nothing sprung on the player to react to in the sense the rest of the
canon means it (**inferred**).

## 8. Camera and input

The perspective is a fixed isometric view; PCGamingWiki's own taxonomy classifies the control
scheme simply as "Point and select" and lists no rotation, pan or zoom feature under its Video or
Input sections (**verified**, PCGamingWiki). No source found describes any camera movement at all
— no drag, no scroll-zoom, no rotation step. That absence is itself worth recording plainly: even
the genre's more sparing entries usually keep a zoom, and no evidence of one turned up here.

Default binds found: left-click selects and moves (**verified**, How To Play Guide and the general
Steam controls thread), number keys select a weapon (**verified**, How To Play Guide), `Alt`
(held) shows attack order and `Ctrl` (held) shows extended unit/ability information (**verified**,
How To Play Guide). **The two sources on the fire button conflict.** One AI-summarised search
result described left-click selecting a weapon icon and right-click firing on the target; a
different Steam Community discussion, summarised the same way, described right-click as a plain
cancel with left-click covering both movement and firing. Neither is a primary quote and this file
does not resolve the conflict — see the gap list, first item. No cycle-target key was found in any
source.

## 9. Confirmation and refusal

Firing a weapon is the one truly irreversible in-battle action: it cannot be moved after, and
there is no "undo fire," only **Undo Move**, unlimited-use but only for movement taken before that
mech has fired (**verified**, How To Play Guide; "the player to freely undo move actions if they
haven't yet fired their weapons," **verified**, thoughtsabout.games). **Reset Turn** is a second,
coarser grain: one full-turn rollback per battle, and the UI marks it spent with a "RESET USED"
indicator once used (**verified**, thoughtsabout.games). No dialogue-box confirmation of any kind
was found anywhere in the sources gathered — every commitment reads as a bare click, backstopped
by the preview-then-undo system rather than an "are you sure?" prompt (**inferred**, from the
absence of any such mention across every source above).

What the game refuses and how it presents the refusal is not settled: whether the move-after-
firing rule shows as a disabled state on the mech or simply yields no highlighted tiles if
attempted is the same open question as heading 2; see the gap list.

## 10. What the game hides, and what its players added

Controller support was not in the original release; it shipped in a November 2018 update, "added
in the November 2, 2018 update," with the UI "designed with controllers in mind" once it landed
(**verified**, PCGamingWiki; the controller-support design claim is **verified** against the
earlier Steam News search result cited in this job's research). Touchscreen support followed even
later, in the April 2020 1.2 update (**verified**, PCGamingWiki). Both are retrofits onto a
mouse-and-keyboard interface that was not originally built to accommodate them.

Community friction, repeated across independent threads: players have twice separately asked for
**Undo Move** to be moved further from **End Turn** because the two are close enough to mis-click
between (**verified**, [thread one](https://steamcommunity.com/app/590380/discussions/0/1694914735994678222/), [thread two](https://steamcommunity.com/app/590380/discussions/0/1697167355212699840/)).
A third, separate thread asks for the graduated-undo system in heading 9 to be extended one grain
further, to weapon actions and not just moves (**verified**, [thread three](https://steamcommunity.com/app/590380/discussions/0/1697167355222689214/)).
Both are exactly the class of finding this heading exists to catch: a placement problem and a
scope boundary invisible to design intent, visible only in complaint volume.

---

## What transfers

- **Heading 5 and 6, together, are the boundary case for brief Two (the enemy's file) and for
  `conventions.md`'s *What of the enemy is drawn*.** This game proves what total disclosure looks
  like with contract 3's asymmetry switched off; it is not a source of drawing technique for a
  rung or a marker, it is the argument that this game's departure from it has to keep answering.
- **Heading 6 bears on brief Five (the strip, and the pause).** The two-phase Vek turn is the
  clearest existing evidence that a phase banner can fully replace a per-unit order display when
  nothing on the other side's turn is ever secret — the same premise brief Five's banner design
  already assumes for the unfound-hostile case specifically.
- **Heading 3 and 5 together bear on brief Four (who a shot would wake).** Telegraphing every
  attack a full turn ahead is the strongest form of "shown before committing" found in the set;
  it is the extreme end of the spectrum brief Four sits on, one rung short of preview.
- **Heading 9 bears on `conventions.md`'s *Selecting and ordering*.** The genre section there
  currently states a flat "no undo, ever" as the standard; this game's two-tier undo (unlimited
  pre-fire move undo, plus one single-use full-turn reset) is a second shipped model of graduated
  commitment that the current text does not mention.
- **Heading 5 also feeds the queued onboarding job.** Interface.md already names this game as the
  argument that job has to answer rather than route around; nothing in this file changes that, it
  only confirms in detail what "total disclosure" looks like on screen.

## The gap list

1. **Which mouse button fires and which cancels.** Heading 8. Sources conflict outright: one
   summary has left-click selecting a weapon and right-click firing on the target; another has
   left-click for both move and fire with right-click as a plain cancel. A clip of one full attack
   — weapon selected through the click that fires, cursor visible throughout — would settle it,
   and it is the most consequential item here because it is the direct point of comparison for
   brief Three's own right-click rebinding.
2. **Whether firing has one commit or two.** Heading 9. The same clip as item 1, watched frame by
   frame, would show whether the click that selects a target also fires, or whether a separate
   confirm step exists that no source described.
3. **The `ENEMY TURN` banner's timing and the blacked screenshot corners.** Heading 6 and heading
   1. A clip spanning one full hostile phase, from the banner's appearance to its disappearance,
   would settle whether there is a minimum dwell, an entry or exit animation, and whether the
   corners going black in the one screenshot found is deliberate or incidental to that capture.
4. **Whether the no-move-after-firing rule is drawn or just enforced.** Heading 2 and heading 9. A
   screenshot taken the instant after a mech fires, before ending its turn, with that mech still
   selected, would show whether its move highlight or weapon icon changes state or simply vanishes
   without a mark.
5. **Whether the tile-info card and the compact roster list are always present.** Heading 1. A
   screenshot of a battle with nothing hovered and no mech selected, set against one mid-hover and
   one mid-selection, would settle both questions in one comparison.
6. **Whether a target-cycle key exists.** Heading 3. A clip of a weapon whose range covers more
   than one valid target being selected would show whether there is any way to step between
   targets short of moving the mouse.
7. **Whether movement range is cost-banded or a flat pool.** Heading 4. A screenshot of a mech's
   highlighted range next to mixed terrain — water, mountain, rubble — in the same frame would
   settle whether terrain changes the cost of entering a tile or only ever blocks it outright.
8. **Whether any camera zoom exists.** Heading 8. No source confirms or denies one; a screenshot of
   the game's own settings or options screen, if it lists a camera or zoom control, would settle
   it in a single frame, and its absence there would be the answer instead.
