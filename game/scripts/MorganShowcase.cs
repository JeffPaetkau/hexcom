using System;
using System.Text.Json;
using Godot;
using Hexcom.Rules;

namespace Hexcom.Game;

/// <summary>
/// A showcase, not the game: Sgt. Alex Morgan on the game's own terrain, under its sky and sun. He
/// stands in the model's rest pose, eases into the reference image's pose, holds it, then walks a
/// loop and stops to stand at one end. Run it with
/// <c>Godot_v4.7.2-stable_mono_win64_console --path game res://scenes/Morgan.tscn</c>.
/// </summary>
/// <remarks>
/// <para>
/// The ground, sky and sun come from <see cref="World"/>'s own builders and the same terrain seed,
/// and the camera is the game's own <see cref="TacticalCamera"/> with the game's controls (WASD or
/// the arrows pan, Q and E turn, the wheel zooms, the middle button drags, the right button orbits,
/// the screen edges pan, Shift hurries). Two differences, both about him: the camera follows him
/// until you pan away, and Home or F, which recentre on the map's origin in the game, recentre on
/// him and follow again here. Keys 1 to 5 are presets around him (behind, front, side, close, the
/// game's default tactical height); the game does not use them. Escape quits, F11 toggles a window.
/// Nothing of the board, the HUD or the rules' units is here; World.tscn stays the main scene.
/// </para>
/// <para>
/// The model is <c>res://characters/morgan/morgan.glb</c>, written (with
/// <c>morgan_motion.json</c> beside it) by <c>art/characters/sgt_morgan/scripts/export_godot.py</c>;
/// the .glb is not committed. Its animations are Rest, Hero (static poses), Walk and Idle (in
/// place): this script moves him along the path at the speed the export measured for the walk, so a
/// planted foot stays planted, and sets him on the ground with <see cref="TerrainView.MeshHeight"/>.
/// He is scaled from his measured height in boots to the rules' standing man, 1.80 m.
/// </para>
/// <para>
/// A capture: <c>-- --shot out.png --view side --at 12</c> starts <c>--at</c> seconds after the
/// scene starts (the intro is the first <see cref="IntroSeconds"/>), waits <c>--shot-after</c>
/// frames (default 10), saves the viewport and quits. <c>--view</c> is follow, front, three, side,
/// close (a free camera that frames him exactly, for pictures) or tactical (the game's camera at its
/// default pitch and distance). With Godot's own <c>--write-movie out.avi --fixed-fps 30
/// --quit-after N</c> it records instead.
/// </para>
/// </remarks>
public partial class MorganShowcase : Node3D
{
    private const string ModelPath = "res://characters/morgan/morgan.glb";
    private const string MotionPath = "res://characters/morgan/morgan_motion.json";

    /// <summary>The rules' standing man (summary.md, physical constants).</summary>
    private const float RulesHeight = 1.80f;

    /// <summary>Length of each straight of the loop, metres.</summary>
    private const float Straight = 18f;

    /// <summary>Radius of the turn at each end, metres.</summary>
    private const float TurnRadius = 1.4f;

    /// <summary>Seconds he stands at the near end before turning and walking off again.</summary>
    private const float IdleSeconds = 5f;

    /// <summary>Seconds over which walk and idle hand over to each other.</summary>
    private const float Blend = 0.35f;

    /// <summary>The intro: the rest pose held, the move into the hero pose, the hero pose held, the step off.</summary>
    private const float RestHold = 1.5f, ToHero = 1.5f, HeroHold = 3f, ToWalk = 0.6f;

    private const float IntroSeconds = RestHold + ToHero + HeroHold;

    private Terrain _terrain = null!;
    private TerrainView _terrainView = null!;
    private MeshInstance3D _farPlane = null!;
    private Node3D _morgan = null!;
    private AnimationPlayer? _player;
    private Camera3D _camera = null!;
    private TacticalCamera _tactical = null!;

    private float _speed = 1.3f;
    private float _scale = 1f;
    private float _walkLength = 1f;
    private Vector2 _start, _along, _across;
    private float _t;
    private string _view = "follow";
    private bool _interactive;
    private bool _follow = true;
    private string _playing = "";
    private Vector3 _cameraAt;
    private bool _cameraPlaced;
    private Vector2 _at, _facing;

    private string? _shot;
    private int _shotAfter = 10;

    public override void _Ready()
    {
        var args = OS.GetCmdlineUserArgs();
        _shot = ValueOf(args, "--shot");
        _shotAfter = int.TryParse(ValueOf(args, "--shot-after"), out var after) ? after : 10;
        var view = ValueOf(args, "--view");
        _interactive = _shot is null && view is null;
        _view = view ?? "tactical";
        _t = float.TryParse(ValueOf(args, "--at"), System.Globalization.CultureInfo.InvariantCulture, out var at) ? at : 0f;

        AddChild(World.BuildSky());
        AddChild(World.BuildSun(World.DefaultSun));

        _terrain = new Terrain(World.Seed);
        var surface = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/terrain.gdshader") };
        surface.SetShaderParameter("surface_map", TerrainView.BakeSurfaceMap(_terrain));
        surface.SetShaderParameter("map_half_extent", (float)Terrain.MapHalfExtent);
        surface.SetShaderParameter("hex_size", Units.HexSize);
        _terrainView = new TerrainView(_terrain, surface);
        AddChild(_terrainView);
        _farPlane = new MeshInstance3D
        {
            Name = "FarPlane",
            Mesh = new PlaneMesh { Size = new Vector2(World.PlainReach * 2f, World.PlainReach * 2f), Material = surface },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };
        AddChild(_farPlane);

        ReadMotion();
        ChoosePath();

        var model = GD.Load<PackedScene>(ModelPath);
        if (model is null)
        {
            GD.PushError($"{ModelPath} is missing: run art/characters/sgt_morgan/scripts/export_godot.py (game/characters/morgan/README.md)");
            GetTree().Quit(1);
            return;
        }
        _morgan = model.Instantiate<Node3D>();
        _morgan.Scale = Vector3.One * _scale;
        AddChild(_morgan);
        _player = _morgan.FindChild("AnimationPlayer", true, false) as AnimationPlayer;
        if (_player is not null)
        {
            foreach (var name in _player.GetAnimationList())
            {
                _player.GetAnimation(name).LoopMode = Animation.LoopModeEnum.Linear;
            }
            if (_player.HasAnimation("Walk")) _walkLength = (float)_player.GetAnimation("Walk").Length;
            GD.Print($"animations: {string.Join(", ", _player.GetAnimationList())}");
        }
        else
        {
            GD.PushWarning("no AnimationPlayer in the model; he will glide");
        }

        // The game's camera, with the game's bindings; Home and F are taken over (see the remarks).
        Bindings.Ensure();
        InputMap.ActionEraseEvents(Bindings.Home);
        _camera = new Camera3D { Fov = 40f, Near = 0.05f, Far = 20000f };
        AddChild(_camera);
        _tactical = new TacticalCamera { Terrain = _terrain, ControlsEnabled = _interactive };
        AddChild(_tactical);

        Pose(0f, first: true);
        if (_interactive)
        {
            Preset(3);
            _tactical.Settle();
        }
        else UseView(_view);

        if (!_interactive || Array.IndexOf(OS.GetCmdlineArgs(), "--write-movie") >= 0)
        {
            var window = GetWindow();
            window.Mode = Window.ModeEnum.Windowed;
            if (_shot is not null) window.Size = new Vector2I(1600, 900);
        }
    }

    /// <summary>Speed and height from the export's record, with fallbacks so a bare .glb still runs.</summary>
    private void ReadMotion()
    {
        var height = 1.88f;
        if (FileAccess.FileExists(MotionPath))
        {
            using var doc = JsonDocument.Parse(FileAccess.GetFileAsString(MotionPath));
            var root = doc.RootElement;
            if (root.TryGetProperty("rest_height_m", out var h)) height = h.GetSingle();
            if (root.TryGetProperty("walk", out var walk) && walk.TryGetProperty("speed_mps", out var v)) _speed = v.GetSingle();
        }
        _scale = RulesHeight / height;
        _speed *= _scale;
        GD.Print($"Morgan: {height:F3} m in boots, scaled {_scale:F3} to {RulesHeight} m; walks at {_speed:F2} m/s");
    }

    /// <summary>
    /// The straightest, flattest stretch of paved road near the game's opening position, walked
    /// out on one side of the centreline and back on the other. Chosen from the terrain itself,
    /// so it is the same every run.
    /// </summary>
    private void ChoosePath()
    {
        var (hx, hz) = new Hex(171, -66).Centre;
        var home = new Vector2((float)hx, (float)hz);
        var best = float.MaxValue;
        var span = (int)Math.Ceiling((Straight + 2 * TurnRadius + 4f) / Road.Spacing);
        foreach (var road in _terrain.Roads)
        {
            if (!road.Paved) continue;
            var p = road.Points;
            for (var i = 0; i + span < p.Count; i++)
            {
                var a = new Vector2((float)p[i].X, (float)p[i].Z);
                var b = new Vector2((float)p[i + span].X, (float)p[i + span].Z);
                var bend = 0f;
                var rise = 0f;
                var low = float.MaxValue;
                var high = float.MinValue;
                for (var j = i; j <= i + span; j++)
                {
                    var q = new Vector2((float)p[j].X, (float)p[j].Z);
                    bend = Math.Max(bend, DistanceToLine(q, a, b));
                    var y = (float)_terrain.Height(q.X, q.Y);
                    low = Math.Min(low, y);
                    high = Math.Max(high, y);
                }
                rise = high - low;
                var score = bend * 4f + rise + a.DistanceTo(home) * 0.01f;
                if (score < best)
                {
                    best = score;
                    _along = (b - a).Normalized();
                    _across = new Vector2(-_along.Y, _along.X);
                    // The loop's two legs run either side of the centreline, a turn's radius out.
                    _start = a + _along * 2f - _across * TurnRadius;
                }
            }
        }
        GD.Print($"path from ({_start.X:F1}, {_start.Y:F1}) heading ({_along.X:F2}, {_along.Y:F2}); score {best:F2}");
    }

    private static float DistanceToLine(Vector2 q, Vector2 a, Vector2 b)
    {
        var d = (b - a).Normalized();
        var r = q - a;
        return Math.Abs(r.X * d.Y - r.Y * d.X);
    }

    /// <summary>The loop's legs in order: walk out, turn, walk back, stand, turn.</summary>
    private float[] Legs()
    {
        var straight = Straight / _speed;
        var turn = Mathf.Pi * TurnRadius / _speed;
        return new[] { straight, turn, straight, IdleSeconds, turn };
    }

    /// <summary>Where he is, which way he faces, and whether he walks, at time t into the loop.</summary>
    private (Vector2 At, Vector2 Facing, bool Walking, float WalkTime) StateAt(float t)
    {
        var legs = Legs();
        var cycle = 0f;
        foreach (var leg in legs) cycle += leg;
        var loops = Mathf.Floor(t / cycle);
        var u = t - loops * cycle;
        var walkPerLoop = cycle - IdleSeconds;
        var walked = loops * walkPerLoop;

        var a = _start;
        var b = _start + _along * Straight;
        var aBack = a + _across * 2f * TurnRadius;
        var bBack = b + _across * 2f * TurnRadius;

        if (u < legs[0])
        {
            var s = u * _speed;
            return (a + _along * s, _along, true, walked + u);
        }
        u -= legs[0];
        walked += legs[0];
        if (u < legs[1])
        {
            var angle = u * _speed / TurnRadius;
            var centre = b + _across * TurnRadius;
            var from = -_across;
            var at = centre + Rotate(from, angle) * TurnRadius;
            return (at, Rotate(_along, angle), true, walked + u);
        }
        u -= legs[1];
        walked += legs[1];
        if (u < legs[2])
        {
            var s = u * _speed;
            return (bBack - _along * s, -_along, true, walked + u);
        }
        u -= legs[2];
        walked += legs[2];
        if (u < legs[3])
        {
            return (aBack, -_along, false, walked);
        }
        u -= legs[3];
        {
            var angle = u * _speed / TurnRadius;
            var centre = a + _across * TurnRadius;
            var from = _across;
            var at = centre + Rotate(from, angle) * TurnRadius;
            return (at, Rotate(-_along, angle), true, walked + u);
        }
    }

    /// <summary>Turns v by angle radians, the way that takes <see cref="_along"/> towards <see cref="_across"/>.</summary>
    private Vector2 Rotate(Vector2 v, float angle)
    {
        var sign = _along.X * _across.Y - _along.Y * _across.X >= 0 ? 1f : -1f;
        return v.Rotated(sign * angle);
    }

    public override void _Process(double delta)
    {
        if (_morgan is null) return;
        _t += (float)delta;
        Pose((float)delta, first: false);

        if (_shot is not null && _shotAfter-- <= 0)
        {
            var image = GetViewport().GetTexture().GetImage();
            var error = image.SavePng(_shot);
            GD.Print(error == Error.Ok ? $"captured {image.GetWidth()}x{image.GetHeight()} to {_shot} at t={_t:F2}" : $"capture failed: {error}");
            GetTree().Quit(error == Error.Ok ? 0 : 1);
            _shot = null;
        }
    }

    /// <summary>
    /// What he does at time t since the start: the intro (rest, into the hero pose, hold) at the
    /// loop's start, then the loop. The animation, how long to blend into it, and where in it to be.
    /// </summary>
    private (Vector2 At, Vector2 Facing, string Animation, float Seek) Schedule(float t)
    {
        if (t < IntroSeconds)
        {
            var (at0, facing0, _, _) = StateAt(0f);
            return (at0, facing0, t < RestHold ? "Rest" : "Hero", 0f);
        }
        var (at, facing, walking, walkTime) = StateAt(t - IntroSeconds);
        return (at, facing, walking ? "Walk" : "Idle", walking ? walkTime % _walkLength : 0f);
    }

    private float BlendInto(string from, string to)
        => (from, to) switch
        {
            ("Rest", "Hero") => ToHero,
            ("Hero", _) => ToWalk,
            _ => Blend,
        };

    private void Pose(float delta, bool first)
    {
        var (at, facing, wanted, seek) = Schedule(_t);
        _at = at;
        _facing = facing;
        var y = TerrainView.MeshHeight(_terrain, at.X, at.Y);
        _morgan.Position = new Vector3(at.X, y, at.Y);
        // The model faces its +Z (glTF from Blender's -Y); turn +Z onto the facing.
        _morgan.Rotation = new Vector3(0f, Mathf.Atan2(facing.X, facing.Y), 0f);

        if (_player is not null && _player.HasAnimation(wanted) && wanted != _playing)
        {
            _player.Play(wanted, first ? 0f : BlendInto(_playing, wanted));
            if (first) _player.Seek(seek, true);
            _playing = wanted;
        }

        _farPlane.Position = new Vector3(at.X, World.FarPlaneHeight, at.Y);
        _terrainView.Update(at);

        if (_interactive)
        {
            if (Panned()) _follow = false;
            if (_follow && !_tactical.Dragging) _tactical.Set(focus: at);
        }
        else
        {
            PlaceCamera(at, y, facing, delta, first);
        }
    }

    /// <summary>Whether the player is panning the game camera (keys, middle drag or a screen edge), which ends following.</summary>
    private bool Panned()
    {
        if (Input.GetVector(Bindings.Left, Bindings.Right, Bindings.Back, Bindings.Forward) != Vector2.Zero) return true;
        if (Input.IsMouseButtonPressed(MouseButton.Middle)) return true;
        if (!GetWindow().HasFocus()) return false;
        var mouse = GetViewport().GetMousePosition();
        var size = GetViewport().GetVisibleRect().Size;
        const float edge = 8f;
        return mouse.X >= 0 && mouse.Y >= 0 && mouse.X <= size.X && mouse.Y <= size.Y
            && (mouse.X < edge || mouse.Y < edge || mouse.X > size.X - edge || mouse.Y > size.Y - edge);
    }

    /// <summary>The game camera's bearing (zero north, clockwise) for looking along a ground direction.</summary>
    private static float Bearing(Vector2 look) => Mathf.RadToDeg(Mathf.Atan2(look.X, -look.Y));

    /// <summary>Keys 1 to 5: behind, front, side, close, the game's default; all centred on him, following.</summary>
    private void Preset(int key)
    {
        var f = _facing;
        var side = new Vector2(-f.Y, f.X);
        var (look, pitch, distance) = key switch
        {
            1 => (f, 20f, 8f),
            2 => (-f, TacticalCamera.LowestPitchDegrees, 6f),
            3 => ((-f + side * 0.7f).Normalized(), 16f, 7f),
            4 => (-f, TacticalCamera.LowestPitchDegrees, TacticalCamera.Closest),
            _ => (f, TacticalCamera.DefaultPitchDegrees, TacticalCamera.DefaultDistance),
        };
        _follow = true;
        _tactical.Set(focus: _at, yawDegrees: Bearing(look), pitchDegrees: pitch, distance: distance);
    }

    /// <summary>The free camera used for pictures and movies: fixed to him, low and close where the game camera cannot go.</summary>
    private void PlaceCamera(Vector2 at, float y, Vector2 facing, float delta, bool first)
    {
        var body = new Vector3(at.X, y, at.Y);
        var forward = new Vector3(facing.X, 0f, facing.Y);
        var right = forward.Cross(Vector3.Up);
        Vector3 eye, look;
        switch (_view)
        {
            case "front":
                eye = body + forward * 5f + Vector3.Up * 1.3f;
                look = body + Vector3.Up * 0.95f;
                break;
            case "three":
                eye = body + forward * 4.2f + right * 2.6f + Vector3.Up * 1.45f;
                look = body + Vector3.Up * 0.95f;
                break;
            case "side":
                eye = body - right * 5f + Vector3.Up * 1.2f;
                look = body + Vector3.Up * 0.95f;
                break;
            case "feet":
                eye = body - right * 2.6f + Vector3.Up * 0.45f;
                look = body + Vector3.Up * 0.3f;
                break;
            case "feet_front":
                eye = body + forward * 2.6f + Vector3.Up * 0.45f;
                look = body + Vector3.Up * 0.3f;
                break;
            case "close":
                eye = body + forward * 1.7f - right * 0.7f + Vector3.Up * 1.55f;
                look = body + Vector3.Up * 1.35f;
                break;
            case "tactical":
                _tactical.Set(focus: at, yawDegrees: Bearing(-_along),
                    pitchDegrees: TacticalCamera.DefaultPitchDegrees, distance: TacticalCamera.DefaultDistance);
                _tactical.Settle();
                return;
            default:
                eye = body - forward * 4.5f - right * 1.8f + Vector3.Up * 1.9f;
                look = body + Vector3.Up * 1.1f;
                break;
        }

        // The follow view trails, so a turn reads as a turn; the others stay fixed to him.
        if (_view == "follow" && _cameraPlaced && !first)
        {
            _cameraAt = _cameraAt.Lerp(eye, 1f - Mathf.Exp(-2.5f * delta));
        }
        else
        {
            _cameraAt = eye;
            _cameraPlaced = true;
        }
        var ground = TerrainView.MeshHeight(_terrain, _cameraAt.X, _cameraAt.Z) + 0.2f;
        if (_cameraAt.Y < ground) _cameraAt.Y = ground;
        _camera.LookAtFromPosition(_cameraAt, look, Vector3.Up);
    }

    private void UseView(string view)
    {
        _view = view;
        _cameraPlaced = false;
        if (view == "tactical")
        {
            foreach (var child in _tactical.GetChildren())
            {
                if (child is Camera3D camera) camera.MakeCurrent();
            }
        }
        else
        {
            _camera.MakeCurrent();
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is not InputEventKey { Pressed: true, Echo: false } key) return;
        switch (key.PhysicalKeycode != Key.None ? key.PhysicalKeycode : key.Keycode)
        {
            case Key.Escape: GetTree().Quit(); break;
            case Key.F11:
                var window = GetWindow();
                if (window.Mode == Window.ModeEnum.Windowed) window.Mode = Window.ModeEnum.Fullscreen;
                else { window.Mode = Window.ModeEnum.Windowed; window.Size = new Vector2I(1600, 900); }
                break;
            case Key.Home:
            case Key.F:
                if (_interactive) { _follow = true; _tactical.Set(focus: _at); }
                break;
            case Key.Key1: if (_interactive) Preset(1); break;
            case Key.Key2: if (_interactive) Preset(2); break;
            case Key.Key3: if (_interactive) Preset(3); break;
            case Key.Key4: if (_interactive) Preset(4); break;
            case Key.Key5: if (_interactive) Preset(5); break;
        }
    }

    private static string? ValueOf(string[] args, string flag)
    {
        var at = Array.IndexOf(args, flag);
        return at >= 0 && at + 1 < args.Length ? args[at + 1] : null;
    }
}
