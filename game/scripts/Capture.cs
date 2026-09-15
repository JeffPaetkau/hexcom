using System;
using Godot;
using Hexcom.Game.Rules;

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
/// cursor on a ground point, <c>--move q,r</c> orders the unit to a hex and waits for the
/// walk, and <c>--end-turn</c> presses the button after it. <c>--shot-after N</c> waits N
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

    /// <summary>A point on the ground to treat as the cursor, so the hover marks can be pictured.</summary>
    public Vector2? Hover { get; private init; }

    /// <summary>A hex to order the unit to before the picture; the capture waits for the walk.</summary>
    public Hex? Move { get; private init; }

    /// <summary>Whether to press End Turn after any move, before the picture.</summary>
    public bool EndTurn { get; private init; }

    private bool _dragged, _moved, _endedTurn;

    /// <summary>The capture this run was asked for, or null for an ordinary interactive run.</summary>
    public static Capture? Requested()
    {
        var args = OS.GetCmdlineUserArgs();

        var path = ValueOf(args, "--shot");
        if (path is null) return null;

        return new Capture(path, IntOf(args, "--shot-after") ?? 8)
        {
            Focus = PairOf(args, "--focus"),
            YawDegrees = FloatOf(args, "--yaw"),
            PitchDegrees = FloatOf(args, "--pitch"),
            Distance = FloatOf(args, "--zoom"),
            Sun = PairOf(args, "--sun"),
            Drag = PairOf(args, "--drag"),
            Hover = PairOf(args, "--hover"),
            Move = PairOf(args, "--move") is { } hex ? new Hex((int)hex.X, (int)hex.Y) : null,
            EndTurn = Array.IndexOf(args, "--end-turn") >= 0,
        };
    }

    /// <summary>Called once a frame. Saves and quits when the wait is up; true on the frame it did.</summary>
    public bool Tick(Node node, Board board)
    {
        // Orders go in first and the countdown waits for the walk to finish.
        if (board.Busy) return false;

        if (Move is { } target && !_moved)
        {
            _moved = true;
            if (!board.OrderTo(target)) GD.Print($"move to {target} refused");
            return false;
        }

        if (EndTurn && !_endedTurn)
        {
            _endedTurn = true;
            board.EndTurn();
        }

        if (Drag is { } drag && !_dragged && _framesLeft <= 4)
        {
            _dragged = true;
            SimulateDrag(node, drag);
        }

        if (_framesLeft-- > 0) return false;

        var image = node.GetViewport().GetTexture().GetImage();
        var error = image.SavePng(_path);

        GD.Print(error == Error.Ok
            ? $"captured {image.GetWidth()}x{image.GetHeight()} to {_path}"
            : $"capture to {_path} failed: {error}");

        node.GetTree().Quit(error == Error.Ok ? 0 : 1);
        return true;
    }

    private static void SimulateDrag(Node node, Vector2 drag)
    {
        var from = node.GetViewport().GetVisibleRect().Size / 2f;
        const int steps = 8;

        Input.ParseInputEvent(new InputEventMouseButton
        {
            ButtonIndex = MouseButton.Middle, Pressed = true, Position = from, GlobalPosition = from,
        });

        for (var step = 1; step <= steps; step++)
        {
            var at = from + drag * step / steps;
            Input.ParseInputEvent(new InputEventMouseMotion
            {
                Position = at, GlobalPosition = at, Relative = drag / steps, ButtonMask = MouseButtonMask.Middle,
            });
        }

        Input.ParseInputEvent(new InputEventMouseButton
        {
            ButtonIndex = MouseButton.Middle, Pressed = false, Position = from + drag, GlobalPosition = from + drag,
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

    private static Vector2? PairOf(string[] args, string flag)
    {
        var parts = ValueOf(args, flag)?.Split(',');
        if (parts is not { Length: 2 }) return null;

        var culture = System.Globalization.CultureInfo.InvariantCulture;
        return float.TryParse(parts[0], culture, out var x) && float.TryParse(parts[1], culture, out var z)
            ? new Vector2(x, z)
            : null;
    }
}
