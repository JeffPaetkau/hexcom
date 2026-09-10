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
/// Godot_v4.7.2-stable_mono_win64_console --path game -- --shot map.png --fit
/// Godot_v4.7.2-stable_mono_win64_console --path game -- --shot old.png --scenario compound --zoom 44
/// </code>
/// <para>
/// Five of the flags are settings and live here: <c>--shot</c>, <c>--shot-after</c>,
/// <c>--scenario</c>, <c>--ai</c> and <c>--windows</c>. Everything else on the line is a
/// <see cref="SandboxScript"/> step, run in the order it was typed, because <c>--move</c> then
/// <c>--pass</c> is a different battle from <c>--pass</c> then <c>--move</c>. The test for which
/// side of that line a flag falls on is whether somebody at the keyboard could do it.
/// </para>
/// <para>
/// The camera flags came in with the waystation and they are not decoration: a map 85 metres
/// across drawn at 44 pixels to the metre is four screens wide, so without <c>--fit</c> or
/// <c>--zoom</c> every picture of it is a picture of one corner. <c>--fit</c> is the one to reach
/// for, because it works the figure out from the map rather than being told it, and it is what
/// puts an attention field at its true reach in a frame that shows what the reach is against.
/// They are steps rather than settings, so put them <em>last</em>: anything a soldier does
/// afterwards may pull the camera back to whoever is up next.
/// </para>
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
    private const string AiFlag = "--ai";
    private const string WindowsFlag = "--windows";
    private const string ScenarioFlag = "--scenario";

    private readonly string _path;
    private int _framesLeft;

    private SandboxCapture(string path, int framesLeft, bool automatic, bool byHand, string? scenario, SandboxScript script)
    {
        _path = path;
        _framesLeft = framesLeft;
        Automatic = automatic;
        AnswerWindowsByHand = byHand;
        Scenario = scenario;
        Script = script;
    }

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

    /// <summary>
    /// Whether a move stops with its reaction window open instead of taking every recommendation.
    /// </summary>
    /// <remarks>
    /// The setting the whole of <c>--place</c> and <c>--resolve</c> hangs off, and off by default
    /// so that every command written before it existed still means what it meant. With it on, a
    /// <c>--move</c> pays for the walk and stops, and the picture can be taken with the question
    /// still on screen — which is a state entry 040 made reachable and nothing could photograph.
    /// </remarks>
    public bool AnswerWindowsByHand { get; }

    /// <summary>Which of <see cref="SandboxScenario.All"/> to open, or null for the default.</summary>
    public string? Scenario { get; }

    /// <summary>Everything else on the command line, in the order it was typed.</summary>
    public SandboxScript Script { get; }

    /// <summary>The capture this run was asked for, or null for an ordinary interactive run.</summary>
    public static SandboxCapture? Requested()
    {
        var args = OS.GetCmdlineUserArgs();

        var path = SandboxScript.ValueOf(args, PathFlag);
        if (path is null) return null;

        var delay = SandboxScript.ValueOf(args, DelayFlag);

        return new SandboxCapture(
            path,
            int.TryParse(delay, out var frames) ? frames : 4,
            args.Contains(AiFlag),
            args.Contains(WindowsFlag),
            SandboxScript.ValueOf(args, ScenarioFlag),
            SandboxScript.Parse(args));
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
}
