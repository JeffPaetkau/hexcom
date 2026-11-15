# Session log (take 2)

Newest first. One entry per working session: what was done, what is next, anything a fresh
session must know. Take 1's log is `archive/v1/notes/session_log.md`.

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
