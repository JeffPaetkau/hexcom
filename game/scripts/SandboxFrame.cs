using System.Collections.Generic;
using Hexcom.Core.Battles;
using Hexcom.Core.Movement;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Game;

/// <summary>One turn <see cref="Commander"/> took in the sandbox, and what it chose to do with it.</summary>
/// <param name="Unit">Whose turn it was.</param>
/// <param name="Orders">What it did, in order, each carrying the appraisal it was picked on.</param>
/// <param name="Banked">What it had left when the turn ended, which is what it can react with.</param>
/// <remarks>
/// <see cref="Order"/> already carries the reasoning; this only remembers whose it was, because
/// by the time the frame is drawn the unit has finished and the battle has moved on to somebody
/// else. What it does <b>not</b> carry is what the orders <em>did</em> — a move's reaction window,
/// a shot's outcome — because <c>Commander.TakeTurn</c> does not return those. See entry 020 in
/// <c>docs/decisions.md</c>.
/// </remarks>
public sealed record TakenTurn(Unit Unit, IReadOnlyList<Order> Orders, int Banked);

/// <summary>Everything the sandbox has worked out about the current moment, ready to be drawn.</summary>
/// <param name="Battle">The battle itself. Queried, never changed, by anything that takes a frame.</param>
/// <param name="Layer">Which storey is on screen. The sandbox looks at one at a time.</param>
/// <param name="Hover">The node under the cursor, if it is over the map at all.</param>
/// <param name="Reach">Where the active unit could get to, and for what.</param>
/// <param name="View">What the active unit can make out, per node on the current layer.</param>
/// <param name="LastWindow">What the last committed move got shot at with. Debug readout only.</param>
/// <param name="Turns">
/// The turns <see cref="Commander"/> has taken since a person last did anything, newest last.
/// Empty until somebody hands it a turn.
/// </param>
/// <param name="HostilesAutomatic">Whether every hostile turn goes to <see cref="Commander"/>.</param>
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
    string LastWindow,
    IReadOnlyList<TakenTurn> Turns,
    bool HostilesAutomatic);
