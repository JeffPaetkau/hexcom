using System.Linq;
using Godot;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;

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
/// Godot_v4.7.2-stable_mono_win64_console --path game -- --shot out.png
/// Godot_v4.7.2-stable_mono_win64_console --path game -- --shot out.png --hover 4,2 --pass 3 --ai
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
    private const string HoverFlag = "--hover";
    private const string PassFlag = "--pass";
    private const string AiFlag = "--ai";

    private readonly string _path;
    private int _framesLeft;

    private SandboxCapture(string path, int framesLeft, NodeId? hover, int passes, bool automatic)
    {
        _path = path;
        _framesLeft = framesLeft;
        Hover = hover;
        Passes = passes;
        Automatic = automatic;
    }

    /// <summary>
    /// Where to put the cursor for the capture, if anywhere.
    /// </summary>
    /// <remarks>
    /// A capture is deaf, deliberately — the window opens under whatever the pointer was already
    /// doing, so a run that read the real mouse would not reproduce. That kept the whole
    /// cursor-driven half of the HUD out of every picture ever taken: the path preview, the sight
    /// readout, the shot under the cursor and what it is worth are all hover-only, and so none of
    /// them could be checked the way the rest of the drawing can. Naming the node on the command
    /// line gets them into the frame while keeping the run reproducible, which is the whole
    /// bargain — the cursor is now an argument rather than an accident.
    /// </remarks>
    public NodeId? Hover { get; }

    /// <summary>
    /// How many turns to hand straight on before the picture is taken.
    /// </summary>
    /// <remarks>
    /// Nobody has done anything after the passes — the sandbox drives both sides by hand and a
    /// capture has no hands — so this reaches later soldiers, not later situations. That is
    /// enough for most of what a still has to settle, because whose turn it is decides most of
    /// the HUD: the demo's scout carries a blade and can therefore never produce a shot readout
    /// at all, and one pass of the turn brings up somebody holding a rifle. Anything that needs
    /// the battle to have actually <i>moved</i> wants a scripted scenario, which is a different
    /// and larger thing.
    /// </remarks>
    public int Passes { get; }

    /// <summary>
    /// Whether the hostile side takes its own turns, through <c>Commander</c>, during the passes.
    /// </summary>
    /// <remarks>
    /// Without this a pass hands every turn on untouched, whoever holds it, and the picture can
    /// only ever show the opening deployment from a later soldier's point of view. With it each
    /// pass is one of <em>ours</em> standing still while the other side does whatever it decides
    /// to, which is the first way a capture has had of showing a situation rather than a
    /// starting position — and the only way of putting the enemy's reasoning in a picture, since
    /// the orders it chose are what the HUD prints. Entry 009 in <c>docs/decisions.md</c>.
    /// </remarks>
    public bool Automatic { get; }

    /// <summary>The capture this run was asked for, or null for an ordinary interactive run.</summary>
    public static SandboxCapture? Requested()
    {
        var args = OS.GetCmdlineUserArgs();

        var path = ValueOf(args, PathFlag);
        if (path is null) return null;

        var delay = ValueOf(args, DelayFlag);
        var passes = ValueOf(args, PassFlag);

        return new SandboxCapture(
            path,
            int.TryParse(delay, out var frames) ? frames : 4,
            ParseNode(ValueOf(args, HoverFlag)),
            int.TryParse(passes, out var turns) ? turns : 0,
            args.Contains(AiFlag));
    }

    /// <summary>
    /// <c>q,r</c>, or <c>q,r,layer</c>, or <c>q,r,layer,region</c>. Axial, the way the maps are
    /// authored, so a node can be typed straight off <c>DemoMaps</c>.
    /// </summary>
    private static NodeId? ParseNode(string? text)
    {
        if (text is null) return null;

        var parts = text.Split(',');
        if (parts.Length < 2) return null;

        if (!int.TryParse(parts[0], out var q) || !int.TryParse(parts[1], out var r)) return null;

        var layer = parts.Length > 2 && int.TryParse(parts[2], out var l) ? l : 0;
        var region = parts.Length > 3 && int.TryParse(parts[3], out var n) ? n : 0;

        return new NodeId(new Hex(q, r), layer, region);
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
