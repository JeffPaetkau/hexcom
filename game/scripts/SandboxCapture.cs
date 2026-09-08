using System.Linq;
using Godot;

namespace Hexcom.Game;

/// <summary>
/// Renders a few frames, writes the viewport to a PNG and quits. Off unless asked for.
/// </summary>
/// <remarks>
/// <para>
/// The view territory's standing problem is that nobody can say a change was <i>seen</i> working
/// — the rules have tests and the drawing has nothing, so every claim about the sandbox has had
/// to be hedged down to "it typechecks". This closes that gap for anything a still picture can
/// settle, which is most of what goes wrong here: a scale error, a polygon inside out, a panel
/// off the edge of the screen.
/// </para>
/// <para>
/// Run it with the arguments Godot passes through after <c>--</c>:
/// </para>
/// <code>
/// godot --path game -- --shot out.png
/// </code>
/// <para>
/// Not with <c>--headless</c>. The headless driver does not rasterise, so the capture comes back
/// blank — a window has to open for there to be anything to save. The wait exists because the
/// first frame is drawn before the font atlas is resident, and a capture taken then loses every
/// label on the map.
/// </para>
/// </remarks>
public sealed class SandboxCapture
{
    private const string PathFlag = "--shot";
    private const string DelayFlag = "--shot-after";

    private readonly string _path;
    private int _framesLeft;

    private SandboxCapture(string path, int framesLeft)
    {
        _path = path;
        _framesLeft = framesLeft;
    }

    /// <summary>The capture this run was asked for, or null for an ordinary interactive run.</summary>
    public static SandboxCapture? Requested()
    {
        var args = OS.GetCmdlineUserArgs();

        var path = ValueOf(args, PathFlag);
        if (path is null) return null;

        var delay = ValueOf(args, DelayFlag);
        return new SandboxCapture(path, int.TryParse(delay, out var frames) ? frames : 4);
    }

    /// <summary>
    /// Called once a frame. Saves and quits when the wait is up; returns true on the frame it
    /// captured, so the caller can say so.
    /// </summary>
    public bool Tick(Node node)
    {
        if (_framesLeft-- > 0) return false;

        var image = node.GetViewport().GetTexture().GetImage();
        var error = image.SavePng(_path);

        GD.Print(error == Error.Ok
            ? $"captured {image.GetWidth()}x{image.GetHeight()} to {_path}"
            : $"capture to {_path} failed: {error}");

        node.GetTree().Quit(error == Error.Ok ? 0 : 1);
        return true;
    }

    /// <summary>Reads <c>--flag value</c> and <c>--flag=value</c>, because both get typed.</summary>
    private static string? ValueOf(string[] args, string flag)
    {
        var joined = args.FirstOrDefault(a => a.StartsWith(flag + "="));
        if (joined is not null) return joined[(flag.Length + 1)..];

        var index = System.Array.IndexOf(args, flag);
        return index >= 0 && index + 1 < args.Length ? args[index + 1] : null;
    }
}
