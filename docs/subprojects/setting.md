# Setting and campaign

The fiction: who is fighting, why it is happening at squad scale, and what a mission is. Science
fiction — Star Trek, Star Wars, Babylon 5 in register.

Read [../map.md](../map.md) first.

## Owns

```
docs/setting.md      the bible
docs/setting/**      the parts that outgrew it — the mission book and the roster
```

## Must not touch

All code, all tests, `docs/design.html`, and the other territory docs. This territory writes
prose. If the fiction wants a rule that does not exist, that is a proposal for Core in
`../decisions.md`, not an edit.

## Depends on

Nothing, which makes this the only territory that can start at any moment without waiting for
anybody. But it is not unconstrained — see below.

---

## The job — the sites of Calder

Branch `setting/sites`. Take a worktree; the rule in `CLAUDE.md` has no exception for prose.

Entry 027 says a campaign map is a list of installations and who is working them, and section 7
of the bible answers only half of that: it gives a palette — pumping stations, relay masts,
freight sheds, a water plant, one refinery, and the roads between them — and no list. The
previous brief left this unwritten on the grounds that nobody needed a site list yet. Somebody
does now: mission files are being written against maps, and the question *what should this place
be able to carry* has to be answerable before a map is drawn rather than after.

**Where the output goes:** `docs/setting/sites.md`.

**What it has to contain.**

- **A dozen or so named places**, each with what it is, who works there, and what the ground
  offers. Ordinary country as well as industry — the waystation is the more useful reading of
  this world precisely because people live at it, and a list of nothing but installations loses
  that.
- **Which of the six mission shapes each one can carry, and why.** This is the whole value and
  it is the discipline the roster used one rung out: a site is not a description, it is an
  answer to *what could happen here*. A place with no standoff cannot carry a reconnaissance. A
  place with nothing worth spending four turns on cannot carry a sabotage. Section 9 of
  [`../setting/missions.md`](../setting/missions.md) says what each shape needs from the ground
  and it is the checklist to work against.
- **A size, in metres, with the reason.** Entry 007 fixes the useful band at 70 to 105 m across,
  because that is where a rifle at 55, a sight range of 45, a rifle heard at 18 and a shout at 15
  stop being the same number. A site that wants to be smaller than that has to say what it gives
  up, the way `waystation.hexmap`'s header says what the compound gives up.
- **The two that exist, described rather than respecified.** `compound.hexmap` and
  `waystation.hexmap` are built and Content owns them. The list adopts what they are, names them
  as the ones already standing, and does not tell Content to change a hex.

**Out of scope.** Hex layouts, tile counts, wall profiles, anything that reads as a map spec —
Content owns what gets built and this is a palette. Also who currently holds which site, which is
campaign state and belongs to a layer nobody has built.

**How to know it worked:** somebody about to author a map can pick a site off the list and know,
before drawing a hex, which mission shapes it is for and roughly how big it has to be for the
ranges to discriminate on it.

**Probably next after this**, and noted so it is not lost: the people who live at these places.
Bible section 5 argues `Side.Neutral` should be somebody rather than nobody, and the roster's
method would carry straight over. It is not briefed, and the reason is a real one — contacts only
form between hostiles and `IsHostileTo` excludes neutrals, so a civilian written up today is a
person the rules cannot make behave. The want is already filed with Core in entry 026. Wait for
it.

## Recent work

```bash
git log --oneline -20 -- docs/setting.md docs/setting/ docs/subprojects/setting.md
```
