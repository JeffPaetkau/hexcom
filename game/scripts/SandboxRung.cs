using Godot;
using Hexcom.Core.Awareness;

namespace Hexcom.Game;

/// <summary>
/// A rung of the enemy's ladder as the player sees it: a badge drawn on his body or at the place he
/// believes in, and the words the held key glosses it with.
/// </summary>
/// <remarks>
/// <para>
/// <b>Brief two, and a glyph rather than a word.</b> Under a hostile's name the map used to print the
/// enum — <c>SEARCHING</c>, <c>ALERTED</c> — which a player reads as a measured scale, and contract 3
/// says that scale is not theirs. Both games in the reference set with a state between unaware and
/// engaged draw it as a glyph on the body (<i>Amending Two</i>), and Phoenix Point's transient popup is
/// the shipped failure, so the badge is persistent: it is on the body for as long as the rung is.
/// </para>
/// <para>
/// <b>Two glyphs and two weights, not five points on a line.</b> A question mark while he is working it
/// out, an exclamation mark once he knows; a single rim while it is new, a double rim once he is acting on
/// it, and filled when he has a live fix. So <i>noticed something</i> and <i>looking for you</i> are both
/// questions, and <i>knows you are here</i> and <i>on you</i> are both answers, which is the one
/// distinction the player can act on. Unaware carries nothing, as it does in every game that has the
/// state.
/// </para>
/// <para>
/// <b>A rung that falls is drawn as loudly as one that rises.</b> No game in the set has a ladder that
/// comes down, and a player borrowing the genre's will assume this one cannot. So a rung that moved since
/// our last order carries an arrow beside the badge, up in the rung's own colour or down in the cold
/// blue nothing else on the badge uses — and a hostile who fell all the way to unaware keeps an empty rim
/// with the arrow until the order after, rather than simply losing his badge.
/// </para>
/// </remarks>
public static class SandboxRung
{
    /// <summary>The badge's radius, in pixels.</summary>
    public const float Radius = 8f;

    /// <summary>
    /// What a rung is called when a word is wanted — the held key's terms, the soldier's own line.
    /// </summary>
    /// <remarks>
    /// <i>Amending Two</i>: what the rungs are called on screen is the brief's decision, not a passthrough
    /// of the enum. Klei renamed an alarm because players read its naming as more informative than it
    /// was. Each of these says what the man is doing about us, and none of them sits beside another as
    /// a step up a scale — <c>Searching</c> beside <c>Alerted</c> did.
    /// </remarks>
    public static string Words(AwarenessState state) => state switch
    {
        AwarenessState.Suspicious => "noticed something",
        AwarenessState.Searching => "looking for you",
        AwarenessState.Alerted => "knows you are here",
        AwarenessState.Engaged => "on you",
        _ => "has not noticed you",
    };

    /// <summary>
    /// A rung's badge, centred on a screen point.
    /// </summary>
    /// <param name="moved">Which way the rung went since our last order: up, down, or 0 for not at all.</param>
    /// <param name="looksFirst">
    /// Whether his own go comes before the next go of the soldier who is up — which is to say he has not
    /// looked since that soldier started moving, and will before it moves again. See
    /// <see cref="SandboxFrame.LooksFirst"/>.
    /// </param>
    public static void Draw(CanvasItem canvas, Font font, Vector2 centre, AwarenessState state, int moved, bool looksFirst)
    {
        if (state == AwarenessState.Unaware && moved == 0) return;

        var hue = SandboxPalette.AlarmHue(state);

        if (state == AwarenessState.Unaware)
        {
            canvas.DrawCircle(centre, Radius, new Color(SandboxPalette.UnitShadow, 0.7f));
            canvas.DrawArc(centre, Radius, 0, Mathf.Tau, 20, SandboxPalette.TextDim, 1.5f, true);
        }
        else
        {
            var live = state == AwarenessState.Engaged;
            var acting = state >= AwarenessState.Searching;

            canvas.DrawCircle(centre, Radius, live ? hue : new Color(SandboxPalette.UnitShadow, 0.85f));
            canvas.DrawArc(centre, Radius, 0, Mathf.Tau, 20, hue, acting ? 2.5f : 1.5f, true);
            if (acting) canvas.DrawArc(centre, Radius + 3.5f, 0, Mathf.Tau, 24, hue, 1.5f, true);

            var glyph = state >= AwarenessState.Alerted ? "!" : "?";
            const int size = 13;
            canvas.DrawString(font, centre + new Vector2(-10, size * 0.36f), glyph, HorizontalAlignment.Center, 20, size,
                live ? SandboxPalette.UnitShadow : hue);
        }

        // Both adornments go out to the left, away from the name the badge hangs beside: the hourglass
        // next to the badge, the arrow beyond it.
        if (moved != 0)
        {
            var at = centre - new Vector2(Radius + 9 + (looksFirst ? 13 : 0), 0);
            var up = moved > 0;
            canvas.DrawColoredPolygon(up
                    ? [at + new Vector2(0, -6), at + new Vector2(5, 3), at + new Vector2(-5, 3)]
                    : [at + new Vector2(0, 6), at + new Vector2(-5, -3), at + new Vector2(5, -3)],
                up ? SandboxPalette.AlarmHue(state == AwarenessState.Unaware ? AwarenessState.Suspicious : state) : SandboxPalette.RungFalls);
        }

        if (looksFirst)
        {
            // An hourglass: his look is still to come.
            var at = centre - new Vector2(Radius + 9, 0);
            canvas.DrawColoredPolygon([at + new Vector2(-4, -6), at + new Vector2(4, -6), at], SandboxPalette.TextBright);
            canvas.DrawColoredPolygon([at + new Vector2(-4, 6), at, at + new Vector2(4, 6)], SandboxPalette.TextBright);
        }
    }
}
