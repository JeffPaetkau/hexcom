using Godot;
using Hexcom.Core.Awareness;
using Hexcom.Core.Maps;
using Hexcom.Core.Vision;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>Every colour the sandbox draws with, the two materials it draws them through, and the few rules about which one to pick.</summary>
/// <remarks>
/// <para>
/// Shared by the map and the readouts, which is why it is neither's. A side is the same colour
/// in the world as it is in the turn order, and an alarm state is the same colour under a
/// soldier's feet as in the HUD — that consistency is the only reason this is one table rather
/// than two.
/// </para>
/// <para>
/// The greybox adds a third dimension and no new colours. Entry 049's rule stands: a wall's
/// look comes from what it stops and what it costs, and a material is a colour with a
/// thickness. So there are exactly two materials, one for things and one for readouts, and
/// every mesh carries its colour on its vertices — the material says only whether the colour is
/// lit and whether it is see-through.
/// </para>
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
    public static readonly Color ExitFill = new("2a4a6a", 0.75f);

    /// <summary>A route paid for and not yet walked, while its reaction window is open.</summary>
    public static readonly Color CommittedColor = new("f2c14e");
    public static readonly Color ReachFill = new("1f4438");
    public static readonly Color RegionEdge = new("434a55");
    public static readonly Color PathColor = new("6fd3b0");
    public static readonly Color TextDim = new("8d96a5");
    public static readonly Color TextBright = new("dfe5ee");
    public static readonly Color Unseen = new("0b0d10", 0.55f);
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
    public static readonly Color LinkFill = new("c8a24a");
    public static readonly Color LinkText = new("f0d190");
    public static readonly Color UnitOutline = new("0a0c0f", 0.7f);

    /// <summary>The cursor's hex, outlined so the pick can be checked against the readout.</summary>
    public static readonly Color HoverEdge = new("dfe5ee", 0.8f);

    /// <summary>
    /// Things: ground, walls, bodies. Lit, opaque, coloured by their vertices.
    /// </summary>
    /// <remarks>
    /// Culls nothing, so the winding of a polygon cannot punch a hole in the map — see
    /// <see cref="MeshBuilder"/>. Rough rather than glossy because a highlight on a blockout is a
    /// claim about a surface nobody has designed.
    /// </remarks>
    public static readonly StandardMaterial3D Solid = new()
    {
        VertexColorUseAsAlbedo = true,
        Roughness = 1f,
        Metallic = 0f,
        CullMode = BaseMaterial3D.CullModeEnum.Disabled,
    };

    /// <summary>
    /// Readouts: the attention fields, the held arcs, the reach, the routes, the ghosts. Unlit,
    /// see-through, drawn in the order they were added.
    /// </summary>
    /// <remarks>
    /// Unlit so that a readout is the colour the palette says and not that colour in shadow — a
    /// wedge that darkened on the far side of a wall would be saying something about the wall.
    /// It writes no depth, which is what lets several tints on one hex composite in the order
    /// they were added instead of fighting over which is in front at the same height; and it is
    /// tested against depth, so a wall still hides the reach behind it.
    /// </remarks>
    public static readonly StandardMaterial3D Clear = new()
    {
        VertexColorUseAsAlbedo = true,
        ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded,
        Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
        DepthDrawMode = BaseMaterial3D.DepthDrawModeEnum.Disabled,
        CullMode = BaseMaterial3D.CullModeEnum.Disabled,
    };

    /// <summary>
    /// The same as <see cref="Clear"/>, drawn before it: the storeys above the one being looked
    /// at, and the railings the eye goes through.
    /// </summary>
    /// <remarks>
    /// Transparent meshes are sorted by distance and both of these sit at the origin, so
    /// without a priority the engine picks an order and the readouts sometimes vanish under a
    /// ghosted roof. The lower priority says the ghosts go on first, whatever the distance.
    /// </remarks>
    public static readonly StandardMaterial3D ClearBehind = new()
    {
        VertexColorUseAsAlbedo = true,
        ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded,
        Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
        DepthDrawMode = BaseMaterial3D.DepthDrawModeEnum.Disabled,
        CullMode = BaseMaterial3D.CullModeEnum.Disabled,
        RenderPriority = -1,
    };

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
