# Weapon analysis — "AR-12 Carbine" (held + icon) and "P9 Sidearm" (icon)

**CONVENTION: all left/right are the SOLDIER'S OWN left and right (his left hand, his right shoulder). Likewise for the rifle: the rifle's RIGHT side is the ejection-port side, i.e. the shooter's right when shouldered. When the viewer's side is meant it is written "viewer's left/right".**

Pixel coordinates are FULL-image coordinates in `/home/user/sgt_morgan/ref/reference_full.png` (1672 x 941) unless prefixed "icon-crop"/"crop". Hex colours are PIL 3x3 means (or "single" = one pixel) at the stated full-image (x,y). Scale at the soldier's depth: 4.72 px/cm (from the pose analysis, 185.5 cm man = 875 px). The rifle is 15-35 cm nearer the camera than the body so it is 3-7 % larger than that scale; not corrected for.

Crop-to-full mapping (recovered by template matching, mse < 2.5 in all cases):

| crop | scale | full-image origin (x,y) | covers (full px) |
|---|---|---|---|
| crop_hands_rifle.png | x3 | (630, 230) | 320 x 340 |
| crop_torso_vest.png | x3 | (630, 140) | 360 x 350 |
| crop_belt_hips.png | x3 | (630, 410) | 360 x 220 |
| crop_soldier_full.png | x2 | (580, 20) | 440 x 915 |
| crop_icon_carbine.png | x3 | (55, 215) | 350 x 120 |
| crop_icon_pistol.png | x3 | (55, 355) | 350 x 120 |
| crop_arm_right_viewerleft.png | x3 | (600, 170) | 170 x 320 |
| crop_arm_left_viewerright.png | x3 | (850, 170) | 150 x 320 |
| crop_legs_knees.png | x3 | (630, 550) | 360 x 280 |

(full = origin + crop/scale.) My own working zooms (x4-x10, gamma-lifted, 10-px grids) were made with PIL from the full image; coordinates below were read from those.

---

## 0. Executive summary

* **Real-world basis: AR-15 / M4-pattern carbine**, direct-impingement layout: flat-top upper with a continuous Picatinny top rail, separate lower with STANAG-type magazine, carbine receiver extension (buffer tube) with a **skeletonised polymer stock**, free-float **octagonal handguard with a row of large round lightening holes on the lower facets**, 30-round ribbed magazine, A2-style pistol grip (icon). The game name "AR-12" is fictional; model it as a 16 in-barrel, 13 in-handguard AR-15 carbine (OAL about 86 cm) and dress it with the accent scheme below.
* **Colour scheme (both views agree):** matte dark grey-black metal (median #413c3b class, NOT pure black) with lighter worn edges, a semi-gloss black buffer tube, **tan/FDE paint accents** (held rifle #a68869 - #d4a271; icon duller #88745b - #917652) in six fixed places (stock stripe, stock QD plate, upper-receiver rear panel, lower-receiver/magwell plates, handguard rear-top patch), glossy blued-steel barrel with blue rim light, and one **bronze/burnt-bronze muzzle device** (#5f4c3e - #6a5344).
* **Held rifle vs icon, big differences:** (1) held rifle has a 31-32 cm (13 in) handguard, icon a 22 cm (9 in) one; (2) icon has a full-size tube red-dot (CompM4 class) on the top rail, held rifle shows NO optic above the rail but a **cylindrical Scout-type weapon light on the right side at the receiver/handguard joint**; (3) icon has a long underbarrel laser/light module, held rifle has nothing under the handguard (bare C-clamp grip); (4) held rifle's muzzle is rendered as THREE parallel tubes (AI artefact), icon has a single barrel + birdcage; (5) icon has a light-blue "window" on the upper receiver where the held rifle has a tan vertical panel; (6) icon magazine is ~16 cm (40-rd look), held is ~12 cm (30-rd).
* **Recommendation in one line:** build the HELD rifle's proportions, handguard and accessories (it is the hero view the model will be judged against), take the icon's single-barrel muzzle, trigger guard, grip and (optionally, low-mounted) optic, and use real AR-15 dimensions everywhere the render is internally inconsistent (see 1.1).
* **Sidearm:** the "P9 Sidearm" icon is a SIG P226-class DA/SA 9 mm with a rail light. **No pistol and no holster are visible anywhere on the soldier** (right hip carries two polymer rifle-mag/utility carriers, left hip two soft pouches). Recommend omitting the pistol from the body or putting a holster at the small of the back (invisible from the front). Same conclusion as the gear-inventory note, sections 13 and 16.

---

## 1. Rifle pose in the reference (needed to read every measurement)

From the pose analysis (confirmed by my own zooms): butt over his RIGHT pectoral, muzzle down toward his LEFT thigh. Reference line used here: butt-plate centre **B = (695, 268)** to muzzle tip **M = (903, 570)**; length 366.7 px = 77.7 cm projected, **55.4 deg below horizontal**, muzzle about 25 deg toward the camera (foreshortening 0.914 along the bore if the true butt-to-muzzle length is 85 cm). The camera sees the rifle's **RIGHT side** (ejection port, forward assist side); the top rail is the upper-right silhouette edge in the image; the magazine hangs toward the lower-left. Roll about the bore is small (ejection port appears full height, 2.7 cm projected vs 2.3 cm real), so treat the view as a near-pure right-side elevation.

"along" below = distance along the bore from B, corrected for foreshortening (cm); "off" = perpendicular distance from the B-M line, + = toward the rifle's top. Note B sits ~4.5 cm BELOW the true bore (bore runs through the buffer tube), so the true bore is at off ≈ +4.5 cm at the butt and 0 at the muzzle.

| landmark (held rifle) | full px | along cm | off cm |
|---|---|---|---|
| butt heel (top-rear corner) | (706, 243) | -3.3 | +4.9 |
| butt toe | (683, 296) | +3.8 | -5.5 |
| buffer-tube rear cap | (705, 243) | -3.5 | +4.7 |
| stock/receiver junction (castle nut) | (748, 300) | 13.1 | +5.4 |
| charging-handle latch (est.) | (752, 312) | 15.9 | +4.7 |
| upper receiver top-rear | (757, 300) | 14.3 | +7.0 |
| tan QD-plate centre (stock) | (741, 330) | 17.9 | +0.6 |
| top-rail band at receiver | (780, 307) | 18.6 | +10.1 |
| ejection port rear edge | (778, 358) | 28.1 | +3.7 |
| ejection port front edge | (802, 392) | 37.7 | +3.8 |
| mag-release button glint | (764, 384) | 31.2 | -1.9 |
| index fingertip on receiver | (750, 398) | 32.0 | -6.0 |
| magazine top at magwell | (770, 405) | 36.0 | -3.4 |
| magazine baseplate centre | (748, 455) | 42.7 | -13.2 |
| weapon-light rear (knurled) | (813, 362) | 33.5 | +9.3 |
| weapon-light front (bezel) | (832, 394) | 42.1 | +8.8 |
| handguard rear end | (793, 402) | 38.5 | +1.0 |
| hole #1 ... #7 (lower facet) | (822,447) ... (853,510) | 50.9 ... 67.0 | ~0 to -1.5 |
| screw glints (right face, upper edge) | (851,478) (855,486) (860,497) | 60.6, 62.7, 65.4 | +1.3 to +2.0 |
| thumb across top rail | (850, 445) | 54.2 | +5.8 |
| top-rail band at handguard | (872, 438) | 55.7 | +10.5 |
| handguard front cap | (873, 512) | 70.0 | +1.7 |
| bronze tube start | (868, 512) | 69.3 | +0.9 |
| lower thin rod end | (878, 565) | 80.8 | -3.8 |
| bronze tube end | (896, 571) | 84.3 | -1.3 |
| top rod end (muzzle tip) | (903, 570) | 85.0 | 0.0 |

Projected widths: buffer tube 12.8 px = 2.7 cm (real 29.2 mm, matches); butt plate 57.8 px = 12.2 cm; magazine across ribs 6.6 cm (real mag depth 7 cm, matches); magazine protrusion 11.6 cm (30-rd, matches); handguard height 5.9 cm (real 4.5-5.5, slightly chunky); weapon-light 2.9 cm diameter; ejection port 8.8 x 2.7 cm (real dust cover 7.9 x 2.3 cm, 11-15 % chunky); exposed muzzle assembly 13.8 cm.

### 1.1 Internal inconsistencies of the render (do NOT copy)
* The top-rail band sits +10 cm off the B-M line all along its length (parallel to it within 0.5 deg), i.e. about 6-7 cm above where the barrel exits the handguard. On a real AR the rail top is ~3 cm above the bore. The three "muzzle" tubes exit from the lower third of the handguard's front face. AI anatomy; build the real geometry (bore centred in handguard, rail 3 cm above bore).
* The weapon-light cylinder (along 33.5-42.1 cm) straddles the receiver/handguard joint (38.5 cm) by 5 cm. On the model put it fully on the handguard (rearmost M-LOK slot, offset mount) with its tail cap just forward of the receiver face.
* Three parallel muzzle tubes: use one barrel (see 3.12).

---

## 2. Identity and recommended master dimensions (real-world, cited)

| item | real-world figure | source |
|---|---|---|
| M4 carbine OAL 838 mm stock extended / 756 mm retracted; barrel 368 mm (14.5 in); 2.92 kg empty, 3.52 kg loaded | Wikipedia M4 carbine infobox | https://en.wikipedia.org/wiki/M4_carbine |
| Mil-spec receiver extension (buffer tube) OD 1.148 in = 29.2 mm, carbine tube 8-9 in long, 6 positions, hardcoat anodised matte black | UTG / Brownells product pages | https://www.tractorsupply.com/tsc/product/utg-pro-receiver-extension-tube-for-mil-spec-ar-15-6-position-black-hardcoat-anodized-aluminum-6089723 , https://brownells.co.uk/AR-15/M16-MIL-SPEC-BUFFER-TUBE-6-POSITION |
| Picatinny MIL-STD-1913: slot width 5.23 mm, pitch 10.01 mm centre-to-centre, slot depth 3.00 mm | Wikipedia Picatinny rail | https://en.wikipedia.org/wiki/Picatinny_rail |
| M-LOK slot 32 x 7 mm, 8 mm web between slots (20 mm module), corner radius 2.38 mm | Wikipedia M-LOK | https://en.wikipedia.org/wiki/M-LOK |
| PMAG 30 AR/M4 GEN M3: max length 7.5 in (190 mm), 30 rd 5.56 | Magpul retail spec | https://www.landmsupply.com/magpul-pmag-30-ar-m4-gen-m3 , https://en.wikipedia.org/wiki/STANAG_magazine (20/30 rd standard) |
| Aimpoint CompM4: 120 mm long, 53 x 60 mm sight, 72 x 72 mm with mount, 265 g / 335 g, 38 mm objective | Wikipedia CompM4 | https://en.wikipedia.org/wiki/Aimpoint_CompM4 |
| SureFire M600V Scout light 104 mm long, bezel 34.8 mm; M600U 5.5 in long, bezel 1.125 in; body 1 in | retailer specs | https://www.batteryjunction.com/products/surefire-m600v-a-bk , https://www.midwestgunworks.com/page/mgwi/prod/m600u-z68-bk |
| A2 birdcage flash hider ~2.25-2.5 in long, ~1 in diameter (compact variants 1.75 in) | Brownells / KAK listing | https://brownells.co.uk/556-NATO-A2-BIRDCAGE-FLASH-HIDER-FOR-AR-15-KAK-INDUSTRY-LLC-556-NATO-A2-BIRDCAGE-FLASH-HIDER-1-2X28-FOR-AR-15-Black-Steel-22-Caliber-223-224-1-2-28-430113026 |
| A2 pistol grip about 4 in (10.2 cm) tall | Brownells | https://www.brownells.com/gun-parts/rifle-parts/rifle-grips/ar-15-a2-pistol-grip/ |
| Ejection-port dust cover 3.10 x 0.92 in (79 x 23 mm) | Brownells / ar15.build listings | https://brownells.co.uk/AR-15-EJECTION-PORT-COVER-ASSEMBLY-2 |
| Flat-top upper receiver about 8 x 3 x 2.75 in box; carbine upper ~7.5 in, standard ~9.5 in | ar15.build listing | https://www.ar15.build/products/upper-receiver/116825/anderson-manufacturing-ar15-a3-stripped-upper-receiver-with-parts-kit |
| MFT BATTLELINK Minimalist skeletonised stock: 7.084 in L x 5.22 in H x 1.752 in W (180 x 133 x 44.5 mm), 5.8 oz, angled rubber buttpad, QD socket | Primary Arms | https://www.primaryarms.com/mission-first-tactical-battlelink-minimalist-stock-commercial-scorched-dark-earth-bmssde |
| SIG Sauer P226: OAL 196 mm, barrel 112 mm, height 140 mm, width 38.1 mm | Wikipedia P226 | https://en.wikipedia.org/wiki/SIG_Sauer_P226 |

**Recommended master dimensions for the Blender rifle** (chosen so the hero silhouette matches the held render while every part is a real part):

* Overall length muzzle to butt **860 mm** (held render: 85 cm assumed, icon: 250 px ≈ 86 cm at 0.344 cm/px).
* Barrel **16 in = 406 mm**, government/M4 profile (Ø 19 mm at the muzzle, 0.75 in), with a **64 mm bronze A2/3-prong device** → exposed barrel+device beyond a 330 mm handguard ≈ 130-140 mm (held: 138 mm measured). The icon's 190 mm exposure would need a 12 in handguard; prefer the held value.
* Handguard **330 mm (13 in)**, octagonal, 55 mm tall over the top rail, 45 mm wide.
* Upper receiver (flat-top) 205 mm long x 70 mm tall x 60 mm wide (rail 25 mm wide); lower 200 mm long including the grip boss.
* Buffer tube Ø 29.2 mm, 210 mm long; stock body 180 x 133 x 45 mm (MFT Minimalist class, fixed in position 3 of 6).
* Magazine 30-rd, 190 mm total, 120 mm protruding, 70 mm deep x 24 mm wide.
* Rail: 10.01 mm pitch, 5.23 mm slots, 3.0 mm deep, 21.2 mm across the top flat.

---

## 3. Component by component (held rifle → icon → recommendation)

### 3.1 Stock (skeletonised polymer)
**Held** (zooms `stock`, `stock_bright`): fixed-looking skeleton stock hanging under the fully exposed buffer tube. Butt plate from heel (706,243) to toe (683,296): 12.2 cm tall, raked ~15 deg (toe forward), dark #141211, no visible rubber ribbing (too small to resolve; assume a textured rubber pad). Body dark grey median **#3d3733** (lit cheek area #5e4f44 at (725,290); lower arm in deep shadow #010100 at (700,300)). A **large triangular/trapezoidal lightening cut-out** at (688-712, 265-300) through which the dark glove/vest is seen (#020301). Upper body = cheek-rest bar directly under the tube; lower arm runs from the toe forward-up to the receiver end-plate. Two tan accents: **a tan stripe along the upper body just below the tube**, warmest pixel (718,281) #a68869 (single #c1a27f), about 1 x 7 cm; and a **tan rectangular frame (QD-socket/sling-slot plate)** at (730-752, 308-350), centre (741,330), outline #bf9c70 (single #cea676), interior #86694f, about 3 x 7 cm — sits at the stock's front-bottom where it meets the receiver end plate. Scuffed: lighter grey streaks (#5e4f44-#8d8787) along the cheek rest.
**Icon** (`icon_stock`): same family — boxy skeleton stock 53 px long (18.2 cm) x 38 px tall (13 cm), straight top comb continuous with the receiver, near-vertical butt pad (#0d0f11, 13 px/4.5 cm thick dark rubber), **one large open window** in the middle, slim lower strut, a **horizontal tan stripe near the top** at (120-150, 256-262) #88745b (single #a0896d). Body #1d1d1d median, #303131 lit.
**Recommendation:** MFT BATTLELINK-Minimalist-class skeleton stock (180 x 133 x 45 mm), black polymer #3a3530 with edge wear to #5e4f44, angled rubber buttpad, one big window, tan stripe 10 x 70 mm inlaid below the tube, tan QD plate 30 x 70 mm at the lower front. Follow the HELD proportions (icon agrees within 5 %).

### 3.2 Buffer tube / receiver extension / end plate
**Held:** glossy black cylinder exposed along the whole stock top from (705,243) (rear cap, which protrudes ~1 cm past the butt heel) to the receiver at (748,300): 13 cm visible + ~3.5 cm overhang → ~16.5 cm of tube outside the receiver → a carbine tube (21 cm) with the stock at position 3-4. Projected Ø 2.7 cm (real 29.2 mm). Strong specular: highlight #807a75 mid, **#b5b0b1 → #ece7e9** peak at (741,297); shadow side warm dusty #534232 at (712,262). Castle nut / end plate not resolved (hidden by the tan QD frame).
**Icon:** tube hidden inside the stock's top rail, only the junction ring at x≈158.
**Recommendation:** mil-spec Ø 29.2 x 210 mm hardcoat tube, semi-gloss black (roughness ~0.35), 6 notches underneath, castle nut + QD end plate at the receiver; follow HELD (exposed tube is a strong silhouette cue).

### 3.3 Lower receiver
**Held** (zooms `lower_mag`, `magwell_top`, `receiver_bright`): grey-black forged lower, median **#403c39**, darkest near the hand #262321. Pistol grip and trigger are completely hidden behind the right hand (hand at 690-752 x 325-400; grip estimated centre (735,395)). **Mag-release button**: round bright glint at **(764,384)** (#676261 mean, #c0bbbb single), on the right side just above the magwell front, 31 cm from the butt — standard position. Index finger (fully extended, trigger discipline) lies along the lower's right side with the tip at (750,398). **Magwell** flared lip at (750-790, 400-410). Tan accents: a small vertical tan mark at (774,390) (#736456, single #b09f8c, about 0.7 x 3 cm) just behind the magwell on the lower's right face, and a **gold rivet-like patch at the magwell front edge (792,417)** #8d764b (single #a18958). A dark slot at (775-780, 400-415) = the mag-catch slot in the magwell.
**Icon** (`icon_receiver`): lower #4e4f4e; **A2/MOE-type pistol grip** (165-182 x 268-305, 37 px = 12.7 cm, swept back ~20 deg, black #121415, flat sides); **trigger guard** (183-200 x 270-283) rounded-rectangular, black #040404, with the curved trigger visible; **two stacked gold/brass plates on the right side above the magazine** at (203-215, 262-270) and (210-227, 265-273), #917652 (single #bd9d73), each about 1.5 x 4 cm — these are the icon's version of the held rifle's tan magwell accents.
**Recommendation:** standard AR-15 lower, matte dark grey #3d3936 with light edge wear #686463; A2-shape polymer grip 102 mm tall (icon); integral/standard trigger guard (icon); Ø 8 mm mag-release button on the right (held, (764,384)); tan plates: one 15 x 40 mm plate on the right magwell face + one small rivet patch at the magwell front (combine held + icon). Bolt catch (left side), selector (left side, add an ambi lever on the right as a 25 mm paddle if desired), takedown/pivot pins Ø 6.4 mm both sides — none visible, all standard.

### 3.4 Upper receiver, charging handle, ejection port, forward assist, deflector
**Held** (zooms `upper_recv`, `receiver_bright`, `rear_receiver_ch`): flat-top upper, median **#413c3b**, lit edges #686463 at (772,352), shadow #44413e. Rear top at (745-757, 300-312) shows a rounded bump = **charging-handle latch/rear**, est. (752,312). **Ejection port**: dark rectangular cavity from (778,358) to (802,392): 8.8 x 2.7 cm projected (9.6 cm along after foreshortening; real dust cover 79 x 23 mm — render is ~15 % chunky), interior #3e3a39 median with a glossy glint (bolt carrier) at (793,384); **no dust cover visible hanging below it → model the port OPEN with the door swung down flat against the lower, or omit the door.** **Tan vertical panel behind the port** on the upper's right rear face: from (752,305) to (768,345), 1 x 8.5 cm, **#d4a271 at (767,342)** (single #d29b65) — this occupies exactly the spot where the icon has its light-blue window. Forward assist and brass deflector are not resolved (they would sit at (795-805, 345-360)); nothing contradicts standard ones.
**Icon:** upper #4c4b4b median, lit #807d80; continuous top rail y 243-249; charging handle hump at (160-170, 243-247); **light-blue glowing "window"** at (178-197, 249-257) **#80a8c2 - #86abc6** (single #98c1de at (190,256)) — reads as a sci-fi ammo counter / display panel; **ejection port** at (200-218, 250-258) glossy black #121212 (closed dust cover look), 18 px = 6.2 cm.
**Recommendation:** M4-style flat-top upper 205 mm long, matte dark grey, standard forward assist (Ø 16 mm button) and brass deflector on the right, mil-spec charging handle with a right-side-only latch. Ejection port 79 x 23 mm, **open, door down**, bright steel bolt carrier visible inside (#8a8a8a). For the panel behind the port follow the **HELD tan panel** (10 x 85 mm FDE) for photorealism; if the orchestrator wants the sci-fi cue, make it a recessed 60 x 20 mm panel with a dim blue emissive (#80a8c2 at low strength) — do not do both.

### 3.5 Top rail
**Held:** a continuous ribbed band along the whole upper-right silhouette from the receiver rear (775,300) to the handguard front (885,520), parallel to the bore within 0.5 deg: a **monolithic-looking Picatinny rail ~60 cm long** (receiver + handguard rails aligned). Rim-lit blue-grey: #283547 at (780,307) in shadow, **#697b97 (single #6d7e9d) at (872,438)**, lit tops #78706d at (828,382). In the x3 crop it looks twisted/braided — that is Lanczos ringing on the 10 mm slot pitch, not a sling or paracord. The left thumb lies across it at (846-880, 428-447).
**Icon:** same, slotted band at y 243-249 from x 160 to 300, with a visible slot row at (240-300, 251-255).
**Recommendation:** MIL-STD-1913 rail, 10.01 mm pitch, 5.23 mm slots, 3.0 mm deep, continuous over receiver and handguard (handguard rail aligned to the receiver rail), with "T-numbers" optional. No iron sights on it (see 3.7).

### 3.6 Optic
**Held:** **no optic protrudes above the top rail** anywhere between the receiver rear and the handguard end (checked against the dark vest background (#362b1f) in gamma-lifted zooms). The only optic-like object is the side-mounted cylinder described in 3.9 (weapon light).
**Icon:** **tube red-dot sight on a high mount on the receiver top rail**, (183-220, 232-243), 37 px = 12.7 cm long, Ø ~10 px = 3.5 cm, mount 5 px = 1.7 cm, total height above rail ~17 px = 5.8 cm; body #262828 median (#363434 lit), bright eyepiece ring at the rear (left), flared objective with a dark/blue-black lens #0d1011 at the front. Dimensions match an **Aimpoint CompM4/M68 CCO (120 mm long, 72 mm tall with mount)**.
**Recommendation:** Option A (preferred, keeps the hero silhouette): a **compact micro red dot (T-2 class, 68 x 30 x 36 mm) on a low absolute-co-witness mount (total ~45 mm above the rail)** at the receiver's front, black with a faint blue lens tint — small enough to vanish against the dark vest from the hero angle, satisfies "optic exists" from the loadout icon. Option B (icon-exact): CompM4 120 mm tube on a 72 mm-tall mount; accept that it will protrude above the rail in the hero view where the render shows nothing. Do not use the side cylinder as the optic — its knurled tail cap and flat bezel read as a light.

### 3.7 Iron sights
Neither view shows a front-sight tower, gas-block sight or rear BUIS; the icon has a tiny stub at the handguard's front-top (300-308, 250-256) that could be a folded front sight. **Recommend:** low-profile gas block inside the handguard, no fixed sights; optionally a pair of folded polymer BUIS (Magpul MBUS class, 12 mm tall folded) — purely optional.

### 3.8 Handguard
**Held** (zooms `handguard`, `handguard_bright`): free-float, **octagonal/slab-sided**, from the receiver face (793,402) to the front cap (873,512): **31.5 cm along the bore (13 in)**, 5.9 cm tall projected. Right (3 o'clock) face: flat, lit warm grey **#5e5040 at (812,430)**, median **#393532**, mid #36332f, with **2-3 dark elongated slots** (M-LOK pattern) at (812-845, 425-470) and **a row of small bright socket-head screws near the upper edge toward the front**: (851,478), (855,486), (860,497) (#929194 mean, #d6d6d8 peak) ≈ 25 mm apart. Lower (4:30 o'clock) facet: **a row of 7-8 round/oval lightening holes**, centres (822,447) (827,457) (832,467) (838,478) (843,490) (848,500) (853,510): **pitch ≈ 2.6 cm, Ø ≈ 1.3-1.5 cm**, interiors #2b2927, facet between holes in deep shadow #0d0a08. Rear-top: **tan patches** at (809,426) #685840 (single #7f6c50) and a duller one at (799,408) #312e28, ~1.5 x 2 cm each. Front cap at (862-882, 500-522), bevelled, blue-lit #596672 (single #92a1b0 at (877,521)). The handguard is slightly warmer/browner than the receiver (dust).
**Icon** (`icon_front`): shorter — x 235-300 = 65 px = **22 cm (9 in)**, 21 px = 7 cm tall incl. rail; **7 big round holes** along the lower edge at y≈261, x 243-297, pitch 7.5 px = 2.6 cm (same pitch as held!), Ø ~5 px = 1.7 cm, hole rims bright #9e9897 (bare metal); a small rectangular slot row along the top at y 251-255; gold patch at (233-248, 253-262) #957d62 at the rear-top. Body #403f3e median, #585856 upper.
**Recommendation:** HELD length **330 mm**, octagonal section 45 wide x 55 tall (incl. rail), aluminium matte dark grey #393532 with warm dust tint, **M-LOK slots (32 x 7 mm, 20 mm module) at 3, 9 and 6 o'clock**, **round Ø 14 mm vent holes at 26 mm pitch on the 4:30 and 7:30 facets** (8 holes each side, starting 125 mm behind the front), 3 socket-head screws Ø 5 mm on the right face near the top edge at 190/215/240 mm from the rear (as seen), two tan paint patches 15 x 20 mm at the rear-top right, 2 clamp screws at the rear underside. Front cap chamfered 3 mm.

### 3.9 Weapon light (the side cylinder)
**Held** (zoom `optic_bright`): cylinder on the rifle's **right side, top edge level with the top rail**, from the knurled rear end (813,362) to the flat rounded front bezel (832,394): **8.6 cm long along the bore, Ø 2.9 cm**, centre (822,378), i.e. 33.5-42.1 cm from the butt, straddling the receiver/handguard joint (38.5 cm; see 1.1). Rear 1.5 cm has fine circumferential ribs (knurled tail cap, #46433a), body median **#302f30** with highlight #8f8b84 (peak #c9c6be at (827,385)), bezel face in shadow #020000. No cable/pressure switch resolved.
**Icon:** none on the side; the icon's accessory is the underbarrel unit (3.10).
**Recommendation:** SureFire **M600-Scout-class light**: body Ø 25 mm, bezel Ø 35 mm, length 105-137 mm (use 110 mm), black hardcoat #302f30, knurled tail cap 18 mm long, on an **offset M-LOK mount at the 1:30 o'clock position of the rearmost handguard slot**, tail cap 10 mm forward of the receiver face. Follow HELD (strong hero-view feature).

### 3.10 Underbarrel accessory / foregrip
**Held:** **nothing under the handguard.** The left hand wraps the handguard directly (overhand/C-clamp, thumb over the top rail, four fingertips visible under the lower facets at (806,458) (812,470) (820,483) (828,495)); no vertical grip, hand stop or laser box between the fingers.
**Icon:** a **long dark underbarrel module** at (240-300, 266-280): 60 x 14 px = **20.6 x 4.8 cm**, ribbed body #181a19 median (#363636 lit), angled rear face, lighter lens/aperture at the front end — proportions of a long PEQ/DBAL-type laser-illuminator or a light+laser bar; too thin for a grenade launcher, too long for a vertical grip.
**Recommendation:** follow HELD — **no underbarrel accessory** (adding one would collide with the modelled left hand). If the orchestrator wants the icon's module for a stowed/third-person variant, use a PEQ-15-class box 117 x 71 x 41 mm on the 6 o'clock M-LOK, front 40 mm behind the handguard end.

### 3.11 Rail covers
None visible on either view (bare slots, bare top rail). Recommend none; optionally one 3-slot polymer M-LOK panel on the left (hidden) side.

### 3.12 Barrel, gas block, muzzle device
**Held** (zooms `muzzle`, `muzzle_bright`): **three parallel tubes** leave the handguard's lower front: (a) **top rod** Ø 1.1 cm, glossy blued steel #4d5f73 → specular #d2dff1 at (897,555), from (872,508) to the furthest tip (903,570) = 85.0 cm; (b) **central bronze tube** Ø 2.1-2.3 cm with 2-3 ring grooves at (876,530) and (885,548), **#5f4c3e (single #6a5344) at (874,554)**, warm dark bronze, ends at (896,571) with a dark cupped mouth #15191d (84.3 cm); (c) **lower rod** Ø 1.0 cm, glossy, #554f4b, ends at (878,565) = 80.8 cm. Exposed assembly 13.8 cm. There is no real AR part set that looks like this; it is the image model's "barrel + gas tube + rods" confusion.
**Icon** (`icon_front`): **single barrel** Ø ~5 px = 1.7 cm, #5d5b5c, from the handguard front (300) to a **birdcage flash hider** at (335-355, 257-267): 20 px = 6.9 cm long, Ø 9 px = 3 cm, black #0f1315 with slotted sides and a slight forward flare; exposure 55 px = 19 cm (12 in handguard look). Tiny stub above the barrel root at (300-308, 250-256) = gas block / folded sight.
**Recommendation:** **single 16 in government-profile barrel** (Ø 19 mm at the muzzle, Ø 25 mm under the handguard), dark parkerised steel #2a2c30 with a glossy blued look (roughness 0.25, strong anisotropic highlight) and the reference's **blue rim-light** in look-dev; **A2-type birdcage (or 3-prong) flash hider 64 mm long, Ø 22 mm, in burnt-bronze PVD #5f4c3e - #6a5344 with 2 decorative ring grooves** — this carries the held image's distinctive warm muzzle colour onto a real part. Exposed barrel + device 130-140 mm beyond the 330 mm handguard. Low-profile gas block (Ø 19 mm bore, 30 mm long) 190 mm from the receiver face, inside the handguard; gas tube not visible. Do not model the two side rods.

### 3.13 Magazine
**Held** (zoom `lower_mag`): straight-sided box magazine hanging perpendicular to the bore (toward his right hip), from the magwell (770,405) to the baseplate (748,455): **11.6 cm protruding**, 6.6 cm deep (front-to-back), **3 longitudinal ribs/ridges** on the visible right face catching light (#625a56 at (752,431)), body **#3f3c36 lit / #464440 shadow, median #423e3a**, thick **baseplate** band 3-4 mm, #595452 at (748,453), slightly lighter than the body (worn aluminium or grey polymer). No visible witness windows, no visible curvature (straight like a USGI 20/30 upper section). Baseplate outer corner (731,445).
**Icon:** (203-228, 272-322), 47 px = **16 cm protruding (40-rd look)**, slight forward curve, **4 vertical ribs** #474647 on #312f31 (median #0e1216 in shadow), bright baseplate edge, lower front corner rounded.
**Recommendation:** **30-round STANAG-size magazine, 190 mm total, 120 mm protruding, 70 x 24 mm section** (PMAG 30 max length 7.5 in), modelled as a **straight ribbed aluminium/polymer body with 3 ribs on each face** (held rifle), light grey-black #3f3c36 with bright edge wear #625a56 on the ribs and a 4 mm steel-grey baseplate #595452; no windows. Follow HELD for length and rib count; take nothing from the icon except the rounded baseplate corner.

### 3.14 Sling and sling points
**Held:** **no sling is visible** — no webbing from the stock/receiver to the vest, nothing hanging below the rifle; the dark strap-like patch at (850-880, 395-430) flagged as "possible sling" in the pose note is the left glove's wrist cuff and the vest's dark side in my zooms. The tan rectangular frame on the stock (3.1) is a plausible **QD socket / sling slot plate**.
**Icon:** no sling.
**Recommendation:** no sling modelled (both hands are on the gun and nothing hangs in the render). Add attachment points only: QD socket Ø 9 mm in the stock's tan plate, QD socket in the receiver end plate, and one M-LOK QD socket on the handguard's left side at 250 mm from the rear.

### 3.15 Colour and finish palette (held rifle, FULL-image coordinates)

| part | colour (hex) | sampled at | finish note |
|---|---|---|---|
| upper receiver body | #413c3b (median), lit edge #686463, shadow #44413e | region (745,300)-(800,380); (772,352); (755,345) | matte anodised, edge wear 1 stop lighter |
| lower receiver | #403c39 median, #262321 darkest | region (745,375)-(790,410); (760,392) | same |
| stock body | #3d3733 median, lit #5e4f44, butt #141211 | (725,290); (690,270) | matte polymer, scuffed |
| buffer tube | #534232 shadow / #807a75 / #b5b0b1 highlight / #ece7e9 peak | (712,262) (722,268) (741,297) | semi-gloss hardcoat, dusty warm shadow |
| tan accent, stock stripe | #a68869 (single #c1a27f) | (718,281) | chipped FDE paint |
| tan accent, stock QD frame | #bf9c70 (single #cea676), interior #86694f | (738,318) (741,330) | |
| tan accent, upper rear panel | #d4a271 (single #d29b65) | (767,342) | brightest tan |
| tan accent, lower small mark | #736456 (single #b09f8c) | (774,390) | |
| tan accent, magwell front | #8d764b (single #a18958) | (792,417) | |
| tan accent, handguard rear-top | #685840 (single #7f6c50); #312e28 | (809,426); (799,408) | |
| magazine | #423e3a median, #3f3c36 lit, ribs #625a56, baseplate #595452 | (760,425) (752,431) (748,453) | worn grey |
| handguard right face | #393532 median, lit #5e5040, mid #36332f | (812,430) (835,470) | matte, warm dust |
| handguard lower facet / holes | #0d0a08 between holes; hole interior #2b2927 | (845,488) (838,478) | |
| handguard screws | #929194 (peak #d6d6d8) | (855,486) | bare steel |
| top rail band | #283547 (receiver, shadow); #697b97 / #6d7e9d (handguard, rim-lit); #78706d lit tops | (780,307) (872,438) (828,382) | blue rim light from his left |
| weapon light | #302f30 median; highlight #8f8b84 / #c9c6be; tail #46433a | (822,378) (827,385) (815,365) | hardcoat black |
| barrel (top rod) | #4d5f73 / #575f6e, specular #d2dff1 | (884,534) (880,528) (897,555) | glossy blued steel |
| bronze muzzle tube | #5f4c3e (single #6a5344); mouth #15191d | (874,554) (895,568) | burnt bronze, ring grooves |
| ejection port interior | #3e3a39 median | region (778,358)-(802,392) | glossy glint = bolt carrier |
| mag release button | #676261 (peak #c0bbbb) | (764,384) | bare steel |

Icon palette (for reference, muted by the UI's dark card #0f1317): stock #1d1d1d/#303131 with tan #88745b; upper #4c4b4b/#807d80; blue window #80a8c2-#98c1de; ejection port #121212; lower #4e4f4e; gold plates #917652/#bd9d73; grip #121415; magazine #312f31 ribs #474647; optic #262828/#363434 lens #0d1011; handguard #403f3e/#585856, hole rims #9e9897, gold patch #957d62; underbarrel unit #181a19/#363636; barrel #5d5b5c; flash hider #0f1315.

### 3.16 Wear pattern (held rifle)
* Edge wear: all receiver and handguard edges 1-1.5 stops lighter (#686463 vs #413c3b) — hardcoat worn to bare aluminium along edges, rail corners and the magwell lip.
* Tan paint: every tan accent shows chipped/scuffed edges and darker worn centres (stripe #a68869 centre vs #c1a27f peak); the icon shows them even duller (#88745b) — paint them as hand-brushed FDE with 20-30 % chipping.
* Dust: warm brown-grey veil on upward-facing and shadow surfaces (buffer tube shadow #534232, handguard right face #5e5040); grime packed into the handguard holes (#2b2927) and rail slots.
* Steel parts (barrel, screws, mag release, bolt carrier) polished bright by handling, picking up the blue rim light.
* Stock: light grey scuff streaks on the cheek rest (#5e4f44 → #8d8787), consistent with the butt resting on the plate carrier.

---

## 4. Held rifle vs icon — difference list and which to follow

| component | held rifle | icon | follow |
|---|---|---|---|
| overall identity | AR-15 carbine, ~85 cm | AR-15 carbine, ~86 cm | both agree |
| stock | skeleton, tan stripe + tan QD frame, exposed buffer tube | skeleton, tan stripe, tube hidden | HELD (add icon's rubber pad look) |
| upper receiver panel | tan 10 x 85 mm panel behind port | light-blue glowing window | HELD (tan); blue only as an optional dim emissive |
| ejection port | open, dark cavity, 8.8 cm | closed glossy, 6.2 cm | HELD (open, door down), real 79 x 23 mm |
| pistol grip, trigger guard | hidden by hand | A2/MOE grip, standard guard | ICON |
| mag release | right side at (764,384) | not resolved | HELD |
| magazine | 30-rd look, straight, 3 ribs, 11.6 cm | 40-rd look, 4 ribs, 16 cm | HELD (30-rd, 3 ribs) |
| lower tan plates | small mark + magwell rivet patch | two 15 x 40 mm gold plates | combine: one plate + rivet patch |
| top rail | continuous, no optic above it | continuous, CompM4-class optic | rail: both; optic: see 3.6 (micro RDS low, or CompM4 if icon-exact) |
| iron sights | none | none/folded stub | none (optional folded BUIS) |
| handguard length | 31.5 cm (13 in) | 22 cm (9 in) | HELD 330 mm |
| handguard holes | 7-8 round, Ø 1.4 cm, pitch 2.6 cm, lower facets | 7 round, Ø 1.7 cm, pitch 2.6 cm | both agree; Ø 14 mm, 26 mm pitch |
| side slots/screws | M-LOK slots + 3 screws right face | small slot row top | HELD |
| handguard tan patch | rear-top right, two patches | rear-top, one patch | HELD |
| weapon light | Scout-type cylinder, right side, at the joint | none | HELD |
| underbarrel module | none | 21 x 5 cm laser/light bar | HELD (none) |
| barrel / muzzle | three tubes, bronze centre, 13.8 cm exposed | single barrel + birdcage, 19 cm exposed | ICON geometry (single barrel + birdcage) with HELD exposure (13-14 cm) and HELD bronze colour on the device |
| sling | none | none | none; QD sockets only |
| finish | dark grey, edge wear, dust, tan chips | darker, cleaner | HELD |

---

## 5. "P9 Sidearm" icon and holster check

**Icon** (`crop_icon_pistol.png`, full (55,355)-(405,475); my zoom `icon_pistol_big` of (95-320, 365-455)): right-side view, muzzle to the viewer's right. **SIG Sauer P226/P229-class DA/SA hammer-fired 9 mm**: external hammer spur at (158-165, 372-378); slide with a rounded top, **5 angled REAR cocking serrations** at (160-175, 375-392), no front serrations; slide median **#4f5050**, top #868788, side #5a5a5b (bead-blasted stainless/grey Nitron look with worn bright edges), bright muzzle crown at (315-320, 378-392); frame darker **#3a3a3a**; two bright pins/levers at (175,392)/(180,392) (slide stop + decocker) and two round frame pins at (205,398) and (225,398); **trigger guard** rounded-rectangular with a slight front hook, #090d0e, (200-232, 398-418); curved DA trigger; **grip** #343434 median (#434343 lit) with **stippled textured panels** (dotted field at (150-185, 405-440)), flat front strap, slight beavertail, magazine baseplate flush with a small lip at (150-200, 445-450); **rail-mounted compact weapon light/laser** (TLR-1/X300 class) under the dust cover at (235-278, 396-416), #181818 median (#2c2a26 lit), 43 x 20 px, lens forward. Icon proportions are stretched: OAL/height = 119/67 px = 1.78 vs a real P226 196/140 mm = 1.40 — build a real P226 (196 x 140 x 38 mm, 112 mm barrel) rather than the icon's proportions. Finish: medium-grey slide, darker frame, black polymer grip, matte black light.

**On the soldier — is a pistol or holster visible? NO.**
* His RIGHT hip / upper thigh (viewer's left), (655-707, 490-600): two vertical items on a black belt/drop platform with thigh straps at y≈520 and y≈575. Item A (655-677, 500-595): narrow, tall, dark grey body #2d2a29 with a tan front panel #554a40 (666,540), tapering lower tip at (665-672, 590-600) — knife-sheath / baton / flashlight-carrier shape, or an open-top polymer mag carrier. Item B (680-707, 495-585): boxy tan pouch #69574b (693,540), dark base #070909, bright clasp — mag/utility pouch. **Neither shows a pistol grip, slide, or holster hood.** (Gear-inventory note reads these as twin open-top polymer rifle-mag carriers; consistent.)
* His LEFT hip (viewer's right), (895-940, 470-545): two soft olive-grey pouches #3f4142 / #363837 on the belt — no holster.
* Chest/vest: no chest holster; the small black clip at (800-815, 243-258) noted by the gear analyst is not a holster.
* The brass/tan cylinder behind his LEFT shoulder at (895-915, 140-180), #cac1ab at (905,160), is a back-mounted radio antenna/tube, not a weapon.

**Recommendation:** do not invent a visible holster. Either omit the P9 from the character entirely (loadout UI item only) or add a **small-of-the-back / rear belt holster at the 5-6 o'clock position on the rigger belt (y≈490-512)** so that it is invisible from the front; if a P9 prop is needed for animation, build the P226-class pistol above with its 86 mm light and keep it hidden in that holster.

---

## 6. Blender build notes (rifle)

* Pivot/origin: bolt face on the bore axis at the receiver face; +Y toward the muzzle, +Z up, +X toward the rifle's right (ejection side). Bore height above the buffer-tube centre = 0 (in-line stock); rail top at Z = +30 mm; mag baseplate at Z ≈ -190 mm (120 mm protrusion below a 70 mm-deep magwell); stock toe at Z ≈ -95 mm, heel at Z ≈ +25 mm.
* Along +Y from the receiver face: handguard 0 → 330 mm; weapon light 10 → 120 mm at (X +40, Z +15) rotated 45 deg (1:30 o'clock); vent holes from 205 → 330 mm at 26 mm pitch on the 4:30/7:30 facets; screws on the right face at 190/215/240 mm, Z +20; gas block at 190 mm; barrel muzzle at ~370 mm from the receiver face (16 in = 406 mm measured from the bolt face, ~36 mm of which is inside the receiver), muzzle device 370 → 434 mm.
* Behind the receiver face (−Y): upper receiver to −205 mm; charging handle latch at −200 mm, Z +22; ejection port from −160 to −81 mm (79 mm), Z −5 to +18; forward assist at −175 mm, X +30; mag release at −120 mm, X +28, Z −20; tan upper panel −200 to −115 mm, Z 0 to +10, X +30; buffer tube −205 → −415 mm; stock body −235 → −415 mm; butt pad at −415 mm, 12 deg rake.
* Material slots: (1) anodised dark grey metal #3d3936 base with edge-wear mask; (2) black semi-gloss hardcoat (tube, light); (3) black polymer (stock, grip, guard); (4) FDE paint #b8905f with chip mask (six accent locations); (5) burnt-bronze metal #5f4c3e (muzzle device); (6) blued steel (barrel, pins, screws, bolt carrier) with blue tinted specular; (7) optional blue emissive for the receiver panel.
* Poly budget suggestion: receiver set 25-35 k tris, handguard with real holes/slots 15-20 k, stock 6-8 k, magazine 3 k, light 3 k, optic 4 k, muzzle 2 k.

---

## 7. Confidence and open questions

* High (±3 px): rifle axis, butt plate, buffer tube, ejection port position/size, magazine size and ribs, handguard length and hole row, light cylinder position/size, tan accent positions, muzzle tube count and colours.
* Medium: handguard side slot pattern (M-LOK vs plain slots), screw count (3 seen, could be 4), charging-handle latch, tan panel exact edges, hole diameters (1.3-1.7 cm).
* Low / judgement calls flagged to the orchestrator: (1) optic — none in the held view vs CompM4 in the icon (3.6, two options); (2) blue window vs tan panel (3.4); (3) interpretation of the three muzzle tubes (3.12, recommended single barrel + bronze device); (4) whether to carry any sidearm on the body (5).
* Not visible, assumed standard: forward assist, brass deflector, bolt catch, selector, takedown pins, trigger, pistol grip (held), dust cover door, gas block, castle nut/end plate.

## 8. Sources opened
Wikipedia: M4 carbine — https://en.wikipedia.org/wiki/M4_carbine ; Picatinny rail — https://en.wikipedia.org/wiki/Picatinny_rail ; M-LOK — https://en.wikipedia.org/wiki/M-LOK ; STANAG magazine — https://en.wikipedia.org/wiki/STANAG_magazine ; Aimpoint CompM4 — https://en.wikipedia.org/wiki/Aimpoint_CompM4 ; SIG Sauer P226 — https://en.wikipedia.org/wiki/SIG_Sauer_P226 . Retail/spec pages: UTG mil-spec receiver extension (1.148 in) — https://www.tractorsupply.com/tsc/product/utg-pro-receiver-extension-tube-for-mil-spec-ar-15-6-position-black-hardcoat-anodized-aluminum-6089723 ; Brownells mil-spec buffer tube — https://brownells.co.uk/AR-15/M16-MIL-SPEC-BUFFER-TUBE-6-POSITION ; Magpul PMAG 30 GEN M3 (7.5 in) — https://www.landmsupply.com/magpul-pmag-30-ar-m4-gen-m3 ; SureFire M600V — https://www.batteryjunction.com/products/surefire-m600v-a-bk ; SureFire M600U — https://www.midwestgunworks.com/page/mgwi/prod/m600u-z68-bk ; KAK A2 birdcage — https://brownells.co.uk/556-NATO-A2-BIRDCAGE-FLASH-HIDER-FOR-AR-15-KAK-INDUSTRY-LLC-556-NATO-A2-BIRDCAGE-FLASH-HIDER-1-2X28-FOR-AR-15-Black-Steel-22-Caliber-223-224-1-2-28-430113026 ; A2 pistol grip — https://www.brownells.com/gun-parts/rifle-parts/rifle-grips/ar-15-a2-pistol-grip/ ; ejection port cover — https://brownells.co.uk/AR-15-EJECTION-PORT-COVER-ASSEMBLY-2 ; flat-top upper dimensions — https://www.ar15.build/products/upper-receiver/116825/anderson-manufacturing-ar15-a3-stripped-upper-receiver-with-parts-kit ; MFT BATTLELINK Minimalist stock — https://www.primaryarms.com/mission-first-tactical-battlelink-minimalist-stock-commercial-scorched-dark-earth-bmssde .

---

## Errata (consolidator)

Corrections after cross-checking against the other analyst notes and re-sampling `reference_full.png`. The body of this file is unchanged; `analysis_consolidated.md` carries the agreed values.

1. **§3.4 recommendation "mil-spec charging handle with a right-side-only latch".** Real-world error: the mil-spec AR-15 charging-handle latch is on the LEFT side (shooter's left). Recommend the standard left-side latch (or an ambidextrous handle). The rounded bump at (752,312) is the handle's rear, visible from the right side regardless.
2. **§5 "His LEFT hip ... two soft olive-grey pouches #3f4142 / #363837".** The gear note's closer zoom (§11) resolves the inner cell as an olive Cordura flap pouch with a square metal snap (frag-grenade pouch) and the outer cell as a grey HARD polymer box (#363a3b) with hinged lid — adopted in the consolidated note.
3. **§1 "the magazine hangs toward the lower-left".** Image-relative; the magazine hangs toward HIS RIGHT hip (as §3.13 says).
4. **Confirmed by the consolidator:** magazine extent (magwell (770,405) → baseplate (748,455), x≈725–775) over the pose note's (762–795, 365–462); no sling; camera sees the rifle's right side; weapon light on the rifle's right side.
