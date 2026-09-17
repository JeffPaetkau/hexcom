using Godot;
using Hexcom.Rules;

namespace Hexcom.Game;

/// <summary>
/// The world: an endless asphalt plain under an open sky with a sun, and the camera that looks
/// at it. Everything is built in code so that what is on screen is what the source says.
/// </summary>
/// <remarks>
/// The plain is one very large quad that follows the camera, textured by a shader in world
/// coordinates, so it never runs out and never swims. Fog the colour of the horizon takes the
/// far edge into the sky. Escape quits; that is a convenience for now, not a decision about
/// menus.
/// </remarks>
public partial class World : Node3D
{
    /// <summary>Metres the far plane extends each way from the focus. Well past where fog ends it.</summary>
    private const float PlainReach = 20000f;

    /// <summary>
    /// Where the far plane sits. It only shows beyond the eight kilometres of terrain mesh,
    /// deep in fog, and is kept below the hills so it never pokes through a valley before then.
    /// </summary>
    private const float FarPlaneHeight = -25f;

    private static readonly Color Horizon = new(0.72f, 0.79f, 0.90f);

    /// <summary>The landscape's seed. One number decides every hill.</summary>
    private const int Seed = 7;

    /// <summary>
    /// Where the unit stands at the start unless a capture says otherwise: beside the highway
    /// cutting, ten metres north of the bluff, so a run of the game opens on the ground that
    /// has every kind of step in it.
    /// </summary>
    private static readonly Hex Home = new(171, -66);

    private TacticalCamera _camera = null!;
    private MeshInstance3D _ground = null!;
    private ShaderMaterial _surface = null!;
    private Terrain _terrain = null!;
    private TerrainView _terrainView = null!;
    private Board _board = null!;
    private Capture? _capture;
    private bool _probed;

    public override void _Ready()
    {
        _capture = Capture.Requested();

        AddChild(BuildSky());
        AddChild(BuildSun(_capture?.Sun ?? DefaultSun));

        _terrain = new Terrain(Seed);
        _surface = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/terrain.gdshader") };
        _surface.SetShaderParameter("surface_map", TerrainView.BakeSurfaceMap(_terrain));
        _surface.SetShaderParameter("map_half_extent", (float)Terrain.MapHalfExtent);

        // The grid is never shown in play; --grid draws it for checking that the marks on the
        // board land where the rules think the hexes are. Its size comes from the rules, not
        // the shader default, so the two cannot drift apart.
        _surface.SetShaderParameter("hex_size", Units.HexSize);
        if (System.Array.IndexOf(OS.GetCmdlineUserArgs(), "--grid") >= 0)
        {
            // Faint enough that the marks on the hexes still read through it: a brighter grid
            // hides a see-through mark that fills a cell, because the eye reads the cell as
            // its own colour rather than as marked.
            _surface.SetShaderParameter("grid_strength", 0.25f);
        }

        _terrainView = new TerrainView(_terrain, _surface);
        AddChild(_terrainView);

        _ground = BuildGround();
        AddChild(_ground);

        _camera = new TacticalCamera
        {
            Terrain = _terrain,
            TraceInput = System.Array.IndexOf(OS.GetCmdlineUserArgs(), "--trace-input") >= 0,
        };
        AddChild(_camera);

        var hud = new Hud();
        AddChild(hud);

        _board = new Board
        {
            Camera = _camera,
            Hud = hud,
            Terrain = _terrain,
            Surface = _surface,
            AlwaysTrip = _capture?.Trip ?? false,
            PointerOverride = _capture?.Hover,
            Start = _capture?.UnitAt ?? Home,
        };
        AddChild(_board);

        // The camera opens over the unit; a capture may move it afterwards.
        var (homeX, homeZ) = _board.Start.Centre;
        _camera.Set(focus: new Vector2((float)homeX, (float)homeZ));
        _camera.Settle();
        hud.EndTurnPressed += _board.EndTurn;
        hud.ShowPortrait(_board.PieceMesh);

        _terrainView.Update(new Vector2(_camera.Focus.X, _camera.Focus.Z));
        PrintHeightsIfAsked();

        PlaceWindowOnLeftMonitor(_camera.TraceInput);

        if (_capture is { } capture)
        {
            // Controls stay on only when the capture is going to drive them itself.
            _camera.ControlsEnabled = capture.Drag is not null || capture.Orbit is not null;
            _camera.Set(capture.Focus, capture.YawDegrees, capture.PitchDegrees, capture.Distance);
            _camera.Settle();

            // A picture is always a 1600 by 900 window, whatever the monitor: captures are
            // compared with each other, and a 4K one is four times the file for the same check.
            SetWindowed();
        }
    }

    /// <summary>
    /// <c>--heights x0,z0,x1,z1</c> prints the ground along a line, for looking at the numbers
    /// behind something a picture cannot explain.
    /// </summary>
    private void PrintHeightsIfAsked()
    {
        var args = OS.GetCmdlineUserArgs();
        var at = System.Array.IndexOf(args, "--heights");
        if (at < 0 || at + 1 >= args.Length) return;

        var parts = args[at + 1].Split(',');
        if (parts.Length != 4) return;

        var culture = System.Globalization.CultureInfo.InvariantCulture;
        double x0 = double.Parse(parts[0], culture), z0 = double.Parse(parts[1], culture);
        double x1 = double.Parse(parts[2], culture), z1 = double.Parse(parts[3], culture);

        const int samples = 80;
        var text = new System.Text.StringBuilder();
        for (var i = 0; i <= samples; i++)
        {
            var t = (double)i / samples;
            var x = x0 + (x1 - x0) * t;
            var z = z0 + (z1 - z0) * t;
            text.Append(culture, $"{x:F1},{z:F1}: base {_terrain.BaseHeight(x, z):F2} ground {_terrain.Height(x, z):F2}\n");
        }
        GD.Print(text.ToString());
    }

    private void SetWindowed()
    {
        var window = GetWindow();
        window.Mode = Window.ModeEnum.Windowed;
        window.Size = new Vector2I(1600, 900);
        DisplayServer.WindowSetCurrentScreen(DisplayServer.WindowGetCurrentScreen());
    }

    public override void _Process(double delta)
    {
        var focus = _camera.Focus;
        _ground.Position = new Vector3(focus.X, FarPlaneHeight, focus.Z);
        _terrainView.Update(new Vector2(focus.X, focus.Z));

        if (_capture is { Orbit: not null } && !_probed)
        {
            _probed = true;
            GD.Print($"ground under probe before: {_camera.GroundUnder(Capture.ProbePoint(this))}");
        }

        if (_capture?.Tick(this, _board) == true)
        {
            GD.Print($"focus {_camera.Focus}; unit at {_board.Unit.Position} with {_board.Unit.Ap} AP; {_board.MarkCount} hexes marked");
            if (_capture.Orbit is not null) GD.Print($"ground under probe after: {_camera.GroundUnder(Capture.ProbePoint(this))}");
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        switch (@event)
        {
            case InputEventKey { Pressed: true, Echo: false, Keycode: Key.Escape }:
                GetTree().Quit();
                break;
            case InputEventKey { Pressed: true, Echo: false, Keycode: Key.F11 }:
                if (GetWindow().Mode == Window.ModeEnum.Windowed) GetWindow().Mode = Window.ModeEnum.Fullscreen;
                else SetWindowed();
                break;
        }
    }

    /// <summary>The earliest hook there is; with the trace on, anything that arrives at all is printed here.</summary>
    public override void _Input(InputEvent @event)
    {
        if (_camera.TraceInput && @event is InputEventMouseButton button)
        {
            GD.Print($"  raw {button.ButtonIndex} {(button.Pressed ? "down" : "up")} mask {button.ButtonMask}");
        }
    }

    private static WorldEnvironment BuildSky()
    {
        var sky = new ProceduralSkyMaterial
        {
            SkyTopColor = new Color(0.22f, 0.42f, 0.78f),
            SkyHorizonColor = Horizon,
            SkyCurve = 0.12f,
            // The sky's lower half is never seen directly, the plain covers it, but the fog
            // samples it through a blurred radiance map: a dark ground there bleeds a dark band
            // into the horizon. So it is the horizon colour all the way down.
            GroundBottomColor = Horizon,
            GroundHorizonColor = Horizon,
            SunAngleMax = 3f,
            SunCurve = 0.12f,
            UseDebanding = true,
        };

        var environment = new Godot.Environment
        {
            BackgroundMode = Godot.Environment.BGMode.Sky,
            Sky = new Sky { SkyMaterial = sky },
            AmbientLightSource = Godot.Environment.AmbientSource.Sky,
            AmbientLightSkyContribution = 1f,
            // Held down so the sun, not the blue sky, decides what colour the ground is.
            AmbientLightEnergy = 0.5f,
            ReflectedLightSource = Godot.Environment.ReflectionSource.Sky,
            TonemapMode = Godot.Environment.ToneMapper.Filmic,
            TonemapExposure = 1.15f,
            TonemapWhite = 6f,
            FogEnabled = true,
            FogLightColor = Horizon,
            FogDensity = 0.0005f,
            // Fog takes its colour entirely from the sky behind it, so the far plain meets the
            // horizon in exactly the sky's colour rather than a guess at it.
            FogAerialPerspective = 1f,
            FogSkyAffect = 0f,
            FogSunScatter = 0.1f,
        };

        return new WorldEnvironment { Environment = environment };
    }

    /// <summary>Where the sun sits: 38 degrees up, in the south-south-west (bearing 215). Low enough that hills shade.</summary>
    private static readonly Vector2 DefaultSun = new(38f, 215f);

    /// <param name="sun">Elevation above the horizon and compass bearing of the sun, degrees.</param>
    private static DirectionalLight3D BuildSun(Vector2 sun)
        => new()
        {
            // A light shines along its -Z. Pitch it down by the elevation, then turn it so the
            // light travels away from the bearing the sun is at.
            RotationDegrees = new Vector3(-sun.X, 180f - sun.Y, 0f),
            LightColor = new Color(1f, 0.96f, 0.90f),
            LightEnergy = 1.8f,
            LightAngularDistance = 0.5f,
            ShadowEnabled = true,
            DirectionalShadowMode = DirectionalLight3D.ShadowMode.Parallel4Splits,
            DirectionalShadowMaxDistance = 300f,
            ShadowBlur = 0.7f,
        };

    /// <summary>The flat plane that fills in past the terrain mesh, in the same surface so the horizon matches.</summary>
    private MeshInstance3D BuildGround()
        => new()
        {
            Name = "FarPlane",
            Mesh = new PlaneMesh { Size = new Vector2(PlainReach * 2f, PlainReach * 2f), Material = _surface },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };

    /// <summary>Open on the leftmost monitor, centred. The user works on the middle one.</summary>
    private static void PlaceWindowOnLeftMonitor(bool trace)
    {
        var count = DisplayServer.GetScreenCount();
        if (count < 2) return;

        var left = 0;
        for (var screen = 1; screen < count; screen++)
        {
            if (DisplayServer.ScreenGetPosition(screen).X < DisplayServer.ScreenGetPosition(left).X) left = screen;
        }

        if (trace)
        {
            for (var screen = 0; screen < count; screen++)
            {
                GD.Print($"screen {screen} at {DisplayServer.ScreenGetPosition(screen)} size {DisplayServer.ScreenGetSize(screen)}");
            }
            GD.Print($"window opened on screen {DisplayServer.WindowGetCurrentScreen()} as {DisplayServer.WindowGetMode()} "
                + $"size {DisplayServer.WindowGetSize()}; leftmost is {left}");
        }

        // Already there when the project settings put it there; the move is only a fallback for
        // a machine whose monitors are numbered differently.
        if (DisplayServer.WindowGetCurrentScreen() == left) return;

        DisplayServer.WindowSetCurrentScreen(left);
    }
}
