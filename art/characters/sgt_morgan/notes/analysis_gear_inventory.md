# Sgt. Alex Morgan — Complete Gear and Clothing Inventory

**CONVENTION: all "left" and "right" in this document are the SOLDIER'S OWN left and right** (his left hand, his right shoulder). The soldier faces the camera, so his RIGHT side is on the VIEWER'S LEFT (x < ~810) and his LEFT side is on the VIEWER'S RIGHT (x > ~810). When a viewer side is meant it is written explicitly as "viewer's left/right".

Source: `/home/user/sgt_morgan/ref/reference_full.png` (1672x941). All pixel coordinates below are in that FULL image. Colours are PIL samples (median of a 3x3 or 5x5 patch, or median/15th/85th-percentile of a named box). Additional zoom crops were produced at 5x–12x Lanczos and inspected.

## 0. Scale, lighting and how to read the colours

- Figure extents: top of hair y≈22, bottom of boot soles y≈905–912 at x≈648–990. Height ≈ 890 px. Assuming a stature of ~1.85 m this gives **≈2.1 mm/px (±10 %)**; shoulder width including pauldrons is 310 px (x 655→965) ≈ 65 cm, i.e. the design is heroically broad-shouldered (about 7.8 heads tall; chin y≈125, so head ≈103 px ≈ 21.5 cm). Treat mm figures below as derived from px; ratios are more trustworthy than absolutes.
- Lighting: warm key light from the viewer's upper-left (soldier's right / front), a cool blue-cyan fill/rim from the hangar lights on the viewer's right. **Everything on the soldier's LEFT reads grey-blue and everything on his RIGHT reads warm tan.** Where a material appears on both sides (forearm guards, pauldron bases, kneepads) the right-side sample is the better albedo guide; the left-side value is the same material under blue fill.
- Dust/weathering: a general pale dust accumulation on all upward-facing and knuckle-facing surfaces (sampled highlights of #9A8D85–#D2C5B5 on tan armour, #A19689 on the right boot upper). Paint chips expose a dark grey-brown substrate (#2E2B27–#453D3B).

### 0.1 Master palette (albedo guesses after discounting light)

| Material | Representative hex (sample coords) | Shadow | Highlight | Use on |
|---|---|---|---|---|
| Base-layer fabric (black-brown ripstop/knit) | #332F2D (box 885–925,300–370 median) | #040303 | #6F6760 | combat shirt, sleeves, torso under vest |
| Neck gaiter (olive-grey fleece) | #373029 (box 750–850,135–195 median); lit folds #74675E (760,170), #6C5946 (815,195) | #0A0704 | #9E8373 | gaiter |
| Vest Cordura (olive-brown) | #463E34 (box 800–850,245–262 median); #413D2E (785,255) | #0F0B09 | #776958 | plate carrier body, straps, mag pouches |
| Vest hard admin panel (khaki polymer) | #7E715F (box 745–828,198–240 median); #857660 (805,215) | #221C15 | #A09486 | chest panel |
| Tan hard armour (desert-tan painted polymer) | #837163 (box 630–700,315–355 median); lit #D1BBAA (655,328); #A3998D (690,205) | #191511 | #C6B19F | pauldrons, forearm guards, kneepad frames, pouch faceplates |
| Same tan armour on the blue-lit LEFT side | #575655 (box 882–940,370–430 median); #535354 (box 900–930,185–250) | #1A1B1C | #897D73 | left forearm guard, left pauldron base |
| Emblem plate (light blue-grey, brushed) | #B3C2D6 (942,212); box median #5A6A7A | #131719 | #BFCEDC | left pauldron badge; small box on left pauldron (#AFC2D5 at 952,268) |
| Black webbing / straps | #22211F (belt box median); #171615 (thigh strap box) | #080706 | #393632 | belt, thigh straps, kneepad straps, PALS rows |
| Black polymer (buckles, pouch bodies, toe caps) | #1C1C1E (710,525); #070604 | #000000 | #3C3D45 | hip pouch bodies, buckles |
| Gunmetal hardware (ladder locks, eyelets) | #140F06 (745,170); #322D29 (848,172); #37302C (706,816) | — | #8F8E8B (rivet 752,208) | buckles, rivets, eyelets |
| Glove leather/synthetic | #36322F (box 690–750,340–385 median) | #0B0A09 | #867B75; dusty knuckles #8F837C (708,352) | both gloves |
| Trouser camo – darkest blotch | #0A0B08 (785,560); #171513 (765,590) | — | — | camo |
| Trouser camo – mid | #262524 (box 700–790,580–615 median); #322E29 (725,560) | — | — | camo |
| Trouser camo – light/tan blotch | #615348 (880,595); #685D53 (R-thigh highlight); #534C3F (840,590) | — | — | camo |
| Boot leather (black, dusty) | #242322 (box 690–765,800–860 median); toe #40352C (925,885) | #0B0A08 | #A19689 | boot uppers |
| Boot sole rubber | #11100D (L sole box median); #26282E (720,890) | #000000 | #645C57 | outsoles |
| Cylinder cap (black rubber) | #111518 (904,140) | | | antenna cap |
| Cylinder body (brass/gold) | #705E46 (903,152) → specular #D3CAAF (905,158) | | | antenna body |
| Cylinder lower (steel) | #757D83 (908,172); #6C6B71 (909,178) | | | antenna base |
| Kneepad side tab (desaturated red/rose) | #917A7B (927,640) | | | left kneepad tab |
| Floor (contact shadows / reflections) | #E7D4BF (820,850); #D9C6B1 (800,905) | | | reference only |

## 1. Silhouette summary and attachment hierarchy (for rigging)

Head-to-toe, the figure wears: no helmet; a fleece neck gaiter; a black-brown long-sleeve combat shirt (base layer); an olive-brown plate carrier with a hard khaki admin/electronics panel, two padded shoulder straps with stacked ladder-lock buckles, a cummerbund with PALS, and three (probably four) closed-flap rifle-mag pouches on the front; three-tier tan polymer shoulder pauldrons on both shoulders (left one carries a blue-grey emblem plate and a small clip-on box); a brass-and-steel cylinder (antenna/beacon) rising behind the LEFT shoulder; tan segmented forearm guards on both forearms; a small lateral elbow cap on the left elbow; black hard-knuckle gloves; a black 45 mm belt; a right-side two-cell pouch above the belt and a right drop-leg panel with twin tall polymer carriers held by two thigh straps; a left drop-leg two-cell pouch (flap cell + grey hard box) with one thigh strap; dark low-contrast camo combat trousers with integrated knee sleeves and hard-shell cap kneepads, reinforced shins, cuffs stacked loosely over the boot collars; black 8-inch lace-up tactical boots with rubber toe bumpers and a lateral ankle strap. He holds the AR-12 carbine (not inventoried in detail here).

Parenting map (Blender): gaiter → neck (with head influence); combat shirt → body mesh (skinned); plate carrier front/back/cummerbund → spine_02/spine_03 (rigid-ish, slight lag); shoulder straps → clavicle/spine_03; pauldrons → upper-arm bone with ~50 % clavicle influence (they must ride the deltoid, not the torso); cylinder → back plate of vest; forearm guards → lowerarm bone (rigid); elbow cap → lowerarm with elbow twist; gloves → hand/finger bones; belt → pelvis; right upper hip pouch → vest lower edge or belt (see §10); drop-leg panels → thigh bone (rigid, hanger strap skinned to pelvis); kneepads → shin bone with ~30 % thigh; trousers → skinned; boots → foot/ball bones; laces as separate curves.

## 2. Head and neck

### 2.1 No head gear
- No helmet, no cap, no eye protection, no earpiece/comms headset (right ear at (720–735, 70–100) is bare; left ear hidden/turned). No face paint. Short hair, ~1-week stubble (face/hair covered by other analysts).

### 2.2 Neck gaiter / neck warmer
- **Real-world equivalent:** polyester fleece or jersey-knit neck gaiter (tube ~30 cm long, 20 cm flat diameter), worn pushed down and bunched into 3–4 horizontal rolls.
- **Position:** fills the collar opening of the plate carrier; spans x 745–855, y 128–200 (≈110 x 72 px → ~23 x 15 cm visible). Sits over the base-layer collar and UNDER both shoulder straps (straps overlap its lower edge at y≈190–200). Upper roll touches the jaw shadow at y≈130.
- **Form:** thick soft roll at the top (y 128–150), two more fold lines at y≈158 and y≈175, flat bunched fabric at y 185–200 disappearing under the vest; left side has a vertical fold descending at x≈835–850.
- **Colour:** olive-grey-brown; box median #373029, lit folds #74675E (760,170) / #6C5946 (815,195) / #5A5348 (800,170); deep shadows #0A0704; warm top highlight #6B4A33 (790,140) from skin bounce.
- **Material:** matte, soft, slightly fuzzy fleece — no sheen, broad soft folds, pilling at the top roll.
- **Weathering:** light dust on the top roll; slightly darker (sweat/dirt) where it meets the vest.

## 3. Base layer — combat shirt

- **Real-world equivalent:** dark "combat shirt" (torso in soft knit, sleeves in ripstop) with a padded, ribbed shoulder yoke. Long sleeves end under the glove cuffs.
- **Colour:** very dark warm grey-brown #332F2D (left sleeve box median), #49433E on the lit right shoulder (box 695–730,275–310), shadows to #040303; subtle sheen on fold crests (#6F6760–#7F7165).
- **Construction cues seen:**
  - Under both pauldrons the fabric shows **fine vertical ribs/pleats** (at (690–740,195–245) on the right shoulder and (880–930,255–300) on the left) — a quilted/ribbed shoulder yoke, pitch ≈2 px ≈ 4 mm.
  - A long **raised seam** runs down the outside of the left upper arm from the pauldron to the elbow (x≈925→955, y 260→330) with fabric pulling across it; another seam along the inner right forearm beside the forearm guard.
  - Diagonal micro-weave (ripstop grid) visible at 5x on the left sleeve between pauldron and forearm guard (885–945, 300–370).
  - Sleeve ends go INTO the glove gauntlet cuff (black neoprene cuff at (865–885, 425–440) on the left wrist, #444D5A, and under the right forearm guard wrist band at (700–712, 333–345)).
  - Elbow area of the left sleeve (935–965, 320–360) bunches; a small two-piece grey elbow cap sits on the lateral elbow (§7.3).
- **Weathering:** fine dust on the shoulder yoke; slight fading on fold crests; no tears.

## 4. Plate carrier ("Tactical Vest")

**Real-world equivalent:** medium plate carrier (10x12 in / 25x30 cm front plate bag) in olive-brown 500D Cordura, hard polymer admin/electronics panel riveted to the upper front, two PALS rows below it, three single-mag closed-flap pouches on the lowest front row, padded shoulder straps with stacked ladder-locks, PALS cummerbund. Front bag spans x≈740–890 (150 px ≈ 32 cm) and y≈195–400 (205 px ≈ 43 cm including the pouch row).

### 4.1 Front bag body
- Olive-brown Cordura, median #463E34, highlight #776958, shadow #0F0B09 (box 800–850, 245–262). The lit area directly around the admin panel reads #857660–#8E7D67 (805,215 / 790,200) because the panel itself is khaki; the fabric is darker than the panel.
- Edges bound with black/dark webbing binding (lower hem y≈400 reads #1A1810-ish).
- Upper edge (y≈195–200) sits ~2 cm below the collarbone under the gaiter.
- Left side panel (x 862–885, y 220–290) is almost black #1D1C1B (shadow) with a PALS row and a small olive/grey rectangular pouch at (875–895, 265–295).

### 4.2 Chest admin / electronics panel
- **Where:** x 745–828, y 198–240 (83 x 42 px ≈ 17.5 x 9 cm). Angular, bevelled hard panel, 6–8 mm thick, proud of the fabric, top edge canted slightly (viewer's-left end ~4 px higher).
- **Colour:** khaki polymer, median #7E715F, highlight #A09486, shadow #221C15; strong paint chipping (light edges, dark pits).
- **Details, viewer's left-to-right:**
  - Two silver domed rivets/LED-like studs in a vertical pair on the panel's left column at (752,208) #8F8E8B and (752,221) #8E8072, ≈3 px (6 mm) dia, blue-white speculars.
  - A dark grey rectangular label/plate at (770–795, 203–210) #78726D — engraved nameplate or a thin strip display (≈5 x 1.5 cm).
  - A horizontal slot/handle recess at (768–790, 224–230) #635750 (≈4.5 x 1.2 cm).
  - A single silver rivet at the panel's lower right (≈818,231).
  - Right ~40 % of the panel is a plainer field with a faint raised square boss (≈805–825, 205–235).
- **Attachment:** riveted/bolted onto the plate bag (corner rivets), or a hard placard on hook-and-loop plus the side-release buckle(s) below it (4.3).

### 4.3 PALS/webbing row under the panel (y 240–265)
- Two horizontal rows of 25 mm PALS webbing (#625745 lit at (800,258)) at ≈38 mm spacing across x 745–885.
- A black polymer **side-release buckle (female half)** at (745–765, 243–265), ≈4 x 4.5 cm, on a short webbing stub — consistent with a detachable front placard.
- A black hard rectangular object at (800–815, 243–258) with a silver pin at its lower end — most likely a black polymer belt-clip (knife/multitool clip or strobe mount); alternative: male half of a second side-release buckle. ≈3 x 3 cm.

### 4.4 Front magazine pouches (lowest row, y 265–320)
- **Count:** THREE fully visible closed-flap single rifle-mag pouches at x 790–815, 818–846, 850–882 (each ≈27 x 50 px ≈ 5.7 x 10.5 cm visible; real pouches ~7.5 x 14 cm; flaps 2–3 cm tall). A **fourth** is probably present at x≈755–790 behind the rifle receiver/magwell (the loadout icon shows a symmetric row and the PALS continues) but is not resolvable. State as "3 visible + 1 inferred".
- **Gap** between pouches ≈3 px (~6 mm); all on the same PALS row, bottoms aligned at y≈318.
- **Construction:** Cordura box pouch with tuck flap; each flap has a vertical centre strip (buckle/velcro tab) — the centre pouch shows a small square buckle plate at (830,300) ≈1.5 cm; outer pouches show a vertical stitched strip; bottoms have a drain-grommet shadow. Flap #574D3E (830,272), bodies #363028 / #343029 / #332F28, highlights ≈#5D5043, shadows ≈#030303.
- **Weathering:** dust along flap tops; darker grime at the bottoms.

### 4.5 Shoulder straps
- Two padded shoulder straps ~35 px (≈7 cm) wide: 25–38 mm olive webbing stitched down the centre of a black padded base.
  - **Right strap** (x 725–760, y 160–255): median #6D5F50 (lit), highlight #B4A697, shadow #0C0804. Three dark gunmetal **ladder-lock buckles** stacked at y≈165–185, 200–215, 232–250 (one every ≈35 px ≈ 7 cm), each spanning the strap width, worn-silver edges (#140F06 at (745,170)). A loose webbing tail passes through them.
  - **Left strap** (x 822–858, y 160–255): median #443D36, shadow #0B0907, highlight #958A7F. One large metal tri-glide/ladder-lock at (835–860, 165–185) #322D29 and two smaller ones at y≈205 and y≈240. A black elastic keeper loop at the top (805–830, 150–175).
- Both straps pass over the gaiter's lower edge and over the trapezius; on the left the rear bag edge is visible at (890–930, 165–195).
- The hangar fill gives the left strap a blue edge (#282624 at (835,215)).

### 4.6 Cummerbund and lower vest
- Below the pouch row the front bag continues to y≈400 with two more PALS rows (dark, #1A1810) carrying nothing in the centre; bound hem ≈ at the navel.
- A **cummerbund** (black/dark-olive, 3 PALS rows) wraps the flanks: visible at (840–900, 360–400) on the left with ladder-lock slots and vertical ribbed padding/mesh, shadowed under the right arm at (700–740, 380–400). Thickness ≈2 cm.
- Between the vest hem (y≈400) and the belt (y≈490) a 90 px (~19 cm) band of trousers/shirt is exposed — the carrier rides high.

### 4.7 Loadout-icon vest vs the figure's vest
- Icon (x 150–300, y 490–610) shows: lighter grey-khaki fabric (#4A4846 at (210,545), strap #908D90 at (190,520)), admin panel with grey label (#1A1816 at (222,520) — the icon's panel is dark where the figure's is khaki), two straps each with 3 ladder locks (matches), black crew-neck shirt with no gaiter, a row of **5** front pouches (two tall flap pouches, one narrow pouch with dangling cord, two more), **no pauldrons, no forearm guards, no cummerbund pouches**, and a grey elbow pad on the icon's viewer-right arm = soldier's LEFT elbow (agrees with the small cap on the figure's left elbow).
- Treat the figure as authoritative for colour and pouch count (3+1); use the icon only as evidence for the hidden fourth pouch and left-side elbow protection.

## 5. Shoulder pauldrons

Both are **three-tier articulated (lame-style) shoulder guards** of painted polymer (or thin alloy) over a padded fabric base, strapped around the upper arm and tabbed to the shoulder strap. Right one is key-lit and tan; left one is in blue fill and carries the emblem plate.

### 5.1 Right pauldron (viewer's left)
- **Tier 1 – cap plate:** x 668–718, y 190–240 (≈50 x 50 px ≈ 10.5 x 10.5 cm). Angular wedge sloping down and outward (top edge (672,190)→(718,205)), raised bevel rim ~3 px, dark slot near the top inner corner (≈710,195), two silver studs with blue speculars at ≈(700,200) and ≈(683,228) (≈6 mm dia). Face reads very light tan in the key light: #A3998D (690,205), rim #D2C5B5 (672,222); box median #453D3B (shadowed underside); shadow #0D0C0B. Lower edge overlaps tier 2 by ~1 cm.
- **Tier 2:** x 655–700, y 245–285 (≈45 x 40 px ≈ 9.5 x 8.5 cm), same tan with a rectangular recessed panel, highlight #A29588, median #47413C, shadow #090605.
- **Tier 3 – bicep band:** x 640–690, y 285–325, narrower (≈5 cm tall) curved band wrapping the biceps; a black elastic strap with a small silver cam buckle visible at the band's outer edge (≈(640–648, 300–318)).
- **Weathering:** heavy edge wear to the bevel (bright dust highlights), dark grey chips in the face centre, a sooty smear on tier 2.
- **Attachment:** webbing tab from under tier 1 hooks to the right shoulder strap at (720–730, 215–230); tiers linked by elastic/rivets on the inner side; bicep band closes with the cam buckle.

### 5.2 Left pauldron (viewer's right) — carries the emblem
- **Tier 1 – cap plate:** x 895–960, y 185–250 (≈65 x 65 px ≈ 13.5 x 13.5 cm; larger on screen because closer and more frontal). Plate reads dark gunmetal-grey here (#767779 (915,200), #42464B (925,235), median #535354) with a tan bevelled rim (#84807D highlights). Round rivet at ≈(905,205).
- **Emblem plate:** shield/pentagonal recess on the outer face, x 932–957, y 195–240 (≈25 x 45 px ≈ 5 x 9.5 cm), thin dark border, filled with a **light blue-grey brushed plate** #B3C2D6 (942,212) / median #5A6A7A / highlight #BFCEDC. On it a **white/pale emblem: two long diagonal strokes crossing in an "X" with a short vertical spike, forming a 4–5 point star / crossed-blades mark**, ≈12 px (2.5 cm) tall, slightly weathered (broken strokes). NOTE: this is NOT the UI header logo at (40–110, 115–185), which is a downward-pointing shield/arrowhead with a notched chevron and central vertical bar (#565859). Model the shoulder emblem as the X-star; alternative: the faction arrowhead if one unified logo is wanted.
- **Tier 2:** x 912–960, y 252–290 (≈48 x 38 px ≈ 10 x 8 cm), grey-blue in this light (median #514F4E, highlight #A2B3C5, shadow #101214), horizontal recess and a rivet.
- **Small clip-on box:** light blue-grey rectangular block on tier 2's outer face at ≈(945–960, 258–280) (≈15 x 22 px ≈ 3 x 4.5 cm), #AFC2D5 (952,268) — reads as a small IR strobe / beacon / light module (alt: hard pen pouch). It is the lightest object on the figure after the emblem plate.
- **Tier 3 – bicep band:** x 905–965, y 290–335, dark, with a horizontal slot; ends at the ribbed shoulder-yoke fabric.
- **Weathering:** chipped bevel, scratches across the emblem plate, dust on the top edge.
- **Attachment:** as right; tab to left shoulder strap at (885–895, 205–220).

**Ambiguity (colour):** right pauldron tan vs left pauldron grey. Best interpretation: both the same desert-tan painted polymer, the left in blue fill light; the emblem plate and small box are a genuinely different, lighter material (brushed aluminium / pale grey polymer). Alternative: the left pauldron is deliberately grey-blue steel (faction/rank marking). If asymmetry is chosen, keep tan bevel rims on both.

## 6. Cylinder / antenna behind the LEFT shoulder

- **Correction to the brief:** the cylinder is behind the soldier's **LEFT** shoulder (viewer's right), at x 898–912, y 135–185 (≈14 x 50 px ≈ 3 cm dia, 10.5 cm visible), rising vertically just outboard of the left shoulder strap and inboard of the pauldron cap, i.e. mounted on the rear plate bag / upper back.
- **Form:** rounded black cap (y 135–148, #111518) like a rubber antenna boot; brass/gold body (y 148–170; #705E46 → specular #D3CAAF / #CECCC7) with a ring groove at y≈152; steel/silver lower segment (y 170–185; #757D83, #6C6B71, #585E67) disappearing behind the strap.
- **Best interpretation:** stubby radio antenna base / beacon (brass BNC-type connector + black rubber tip) on a radio in a back pouch. **Alternatives:** brass-cased 40 mm illumination/signal flare clipped to the back; chem-light holder; hydration bite valve (unlikely — too rigid and brass-coloured).
- **Attachment:** parent to the vest back bag (spine_03); slight backward lean (~5°).

## 7. Arms — bicep bands, elbow, forearm guards

### 7.1 Bicep bands — see §5 (tier 3 of each pauldron).

### 7.2 Right forearm guard (viewer's left; the arm on the rifle grip)
- **Real-world equivalent:** segmented hard-shell forearm guard (motocross/airsoft forearm protector style): three polymer plates on a padded sleeve with two elastic straps and cam/ladder buckles.
- **Where:** x 625–700, y 308–358 (≈75 x 50 px ≈ 16 x 10.5 cm), from ~3 cm below the elbow to the wrist; wrist end toward the glove at x≈700.
- **Plates:** (a) elbow-end band (x 625–645) with a **silver cam-buckle loop** on its outer edge at ≈(633–640, 315–325) and a strap keeper; (b) main plate (x 645–685) with two horizontal grooves at y≈330 and y≈345, a raised central rib, black stencilled marks (smudged lettering ≈(660–675, 335–342)); (c) wrist band (x 685–700) against the glove cuff.
- **Colour:** lit tan #D1BBAA (655,328), #CEB8A6 (660,330); mid #7E6C5C (650,345); box median #837163; highlight #C6B19F; shadow #191511. Grey-black paint-loss streaks and dark scuffs run diagonally along the plates.
- **Underside:** black nylon/neoprene sleeve, black 25 mm straps.

### 7.3 Left forearm guard and lateral elbow cap (viewer's right)
- **Forearm guard:** x 880–945, y 360–435 (≈65 x 75 px ≈ 13.5 x 16 cm, seen more end-on). Three plates: upper band (885–940, 365–385); main plate (885–940, 385–420) with a vertical raised rib and a small rectangular grey inset at ≈(905,407) (#4F555C, ≈1 x 2 cm — tiny indicator window or recessed panel); lower band near the wrist (900–940, 420–435). A black 25 mm strap with ladder-lock across y≈425–435 (#3C3D45). Colour in blue fill: median #575655, lit tan #8C7A6E (893,398), highlight #897D73, shadow #1A1B1C. Weathering: scuffs on the rib, dust on top faces.
- **Lateral elbow cap:** small two-piece grey polymer cap on the OUTSIDE of the left elbow at x 950–968, y 335–365 (≈18 x 30 px ≈ 4 x 6 cm): an upper slim fin (950–965, 335–350) and a lower square pad (952–968, 350–365), lighter grey-blue (#A2B3C5-class highlights), held by a black elastic around the elbow. Matches the elbow pad in the vest icon. **No equivalent visible on the right elbow** (hidden behind the rifle stock); best guess: present on both, right simply hidden.

## 8. Gloves

- **Real-world equivalent:** hard-knuckle tactical gloves (Mechanix M-Pact / Oakley SI Assault class): goatskin/synthetic leather palm and fingers, stretch-knit back, moulded TPR knuckle guard, TPR finger-joint pads, short neoprene gauntlet cuff with hook-and-loop closure.
- **Right glove** (x 690–750, y 340–390): hand on the pistol grip; index finger extended along the receiver at (735–752, 372–385). Knuckle guard: ribbed black TPR plate across the four MCP knuckles at (695–735, 345–370), each knuckle a rounded boss with 2–3 horizontal ribs; back of hand shows a fine carbon/honeycomb texture; finger backs have stitched articulation panels at each joint. Colours: median #36322F, back #605A55 (700,345), fingers #423E3C (745,380), dusty knuckle tops #8F837C–#9A8D85 (708,352 / 705,350), shadow #0B0A09. Cuff: black neoprene under the forearm guard wrist band.
- **Left glove** (x 825–880, y 425–470): wraps under the handguard, thumb over the top rail, fingers curled under at (830–860, 445–470). Same construction; cooler colours: median #343436, back #5F564E (850,445), fingers #3C3739 (840,462), rim-lit edge #3D3B43 (862,440), highlight #67686D, shadow #060708. Gauntlet cuff at (865–885, 425–440) #444D5A with a velcro tab.
- **Weathering:** pale dust on knuckle tops and finger backs; shiny worn leather on finger pads; palm (not visible) assume suede-grey.

## 9. Belt

- Black nylon **rigger-style belt**, y 490–512 (22 px ≈ 4.5 cm wide), visible x 700–760 and x 850–880 (middle hidden behind the rifle magazine). Box median #22211F, shadow #090908, highlight #766352 (dust). Small silver hardware glint at (750,500) — a keeper or the edge of a cobra-style buckle; buckle itself behind the mag (x 765–800) — best guess a flat metal cobra/quick-release buckle, offset slightly to the soldier's right.
- Trouser waistband and fly visible between belt and vest hem: waistband seam y≈475–490, fly seam vertical at x≈810, belt loops suggested at x≈805 and x≈850 (dark vertical bars y 475–495).
- The belt carries the right drop-leg hanger strap (black, from (690–700, 505) down to the twin carriers) and the left drop-leg hanger (behind the left pouch at (905–915, 480–500)). Thin keeper straps hang at (668–682, 575–605) ending in tan metal tips.

## 10. Right hip and right drop-leg rig (viewer's left)

### 10.1 Upper right pouch (above the belt)
- x 682–722, y 395–470 (≈40 x 75 px ≈ 8.5 x 15.5 cm). **Two-cell vertical pouch**: two slim tubes with tan/khaki polymer face plates and a black polymer body/edge, a lid per cell with a small silver snap/stud at ≈(700,420) and ≈(712,420); a black elastic/retention strip between the cells. Colours: box median #21201B (shadowed), highlights #786756, #6F6251 (685,445), #574D45 (700,430), shadow #020100.
- **Position puzzle:** it hangs at y 395–470, ABOVE the belt (y 490), beside the lower ribs/hip — so it is attached either to the lower side PALS of the plate carrier/cummerbund or to a hanger dropping from the vest. **Best interpretation:** double pistol-magazine pouch (for the P9) on the carrier's right lower side PALS. **Alternatives:** double 40 mm grenade pouch; shotgun-shell/flare pouch; holster seen edge-on (rejected — two lidded cells are clearly visible).

### 10.2 Twin polymer carriers on the right thigh (drop-leg)
- x 662–735, y 482–600 (≈73 x 118 px ≈ 15.5 x 25 cm total); each tube ≈25 x 110 px ≈ 5 x 23 cm. Two tall open-top hard-shell carriers side by side on a drop-leg platform: **tan/FDE face plates** (#816F5F highlights; #4C4034 (690,540); #584631 (700,530)) riveted to **black polymer bodies** (#2A2622 (715,545), shadows #070604), 3–4 horizontal vent slots down each face, a round rivet near the top, small stencil marks, a black bungee tension cord. The inner tube is slightly taller (top y≈482 vs ≈490).
- **Platform straps:** two black 1.5-inch thigh straps around the right thigh at y 520–536 and y 560–580 (each ≈16 px ≈ 3.3 cm; medians #171615 / #141313; highlights #393632), gunmetal ladder-lock buckles on the front of the thigh at ≈(733,527) #4C4943 and ≈(733,567); flat (non-elastic) straps. Tails hang from the lower buckle to (668–682, 575–605), tan metal tips.
- A black hanger strap runs from the belt (≈695, 505) down behind the carriers.
- **Best interpretation:** twin open-top polymer rifle-magazine carriers (height fits a 5.56 STANAG mag plus overhang) — his two spare rifle mags. **Alternatives:** tourniquet + flashlight holders; twin 40 mm grenade/flare tubes. **Not a pistol holster** — no pistol is visible anywhere (§16).

## 11. Left hip and left drop-leg rig (viewer's right)

- Pouch block at x 905–960, y 462–560 (≈55 x 100 px ≈ 11.5 x 21 cm), two cells side by side:
  - **Inner cell (x 905–935):** olive Cordura/polymer box with a top flap and a square metal snap at (930,478) (#565955), vertical ribbed face (#4B5358 (922,500) in blue fill), shadow #080806.
  - **Outer cell (x 935–960):** grey hard polymer box (#363A3B (948,505), highlight #53595B) with hinged lid, a vertical rib and a small latch — radio/GPS hard case or rigid utility box.
  - Top surface #4E504D (925,475). A further dark item/strap behind at (900–915, 540–560).
- **Strap:** a single black 1.5-inch thigh strap around the left thigh at y 560–580 (x 830–900; median #312D29 at (865,570), shadow #050504), buckle at the front ≈(840,570) — pouch block hangs just above it: drop-leg platform with lower strap below the pouch.
- **Best interpretation:** inner cell = **frag-grenade pouch** (flap + snap, matches the "Frag Grenade" utility slot); outer cell = hard utility/radio box. **Alternatives:** double rifle-mag hard pouch; rolled dump pouch. Do not add a visible grenade — none is rendered.

## 12. Trousers (combat trousers)

- **Real-world equivalent:** combat trousers (Crye G3/G4-style) with articulated knees, integrated kneepad sleeves, reinforced shins, stretch gusset, in a dark low-contrast camouflage.
- **Camo pattern:** organic soft-edged blotches, 15–40 px (3–8 cm), four values: near-black #0A0B08 (785,560); charcoal-brown #171513 (765,590) / #262524 (R-thigh box median); olive-brown #322E29 (725,560) / #3E3A35 (L-thigh box median); tan #615348 (880,595) / #534C3F (840,590) / #685D53 (R-thigh highlights). Tan blotches are larger and more frequent on the lit thighs and shins ((700–760, 585–615), (880–920, 585–615), (895–915, 730–760) #3F3932); shadows kill contrast to near-uniform black. No hard/digital edges. Closest real pattern: MultiCam Black / A-TACS LE; model as a dark 4-tone blotch texture with 10–15 % contrast.
- **Construction visible:**
  - Waistband with belt loops and centre fly (seam x≈810, y 475–560), heavy topstitching.
  - Crotch gusset: large dark diamond (780–840, 540–600), stress folds radiating to the inner thighs.
  - Thighs: outer-thigh seams hidden by the drop-leg rigs; no cargo-pocket flaps visible (absent or hidden under the rigs) — best guess: standard side cargo pockets exist under the rigs; do not model flaps where the rigs sit.
  - **Knee sleeves:** a black, smoother panel surrounds each kneepad — right (690–770, 610–700), left (860–945, 605–700) — a sewn-in black Cordura/neoprene knee-cap sleeve (#252527 at (770,660)) into which the hard cap is inserted; a horizontal black strap with gunmetal ladder-lock crosses beside/behind the right knee at (745–770, 640–660) (buckle ≈(758,650)) and a matching one on the left knee's inner side.
  - Above each knee the fabric is gathered into articulation darts (y 575–610), with a dark horizontal stitched band at (700–780, 578–585) and (830–920, 575–585).
  - **Shins:** reinforced lower-leg panel; the left outer shin shows a vertical dark panel with piping at x 925–965, y 690–760 (#27282A at (930,700)) — a lower-leg cargo pocket or reinforcement panel with hidden vertical zip (ambiguous; model as a slim calf pocket with piped edge). The right shin shows a vertical seam at x≈735–745, y 700–790.
  - **Cuffs/hem:** legs NOT tucked in. Hems (≈y 800–810) loose, slightly bloused, **stacked over the boot collars**: 2–3 heavy folds at (690–770, 760–810) and (880–960, 760–810). Cuff colours #171514 (720,790), #25221B (920,790). No visible drawcord, elastic or ankle tie; slightly tapered hem.
- **Weathering:** dust on upper thigh surfaces (#685D53 highlights); darker grime at cuffs; knee sleeves scuffed.

## 13. Kneepads (integrated hard-shell caps)

- **Real-world equivalent:** hard-shell cap kneepads (Crye AirFlex hard cap / Hatch XTAK type) inserted into the trouser knee sleeves, with a rear strap.
- **Right kneepad:** cap x 695–760, y 615–700 (≈65 x 85 px ≈ 13.5 x 18 cm). Hexagonal/angular cap: a tan **bevelled outer frame** (#5F554F (703,650), #70645A (710,640), highlight #796C62) ~6 px (12 mm) wide surrounding a **recessed darker centre panel** (#2A2620 (718,660), #2F2B27) that is heavily pitted/chipped; two cut-outs along the top edge — a "D"-shaped slot at ≈(727,625) and a rectangular slot at ≈(705,622); a small square bolt/rivet at ≈(745,632); a short slot near the bottom right ≈(740,690). Cap bulges ~2 cm and tapers downward. Black flexible base/sleeve (#252527) wraps the knee; strap with buckle at (748–770, 640–660).
- **Left kneepad:** cap x 862–940, y 610–700 (≈78 x 90 px ≈ 16 x 19 cm, more frontal). Same design: frame reads grey-blue here (#7A7972 (870,625)) / tan where lit (#948169 (872,640)), centre #343532 (893,655); three slots along the top edge, a side slot on the outer edge; a **small red/rose tab** on the outer side at ≈(925–930, 636–652) (#917A7B at (927,640)) — rubber pull-tab or coloured strap end (≈1 x 3 cm); keep it, it is the only warm accent on the legs. Black base sleeve, inner-side strap.
- **Weathering:** both centres heavily chipped (paint flaked to dark substrate on ~30–40 % of the face), dust on the upper bevel, grime in the slots.

## 14. Boots

- **Real-world equivalent:** 8-inch black leather/nylon tactical boots (Lowa Zephyr / Salomon Quest 4D class): full-grain black leather vamp and quarters, nylon padded collar, moulded rubber toe bumper, rubber rand, deep-lug outsole, round laces, small lateral collar strap.
- **Dimensions:** collar top y≈800 to sole bottom y≈905–912 → ≈110 px ≈ 23 cm tall; right boot length (side view, foreshortened) x 648–770 ≈ 122 px (real ~30 cm); sole thickness ≈ 25 px (5 cm) at the heel incl. lugs.
- **Right boot** (seen from its lateral/outer side, viewer's left):
  - Eyelets: **6–7 pairs** along the throat, visible on the near side at y≈808, 818, 828, 838, 848, 858 (+ a top pair at the collar). Lower 4–5 are round gunmetal eyelets (#37302C at (706,816)); top 2 larger/open (speed hooks) on the padded collar. Lace: round black cord, criss-crossed, bow at the top tucked behind the collar.
  - A **lateral collar strap** with small buckle at (745–760, 812–830): black webbing ~1.5 cm rounding the ankle — model on both boots.
  - Stitched toe-cap seam across the vamp at (690–740, 850–860); moulded **rubber toe bumper** (655–700, 858–885), dusty (#363231 (668,866), highlight #6D645E); leather box median #242322, highlight #A19689, shadow #0B0A08.
  - Sole: black rubber rand, bluish midsole reflection #363D4B (700,880), outsole #26282E (720,890), chevron lugs ~8 mm deep at ~1.5 cm pitch, heel breast at x≈735.
- **Left boot** (seen from the front, viewer's right):
  - **7–8 lace crossings**; eyelets at y≈810, 822, 834, 845, 856, 866 plus the top collar pair; eyelets #0C0C0C (927,812) in shadow; laces #4A473F (935,850), #41362D (915,840).
  - Padded tongue/collar rises to y≈800; lateral collar strap at (952–965, 820–838).
  - Toe bumper (900–980, 860–895) with dusty tan cast #A6998E; leather #2C2924 median; toe #40352C (925,885); sole #11100D (median), lugs #010101 (960,905).
- **Trouser/boot interface:** hem drapes over the collar; the collar's top ~1–2 cm and all the laces are exposed; no gaiter, no tucked blousing.
- **Weathering:** dust on toe bumpers and vamp tops; scuffed lateral quarters; contact shadow and a soft reflection on the floor (floor #E7D4BF lit, #D9C6B1 tiles).

## 15. Weapon handling (brief; the carbine is another analyst's task)

- AR-12 carbine at low ready across the body: stock in the right shoulder pocket at (690–730, 240–330), right hand on the pistol grip, left hand under the M-LOK handguard at (825–880, 425–470), muzzle down-left to (885,560). Black cylindrical weapon light on the handguard's right side at (808–842, 358–402). Tan/gold accent plates on receiver and stock (#484541 class). Gear contact points: stock against right pauldron tier 3 and the vest; magazine (735–790, 420–470) in front of the belt buckle; handguard over the left thigh strap.

## 16. Loadout-card icons vs the figure — contradictions

| Card | Icon shows | Figure shows | Verdict |
|---|---|---|---|
| ARMOR – Tactical Vest (150–300, 490–610) | Lighter grey-khaki carrier, 5 pouches, no pauldrons/forearm guards, black crew-neck shirt, grey elbow pad on soldier's LEFT elbow | Olive-brown carrier, 3 visible (+1 hidden) pouches, pauldrons + forearm guards, gaiter, left elbow cap | Follow the figure; icon only confirms hidden 4th pouch and left-only elbow pad |
| UTILITY – Frag Grenade (185–250, 635–725) | Olive Mk 2 "pineapple" grenade (#4B4634 body (215,690), grey fuse #414342 (215,650)) | No grenade visible anywhere | Carried inside the left-hip flap pouch (§11) — do not model an exposed grenade |
| SECONDARY – P9 Sidearm (150–300, 370–450) | Black P226-style DA/SA pistol with rail light (#575757 slide (230,392), #1C1E1D grip) | **No holster or pistol visible**; right thigh occupied by twin polymer carriers | Omit, or add a holster at the small of the back (invisible from the front). Flag to orchestrator |
| PRIMARY – AR-12 Carbine | Red-dot/holo optic on top, foregrip/light under the handguard | Side-mounted cylindrical light; top optic not clearly visible from this angle | Weapon analyst to decide |

## 17. Items explicitly NOT present

No helmet, no eyewear, no headset, no watch (wrists covered), no visible knife (unless the black clip at (800–815, 243–258) is a sheath clip), no visible pistol/holster, no exposed grenade, no backpack visible from the front (straps go over the back; the cylinder implies a back-mounted radio), no name tapes or flag patches (the only insignia is the shoulder emblem), no hydration tube.

## 18. Weathering summary by zone

- **Dust gradient:** heaviest on upward-facing tan armour (pauldron caps, forearm-guard tops, kneepad frames: highlights to #D2C5B5) and on glove knuckles (#8F837C); medium on boot toes and vamps (#A19689); lightest on dark Cordura (vest highlights only #776958).
- **Paint chips:** admin-panel edges, both pauldron bevels, both kneepad centres (most severe), forearm-guard ribs. Chips irregular, 2–8 mm, exposing dark grey-brown substrate.
- **Grime/soot:** diagonal black streaks on the right forearm guard (stencil area 660–675, 335–342), pouch bottoms, trouser cuffs, boot quarters.
- **Fabric wear:** sheen on base-layer fold crests; fading on the gaiter top roll; stress whitening at the trouser crotch gusset.
- **Hardware:** gunmetal buckles with bright worn edges; silver rivets with blue speculars (panel (752,208)/(752,221); right pauldron studs).

## 19. Ambiguities and best interpretations (consolidated)

1. **Left vs right pauldron colour** — same tan material under different light (best) vs deliberate grey-blue left pauldron (alt). Emblem plate and small box are a genuinely lighter material either way.
2. **Shoulder emblem design** — X / 4-point star with central spike as rendered (best) vs the UI faction arrowhead logo (alt).
3. **Cylinder behind LEFT shoulder** — radio antenna base (best) vs brass flare/chem-light (alt). It is on the LEFT, not the right as the brief says.
4. **Upper right pouch** — double pistol-mag pouch on carrier side PALS (best) vs double 40 mm/shell pouch (alt).
5. **Right thigh twin carriers** — open-top polymer rifle-mag carriers (best) vs tourniquet/flashlight holders or 40 mm tubes (alt).
6. **Left hip block** — frag-grenade flap pouch + hard utility box (best) vs double hard mag pouch (alt).
7. **Fourth front mag pouch** — inferred behind the rifle; icon supports it.
8. **Black object at (800–815, 243–258)** — polymer belt clip/knife-sheath clip (best) vs buckle half (alt).
9. **Right elbow cap** — hidden; mirror the left one (best) or omit (alt).
10. **Left shin panel (925–965, 690–760)** — slim calf pocket with piped edge and hidden zip (best) vs plain reinforcement panel (alt).
11. **Belt buckle** — hidden; cobra quick-release (best) vs plain webbing buckle.
12. **Trouser cargo pockets** — present under the drop-leg rigs (best); none visible.
13. **Pistol/holster** — absent from the render despite the loadout card; flag rather than invent.
14. **Boot eyelet count** — 7 pairs (6 eyelets + 1 top hook pair) is the best count; 8 possible on the left boot.

## 20. Quick dimension sheet (px → mm at 2.1 mm/px)

| Item | Box (x0,y0)-(x1,y1) | px (w x h) | ≈ mm |
|---|---|---|---|
| Neck gaiter | (745,128)-(855,200) | 110 x 72 | 230 x 150 |
| Admin panel | (745,198)-(828,240) | 83 x 42 | 175 x 90 |
| Vest front bag | (740,195)-(890,400) | 150 x 205 | 315 x 430 |
| Shoulder strap width | — | 35 | 73 |
| Mag pouch (each) | e.g. (818,268)-(846,318) | 28 x 50 | 60 x 105 |
| R pauldron cap | (668,190)-(718,240) | 50 x 50 | 105 x 105 |
| L pauldron cap | (895,185)-(960,250) | 65 x 65 | 135 x 135 |
| Emblem plate | (932,195)-(957,240) | 25 x 45 | 52 x 95 |
| Small box on L pauldron | (945,258)-(960,280) | 15 x 22 | 30 x 45 |
| Cylinder | (898,135)-(912,185) | 14 x 50 | 30 x 105 |
| R forearm guard | (625,308)-(700,358) | 75 x 50 | 160 x 105 |
| L forearm guard | (880,360)-(945,435) | 65 x 75 | 135 x 160 |
| L elbow cap | (950,335)-(968,365) | 18 x 30 | 40 x 65 |
| Belt | y 490–512 | 22 tall | 45 |
| Thigh strap | y 520–536 | 16 tall | 33 |
| R upper pouch | (682,395)-(722,470) | 40 x 75 | 85 x 155 |
| R twin carriers | (662,482)-(735,600) | 73 x 118 | 155 x 250 |
| L hip block | (905,462)-(960,560) | 55 x 100 | 115 x 210 |
| R kneepad cap | (695,615)-(760,700) | 65 x 85 | 135 x 180 |
| L kneepad cap | (862,610)-(940,700) | 78 x 90 | 165 x 190 |
| Boot height | y 800–910 | 110 | 230 |
| Boot sole thickness (heel) | — | 25 | 50 |

---

## Errata (consolidator)

Corrections after cross-checking against the other analyst notes and re-sampling `reference_full.png`. The body of this file is unchanged; `analysis_consolidated.md` carries the agreed values.

1. **§4.2 viewer-relative wording (convention slip).** "Two silver domed rivets ... on the panel's left column at (752,208)/(752,221)" → the column on HIS RIGHT (viewer's left). "A single silver rivet at the panel's lower right (≈818,231)" → his LEFT lower corner. "Right ~40 % of the panel is a plainer field (≈805–825 ...)" → the his-LEFT ≈40 %. (The list heading says "viewer's left-to-right", but the convention requires "viewer's" on each use.)
2. **§13 Right kneepad "a short slot near the bottom right ≈(740,690)".** Viewer-relative; it sits on the inner (his-LEFT) side of the right kneepad.
3. **§14 Right boot "(seen from its lateral/outer side, viewer's left)".** Wrong side. The right foot is turned ≈90° to his right (toe at x=631), so the camera sees its MEDIAL (instep/arch) side — a right foot turned outward shows its inside from the front. Consequently the collar strap/buckle at (745–760, 812–830) is on the medial side of the right boot, while on the left boot (seen head-on) it shows on the LATERAL side at (952–965, 820–838): model a collar strap that wraps the whole ankle, buckle visible on the camera-facing side. "Heel breast at x≈735" and the eyelet count are unaffected.
4. **§2.1 "right ear at (720–735, 70–100) is bare".** Coordinates are outside the head. The right ear is at x 753–770, y 84–112 (face note §2). "Bare" stands.
5. **§4.4 Front mag pouches "y 265–320 ... bottoms aligned at y≈318".** Luminance profiles at x=832 and 866 show the lit pouch bodies continuing to y≈332 with the bottom-edge shadow at y≈336–356: pouch bottoms ≈334, pouches ≈265–335 (≈70 px ≈ 15 cm incl. flap). The vest hem at y≈395–400 (§4.6) is confirmed.
6. **§0 scale: "Height ≈ 890 px ... about 7.8 heads tall; chin y≈125, head ≈103 px".** Consolidated scale is 875 px standing (skull top y=20 → right sole y=895), head 109 px (chin y=129), 8.0 heads, 0.212 cm/px (4.72 px/cm). The §20 mm figures (at 2.1 mm/px) are ≈1 % high — negligible.
7. **§15 "muzzle down-left to (885,560)".** Image-relative; the muzzle points down toward his LEFT thigh, tip at (903,570) (weapon note).
8. **§6 / §19 ambiguity 3.** Confirmed by the consolidator on the image: the brass cylinder is behind his LEFT shoulder (x 898–912). Your correction to the brief stands.
