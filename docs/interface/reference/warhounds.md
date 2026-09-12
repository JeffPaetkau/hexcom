# Warhounds — reference file

Read [../../map.md](../../map.md) and [../../subprojects/interface.md](../../subprojects/interface.md)
first. This is one of the ten reference files interface.md's job table calls for; it is evidence,
not recommendation — see that file's rules before reading conclusions into it that are not here.

**What this game is the authority on, and what it is only an instance of.** Warhounds (Everplay
DMCC, released 11 August 2026) is the only shipped title found anywhere in the reference set with
a reserve mechanic that resembles ours at all: declaring overwatch spends the operator's remaining
action points on it. It is authority on that comparison, and on nothing else in its bank — its
version is all-or-nothing where `ReactionModel.Banked` is graded, which is most of what makes it
worth a section of `conventions.md` rather than a footnote. It is also the clearest shipped example
found of a *transparent* hit-chance readout: percentages per bullet in a burst, not one number for
the whole attack. Everywhere else — classes, loadout, base management, cover-and-flank arithmetic —
it is an ordinary instance of the XCOM/Jagged Alliance shelf the canon list already covers, and nine
of these ten headings say so plainly by coming back thin.

**Read, not played, and unusually so.** No screenshot in this pass. Every claim below is off
published text: the Steam store page, a scatter of community wikis, two previews, and one
developer-quoted design explainer. This is the thinnest file in the set by the brief's own
prediction, and the reason is not effort — it is that a game three weeks old at time of writing has
no accumulated screenshot corpus, no wiki with images, and no mod scene to mine for what the
shipped UI failed to do.

**A note on source quality, because it shapes every tag below.** Several of the sites cited —
`warhounds.org`, `warhoundswiki.wiki`, `warhounds-game.wiki`, `warhounds.online`, `warhounds.net` —
read as templated strategy-guide content rather than developer documentation or hands-on reporting:
generic tactical advice ("treat every action point as a promise"), no screenshots, no exact
keybinds, no panel positions, and near-identical phrasing across nominally independent domains.
None was caught stating something the others contradict, so nothing here is *known* wrong, but
"published" and "corroborated by someone who has touched the build" are not the same claim, and the
tag key below is honest about which of those this file can offer.

## Tags

| | |
|---|---|
| **observed** | read off a named shot in `shots/`. Not used in this file — pass one, and this game has no shots yet. |
| **verified** | a published source, with the link. Everything tagged this way below is community-wiki or press text, not a developer-authored manual or a screenshot; see the note above. |
| **remembered** | model knowledge, unchecked. Used sparingly and flagged for the gap list. |
| **inferred** | drawn from something else in this file, which it names. |

## Sources

- [Warhounds on Steam](https://store.steampowered.com/app/3929470/Warhounds/) — the "About This
  Game" text, feature bullets, tags, release date
- [Warhounds Wiki — home](https://warhounds.org/) — classes, general framing
- [Warhounds Wiki — Ballistics and Line of Sight](https://warhounds.org/combat/ballistics-and-line-of-sight/)
- [Warhounds Wiki — FAQ: Saves, Mods, Cheats](https://warhounds.org/faq/)
- [Warhounds Wiki (warhoundswiki.wiki) — Cover and Overwatch Guide](https://warhoundswiki.wiki/guides/cover-and-overwatch/)
- [Warhounds Wiki (warhoundswiki.wiki) — PC Controls Guide](https://warhoundswiki.wiki/guides/controls/)
- [Warhounds Wiki (warhounds-game.wiki) — Tactical Combat Guide](https://warhounds-game.wiki/guide/warhounds-tactical-combat-guide)
- [Warhounds Reference (warhounds.online) — No RNG Explained](https://www.warhounds.online/en/mechanics/no-rng)
- [GeekDad — Video Game Preview: 'Warhounds'](https://geekdad.com/2026/03/video-game-preview-warhounds/)
- [theGeek.games — Warhounds: Precise Shots, Ruthless Consequences](https://thegeek.games/2026/02/22/warhounds-precise-shots-ruthless-consequences/)
- [JEU.VIDEO — Warhounds review: a promising tactics game that still asks for patience](https://jeu.video/en/article/warhounds-review-steam-verdict-en)

## Nothing found

- **Heading 1, screen furniture.** No source describes where any persistent HUD element sits on
  screen. An ability/item bar is implied by the controls guide's "ability / item bar shortcuts"
  category, but never placed or pictured.
- **Heading 4, cover indicators.** The cover-and-overwatch guide says outright that it does not
  specify "HUD icons, percentages, or visual indicators for cover levels" — a gap named by the
  source itself, not one this file is guessing at.
- **Heading 5, the enemy.** No source anywhere describes how a suspected, remembered, or unseen
  enemy is drawn, or names an alert-state icon. Silence here could mean the game has nothing beyond
  the XCOM-shelf binary (hidden, then fully drawn) or could mean nobody has written about it yet.
  This file cannot tell which.
- **Heading 9, confirmation beyond the aim preview.** The only cancel/confirm behaviour any source
  names is backing out of an aim preview before it is fired. Nothing describes a second-click
  confirmation on a move, a warning dialogue, or an irreversible action the game blocks outright.

---

## 1. Screen furniture

No source lists the HUD's persistent elements or their screen positions. What can be said only by
inference: an ability/item bar exists (the controls guide assigns it a remap category — "quick
access to smoke, scanners, drones, grenades" — *inferred*), and a mission runs 25–40 minutes per
the store page, which implies *something* tracks progress toward that, unnamed. Difficulty and save
mode are chosen outside a mission, not drawn during one (*inferred*, from the FAQ's save-mode list
being a setup-time choice).

**What a picture would settle:** everything. A single frame of a mid-mission moment with no menu
open — what sits at the edges of the screen, and whether the store page's five-class roster shows
anywhere during play or only in the recruitment screen — would turn this heading from empty to
populated.

## 2. The soldier

Two action points per turn (*verified*, GeekDad and the tactical-combat guide agree). Movement
range is colour-coded by which action pays for it: "the spaces to which they can move are bordered
by blue lines to show how far they can move using one action and then yellow for their second
action" (*verified*, GeekDad). An ability/item bar exists for consumables and gadgets — smoke,
scanners, drones, optical camouflage (*verified*, Steam page + controls guide) — but no source says
where it sits, what its icons show at rest, or what a hover over an entry reveals.

Cancel exists as "exit aim previews without ending turn" (*verified*, controls guide), which is
narrower than an undo: it backs out of a shot or ability that has not yet fired, not out of a move
that already landed. No source says how far back a cancel goes, or whether a queued-but-uncommitted
move can be cancelled the same way a shot can.

**What a picture would settle:** a soldier selected with the ability bar on screen and the cursor
hovering one entry — its cost, its tooltip text, and whether the bar is the same bottom-row-of-
icons shape the canon list uses or something else. Also whether the blue/yellow movement bands
carry a number on the tile or only the colour.

## 3. The target

The shot readout is the best-documented heading in this file, because the developers' own
transparency pitch is quoted by three independent sources. It resolves **per projectile**, not per
attack: "the hit chances on a three-round attack are 100%, 90%, and 80%, respectively" for a burst
against a clear line of sight, each bullet penalised further than the last (*verified*, theGeek.games
and warhounds.online, quoting what reads as a developer explainer). Damage is a range, not a fixed
number — a starter rifle is described as "1-2 damage per shot, so if all three shots connect, total
damage can land anywhere between 3 and 6 points" (*verified*, theGeek.games). Cover produces a
graze floor: a target behind heavy cover can only be hit for minimum damage (*verified*, same
source). A miss keeps its trajectory and can strike a barrel, another enemy, or an ally in the line
(*verified*, same source) — a consequence of the physical-ballistics pitch rather than a stated UI
element, and it is not clear whether the *preview* warns of this before the trigger is pulled or the
player only discovers it after firing (flagged for the gap list).

The attack preview is confirmed to exist and to separate "accuracy bonuses from distance and cover
penalties" before commitment (*verified*, warhounds.net), and one guide advises "verify that the
preview displays 100% before committing" (*verified*, Ballistics and Line of Sight) — but no source
itemises which named terms appear in it (flank? elevation? suppression?) or whether the breakdown
is shown by default or behind a gesture. No source mentions a target-cycling key or the order
targets are offered in.

**What a picture would settle:** the attack preview itself, mid-aim, on a target with cover and at
range — every labelled term in the breakdown, in the order they are listed, and whether the
per-bullet percentages (100/90/80-style) sit on the same panel as the modifier breakdown or
somewhere else. Also whether target-cycling exists at all: a clip of switching targets without
moving the cursor off the trigger key would settle it outright.

## 4. The tile

Movement range is drawn in two colour bands keyed to which action point pays for the hex, as
above (*verified*, GeekDad). A path preview is implied by the existence of a bordered range at all,
though no source names it as a separate line drawn to the cursor (*inferred*). Cover is a tile
property that affects hit chance and can be wholly or partly destroyed by sustained fire or
explosives — "soft cover can be chewed down" (*verified*, Cover and Overwatch Guide) — but, as
flagged above, no source names an icon, shading, or percentage the tile itself carries. No source
mentions a detection or concealment ring of any kind; optical camouflage is named as squad
equipment (*verified*, Steam page) but nothing describes it as drawing a radius on the ground the
way Mutant Year Zero's torch-off circles do.

**What a picture would settle:** one frame with a tile in each of full cover, half cover, and open
ground selected or hovered in turn — whatever mark (if any) distinguishes them. And, separately, a
frame during optical-camouflage use showing whether anything is drawn on the ground for it.

## 5. The enemy

Nothing found, and flagged above as a genuine unknown rather than a confirmed empty heading — the
distinction the interface.md brief asks this pass to keep straight. The published material describes
enemies only as combat participants (classes are the player's own five; nothing names an opposing
roster or its states) and never as an interface object: no word on whether a suspected-but-unseen
hostile is marked, whether an alert level is shown as an icon or a bar, or whether the moment of
first contact is called out on screen. Given the game's XCOM/Jagged Alliance lineage this file
would guess (*remembered*, unchecked) that it follows the modern-XCOM shelf — hidden until seen,
then drawn fully and permanently — but nothing published confirms or denies it, and this is exactly
the kind of confident-sounding guess the brief warns a documentary pass will make without noticing.
It is listed here instead.

**What a picture would settle:** the single most valuable capture in this file — the frame at the
instant a previously unseen enemy is first spotted. What appears (a body, a marker, an alert icon,
nothing until the enemy's own turn), and whether anything at all is drawn for a hostile that has
been heard but not seen, if that state exists here.

## 6. Turn order and time

Alternating, not interleaved: sources describe "player turn" then "enemy turn" as a whole, in the
XCOM shape, with no mention of a shared initiative order or a strip of portraits (*verified*, by
absence across every source that discusses turn structure, plus the tactical-combat guide's advice
to "secure the squad for the enemy turn" as a single block). No source names a banner, a phase
indicator, or anything shown to the player while the enemy side is acting. This is itself a finding:
if the game shows nothing during the opposing turn, that is a data point the onboarding brief's
alternating-banner precedent (XCOM's "Enemy Turn" card) would want confirmed or denied, not assumed.

**What a picture would settle:** a frame from the moment control passes to the enemy side — banner,
dimmed input, or nothing at all.

## 7. Reactions

Overwatch is cone-based and, per `conventions.md`'s own section on this game, spends the operator's
entire remaining action-point balance to declare — all-or-nothing where Hexcom's bank is graded.
Independent sources here corroborate the shape without contradicting it: overwatch is "claiming a
zone of fire," triggers "when enemies move through the designated fire zone" (*verified*, Cover and
Overwatch Guide), and can be laid more than once per squad since "two overwatch shots can fail to
stop a moving enemy, so layer your coverage" (*verified*, same source) — implying multiple
soldiers' cones stack independently rather than one shared reaction economy. No source describes
what happens on screen at the moment a cone fires: no camera-cut, no tick clock, no visible
countdown analogous to Hexcom's reaction window.

**What a picture would settle:** a clip of an overwatch cone actually firing — camera behaviour (cut
to the shooter, or none), what if anything marks the trigger point on the ground, and how the cone
itself is drawn while idle versus at the instant it resolves.

## 8. Camera and input

A free, not stepped, camera: "a 3-D isometric view which you can rotate 360 degrees" (*verified*,
GeekDad), with multiple floors modelled for structures and play that moves across rooftops
(*verified*, GeekDad; corroborated by a beginner-guide mission description of "moving across the
rooftop... eventually pushing inside the palace"). This makes Warhounds a second shipped example
alongside Jagged Alliance 3 of the free-yaw camera `conventions.md`'s own recommendation already
argues for — the canon's stepped-camera default is not the newest word on this even within its own
genre.

No source publishes a default keybind list; the controls guide explicitly declines to, instead
naming remap *categories* — select/confirm, cancel/back, camera move/rotate/zoom, next/previous
unit, overwatch/denial, end turn, ability shortcuts (*verified*, PC Controls Guide) — and directs a
player to the in-game remapper instead. Keyboard and mouse are called "the reliable baseline... at
launch," with controller and Steam Deck support described as still maturing post-release
(*verified*, same source).

**What a picture would settle:** the in-game Options → Controls screen itself, which would turn
every one of those named categories into an actual key. Separately, a clip of the camera mid-
rotation would settle whether it animates smoothly or steps despite being freely aimable.

## 9. Confirmation and refusal

The only in-mission confirmation behaviour any source names is the aim-preview cancel described
under heading 2: back out of a shot or ability before it fires, at no cost. Nothing describes a
second-click confirmation on anything, a warning drawn on a risky action, or a move the game refuses
to let a player make. The more interesting refusal mechanism found sits one level up, at the save
system rather than the turn: three save modes exist — free saving outside the opening missions,
checkpoint-only (mission start and finish), and Ironman with "one save updated each turn"
(*verified*, FAQ: Saves, Mods, Cheats). Ironman is the genre's usual answer to *the player must live
with a bad turn*, done entirely outside the tactical UI rather than as an in-mission undo block.

**What a picture would settle:** whether anything at all warns before a committed action a player
cannot take back — the concealment-ring equivalent this game may or may not have. A clip of a shot
fired that breaks something unintended (the barrel-explosion or ally-in-the-line case from heading
3) would show whether the game warns first or only shows consequences after.

## 10. What the game hides, and what its players added

No official mod tools, Steam Workshop, or developer console exist as of the sources checked
(8 September 2026); community modding is limited to file edits, and third-party trainers (Cheat
Happens live, WeMod listed as coming soon) exist unaffiliated with the developer (*verified*, FAQ).
Official modding tools are stated as planned "around the game's first anniversary" (*verified*,
same page) — roughly a year past what this file can check now. Two patches are named: 1.0.1 touched
gamepad layout, and a later patch added Simplified Chinese localisation alongside unspecified "UI
fixes" (*verified*, FAQ page's version history) — the detail of which fixes is not itemised anywhere
found.

**What a picture would settle:** the patch notes themselves, in full, for what "UI fixes" turned out
to mean — the nearest this game has to the mod-download record job 1 uses for XCOM 2, at a fraction
of the size.

---

## What transfers

- **The reserve is all-or-nothing here, confirmed independently of `conventions.md`'s own citation**
  — bears on that file's *Points, and the reserve* section, which already uses this game as the one
  shipped comparison for a graded bank; nothing found here weakens that reading.
- **Per-projectile transparent hit chance (100/90/80-style) is a second shape for "the arithmetic
  behind the number," distinct from XCOM's single hover-to-expand figure** — bears on *Readouts*:
  a genre example that shows several numbers at once by design, worth weighing against "headline at
  the thing, breakdown on demand" as brief one is written.
- **A free 360° camera with modelled floors, shipped in 2026** — bears on *The camera* section,
  which cites Jagged Alliance 3 and Silent Storm for the same case; this is a third and more recent
  one.
- **Alternating whole-side turns with no reported on-screen indicator for the opposing turn** —
  bears on *Turn order and whose go it is* and on the onboarding brief's banner precedent; if
  confirmed empty, it is a data point against assuming every alternating game marks the handover.
- **Movement range coded by which action point pays for a tile, not by a single reachable/
  unreachable boundary** — bears on *The tile*, as an example of a second axis (which resource, not
  just how far) drawn directly on the ground.

## The gap list

1. **The moment an unseen enemy is first spotted** (heading 5) — a frame at first contact, whatever
   is on screen the instant before and after. Nothing published says whether this game has any
   state between *undetected* and *fully drawn*, and that is the single largest unknown in the file:
   it decides whether Warhounds belongs on the XCOM shelf or has something contact-file-shaped that
   the canon does not.
2. **The attack preview, itemised** (heading 3) — a soldier aiming at a covered target at range, the
   full breakdown panel visible: every named modifier, in order, alongside the per-bullet
   percentages. Settles whether the terms are shown by default or behind a hover, and whether
   Warhounds is a second example for or a counter-example against "one number, expandable."
2b. **Target-cycling** (heading 3) — a clip of switching aim between two visible targets without
    releasing the aim mode, to confirm the mechanism exists at all before asking how it orders
    targets.
3. **A tile in each cover state, selected or hovered** (heading 4) — full cover, half cover, open —
   whatever mark (if any) each carries. The Cover and Overwatch Guide says this is undocumented even
   by the community, so a single capture would out-do every published source at once.
4. **The handover to the enemy turn** (heading 6) — one frame at the instant control passes. Settles
   whether a banner, a dimmed screen, or nothing marks it, which the onboarding brief's XCOM
   precedent assumes without this game confirming or denying it.
5. **An overwatch cone firing** (heading 7) — a clip from cone placement through to the shot landing.
   Settles camera behaviour (cut or none) and whether the trigger point is marked on the ground,
   which the Hexcom reaction window's own camera-cut behaviour has no shipped company for yet
   without it.
6. **The ability bar, mid-hover** (heading 2) — a soldier selected, the bar on screen, cursor over
   one entry. Settles where it sits, what a hover reveals, and whether it resembles the canon's
   bottom-row shape.
7. **A miss that hits something else** (heading 3 / 9) — a clip where a missed shot's continued
   trajectory strikes a barrel, an enemy, or an ally. Settles whether the preview warns of this risk
   before the trigger is pulled or the consequence is only shown after, which is the difference
   between a *shown-before-committing* figure and a *told-you-so* one.
8. **The Options → Controls screen** (heading 8) — settles every real keybind at once, in place of
   the category names the controls guide gives instead.
9. **A full mid-mission frame with nothing open** (heading 1) — settles the whole of screen
   furniture, which no source addresses directly at all.
10. **The patch notes for the "UI fixes" patch, in full** (heading 10) — a still cannot do this; the
    text itself would do it, and it is the nearest thing this game has to job 1's modding record.
