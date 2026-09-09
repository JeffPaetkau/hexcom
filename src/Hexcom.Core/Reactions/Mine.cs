using Hexcom.Core.Combat;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;

namespace Hexcom.Core.Reactions;

/// <summary>
/// A charge left on a tile with a trigger on it.
/// </summary>
/// <remarks>
/// A mine is an overwatch that nobody is standing behind. That is not a metaphor, it is the
/// implementation: it goes off inside the same <see cref="ReactionWindow"/> an overwatch fires
/// in, at the tick the mover arrives on its tile, on the same clock and in the same resolution
/// order. What it needed was not a mechanism but an owner — everything else in a window is
/// offered to a unit out of that unit reserve, and a mine belongs to the ground.
/// <para>
/// It is what lets a squad shape an approach it is not watching, which is the one thing every
/// other way of acting out of turn cannot do: an overwatch expires when its owner turn comes
/// round and an ambush is spent the moment it springs, so both of them cost somebody standing
/// there. A mine costs a turn once and then holds the ground for the rest of the fight.
/// </para>
/// <para>
/// <b>It does not go off under the side that laid it.</b> They know where they put it. That is
/// a simplification rather than a rule of physics — a minefield you laid and then had to retreat
/// through is a good situation and this one throws it away — and it is here because the
/// alternative is a squad walking into its own charges with no way to be told about them, which
/// is worse. Spotting a mine wants the awareness ladder, and nothing has taught it to yet.
/// </para>
/// </remarks>
public sealed class Mine(NodeId node, Side laidBy, ThrownProfile charge, UnitId? layer = null)
{
    /// <summary>The tile it is under.</summary>
    public NodeId Node { get; } = node;

    /// <summary>Whose it is. Anybody else who stands on it sets it off.</summary>
    public Side LaidBy { get; } = laidBy;

    public ThrownProfile Charge { get; } = charge;

    /// <summary>
    /// Who laid it, while they last.
    /// </summary>
    /// <remarks>
    /// Carried so that the bang can be attributed to somebody, because the detection model holds
    /// contacts per pair and a noise has to be about a person. A mine laid by somebody who has
    /// since gone down is therefore heard by nobody — a real hole, and the sort that wants a
    /// noise channel with no subject rather than a patch here.
    /// </remarks>
    public UnitId? Layer { get; } = layer;

    /// <summary>False until it goes off. A mine works once.</summary>
    public bool Spent { get; internal set; }

    public override string ToString() => $"{Charge.Name} at {Node} ({LaidBy}){(Spent ? " spent" : "")}";
}

/// <summary>A mine on the route, and the tick the mover steps on it.</summary>
public sealed record MineTrigger(Mine Mine, int At)
{
    public override string ToString() => $"{Mine.Charge.Name} under {Mine.Node} at t{At}";
}

/// <summary>What a mine did, and where the mover had got to when it did it.</summary>
public sealed record BlastResolution(Mine Mine, int At, NodeId Caught, BlastOutcome Outcome);
