# The roster

Twenty-four people, twelve a side, written as the numbers they already are.

**This document is downstream of the rules**, on the same terms as [the bible](../setting.md)
and [the mission book](missions.md): where the fiction and the code disagree the code is right,
and where the fiction wants something the code does not do, that is an entry in
[../decisions.md](../decisions.md) addressed to whoever owns it. The order of authority is the
code, then [design.html](../design.html), then the bible, then the mission book, then this.

**Nothing here invents a statistic and nothing here proposes one.** A soldier in this file is a
`UnitStats`, a `CostProfile`, a `Loadout` and three sentences, and every one of those values
exists in `src/Hexcom.Core` today. That constraint is not modesty. It is the whole method: a
person who cannot be written down in what exists is a finding for Core, not a licence to
describe a soldier the game cannot field.

---

## 1. What a name is for

Three territories are about to need these people. `Battle.Deploy` takes a name as its first
argument. A mission file has to say who goes. And the interface puts those strings in front of a
player, which is where the current arrangement becomes a problem worth fixing.

The sandbox today fields **Vance**, **Orsini** and **Bekker** against **Sentry**, **Spotter**,
**Watchman** and **Hollis**. Four of those seven are people and three are posts, and the split
runs along the side line — which is exactly the asymmetry section 4 of the bible spends a page
denying. Same armoury, eleven years apart, possibly the same sergeant. A side whose soldiers are
job titles is a side you are allowed to shoot without thinking, and this is a game about a
garrison being bored rather than about obstacles being cleared.

**So the roster adopts the names and keeps the posts.** Both halves matter.

**Adopting is right and it is also cheap.** Vance, Orsini, Bekker and Hollis are in `game/`, in
`content/`'s tests and in a doc comment that measures the opening frame off them. Renaming any of
them would invalidate prose in three territories to gain nothing, and a name has no properties to
get wrong. They are in the roster below, with the numbers they already carry, and this file
changed none of them.

**Sentry, Spotter and Watchman are not names to adopt or replace, because they were never
names.** They are the three posts on a crossroads: the man on the road outside the west gate, the
man on the roof with the set, the man up the tower. The roster's job is to say who is standing
each one tonight — and the words themselves stay, because a briefing needs them. *There is a
sentry outside the west gate* is how you describe a place you have not been to. *That is Cobb, he
has been there since two* is how you describe it once you have watched it for an hour, and the
difference between those two sentences is the whole approach game.

What that asks of anybody else is one line: when `game/` is next open for another reason, the
three post strings can take the names in section 6. Nothing depends on it and nothing breaks
until it happens.

---

## 2. How a soldier is written down

Four things vary and there are no others.

**The archetype**, from `UnitStats`:

| | AP | Initiative | Perception | Encumbrance | Radio |
|---|---|---|---|---|---|
| `Default` | 50 | 10 | 10 | 0 | no |
| `Scout` | 55 | 14 | 13 | 0 | no |
| `Trooper` | 45 | 8 | 9 | 3 | no |
| `Signaller` | 50 | 10 | 12 | 1 | **yes** |

**The price list they pay against**, from `CostProfile`, attached through the archetype's `Costs`
property:

| | Movement | Firing | Posture |
|---|---|---|---|
| `Default` | 1.0 | 1.0 | 1.0 |
| `Scout` | 0.8 | 1.4 | 1.0 |
| `Gunner` | 1.5 | 0.8 | 1.0 |

Neither `UnitStats.Scout` nor `UnitStats.Trooper` currently attaches one — both run on
`CostProfile.Default` — so `UnitStats.Scout with { Costs = CostProfile.Scout }` is a composition
of two existing records and not a new number. It is how this roster makes two scouts different
from each other.

**Whether they can place a round**, which is `CanCallShots`, off on every archetype and
documented as *meant to stay a thing that is earned*. One soldier a side has it here, and section
7 says why that is the right count.

**The kit**, from `Loadout`:

| | Weapon | Field / plate a face | Recharge | Carries |
|---|---|---|---|---|
| `Rifleman` | slug rifle, 11, heard at 18 m | 6 / 8 | 2 | two frag |
| `Beamer` | pulse carbine, 8, silent, flash 1.0 | 10 / 3 | 2 | one plasma |
| `Heavy` | repeater, 6 × 3, heard at 26 m | 8 / 14 | 1 | one frag |
| `Infiltrator` | power blade, 16, contact, silent | 4 / 2 | 3 | two claymores |
| `Sidearm` | beam sidearm, 5, silent | 5 / 4 | 2 | nothing |

That is the whole vocabulary: four archetypes, three price lists, one earned permission, five
kits. Everything below is a selection from it.

**One thing to know before reading the two details.** `Radio` is a property of `UnitStats`, not
of the `Signaller` archetype — `UnitStats.Trooper with { Radio = true }` compiles and would give
you a well-plated soldier carrying the set. This roster never does it, and the reason is in the
next section.

---

## 3. The set

The bible says the man carrying the radio is the most valuable target on the field. `UtilityModel`
values a soldier removed at their own starting vitality, so it says he is worth exactly what the
rifleman beside him is worth. That disagreement is recorded as open in the bible, in `core.md`
and in the `RemovalBonus` remarks, and the roster does not get to settle it — it is a number and
numbers are Core's. What the roster owes is the fiction's side of the argument, stated in a way
that can be checked.

**Who carries it: the one whose job is already to be still and looking.** `UnitStats.Signaller`
is Perception 12 against Default's 10, Encumbrance 1, and not one point of action or initiative
above an ordinary soldier. Those numbers describe an observer carrying an awkward extra thing,
and they describe nobody else. So the set goes to an observer, and — this is the part with money
on it — **it goes with `Loadout.Sidearm` or `Loadout.Beamer` and never with `Heavy`**. A beam
sidearm does 5 at 8 m. The set is deliberately in the hands of the person least able to defend
it, because a detail that has to choose between calling and fighting will fight, and then nobody
calls.

**Why not the commander.** The obvious alternative is that keying the set is a judgement, so it
should belong to whoever makes judgements. That is true about the *decision* and wrong about the
*hardware*, and separating them is the best thing in this section. The order to call goes from
the commander to the man with the set the way everything else in this world travels: line of
sight, or fifteen metres of shouting, which is `AwarenessTracker.CanReach` with no radio.

**So a detail is tethered.** The commander and the set have to stay within about fifteen metres
of each other or the side cannot decide to use the one thing that reaches all of it. That tether
is the shape of every position in the game, and it is why splitting a detail across the
waystation costs something real: the mission book measures the barn at 24 m from the compound
centre and the watchtower at 28, both outside a shout — so a detail spread over that ground
depends on the set absolutely, and the man carrying it becomes the target the bible claims he is
for the reason `CanReach` gives rather than for a reason anybody asserted.

**What the squad does when he goes down**, in the order it happens:

- **Before anything reaches Alerted**, killing the set removes the channel outright. `Relay` runs
  at `AwarenessModel.AlertedAt`, so a set that was never keyed leaves nothing behind, and
  `Battle.Withdraw` calls `AwarenessTracker.Forget`, so what he personally knew goes with him.
- **After it**, killing him is worth much less. His side already holds 0.6 of what he had, and
  0.6 of 75 is 45, which is under Searching at 50 — a bearing and not a target, but it does not
  decay out of the world just because he did.
- **Either way, the detail collapses inward.** With no set, word travels line of sight or fifteen
  metres, so the doctrine when the roof goes quiet is to close up until everyone can hear
  everyone. That is eighty-five metres of crossroads collapsing to whatever fits inside a
  fifteen-metre shout, and it is the single largest thing a quiet kill buys.

**Two sets a side, not one.** The extraction briefing in the mission book puts eight on a depot
with two sets between them, which is what a garrison does when it has learned this. The second
set is redundancy and it is also a decision: the second signaller is a second badly-armed
soldier, and a detail of six that spends two of its places on sets has four people left to hold a
crossroads with.

---

## 4. The Commission detail

Twelve on the strength. Six go out; which six is the mission's question and section 7 is about
how it is asked.

The Commission contracts rather than raises, and buys kit as a system from the people who still
make emitters, so it is a shade heavier on fields than on plate. That is a tendency across twelve
and never a rule about any six — the bible lists it as free for exactly that reason, and every
one of the five kits is on this list.

**Auber** — `UnitStats.Default`, `Loadout.Rifleman`.
Holds the detail, which here means deciding when the set gets used and almost nothing else, since
nothing in the rules makes one soldier command another. Was a licensing inspector before the
withdrawal and has never entirely stopped sounding like one, which is useful on a site with a
shift on it and unbearable everywhere else. Carries the rifle rather than a carbine because the
one thing he refuses to give up is being able to answer at fifty metres.

**Vance** — `UnitStats.Scout with { Costs = CostProfile.Scout }`, `Loadout.Infiltrator`.
The blade, and the only weapon in the game that takes somebody out of the fight without telling
anybody. Four field and two plate a face means one mistake ends her, and the price list she pays
against — four fifths over ground, seven fifths on the trigger — says the same thing twice: she
is the fastest thing on the detail and the last person you want in an exchange. She also carries
the two claymores, which are 20 damage and the loudest object anybody brings, and the joke on the
detail is that she owns both ends of the noise table.

**Orsini** — `UnitStats.Trooper with { Costs = CostProfile.Gunner }`, `Loadout.Heavy`.
Fourteen plate a face, a repeater, and half again the price of every step, which is a soldier who
picks a position and stays in it. Three rounds into one face is the reliable way through good
plate and he is the reason the detail can force a door at all. Initiative 8 less 3 encumbrance
means he acts late in almost every round, so what he mostly does is be somewhere before the round
starts.

**Bekker** — `UnitStats.Default`, `Loadout.Rifleman`.
Ordinary in every number on the sheet, which on this detail is a description of the job and not a
complaint. Carries a rifle that reaches 55 m against a sight range of 45, which is the standing
argument for giving him the ground that has to be watched rather than crossed. Was a
freight dispatcher and reads a yard faster than anyone here reads a map.

**Ferrand** — `UnitStats.Signaller`, `Loadout.Sidearm`.
The set. Five damage at eight metres is not a defence and everyone including Ferrand understands
that the arrangement is that somebody else does the defending. Talks less on the net than any
signaller either side has, which is a compliment where he comes from.

**Naismith** — `UnitStats.Signaller`, `Loadout.Beamer`.
The second set, and better placed to survive holding it: ten field a face is the best shield on
the list, and against a bored garrison carrying slugthrowers it stops a seventh of what arrives,
which is worth having and is not worth relying on. Goes out on anything that will split up. The
standing order is that Ferrand and Naismith are never on the same side of the same wall.

**Tolliver** — `UnitStats.Scout`, `Loadout.Beamer`.
Perception 13 and initiative 14 on list-price movement: quick to act rather than quick over
ground, which is the difference between him and Vance and the reason both are on the sheet.
Carbine and ten field a face makes him the one who goes and looks at things that might look back.
The flash of 1.0 every time he fires is the argument for not sending him to look at things he
will want to shoot.

**Cray** — `UnitStats.Default with { CanCallShots = true }`, `Loadout.Rifleman`.
The one who can name the face. Section 3 of the bible is that nobody wins a frontal exchange and
that the only reliable ways to hurt somebody are a face their kit has already been worn off, the
wrong family, or shooting first — and Cray is the detail's answer to the first of those. Pays for
it in accuracy for taking the time, which is why it is one soldier and not four.

**Idris** — `UnitStats.Default`, `Loadout.Beamer`.
Eight damage into unshielded flesh and nothing at all into a fresh field, so her whole usefulness
is arriving after somebody else has worn a face down. Silent, which means she is the one who can
fire twice from the same place without the neighbourhood forming an opinion about where she is.
Keeps the carbine cleaner than the manual asks and has views about people who do not.

**Mowat** — `UnitStats.Trooper`, `Loadout.Heavy`.
The same plate as Orsini and the list price for moving in it, so he is the heavy who can still be
somewhere else by the end of the turn. Eight field a face at a recharge of one is eight turns to
bring a spent side back, where Bekker's kit does it in three — so a worn face on Mowat stays worn
for the rest of the fight and he turns square to the threat rather than presenting a shoulder.
Counts his rounds out loud and nobody has asked him to stop.

**Lindqvist** — `UnitStats.Default`, `Loadout.Beamer`.
Second carbine, and the one who carries the plasma charge into anything with plate behind a door.
Eighteen damage in a three metre radius against a quarter mitigation is the detail's answer to a
position it cannot flank. Was on the emitter line at the works before the withdrawal and will not
discuss it.

**Pell** — `UnitStats.Default`, `Loadout.Rifleman`.
The newest on the sheet and given the plainest kit for it, because a slug rifle asks nothing of
the person holding it beyond hitting what they aimed at. Six field and eight plate a face is the
most balanced protection anybody carries and it is the right thing to be wearing when you do not
yet know what you are going to meet. Follows Bekker around and is not subtle about it.

---

## 5. The Cadre detail at the crossroads

Twelve again, and the same depth, because the alternative is a side made of spawn points.

The Cadre garrisons rather than deploys. These twelve are the strength for this stretch of road
and they rotate through the sites on it, a fortnight at a stretch, for as long as anybody
remembers ordering them to. Four of them hold the waystation tonight and the Commission's
estimate says four with all the uncertainty that deserves.

**The rotation is why the approach game works**, and the number underneath it is not a design
compromise. Certainty decays 15 a turn against a Searching bar of 50, so a sentry who half-saw
something at 35 is back to nothing in three turns. That is what a fortnight of nothing does to
people, and it is written into `AwarenessModel` whether anybody meant it as a portrait or not.

The Cadre has depots and workshops rather than purchase orders, so it tilts toward plate and
slugthrowers. **The four on the waystation tonight do not**, three of them being on bought
carbines, and that is worth stating rather than tidying away: the tilt is a tendency across
twelve, salvage is how a garrison stays equipped, and the bible is explicit that which side
favours which family must never become a rule.

Added up across all twelve, which is the only level at which the tilt is visible at all:

| | Field, all faces | Plate, all faces | Slugthrowers | Emitters |
|---|---|---|---|---|
| Commission | 89 | 78 | 6 | 6 |
| Cadre | 85 | 83 | 7 | 5 |

Four points of field and five of plate. That is the entire difference between the two sides, and
it is smaller than the difference between any two soldiers on either list.

**Rask** — `UnitStats.Default`, `Loadout.Rifleman`.
Holds the detail and has held it since before anybody thought to confirm that he should. Decides
when the set is used, which he has done four times in eleven years and regretted twice. Signs the
maintenance returns for a pumping station he has not personally inspected in two years, and both
sides file those returns, and neither believes them.

**Teague** — `UnitStats.Signaller`, `Loadout.Beamer`. **The post on the house roof.**
The set, three metres up behind a railing, with the whole crossroads under him and a carbine he
has fired at a person once. Perception 12 and a flat line to both gates makes him the reason the
two at the east end are ever told anything, and `CanReach` gives a radio the whole side — so
whatever Teague works out, everybody knows, including a tower that could not have noticed it
itself. He is the most valuable target on this map and he is on a roof reachable by one ladder,
which is either an excellent arrangement or the only mistake that matters.

**Cobb** — `UnitStats.Default`, `Loadout.Beamer`. **The post outside the west gate.**
Stands on the road facing the way anybody sensible would come, twenty-five metres out, where one
look at an approaching soldier is worth 35 to 37 certainty against a Searching bar of 50. Which
is to say he is the first decision of the battle and he does not know it. Bored, cold, and four
nights from the end of a rotation he has spent thinking about a boat.

**Marek** — `UnitStats.Default`, `Loadout.Rifleman`. **The post in the watchtower.**
Four metres up with the longest weapon in the game and 54 to 56 m of open ground between him and
the west road, which is past `AwarenessModel.SightRangeMetres` of 45 — so he can shoot what he
cannot notice, and until somebody tells him or somebody walks six metres closer he is furniture.
Knows it, and has said so in writing. The tower was built to watch the road before the road
mattered and nobody has moved it.

**Hollis** — `UnitStats.Default`, `Loadout.Beamer`. **In the barn on the east road.**
Head-high walls, one door on the west, and no line to the west road at all. The barn is 24 m from
the compound and a shout carries 15, so his entire connection to the fight runs through Teague's
set — if the roof goes quiet, so does he, and he thinks about that more than the others do. Grew
up eleven kilometres from here and is the only one on the detail actually from Calder.

**Ganz** — `UnitStats.Signaller`, `Loadout.Sidearm`.
The second set, kept off the roof and out of the obvious place on purpose. Five damage at eight
metres and the standing instruction to run rather than answer, which he has agreed to and nobody
has tested. Does the ration returns, which is how he knows to the day how long the rotation has
left.

**Duvall** — `UnitStats.Trooper with { Costs = CostProfile.Gunner }`, `Loadout.Heavy`.
Fourteen plate a face and half again the cost of every step: the Cadre's answer to a door, and
the reason nobody walks the main road in daylight. Firing at four fifths list price means his
reactions land early on a mover's timeline and catch them further back along the route, which is
a real consequence of being planted rather than quick. Sleeps in the barn because the compound is
noisy.

**Ilves** — `UnitStats.Scout with { Costs = CostProfile.Scout }`, `Loadout.Infiltrator`.
The Cadre has a blade too, and this is the sentence that makes the two sides the same armoury
rather than a claim about it. Four field and two plate a face on a garrison soldier is a strange
thing to be wearing while standing still for a fortnight, and she does not stand still — the
detail's one honest patrol, out past the bridge and back at hours nobody can predict, which is
the closest thing this garrison has to not being bored.

**Brill** — `UnitStats.Default with { CanCallShots = true }`, `Loadout.Rifleman`.
The one on this side who can name the face, and the mirror of Cray down to the accuracy he pays
for it. Both sides teach the same doctrine because both sides were taught it by the same manuals,
and one soldier in twelve who can place a round is what that doctrine costs to keep.

**Ostrowe** — `UnitStats.Trooper`, `Loadout.Heavy`.
Second repeater, list price for moving, recharge 1. The two of them together can hold the gate
against anything the approach can bring, which is precisely why nothing sensible comes through
the gate. Repairs things that are not his and has never once been thanked for it.

**Nye** — `UnitStats.Default`, `Loadout.Rifleman`.
Eighteen metres of noise every time he fires, on a map where the barn is 24 from the compound and
the wood is 35, so the first round Nye sends decides how much of the map is awake. Understands
this better than anybody on the detail and is therefore the last of them to shoot. Plays cards
badly and constantly.

**Sivet** — `UnitStats.Scout`, `Loadout.Rifleman`.
Initiative 14 and perception 13 with a slug rifle: the fastest reactor on the side, holding the
weapon with the longest reach, which is an odd combination that exists because the depot had
rifles and the rotation needed somebody quick. Takes the second waking shift with Cobb most
nights. Is the one who will notice, if anybody does.

---

## 6. The sandbox, named

The check on all of the above: every deployment the sandbox makes, with the name this file gives
it and the numbers it is already carrying.

| Deployed as | Numbers on it today | This roster | Numbers here |
|---|---|---|---|
| Vance | `Scout`, `Infiltrator` | Vance | plus `Costs = CostProfile.Scout` |
| Orsini | `Trooper`, `Heavy` | Orsini | plus `Costs = CostProfile.Gunner` |
| Bekker | `Default`, `Rifleman` | Bekker | unchanged |
| Sentry | `Default`, `Beamer` | **Cobb** | unchanged |
| Spotter | `Signaller`, `Beamer` | **Teague** | unchanged |
| Watchman | `Default`, `Rifleman` | **Marek** | unchanged |
| Hollis | `Default`, `Beamer` | Hollis | unchanged |

The compound scenario fields the same seven posts less two, so the same four names cover it.

**Two things about that table, and both are deliberate.**

**Nothing in the fourth column is asked for.** The two cost profiles are what this roster would
attach if it owned the file, and it does not; every scenario, test and doc comment in three
territories reads correctly with the column ignored, because the archetypes already run on
`CostProfile.Default` and that is what they are running on now. If the profiles are ever added,
Vance covers ground at four fifths and pays seven fifths on the trigger, and Orsini pays half
again per step and four fifths per shot. Those are the two soldiers the profiles were written
for, and nobody has ever used them.

**Three of the seven strings are posts and the roster does not need them changed to be useful.**
A briefing can say *the sentry outside the west gate* and a readout can say *Cobb*, and the two
sentences are about the same man. What the second one buys is that the picture stops having a
side made of furniture in it.

---

## 7. Fielding six

A mission wants six and the roster is twelve, and choosing between them is the tactical half of
the campaign decision entry 027 describes. The arithmetic is short enough to write down.

**One set is compulsory and two is a real cost.** Without one, the side cannot tell anybody
anything beyond line of sight and fifteen metres — which is the condition every mission in the
book tries to impose on the *other* side. A detail of six with two sets has four people left to
do the work.

**One earned permission a side, and no more.** `CanCallShots` is the answer to the bible's
central doctrine — a face already worn off — and if everybody has it the doctrine stops being a
plan and becomes a default. One in twelve means a mission has to decide whether to bring the
answer to worn plate or something else, which is the loadout guess in miniature.

**The blade is a mission, not a soldier.** Four field and two plate a face is the thinnest kit in
the game, and the arithmetic in section 3 of the bible costs a quiet kill at two or three
contacts, twenty to sixty action points, and the target staying unaware through all of it.
Bringing the infiltrator is committing to that plan before the first turn.

**Everything else is the guess.** A field stops all of a beam and a seventh of a slug; plate
stops all of a slug and a quarter of a beam. Six people kitted against the wrong half of the
armoury have lost before they set out, and what they were kitted against was decided by whatever
the last look at the site brought home.

---

## 8. What carries between missions

**Nothing carries between missions today**, and it is worth saying that first, because there is
no layer holding anything: a `Unit` takes its vitality from `UnitStats` and its `Protection` from
its `Loadout` at construction, and every battle constructs everybody afresh. So what follows is
an argument about what a campaign should carry when there is one — entry 027's argument — and not
a description of something running.

**The argument is that wear carries and wounds do not**, and it is read off how the two layers
behave inside a battle. Plate ablates and never comes back; fields recharge every turn. A
rifleman who spent a night presenting his left flank to a repeater ended it with that face thin,
and the honest way to carry that forward is that it is still thin next time — until somebody
issues him plate, which is stock a quartermaster could have spent on somebody else. Vitality does
the opposite and should: a soldier is either on the sheet or off it, and there is nothing in
between for a healing system to model. **A name accumulates worn kit, and nothing else.**

**This file makes no claim about how many missions anybody has survived**, and it never will,
because that is campaign state and there is no layer holding it. Everything above is who somebody
was before the withdrawal and what they are carrying tonight. Both are true on the first mission
and on the fortieth.

---

## 9. What is load-bearing here and what is free

On the same terms as section 10 of the bible, so that a later session knows what it may throw
away.

| | |
|---|---|
| **Load-bearing** | That a soldier is an existing set of numbers plus three sentences, and that a person who cannot be written that way is a finding rather than a licence. It is the only thing keeping a roster from becoming a request for statistics. |
| | That the set goes to the worst-armed observer and the decision to use it belongs to somebody else, which puts a fifteen-metre tether on every position either side takes. |
| | That both sides are the same armoury and both get the same depth. Section 9 of the bible — *the enemy is bored, which is why the approach works* — is unwriteable without twelve Cadre names and a rotation. |
| | That the posts are posts. Sentry, Spotter and Watchman describe places, and a game where one side's soldiers are places is the asymmetry section 4 denies. |
| **Free** | Every name in it. Auber, Ferrand, Rask, Teague, all of them — replace any, keep the numbers beside it. The four already in the code are free too and adopting them was a cost argument, not a claim. |
| | Every biographical sentence. What Auber inspected, where Duvall sleeps, what Cobb is thinking about. None of it pays for a mechanic and all of it can go. |
| | Which twelve is the Commission and which is the Cadre. The denial mission in the book hands the player the garrison, and when it does, section 5 is the roster and section 4 is the threat. |
| | The tilt in kit on either list. It is a tendency, the four on the waystation already break it, and the bible is explicit that it must never become a rule. |

## Recent work

```bash
git log --oneline -20 -- docs/setting/ docs/setting.md
```
