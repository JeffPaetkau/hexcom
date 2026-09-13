# The capture list — one ranked sitting, not eighty-nine questions

The ten reference files under [reference/](reference/) end with 89 gap questions, each ranked
inside its own file and against nothing else. This is the one list they collapse into, ranked
across all ten by **what a picture would change** — not by heading, not by game, and not by how
interesting the question is.

Read [../subprojects/interface.md](../subprojects/interface.md) for the inbox and the shots
mechanism before capturing anything. In short: drop results in `reference-inbox/<game>/` at the
repository root, and curated crops land in `reference/shots/<game>/` named for what they show.

**How this is ranked, so a disagreement with the order is checkable.**

1. **Would the answer flip a recommendation, or only confirm one?** A flip outranks a confirmation
   every time, and the top of this list is questions where `conventions.md` currently commits to
   something a picture could overturn.
2. **Is it reachable?** Five of the ten games can be played — XCOM 2, Invisible Inc., Warhounds,
   Phantom Brigade, Future War Tactics. A question about one of those outranks an equally
   important one about a game nobody can photograph, because an answer is worth more than a wish.
3. **How early does the thing it changes get built?** Brief one is first in the queue, so a
   question that decides a brief-one gesture outranks one that sharpens brief six.

**The cut line is after C12.** Everything above it would change something. Everything below it
would confirm something, and confirmation is worth having but not worth a sitting.

**Pass two has run against the twelve above the line. Eight are answered, two half answered, one
not answered, and C8 was not capturable.** Four answers contradicted something the set had
written: C1, C5, C10 and C12. Three of them move a recommendation (C1, C5, C12), which is the
outcome this list was ranked to find. C10 contradicted its reference file and confirmed the
recommendation that cited it. Entry 089 has them. Each entry below says in its first line what came back. A struck heading
was answered or ruled out; an unstruck one is still open, in whole or in part. **For a clip,** the
moments were found on a low-resolution contact sheet and then read from full-resolution frames
pulled at those times. That breaks the letter of *never sample at a fixed rate* only to find where
to look, and every claim cites a full-resolution frame.

**Two ways to answer.** Most entries want a still. Where the finding is a transition — a state
becoming another state, a dwell, a moment of firing — a still cannot settle it and the entry says
**clip**. A clip is read by pulling named frames out of it, never by watching it; the `ffmpeg`
invocation is in `interface.md`.

---

## Above the line — these change a recommendation

### ~~C1 · XCOM 2 · heading 3 · is the shot breakdown open by default, or behind a click?~~
**Answered: open by default.** Entering the aim shows the breakdown open. Each column has its own
chevron that folds it, and the fold is sticky across targets. `reference/xcom2.md` heading 3.

**Playable.** The frame: a soldier the instant after entering targeting mode on a visible target,
before any further click, full HUD in shot. A second frame after clicking the chevron beside
`HIT`, if it does anything.

**Changes:** brief one's gesture for *show me the terms*, which is the first thing View builds.
The brief named *XCOM's hover*, the reference file found a docked list instead, and whether that
list is shown by default or gated is the difference between a genre that discloses the arithmetic
and one that hides it. `conventions.md` currently recommends held-key disclosure and marks the
recommendation **provisional** against this entry. It is first on the list because it is the only
question here that decides how something gets built next week.

### ~~C2 · Invisible, Inc. · heading 4 · all three vision bands, plus the fog memory, in one frame~~
**Answered.** All three bands in one cone, and the fog memory in the same capture. They read apart
in a native-resolution crop; in the full frame the two reds merge. `reference/invisible-inc.md`
heading 4.

**Playable.** One frame around a single guard with watched (dark red), noticed (light red) and
hidden (yellow) all present, and ideally a seen-but-not-currently-visible area in the same shot.

**Changes:** the only shipped exemplar for a graded per-tile exposure field, which is what this
game already paints. Four visual states described by four separate sources have never been seen
against each other, and the game's own designers shipped an alternate *reduced walls* mode
because they treated the default as a legibility compromise. If striped shading at three levels
is genuinely hard to read — and another designer's published critique says it is — then this
game's graded attention tint inherits the problem and brief one has to answer it rather than
discover it.

### ~~C3 · Invisible, Inc. · heading 5 · the investigating and alerted badges, close enough to read~~
**Answered.** A yellow `?` triangle and a red `!` triangle over the body. At the interest point, a
yellow shield-shaped `?` stands on a corner-bracketed tile. `reference/invisible-inc.md` heading 5.

**Playable.** Two frames: a guard investigating (the yellow `?` triangle, and the separate
floating `?` at the point it is walking to) and a guard alerted (the red `!` triangle). Crop
close.

**Changes:** brief two's *noticed* mark, which `conventions.md` recommends as the one real
borrowing available for a state short of seen. Two games converge on the idea; nobody has looked
at either drawing. The second `?` at the interest point is the detail most worth having, because
it is the same object as this game's marker — a glyph at a place somebody believes in — and no
other game in the set draws one.

### ~~C4 · Warhounds · heading 7 · the overwatch cone, idle and firing~~
**Answered.** Entered from the action bar; `Brings out of cover` drawn at the cursor while placing;
the idle sector drawn as tinted grid tiles; on firing, no camera cut and no trigger point on the
ground. `reference/warhounds.md` heading 7.

**Playable.** A clip from cone placement through to the shot landing, plus one still of the cone
sitting idle on the ground.

**Changes:** everything in *Points, and the reserve*, which is built on the one shipped game with
a comparable bank and is flagged **read, not played** in entry 067. It also settles half of the
newly corrected Reactions finding: two games draw the player's own held arc, and this is the one
whose bank works most like ours. Whether the cone marks its trigger point on the ground, and
whether the camera cuts to the shooter, are both unanswered anywhere in ten games.

### ~~C5 · Warhounds · heading 3 · the attack preview, itemised~~
**Answered, and it contradicts the file.** Open by default in attack mode: one figure,
`PRECISION 17%`, with its terms itemised in a panel docked at the right edge, and no per-bullet
percentage anywhere. `reference/warhounds.md` heading 3.

**Playable.** A soldier aiming at a covered target at range, the full breakdown panel in frame:
every named term in the order it is listed, alongside the per-bullet percentages.

**Changes:** brief one's headline-and-breakdown decision from the opposite direction to C1. This
is the set's only game that shows several numbers at once by design, on a deliberate transparency
pitch, and `conventions.md` now cites it as the counter-case to a folded single figure. Whether
the terms are shown by default or behind a gesture is the same question as C1 with a different
answer available.

### C6 · Warhounds · heading 5 · the instant an unseen enemy is first spotted
**Half answered.** Only the after frame was captured: an `ATTENTION!` banner reading `Enemy squad
detected`, and the enemies drawn as bodies with health bars. The before frame and any heard-but-
unseen state are still open. It does confirm the law's tenth case on the fog side.
`reference/warhounds.md` heading 5.

**Playable.** The frame before and the frame after first contact, full screen. And separately,
anything at all drawn for a hostile heard but not seen, if that state exists.

**Changes:** whether *zero of ten games carry a belief about an enemy that can be wrong* is exactly
right or only nine-tenths right. Warhounds is the one file whose enemy heading came back as a
genuine unknown rather than a confirmed absence, and it is the newest game in the set. It also
completes the no-undo law in `conventions.md`, whose tenth case is unconfirmed only on the fog
side.

### ~~C7 · Invisible, Inc. · heading 6 · one full corporate turn, end to end~~
**Answered.** An `ENEMY ACTIVITY` banner up for at least 1.43 s with the HUD hidden, a red backdrop
tint for the rest of the phase, a camera that never moves, an `AGENT ACTIVITY` banner, and input
back at 5.0 s. One indicator for the phase. `reference/invisible-inc.md` heading 6.

**Playable. Clip.** From the frame the player's input stops to the frame it returns.

**Changes:** entry 065's banner, which was decided with no shipped precedent to check against.
What the closest relative in existence does while the player has no input — whether the camera
follows guards, whether anything names the phase, whether it is silent until something perceptible
happens — is undocumented, and this game's own decision is *one indicator per contiguous stretch*.
Also the only chance in the set to see what a turn-based stealth game shows when a guard the
player has not found takes its turn.

### ~~C8 · XCOM 2 · heading 4 and 9 · Gotcha Again's tile icons, on the tile~~
**Not capturable from the user's copy, and struck as that rather than as answered.** The GOG build
cannot load Workshop mods (entry 088). Brief four's glyph vocabulary stays provisional. Published
screenshots could settle it at the grade *verified*, never *observed*.

**Playable, with the mod installed.** A destination tile hovered in each of the mod's situations
it can reach: the red reticle for a shootable enemy, the yellow for a flanked one, the reticle
added to an enemy's own overwatch icon with the marker on the tile that would spring it.

**Changes:** brief four's drawing, not its case — the case is made by 272,071 subscribers. What is
worth seeing is the *vocabulary*: a community solved this exact problem with a small set of glyphs
on the destination tile, and the shapes it chose are free evidence about what reads at a glance
and what does not.

### C9 · Phantom Brigade · heading 3 · the `Ctrl`-held breakdown, in full
**Half answered.** Without Ctrl, the target already carries `100%`, `Optimal` over `2X Crit - 15%`,
and a `Predicted damage` line. The one Ctrl effect on film reveals every unit's badge at once. The
split and the scatter cone are in no frame. `reference/phantom-brigade.md` heading 3.

**Playable.** The targeting widget with `Ctrl` held, both split numbers and the scatter cone
visible at once.

**Changes:** whether a breakdown actually repairs a folded number's misreading. This game's own
players argue in public about its headline figure as though it were a hit chance, which it is not,
and the breakdown that should settle it exists. If players still misread the headline with the
breakdown one key away, then *headline at the thing, breakdown on demand* has a failure mode that
brief one has to design against rather than rely on.

### ~~C10 · Future War Tactics · heading 4 · the colour-coded zones, mid-planning~~
**Answered, and it contradicts the file.** Two nested outlines on square tiles and no tint. It is
banded, not graded. `reference/future-war-tactics.md` heading 4.

**Playable.** A soldier selected mid-move-planning with the whole walkable area and its outer
edge in frame.

**Changes:** whether this game is a banded system like the rest of the genre or a graded field like
this project's, which is the one thing it is in the reference set for and the one thing no
screenshot caught. It bears directly on the largest recommendation the synthesis changed — that
the reserve's cliffs belong on the move range, cut at thresholds rather than at whole action
points — because a graded field cannot show a cliff and this is the set's only candidate for one.

### C11 · Phantom Brigade · heading 4 · the optimal-range ring and the falloff graph, composed
**Not answered.** The frame caught the destination mode and enemy fire drawn as red wedges on the
ground, not the ring and the graph together. `reference/phantom-brigade.md` heading 4.

**Playable.** One frame with both on screen at once, against a partly destroyed piece of cover.

**Changes:** brief one's whole premise at the point where it is most likely to break. Every figure
in this project's panel is about to become a spatial readout, and composition — two overlays and a
world-space ring in the same frame — is exactly where a spatial readout either holds together or
turns into clutter. This is the only game in the set that draws a range band and a falloff graph
simultaneously, and nobody has seen them together.

### ~~C12 · Future War Tactics · heading 5 · a contact that has just broken line of sight~~
**Answered, and it contradicts the set's emptiest heading.** A red beacon stands where each lost
enemy was last seen, and it is still up on the next turn. `reference/future-war-tactics.md`
heading 5; entry 089.

**Playable.** The turn after a previously seen enemy leaves sight, HUD exactly as the player sees
it, nothing cleared or re-framed.

**Changes:** the tenth data point on the emptiest heading in the set. Nine files have looked for a
persisted contact and found nothing; this is the last game where the question is open rather than
answered, and a tenth confirmation is what turns *no game in the set* into a claim that can carry
brief two's stakes.

---

## Below the line — these confirm, and several cannot be captured at all

**C13 · Shadow Tactics · heading 5 · one guard mid-detection, head and cone both in frame.** Not
playable. Confirms the correction `conventions.md` has already made — the fill is on the cone and
there is no head gauge. Ranked here rather than higher because the reference file's `verified`
sources already carry it and a picture would only close the loop.

**C14 · Phoenix Point · heading 7 · the overwatch cone being adjusted before confirming.** Not
playable. Would upgrade the set's one `verified` precedent for drawing a held arc, and would show
whether `Ctrl`+scroll previews live or steps. Bears on the adjust step `conventions.md` now
recommends adding to `HoldArc`.

**C15 · Phoenix Point · heading 5 · the *Alerted* popup's duration and position.** Not playable.
**Clip.** Would settle whether the shipped failure behind *persistent, not announced* is a
sub-second miss or an attention problem. The requirement does not depend on which.

**C16 · Mutant Year Zero · heading 7 · a move that springs an enemy overwatch, full HUD.** Not
playable. **Clip.** The set's zero-telegraph extreme, and the only chance to see what a reaction
firing looks like when nothing was drawn beforehand. Ranked below the line only because the
finding — nothing is telegraphed — is already `verified` from the developers' own forum answer.

**C17 · Into the Breach · heading 6 · one full hostile phase, banner in and banner out.** Not
playable. **Clip.** Would give entry 065's minimum dwell a measured figure instead of an argued
range, and would settle whether the blacked screen corners in the one existing screenshot are
deliberate.

**C18 · Tactical Breach Wizards · heading 6 · the end-turn hover order preview.** Not playable.
Confirms the third answer to turn order that `conventions.md` now records but cannot take, and
would show whether it is a strip that appears on demand or something with no relation to one.

**C19 · XCOM 2 · heading 1 · the squad portrait strip at minimum and maximum squad size.**
Playable, and it only confirms — whether brief one's own soldier strip needs an overflow
affordance from the start or can add one later.

**C20 · Warhounds · heading 8 · the Options → Controls screen.** Playable, one frame, and it turns
every remap category the community guide names into an actual key. Cheap, and it would let the
camera and gesture sections cite a second modern bind list rather than one.

**Not on this list at all, and deliberately.** Every question in the ten gap lists about a mod's
changelog, a subscriber count, a patch note or a Nexus listing. Those are research tasks and not
photographs, and putting them in a capture list would waste a sitting on things a browser settles
in a minute. They stay in their own files' gap lists, where the next research pass will find them.
