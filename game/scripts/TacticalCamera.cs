using Godot;

namespace Hexcom.Game;

/// <summary>
/// The tactical camera: a point on the ground it looks at, a distance back from it, a yaw and a
/// pitch. Each of the four eases towards a target, so every way of moving the camera feels the
/// same and a capture can skip the easing by landing on the targets at once.
/// </summary>
/// <remarks>
/// <para>
/// Controls are the genre's: WASD or the arrows pan, Q and E turn while held, the wheel
/// zooms, the middle button drags the ground, the right button orbits, the screen edges pan,
/// Shift hurries, Home (or F) recentres. Left click is untouched: it belongs to whatever will
/// be selected later.
/// </para>
/// <para>
/// Yaw is a compass bearing in radians: zero looks north (-Z) and it increases clockwise seen
/// from above. It is free: nothing snaps it to the hex grid's six bearings, by the user's
/// choice, so the grid will have to stay legible from any angle.
/// </para>
/// </remarks>
public partial class TacticalCamera : Node3D
{
    public const float Closest = 5f;
    public const float Furthest = 400f;
    public const float DefaultDistance = 40f;

    public const float LowestPitchDegrees = 12f;
    public const float HighestPitchDegrees = 85f;
    public const float DefaultPitchDegrees = 55f;

    public const float FieldOfView = 50f;

    /// <summary>How much one wheel notch multiplies or divides the distance.</summary>
    private const float ZoomStep = 1.2f;

    /// <summary>
    /// Keyboard pan speed as a share of the distance per second, so the ground crosses the screen
    /// in about the same time at any zoom.
    /// </summary>
    private const float PanRate = 0.7f;

    private const float FastMultiplier = 2.5f;

    /// <summary>How fast a held Q or E turns the camera.</summary>
    private const float TurnDegreesPerSecond = 90f;
    private const float OrbitRadiansPerPixel = 0.005f;
    private const float EdgeMarginPixels = 8f;

    /// <summary>How quickly each value closes on its target, per second. Larger is snappier.</summary>
    private const float Smoothing = 12f;

    private Camera3D _camera = null!;

    private Vector3 _focus, _focusTarget;
    private float _yaw, _yawTarget;
    private float _pitch, _pitchTarget;
    private float _distance, _distanceTarget;

    private bool _dragging, _orbiting;
    private Vector3 _grabbed;
    private Vector2 _orbitReturn;
    private Vector3 _pivot;

    /// <summary>Off during a capture, so nothing at the keyboard or the window edge can move the shot.</summary>
    public bool ControlsEnabled { get; set; } = true;

    /// <summary>The ground, for standing the focus on it and for finding what the cursor is over. Flat if null.</summary>
    public Rules.Terrain? Terrain { get; set; }

    /// <summary>Print every mouse button that arrives, for finding out what a mouse actually sends.</summary>
    public bool TraceInput { get; set; }

    /// <summary>The point on the ground being looked at, at the ground's height.</summary>
    public Vector3 Focus => OnGround(_focus);

    /// <summary>
    /// Whether a mouse button is moving the camera. The cursor is captured or busy holding the
    /// ground, so nothing else should read it as pointing at anything.
    /// </summary>
    public bool Dragging => _dragging || _orbiting;

    public float Distance => _distance;

    public override void _Ready()
    {
        Bindings.Ensure();

        _camera = new Camera3D { Fov = FieldOfView, Near = 0.3f, Far = 20000f, Current = true };
        AddChild(_camera);

        Home();
        Settle();
    }

    public override void _Process(double delta)
    {
        if (ControlsEnabled && !_dragging && !_orbiting)
        {
            ReadKeys((float)delta);
            EdgePan((float)delta);
        }

        Ease((float)delta);
        Place();
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (!ControlsEnabled) return;

        switch (@event)
        {
            case InputEventMouseButton button:
                OnButton(button);
                break;
            case InputEventMouseMotion motion:
                OnMotion(motion);
                break;
        }
    }

    /// <summary>Back to the origin, looking north from the default height and distance.</summary>
    public void Home()
    {
        _focusTarget = Vector3.Zero;
        _yawTarget = 0f;
        _pitchTarget = Mathf.DegToRad(DefaultPitchDegrees);
        _distanceTarget = DefaultDistance;
    }

    /// <summary>Set any of the four targets directly. Degrees for the angles; null leaves a value alone.</summary>
    public void Set(Vector2? focus = null, float? yawDegrees = null, float? pitchDegrees = null, float? distance = null)
    {
        if (focus is { } f) _focusTarget = new Vector3(f.X, 0f, f.Y);
        if (yawDegrees is { } y) _yawTarget = Mathf.DegToRad(y);
        if (pitchDegrees is { } p) _pitchTarget = Mathf.DegToRad(Mathf.Clamp(p, LowestPitchDegrees, HighestPitchDegrees));
        if (distance is { } d) _distanceTarget = Mathf.Clamp(d, Closest, Furthest);
    }

    /// <summary>Arrive at every target now. What a capture does instead of waiting.</summary>
    public void Settle()
    {
        _focus = _focusTarget;
        _yaw = _yawTarget;
        _pitch = _pitchTarget;
        _distance = _distanceTarget;
        Place();
    }

    /// <summary>One wheel notch in (positive) or out.</summary>
    public void Zoom(int notches)
        => _distanceTarget = Mathf.Clamp(_distanceTarget / Mathf.Pow(ZoomStep, notches), Closest, Furthest);

    private void ReadKeys(float delta)
    {
        var fast = Input.IsActionPressed(Bindings.Fast) ? FastMultiplier : 1f;

        var move = Input.GetVector(Bindings.Left, Bindings.Right, Bindings.Back, Bindings.Forward);
        if (move != Vector2.Zero)
        {
            var speed = _distanceTarget * PanRate * fast;
            _focusTarget += (Right() * move.X + Forward() * move.Y) * speed * delta;
        }

        // Held keys turn continuously, the way the mouse does; the easing gives them their
        // start and stop.
        var turn = Input.GetAxis(Bindings.TurnLeft, Bindings.TurnRight);
        if (turn != 0f) _yawTarget += turn * Mathf.DegToRad(TurnDegreesPerSecond) * fast * delta;

        if (Input.IsActionJustPressed(Bindings.Home)) Home();
    }

    /// <summary>Pan when the cursor rests against an edge of a focused window.</summary>
    private void EdgePan(float delta)
    {
        if (!GetWindow().HasFocus()) return;

        var mouse = GetViewport().GetMousePosition();
        var size = GetViewport().GetVisibleRect().Size;
        if (mouse.X < 0 || mouse.Y < 0 || mouse.X > size.X || mouse.Y > size.Y) return;

        var push = Vector2.Zero;
        if (mouse.X < EdgeMarginPixels) push.X -= 1;
        if (mouse.X > size.X - EdgeMarginPixels) push.X += 1;
        if (mouse.Y < EdgeMarginPixels) push.Y += 1;
        if (mouse.Y > size.Y - EdgeMarginPixels) push.Y -= 1;
        if (push == Vector2.Zero) return;

        _focusTarget += (Right() * push.X + Forward() * push.Y) * _distanceTarget * PanRate * delta;
    }

    private void OnButton(InputEventMouseButton button)
    {
        if (TraceInput) GD.Print($"mouse {button.ButtonIndex} {(button.Pressed ? "down" : "up")} at {button.Position}");

        switch (button.ButtonIndex)
        {
            case MouseButton.WheelUp when button.Pressed:
                Zoom(1);
                break;
            case MouseButton.WheelDown when button.Pressed:
                Zoom(-1);
                break;

            case MouseButton.Middle:
                if (button.Pressed && GroundUnder(button.Position) is { } point)
                {
                    _dragging = true;
                    _grabbed = point;
                }
                else
                {
                    _dragging = false;
                    if (TraceInput) GD.Print($"drag ended with focus {_focus}");
                }
                break;

            case MouseButton.Right:
                if (button.Pressed)
                {
                    // The orbit turns about the ground under the cursor, or about the focus
                    // when the cursor is on the sky.
                    _orbiting = true;
                    _orbitReturn = button.Position;
                    _pivot = GroundUnder(button.Position) ?? _focus;
                    Input.MouseMode = Input.MouseModeEnum.Captured;
                }
                else if (_orbiting)
                {
                    _orbiting = false;
                    Input.MouseMode = Input.MouseModeEnum.Visible;
                    Input.WarpMouse(_orbitReturn);
                }
                break;
        }
    }

    private void OnMotion(InputEventMouseMotion motion)
    {
        if (_orbiting)
        {
            // Dragging right swings the camera to the right around the pivot; dragging up tilts
            // it towards top-down. Direct rather than eased: a drag is already continuous under
            // the hand, and the pivot only stays pinned if the camera is where the maths put it.
            _yawTarget += motion.Relative.X * OrbitRadiansPerPixel;
            _pitchTarget = Mathf.Clamp(
                _pitchTarget - motion.Relative.Y * OrbitRadiansPerPixel,
                Mathf.DegToRad(LowestPitchDegrees),
                Mathf.DegToRad(HighestPitchDegrees));
            _yaw = _yawTarget;
            _pitch = _pitchTarget;
            Place();

            // Turning about the focus moved the pivot on screen; slide the focus so the pivot
            // is back under the cursor. A translation is exact, so one correction does it.
            if (GroundUnder(_orbitReturn) is { } now)
            {
                var shift = _pivot - now;
                shift.Y = 0f;
                _focus += shift;
                _focusTarget = _focus;
                Place();
            }
        }
        else if (_dragging && GroundUnder(motion.Position) is { } under)
        {
            // The ground point grabbed stays under the cursor. Moving the camera is a pure
            // translation, so on flat ground one correction is exact; on a hill the next
            // motion event corrects the little that the changing height leaves over.
            var shift = _grabbed - under;
            shift.Y = 0f;
            _focusTarget += shift;
            _focus += shift;
            Place();
        }
    }

    /// <summary>Where the ray through a screen point meets the ground, or null if it never does within reason.</summary>
    /// <remarks>
    /// Marched along the height function rather than intersected with a plane, in steps that
    /// start at half a metre and grow with distance, then bisected to the millimetre. A couple
    /// of hundred height samples at most, which is nothing per frame.
    /// </remarks>
    public Vector3? GroundUnder(Vector2 screen)
    {
        var origin = _camera.ProjectRayOrigin(screen);
        var direction = _camera.ProjectRayNormal(screen);
        var limit = Mathf.Max(200f, _distance * 20f);

        if (Terrain is null)
        {
            if (direction.Y >= -1e-4f) return null;
            var flat = -origin.Y / direction.Y;
            return flat > limit ? null : origin + direction * flat;
        }

        float Above(float at)
        {
            var p = origin + direction * at;
            return p.Y - (float)Terrain.Height(p.X, p.Z);
        }

        if (Above(0f) <= 0f) return null;

        var previous = 0f;
        var step = 0.5f;
        for (var t = step; t < limit; t += step)
        {
            if (Above(t) <= 0f)
            {
                float low = previous, high = t;
                for (var i = 0; i < 12; i++)
                {
                    var mid = (low + high) / 2f;
                    if (Above(mid) <= 0f) high = mid;
                    else low = mid;
                }
                return origin + direction * high;
            }

            if (direction.Y >= 0f && origin.Y + direction.Y * t > 80f) return null;
            previous = t;
            step = Mathf.Max(0.5f, t * 0.02f);
        }

        return null;
    }

    private Vector3 OnGround(Vector3 point)
        => new(point.X, Terrain is null ? 0f : (float)Terrain.Height(point.X, point.Z), point.Z);

    private void Ease(float delta)
    {
        var t = 1f - Mathf.Exp(-Smoothing * delta);

        _focus = _focus.Lerp(_focusTarget, t);
        _yaw = Mathf.Lerp(_yaw, _yawTarget, t);
        _pitch = Mathf.Lerp(_pitch, _pitchTarget, t);

        // Distance eases in log space, so a notch in feels like a notch out.
        _distance = Mathf.Exp(Mathf.Lerp(Mathf.Log(_distance), Mathf.Log(_distanceTarget), t));
    }

    /// <summary>The direction along the ground the camera looks in.</summary>
    private Vector3 Forward() => new(Mathf.Sin(_yaw), 0f, -Mathf.Cos(_yaw));

    private Vector3 Right() => new(Mathf.Cos(_yaw), 0f, Mathf.Sin(_yaw));

    private void Place()
    {
        var ground = OnGround(_focus);
        var back = -Forward() * (_distance * Mathf.Cos(_pitch));
        var up = Vector3.Up * (_distance * Mathf.Sin(_pitch));

        // Never inside a hill: a low camera behind a rise is lifted just clear of it.
        var position = ground + back + up;
        if (Terrain is not null)
        {
            position.Y = Mathf.Max(position.Y, (float)Terrain.Height(position.X, position.Z) + 1.5f);
        }

        _camera.Position = position;
        _camera.LookAt(ground, Vector3.Up);
    }
}
