# The Hexcom bible

Who is fighting, why it happens twelve people at a time, and what a mission is.

**This document is downstream of the rules.** Ten systems are built and they assert a great deal
about the world whether anybody meant them to or not. Where the fiction and the code disagree,
the code is right and this file changes. Where the fiction needs something the code does not do,
that is an entry in [decisions.md](decisions.md) addressed to whoever owns it — never a licence
to describe a game that does not exist.

Read [design.html](design.html) before proposing anything here. The order of authority is the
code, then the design doc, then this.

Every load-bearing claim below names the mechanic it pays for. A claim that pays for nothing is
decoration, and the last section says which ones those are so that a later session knows what it
is free to throw away.

---

## 1. What the rules already assert

Read out of the source, not remembered. These are the constraints the fiction had to be built
around.

| The rules say | Therefore the world has |
|---|---|
| Beam and kinetic weapons both exist; a field stops all of a beam and a seventh of a slug, plate stops all of a slug and a quarter of a beam | two weapon families in live competition, and no soldier carrying the answer to both |
| Fields and plate are tracked on six body faces, and a spent face can be turned away for a point | powered personal equipment, worn, with a front and a back that matter |
| Fields recharge one to three a face each turn; plate never comes back | equipment that recovers between contacts and degrades across a campaign |
| A soldier has 20 vitality; the hardest single blow in the game is 16 before anything stops it | people who are difficult to kill and who mostly survive being shot at |
| Only a unit with a radio reaches its whole side; otherwise word travels 15 m by shout or by line of sight | a squad with one set between it, and a reason that is not poverty |
| Relayed word is worth 0.6 of the caller's certainty | an alarm that gives a bearing, not a target |
| Certainty decays 15 a turn against rungs at 25, 50, 75 and 100 | sentries who settle back down; a garrison, not an army in contact |
| Full attention spans 120°, the corner of the eye 200° at 0.45, behind is 0.08 | positions that can be walked round rather than merely approached |
| A slug rifle is heard 18 m, a repeater 26 m, a beam not at all; a beam paints a line back down its own path | two ways to give yourself away, and a real choice about which risk to run |
| A hex is 2.00 m across and a turn walks ten of them | a fight measured in tens of metres and tens of seconds |
| A map on which the ranges discriminate is 70 to 105 m across (entry 007) | one building, one yard, one installation — never a front |

Six things the fiction has to explain, in the order the rest of this document takes them:

1. Why both weapon families are still in service.
2. Why the fight is twelve people and not twelve hundred.
3. Why a squad has one radio.
4. Why anyone would knife a sentry rather than shoot him.
5. Why winning is not killing everybody.
6. Why these people keep coming back to do it again.

---

## 2. The premise: everything happens under the lid

A generation ago this region was administered, supplied and defended by a single power. Call it
**Meridian**. Meridian built the settlements, the orbital handling, the field-emitter industry
that puts a shield on an infantryman, and — because it had enemies once — an automated
interdiction layer to keep anything hostile from moving freely overhead.

Meridian is gone. The interdiction layer is not.

It still runs, on standing orders nobody living has the authority to revoke, and it does what it
was built to do: it destroys things that announce themselves. A powered vehicle, a radar, a
battery firing, an aircraft, a transmitter left keyed for more than a moment — all of it reads as
exactly the sort of thing the layer was left there to remove. Soldiers call it **the lid**. Both
sides have learned its tolerances the expensive way, and the surviving doctrine on both sides is
the same: stay small, stay quiet, stay under it.

**What the lid pays for.** Everything about the scale of this game.

- **No support of any kind.** No air, no artillery, no armour, no drones, no orbital eyes. What
  the infantry cannot do does not get done. That is why twelve people in a compound is the whole
  war and not a skirmish inside a larger one.
- **No sensor net, so no aggro radius.** Detection is people looking at things. Every enemy who
  knows about you learned it through a channel you can see and cut, because there is no channel
  that does not run through a person.
- **One radio a squad, carried by somebody specific, used sparingly.** Not scarcity: discipline.
  A set is a liability that occasionally has to be used anyway, and the man carrying it is worth
  killing first. That is the fiction for `UnitStats.Signaller` and it is the reason it is a
  property of a soldier rather than of a side.
- **Beam weapons matter more than their damage.** A weapon that paints a bright line back to the
  shooter is a bad habit in a world that punishes emitting. The pulse carbine's flash of 1.0 is
  the highest signature in the game and the fiction agrees with the number.

**What the lid does not do**, and this is the part to hold on to: it is not a referee and nobody
controls it. It kills whatever crosses it, including things that belong to whoever is winning. It
is weather, and the war is fought in it.

---

## 3. Why both weapons are still in service

This is the setting's central technical fact and it earns its place by explaining the one thing
about the armoury that is genuinely strange.

Energy weapons killed the bullet, once. For about a generation the emitter carbine was simply
better than anything that threw a solid object, and Meridian's armies carried nothing else.

Then personal field emitters became cheap enough to issue to everybody, and a field is very good
indeed at stopping a beam and nearly useless against a lump of metal arriving fast. Within a few
years the antique thing that fields shrug at — a rifle firing a slug — was the best answer
available, and every arsenal in the region went looking for the tooling it had scrapped.

The counter to *that* was ablative plate, which stops rounds and cooks under a sustained beam.

**So the loop closed, and it has stayed closed, because each answer is cheap and neither is
general.** Every soldier on this ground carries the right answer to half of what is shooting at
them and the wrong answer to the other half, and knows it. That is why a squad wants both
families in it, why enemy composition is worth knowing before you set out, and why nobody has
simply won the argument.

Two consequences worth stating plainly, because both are already true in the code:

**Nobody wins a frontal exchange.** A pulse carbine into a shielded chest achieves nothing at
all; a slug rifle into good plate does one point. The first exchange of a firefight between two
prepared soldiers is mostly noise. The only reliable ways to hurt somebody are to reach a face
their kit has already been worn off, to be shooting the family they are not protected against, or
to be shooting before they know you are there. **That is the whole design of the game, stated as
doctrine, and both sides teach it.**

**The field stops the first blow. It is the second one that kills.** Layers wear as they work, so
a run of hits into one face is nothing like a run of separate hits. A power blade into the back of
a shielded soldier goes 4, then 15. Into an unshielded one it goes 10, then 16.

| Kit on the face | Blade strikes | Turns spent behind them |
|---|---|---|
| Infiltrator — field 4, plate 2 | 10 + 16 | one |
| Sidearm — field 5, plate 4 | 8 + 15 | one |
| Rifleman — field 6, plate 8 | 7 + 12 + 13 | two |
| Heavy — field 8, plate 14 | 6 + 12 + 11 | two |
| Beamer — field 10, plate 3 | 4 + 15 + 14 | two |

This is the answer to question four. A knife is still a knife in an age of personal shields
because the shield buys the wearer exactly one mistake, and standing behind somebody for two
seconds is how you take it away from them. It also says exactly what a quiet kill costs: twenty
to sixty action points, two or three separate contacts, and the target staying unaware through
all of them. That is a plan, not a reflex, and it is the right price for the most valuable thing
in the game.

---

## 4. The two sides

Meridian withdrew. Its apparatus on the ground did not, and it split along the seam every
withdrawing power leaves behind: between the people who hold the writs and the people who hold
the ground.

**The Commission** is the civil administration, continuing under an emergency instrument that
nobody has the standing to revoke and nobody quite believes in. It has the archives, the
registries, the licences and the accounts. It is solvent, legally meticulous, and slightly
embarrassed. Its soldiers are contracted rather than raised: better equipped than they are
trained, and kitted by purchase, which tilts them toward the field-emitter side of the armoury —
carbines and heavy shields, bought as a system from the people who still make them.

**The Cadre** is the garrison that was left in place and never received an order to stand down.
It has the depots, the armouries, the installations and eleven years of local knowledge. It is
short of everything except stock and competence, which tilts it toward plate and slugthrowers —
the things a depot has and a workshop can keep running.

Both claim to be Meridian's continuation. Both are partly right, and both know it.

**Neither can call it a war**, and this is the single most productive constraint in the setting.
A war would mean there are two governments here, which is precisely the thing each side exists to
deny. So there are no declarations, no fronts, no offensives and no prisoners of war. There are
incidents. A pumping station changes hands overnight and both sides file a report describing a
maintenance dispute. Twelve people go somewhere at four in the morning and the ones who come back
do not talk about it.

What that buys:

- **Squad scale, twice over.** The lid makes anything larger a target; deniability makes anything
  larger an admission.
- **Identical kit and shared doctrine.** It is the same armoury, eleven years apart. A soldier on
  the far side of a compound wall was trained by the same manuals, and possibly by the same
  sergeant. Nothing in the code distinguishes the two sides mechanically, and nothing should.
- **Objectives that are about possession, not casualties.** You cannot annihilate a garrison you
  officially believe to be your own service acting under a misapprehension. You can take the
  records core out of their building, which settles the argument in a way killing them does not.

The tilt in kit is a tendency and never a rule. Both sides field both families, both sides
salvage, and any mission may present any composition — which is what keeps the loadout decision
in section 8 honest.

---

## 5. The people who live here

`Side.Neutral` is in the code, `IsHostileTo` already excludes it, and the win check already
filters it out. Nothing uses it.

The setting says it should. These installations are not fortifications; they are places where
people work. A pumping station has a shift on it. A freight yard has drivers in it. The compound
in the demo map has somebody's tools in the corner.

They matter for three reasons and one of them is mechanical:

- Neither side can be seen to kill them, because both sides are claiming to govern them. That is
  the deniability premise applied at the level of a single trigger pull.
- They are the reason a site is worth taking at all. Ground with nobody on it is not worth twelve
  people.
- **They are a detection channel with legs.** A worker who sees you is not a threat and is not a
  target, and telling somebody is exactly what they will do.

Nothing in the rules makes a neutral behave like a person yet. Written up as an entry rather than
described here as though it worked.

---

## 6. What a mission is

The rules currently end a battle when one side has nobody left in play. That is the worst-fitting
objective in the game and the numbers say so: fields recharge every turn, so a squad that breaks
contact for three turns is whole again, and a frontal exchange between prepared soldiers achieves
close to nothing. Elimination is not a hard objective here. It is an *unreachable* one, most of
the time, and a game that demands it is a game where both sides shoot at each other until
somebody's plate runs out.

Six mission shapes fit the machinery. They are ordered by what they cost to build. **The outline
is here and the missions themselves are in [setting/missions.md](setting/missions.md)** — what
each one is called, the words a soldier is given, what winning is in quantities the rules already
have, and what the ground has to offer.

| Mission | What it is | What it needs that does not exist |
|---|---|---|
| **Withdrawal** | be there, do the thing, leave with nobody above a rung | **nothing** — the awareness ladder already measures it exactly |
| **Reconnaissance** | put eyes on a named place and get out | an objective node, and a record of whether it was ever traced |
| **Sabotage** | reach a thing and spend points on it | an interactable at a node, and a price in action points |
| **Extraction** | bring a person or an object off the map | a carried thing, an exit region, and a neutral who follows |
| **Denial** | stop them doing any of the above to you | the mirror of the others, plus a clock |
| **Capture** | take somebody alive | subdual — a way to put a soldier down that is not damage |

**The first row is the important one.** A mission of the form *get in, get out, and be at
Unaware or Suspicious across the whole hostile side when you leave* needs no new rules at all —
it is readable off `AwarenessTracker` today. It is also the purest expression of what this game
is about, and it is available now rather than after an objective system exists. Written up as an
entry so that Core and Content can decide whether it is worth having early.

**What winning means.** Possession and information, not bodies. A mission is won by having the
thing, having seen the thing, having broken the thing, or having got the person out — and the
soldiers coming home is a separate and equally real success condition, because they are the
campaign's actual resource. A squad that achieves the objective and loses four people has lost —
though not the mission, which it won. That distinction is
[setting/missions.md](setting/missions.md) section 1: the mission is won or lost on the objective,
and the four people are a campaign judgement the roster already measures.

**What the alarm costs.** Word does not stop at the edge of the map. A radio call from a garrison
that has properly registered you is the difference between an incident and a manhunt, and it is
the natural home for a mission clock: once the net has it, you have a fixed number of rounds
before this stops being a fight you can win. The channel is already built; nothing above it is.

---

## 7. The tech register

Names for what exists. **This is additive** — nothing here asks for an identifier to be renamed,
and the English words already in the code are the words the world uses.

**Weapons.** What soldiers call them is in italics.

| In code | In the world |
|---|---|
| `PulseCarbine` — beam, 8, 14/42 m, silent, flash 1.0 | The standard emitter weapon, Meridian pattern and still in production. Excellent against unshielded flesh, useless against a fresh field, and it draws a line straight back to you every time you use it. *A lamp.* |
| `SlugRifle` — kinetic, 11, 20/55 m, heard at 18 m | The weapon that came back from the dead. Longest reach in the game, hits hardest of the rifles, and tells the neighbourhood. *A rifle*, without qualification — it is the one that gets to keep the plain word. |
| `Repeater` — kinetic, 6 × 3, 11/30 m, heard at 26 m | Short, automatic, and the loudest thing anybody carries. Three rounds into one face is the reliable way through good plate, which is exactly the burst walking through the hole the first round made. |
| `Sidearm` — beam, 5, 8/20 m, silent | What you have when your job was not shooting. Signallers, drivers, everybody's second weapon. |
| `PowerBlade` — beam, 16, contact, silent | A field edge: the same emitter industry as the carbine, dumped into a contact-range point instead of thrown down a line. The only way to take somebody out of the fight without telling anybody, and it takes two or three goes. *The edge.* |

**Protection.** A personal emitter and a plate carrier, both worn, both Meridian-derived.

- The shield is **a field**. It has six faces because the emitter is a harness rather than a
  bubble, and it recovers between contacts. *His field's down* is the most useful sentence in this
  world.
- The armour is **plate**. Ablative, unpowered, does not come back, and the reason a soldier
  slowly runs out of good sides to present.

**The net.** The radio, and the word for the side-wide channel. *On the net* means the whole side
knows. Using it is a decision with a cost, not a default state.

**Roles.** The words in `UnitStats` and `Loadout` are the world's words and want no translation:
scout, trooper, signaller; rifleman, beamer, heavy, infiltrator. *Beamer* is already soldier
slang for somebody carrying an emitter weapon and it should stay that way.

**Places.** The theatre is a world called **Calder**: a settled place with an industrial spine
through it and ordinary country either side. Pumping stations, relay masts, freight sheds, a
water plant, one refinery — and the roads between them, with the farms, crossings, waystations
and cottages that were there first. Low buildings, hard standing, perimeter walls, and sandbags
where somebody improved a position eleven years ago and nobody took them away.

Content owns what actually gets built and this is a palette rather than a map list, but two maps
exist and the setting should agree with them: `compound.hexmap` is the walled industrial case and
`waystation.hexmap` is the other one — a settlement at a crossroads, 85 m across, with a barn, a
bridge, two cottages and a watchtower. **That second one is the more useful reading of the
world.** People live at these places as well as working at them, which is section 5's argument
about neutrals arriving from the map rather than from the fiction.

**The ladder.** `Unaware`, `Suspicious`, `Searching`, `Alerted`, `Engaged` are plain English that
a player can read and should not be dressed up.

---

## 8. The campaign

**A thin frame, not a second game.** That is a recommendation with an argument behind it rather
than a preference, and the argument is that the interesting campaign decision already exists in
the tactical layer and needs almost nothing built around it to become real.

What the rules already give a campaign for free:

- **Soldiers persist and can be lost.** Vitality 20 against a hardest-blow-in-the-game of 16
  means people usually survive; a name that comes back next mission is credible.
- **Plate never recovers and fields always do**, so the thing that carries across missions is
  equipment wear, not wounds. Resupply is a real decision and healing is not.
- **`CostProfile` and `UnitStats` already make one soldier different from another**, in points
  spent moving and shooting. A veteran is a set of numbers that already exist.

**The decision that makes it a campaign is the loadout guess.** Section 3 says every soldier
carries the right answer to half of what is shooting at them. So the question before every
mission is *what are we going to meet*, and the answer is bought with reconnaissance,
informants, and what the last mission saw. **Intelligence is the campaign currency and loadout is
what it is spent on** — which means the strategy layer is the same game one level up: you are
acquiring information under uncertainty and committing to a guess before you know whether it was
right.

That is a frame worth building and a small one. A roster, a map of sites, a clock, a market for
what you carry, and a record of what each side has been seen fielding. It does not want a second
combat model, an economy, or a research tree.

**Ground changes hands as sites, not as a front**, because there is no front — the lid forbids
one and the deniability premise forbids admitting one. A campaign map is a list of installations
and who is currently working them.

**The clock is political.** Both sides are running out of the ability to pretend. Somewhere
beyond the edge of this is an arbitration, an audit, or a returning patron, and the campaign is
the argument each side is assembling for it. That is where a campaign ends: not with one side
destroyed, but with one side holding enough ground and enough evidence that the question stops
being open.

---

## 9. Tone

Three registers were named at the start of this project and they are not the same thing. The
honest answer is that the design points hard at one of them, borrows the silhouette from another,
and should take almost nothing from the third.

**Babylon 5 is the weather, and this is the argument the design makes for itself.** Institutions
failing slowly. People doing their jobs competently inside them. Consequences that accumulate and
do not resolve. Information that is scarce, partial, late and worth more than firepower. Every
mechanic in this game is about not knowing something — a coarse alarm rung, a stale marker where
somebody thinks you are, a sentry who has not looked yet — and a stealth-first design whose whole
first act is about not being found is a design about anxiety and incomplete information. That is
this register and not either of the others.

**Star Trek supplies the proceduralism and none of the humanism.** The right half is real and
worth having: these are professionals doing a difficult job carefully, with kit they understand,
by a doctrine they were taught. The turn is a checklist. The wrong half is that Trek's problems
are solved by understanding and this game has no verb for that. Take the register of competence,
not the register of resolution.

**Star Wars supplies the silhouette and nothing else.** Soldiers with energy weapons, shields and
powered blades read as Star Wars at a glance, and that is a legitimate thing to inherit because
it makes the armoury instantly legible. Take none of the rest. There is no protagonist here,
violence is not clean, and twelve interchangeable professionals is the opposite of a mythic
structure. A game where the decisive act is knifing a bored man who has not seen you is not
mythic and should not pretend to be.

**The tone in one line:** competent people doing quiet, deniable work for institutions that have
outlived their mandate, in a place that used to be somebody's and is now nobody's.

**What that means for anyone writing or drawing.** Nothing is new; everything is eleven years
old and maintained. Kit is worn, mismatched and cared for. Nobody is a monster and nobody is
having an adventure. The enemy is bored, which is why the approach works. Understatement is the
house style — the design doc's own voice is the right voice for this world, and this file is
written in it deliberately.

---

## 10. What is load-bearing and what is free

The most useful thing in this document. **Load-bearing** means a mechanic is explained by it, and
changing it leaves the mechanic unmotivated. **Free** means it can be replaced tomorrow by anyone
with a better idea and nothing breaks.

| | |
|---|---|
| **Load-bearing** | The field-and-plate loop, and that neither family has won. It is the direct explanation of two weapon families, `Mitigation`, and why a squad wants both. |
| | The lid, or something that does its job. It is the only thing paying for squad scale, for no support, for no sensor net, and for one radio. |
| | That neither side can call it a war. It pays for objectives that are not elimination, for identical kit, and for the whole political register. |
| | That the enemy is a garrison rather than an army in contact. Detection decay of 15 a turn describes people who settle down, and the approach game only works against them. |
| | That firing is the loudest thing a soldier does. It is in the scorer, in `AnnounceFire`, and in the weapon table. |
| **Free** | Every proper noun. Meridian, the Commission, the Cadre, Calder, and the lid as a word. Rename any of them without consequence; keep what each one does. |
| | Eleven years since the withdrawal, and any other date. |
| | Which side tilts toward which weapon family. It is a tendency, it is not in the code, and it must never become a rule. |
| | Calder's geography, the site list, and everything about what an installation looks like. That is Content's. |
| | That a turn is about twelve seconds — ten strides at 1.73 m, at a walking pace. Derived and useful for anyone writing, and nothing depends on it. |

---

## Open questions

- **Whether the withdrawal was a collapse or a decision.** It changes what people feel about
  Meridian and nothing else. Left open deliberately: it is the largest piece of free space in
  the setting and the first thing worth filling in when somebody has a reason to.
- **Whether there is a third party with soldiers on the ground.** The neutral side in the code is
  civilians here. A third armed claimant would fit the register, and would want rules nobody has
  asked for.
- **Night.** The design doc lists light level as a detection factor and `AwarenessModel` has no
  such term, so the setting does not currently get to use darkness as a tool. Not raised as a
  finding, because the model works without it and inventing a need for it would be the fiction
  bending the rules. Noted so that nobody writes a night raid and assumes it is modelled.
- **What a soldier is worth.** The scorer values a soldier removed at their own vitality, so a
  signaller is worth no more than the rifleman beside them — which the design doc lists as open
  and which the fiction disagrees with strongly. The setting's answer is that the man with the
  net is the most valuable target on the field; the code's answer is that he is average. Core's
  question, and it is already in `core.md`.
- ~~**Whether missions want a defeat condition other than the squad being destroyed.**~~
  **Answered** in [setting/missions.md](setting/missions.md) section 1, and in
  [decisions.md](decisions.md) entry 030. They do, the failure is the objective becoming
  unreachable rather than the casualty count, and the sentence above about four people is a
  campaign judgement that the roster already measures. Left here rather than deleted so that
  anybody who read the question finds the answer.

## Recent work

```bash
git log --oneline -20 -- docs/setting.md docs/subprojects/setting.md
```
