using System.Collections.Generic;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Reactions;

/// <summary>
/// One instant on a committed move: where the mover is, and which way it is looking.
/// </summary>
/// <param name="Tick">
/// Action points spent getting here from the start of the move. The clock inside a reaction
/// window is denominated in action points, so this is both a price and a time.
/// </param>
public readonly record struct MoveStep(int Tick, NodeId Node, HexDirection Facing)
{
    public override string ToString() => $"t{Tick}: {Node} facing {Facing}";
}

/// <summary>
/// A route a unit has committed to, read as a timeline.
/// </summary>
/// <remarks>
/// This is the whole trick behind the reaction window, and it costs almost nothing because the
/// data was already there. A route arrives from the pathfinder as a list of links with an
/// action point price on each, so "where will the mover be once three points have been spent"
/// is arithmetic over a running total. Nothing new has to be simulated.
/// <para>
/// The consequence is that a reactor is not choosing between shooting before the move and
/// shooting after it. It is choosing a moment. An action started at tick <c>t</c> costing
/// <c>k</c> lands at <c>t + k</c>, against wherever the mover will be by then — which is why a
/// bad, cheap shot that catches somebody in the open beats a good, slow one that arrives after
/// they have reached cover.
/// </para>
/// <para>
/// Stance is fixed for the duration: changing it is an action of its own, and a unit cannot
/// take one while a committed move is running.
/// </para>
/// </remarks>
public sealed class CommittedMove
{
    private readonly MoveStep[] _steps;

    /// <param name="costs">
    /// What the mover pays per link. The timeline has to be priced the same way the route was, or
    /// the clock a reaction lands on stops matching the points that were actually spent.
    /// </param>
    public CommittedMove(
        NodeId start,
        IReadOnlyList<TraversalLink> path,
        HexDirection facing,
        Stance stance,
        CostProfile? costs = null)
    {
        Stance = stance;
        var pricing = costs ?? CostProfile.Default;

        var steps = new List<MoveStep>(path.Count + 1) { new(0, start, facing) };
        var tick = 0;

        foreach (var link in path)
        {
            tick += pricing.Move(link.ApCost);

            // Steps within one hex — vaulting a barricade from one half to the other — move you
            // without turning you, so the heading carries over.
            facing = link.From.Hex.DirectionTo(link.To.Hex) ?? facing;
            steps.Add(new MoveStep(tick, link.To, facing));
        }

        _steps = [.. steps];
        Duration = tick;
    }

    /// <summary>How the mover is carrying itself throughout. Constant, by construction.</summary>
    public Stance Stance { get; }

    /// <summary>Total action points the move costs, and therefore how long the window is.</summary>
    public int Duration { get; }

    /// <summary>Every place the mover passes through, and the tick it arrives at each.</summary>
    public IReadOnlyList<MoveStep> Steps => _steps;

    public NodeId Start => _steps[0].Node;

    public NodeId Destination => _steps[^1].Node;

    /// <summary>
    /// The mover as it will be at <paramref name="tick"/>. Ticks before the start and after the
    /// end clamp, so a slow action that lands after the move is over finds the mover standing
    /// at its destination — which is exactly the penalty for taking too long over the shot.
    /// </summary>
    public MoveStep StepAt(int tick)
    {
        if (tick <= 0) return _steps[0];
        if (tick >= Duration) return _steps[^1];

        // The mover occupies a step from its arrival tick until the next one, so the answer is
        // the last step booked at or before the tick asked about.
        var found = _steps[0];
        foreach (var step in _steps)
        {
            if (step.Tick > tick) break;
            found = step;
        }
        return found;
    }

    public NodeId PositionAt(int tick) => StepAt(tick).Node;

    public HexDirection FacingAt(int tick) => StepAt(tick).Facing;

    /// <summary>Everything a shot needs to know about the mover at one instant.</summary>
    public UnitPose PoseAt(int tick)
    {
        var step = StepAt(tick);
        return new UnitPose(step.Node, Stance, step.Facing);
    }

    /// <summary>
    /// The ticks at which the mover is somewhere new. A reactor only ever needs to consider
    /// these: between two of them nothing about the target changes, so there is no point
    /// offering the player a choice that resolves to the same shot.
    /// </summary>
    public IEnumerable<int> ArrivalTicks
    {
        get
        {
            foreach (var step in _steps) yield return step.Tick;
        }
    }

    public override string ToString() => $"{Start} to {Destination} in {Duration} ticks";
}
