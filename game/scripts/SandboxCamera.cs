using System.Linq;
using Godot;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;

namespace Hexcom.Game;

/// <summary>
/// Where the map is being looked at from: a point on the ground, a distance back from it, and
/// one of six directions to look along.
/// </summary>
/// <remarks>
/// <para>
/// A pitched camera whose yaw snaps to the six hex bearings, which is the fourth decision in
/// the greybox brief and the one that keeps the arcs legible. Facing is a rule here — six body
/// faces, arcs measured from <c>Unit.Facing</c>, a front cone of 120 degrees — and a wedge on
/// the ground is readable only when the camera agrees with the grid it is drawn on. From a
/// free orbit every wedge is a different shape at every angle; from a bearing the hexes tile
/// the screen the same way at every step of the turn, so a player learns what a held arc looks
/// like once. The pitch is fixed for the same reason. What a person loses is the ability to
/// look along a wall, and a blockout is not the view to find out whether they need to.
/// </para>
/// <para>
/// <b>Distance is a drawing figure and nothing else.</b> The camera moves itself and never the
/// layout: <see cref="SandboxScale.World"/> is a constant the camera cannot reach, which is
/// contract 5 in <c>docs/map.md</c> kept the same way the flat view kept it. Zooming in three
/// dimensions is a distance, and <c>--zoom N</c> is now metres back from the ground rather than
/// pixels to a hex; the threshold below which tiles carry their own labels moved with it, see
/// <see cref="LegibleAt"/>.
/// </para>
/// <para>
/// The camera is looked at through this class and never touched directly, so that every way of
/// moving it — the keys, the wheel, a drag, a script step, the follow after an action — goes
/// through the same clamps and the same snap. It rewrites the node's transform whenever
/// anything changes rather than animating towards it: a capture has to land on the same frame
/// every run, and a smoothed camera would put the same command in a different place depending
/// on how many frames it was given.
/// </para>
/// </remarks>
public sealed class SandboxCamera
{
    /// <summary>Closest the camera may come to the ground, in metres.</summary>
    public const float Closest = 6f;

    /// <summary>Furthest back it may go. The waystation fits a 1600 by 900 viewport at about 120.</summary>
    public const float Furthest = 260f;

    /// <summary>
    /// Beyond this distance a tile stops carrying its own detail — cost labels, cover outlines,
    /// the region inset.
    /// </summary>
    /// <remarks>
    /// The flat view switched its detail off below 22 pixels to a hex radius, on the grounds that
    /// a two-digit AP cost set at 15 points does not fit in a 14-pixel hex. The same hex is
    /// drawn at about 1650 / distance pixels across from this camera — a 50 degree field over
    /// a 900 pixel viewport — so the same threshold is a distance of about 70 metres. Past it,
    /// what survives is what is legible: ground, walls, soldiers, and who is attending to where.
    /// </remarks>
    public const float LegibleAt = 70f;

    /// <summary>Vertical field of view, degrees.</summary>
    public const float FieldOfView = 50f;

    /// <summary>How far above the horizontal the camera looks down, degrees.</summary>
    /// <remarks>
    /// Steep enough that a hex reads as a hex rather than as a strip, and shallow enough that a
    /// three-metre wall has a visible side. Fifty-five is the usual compromise for a tactics
    /// game and nothing here argues for a different one yet.
    /// </remarks>
    public const float PitchDegrees = 55f;

    /// <summary>How much a wheel notch or a zoom key changes the distance.</summary>
    private const float ZoomStep = 1.25f;

    private readonly Camera3D _camera;

    public SandboxCamera(Camera3D camera, float distance)
    {
        _camera = camera;
        _camera.Fov = FieldOfView;
        _camera.Near = 0.5f;
        _camera.Far = 1000f;
        Distance = Mathf.Clamp(distance, Closest, Furthest);
        Place();
    }

    /// <summary>The point on the ground the camera is looking at, on the rules' plane.</summary>
    public CoreVec2 Focus { get; private set; }

    /// <summary>The height of the ground under the focus, so that stepping onto a roof lifts the view with it.</summary>
    public double FocusHeight { get; private set; }

    /// <summary>Metres from the focus back to the camera.</summary>
    public float Distance { get; private set; }

    /// <summary>
    /// Which of the six hex bearings the camera looks along, as a direction index.
    /// </summary>
    /// <remarks>
    /// One by default, which is north: the camera stands to the south of the focus looking
    /// north, so up the screen is up the map the way the flat view had it, and a capture of the
    /// same command shows the same map the same way up.
    /// </remarks>
    public int Yaw { get; private set; } = 1;

    /// <summary>The bearing being looked along, in the rules' radians.</summary>
    public double YawRadians => ((HexDirection)Yaw).BearingRadians();

    /// <summary>Whether a tile is currently close enough to be worth labelling. See <see cref="LegibleAt"/>.</summary>
    public bool ShowsTileDetail => Distance <= LegibleAt;

    /// <summary>Look at a point on the plane, at a height.</summary>
    public void LookAt(CoreVec2 plane, double height)
    {
        Focus = plane;
        FocusHeight = height;
        Place();
    }

    /// <summary>Look at the middle of a hex, at the floor height of the tile there.</summary>
    public void LookAt(BattleMap map, Hex hex, int layer)
    {
        var height = map.GetTile(new TileAddress(hex, layer))?.FloorHeight ?? layer * map.LayerHeight;
        LookAt(SandboxScale.World.Center(hex), height);
    }

    /// <summary>
    /// Drag the ground by a screen distance — the cursor keeps hold of what is under it, near
    /// enough.
    /// </summary>
    /// <remarks>
    /// Near enough because the ground is foreshortened: a pixel near the top of the screen is
    /// more metres than one near the bottom. The drag uses the scale at the focus, which is the
    /// middle of the screen, so a drag started there tracks exactly and one started at the top
    /// runs a little slow. A drag that tracked perfectly would need the pick ray, and a pan is
    /// not worth a ray.
    /// </remarks>
    public void Pan(Vector2 screen, Vector2 viewport)
    {
        var metresPerPixel = 2f * Distance * Mathf.Tan(Mathf.DegToRad(FieldOfView / 2f)) / viewport.Y;

        var forward = new CoreVec2(System.Math.Cos(YawRadians), System.Math.Sin(YawRadians));
        var right = new CoreVec2(forward.Y, -forward.X);

        // Dragging right moves the ground right, so the focus goes left; dragging down moves it
        // down the screen, which is towards the camera, so the focus goes forward.
        Focus -= (right * screen.X - forward * screen.Y / Mathf.Sin(Mathf.DegToRad(PitchDegrees))) * metresPerPixel;
        Place();
    }

    /// <summary>One notch in or out.</summary>
    public void ZoomBy(int notches) => ZoomTo(Distance / Mathf.Pow(ZoomStep, notches));

    /// <summary>Move to a distance, clamped.</summary>
    public void ZoomTo(float distance)
    {
        Distance = Mathf.Clamp(distance, Closest, Furthest);
        Place();
    }

    /// <summary>Turn one bearing left or right, keeping the focus where it is.</summary>
    public void Turn(int steps)
    {
        Yaw = ((Yaw + steps) % 6 + 6) % 6;
        Place();
    }

    /// <summary>Face a bearing directly, by direction index.</summary>
    public void TurnTo(int yaw)
    {
        Yaw = (yaw % 6 + 6) % 6;
        Place();
    }

    /// <summary>
    /// Pull back until the whole map is on screen at once.
    /// </summary>
    /// <remarks>
    /// Every storey, not the one being drawn, and worked out from the map's own extent rather
    /// than told. The map is treated as a disc of the radius its furthest tile is at, and the
    /// distance is what puts that disc inside the narrower of the two fields of view — the
    /// vertical one directly, the horizontal one through the viewport's aspect. Pitch
    /// foreshortens the disc vertically, which is why the vertical term is the binding one on a
    /// wide viewport: the map is a squashed ellipse that is still as wide as it ever was.
    /// </remarks>
    public void Fit(BattleMap map, Vector2 viewport)
    {
        var hexes = map.Tiles.Select(t => t.Address.Hex).Distinct().ToList();
        if (hexes.Count == 0) return;

        var layout = SandboxScale.World;
        var centres = hexes.Select(layout.Center).ToList();
        var middle = centres.Aggregate(CoreVec2.Zero, (a, b) => a + b) / centres.Count;
        var radius = (float)centres.Max(c => CoreVec2.Distance(c, middle)) + (float)layout.Size;

        var half = Mathf.DegToRad(FieldOfView / 2f);
        var aspect = viewport.X / viewport.Y;

        // The disc seen from a pitched camera: its front edge is nearer and lower on screen,
        // its back edge further and higher. Treating it as a sphere of the same radius is the
        // simple over-estimate, and then a little more so the edge tiles are not on the border.
        var vertical = radius / Mathf.Sin(half);
        var horizontal = radius / Mathf.Sin(Mathf.Atan(Mathf.Tan(half) * aspect));

        Focus = middle;
        FocusHeight = 0;
        ZoomTo(Mathf.Max(vertical, horizontal) * 0.8f);
    }

    /// <summary>Where a scene point lands on the screen, or null if it is behind the camera.</summary>
    public Vector2? Project(Vector3 scene)
        => _camera.IsPositionBehind(scene) ? null : _camera.UnprojectPosition(scene);

    /// <summary>The ray through a screen point, for picking.</summary>
    public (Vector3 Origin, Vector3 Direction) Ray(Vector2 screen)
        => (_camera.ProjectRayOrigin(screen), _camera.ProjectRayNormal(screen));

    /// <summary>Whether a scene point is comfortably in shot — inside the middle of the screen.</summary>
    public bool Frames(Vector3 scene, Vector2 viewport, float marginFraction = 0.2f)
    {
        if (Project(scene) is not { } at) return false;
        var margin = viewport * marginFraction;
        return new Rect2(margin, viewport - margin * 2).HasPoint(at);
    }

    private void Place()
    {
        var pitch = Mathf.DegToRad(PitchDegrees);
        var back = SandboxScale.Along(YawRadians) * (-Distance * Mathf.Cos(pitch));
        var up = Vector3.Up * (Distance * Mathf.Sin(pitch));

        var target = SandboxScale.ToScene(Focus, FocusHeight);
        _camera.Position = target + back + up;
        _camera.LookAt(target, Vector3.Up);
    }
}
