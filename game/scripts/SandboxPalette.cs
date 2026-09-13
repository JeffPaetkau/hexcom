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

    /// <summary>The outer edge of where the active soldier can get to at all.</summary>
    /// <remarks>
    /// Neutral, because it is the one edge that says nothing about the reserve, and a pale line on
    /// the ground is the one colour no cover outline, route, side or arc already uses.
    /// </remarks>
    public static readonly Color ReachEdge = new("c7ced8", 0.45f);

    /// <summary>The three reserve rungs drawn on the ground and on the soldier's points. See <see cref="BandHue"/>.</summary>
    public enum Band { Floor, Cheapest, Better }

    /// <summary>
    /// A reserve rung's colour, on the ground and on the soldier's points bar alike.
    /// </summary>
    /// <remarks>
    /// <para>
    /// One violet family, getting brighter as the rung gets dearer. The move range's edges share the
    /// ground with the cover outlines, which already own blue, yellow and orange, and with the route,
    /// the sides, the arcs and the aim — so the genre's own blue-and-yellow would have read as cover.
    /// Violet is the hue nothing on the map was using.
    /// </para>
    /// <para>
    /// The same three colours mark the rungs on the points bar under the soldier, which makes the
    /// bar the legend for the ground: a player who reads <i>snap</i> in this colour on the soldier
    /// has been told what the line of that colour on the ground means.
    /// </para>
    /// </remarks>
    public static Color BandHue(Band band) => band switch
    {
        Band.Better => new Color("d2abff"),
        Band.Cheapest => new Color("a67cf2"),
        _ => new Color("7f73c2"),
    };
    public static readonly Color RegionEdge = new("434a55");
    public static readonly Color PathColor = new("6fd3b0");
    public static readonly Color TextDim = new("8d96a5");
    public static readonly Color TextBright = new("dfe5ee");
    public static readonly Color Unseen = new("0b0d10", 0.55f);
    public static readonly Color CoverLightHue = new("6fa8c8");
    public static readonly Color CoverHalfHue = new("d8b25a");
    public static readonly Color CoverFullHue = new("d1743c");
    /// <summary>
    /// The two sides, at a saturation the ground is not allowed to reach.
    /// </summary>
    /// <remarks>
    /// The play-through's fifth finding was that our soldiers do not read against the terrain,
    /// and the measurement behind these two figures is why: every ground fill in this table sits
    /// between 12 and 24 per cent saturation, and the old player hue was a 45 per cent teal
    /// against a 24 per cent brown — a difference a hex of attention tint could close on its own.
    /// Both sides are now above 70 per cent, which no ground fill may approach; that is the rule,
    /// and the hexes are the numbers that keep it. Value is doing work too, and the reason the
    /// hostile hue went up rather than down: a body is lit from one side and shadowed on the
    /// other, so the dark half of it has to still beat the ground it stands on.
    /// <para>
    /// Entry 049's figures-not-names rule is about walls and ground, and it does not stop a
    /// soldier having a colour of its own — a side is not a kind of terrain. What the rule does
    /// forbid is the reverse: a ground fill drifting up towards these, which is the change to
    /// refuse when somebody proposes it.
    /// </para>
    /// </remarks>
    public static readonly Color PlayerHue = new("2ce8b0");

    public static readonly Color HostileHue = new("ff5a35");
    public static readonly Color NeutralHue = new("c8d2e0");

    /// <summary>
    /// The contact ring under a body, standing in for the shadow a blockout does not cast.
    /// </summary>
    /// <remarks>
    /// Darker than every ground fill in this table, which is what makes it work on all of them
    /// rather than on the one it was picked against. Opaque: it goes in the bodies mesh, and that
    /// material does not read alpha.
    /// </remarks>
    public static readonly Color UnitShadow = new("07090c");
    public static readonly Color Panel = new("1b1f26", 0.92f);
    public static readonly Color GhostHue = new(HostileHue, 0.55f);
    public static readonly Color OverwatchHue = new("f2c14e");
    public static readonly Color AmbushHue = new("d95f9a");
    public static readonly Color LinkFill = new("c8a24a");
    public static readonly Color LinkText = new("f0d190");
    public static readonly Color UnitOutline = new("0a0c0f", 0.7f);

    /// <summary>The cursor's hex, outlined so the pick can be checked against the readout.</summary>
    public static readonly Color HoverEdge = new("dfe5ee", 0.8f);

    /// <summary>The firing mode: the line of fire and the ring round the target.</summary>
    /// <remarks>
    /// White, and neither side's hue nor the committed yellow. Hostile red on a line pointing at a
    /// hostile reads as a threat coming the other way, and yellow already means a walk that is
    /// paid for; an aim is neither of those — it is a question the player has not answered yet.
    /// </remarks>
    public static readonly Color AimColor = new("ffffff", 0.9f);

    /// <summary>An action bar slot that would do something if pressed, and one that would say no.</summary>
    /// <remarks>
    /// Both on the bar's own plate, so the difference is a step of lightness and not a colour: colour on
    /// the bar is kept for the edge that says which state landed, and a dimmed slot still shows its price.
    /// </remarks>
    public static readonly Color SlotReady = new("38414e");
    public static readonly Color SlotDim = new("15181c");

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

    /// <summary>
    /// A side's colour for a readout painted across the ground, rather than for a body.
    /// </summary>
    /// <remarks>
    /// <b>The one place a side is two colours, and the reason is that one of them covers the
    /// whole map.</b> The attention field tints every tile a soldier is attending to, out to its
    /// sight range, so five soldiers on the waystation put a wash of side colour over most of the
    /// ground. Raising <see cref="PlayerHue"/> and <see cref="HostileHue"/> to fix the
    /// play-through's fifth finding raised that wash with them and washed the terrain out
    /// altogether — a body that reads well against ground it has itself repainted has not been
    /// fixed. So the field keeps the values the two hues had before, which were chosen against
    /// the terrain and were never the thing that was wrong.
    /// <para>
    /// Side identity survives the split because hue is what carries it and hue is what is shared:
    /// green is ours and orange is theirs in the field, on the body, in the turn order and on the
    /// label. What differs is saturation, and only where the readout has to sit under something
    /// else rather than on top of it.
    /// </para>
    /// </remarks>
    public static Color AttentionHue(Side side) => side switch
    {
        Side.Player => new Color("74d3b4"),
        Side.Hostile => new Color("e0674a"),
        _ => new Color("aab2bd"),
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
