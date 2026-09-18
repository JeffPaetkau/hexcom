using Godot;

namespace Hexcom.Game;

/// <summary>
/// The look of the screen furniture: dark glass panels, a cyan accent, slanted buttons and a
/// condensed face. Built in code so there is one place it lives.
/// </summary>
public static class SciFi
{
    public static readonly Color Accent = new(0.35f, 0.88f, 1f);
    public static readonly Color AccentDim = new(0.35f, 0.88f, 1f, 0.45f);
    public static readonly Color Text = new(0.86f, 0.95f, 1f);
    public static readonly Color Muted = new(0.5f, 0.68f, 0.78f);
    public static readonly Color Glass = new(0.02f, 0.06f, 0.09f, 0.82f);
    public static readonly Color GlassLit = new(0.06f, 0.14f, 0.2f, 0.9f);

    // Marks on hexes: one shape, the colour says what the hex means. See-through, because a
    // mark that hides the ground hides what it is about. Movement is a quiet dark grey; the
    // other two are reserved for what comes: warning in orange, danger in red.
    public static readonly Color MarkMove = new(0.05f, 0.05f, 0.06f, 0.18f);
    public static readonly Color MarkWarning = new(1f, 0.62f, 0.1f, 0.22f);
    public static readonly Color MarkDanger = new(0.95f, 0.15f, 0.1f, 0.35f);

    /// <summary>The warning colour for text: the orange of the marks, opaque.</summary>
    public static readonly Color Warning = new(1f, 0.62f, 0.1f);

    /// <summary>The danger colour, opaque: the enemy's name, the ring under him on his turn, the edge of the target card.</summary>
    public static readonly Color Danger = new(1f, 0.32f, 0.22f);

    /// <summary>Hit points, on both cards: the green every game in the genre uses for what is left of a soldier.</summary>
    public static readonly Color Health = new(0.45f, 0.9f, 0.5f);

    /// <summary>A round in flight: hot and pale, so it reads against ground and sky alike for the moment it is there.</summary>
    public static readonly Color Tracer = new(1f, 0.92f, 0.6f);

    /// <summary>A side's colour on the cards: ours is the interface's own cyan, theirs the danger red.</summary>
    public static Color SideColour(Hexcom.Rules.Side side) => side == Hexcom.Rules.Side.Player ? Accent : Danger;

    private static Font? _font;

    /// <summary>A condensed system face if the machine has one, otherwise whatever it has.</summary>
    public static Font Face()
        => _font ??= new SystemFont { FontNames = new[] { "Bahnschrift", "Segoe UI", "Arial" } };

    public static Theme Theme()
    {
        var theme = new Theme { DefaultFont = Face(), DefaultFontSize = 18 };

        theme.SetColor("font_color", "Label", Text);
        theme.SetColor("font_color", "Button", Accent);
        theme.SetColor("font_hover_color", "Button", Text);
        theme.SetColor("font_pressed_color", "Button", Glass);
        theme.SetColor("font_focus_color", "Button", Accent);
        theme.SetFontSize("font_size", "Button", 22);

        theme.SetStylebox("normal", "Button", Slanted(Glass, Accent));
        theme.SetStylebox("hover", "Button", Slanted(GlassLit, Accent));
        theme.SetStylebox("pressed", "Button", Slanted(Accent, Accent));
        theme.SetStylebox("focus", "Button", new StyleBoxEmpty());

        theme.SetStylebox("panel", "PanelContainer", Panel());

        theme.SetStylebox("background", "ProgressBar", Bar(new Color(1f, 1f, 1f, 0.08f)));
        theme.SetStylebox("fill", "ProgressBar", Bar(Accent));

        return theme;
    }

    /// <summary>A panel of dark glass with a hairline border and a heavier edge on the left, in the accent or a colour of the caller's.</summary>
    public static StyleBoxFlat Panel(Color? edge = null)
    {
        var colour = edge ?? Accent;
        var box = new StyleBoxFlat { BgColor = Glass, BorderColor = new Color(colour, AccentDim.A) };
        box.SetBorderWidthAll(1);
        box.BorderWidthLeft = 3;
        box.SetCornerRadiusAll(2);
        box.SetContentMarginAll(16);
        return box;
    }

    /// <summary>The fill of a bar in a colour of the caller's, for a bar that is not the accent.</summary>
    public static StyleBoxFlat Fill(Color colour) => Bar(colour);

    /// <summary>A small framed square, for a photo or an icon.</summary>
    public static StyleBoxFlat Tile()
    {
        var box = new StyleBoxFlat { BgColor = new Color(0f, 0f, 0f, 0.35f), BorderColor = AccentDim };
        box.SetBorderWidthAll(1);
        box.SetCornerRadiusAll(2);
        return box;
    }

    /// <summary>A thin accent line to divide sections of a card.</summary>
    public static Control Rule()
    {
        var rule = new ColorRect { Color = AccentDim, CustomMinimumSize = new Vector2(0, 1) };
        return rule;
    }

    private static StyleBoxFlat Slanted(Color fill, Color border)
    {
        var box = new StyleBoxFlat { BgColor = fill, BorderColor = border, Skew = new Vector2(0.18f, 0f) };
        box.SetBorderWidthAll(1);
        box.SetCornerRadiusAll(1);
        box.SetContentMarginAll(12);
        box.ContentMarginLeft = 28;
        box.ContentMarginRight = 28;
        return box;
    }

    private static StyleBoxFlat Bar(Color fill)
    {
        var box = new StyleBoxFlat { BgColor = fill };
        box.SetCornerRadiusAll(1);
        return box;
    }
}
