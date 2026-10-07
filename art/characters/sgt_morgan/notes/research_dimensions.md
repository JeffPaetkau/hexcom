# Research D — Real-world dimensions reference for Sgt. Alex Morgan

Written 2026-10-06 15:25–15:55 UTC (time-boxed ~30 min of fetching + 10 min write-up).
Target body: lean athletic male, 185 cm, 82–85 kg. All numbers in **mm** unless noted.
Every row has a source column. Tags: **[opened]** = page actually fetched with WebFetch/curl and the number read from it;
**[snippet]** = number came from a search-result snippet of a page I could NOT open (403/404/503/paywall) — verify before relying on it;
**[derived]** = computed here from opened data; **[uncited]** = my own typical value, no source — measure from the reference instead.

## 0. What was actually run (reproducible)

| Step | Command / URL | Result | Time |
|---|---|---|---|
| ANSUR II male CSV download | `curl -L -A "Mozilla/5.0" -o ansur2_male.csv https://tools.openlab.psu.edu/publicData/ANSUR_II_MALE_Public.csv` (link found by opening https://www.openlab.psu.edu/ansur2/) | 2.0 MB, 4082 subjects × 93 measures, saved `/home/user/sgt_morgan/assets/dimensions/ansur2_male.csv` | ~3 s |
| Target-window statistics | `python3 -I /home/user/sgt_morgan/scripts/research/ansur2_target_stats.py <csv> /home/user/sgt_morgan/assets/dimensions/ansur2_target_stats.md` | tight filter stature 1830–1870 & 82–85 kg → **n=30**; loose (78–90 kg) → n=115; stature-only → n=380. Full 93-row table in `ansur2_target_stats.md` | 0.47 s |
| Crye AirFlex knee pad spec sheet | WebFetch https://www.cryeprecision.com/Resources/en/SpecSheets/PADKC3_SPEC.pdf → saved → `pdftotext -layout` | Only weight (0.34 lb/pair) and "one size"; no dimensions | — |
| AustriAlpin FC45CF-K datasheet | WebFetch https://www.austrialpin.at/en/service/data-sheet/pdf/fc45cf-k-cobraframe/ → `pdftotext` (`assets/dimensions/austrialpin_fc45cf_k.pdf`) | 38 × 58 × 10 mm, 41 g, 45 mm webbing, 9 kN / 18 kN | — |
| Belleville C312ST spec sheet | WebFetch https://www.bellevilleboot.com/pdf/C312ST.pdf → `pdftotext` (`assets/dimensions/belleville_C312ST.pdf`) | 8 in height "standard military height", Vibram Incisor, padded collar/tongue | — |
| Failed downloads | `https://www.openlab.psu.edu/ansur2/ANSUR_II_MALE_Public.csv` (404 — wrong host), `https://apps.dtic.mil/sti/tr/pdf/ADA244533.pdf` (Greiner 1991 hand anthropometry; DTIC returns an HTML challenge page both to WebFetch (403) and curl), Europe PMC fullTextXML for PMC3485457 (not open-access, 150-byte stub) | | |
| Pages that refused WebFetch | eotechinc.com (404 on product URL), surefire.com (404), aimpoint.us (403), salomon.com (404), lowa.com/en-us (404; **professional.lowa.com worked**), cryeprecision.com/jumpable-plate-carrier-2-0 (404), austrialpin product page (403; datasheet PDF worked), msis.jsc.nasa.gov (DNS gone), pmc.ncbi.nlm.nih.gov (CAPTCHA), link.springer.com tables (cookie redirect), darntough.com, mechanix.com, buff.com, magpul PMAG page (404), tingleyrubber/pelicansales (partial/404), decathlon (403), rockywoods/needlesports (no dims on page) | Replaced by retailer/third-party pages where possible (listed per row) | |

Scripts: `/home/user/sgt_morgan/scripts/research/ansur2_target_stats.py`. Data: `/home/user/sgt_morgan/assets/dimensions/`.

## 1. Anthropometry — ANSUR II, filtered to the target body

Source for every row in this section: ANSUR II MALE public CSV **[opened]** (link page: https://www.openlab.psu.edu/ansur2/ ; file: https://tools.openlab.psu.edu/publicData/ANSUR_II_MALE_Public.csv). Units mm (the `weightkg` column is hectograms). "Tight" = 30 men 1830–1870 mm tall weighing 82.0–85.0 kg (mean stature 1846, mean weight 83.6 kg) — this is literally the Sgt. Morgan body. "Loose" = n=115 (78–90 kg) as sanity check. Full-population 50th/95th percentile shown for context. **Recommendation: build the base mesh to the Tight column.**

### 1a. Heights / lengths (standing landmarks from floor)

| Measure (ANSUR name) | Tight mean | Loose mean | Pop 50th | Pop 95th |
|---|---|---|---|---|
| Stature | 1846 | 1847 | 1755 | 1870 |
| Cervicale height (C7, base of neck back) | 1596 | 1596 | 1517 | 1623 |
| Suprasternale height (top of sternum) | 1513 | 1514 | 1437 | 1540 |
| Acromial height (shoulder point) | 1516 | 1515 | 1439 | 1546 |
| Axilla height (armpit) | 1405 | 1404 | 1328 | 1427 |
| Chest (nipple) height | 1363 | 1362 | 1289 | 1387 |
| 10th rib height | 1184 | 1185 | 1119 | 1211 |
| Waist height (omphalion / navel) | 1127 | 1126 | 1055 | 1145 |
| Iliocristale height (top of hip bone) | 1128 | 1129 | 1061 | 1148 |
| Trochanterion height (hip joint) | 958 | 959 | 899 | 985 |
| Buttock height | 939 | 943 | 885 | 972 |
| Crotch height (inseam landmark) | 898 | 904 | 845 | 925 |
| Wrist height (standing, arms down) | 887 | 887 | 847 | 917 |
| Knee height, mid-patella | 517 | 520 | 487 | 536 |
| Lateral femoral epicondyle height (knee joint axis) | 523 | 523 | 491 | 537 |
| Tibiale height | 498 | 499 | 468 | 513 |
| Lateral malleolus height (ankle bone) | 76 | 76 | 73 | 83 |
| Sitting height | 956 | 953 | 918 | 977 |
| Eye height sitting | 842 | 837 | 804 | 860 |
| Span (fingertip to fingertip) | 1897 | 1908 | 1812 | 1957 |
| Thumb-tip reach | 851 | 848 | 811 | 886 |

[derived] Standing eye height ≈ stature − (sitting height − eye height sitting) = 1846 − 114 = **~1732 mm**. Navel-to-crotch ≈ 1127 − 898 = 229 mm. Shoulder (acromion) to crotch = 618 mm. Floor-to-knee-axis 523 → shank+foot = 523; thigh (trochanterion→knee axis) = 958 − 523 = **435 mm**; lower leg (knee axis→lateral malleolus) = 523 − 76 = **447 mm**.

### 1b. Breadths / depths

| Measure | Tight mean | Loose mean | Pop 50th | Pop 95th |
|---|---|---|---|---|
| Biacromial breadth (bone shoulder width) | 424 | 426 | 415 | 447 |
| Bideltoid breadth (outside of deltoids) | 506 | 507 | 509 | 567 |
| Chest breadth | 290 | 290 | 289 | 320 |
| Chest depth | 245 | 244 | 253 | 298 |
| Waist breadth | 315 | 314 | 325 | 385 |
| Waist depth | 219 | 221 | 234 | 300 |
| Bicristale breadth (iliac crests) | 280 | 279 | 275 | 305 |
| Hip breadth (standing) | 343 | 345 | 344 | 387 |
| Buttock depth | 232 | 236 | 246 | 291 |
| Interscye I / II (back width between armpits) | 425 / 449 | 423 / 450 | 430 / 450 | 491 / 501 |
| Forearm–forearm breadth (arms folded) | 561 | 565 | 579 | 667 |
| Thigh clearance (seated thigh thickness) | 175 | 177 | 180 | 207 |
| Shoulder length (neck to acromion) | 155 | 157 | 150 | 167 |
| Waist back length (C7→waist) | 490 | 487 | 477 | 524 |
| Waist front length sitting | 396 | 395 | 386 | 438 |

### 1c. Girths (circumferences)

| Measure | Tight mean | Loose mean | Pop 50th | Pop 95th |
|---|---|---|---|---|
| Neck circumference | 389 | 390 | 395 | 443 |
| Neck circumference at base | 431 | 432 | 433 | 479 |
| Shoulder circumference | 1175 | 1181 | 1176 | 1288 |
| Chest circumference | 1029 | 1030 | 1056 | 1207 |
| Waist circumference (omphalion) | 893 | 894 | 937 | 1131 |
| Buttock circumference | 994 | 1006 | 1017 | 1149 |
| Vertical trunk circumference | 1688 | 1685 | 1664 | 1814 |
| Biceps circumference flexed | 342 | 349 | 357 | 418 |
| Forearm circumference flexed | 305 | 309 | 310 | 348 |
| Wrist circumference | 179 | 178 | 176 | 191 |
| Thigh circumference (upper) | 600 | 610 | 624 | 723 |
| Lower thigh circumference | 402 | 405 | 408 | 463 |
| Calf circumference | 382 | 387 | 392 | 443 |
| Ankle circumference | 228 | 231 | 228 | 254 |
| Heel–ankle circumference | 351 | 353 | 343 | 372 |
| Ball-of-foot circumference | 258 | 257 | 252 | 273 |

### 1d. Arm & hand

| Measure | Tight mean | Loose mean | Pop 50th | Pop 95th |
|---|---|---|---|---|
| Shoulder–elbow length | 382 | 384 | 363 | 394 |
| Acromion–radiale (upper arm bone) | 351 | 352 | 335 | 365 |
| Radiale–stylion (forearm bone) | 281 | 283 | 267 | 295 |
| Forearm–hand length | 502 | 503 | 480 | 520 |
| Forearm centre-of-grip length | 365 | 366 | 348 | 379 |
| Sleeve length spine–wrist | 928 | 931 | 895 | 963 |
| Sleeve outseam | 623 | 625 | 592 | 645 |
| Hand length | 201 | 201 | 193 | 210 |
| Palm length | 120 | 120 | 116 | 127 |
| Hand breadth (metacarpal) | 91 | 90 | 88 | 96 |
| Hand circumference | 218 | 216 | 212 | 230 |

[derived] Middle-finger length ≈ hand length − palm length = **~81 mm**. Individual finger lengths are not in ANSUR II; Greiner 1991 (US Army, male means) gives thumb 69.7, index 75.3, middle 83.8 mm **[snippet — DTIC PDF https://apps.dtic.mil/sti/tr/pdf/ADA244533.pdf blocked]**. Scale ring ≈ 0.93× and little ≈ 0.78× of middle **[uncited]**.

### 1e. Leg & foot

| Measure | Tight mean | Loose mean | Pop 50th | Pop 95th |
|---|---|---|---|---|
| Buttock–knee length (sitting) | 641 | 645 | 617 | 669 |
| Buttock–popliteal length | 524 | 528 | 502 | 548 |
| Knee height sitting | 585 | 586 | 553 | 602 |
| Popliteal height | 459 | 460 | 430 | 471 |
| Functional leg length | 1174 | 1181 | 1131 | 1224 |
| Foot length | 281 | 282 | 271 | 293 |
| Foot breadth (horizontal) | 104 | 103 | 102 | 111 |
| Ball-of-foot length (heel→1st metatarsal head) | 209 | 210 | 201 | 218 |
| Heel breadth | 71 | 73 | 72 | 82 |
| Bimalleolar breadth (ankle width) | 76 | 77 | 75 | 81 |
| Lateral malleolus height | 76 | 76 | 73 | 83 |

[derived] Hallux (big toe) region length from 1st metatarsal head to toe tip ≈ foot length − ball-of-foot length = 281 − 209 = **~72 mm**; big-toe width **~25 mm** and arch height **~20–25 mm** at the navicular are [uncited] typical values — no open table found (PMC foot-anthropometry tables were CAPTCHA-blocked). Foot 281 mm ≈ Mondopoint 280 ≈ US men's 11 / EU 45 [uncited mapping].

### 1f. Head & face

| Measure | Tight mean | Loose mean | Pop 50th | Pop 95th | Source |
|---|---|---|---|---|---|
| Head length (glabella→occiput) | 203 | 202 | 200 | 211 | ANSUR II [opened] |
| Head breadth | 154 | 154 | 154 | 163 | ANSUR II |
| Head circumference | 581 | 578 | 574 | 601 | ANSUR II (Wikipedia "Human head" gives 57 cm male average, mass 2.3–5 kg: https://en.wikipedia.org/wiki/Human_head [opened]) |
| Tragion → top of head | 132 | 132 | 131 | 141 | ANSUR II |
| Menton–sellion length (face length, nose bridge→chin) | 126 | 125 | 123 | 134 | ANSUR II |
| Bizygomatic breadth (face width) | 142 | 142 | 143 | 153 | ANSUR II |
| Bitragion–chin arc / submandibular arc | 332 / 314 | 332 / 315 | 332 / 315 | 355 / 345 | ANSUR II |
| Interpupillary breadth | 64.4 | 64.3 | 64.0 | 70.0 | ANSUR II |
| Ear length / breadth / protrusion | 65 / 37 / 24 | 65 / 37 / 23 | 64 / 36 / 23 | 72 / 41 / 28 | ANSUR II |
| Intercanthal distance | 33.3 ± 2.7 | | | | Farkas NAW male norms **[snippet]** via https://jkamprs.springeropen.com/articles/10.1186/s40902-019-0191-7/tables/2 (redirects to Springer login) |
| Eye fissure length | 31.3 ± 1.3 | | | | same [snippet] |
| Biocular (outer-canthus) width | 91.2 ± 3.0 (89.4 ± 3.6 in another table) | | | | same [snippet]; https://www.banglajol.info/index.php/JNINB/article/view/65450/50681 (503) |
| Nose width (alar) | 34.9 ± 2.1 (34.7 ± 2.6) | | | | same [snippet] |
| Mouth width | 54.5 ± 3.0 (53.3 ± 3.3) | | | | same [snippet] |
| Total head height vertex→menton | ~232 | | | | [uncited] typical male; ANSUR has no direct measure — use 126 (menton–sellion) + ~106 (sellion→vertex) |

## 2. Footwear — 8-inch tactical boot

| Item | Value (mm) | Source |
|---|---|---|
| Shaft height, "8-inch" US military boot | 203 (8 in "Standard Military Height") | Belleville Khyber TR550 page https://www.bellevilleboot.com/index.php?l=product_detail&p=130 [opened]; Belleville C312ST spec PDF https://www.bellevilleboot.com/pdf/C312ST.pdf [opened] |
| Salomon Quest 4D Forces 2 height | 160 (lower than an 8 in boot) | vetsecurite listing **[snippet]** https://vetsecurite.com/en/shoes/9222-salomon-quest-4d-gtx-forces-2-coyote-salomon.html (403) |
| Salomon Quest 4D Forces 2 weight | 600–700 g per boot; nubuck + Cordura upper; metal upper eyelets, lace locks mid-foot; Mondopoint chart 231–324 mm | https://varusteleka.com/en/product/salomon-quest-4d-gtx-forces/60094 [opened] |
| Lowa Zephyr GTX Mid TF shaft height | inside 110, ISO 150, outside 145; "closed hooks" lacing; injected construction | https://professional.lowa.com/en/zephyr-gtx-mid-tf [opened] |
| Lowa Zephyr weight | 560 g (EU 43) | cop-shop.de **[snippet]** |
| Full lug sole thickness (Vibram 360 Force full sole) | 9.6 (18 iron) | https://www.montanaleather.com/product/1321-360-force-vibram-full-sole/ [opened] |
| Sole stack, heel/toe | heel ~30–35, forefoot ~20–25, lug depth 4–6 | [uncited] typical for EVA-midsole tactical boots; measure from `ref/crop_boots_feet.png` |
| Belleville outsole | Vibram Ibex (Khyber) / Vibram Incisor (C312); EVA midsole; padded collar & tongue; soft toe or steel toe (ASTM F2413) | Belleville pages above [opened] |
| Lacing hardware, typical 8 in boot | 2 lower eyelets + 6 speed hooks (Rothco 10 in example) | **[snippet]** emergencyresponderproducts.com Rothco speedlace page |
| Lace diameter | 4 (mil-spec "550" style); 3 for thinner laces | **[snippet]** https://m-tac.us/products/m-tac-boot-laces-nylon-mil-spec (403) |
| Lace length | 8–10 eyelet pairs → 1600–1830 (63–72 in); 10–12 pairs → 1830–2130 (72–84 in) | **[snippet]** myshoesreview.com (404 on fetch) |
| Last vs foot | boot internal length ≈ foot length + 15–22 toe allowance → 281 + ~18 ≈ 299 internal; outsole adds ~10–15 at toe and heel | **[snippet]** meermin.com/pages/rois & last patent; apply to ANSUR foot 281 |
| Eyelet spacing, tongue, welt | eyelets ~25 pitch on the vamp; gusseted tongue to top hook; cemented (no welt) on Salomon/Lowa, Belleville strobel-stitch | [uncited]/Belleville PDF [opened] ("athletic strobel-stitch construction") |

## 3. Military socks

| Item | Value | Source |
|---|---|---|
| Over-the-calf tactical boot sock height | ~430 mm (17 in heel→cuff), to just below knee; 79% merino / 20% nylon / 1% Lycra | **[snippet]** Decathlon Darn Tough OTC page (403) |
| Darn Tough Tactical Full Cushion OTC | 68% merino / 28% nylon / 4% Lycra; sizes S UK 5–7 … XL UK 12+ | https://www.trekitt.co.uk/dpt/pgr/darn-tough-tactical-full-cushion-over-the-calf-gravel__8592 [opened] |
| Boot-height (mid-calf) sock T4033 | 80/19/1 merino/nylon/Lycra | **[snippet]** offbase.co (404) |
| Modelling note | ribbed cuff ~40–50 mm tall; shows above an 8 in boot only if OTC | [uncited] |

## 4. Combat trousers (Crye G3 Combat Pant)

| Item | Value | Source |
|---|---|---|
| Fabric | Mil-spec 50/50 NYCO ripstop + 4-way stretch woven accents; stretch diamond gusset; double-layer seat; 10 pockets; cargo pockets hide bottle/mag stabilisers; knee-pad height adjust inside front thigh pocket; flap over kneecap opening | https://www.cryeprecision.com/g3-combat-pant [opened] |
| Size chart | waist 28–46 in 2 in steps (fits waist ±1 in); inseam Short 737–787, Regular 787–838, Long 838–889, XLong 889–940 (29–31/31–33/33–35/35–37 in) | https://www.cryeprecision.com/size-charts/g3-combat-pant/ [opened] |
| Target size | waist 893 mm ANSUR → **34 waist**; crotch height 898 → inseam ≈ 32–33 in → **34 Regular/Long** | [derived] |
| Garment weight | 726 g | https://offbase.co/collections/apparel/products/crye-precision-g3-combat-pant [opened] |
| Waist adjustment | Velcro closure gives 1.5 in (38 mm) adjustment | same offbase page [opened] |
| NYCO ripstop weight | 6.6 oz/yd² (224 g/m²) MIL-DTL-44436 class 10; soft-finish variant 250 g/m² (7.37 oz) | **[snippet]** fibre2fashion / mh-chine listings; carrington.co.uk opened but no numbers |
| Ripstop grid | reinforcement yarn every ~5–8 mm (MIL ripstop ≈ 0.25 in grid) | [uncited] — check against a 4K NYCO texture |
| Cargo pocket (G3) | ~230 tall × 190 wide, zip/velcro flap; knee-pad pocket opening ~150 wide; ankle: elastic cuff + drawcord | [uncited] estimates — no vendor publishes these; measure `ref/crop_legs_knees.png` |
| Rise | front ≈ 260–280 (sits below navel: waist height 1127 − crotch 898 = 229 minus ~40 drop) | [derived]/[uncited] |
| Seam allowance | 10–13 mm felled seams | [uncited] |

## 5. Combat shirt (Crye G3 Combat Shirt)

| Item | Value | Source |
|---|---|---|
| Torso | DRIFIRE flame-resistant wicking knit; sleeves 50/50 NYCO ripstop; double-layer bicep pocket with Velcro; eye-pro holder & pen pocket; elbow-pad pockets for AirFlex elbow pads; zip (mandarin) collar with comfort placket | https://www.cryeprecision.com/g3-combat-shirt [opened] |
| Size chart | chest circumference & height bands, e.g. LG Long = chest 1067–1168 (42–46 in), height 1829–1930 (72–76 in) | https://www.cryeprecision.com/size-charts/g3-combat-shirt/ [opened] |
| Target size | chest 1029, stature 1846 → **MD–LG Long** | [derived] |
| Bicep pocket | ~150 tall × 130 wide loop field; elbow pad pocket ~200 × 150 | [uncited] — measure `ref/crop_arm_*.png` |
| AirFlex elbow pad | pair 0.06 lb (27 g), black only, one size | https://ctomsinc.com/products/crye-airflex-field-elbow-pads [opened] |

## 6. Plate carrier & load carriage

| Item | Value (mm unless noted) | Source |
|---|---|---|
| SAPI medium plate | 241 × 318 (9.5 × 12.5 in), 1.82 kg; ESAPI medium 2.50 kg; sizes XS 184×292 … XL 280×356; side plates 152×152 / 152×203 / 178×203 | https://en.wikipedia.org/wiki/Small_Arms_Protective_Insert [opened] |
| ESAPI curvature (training plate, same geometry) | multi-curve: longitudinal radius 18 in (457), latitudinal radius 10 in (254); small plate 8.75 × 11.75 in | https://www.officer.com/on-the-street/body-armor-protection/product/10222733/team-wendy-esapi-non-ballistic-training-plate [opened] |
| ESAPI thickness | ≤ 25.4 (1.00 in threshold) | **[snippet]** navysbir.com N232-082 PDF |
| Plate corner cut | shooter's cut: top corners clipped ~50–65 mm at ~45° | [uncited] |
| Crye JPC 2.0 | "just over one pound" (~0.5 kg); fits plates S 298×222, M 318×241, L 337×267, XL 356×286 (11.75×8.75 … 14×11.25 in); Skeletal cummerbund, pouches inside/outside; webbing loops on shoulder straps; Velcro front panel | https://bravocompanyusa.com/crye-precision-jumpable-plate-carrier-jpc-2-0/ [opened] |
| JPC size by chest | S 33–36 in, M 37–40, L 41–45, XL 46–49 → target chest 40.5 in → **M/L** | **[snippet]** rmadefense.com |
| Shoulder strap | ~75 wide (3 in) with 6–10 pad; carrier body ≈ plate + 20–25 margin | [uncited] |
| Cummerbund height | 3 PALS rows ≈ 125–150 | [uncited] |
| PALS webbing | 25 (1 in) Type III nylon webbing; rows "25 mm apart"; bar-tack/stitch spacing 38 (1.5 in), accepted 35–40; laser-cut 500–1000D laminate equivalents | https://en.wikipedia.org/wiki/Pouch_Attachment_Ladder_System [opened] |
| PALS row pitch | Wikipedia wording ("1 in webbing spaced 1 in apart") implies **50.8 pitch**; the task brief's 38 pitch is the *column* stitch spacing. Cross-check: Agilite admin pouch 5.1 in tall = 3 rows; Esstac Tall 5.25 in = 3 rows → 3 rows span ≈ 127 → consistent with 25 webbing + 25 gap. Measure against the 25 mm webbing visible in `ref/crop_torso_vest.png` before committing | [derived] |
| Pouch: BFG Ten-Speed triple M4 | 235 × 140 closed (9.25 × 5.5 in); elastic | **[snippet]** primaryarms.com (404 on fetch) |
| Pouch: Esstac KYWI single 5.56 | Tall 133 × 83 (5.25 × 3.25 in); Midlength 109 × 83; Shorty 89 × 83 | https://esstac.com/single-5-56-tall-kywi-pouch/ [opened] (Mid/Shorty [snippet]) |
| Pouch: HSGI TACO single | 76 wide (3 in) | **[snippet]** evike.com |
| Pouch: admin (Agilite Wide) | 260 × 130 (10.23 × 5.1 in), 163 g, 500D Cordura, 6 col × 3 row PALS | https://agilitegear.com/en-fr/products/wide-admin-pouch [opened] |
| Pouch: radio PRC-152 (Tactical Tailor Fight Light) | 229 tall × 76 wide × 57 deep (9 × 3 × 2.25 in), Hypalon | https://tacticaltailor.com/fight-light-prc-152-pouch/ [opened] |
| Pouch: GP / IFAK (Rescue Essentials 500D) | 190 × 152 × 89 (7.5 × 6 × 3.5 in), 340 g, 51 × 140 Velcro field | https://www.boundtree.com/first-aid-trauma-wound-care/individual-first-aid-kits-ifaks-/rescue-essentials-500d-ifak-pouch/p/3423-00417 [opened] |
| Pouch: dump (Point Blank) | deployed 178 × 102 × 89 (7 × 4 × 3.5 in); stowed 127 × 89 × 25 | https://blackboxsafety.com/products/dump-pouch-7-h-x-4-w-x-3-5-ddeployed-5-h-x-3-5-w-x-1-d-stowed [opened] |
| Pouch: dump (Savotta) | 130 × 300 × 130 deployed, 150 g, 500D; 2 PALS columns | https://savotta.fi/products/dump-pouch [opened] |
| Pouch: frag, double (Condor) | 152 × 57 × 51 (6 × 2.25 × 2 in), flap + quick-release buckle | https://copquest.com/condor-double-frag-grenade-pouch_92-2075.htm [opened] |
| Pouch: frag, single | Condor 102 × 89 × 64 (4 × 3.5 × 2.5 in); Tactical Tailor 89 × 64 × 64 | **[snippet]** condoroutdoor.com (truncated) |
| Pouch: double pistol mag (Tactical Tailor) | 140 tall × 102 wide × 38 deep (5.5 × 4 × 1.5 in), 1000D Cordura, 2 short MALICE clips | https://tacticaltailor.com/double-pistol-mag-pouch/ [opened] |
| Cobra buckle FC45 (1.75 in belt) | 58 wide × 38 long × 10 deep, 41 g, 45 webbing, 9 kN tensile / 18 kN loop | AustriAlpin datasheet PDF https://www.austrialpin.at/en/service/data-sheet/pdf/fc45cf-k-cobraframe/ [opened, pdftotext] |
| ITW Nexus side-release / ladder-lock / tri-glide | made for 15/20/25/30/40/50 webbing; **no dimensions published on the pages reached**. Typical 1 in SR buckle ≈ 70 × 35 × 11; 1 in ladder-lock ≈ 38 × 32 × 6; 1 in tri-glide ≈ 38 × 27 × 4 | https://needs-needlesports.dc02.gob2b.com/Catalogue/Accessories/Buckles-Webbing-Repair/ACE-SR-ACE-SR and …/ACE-TG-ACE-TG [opened]; dims [uncited] |
| Mil-spec hook & loop (A-A-55126) | widths 19 / 25 / 38 / 51 (3/4–2 in) at McMaster, up to 102 & 152 (4, 6 in) at MMI; hook 2.0 thick (0.079 in), loop 2.5 (0.098 in) | https://www.mcmaster.com/products/hook-and-loop/military-specification~fed-spec-a-a-55126-type-ii-class-1/ [opened]; MMI widths **[snippet]** soldiersystems.net |

## 7. Hard armour pads

| Item | Value | Source |
|---|---|---|
| Crye AirFlex Combat Knee Pad | pair 0.34 lb (154 g), one size, flexible cap; no dims published | https://www.cryeprecision.com/airflex-combat-knee-pad [opened] + spec PDF [opened] |
| Alta AltaFlex hard-cap knee pad | 229 long × 165 wide × 38 thick (9 × 6.5 × 1.5 in); 12.7 (1/2 in) neoprene foam; cap held by 6 brass grommets | dims **[snippet]** pelicansalessupply (404); foam/grommets https://tingleyrubber.com/products/altaflex-hard-cap [opened] |
| Arc'teryx LEAF knee caps | TPU shell over 10 mm EV50 foam, 225 g, elastic straps | https://uspatriottactical.com/arc-teryx-leaf-knee-caps [opened] |
| Alta AltaContour 360 elbow pad | 180 tall × 120 wide, 240 g/pair, Vibram rubber cap, 12.7 neoprene, two wide straps | https://milgear.fi/en/product/alta-tactical-altacontour-360-vibram-cap-elbow-pads/52027 [opened] |
| Shoulder / deltoid pads | Coyote Tactical 64 × 203 (2.5 × 8 in), 227 g; TYR 70 × 320, 190 g/pair, threaded on PC shoulder straps | https://offbase.co/products/coyote-tactical-solutions-shoulder-pads [opened]; https://varusteleka.com/en/products/tyr-tactical-shoulder-pads-multicam-surplus [opened] |
| Forearm guards | 220–260 long × 130–195 wide × 10–16 thick (sport guards study) | **[snippet]** jssm.org table |

## 8. Tactical gloves (Mechanix M-Pact)

| Item | Value | Source |
|---|---|---|
| Construction | TPR (thermoplastic rubber) knuckle guard; EVA accordion finger padding; synthetic-leather palm; fingertip reinforcement; elastic/Velcro wrist with ID patch | https://militarykit.com/products/mechanix-wear-m-pact-3-gloves-coyote [opened] |
| Size chart | S finger 123–130 / palm 65–75; M 130–138 / 75–85; **L 138–145 / 85–98**; XL 145–152 / 98–110 | same page [opened] |
| Target size | ANSUR hand breadth 91, middle finger ~81 → **Large** | [derived] |
| Knuckle guard | one piece ~95 wide × 35 tall × 6 thick spanning 4 MCP knuckles | [uncited] — measure `ref/crop_hands_rifle.png` |

## 9. Neck gaiter

| Item | Value | Source |
|---|---|---|
| Buff Original tube | 530 × 225 flat (53 × 22.5 cm), seamless 4-way stretch microfiber | **[snippet]** gooutdoors.co.uk / absolute-snow (pages opened returned only nav / 403) |

## 10. Belt

| Item | Value | Source |
|---|---|---|
| 1.75 in rigger belt (HSGI Cobra) | 2 layers 44.5 (1.75 in) Type 13 webbing, each 2.0–3.0 thick (0.080–0.120 in) → belt ≈ 5–6 thick; 5 rows of #138 stitching; sizes S 28–30 … XL 40–42 in; interior Velcro, D-ring | https://spotterup.com/hsgi-cobra-1-75-rigger-belt-d-ring-interior-velcro/ [opened] |
| Cobra buckle | see §6: 58 × 38 × 10 | AustriAlpin PDF [opened] |
| Battle belt (padded outer) | ≈ 75–100 tall sleeve with 2 PALS rows, 10–15 thick | [uncited] |

## 11. M67 fragmentation grenade

| Item | Value | Source |
|---|---|---|
| Body | diameter 64 (2.5 in), length 90 (3.53 in) incl. fuze, 400 g, spheroidal steel body, M213 fuze 4–5.5 s | https://en.wikipedia.org/wiki/M67_grenade [opened] |

## 12. AR-15 / M4-type carbine, 16 in barrel

| Item | Value (mm) | Source |
|---|---|---|
| M4 reference (14.5 in barrel) | OAL 838 extended / 756 collapsed; 2.92 kg empty, 3.52 kg loaded; forged 7075-T6 receivers | https://en.wikipedia.org/wiki/M4_carbine [opened] |
| 16 in-barrel carbine OAL | ≈ 876 extended / 794 collapsed (M4 + 38) | [derived] |
| Upper receiver (flat-top) | ~203 long × 76 tall × 70 wide (Anderson stripped upper 8 × 3 × 2.75 in listing) | **[snippet]** ar15.build |
| Lower receiver | ~216 long (mag-well front → rear of extension) × 98 tall (3.875 in) × 32 wide; alt listing 197 × 114 × 32 | **[snippet]** thegunzone.com (403) |
| Buffer tube (receiver extension) | mil-spec OD 29.1–29.2 (1.146–1.148 in), commercial 29.7–29.8 (1.168–1.170); carbine tube 184 (7.25 in) mil-spec vs 198 commercial; 6-position | https://wooxstore.com/blogs/woox-journal/mil-spec-vs-commercial-buffer-tube-ar15-stock-fit [opened]; lengths **[snippet]** gunsmagazine.com |
| Stock (Magpul CTR mil-spec) | 178 long × 132 tall × 43 wide; LOP 262 collapsed → 345 extended; 252 g (360 g with tube) | https://magpul.com/ctr-carbine-stock-mil-spec.html [opened] |
| Pistol grip (Magpul MOE) | 102 tall, max 30 thick, 79 g | https://magpul.com/moe-grip-ar15-m4.html [opened] |
| Handguard 13 in M-LOK (BCM MCMR-13) | top rail 330 (13 in), total 340 (13.4 in), ID 33 (1.30 in), width 38 (1.5 in), 298 g; Faxon 13 in: flat-to-flat 39, peak 42, ID 34 | https://store.xtremeairsoft.net/products/bcm-mcmr-free-float-m-lok-handguard [opened]; Faxon **[snippet]** rainierarms |
| M-LOK slot | 32 long × 7 wide, 8 between slots (→ 40 pitch), 2.38 corner radius; 20 mm metric interval basis | https://en.wikipedia.org/wiki/M-LOK [opened] |
| Picatinny MIL-STD-1913 | slot width 5.23 (0.206 in), pitch 10.01 (0.394 in), slot depth 3.00 (0.118 in); top width 21.2 (0.835 −0.005 in), base/neck width 15.67 (0.617 −0.010 in), datum separation 19.0 (0.748 ±0.002 in), datum vertical 2.74 (0.108 in), 45° ±20′ flanks (STANAG 4694) | https://en.wikipedia.org/wiki/Picatinny_rail [opened]; https://www.thomasmechanicaldesign.com/the-mitch-blog/picatinny-and-nato-rails-gdt [opened]; Weaver slot 4.57 (0.180 in) https://bulletin.accurateshooter.com/2009/02/tech-tip-picatinny-vs-weaver-rail-specifications/ [opened] |
| 30-rd magazine (Magpul PMAG GEN M3) | 190 long (7.5 in) × 66 (2.6 in front-to-back) × 22 (0.87 in thick); 146 g empty / 503 g loaded | https://www.trex-arms.com/store/MAGPUL-ARM4-PMAG/ [opened]; https://copsplus.com/rifle-magazines/magpul-mag557-blk-pmag-30-ar-m4-gen-m3-30-round-5-56x45mm-nato-223-remington-polymer-magazine [opened] |
| STANAG magazine curve | STANAG 4179 is an interface spec only, no public dims; USGI 30-rd body is straight for the top ~60 (mag-well section) then curves; curve radius ≈ 250–300 | https://en.wikipedia.org/wiki/STANAG_magazine [opened]; radius [uncited] |
| A2 flash hider | 44.5 long × 21.8 dia (1.75 × 0.86 in), 85 g, 1/2-28 thread, 5 ports (closed bottom) | https://ar15discounts.com/products/dirty-bird-industries-1-2-28-a2-birdcage-flash-hider/ [opened]; port count [uncited] |
| Charging handle | mil-spec ≈ 190 long × 29 wide at latch (Radian Raptor listed 270 × 97 × 27 — package dims) | **[snippet]** dfcarms.com; mil-spec dims [uncited] |
| Trigger guard | KAC combat guard 27 g; mil-spec guard ≈ 60 long × 32 tall opening, 6 thick | https://ar15discounts.com/products/knights-armament-ar-15-combat-trigger-guard/ [opened]; dims [uncited] |
| EOTech EXPS3 | 89 L × 61 W × 71 H (3.5 × 2.4 × 2.8 in; EOTech lists 3.8 × 2.3 × 2.9), 318 g (11.2 oz), window 30 × 22 (1.20 × 0.85 in), 70 (2.75 in) rail footprint, QD lever mount, lower-1/3 co-witness (+7 mm riser) | https://tnvc.com/shop/eotech-exps-3/ [opened] |
| Aimpoint Micro T-2 | 68 L × 41 W × 36 H, 84 g sight / 105 g with mount, 2 MOA, CR2032 | https://tnvc.com/shop/aimpoint-micro-t-2/ [opened] |
| SureFire M600DF Scout | 141 long (5.56 in), bezel 28.6 (1.125 in), 146 g with batteries, M75 thumbscrew Picatinny mount; body ≈ 25 dia | https://www.batteryjunction.com/products/surefire-m600df-tn-scout-high-output-led-weapon-light [opened]; body dia [uncited] |

## 13. SIG Sauer P226

| Item | Value (mm) | Source |
|---|---|---|
| P226 | OAL 196 (7.7 in), barrel 112 (4.4 in), height 140 (5.5 in), width 38.1 (1.5 in), 964 g with magazine; 9×19 15/17/18/20-rd mags | https://en.wikipedia.org/wiki/SIG_Sauer_P226 [opened] (sigsauer.com product page 404) |
| Sight radius | ≈ 160 | [uncited] |

## Recommendation for the modellers

1. **Body**: build/scale the base mesh (MPFB/MakeHuman) to the §1 "Tight" column (`assets/dimensions/ansur2_target_stats.md` has all 93 measures). Key anchors: stature 1846, acromial 1516, crotch 898, knee axis 523, biacromial 424, bideltoid 506, chest girth 1029, waist 893, hip 343 breadth, head 203 × 154, face width 142, IPD 64, hand 201 × 91, foot 281 × 104. Note the target is noticeably **leaner than the ANSUR median** (waist 893 vs 937, thigh 600 vs 624) but has a 95th-percentile skeleton (acromial height, leg lengths) — do not just scale the average soldier.
2. **Gear**: sizes that fit this body are G3 pant 34 Regular/Long, G3 shirt MD/LG Long, JPC medium plate (241 × 318, multi-curve R457/R254), gloves Large, belt Large (36–38 in with gear), boot EU 45/Mondo 280 with ~300 internal length.
3. **Weapon**: the 16 in carbine at ~876 mm OAL is 47% of stature — rifle proportion errors are the most visible mistakes in the two rejected attempts' class of problem; model the receiver pair at 216 × ~98 and the mag at 190 × 66 × 22 first, then hang the 340 mm handguard and 178 mm stock off them.
4. **Open gaps to measure from the reference image rather than the web**: PALS row pitch (38 vs 50.8 — resolve against the 25 mm webbing), pouch loadout dims, knee-pad cap outline, knuckle-guard outline, boot sole stack/lug depth, sock cuff visibility, face norms beyond ANSUR (nose/mouth values are snippet-only).
5. **Don't repeat**: DTIC, PMC, Springer, Mechanix, Darn Tough, Buff, Salomon, EOTech, SureFire, Aimpoint official pages all block headless fetching — use the retailer mirrors listed above or download PDFs with curl and read them with `pdftotext`.
