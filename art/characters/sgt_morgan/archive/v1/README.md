# Take 1 (archived 2026-11-14, reference only)

Take 1 built Sgt. Alex Morgan part by part, from eighteen specs, starting with the foot. It ran
from 2026-10-06 to 2026-10-27 (git tag `sgt_morgan-v1`, commit 9edc6b6). Jeff stopped it on
2026-11-14 for a breadth-first take 2 (see `../../PLAN.md`). Nothing here is binding any more;
read it for facts, numbers and lessons, not as instructions.

Worth reading before redoing a thing:

- `notes/analysis_*.md`: the reference image analysed (proportions and pose landmarks, gear
  inventory, weapon, face and grooming, lighting and camera). The consolidated analysis is the
  best single summary.
- `notes/research_dimensions.md`: ANSUR II and real-product dimensions.
- `spec/NN_*.md` §2-§3 of each: the reference observations and real-world dimensions per part.
  These are still good evidence. The construction plans (§4 onward) belong to take 1's method.
- `spec/08_rig_pose.md`: the rig choice (MPFB `default`, 163 bones), the bone map to Godot's
  humanoid profile and the hero-pose solve.
- `spec/17_scene_camera_lighting.md`: the matched hero camera and lights (`scripts/eval/` still
  implements it).
- `notes/research_foot_hires.md` and `notes/critic/`: the foot's realism loop. The lesson:
  a real scan beat seventeen days of modelling everywhere except between the toes, and the
  blind critics' scores only rose once the scan's forms were transferred.
- `notes/session_log.md`: everything that happened, newest first.

Code moved here: the part scripts (`scripts/parts/`, `p01/`), the research scripts, the old
`build_all.py`, the spec-writing workflows, `assets/interfaces.json`. The shared tooling stayed in
`scripts/` (setup, `lib/`, `eval/`, `tools/`, `server/`) because take 2 uses it.
