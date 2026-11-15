# Sgt. Alex Morgan in Godot (first look)

A showcase of the soldier model from `art/characters/sgt_morgan/` walking on the game's terrain.
It is not wired into the game: `scenes/World.tscn` is still the main scene and runs as before.

## Files

| File | What | In git |
|---|---|---|
| `morgan.glb` | the soldier: Morgan.Rig (MPFB default, 163 bones), one skinned mesh per part, baked textures, the `Walk` and `Idle` animations | no (regenerated) |
| `morgan_motion.json` | the export's record: walk speed, clip frames, measured height, triangle count | no (regenerated) |
| `../../scenes/Morgan.tscn`, `../../scripts/MorganShowcase.cs` | the showcase scene | yes |

## Regenerate the model

From `art/characters/sgt_morgan/` in Git Bash (needs `cache/assembled.blend`, built by
`scripts/assemble.py`; the CMU clips download themselves into `assets/mocap/cmu/` the first time):

```bash
source cache/env.sh
"$SGT_BLENDER" -b --python scripts/export_godot.py -- --stage all
```

Add `--src <copy>.blend` to export from a snapshot while other agents rebuild the parts.
`--stage mesh` (about 18 to 22 minutes on the RTX 3050: strip, decimate, bake) and `--stage anim` (about a
minute: retarget, export) can be run separately; see the script's docstring and
`scripts/export_godot.md` for what it simplifies and what is wrong.

## Run

Build the C# first (Godot loads the assembly from `.godot/mono/temp/bin/`), import the new .glb once,
then run the scene:

```bash
GODOT="$LOCALAPPDATA/Microsoft/WinGet/Packages/GodotEngine.GodotEngine.Mono_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe"
cd game
dotnet build Hexcom.Game.csproj
"$GODOT" --headless --path . --import
"$GODOT" --path . res://scenes/Morgan.tscn
```

It opens borderless full-screen like the game (F11 is not wired here; Escape quits). Keys 1 to 5
switch the view: follow, front, side, close, tactical (the game's camera at its default pitch and
distance). He walks 18 m along the straightest, flattest stretch of paved road near the game's
opening position, turns, walks back, stands for five seconds, turns, and repeats.

Captures and a movie (a window opens; the harness cannot render headless):

```bash
"$GODOT" --path . res://scenes/Morgan.tscn -- --shot side.png --view side --at 4
"$GODOT" --path . res://scenes/Morgan.tscn --windowed \
    --write-movie morgan.avi --fixed-fps 30 --quit-after 1240 -- --view follow
ffmpeg -i morgan.avi -c:v libx264 -crf 22 -pix_fmt yuv420p morgan.mp4
```

`--at` starts the loop that many seconds in; `--shot-after N` waits N frames before saving (10).

## Running it from Windows PowerShell (5.1)

PowerShell 5.1 has no `&&` and no `$GODOT`; use:

```powershell
$godot = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\GodotEngine.GodotEngine.Mono_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64.exe"
cd E:\hexcom\game
dotnet build
& $godot --path . res://scenes/Morgan.tscn
```

If Godot reports missing imports (after a fresh export), run `& $godot --headless --path . --import`
once first. Keys 1-5: follow, front, side, close, tactical camera; Escape quits.
