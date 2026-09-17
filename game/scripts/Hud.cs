using System;
using Godot;

namespace Hexcom.Game;

/// <summary>
/// The screen furniture: a card about the active unit top right, and End Turn bottom right.
/// </summary>
/// <remarks>
/// The card is a column of rows that grows as the game learns more about a unit. Today it
/// carries a photo tile, a name and type, the action points as a bar, and the cost of the
/// move under the cursor; ammo and the rest slot in as rows when they exist.
/// </remarks>
public partial class Hud : CanvasLayer
{
    private const int Margin = 24;

    private const int PortraitPixels = 176;

    private Label _apValue = null!;
    private ProgressBar _apBar = null!;
    private Label _moveValue = null!;
    private Control _moveRow = null!;
    private Label _riskValue = null!;
    private Control _riskRow = null!;
    private Label _note = null!;
    private PanelContainer _photo = null!;
    private Label _placeholder = null!;

    public event Action? EndTurnPressed;

    public override void _Ready()
    {
        var theme = SciFi.Theme();

        AddChild(Anchored(Control.LayoutPreset.TopLeft, BuildCard(theme), theme));
        AddChild(Anchored(Control.LayoutPreset.BottomRight, BuildEndTurn(theme), theme));
    }

    /// <summary>
    /// Put a picture of the token in the photo slot, rendered live from its own mesh in a small
    /// offscreen world lit the same way as the board.
    /// </summary>
    public void ShowPortrait(Mesh piece)
    {
        var viewport = new SubViewport
        {
            Size = new Vector2I(PortraitPixels, PortraitPixels),
            TransparentBg = true,
            OwnWorld3D = true,
            Msaa3D = Viewport.Msaa.Msaa4X,
            RenderTargetUpdateMode = SubViewport.UpdateMode.Always,
        };

        viewport.AddChild(new MeshInstance3D { Mesh = piece });
        viewport.AddChild(new DirectionalLight3D
        {
            RotationDegrees = new Vector3(-48f, 150f, 0f),
            LightEnergy = 1.6f,
            LightColor = new Color(1f, 0.96f, 0.9f),
        });
        viewport.AddChild(new WorldEnvironment
        {
            Environment = new Godot.Environment
            {
                BackgroundMode = Godot.Environment.BGMode.Color,
                BackgroundColor = new Color(0f, 0f, 0f, 0f),
                AmbientLightSource = Godot.Environment.AmbientSource.Color,
                AmbientLightColor = new Color(0.55f, 0.65f, 0.8f),
                AmbientLightEnergy = 0.6f,
            },
        });

        // Three-quarter view from a little above, framed on the token's middle.
        var camera = new Camera3D { Fov = 30f, Current = true };
        camera.Position = new Vector3(2.4f, 2.0f, 2.9f);
        viewport.AddChild(camera);
        AddChild(viewport);
        camera.LookAt(new Vector3(0f, 0.9f, 0f), Vector3.Up);

        _placeholder.Visible = false;
        _photo.AddChild(new TextureRect
        {
            Texture = viewport.GetTexture(),
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
            StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered,
        });
    }

    /// <summary>
    /// Show the points left, what the move under the cursor would cost if there is one, and
    /// the chance of a fall on the way if there is any.
    /// </summary>
    public void ShowAp(int ap, int max, int? moveCost, double? risk = null)
    {
        _apValue.Text = $"{ap} / {max}";
        _apBar.MaxValue = max;
        _apBar.Value = ap;

        _moveRow.Visible = moveCost is not null;
        if (moveCost is { } cost) _moveValue.Text = cost.ToString();

        _riskRow.Visible = moveCost is not null && risk is > 0;
        if (risk is { } chance) _riskValue.Text = $"{Math.Round(chance * 100)}%";
    }

    /// <summary>A line about something that has just happened to the unit, or null to clear it.</summary>
    public void ShowNote(string? note)
    {
        _note.Visible = note is not null;
        _note.Text = note ?? "";
    }

    private Control BuildCard(Theme theme)
    {
        var card = new PanelContainer { Theme = theme, CustomMinimumSize = new Vector2(360, 0) };

        var column = new VBoxContainer();
        column.AddThemeConstantOverride("separation", 10);
        card.AddChild(column);

        // Photo tile beside name and type.
        var header = new HBoxContainer();
        header.AddThemeConstantOverride("separation", 14);

        _photo = new PanelContainer { CustomMinimumSize = new Vector2(88, 88) };
        _photo.AddThemeStyleboxOverride("panel", SciFi.Tile());
        _placeholder = new Label
        {
            Text = "?",
            HorizontalAlignment = HorizontalAlignment.Center,
            VerticalAlignment = VerticalAlignment.Center,
        };
        _placeholder.AddThemeFontSizeOverride("font_size", 40);
        _placeholder.AddThemeColorOverride("font_color", SciFi.Muted);
        _photo.AddChild(_placeholder);
        var photo = _photo;

        var identity = new VBoxContainer { SizeFlagsVertical = Control.SizeFlags.ShrinkCenter };
        identity.AddThemeConstantOverride("separation", 2);
        var name = new Label { Text = "UNIT 1" };
        name.AddThemeFontSizeOverride("font_size", 26);
        var kind = new Label { Text = "RIFLEMAN" };
        kind.AddThemeFontSizeOverride("font_size", 16);
        kind.AddThemeColorOverride("font_color", SciFi.Muted);
        identity.AddChild(name);
        identity.AddChild(kind);

        header.AddChild(photo);
        header.AddChild(identity);
        column.AddChild(header);

        column.AddChild(SciFi.Rule());

        // Action points: a label row and a bar.
        var apRow = Row("ACTION POINTS", out _apValue);
        column.AddChild(apRow);

        _apBar = new ProgressBar { ShowPercentage = false, CustomMinimumSize = new Vector2(0, 8) };
        column.AddChild(_apBar);

        _moveRow = Row("MOVE", out _moveValue);
        column.AddChild(_moveRow);

        // The chance of a fall on a hurried way, in the warning colour, only when there is one.
        _riskRow = Row("FALL RISK", out _riskValue);
        _riskValue.AddThemeColorOverride("font_color", SciFi.Warning);
        column.AddChild(_riskRow);

        _note = new Label { Visible = false };
        _note.AddThemeFontSizeOverride("font_size", 15);
        _note.AddThemeColorOverride("font_color", SciFi.Warning);
        column.AddChild(_note);

        return card;
    }

    private static Control Row(string caption, out Label value)
    {
        var row = new HBoxContainer();

        var label = new Label { Text = caption, SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
        label.AddThemeFontSizeOverride("font_size", 15);
        label.AddThemeColorOverride("font_color", SciFi.Muted);

        value = new Label { HorizontalAlignment = HorizontalAlignment.Right };
        value.AddThemeFontSizeOverride("font_size", 22);

        row.AddChild(label);
        row.AddChild(value);
        return row;
    }

    private Control BuildEndTurn(Theme theme)
    {
        var button = new Button { Text = "END TURN", Theme = theme, CustomMinimumSize = new Vector2(200, 56) };
        button.Pressed += () => EndTurnPressed?.Invoke();
        return button;
    }

    /// <summary>Pin a control to a corner of the screen with the standard margin.</summary>
    private static Control Anchored(Control.LayoutPreset corner, Control content, Theme theme)
    {
        var margin = new MarginContainer { Theme = theme };
        margin.SetAnchorsAndOffsetsPreset(corner);
        margin.GrowHorizontal = corner is Control.LayoutPreset.TopRight or Control.LayoutPreset.BottomRight
            ? Control.GrowDirection.Begin
            : Control.GrowDirection.End;
        margin.GrowVertical = corner is Control.LayoutPreset.BottomLeft or Control.LayoutPreset.BottomRight
            ? Control.GrowDirection.Begin
            : Control.GrowDirection.End;
        foreach (var side in new[] { "margin_left", "margin_top", "margin_right", "margin_bottom" })
        {
            margin.AddThemeConstantOverride(side, Margin);
        }

        margin.AddChild(content);
        return margin;
    }
}
