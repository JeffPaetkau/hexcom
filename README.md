# Hexcom

Turn-based sci-fi squad tactics on a hex grid. Take 2: the interface is built first, piece by
piece, and the rules will be brought in to match it. Read [summary.md](summary.md) for what the
first approach learned.

## What exists

A landscape under an open sky with a sun, a tactical camera, and two units: our blue wooden
piece and a red enemy one, each with 100 action points a turn, thirty hit points and a rifle
with twelve rounds that does ten damage out to fifty-five metres
([Weapon.cs](rules/Hexcom.Rules/Weapon.cs), [Unit.cs](rules/Hexcom.Rules/Unit.cs)). The
turns alternate, ours then theirs, and both are played from the same mouse until there is an
opponent to play the other side; both sides see everything, fog of war comes later. A shot
costs 35 points, cannot miss the next hex, hits at 80% at twenty metres and two fifths of that
at the limit, and
is refused with a reason past it, with no rounds or without the points
([Shooting.cs](rules/Hexcom.Rules/Shooting.cs)); there is no cover, armour, reaction or
reloading yet. A unit can move, priced by the ground: five points a stride
across a field or along a dirt track, four along a paved road, more uphill than down, too
steep a bank refused, and ground too steep to stand on refused even when the step onto it is
level, so no one sidles along a cliff face; and a descent of one in four or steeper can be
hurried, cheaper than the careful step but with a chance of a fall that compounds along the
run, a fall costing the rest of the turn ([MovementCosts.cs](rules/Hexcom.Rules/MovementCosts.cs)
holds the numbers and the reasoning). A unit faces one of the six hex directions
([Facing.cs](rules/Hexcom.Rules/Facing.cs)): it arrives from a walk facing the way it came,
faces what it fires at for nothing extra, and otherwise turns on the spot for four points a
sixth of a turn, so an about-face is twelve. Facing decides nothing yet; perception, next,
will read it for where the soldier is looking. A hex is a metre from centre to centre, the room a soldier takes
standing or crouching, a stride is one hex, and a turn stands for ten seconds, so a full
turn of walking is twenty metres at two metres a second and the piece walks each step in the
time it cost ([Units.cs](rules/Hexcom.Rules/Units.cs)), played at double speed
(`Board.PlaybackSpeed`; one is real time). Reach is Dijkstra over the hexes with the ground asked for the
price of each step ([Movement.cs](rules/Hexcom.Rules/Movement.cs)), so the outline of what
a unit can reach stretches along a road and shrinks up a hillside, and the piece walks the
cheapest way rather than the straight one. Each soldier pays against the shared price list
through a [CostProfile](rules/Hexcom.Rules/CostProfile.cs). The ground is one
continuous height function ([Terrain.cs](rules/Hexcom.Rules/Terrain.cs), plain C#): hills,
rolling ground and detail from seeded noise, with paved roads and dirt tracks laid on it as
splines that flatten the ground onto their own smoothed profile, and one authored landform, a
bluff south of the highway cutting whose face runs from a gentle ramp to a sheer cliff so every
grade the price list cares about, refusals included, is within a turn of the standard picture.
The view draws it as a
quadtree of mesh chunks out to eight kilometres ([TerrainView.cs](game/scripts/TerrainView.cs))
with a shader that decides grass, dirt and asphalt per pixel from a baked road-distance map,
the slope and noise. The hex grid is not drawn; it is how the game works, not something it
shows (run with `-- --grid` to draw it for checking alignment). The unit whose turn it is stands in a
ring of its side's colour, the HUD's cyan for ours and the danger red for theirs; the hex under
the cursor gets a white ring of the same size, so the two
coincide when the cursor is on the unit, and every hex the unit can reach carries a filled
see-through disc of that size: dark grey where a careful way fits the points, orange where only
a hurried way down a slope does, and the card shows the fall risk of the hovered orange hex;
an enemy the unit can fire at from where it stands carries a red disc
([SciFi.cs](game/scripts/SciFi.cs) holds the three). A left click walks there and
pays for it, clicking an orange hex is accepting the risk, and clicking an enemy under a red
disc fires: a tracer draws the round, ending on the target or going past on a miss, and a
piece put down topples away from the shot and lies there dulled. The rings are meshes draped on the drawn ground and depth
tested, so a piece hides the far side of its own ring; the hex marks are painted by the terrain
shader itself from a one-texel-per-hex texture ([HexMarks.cs](game/scripts/HexMarks.cs)), so
nothing can poke through them on a slope. A card top left shows the unit whose turn it is, a
live portrait of its token, its name in its side's colour, its action points and hit points as
bars, its rifle with the rounds left and the numbers under, and which way it faces as a compass
point, the piece itself carrying a short pale nose at eye height that says the same; with the
cursor on a hex it does not face, the card adds what a right click's turn would cost, in orange
if it cannot be paid; with the cursor on an enemy a
second card top right, red-edged, shows their hit points and what the shot would be, the range,
the chance, the damage and the cost, or why it is refused. End Turn, bottom right, passes the
board to the other unit and the camera goes to it; its points come back as its turn starts.
One world unit is one metre
([Units.cs](rules/Hexcom.Rules/Units.cs)). The rules are their own engine-free library,
[rules/Hexcom.Rules](rules/Hexcom.Rules): the hex maths, the ground, the unit, the price
list and the movement, with xUnit tests beside it in
[rules/Hexcom.Rules.Tests](rules/Hexcom.Rules.Tests) that price steps on ground drawn by
hand. The game project references the library; nothing in the library knows about Godot.

## Running

Godot 4.7.2 .NET (`Godot_v4.7.2-stable_mono_win64_console`, installed by WinGet; not on PATH).
Build first: Godot loads the assembly the build produces. The solution must stay a classic
`Hexcom.sln`; the .NET 10 SDK creates `.slnx` by default and Godot does not look for that.

```bash
dotnet build Hexcom.sln --nologo -v q
```

```bash
dotnet test rules/Hexcom.Rules.Tests --nologo
```

```bash
Godot_v4.7.2-stable_mono_win64_console --path game
```

From PowerShell the full path needs the call operator in front of it:

```powershell
& "C:\Users\Jeff Paetkau\AppData\Local\Microsoft\WinGet\Packages\GodotEngine.GodotEngine.Mono_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64_console.exe" --path game
```

It opens fullscreen on the leftmost monitor; F11 switches to a window and back.

## Camera controls

| Control | Does |
|---|---|
| Left click | move the unit to the hex under the cursor if in reach, or fire at the enemy standing on it if in range |
| Right click | turn the unit on the spot to face the hex under the cursor, four points a sixth of a turn |
| End Turn button | pass the turn to the other unit, whose action points come back |
| W A S D, arrows | pan (Shift hurries) |
| Screen edges | pan |
| Q, E | turn while held (Shift hurries) |
| Mouse wheel | zoom |
| Middle drag (wheel pressed) | pan by dragging the ground |
| Right drag | orbit (yaw and pitch) |
| Home, F | recentre |
| F11 | fullscreen or windowed |
| Escape | quit |

## Taking a picture

Every visual change is checked with a capture, not a claim. Not with `--headless`: a window has
to open to draw anything.

```bash
Godot_v4.7.2-stable_mono_win64_console --path game -- --shot out.png --pitch 15 --zoom 30 --yaw 60
```

Flags: `--focus x,z`, `--yaw` and `--pitch` in degrees, `--zoom` in metres back from the
focus, `--sun elevation,bearing` in degrees, `--hover x,z` to put the cursor on a ground
point, `--face q,r` to turn the unit to face a hex and wait for the turn, `--move q,r` to
order the unit to a hex and wait for the walk (or `--mid-walk N` to take
the picture N frames into the walk, turn or shot, instead), `--fire N` to fire N shots at
the enemy after the move (`--sure` makes every shot hit, `--miss` every shot miss),
`--end-turn` to press the button after that, or `--play "fire fire end end fire"` for the
orders in any other order, a step per word (`face:q,r`, `move:q,r`, `fire` or `end`), `--unit q,r` to
start our unit on a chosen hex (for picturing reach on particular ground; without it the unit
starts beside the highway cutting, north of the bluff, with the camera over it) and
`--enemy q,r` the enemy (without it he stands twenty-three metres east along the highway),
`--trip` to make every hurried step fall, `--shot-after N` frames to wait at the end (default 8), `--drag dx,dy`
to feed a middle-button drag in pixels through the input pipeline first, `--orbit dx,dy` to
feed a right-button drag from an off-centre point (the console prints the ground under that
point before and after, which should match). The console prints the focus, whose turn it is,
and each unit's hex, facing, points, hit points and rounds at the moment of the picture.

Running with `-- --trace-input` prints every mouse button Godot receives, for checking what a
mouse actually sends. `--heights x0,z0,x1,z1` prints the ground height along a line, for
looking at the numbers behind something a picture cannot explain.
