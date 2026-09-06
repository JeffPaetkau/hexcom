using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Units;

/// <summary>Identity of a unit within one battle. Stable across the whole fight.</summary>
public readonly record struct UnitId(int Value)
{
    public override string ToString() => $"U{Value}";
}

/// <summary>Who a unit fights for.</summary>
public enum Side
{
    Player,
    Hostile,
    Neutral,
}

/// <summary>
/// What a soldier brings to the fight, before gear and situation.
/// </summary>
/// <param name="ActionPoints">Points received at the start of each turn.</param>
/// <param name="Initiative">
/// Base rating for how early in the round this unit acts. A ten-sided roll is added to it, so
/// a two point difference in rating is real but far from decisive.
/// </param>
/// <param name="Perception">How readily this unit notices things. Used by the detection model.</param>
/// <param name="Encumbrance">
/// Weight of armour and kit, subtracted from initiative. The cost of being well protected is
/// going later.
/// </param>
/// <param name="Radio">
/// Whether this unit can call a contact in to its whole side. Without one, word only travels
/// as far as a shout or a line of sight, which is what makes the radio operator the first
/// thing worth killing quietly.
/// </param>
public sealed record UnitStats(
    int ActionPoints = 10,
    int Initiative = 10,
    int Perception = 10,
    int Encumbrance = 0,
    bool Radio = false)
{
    public static readonly UnitStats Default = new();

    /// <summary>Light kit, quick off the mark, sharp eyes.</summary>
    public static readonly UnitStats Scout = new(ActionPoints: 11, Initiative: 14, Perception: 13);

    /// <summary>Heavy armour, slow to react.</summary>
    public static readonly UnitStats Trooper = new(ActionPoints: 9, Initiative: 8, Perception: 9, Encumbrance: 3);

    /// <summary>Carries the net. Kill this one first, and the rest have to shout.</summary>
    public static readonly UnitStats Signaller = new(Perception: 12, Encumbrance: 1, Radio: true);
}

/// <summary>
/// One soldier on the field.
/// </summary>
/// <remarks>
/// Mutable, and owned by its <c>Battle</c>. Everything that changes here changes through a
/// battle method, so the whole of a fight can be replayed from a seed and a list of commands.
/// </remarks>
public sealed class Unit
{
    public Unit(
        UnitId id,
        string name,
        Side side,
        NodeId position,
        UnitStats? stats = null,
        HexDirection facing = HexDirection.NorthEast)
    {
        Id = id;
        Name = name;
        Side = side;
        Position = position;
        Facing = facing;
        Stats = stats ?? UnitStats.Default;
        ActionPoints = Stats.ActionPoints;
    }

    public UnitId Id { get; }
    public string Name { get; }
    public Side Side { get; }
    public UnitStats Stats { get; }

    public NodeId Position { get; internal set; }

    /// <summary>
    /// Which way the unit is looking. Set for free by moving, and at a cost by turning on the
    /// spot. Facing does not decide what can be seen — that stays pure geometry — but it decides
    /// how readily anything is noticed, which is what makes a position flankable.
    /// </summary>
    public HexDirection Facing { get; internal set; }
    public Stance Stance { get; internal set; } = Stance.Standing;

    /// <summary>Points left this turn.</summary>
    public int ActionPoints { get; internal set; }

    /// <summary>False once a unit has left the fight. Stale turn queue entries are skipped.</summary>
    public bool InPlay { get; internal set; } = true;

    /// <summary>Where this unit is and how it is carrying itself, for the sight solver.</summary>
    public Vantage Vantage => new(Position, Stance);

    /// <summary>Whether these two would shoot at each other.</summary>
    public bool IsHostileTo(Unit other)
        => Side != Side.Neutral && other.Side != Side.Neutral && Side != other.Side;

    public override string ToString() => $"{Name} [{Id} {Side}] at {Position}";
}
