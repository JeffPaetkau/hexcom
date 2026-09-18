using System;
using Godot;
using Hexcom.Rules;
using Side = Hexcom.Rules.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>
/// The screen furniture: a card about the active unit top left, a card about the enemy under
/// the cursor top right, and End Turn bottom right.
/// </summary>
/// <remarks>
/// The unit card is a column of rows that grows as the game learns more about a unit. Today it
/// carries a photo tile, a name and type in the side's colour, the action points and the hit
/// points as bars, the rifle with its rounds, and the cost of the move under the cursor. The
/// target card appears when the cursor is on an enemy and says what a shot at them would be:
/// their hit points, the range, the chance, the damage and the cost, or why the shot is
/// refused. Nothing on either card is a number the rules did not give.
/// </remarks>
public partial class Hud : CanvasLayer
{
    private const int Margin = 24;

    private const int PortraitPixels = 176;

    private Label _name = null!;
    private Label _kind = null!;
    private Label _apValue = null!;
    private ProgressBar _apBar = null!;
    private Label _hpValue = null!;
    private ProgressBar _hpBar = null!;
    private Label _roundsValue = null!;
    private Label _weaponDetail = null!;
    private Label _facingValue = null!;
    private Label _moveValue = null!;
    private Control _moveRow = null!;
    private Label _turnValue = null!;
    private Control _turnRow = null!;
    private Label _riskValue = null!;
    private Control _riskRow = null!;
    private Label _note = null!;
    private PanelContainer _photo = null!;
    private Label _placeholder = null!;
    private MeshInstance3D? _portrait;

    private Control _targetCard = null!;
    private Label _targetName = null!;
    private Label _targetHpValue = null!;
    private ProgressBar _targetHpBar = null!;
    private Label _rangeValue = null!;
    private Label _hitValue = null!;
    private Label _damageValue = null!;
    private Label _shotValue = null!;
    private Label _refusal = null!;

    public event Action? EndTurnPressed;

    public override void _Ready()
    {
        var theme = SciFi.Theme();

        AddChild(Anchored(Control.LayoutPreset.TopLeft, BuildCard(theme), theme));
        AddChild(Anchored(Control.LayoutPreset.TopRight, BuildTargetCard(theme), theme));
        AddChild(Anchored(Control.LayoutPreset.BottomRight, BuildEndTurn(theme), theme));
    }

    /// <summary>
    /// Put a picture of the token in the photo slot, rendered live from its own mesh in a small
    /// offscreen world lit the same way as the board. Called again with another mesh when the
    /// turn passes, and the same little world shows the new piece.
    /// </summary>
    public void ShowPortrait(Mesh piece)
    {
        if (_portrait is not null)
        {
            _portrait.Mesh = piece;
            return;
        }

        var viewport = new SubViewport
        {
            Size = new Vector2I(PortraitPixels, PortraitPixels),
            TransparentBg = true,
            OwnWorld3D = true,
            Msaa3D = Viewport.Msaa.Msaa4X,
            RenderTargetUpdateMode = SubViewport.UpdateMode.Always,
        };

        _portrait = new MeshInstance3D { Mesh = piece };
        viewport.AddChild(_portrait);
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

    /// <summary>Show who is up and everything the card knows about them: name, side, points, hit points, rifle and rounds.</summary>
    public void ShowUnit(Unit unit)
    {
        _name.Text = unit.Name;
        _name.AddThemeColorOverride("font_color", SciFi.SideColour(unit.Side));
        _kind.Text = unit.Side == Side.Player ? "RIFLEMAN" : "HOSTILE RIFLEMAN";

        _apValue.Text = $"{unit.Ap} / {Unit.MaxAp}";
        _apBar.MaxValue = Unit.MaxAp;
        _apBar.Value = unit.Ap;

        _hpValue.Text = $"{unit.HitPoints} / {Unit.MaxHitPoints}";
        _hpBar.MaxValue = Unit.MaxHitPoints;
        _hpBar.Value = unit.HitPoints;

        var weapon = unit.Weapon;
        _roundsValue.Text = $"{unit.Rounds} / {weapon.Rounds}";
        _roundsValue.AddThemeColorOverride("font_color", unit.Rounds > 0 ? SciFi.Text : SciFi.Warning);
        _weaponDetail.Text = $"{weapon.Damage} DAMAGE  ·  {weapon.MaxRange:0} M RANGE  ·  {weapon.ShotCost} AP A SHOT";

        _facingValue.Text = Facing.Name(unit.Facing);
    }

    /// <summary>Show what turning to face the hex under the cursor would cost, in the warning colour if it cannot be paid, or hide the row with null.</summary>
    public void ShowTurn(int? cost, bool affordable = true)
    {
        _turnRow.Visible = cost is not null;
        if (cost is { } points) _turnValue.Text = points.ToString();
        _turnValue.AddThemeColorOverride("font_color", affordable ? SciFi.Text : SciFi.Warning);
    }

    /// <summary>Show what the move under the cursor would cost if there is one, and the chance of a fall on the way if there is any.</summary>
    public void ShowMove(int? moveCost, double? risk = null)
    {
        _moveRow.Visible = moveCost is not null;
        if (moveCost is { } cost) _moveValue.Text = cost.ToString();

        _riskRow.Visible = moveCost is not null && risk is > 0;
        if (risk is { } chance) _riskValue.Text = $"{Math.Round(chance * 100)}%";
    }

    /// <summary>Show the enemy under the cursor and what a shot at them would be, or hide the card with null.</summary>
    public void ShowTarget(Unit? target, Shot? shot)
    {
        _targetCard.Visible = target is not null;
        if (target is null || shot is null) return;

        _targetName.Text = target.Name;
        _targetName.AddThemeColorOverride("font_color", SciFi.SideColour(target.Side));

        _targetHpValue.Text = $"{target.HitPoints} / {Unit.MaxHitPoints}";
        _targetHpBar.MaxValue = Unit.MaxHitPoints;
        _targetHpBar.Value = target.HitPoints;

        _rangeValue.Text = $"{shot.Range:0} M";
        _hitValue.Text = shot.CanFire ? $"{Math.Round(shot.HitChance * 100)}%" : "—";
        _hitValue.AddThemeColorOverride("font_color", shot.CanFire ? SciFi.Accent : SciFi.Muted);
        _damageValue.Text = shot.Damage.ToString();
        _shotValue.Text = $"{shot.Cost} AP";

        _refusal.Visible = !shot.CanFire;
        _refusal.Text = shot.Refusal ?? "";
    }

    /// <summary>A line about something that has just happened, or null to clear it.</summary>
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
        _name = new Label { Text = "UNIT" };
        _name.AddThemeFontSizeOverride("font_size", 26);
        _kind = new Label { Text = "RIFLEMAN" };
        _kind.AddThemeFontSizeOverride("font_size", 16);
        _kind.AddThemeColorOverride("font_color", SciFi.Muted);
        identity.AddChild(_name);
        identity.AddChild(_kind);

        header.AddChild(photo);
        header.AddChild(identity);
        column.AddChild(header);

        column.AddChild(SciFi.Rule());

        // Action points: a label row and a bar.
        column.AddChild(Row("ACTION POINTS", out _apValue));
        _apBar = new ProgressBar { ShowPercentage = false, CustomMinimumSize = new Vector2(0, 8) };
        column.AddChild(_apBar);

        // Hit points: the same, in the health colour.
        column.AddChild(Row("HIT POINTS", out _hpValue));
        _hpBar = HealthBar();
        column.AddChild(_hpBar);

        column.AddChild(SciFi.Rule());

        // The weapon: its name with the rounds left, and its numbers in a muted line under.
        column.AddChild(Row("RIFLE  ·  ROUNDS", out _roundsValue));
        _weaponDetail = new Label();
        _weaponDetail.AddThemeFontSizeOverride("font_size", 14);
        _weaponDetail.AddThemeColorOverride("font_color", SciFi.Muted);
        column.AddChild(_weaponDetail);

        // Which way the soldier faces, as a compass point; the board shows it as the piece's nose.
        column.AddChild(Row("FACING", out _facingValue));

        _moveRow = Row("MOVE", out _moveValue);
        column.AddChild(_moveRow);

        // What a right click would cost: the turn on the spot to face the hovered hex.
        _turnRow = Row("TURN TO FACE  ·  RIGHT CLICK", out _turnValue);
        column.AddChild(_turnRow);

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

    /// <summary>The card about the enemy under the cursor: who, how hurt, and the shot at them.</summary>
    private Control BuildTargetCard(Theme theme)
    {
        var card = new PanelContainer { Theme = theme, CustomMinimumSize = new Vector2(300, 0), Visible = false };
        card.AddThemeStyleboxOverride("panel", SciFi.Panel(SciFi.Danger));
        _targetCard = card;

        var column = new VBoxContainer();
        column.AddThemeConstantOverride("separation", 10);
        card.AddChild(column);

        var caption = new Label { Text = "TARGET" };
        caption.AddThemeFontSizeOverride("font_size", 15);
        caption.AddThemeColorOverride("font_color", SciFi.Muted);
        column.AddChild(caption);

        _targetName = new Label { Text = "HOSTILE" };
        _targetName.AddThemeFontSizeOverride("font_size", 26);
        column.AddChild(_targetName);

        column.AddChild(SciFi.Rule());

        column.AddChild(Row("HIT POINTS", out _targetHpValue));
        _targetHpBar = HealthBar();
        column.AddChild(_targetHpBar);

        column.AddChild(Row("RANGE", out _rangeValue));
        column.AddChild(Row("HIT CHANCE", out _hitValue));
        column.AddChild(Row("DAMAGE", out _damageValue));
        column.AddChild(Row("SHOT", out _shotValue));

        _refusal = new Label { Visible = false };
        _refusal.AddThemeFontSizeOverride("font_size", 15);
        _refusal.AddThemeColorOverride("font_color", SciFi.Warning);
        column.AddChild(_refusal);

        return card;
    }

    private static ProgressBar HealthBar()
    {
        var bar = new ProgressBar { ShowPercentage = false, CustomMinimumSize = new Vector2(0, 8) };
        bar.AddThemeStyleboxOverride("fill", SciFi.Fill(SciFi.Health));
        return bar;
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
