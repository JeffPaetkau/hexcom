# Hexcom

Turn-based sci-fi squad tactics on a hex grid. Take 2: the interface is built first, piece by
piece, and the rules will be brought in to match it. Read [summary.md](summary.md) for what the
first approach learned.

## What exists

A landscape under an open sky with a sun, a tactical camera, and one unit: a blue wooden
piece with 100 action points a turn that can move, priced by the ground: five points a stride
across a field or along a dirt track, four along a paved road, more uphill than down, too
steep a bank refused, and ground too steep to stand on refused even when the step onto it is
level, so no one sidles along a cliff face; and a descent of one in four or steeper can be
hurried, cheaper than the careful step but with a chance of a fall that compounds along the
run, a fall costing the rest of the turn ([MovementCosts.cs](rules/Hexcom.Rules/MovementCosts.cs)
holds the numbers and the reasoning). A hex is a metre from centre to centre, the room a soldier takes
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
shows (run with `-- --grid` to draw it for checking alignment). The active unit stands in a
ring of the HUD's cyan, the hex under the cursor gets a white ring of the same size, so the two
coincide when the cursor is on the unit, and every hex the unit can reach carries a filled
see-through disc of that size: dark grey where a careful way fits the points, orange where only
a hurried way down a slope does, and the card shows the fall risk of the hovered orange hex
([SciFi.cs](game/scripts/SciFi.cs) also holds the red for danger); a left click walks there and
pays for it, and clicking an orange hex is accepting the risk. The rings are meshes draped on the drawn ground and depth
tested, so a piece hides the far side of its own ring; the hex marks are painted by the terrain
shader itself from a one-texel-per-hex texture ([HexMarks.cs](game/scripts/HexMarks.cs)), so
nothing can poke through them on a slope. A card top left shows the active unit, a live portrait of
its token, and its points; End Turn, bottom right, restores them. One world unit is one metre
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
| Left click | move the unit to the hex under the cursor, if in reach |
| End Turn button | restore the unit's action points |
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
point, `--move q,r` to order the unit to a hex and wait for the walk (or `--mid-walk N` to take
the picture N frames into the walk instead), `--end-turn` to press the button after it, `--unit q,r` to start the unit on a chosen hex (for picturing reach on
particular ground; without it the unit starts beside the highway cutting, north of the bluff,
with the camera over it), `--trip` to make every hurried step fall, `--shot-after N` frames to wait at the end (default 8), `--drag dx,dy`
to feed a middle-button drag in pixels through the input pipeline first, `--orbit dx,dy` to
feed a right-button drag from an off-centre point (the console prints the ground under that
point before and after, which should match). The console prints the focus, the unit's hex
and its points at the moment of the picture.

Running with `-- --trace-input` prints every mouse button Godot receives, for checking what a
mouse actually sends. `--heights x0,z0,x1,z1` prints the ground height along a line, for
looking at the numbers behind something a picture cannot explain.
