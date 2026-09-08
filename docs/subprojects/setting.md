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

## The job — write the bible, downstream of the mechanics

Branch `setting/bible`. No worktree strictly needed if nothing else is running, but take one
anyway; the rule in `CLAUDE.md` does not have an exception for prose.

**The discipline that makes this hard.** Ten systems are already built, and they imply a great
deal about the world whether anybody meant them to or not. The fiction is downstream of them, and
its first job is to be *consistent with* what the rules already assert rather than to invent
freely. Read `../design.html` before writing a word. Some of what is already committed:

- **Beam and kinetic weapons both exist**, and each defeats what the other cannot — shields soak
  beams and shrug at solid objects, ablative plate stops rounds and cooks under a beam. So neither
  has superseded the other, which is a strange and specific thing to be true of an armed force,
  and the setting should have a reason for it.
- **Protection is per body face**, six of them, and a soldier can turn a fresh shield to a threat
  for a point. That is powered equipment worn by individuals.
- **Not everybody has a radio.** Word travels by radio, by shouting, or by watching a comrade
  react, and only a radio reaches the whole side. Killing the radio operator is a tactic. A
  squad with one radio between it says something about how well equipped these people are.
- **A powered blade is silent** where a slug rifle is heard through walls and a beam paints a
  line back to the shooter. Melee is a stealth tool, not a last resort.
- **The fight is decided by who saw whom first.** If the fiction makes these people into a
  line-of-battle army, it is fighting the game.

**What the bible has to answer**, roughly in order of how much else depends on it:

1. **Who are the two sides, and why is this happening at squad scale?** Twelve people in a
   compound, not a war front. What kind of conflict is fought this way?
2. **What is a mission, and what does winning one mean?** The rules currently end when one side
   is down. Extraction, sabotage, capture and reconnaissance are all better fits for a
   stealth-first game, and each implies rules that do not exist yet.
3. **The tech register.** Enough to name things. The kit already has mechanical identities —
   `WeaponProfile`, `FireMode`, shields, ablative plate — and they need names that carry the
   world.
4. **The campaign shape.** What connects one mission to the next: soldiers who persist and can
   be lost, ground that changes hands, a clock. This is where the strategy-layer territory
   begins, and the answer decides whether that is a second game or a thin frame.
5. **Tone.** Three registers are named above and they are not the same. Star Trek is procedural
   and humane, Star Wars is mythic, Babylon 5 is political and worn-down. The stealth-first,
   information-scarce design points hard at the third; that is worth arguing rather than
   assuming.

**Where the output goes:** `docs/setting.md`, created by this work. Anything that turns out to
need a rule goes to Core through `../decisions.md`. Anything that turns out to need a map goes
to Content the same way.

**What would make this fail:** writing a setting that the eight built systems then have to be
bent to fit. The order is fiction-follows-mechanics here, unusually — the mechanics were built
first and they are good, so the fiction earns its place by explaining them.

## Recent work

```bash
git log --oneline -20 -- docs/setting.md docs/subprojects/setting.md
```
