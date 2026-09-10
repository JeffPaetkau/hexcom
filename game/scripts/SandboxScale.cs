using Godot;
using Hexcom.Core.Hexes;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;

namespace Hexcom.Game;

/// <summary>
/// The one layout the rules are given, in metres, and the mapping from the plane the rules
/// compute in to the space the engine draws in.
/// </summary>
/// <remarks>
/// <para>
/// This type used to hold two layouts — the world in metres and a canvas in pixels — because a
/// flat view has to draw a two-metre hex forty-four pixels wide, and the day it handed the
/// pixels layout to <c>Battle</c> instead was the bug <c>docs/decisions.md</c> entries 002 and
/// 005 describe: every range in the game compared against a distance twenty times too long, and
/// a stealth game in which nobody could be detected. In three dimensions one engine unit is one
/// metre and the second layout is gone, so the conversion this type existed to police is now a
/// conversion of one.
/// </para>
/// <para>
/// <b>It stays anyway, and the reason is entry 005.</b> Contract 5 in <c>docs/map.md</c> says
/// rendering scale is never fed into <c>Battle</c>, and the place that makes that enforceable
/// rather than merely true is the place that owns the layout the battle is given. It is one
/// property now. The next session to see a class with one property in it will want to inline it
/// at the call site, and the call site is exactly where a zoom factor would one day get
/// multiplied in — because the camera lives there, and a camera that moves the world scale is
/// the bug all over again, one frame at a time. So <see cref="World"/> is built here, from a
/// constant, and nothing that knows about the camera may build a layout.
/// </para>
/// <para>
/// What it also owns is the axis mapping. The rules compute on a plane with Y running north and
/// heights in metres above it; Godot draws with Y running up and Z running towards the viewer.
/// So a rules point <c>(x, y)</c> at height <c>h</c> is drawn at <c>(x, h, -y)</c>, and a bearing
/// the rules quote from east towards north is a direction <c>(cos, 0, -sin)</c> on the ground.
/// Every conversion goes through the two methods below, because the one place that knows the
/// sign of Z is the one place a mirror-image map cannot be introduced from.
/// </para>
/// </remarks>
public static class SandboxScale
{
    /// <summary>
    /// How many metres one hex radius is worth. <b>Decided.</b>
    /// </summary>
    /// <remarks>
    /// 1.0 — a hex two metres corner to corner and 1.73 metres between centres, which is one
    /// soldier's standing space, because a soldier occupies exactly one and walls sit on its
    /// edges. <c>docs/decisions.md</c> entry 007 is where it was chosen and why. It is a constant
    /// and not an <c>[Export]</c> deliberately: world scale is a rule the tests, the awareness
    /// ranges and eventually the art all agree on, and a value the inspector can quietly
    /// override is not a rule.
    /// </remarks>
    public const double MetresPerHexSize = 1.0;

    /// <summary>Metres. The only layout <c>Hexcom.Core</c> is ever given.</summary>
    public static readonly HexLayout World = new(MetresPerHexSize);

    /// <summary>A point on the rules' plane at a height above it, as a point in the scene.</summary>
    public static Vector3 ToScene(CoreVec2 plane, double height)
        => new((float)plane.X, (float)height, (float)-plane.Y);

    /// <summary>A point in the scene, back to the rules' plane. The height is dropped.</summary>
    public static CoreVec2 ToPlane(Vector3 scene) => new(scene.X, -scene.Z);

    /// <summary>A bearing the rules quote — radians from east towards north — as a direction along the ground.</summary>
    public static Vector3 Along(double bearingRadians)
        => new((float)System.Math.Cos(bearingRadians), 0f, (float)-System.Math.Sin(bearingRadians));
}
