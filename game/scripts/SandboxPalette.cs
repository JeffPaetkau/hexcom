using Godot;
using Hexcom.Core.Awareness;
using Hexcom.Core.Maps;
using Hexcom.Core.Vision;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>Every colour the sandbox draws with, and the few rules about which one to pick.</summary>
/// <remarks>
/// Shared by the map and the readouts, which is why it is neither's. A side is the same colour
/// in the world as it is in the turn order, and an alarm state is the same colour under a
/// soldier's feet as in the HUD — that consistency is the only reason this is one table rather
/// than two.
/// </remarks>
public static class SandboxPalette
{
    public static readonly Color Background = new("14171c");
    public static readonly Color FloorFill = new("2b3038");
    public static readonly Color RoughFill = new("3b332a");
    public static readonly Color TransitFill = new("3a2630");

    /// <summary>Ground nobody can be on: deep water, a hole. Read off <c>GroundType.Passable</c>.</summary>
    public static readonly Color ImpassableFill = new("18222e");

    /// <summary>Where our side may walk off the field, if the mission gives us one.</summary>
    public static readonly Color ExitFill = new("2a4a6a");

    /// <summary>A route paid for and not yet walked, while its reaction window is open.</summary>
    public static readonly Color CommittedColor = new("f2c14e");
    public static readonly Color ReachFill = new("1f4438");
    public static readonly Color RegionEdge = new("434a55");
    public static readonly Color PathColor = new("6fd3b0");
    public static readonly Color TextDim = new("8d96a5");
    public static readonly Color TextBright = new("dfe5ee");
    public static readonly Color Unseen = new("0b0d10", 0.66f);
    public static readonly Color CoverLightHue = new("6fa8c8");
    public static readonly Color CoverHalfHue = new("d8b25a");
    public static readonly Color CoverFullHue = new("d1743c");
    public static readonly Color PlayerHue = new("74d3b4");
    public static readonly Color HostileHue = new("e0674a");
    public static readonly Color NeutralHue = new("aab2bd");
    public static readonly Color Panel = new("1b1f26", 0.92f);
    public static readonly Color GhostHue = new("e0674a", 0.55f);
    public static readonly Color OverwatchHue = new("f2c14e");
    public static readonly Color AmbushHue = new("d95f9a");
    public static readonly Color LinkFill = new("c8a24a", 0.28f);
    public static readonly Color LinkText = new("f0d190");
    public static readonly Color UnitOutline = new("0a0c0f", 0.7f);

    public static Color CoverHue(CoverGrade grade) => grade switch
    {
        CoverGrade.Full => CoverFullHue,
        CoverGrade.Half => CoverHalfHue,
        _ => CoverLightHue,
    };

    public static Color SideHue(Side side) => side switch
    {
        Side.Player => PlayerHue,
        Side.Hostile => HostileHue,
        _ => NeutralHue,
    };

    public static Color AlarmHue(AwarenessState state) => state switch
    {
        AwarenessState.Engaged => new Color("ff6a4d"),
        AwarenessState.Alerted => new Color("e0674a"),
        AwarenessState.Searching => new Color("d8942a"),
        AwarenessState.Suspicious => new Color("c9b04a"),
        _ => new Color("6b7480"),
    };
}
