# Sgt. Alex Morgan in Godot (first look)

A showcase of the soldier model from `art/characters/sgt_morgan/` walking on the game's terrain.
It is not wired into the game: `scenes/World.tscn` is still the main scene and runs as before.

## Files

| File | What | In git |
|---|---|---|
| `morgan.glb` | the soldier: Morgan.Rig (MPFB default, 163 bones), one skinned mesh per part, baked textures, the `Rest` and `Hero` poses and the `Walk` and `Idle` animations | no (regenerated) |
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

It opens borderless full-screen like the game (F11 toggles a window; Escape quits).

What happens: he stands in the model's rest pose (MPFB's A-pose, the carbine in his right hand),
eases over 1.5 s into the reference image's pose (`hero_pose.json`, the carbine in both hands),
holds it for 3 s, steps off into the walk, walks 18 m along the straightest, flattest stretch of
paved road near the game's opening position, turns, walks back, stands for five seconds, turns,
and repeats.

The camera is the game's own, with the game's controls: WASD or the arrows pan, Q and E turn,
the mouse wheel zooms, the middle button drags the ground, the right button orbits, the screen
edges pan, Shift hurries. It follows him until you pan away; Home or F (which recentre on the
map's origin in the game) recentre on him and follow again. Keys 1 to 5 (not used by the game)
are presets around him: behind, front, three-quarter front (the opening view), close, and the
game's default tactical height (55 degrees, 40 m).

Captures and a movie (a window opens; the harness cannot render headless):

```bash
"$GODOT" --path . res://scenes/Morgan.tscn -- --shot side.png --view side --at 4
"$GODOT" --path . res://scenes/Morgan.tscn --windowed \
    --write-movie morgan.avi --fixed-fps 30 --quit-after 1420 -- --view follow
ffmpeg -i morgan.avi -c:v libx264 -crf 22 -pix_fmt yuv420p morgan.mp4
```

`--at` jumps that many seconds after the start (the intro is the first 6 s); `--shot-after N` waits
N frames before saving (10). `--view` picks a free camera fixed to him for pictures (follow, front,
three, side, close, feet, feet_front) or `tactical`, the game camera at its default height. Without
`--view` and `--shot` the game camera and its controls are live, as in an ordinary run.

## Running it from Windows PowerShell (5.1)

PowerShell 5.1 has no `&&` and no `$GODOT`; use:

```powershell
$godot = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\GodotEngine.GodotEngine.Mono_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64.exe"
cd E:\hexcom\game
dotnet build
& $godot --path . res://scenes/Morgan.tscn
```

If Godot reports missing imports (after a fresh export), run `& $godot --headless --path . --import`
once first. The game's camera controls work as in the game (see Run above); F or Home recentres on
him, keys 1-5 are presets (behind, front, three-quarter, close, tactical); Escape quits.
