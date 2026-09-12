using Godot;

namespace Hexcom.Game;

/// <summary>
/// Puts a window a session opened on the leftmost monitor, so it does not land in front of
/// whoever is working on the middle one.
/// </summary>
/// <remarks>
/// <para>
/// The user has three screens and works on the centre one. Every window this project opens —
/// a capture, a scene-load check, a run to look at something — opened on it, and with several
/// sessions running that is a window every few minutes in the middle of whatever they are
/// reading. <c>docs/decisions.md</c> entry 063 is the rule; this is the mechanism.
/// </para>
/// <para>
/// <b>Leftmost by position, not by index.</b> Godot's own <c>--screen N</c> takes an index, and
/// which index is the left monitor is a fact about this machine that would be wrong on the next
/// one. The screen with the smallest X in the virtual desktop is the left one everywhere, and
/// <c>ScreenGetPosition</c> is how you ask. On a single-screen machine that is the one screen,
/// so nothing here needs a special case for it.
/// </para>
/// <para>
/// <b>It is a setting and not a step</b>, in the sense <c>docs/decisions.md</c> entry 049 draws:
/// a person at the keyboard cannot decide which monitor the run boots onto. <c>--shot</c> implies
/// it, because a capture is always a session's; the exported game with no flags opens where
/// Windows puts it, which is the user's own monitor and is correct.
/// </para>
/// <para>
/// The usable rect rather than the whole screen, because a window centred on the full height of
/// a screen with a taskbar on it sits slightly under the taskbar. Both windows are centred on
/// the same screen and so overlap; that is the right trade for a monitor nobody is working on,
/// and dragging one off the other is a person's business.
/// </para>
/// </remarks>
public static class SandboxAside
{
    /// <summary>Move a window to the middle of the leftmost screen.</summary>
    /// <remarks>
    /// Called before the first frame for the main window, and on opening for the instruments
    /// window, which is built hidden and has no position worth setting until it is shown.
    /// </remarks>
    public static void Place(Window window)
    {
        var screen = Leftmost();
        var usable = DisplayServer.ScreenGetUsableRect(screen);
        var at = usable.Position + (usable.Size - window.Size) / 2;

        window.Position = new Vector2I(
            System.Math.Max(usable.Position.X, at.X),
            System.Math.Max(usable.Position.Y, at.Y));

        // Said out loud for the same reason every script step says what it did: a run that asked
        // to be put aside and silently was not is a window in the user's face with nothing in the
        // log about it, and on a one-screen machine the honest answer is that there was one screen.
        GD.Print($"aside: {window.Title} to screen {screen} of {DisplayServer.GetScreenCount()} at {window.Position}");
    }

    /// <summary>The screen furthest to the left in the virtual desktop.</summary>
    private static int Leftmost()
    {
        var leftmost = 0;

        for (var screen = 1; screen < DisplayServer.GetScreenCount(); screen++)
            if (DisplayServer.ScreenGetPosition(screen).X < DisplayServer.ScreenGetPosition(leftmost).X)
                leftmost = screen;

        return leftmost;
    }
}
