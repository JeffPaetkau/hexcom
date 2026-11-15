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
