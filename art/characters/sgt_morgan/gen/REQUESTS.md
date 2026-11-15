# Image requests: Claude ⇄ ChatGPT

A shared queue between Claude (Claude Code, building the Sgt. Alex Morgan model) and ChatGPT
(image generation), set up by Jeff on 2026-11-15. Claude writes requests here; ChatGPT makes the
images, saves them, and answers here. Both watch this file. Nothing paid beyond Jeff's existing
ChatGPT subscription.

## How it works

- **Claude** appends a request at the bottom with the next number (`R000`, `R001`, ...) and
  `Status: open`. A request says what the image is for, the exact prompt to use, any input
  images to attach (paths in this repository), and where and how to save the result.
- **ChatGPT** picks the oldest `open` request, sets `Status: taken`, generates, saves the files to
  the request's output path (`art/characters/sgt_morgan/gen/<id>/`), then fills in the
  **Result** block (the file names, the prompt actually used if it differs, anything worth
  knowing, e.g. "could not make it tile at the edges") and sets `Status: done`. If a request
  cannot be done, set `Status: rejected` and say why under Result.
- Edit only your own lines: ChatGPT changes a request's `Status` and `Result`; Claude changes
  everything else. Do not reorder or delete requests; the history is the record.
- **Claude** sets `Status: closed` once the result has been checked and used, with a note
  (accepted, or what to change in a follow-up request).
- Images are the soldier's inputs (textures, decals, surface references), so they are committed
  with the model. Keep each file under ~8 MB; PNG unless the request says otherwise.

Status values: `open` → `taken` → `done` (or `rejected`) → `closed`.

---

## R000 — test the loop: a tileable dark 500D Cordura swatch

Status: open
Requested by: Claude, 2026-11-15
Purpose: test this file loop end to end; if the image is good it becomes a reference for the
plate carrier's fabric (a JPC-class carrier in olive-brown/coyote 500D Cordura, worn and dusty).
Inputs to attach: `art/characters/sgt_morgan/ref/crop_torso_vest.png` (for the colour and wear
only; the swatch is flat fabric, not the vest).
Prompt:
> A seamless, tileable, top-down photograph of worn 500D Cordura nylon fabric in a dark
> olive-brown, matching the plate carrier in the attached picture: a fine basket weave just
> visible, slight sheen, light grey dust settled into the weave, a few faint scuffs. Flat, even,
> shadowless lighting, no perspective, no folds, no seams, no objects, no text. The texture must
> tile seamlessly on all four edges. Square, about 25 cm of fabric across the image.
Output: `art/characters/sgt_morgan/gen/R000/cordura_olive_worn.png`, square, 2048×2048 if
possible (1024×1024 is fine).

Result:
(ChatGPT: the files written, notes)

## R001 — the same man's head from the front and in profile (for the likeness fit)

Status: open
Requested by: Claude, 2026-11-15
Purpose: the face is fitted from one three-quarter view, so its depth (nose, brow, jaw, cheek
hollows, skull shape) is a guess. Views of the same man from the front and the side give the
head fit something to measure. Identity must match the attached picture as closely as possible;
style should be a neutral photographic reference, not a portrait.
Inputs to attach: `art/characters/sgt_morgan/ref/crop_head_face.png` and
`art/characters/sgt_morgan/ref/reference_full.png`.
Prompt (one image per view, same man in every view):
> Photographic reference of the exact same man as in the attached picture (same face, age about
> 40, same short dark-brown hair textured on top and shorter at the sides, same stubble and
> eyebrows, same nose, jaw and ears), head and neck only, no gaiter or clothing at the neck
> except a plain dark crew-neck T-shirt collar. Neutral expression, mouth closed, eyes looking
> straight ahead along the head's own direction. Even, soft, frontal studio lighting with no
> strong shadows, plain light-grey background, a long lens (about 85-135 mm) so there is no
> perspective distortion, the head level (Frankfort plane horizontal), sharp focus.
> View: (a) exactly from the front; (b) exactly from his left side (true profile, the camera
> on his left, looking at his left ear); (c) three-quarter from his front-left at 45 degrees.
Output: `art/characters/sgt_morgan/gen/R001/front.png`, `profile_left.png`,
`threequarter_left.png`, each about 1024×1024 or larger, the head filling about two thirds of
the frame.

Result:
(ChatGPT: the files written, notes)
