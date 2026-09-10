using Godot;

namespace Hexcom.Game;

/// <summary>
/// A flat surface over the picture that draws whatever it is handed.
/// </summary>
/// <remarks>
/// The scene is three-dimensional now and the readouts are not: text is set at a point size and
/// stays legible at any distance, which is the lesson the flat view learned the hard way about
/// labels quoted in hex radii. So the map's labels and the HUD both draw here, on a
/// <c>CanvasLayer</c> over the viewport, in screen pixels. Two of these hang under the sandbox —
/// one for <see cref="BattleView"/>'s labels and one for <see cref="BattleHud"/> — so that
/// neither class can reach the other's drawing, which is the boundary entry 014 in
/// <c>docs/decisions.md</c> is about.
/// </remarks>
public partial class SandboxCanvas : Node2D
{
    /// <summary>What to draw, given this item to draw on. Set once, called on every redraw.</summary>
    public System.Action<CanvasItem>? Painter { get; set; }

    public override void _Draw() => Painter?.Invoke(this);
}
