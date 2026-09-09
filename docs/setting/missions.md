# The mission book

What twelve people are sent to do, in the words they are sent in.

**This document is downstream of the rules**, on the same terms as [the bible](../setting.md):
where the fiction and the code disagree the code is right, and where the fiction wants something
the code does not do, that is an entry in [../decisions.md](../decisions.md) addressed to
whoever owns it. The order of authority is the code, then [design.html](../design.html), then the
bible, then this.

Section 6 of the bible answered *what is a mission* in outline: six shapes, ordered by what each
would cost to build. This file turns that outline into the thing somebody building objectives
actually needs — the words a soldier is given, and what those words mean in quantities the rules
already have.

**It is not a format.** What a mission file says is Content's and what a battle does about it is
Core's. Everything here is written so that both can be argued with before either is built.

---

## 1. The question that had to be settled first

The bible asserts that a squad which achieves its objective and loses four people has lost, and
nothing anywhere measures that. It is the last open question in [../setting.md](../setting.md)
and it decides whether the six shapes below are win conditions or whole scoring models.

**The answer is that a mission can be failed without the squad being destroyed, that the failure
is a real in-battle condition, and that casualties are not it.**

Three things follow, and the third is the one that keeps this cheap.

**A battle has three endings, not two.** Today `Battle.IsDecided` is true when at most one side
still has somebody standing, which is the elimination condition entry 026 is about. What every
mission below wants instead is: **the objective was achieved**, **the objective was settled
against you**, or **it stopped being reachable and everybody came home anyway**. The third is not
a draw and it is not a loss. It is the commonest honest outcome of quiet work, and a game that
cannot express it is a game where the only way to stop is to die.

**The failure is the objective, never the butcher's bill.** Each shape below has a moment where
the thing you came for becomes unavailable — the clerk did not come to the culvert, the mast is
being watched by four people who are now awake, the whole hostile side has registered you and is
still standing and the withdrawal condition cannot be recovered. That moment is checkable, it
usually arrives long before anybody is dead, and it is what makes these missions loseable.

**Casualties are the campaign's to grade, and it already has the data.** Entry 027 records that
soldiers persist and that plate never recovers, so a squad that loses four people has lost four
people whether or not anything scored it. The roster is the measurement. Nothing tactical needs
to weigh a dead rifleman against a records core — and it should not be asked to, because the one
thing in the code that prices a soldier is `UtilityModel`, which values them at their own
vitality, and the bible already records that the fiction disagrees with that number. Putting an
unsettled figure inside the win check is the worst available place for it.

**So: the six shapes are win conditions and not scoring models**, and *a squad that achieved the
objective and lost four people* is a mission won and a campaign going badly. That is the useful
reading anyway. It is what makes the fourth soldier's life a decision the player makes rather
than a number the game deducts.

---

## 2. What a briefing is

Every briefing in this world has the same six parts, because the deniability premise and the lid
between them leave no room for a seventh. This is the shape all six shapes share, arrived at from
the fiction; what a mission file does with it is Content's business.

| | |
|---|---|
| **The instrument** | Under what authority, and what this will be filed as. Nobody is at war, so everything is an inspection, a maintenance visit, or a transfer of a registered person. |
| **What is there** | The site, and who is on it, stated with the uncertainty it actually has. *Six or seven, one with a set* is a real briefing. *Six* is a lie. |
| **The task** | What you are to do, in one sentence. If it takes two, it is two missions. |
| **The restraint** | What you are not to do. This is where the workers live, and it is not decoration: neither side can be seen to kill the people it claims to govern. |
| **The way off** | Where you come off the ground, and by when. Nobody is coming to get you. |
| **The stop** | What ends the task short. Every briefing has one and every one of them is different, which is why it is the interesting line. |

Two things worth saying about that table before the six sections use it.

**The uncertainty in the second row is the campaign.** Entry 027 makes intelligence the campaign
currency and the loadout guess what it is spent on: a field stops all of a beam and a seventh of
a slug, plate stops all of a slug and a quarter of a beam, so a squad kitted for the wrong half
of the armoury has lost before it set out. *We think four, and the last two reports disagree* is
therefore not colour. It is the price of the last mission's reconnaissance, showing up in this
mission's briefing.

**The sixth row is the mission clock.** More on what it is made of in section 9.

---

## 3. Withdrawal — *an inspection*

Go, be there, come back, and leave nothing behind you but a shift that had an uneventful night.

Called **an inspection** on paper, which is what makes it filable: the Commission inspects its
own installations and the Cadre garrisons its own depots, and both statements are true enough to
survive a report. Soldiers call it **a walk**. Nobody has ever called it a withdrawal outside a
staff college.

> Instrument 4-11 continues in force and this is an inspection of the pumping station at Ash
> Reach, filed accordingly.
>
> There is a shift on the plant and a Cadre detail of six or seven with it, one of whom carries
> a set. They are a fortnight into a rotation and they are bored, which is the whole of your
> advantage.
>
> You will enter the yard, confirm the plant is running and the transfer pumps are on Commission
> stock, and leave.
>
> You will not be seen. You will not fire. If one of the shift sees you, you have failed the
> task, and you will still not fire.
>
> Off the way you came, before first light.
>
> If you are properly registered — registered, not a dog barking — the task is over. Come home.
> There is nothing at Ash Reach worth the second half of this night.

**Won when** every soldier is off the ground and no hostile ever held more than a suspicion about
any of them. That is `AwarenessTracker.HighestAwarenessOf` against `AwarenessModel.SuspiciousAt`
and `SearchingAt`, which is to say the reading is free and has been since the awareness ladder
was built. *A dog barking* is Suspicious at 25. *Properly registered* is Searching at 50, the
rung where a sentry stops scanning and starts walking towards where he thinks you were.

**Gone wrong when** somebody reaches Searching **and lives to keep it, or has already passed it
on.** That qualification is not a softening; it is the best thing in the game and it is already
built. A unit going down goes through `Battle.Withdraw`, which calls `AwarenessTracker.Forget`,
so silencing the man who saw you genuinely takes his certainty out of the world — with no new
rule, today. And the counter-play is built too: `Relay` fires at Alerted, so if he called it in
before you reached him, his side holds 0.6 of what he had and that survives him. **The mission is
lost when the knowledge outlives the man**, which is a rule the fiction would have been proud to
invent and did not have to.

What that means for the reading is in [../decisions.md](../decisions.md) entry 030: the awareness
has to be sampled as each soldier leaves rather than polled at the end, because by the end
`Forget` has cleared it.

**A note on the shift.** The briefing says being seen by a worker fails the task, and nothing in
the rules can currently notice that: contacts are only ever formed between hostiles, and
`IsHostileTo` excludes `Side.Neutral`. That is the want the bible files in section 5 and entry 026
carries, and it is written here as an order a soldier is given rather than as a condition anything
checks.

**The ground needs** two things and neither is a wall: somewhere to come in from, and somewhere
to go out to. They are usually the same edge and it is better when they are not, because coming
off where you went on is the one route the garrison has had all night to walk past.

**This is the shape the compound can carry today**, and section 9 says how.

---

## 4. Reconnaissance — *an assessment*

Put eyes on a named place, long enough to be sure of what is in it, and get out with the answer.

Called **an assessment**, and filed against whatever proceeding both sides are assembling
arguments for. Soldiers call it **a look**, and the man sent forward is *having a look*, which is
the same word the rules use for what a soldier does at the end of every turn.

> An assessment of the Cadre holding at Kestrel Yard, ahead of the arbitration.
>
> We believe plate is coming through it in quantity. We do not know how much, the last two
> reports disagree, and one of them is nine weeks old.
>
> Get eyes on the loading floor and on whatever is under the north canopy. Properly on it —
> traced, not glimpsed from the road.
>
> There is a night shift in the sheds. They are not ours and they are not theirs and you will
> leave them entirely alone.
>
> Off by the stream, two hours after you are on the ground.
>
> If they know you were there, they will move it, and the assessment is worth nothing before
> you are home. Being shot at is survivable. Being identified is the failure.

**Won when** a soldier has held the objective in full attention with a clear line to it, and then
got off the ground. Both halves of that are existing calls: `SightSolver.Trace` between the
soldier's vantage and a vantage at the place answers the line, and
`AwarenessTracker.IsWatching(observer, place)` answers the attention, being the front 120° cone
at acuity 1.0 rather than the corner of the eye at 0.45. Entry 026 costed reconnaissance at *an
objective node, and a record of whether it was ever traced*. That is right, and it is cheaper
than it sounds: the node is content, and the record is a flag set by two queries that exist.

**Gone wrong when** the answer stops being worth carrying home. That is the interesting failure
in the six, because it is not about you at all — it is about whether the thing you came to count
will still be there when somebody acts on your count. A reconnaissance that is detected has
succeeded at seeing and failed at the mission.

**The ground needs** something worth looking at, and — this is the part the ground genuinely
supplies — somewhere to look at it *from*. A place with no standoff on it is not a
reconnaissance, it is a burglary. The vantage matters more than the objective: a loading floor
with a ridge at thirty metres and a wood at thirty-five is a mission, and the same floor in the
middle of open hard standing is not.

---

## 5. Sabotage — *maintenance*

Reach a thing, spend real time on it, and leave it looking like it broke.

Called **a maintenance intervention**, and it is the purest expression of the deniability
premise in the book: both sides file the paperwork, and the paperwork is not entirely false,
because the mast really is out of specification and the Commission really does maintain it.
Soldiers call it **servicing it**.

> The relay mast at Fen Cross is Commission inventory and has been out of specification since
> March. You are the maintenance.
>
> Four on the site, in the hut, and they take it in turns to be awake. There is no set at Fen
> Cross that we know of, which is the reason it is tonight.
>
> The mast wants a man at the base of it with the housing off for the better part of a minute.
> That is a great deal longer than it sounds.
>
> Leave the housing shut when you are done. It is to read as a fault.
>
> Off south, over the ridge, whenever you have finished.
>
> You will not get that minute if anybody is looking for you. If it turns into a fight, it
> has stopped being maintenance and there is nothing else it can be, so break it and go.

**Won when** the thing has had the points spent on it and the squad is off. Entry 026 costed this
at *an interactable at a node, and a price in action points*, and the price is the whole design.
A soldier receives 50 points a turn, a walk is 5 a hex, and the bible derives a turn at about
twelve seconds. So the better part of a minute at the base of a mast is four or five turns of a
soldier standing still in the open doing something that is not shooting, watching or moving. That
is the most expensive thing anybody can buy with the resource this game is denominated in, and it
is what makes sabotage the shape that most wants a second soldier watching the approach.

**What the fiction insists on is that the price is paid in turns and not in an action.** The
figure itself is Content's, and it is the one number in this book worth arguing about, because a
sabotage that can be done in a single turn is a door and not a mission.

**Gone wrong when** the clock beats the work. Sabotage is the shape that turns a mission clock
from a nicety into the point: unlike a walk, you cannot finish early, so once the net has you
the question is only whether the remaining rounds cover the remaining points.

**The ground needs** a thing at a place, and cover *at* that place rather than on the way to it.
Every other mission is about the approach. This one is about the four or five turns after the
approach is over, standing at the base of something, which is the only time in this game a
soldier chooses to be stationary and useless.

---

## 6. Extraction — *a recovery*

Bring a person or an object off the ground with you.

Called **a recovery** where it is property and **a transfer of a registered person at her own
request** where it is not, both under the same instrument, and the second phrasing is doing an
enormous amount of work: there are no defectors because there are no two states to defect
between. Soldiers call it **a lift**.

> Instrument 4-11, transfer of a registered person at her own request.
>
> Sennet Ory keeps the depot ledgers at Marrow. She has asked to come across and she is bringing
> eleven years of them with her. The detail on the depot is eight and two of them carry sets.
>
> She will be at the culvert under the west road at four.
>
> She is fifty-one, she has never done this, she will be slower than you and she will not go
> prone. Nobody is to raise a weapon anywhere near her.
>
> Out by the west road, on foot, all of you together.
>
> If she is not at the culvert by twenty past she is not coming, and you are to leave without
> her. If it goes loud with her on the ground between you, the task is her. It was never the
> ledgers.

**Won when** the carried thing is off the map with the squad. The verb for leaving already exists
— `Battle.Withdraw` takes a unit out of play — and what does not exist is anything that ties it
to a place, or any notion of a unit that follows another one.

**Gone wrong when** the thing cannot leave. A person who is dead cannot be extracted and neither
can a person the squad has become separated from, and that is the failure that makes this shape
different from every other: it is the only one where the mission can be lost by something that
happens to somebody who is not a soldier. Which is exactly why it wants `Side.Neutral` to do
something, and why the bible files that as a want rather than a fact.

**The ground needs** an exit that a person can be told about in advance, and this is where the
question the bible left open gets its answer: **an exit is a place on the map that a briefing can
name, and the briefing names it because the person meeting you there has to be able to find it.**
A culvert, a bridge, a gate, the cut on the ridge. *Off the west edge* is a boundary condition.
*The culvert under the west road at four* is a mission, and the difference is that the second one
can go wrong.

---

## 7. Denial — *site security*

Be the ones already there.

Called **site security** or **a standing detail**, which is the only mission in the book that is
described accurately by its own paperwork. Soldiers call it **sitting on it**.

> You are the detail at Fen Cross for six nights. This is the whole of the order.
>
> The mast is out of specification and there is a Commission maintenance instrument outstanding
> against it, which means somebody is coming, and it will not be a maintenance party.
>
> Two awake at any time. The set stays with whoever is awake.
>
> Nobody who works here is to be stopped, questioned, or kept on the site after their shift.
>
> Nobody comes off. You are relieved on the seventh morning.
>
> If you have somebody registered and you are sure, use the set. That is what it is for and this
> is the mission where using it is not a mistake.

**Won when** the clock runs out with the objective intact, which makes this the one shape that
*requires* a round limit rather than merely benefiting from one. `Battle.Round` exists and counts,
so the measurement is free; the decision about what a fixed round count does to a battle is
Core's.

**Gone wrong when** they achieve theirs, which means denial is the mirror of the other five and
cannot be specified without them. It is placed fifth for that reason and not because it is hard.

**The ground needs** exactly what the other five need, read from the other side: the vantages a
reconnaissance would use are now the vantages you have to cover, and the culvert is now the hole
in your own perimeter.

**This is the shape that makes the rest of the book honest.** Every other mission in it is
written against a garrison that is bored, that settles back down at 15 certainty a turn, and that
has not looked in your direction yet. Denial is the mission where the player *is* that garrison,
finds out what it is like to be walked around at 200° and 0.45 acuity, and stops thinking of the
sentry as a puzzle piece. It is worth building for that alone.

---

## 8. Capture — *a detention*

Take somebody off the ground alive and able to answer questions.

Called **a detention pending interview**. There are no prisoners of war, because there is no war;
there is a person detained under an instrument, with paperwork, and the paperwork is the point,
since a detention that cannot be filed is a disappearance and both sides need very badly not to
be doing those. Soldiers call it **a collection**.

> Detention order under Instrument 4-11 against Halloran Vesk, who was Meridian ordnance and is
> now whatever the Cadre is calling it at Marrow.
>
> He is on the depot most nights. He has a sidearm he has not drawn in nine years and he is
> never alone.
>
> He is to be brought out and he is to be able to answer questions. That is the whole of the
> difficulty.
>
> Nobody else on that site is to be touched who does not touch you first.
>
> Out by the west road. He walks.
>
> If he cannot walk, the order is void and you have committed the thing we have both spent
> eleven years not doing. Leave him and come home.

**Won when** he is off the ground and not down. **Gone wrong when** he is down, which is the only
failure state in the book that the squad reaches by succeeding too well.

**Nothing in the rules can do this**, and it is worth being exact about why, because the shape is
one verb away rather than one system away. A power blade does 16 and a soldier has 20 vitality,
so the bible's own arithmetic — infiltrator kit, 10 then 16 — is a man dead on the second strike.
Every weapon in the game reduces vitality and `Battle.Fire` calls `Withdraw` the moment vitality
reaches zero. There is no way to put a soldier down that is not damage, and therefore no
difference between a captured man and a killed one. Entry 026 called that subdual and put it last
in the order. That is the right place for it.

**The ground needs** what an extraction needs, plus somewhere he can be taken *from* that is not
in view of the other seven, since he has to be reached quietly, taken quietly, and then walked
out at his pace and not yours.

---

## 9. What the ground has to offer

The `.hexmap` format holds ground and nothing else, and entry 024 records that as a decision
rather than an omission: *deployments and objectives are not ground.* So the question of what an
extraction needs an exit for, and what a reconnaissance needs worth seeing, was left open on
purpose. Here is the fiction's answer, before anybody writes a format for it.

**Four things a mission needs that a map cannot hold**, in the order they hurt:

| | |
|---|---|
| **Somewhere to start** | Where the squad is when the first turn begins, and which way each of them is facing. Facing is not a detail: the difference between the front cone and the corner of the eye is 1.0 against 0.45, and a deployment that faces the wrong way has made a decision on the player's behalf. |
| **Somewhere to end** | A named exit that a briefing can say out loud. Not an edge — a place. |
| **Something to do** | The node, thing or person the middle four shapes are about. |
| **When it stops** | A round count, or a condition that starts one. |

**And two things a map can hold, which the six shapes lean on entirely.**

*Standoff*, which is a reconnaissance's whole substance and a sabotage's whole absence. And
*one way in that is not the way everybody uses*, which is the difference between an approach and
a queue.

Both maps in `content/` already have the second. The compound has a breach in a solid wall and a
rooftop reachable only by ladder. The waystation has a gate at each end of the main road and a
drain under the south wall that somebody small and patient can crawl through, which is a
sixty-second briefing in one statement of a map file.

### Which of the six the compound can carry today

**Withdrawal, and only withdrawal.** Deploy the hostile detail in and around the walls, put the
squad on the open ground west of them, and the mission is *cross the compound, look at the far
side of it, come back out without anybody getting to Searching*. The ground carries that today,
the deployment is what the sandbox already hard-codes, the reading is `HighestAwarenessOf`
against the rungs in `AwarenessModel`, and the leaving is `Battle.Withdraw`. Not one of those
four wants a new rule.

**The ending does**, and it is worth being precise rather than triumphant about it: a squad that
walks off this map ends the battle in the same state as a squad that was killed on it, and by the
time anybody could poll the awareness, `Forget` has cleared it. Two small things, both in entry
030, and they are the difference between a win condition that is readable and a mission that can
be played.

**With one caveat that should be stated rather than discovered.** The compound is 20.8 m across.
A slug rifle is heard at 18 m and a shout carries 15 m, so essentially every point on that map is
within earshot of every other, and the whole apparatus of relays, radios and word travelling is
flattened to *everybody knows at once*. The compound can carry the win condition. It cannot make
the alarm mean anything, and a mission clock on it would be theatre.

**The waystation is where these become missions**, and the numbers are worth writing down because
they were the point of building it that size. Measured off `waystation.hexmap` at 1.73 m between
hex centres:

| From the compound centre | Hexes | Metres |
|---|---|---|
| The west gate | 4 | 6.9 |
| The bridge, the one crossing of the stream | 8 | 13.8 |
| The cottages | 12 | 20.8 |
| The barn | 14 | 24.2 |
| The watchtower, four metres up | 16 | 27.7 |
| The east wood | 20 | 34.6 |

The barn and the tower are outside voice range of the compound and outside the 18 m a rifle
carries, so a detail split between them is a side that genuinely depends on its set — and the man
carrying it becomes the target the bible says he is, for the reason `AwarenessTracker.CanReach`
gives rather than for a reason anybody wrote. The bridge is four hexes outside the west gate and
its planking is the loudest ground on the map. That is an exit, a chokepoint and a mistake
waiting to be made, all authored in one line of a map file, and it is the best argument in the
project for objectives being content rather than code.

### The clock, and what is under it

The bible says word does not stop at the edge of the map and that a radio call is the difference
between an incident and a manhunt. Here is what is actually built underneath that.

`AwarenessTracker.Relay` runs whenever a contact reaches `AlertedAt`, and `CanReach` decides how
far it goes: **the whole side if the caller has a set, otherwise line of sight or 15 m of
shouting.** A relayed contact arrives at 0.6 of the caller's certainty, so 75 relays as 45, which
is below Searching at 50 — the alarm gives a bearing and not a target, exactly as the bible
claims, and the claim is arithmetic rather than assertion.

So the counter-play the fiction wants already exists in full: **kill the sets and there is no
clock**, because a garrison without a radio can only tell the people who can see it or hear it
shout. Nothing needs building for that. What does not exist is any channel that leaves the map,
and therefore nothing that starts a clock — there is no *off the net* for the alarm to reach.

**The mission clock is the one genuinely new thing the six shapes want**, and it is small: a
round count that starts when a hostile who has a set has properly registered somebody and has had
a turn in which to use it. Everything in that sentence except the count is a query that exists.

---

## 10. What this book asks for that does not exist

Collected, in the order the shapes need them, so that nobody has to reread six sections to find
out what is missing. The findings behind rows one to three are in
[../decisions.md](../decisions.md) entry 030; the rest restate entry 026 with the fiction now
attached.

| | Wanted by | What it is |
|---|---|---|
| 1 | all six | An ending that is not elimination, and one that can tell *left* from *killed*. |
| 2 | withdrawal | The awareness reading sampled as each soldier leaves, not polled at the end. |
| 3 | all six | A named exit, a deployment with facing, and a round count. None of them are ground. |
| 4 | reconnaissance | An objective node, and a flag saying it was traced. |
| 5 | sabotage | A thing at a node, and a price in action points to work on it. |
| 6 | extraction | A carried thing, and a neutral who follows. |
| 7 | denial | A round limit that ends a battle. |
| 8 | capture | Subdual: a way to put a soldier down that is not damage. |

Nothing in this table is a request. Rows one, two, seven and eight are rules and therefore Core's;
rows three to six are content and therefore Content's; and the whole point of writing the fiction
first was that both of them get to disagree with it before either builds anything.

---

## What is load-bearing here and what is free

On the same terms as section 10 of the bible, since a later session should know what it may throw
away.

| | |
|---|---|
| **Load-bearing** | That a mission is won or lost on the objective and that casualties are the campaign's to grade. Everything in section 1 hangs on it, and it is what keeps the win check out of the argument about what a soldier is worth. |
| | That failure arrives when the objective becomes unreachable, not when somebody dies. It is what makes five of the six shapes loseable at all. |
| | The six-part briefing. It is the shape a mission file has to be able to express, and it was derived from the premise rather than from a format. |
| | That an exit is a named place and not an edge, because a person who is meeting you there has to be able to find it. |
| **Free** | Every proper noun in every briefing. Ash Reach, Kestrel Yard, Fen Cross, Marrow, Sennet Ory, Halloran Vesk, Instrument 4-11. Replace any of them; keep the shape of the sentence they are in. |
| | Which site carries which shape. Content owns what gets built and the bible is a palette, not a map list. |
| | Twenty minutes at the base of the mast, six nights at Fen Cross, four o'clock at the culvert. Illustrative, and the only one of them with a number behind it is the two turns section 5 works out. |

## Recent work

```bash
git log --oneline -20 -- docs/setting/ docs/setting.md
```
