# Setting and campaign

The fiction: who is fighting, why it is happening at squad scale, and what a mission is. Science
fiction — Star Trek, Star Wars, Babylon 5 in register.

Read [../map.md](../map.md) first.

## Owns

```
docs/setting.md      the bible
docs/setting/**      the parts that outgrew it — missions.md so far
```

## Must not touch

All code, all tests, `docs/design.html`, and the other territory docs. This territory writes
prose. If the fiction wants a rule that does not exist, that is a proposal for Core in
`../decisions.md`, not an edit.

## Depends on

Nothing, which makes this the only territory that can start at any moment without waiting for
anybody. But it is not unconstrained — see below.

---

## The job — write the roster

Branch `setting/roster`. Take a worktree; the rule in `CLAUDE.md` has no exception for prose.

The bible and [`../setting/missions.md`](../setting/missions.md) between them say who is fighting
and what they are sent to do. Neither says who *they* are, and three other territories are about
to need that: `Battle.Deploy` takes a name, a mission file has to list a squad, and the interface
puts those names in front of a player. Today the sandbox deploys two people called Vance and
Orsini against four called Sentry, Watchman and so on — **one side has names and the other has
job titles**, which is precisely the asymmetry section 4 of the bible denies. Same armoury,
eleven years apart, and possibly the same sergeant.

**Where the output goes:** `docs/setting/roster.md`.

**What it has to contain.**

- **Twelve people a side**, named, with the numbers they already have. `UnitStats` gives
  `Scout`, `Trooper` and `Signaller`; `CostProfile` gives `Scout` and `Gunner`; `Loadout` gives
  rifleman, beamer, heavy and infiltrator. **Invent no new statistic and propose no new one.** A
  soldier here is an existing set of numbers plus three sentences, and the discipline of writing
  them that way is most of the value — if a person cannot be expressed in what exists, that is a
  finding for Core in `../decisions.md` and not a licence.
- **What a name is for.** Vance and Orsini already exist in `game/`. Say whether the roster
  adopts them or replaces them, and be aware that adopting is the cheaper answer and probably
  the right one.
- **The signaller, specifically.** The bible says the man with the set is the most valuable
  target on the field and `UtilityModel` says he is average — an open question in both
  `../setting.md` and `core.md`. The roster is where the fiction has to put its money down: who
  carries it, why that person, and what the squad does when he goes down.
- **Both sides, in the same file and to the same depth.** A Cadre detail with names and a
  rotation is what makes the approach game feel like something being done to people rather than
  to obstacles, and section 9 of the bible — *the enemy is bored, which is why the approach
  works* — is unwriteable without it.
- **What carries between missions**, in the terms entry 027 already set: plate never recovers,
  fields always do, so what a name accumulates is worn kit and not wounds. One paragraph, not a
  campaign system.

**Out of scope.** Stats, rules, loadout balance, and anything that would need `src/` to change.
Also any claim about how many missions somebody has survived, which is campaign state and belongs
to a layer nobody has built.

**How to know it worked:** the sandbox's six deployments can be given names and two lines each
out of this file with nothing invented, and a Cadre sentry reads as somebody a fortnight into a
rotation rather than as a spawn point.

**Probably next after this**, and noted so it is not lost: the sites of Calder as a list, which
is what entry 027's campaign map wants under it. Not briefed yet, because Content owns what gets
built and there is no reason to write a site list before somebody needs one.

## Recent work

```bash
git log --oneline -20 -- docs/setting.md docs/setting/ docs/subprojects/setting.md
```
