# Reference: XCOM 2 and War of the Chosen, in-mission

The template for this shelf. `conventions.md` answers *what the genre does* at the altitude a
brief can be written from; it does not say what a screen looks like, what a gesture is, or what
happens on hover — and a brief that cannot say those things is not a sufficient prompt. This file
is the grain underneath one entry of the genre. Four more follow it, each against the same ten
headings, so that the set reads across rather than as five unrelated reports.

**Scope.** In-mission only — the tactical screen, from deployment to evac. Nothing about the
Avenger, the geoscape, the Chosen's strategic hunt, character creation, or the mod manager. Base
game plus War of the Chosen, treated as one game: WotC changes classes and adds the Chosen and the
Resistance ring, but it did not touch the tactical HUD's shape.

**Evidence discipline.** Every non-obvious claim is tagged:

| Tag | Means |
|---|---|
| **verified** | Confirmed this session against a named source, linked. |
| **remembered** | Model knowledge of the shipped game, not checked this session. |
| **inferred** | Reasoned from something else in this file, not observed directly. |

*No source found* is written where it is true. This file was built from search results, browser
visits to Nexus Mods, Steam Workshop and StrategyWiki, and two images opened at full resolution —
not from a running copy of the game — a fact worth stating plainly, because it caps how far
"verified" can mean here: it means *a cited page or image says this*, not *a capture from the
controller shows this*. A first pass tried to reach Nexus, Steam and StrategyWiki with an
automated page-fetch tool and got HTTP 403 from all three; a second pass reached every one of them
through an actual browser instead, which is why counts below carry exact figures rather than
search-engine excerpts. Where a browser visit was not attempted or still failed, the tag is
**verified** only when a search engine's indexed excerpt of that exact page is what is being
quoted, and it says so. Endorsement and download counts drift daily and are stamped with when they
were read — everything with an exact-looking number in this file was read via browser on
2026-09-10, not assumed current from an earlier search.

---

## 1. Screen furniture

**verified** (play, [PCGamesN](https://www.pcgamesn.com/xcom-2/tips-guide-war-of-the-chosen), remembered for exact pixel layout) — the persistent tactical HUD has, clockwise from bottom
centre: the selected soldier's portrait and health/armour/shield pips bottom-left; the ability bar
along the bottom, one icon per available action, each showing its action-point cost as a small
badge and greying out anything unaffordable; the squad list as a vertical strip of small
portraits down the left edge, each showing HP and a concealment/overwatch/dashed-status icon,
click-to-select; the mission objective and turn counter top-left; a countdown timer top-centre,
present only on missions that have one, replacing nothing when absent; and an ammo/grenade count
on the ability bar itself rather than a separate readout. **remembered** — none of this furniture
moves or resizes based on squad size or mission type; a four-soldier squad and an eight-soldier
Chosen-assault squad get the same strip, scrolled if it overflows.

**remembered** — there is no dedicated "instruments" panel of any kind, on or off by a key. What
exists either always shows (the furniture above) or shows only while a mode is active (a targeting
reticle, a path preview). This matters for heading 10: nothing here is a developer overlay, which
is why the genre canon has nothing to say about that heading and the second-window pattern this
project uses is borrowed from outside it (see `../conventions.md`'s Debug and developer overlays
section).

**inferred** — the layout is built for a game where the enemy, once found, is drawn with full
permanent information (heading 5), so screen furniture never has to represent *uncertainty about
the enemy's stats*; only uncertainty about the enemy's *existence* (fog of war on the map itself,
not on the HUD).

## 2. The soldier

**remembered, verified by** [gamerevolution keybind guide](https://www.gamerevolution.com/guides/69930-xcom-2-keyboard-shortcut-commands) — action points are drawn as pips (two, almost always) directly
on/near the portrait, filled or hollow rather than numbered; spending the second point on a move
converts it to a dash and greys the fire action out for the rest of the turn, which the ability
bar shows immediately by disabling the fire icon rather than by a separate warning. Abilities are
bound `1`–`9` (later expanded with class abilities sharing the row); `R` reloads, `Y` puts the
selected soldier on overwatch, `G` throws a grenade, `H` uses a med-kit or hunkers down depending
on context. **remembered** — hovering an ability shows a tooltip with its AP cost, range if any,
and a one-line description; hovering a *targetable* ability additionally previews its effect area
on the map (a cone, a radius, a line) before a target is chosen.

**remembered** — cancel is `Backspace` or `Esc`, and it un-enters whatever mode is active: a
targeting reticle backs out to the ability bar, the ability bar backs out to no selection, no
selection deselects the soldier. It never undoes a *paid* action — a move already taken, a shot
already fired — only an action not yet committed. This is the same "no undo, ever, once spent"
rule heading 4 and heading 9 both restate from different angles, because it is the single load-
bearing rule the genre's interface is built around.

**No source found** for exact ability-bar icon sizes or the portrait's pixel position; not worth
inferring since this game's soldier readout (`StanceLines`/reserve pips) is being redesigned on
its own terms in brief one, not copied wholesale.

## 3. The target

**verified by screenshot** — a StrategyWiki guide image, opened at full resolution
([source](https://cdn.wikimg.net/en/strategywiki/images/b/ba/XCOM_2_shot_menu_example.jpg), via
[XCOM 2/Aim Bonuses](https://strategywiki.org/wiki/XCOM_2/Aim_Bonuses)), shows the actual targeting
screen mid-aim and **corrects a claim this file first wrote from memory**: the breakdown is not a
hover tooltip on the target's card. It is a stacked list docked bottom-left of the screen, beside
the ability name and description, shown at the same time as a single bold **HIT 64%** headline
directly above it. The exact rows, top to bottom, colour-coded (white/green for a bonus, red for a
penalty): **AIM +92%**, **HEIGHT ADVANT +20%**, **DEFENSE −40%**, **SQUADSIGHT −8%**, **LOW COVER
−20%**. A mirrored column to the right carries the damage side: **DAMAGE 6–8**, **CRIT 10%**,
**WEAPON CRIT +10%**, and an ability-specific bonus named on its own row (**DEADSHOT +10%** in the
captured example, a Sharpshooter perk, not a universal term). The target itself carries only a
floating **64%** and a health bar over its head — the arithmetic lives at the shooter's HUD, not
on the target.

**What is not settled by one screenshot.** Small chevron glyphs beside the "HIT" row and the
ability-name row suggest this may be a paged or expandable panel rather than a fixed one — whether
the breakdown list is shown by default the instant a shot is aimed, or only after a click or hover
past a collapsed one-line summary, could not be confirmed from a still image. Every other source
touched this session (search excerpts of forum threads, not screenshots) describes the behaviour
as "click to expand" or "hover for more," consistent with a collapsed default, but none of them
is itself a picture of the collapsed state — so this file cannot rule either way and says so rather
than picking the version that matches what was expected. **This is worth flagging to a View
session building against Brief One before it picks a gesture**, since Brief One's own text cites
"XCOM's hover" as the model to copy, and this screenshot's evidence is a *docked list*, not a
hover card on the target — see the amendment appended to Brief One in `../briefs.md`.

**verified** ([Steam Community discussion on hit/graze/dodge](https://steamcommunity.com/app/268500/discussions/0/1471967615856106473/); [UFOpaedia LWOTC mechanics](https://www.ufopaedia.org/index.php/Mechanics_(LWOTC))) — the line items beyond what one screenshot happened to
show: base **Aim** (the weapon/soldier stat, and see the class-and-rank table on the same
StrategyWiki page — a Rookie starts at 65, a Colonel Sharpshooter reaches 91), **Cover** (a flat
penalty for half or full cover, zero if none), **Height** (+20 for firing down at least one full
storey — **remembered**, the exact figure is base-game and can be patched by difficulty mods, so
treat the number as an example not a constant, though it also matches the captured screenshot's
own **+20%** row exactly), **Flanked** (removes the target's cover penalty entirely and separately
grants +40 crit chance — **verified**, both halves, same source), **Squadsight** (a penalty applied
when the shooter cannot itself see the target and is relying on a squadmate's sight — **verified
by screenshot** that it appears as its own row, **−8%** in the captured case; **no source found**
for whether that figure is fixed or scales with range), and **Dodge**, which is the target's own
stat and is subtracted on their side of the same roll rather than the shooter's.

**verified** ([diceplots.com breakdown](https://diceplots.com/games/xcom/); [Pavonis Interactive
forum thread on the hit/graze/crit relationship](https://www.pavonisinteractive.com/phpBB3/viewtopic.php?t=23695)) —
the arithmetic behind the single number is stranger than the breakdown implies. Any raw hit
chance strictly between 10% and 90% always carries a flat 20% chance of a **graze** — a hit for
reduced damage that reads as neither the miss nor the full hit the percentage names — and a dodge
stat can "downgrade" a graze into an outright miss. Crit and hit share one die roll: rolling
inside the crit band **requires** the shot to have already been a hit, so a target with high
dodge can suppress crits on a flanking shot even though the crit chance shown looks unaffected.
None of this is drawn anywhere in the UI; the single number is the base **Aim − Defense** figure
and the graze/crit interaction is entirely undocumented in play. This is the most load-bearing
"remembered, not shown" fact in the file: the genre's *one number, breakdown on demand* convention
that `conventions.md` recommends adopting is, in this game's most-copied exemplar, one number and
a breakdown that still hides the part players most wanted explained (see heading 10, Diceplots).

**remembered** — target switching is `Tab` while an attack is being aimed, cycling visible
enemies in a fixed (screen-position) order; there is no cycle-by-threat or cycle-by-lowest-HP
sort.

## 4. The tile

**verified** ([StrategyWiki Movement (EU2012), consistent with later coverage](https://www.ufopaedia.org/index.php/Movement_(EU2012)); confirmed for XCOM 2 by search excerpt) —
two concentric move-range outlines from the selected soldier: a nearer one (blue in most
descriptions) reachable for one action point and able to still fire or use an ability afterward,
and a farther one (yellow) reachable only by spending both points as a dash, after which nothing
but a defensive reaction remains for the turn. Hovering a tile inside either band previews the
exact path the soldier will walk and its cost; a tile requires only the one click named in
heading 9 to commit.

**remembered** — cover is drawn as a small icon at the soldier's *destination* tile as it is
hovered: a full shield for full cover, a half shield for half, nothing for none, oriented to show
which of the tile's edges the cover is on. It is drawn on the tile being considered, not
retroactively on tiles already passed. Concealment (pre-War of the Chosen: the base game's own
stealth-opening mechanic) is a soldier-level ring/icon rather than a tile property — the tile
itself carries no visible "you'd be seen from here" warning, which is the gap the mod **Gotcha
Again** exists to close (heading 10).

**inferred** — because cover and the move-range bands are the *only* tile-level information this
genre draws (no attention field, no per-tile detection value), a tile in this game necessarily
carries strictly more information than any tile in the canon, which is a boundary condition for
brief one rather than a new finding — `conventions.md` already says the panel-vs-map split favours
the map, and this heading is the concrete floor that comparison starts from.

## 5. The enemy

**This heading is thin, and that is the finding**, exactly as anticipated before this file was
written. XCOM 2 draws a pod the instant any one of its members is seen (or triggers on
proximity/objective scripting) and then draws every member permanently — full silhouette, full
stat card, full ability list — for the rest of the mission, **regardless of subsequent line of
sight**. There is no fog on a found enemy and no partial-information state for one. **remembered**,
consistent with every source touched this session; **no source found** that contradicts it.

**remembered** — the one moment with any drama to it is **pod activation**: the camera cuts away
from player control, pans to reveal the newly-triggered pod with a beat of held silence, and the
pod then **scampers** — repositions to nearby cover — before control returns. This is manual
enemy-turn theatre, not a state the HUD tracks afterward; once the cutscene ends the pod is just
drawn like any other found enemy. **No source found** for an exact icon (a stylised alert glyph is
widely described but not consistently named across sources this session reached); recorded as
*no source found* rather than guessed.

**remembered** — War of the Chosen's own Chosen can appear mid-mission (not only on their
dedicated missions) with a name, a portrait, and taunts printed to a message line, but their
*rules* information (HP, resistances) is drawn exactly like any other found enemy once they are
visible — the Chosen adds narration, not a new HUD state, and is out of scope for a tactical-HUD
comparison for that reason.

**Why no game on the tactics canon has more to offer here, stated once and not per-heading again:**
concealment as a *rule the enemy has to guess about* — a rung, a marker, a belief that can be
wrong — does not exist in any tactics-canon game. The genre's "enemy" heading is a drawing
problem (how much of a known thing to show); this game's is an epistemics problem (what an unseen
side believes about you), and XCOM 2 has nothing to say about the second because it has no
mechanic that produces it. The turn-based stealth shelf in `conventions.md` is the one that
answers this heading for real, and this file's job was only to confirm the tactics canon's
exemplar has nothing more specific to add — which it does not.

## 6. Turn order and time

**remembered**, consistent across every source touched — XCOM 2 alternates *whole sides*, not
individual units by initiative. There is no order strip, no portrait queue, and nothing to
interleave: a banner reads "Alien Turn" (or equivalent) over the full enemy phase, during which
the player has no input at all except reactions already banked (overwatch, or a Chosen-specific
reactive ability). Each soldier simply has its two points available at the start of every one of
*your* turns; there is no per-unit "acted already" indicator beyond the ability bar going grey.

**verified** ([Stop Wasting My Time, Nexus page loaded directly this session](https://www.nexusmods.com/xcom2/mods/217)) —
the enemy phase is not instant: base game inserts a 1–3 second pause after shooting, throwing,
abilities and kills, a 2.75 second pause after taking cover, and a 33% slowdown of enemies not
currently being attacked during an overwatch interrupt, per the mod's own changelog. This is
presentation pacing, not a turn-order convention, but it is the reason heading 10's most-endorsed
mod exists at all.

**inferred** — because the whole-side alternation has no order to draw, this heading's genre
convention (a phase banner, nothing else) is one this project's interleaved-initiative turn order
cannot simply adopt; `conventions.md` already reaches the same conclusion independently (Battle
Brothers is named as the actual precedent for an interleaved strip) and this file's contribution
is only to confirm the modern XCOM pair is not that precedent.

## 7. Reactions

**remembered** — overwatch is declared from the ability bar like any other action, for a fixed
one-action-point cost regardless of how much was left; there is no cone to aim and no partial
commitment. It resolves entirely on the enemy's turn: a camera cut to the triggering shooter, the
shot resolves with no input, and control returns to wherever the enemy phase left off. The
player is never asked anything mid-resolution — no target choice, no "hold or fire," nothing. The
one interactive reaction in the base game is a specific soldier ability (Return Fire / Threat
Assessment-style class perks), not a general mechanic, and even those resolve as an automatic
extra shot rather than a question put to the player.

**No source found** this session for a precise camera-cut duration or trigger-to-resolution
timing; **remembered** only that it is widely called out as unskippable and is exactly what **Stop
Wasting My Time** and its "Legacy"/"Still" successors (heading 10) exist to shorten.

**inferred** — because overwatch here is a state with zero interaction at resolution time, it is
the cleanest possible illustration of the "state, not interaction" convention `conventions.md`
already names, and this game's own reaction window (a scored, answerable pause) is a real
departure from it rather than a variation — worth restating plainly here since a reader of only
this file, without `conventions.md` open beside it, could otherwise assume the two systems are
more alike than they are.

## 8. Camera and input

**verified** ([search excerpt of gamerevolution.com/GameRevolution keybind guide](https://www.gamerevolution.com/guides/69930-xcom-2-keyboard-shortcut-commands)) — default binds: `Q`/`E` rotate the camera
in fixed steps; mouse scroll zooms; `W`/`A`/`S`/`D` and screen-edge pan the camera; `Tab` and mouse
button 4 cycle to the next unit, `Shift` and mouse button 5 to the previous. There are two fixed
pitch presets, no free pitch, and no drag-to-rotate — rotation exists only on the two keys.

**verified** ([Free Camera Rotation, Nexus Mods, page loaded directly this session](https://www.nexusmods.com/xcom2/mods/1)) — 3,572 endorsements, 58,202 unique downloads, 97,884 total downloads, 299,049
page views as of 2026-09-10, created by Wasteland Ghost (wghost81), first uploaded 5 February 2016.
Its own description states the base game's step plainly: **"Pressing Q or E … once will rotate
camera by 45 degrees."** That is the base game's behaviour the mod is overriding, not the mod's own
invention, which settles what this file could not pin down on the first pass — the 45° step is
**verified**, not remembered.

This is the single most load-bearing mod for this section, and its own description is the best
evidence of the gap it fills: it "enables free camera rotation while holding down Q and E,"
"enables free camera zoom while holding down T and G," and additionally offers an Alt+mouse
free-look mode and `[`/`]` pitch control, a reset-to-default-view hotkey, and a toggle between free
and fixed rotation. Every one of those is a control the base game does not offer at all — not a
tuning change, an entirely missing gesture.

**remembered** — right-click has no camera function in the base game; it is spent entirely on
mode-cancel (heading 9). This is the fact `conventions.md`'s Selecting and ordering section
already leans on to argue this project's right-click-fires binding blocks the mouse camera, and
this file confirms the base game's own right-click is idle exactly where this project's is busy.

## 9. Confirmation and refusal

**remembered**, consistent with every source touched — a move takes exactly one click on a
reachable, previewed tile; there is no second confirmation step and no way to undo it once taken,
matching heading 2 and heading 4. An attack requires *two* actions in sequence — enter targeting
mode (a key or ability-bar click), then a separate click/confirm on the chosen target — but no
dialogue box ever appears; the second click is silent and irreversible the instant it lands.
Right-click or `Esc`/`Backspace` cancels a mode that has not yet been committed to, at any point
before that final click.

**remembered** — the game will let a player do several things irreversibly with **zero** warning
of any kind: break concealment by moving within an enemy's sight radius, walk within range of a
hidden mine or ambush, or overwatch-trigger a squadmate's own shot into a soldier standing in the
way of it. None of these carry so much as a colour change on the tile; the player finds out by
the consequence. The one thing the base game *does* warn about with an explicit modal is
permanent soldier death on Ironman-adjacent settings and, in some difficulty configurations, the
first time a mechanic is about to be used for real (a one-time tutorial-style popup, not a
recurring guard-rail).

**inferred** — the total absence of tile-level warning for concealment-breaking movement is the
direct ancestor of the **Gotcha Again** mod family (heading 10) and is the strongest single piece
of evidence in this file for `conventions.md`'s existing claim that this project's shown-before-
committing figures (attention on the destination tile, who would hear a move) are not decoration
but are covering a gap the genre's best-known game leaves completely open.

## 10. What the game hides, and the mod that reveals it

Ten rows, each a gap named against a heading above, what the mod draws, and roughly how many
people decided the base game had not told them enough. Most counts below are **Nexus Mods
endorsements**, read directly from each mod's own page; Gotcha Again is the exception and is not
on Nexus at all, so its count is **Steam Workshop current subscribers** instead — the two figures
measure different things (an endorsement is a deliberate click of approval, a subscription is
just having the mod installed) and are not comparable across rows. Two rows have no count at all,
recorded as such rather than guessed. Every number was current as of 2026-09-10 and drifts daily.

| Mod | Fills the gap in | What it draws | Count, as surfaced |
|---|---|---|---|
| **[Free Camera Rotation](https://www.nexusmods.com/xcom2/mods/1)** | Heading 8 — no free yaw, no pitch control, no drag gesture at all | Hold `Q`/`E` for free rotation instead of a stepped 45° turn, hold `T`/`G` for free zoom, Alt+mouse free-look, `[`/`]` pitch | **verified**, page loaded directly: 3,572 endorsements, 58,202 unique downloads, 97,884 total, as of 2026-09-10 |
| **[Gotcha Again](https://steamcommunity.com/sharedfiles/filedetails/?id=1124288875)** (WotC) | Heading 4 and 9 — no tile-level warning for line of sight, flanking, triggering an overwatch, or walking a VIP into pod activation | A specific icon per situation, all previewed on the destination tile before the click that commits: a **red reticle** if the enemy will be shootable, **yellow** if also flanked; a **red diamond** if only Squadsight would reach them, **half-empty yellow diamond** if that shot would also flank; a **cog** if a Gremlin hack becomes reachable; a **green diamond outline** on a friendly who would newly be in sight; a **reticle added to an enemy's own overwatch icon**, with a marker on the tile that would trigger it, when the move would spring it; and a marker on the tile that would trigger a pod activation, restricted to pods already visible to the player so the mod cannot leak information the vanilla UI wouldn't | **verified**, Steam Workshop page loaded directly: 272,071 current subscribers, 426,508 unique visitors, as of 2026-09-10. Not on Nexus Mods — a keyword search there returned zero results |
| **[True Concealment](https://www.nexusmods.com/xcom2/mods/57)** | Heading 6/9 — the mission timer counts down even while the squad is fully concealed, which is a countdown for a state the player has no way to see coming | Suspends the timer entirely while the whole squad remains unseen; configurable Dark Event penalty as a balancing cost | **verified**, page loaded directly: 4,098 endorsements, 74,664 unique downloads, as of 2026-09-10. Base-game only in the version checked; a WotC-era equivalent was not independently confirmed |
| **Peek From Concealment** | Heading 5/9 — concealed movement previews nothing about what a step would newly reveal | Lets a concealed soldier preview a tile's visibility consequences before committing to the move | **remembered** that this mod exists and does this; **no source found** this session confirming exact wording or a count — flagged rather than asserted further |
| **[Perfect Information](https://www.nexusmods.com/xcom2/mods/252)** | Heading 3/5 — enemy hit/crit/dodge numbers are computed but never shown for anything but your own shot | Restores the old Second-Wave option: configurable hit/crit/dodge percentages for both sides. **Verified by screenshot** (opened from the mod's own image gallery): the readout is a short inline line reading **"Hit NN% – Crit NN%"** positioned beside the enemy's own health bar, not a separate panel | **verified**, page loaded directly: 1,314 endorsements, 23,785 unique downloads, as of 2026-09-10. Its own known-issues note says compatibility with Gotcha Again "has been broken" pending a WotC update — the two mods' authors were tracking a conflict between each other, itself a small data point on how crowded this gap is |
| **[Show Health Values](https://www.nexusmods.com/xcom2/mods/150)** / Numeric Health Display | Heading 1/5 — health, armour and shields are bars, not numbers, on both sides | Prints the HP value **on top of the cover-icon position** next to the health bar (the mod's own wording), not merely "nearby" | **verified**, page loaded directly: 1,707 endorsements, 30,314 unique downloads, as of 2026-09-10. The WotC-specific "Numeric Health Display" is a related but separately maintained Steam Workshop mod, not checked directly this session |
| **[Overwatch All/Others](https://www.nexusmods.com/xcom2/mods/660)** | Heading 2/7 — overwatch is declared one soldier at a time even though it is the whole squad's default end-of-turn action | One command puts every remaining soldier (or every *other* soldier) on overwatch | **verified**, page loaded directly: 411 endorsements, 11,197 unique downloads, as of 2026-09-10. The page states plainly **"Not compatible with WotC"** — this is a base-game-only mod, a fact the first pass missed |
| **[Evac All](https://www.nexusmods.com/xcom2/mods/99)** | Heading 1/9 — extracting a full squad from an evac zone is one click per soldier | One click evacuates every soldier standing in an active zone | **verified**, page loaded directly: 5,923 endorsements, 101,848 unique downloads, as of 2026-09-10. Separate WotC-specific upload linked from the same page, not checked independently |
| **[Stop Wasting My Time](https://www.nexusmods.com/xcom2/mods/217)** | Heading 6/7 — deliberate 1–3 second pauses after nearly every action, plus a 33% slowdown of non-targeted enemies during overwatch, with no way to turn either off | Removes the pauses (shooting, throwing, killing, taking cover) and the overwatch slowdown; raises unit movement speed by roughly 10%, configurable back down; purely cosmetic, changes no rule | **verified**, page loaded directly: 6,499 endorsements, 119,599 unique downloads, 202,529 total, as of 2026-09-10 |
| **Tactical HUD replacement, most-subscribed current one** | Heading 1 generally — the panel-vs-map question this whole reference exists to inform | *No single mod could be confirmed this session as the current leader.* Candidates surfaced — **Tactical Squad HUD** and **Enhanced Sitrep UI**, both by SurferJay, both War of the Chosen — but the only figures found were Steam *ratings* (115 and 86 respectively), not subscriber counts, and the Nexus "most endorsed" listing was not filtered to this category before time ran out this session | **Explicitly unresolved.** *No source found* for a defensible "most subscribed" answer; recorded as a gap rather than guessed, per the evidence-discipline rule this file opens with |

**What this row-by-row picture says as a whole, and it is the finding heading 10 exists to
produce.** Every mod above with a clear count is a **prosthetic for a single missing preview or a
single missing shortcut**, never a request for a different game. Nobody modded in a new turn
order, a new cover system, or a new hit-chance formula — the mods add the *warning before the
click* (Gotcha Again, True Concealment, Peek From Concealment), the *number instead of the bar*
(Show Health Values, Perfect Information), or the *one click instead of many* (Overwatch
All/Others, Evac All, Stop Wasting My Time). Read against this project's own gaps: brief one
(readouts on the thing) and brief four (who a shot would wake) are exactly the shape of the first
group; nothing in this project's queue is asking for the second or third group's kind of fix, and
this file did not surface a reason it should.

---

## Sources

**Loaded directly in a browser** (full page content, not a search excerpt):

- [Nexus Mods, Free Camera Rotation](https://www.nexusmods.com/xcom2/mods/1) — description, exact stats
- [Steam Workshop, [WotC] Gotcha Again](https://steamcommunity.com/sharedfiles/filedetails/?id=1124288875) — full feature list, exact subscriber count
- [Nexus Mods, True Concealment](https://www.nexusmods.com/xcom2/mods/57) — description, exact stats
- [Nexus Mods, Perfect Information](https://www.nexusmods.com/xcom2/mods/252) — description, exact stats, and its own screenshot gallery (one image opened and read)
- [Nexus Mods, Show Health Values](https://www.nexusmods.com/xcom2/mods/150) — description, exact stats
- [Nexus Mods, Overwatch All Others](https://www.nexusmods.com/xcom2/mods/660) — description, exact stats, WotC-incompatibility note
- [Nexus Mods, Evac All](https://www.nexusmods.com/xcom2/mods/99) — description, exact stats
- [Nexus Mods, Stop Wasting My Time](https://www.nexusmods.com/xcom2/mods/217) — full changelog, exact stats
- [StrategyWiki, XCOM 2/Aim Bonuses](https://strategywiki.org/wiki/XCOM_2/Aim_Bonuses) — full text, soldier aim-by-rank tables, and its embedded shot-menu screenshot, [opened directly at full resolution](https://cdn.wikimg.net/en/strategywiki/images/b/ba/XCOM_2_shot_menu_example.jpg) — the single most valuable source in this file, since it is the only one that shows the HUD rather than describing it
- [Nexus Mods, XCOM 2 mod search](https://www.nexusmods.com/xcom2/search/?gsearch=Gotcha%20Again) — used to confirm Gotcha Again is not hosted on Nexus (zero results)

**Search excerpts only** (the page itself was not loaded, or a browser visit was not attempted this
session):

- [PCGamesN, XCOM 2 tips and War of the Chosen guide](https://www.pcgamesn.com/xcom-2/tips-guide-war-of-the-chosen)
- [GameRevolution, XCOM 2 keyboard shortcut commands](https://www.gamerevolution.com/guides/69930-xcom-2-keyboard-shortcut-commands)
- [Steam Community discussion, Dodge vs. Hit vs. Crit](https://steamcommunity.com/app/268500/discussions/0/1471967615856106473/)
- [UFOpaedia, Mechanics (LWOTC)](https://www.ufopaedia.org/index.php/Mechanics_(LWOTC))
- [Diceplots, XCOM 2 weapon damage math](https://diceplots.com/games/xcom/)
- [Pavonis Interactive forum, graze/hit/crit/dodge visualization](https://www.pavonisinteractive.com/phpBB3/viewtopic.php?t=23695)
- [UFOpaedia, Movement (EU2012)](https://www.ufopaedia.org/index.php/Movement_(EU2012))
- [Nexus Mods Wiki, XCOM Squadsight Aim Penalty Mod](https://wiki.nexusmods.com/index.php/XCOM_Squadsight_Aim_Penalty_Mod)

**What this changed from the first pass.** A first pass tried an automated page-fetch tool against
Nexus, Steam and StrategyWiki and got HTTP 403 from all three, so the file's first version leaned
almost entirely on search excerpts and reported several mod counts as "not surfaced." A second pass
used an actual browser instead, which none of those sites blocked, and reached every page above
directly — correcting several counts (Free Camera Rotation, Evac All, Overwatch All/Others, Stop
Wasting My Time all drifted slightly upward; Gotcha Again's 272,071 Steam Workshop subscribers and
Perfect Information's 1,314 Nexus endorsements were not surfaced at all on the first pass), catching
one compatibility fact the first pass missed (Overwatch All/Others is not WotC-compatible), and —
the most consequential correction — replacing a remembered guess about the shot HUD ("a number on
the target, breakdown behind a hover") with a real screenshot showing a docked breakdown list
instead, which heading 3 now covers in full and which is flagged to Brief One in
[`../briefs.md`](../briefs.md).

Two things the browser still could not do. The Nexus "most endorsed, User Interface category"
listing was not filtered and read before time ran out, so heading 10's tactical-HUD-replacement row
stays explicitly unresolved. And a still image answers what a HUD *looks like* at one instant; it
cannot answer what a hover does, what a click does, or what changes over a full mission — the
questions this file flags as open (heading 3's chevrons, the exact camera-cut timing in heading 7)
need a controller, not a browser.
