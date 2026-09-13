# Hexcom

Turn-based squad tactics on a hex grid. Stealth-first, action-point movement, individual
initiative. Desktop only.

## The one architectural rule

`Hexcom.Core` is plain .NET and **never references a game engine**. Every rule — hex geometry,
cover, movement, line of sight, detection, initiative, damage, AI — lives there. Godot is a
presentation and input layer that queries the core and draws the answer.

That buys three things: the rules are unit-testable headless, balance can be tuned by running
AI-vs-AI matches with no window open — a three-a-side match on a radius-sixteen map takes about
two seconds, so a thousand of them is a lunch break rather than an afternoon — and if the art
pipeline ever forces a move off Godot, only the view layer is lost.

If you ever find yourself adding `using Godot;` to a file under `src/`, stop.

```
src/Hexcom.Core/        the rules — no engine references, ever
tests/Hexcom.Core.Tests/  xUnit
content/                maps and missions as text, and the library that reads them; its own tests beside it
game/                   the Godot 4 project (view + input only)
docs/                   design doc, setting bible, and the project map the work is divided by
docs/interface/         what the genre's interface does, a reference file per game behind it with shots from play, and the queue of briefs
```

Work is split into territories with path-based ownership so that several sessions can run at
once without colliding. [`docs/map.md`](docs/map.md) is the constitution;
[`docs/decisions.md`](docs/decisions.md) is the append-only log of anything that crosses a
boundary.

## Running it

Tests, and the fastest way to see whether anything is broken:

```bash
dotnet test
```

The sandbox needs **Godot 4.7 .NET edition** ([godotengine.org](https://godotengine.org/download)
— the build labelled ".NET", not the plain one; `winget install GodotEngine.GodotEngine.Mono` on
Windows). Open `game/project.godot` in the editor and press F5, or from a shell:

```bash
dotnet build Hexcom.sln && Godot_v4.7.2-stable_mono_win64_console --path game -- --aside
```

That long name is the executable's real one. The WinGet package puts its directory on the PATH
but makes no `godot` alias, so `godot` itself resolves to nothing; the `_console` build is the one
to script with, because it keeps its output on the terminal. On another platform or another
install, substitute whatever your Godot binary is called.

Build first — Godot loads the C# assembly from `game/.godot/mono/temp/bin/`, and a scene launched
before it exists fails with a message about not being able to instantiate the script. If your
Godot is a different 4.x, change the `Godot.NET.Sdk` version in `game/Hexcom.Game.csproj` to
match.

To render a frame and write it to a file rather than watch it — useful in CI, and the only way an
automated session can check its own drawing:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --aside --shot out.png
```

A capture ignores the mouse and the keyboard, so that two runs of it agree. `--hover q,r[,layer]`
parks the cursor on a node and `--pass N` hands the turn on N times first, which between them put
the readouts that depend on either back into the picture — the route preview, the cover and
sight figures, and the shot under the cursor. `--ai` hands every hostile turn to the AI during
those passes, so the picture shows a situation the enemy made rather than the opening deployment:

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --aside --shot out.png --hover 2,0 --pass 6 --ai
```

`--fit` pulls back until the whole map is in one picture, `--zoom N` puts the camera N metres
back, `--yaw N` turns it to one of the six hex bearings, `--look q,r` centres on a hex, and
`--scenario name` picks which battle to open. `--omniscient` draws every soldier in play; without
it the picture is the game, and a hostile nobody of yours has found is not in it.
`--instruments` opens the second window and writes it beside the picture as
`out.instruments.png`.

**Nothing animates in a capture.** The camera turns smoothly and a soldier walks its route when
a person is playing; with `--shot` on the line both land on their end state within the call that
starts them, so `--yaw N` still lands on the frame it names and two runs of one command still
produce the same file to the byte. `--still` turns the same two off for a person who would rather
they were, and `--pace N` sets the walking pace in metres a second, ten by default.

**`--aside` opens this run's windows on the leftmost monitor**, which is what keeps an automated
session from putting a window in front of whoever is working on another one. `--shot` implies it.
It changes no pixels — the same command on either monitor produces the same file — and the game
you double-click opens where your window manager puts it, as it should. The window appears where
your system put it for an instant first, because Godot opens it before any script runs; add
Godot's own `--screen N` before the `--`, using the index `--aside` prints, to place it at
creation instead.

**And a capture can act.** Everything on the line but `--shot`, `--shot-after`, `--scenario`,
`--ai`, `--windows`, `--omniscient`, `--instruments`, `--still`, `--aside`, `--edge-pan` and
`--pace` is a step, run in the order it
was typed: `--move`, `--fire`, `--aim`, `--next-target`, `--confirm`, `--back-out`, `--stance`,
`--face`, `--overwatch`, `--arm`, `--spring`, `--shout`, `--extract`, `--pass`, `--until NAME`,
`--ai-turn`, `--hostiles`, `--place`, `--resolve`, `--details` (`Ctrl` held for the rest of the
run) and `--fold`, plus the camera. Each step calls the same
method its key calls, so a picture can only ever show a state somebody at the keyboard could
have reached, and each one prints what it did — a misspelt name would otherwise make a perfectly
good picture of the wrong moment.

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --aside --shot out.png --scenario compound --omniscient   --ai --pass 3 --hostiles hand --until Watchman --overwatch narrow --until Orsini --move 1,0
```

That one walks Orsini across the front of a rifleman holding an arc, and the picture reports
what he did about it: *t15 Watchman (overwatch) snap at (0,1)@0: hit Front for 0*.

The sandbox is a greybox: the battle as boxes on the ground the rules describe, every tile at
its floor height, every wall at the height its profile gives it, every soldier a body at its
stance height with its facing marked, and no art. **It opens as the game a person plays**: you
against the AI on the waystation mission, answering your own reaction windows, seeing what your
side knows — a hostile is on the map only while one of yours has eyes on it, or as a ghost at the
place they were last seen. `O` shows everything and `H` takes the hostile side back off the AI,
so every other way of running it is a keystroke away; a capture opens on the older defaults
instead, with nothing on, which is why the commands above say `--ai` when they want it.
It fights `content/missions/waystation.hexmission` — three of yours on the
west road against a garrison holding the crossroads, one on the house roof with the radio and one
in the watchtower. The map, who stands where facing which way, the way off, the objective and the
clock all come out of that one file; nothing about the waystation is written down in the game
code. `--scenario compound` opens the older and much smaller fight instead: two of yours outside a
walled compound against three inside it, on a map with no mission, deployed by hand — the fixture
every capture is diffed against.

**Where you are looking.** The left hand drives the camera and never leaves the four keys it
starts on.

| | |
|---|---|
| `W` `A` `S` `D` | pan, in screen terms — `W` moves the view up the screen whichever bearing you are on |
| `Q` / `E` | turn to the previous or next of the six hex bearings, animated rather than snapped |
| wheel, `+` / `-` | zoom |
| `F` / `G` | see the whole map / go back to whoever is up |
| PgUp / PgDn | change storey (the roof is storey 1); the storeys above the one you are on are ghosted |

**The mouse drives it too.** A middle-drag pans and a right-drag turns the camera freely. The
arrow keys pan as well. A right *click* backs out of whatever you were half way through and never
spends a point; it is told apart from a drag by whether the pointer moved. The pointer
resting near an edge of the window can push the view that way, and does not unless `--edge-pan`
asks for it: it is the one camera gesture that happens while your hand is doing nothing.

**What the soldier does.**

| | |
|---|---|
| left-click | move whoever is up — or, on a hostile, aim at it; on the one already aimed at, fire |
| hover | show the route, the cost of each awkward step, and what cover the cursor has |
| `1` | aim: at the hostile under the cursor, or the nearest one in sight |
| tab | aim at the next hostile in sight — including one on a storey the cursor cannot reach |
| space | fire, while aiming; end the turn, while not |
| right-click, `Esc` | back out: stop aiming, or put the briefing away |
| `P` | fold the shot's terms away, or open them again — it stays as you leave it |
| hold `Ctrl` | every figure's terms on the map at once, for as long as it is held |
| `C` | cycle stance: standing, crouching, prone |
| `Z` / `X` | turn on the spot |
| `V` | cycle the overwatch arc: none, narrow, standard, wide |
| `B` | arm an ambush, or spring it on whoever is under the cursor |
| `T` | walk off the field, if you are standing somewhere your side may leave from |
| `L` | call a contact in, so everybody in earshot knows |
| space, `1`–`9`, tab | while a window is open: run it, with every soldier doing what the window says they will unless you changed it; change the chosen soldier's answer; choose somebody else. Only your own side's soldiers are offered, and a window with nothing of yours in it does not stop |

**What the whole run is set to.**

| | |
|---|---|
| `H` | hand the hostile side to the AI for every turn, or take it back |
| `J` | let the AI take this turn, whoever is up — "what would you do here?" of your own soldier |
| `K` | answer reaction windows by hand rather than taking the recommendation |
| `O` | see everything — every soldier in play — or only what your side knows |
| `M` | the full briefing, in the six parts the squad was given it |
| `I` | the instruments window |
| `R` | new battle |

**The instruments live in a window of their own**, which `I` opens and which can sit on another
monitor. In it: which battle this is and which switches are on, the keys in this table, and every
turn the AI has taken since you last acted with the reasoning behind each. All of it fails the
test the main view is built to — *would a player who never presses `O` want it* — and the window
being shut is what a shipped interface would look like.

Tiles in reach show their cost, inside the edges described above. Dull red tiles can be crossed but not stood in,
dark blue ones cannot be entered at all, and the blue-outlined ones are where your side may walk
off the field. Darkened tiles are dead ground the active unit has no eyes on, and outlined
tiles have cover from where it is standing — blue light, yellow half, orange full. The tint in a
side's colour is how much attention each soldier has on each piece of ground, at the reach the
rules judge by; the yellow tint is an arc being held, out to the weapon's range.

Walls are drawn from what they do rather than from what they are called, so a map that invents
its own kit draws correctly on the day it is written: the hue is green if you can push through
it, white if it is a building wall nothing gets over, and otherwise the colour of the cover it
gives; the thickness is how much of a body it stops, from a hairline you can see through to the
heaviest thing on the map; and the height is the height the sight trace uses. The strip on the right is the turn order with each unit's initiative roll —
only the soldiers your side knows about, with the next round marked. A hostile nobody has found
holds no slot, so the strip cannot be used to count them; when it is their go a banner says so,
once for the whole run of their turns, and anything your soldiers perceived of it — a shot at one
of them, somebody found or lost — is listed above the keys afterwards.

**The readouts are on the things they describe.** The panel at the top left says only what has
nowhere on the map to go — the mission, the round, whose weapon and the storey. Everything else
hangs from something, and each thing carries one figure with its terms a gesture away.

Over the soldier whose go it is, a bar of its points cut where the reserve steps, and a line saying
each step as a move: *aimed ≤0 · standard ≤14 · snap ≤28 · banks ≤35* is a fresh rifleman who may
spend fourteen and still bank a standard shot, and past thirty-five holds nothing at all. The same
steps are drawn on the ground as violet edges round the move range, in the same colours, with a
pale edge at the limit of reach — so the ground says what the soldier will hold *there*. Under the
bar, its own exposure exactly and the highest rung the other side has reached on it.

Point at an enemy and its hit chance is over its head, with what the shot costs and what it is
worth. Aim — `1`, tab, or a click — and the shot's terms open at the right edge and stay open while
you aim: the chance and the price, which plates it can reach and what each still carries, who
taking it would give you away to, and what it is expected to take off and what the scorer makes of
it, term by term. A beam landing squarely on a full shield reads well on the plates and achieves
nothing on the last line, and the last line is the one the AI ranks by. `P` folds the terms away,
and they stay folded until you open them again.

Point at the ground and beside the tile is what getting there costs, what stopping there would
bank, and who would hear the walk. **Hold `Ctrl` for every figure's terms at once**: at each enemy
your soldier is taking seriously, how far, how much it has worked out about them, the worst shot
they could put into it, and whether they can see it — a contact merely *remembered* is quoted at
the ghost where it is believed to be; at the soldier, the bar they act from, the arc it holds, who a
shout would reach, who has a line to it, and what each posture key would buy, scored the way the AI
would; and at the cursor, cover, exposure, distance and range band, attention and noise. A hostile
nobody of yours has found is *somebody unseen* everywhere, never a name.

**A move opens a window, and you can answer it yourself.** Press `K` and a move is paid for and
held rather than resolved: the soldier stands at the start of a walk it has not taken, the route
is drawn out of it with the tick each step lands on, and everybody who could do something about
it is listed with what each option is worth. The scores are the same call the AI's own
recommendation is made with, which is why *hold fire* reads as `+0.00` — an answer worth nothing
beats every answer worth less, by arithmetic, and there is no rule anywhere saying it should.
It works the other way too: hand the hostile side to the AI and its moves stop for you to answer
with your own sentries.

The translucent field round each unit is how much of its attention each part of the ground has,
drawn at the reach the rules actually judge by. It is graded twice over, because the model is:
across the arc, from the front through the corner of the eye to the little that gets noticed
behind, and outwards, gently at first and then sharply, to the forty-five metres past which a
look is worth nothing at all. The circle is where that happens. It is the reason the map is
eighty-five metres across and the reason the view can be pulled back — a soldier's attention is
half the width of this map, and on a compound you can cross in a turn and a half it reached off
the edge in every direction and told you nothing.

Under each enemy is how alarmed they are — coarse on purpose, though holding `Ctrl` names the
rung at which they will act on it, because a rung nobody can place means nothing. Your own
soldier's exposure is reported exactly, because that is information about yourself; so is how
much of their attention the place under the cursor has, which is the figure the field draws in
colour. Faint red circles are where an enemy *believes* one of yours to be; they stop moving when
you do. An outlined wedge is an arc being held — yellow for an overwatch, pink for an armed
ambush — drawn out to the weapon's maximum range, with the optimal band marked inside it, and the
figure beside it in the turn order is what that unit has banked to answer with.

Press `H` and the other side plays itself. Every turn it takes is written up in the block at the
bottom of the screen, one line per order with the score broken into the terms it was ranked on —
what the action does, what it sets up, and what it cost — so a move to a firing position reads
as the near-worthless walk it is plus the shot at the end of it, and a soldier dropping prone
reads as what that spares it. That block is the enemy's mind laid open, which a finished game
would never show; the sandbox shows it because an AI can only be checked by somebody who can see
what it thought. A soldier that can see nobody does nothing, and the block says so — that is the
current limit of the AI, not a fault in the display.

**There is something to win.** The waystation's mission file says it: go in, look at what is in
the house, and come out by the cottages without anybody properly registering you. The task is on
the top line, `M` shows the whole briefing in the six parts the squad was given it, the exit and
the named ground are drawn on the map, and `T` walks a soldier standing on the exit off the
field. The file also carries a clock — thirty rounds, before first light — which the sandbox
applies and counts down in the status line, because the rules have no clock of their own yet.

Losing a man usually costs the mission rather than being counted as a loss of its own, because
what is judged is the highest rung any enemy held on each soldier as they left, which is the
right way round for a squad whose orders were to go unnoticed. Hand both sides to the AI and
watch it settle in three or four rounds: the scout walks down the road in plain view, through the
gate, takes the look from two hexes outside the door, and is killed there by the man on the roof
while the other two wait at the cottages and leave. The look is taken every time and the mission
is achieved none of the time. That is not a bug in the loader. It is what a squad that is paid
for arriving and charged nothing for being seen on the way will do, and the missing half is in
the design doc.

Go prone and watch the visible area collapse. Pass a few turns and watch the order interleave
rather than alternate. Walk round behind a sentry and watch it stay unaware while the same walk
in front of it does not. Press `F` and look at the rifleman in the watchtower: it can see all
three of yours and its circle stops six metres short of them, so it knows nothing and will do
nothing until somebody walks closer or somebody tells it. The one who would tell it is the
signaller on the house roof, whose radio reaches the whole side — which is what makes the roof
the position worth reaching first, and the scout's blade the only thing that takes it quietly.

You drive both sides, so the three reactions are all easy to try. The HUD reports which tick each
shot went off on and where the target was standing when it landed.

- **Overwatch** — give a sentry a narrow arc with `V`, end its turn, then run one of yours across
  it. Run the same route again with the arc set wide and watch the same weapon shoot worse.
- **Surprise** — walk one of yours across the front of a sentry that declared nothing. It answers
  anyway, out of half a bank and a beat late. Do it again with the same sentry and nothing
  happens: you cannot startle somebody twice with the same soldier.
- **Ambush** — press `B` on two or three of theirs in a row to arm them, then walk one of yours
  into the arc. All of them fire in one window, before you get to answer. Or hover a target and
  press `B` again with an armed unit active to spring it deliberately.

Those are the other side reacting, so a window only stops for them with the instruments window open
(`I`, then `K` if windows are not already being answered by hand) — answering the enemy's reactions
is a tester's job, not a player's.

### Building something to hand somebody

The two commands above run the game out of a checkout. To get an executable a person can be given
instead, from the repository root:

```bash
mkdir -p build && Godot_v4.7.2-stable_mono_win64_console --headless --path game --export-release "Windows Desktop" ../build/Hexcom.exe
```

That leaves `build/Hexcom.exe`, which is the whole game in one file — no pack, no assemblies
beside it, nothing to keep together — and `build/Hexcom.console.exe`, which is the same game with
its output on the terminal and takes every capture and script flag above. `build/` is not tracked,
because a built game is derived exactly as a test result is.

It needs Godot's **mono** export templates for the matching version installed, which is a 1.2 GB
download and the one thing the command does not do for you. `## Shipping it` in
[docs/subprojects/view.md](docs/subprojects/view.md) says where they go, how to tell they are
there, and what the failure looks like when they are not.

## What is built

- **Hex geometry** — axial coordinates, flat-top layout, distance, rings, lines. `HexLayout`
  converts to world space; rotating it 30° renders pointy-top without touching the logic.
- **Corner graph** — every grid corner has one canonical name shared by the three hexes that
  meet at it, so walls live on a global corner graph rather than per-tile.
- **Cover as chords** — a wall joins any two corners of a hex. Six sides, six minor chords, three
  bisectors: fifteen segments per hex, one uniform representation for building faces, sandbag
  lines and barricades cutting diagonally across a tile.
- **Region partition** — chords cut a hex into regions by planar face traversal. Regions below
  60% of a hex are crossable but not standable, so a bisected tile can be vaulted through but
  never occupied.
- **Movement graph** — typed, individually priced links (walk, vault, climb, ladder, drop,
  stairs, door, crawl) instead of uniform grid steps. Climbs, ledges and drops are generated
  from floor heights; ladders and stairs are authored. A stride costs five of fifty points, so
  ten hexes of open ground is a whole turn — and how you carry yourself is priced too: a crouch
  costs half again per hex and a crawl three times, so going flat buys its concealment with
  ground rather than for nothing.
- **Pathfinding** — Dijkstra over action points, returning the whole reachable set. Transit
  regions are pathed through but excluded from valid destinations.
- **Sight and cover** — one trace answers both, because they are the same question. The top of
  each wall the line crosses is projected back onto the target as a waterline; cover is graded
  by how much of the silhouette falls below it, and the target is invisible when an opaque wall
  submerges all of it. Stance, elevation and range are not special cases — a prone soldier
  behind sandbags vanishes, and a shooter on a roof negates that same cover, purely from the
  geometry.
- **Units and the turn loop** — a `Battle` owns the map, the units and whose turn it is. Turn
  order is a queue over a battle clock rather than sides alternating, so play interleaves: one
  of yours, two of theirs, one of yours. Initiative is a rating plus a d10, less the weight of
  your kit. Every roll comes from one seeded generator, so a whole fight replays identically
  from a seed and a list of commands — which is what makes headless balance runs possible.
- **Detection and awareness** — no aggro radius anywhere. Every enemy that knows about you
  learned it through a channel you can see and cut: looking (on their own turn, so a sentry that
  has already acted leaves a window), hearing (immediate, and it reports a place rather than a
  person), or being told by radio, by shouting, or by watching a comrade react. Only a unit with
  a radio reaches the whole side. Each enemy holds a belief about where you are, and it goes
  stale the moment you move.
- **Facing and vision cones** — a unit looks one way: full attention across 120°, a corner of the
  eye out to 200°, a twelfth behind. Coming at a sentry from the rear is worth an order of
  magnitude, so a position is flankable rather than merely approachable. Facing changes how
  readily something is *noticed*, never whether it could be seen — line of sight stays geometry.
  Moving turns you to face your line of travel for free; watching one way while standing still
  costs a fraction of a stride.
- **Weapons, shooting and protection** — beam against kinetic, and each defeats what the other
  cannot. Shields soak beams and shrug at solid objects; ablative plate stops rounds and cooks
  under a beam. Both are tracked **per side of the body** — front, two shoulders, two flanks and
  the back — so the walk round the back that buys an unnoticed approach also buys the thin side
  of the armour, and a soldier whose front shield has collapsed can turn a fresh one to the
  threat for a point. Hit chance comes from the sight trace's exposure figure, weapon range
  bands, fire mode and stance. Firing gives you away through the channel your weapon uses: a slug
  rifle is heard through walls, a beam paints a line back to you for anyone facing your way, and
  a powered blade does neither. Reach is metres for everything that is fired and is deliberately
  not metres for a blade: melee means *adjacent*, and the movement graph answers it, walls and
  storeys included. Measuring a knife along a rifle's line made it reach worst exactly when the
  target was lowest and least able to avoid it.
- **A body is a hexagon too** — so a shot is never at one plate. Head-on you can reach half the
  front and a quarter of each shoulder; on the corner, two plates equally. Which one a round
  finds is rolled against those shares. A slug that arrives at an angle skips off and loses some
  of its damage; a beam lands where it lands and burns. The averages are flattened so the
  bearing you approach from decides *which side wears*, never how much gets through — a hexagon
  is bookkeeping, not a claim that soldiers are hexagonal. Ordinary soldiers do not choose where
  a round lands; placing one on a named plate is something a soldier earns, and costs accuracy.
- **Everyone pays their own prices** — the price list describes the world, but what a given
  soldier spends on it is about them. A scout quick over ground and slow on the trigger and a
  gunner the other way round spend the same fifty points on very different turns, and gear that
  shaves a point off firing is a multiplier on the wearer. Inside a reaction window that is not
  only economy: cost is time, so the slow shooter's round lands later and catches the runner
  further along.
- **The reaction window, and overwatch** — a move is committed before anyone answers it, so for
  its duration both sides know the future. Inside the window **action points are time**: a
  reactor placing an action at tick *t* that costs *k* resolves at *t + k*, against wherever the
  mover will be by then. A three point snap shot catches a runner in the open; a slower, better
  shot arrives after the same runner is behind a wall. Reactions are paid for out of what was
  left at the end of your own turn, so sprinting somewhere leaves you nothing to answer with, and
  the choice to hold points back is made before you know whether it will pay. Overwatch is the
  first of the three kinds: a declared arc, an aiming bonus that sharpens as the arc narrows, and
  a shot cheap enough to land early in the window. A watchman only fires at somebody it has
  actually noticed — holding an arc buys it a look at the moment of the crossing, not certainty
  about what is there, so a careful enough approach still gets across.
- **Surprise** — the involuntary one, that nobody sets up and everybody has. It fires on the
  single moment a contact crosses into being noticed, so you cannot startle somebody who was
  already tracking you and a firefight does not generate one per move. Half the reserve, no
  aiming bonus, and it starts a beat after registering rather than at the top of the window —
  which is where "the weapon was already pointed" stops being a claim about overwatch and starts
  being arithmetic. Two bars, not one: something at the edge of what you can make out is enough
  to duck or spin round and nowhere near enough to shoot at, so a crawler at forty metres makes a
  sentry twitch without drawing fire. Behind is still behind.
- **Ambush** — a squad arms against an agreed arc and waits; when one of them says now, every
  armed member fires in the same window, before the target does anything about any of it. That is
  what makes an alpha strike survive interleaved initiative. Structurally it is a committed move
  of *zero* length — the same timeline, one instant — so the cheap shots still land before the
  expensive ones and a squad stops spending reserves on somebody already down. Springing calls
  the contact in first, so an ambusher has to be reachable by radio, shout or line of sight to
  join in, and one who got bored and spent its turn moving is still armed and out of the trap.

- **Judgement, in vitality** — every action a soldier could take is scored in the only currency
  that ends a fight: points of soldier. What a shot is worth is what gets through the shields and
  the plate it will actually meet, so a beam landing squarely on a full force shield reads as the
  nothing it is, and wearing eight points off a plate that never comes back reads as the progress
  it is. What a *posture* is worth is worked out by asking the ordinary questions twice, once
  about the soldier as they are and once about the soldier as they would be: turning earns its
  keep by buying a look rather than by presenting a better plate, going flat earns its keep by
  being harder to find as much as by being harder to hit, and diving behind a knee-high wall
  scores the shot it costs you as well as the shot it saves you. What calling a contact in is
  worth is whatever the people who can hear it could then do about it — nothing if they already
  knew, a great deal if one of them was a rung short of being allowed to fire down the arc they
  are already holding. Action points are priced in the same currency, which is what lets a cheap
  bad option be compared with an expensive good one at all.

  Firing is priced as the loudest thing a soldier does. A shot is worth its damage *less* what it
  tells everybody — the man you shot at knows for certain, everyone in earshot of a slug hears
  roughly where, everyone facing a beam sees exactly where — measured by how much closer each of
  them comes to acting on it, times what they would then do about you. Somebody who already has a
  live fix learns nothing and costs nothing.

  Nothing in it is a ladder. The old policy for picking a reaction was one — shoot if you can,
  otherwise turn, otherwise get low, otherwise call it in — and it could not tell a shot that
  would be soaked from one that would not, because it ranked shots on damage arriving rather than
  damage arriving anywhere. That is gone. The AI and the interface rank by the same call, and it
  returns its terms separately so a player can be told *why* rather than shown a number.

- **A soldier that takes its own turn** — the search half, over the same judgement. Every hex it
  could stand in crossed with everybody it could shoot from there, plus turning, getting lower,
  and holding an arc. Greedy, with one step of lookahead on moves, because walking is not an
  achievement: a move to a firing position is worth nothing on its own and a great deal because
  of the shot at the far end of it, so the two are ranked together and carried out separately.
  What falls out is a soldier that goes round a man in cover rather than shooting through it —
  nobody wrote that down; the sight trace reports less of a target behind sandbags and the
  arithmetic does the rest.

  Doing nothing is a candidate with a real score. Points left at the end of a turn become the
  reserve you answer somebody else's move with, so holding is worth whatever it could afford to
  do about the threats you know about — which has a cliff in it, because a bank too small to fire
  from is worth nothing to fire with. An action has to beat holding rather than beat zero. It is
  also why declaring an arc is ever chosen, and why *which* arc comes out of the arithmetic
  rather than off a preference list.

  Two sides driven by it fight a skirmish to a decision with no window open, and replay
  identically from a seed. That is the thing the engine-free split was built for.

- **Grenades, and the second trace** — everything else the map is asked is whether a *straight
  line* gets through, and the whole point of throwing something is that it does not have to. So
  there is a second query beside the sight solver: it crosses exactly the same walls and asks a
  different question of each, whether the top is above the *parabola* rather than above the line.
  A soldier throws as flat as the obstacles allow, so the arc is the lowest one that clears
  everything in the way — nought on open ground, where it degenerates back into the sight line.
  When the arc a wall demands is more than an arm can manage the throw clips it and drops short,
  which is how a grenade ends up at your own feet.

  Where it lands, the wave reaches each soldier by distance, by what is between them and the
  burst, and by how much of them is standing up in it. All three are geometry already in the
  game: the burst traces outward through the same waterline arithmetic, so a wall shelters you
  from a charge on the far side of it and does nothing about one lobbed over — and going flat
  quarters what you catch, because a prone silhouette is a quarter the height of a standing one.
  Nothing about explosions and cover had to be written down. A blast hits the faces a round would
  hit and goes through the layers a round goes through, so fragmentation is the answer to a
  shielded soldier exactly as a beam is the answer to an armoured one.

  A charge is the first thing in this game that runs out, which is the whole of what stops the
  scorer leading with grenades: it is worth about one clean rifle shot to still have one, so
  against a man in the open the rifle wins and against a man behind a wall it does not. And a
  grenade is aimed at a *place*, so it may be thrown at a remembered one — the decision is made
  on the belief and the world answers it, and if he moved, the grenade is wasted.

- **Mines** — an overwatch that nobody is standing behind. Not a metaphor: a mine resolves inside
  the same window an overwatch fires in, at the tick the mover's foot lands on its tile, on the
  same clock and in the same order. What it needed was not a mechanism but an owner, because
  everything else in a window is offered to a unit out of that unit's reserve. It is the only way
  to shape an approach nobody is watching — an overwatch expires when its owner's turn comes
  round and an ambush is spent the moment it springs, so both of them cost somebody standing
  there.

  An explosion is heard from *where it went off* rather than from who set it off, which is the
  one way in this game to make a great deal of noise somewhere you are not. Everybody in earshot
  marks you at the crater, and being blown up does not tell you who did it — unlike being shot at,
  which settles the question.

- **A window a person can answer** — a move is *committed* and not yet resolved: the route priced,
  the points spent, the offers made, nothing placed. It stays that way until somebody resolves it,
  so an interface can draw the choices, let a player place their own over as many frames as they
  like, and only then run it. Moving is those two halves with every recommendation taken between
  them, which is what a headless match wants and what every existing caller still gets.

  It had to be a state the battle sits in rather than a question asked inside a call, and that is
  forced rather than preferred: input arrives across frames, so a callback would have to stop the
  engine until the player chose. The seam reaches through the AI as well, because the window worth
  answering is the one the *enemy's* move opens — a commander can be told to hand its windows out,
  stopping the turn with one open and resuming once it is answered, and it reports what each order
  did as well as what it was chosen on.

  **Holding fire is an option like any other**, wherever there was already a choice. Nothing could
  decline a reaction before, so a reactor took its best option even when every option scored below
  zero — which happens, because a beam that will be soaked entirely is worth about what it costs.
  It is priced at exactly nothing, so it wins by arithmetic whenever every answer is worse than
  nothing. Not offered to surprise: that one is the flinch, and the whole of what it models is
  that a soldier caught out does *something*.

- **A battle that ends because somebody did what they came for** — three endings rather than two.
  The mission achieved, the mission settled against you, or the mission out of reach and everybody
  home anyway; the third is the commonest honest outcome of quiet work. Casualties are not a term
  in any of them, deliberately: the campaign holds the roster and grades those, and nothing
  tactical should be made to weigh a dead rifleman against what the squad came for.

  The first mission shape needed no new measurement. *Leave with nobody above a suspicion* is
  readable off the awareness ladder against thresholds that already existed — what it needed was
  somewhere to leave from, a way to tell walking off the field from being carried off it, and the
  reading taken **as each soldier goes** rather than afterwards, because leaving makes the tracker
  forget and a condition asked after the fact reads *unaware* for everybody, trivially and always.
  Sampling per departure rather than keeping a high-water mark is also what preserves the best
  move in the game: silencing a witness really does take his contact out of the world.

  It is the first thing that gives a soldier who can see nobody something to want, and the way it
  does that is a gradient rather than a flag. Worth everything from inside the exit and nothing a
  pace outside, and a search one step deep would never set off; sloped over the approach, measured
  in action points along the movement graph, every stride toward it scores.

- **A mission is a journey with something in the middle of it** — go, do the thing, come back. It
  is one quantity, measured in action points: getting to the place, whatever the job itself costs,
  and getting to the exit. So a stride toward a charge and a stride spent setting it are worth the
  same, and the score is continuous across the moment the task completes — finishing it does not
  jolt anything, it shortens what is left. The exit is not the far end: standing on it with the
  job undone is further from done than standing at the place, because the way home runs by way of
  the thing you came for.

  That was found rather than designed. The first version modelled only the leaving, and twelve
  matches on a real map ended in round two with a squad that walked out of the gate and never went
  near what it was sent to look at — correct play, given what it had been told. Three shapes now
  exist over one structure: get out unseen, put eyes on a place, or spend long enough on
  something. The horizon the pull is measured over stretches to the length of the job, so a
  mission longer than a few turns still slopes all the way back to where the squad started.

- **A mission stops** — the sixth part of every briefing in the book, and the first thing in the
  rules that reads a round number. Two halves, in two places, and keeping them apart is the whole
  of it. A limit is a property of the *mission*: the same ground under a different briefing is
  over at a different hour, so it hangs on the objective as a round number and a comparison. *The
  alarm went out* is a fact about the *awareness model*: somebody carrying a set worked out that
  there is a person here and passed it on, which would be true of that ground with no mission on
  it at all. A mission can stop at an hour, or so many rounds after the garrison knows, or
  whichever comes first.

  A set and not a shout, and on real ground that is the difference between an incident and a
  mission: the waystation's barn and watchtower are both outside earshot of the compound, so a
  sentry who shouts has told one man. And word already sent cannot be unsent — everything a
  departing soldier knew is forgotten, which is what makes silencing a witness work, but an alarm
  they raised first survives them. That is why the man with the radio is worth killing *first*
  rather than merely killing. The clock running out is abandonment and not failure: a squad still
  in the field at first light has lost the mission and has not lost the squad.

- **Not being seen is priced** — the term the first measured numbers said was missing. For each
  enemy, what they will hold on a soldier after an action — what they hold now; the one look a
  walk across their front hands them on the way, priced as the reaction window takes it; the look
  the new pose hands them a round for as long as it is held, or the forgetting if it finds nothing;
  and whatever the noise hands them — is read as a share of the way to the rung the mission is
  lost at, and the worst of them is how much of the mission is gone; an action is worth the
  difference, times what the objective is worth. A slope up to the rung rather than a cliff at it,
  and on past it up to the ceiling, so a search one step deep can see it coming and can see the
  way back. Two things fall out of the shape: each soldier keeps itself quiet even after a comrade
  is noticed, and a shot counts the man being shot at only at the chance he survives it — the
  quiet kill, priced.

- **A squad can be briefed, and a briefing holds.** Every soldier of a side is handed a marker on
  each post the mission names, at the rung it says and facing the way it says he watches. The
  marker keeps until the soldier has had a line to the place and found nobody there, because a
  post is not a sighting and does not fade like one. A marker made by a look keeps the facing it
  saw; one made by ear has none, and is priced as if he could be looking any way at all.

- **The hour, as the scorer sees it.** A per-action scorer cannot price time, so the clock goes
  into the one rate that matters: the objective's slope is stretched by the ratio of the mission's
  length to the night left, one while the night is the longer and steeper once it is not. Stretched
  rather than re-sloped, so a soldier further from home than the night allows is still drawn home
  rather than stopping wanting it.

- **Maps are text** — `content/maps/*.hexmap`, and `MapLibrary.Load("compound")` from anywhere.
  The format is the corner graph written down: a `tile`, a `chord` between two corners of a hex,
  an authored `link`. Everything friendlier — `fill disc`, `wall solid line 2,-3 to 2,2 nw sw`,
  `enclose`, `breach` — expands to those three, and a writer lowers any map back to them so the
  shorthand can be shown to add nothing. The demo compound is thirteen statements; the first map
  at the size the ranges need, 85 m across and eighteen hundred tiles, is forty-five. A map brings
  its own wall profiles and ground types if it wants them, and `block` draws the rectangles a town
  is made of. `content/README.md` is the reference.
  The sandbox reads its maps this way and no other, so what the game draws and what a headless
  test loads are the same file.

- **Missions are text too, in a file of their own** — `content/missions/*.hexmission`, and
  `MissionLibrary.Load("waystation")`. A map holds ground and nothing else on purpose, so the
  four things a mission needs that ground cannot carry go here: where each side starts and which
  way it is looking, a named place to leave by, what the side came to do, and when it stops. Plus
  the squads, the briefing in the six parts the mission book gives one, and what the squad is told
  about the posts it will meet — `told player searching Cobb Teague Marek` — so a squad driven by
  the AI no longer walks its first turn blind into the view of a sentry its own briefing names.
  The round limit is the objective's own deadline, read by the rules. `Mission.Begin(seed)` hands
  back a battle deployed, briefed, ordered and started. It is a separate file rather than a block in
  the map because ground outlives missions and one battlefield can carry several of them, and the
  reasoning is in `content/README.md`. The sandbox fights from it too, so what you play and what
  a headless match measures are the same seven soldiers standing in the same places. Both sides
  are named out of the roster, and the ground the briefing talks about — the compound, the house,
  the cottages — is named ground the objective can point at and the view can label.

- **The waystation has been fought over** — by the AI on both sides, a dozen seeds, headless,
  with a recorder in `content/Hexcom.Content.Tests/Waystation` that writes down where everybody
  went, who threw what at which piece of ground, and the highest rung each hostile ever reached
  about each of ours. The map was redrawn from what the routes said: a tree line so the west road
  is a queue and the fields an approach, a stream too deep to wade so the bridge and the ford are
  the crossings, and sandbags at the gate the sentry stands at. What the matches measured is in
  `docs/decisions.md` from entry 037. The first dozen never reached a decision at all. The same
  dozen fought from the mission file all settle, and what they settle *as* has moved twice: with
  only a way off the field written down they walked out in round 2 without going near the house
  (entry 048), and now that the file states the real task they cross the map and take the look in
  round 2 instead, twelve times out of twelve, and are seen doing it twelve times out of twelve
  (entry 081). The recorder writes the job down separately from the verdict for that reason —
  abandoned with the look taken and abandoned without leaving the road are opposite findings.

- **And the map has been measured against its own briefing**, which turned out to say more than
  anybody drew on purpose. The task is to get eyes on what is in the house: of the 1693 places a
  soldier can stand outside the compound wall not one has a line into it, of the 54 inside exactly
  fourteen do, all of them south of the door — and every one of the fourteen is overlooked by the
  roof the man with the radio is standing on. Ask it of the node the objective actually aims at,
  the middle of the room rather than the house at large, and the fourteen become four in a line
  straight out from the door; the drain under the south wall, the way in nobody watches, opens one
  stride short of the nearest of them. So the ground states the mission: in by the drain, a stride
  to the only place the room can be read from, and the roof is the whole problem. Entries 059 and
  081, and four tests hold it.

- **There is a second battlefield, of the other shape** — Kestrel Yard, a freight yard in a works
  town, radius 14 against the waystation's 24, with its own reconnaissance: get eyes on the
  loading floor inside the shed and leave over the footbridge. Every wall is a building face, and
  it was measured against its briefing before it was called drawn: the floor is seen from the
  shed, from the yard through the roller door and from the office across the lane, all of it
  watched, and the duct under the shed lands a stride from a look. Fought over two dozen times, the
  look is taken every match and the squad goes in by the gate every match. What it found that is
  not the map's — that a roof does not stop anybody seeing into the room beneath it, and that a
  line past the seam of a two-storey wall sees through — is in `docs/decisions.md` entry 092. In a
  town the walls bind before the weapon ranges do: no post on it sees as far as the rules allow.

## What is not built yet

Suppression, saves, art, and the strategy layer. See the design doc for where these are
heading.

**Three of the six mission shapes are built and three are not.** Extraction wants a thing that can
be carried; capture wants a way to put somebody down that is not damage; denial wants the mirror
of the others. The clock all three were waiting on exists. None needs new geometry.

**A mission file cannot say when it stops yet.** The rules read a clock now; the format that
writes one is Content's, and until it lands the round limit in `waystation.hexmission` is still
applied by whatever runs the battle rather than by the mission.

**Nobody patrols.** A garrison is however many soldiers were deployed, standing exactly where they
were put, and three of the waystation's four never act at all. Neither a mission file nor the AI
can say what a soldier is *doing* rather than where it is, so the fiction's one honest patrol is
unwritable and a fifth sentry would be a fifth sentry standing still.

**Nothing tells a commander how the battle is going.** It weighs one action against another at
one moment, so it cannot weigh cutting its losses against pressing on — and it is therefore not
offered the choice, which the rules allow and which is one of the three endings. A squad being
cut to pieces stands and takes it.

**Briefed, nothing wins the waystation; blind, it is won one match in seven.** A batch of
headless matches — `tests/Hexcom.Core.Tests/Measured`, off by default, `HEXCOM_BATCH=1` to run
it, `HEXCOM_PROGRESS=<file>` to watch it — plays the reconnaissance a hundred times an arm.
Before being seen was priced, the mission was a footrace (`docs/decisions.md` entry 083). With
it priced, the followers were tagged crossing the gate sentry's front on the way to hidden ground
and the term went dead once anybody held them, so they walked to the gate and started a war
(087). With the crossing priced as the window takes it, the recovery priced past the rung and
the briefing holding, a briefed squad is never seen, never fires and never goes in: it finds the
hidden ground at the bridge in round one, and every way forward from there crosses the sentry's
front or is heard by four men, while the way round leaves the direct line before it comes back,
which a search one step deep cannot see (091). Blind, the same squad walks in, is seen, hides
until it is forgotten and walks out under Suspicious — fifteen matches of a hundred achieved,
where there were none. The route that goes round rather than past is the head of Core's next
brief; whether being forgotten should be that cheap is Master's.

**Most numbers in the game are still arguments.** Four have been measured, and so have the firing
prices as a whole: they stay, because a quarter dearer takes the surprise snap out of a startled
sentry's purse and wins the waystation once in a hundred (`docs/decisions.md` entry 095). The rest
have not.
What an objective is worth has been measured twice and is saturated both times.

**A soldier still only looks one step ahead.** An objective slopes, so it draws a unit from
several turns away; a marker does not, so hunting still reaches about one move and two survivors
who lose each other out of that range still stand still. That is the search rather than the
scoring, and it is the same limit that stops a blade carrier crossing open ground.

**Acting on the real position of a unit you have lost track of** is exactly the cheating the whole
scheme exists to prevent, and for a long time the answer to it was that nobody went and looked at
all. That is no longer the answer. A soldier now builds a threat from a *marker* — where contact
was last made — discounted by how long it has gone unconfirmed, so it will walk round a corner it
heard something behind and lob a charge over a wall it cannot see through, and it does both on
its own belief rather than on the field. What it will not do is walk two turns to get there: the
search is one step deep, and a soldier that will not cross open ground for a knife will not cross
it for a marker either.

## The setting

Science fiction, people rather than monsters, and written downstream of the rules — the systems
were built first, so the fiction earns its place by explaining them rather than by inventing
freely. [`docs/setting.md`](docs/setting.md) is the bible;
[`docs/setting/missions.md`](docs/setting/missions.md) is the mission book, six shapes a mission
can take with the words a squad is briefed in and what winning each one is in quantities the
rules already have; and [`docs/setting/roster.md`](docs/setting/roster.md) is the roster, twelve
people a side written as nothing but the numbers that already exist — a `UnitStats`, a
`CostProfile`, a `Loadout` and three sentences each.

The short version. A power that administered this region has withdrawn and left its automated
interdiction still running overhead, which destroys anything that announces itself: no aircraft,
no artillery, no drones, no sensor net, and one radio a squad carried by somebody specific. What
is left of its apparatus has split into two claimants who each say they are its continuation, and
who therefore cannot admit that what they are doing is a war. So it is fought twelve people at a
time, over installations rather than ground, by professionals with identical kit out of the same
armoury eleven years apart.

Both weapon families survive because neither answer is general. Force fields stop beams and shrug
at solid objects, ablative plate stops slugs and cooks under a beam, so every soldier carries the
right answer to half of what is shooting at them. Nobody wins a frontal exchange, which is why
both sides teach the same doctrine and why the game is about seeing first.

A mission is therefore about possession and information rather than casualties, and a battle
wants three endings rather than two: the objective achieved, the objective settled against you,
or the objective out of reach and everybody home anyway. The cheapest of the six shapes is a
withdrawal — get in, do the thing, and leave with nobody on the other side above a suspicion —
which is readable off the awareness ladder that already exists.
