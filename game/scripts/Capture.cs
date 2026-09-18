using System;
using System.Collections.Generic;
using Godot;
using Hexcom.Rules;

namespace Hexcom.Game;

/// <summary>
/// Renders a few frames, writes the viewport to a PNG and quits. Off unless asked for.
/// </summary>
/// <remarks>
/// <para>
/// The interface is the only view into how this project is going, so every change to it needs
/// a picture rather than a claim. Run with the arguments Godot passes through after <c>--</c>:
/// </para>
/// <code>
/// Godot_v4.7.2-stable_mono_win64_console --path game -- --shot out.png
/// Godot_v4.7.2-stable_mono_win64_console --path game -- --shot low.png --pitch 15 --zoom 30 --yaw 60
/// </code>
/// <para>
/// <c>--focus x,z</c>, <c>--yaw</c> and <c>--pitch</c> (degrees) and <c>--zoom</c> (metres back
/// from the focus) set the camera, which lands there at once rather than easing.
/// <c>--sun elevation,bearing</c> moves the sun for the run. <c>--hover x,z</c> puts the
/// cursor on a ground point, <c>--face q,r</c> turns the unit to face a hex and waits for the
/// turn, <c>--move q,r</c> orders the unit to a hex and waits for the
/// walk, <c>--enemy q,r</c> puts the enemy on a hex, <c>--fire N</c> fires N shots at him after
/// the move (<c>--sure</c> makes every shot hit and <c>--miss</c> every shot miss), and
/// <c>--end-turn</c> passes the turn after that. <c>--play "fire end end fire"</c> gives the
/// orders in any order, a step per word: <c>face:q,r</c>, <c>move:q,r</c>, <c>fire</c> or
/// <c>end</c>; each is waited for. <c>--shot-after N</c> waits N
/// frames at the end, default eight, so the sky and shadows have settled. Not with <c>--headless</c>: the headless driver does not rasterise, so a window has
/// to open for there to be anything to save.
/// </para>
/// </remarks>
public sealed class Capture
{
    private readonly string _path;
    private int _framesLeft;

    private Capture(string path, int framesLeft)
    {
        _path = path;
        _framesLeft = framesLeft;
    }

    public Vector2? Focus { get; private init; }
    public float? YawDegrees { get; private init; }
    public float? PitchDegrees { get; private init; }
    public float? Distance { get; private init; }

    /// <summary>Sun elevation and bearing in degrees, or null for the world's default.</summary>
    public Vector2? Sun { get; private init; }

    /// <summary>
    /// A middle-button drag in pixels from the centre of the screen, fed through the input
    /// pipeline before the picture is taken, so the mouse pan can be exercised without a hand
    /// on the mouse. Null for none.
    /// </summary>
    public Vector2? Drag { get; private init; }

    /// <summary>
    /// A right-button drag in pixels, from <see cref="ProbePoint"/>, fed through the input
    /// pipeline before the picture: the ground under that point should not move.
    /// </summary>
    public Vector2? Orbit { get; private init; }

    /// <summary>Where an orbit starts on screen: off centre, so pinning is distinguishable from turning about the focus.</summary>
    public static Vector2 ProbePoint(Node node) => node.GetViewport().GetVisibleRect().Size / 2f + new Vector2(300f, 150f);

    /// <summary>A point on the ground to treat as the cursor, so the hover marks can be pictured.</summary>
    public Vector2? Hover { get; private init; }

    /// <summary>A hex to put our unit on at the start, for picturing reach on chosen ground.</summary>
    public Hex? UnitAt { get; private init; }

    /// <summary>A hex to put the enemy on at the start.</summary>
    public Hex? EnemyAt { get; private init; }

    /// <summary>A roll to use for every shot, so a hit (0) or a miss (1) can be pictured without luck. Null throws the dice.</summary>
    public double? ShotRoll { get; private init; }

    /// <summary>Frames into a walk or a shot to take the picture instead of waiting for it to end, or null to wait.</summary>
    public int? MidWalk { get; private init; }

    /// <summary>Whether every hurried step falls, so a fall can be pictured without luck.</summary>
    public bool Trip { get; private init; }

    private bool _dragged, _orbited;
    private int _busyFrames;

    /// <summary>The orders still to give, in order: <c>move:q,r</c>, <c>fire</c> or <c>end</c>.</summary>
    private readonly Queue<string> _steps = new();

    /// <summary>The capture this run was asked for, or null for an ordinary interactive run.</summary>
    public static Capture? Requested()
    {
        var args = OS.GetCmdlineUserArgs();

        var path = ValueOf(args, "--shot");
        if (path is null) return null;

        var capture = new Capture(path, IntOf(args, "--shot-after") ?? 8)
        {
            Focus = PairOf(args, "--focus"),
            YawDegrees = FloatOf(args, "--yaw"),
            PitchDegrees = FloatOf(args, "--pitch"),
            Distance = FloatOf(args, "--zoom"),
            Sun = PairOf(args, "--sun"),
            Drag = PairOf(args, "--drag"),
            Orbit = PairOf(args, "--orbit"),
            Hover = PairOf(args, "--hover"),
            UnitAt = PairOf(args, "--unit") is { } start ? new Hex((int)start.X, (int)start.Y) : null,
            EnemyAt = PairOf(args, "--enemy") is { } enemy ? new Hex((int)enemy.X, (int)enemy.Y) : null,
            ShotRoll = Array.IndexOf(args, "--sure") >= 0 ? 0.0 : Array.IndexOf(args, "--miss") >= 0 ? 1.0 : null,
            MidWalk = IntOf(args, "--mid-walk"),
            Trip = Array.IndexOf(args, "--trip") >= 0,
        };

        // The short flags are the common script, a turn to face somewhere, a move, some shots
        // and an end of turn, in that order; --play spells out any other order, a step per word.
        if (ValueOf(args, "--face") is { } face) capture._steps.Enqueue($"face:{face}");
        if (ValueOf(args, "--move") is { } move) capture._steps.Enqueue($"move:{move}");
        for (var shots = IntOf(args, "--fire") ?? 0; shots > 0; shots--) capture._steps.Enqueue("fire");
        if (Array.IndexOf(args, "--end-turn") >= 0) capture._steps.Enqueue("end");
        foreach (var step in (ValueOf(args, "--play") ?? "").Split(' ', StringSplitOptions.RemoveEmptyEntries)) capture._steps.Enqueue(step);

        return capture;
    }

    /// <summary>Called once a frame. Saves and quits when the wait is up; true on the frame it did.</summary>
    public bool Tick(Node node, Board board)
    {
        // Orders go in one at a time and the countdown waits for each to finish, unless the
        // picture is wanted so many frames into an animation itself.
        if (board.Busy)
        {
            return MidWalk is { } mid && ++_busyFrames >= mid && Shoot(node);
        }

        if (_steps.TryDequeue(out var step))
        {
            Play(step, board);
            return false;
        }

        if (Drag is { } drag && !_dragged && _framesLeft <= 4)
        {
            _dragged = true;
            SimulateDrag(node, drag, MouseButton.Middle, node.GetViewport().GetVisibleRect().Size / 2f);
        }

        if (Orbit is { } orbit && !_orbited && _framesLeft <= 4)
        {
            _orbited = true;
            SimulateDrag(node, orbit, MouseButton.Right, ProbePoint(node));
        }

        if (_framesLeft-- > 0) return false;

        return Shoot(node);
    }

    /// <summary>One step of the script: a move to a hex, a shot at the enemy, or the end of the turn.</summary>
    private static void Play(string step, Board board)
    {
        if (step == "end") board.EndTurn();
        else if (step == "fire") { if (!board.FireAtEnemy()) GD.Print("shot refused"); }
        else if (step.StartsWith("move:") && PairIn(step[5..]) is { } hex)
        {
            var target = new Hex((int)hex.X, (int)hex.Y);
            if (!board.OrderTo(target)) GD.Print($"move to {target} refused");
        }
        else if (step.StartsWith("face:") && PairIn(step[5..]) is { } toward)
        {
            var target = new Hex((int)toward.X, (int)toward.Y);
            if (!board.FaceToward(target)) GD.Print($"turn to face {target} refused");
        }
        else GD.Print($"unknown step {step}");
    }

    /// <summary>Save the viewport and quit; always true, for the caller's convenience.</summary>
    private bool Shoot(Node node)
    {
        var image = node.GetViewport().GetTexture().GetImage();
        var error = image.SavePng(_path);

        GD.Print(error == Error.Ok
            ? $"captured {image.GetWidth()}x{image.GetHeight()} to {_path}"
            : $"capture to {_path} failed: {error}");

        node.GetTree().Quit(error == Error.Ok ? 0 : 1);
        return true;
    }

    private static void SimulateDrag(Node node, Vector2 drag, MouseButton button, Vector2 from)
    {
        const int steps = 8;
        var mask = button == MouseButton.Right ? MouseButtonMask.Right : MouseButtonMask.Middle;

        Input.ParseInputEvent(new InputEventMouseButton
        {
            ButtonIndex = button, Pressed = true, Position = from, GlobalPosition = from,
        });

        for (var step = 1; step <= steps; step++)
        {
            var at = from + drag * step / steps;
            Input.ParseInputEvent(new InputEventMouseMotion
            {
                Position = at, GlobalPosition = at, Relative = drag / steps, ButtonMask = mask,
            });
        }

        Input.ParseInputEvent(new InputEventMouseButton
        {
            ButtonIndex = button, Pressed = false, Position = from + drag, GlobalPosition = from + drag,
        });
    }

    private static string? ValueOf(string[] args, string flag)
    {
        var at = Array.IndexOf(args, flag);
        return at >= 0 && at + 1 < args.Length ? args[at + 1] : null;
    }

    private static float? FloatOf(string[] args, string flag)
        => float.TryParse(ValueOf(args, flag), System.Globalization.CultureInfo.InvariantCulture, out var value) ? value : null;

    private static int? IntOf(string[] args, string flag)
        => int.TryParse(ValueOf(args, flag), out var value) ? value : null;

    private static Vector2? PairOf(string[] args, string flag) => PairIn(ValueOf(args, flag));

    private static Vector2? PairIn(string? value)
    {
        var parts = value?.Split(',');
        if (parts is not { Length: 2 }) return null;

        var culture = System.Globalization.CultureInfo.InvariantCulture;
        return float.TryParse(parts[0], culture, out var x) && float.TryParse(parts[1], culture, out var z)
            ? new Vector2(x, z)
            : null;
    }
}
