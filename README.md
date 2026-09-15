# Hexcom

Turn-based sci-fi squad tactics on a hex grid. Take 2: the interface is built first, piece by
piece, and the rules will be brought in to match it. Read [summary.md](summary.md) for what the
first approach learned.

## What exists

An endless asphalt plain under an open sky with a sun, a tactical camera, and one unit: a
blue wooden piece with 50 action points a turn that can move, five points a hex. The hex
grid is not drawn; it is how the game works, not something it shows (run with `-- --grid`
to draw it for checking alignment). The hex under the cursor gets a white ring and the edge
of the unit's reach a smoothed white outline with corners rounded to the same radius; a left
click walks there and pays for it. A card top left shows the active unit, a live portrait of
its token, and its points; End Turn, bottom right, restores them. One world unit is one metre
([Units.cs](game/scripts/Units.cs)); the hex maths, the unit and the movement rules are plain
C# under [game/scripts/rules](game/scripts/rules), ready to move into an engine-free library.

## Running

Godot 4.7.2 .NET (`Godot_v4.7.2-stable_mono_win64_console`, installed by WinGet; not on PATH).
Build first: Godot loads the assembly the build produces. The solution must stay a classic
`Hexcom.sln`; the .NET 10 SDK creates `.slnx` by default and Godot does not look for that.

```bash
dotnet build Hexcom.sln --nologo -v q
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
point, `--move q,r` to order the unit to a hex and wait for the walk, `--end-turn` to press
the button after it, `--shot-after N` frames to wait at the end (default 8), `--drag dx,dy`
to feed a middle-button drag in pixels through the input pipeline first. The console prints
the focus, the unit's hex and its points at the moment of the picture.

Running with `-- --trace-input` prints every mouse button Godot receives, for checking what a
mouse actually sends.
