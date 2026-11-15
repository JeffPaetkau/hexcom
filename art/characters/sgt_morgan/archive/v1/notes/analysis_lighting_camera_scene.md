# Sgt. Alex Morgan — Camera, Lighting, Background and Grading Analysis (evaluation-scene spec)

**CONVENTION: all "left"/"right" in this file are the SOLDIER'S OWN left and right** (his left hand, his right shoulder). When the picture side is meant it is written "viewer's left" / "viewer's right". The soldier faces the camera, so his RIGHT side is on the VIEWER'S LEFT (small image x) and his LEFT side is on the VIEWER'S RIGHT (large image x).

Source: `/home/user/sgt_morgan/ref/reference_full.png` (1672 x 941 px, 16:9). All pixel coordinates below are FULL-image coordinates (x right, y down). Colours are sRGB hex sampled with PIL as a 5x5 mean around the stated pixel unless noted. Luminance "lum" = 0.2126R+0.7152G+0.0722B on 0–255. Linear values are sRGB-decoded.

Blender world frame used throughout (same as the pose/proportions note): +Z up, character origin at the floor between the feet, character faces −Y, camera on the −Y side, **+X = his LEFT = viewer's right**, −X = his RIGHT = viewer's left.

Method: ruler-gridded Lanczos zooms (x2–x7), numpy seam tracking + least-squares line fits on the floor, bright-blob segmentation (L>150) for lamps/bokeh, Laplacian-variance sharpness per region, radial profiles for bloom, histogram statistics on the scene with UI panels masked out. Figure scale from the pose note: 875 px for ~185.5 cm → **4.72 px/cm at the figure's depth; f/D = 473 px per metre**.

---

## 0. One-page summary of the numbers

| Quantity | Value (recommended) | Range / confidence |
|---|---|---|
| Image | 1672 x 941, aspect 1.777 | render 1672x941 or 1920x1080 |
| Figure height in frame | 875 px of 941 = 93 % of frame height | hard |
| Figure horizontal centre | stance midpoint x≈830, image centre x=836 → camera yaw ≈ 0° | hard |
| Horizon (eye level) | **y ≈ 615** (below image centre 470.5 → camera tilted UP) | 585–650 |
| Camera height above floor | **0.60 m** (= 0.32 H, roughly knee height; knee joint is 0.52 m) | 0.54–0.67 m |
| Camera pitch | **+3.9° (up)** | 3.1–4.8° |
| Focal length (36 mm sensor) | **46 mm** (f_px ≈ 2130; HFOV 42.8°, VFOV 24.9°) | 42–54 mm |
| Camera distance to character origin | **4.5 m** (invariant: f_px = 473 × D) | 4.3–5.3 m |
| Face seen from below by | ≈ 14° (eye line 1.73 m is 1.13 m above camera) | 12–15° |
| Focus | on the figure (face, hands, boots all sharp; floor sharp within ±0.5 m) | hard |
| Far-background circle of confusion | **≈ 15 px** (14–19 px bokeh discs on point lamps) → **f/1.5** at 46 mm | f/1.3–1.8 |
| Mid-background (≈10 m) blur | ≈ 8–10 px (left crates) | consistent with f/1.5 |
| Vignette | none measurable (< 0.2 EV) | add 0–0.15 EV at most |
| Key light | warm (≈4500 K), from his RIGHT-FRONT-ABOVE = viewer's upper-left; az ≈ 40° viewer's-left of camera axis, el ≈ 42° | az 30–50°, el 35–50° |
| Cool side light | steel-blue (linear ≈ 0.55, 0.76, 1.0), from his LEFT, slightly behind, el ≈ 35° | az 80–110° viewer's right |
| Key : cool : ambient at the figure | ≈ 1.3 : 1 : 0.05 (irradiance) | — |
| Floor | dark, slightly cool grey sealed concrete slabs, roughness ≈ 0.3, strong grazing reflections, seams 15–20 mm | — |
| Warm floor pool | ellipse ≈ 1.3 m wide centred ≈ 0.4 m in front of the feet, slightly to his right, #c9baaa peak | — |
| Black level | crushed: 0.1 % of scene pixels = 0, 1 % ≤ 2, 2.2 % ≤ 5 | hard |
| Grading | low-key, low saturation (median 0.21), teal-ish shadows, warm highlights, ACES/AgX-like highlight desaturation | — |

---

## 1. Camera

### 1.1 Framing and scale
* Top of skull y=20, his RIGHT sole (floor datum) y=895, his LEFT sole y=907 (left foot 10–20 cm nearer the camera). Standing height 875 px.
* Head height 109 px for a ~23.5 cm head → 4.64 px/cm vs 4.72 px/cm for the whole body: **no measurable head-vs-feet foreshortening** (< 2 %). At D=2.5 m a 1.85 m figure would show ≈ 7 % difference; at 4.5 m ≈ 2 %. This alone puts the camera at ≥ 4 m.
* Stance midpoint x≈830 vs image centre 836 → the optical axis passes through the figure; no horizontal lens shift, yaw ≈ 0°.

### 1.2 Horizon / camera height (evidence)
The floor seams were tracked column-by-column (dark minima) and line-fitted:

| Seam | x-range | fitted slope | angle | y at x-start → x-end |
|---|---|---|---|---|
| S1 (diagonal, viewer's left) | 400–616 | −0.137 | −7.8° | 866 → 836 |
| S1b (continuation right of his right boot) | 784–888 | −0.143 | −8.1° | 800 → 785 |
| S3 (dark grating strip, viewer's right) | 1100–1248 | −0.158 | −9.0° | 830 → 804 |
| S4 (near bottom, viewer's left) | 400–580 | −0.121 | −6.9° | 907 → 884 |
| S2 (long seam, viewer's right) | 1000–1572 | +0.012 | +0.7° | 806 → 814 |
| S5 | 1008–1632 | −0.005 | −0.3° | 748 → 745 |
| S6 | 1000–1632 | −0.008 | −0.5° | 778 → 773 |
| S7 (viewer's left) | 464–636 | +0.006 | +0.3° | 801 → 802 |
| S8 (viewer's left) | 412–632 | −0.020 | −1.2° | 774 → 770 |

* Family B (S2, S5–S8) is horizontal to within ±1°: **camera roll = 0°**, and these seams are parallel to the image plane.
* Family A (S1, S1b, S3, S4) all rise toward the viewer's right at 7–9°. They are *not* perpendicular to family B in the world (they would otherwise converge steeply to a central vanishing point). They fit lines in plan at ≈ 55° to the image plane converging to a vanishing point ≈ (2330, 615), i.e. on a horizon near **y ≈ 615**. The individual slopes are noisy (the image is generator-made; seams wobble), so this is ±30 px.
* Independent far-scale cues: (a) the four helmets on the left crate stack are ≈ 60 px wide; at 0.29 m a helmet → that stack is ≈ 10 m from the camera; its floor contact at y≈750 then gives y_h = 750 − 207·h and, combined with f/D = 473, **h ≈ 0.55–0.65 m, y_h ≈ 585–640**. (b) The far wall / far crate line at y≈690 with 1.0–1.2 m crates ≈ 90 px tall puts the far wall at 20–28 m, which needs y_h ≈ 630–650. (c) The pose analyst's independent read of the far floor band: y_h 580–610.
* Figure cues: we look slightly down on the boot tops and knee-pad chamfers (knee pads y 600–650 straddle the horizon), and clearly **up** at the undersides of the vest pouches (y≈455: their lit bottoms are visible), the chin (deep under-jaw shadow with nostrils visible). Consistent with y_h between 530 and 650.

**Adopted: horizon y_h = 615 (±30).** With the feet 280 px below the horizon: h/D = 280/2130 → **camera height 0.59–0.60 m** at D = 4.5 m (0.54 m if y_h=640, 0.64 m if y_h=590). The image centre (470.5) is 145 px above the horizon → **camera pitched UP by atan(145/2130) = 3.9°**. (A level camera with lens shift_y = −0.087 reproduces the same image and keeps verticals exactly vertical; both are acceptable — verticals in the reference show no measurable convergence, as expected for 3.9°.)

### 1.3 Focal length and distance
* Only f/D is fixed by the framing: f_px = 473·D (m). Face-from-below angle 12–15° (pose note; nostrils and under-jaw visible, head pitch ≈ −3°) with Δh = 1.13 m → D = 4.2–5.3 m → f_px 2000–2500 → **42–54 mm on a 36 mm sensor**.
* Recommended **46 mm at 4.50 m** (f_px 2137, HFOV 42.8°, VFOV 24.9°), which also matches the pose analyst's 45–50 mm / 4.3–4.7 m. Alternative with round numbers: **50 mm at 4.91 m** (identical framing; same camera height 0.59 m and same pitch; all light positions below are relative to the figure and do not change; background distances from the camera scale by 1.09).
* Floor depth map for the adopted camera (distance from camera Z = f·h/(y − y_h) = 1278/(y − 615)): y=941 (bottom of frame) → 3.9 m (0.6 m in front of the feet); y=895 (feet) → 4.5 m; y=850 → 5.4 m; y=800 → 6.9 m; y=750 → 9.5 m; y=700 → 15 m; y=690 → 17 m; y=660 → 28 m.

### 1.4 Depth of field (what is sharp)
Laplacian variance of luminance (higher = sharper), 1672-px image:

| Region | lapVar | reading |
|---|---|---|
| Face (770–860, 40–140) | 898 | sharp |
| Chest plate (760–840, 210–300) | 1439 | sharp |
| Rifle receiver (720–800, 320–400) | 2332 | sharpest (hard edges) |
| His right glove | 1846 | sharp |
| Knee pads R / L | 698 / 1474 | sharp |
| Boots R / L | 1013 / 1373 | sharp (the nearer left boot is not softer) |
| Floor at the feet (780–900, 890–930) | 577 | sharp |
| Floor bottom-left (420–600, 900–940) | 949 | sharp (seam + texture) |
| Floor mid (1000–1300, 780–840) ≈ 6–8 m | 308 | softening |
| Floor far (950–1300, 700–750) ≈ 10–15 m | 86 | blurred |
| Left crates ≈ 10 m | 42 | blurred (edge softness ≈ 8–10 px) |
| Far-centre crates ≈ 17 m | 27 | heavily blurred |
| Ceiling trusses ≥ 15 m | 18 | heavily blurred |
| Ramp/stairs ≈ 15 m | 26 | heavily blurred |

Bokeh discs on distant small lamps (bright-blob bounding boxes incl. soft edge): ceiling lamp (1114–1127, 58–74) **14 x 17 px**; far strip lamp (1227–1240, 626–644) **14 x 19 px**; lamp (1482–1493, 379–393) 12 x 15 px; dropship landing light (1099–1127, 406–420) 29 x 15 px (rectangular lamp); ramp lamps 21 x 10 and 37 x 14 px (rectangular lamps). Disc edge profile (ceiling lamp, radial mean): r=0:243, 4:222, 6:167, 8:94, 10:59, 12:36, 16:26 → soft-edged (Gaussian-like game DOF), not a hard lens disc.

→ **CoC at ≥15 m ≈ 15 px = 0.32 mm on a 36 mm sensor.** With c∞ = f²/(N·(s−f)): N = 46²/(0.323 × 4454) ≈ **f/1.5** (f/1.6 for 50 mm at 4.9 m). Check at 10 m: CoC = 8.3 px (matches the crates). DOF for a 2 px CoC at f/1.5: 3.9–5.3 m → the whole figure, the floor pool and the near floor stay sharp, as observed. If the stand-in background is built nearer than the distances in §4, open the aperture accordingly (CoC ∝ |s2−s|/s2).

### 1.5 Vignette and lens artefacts
* Floor luminance along y=930: x=400:57, 480:72, 560:96, 600:133, 640:187 (pool), 700:79 (boot reflection), 820:185, 920:88, 1000:122, 1100:90, 1200:100 (reflection streak), 1300:55, 1400:51, 1500:56, 1600:66, 1660:77. The right-hand corner gets **brighter** toward the edge; the left-hand fall-off follows the warm pool's radius. Top strip y 0–20: 16–37 mid-frame, 60 at the right edge (lit hull). → **No measurable vignette.** If any, ≤ 0.15 EV.
* No chromatic aberration visible on the high-contrast lamp edges, no film grain, no barrel distortion (family-B seams are straight). Slight global oversharpening halo typical of an upscaled render; do not emulate.

---

## 2. Lighting

### 2.1 Sampled evidence

Skin (albedo ≈ 0.45–0.5):

| Point | (x,y) | hex | lum | R/B | note |
|---|---|---|---|---|---|
| His RIGHT temple / brow (brightest skin) | (778,70) | #e6bfac | 198 | 1.34 | key highlight; max pixels #fad4bf–#ffddc7 at (776–784, 66–87) |
| His RIGHT forehead | (790,55) | #cd9882 | 162 | 1.57 | warm key |
| His RIGHT cheek | (792,100) | #d19b87 | 165 | 1.54 | warm key |
| His RIGHT ear | (768,95) | #d0a488 | 171 | 1.53 | key reaches the ear → key is frontal enough (az ≤ 50°) |
| Nose bridge | (814,78) | #ca907c | 155 | 1.63 | specular, warm |
| His LEFT forehead | (835,52) | #93878d | 138 | 1.05 | fill side: neutral-grey, slightly cool |
| His LEFT cheek | (840,100) | #b09a9d | 158 | 1.12 | cool fill, desaturated; cheek nearly as bright as the key cheek because the head is turned 22° toward his left (toward the cool source) |
| His LEFT jaw edge | (852,118) | #272a2b | 42 | 0.91 | only a faint cool rim — no strong backlight |
| Under jaw / neck | (812,140) | #110b06 | 12 | — | deep shadow: nothing lights from below the chin; ambient is very low |

Neutral / metallic surfaces (give light colour):

| Point | (x,y) | hex | lum | normalised linear colour (R=1) | reading |
|---|---|---|---|---|---|
| Rifle receiver top specular | (760,330) | #9e8976 | 140 | (1.00, 0.72, 0.52) | **key colour ≈ 4300–4600 K** |
| Chest plate top (tan) | (800,220) | #897967 | 123 | — | lit from above |
| His RIGHT pauldron spec | (690,195) | #8a7a6e | 125 | — | warm |
| His RIGHT elbow pad | (640,320) | #978578 | 136 | — | warm |
| His LEFT pauldron front (steel) | (940,240) | #768ea5 | 138 | (0.49, 0.73, 1.00) | **cool light ≈ steel blue (12 000 K look)** |
| His LEFT pauldron top | (930,205) | #596b7b | 104 | — | cool |
| His LEFT forearm pad | (900,420) | #4e545d | 83 | — | cool |
| His LEFT knee-pad outer rim | (925,630) | #333945 | 57 | — | cool edge |
| His LEFT shin (trouser) | (935,720) | #333b47 | 58 | (0.52, 0.73, 1.00) | cool light reaches the floor level of the figure → broad source, not a small rim |
| His RIGHT shin (trouser, unlit) | (760,730) | #151517 | 21 | — | ambient level on black fabric |
| His RIGHT thigh (unlit) | (760,560) | #110f0e | 15 | — | ambient level |
| Vest pouch front | (830,420) | #2e2e30 | 46 | — | shadowed by rifle/hands |
| Vest pouch underside | (835,455) | #54504d | 81 | — | **floor bounce lights undersides** (brighter than the fronts) |
| Floor pool between the feet | (830,885) | #c9baaa | 188 | (1.00, 0.84, 0.69) | warm pool |
| Floor pool, bottom centre | (830,935) | #c7b29d | 181 | — | pool extends off-frame |
| Floor cool slab (unlit) | (1300,930) | #32373e | 55 | — | ambient + cool reflections |
| Floor reflection streak | (1115,735) | #98b0c5 | 172 | (0.55, 0.77, 1.00) | reflection of cool lamps |

### 2.2 KEY light — warm, from his right-front-above (viewer's upper-left)
* **Direction:** azimuth ≈ 40° to the viewer's LEFT of the camera axis (i.e. toward −X), elevation ≈ 42°. Evidence: brightest skin on his right brow/temple; nose shadow falls down and toward his left (viewer's right) onto the upper lip; the chin casts a hard-ish shadow onto the neck (#110b06); eye sockets only moderately shaded and upper lids lit (so the key is not above 50°); his right ear fully lit (so not more than ~50° to the side); top faces of harness straps, buckles, chest plate and rifle receiver are lit.
* **Colour:** Blackbody **4500 K** (±300 K); normalised linear ≈ (1.00, 0.77, 0.56), sRGB ≈ #ffe4c4. The floor pool reads slightly less warm (≈5000 K) because the concrete is cool grey.
* **Softness:** large source. Nose-shadow and chin-shadow edges are soft over ≈ 3–5 px at the face (≈ 1 cm); use a 1.5 x 1.5 m area light at 3.5 m (or a spot with 0.5 m radius).
* **Intensity target:** his right temple ≈ #e6bfac; right cheek ≈ #d19b87; chest plate top ≈ #897967; rifle receiver top spec ≈ #9e8976.
* **Cast shadow:** no body shadow is visible on the floor (the area to the viewer's right of the legs, x 900–1100 / y 700–880, reads 100–150 lum — bright reflections). Either the key is higher than the face suggests (≥ 55°, shadow hidden behind the figure) or the game simply did not render it. Recommendation: keep el ≈ 42° for the face modelling and, in Cycles, use Light Linking → Shadow Linking so the floor does not receive the character's key shadow (or raise the key to 55° and accept slightly deeper eye sockets).

### 2.3 COOL side light — steel blue, from his left, slightly behind, broad
* **Direction:** azimuth ≈ 100° (viewer's right, 10° behind the shoulder plane), elevation ≈ 35°. Evidence: whole left side lit cool from pauldron (138 lum) to forearm pad, knee-pad rim, shin (#333b47) and the viewer's-right edge of the trousers; left pauldron FRONT face is lit (so the source wraps to the front: az < 110°); his left cheek is cool-grey; left jaw edge shows only a faint rim (so it is not a hard backlight).
* **Colour:** linear ≈ **(0.55, 0.76, 1.00)**, sRGB-normalised ≈ #c4e2ff (≈ 12 000 K look). Same family as the hangar lamps (#e4f2fa core, #bad8eb edges) and their floor reflections (#98b0c5).
* **Softness:** very soft (3 x 3 m or larger at 4 m) — no hard terminator anywhere on the left side.
* **Intensity:** on surfaces facing it, equal to or slightly below the key: left pauldron front #768ea5 (0.25 linear) vs right pauldron spec #8a7a6e (0.20); left cheek 0.34 vs right cheek 0.38 linear. Set irradiance ≈ 0.75–0.8 x key.

### 2.4 Rim / kicker
* No dedicated hot rim: hair top #35271e, hair side #45352a, left jaw edge #272a2b, top of the right pauldron no edge flare. The cool side light already supplies the blue edge on the legs and arms. Optional: a weak cool kicker (10–15 % of key) from az 150°, el 45° for silhouette separation of the dark trousers against the dark hull — keep it subtle or the reference look is lost.

### 2.5 Ambient / fill and floor bounce
* Ambient is very low and cool: unlit black fabric #151517–#110f0e (lum 15–21); deep under-jaw #110b06. Ambient irradiance ≈ 5 % of the key, colour ≈ (0.6, 0.75, 1.0).
* Floor bounce is warm and local: the pouch undersides (#54504d, lum 81) are brighter than their fronts (#2e2e30). The bounce comes from the warm pool (lum 180–190, ≈ 1.3 m wide) directly under the figure. The chin stays dark, so the bounce must not be a large uplight — a physically reflective floor plus, optionally, a small warm uplight at 5–8 % of key.

### 2.6 Contact shadows under the boots
* Profile along y=903 (just under his right sole), x=600→800: 136,156,150,160,158,168,185,144,143,137,129,126,134,143,157,145,**125,93,73,76,81,82,79,76,76,73,71,70,72,74,76,81,110,206**,222,219,215 → under the sole (x 690–755) lum ≈ 70–80, bright floor 145–220 on both sides; **penumbra ≈ 15–20 px (3–4 cm) on the viewer's-left side, ≈ 5–10 px on the right.**
* Under his left boot (y=912, x=860→1000): 161 … 164 at x=895, then 95, 69, 51, 39, 35, 30, 28 (x 905–940), 31, 35, 39, 43, 50 (x 950–975), 115, 147 → **core 28–31 lum, penumbra ≈ 30 px (6 cm) toward the viewer's left, ≈ 10 px toward the right.** Directly under the sole (x=930, y 901–910) the floor is 0–8 → true black contact core.
* Reading: a dark AO-like contact core with a soft, asymmetric penumbra — consistent with a large soft key from the viewer's upper-left plus a large cool source from the viewer's right. Nothing hard-edged.
* The dark smudges directly below each boot in the image (x 700–760 and 905–975, y 905–941, lum 50–80 inside a 160–190 pool) are the **glossy-floor reflections of the boots**, not shadows.

### 2.7 Floor pool (warm spot on the floor)
* Two bright blobs split by the right boot's reflection: (596–693, 905–940) mean #d1bca3, peak 231 at (666,907); (763–906, 905–940) mean #c9b6a0, peak 237 at (788,922). Pool centre ≈ image (750, 925+) → world ≈ (−0.17, −0.4, 0) i.e. **0.4 m in front of the feet and 0.17 m toward his right**, extending off the bottom of the frame; radius to half brightness ≈ 0.6–0.7 m (lum 133 at x=600, 96 at 560, 72 at 480, 57 at 400 along y=930).
* Geometrically this is NOT the mirror reflection of the key (that would land 0.4 m in front of the camera) and not the key's diffuse hot-spot (the key is aimed at the chest). Treat it as the game's separate **floor-pool spot**: same warm colour, narrow cone, aimed at the floor just in front of the feet. In Blender: a spot that lights only the floor via Light Linking (or accept ~15 % extra on the boots).

### 2.8 Background emitters that matter for reflections and bokeh (all sampled at the blob peak)

| Lamp | bbox (x,y) | hex at peak / mean | colour family |
|---|---|---|---|
| Ceiling lamp (top centre) | (1114–1127, 58–74) | #e4f2fa / #bad8eb | cool white |
| Lamp on hull/wall | (1482–1493, 379–393) | #edf6fb / #c0dced | cool white |
| Lamp at right frame edge | (1653–1671, 164–185) | #e2edf2 / #c8d9e7 | cool white |
| Dropship landing light (rectangular) | (1099–1127, 406–420) | #f2f2f2 / #dfe2e5 | neutral white, brightest |
| Dropship small warm lamp | (1064–1087, 360–371) | #faecc8 / #eed1a3 | warm (≈3500 K) |
| Dropship upper window/panel | (1144–1207, 202–229) | #e4d4c2 / #d0c0af | warm-white, 64x28 px |
| Far frosted panel light | (1105–1131, 533–573) | #aec7d7 / #9fb6c8 | cool, 27x41 px |
| Far vertical strip lights (x3 stacked) | (1227–1240, 606–644), (1230–1239, 606–621) | #c5dbea / #c4dae7 | cool |
| Stair stringer strip lights | (1477–1518, 612–634), (1532–1557, 626–633), (1545–1555, 653–671), (1554–1563, 633–651) | #9caec2…#9bacc0 | cool |
| Stair base lamps | (1509–1545, 670–683), (1448–1468, 673–682) | #eff4fb, #c1dfef | cool white |
| Orange tube lamp near stairs | (1336–1393, 549–562) | core #f9f6f3, halo #f1e6d7, floor reflection (1333–1362, 653–664) #ead3b8 | warm (≈3000 K), 58x14 px |
| Warm pillar lamp, viewer's left | (547–574, 99–120) | #f4f3ee / #eae1d3 | warm-white |
| Helmet visor glow (2nd helmet) | (492,450) | #b4b8bc, 6x6 px | neutral blue-white point |

Bloom: ceiling lamp halo decays to background within 8 px beyond the disc (mild); orange lamp (1370,559) radial: 248, 200 (r=4), 174 (8), 125 (12), 100 (16), 84 (20), 67 (24), 51 (30), 34 (38) → broad soft glow ≈ 30 px; far panel (1119,538): 250, 191 (6), 141 (8), 102 (12), 90 (16), 77 (24), 65 (36) → broad glow plus haze. → **mild bloom plus atmospheric haze in the far hangar** (far wall lifted to #4f5455 while near blacks are 0).

---

## 3. Floor

* **Material:** dark, slightly cool grey sealed/polished concrete in large slabs with recessed dark seams and a few flush steel grating strips. Reads as semi-gloss: reflections of lamps stretch into vertical streaks (source panel ≈ 85 px tall at (1105–1131, 533–616) → its streak runs y 688→900, ≈ 2.5x stretched, fading 240 → 100 lum), reflections of the dark boots are visible as blurred smudges ≈ 40 px tall directly below them, and at grazing angle the lamp reflections reach the lamp's own brightness (peak 244 at (1120,754) vs 243 at the lamp).
* **Colours:** unlit slab under cool ambient #32373e (1300,930), #393c3c (1000,730), #3f4349 (1250,760); lit by warm pool #c9baaa; cool reflection streaks #98b0c5–#bccfde; seam #464548 (1180,806) ≈ 25 % darker than the slab beside it; grating strip #646870 (1180,825); mottled lighter patches #817976 (1050,870), #625e5b (1050,800). Near-floor slab beside the pool #87786a (600,890), #6a5f53 (560,930), #4b453f (480,930).
* **Pattern / scale** (depths from §1.3): family-B seams (parallel to the image plane) at y≈746, 776, 808 on the viewer's right → 9.8, 7.9, 6.6 m from camera (spacing 1.3–1.9 m); on the viewer's left at y≈772, 801, ~852, ~895 → 8.1, 6.9, 5.4, 4.6 m (spacing 0.8–1.5 m). Family-A seams run at ≈ 55° to the image plane in plan (converging to ≈ (2330, 615)). Treat the floor as **1.5 x 1.5 m slabs (±0.3 m irregularity) whose grid is sheared: one seam set parallel to X, the other at ≈ 55° to X**; seams 15–20 mm wide, 5–10 mm deep. A recessed grating strip ≈ 0.3 x 1.6 m lies at image (1100–1262, 805–837) → camera-relative Z ≈ 6.2 m, X ≈ +1.0 m (its long axis along family A).
* **Suggested Principled BSDF:** Base Color sRGB #4a4b4e (linear ≈ 0.07) modulated ±20 % by a large soft noise (patches 0.5–1.5 m) and a fine grain; Roughness 0.30 base, map 0.22–0.45 (lower in smooth/mopped patches, higher in dusty ones); Specular IOR 1.50 (level 0.5); Metallic 0; optional Coat 0.1 roughness 0.2 for the "sealed" sheen; Bump strength 0.05–0.1 from the fine grain; seams as darker (#222326) grooves in the base colour + bump. Anisotropy 0 — the vertical streaking arises naturally from roughness at grazing angles.

---

## 4. Background inventory (for a stand-in set)

Positions are given relative to the CAMERA for the adopted camera (46 mm, camera at world (0, −4.5, 0.60)); Z = distance from camera along +Y, X = lateral (+ = his left = viewer's right), H = height above floor. World Y = Z − 4.5. Derived from Z = 1278/(y_floor − 615), X = (x − 836)/2130·Z, H = 0.6 + (615 − y)/2130·Z. All ±20 %.

| # | Element | Image bbox (x,y) | Camera-relative placement | Size | Colours (sRGB) |
|---|---|---|---|---|---|
| 1 | Hangar shell | whole frame | far wall at Z ≈ 17–20 m; ceiling trusses visible at top from Z 12–25 m at H 5–8 m; suggest hangar 40 m wide, 40 m deep, 10 m high | — | trusses #161918, #0c1014; far wall (hazy) #4f5455; walls near-left #141b1d, #212932 |
| 2 | Crate stack with 4 helmets (viewer's left, behind his right arm) | x 410–600 (continues behind UI), y 445–750 | Z ≈ 9.5 m, X ≈ −3.5 … −1.05 m (floor contact y≈750) | lower tier crates 0.7 m tall (hard cases, dark blue-grey with white labels), upper tier to 1.15 m, helmets 0.28 m on top (tops at 1.36 m) | crates #45413d, #404a53, #151b20, black #040404; labels #3d474e (blurred); helmets: black #22211f, dark grey w/ blue-white visor light #b4b8bc, olive-gold #68543a, tan #483e2f |
| 3 | Racks / hanging gear behind the stack | x 430–640, y 100–450 | Z ≈ 11–12 m, X −2.2 … −1.0 m, H 1.5–3.5 m | steel shelving 3.5 m tall with vests/uniforms hanging | steel #1a1a1a, gear #262219, #5a5144 (lit) |
| 4 | Lit pillar + warm lamp (viewer's left of head) | x 540–580, y 0–400; lamp (547–574, 99–120) | Z ≈ 12 m, X ≈ −1.55 m, lamp at H ≈ 3.45 m | pillar 0.4 m wide | pillar lit #5a5144, dark #161614; lamp #f4f3ee |
| 5 | Dark columns / wall left of the figure | x 600–700, y 0–450 | Z ≈ 10–14 m, X −1.2 … −0.6 m | steel columns 0.3–0.5 m | #141b1d, #161614, #212932 |
| 6 | Dropship / shuttle hull (viewer's right) | x 960–1672+, y 0–580; nose at x≈1000 | nose at Z ≈ 11 m, X ≈ +0.85 m; hull runs back to Z ≈ 18 m, X ≈ +7 m (axis ≈ 48° to X, nose toward the character); belly H ≈ 0.8 m (y≈580), top ≥ 4 m (exits frame at x>1400) | ≥ 9 m long, ≈ 4 m tall, 3–4 m wide; angular panelled grey hull, landing-gear bay underneath | hull #1b1f28, #242627, #363737 (upper lit), nose shadow #121619, belly #13171a |
| 6a | Dropship lamps | see §2.8 | landing light at (X +1.5, Z 11.5, H 1.7) 0.22x0.1 m white; warm lamp (X +1.3, Z 11.5, H 1.95) 0.2x0.1 m; upper window (X +2.1, Z 13, H 3.0) 0.6x0.25 m warm-white; lamp (X +4.6, Z 15, H 2.2); lamp (X +7.0, Z 18, H 4.3) | — | #f2f2f2, #faecc8, #e4d4c2, #edf6fb, #e2edf2 |
| 7 | Boarding stair / ramp | x 1400–1660, y 380–720 | base Z ≈ 15 m, X +4.25 … +5.7 m; rises to H ≈ 2.3 m at x≈1650 (continues up to the hull door) | mobile stair ≈ 1.2 m wide, 3 m tall, 35–40° incline, lit strip lights along both stringers, two lamps at the base | treads #222328, rails #0b0e0f, strips #9caec2–#c4dae7, base lamps #eff4fb / #c1dfef |
| 8 | Orange tube lamp (near stair base) | (1336–1393, 549–562) | Z ≈ 15 m, X ≈ +3.7 m, H ≈ 1.0 m | 0.4 x 0.1 m horizontal tube | core #f9f6f3, glow #f1e6d7, floor reflection #ead3b8 |
| 9 | Dark red case (right frame edge) | x 1620–1672, y 620–800 | Z ≈ 6.9 m, X ≈ +2.6 … +3.0 m, H 0–0.6 m | ≈ 0.6 m tall tool/ammo case, mostly in shadow | maroon #443031 (lit edge), #4a1a1a (face, est.), shadow #0f0707 |
| 10 | Far-centre container/crate rows under the hull | x 950–1300, y 580–700 | Z ≈ 17 m, X −0.9 … +3.7 m, H 0–1.6 m | rows of 1.0–1.2 m crates, haze-lifted | #3b3f42, #1b2126; wall behind #4f5455 |
| 10a | Far lamps | (1105–1131, 533–573); (1227–1240, 606–644) | frosted panel 0.22x0.33 m at (X +2.25, Z 17, H 1.4); vertical strips 0.1x0.3 m at (X +3.2, Z 17, H 0.6–0.8) | — | #aec7d7, #c5dbea |
| 11 | Ceiling lamps | (1114–1127, 58–74) etc. | 0.4x0.4 m cool lamps at H ≈ 6 m, Z 15–25 m, spaced ≈ 4 m (only 1–2 visible between the hull and the UI) | — | #e4f2fa |
| 12 | Floor grating strip | (1100–1262, 805–837) | Z ≈ 6.2 m, X ≈ +1.0 m | 0.3 x 1.6 m, flush, darker | #646870 |

Scale check of the stand-in: a 0.29 m helmet must project to ≈ 60 px wide; the stair base lamps ≈ 35 px wide; the dropship belly edge must sit at y ≈ 560–580 across x 1000–1400; the far wall/floor line at y ≈ 690.

---

## 5. Global grading (measured on the scene with the UI panels masked)

* Luminance percentiles (0–255): 0.1 %: 0, 1 %: 2, 5 %: 9, 25 %: 23, 50 %: **42**, 75 %: 68, 95 %: 150, 99 %: 212, 99.9 %: 242. Figure box (620–1000, 150–900): 1 %: 1, 50 %: 48, 95 %: 181, 99 %: 221. → low-key image, **black point hard-crushed to 0**, 2.2 % of pixels ≤ 5; only 0.003 % of pixels ≥ 250 (lamp cores clip at 246–250).
* Channel means: whole scene (53.5, 54.2, 54.8) = neutral overall. By tone band: shadows (lum<40) mean (20.9, 23.1, 24.2) → **cool/teal shadows (+3 blue)**; low-mids (57.6, 59.3, 61.4) slightly cool; mids (121.3, 117.2, 115.0) slightly warm; highlights (lum>160) (204.3, 192.5, 179.6) → **warm highlights (+25 red over blue)**. Classic mild teal-and-orange split.
* Saturation (max−min)/max: 25 %: 0.13, median **0.21**, 75 %: 0.28, 95 %: 0.41 → desaturated military palette. The most saturated things are the warm skin (0.35–0.39) and the cool pauldron (0.29).
* Highlight handling: saturated lamp cores go to near-white (#f9f6f3 orange lamp core, #eff4fb cool lamp core) while their haloes keep the colour (#f1e6d7, #c1dfef) → ACES/AgX-style **highlight desaturation**; use AgX (or Filmic), never Standard.
* Contrast: high (crushed blacks, bright speculars, mid-grey at 42). Equivalent to AgX "Medium High Contrast" / Filmic "High Contrast".
* Haze: far wall #4f5455 (lum 83) and far crates #3b3f42 vs near unlit surfaces at 15–25 lum → aerial perspective in the hangar (depth fog ≈ 0 at 5 m rising to ≈ 35–45 % of #2c3238 at 20 m).
* Bloom: mild (see §2.8); no vignette; no grain; no CA.

---

## 6. Concrete Blender / Cycles setup

### 6.1 Scene & camera
* Units metres. Character origin (0, 0, 0) at the floor between the feet; rest/pose faces −Y.
* Render 1672 x 941 (or 1920 x 1080; identical aspect). Cycles, 512–1024 samples, denoise on; Filter width 1.5 px (the reference is soft-edged).
* **Camera:** location **(0.00, −4.50, 0.60)**; rotation_euler **(93.9°, 0°, 0°)** (90° = level, +3.9° tilts up); lens **46 mm**, sensor width 36 mm, sensor fit Horizontal; shift 0/0; clip 0.1–300 m.
  * Alternative A (level camera, shifted lens): rotation (90°, 0, 0), shift_y = −0.087.
  * Alternative B (50 mm): location (0, −4.91, 0.59), same rotation, lens 50.
* **Depth of field:** on; focus object = empty at (0, 0, 1.30) (chest/face) or focus distance 4.50 m; **f-stop 1.5** (1.6 for the 50 mm variant); blades 0; ratio 1.0. Verify: a 0.4 m lamp at 20 m should render as a ≈ 15 px soft disc at 1672 px width; the left crates (≈10 m) ≈ 8 px soft.
* Verification overlay: render, then difference-blend over the reference: skull top must land at y=20, his right sole at y=895, pupils at (800,79)/(833,77), stance centre x≈830, far floor line y≈690.

### 6.2 Lights (all aimed with a Track-To at the stated target; powers assume Cycles' Watt convention and exposure 0 — calibrate per §6.6)

| Light | Type / size | Location (world, m) | Target | Colour | Power | Purpose / notes |
|---|---|---|---|---|---|---|
| KEY | Area, square **1.5 m** | **(−1.70, −2.00, 3.60)** | (0, 0, 1.25) | Blackbody **4500 K** | **800 W** | az 40° viewer's-left, el 42°, 3.5 m from chest. Shadow-link so the floor receives no body shadow (or el 55°). |
| COOL SIDE | Area, square **3.0 m** | **(3.20, 0.60, 3.60)** | (0, 0, 1.00) | linear **(0.55, 0.76, 1.00)** | **600 W** | az 100° viewer's-right (10° behind shoulder plane), el 35°, 4 m. Broad wrap onto his left side; faint rim on jaw. |
| FLOOR POOL | Spot, radius 0.3 m, cone **24°**, blend 0.7 | (−0.90, −2.40, 4.20) | floor point (−0.20, −0.50, 0) | Blackbody 4500 K | 500 W | Light-link to the floor only. Produces the ≈1.3 m warm ellipse 0.4 m in front of the feet, peak ≈ #c9baaa. |
| UNDER FILL (optional) | Area 1.0 m, facing up (rot X 180°) | (−0.30, −1.00, 0.05) | — | Blackbody 4500 K | 40–60 W | Lifts pouch undersides to ≈ #54504d; must leave the under-jaw at ≈ #110b06. Skip if the glossy floor already does it. |
| KICKER (optional) | Area 1.0 m | (1.80, 3.00, 3.80) | (0, 0, 1.0) | (0.55, 0.76, 1.0) | 100 W | az 150°, el 45°; separation of the dark trousers from the dark hull. Keep ≤ 12 % of key. |
| WORLD | HDRI or gradient | — | — | cool | strength 0.05–0.10 | see §6.3 |
| Background emitters | emission planes | per §4 | — | per §2.8 | strength 60–300 | bokeh discs + floor reflection streaks; negligible on the figure |

Direction formula used (from the chest at (0,0,1.3)): light = chest + d·(sin φ·cos el, −cos φ·cos el, sin el) with φ measured from the camera axis, positive toward +X (viewer's right). KEY φ=−40°, el 42°, d 3.5; COOL φ=+100°, el 35°, d 4.0.

Irradiance ratio at the figure: KEY : COOL : WORLD ≈ 1.3 : 1 : 0.05. FLOOR POOL ≈ 0.6 x key on the floor.

### 6.3 World / HDRI
* Preferred: a dark industrial-interior HDRI (e.g. Poly Haven "aircraft_workshop_01" or any dim hangar/garage interior) at **strength 0.05–0.10**, rotated so its brightest windows/lamps sit behind-right of the character (toward +X, +Y), tinted cool via a Hue/Sat or Mix with (0.6, 0.75, 1.0). Target: unlit black trouser cloth renders ≈ #151517–#1a1a1c; under-jaw ≈ #110b06.
* Procedural alternative: Sky/Background gradient: zenith linear (0.010, 0.020, 0.035) (sRGB ≈ #1b2733), horizon (0.004, 0.006, 0.008), ground (0.012, 0.010, 0.008) (warm floor bounce), strength 1.0.
* Haze: Principled Volume in a 40 x 40 x 10 m box, density **0.004** (0.002–0.006), anisotropy 0.3, colour (0.7, 0.8, 1.0); or compositor depth fog to #2c3238, 0 % at 5 m → 40 % at 20 m. The far wall should render ≈ #4f5455, the far crates ≈ #3b3f42.

### 6.4 Floor
Plane 40 x 40 m at Z=0 with the material of §3: Base Color #4a4b4e (±20 % mottle), Roughness 0.30 (map 0.22–0.45), IOR 1.50, Coat 0.1 (optional), Bump 0.05–0.1, seams 15–20 mm (#222326) on a sheared 1.5 m grid (one set parallel to X, the other at 55° to X), one 0.3 x 1.6 m grating strip at world (+1.0, +1.7, 0). Floor targets after grading: cool slab #32373e, reflection streak of a cool lamp #98b0c5–#bccfde, boot reflection smudge ≈ 50–80 lum inside the pool, pool core ≈ #c9baaa.

### 6.5 Stand-in set (blocking)
Build the §4 table as boxes/cylinders with the listed colours (Principled, roughness 0.5–0.7, dark grey/blue-grey), plus emission planes for every lamp in §2.8. Minimal set that reproduces the composition: hull (box 9 x 3.5 x 4 m, rotated 48° about Z, belly at 0.8 m, at world (+4, +10, 2.8)), stair (ramp 1.2 x 4 x 3 m at (+5, +10.5, 1.5)), crate stack + 4 helmet spheres at (−2.3, +5, 0–1.36), racks (−1.6, +7, 0–3.5), pillar (−1.55, +7.5, 0–8), red case (+2.8, +2.4, 0–0.6), far crate rows (+1.4, +12.5, 0–1.6), far wall at Y=+13 to +15, ceiling trusses at H 6–8 m, 2 ceiling lamps at H 6 m.

### 6.6 Colour management and compositing
* **Blender 4.x:** View Transform **AgX**, Look **"AgX - Medium High Contrast"**, Exposure **0.0**, Gamma 1.0, Display sRGB. (Blender 3.x: Filmic + "High Contrast".) Never "Standard" — the reference has filmic highlight roll-off and desaturation.
* Compositor chain after the render layer: Color Balance (Lift/Gamma/Gain): Lift (0.985, 1.000, 1.025), Gamma (1.0, 1.0, 1.0), Gain (1.035, 1.000, 0.960) → teal shadows / warm highlights. Hue-Saturation: Saturation 0.92. RGB Curves: pull input 0.02 → 0 (crush blacks to a true 0; 2 % of pixels should hit ≤ 5). Glare: Fog Glow, threshold 2.0, size 7, mix −0.80 (only lamp cores bloom; halo ≈ 8 px on small lamps). No vignette (or ellipse mask ≤ 0.15 EV). No grain, no chromatic aberration.
* **Calibration (render the character with only the lights named, read 5x5 means, allow ±8 levels):**
  * KEY only: his right temple (778,70) ≈ #e6bfac; right cheek (792,100) ≈ #d19b87; chest plate top (800,220) ≈ #897967; rifle receiver top spec (760,330) ≈ #9e8976.
  * COOL only: left pauldron front (940,240) ≈ #768ea5; left shin (935,720) ≈ #333b47; left forehead (835,52) ≈ #93878d once the key is added.
  * WORLD only: unlit right shin (760,730) ≈ #151517.
  * FLOOR POOL: floor at (830,885) ≈ #c9baaa, at (600,890) ≈ #87786a, at (480,930) ≈ #4b453f.
  * All lights: contact core under the soles ≤ #0a0a0a; under-jaw (812,140) ≈ #110b06; scene median luminance ≈ 42/255; 99th percentile ≈ 212.

### 6.7 bpy snippet (camera, key, cool, floor-pool, DOF)
```python
import bpy, math
def track(obj, target):
    c = obj.constraints.new('TRACK_TO'); c.target = target
    c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
def empty(name, loc):
    e = bpy.data.objects.new(name, None); e.location = loc
    bpy.context.scene.collection.objects.link(e); return e
scn = bpy.context.scene
scn.render.resolution_x, scn.render.resolution_y = 1672, 941
cam_d = bpy.data.cameras.new('RefCam'); cam = bpy.data.objects.new('RefCam', cam_d)
scn.collection.objects.link(cam); scn.camera = cam
cam.location = (0.0, -4.50, 0.60); cam.rotation_euler = (math.radians(93.9), 0, 0)
cam_d.lens = 46; cam_d.sensor_width = 36; cam_d.sensor_fit = 'HORIZONTAL'
cam_d.dof.use_dof = True; cam_d.dof.focus_object = empty('Focus', (0, 0, 1.30))
cam_d.dof.aperture_fstop = 1.5; cam_d.dof.aperture_blades = 0
def blackbody(light_data, kelvin):
    light_data.use_nodes = True; nt = light_data.node_tree
    bb = nt.nodes.new('ShaderNodeBlackbody'); bb.inputs[0].default_value = kelvin
    nt.links.new(bb.outputs[0], nt.nodes['Emission'].inputs['Color'])
def area(name, loc, target, size, power, color=None, kelvin=None):
    d = bpy.data.lights.new(name, 'AREA'); d.shape = 'SQUARE'; d.size = size; d.energy = power
    if color: d.color = color
    if kelvin: blackbody(d, kelvin)
    o = bpy.data.objects.new(name, d); o.location = loc; scn.collection.objects.link(o)
    track(o, empty(name + '_tgt', target)); return o
area('KEY',  (-1.70, -2.00, 3.60), (0, 0, 1.25), 1.5, 800, kelvin=4500)
area('COOL', ( 3.20,  0.60, 3.60), (0, 0, 1.00), 3.0, 600, color=(0.55, 0.76, 1.00))
d = bpy.data.lights.new('FLOOR_POOL', 'SPOT'); d.energy = 500
d.spot_size = math.radians(24); d.spot_blend = 0.7; d.shadow_soft_size = 0.3; blackbody(d, 4500)
o = bpy.data.objects.new('FLOOR_POOL', d); o.location = (-0.90, -2.40, 4.20)
scn.collection.objects.link(o); track(o, empty('POOL_tgt', (-0.20, -0.50, 0.0)))
scn.view_settings.view_transform = 'AgX'
scn.view_settings.look = 'AgX - Medium High Contrast'; scn.view_settings.exposure = 0.0
```

---

## 7. Uncertainties and how they propagate
* Horizon ±30 px → camera height 0.54–0.67 m and pitch 3.1–4.8°. Everything about the figure's framing is unaffected; only the floor's apparent recession and the far-wall line (y≈690) move. Tune by matching the far floor line and the helmet-shelf height (y≈490).
* Focal 42–54 mm with the distance scaled to keep f/D = 473 px/m. Face-from-below angle is the discriminator: render, then compare how much nostril/under-jaw is visible against (800–840, 85–140).
* Light azimuths ±10°, elevations ±8°. The two hard constraints are the brightest skin at his right temple (776–784, 66–87) and the cool-lit left pauldron front (#768ea5); the nose shadow must fall toward his left (viewer's right).
* The reference shows no body shadow on the floor; this is a generator/game inconsistency with a 42° key — handled by shadow-linking (§6.2).
* Floor-seam geometry is approximate (seams wobble); only the near seams at y ≥ 800 are sharp enough to matter for like-for-like renders.

## 8. Machine-readable summary
```json
{
  "convention": "left/right = soldier's own; +X = his left = viewer's right; character faces -Y; camera at -Y; Z up; origin on floor between feet",
  "image": {"w": 1672, "h": 941, "px_per_cm_at_figure": 4.72, "f_over_D_px_per_m": 473},
  "camera": {"horizon_y": 615, "horizon_y_range": [585, 650], "height_m": 0.60, "height_range_m": [0.54, 0.67],
             "pitch_up_deg": 3.9, "roll_deg": 0, "yaw_deg": 0, "focal_mm_36": 46, "focal_px": 2130, "focal_range_mm": [42, 54],
             "distance_m": 4.5, "hfov_deg": 42.8, "vfov_deg": 24.9, "location": [0, -4.5, 0.60], "rotation_deg": [93.9, 0, 0],
             "alt_50mm": {"location": [0, -4.91, 0.59], "lens": 50, "fstop": 1.6},
             "dof": {"focus": [0, 0, 1.30], "fstop": 1.5, "blades": 0, "far_coc_px": 15, "coc_10m_px": 8},
             "vignette_ev": 0.0, "chromatic_aberration": false, "grain": false},
  "lights": {
    "key":   {"type": "area", "size_m": 1.5, "location": [-1.70, -2.00, 3.60], "target": [0, 0, 1.25], "azimuth_deg_from_camera_axis": -40, "elevation_deg": 42, "kelvin": 4500, "power_w": 800,
              "targets": {"R_temple_778_70": "#e6bfac", "R_cheek_792_100": "#d19b87", "chest_top_800_220": "#897967", "rifle_spec_760_330": "#9e8976"}},
    "cool":  {"type": "area", "size_m": 3.0, "location": [3.20, 0.60, 3.60], "target": [0, 0, 1.00], "azimuth_deg_from_camera_axis": 100, "elevation_deg": 35, "color_linear": [0.55, 0.76, 1.00], "power_w": 600,
              "targets": {"L_pauldron_front_940_240": "#768ea5", "L_shin_935_720": "#333b47", "L_forehead_835_52": "#93878d"}},
    "floor_pool": {"type": "spot", "cone_deg": 24, "blend": 0.7, "radius_m": 0.3, "location": [-0.90, -2.40, 4.20], "target": [-0.20, -0.50, 0.0], "kelvin": 4500, "power_w": 500, "light_link": "floor only",
              "targets": {"floor_830_885": "#c9baaa", "floor_600_890": "#87786a", "floor_480_930": "#4b453f"}},
    "under_fill_optional": {"type": "area", "size_m": 1.0, "location": [-0.30, -1.00, 0.05], "facing": "up", "kelvin": 4500, "power_w": 50, "target": {"pouch_underside_835_455": "#54504d"}},
    "kicker_optional": {"type": "area", "size_m": 1.0, "location": [1.80, 3.00, 3.80], "color_linear": [0.55, 0.76, 1.0], "power_w": 100},
    "world": {"hdri": "dark industrial interior (e.g. Poly Haven aircraft_workshop_01)", "strength": 0.08, "tint_linear": [0.6, 0.75, 1.0], "target": {"unlit_trouser_760_730": "#151517", "under_jaw_812_140": "#110b06"}},
    "ratio_key_cool_world": [1.3, 1.0, 0.05],
    "contact_shadow": {"core_lum": "0-8", "penumbra_px": "10-30", "penumbra_cm": "2-6"}
  },
  "floor": {"base_color_srgb": "#4a4b4e", "roughness": 0.30, "roughness_range": [0.22, 0.45], "ior": 1.5, "coat": 0.1, "slab_m": 1.5, "seam_mm": 18, "seam_color": "#222326",
            "grid": "one seam set parallel to X, other at 55 deg to X", "grating_strip": {"size_m": [0.3, 1.6], "world": [1.0, 1.7, 0]},
            "samples": {"cool_slab_1300_930": "#32373e", "streak_1115_735": "#98b0c5", "seam_1180_806": "#464548", "pool_830_885": "#c9baaa"}},
  "background_camera_relative": {
    "far_wall_Z_m": 18, "crate_stack": {"Z": 9.5, "X": [-3.5, -1.05], "H": 1.15, "helmets_top_H": 1.36},
    "dropship": {"nose": {"Z": 11, "X": 0.85}, "tail": {"Z": 18, "X": 7.0}, "belly_H": 0.8, "top_H": 4.2, "axis_deg_to_X": 48},
    "stairs": {"Z": 15, "X": [4.25, 5.7], "top_H": 2.3}, "orange_lamp": {"Z": 15, "X": 3.7, "H": 1.0}, "red_case": {"Z": 6.9, "X": 2.8, "H": 0.6},
    "far_crates": {"Z": 17, "X": [-0.9, 3.7], "H": 1.6}, "pillar_lamp": {"Z": 12, "X": -1.55, "H": 3.45}, "ceiling_lamp": {"Z": 20, "X": 2.7, "H": 5.8}},
  "grading": {"view_transform": "AgX", "look": "Medium High Contrast", "exposure": 0.0, "gamma": 1.0,
              "lift": [0.985, 1.0, 1.025], "gain": [1.035, 1.0, 0.96], "saturation": 0.92, "black_crush_input": 0.02,
              "bloom": {"type": "fog_glow", "threshold": 2.0, "size": 7, "mix": -0.8}, "haze_density": 0.004,
              "measured": {"lum_median": 42, "lum_p1": 2, "lum_p99": 212, "pct_le5": 2.2, "shadow_mean_rgb": [20.9, 23.1, 24.2], "highlight_mean_rgb": [204.3, 192.5, 179.6], "sat_median": 0.21}}
}
```

---

## Errata (consolidator)

Corrections after cross-checking against the other analyst notes and re-sampling `reference_full.png`. The body of this file is unchanged; `analysis_consolidated.md` carries the agreed values.

1. **§2.1 "Vest pouch underside (835,455) #54504d — floor bounce lights undersides (brighter than the fronts)" and §2.5.** Mislabelled sample: (835,455) lies inside the LEFT GLOVE (825–880 × 425–470); re-sampled #524e49 = the back of the left glove's fingers, lit by the key. "Vest pouch front (830,420) #2e2e30" is the dark vest side/cummerbund beside the handguard, not a pouch. The vest's front pouches end at y≈335 and the carrier hem is at y≈398. The floor-bounce inference is therefore unsupported by these samples; keep UNDER FILL optional/off unless the glossy floor needs help — the deep under-jaw (#110b06) still rules out a strong uplight. Likewise **§1.2 "we ... clearly up at the undersides of the vest pouches (y≈455: their lit bottoms are visible)"** — same error; the horizon argument stands on the other cues.
2. **§2.1 "His LEFT pauldron front (steel) (940,240) #768ea5"** and the derived "cool light ≈ steel blue". The sample sits at the lower edge of the EMBLEM PLATE (932–957 × 195–240), a genuinely lighter blue-grey brushed material; the pauldron itself is the same tan polymer as the right one, seen under the cool light (gear note §5). The cool-light colour (0.55, 0.76, 1.00) is still supported by the left shin (#333b47) and floor-streak (#98b0c5) samples; #768ea5 remains a valid render target for that pixel, but label it "emblem plate / pauldron".
3. **§2.1 "His RIGHT elbow pad (640,320) #978578".** That is the elbow-end band of the right forearm guard (gear note §7.2); no separate right elbow pad is visible (hidden behind the stock, if present).
4. **§1 Camera.** Adopted as the consolidated camera (46 mm, 4.5 m, 0.60 m, horizon 615, pitch +3.9°) with the pose note's ranges folded in (horizon 585–650, height 0.54–0.67 m).
