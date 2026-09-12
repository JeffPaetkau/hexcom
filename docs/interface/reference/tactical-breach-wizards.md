# Tactical Breach Wizards — reference file, pass one (documentary)

Job 10 of 10 in [../../subprojects/interface.md](../../subprojects/interface.md). Published
material only; no screenshot has been captured against this file yet.

**What this game is the authority on.** Removing the genre's uncertainty rather than dressing it
up: Tactical Breach Wizards (Suspicious Developments, 2024) has no miss chance and no random
damage at all, and its designer, Tom Francis, has said in interviews that this was a direct answer
to what he found frustrating in XCOM 2. Its second contribution is the *seer* — a party member
whose fiction is "can see one second into the future," which is the diegetic excuse for a rewind
that costs nothing and can be used as many times as a player likes before a turn is locked in. And
its enemies telegraph their intended target with a laser sight during the player's own turn, which
is the closest thing in the set to Into the Breach's shown-intent played out through vision rather
than through a fixed marker.

**What it is only an instance of.** The action bar, the single move-plus-action economy, cover
that blocks a shot outright, and an isometric camera are the tactics canon's furniture and this
game does not depart from any of it in a way that is documented anywhere found. And it has no
contact file, no fog of war, and — as far as this pass could establish — no persistent detection
meter: it appears to inherit XCOM: Chimera Squad's breach-and-clear structure, where a room's
occupants are known the moment the door goes in rather than found gradually. That makes it, for
heading 5 specifically, closer kin to the older tactics canon than to the stealth shelf, despite
being the newest game in the set.

## Tags

| | |
|---|---|
| **observed** | not available in this pass |
| **verified** | a published source, linked in Sources below |
| **remembered** | model knowledge, unchecked against a source this pass could load |
| **inferred** | drawn from another claim in this file, which it names |

Several sources that should carry the best evidence here — the Fandom wiki, Neoseeker's mechanics
pages, the in-game-controls video, TV Tropes — returned an access error to this session's fetch
tool on every attempt (403 or 402). What follows leans harder on games-press review text and
Steam discussion threads than the file would like, and the gap list below says so per heading
rather than once at the top.

## Sources

- [PCGamesN — "Tactical Breach Wizards is an indie XCOM that strips away the uncertainty"](https://www.pcgamesn.com/tactical-breach-wizards/xcom) — Tom Francis interview: no dice, the seer's fiction, Into the Breach comparison
- [Barrel Drill — Tactical Breach Wizards review](https://www.barreldrill.com/tactical-breach-wizards-review/) — action economy, laser-sight telegraph, rewind, upgrade screen
- [Console Creatures — Tactical Breach Wizards review](https://www.consolecreatures.com/review-tactical-breach-wizards/) — cover and line of sight, Dall's vision-blocking Riot Block
- [The Gamer — "The Best Beginner Tips In Tactical Breach Wizards"](https://www.thegamer.com/tactical-breach-wizards-best-beginner-tips/) — action economy, aim lines, end-turn-button turn-order hover
- [Wikipedia — Tactical Breach Wizards](https://en.wikipedia.org/wiki/Tactical_Breach_Wizards) — squad size, seer, rewind window, objectives and confidence
- [Steam Community discussion — "Turning camera and controls in general"](https://steamcommunity.com/app/1043810/discussions/0/4515507184334768512/) — camera binds and their complaints
- [Turn Based Lovers — "Breach, Spell, Repeat: Chimera Squad-Like Tactical Breach Wizards Review"](https://turnbasedlovers.com/review/breach-spell-repeat-chimera-squad-like-tactical-breach-wizards-review/) — the Chimera Squad comparison this file leans on for heading 5

**Not found, and worth naming because a future session may waste time retrying them:** the Fandom
wiki (`tactical-breach-wizards.fandom.com`, 403), Neoseeker's Basic Mechanics and Perks pages
(403), TV Tropes (403 direct and through a reader proxy), PC Gamer's interview piece and review
(fetched as membership-wall stubs with the article body stripped), GameSpot and TechRaptor
reviews (403), the official controls video (not fetchable — video).

## Nothing found

Nothing under headings 1 through 9. Every one has at least a remembered or verified claim. What
is genuinely absent from the game rather than from this pass's sources is called out inside the
relevant heading instead — no reaction *stance* the way Reactions in `conventions.md` means it, no
fog of war, no contact file.

---

## 1. Screen furniture

Ability icons sit along the left edge of the screen for the selected soldier — reported
consistently enough across summarised guide pages to treat as **remembered**, but this pass could
not load a page that showed rather than described it, so it is not **verified**. A bar of
turn-control buttons along the bottom includes end turn, and — see heading 6 — end turn doubles as
a hover target that previews the enemy turn order **(verified** — The Gamer). Health bars are
drawn over each unit's head or body and carry a damage preview once a shot is aimed: guide
summaries describe a bar with a yellow segment for guaranteed damage and a skull icon for a sure
kill, a cracked skull for overkill, but the source for this (Neoseeker, a maxutmost review) could
not be loaded directly, so it is **remembered** rather than **verified** — flagged below.

No morale, panic, or squad-wide alarm meter is drawn during a mission in anything read for this
file; "confidence" is a between-mission currency for cosmetic unlocks, earned by clearing optional
objectives, and is not drawn on the battlefield HUD at all **(verified** — Wikipedia, The Gamer).

**What a picture would settle.** A full-screen shot at the moment a soldier is selected mid-turn,
with the ability bar, a health bar mid-target, and the end-turn button all in frame, would settle
the layout this heading can currently only describe.

## 2. The soldier

The default economy is one move and one action point per turn per soldier, and this is spent, not
banked or graded — there is nothing here resembling the reserve of `conventions.md`'s ninth
section **(verified** — Barrel Drill: "your heroes can walk once and spend a single action point
on their base attacks/powers"). Several abilities are reported as not costing that action point at
all, letting a soldier "shoot and move in whichever order works best" **(verified** — The Gamer),
which reads as a per-ability exception on the cost side rather than a second pocket of points.

There is no separate "cancel" gesture found anywhere in this pass. What replaces it structurally is
the rewind: rather than backing out of one half-entered order, a player is reported to redo the
whole turn from any point in it, as many times as they like, until they choose to end it
**(verified** — PCGamesN, Barrel Drill, Wikipedia all agree on this shape independently). Whether
there is additionally a narrower, single-step undo — the equivalent of the genre's right-click
cancel, for backing out of a menu without touching a committed move — is not established by
anything read here.

**What a picture would settle.** A soldier mid-ability-selection, with the bar, a hover tooltip if
one exists, and the cursor over an ability icon, would settle whether a tooltip carries a cost, a
description, both, or neither by default. A short clip of a player opening an ability then
pressing whatever cancels it would settle whether cancel and rewind are the same action or two.

## 3. The target

The headline fact for this heading is an absence: there is no percentage hit chance anywhere in
this game, by design. Tom Francis is on record contrasting this directly with XCOM's dice and
citing Into the Breach's "almost as close to chess... in terms of knowing 100% what everyone's
going to do" as the nearer model **(verified** — PCGamesN). What a shot readout shows instead, per
guide summaries this pass could not load directly, is the damage-preview health bar described
under heading 1: a guaranteed-damage segment and a skull for a kill **(remembered**, flagged).
Whether there is a breakdown of *why* a number is what it is — the equivalent of XCOM's modifier
list behind a hover — was not found stated anywhere, positively or negatively.

Target switching: not established. Nothing read names a key or a gesture for cycling between
targets when more than one is in range of an ability.

**What a picture would settle.** A shot lined up on a target with the full readout on screen,
including whatever is shown for a graze, a non-lethal hit, and a guaranteed kill side by side (three
separate crops, since the state changes with the target), would settle both open questions in this
heading at once. It is also exactly the kind of thing a still cannot fully settle if any element of
it animates on aim — a short clip covering the moment a cursor moves from a full-health target to
a near-dead one would catch a transition a screenshot would miss.

## 4. The tile

Cover is binary and absolute rather than a modifier: "any barrier above waist height will
completely block attacks in both directions," shown as "yellow aim lines" that stop dead at the
barrier **(verified** — Console Creatures, corroborated independently by The Gamer's beginner
guide). This is a harder rule than anything in `conventions.md`'s Readouts section describes for
this project — cover here is not a percentage penalty, it is a wall between a line and its target,
full stop, in both directions. At least one soldier ability (Dall's Riot Block, upgraded) can
create or extend this blocking effect deliberately **(verified** — Console Creatures), which
means the aim line is not only a readout of the map but sometimes a readout of a decision just
taken.

Movement range and its preview, band by band: not established by anything read. No source
described whether reachable tiles are tinted, banded by cost, or simply implied by a path preview
on hover.

No concealment or detection ring of any kind is described anywhere in this pass, which is
consistent with the "nothing found" note on fog of war under heading 5 — there is nothing here for
a ring to gate.

**What a picture would settle.** A soldier with a full movement budget, hovering a tile at roughly
half that range, with the path drawn — this settles whether range is banded, tinted, or a bare
outline, none of which this file can currently distinguish.

## 5. The enemy

This is the heading where this game answers *unlike* the genre's other member closest to us in
subject. There is no fog of war, no suspected-but-unconfirmed contact, and no marker for an enemy
last seen somewhere it has since left — nothing read across seven reviews and two guide sites
mentions anything of the kind, and one review frames the whole game as "Chimera Squad-like"
**(verified** — Turn Based Lovers), which is the tactics-canon shelf's own answer to *breach and
clear*: a room's occupants are established the moment the door goes in, not discovered gradually
the way Invisible, Inc.'s or this project's own contact file works. An enemy is either in line of
sight — in which case it is drawn exactly, full stop, the same rule as cover under heading 4 — or
it is not drawn at all, with nothing standing in for what it might be doing meanwhile.

**What of the enemy is telegraphed** is real and is the game's second-best-known feature: enemies
that are able to act point a laser sight at whoever they would shoot if the turn ended now, visible
during the player's own turn and updating as the plan changes **(verified** — Barrel Drill,
corroborated by a second review's complaint that five crossing sights become hard to read at once).
At least one enemy type, described as a "tracker," is reported to acquire and follow a specific
soldier across their move and fire only if it still has line of sight at the end of it
**(remembered**, one search-summary source, not independently loaded). Alert states in the sense
`conventions.md` means them — a ladder with rungs, `Unaware` through `Engaged` — were not found
anywhere; whether an enemy simply is or is not aware, with nothing graded between, is a plausible
guess from the breach-and-clear framing but is an inference, not a finding, and is exactly the
sort of thing this pass's own rule says must be flagged rather than assumed.

**What a picture would settle.** A room mid-plan with at least two crossing laser sights and the
soldiers they are aimed at both in frame would settle how legible the telegraph actually is — one
review's complaint suggests the honest answer may be *not very*, at higher enemy counts, which
is itself worth knowing. Separately: any single frame from the first few seconds of a level, before
the first action is taken, would settle whether "breach" shows every occupant of a room at once or
staggers them in — this is the one item on this list a still can answer and this pass had no
access to a clip or a let's-play frame to check it against.

## 6. Turn order and time

There is no persistent order strip. Hovering the end-turn button reveals the order enemies will
act, described as becoming load-bearing once a third squad member with an order-sensitive ability
is unlocked, and non-human actors (turrets) or magically-quickened enemies are reported to act
first in that order **(verified** — The Gamer). This is a gesture-revealed order rather than an
always-on readout, which is a genuinely different answer from every strip-drawing game in
`conventions.md`'s Turn order section — those all commit to the strip being visible continuously,
because their order is durable for the round; this game's order preview is requested on demand,
which fits a design where the player is expected to be replanning constantly rather than reading a
fixed schedule once per round.

What the player is shown while enemies act, and whether a whole-side turn has a phase banner the
way the alternating shelf's games do: not established. Given the rewind mechanic replaces most of
what a phase boundary would otherwise need to communicate — the player already knows exactly what
is about to happen before committing — a banner may be unnecessary here in a way it is not
elsewhere, but that is reasoning forward from the mechanic, not something any source states.

**What a picture would settle.** A screenshot with the cursor hovering the end-turn button and
the resulting order preview both visible would settle what that preview actually looks like — a
list, a set of highlighted portraits, numbers on the enemies themselves. A clip of an enemy turn
resolving, start to finish, would settle whether anything marks the phase at all.

## 7. Reactions

There is no universal reaction stance comparable to overwatch, and nothing resembling this
project's banked reserve. What exists instead is per-character, per-ability: one ability
("Predictive Bolt," attributed to a character named Zan in guide summaries) is described as
setting up a zone such that the first enemy to enter it, in either side's turn, takes damage, and
a second ("Shield Bash," attributed to a character named Sterling) is described as triggering
during the enemy's turn for a free knockback. Neither of these claims could be corroborated by a
directly-loaded source — they surfaced only in a search engine's own summary of guide pages this
session could not fetch — so both are **remembered** and flagged, not **verified**. If accurate,
the shape is notable regardless: a "reaction" here is a named ability a specific soldier owns and
must have equipped, not a state any soldier can enter by spending a point, which is a real
departure from every game in `conventions.md`'s Reactions section, all of which treat overwatch as
a generic action available to whoever wants it.

**What a picture would settle.** Nothing here is well enough established even to know what to
photograph. A clip of a Predictive Bolt zone triggering on an enemy's move, if the ability is
correctly named, would be the minimum to move this heading from remembered to verified.

## 8. Camera and input

The camera rotates on a right-mouse-button drag; WASD is reported as an alternative for panning.
Players in a Steam discussion asked for `Q`/`E` stepped rotation and reported it does not exist —
the request itself, and the absence, both **verified** by that thread directly. This is the
opposite gap from this project's own history: `conventions.md`'s Camera section describes the
genre defaulting to a *stepped* camera and free rotation being the newer, better-liked departure;
this game shipped free-drag-only with no step at all, and its own players are asking for the step
back, for exactly the reason the genre's older games had one — a controller-friendly, discrete turn
of the view. Zoom, pitch limits, and edge-pan were not established by anything read.

The mission editor is reported to include a "Floor Hole" tile and multi-level room layouts with
windows on different floors **(remembered**, search-summary sourced), but nothing found describes
how the camera or the HUD handles a second storey — whether it is drawn transparently, cut away, or
simply visible from the isometric angle without any special handling at all.

**What a picture would settle.** A clip of a right-drag rotation in progress would settle the
speed argument the same way `conventions.md`'s own camera section already flags as unmeasured
elsewhere. A screenshot of a multi-floor room would settle the storey question outright — this is
a still question, not a clip one.

## 9. Confirmation and refusal

The clearest finding in this heading is structural rather than a specific dialogue: this game
appears to use *rewind* as its confirmation mechanism, in place of the confirm-the-shot click every
other game in `conventions.md`'s Selecting and ordering section uses. Because a player can undo
anything up to the moment they end their turn, nothing needs a modal "are you sure" — the recourse
for a bad decision is to rewind it, not to have been warned in advance. Ending the turn itself is
reported to carry "a little warning first" before it commits **(remembered**, one uncorroborated
search summary, flagged), which — if accurate — is the one moment in the whole turn that is not
trivially reversible, since a mistake there hands the state to the enemy's own turn.

Window-kills are reported as instant and bypass a target's remaining health and armour outright
**(remembered**, search-summary sourced, corroborated in general shape by the achievements-guide
title but not read directly). Whether that irreversibility is flagged to the player before the
throw — the equivalent of this project's own shown-before-committing rule for a move into an
unseen arc — is not established either way.

**What a picture would settle.** A clip of a player attempting to end a turn with an unresolved
telegraphed shot against them, if such a warning exists, would settle both what it looks like and
what triggers it. A clip of a window-kill being set up and thrown would settle whether anything on
screen marks it as the irreversible, armour-bypassing move guide pages describe.

## 10. What the game hides, and what its players added

The between-mission "confidence" currency and its cosmetic outfit unlocks are the one system found
that lives entirely outside the tactical HUD — a meta-progression screen described as a "witchcraft
bench" **(verified** — Barrel Drill), which this file has not otherwise touched because it is not
part of the battle interface this territory is scoped to. The Steam Deck and camera-control
discussion threads are themselves the community record this heading exists to catch: multiple
players independently ask for stepped `Q`/`E` camera rotation and for end-turn to be rebindable to
space, neither of which is reported as shipped. No fan-made UI mod, accessibility patch, or
community fix comparable to XCOM 2's Nexus mod scene turned up in anything searched — the game is
recent enough, and small enough in scope, that this may simply not exist yet rather than have been
missed.

**What a picture would settle.** Nothing photographable — this heading's finding is about what is
absent from the discourse, not about a frame. The one thing worth checking that a clip could
settle is whether an in-game accessibility or settings menu exposes anything (camera speed,
colour-blind palettes for the aim lines and health-bar skull icons) that the discussion threads
found insufficient. A screenshot of the settings menu, full page, would settle that outright.

---

## What transfers

- **Heading 3's absence of a hit chance is the loudest single fact in this file**, and it bears on
  `conventions.md`'s Readouts section from the opposite direction every other game in the set does:
  where the rest debate *where* to put the arithmetic, this game is evidence that a tactics
  interface can work with none to put anywhere. Not a recommendation for this project — contract 3
  and the exposure/alarm split give this game reasons XCOM never had to keep numbers — but worth
  the synthesis pass weighing, since brief one is entirely about placement and assumes a number
  exists to place.
- **Heading 4's binary cover — a wall either blocks a shot completely or it does not — is worth
  the synthesis pass reading against `GunneryModel`'s graded cover penalty.** This project's cover
  is a modifier; this game's is a gate. The two are not directly comparable rules, but the *readout*
  question survives the difference: a binary rule is exactly the kind that benefits most from being
  drawn as a line that visibly stops, which is brief one's placement argument in its strongest form.
- **Heading 5's finding — this is the newest game in the set and it still has no contact file — is
  evidence for the synthesis's expected split, not against it.** It confirms the tactics canon and
  the stealth shelf are still two different lineages as of 2024, and that breach-and-clear (Chimera
  Squad, and now this) is a third answer distinct from both: everyone visible, nobody hidden,
  nothing remembered. Brief two has no ancestor here either.
- **Heading 6's on-demand turn-order preview, rather than a persistent strip, is a genuine third
  answer** next to this project's own dropped-slot departure (brief five) and the alternating
  shelf's whole-side banner. Worth naming to the synthesis specifically because brief five's
  argument was about what a slot *reveals*; this game reveals the same information but only on
  request, which is a cheaper way to withhold nothing while still not shouting it.
- **Heading 7's per-ability, character-owned reactions — if the two examples here are real — are a
  useful negative case for brief six.** Brief six's default-answer proposal assumes a reaction is a
  generic window any soldier can enter; a design where "reaction" is instead a specific equipped
  ability suggests the alternative this project is not taking, and is worth one line in the
  synthesis saying why not, since the reasons (a shared `ReactionWindow.Appraise` that has to score
  arbitrary combinations of soldiers) are particular to this project rather than obviously superior.
- **Heading 9's rewind-as-confirmation is the most structurally different answer in the set to
  Selecting and ordering's no-undo convention**, and it is a genre answer this project's own fog
  rules out for the reason `conventions.md` already gives: a rewind here costs nothing because
  nothing was hidden from the player when they made the choice. The synthesis need not re-argue
  this — entry 058 already settled that softening the no-undo rule is the wrong move for a fogged
  game — but a one-line note that this game's rewind is *enabled by* its lack of fog, not
  independent of it, would keep a future session from citing it as a counter-example out of
  context.

## The gap list

1. **Heading 5 — does a room's occupants appear all at once on breach, or staggered in?** A single
   frame from the first moment of a level, before any action is taken, with every enemy in the
   opening room visible or not. This is the largest open question in the file because it decides
   whether the "no contact file" finding above is exactly right or only mostly right — a staggered
   reveal would be a small, cheap piece of the genre's other shelf this game does have after all.
2. **Heading 3 — what does a shot's readout actually show, term by term?** Three crops of the same
   target at full health, near death, and dead-on-this-hit, with the full readout in frame each
   time. Settles whether the yellow-segment-and-skull description above is accurate at all, which
   the file currently cannot verify from any source it could load.
3. **Heading 7 — do "Predictive Bolt" and "Shield Bash" exist and work as described?** A clip of
   either triggering during an enemy's turn. Everything this file says about per-ability reactions
   rests on an unverified search summary, and the "what transfers" note above about brief six is
   only as good as this being true.
4. **Heading 6 — what does the end-turn hover preview look like?** One screenshot, cursor on the
   button, preview open. Settles whether this is closer to a strip that only appears on demand or
   something with no relation to a strip at all — the two would transfer very differently.
5. **Heading 8 — how fast is the right-drag rotation, and is there any zoom or pitch limit?** A
   short clip of a full rotation. This is the same unmeasured-speed gap `conventions.md`'s own
   Camera section already flags for the project's build, so a number here would be doubly useful.
6. **Heading 4 — is movement range banded, tinted, or an outline?** One screenshot, a soldier
   selected with a partial-range hover. Nothing read anywhere describes this at all.
7. **Heading 9 — is there actually a warning before ending a turn, and what does it warn about?**
   A clip of ending a turn with something telegraphed and unresolved against the player. The
   single source for this claim could not be independently loaded.
8. **Heading 8 — how is a second storey drawn?** One screenshot of a multi-level room from the
   normal play camera. Settles whether verticality is a HUD problem here at all or invisible by
   construction of the isometric angle.
9. **Heading 2 — is there a single-step cancel distinct from full rewind?** A clip of a player
   opening then backing out of one ability without touching an already-committed move. Distinguishes
   a genre-standard cancel from this game having replaced the whole category with rewind.
10. **Heading 9 — is a window-kill flagged as irreversible before it is thrown, or only after?** A
    clip of one being set up. Bears directly on brief four's shot-bill question by analogy: this
    game has its own version of "the player sees the price and not the bill," if the throw is not
    flagged in advance.
