using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Units;

/// <summary>
/// Where a unit is, how it is carrying itself, and which way it is looking, at one instant.
/// </summary>
/// <remarks>
/// Exists so a shot can be worked out against a unit that is not there yet. Inside a reaction
/// window the interesting question is what a shot would do to the mover three ticks from now,
/// and answering it by shuffling the real unit around and putting it back would be a fine way
/// to leave the battle in a state nobody asked for.
/// </remarks>
public readonly record struct UnitPose(NodeId Position, Stance Stance, HexDirection Facing)
{
    public Vantage Vantage => new(Position, Stance);

    /// <summary>The unit as it actually is.</summary>
    public static UnitPose Of(Unit unit) => new(unit.Position, unit.Stance, unit.Facing);

    public override string ToString() => $"{Position} ({Stance}, facing {Facing})";
}

/// <summary>Which pocket an action is paid out of.</summary>
/// <remarks>
/// A unit has two, and they never mix. The turn allowance is spent on its own turn and refills
/// when that turn comes round again; the reserve is what was left over, and is spent reacting
/// to other people. Reacting does not refresh it, so a unit answers about one move a round
/// however many chances it is given.
/// </remarks>
public enum ApSource
{
    /// <summary>The unit's allowance for its own turn.</summary>
    Turn,

    /// <summary>Points banked at the end of the last turn, for acting out of turn.</summary>
    Reserve,
}
