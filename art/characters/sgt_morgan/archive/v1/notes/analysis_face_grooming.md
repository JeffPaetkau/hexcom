# Sgt. Alex Morgan - Head, Face, Skin and Grooming Analysis

**CONVENTION: "left" and "right" always mean the SOLDIER'S OWN left and right** (his left hand, his right shoulder). When the picture side is meant, it is written explicitly as "viewer's left" / "viewer's right". In the reference the soldier's RIGHT side of the face is on the VIEWER'S LEFT, and it is the lit, near, more visible side.

Source: `/home/user/sgt_morgan/ref/reference_full.png` (1672x941). `crop_head_face.png` (850x850, x5) was located by template match at full-image origin **(715, 30)**, so crop pixel (cx, cy) = full pixel (715 + cx/5, 30 + cy/5). All coordinates below are **full-image pixels** unless stated. Colours are 3x3 means at the stated pixel (sRGB hex). Extra zooms I made are in `/home/user/sgt_morgan/ref/face_zooms/` (listed at the end).

Pixel scale: the head is only ~103 px tall (hair top y=29 to menton y=131.5) in the full frame, so one pixel is roughly **2.1 mm** (scale ~0.47 px/mm, anchored on interpupillary 31 px = ~66 mm and ear height 28.5 px = ~61 mm). Positional precision is about +/-1 px (+/-2 mm); ratios carry ~8-10% uncertainty. mm values are projected (foreshortened) unless marked "corrected".

---

## 1. Head pose, camera and lighting (must be reproduced before any likeness comparison)

| Item | Value | Evidence |
|---|---|---|
| Yaw | **~17 deg (range 12-22) toward the soldier's LEFT** (nose points to viewer's right) | Face midline (nasion x=815, subnasale 816, menton 816) sits right of the silhouette centre; half-width from midline to near cheek edge 44 px vs far cheek edge 29 px (ratio 1.5 => sin(yaw) ~0.2); soldier's right ear fully visible, left ear hidden; far outer canthus only 5 px from the far face silhouette. |
| Pitch | **~12 deg chin-up relative to camera ray** (range 8-15). Roughly 10 deg of that is the low camera (camera at about chest height for the full-body shot), so head-vs-torso pitch is only ~3-6 deg chin-up. | Both nostrils fully visible (dark holes at (813,94) and (822,95)); submental underside visible as a shadow band y=128-135; ear top (y=83.5) sits 7 px BELOW the eye line (y=77) and 11.5 px below the brow line (y=72), whereas on a level head the ear top aligns with the brow. Forehead appears short (24 px) vs lower third (34.5 px). |
| Roll | **0 to +2 deg** (viewer's right side very slightly higher) - treat as 0 | Iris centres (800,77) and (831,77) level; mouth corners (804,109) and (830,111) - the 2 px drop on the far corner is perspective from the yaw, not roll. |
| Gaze | Along the head axis, maybe 3-5 deg further to his left, slightly upward, focused at distance | Irises roughly centred in the fissures (near iris 1 px nasal); upper lid covers top ~20% of iris, lower lid touches iris bottom; no sclera visible under the iris. |
| Key light | Warm white, from upper viewer's-left (soldier's right-front), ~40-50 deg elevation, ~40 deg to the soldier's right of the camera | Hot spots: right temple (782,72) #dbb49d, right zygomatic (780,88) #ecc3ad, nose bridge (815,82) #d39a86, forehead (818,58) #bd8a79. Nose casts a shadow onto the philtrum and the soldier's left upper lip. |
| Fill / rim | Cool blue-grey hangar light from viewer's right and behind; soldier's left cheek/jaw in shadow with a cyan-grey rim | Shadow cheek (842,92) #ae8e8c; rim (843,96) #967472; shadow forehead (835,64) #b6a6ab. Rim runs down the full left silhouette from temple (x=844, y=44-86) to jaw (x=842, y=112). |

Consequence for the modeller: the lit-side skin tones below are **lit** values. Albedo should be set so that a render under a matching key+cool fill reproduces them, not by painting these hexes directly (see section 7 for albedo estimates).

---

## 2. Landmark table (full-image px)

| Landmark | x | y | Notes |
|---|---|---|---|
| Hair top (highest spike) | 810 | 29 | Spikes reach y=28-29 between x=790 and 830 |
| Trichion (central hairline) | 810 | 48 | Hairline is bright skin from y=47-48 at x=800-815 |
| Hairline temple corner, right | 779 | 52 | Soft corner, not a receding notch |
| Hairline temple corner, left | 838 | 50 | In shadow, read from rim |
| Glabella | 815 | 72 | Lit, lum 134-153 between the brows (x=812-818) |
| Nasion | 815 | 76 | Deepest point of bridge, at eye level |
| Right brow: inner end / peak / outer tail | 809 / 796 / 786 | 72 / 70.5 / 73.5 | Dark band y=69.5-74 |
| Left brow: inner end / peak / outer tail | 819 / 832 / 843 | 72 / 70.5 / 74 | Tail thins to a point at (843,74) |
| Right eye: outer canthus / inner canthus | 789 / 807 | 77 / 78 | Fissure 18 px wide |
| Right iris centre | 800 | 77 | Visible iris ~8-9 px wide (x=796-805), fissure height ~5 px (y=74.5-79.5) |
| Left eye: inner canthus / outer canthus | 821 / 839 | 78 / 76 | Fissure 18 px wide |
| Left iris centre | 831 | 77 | Visible iris ~8 px (x=827-835) |
| Pronasale (nose tip) | 815 | 90 | Lum peak 175 on dorsum profile |
| Nostrils (darkest pixels) | 813 / 822 | 94 / 95 | lum 8 and 10 |
| Alar outer edges, right / left | 806 / 827 | 94 / 94 | Alar base width 21 px |
| Subnasale | 816 | 97 | |
| Upper lip vermilion top (centre) | 816 | 105.5 | |
| Stomion (lip line) | 816 | 109 | Line runs (804,109) -> (830,111) |
| Mouth corners, right / left | 804 / 830 | 109 / 111 | Mouth width 26 px |
| Lower lip vermilion bottom | 816 | 113.5 | |
| Mentolabial sulcus | 816 | 117 | lum minimum 41 |
| Chin pad (soft-tissue pogonion, lit) | 816 | 123 | lum 108-138 |
| Menton (lowest chin point) | 816 | 131.5 | Lit chin pad ends y=126, shadowed underside to 133-135 |
| Zygomatic edge right (face meets ear) / left (far silhouette) | 771 / 845 | 90 / 89 | Face width excl. ear 74 px; incl. visible ear 92 px (ear back x=753) |
| Gonion right / left | 768 / 842 | 113 / 112 | Bigonial 74 px (near-side ramus visible because of yaw) |
| Chin width (lit pad) at y=124 | 805-828 | 124 | 23 px |
| Right ear: top / bottom / front / back | 760 / 764 / 770 / 753 | 83.5 / 112 / 98 / 95 | Height 28.5 px, width 17 px |
| Head silhouette width incl. hair at y=60 | 754-844 | 60 | 90 px; sides nearly vertical from y=50 to y=86 |
| Neck visible from | - | 132 | Gaiter top edge y~150 (viewer's left) rising to y~135 (viewer's right) |

Facial thirds (projected): upper (trichion->brow) **24 px (29%)**, middle (brow->subnasale) **25 px (30%)**, lower (subnasale->menton) **34.5 px (41%)**. Correcting ~12 deg pitch-up gives roughly 31/31/38: **the lower third is genuinely long** (long chin and jaw), the upper third is short-to-medium.

---

## 3. Proportion ratios (use these as the likeness checklist)

| Ratio | Reference value | Typical adult male | Reading |
|---|---|---|---|
| Bizygomatic width (excl. ear) / total face height (trichion-menton) | 74 / 83.5 = **0.89** | ~0.75 | Face reads broad/boxy in this pose; yaw adds near-side depth, so the true value is ~0.8. Still a wide-skulled head. |
| Bizygomatic / nasion-menton | 74 / 55.5 = **1.33** | ~1.15 | as above |
| Bigonial / bizygomatic (projected) | 74 / 74 = **1.0** | ~0.85 | Very square jaw; corrected estimate 0.9. |
| Chin width / bigonial | 23 / 74 = **0.31** | ~0.3 | broad, squared chin |
| Chin width / mouth width | 23 / 26 = **0.88** | ~0.75 | chin almost as wide as the mouth |
| Intercanthal / eye fissure width | 14 / 18 = **0.78** | ~1.0 | eyes are LARGE and set CLOSE (or the fissures are long) |
| Interpupillary / bizygomatic | 31 / 74 = **0.42** | ~0.46 | consistent with close-set eyes on a wide face |
| Fissure height / fissure width | 5 / 18 = **0.28** | 0.33-0.38 | narrowed, hooded eyes |
| Canthal tilt | right +3 deg, left +6 deg (perspective) -> **about +4 deg** | 0 to +5 | slight positive (outer corner higher) |
| Brow lower edge to upper lid margin | **1.5-2 px (~4 mm)** | 8-12 mm | brows sit very low; heavy, hooded orbit |
| Nose length (nasion-subnasale) / nasion-menton | 21 / 55.5 = **0.38** | ~0.43 | reads medium-short because the tip rises in the chin-up pose; corrected ~0.41 |
| Alar width / intercanthal | 21 / 14 = **1.5** | ~1.0-1.1 | broad nose base relative to the eye spacing |
| Alar width / mouth width | 21 / 26 = **0.81** | 0.65-0.7 | nose base wide relative to mouth |
| Nose bridge width at nasion | **7 px (~15 mm)** | 15-18 mm | narrow, high bridge |
| Mouth width / intercanthal | 26 / 14 = **1.86** | ~1.5-1.6 | |
| Mouth width / interpupillary | 26 / 31 = **0.84** | ~0.8-0.85 | normal; mouth is foreshortened by yaw so true width ~27-28 px (~58 mm) |
| Mouth width / bizygomatic | 26 / 74 = **0.35** | ~0.37 | |
| Upper vermilion : lower vermilion height | 3 : 4.5 px = **1 : 1.5** | 1 : 1.3-1.6 | thin upper lip, moderately full lower lip |
| Total lip height / mouth width | 7.5 / 26 = **0.29** | ~0.3 | |
| Philtrum (subnasale->vermilion) | **8.5 px (~18 mm)** | 13-17 mm | slightly long philtrum (pitch-up inflates it) |
| Stomion->menton / subnasale->menton | 22.5 / 34.5 = **0.65** | ~0.67 | |
| Ear height / nasion-menton | 28.5 / 55.5 = **0.51** | ~0.5 | normal-size ear |
| Ear height / nose length | 28.5 / 21 = **1.36** | ~1.1-1.2 | ear reads long vs the foreshortened nose |
| Forehead height / nasion-menton | 24 / 55.5 = **0.43** | ~0.5 | medium-low forehead (pose-compressed) |
| Hair top above trichion | **19 px (~40 mm projected)** | - | tall textured top |

---

## 4. Face shape and bone structure

- **Overall shape:** long rectangle / soft "square-oblong". Vertical temple-to-jaw sides (silhouette x=754 and x=844 barely change between y=50 and y=86), then a straight jawline that converges to a broad chin. Not oval, not heart; closest MakeHuman presets are a blend of *head-square* and *head-rectangular* with a slightly *head-oval* top.
- **Forehead:** medium height, broad, mildly sloped back (~10-15 deg), with a visible frontal-boss highlight at (818,58). Brow ridge (supraorbital) is prominent: strong shadow pocket between brow and upper lid, lit glabella. Two vertical **glabellar frown lines ("11 lines")** at x~813 and x~817, running from y~71 up to y~58 (about 13 px / 27 mm long; the line pixel (813,64) is #a17669 vs flanking skin #a57c6f, i.e. shallow). One faint horizontal forehead crease at y~63-64 on the right half. These lines are part of the stern read and must exist in the normal/displacement map.
- **Cheekbones:** high and prominent. The right zygomatic arch catches the brightest skin highlight in the whole face (#ecc3ad at (780,88)); below it a definite **cheek hollow** (sub-zygomatic concavity) from about (778,96) to (792,108), skin there #c08c77 - a lean, athletic face, low facial fat.
- **Nasolabial folds:** moderate, visible on the right side from the ala (806,95) down to just lateral of the mouth corner (803,111); shadow pixel (803,104) #8d6454. Not deep (no older-than-45 read).
- **Jaw:** strong, angular, well-defined gonial angle (~115-120 deg visually) at (768,113) right / (842,112) left. Masseter bulge visible on the right between the ear and the gonion. Jawline from gonion to chin is straight and sharp; under-jaw plane is visible as the shadow band y=128-135.
- **Chin:** broad, square-ish with soft corners, projects forward strongly (pogonion lit, submental in deep shadow #3e2b1e at (812,133)). A very faint central vertical dimple hint at (816,120-124); treat as a *slight* cleft (chin-cleft +0.15), not a true butt chin. Mentolabial sulcus is clearly defined (lum 41 at (816,117)) and about 4 px (8 mm) below the lower lip.
- **Ears:** only the right ear is visible (left hidden by the yaw). 28.5 px tall x 17 px wide (~61 x 36 mm). Well-defined rolled helix (#b6806a at (762,92)), visible antihelix, moderately large **free (unattached) lobe** (#d48b72 at (765,108) - strong red subsurface). Ear protrudes moderately (~20-25 deg from the skull; the whole concha is visible in a 17 deg yaw). Ear sits low in projection (top at eye level minus 7 px) because of the pitch; model with standard placement (ear top = brow line) and let the pose do it.
- **Neck:** thick and muscular. Visible width at y=150 roughly 62-66 px (~130-140 mm, corrected) versus bigonial 74 px -> neck width ~0.85-0.9 of jaw width. Sternocleidomastoid ridge visible on the right (lit, (778,146) #af816c). Larynx hidden by the gaiter shadow. Deep shadow under the jaw (#100a04 at (805,138)), so the jaw plane reads as overhanging the neck - requires a real chin projection, not a weak one.

---

## 5. Eyes, brows, lashes

- **Eye shape:** almond, horizontally long (18 px / ~38 mm fissures - large for the head), vertically narrow (5 px). Upper lid: hooded, the lid fold is barely visible - the skin between brow and lash line drapes over the crease, strongest on the lateral half. Lower lid: fairly straight, with a 1 px darker band under it (tear-trough / lower-lid shadow #a77669 right, #75524e left in shadow). Deep-set orbit: strong shadow from the brow ridge.
- **Canthal tilt:** slightly positive (~+4 deg): outer canthi 1-2 px higher than inner canthi.
- **Spacing:** inner canthi 14 px apart (~30 mm), interpupillary 31 px (~66 mm). Close-set relative to the fissure length (ratio 0.78).
- **Iris colour:** rendered iris pixels are **dark, warm, desaturated brown-grey**: right iris mean #50362e (darkest #241412), left iris mean #433230 (darkest #140200). Not one iris pixel has a blue hue (checked by HSV). The "light eyes" impression at thumbnail scale is a contrast illusion against pink skin plus the sclera catchlight at (794,77) #8d726b. Recommended iris albedo: **grey-hazel #5b4a3e body, #3a2d26 limbal ring, muted olive-grey radial fibres #6e6253**. Do NOT make them bright blue; if a cooler look is wanted, A/B test a steel grey #5a6068 at reference scale.
- **Sclera:** off-white in shadow; brightest sclera pixel #bbaaa5 (right, lateral), mean #7b5d54 (right), #513f3c (left). Use sclera albedo ~#e6e0da with strong AO in the medial canthus; the medial third of each fissure is in shadow (x=803-807 and 819-824 both dark).
- **Visible iris:** ~8-9 px wide of an 18 px fissure (ratio ~0.47) - the lids hide the top 20% and bottom 5% of the iris. Iris diameter ~11.5-12 mm as normal.
- **Eyebrows:** medium-thick (3.5-4.5 px / 8-9 mm at the body), **straight with a slight lateral downward hook**, low-set, dense. Inner ends start 10 px apart (x=809 and x=819) - squared, slightly vertical inner heads, no unibrow. Peak at about 60-65% of the way out ((796,70.5) right). The tail tapers to a point beyond the orbit edge ((786,73.5) right, (843,74) left). Colour: right brow mean **#654233**, left #4a3228 (shadow) - dark brown, clearly darker and cooler than the lit hair. Hair direction: inner third brushed up/outward, body horizontal-lateral, tail downward-lateral.
- **Eyelashes:** read as a solid dark lash line (#3b2219 at (799,73)) ~1 px thick; short (3-4 mm), dark brown-black, not long or curled. Lower lashes very sparse/short - just a faint darkening.
- **Crow's feet:** 2-3 faint radial lines at the right outer canthus, (786-789, 76-81), pixel (787,79) #ae7d69 vs cheek #c5907d. Shallow.

---

## 6. Nose and mouth

- **Nose:** straight, high and narrow bony bridge (7 px / 15 mm at the nasion), **subtle dorsal hump at the bony-cartilaginous junction around y=86-88** (dorsum luminance plateau 168-175 then a dip). Length nasion->subnasale 21 px (~45 mm projected, ~50 mm corrected). Tip moderately defined, slightly rounded/bulbous (tip highlight (815,90) #c59180, tip side (812,92) #855749), tip rotation slightly upward in this pose (columella visible). Alar base width 21 px (~45 mm) - broad relative to the eye spacing; alae are rounded, nostrils oval, ~3 x 2 px (6 x 4 mm), angled ~30 deg from horizontal. Columella slightly lower than the alar rims. Nose midline is 1 px right-of-centre (toward the soldier's left), i.e. straight within tolerance.
- **Mouth:** closed, pressed lightly; **width 26 px (~55 mm projected, ~58 mm corrected)**, corners level with a 2 px perspective drop toward the far side; corners are slightly tucked (small shadow dots (807,109) and (826,111)). **Upper lip thin** (vermilion ~3 px / 6 mm) with a shallow cupid's bow and a long, slightly defined philtrum (8.5 px / 18 mm, ridges visible as a lit band x=813-819). **Lower lip fuller** (4.5 px / 9-10 mm), with a central highlight (820,112) #8f6862. Lip colour: upper mean **#7f574f** (in nose shadow, (816,109) #5e2c25 at the lip line), lower mean **#8a5c55** - desaturated dusty rose-brown, only ~15% more saturated than the surrounding skin. Vermilion border is soft, no strong lip liner edge. Teeth not visible.

---

## 7. Skin tones, complexion, age

Sampled (3x3 mean) in the full image:

| Area | Pixel | Hex | Comment |
|---|---|---|---|
| Forehead centre, lit | (795,62) | **#c59684** | region mean (795-825, 52-66) = #b98879 |
| Forehead highlight | (818,58) | #bd8a79 | frontal boss |
| Forehead, shadow side (left) | (835,64) | #b6a6ab | cool fill, desaturated mauve-grey |
| Temple right (hot spot) | (782,72) | #dbb49d | brightest flat skin |
| Zygomatic highlight right | (780,88) | #ecc3ad | specular peak |
| Cheek right, mid | (790,92) | **#ca9683** | region mean (782-800, 84-98) = #c5907d |
| Cheek hollow right | (786,102) | #c08c77 | |
| Cheek left (shadow) | (842,92) | #ae8e8c | region mean #ad9598 incl. rim |
| Under-eye right | (798,83) | **#ac7c6d** | region mean #a77669 - about 12% darker and redder than cheek |
| Under-eye left | (829,82) | #724d45 | shadow |
| Nose bridge | (815,82) | **#d39a86** | dorsum region mean #d19a88 |
| Nose tip | (815,90) | #c59180 | slightly redder than dorsum |
| Ala right | (806,93) | #c28a77 | |
| Nostril (hole) | (813,94) | ~#100806 | lum 8 |
| Philtrum (in nose shadow) | (816,105) | #885f55 | |
| Jaw edge right, lit | (772,118) | #c19078 | |
| Chin pad (stubbled) | (818,123) | #7e5d51 | region mean #815f53 |
| Submental shadow | (812,133) | #3e2b1e | |
| Neck right, lit SCM | (778,146) | **#af816c** | neck region mean (768-790,140-156) #825f4d (mostly jaw shadow) |
| Neck right side | (790,150) | #b98972 | |
| Neck under jaw, deep shadow | (805,138) | #100a04 | |
| Ear helix / lobe / concha | (762,92) / (765,108) / (766,98) | #b6806a / **#d48b72** / #e4ac94 | lobe shows strong red subsurface |

**Albedo recommendation (sRGB, before lighting):** base skin **#b98670**; cheek/nose/ear SSS redness tint **#c98272**; forehead and chin slightly more yellow/olive **#b5876e**; under-eye **#9d7266**; lips **#9a6a62**. Fitzpatrick II-III, light-medium Caucasian, slightly ruddy/wind-burnt on the lit cheek, no tan line visible.

**Complexion details:**
- Surface: smooth-matte with a moderate oily sheen on the T-zone (forehead boss, nose bridge/tip, zygomatic). Pore texture is not resolvable at this pixel scale (high-pass texture of lit cheek is only 2.3-2.4 lum units); model pores at normal realistic density (visible only in close-ups) - the reference does not demand coarse pores.
- Redness: cheeks (both), nose tip/alae, ear lobe/helix, under-eyes. No broken capillaries, no acne.
- Lines/wrinkles: two glabellar "11" lines (prominent for the read), faint horizontal forehead crease, crow's feet (shallow, 2-3 lines), moderate nasolabial folds, defined mentolabial sulcus, faint lower-lid crease. No marionette lines, no neck bands.
- **Moles, scars, freckles: none detected.** A local-contrast scan of all smooth skin (7x7 median difference > 22 lum) returned only edge pixels (hairline, ear junction, nose base, mouth corners) and the glabellar line - no isolated spot. No facial scar, no eyebrow scar, no split lip.
- **Age estimate: 38-42.** Mature bone definition, early expression lines, no sagging, hair not grey; stubble shows a grey cast on the chin (see below).
- **Expression:** stern-neutral, resolute. Lips lightly pressed and level, brows level and lowered a touch (glabellar tension), eyes narrowed to ~0.28 aspect, gaze into the middle distance to his left and slightly up. No smile, no asymmetry beyond perspective. Mirror comparison (`z_head_and_mirror.png`) shows a symmetric face; the only asymmetry is pose.

---

## 8. Hair

- **Style:** short textured crop / modern "messy quiff" with tapered sides. Top is piecey and spiky, pushed **up and toward the soldier's RIGHT (viewer's left)** with a forward-up lift at the fringe; strands at the back-left splay up and backward. The look is product-separated (matte-to-light sheen clay), slightly dishevelled, not combed flat.
- **Lengths (estimates):** top **35-45 mm** (longest at the front fringe/quiff, ~45 mm; crown ~35 mm); projected spike height above the hairline is 19 px (~40 mm). Upper sides (parietal ridge) **10-15 mm** blending into the top. Temple/side **taper 3 -> 1 mm** downward: a skin-blended fade that reaches skin level at the top of the ear (the right temple fade zone (757-775, 55-75) averages #7c6150 at lum 103, i.e. scalp showing through ~50%). Sideburns are very short (part of the fade) and end at about the tragus level (y~92). Back/nape: not visible; assume the same taper (8 mm at the occipital bulge to 1 mm at the nape).
- **Hairline:** gently arched / rounded, no widow's peak, no real temple recession: centre trichion at y=48, temple corners at y=50-52 (soft corners at x=779 and x=838). Baby hairs/edge is slightly irregular, with the fringe lifted so the forehead is fully exposed.
- **Colour:** medium-dark warm brown with strong golden-brown highlights under the key light. Percentiles over the hair region (762-845, 28-50): p5 **#1e1816**, p25 **#37261e**, p50 **#4f483a**, p75 **#907060**, p95 **#bd8871**; mean #634b40. Shadow mean **#30241c**, mid-tone mean **#614d42**, highlight mean **#aa7e6e**. Recommended hair albedo: root/base **#3a2a1e**, tip/highlight **#8a6549**, with ~10% of strands at #a07a5e to produce the piecey lit tips. Sheen is low-moderate (no wet look). No visible grey in the scalp hair.
- **Direction map:** front third sweeps up and to the right (soldier's right) at ~45-60 deg from the scalp; mid-top mostly upward with a right lean; back-left strands lean back/up; sides lie flat, combed down/back toward the ear. Several individual spikes stick out against the dark background at (765-790, 32-48) and (826-842, 30-45) - these silhouette spikes are a key likeness cue; a smooth hair cap will fail.

---

## 9. Stubble (beard) and facial hair map

- **Type:** 3-5 day stubble, length **2.5-4 mm** (chin/moustache the longest, ~4 mm; cheeks ~2 mm). Uniformly trimmed look, not a shaped beard.
- **Density map** (high-pass texture and darkening relative to bare skin):
  - **Dense:** chin pad and under-lip "soul patch" zone (806-828, 114-130), region mean #815f53 vs bare cheek #c5907d - about 35% darker; moustache / upper lip (806-826, 99-106), mean #745147 (also in nose shadow); along the jawline from gonion to chin on both sides; under the jaw onto the upper neck down to about y=140-142 (visible on the lit right neck, (780-812,128-140) mean #4e372a).
  - **Medium:** lower cheeks below a line from the tragus (770,98) to the mouth corner (804,109); right jaw region (772-790, 112-124) mean #a97d66, high-pass 5.2 vs 2.3 for bare skin.
  - **Sparse / fading out:** upper cheek between that line and the cheekbone; bare above the nose-tip level (y<~97) on the cheek. The cheek hollow (786,102) is nearly bare.
  - **Bare:** cheekbones, under-eyes, nose, forehead, the neck below ~y=142 (gaiter hides the rest).
- **Colour:** dark brown **#3b2a22** hairs; chin darkest-20% pixel mean **#614236**, jaw darkest-20% **#8c634f** (lit). The chin reads cooler/greyer (#815f53, low saturation) than the warm jaw (#a97d66): **~20-30% grey/white hairs on the chin and soul patch, ~10% on the moustache, almost none on the cheeks**. This salt-and-pepper chin is a strong age/identity cue.
- Shaved neckline: none visible (natural fade under the jaw).

---

## 10. MakeHuman / MPFB modifier directions (start from Caucasian male macros)

Macros: Gender 1.0 (male); Age ~0.55-0.60 (about 40 y); Muscle ~0.70; Weight/BodyFat ~0.45 (lean face); Proportions ~0.55; Caucasian 1.0.

Head:
- head/head-square **+0.5**, head/head-rectangular **+0.3**, head/head-oval -0.2, head/head-round -0.3; head/head-scale-horiz **+0.2** (wide skull); head/head-scale-depth +0.1; head/head-fat **decr -0.3**; head/head-age +0.2 (temple and bone definition); head/head-angle 0.
Forehead:
- forehead/forehead-scale-vert **-0.15** (medium-low); forehead/forehead-nubian (slope) **+0.15**; forehead/forehead-temple **decr -0.1** (vertical sides, keep width); forehead/forehead-bulge +0.1 (frontal boss highlight).
Eyebrows / brow ridge:
- eyebrows/eyebrows-trans **down +0.4** (very low-set brows); eyebrows/eyebrows-angle **down +0.1** (slight lateral droop); eyebrows/eyebrows-protrude (brow ridge) **+0.3**.
Eyes (apply to both r- and l-):
- eyes/eye-scale **+0.25** (large fissures); eyes/eye-trans **in +0.2** (close-set); eyes/eye-height1 (fissure openness) **-0.3** (narrowed); eyes/eye-height2 (upper lid) -0.2; eyes/eye-corner (outer) **up +0.1** (positive tilt); eyes/eye-bag **+0.2** (lower-lid shadow); eyes/eye-push1/eye-push2 (depth) **in +0.3** (deep-set); eyes/eye-epicanthus 0; eyes/eye-trans-down 0.
Cheeks:
- cheek/cheek-bones **+0.5** (prominent, high); cheek/cheek-volume **-0.35** (hollow); cheek/cheek-inner -0.2; cheek/cheek-trans **up +0.1**.
Nose:
- nose/nose-scale-vert **+0.05** (medium, slightly long after pose correction); nose/nose-trans **down 0** ; nose/nose-width1 (bridge) **-0.3** (narrow bridge); nose/nose-width2 (mid) -0.1; nose/nose-width3 (base) **+0.25** (broad alar base); nose/nose-point-width **+0.1** (rounded tip); nose/nose-hump **+0.15** (subtle); nose/nose-nostrils-width +0.2; nose/nose-nostrils-angle (flare) +0.1; nose/nose-base-up/down 0; nose/nose-septumangle +0.05; nose/nose-curve (straight) 0; nose/nose-volume +0.1.
Mouth:
- mouth/mouth-scale-horiz **+0.15** (~58 mm); mouth/mouth-scale-vert -0.1; mouth/mouth-upperlip-height **-0.3** (thin upper lip); mouth/mouth-lowerlip-height **+0.15**; mouth/mouth-upperlip-volume -0.2; mouth/mouth-lowerlip-volume +0.1; mouth/mouth-cupidsbow **-0.2** (shallow bow); mouth/mouth-cupidsbow-width +0.1; mouth/mouth-philtrum-volume **+0.2** (visible ridges) and philtrum length +0.15; mouth/mouth-angles **down +0.05** (level-to-slightly-down, stern); mouth/mouth-dimples -0.1; mouth/mouth-laugh-lines +0.15 (moderate nasolabial).
Chin / jaw:
- chin/chin-width **+0.4**; chin/chin-height **+0.25** (long lower third); chin/chin-prominent **+0.4** (strong forward projection); chin/chin-jaw-drop **+0.1**; chin/chin-cleft **+0.15** (faint); chin/chin-bones **+0.3** (squared corners); chin/chin-prognathism 0.
- MPFB jaw group (if available): jaw-angle **squarer / lower +0.4**, jaw-width **+0.35**, jaw-mass +0.2, gonion definition +0.3.
Ears:
- ears/ear-scale **0** (normal 61 mm); ears/ear-lobe **+0.2** (fuller, unattached); ears/ear-flap (protrusion) **+0.25**; ears/ear-shape-square +0.1 (rolled helix); ears/ear-rot 0; ears/ear-trans-down 0 (do NOT lower the ear to match the pose; the pitch does it); ears/ear-wing +0.1.
Neck:
- neck/neck-scale-horiz **+0.3**; neck/neck-scale-depth **+0.25**; neck/neck-scale-vert -0.05 (gaiter hides length; keep normal); neck/neck-trans 0; neck/neck-double -0.3 (sharp submental angle).
Skin / assets:
- Skin: light Caucasian base with a custom albedo (section 7), SSS radius red-biased for ears, nose and lips. Eyebrow asset: dense straight brows ("eyebrow004/007"-class), recoloured #5a3d30. Eye asset: brown/hazel iris darkened to #5b4a3e, limbal ring strong. Eyelashes short. Hair: a short textured-crop particle/curve groom (no MakeHuman proxy hair looks right); stubble as a separate particle system (section 9 map) with 2.5-4 mm length and a greyed chin.

Expression (pose/shape keys): brow-lower (corrugator) 0.25 both sides, lips-pressed 0.2, lid-tightener (squint) 0.25, jaw clenched 0.1, no smile; head-rig yaw +17 deg left, pitch +5 deg up (plus a low camera), roll 0.

---

## 11. Strategy for measuring likeness objectively

1. **Camera match first.** Render the head with the same yaw/pitch/roll (section 1) and a camera that puts the head at ~103 px tall in a 1672x941 frame (then upscale both renders and reference with the same Lanczos x5/x8). Likeness checks on an un-matched pose are meaningless at this feature scale.
2. **Landmark ratio score.** Mark the 30 landmarks in section 2 on the render (semi-automatic: darkest pixels for nostrils, iris centres and lip line; skin-mask edges for silhouette). Compute every ratio in section 3; report the delta in %; accept **|delta| <= 5%** per ratio and a mean absolute delta <= 3%. Weight the eye-spacing, fissure width, brow-to-lid distance, bigonial/bizygomatic and chin-width ratios double - those carry the identity.
3. **Silhouette IoU.** Threshold head-plus-hair against background (lum > 45 worked on the reference) in both images; target **IoU >= 0.95** for the head silhouette and >= 0.85 for the hair spikes band (y=28-48).
4. **Onion-skin and edge overlay.** 50% blend of reference over render at x8, plus Sobel edge maps in two colours; check that the eye line, nose tip, lip line, mentolabial sulcus and jawline edges coincide within 1 px (2 mm) at full-image scale.
5. **Mirror test and flip test.** Compare the mirrored render against the mirrored reference (file `z_head_and_mirror.png`) - the eye catches proportion errors faster in a mirrored pair.
6. **Native-scale squint test.** Downsample both to the native 90x105 px head and view at 1:1 and at 50% - the character must still read as the same man; then view at x5. Most previous "awful" results fail here because they only look right at 4K.
7. **Colour check.** Sample the 20 points of section 7 on the render under a matched key (warm, upper viewer's-left) and cool fill; convert both to CIE Lab; accept **deltaE <= 6** per point, <= 4 on forehead/cheek/nose means.
8. **Optional automated check.** If dlib/InsightFace can be installed, run 68-point detection on reference and render (both at x5), Procrustes-align, and require RMS <= 2 px at x5 (0.4 px native); and ArcFace cosine similarity >= 0.6 between the x5 crops. Treat as supplementary - the manual ratios are the contract.
9. **Hair and stubble checks.** Count silhouette spikes above the hairline against the background (reference: 8-10 distinct spikes between x=765 and x=842); compare high-pass texture (3x3) on chin, jaw and cheek regions - reference values 4.7, 5.2, 2.4 lum units; render should be within +/-1.5.

---

## 12. Zoom files produced (in /home/user/sgt_morgan/ref/face_zooms/)

- `z_head_x8.png` - head (745,30)-(865,150) at x8; `z_head_grid_x8.png` same with 5 px grid labelled in full-image coordinates; `overlay_landmarks.png` - landmarks of section 2 drawn on the head.
- `g_eye_right_x20.png` (784,66)-(812,88) and `g_eye_left_x20.png` (816,64)-(846,86) with 1 px grid.
- `g_nose_mouth_x14.png` (796,84)-(840,134); `g_hair_top_x10.png` (750,26)-(860,62); `g_jaw_x10.png` (755,95)-(860,140); `g_ear_x16.png` (752,80)-(782,116); `g_temple_fade_x16.png` (760,50)-(800,90).
- `z_head_and_mirror.png` - head and its mirror side by side; `z_lowerface_contrast_x10.png` - autocontrast of (760,88)-(860,145) for the stubble map; `z_hair_contrast_x10.png` - autocontrast of (755,26)-(850,62) for strand direction; `z_shadowside_x10.png` - autocontrast of the shadowed left side (815,40)-(850,135); `z_forehead_glabella_x20.png` - autocontrast of (795,50)-(835,80) showing the two glabellar lines.

---

## Errata (consolidator)

Corrections after cross-checking against the other analyst notes and re-sampling `reference_full.png`. The body of this file is unchanged; `analysis_consolidated.md` carries the agreed values.

1. **§2 "Hair top (highest spike) y=29; spikes reach y=28–29" and the pixel-scale line "head is only ~103 px tall (hair top y=29 to menton y=131.5)".** Crop-boundary artefact: `crop_head_face.png` starts at full-image y=30, so the top of the hair was clipped. A luminance scan of the full image finds hair pixels from y=12–14 (spike tips, x≈812–814) and a solid hair mass from y≈16–20. Correct values: spike tips y=14, hair mass top y=20, skull-top→chin 109 px (→menton ≈111 px). The 2.1 mm/px head scale is anchored on IPD and ear height and still holds.
2. **§3 "Hair top above trichion 19 px (~40 mm projected)".** → 28 px (≈59 mm) to the hair mass and 34 px (≈72 mm) to the spike tips; these include the skull dome above the hairline, so the §8 hair-length estimates (top 35–45 mm) are unchanged. **§11 step 3 "hair spikes band (y=28–48)"** → y=14–48; **§8 "projected spike height above the hairline is 19 px"** → 34 px.
3. **§1 Yaw ~17° (12–22).** The pose note reads ≈22° world; consolidated ≈20° ±5° to his left relative to the camera axis.
4. **§2 / §5 IPD 31 px, iris centres (800,77)/(831,77).** Pose note reads (800,79)/(833,77), IPD 33 px; consolidated IPD 32 ±1 px, eye line y≈77.
5. **Upheld against the pose note:** iris colour is dark warm brown-grey (re-sampled right #5d3e34, left #493735, zero blue-hue pixels); hair sweep toward his RIGHT (viewer's left) confirmed on the x5 crop.
