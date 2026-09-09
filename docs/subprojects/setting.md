# Setting and campaign

The fiction: who is fighting, why it is happening at squad scale, and what a mission is. Science
fiction — Star Trek, Star Wars, Babylon 5 in register.

Read [../map.md](../map.md) first.

## Owns

```
docs/setting.md      and anything under docs/setting/ once there is enough to split
```

## Must not touch

All code, all tests, `docs/design.html`, and the other territory docs. This territory writes
prose. If the fiction wants a rule that does not exist, that is a proposal for Core in
`../decisions.md`, not an edit.

## Depends on

Nothing, which makes this the only territory that can start at any moment without waiting for
anybody. But it is not unconstrained — see below.

---

## The job — write the mission book

Branch `setting/missions`. Take a worktree; the rule in `CLAUDE.md` has no exception for prose.

[`../setting.md`](../setting.md) answers the five questions the bible was asked. Section 6 of it
answers *what is a mission* only in outline — six shapes and what each would cost to build — and
that outline is now the most-cited thing in the setting by everybody else. `../decisions.md`
entry 026 routed it to Core and Content as a finding about objectives. This job turns the outline
into the fiction those two will need when they build one.

**Where the output goes:** `docs/setting/missions.md`. The territory owns `docs/setting/**` and
this is the first thing worth splitting out — the bible should stay a bible.

**What it has to contain**, one section per mission shape:

- **What it is called in the world**, and what a soldier calls it, which is usually different.
  Section 7 of the bible is the register to match; keep it additive, and do not propose renaming
  anything in `src/`.
- **What the briefing says.** The actual words somebody is given before they go. This is the
  useful artefact: it is what a mission file eventually has to be able to express, arrived at
  from the fiction rather than from a format.
- **How you know you have won**, in terms of quantities the rules already have. The withdrawal
  mission is the model here — *leave with the whole hostile side still at Unaware or Suspicious*
  is readable off `AwarenessTracker` today, and saying so is what made entry 026 worth writing.
- **What going wrong looks like**, which is where the alarm and the mission clock live. Word does
  not stop at the edge of the map, and a radio call is the difference between an incident and a
  manhunt.
- **What the ground has to offer** for the mission to be playable at all. The `.hexmap` format
  exists in `content/` and entry 024 records that it deliberately holds ground and nothing else —
  *deployments and objectives are not ground*, and the sandbox hard-codes them today. So the
  question of what an extraction needs an exit for, and what a reconnaissance needs worth seeing,
  is open on purpose and this is the file that should answer it in fiction first.

**Settle this before writing much: whether a mission can be failed without the squad being
destroyed.** The bible asserts that a squad achieving its objective and losing four people has
lost, and nothing anywhere measures that. It is the last open question in `../setting.md` and it
decides whether these six shapes are win conditions or whole scoring models. Argue it in the file
rather than assuming it.

**Out of scope.** A file format, a schema, or anything resembling a spec — that is Content's, and
entry 026 is careful not to hand them one. Rules for objectives are Core's. If the fiction wants
either, it says so in `../decisions.md` and stops there.

**How to know it worked:** somebody building objectives can read one section and know what to
build, and `DemoMaps.Compound` can be pointed at whichever of the six it could carry today with
no new rules at all.

## Recent work

```bash
git log --oneline -20 -- docs/setting.md docs/subprojects/setting.md
```
