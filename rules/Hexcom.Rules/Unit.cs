using System;

namespace Hexcom.Rules;

/// <summary>Who a soldier fights for.</summary>
public enum Side
{
    Player,
    Hostile,
}

/// <summary>
/// A soldier on the board: which side, where they stand, what they pay, what they carry, what
/// they have left to spend this turn, and how much more they can take.
/// </summary>
public sealed class Unit
{
    /// <summary>
    /// A hundred, because the cheapest action sets the resolution of every price. With a metre
    /// stride costing five, a paved road at four is a real saving, a scout at four fifths and a
    /// gunner at half again land on distinct numbers, and turning on the spot or changing stance
    /// can cost a few points and still be cheaper than a step. The turn was fifty when the hex
    /// was 1.73 across; halving the stride at fifty would have priced it at three, where a road
    /// rounds to either nothing or too much and the soldiers blur together. A hundred also
    /// reads as a percentage of the ten seconds a turn stands for.
    /// </summary>
    public const int MaxAp = 100;

    /// <summary>
    /// Thirty: three rifle hits, so a firefight is a few exchanges rather than one, and a
    /// soldier who has taken a hit is worth pulling back rather than already lost. There is no
    /// armour and no recovery, so this is the whole of what stands between a soldier and the
    /// ground.
    /// </summary>
    public const int MaxHitPoints = 30;

    public Unit(Hex position, Side side = Side.Player, string name = "UNIT", Weapon? weapon = null, CostProfile? profile = null)
    {
        Position = position;
        Side = side;
        Name = name;
        Weapon = weapon ?? Weapon.Rifle;
        Profile = profile ?? CostProfile.Default;
        Ap = MaxAp;
        HitPoints = MaxHitPoints;
        Rounds = Weapon.Rounds;
    }

    public Hex Position { get; set; }

    public Side Side { get; }

    public string Name { get; }

    public Weapon Weapon { get; }

    /// <summary>What this soldier pays, against the shared price list.</summary>
    public CostProfile Profile { get; }

    public int Ap { get; private set; }

    public int HitPoints { get; private set; }

    /// <summary>Rounds left in the weapon. Nothing puts them back yet.</summary>
    public int Rounds { get; private set; }

    /// <summary>Out of the fight: no hit points left. A soldier down neither acts nor is shot at.</summary>
    public bool IsDown => HitPoints <= 0;

    public bool CanAfford(int cost) => cost <= Ap;

    public void Spend(int cost) => Ap -= cost;

    public void SpendRound() => Rounds = Math.Max(0, Rounds - 1);

    /// <summary>Take a hit. Hit points never go below nothing.</summary>
    public void Hurt(int damage) => HitPoints = Math.Max(0, HitPoints - damage);

    /// <summary>A new turn: the points come back. Hit points and rounds do not.</summary>
    public void Refresh() => Ap = MaxAp;
}
