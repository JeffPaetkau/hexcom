# Core — the rules

Everything the game is, as plain .NET. Hex geometry, cover, movement, sight, detection,
initiative, damage, reactions, and — next — the AI.

Read [../map.md](../map.md) first, then this. `../design.html` is the source of truth for *why*
any of it is the way it is; this file is how to work on it without breaking something.

## Owns

```
src/Hexcom.Core/**      except Maps/DemoMaps.cs, which belongs to content
tests/**
docs/design.html        and it is the only territory that republishes the artifact
```

## Must not touch

`game/**` — if a rule change needs the view updated, say so in `../decisions.md` and let View do
it. The temptation is strongest when a signature changes and the sandbox stops compiling; resist
it anyway, or note in your commit exactly what you changed there and why it could not wait.

## Depends on

Nothing. Core is the trunk. Everything else depends on it, which is why the contracts in
[../map.md](../map.md) are mostly about not moving the ground under other territories:
no engine references, one query surface for the view and the AI alike, information asymmetric on
purpose, balance numbers in their seven homes, and one horizontal unit is one metre.

---

## The job — going to look (build order 04, the part that is left)

Branch `core/beliefs`. Read the rest of this file before starting; the turn loop below and the
gotchas after it are the things that will bite.

**What exists.** `Tactician` scores one action in vitality; `Commander` generates the actions and
takes a turn with them; `ReactionWindow` ranks by the same scorer. Two sides driven by
`Commander.TakeTurn` fight a skirmish to a decision, replayably, with no window open. That is
build order 04 working.

**The one thing it cannot do, and it is a big one: nobody ever goes and looks.**
`Tactician.Seen` returns only contacts with `EyesOn`, deliberately — a marker left two rounds ago
is a belief about somewhere the threat has probably left, and letting an AI act on the real
position of a unit it cannot see is precisely the cheating the whole scheme exists to prevent.
The consequences are visible in three places and they are all the same hole:

- A unit that knows about nobody stands still for the entire battle. There is nothing for it to
  want, so every option scores nothing and holding wins.
- A unit **cannot move to gain a line of sight**, only to improve one it already has. Flanking a
  man in cover works; stepping round a building to find him does not.
- Being heard costs the shooter nothing when the listener has no line, because what giving
  yourself away is worth is measured by what the person you gave it to could do *from where they
  stand* — and from behind a wall that is nothing. `SomebodyWhoHearsTheShotAndCannotReachYouCostsYouNothingYet`
  pins this rather than approving of it.

**So the job is beliefs.** A `Threat` can already carry a pose that is not where anybody is
standing — that is what it was built for. What is missing is generating threats from
`Contact.LastKnownPosition` rather than from `EyesOn`, discounted for staleness, and letting
`AppraisePosture` do what it already does: a move toward a believed position raises `Noticing`,
because you would be closer and facing the right way. Approach behaviour should fall out of the
scorer that exists rather than needing a second one — if it does not, say so in `../decisions.md`
before building a second one.

**Settle this before writing much.** What a stale belief is worth. A contact three rounds old is
somewhere the enemy *was*; `AwarenessReadout.IsStale` already draws a line at two rounds and
nothing uses it for scoring. Whatever you pick, it wants a `<remarks>` block arguing for it,
because it is the dial that decides whether the AI hunts sensibly or chases ghosts round the map.

**The hard constraint — contract 2 in [../map.md](../map.md).** The AI reads the same public
queries the interface shows. If the AI wants information the interface cannot show, that is a
finding about the interface, to be written up in `../decisions.md` — not a licence to reach into
internals for convenience. It has held through two increments and it is worth saying that it
*paid*: `Gunnery.Expect`, `AwarenessTracker.WouldNotice`, `AwarenessTracker.WouldAnnounce`,
`ReactionModel.Banked` and `Battle.PlanThreat` were all added because the AI needed them, and
every one is a figure a player should have been able to see and could not.

**Two entries the interface audit raised against Core, both open, and the first is not optional.**

- **Entry 011 — `Tactician.Aimed` reads the enemy's contact file on your own soldier as a raw
  certainty.** It breaks the promise in `Tactician`'s own class comment that it reads only what
  its soldier knows, and it is a live cheat rather than a display problem: an AI that knows
  exactly how spotted it is breaks cover at precisely the right moment and never a moment early.
  **Deal with this as part of beliefs**, because it is the same bug — acting on a fact the
  soldier has no way of holding. Fixing beliefs around it and leaving `Aimed` reading the truth
  would be building the honest half on top of the dishonest one.
- **Entry 012 — three queries the AI will want that do not exist**, so the interface cannot show
  them either. What a move would announce and who would hear it is the one that touches this
  job: going to look is worth less if the going gives you away.

**Out of scope.** `game/**`. Entry 009 offers View a way to hand a side to the AI in the sandbox;
the API is there and wiring it up is theirs. Entry 004 is a Core API gap the interface needs and
the AI does not.

**The test that it worked:** two sides that start out of contact find each other and fight,
without either being told where the other is.

After this: grenades and mines (build order 05).

---

## How a turn runs

Worth knowing before touching anything, because most of the surprises are in the order.

```
Battle.Start()      roll initiative, book everyone, hand the first turn out
  └ Advance()       refill AP · recharge shields · clear Reserve and Overwatch
                    (NOT Ambush) · rebook for next round
  the active unit acts
      Move · Fire · Face · ChangeStance · SetOverwatch · Arm · SpringAmbush
  Battle.EndTurn()  Awareness.Observe  ← the only moment a unit looks around
                    Bank               ← leftover AP becomes Reserve, AP zeroed
                    Advance
```

**A reaction window is the only thing that acts out of turn**, and there are exactly two ways one
opens:

- `Battle.Move` opens one on the committed route. Overwatch, surprise, and a trap somebody walked
  into all answer into it.
- `Battle.SpringAmbush` opens one deliberately, on a `CommittedMove` of zero length.

Either way: offers are built in the constructor, `Run()` = `PlaceRecommended()` + `Resolve()`,
and `Resolve` walks the subject along the timeline firing at each landing tick. An interface or
an AI plugs in by placing its own choices between those two calls instead of calling `Run`.

`ReactionWindow.Best` hands the whole list to `Tactician.Best`, which scores each option in
vitality. Nothing about the ordering is written down as a ladder any more, which means a change to
`UtilityModel` can silently change which reaction a unit takes — that is the point, and it is also
the thing to suspect when a reaction test starts failing for no reason you can see.

---

## Gotchas

- **Geometry needs epsilons at boundaries.** Two bugs so far came from exact-equality cases: a
  silhouette exactly as tall as the wall hiding it produced `0.9999999999999999`, and a parapet
  3.5 m overhead was vaultable because the wall profile decided the traversal before the height
  was checked. Suspect float boundaries first when a geometric test fails oddly.
- **A real behaviour change should break tests that assumed the old behaviour.** Adding facing
  broke nine awareness tests whose sentries faced the default direction. The fix was pointing the
  sentries at the approach, not weakening the model. Don't soften a model to keep a stale test
  green.
- **Two pockets, never mixed.** `Unit.ActionPoints` is the turn allowance; `Unit.Reserve` is what
  banked for reacting. `PlanShot` and `Resolve` take an `ApSource` saying which is being spent.
  Zeroing the allowance at `EndTurn` is deliberate: points are spent or banked, never left lying
  on a unit whose turn is over.
- **A reaction moves the mover.** `ReactionWindow.Resolve` walks the unit along its committed
  route and fires from each landing tick, so the mover is genuinely standing there. That is why
  sight, cover and which face a round hits need no special case inside a window — but it does
  mean anything reading a unit's position mid-window sees an intermediate one.
- **`BodyFace` is not `HexDirection`.** Armour faces are the soldier's own sides, so `BodyFace`
  is an offset from `Unit.Facing`, not a compass point. `Battle.FacesPresentedTo` returns a
  *distribution* — a body is a hexagon, so a shot can always reach two or three plates — and the
  round is rolled against it in `Resolve`. Anything that wants one answer takes `Aspects[0]` or
  `ShotPlan.LikeliestFace`.
- **Nothing may assume a particular turn size.** A turn is 50 and a stride is 5, but the
  allowance is expected to vary per soldier, and the whole list was already rescaled once (10 → 50
  so the cheapest action stopped setting the resolution of everything else). Express test
  expectations against `MovementCosts` / `FireMode.ApCost`, never as literals.
- **Loudness is priced off the listed cost of the ground, not what the mover paid.** Crawling
  costs 3× so a crawler spending 3× the points would come out as loud as somebody strolling —
  the stance cancelling itself out. `LoudnessOf` sums `link.ApCost`, deliberately.
- **The price list is not what a soldier pays.** `MovementCosts` and `FireMode.ApCost` describe
  the world; `UnitStats.Costs` says what this soldier spends on it. Never read `FireMode.ApCost`
  or `TraversalLink.ApCost` directly in a rule — go through `CostProfile`. Movement pricing is a
  `Func` handed to `Pathfinder.Reachable`, never baked into the graph, which is built once per
  map. `CommittedMove` must be given the same profile the route was costed with or the reaction
  clock stops matching the points actually spent.
- **Surprise fires on a crossing, not a rise.** `seen.Before < bar && seen.After >= bar`. "Rose"
  would re-trigger all the way up the awareness ladder; "is above" would trigger every move.
  Reactors also get their mid-window look *only if they have reserve banked* — the reserve is
  doubling as alertness, and removing that gate hands every hostile a free extra look per move.
- **`Unit.Ambush` survives `Advance`; `Unit.Overwatch` does not.** An overwatch is a posture held
  for a round; an ambush is a plan that stands until sprung, which is what lets the member who
  chooses the moment still be armed on its own turn. `Unit.Held` is whichever one is set. An
  ambush window is a `CommittedMove` of *zero* length — same timeline, one instant.
- **Arc edges are exclusive, on purpose.** Hex bearings are exact multiples of 60°, so a place
  sitting precisely on the edge of a 120° arc is the common case. Comparisons add
  `Geometry2D.AngleEpsilonDegrees` so the edge falls to the *wider* arc deterministically — one
  spoke over is the corner of the eye, not full attention. Two tests pin this; don't "fix" them.
- **`ShotPlan.ExpectedDamage` is damage arriving at the plate, not damage done.** It ignores
  shields and armour entirely, so a beam landing squarely on a full force shield reads well and
  achieves nothing. Anything *choosing* between shots wants `Gunnery.Expect`, which puts the
  rounds through the layers they will actually meet. This is the single easiest mistake to make
  in this codebase and the old reaction policy made it.
- **A window's scores are only true before it resolves.** `Appraise` reads live state — the
  target's remaining vitality, who has noticed whom — so appraising an option after `Resolve` has
  run gives a different number than the one it was recommended on. A unit that fired has been
  noticed for firing. See entry 004 in `../decisions.md`.
- **Cover works in both directions and the scorer knows it.** Going flat behind a knee-high wall
  takes you out of sight of the man in front of you, and takes him out of yours: `Spared` goes up
  and `Prospect` goes *negative* in the same appraisal. A posture score that only ever improves
  is a posture score with a bug in it.
- **`Order.Worth` is not what the order was picked on.** `Order.Score` is, and it adds
  `Order.Opens` — the shot a move sets up. A move's own `Worth` is almost always negative, because
  walking costs points and buys nothing; ranking on it means never taking a firing position.
  Anything reading an order for display wants both halves.
- **A three-a-side match costs a second or two.** Measured, on a radius-sixteen disc with both
  sides driven by `Commander`: the two skirmish tests run one and two matches respectively, at
  about two seconds each, while every other test in the file is under a fifth of a second. So a
  thousand headless matches is twenty to thirty-five minutes rather than the *seconds* section 01
  of the design doc claims the engine-free split buys. Nothing needs doing about it until
  somebody actually runs a batch, which is what the overwatch gate is waiting for; the figure is
  here so that whoever does is not surprised.
  <br>**Where the time goes has not been profiled.** The shape of the search says it should be
  the sight traces — a decision crosses the reachable set with every known threat and every fire
  mode, and a full allowance reaches a few hundred nodes on open ground — but that is arithmetic
  about the code rather than a measurement of it, and the obvious fix (cache the trace per
  destination and threat within one decision) is a guess at the right one. Profile before
  optimising.
- **A blade carrier will not walk across open ground to reach you.** Greedy with one step of
  lookahead cannot see a knife going in two turns from now, so it correctly works out that this
  turn's walk into rifle range is worse than standing still, and stands still forever. Not a bug
  in the scoring; a limit of the search, and the first thing a deeper one would fix. Note that it
  would still not stab anybody when it arrived — see entry 008 in `../decisions.md`.

---

## Open questions

Owned here. The design doc carries more, marked *Open* in the section they belong to; these are
the ones that block or shape what Core does next.

- **Nobody goes and looks.** The whole of the brief above, and the largest thing standing between
  what exists and an AI anybody would call one.
- **A shot that kills its target still gives you away to the target.** `GivenAway` counts the man
  being shot at among the people who now know where you are, and if he goes down he is not
  anybody. That is the entire argument for the quiet kill and the model does not make it. Fixing
  it means the announcement preview knowing which enemies survive the shot it is previewing,
  which is a small change to `WouldAnnounce` and a fiddly one to get right.
- **Nothing may decline a reaction.** `ReactionOffer.Recommended` is not nullable, so a reactor
  always takes its best option even when every option scores below zero — which happens: a beam
  that will be soaked entirely is worth about what it costs, and the model correctly says all the
  answers are bad and then picks one anyway. Making it nullable is a handful of lines and a real
  behaviour change, so it wants doing deliberately rather than in passing.
- **`ShieldValue` is the dial to watch first.** At 0.15 a fully soaked eight point beam scores
  0.72 against a snap shot costing 0.75 — near enough break-even that the ordering between firing
  pointlessly and doing something else is decided by noise. Either the shield term is too generous
  or a point of reserve is too cheap, and only matches will say which.
- **Melee does not reach.** `../decisions.md` entry 008, addressed here and open: `PowerBlade`
  carries a 2.0 m range and `Gunnery` measures eye to centre of mass in three dimensions, so at
  the hex size settled in entry 007 two adjacent soldiers are further apart than a blade can
  cover. Nothing special-cases melee and something has to — either a reach measured along the
  ground, or an adjacency test, and which one is a design question rather than a number.
- **The overwatch awareness gate can now be re-examined.** Flagged in the doc and in
  `ReactionModel`, with the two dials named. It was gated on having an AI to run matches with;
  there is one, so this is the first thing to point a batch of headless matches at.
- **Every balance number is set by reasoning, not measurement.** Treat the figures as arguments
  rather than findings, and check the design doc for why one is what it is before changing it —
  several are load-bearing in ways their size does not advertise. This is now *testable* rather
  than merely true, which is the whole reason the AI came before grenades.

## Recent work

```bash
git log --oneline -20 -- src/Hexcom.Core tests
```
