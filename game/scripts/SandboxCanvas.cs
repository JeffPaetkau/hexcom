using Godot;

namespace Hexcom.Game;

/// <summary>
/// A flat surface over the picture that draws whatever it is handed.
/// </summary>
/// <remarks>
/// The scene is three-dimensional now and the readouts are not: text is set at a point size and
/// stays legible at any distance, which is the lesson the flat view learned the hard way about
/// labels quoted in hex radii. So the map's labels and the HUD both draw here, on a
/// <c>CanvasLayer</c> over the viewport, in screen pixels. <b>Three</b> of these hang under the
/// sandbox — <see cref="BattleView"/>'s labels, <see cref="BattleHud"/>'s player readouts, and a
/// third inside the instruments window for its other half — so that no class can reach another's
/// drawing, which is the boundary entry 014 in <c>docs/decisions.md</c> is about.
/// <para>
/// The third one is a child of a <c>Window</c> rather than of a <c>CanvasLayer</c>, because a
/// window is a viewport of its own and a <c>Node2D</c> under it draws in it. That is the whole of
/// what putting the instruments on another monitor took.
/// </para>
/// </remarks>
public partial class SandboxCanvas : Node2D
{
    /// <summary>What to draw, given this item to draw on. Set once, called on every redraw.</summary>
    public System.Action<CanvasItem>? Painter { get; set; }

    public override void _Draw() => Painter?.Invoke(this);
}
