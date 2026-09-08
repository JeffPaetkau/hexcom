using System.Collections.Generic;
using Hexcom.Core.Battles;
using Hexcom.Core.Movement;
using Hexcom.Core.Vision;

namespace Hexcom.Game;

/// <summary>Everything the sandbox has worked out about the current moment, ready to be drawn.</summary>
/// <param name="Battle">The battle itself. Queried, never changed, by anything that takes a frame.</param>
/// <param name="Layer">Which storey is on screen. The sandbox looks at one at a time.</param>
/// <param name="Hover">The node under the cursor, if it is over the map at all.</param>
/// <param name="Reach">Where the active unit could get to, and for what.</param>
/// <param name="View">What the active unit can make out, per node on the current layer.</param>
/// <param name="LastWindow">What the last committed move got shot at with. Debug readout only.</param>
/// <remarks>
/// This exists so that drawing has no way to reach back into the node and ask another question.
/// A frame is assembled once, in <see cref="HexSandbox.Recalculate"/>, and everything drawn from
/// it is drawn from the same answers — which is also what stops the map and the readouts
/// disagreeing about a unit that a reaction moved half way through the frame.
/// </remarks>
public sealed record SandboxFrame(
    Battle Battle,
    int Layer,
    NodeId? Hover,
    ReachabilityResult Reach,
    IReadOnlyDictionary<NodeId, SightResult> View,
    string LastWindow);
