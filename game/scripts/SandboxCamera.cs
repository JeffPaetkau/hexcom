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
/// A pitched camera with a free yaw that <em>rests</em> on the six hex bearings. Entry 053 made
/// the yaw snap outright, on the grounds that a held arc is legible only from a camera that
/// agrees with the grid it is drawn on; the first play-through overruled it (entry 057, item 2)
/// and the arcs have had to stay legible anyway. What is left of 053's argument is the resting
/// places: <see cref="Turn"/> moves between bearings and lands on one, so a player who only ever
/// presses <c>Q</c> and <c>E</c> sees exactly the six views 053 chose, and the free orbit is
/// what the mouse does in between. The pitch is still fixed — what a person loses is the ability
/// to look along a wall, and nothing has wanted to.
/// </para>
/// <para>
/// <b>Nothing here animates unless something is driving it.</b> The yaw moves towards
/// <see cref="Turning"/> only when <see cref="Advance"/> is called, and a capture never calls it:
/// <c>HexSandbox</c> holds one <c>Animated</c> flag, false whenever a picture is being taken, and
/// with it false every method below lands on its end state within the call. That is the single
/// settle mechanism the brief asked for — forcing instantly rather than waiting for a settle —
/// and it is what keeps a capture on exactly the code path it was byte-deterministic on.
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
/// moving it — the keys, the wheel, a drag, an orbit, a script step, the follow after an action
/// — goes through the same clamps and the same snap. Panning, zooming and orbiting still rewrite
/// the transform within the call and are not animated at all: they are already continuous under
/// the hand doing them, and smoothing a drag only adds lag to it.
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

    /// <summary>The angle between two neighbouring hex bearings, radians.</summary>
    private const double BearingStep = System.Math.Tau / 6;

    /// <summary>
    /// How sharply a turn closes on the bearing it is heading for, per second.
    /// </summary>
    /// <remarks>
    /// The step taken each frame is the angle still to go times this, which eases out — fast
    /// while the turn is obviously happening and slow as it arrives, the way a head turns. On its
    /// own it would never quite arrive, so <see cref="MinTurnRate"/> puts a floor under the last
    /// few degrees and the step is clamped to what is left. A sixty-degree turn takes about a
    /// fifth of a second, which is long enough to follow and short enough that pressing
    /// <c>Q</c> four times in a row does not feel like queueing.
    /// </remarks>
    private const double TurnResponse = 14.0;

    /// <summary>The slowest a turn may crawl, radians per second, so it arrives rather than approaches.</summary>
    private const double MinTurnRate = BearingStep * 1.5;

    private readonly Camera3D _camera;

    private double _yaw = ((HexDirection)1).BearingRadians();
    private double? _turningTo;

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
    /// The nearest of the six hex bearings to where the camera is actually pointed.
    /// </summary>
    /// <remarks>
    /// One by default, which is north: the camera stands to the south of the focus looking
    /// north, so up the screen is up the map the way the flat view had it, and a capture of the
    /// same command shows the same map the same way up. It is derived rather than stored now
    /// that the yaw is free — it is what a person <em>means</em> when they say which way they
    /// are looking, and it is the only form of the yaw anything outside this class wants.
    /// </remarks>
    public int Yaw => (int)((System.Math.Round((_yaw - BearingStep / 2) / BearingStep) % 6 + 6) % 6);

    /// <summary>The bearing being looked along, in the rules' radians. Continuous.</summary>
    public double YawRadians => _yaw;

    /// <summary>Where a turn is heading, or null when the camera is pointed where it was asked to be.</summary>
    public double? Turning => _turningTo;

    /// <summary>Whether nothing is moving of its own accord, so a picture may be taken.</summary>
    public bool Settled => _turningTo is null;

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

    /// <summary>
    /// Head for the next hex bearing left or right, keeping the focus where it is.
    /// </summary>
    /// <remarks>
    /// Counted from where the camera is <em>heading</em> rather than from where it has got to, so
    /// that three quick presses of <c>Q</c> turn three bearings instead of collapsing into one
    /// while the first is still under way. From a free orbit the first press lands on the nearest
    /// bearing in the direction asked for, which is what tidying up with the keyboard should do.
    /// </remarks>
    public void Turn(int steps)
    {
        var from = _turningTo ?? _yaw;
        var index = (from - BearingStep / 2) / BearingStep;

        // Away from a bearing the first step goes to the next one in the direction asked for
        // rather than past it, which is what Ceiling and Floor do that Round would not.
        var landing = steps > 0 ? System.Math.Ceiling(index) : System.Math.Floor(index);
        if (System.Math.Abs(landing - index) < 1e-6) landing = index + steps;
        else if (System.Math.Abs(steps) > 1) landing += steps - System.Math.Sign(steps);

        HeadFor(BearingStep / 2 + landing * BearingStep);
    }

    /// <summary>Face a bearing directly, by direction index.</summary>
    /// <remarks>
    /// <c>--yaw N</c> and nothing else. It arrives within the call rather than heading for the
    /// bearing, because a script step that took frames to finish would put the same command in a
    /// different place depending on how many it was given — which is the determinism entry 053
    /// established and item 2 of the play-through was not allowed to undo.
    /// </remarks>
    public void TurnTo(int yaw)
    {
        _turningTo = null;
        _yaw = ((HexDirection)((yaw % 6 + 6) % 6)).BearingRadians();
        Place();
    }

    /// <summary>
    /// Turn by an arbitrary angle, abandoning any bearing the camera was heading for.
    /// </summary>
    /// <remarks>
    /// What a drag does. There is no snap at the end of one: a mouse that tidied itself up when
    /// released would be taking the view back off the person holding it, and <c>Q</c> and
    /// <c>E</c> are there for anybody who wants a bearing.
    /// </remarks>
    public void Orbit(double radians)
    {
        _turningTo = null;
        _yaw = Wrapped(_yaw + radians);
        Place();
    }

    /// <summary>
    /// Move a turn along by one frame's worth, and say whether it is still going.
    /// </summary>
    /// <remarks>
    /// The one thing here that takes time, and the only reason <c>HexSandbox</c> processes at
    /// all when it is not capturing. A capture never calls it and never needs to: with animation
    /// off <see cref="Turn"/> lands within the call, so there is nothing part-way through for a
    /// picture to catch.
    /// </remarks>
    public bool Advance(double delta)
    {
        if (_turningTo is not { } target) return false;

        var remaining = Wrapped(target - _yaw + System.Math.PI) - System.Math.PI;
        var step = System.Math.Max(System.Math.Abs(remaining) * TurnResponse, MinTurnRate) * delta;

        if (step >= System.Math.Abs(remaining))
        {
            _yaw = Wrapped(target);
            _turningTo = null;
        }
        else _yaw = Wrapped(_yaw + System.Math.Sign(remaining) * step);

        Place();
        return _turningTo is not null;
    }

    /// <summary>Arrive at a bearing now, wherever a turn had got to. What <c>Animated</c> being off means here.</summary>
    public void Settle()
    {
        if (_turningTo is not { } target) return;
        _turningTo = null;
        _yaw = Wrapped(target);
        Place();
    }

    private void HeadFor(double bearing)
    {
        _turningTo = Wrapped(bearing);
        Place();
    }

    private static double Wrapped(double radians)
        => (radians % System.Math.Tau + System.Math.Tau) % System.Math.Tau;

    /// <summary>
    /// How far <see cref="Fit"/> looks past the middle of the map, as a share of its radius, so the
    /// near rim clears the legend.
    /// </summary>
    /// <remarks>
    /// Brief one's test for a capture at <c>--fit</c> is that no text lies over the map unless it is
    /// attached to something on it, and the legend along the bottom edge is attached to nothing. A
    /// pitched camera puts the near rim of a centred map lower on screen than the far rim is high,
    /// and on the waystation at 1600 by 900 the near rim ran under the legend. Pulling back alone did
    /// not clear it — a quarter further out and the rim was still under — because most of the fault
    /// is where the map sits rather than how big it is. So the view looks this far past the middle,
    /// which lifts the whole map, and stands a little further back than it did (<see cref="FitDistance"/>).
    /// Measured on the waystation and the compound, where the near rim now stops at the legend's edge.
    /// </remarks>
    private const float FitLead = 0.16f;

    /// <summary>How much of the over-estimated distance <see cref="Fit"/> keeps. It was 0.8; see <see cref="FitLead"/>.</summary>
    private const float FitDistance = 0.9f;

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

        Focus = middle - new CoreVec2(System.Math.Cos(YawRadians), System.Math.Sin(YawRadians)) * (radius * FitLead);
        FocusHeight = 0;
        ZoomTo(Mathf.Max(vertical, horizontal) * FitDistance);
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
