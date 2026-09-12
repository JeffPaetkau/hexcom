using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
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
    int ActionPoints = 50,
    int Initiative = 10,
    int Perception = 10,
    int Encumbrance = 0,
    bool Radio = false,
    int Vitality = 20)
{
    /// <summary>What this soldier pays for moving and shooting, against the shared price list.</summary>
    public CostProfile Costs { get; init; } = CostProfile.Default;

    /// <summary>
    /// Whether this soldier can pick which side of a target to shoot at rather than taking
    /// whichever the geometry hands them.
    /// </summary>
    /// <remarks>
    /// Off by default, and meant to stay a thing that is earned. An ordinary rifleman shoots at
    /// a soldier and the hexagon decides where it lands; somebody who has learned to place a
    /// round can name the plate, at a cost in accuracy for taking the time to pick it.
    /// </remarks>
    public bool CanCallShots { get; init; }

    public static readonly UnitStats Default = new();

    /// <summary>Light kit, quick off the mark, sharp eyes — and slow to bring a weapon to bear.</summary>
    /// <remarks>
    /// The cost profile is what makes the post mean anything. Both profiles were written to
    /// describe exactly these two archetypes and until now no soldier the game had ever deployed
    /// carried one, so every unit in every match paid list price and <c>CostProfile</c> was a
    /// record the design doc described as load-bearing and nothing loaded. See
    /// <c>docs/decisions.md</c> entry 046.
    /// <para>
    /// Turning them on changed nothing any test could see and a great deal a batch could: on the
    /// waystation the squad with its archetypes kills about half what the same squad kills at list
    /// price, and takes its look from further out a round sooner. Kept, measured. Entry 083.
    /// </para>
    /// </remarks>
    public static readonly UnitStats Scout = new(ActionPoints: 55, Initiative: 14, Perception: 13)
    {
        Costs = CostProfile.Scout,
    };

    /// <summary>Heavy armour, slow to react, and fast on the trigger once planted.</summary>
    public static readonly UnitStats Trooper = new(ActionPoints: 45, Initiative: 8, Perception: 9, Encumbrance: 3)
    {
        Costs = CostProfile.Gunner,
    };

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
        HexDirection facing = HexDirection.NorthEast,
        Loadout? loadout = null)
    {
        Id = id;
        Name = name;
        Side = side;
        Position = position;
        Facing = facing;
        Stats = stats ?? UnitStats.Default;
        ActionPoints = Stats.ActionPoints;
        Vitality = Stats.Vitality;
        Protection = new Protection(loadout ?? Loadout.Rifleman);
        ThrownLeft = Protection.Loadout.Charges;
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

    /// <summary>
    /// Points banked at the end of the last turn, for acting out of turn.
    /// </summary>
    /// <remarks>
    /// Spent, not refreshed. Whatever goes on reacting is gone until this unit's own turn comes
    /// round again, so a soldier answers about one move a round however many chances the enemy
    /// hands it. That, and the fact that sprinting somewhere leaves nothing to bank, is most of
    /// what stops a reaction window from becoming a cascade.
    /// </remarks>
    public int Reserve { get; internal set; }

    /// <summary>
    /// The arc this unit is watching, if it declared one. Cleared when its next turn starts.
    /// </summary>
    public HeldArc? Overwatch { get; internal set; }

    /// <summary>
    /// The arc this unit armed against, if it is part of an ambush.
    /// </summary>
    /// <remarks>
    /// Unlike an overwatch, this <b>survives</b> the unit's own turn coming round. An overwatch is
    /// a posture you hold for a round; an ambush is a plan the squad committed to, and it stands
    /// until somebody springs it or stands it down. That is also what lets the member who chooses
    /// the moment still be armed when their turn arrives.
    /// <para>
    /// Standing armed is nearly worthless on its own, though, because everybody except the one
    /// who springs it pays out of a reserve that expires every turn. The trap is only fully
    /// loaded while the whole squad still has points banked — which is a handful of turns at
    /// most, and the reason waiting too long costs you the coordination.
    /// </para>
    /// </remarks>
    public HeldArc? Ambush { get; internal set; }

    /// <summary>The arc this unit is holding a shot down, whichever way it came about.</summary>
    public HeldArc? Held => Overwatch ?? Ambush;

    /// <summary>Whether there is anything left to react with.</summary>
    public bool CanReact => InPlay && Reserve > 0;

    /// <summary>What the unit carries, and what is left of it face by face.</summary>
    public Protection Protection { get; }

    public WeaponProfile Weapon => Protection.Loadout.Weapon;

    /// <summary>The charge this soldier carries, if any.</summary>
    public ThrownProfile? Thrown => Protection.Loadout.Thrown;

    /// <summary>
    /// How many are left.
    /// </summary>
    /// <remarks>
    /// The only thing in the game that runs out. Points come back every turn and shields recharge;
    /// a grenade thrown is gone, which is what makes deciding to throw one different in kind from
    /// deciding to shoot. It is also the whole of what stops the scorer leading with grenades.
    /// </remarks>
    public int ThrownLeft { get; internal set; }

    /// <summary>What is left of the soldier. Nothing stops damage once it is through.</summary>
    public int Vitality { get; internal set; }

    public bool IsDown => Vitality <= 0;

    /// <summary>
    /// How this soldier left the field, or null while it is still on it.
    /// </summary>
    /// <remarks>
    /// Carries the reading the other side held at the moment of departure, because by the time
    /// anybody could ask, the tracker has forgotten. See <see cref="Battles.Departure"/>, which
    /// is where the argument for sampling rather than polling is written down.
    /// </remarks>
    public Departure? Left { get; internal set; }

    /// <summary>False once a unit has left the fight. Stale turn queue entries are skipped.</summary>
    public bool InPlay => Left is null;

    /// <summary>Whether this soldier walked off the field rather than being carried off it.</summary>
    public bool GotOut => Left?.Kind == DepartureKind.Extracted;

    /// <summary>Where this unit is and how it is carrying itself, for the sight solver.</summary>
    public Vantage Vantage => new(Position, Stance);

    /// <summary>Whether these two would shoot at each other.</summary>
    public bool IsHostileTo(Unit other)
        => Side != Side.Neutral && other.Side != Side.Neutral && Side != other.Side;

    public override string ToString() => $"{Name} [{Id} {Side}] at {Position}";
}
