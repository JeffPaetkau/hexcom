# Gloves

Build: `"$SGT_BLENDER" -b --python scripts/parts/gloves.py [-- --no-render]` (about 10 s with renders). Output:
`cache/parts/gloves.blend` (collection `Part.Gloves`: `Glove.{L,R}.Shell`, `.Knuckle`, `.Pad.{2,3,4,5}`),
`cache/parts/gloves.json`, `renders/gloves/*.png`.

## 1. What it is

**Identity:** hard-knuckle tactical gloves, Mechanix M-Pact class (take 1 D1 chose a hybrid with an Oakley SI Assault pattern). The construction is:
- stretch knit back;
- synthetic leather or goatskin palm;
- a one-piece moulded TPR knuckle guard with ribbed bosses;
- TPR pads over the PIP joints;
- a neoprene cuff closing with a hook-and-loop tab.

Size L for a 218 mm palm girth. Sources: take 1 `archive/v1/spec/11_gloves.md` §2 to §3 (M-Pact 3 guard envelope 95 x 35 x 6 from research §8; cuff about 45 to 50; hand dimensions from ANSUR via spec 05).

| Quantity | Real / source (mm) | Built (mm) |
|---|---|---|
| Glove over the hand | knit 1.2 + air 1.0 dorsal, about 0.5 palmar | 1.8 offset all round (capped between the fingers by the gap test), Solidify 1.0 |
| Knuckle guard | 95 x 35 x 6, one piece, over the MCP heads | 92 x 34, 4.5 thick + 2 mm bosses over each knuckle, centred 16 mm behind the joint centres |
| PIP pads | one per finger, over the PIP | 18 x 16 x 2.5 on fingers 2 to 5 |
| Cuff | neoprene 3.0, about 45 to 50 beyond the wrist, over the shirt cuff | 50 mm proximal of the wrist joint, 11 mm offset (shirt sleeve + 3.5 air + 3 neoprene) |
| Knuckle breadth (this body) | ANSUR hand breadth 91 | MCP-to-MCP joint centres 74 |

## 2. What the reference shows

Evidence: `ref/crop_hands_rifle.png`, `ref/zoom_glove_*`, spec 11 §2.
- Black gloves.
- On the right hand, a ribbed raised knuckle plate with four bosses (dusty), plus lit PIP pads; the index finger is extended along the receiver.
- On the left glove, the hand is overhand on the handguard, the thumb across the rail, and about 28 mm of neoprene cuff shows below the forearm guard.

## 3. Departures and why

- **Knuckle guard:** a smooth plate with four bosses. It has no ribs yet; the detail rounds add them.
- **Palm:** not separately modelled. The palm leather, heel patch and fingertip caps are detail and material rounds.
- **Cuff tab and pull:** not built.
- **Colours:** flat. Knit #1e1c1b, cuff #1b1c1e, guard #2f2c2a, pads #2a2826.

## 4. Round 1 (2026-11-14)

### Method
1. The hand skin plus the forearm to 70 mm behind the wrist is copied, cut there, and refined.
2. Each vertex is pushed out 1.8 mm on the hand, ramping to 11 mm over the cuff. The push is capped where fingers face each other.
3. The shell is de-spiked (`common.despike`), lightly smoothed, and cut 50 mm proximal of the wrist.
4. The faces proximal of the wrist get the cuff material.
5. The guard and pads are sheets laid on the glove shell. Rays are cast down the back of the hand onto it, in a hand frame: x across the knuckles, y along the fingers, z out of the back of the hand (checked against the thumb).

### Rigging
Everything takes weights from Body.Mesh (Data Transfer, nearest face interpolated) and has an Armature modifier on Morgan.Rig. The fingers bend with the curls.

### Clearance from the skin
- Rest: shell minimum 1.1 mm, 0 inside.
- Hero pose: the guard and pads stay 1.4 to 2.0 mm clear.
- The shells have 498 (left) and 476 (right) vertices inside the skin, at most 1.85 and 1.95 mm deep. Checked by bone: all are on the curled fingers, where fingertips press into the palm and fingers press into each other. This comes from round 0's finger-curl tables (85 to 95° on the ring and little fingers), not the glove's fit.

### Layering
The shirt sleeve ends are inside the cuffs: 0 and 1 of about 325 outward-facing sleeve vertices uncovered.

### Renders looked at
- `gloves_rest_dorsal_L` (back of the left hand): the guard sits across the knuckles, pads on the PIPs, the cuff is a thick band.
- `gloves_rest_front`, `_side`, `_threequarter`.
- `gloves_hero_hands_rifle_pair`: both gloves in the drawn places; the right index is extended as drawn. Without the carbine, the left hand floats where the handguard will be.
- `gloves_hero_soldier_full_pair`.

Two failures were fixed:
- A 30 mm spike at a fingertip, from even-offset Solidify; `common.solidify` now defaults to non-even.
- The guard first sat over the finger bases.

## 5. Still wrong, ranked for round 2

1. **The glove follows the bare hand too closely.** It shows the fingernails' shape and the knuckle creases, and has no fingertip ease (+2.5 at each tip), no seams and no fourchettes. A glove-specific smoothing or a sculpted glove last would fix it.
2. **Finger-to-palm contacts in the pose** (§4): they need either less curl or contact-aware fingers in round 0, and a glove that compresses there.
3. **Knuckle guard:** it needs its moulded ribs (3 per boss at 7 mm pitch), the webs between the bosses, and to follow the knuckle arc better. On the right hand in the pose it is barely readable at hero scale.
4. **Cuff:** no closure tab, pull or binding. It is a uniform ring.
5. **No leather, knit or neoprene materials**, and no dust on the up-facing bosses.
