using Godot;

namespace Hexcom.Game;

/// <summary>
/// The keyboard actions the camera reads, registered in code so they live next to the thing
/// that uses them and are checked by the compiler. Rebinding later means editing one table.
/// </summary>
public static class Bindings
{
    public const string Forward = "camera_forward";
    public const string Back = "camera_back";
    public const string Left = "camera_left";
    public const string Right = "camera_right";
    public const string TurnLeft = "camera_turn_left";
    public const string TurnRight = "camera_turn_right";
    public const string Fast = "camera_fast";
    public const string Home = "camera_home";

    /// <summary>Register every action that is not already in the input map.</summary>
    public static void Ensure()
    {
        Add(Forward, Key.W, Key.Up);
        Add(Back, Key.S, Key.Down);
        Add(Left, Key.A, Key.Left);
        Add(Right, Key.D, Key.Right);
        Add(TurnLeft, Key.Q);
        Add(TurnRight, Key.E);
        Add(Fast, Key.Shift);
        Add(Home, Key.Home, Key.F);
    }

    private static void Add(string action, params Key[] keys)
    {
        if (InputMap.HasAction(action)) return;

        InputMap.AddAction(action);
        foreach (var key in keys)
        {
            // Physical keys, so that WASD is the same four keys on any keyboard layout.
            InputMap.ActionAddEvent(action, new InputEventKey { PhysicalKeycode = key });
        }
    }
}
