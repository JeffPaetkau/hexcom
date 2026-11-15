# Sgt. Alex Morgan — Consolidated Reference Analysis (authoritative)

Consolidated from the five analyst notes in this folder (pose/proportions, gear inventory, face/grooming, weapon, lighting/camera/scene). Where analysts disagreed, the consolidator re-read `/home/user/sgt_morgan/ref/reference_full.png` and its crops and sampled pixels directly; the decisions are listed in "Disputes resolved" at the end. Each analyst file has an "Errata (consolidator)" appendix naming its corrected lines; the original files are otherwise untouched.

**CONVENTION: every "left"/"right" below is the SOLDIER'S OWN left and right** (his left hand, his right shoulder). The soldier faces the camera, so his RIGHT side is on the VIEWER'S LEFT (small image x) and his LEFT side is on the VIEWER'S RIGHT (large image x). Where a picture side is meant it is written "viewer's left/right". For the rifle, "right side" = ejection-port side (shooter's right when shouldered) — this is the side facing the camera.

Source image 1672 x 941 px. All pixel coordinates are FULL-image coordinates (x right, y down). Hex colours are sRGB 3x3 or 5x5 means at the stated pixel unless marked "median" (box median) or "albedo" (lighting-discounted recommendation). Blender frame used by all notes: +Z up, origin on the floor between the feet, character faces −Y, camera at −Y, **+X = his LEFT = viewer's right**.

### Agreed scale
| Quantity | Value |
|---|---|
| Standing height, skull top (y=20) → his right sole (y=895) | **875 px** (881 incl. hair spikes, y=14) |
| Assumed stature | **185.5 cm** (range 183–188) |
| Scale at the figure's depth | **4.72 px/cm = 0.212 cm/px ≈ 2.1 mm/px** |
| Head unit (skull top → chin y=129) | 109 px → **8.0 heads tall** (heroic canon) |
| Floor datum | right sole y=895; left sole y=907 (left foot 10–20 cm nearer the camera) |

---

## 1. Pose & proportions

**Pose in one sentence:** relaxed stock-on-chest patrol carry, standing nearly square to the camera, rifle diagonal across the front (butt on the right pectoral, muzzle down toward the left knee), right hand on the pistol grip with index finger extended along the receiver, left hand wrapped over the handguard, head turned ≈20° to his LEFT, left foot forward and pointed at the camera, right foot turned out ≈90° to his right.

### Vertical landmarks (y px, height above right sole in cm @185.5)
| Landmark | y | cm | Landmark | y | cm |
|---|---|---|---|---|---|
| Hair spike tips | 14 | 186.8 | Vest front-bag hem (bound edge) | ≈398 | 105 |
| Skull top (hair mass) | **20** | 185.5 | Rifle magazine bottom | ≈460 | 92 |
| Hairline (trichion) | 48 | 179.6 | Navel (est.) | 470 | 90 |
| Brow line | 72 | 174.5 | Belt | 490–512 | 86–81 |
| Eye line | **77–78** | 173.2 | Hip joints (est.) | **505** | 82.7 |
| Nose tip / subnasale | 90 / 97 | 169 | Upper right thigh strap | 520–536 | 79 |
| Mouth (stomion) | 109 | 166.6 | Crotch | **535** | 76.3 |
| Chin (lit pad / menton) | **129** / 131.5 | 162.4 | Muzzle tip | 568–570 | 69 |
| Shoulder line (pad tops) | **195** | 148.4 | Lower thigh straps | 560–590 | 67 |
| Shoulder joints (est.) | 200 | 147.3 | Right / left knee centre | **650 / 657** | 51.9 / 50.5 |
| Butt-stock heel | 243 | 138 | Boot collar top | 795–800 | 21 |
| Right / left elbow | 328 / 352 | 120 / 115 | Right / left ankle | 855 / 858 | 8.5 |
| Right / left wrist | 345 / 440 | 117 / 96.5 | Right / left sole | **895** / 907 | 0 / — |

### Horizontal landmarks (x px)
| Landmark | his RIGHT (viewer's left) | his LEFT (viewer's right) | width |
|---|---|---|---|
| Head incl. visible right ear (y≈88) | 753–762 | 845–850 | ≈90 px (face excl. ear 74 px) |
| Face midline (nasion/menton) | — | — | x ≈ 815–817 (head centre 806 → yaw to his left) |
| Shoulders incl. pauldrons (y≈205) | **≈640** | **≈960** | **≈320 px ≈ 68 cm** |
| Shoulders, bare deltoid (est.) | 655 | 950 | 295 px ≈ 62.5 cm |
| Shoulder joints | 675 | 935 | 260 px |
| Chest incl. vest (y≈300) | 690 | 920 | 230 px ≈ 49 cm |
| Elbows / wrists | 632 / 698 | 958 / 870 | — |
| Waist under vest (y≈470) | 745 | 890 | 145 px ≈ 31 cm |
| Hips, body only (y≈500) | 735 | 900 | 165 px ≈ 35 cm |
| Hips incl. drop-leg rigs (y≈520) | 665 | 950 | 285 px ≈ 60 cm |
| Knees / ankles | 727 / 732 | 890 / 928 | 163 / 196 px |
| Right foot toe→heel | 631 → 767 (profile, 136 px) | — | — |
| Left foot | — | heel ≈910, toe 950 (head-on) | — |

### Key ratios and body type
* Head : body **1 : 8.0**. Eye line 0.934 H, chin 0.875 H, shoulder 0.80 H, knee 0.28 H — all normal for a 185 cm male.
* Shoulder : hip breadth **1.95 padded / ≈1.8 bare** (standard 1.35–1.4) → strong V-taper; waist : hip 0.88, lean.
* **Crotch height only 0.41 H** (standard 0.47) with a normal knee height → the thigh (hip→knee ≈31 cm) is ≈28 % short and the torso (chin→crotch 86 cm) ≈13 % long. This is a real property of the drawing. **Decision for the modeller:** build as drawn (hip joints at y≈505); fallback compromise hip joints at y≈480 with the trouser crotch still at y≈535. Do not lengthen the legs to canon.
* Limb girths (clothed): upper arm ≈12.7 cm, forearm ≈11 cm, thigh ≈18 cm, calf ≈15 cm, boot shaft ≈14 cm. Underlying body: muscular-athletic mesomorph, ≈88–95 kg.

### Rotations (all ±5°, A-pose rest; full rig table in the pose note §6)
| Part | Value |
|---|---|
| Pelvis | yaw −10° (turned to his RIGHT → his LEFT hip nearer camera), pitch +2°, roll 0 |
| Chest | yaw ≈ −5° world (nearly frontal), slight extension −3° |
| Neck + head | **head yaw ≈ +20° (±5) to his LEFT relative to the camera axis** (≈ +25° vs chest); pitch −3° chin-up (the visible "chin-up" is mostly the low camera); roll 0 |
| Gaze | along the head axis, 3–5° further left and slightly up, into the distance |
| R shoulder / elbow | flex −8, abd +20, int-rot +45; elbow flex ≈97°, forearm pronated ≈70°, wrist ext 12 / ulnar 10 |
| L shoulder / elbow | flex +12, abd +8, int-rot +20; elbow flex ≈55°, forearm pronated ≈40°, wrist flex 10 / radial 10 |
| R hip / knee / foot | flex −5, abd +14, ext-rot 45; knee flex 15–20°; **toe points ≈90° to his right** (near pure profile) |
| L hip / knee / foot | flex +8, abd +10, ext-rot 22; knee flex 8–10°; **toe points 15–20° to his left of the camera axis**, foot 10–20 cm forward |
| Stance | ankle-to-ankle 41.6 cm, heel-to-heel 31 cm, toe-to-toe 68 cm, knee-to-knee 35 cm; weight ≈55/45 right-heavy; COM ≈ (812,430) ≈ 98 cm up |

### Hands
* **Right hand — pistol grip** (hand box 690–752 × 325–400; forearm arrives nearly horizontal from his right elbow (632,328), pointing toward the camera). Dorsum/knuckle plate faces the camera. **Index finger fully extended** along the right side of the lower receiver, MCP (727,355) → tip (750,398). Middle/ring/little curled around the grip front (MCP 85°, PIP 95°, DIP 50°). Thumb hidden behind the grip.
* **Left hand — overhand C-clamp on the handguard** (hand box 803–882 × 420–497; forearm arrives at 45° from his left elbow (958,352)). Palm on the top/his-left face of the handguard, centred ≈(840,460), ≈60 % of the way to the muzzle. **Thumb lies ACROSS the top rail** (MCP (880,428) → tip (846,447)). Four fingertips visible on the underside at (806,458) (812,470) (820,483) (828,495), index nearest the receiver (MCP 60°, PIP 85°, DIP 45°). **No sling** — the dark strap-like patch at (850–880, 395–430) is the glove cuff and the vest's dark side.

---

## 2. Body & face

### Head pose and camera (reproduce before any likeness check)
Yaw **≈20° to his left** (nose toward viewer's right; right ear fully visible, left ear hidden); pitch ≈12° chin-up relative to the camera ray, of which ≈10° is the low camera (head-vs-torso only ≈3–5°); roll 0 (irises level at y=77). Face seen from ≈13° below → both nostrils and the under-jaw plane visible.

### Landmarks (full px; 1 px ≈ 2.1 mm at the head)
Trichion (810,48); glabella (815,72); nasion (815,76); brows: right inner/peak/tail (809,72)/(796,70.5)/(786,73.5), left (819,72)/(832,70.5)/(843,74); right eye canthi 789–807, left 821–839 (fissures 18 px wide, 5 px tall); **iris centres (800,77) and (831–833,77), IPD ≈32 px (≈66 mm)**; pronasale (815,90); nostrils (813,94)/(822,95); alar width 21 px; subnasale (816,97); stomion (816,109), mouth corners (804,109)/(830,111), width 26 px (≈58 mm corrected); mentolabial sulcus (816,117); chin pad (816,123); menton (816,131.5); gonions (768,113)/(842,112), bigonial 74 px; right ear top/bottom/front/back 83.5/112/770/753 (28.5 × 17 px ≈ 61 × 36 mm), free lobe.

Facial thirds (projected) 24 / 25 / 34.5 px → corrected ≈31 / 31 / 38 %: **the lower third is genuinely long**.

### Shape and structure
* Long rectangle / soft square-oblong head; vertical temple-to-jaw sides; wide skull (bizygomatic/face height 0.89 projected, ≈0.8 true).
* Prominent brow ridge; brows sit only ≈4 mm above the lid margin → heavy, hooded, deep-set orbit. Two vertical glabellar "11" lines (x≈813 and 817, y 58–71), one faint horizontal forehead crease (y≈63), shallow crow's feet (2–3 lines, right canthus).
* High, prominent cheekbones with a definite sub-zygomatic hollow (lean, low facial fat); moderate nasolabial folds.
* Strong angular jaw (gonial angle ≈115–120°, bigonial ≈ bizygomatic), straight sharp jawline, **broad square chin projecting strongly**, faint central cleft (+0.15), defined mentolabial sulcus.
* Nose: straight, high narrow bony bridge (≈15 mm), subtle dorsal hump at y≈86–88, slightly rounded tip, **broad alar base (≈45 mm, 1.5× intercanthal)**, oval nostrils.
* Eyes: almond, long (≈38 mm) and narrow (aspect 0.28), close-set (intercanthal 14 px / fissure 18 px = 0.78), canthal tilt ≈ +4°, hooded upper lid, faint tear-trough.
* Mouth: closed, lightly pressed, level; thin upper lip (≈6 mm, shallow cupid's bow, long defined philtrum ≈18 mm), fuller lower lip (≈9–10 mm).
* Neck: thick, muscular (≈0.85–0.9 × jaw width), SCM ridge visible on the right; deep under-jaw shadow.
* Expression: stern-neutral, resolute — brow-lower 0.25, lid-tightener 0.25, lips-pressed 0.2, jaw clench 0.1, no smile. Symmetric face; the only asymmetry is pose.
* **Age 38–42.** Fitzpatrick II–III, lightly ruddy/wind-burnt on the lit cheek. **No moles, scars or freckles.**

### Skin colour (lit samples → albedo)
| Area | Lit sample (hex @ px) | Albedo recommendation |
|---|---|---|
| Forehead centre | #c59684 (795,62); region mean #b98879; hot spot #bd8a79 (818,58) | base skin **#b98670**; forehead/chin slightly olive **#b5876e** |
| Right temple / zygomatic (brightest skin) | #dbb49d (782,72) · #e6bfac (778,70) · #ecc3ad (780,88) | key-light calibration targets |
| Right cheek mid / hollow | #ca9683 (790,92) · #c08c77 (786,102) · #d19b87 (792,100) | cheek/nose/ear SSS redness **#c98272** |
| Left cheek / forehead (cool fill) | #ae8e8c (842,92) · #b09a9d (840,100) · #93878d (835,52) | same albedo under cool light |
| Under-eye | #ac7c6d (798,83) | **#9d7266** |
| Nose bridge / tip / ala | #d39a86 (815,82) · #c59180 (815,90) · #c28a77 (806,93) | — |
| Lips upper / lower | #7f574f / #8a5c55 (means) | **#9a6a62** (dusty rose-brown, soft border) |
| Ear helix / lobe | #b6806a (762,92) / #d48b72 (765,108) | strong red SSS on the lobe |
| Under-jaw deep shadow | #100a04 (805,138) · #110b06 (812,140) | ambient calibration target |

**Iris: dark warm brown-grey, NOT blue.** Right iris mean #5d3e34, left #493735 (zero blue-hue pixels). Recommended iris albedo **#5b4a3e** body, **#3a2d26** limbal ring, **#6e6253** radial fibres. The "light eyes" read at thumbnail scale is a contrast illusion against the warm skin; at most A/B a steel grey #5a6068. Sclera albedo ≈ #e6e0da with strong medial-canthus AO. Lashes short, dark brown-black (#3b2219 lash line).

### MakeHuman / MPFB start values
Gender 1.0; Age ≈0.55–0.60; Muscle ≈0.70; Weight ≈0.45; Caucasian 1.0. head-square +0.5, head-rectangular +0.3, head-scale-horiz +0.2, head-fat −0.3; eyebrows-trans down +0.4, brow-ridge +0.3; eye-scale +0.25, eye-trans in +0.2, eye-height1 −0.3, eye-push in +0.3, eye-bag +0.2; cheek-bones +0.5, cheek-volume −0.35; nose-width1 (bridge) −0.3, nose-width3 (base) +0.25, nose-hump +0.15; mouth-scale-horiz +0.15, upperlip-height −0.3, lowerlip-height +0.15, cupidsbow −0.2, philtrum +0.2; chin-width +0.4, chin-height +0.25, chin-prominent +0.4, chin-bones +0.3, chin-cleft +0.15, jaw-angle squarer +0.4, jaw-width +0.35; ear-lobe +0.2, ear-flap +0.25; neck-scale-horiz +0.3, neck-scale-depth +0.25, neck-double −0.3. (Full list in the face note §10.)

---

## 3. Grooming

### Hair
* **Style:** short textured crop / messy quiff, tapered sides, skin-blended fade at the temples. Top piecey and spiky, pushed **up and toward his RIGHT (viewer's left)** with a forward-up lift at the fringe; back-left strands splay up/back. Product-separated (matte clay), slightly dishevelled.
* **Extents:** hair mass top y=20, spike tips y=14, hairline y=48 (centre), temple corners y≈50–52 at x≈779/838 — gently arched, no widow's peak, no recession. 8–10 distinct silhouette spikes between x≈765 and 842 (a key likeness cue; a smooth hair cap will fail).
* **Lengths:** top 35–45 mm (fringe longest), upper sides 10–15 mm, temple taper 3 → 1 mm reaching skin at ear-top level; sideburns end at tragus level (y≈92); nape not visible (assume 8 → 1 mm).
* **Colour:** medium-dark warm brown with golden-brown lit tips. Hair-region percentiles p5 #1e1816, p25 #37261e, p50 #4f483a, p75 #907060, p95 #bd8871; shadow mean #30241c, mid #614d42, highlight #aa7e6e. **Albedo: root/base #3a2a1e, tip/highlight #8a6549, ~10 % of strands #a07a5e.** Low-moderate sheen. No grey in the scalp hair.

### Beard stubble
* 3–5 day stubble, **2.5–4 mm** (chin/moustache ≈4 mm, cheeks ≈2 mm), trimmed-uniform, natural (unshaved) neckline fading under the jaw to y≈140–142.
* Density: **dense** on the chin pad / soul patch (806–828 × 114–130), moustache, jawline and under-jaw; **medium** on the lower cheeks below a tragus→mouth-corner line; **sparse** above that; **bare** on cheekbones, under-eyes, nose, forehead, cheek hollow.
* Colour: dark brown hairs **#3b2a22**; chin reads cooler/greyer (#815f53 mean vs warm jaw #a97d66) → **20–30 % grey/white hairs on the chin and soul patch, ~10 % on the moustache, none on the cheeks** (salt-and-pepper chin is an identity cue).
* Brows: dense, medium-thick (8–9 mm), straight with a slight lateral downward hook, low-set, squared inner heads 10 px apart; colour #654233 lit / #4a3228 shadow → asset recolour **#5a3d30**.

### Not present
No helmet, cap, eyewear, headset/earpiece, face paint, watch, name tapes or flag patches. Right ear (753–770 × 84–112) is bare.

---

## 4. Clothing layers

| Layer | Description | Colours |
|---|---|---|
| **Neck gaiter** | Fleece/jersey tube pushed down into 3–4 horizontal rolls filling the carrier's collar opening; spans x 745–855, y 128–200; top roll touches the jaw shadow; sits over the shirt collar and UNDER both shoulder straps (straps overlap it at y≈190–200); vertical fold descending at x≈835–850 on his left. Matte, soft, light dust on the top roll. | median **#373029**; lit folds #74675e (760,170), #7e5849 (800,150), #6c5946 (815,195); shadow #0a0704; skin-bounce top highlight #6b4a33 |
| **Combat shirt (base layer)** | Dark long-sleeve combat shirt: soft knit torso, ripstop sleeves, ribbed/quilted shoulder yoke (fine vertical ribs ≈4 mm pitch visible under both pauldrons), raised seam down the outside of the left upper arm (x 925→955, y 260→330), ripstop micro-grid visible on the left sleeve. Sleeves end inside the glove cuffs. | median **#332f2d**; lit right shoulder #49433e; shadow #040303; fold-crest sheen #6f6760–#7f7165 |
| **Combat trousers** | Crye G3/G4-style: articulated knees with integrated kneepad sleeves, reinforced shins, waistband with belt loops, centre fly (x≈810, y 475–560), large crotch gusset (780–840 × 540–600) with stress folds; articulation darts above the knees (y 575–610) with a stitched band; slim piped calf pocket/panel on the left outer shin (925–965 × 690–760); vertical seam on the right shin (x≈735–745). Cargo pockets assumed under the drop-leg rigs (not visible). **Hems loose, NOT tucked**: 2–3 heavy folds stacked over the boot collars (y 760–810), slightly tapered, no drawcord. Dust on upper thighs, grime at the cuffs. | **Dark low-contrast 4-tone blotch camo** (MultiCam Black / A-TACS LE class, 10–15 % contrast, blotches 3–8 cm, soft edges): near-black #0a0b08, charcoal-brown #171513 / #262524, olive-brown #322e29 / #3e3a35, tan #615348 / #534c3f / #685d53. Knee sleeves black #252527; cuffs #171514 / #25221b |
| **Gloves** | Hard-knuckle tactical gloves (M-Pact / SI Assault class): leather palm, stretch-knit back with carbon/honeycomb texture, moulded ribbed TPR knuckle plate across the four MCPs, TPR finger-joint pads, short neoprene gauntlet cuff with hook-and-loop. Right glove box 690–752 × 325–400; left 825–880 × 425–470. Dusty knuckle tops, shiny worn finger pads. | median **#36322f**; right back #605a55 (700,345), fingers #423e3c, dusty knuckles #8f837c–#9a8d85, shadow #0b0a09; left (cool side) median #343436, back #5f564e–#6a6059 (850,445), fingers #3c3739, cuff #444d5a; glove fingertips in shadow #161412 |
| **Boots** | 8-inch black leather/nylon tactical boots (Lowa Zephyr / Salomon Quest class): full-grain leather vamp and quarters, padded nylon collar, moulded rubber toe bumper, rubber rand, deep chevron-lug outsole (≈8 mm lugs, 1.5 cm pitch), round black laces criss-crossed with bow tucked behind the collar; **7 eyelet pairs** (5 round gunmetal eyelets + 2 speed hooks at the collar; 8 possible on the left boot); a 1.5 cm **collar strap with small buckle wrapping the ankle** (visible on the camera-facing MEDIAL side of the right boot at (745–760, 812–830) and on the LATERAL side of the left boot at (952–965, 820–838)). Boot height ≈110 px ≈ 23 cm (collar y≈800 → sole 905–912), length ≈30 cm (EU 44–45), heel sole ≈5 cm incl. lugs. **The right boot is seen from its MEDIAL (instep) side** because the foot is turned 90° to his right; the left boot is seen head-on. Dust on toe bumpers and vamp tops; scuffed quarters. | leather median **#242322**, highlight #a19689, shadow #0b0a08; left leather #2c2924; toe bumper #363231 (668,866) / #40352c (925,885), dusty cast #a6998e; outsole #26282e / #11100d, lugs #010101; bluish midsole reflection #363d4b; eyelets #37302c; laces #4a473f / #41362d |

---

## 5. Armour

All hard armour is the **same desert-tan painted polymer** (albedo ≈ **#837163**; lit #d1bbaa, highlight #c6b19f, shadow #191511) with heavy edge wear, dark grey-brown chips (#2e2b27–#453d3b substrate) and pale dust (#9a8d85–#d2c5b5) on upward faces. **Pieces on his LEFT read grey-blue (#575655 / #535354 medians) only because they sit in the cool side light** — same material (the left kneepad shows tan #948169 where the warm key reaches it). Alternative (if deliberate asymmetry is wanted): left pauldron in grey-blue steel with tan bevel rims — not recommended.

### Shoulder pauldrons — three-tier articulated (lame-style) guards on both shoulders
Parent to the upper-arm bone with ~50 % clavicle influence (they ride the deltoid). Webbing tab from under tier 1 hooks to the shoulder strap; tiers linked on the inner side; tier 3 closes with a cam buckle.

| | **Right pauldron (viewer's left)** — key-lit, tan | **Left pauldron (viewer's right)** — cool-lit, **carries the emblem** |
|---|---|---|
| Tier 1 cap plate | x 668–718, y 190–240 (≈10.5 × 10.5 cm); angular wedge sloping down/outward, 3 px bevel rim, dark slot near the top inner corner (≈710,195), two silver studs (700,200) / (683,228) with blue speculars. Face #a3998d–#999083 (690,205), rim #d2c5b5, shadowed underside #453d3b | x 895–960, y 185–250 (≈13.5 × 13.5 cm, larger because nearer/frontal). Body #767475 (915,200), #464a4f (925,235), median #535354, tan bevel rim #84807d; round rivet ≈(905,205) |
| Emblem | none | **Shield/pentagonal recess on the outer face, x 932–957, y 195–240 (≈5 × 9.5 cm)**, thin dark border, filled with a **light blue-grey brushed plate #b3c2d6 (942,212) / #97a6b9 (940,215) / median #5a6a7a, highlight #bfcedc**; on it a **white/pale X of two long diagonal strokes plus a short vertical spike (4–5-point star / crossed-blades mark), ≈2.5 cm tall, weathered**. This is NOT the UI faction logo (downward shield/arrowhead with notched chevron, #565859 at (40–110, 115–185)). Model the X-star. |
| Tier 2 | x 655–700, y 245–285 (≈9.5 × 8.5 cm), rectangular recessed panel; #a29588 / #47413c / #090605 | x 912–960, y 252–290 (≈10 × 8 cm), horizontal recess + rivet; #514f4e / #a2b3c5 / #101214. **Small clip-on box** on its outer face at (945–960, 258–280) (≈3 × 4.5 cm) **#afc2d5 (952,268)** — IR strobe / beacon / light module; lightest object on the figure after the emblem plate |
| Tier 3 bicep band | x 640–690, y 285–325 (≈5 cm tall) curved band; black elastic strap + small silver cam buckle at (640–648, 300–318) | x 905–965, y 290–335, dark, horizontal slot, ends at the ribbed yoke |

### Cylinder / antenna — behind the LEFT shoulder
At x 898–912, y 135–185 (≈3 cm dia, 10.5 cm visible), rising vertically just outboard of the left shoulder strap and inboard of the pauldron cap, mounted on the rear plate bag / upper back, ≈5° backward lean. Rounded black rubber cap (y 135–148, #111518) → brass/gold body (y 148–170, #705e46 → specular #d3caaf / #cac1ab, ring groove at y≈152) → steel lower segment (y 170–185, #757d83 / #6c6b71) disappearing behind the strap. Best read: **stubby radio antenna base/beacon** on a back-mounted radio (alt: brass 40 mm flare / chem-light). Parent to the vest back (spine_03). **It is on his LEFT, not his right.**

### Forearm guards — segmented hard-shell, both forearms
* **Right (the arm on the grip):** x 625–700, y 308–358 (≈16 × 10.5 cm), ~3 cm below the elbow to the wrist. Three plates: elbow-end band (625–645) with a silver cam-buckle loop at (633–640, 315–325); main plate (645–685) with two horizontal grooves (y≈330, 345), raised central rib, smudged black stencil (660–675 × 335–342); wrist band (685–700) against the glove cuff. Lit tan #d1bbaa (655,328), mid #7e6c5c, median #837163, shadow #191511; diagonal grey-black paint-loss streaks. Black neoprene sleeve + 25 mm straps underneath.
* **Left:** x 880–945, y 360–435 (≈13.5 × 16 cm, seen more end-on). Upper band (885–940 × 365–385); main plate (885–940 × 385–420) with vertical rib and a tiny grey inset window ≈(905,407) #4f555c; lower wrist band (900–940 × 420–435); black 25 mm strap with ladder-lock at y≈425–435 (#3c3d45). Cool-lit median #575655, lit tan #8c7a6e (893,398), highlight #897d73, shadow #1a1b1c.
* **Lateral elbow cap, left elbow only visible:** two-piece grey polymer cap on the OUTSIDE of the left elbow, x 950–968, y 335–365 (≈4 × 6 cm): slim upper fin + lower square pad, #a2b3c5-class highlights, black elastic. Matches the elbow pad in the vest icon. Right elbow hidden behind the stock — **mirror it to the right (best) or omit**.

### Kneepads — hard-shell caps in the trouser knee sleeves (Crye AirFlex / Hatch XTAK type), rear strap with gunmetal ladder-lock
* **Right:** cap x 695–760, y 615–700 (≈13.5 × 18 cm). Hexagonal/angular; **tan bevelled frame ≈12 mm wide** (#5f554f (703,650), #70645a, highlight #796c62) around a **recessed darker centre** (#2a2620 (718,660), #2f2b27) heavily pitted; "D"-slot ≈(727,625) and rectangular slot ≈(705,622) along the top edge, square bolt ≈(745,632), short slot near the bottom on the inner (his-left) side ≈(740,690). Bulges ≈2 cm, tapers downward. Black sleeve #252527; strap/buckle at (748–770, 640–660).
* **Left:** cap x 862–940, y 610–700 (≈16 × 19 cm, frontal). Same design; frame grey-blue #7a7972 (870,625) / tan where lit #948169 (872,640); centre #343532 (893,655); three top slots, one outer side slot; **small red/rose rubber tab on the outer side ≈(925–930, 636–652) #917a7b** — keep it, the only warm accent on the legs. Inner-side strap.
* Both centres 30–40 % chipped to dark substrate; dust on the upper bevel; grime in slots.

---

## 6. Load-bearing gear and pouches

### Plate carrier ("Tactical Vest")
Medium plate carrier (≈25 × 30 cm front bag) in **olive-brown 500D Cordura** (median **#463e34**, highlight #776958, shadow #0f0b09; edges bound in black webbing). Front bag x≈740–890 (≈32 cm), y≈195–**398** (≈43 cm); upper edge ≈2 cm below the collarbone under the gaiter. **The carrier rides high: between the hem (y≈398, ≈105 cm above the floor) and the belt (y≈490) ≈19 cm of trousers/shirt is exposed.** Parent front/back/cummerbund to spine_02/03 (rigid-ish with slight lag).

* **Chest admin / electronics panel:** x 745–828, y 198–240 (≈17.5 × 9 cm), angular bevelled **khaki hard polymer**, 6–8 mm proud, top edge canted (his-right end ≈4 px higher). Median **#7e715f**, highlight #a09486 / #867861 (805,215), shadow #221c15; strong paint chipping. Details: two silver domed rivets/LED studs in a vertical pair on the panel's **his-RIGHT column** (752,208) #8f8e8b and (752,221) (≈6 mm, blue-white speculars); a dark grey label plate at (770–795, 203–210) #78726d; a horizontal slot/handle recess at (768–790, 224–230) #635750; one silver rivet at the **his-LEFT lower corner** ≈(818,231); the his-left ≈40 % of the panel is a plainer field with a faint raised square boss (805–825 × 205–235); a dark recess along the lower edge (#2e2519 at (795,230)).
* **PALS rows under the panel (y 240–265):** two rows of 25 mm webbing (#625745 lit) across x 745–885; a black female side-release buckle at (745–765, 243–265) (≈4 × 4.5 cm — detachable placard); a black polymer clip/sheath-clip with a silver pin at (800–815, 243–258) (≈3 × 3 cm; alt: second buckle half).
* **Front magazine pouches:** **THREE visible closed-flap single rifle-mag pouches** at x 790–815, 818–846, 850–882, y ≈265–335 (≈6 × 15 cm each incl. flap; bottoms ≈334), ≈6 mm gaps, all on one PALS row; a **fourth inferred** at x≈755–790 behind the rifle magwell (icon supports it). Tuck flaps with a vertical centre strip; the centre pouch shows a small square buckle plate ≈(830,300); drain-grommet shadow at the bottoms. Flap #574d3e, bodies #363028 / #343029 / #332f28, highlight #5d5043, shadow #030303; dust on flap tops, grime at the bottoms.
* **Lower front (y 340–398):** two more dark PALS rows (#1a1810) carrying nothing in the centre; bound hem.
* **Shoulder straps:** two padded straps ≈7 cm wide (olive webbing stitched on a black padded base), passing over the gaiter's lower edge. **Right strap** x 725–760, y 160–255: median #6d5f50, highlight #b4a697, shadow #0c0804; **three dark gunmetal ladder-locks** stacked at y≈165–185, 200–215, 232–250 (one every ≈7 cm) with a loose webbing tail (#140f06 at (745,170)). **Left strap** x 822–858, y 160–255: median #443d36, highlight #958a7f; one large tri-glide at (835–860, 165–185) #322d29, two smaller at y≈205 and 240, black elastic keeper loop at the top (805–830, 150–175); rear bag edge visible at (890–930, 165–195). Left side panel (862–885 × 220–290) near-black #1d1c1b with a PALS row and a small olive/grey pouch at (875–895, 265–295).
* **Cummerbund:** black/dark-olive, 3 PALS rows, ≈2 cm thick, visible on his left at (840–900, 360–400) with ladder-lock slots and ribbed padding; shadowed under the right arm at (700–740, 380–400).

### Belt
Black nylon **rigger belt**, y 490–512 (≈4.5 cm), visible at x 700–760 and 850–880 (centre hidden behind the magazine). Median **#22211f**, shadow #090908, dust highlight #766352. Buckle hidden behind the magazine (x 765–800) — best guess flat cobra/quick-release, offset slightly to his right; a silver keeper glint at (750,500). Trouser waistband seam y≈475–490, belt loops ≈x 805 and 850. Carries both drop-leg hanger straps (right from (690–700, 505); left behind the left pouch at (905–915, 480–500)). Thin keeper tails hang at (668–682, 575–605) ending in tan metal tips.

### Right side (viewer's left)
* **Upper right two-cell pouch:** x 682–722, y 395–470 (≈8.5 × 15.5 cm), ABOVE the belt beside the lower ribs — on the carrier's right lower side PALS / cummerbund. Two slim vertical tubes with tan/khaki polymer face plates and black polymer bodies, a lid per cell with a silver snap at ≈(700,420) and (712,420), black elastic retention strip between. Box median #21201b, highlights #786756 / #6f6251 / #574d45, shadow #020100. **Best read: double pistol-magazine pouch** (alt: double 40 mm / shell pouch).
* **Right drop-leg platform with twin tall open-top polymer carriers:** x 662–735, y 482–600 (≈15.5 × 25 cm total; each tube ≈5 × 23 cm; inner tube slightly taller, top y≈482 vs 490). **Tan/FDE face plates** (#816f5f highlight, #4c4034 (690,540), #584631, #554a40, #69574b) riveted to **black polymer bodies** (#2a2622, #2d2a29, shadow #070604), 3–4 horizontal vent slots per face, a round rivet near the top, stencil marks, black bungee tension cord. **Two flat black 1.5-inch thigh straps** at y 520–536 and 560–580 (medians #171615 / #141313, highlight #393632) with gunmetal ladder-locks on the front of the thigh at ≈(733,527) #4c4943 and (733,567); tails to (668–682, 575–605). Black hanger strap from the belt at ≈(695,505). **Best read: twin open-top rifle-mag carriers (his two spare mags)**; alt: tourniquet/flashlight holders or 40 mm tubes. **NOT a pistol holster.**

### Left side (viewer's right)
* **Left drop-leg two-cell block:** x 905–960, y 462–560 (≈11.5 × 21 cm). **Inner cell (905–935):** olive Cordura/polymer box with top flap and square metal snap at (930,478) #565955, vertical ribbed face #4b5358 (cool-lit), shadow #080806 — **frag-grenade pouch** (matches the "Frag Grenade" utility slot; no grenade is rendered — do not expose one). **Outer cell (935–960):** grey hard polymer box #363a3b (948,505), highlight #53595b, hinged lid, vertical rib, small latch — **radio/GPS hard case / rigid utility box**. Top surface #4e504d. A further dark item/strap behind at (900–915, 540–560). **One black 1.5-inch thigh strap** at y 560–580 (x 830–900; #312d29, shadow #050504), buckle ≈(840,570); the block hangs just above it.

### Loadout-card icons vs the figure — the figure is authoritative
| Card | Icon | Figure | Verdict |
|---|---|---|---|
| ARMOR – Tactical Vest | lighter grey-khaki carrier, 5 pouches, no pauldrons/forearm guards, black crew-neck, grey elbow pad on the soldier's LEFT elbow | olive-brown carrier, 3 (+1 hidden) pouches, pauldrons + forearm guards, gaiter, left elbow cap | follow the figure; icon only confirms the hidden 4th pouch and the left elbow cap |
| UTILITY – Frag Grenade | olive Mk 2 pineapple (#4b4634 body, #414342 fuse) | none visible | inside the left-hip flap pouch; do not model an exposed grenade |
| SECONDARY – P9 Sidearm | P226-class pistol with rail light | **no holster or pistol anywhere** | omit, or hide a holster at the small of the back (invisible from the front); flagged to orchestrator |
| PRIMARY – AR-12 Carbine | tube red-dot on top, long underbarrel module, 9 in handguard | no optic above the rail, side-mounted light, 13 in handguard | see §7 |

### Items explicitly NOT present
No helmet, eyewear, headset, watch, knife (unless the black clip at (800–815, 243–258) is a sheath clip), pistol/holster, exposed grenade, backpack visible from the front, name tapes/flag patches (the shoulder emblem is the only insignia), hydration tube, sling.

### Weathering summary
Dust heaviest on upward-facing tan armour and glove knuckles (highlights to #d2c5b5), medium on boot toes/vamps (#a19689), light on dark Cordura (#776958 highlights). Paint chips 2–8 mm on panel edges, pauldron bevels, kneepad centres (worst), forearm-guard ribs, exposing #2e2b27–#453d3b. Soot/grime streaks on the right forearm guard, pouch bottoms, trouser cuffs, boot quarters. Fabric sheen on fold crests; stress whitening at the crotch gusset. Gunmetal buckles with bright worn edges; silver rivets with blue speculars.

---

## 7. Weapon

### Identity and recommendation
The held "AR-12 Carbine" is an **AR-15 / M4-pattern carbine**: flat-top upper with a continuous Picatinny top rail, separate lower with STANAG-type magazine, carbine buffer tube with a **skeletonised polymer stock**, free-float **octagonal 13 in handguard with a row of large round lightening holes on the lower facets**, 30-round ribbed magazine. **Build the HELD rifle's proportions, handguard and accessories** (hero view); take the icon's single-barrel muzzle, trigger guard, pistol grip and (optionally, low-mounted) optic; use real AR-15 dimensions wherever the render is internally inconsistent.

### Pose of the rifle (camera sees its RIGHT / ejection-port side)
Butt-plate centre B (695,268) → muzzle tip M (903,570): 365 px projected ≈ 77.5 cm; **bore ≈56° below horizontal toward his LEFT in the image plane** (pose 57°, weapon 55.4°), **muzzle ≈25° toward the camera** (true length ≈85 cm). Muzzle direction: pitch ≈50° down, azimuth ≈50° to his left of the camera axis; Blender unit vector ≈ (+0.49, −0.42, −0.76). Rifle "up" (top rail) points up-and-to-his-left in the image; the magazine hangs down-and-to-his-right. Roll about the bore ≈0.

| Landmark | full px | Landmark | full px |
|---|---|---|---|
| Butt heel / toe | (706,243) / (683,296) — plate 12 cm tall, raked ≈15° | Handguard rear end / front cap | (793,402) / (873,512) — 31.5 cm along the bore |
| Buffer-tube rear cap | (705,243) | Lower-facet vent holes #1…#7 | (822,447) … (853,510), pitch ≈2.6 cm, Ø 1.3–1.5 cm |
| Stock/receiver junction | (748,300) | Right-face screws | (851,478) (855,486) (860,497) |
| Charging-handle rear | ≈(752,312) | Weapon light rear / front | (813,362) / (832,394), Ø 2.9 cm, 8.6 cm long |
| Tan QD plate centre (stock) | (741,330) | Thumb across top rail | (850,445) |
| Ejection port | (778,358)–(802,392), open, dark | Bronze muzzle tube start / end | (868,512) / (896,571) |
| Mag-release button glint | (764,384) | Muzzle tip (top rod) | (903,570) |
| Magwell top / mag baseplate centre / outer corner | (770,405) / (748,455) / (731,445) — magazine x≈725–775, y≈400–462, 11.6 cm protruding | Pistol grip (hidden behind the hand) | est. centre (735–742, 395) |

Distances from the body: butt in contact with the vest over the right pectoral (0–3 cm); grip ≈13 cm in front of the chest; magazine bottom ≈15 cm in front of the lower abdomen just above belt height; handguard mid ≈20 cm in front of the left hip; muzzle ≈25–35 cm in front of the left thigh at its outer edge, 69 cm above the floor (≈12 cm above the left kneepad top).

### Render inconsistencies — do NOT copy
The top-rail band sits ≈10 cm above the B–M line (real: rail ≈3 cm above bore); the three "muzzle" tubes exit from the lower third of the handguard face; the weapon light straddles the receiver/handguard joint. Build real geometry: bore centred in the handguard, rail 30 mm above bore, one barrel, light fully on the handguard.

### Master dimensions (real parts chosen to match the hero silhouette)
OAL **860 mm**; barrel **16 in / 406 mm** government profile (Ø 19 mm at the muzzle) with a **64 mm burnt-bronze A2 birdcage / 3-prong device** → 130–140 mm exposed beyond the handguard (held: 138 mm); handguard **330 mm (13 in)**, octagonal, 45 wide × 55 tall incl. rail; flat-top upper 205 × 70 × 60 mm; lower 200 mm incl. grip boss; buffer tube Ø 29.2 × 210 mm (stock fixed at position 3 of 6, ≈16.5 cm of tube exposed); stock body 180 × 133 × 45 mm (MFT BATTLELINK Minimalist class); magazine 30-rd, 190 mm total, 120 mm protruding, 70 × 24 mm section; rail MIL-STD-1913 (10.01 mm pitch, 5.23 mm slots, 3.0 mm deep); M-LOK slots 32 × 7 mm on a 20 mm module.

### Component decisions (held → icon → build)
| Component | Held rifle | Icon | Build |
|---|---|---|---|
| Stock | skeleton stock under a fully exposed glossy buffer tube; large trapezoidal window (688–712 × 265–300); **tan stripe** along the upper body below the tube (≈1 × 7 cm, (718,281)); **tan rectangular QD/sling-slot plate** at (730–752, 308–350) (≈3 × 7 cm); scuffed cheek rest; dark butt plate #141211, no ribbing resolved | same family, one big window, tan stripe near the top, 4.5 cm dark rubber pad, tube hidden | HELD; add the icon's angled rubber butt pad; one QD socket Ø 9 mm in the tan plate |
| Buffer tube | semi-gloss black, Ø 2.7 cm projected, rear cap protrudes ≈1 cm past the heel | hidden | mil-spec Ø 29.2 × 210 mm, roughness ≈0.35, castle nut + QD end plate |
| Lower receiver | grey-black forged; mag-release button on the right at (764,384); index finger along the right face; flared magwell lip (750–790 × 400–410); tan marks at (774,390) (≈0.7 × 3 cm) and a gold rivet patch at the magwell front (792,417); grip and trigger hidden | A2/MOE grip swept ≈20°, rounded-rectangular trigger guard, two stacked gold plates above the mag | standard AR lower; A2-shape grip 102 mm (icon); standard guard (icon); Ø 8 mm mag release right (held); one 15 × 40 mm tan plate on the right magwell face + rivet patch; bolt catch and selector on the LEFT (standard), optional ambi paddle right; takedown pins both sides |
| Upper receiver | flat-top; charging-handle rear bump at (752,312); **ejection port OPEN** (dark cavity 8.8 × 2.7 cm projected, glossy bolt-carrier glint at (793,384), no door hanging); **tan vertical panel behind the port** (752,305)→(768,345), ≈1 × 8.5 cm, #d4a271 — where the icon has its blue window; forward assist / deflector not resolved | continuous rail; **light-blue glowing window** (178–197 × 249–257) #80a8c2–#98c1de; closed glossy port 6.2 cm | M4 flat-top 205 mm; standard forward assist (Ø 16 mm) and brass deflector on the right; **mil-spec charging handle with the standard LEFT-side latch** (or ambi); port 79 × 23 mm **open, door down**, bright bolt carrier #8a8a8a inside; **tan 10 × 85 mm FDE panel** behind the port (photoreal) — OR a recessed 60 × 20 mm dim blue emissive #80a8c2 if the sci-fi cue is wanted, not both |
| Top rail | continuous ribbed band receiver→handguard front, parallel to the bore; rim-lit blue-grey #283547 (shadow) → #697b97 (872,438); lit tops #78706d; the "braided" look in crops is Lanczos ringing on the 10 mm pitch, not paracord | same, slotted | MIL-STD-1913 continuous over receiver and handguard (aligned), T-numbers optional, no rail covers |
| Optic | **none above the rail** | CompM4-class tube red dot on a high mount (≈12.7 cm long, 5.8 cm tall incl. mount) | **Option A (preferred):** compact micro red dot (T-2 class, 68 × 30 × 36 mm) on a low mount (≈45 mm above rail) at the receiver front, black, faint blue lens — vanishes against the dark vest from the hero angle. **Option B (icon-exact):** CompM4 on a 72 mm mount, accepting that it protrudes where the render shows nothing |
| Iron sights | none | none (tiny stub at the handguard front-top could be a folded sight) | none; optional folded polymer BUIS (12 mm folded) |
| Handguard | free-float octagonal, 31.5 cm; right face flat, lit warm grey #5e5040 (812,430), median #393532, 2–3 dark elongated M-LOK slots at (812–845 × 425–470), **3 bright socket-head screws** near the upper edge toward the front (#929194, peak #d6d6d8, ≈25 mm apart); lower facet **7–8 round vent holes** Ø 1.3–1.5 cm at 2.6 cm pitch (interiors #2b2927, facet between #0d0a08); tan patches at (809,426) #685840 and (799,408) #312e28 (≈1.5 × 2 cm); bevelled blue-lit front cap #596672 (peak #92a1b0) | 22 cm (9 in), 7 big holes Ø 1.7 cm at the same 2.6 cm pitch with bright bare-metal rims #9e9897, slot row on top, gold patch at the rear-top #957d62 | **330 mm**, octagonal 45 × 55 mm, matte dark grey #393532 with warm dust; M-LOK at 3, 9 and 6 o'clock; **Ø 14 mm vent holes at 26 mm pitch on the 4:30 and 7:30 facets** (8 per side, from 125 mm behind the front); 3 Ø 5 mm screws on the right face near the top at 190/215/240 mm from the rear; two tan patches 15 × 20 mm rear-top right; front cap chamfered 3 mm |
| Weapon light | cylinder on the **rifle's right side**, top edge level with the top rail, (813,362)→(832,394): **8.6 cm long, Ø 2.9 cm**, centre (822,378); knurled tail cap (rear 1.5 cm, #46433a), body #302f30, highlight #8f8b84 / peak #c9c6be, bezel face in shadow #020000; no cable resolved | none | **SureFire M600-Scout-class**: body Ø 25 mm, bezel Ø 35 mm, 110 mm long, knurled tail cap 18 mm, black hardcoat #302f30, on an **offset M-LOK mount at 1:30 o'clock in the rearmost handguard slot**, tail cap 10 mm forward of the receiver face |
| Underbarrel | **nothing** — bare C-clamp grip | long ribbed PEQ/DBAL-type module 20.6 × 4.8 cm (#181a19 / #363636) | **none** (would collide with the left hand); PEQ-15-class box only for a stowed/third-person variant |
| Barrel / muzzle | **three parallel tubes** (AI artefact): glossy blued top rod Ø 1.1 cm (#4d5f73 → specular #d2dff1) to (903,570); **central bronze tube Ø 2.1–2.3 cm with 2–3 ring grooves, #5f4c3e / #6a5344**, dark mouth #15191d, to (896,571); lower rod Ø 1.0 cm #554f4b to (878,565); 13.8 cm exposed | single barrel Ø 1.7 cm #5d5b5c + black birdcage flash hider 6.9 × 3 cm #0f1315, 19 cm exposed | **single 16 in government-profile barrel**, dark parkerised steel #2a2c30 with a glossy blued look (roughness 0.25, anisotropic highlight, blue rim light in look-dev); **A2 birdcage (or 3-prong) flash hider 64 mm × Ø 22 mm in burnt-bronze PVD #5f4c3e–#6a5344 with 2 ring grooves**; 130–140 mm exposed; low-profile gas block 190 mm from the receiver face inside the handguard; no side rods |
| Magazine | straight box, 11.6 cm protruding, 6.6 cm deep, **3 longitudinal ribs** catching light (#625a56 at (752,431)), body #3f3c36 lit / #464440 shadow / median #423e3a, 3–4 mm baseplate band #595452 (worn aluminium look), no windows, no curve | 16 cm (40-rd look), 4 ribs, slight curve, bright baseplate edge, rounded lower-front corner | **30-rd STANAG-size, 190 mm total, 120 mm protruding, 70 × 24 mm**, straight ribbed body with **3 ribs per face**, #3f3c36 with rib edge wear #625a56, 4 mm steel-grey baseplate #595452; rounded baseplate corner from the icon |
| Sling | none (QD plate on the stock is the only sling hardware) | none | none; QD sockets only: stock tan plate, receiver end plate, handguard left side at 250 mm from the rear |

### Finish palette (held rifle)
| Part | Hex | Note |
|---|---|---|
| Upper receiver | **#413c3b** median, lit edge #686463, shadow #44413e | matte anodised, edge wear 1–1.5 stops lighter |
| Lower receiver | #403c39 median, darkest #262321 | same |
| Stock body | **#3d3733** median, lit cheek #5e4f44 (725,290), butt #141211, scuffs #5e4f44→#8d8787 | matte polymer |
| Buffer tube | shadow #534232 (dusty warm) / #807a75 / highlight #aba6a6–#b5b0b1 / peak #ece7e9 (741,297) | semi-gloss hardcoat |
| Tan/FDE accents (6 places) | stock stripe #a68869 (peak #c1a27f); stock QD frame #bf9c70 (peak #cea676, interior #86694f); **upper rear panel #d4a271 (brightest)**; lower small mark #736456; magwell front #8d764b; handguard rear-top #685840 / #312e28 | hand-brushed FDE **#b8905f** albedo with 20–30 % chipping; icon shows them duller (#88745b–#917652) |
| Magazine | #423e3a median, lit #3f3c36, ribs #625a56, baseplate #595452 | worn grey |
| Handguard right face | **#393532** median, lit #5e5040, mid #36332f, between holes #0d0a08, hole interiors #2b2927, screws #929194 | matte, warm dust |
| Top rail | #283547 (shadow) → #697b97 / #6d7e9d (rim-lit) / #78706d (lit tops) | blue rim light from his left |
| Weapon light | #302f30, highlight #8f8b84 / #c9c6be, tail #46433a | black hardcoat |
| Barrel / steel parts | #4d5f73 / #575f6e, specular #d2dff1 | glossy blued, blue-tinted specular |
| Bronze muzzle device | **#5f4c3e – #6a5344**, mouth #15191d | burnt bronze, ring grooves |
| Ejection port interior / bolt carrier | #3e3a39 median, glossy glint | bright steel |
| Mag-release button | #676261 (peak #c0bbbb) | bare steel |

Blender build frame: origin at the bolt face on the bore axis at the receiver face; +Y toward the muzzle, +Z up, +X toward the rifle's right (ejection side); rail top Z +30 mm; mag baseplate Z ≈ −190 mm; stock toe Z ≈ −95, heel ≈ +25; handguard 0 → 330 mm; light 10 → 120 mm at (X +40, Z +15) rotated 45°; vent holes 205 → 330 mm; screws at 190/215/240 mm, Z +20; gas block 190 mm; muzzle ≈370 mm, device 370 → 434 mm; upper receiver to −205 mm; ejection port −160 → −81 mm, Z −5 → +18; forward assist −175 mm, X +30; mag release −120 mm, X +28, Z −20; tan upper panel −200 → −115 mm; buffer tube −205 → −415 mm; butt pad at −415 mm, 12° rake. Material slots: anodised grey #3d3936 + edge-wear mask; black semi-gloss hardcoat; black polymer; FDE #b8905f + chip mask; burnt bronze #5f4c3e; blued steel; optional blue emissive.

### "P9 Sidearm" (icon only)
SIG Sauer **P226/P229-class DA/SA 9 mm**: external hammer, rounded slide with 5 angled rear serrations (no front), bead-blasted grey slide #4f5050 (top #868788), darker frame #3a3a3a, stippled black polymer grip #343434, rounded trigger guard with slight hook, rail-mounted compact light (TLR-1/X300 class, #181818). Icon proportions are stretched (OAL/height 1.78 vs real 1.40) — **build a real P226 (196 × 140 × 38 mm, 112 mm barrel)**. **No pistol or holster is visible on the soldier**; omit it from the body or hide a small-of-the-back holster at the 5–6 o'clock position on the rigger belt.

---

## 8. Scene & lighting

### Camera (adopted: lighting analyst's solution; pose analyst's range is compatible)
| Quantity | Value | Range |
|---|---|---|
| Render size | 1672 × 941 (or 1920 × 1080; aspect 1.777) | — |
| Figure in frame | 875 px = 93 % of frame height; stance centre x≈830 vs image centre 836 → **yaw 0, no lens shift** | hard |
| Horizon (eye level) | **y ≈ 615** | 585–650 (pose analyst read 580–610) |
| Camera height | **0.60 m** (≈ knee height) | 0.54–0.67 m (pose: 0.65–0.70) |
| Camera pitch | **+3.9° up**, roll 0 | 3.1–4.8° (or level camera with shift_y −0.087) |
| Focal (36 mm sensor) / distance | **46 mm at 4.50 m** (f_px ≈ 2130; HFOV 42.8°, VFOV 24.9°); invariant f_px = 473 × D | 42–54 mm / 4.3–5.3 m; round alternative 50 mm at 4.91 m |
| Face seen from below | **≈13°** | 12–15° |
| Depth of field | focus on the figure (face, hands, boots, near floor sharp); far bokeh discs ≈15 px → **f/1.5** (f/1.6 at 50 mm); mid-background (≈10 m) ≈8 px blur; soft Gaussian-like discs | f/1.3–1.8 |
| Vignette / CA / grain / distortion | none measurable (vignette ≤ 0.15 EV if any) | — |

Blender: camera at **(0.00, −4.50, 0.60)**, rotation (93.9°, 0, 0), lens 46 mm, sensor 36 mm horizontal, DOF focus (0, 0, 1.30), f/1.5, blades 0. Verification overlay: skull top y=20, right sole y=895, pupils (800,77)/(832,77), stance centre x≈830, far floor line y≈690.

### Lights
| Light | Direction (from the chest at (0,0,1.3)) | Colour | Size / softness | Blender (world m) | Calibration targets |
|---|---|---|---|---|---|
| **KEY** — warm, from his RIGHT-front-above (viewer's upper-left) | azimuth ≈40° to the viewer's LEFT of the camera axis (toward −X), elevation ≈42° (face analyst: el 40–50°, az ≈40°) | **4500 K** (±300), linear ≈ (1.00, 0.77, 0.56), sRGB ≈ #ffe4c4 | large: 1.5 m area at 3.5 m; nose/chin shadow edges soft over ≈1 cm | Area 1.5 m at **(−1.70, −2.00, 3.60)** → (0,0,1.25), 800 W | right temple (778,70) #e6bfac; right cheek (792,100) #d19b87; admin-panel top (800,220) #897967; rifle receiver spec (760,330) #9e8976 |
| **COOL SIDE** — steel blue, from his LEFT, slightly behind, broad | azimuth ≈100° (viewer's right, 10° behind the shoulder plane), elevation ≈35°; wraps onto the left pauldron front and reaches the left shin | linear **(0.55, 0.76, 1.00)**, sRGB-normalised ≈ #c4e2ff (≈12 000 K look) — same family as the hangar lamps (#e4f2fa / #bad8eb) and their floor reflections (#98b0c5) | very soft: 3 m area at 4 m, no hard terminator | Area 3.0 m at **(3.20, 0.60, 3.60)** → (0,0,1.00), 600 W | emblem-plate/left-pauldron front (940,240) #768ea5; left shin (935,720) #333b47; left forehead (835,52) #93878d (with key) |
| Rim / kicker | none dedicated (hair top #35271e, left jaw edge #272a2b — only a faint cool rim) | optional cool kicker ≤ 12 % of key from az 150°, el 45° | — | Area 1.0 m at (1.80, 3.00, 3.80), 100 W, optional | — |
| Ambient / world | very low, cool: ≈5 % of key, colour ≈ (0.6, 0.75, 1.0) | dark industrial HDRI at strength 0.05–0.10 tinted cool, brightest part behind-right of the character | — | — | unlit right shin (760,730) #151517; right thigh (760,560) #110f0e; under-jaw (812,140) #110b06 |
| Floor bounce | weak/uncertain (see Disputes #9); the deep under-jaw rules out any strong uplight | optional warm under-fill 5–8 % of key | — | Area 1.0 m facing up at (−0.30, −1.00, 0.05), 40–60 W, optional | must leave the under-jaw ≈ #110b06 |
| **FLOOR POOL** — warm spot on the floor only | ellipse ≈1.3 m wide centred ≈0.4 m in front of the feet and ≈0.17 m toward his right, extending off the bottom of frame; half-brightness radius ≈0.6–0.7 m; not the key's mirror reflection — a separate game spot | 4500 K (reads ≈5000 K on the cool concrete) | spot radius 0.3 m, cone 24°, blend 0.7 | Spot at (−0.90, −2.40, 4.20) → (−0.20, −0.50, 0), 500 W, **light-linked to the floor only** | floor (830,885) #c9baaa; (600,890) #87786a; (480,930) #4b453f; peaks 231–237 at (666,907) / (788,922) |

Irradiance ratio at the figure KEY : COOL : WORLD ≈ **1.3 : 1 : 0.05**; floor pool ≈0.6 × key on the floor. **No body shadow is visible on the floor** (generator inconsistency) → shadow-link the key off the floor, or raise the key to el 55°. Contact shadows under the soles: true-black core (0–8 lum) directly under the soles, soft asymmetric penumbra 15–30 px (3–6 cm) toward the viewer's left, 5–10 px toward the right; the dark smudges below each boot (lum 50–80) are **glossy-floor reflections of the boots**, not shadows.

### Floor
Dark, slightly cool grey sealed/polished concrete in large slabs with recessed dark seams and a few flush steel grating strips; semi-gloss (lamp reflections stretch ≈2.5× into vertical streaks; at grazing angles reflections reach lamp brightness). Slabs ≈1.5 × 1.5 m (±0.3 m) on a **sheared grid: one seam set parallel to X (image-parallel, at y≈746/776/808 right and 772/801/852/895 left), the other at ≈55° to X** (converging to ≈(2330,615)); seams 15–20 mm wide, 5–10 mm deep; one recessed grating strip ≈0.3 × 1.6 m at image (1100–1262, 805–837) → world (+1.0, +1.7, 0). Floor depth map: y=941 → 3.9 m from camera; 895 → 4.5 m; 850 → 5.4 m; 800 → 6.9 m; 750 → 9.5 m; 700 → 15 m; 690 → 17 m.

Colours: unlit slab **#32373e** (1300,930) / #393c3c / #3f4349; warm pool #c9baaa–#d1bca3; cool reflection streaks #98b0c5–#bccfde; seam #464548 (≈25 % darker than the slab); grating #646870; mottled patches #817976 / #625e5b; near slab beside the pool #87786a (600,890), #6a5f53 (560,930), #4b453f (480,930); brightest floor between the feet #d8c5b2 (830,880) / #e7d4bf (820,850). **Principled BSDF:** Base Color #4a4b4e (±20 % large soft mottle + fine grain), Roughness 0.30 (map 0.22–0.45), IOR 1.50, Metallic 0, optional Coat 0.1 (roughness 0.2), Bump 0.05–0.1, seams #222326 in colour + bump, anisotropy 0.

### Background (camera-relative; Z = distance along +Y, X lateral (+ = his left), H height; ±20 %)
Hangar ≈40 × 40 × 10 m; far wall Z ≈17–20 m (hazy #4f5455); ceiling trusses #161918 / #0c1014 at H 5–8 m from Z 12–25 m. **Viewer's left (his right):** crate stack with 4 helmets at Z ≈9.5 m, X −3.5…−1.05 m, crates 0.7 m + tier to 1.15 m (#45413d, #404a53, #151b20, labels #3d474e), helmets 0.28 m (black #22211f, grey with blue-white visor glow #b4b8bc, olive-gold #68543a, tan #483e2f); steel racks with hanging gear behind (Z 11–12 m, H 1.5–3.5 m, #1a1a1a / #262219 / #5a5144); lit pillar 0.4 m wide at X −1.55, Z 12 with a warm lamp at H 3.45 (#f4f3ee); dark steel columns Z 10–14 m (#141b1d, #161614, #212932). **Viewer's right (his left):** dropship/shuttle hull, nose at Z ≈11 m, X +0.85 m, running back to Z ≈18 m, X +7 m (axis ≈48° to X), belly H ≈0.8 m, top ≥4 m, angular panelled grey (#1b1f28, #242627, #363737 lit, nose shadow #121619); its lamps: landing light 0.22 × 0.1 m white #f2f2f2 at (X +1.5, Z 11.5, H 1.7), small warm lamp #faecc8 at (X +1.3, Z 11.5, H 1.95), upper window 0.6 × 0.25 m #e4d4c2 at (X +2.1, Z 13, H 3.0), lamps #edf6fb / #e2edf2 further back; boarding stair 1.2 m wide, 3 m tall, 35–40° at Z ≈15 m, X +4.25…+5.7 m with strip lights #9caec2–#c4dae7 on both stringers and base lamps #eff4fb / #c1dfef; orange tube lamp 0.4 × 0.1 m (core #f9f6f3, glow #f1e6d7, floor reflection #ead3b8) at Z 15, X +3.7, H 1.0; dark-red case ≈0.6 m tall at Z 6.9, X +2.8 (#443031 / #4a1a1a / #0f0707); far crate rows 1.0–1.2 m at Z ≈17 m (#3b3f42, #1b2126); far frosted panel light 0.22 × 0.33 m #aec7d7 at (X +2.25, Z 17, H 1.4) and vertical strips #c5dbea at (X +3.2, Z 17, H 0.6–0.8); ceiling lamps 0.4 m #e4f2fa at H ≈6 m, Z 15–25 m, ≈4 m spacing. Scale check: a 0.29 m helmet → ≈60 px wide; dropship belly edge y≈560–580 across x 1000–1400; far wall/floor line y≈690.

### Grading
Low-key, high-contrast, desaturated (saturation median 0.21); **blacks crushed to 0** (2.2 % of pixels ≤ 5; luminance percentiles 1 %: 2, 50 %: 42, 99 %: 212); mild teal-and-orange split (shadow mean RGB (20.9, 23.1, 24.2), highlight mean (204.3, 192.5, 179.6)); ACES/AgX-style highlight desaturation (lamp cores → near-white, haloes keep colour); mild bloom (≈8 px halo on small lamps, ≈30 px glow on the orange lamp) plus far-hangar haze (far wall lifted to #4f5455). **Blender:** View Transform **AgX**, Look **"AgX – Medium High Contrast"**, exposure 0, gamma 1 (never Standard). Compositor: Color Balance Lift (0.985, 1.0, 1.025) / Gain (1.035, 1.0, 0.96); Saturation 0.92; RGB Curves input 0.02 → 0; Glare Fog Glow threshold 2.0, size 7, mix −0.8; volume haze density ≈0.004 (or depth fog to #2c3238, 0 % at 5 m → 40 % at 20 m); no vignette, grain or CA.

---

## 9. Disputes resolved

Checked against the full image and the crops; pixel values re-sampled by the consolidator.

1. **Left/right convention.** All five files declare and overwhelmingly use the soldier's own left/right. Verified against the image: **right hand on the pistol grip, left hand on the handguard; emblem plate and clip-on box on the LEFT pauldron; brass cylinder/antenna behind the LEFT shoulder; right foot turned out to his right (profile), left foot forward toward the camera; head turned to his LEFT.** Viewer-relative slips found and corrected (see each file's Errata): gear §4.2 admin-panel "left column / lower right / right 40 %" (→ his-right column / his-left corner / his-left 40 %); gear §13 "bottom right" slot on the right kneepad (→ inner, his-left side); gear §14 right boot "seen from its lateral/outer side" (→ **medial/instep side faces the camera** — a right foot turned 90° to the right shows its inside); weapon §1 and gear §15 "magazine/muzzle down-left" (image-relative; → toward his right hip / his left thigh).
2. **Hair top: y=14/20 (pose) vs 22 (gear) vs 29 (face).** Luminance scan finds hair pixels from y=12–14 (spike tips at x≈812–814) and a solid hair mass from y≈16–20. The face analyst's crop starts at full y=30, so its "hair top y=29" was clipped. **Adopted: spike tips y=14, hair mass y=20; head 109 px (skull top → chin 129).** The face note's "hair top 19 px above the trichion" becomes 28 px (mass) / 34 px (spikes), which includes the skull dome; the 35–45 mm hair-length estimate stands.
3. **Iris colour: "reads blue-grey" (pose) vs "brown-grey, not blue" (face).** Re-sampled: right iris mean #5d3e34, left #493735, R/B 1.4–1.8, **zero blue-hue pixels**. Face analyst upheld: **dark warm brown-grey / grey-hazel (#5b4a3e albedo)**; the light-eyed impression is a thumbnail contrast illusion.
4. **Head yaw: 17° (face) vs 22° (pose).** Both relative to the camera axis; overlapping ranges. **Adopted ≈20° ±5° to his left** (≈15° head-on-neck, ≈25° vs chest).
5. **IPD 31 px (face) vs 33 px (pose); eye line y=77 vs 78.** Adopted **32 ±1 px (≈66 mm), y≈77**.
6. **Vest hem: y=460 (pose, "bottom of mag pouches") vs y≈400 (gear).** Luminance profiles at x=832/866 show lit pouch bodies to y≈332, a dark pouch-bottom shadow y≈336–356, lower PALS to y≈388, and a very dark band y≈392–410 before trouser texture. **Adopted: front mag-pouch bottoms y≈334 (pouches ≈265–335, not 265–320), vest front-bag hem y≈395–400 (≈105 cm above the floor); y≈460 is the bottom of the RIFLE magazine.** The pose note's long-torso argument is unaffected (it rests on crotch/knee landmarks).
7. **Magazine extent: (762–795, 365–462) (pose) vs magwell (770,405) → baseplate (748,455), corner (731,445) (weapon).** Scan at y=430–458 shows the magazine's dark metal at x≈725–775, nothing at x>780. **Weapon analyst adopted**; the pose note's x-range was the lower receiver/magwell.
8. **Pose §8 colour-sample mislabels.** (805,30) "hair top #19120d" is the background/gap above the spikes (lum 11) — use the face analyst's hair percentiles; (725,270) "buttstock cheek rest #908b8b" is the buffer-tube specular (re-sampled #aba6a6, lum 204) — the stock body is #3d3733; (795,230) "vest chest plate #362b1f" is the dark recess at the admin panel's lower edge — the panel is #7e715f, the Cordura #463e34; (940,215) "left shoulder pad, lit face #a6b5c6" is the **emblem plate** (#97a6b9 re-sampled) — the pauldron body there is #767475 / #464a4f.
9. **Lighting §2.1 "vest pouch underside (835,455) #54504d → floor bounce".** (835,455) lies inside the left glove (825–880 × 425–470); re-sampled #524e49 = the back of the left glove's fingers, lit by the key. "Vest pouch front (830,420)" is the dark vest side/cummerbund. The floor-bounce inference is therefore unsupported by that sample; **UNDER FILL stays optional/off**, and the deep under-jaw (#110b06) still argues against a strong uplight. Lighting §1.2's "we look up at the undersides of the vest pouches (y≈455)" is the same error (pouches end at y≈335).
10. **Lighting §2.1 "left pauldron front (steel) (940,240) #768ea5".** The sample sits at the lower edge of the emblem plate, a genuinely lighter blue-grey material; the pauldron itself is the same tan polymer as the right one, seen under the cool light (gear §5, supported by the left kneepad reading tan where the key reaches it). The cool-light colour (0.55, 0.76, 1.0) still stands from the left shin (#333b47) and floor-streak (#98b0c5) samples; #768ea5 remains a valid render target for that pixel. Lighting §2.2 "his RIGHT elbow pad (640,320)" is the right forearm guard's elbow-end band; no separate right elbow pad is visible.
11. **Pauldron colour asymmetry (gear ambiguity #1).** Resolved as **same desert-tan material on both shoulders**, grey-blue appearance on the left = lighting; emblem plate and clip-on box are a genuinely lighter material.
12. **Left-hip pouches: "two soft olive-grey pouches" (weapon §5) vs "olive flap pouch + grey hard polymer box" (gear §11).** Gear's closer read adopted (frag-grenade flap pouch inner, hard utility/radio box outer).
13. **Weapon §3.4 "charging handle with a right-side-only latch".** The mil-spec AR-15 latch is on the LEFT side; corrected to a standard left latch (or ambi). The bump at (752,312) is the handle's rear, visible from the right regardless.
14. **Camera: 46 mm / 4.5 m / 0.60 m / horizon 615 (lighting) vs 45–50 mm / 4.3–4.7 m / 0.65–0.70 m / horizon 580–610 (pose).** Compatible; the lighting analyst's full solution is adopted with the combined ranges (horizon 585–650, height 0.54–0.67 m).
15. **Scale: 875 px / 8.0 heads / 4.72 px/cm (pose) vs 890 px / 7.8 heads / 2.1 mm/px (gear) vs 103 px head (face).** Pose adopted (skull top 20 → right sole 895); the gear note's mm figures are ≈1 % high (negligible); the face note's 2.1 mm/px head scale is anchored on IPD/ear and stands.
16. **Shoulder width 322 px (pose, 640–962) vs 310 px (gear, 655–965).** Silhouette scan at y=200–210 gives 320–323 px. **Adopted ≈320 px ≈ 68 cm padded, ≈295 px ≈ 62.5 cm bare.**
17. **Possible sling at (850–880, 395–430) (pose, low confidence).** Weapon analyst's zoom identifies glove cuff + vest side; **no sling**.
18. **Gear §2.1 "right ear at (720–735, 70–100)".** Coordinate error; the right ear is at x 753–770, y 84–112 (face note).
19. **Gaiter colour: #7c5646 (pose, (800,150)) vs median #373029 (gear).** Different sample points, not a conflict: base #373029 with lit folds #74675e–#7e5849.
20. **Hair sweep direction.** Face analyst's "up and toward his RIGHT (viewer's left)" confirmed on the x5 head crop.
