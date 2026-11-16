# Session log (take 2)

Newest first. One entry per working session: what was done, what is next, anything a fresh
session must know. Take 1's log is `archive/v1/notes/session_log.md`.

## 2026-11-15 (late) — round 10, first pair; paused at 22:30 for the night

- **ChatGPT as a fourth critic (R006, round 9).** Overall 4, 22 defects. It caught a broken elbow strap (D1)
  that the three Claude critics missed. Recorded in `notes/critic/soldier_r9/G1_compare.md`.
- **Soft gear (52be96e, 3accada).**
  - Carrier and pouches rebuilt as Cordura over plates and magazines (new `scripts/parts/softgear.py`).
  - Front buckles and admin panel; shoulder pads rest on the shirt and land on the rear bag; the belt is fitted
    per section.
  - Outer-thigh leg rig; radio on the rear bag; tan antenna.
  - A hood over the holstered pistol, on a compact frame (belt.md §14, under Decision 2).
- **Armour and boots (d1ac212).**
  - Straps cleared from the posed sleeve (D1 fixed); worn, grimy plates; upper-arm plates on webbing.
  - Tapered two-plate forearm guards; smaller faceted knee caps.
  - Boots with a toe cap, a suede vamp, panels and a 123 mm sole.
- **Round 10 rendered** (`renders/round_10/`, packet sha 4e199da4).
  - I looked at the hero frame myself. The armour's new grime reads as big, soft, pale camouflage blotches (a
    regression: the plates look like fabric pads), and the right boot still reads smooth at hero scale.
  - Critic C1 was running when Jeff paused; C2 and C3 have not run.
  - R007 (ChatGPT's review of round 10) is `taken`, but ChatGPT ran out of tokens.

**Resume.**
1. If `renders/round_10/critic/results/C1.json` exists, run C2 and then C3; otherwise start with C1. Tally,
   copy to `notes/critic/soldier_r10/`, commit.
2. R007 when ChatGPT is back.
3. Round 10's second pair:
   - Trousers and shirt: seat, shin folds, base colour 1.4 x, even camo, hems out of the boots, a soft roll in
     place of the spiky blousing.
   - The hold and the head: the left hand under the handguard, the head turned further, the stock against the
     carrier, face skin and hair.
   - Armour's grime as scratches, streaks and edge wear rather than blotches, and the boots' panels lighter so
     they read.
4. Then the Godot re-export.

## 2026-11-15 (evening) — round 9: cloth and mass, the hard kit

Two lanes in parallel, each committed on its own:
- **Cloth and mass (22204a1).** The trousers were rewritten: a per-slice hull of the body plus ease, a gusset and
  cloth-simulated drape on the rest body (`scripts/parts/cloth.py`, cached in `cache/cloth/`), with blousing
  over the boots. Brown field dust comes from an optional dust colour in `mat_groups.weather`. Shirt sleeves have
  27-29 mm of ease and simulated folds above the elbow. The carrier's bags, pouches and pads are thicker.
- **Hard kit (ae0ea44).** The armour colour was measured from the zoom crops: worn tan-grey, with no bare
  steel. A `mat_hard` bug made the painted chip threshold draw ~6 % chips at a stated 0.3 %. The right shoulder
  cap now sits forward, the elbow pads are domed and the knee caps faceted. The gloves gained a knuckle guard
  and pads. The boots have a taller toe, a rand and a chunkier sole (now 141-147 mm wide, too wide). The belt
  is a padded band, and the carbine's rail zebra stripes were toned down.
- **Critic round 9 (`notes/critic/soldier_r9/`): 6, 6, 4** (round 8: 4, 5, 4), 0 blocking, 53 items. Worst:
  - the right boot reads as a galosh (all three critics);
  - the armour reads as clean pale plastic;
  - the seat still shows the cleft from behind;
  - the shins carry even foil-like lumps where real cloth folds in a few large planes;
  - the forearm guards read as a cone or drum;
  - the holster lid stands off the hip;
  - the face is waxy, and the hair a hard cap;
  - the pauldrons are slabs with ragged stair-stepped top edges;
  - the upper-arm bands are too bright;
  - the carrier front is plain;
  - the left hand grips overhand;
  - the head turns too little;
  - the trouser legs differ in value from each other and from thigh to shin.

**Next (round 10, worst first).**
- Boots: lace to the toe, panel seams, a narrower sole.
- Armour: grime, contrast and darker plates; fix the pauldrons' ragged edges.
- Trousers:
  - smooth the seat;
  - fold the shins in larger planes;
  - raise the base colour about 1.4 x;
  - make the camo even across both legs.
- Forearm guards: taper them.
- The pose: the left hand cradling from below, the head turned further.
- The head's skin and hair.

## 2026-11-15 — round 8: the look (grade, material separation, wear)

**The evaluation's colour, decided by measurement** (`scripts/tools/look_stats.py`: per-part medians and
chromaticity over each part's exact mask, the lit and shaded bands, the key and cool sides). At spec 17's 4500 K
key the neutral gain onto the reference's neutrals (shirt, gloves, carbine, boots) was (0.73, 1, 1.28) / G in the
lit AND the shaded band, and the key side split from the cool side 1.24 x in r/g against the reference's 1.04 x.
A grade scales both sides alike, so the light's colour was changed: `scripts/eval/scene.py` key 5800 K, the cool
light (0.55, 0.76, 1.00) -> (0.66, 0.82, 1.00). Ungraded neutral gain then (0.96, 1, 0.98). `grade.json`: lift and
gain neutral and no black crush (the reference's darks are neutral to warm, not teal; spec 17's grade pushed the
shadows blue), saturation 0.92 kept. Graded neutral gain (1.01, 1, 1.00). `assemble.py` now grades every Cycles
panel (`<label>_cycles.png` graded over the backdrop, `_cycles_ungraded.png` 16-bit beside it), and the critic
packet says graded.

**Look loop** (`scripts/tools/look_loop.py`): re-materials a copy of `cache/assembled.blend` in memory (catalogue,
part tables, the carbine's material function), sets the lights, renders the hero crops and flat part masks into
`renders/look/<run>/`; no cache is written. Library 16.4 and the parts' changes: see each part's notes, round 8.

**Round 8 rendered** (`renders/round_08/`, on round 7's pose; every part rebuilt): graded neutral gain (1.03, 1, 0.94)
/ G (lit 1.01, 1, 0.94; shaded 1.08, 1, 0.91). Per-part graded median ratio (reference / render) and r/g, b/g against
the reference's: trousers 1.57 (1.14, 0.94 vs 1.05, 0.89), shirt 0.97 (1.04, 0.96 vs 1.12, 0.92), gloves 1.15,
carrier 1.00 (1.17, 0.75 vs 1.21, 0.78), armour 0.93 (1.03, 1.06 vs 1.16, 0.91), belt 0.76, carbine 0.83, boots 1.95
(not touched). The real rebuild showed two things the in-memory copies could not: the emblem plate laid out on the
cap's radius came out 80 mm tall (now on its own radius: 56.5 x 68.4), and in round 7's pose the carbine read
brighter (ratio 0.66 at hardcoat F0 0.095; now 0.080). `--packet` is refused by packet.py for rounds past 5
(spec 18 §8.1.5); its console print no longer crashes on a redirected cp1252 stdout.

## 2026-11-15 — round 5: materials for the whole soldier (head and skin aside)

**Done (uncommitted, for Jeff's review).**
- Library (`scripts/lib/`, LIB_VERSION 16.3, lint and every family self-test pass): painted textures from the image
  queue addressed like CC0 sets (`mat_catalogue.GEN_TEXTURES`, `mat_core.asset_path`); **variants**
  (`materials.get(id, part, variant)` -> `<Part>.Mat.<Variant>`, lint checks it); builders `printed` and `cloth`
  (`mat_fabric`), `painted`, `lens`, `decal` (`mat_hard`); dust's up-facing band exposed to recipes (cloth holds dust
  on its sides); 23 new recipes (camouflage ripstop, olive 500D/1000D Cordura, black ripstop, FR jersey, fleece,
  neoprene, glove knit and synthetic leather, olive and coyote webbing, the painted armour, moulded tan and textured
  black polymer, TPR, moulded rubber, brass, phosphate steel, burnt bronze, brushed FDE, the strobe and optic
  lenses, the emblem decal). `lib/uv.py real_project()`: a metric `UV.Real` by Smart UV Project scaled per island.
  `scripts/tools/seamless.py`: the half-offset blend (R000 and R004 made seamless).
- Parts: each script has a `MATERIALS` table (flat material -> recipe, variant, overrides) applied by
  `common.library_pass()` before the cache is saved (it also makes `UV.Real`, sets `wear_dust_scale` per side,
  drops the flats, runs lint). Trousers (R002 print, dust zones by height, left leg dustier), shirt (jersey torso,
  ripstop sleeves, fleece gaiter), gloves (knit back, synthetic-leather palm by normal, neoprene cuff, TPR guard),
  carrier (R000 Cordura, webbing, polymer, brass antenna), armour (painted shells worn to tan with R004, knee-cap
  frames, the R003 emblem decal on `UV.Decal`, the strobe), belt, carbine (round 2's metal and polymer retuned,
  the rest onto recipes). Boots: take 1's leather retuned in the catalogue. Each part's notes have a round-5 section.
- Requests: R004 (worn grey paint over tan, the armour) made, used, closed. R000/R002/R003 used.
- Round 5 rendered (`renders/round_05/`); albedos tuned against the hero frame with per-part medians over an exact
  part mask (a Workbench flat-colour pass) on a fast loop that re-renders `cache/assembled.blend` after updating its
  library materials in place (scratch tools, not committed).

**Evaluation light (checked, not changed).** `assemble.py` scales spec 17's lights by 0.3 (round 0's choice);
with that the skin anchor's luminance lands on the reference (median ratio 0.97), so the level is right. The
colour is not: against the reference every neutral surface renders warm. The per-channel gain that maps the
skin's render median onto the reference's is (1.04, 1.33, 1.72) in linear light, and the black and grey
materials show the same cast, so it is the 4500 K key (and no grade in the panels), not the materials. The
albedos were kept physically neutral and judged with that cast divided out; re-balancing the key's temperature
(or grading the Cycles panel) is an integration decision.

**Per-part medians, round 5 (cast removed; ratio = reference / render luminance, 1 is a match; round 4 in brackets):**
trousers 1.13 (2.20), shirt 0.76 (0.59), boots 1.09 (1.35), gloves 0.90 (0.99), carrier 1.10 (0.84), armour 0.80
(0.47), belt 0.57 (0.68; its mask lies mostly where the drawn rigs are not), carbine 1.14 (1.81).

**Next.** Wear masks per part (the reference's scuffs, stains and edge fraying are coarser and stronger than ours);
garment panel UVs (the camouflage jumps at Smart-UV islands); the boots' crease and polish fields; the emblem
mask without its outer outline; the evaluation light's colour.

## 2026-11-14 — take 2 begins (Opus, local workstation)

**Jeff's decision.** Back up and start fresh, breadth first: a basic MakeHuman model and skeleton,
posed as in the reference, then every part handed to sub-agents for a round of improvements, then
evaluation, integration, repeat. Kept from take 1: the reference image, the reality-wins rule, the
"keep diving down in detail until it is right" approach, and the work, evaluate, repeat cycle.
Everything else is archived for reference only.

**Done.**
- Take 1 tagged `sgt_morgan-v1` (9edc6b6) and moved to `archive/v1/` (specs, notes, part and
  research scripts, `build_all.py`, `interfaces.json`), with `archive/v1/README.md` saying what is
  still worth reading. The shared tooling stayed in `scripts/` (setup, lib, eval, tools, server).
- `PLAN.md` written (take 2's method, stages, part owners, the rules for a part); `CLAUDE.md`
  updated to point at it.
- Jeff asked for a review of Can It Code?'s "How I Make Any Custom Human Animation With AI" and
  related videos: `notes/research_canitcode.md`. In short: generators and scans for soft living
  forms, code for exact hard parts (the foot's lesson again); choose the skeleton with retargeting
  in mind; an image-to-pose model could replace hand-fitting the hero pose.
- Round 0 (base body, `default` rig, hero pose through the matched camera) handed to an agent.
- **Round 0 (5bcd966)**: `scripts/stages/` (base.py, pose_solve.py, pose.py, keypoints.py,
  eval_round0.py; README). MPFB male 1835 mm, the `default` rig, the hero pose solved to MediaPipe
  and take 1's landmarks through the matched camera (2-10 px on most joints; right wrist 19, hips
  18-20, both explained). The head turns to his LEFT (the image), not right as PLAN.md first said.
- **Round 1, every part a blockout**: carbine (eb5ff4f), clothing: trousers, shirt and gaiter,
  boots, gloves with `scripts/parts/common.py` (e4b3595), gear: carrier, armour, belt with
  `gear_common.py` (7f6b1f4; the P9 holster at the right rear hip, hidden, because the image shows
  no pistol), head and body (7341f97: a male chest, skin, eyes; 81 MPFB face targets fitted to
  landmarks, still heavy and broad, MPFB's targets used up). `scripts/assemble.py` (ced5676)
  rebuilds stale items in order, assembles the posed soldier, renders the hero frame and every
  ref crop with sheets, a turnaround, a clash report and a critic packet; a full rebuild and
  evaluation takes about 200 s. Round 1 rebuilt on one body (64ed4ea): `notes/round_01_*.md`.
  Worst in round 1: the neck (thin gaiter, the carrier straps a yoke, the bag 5 cm high), the
  forearm guards as cones, small pauldron caps, the leg rigs as saddlebags, clog boots, trousers
  like leggings from behind, the hands and stock 15-25 mm inside the carbine, the face.
- **Round 2 started** two at a time: shirt and carrier (the neck), boots and trousers. Next pair:
  the pose and hands (re-solve the hold against the real carbine and the carrier; finger curls;
  a face term for the head yaw) with gloves, and armour with belt. Then head (a new route: MPFB's
  targets are exhausted; a 3D face from the image or a generator, transferred onto MPFB's head as
  the foot's scan was) and carbine round 2.
- **Round 2 so far (evening)**: shirt and carrier, the neck (800d936: a cowl gaiter under the
  straps, the bag 75 mm lower, PALS, buckles, binding); boots and trousers (1a0b57a: laced boots
  with take 1's materials, trousers with seat room and hem rolls; still smooth, no drape); armour
  and belt (734b0ec: straight segmented forearm guards clear of the elbow, bigger pauldron caps,
  two-piece knee caps, the right leg rig turned to the camera and moved inboard); carbine
  (438a410: the forged and moulded forms, take 1's metal and polymer recipes). Jeff: the foot and
  boot work must start from take 1's (cfdc3a0: boots.md §6, body.md §5, a PLAN.md rule).
  Second pass on the Can It Code? videos (19fd287): our hero pose is the single-view depth case.
- **Still running at 21:53 when Jeff stopped for the night** (uncommitted on disk):
  (1) the pose and hands pass: contact and non-penetration terms in `pose_solve.py`
  (`pose_contact.py`, `face_targets.json`), finger curls fitted to the grips, a face term for the
  head yaw, the left foot's heading from 15.5° to about 5°, then the glove fit; (2) the foot port
  and boots round 3: take 1's scan-transferred foot as `scripts/stages/foot.py` (+ `foot/`), the
  sock and 297 mm last, the boots rebuilt round the last per take 1's spec 02, developed on copies
  (`cache/stages/foot_dev.blend`) until the pose pass is done, then wired into assemble and
  evaluated as round 3. If either was cut off, resume it from its files and notes; check
  `git status` and `scripts/assemble.py --status` first.
- **Next after those**: head round 2 by a new route (MPFB's face targets are exhausted: a 3D face
  from the image or a generator, transferred onto MPFB's head as the foot's scan was), then a
  full rebuild and the round 2/3 evaluation with the blind critics on the whole soldier, then
  round 3 per part from each part's notes. Open for Jeff: the plate-top height (60 mm below the
  notch, as drawn), the P9 holster's place (hidden at the right rear hip), spec 02's Q13-Q19,
  and whether to use paid generators (Tripo/Meshy/Higgsfield, an image model for textures).
