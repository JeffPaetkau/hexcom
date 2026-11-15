# Round 1 integration (2026-11-14)

Made by `scripts/assemble.py --round 1 --packet` from the caches as they were. No rebuilds were run, because
the head and body agent was rebuilding the base and the clothing at the same time. Every sheet named here was
opened and looked at. Left and right are the soldier's own.

## What was assembled

| Input | Cache time | State at load |
|---|---|---|
| base.blend | 18:49:42 | the head and body agent's latest at that moment (it was rebuilt again at 18:54) |
| hero_pose.json | 18:50:03 | solved on that base: posed joints within 0.01 mm of the solver, carbine frame exact |
| trousers, shirt, boots, gloves | 18:51:15 to 18:51:58 | rebuilt on the 18:49 base |
| head (hair cap, stubble) | 18:50:07 | one face fit behind the base |
| carrier, armour, belt | 18:26 to 18:29 | **stale**: built on the 18:25 base and the 18:09 clothing |
| carbine | 17:31:59 | fresh (it does not depend on the body) |

- All 148 part meshes are bound to `Morgan.Rig`. 105 are skinned through an Armature modifier. The carbine's 43
  hang from `Carbine.Root`, which is bone-parented to the posed `wrist.R` at `carbine_frame`.
- `cache/assembled.blend` holds the posed soldier with the hero camera, lights and floor.
- `--status` now reports every item except the carbine as stale against the 18:54 base. The round 2 rule
  follows from that: freeze the base for the round, then run `assemble.py --rebuild --round 2` once.

## Reads right against the reference

1. **The silhouette.** In `soldier_full_overlay.png` the render's outline lies on the drawn figure almost
   everywhere: head, shoulders, both arms, legs and the right boot, mostly within 10 px (3 to 5 px at full
   frame). Stance and lean are the drawing's.
2. **The carbine's line.** It runs from the right shoulder to the left thigh. Both hands sit in the drawn
   places, and the right index lies along the receiver (`hands_rifle_overlay.png`). The real-size gun reads
   right; its forward-swung magazine is a declared difference.
3. **The inventory and its placement.** Every item is where the drawing has it:
   - carrier with admin panel and three magazine pouches;
   - antenna behind the left shoulder, on the drawn spot;
   - pauldrons in three tiers, forearm guards and gloves;
   - belt, the right magazine rig and the left block;
   - knee pads and boots.
4. **The knees.** The knee pads and lower legs line up with the drawn knees within about 10 px
   (`legs_knees_overlay.png`), even though the thighs are the real (longer) length.
5. **The left arm.** Its outline matches the drawing best of all (`arm_L_overlay.png`).

## Wrong in the whole picture, ranked

1. **The neck and collar, the worst area in the hero frame** (`head_face_compare.png`, `torso_vest_overlay.png`):
   - The gaiter is a thin stack of rings. The drawing has a bulky cowl from the jaw to the strap line.
   - The carrier's shoulder straps stand up off the shoulders like a yoke. In `turnaround.png` side views they
     arch above the trapezius; in the drawing they lie over the gaiter.
   - The front bag's top edge rides about 60 px (×3) above the drawn bag top, roughly 5 cm. It covers where the
     drawing shows the gaiter and the upper strap webbing.
2. **The forearm guards dominate the arms.** They are fat cones flaring at the elbow:
   - The left guard starts about 25 mm higher up the forearm than drawn.
   - The right guard's elbow band goes 34 mm into the body at the 102° elbow.
   - The drawing shows straight, segmented sleeves.
3. **The pauldron caps are small and sit too far toward the chest.** On the left arm the drawn cap is on the
   outside of the shoulder, about 30 px (full frame), roughly 7 cm, further out than ours (`arm_L_overlay.png`).
4. **The leg rigs read as saddlebags.** In `belt_hips_overlay.png`:
   - The right platform sits about 7 cm too far out to the side. The drawn carriers face the camera on the
     front-outer thigh.
   - The left block is about 20 mm too wide and stands off the hip.
   - The thigh straps of the stale belt cache are buried in the 18:51 trousers (see the clashes).
5. **The head is still a blockout:**
   - The hair cap gives the right short-hair mass in colour, but the silhouette is narrower than the drawn hair.
   - The stubble is patchy, with skin showing through. It was built on the face before the latest fit.
   - The face is not yet his (`head_face_overlay.png`), although eyes, nose and mouth sit on the drawn ones.
6. **The hold is not a contact.** It reads right in the picture, but the carbine passes into both hands and
   the right forearm (clash list, items 3 and 4).
7. **The boots read as clogs.** Flat slab soles, a low lumpy toe and a straight shaft. The left boot runs
   about 18 px (×3 crop), roughly 4 cm, past the drawn toe (`boots_feet_overlay.png`). The right boot matches.
8. **The trousers.**
   - From behind, the seat is skin-tight like leggings (`turnaround.png`, back).
   - The lower legs are slim and smooth tubes with no stack on the boots.
9. **Colour (Cycles, ungraded, lights at 0.3).** Armour and carrier come out light tan and warm. The
   reference's are worn grey-olive. The skin is orange. Colour is not this round's subject, but the critics
   will see it.

## Clashes (hero pose; `clashes.md` has every pair and place)

Each clash is marked **real** (it needs a fix), **stale** (it comes from a cache built on older inputs, so a
rebuild in order fixes it) or **designed** (hidden and intended). The positions are posed world mm.

| # | Clash | Verts | Max | Kind |
|---|---|---:|---:|---|
| 1 | Right forearm guard (elbow band, foam, sleeve) inside the body at the back of the 102° elbow (-379, 101, 1300) | 245 | 33.6 mm | real: elbow pinch (pose / body weights) and guard fit |
| 2 | Shirt inside the body at the same right elbow | 85 | 18.6 mm | real: elbow pinch |
| 3 | Handguard inside the left hand (skin 17.6, glove 19.4); barrel and light in the left glove | 1121 | 17.6 mm | real: pose, hand-carbine contact |
| 4 | Stock, QD socket and paint inside the right forearm (skin 15–16, glove cuff 24.9, shirt 13–23); grip 14 mm in the right palm | ~2000 | 24.9 mm | real: pose |
| 5 | Stock 9.8 mm into the right forearm guard (`Guard.R.Main`, sleeve, foam) | 81 | 9.8 mm | real: pose |
| 6 | Carrier strap pads into the gaiter, front of the neck and behind it | 24 | 9.6 mm | real: carrier and shirt disagree on who is on top |
| 7 | Belt's left and right thigh straps under the trousers' shell and cargo pockets | 7403 | 5.1 mm | stale (belt 18:29 vs trousers 18:51) |
| 8 | Forearm guard sleeves under the shirt sleeves, both arms; tier 3 elastic in the sleeve | ~1400 | 6.4 mm | stale (armour 18:26 vs shirt 18:51) |
| 9 | Belt inside the carrier's pistol-magazine carrier, right flank (-251, 78, 1081) | 34 | 5.7 mm | real: placement |
| 10 | Carrier cummerbund under the shirt at both flanks | ~570 | 3.3 mm | stale |
| 11 | Knee pad bases under the knee pockets; knee straps in the shell | ~500 | 3.0 mm | stale |
| 12 | Right glove 3 mm into the front bag's lower right corner; front bag 3.6 mm into the stock | 52 | 3.6 mm | real: pose and carrier |
| 13 | Trousers through the shirt at the lower back (-42, 168, 990) | 12 | 2.8 mm | real: skinning (trousers note §5.3) |
| 14 | Glove shells 2 mm into the skin on every curled finger | 2659 | 2.1 mm | real: round 0's curl tables |
| 15 | Feet inside the boot soles (heel and ball, z 21–37) | 282 | 11.9 mm | designed: the sole is a solid slab up to the rand; the foot stands on its footbed inside it |

Not found: no part inside the head, nothing in the boots except the feet, no trousers–boots clash.

## Round 2 integration items, per part

**body and pose (round 0)**
1. Re-solve the hold as contact:
   - left palm and fingers on the handguard surface plus the glove (about 3 mm), not 18 mm into it;
   - right palm on the grip;
   - the stock at least 3 mm clear of the right forearm guard, with the butt on the carrier bag's outer face
     (as the carrier note asks).
   This one change fixes clashes 3, 4, 5 and 12.
2. Right elbow at 102°: add a corrective shape or smoothed weights at the olecranon, or less flexion (clashes 1
   and 2). Every garment and the guard inherit this pinch.
3. Finger curls: 2 mm less closure, or a contact-aware curl (clash 14).
4. Freeze the base for the round before the parts rebuild. Every base rebuild makes every part stale.

**head**
1. Rebuild after the last face fit. The stubble is patchy because the face moved under it; also give the
   stubble a minimum offset above the skin.
2. Add hair volume at the sides and top, so the silhouette reaches the drawn hairline in `head_face_overlay.png`.
3. Start `scripts/parts/head.md`. There are no head notes yet.

**shirt (and gaiter)**
1. Make the gaiter the drawn cowl: wider, taller, rising to the jaw. It is the biggest single miss in the
   hero head crop.
2. Agree with the carrier that the straps lie over the gaiter: the gaiter tucks under the strap pads (clash 6).
3. Right elbow: more ease at the olecranon, or rely on the body fix (clash 2).
4. Lower back: keep the tail inside the trousers (clash 13, shared with trousers).

**trousers**
1. Hem stack onto the boots.
2. Ease at the seat and the back of the thighs: from behind they read as leggings.
3. Lower back ease, with the shirt (clash 13).
4. After any change, the belt and armour must refit (clashes 7 and 11 came from the 18:51 rebuild).

**boots**
1. Left boot: check its heading (17° to his left) and length against `boots_feet_overlay.png`. It reaches
   about 4 cm past the drawn toe while the right matches.
2. A smoother toe box and a shaft that follows the shin, so the boot stops reading as a clog.
3. Clash 15 is designed and hidden; a footbed cavity can wait for the detail rounds.

**gloves**
1. No fit change is needed for clashes 3, 4 and 14: they come from the pose and curls. After the pose re-solve,
   check that the left palm rests on the handguard through the glove.
2. Right glove into the front bag (clash 12): it goes with the pose.

**carrier**
1. Lay the shoulder straps on the shoulders and over the gaiter. In the side views they now stand up as a yoke.
2. Lower the front bag's top about 5 cm toward the drawn position and bring it closer to the upper chest. The
   carrier note's item 3 (plate pitch) is the likely route.
3. Pistol-magazine carrier vs belt (clash 9): lift it clear of the belt, or move it outboard.
4. Rebuild on the current shirt (clash 10).

**armour**
1. Forearm guards: straighter, segmented sleeves that start about 25 mm further down the forearm, without the
   elbow flare. Rework the right elbow band so it clears the 102° fold (clash 1).
2. Pauldron cap: larger, and moved out to the side of the shoulder (about 7 cm on the left in the hero view).
3. Rebuild on the current shirt and trousers (clashes 8 and 11). The right knee pad sits a little to the
   outside of the drawn cap.

**belt**
1. Rebuild on the current trousers (clash 7).
2. Right platform: about 7 cm inboard and turned toward the front of the thigh, so the carriers face the camera
   as drawn.
3. Left block: narrower, and closer to the hip.
4. Clash 9 with the carrier: decide who moves.
5. The P9 grip sticks out backwards above the holster in the side views. It is hidden in the hero frame, but it
   looks odd from behind.

**carbine**
1. Nothing to change for integration: it is fresh, and its clashes are all the hold (pose item 1).
2. In Cycles its receivers and the FDE paint read lighter than the reference (carbine note §6, item 6).

**integration (assemble.py)**
1. Round 2 should run as one `--rebuild` after the base freeze, so no stale cache enters the evaluation.
2. Colour: compare the ungraded Cycles with the grade (`scripts/eval/grade.py`) before the materials round, so
   colour judgements are made on the graded image.

## Files

`renders/round_01/`:
- per preset: `<label>_{clay,parts,cycles}.png`, `<label>_compare.png`, `<label>_overlay.png`;
- `turnaround.png`;
- `clashes.json`, `clashes.md`;
- `assembly.json`;
- `critic/`: a packet of 34 images, critics not run. The brief is `critic/brief.md`; it is generated from
  `critic_spec.md`, which is written as packet.py's spec.
