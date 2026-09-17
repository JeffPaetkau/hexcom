namespace Hexcom.Rules;

/// <summary>A soldier on the board: where they stand, what they pay, and what they have left to spend this turn.</summary>
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

    public Unit(Hex position, CostProfile? profile = null)
    {
        Position = position;
        Profile = profile ?? CostProfile.Default;
        Ap = MaxAp;
    }

    public Hex Position { get; set; }

    /// <summary>What this soldier pays, against the shared price list.</summary>
    public CostProfile Profile { get; }

    public int Ap { get; private set; }

    public bool CanAfford(int cost) => cost <= Ap;

    public void Spend(int cost) => Ap -= cost;

    /// <summary>A new turn: everything back.</summary>
    public void Refresh() => Ap = MaxAp;
}
