# Hexcom

Turn-based sci-fi squad tactics on a hex grid. Take 2: the interface is built first, piece by
piece, and the rules will be brought in to match it. Read [summary.md](summary.md) for what the
first approach learned.

## What exists

An endless asphalt plain under an open sky with a sun, and a tactical camera. No grid is
drawn yet; one world unit is one metre and the hex geometry the grid will use is noted in
[Units.cs](game/scripts/Units.cs).

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
focus, `--sun elevation,bearing` in degrees, `--shot-after N` frames to wait (default 8),
`--drag dx,dy` to feed a middle-button drag in pixels through the input pipeline first (the
console prints the focus it ends at).

Running with `-- --trace-input` prints every mouse button Godot receives, for checking what a
mouse actually sends.
