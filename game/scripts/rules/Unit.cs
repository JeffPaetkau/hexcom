namespace Hexcom.Game.Rules;

/// <summary>A soldier on the board: where they stand and what they have left to spend this turn.</summary>
public sealed class Unit
{
    /// <summary>
    /// Fifty rather than ten, as v1 settled: the cheapest action sets the resolution of every
    /// price. At a stride of five, turning on the spot can cost two and a per-soldier movement
    /// multiplier anywhere from three fifths to double lands on a distinct number; at a stride
    /// of one none of that can be expressed.
    /// </summary>
    public const int MaxAp = 50;

    public Unit(Hex position)
    {
        Position = position;
        Ap = MaxAp;
    }

    public Hex Position { get; set; }

    public int Ap { get; private set; }

    public bool CanAfford(int cost) => cost <= Ap;

    public void Spend(int cost) => Ap -= cost;

    /// <summary>A new turn: everything back.</summary>
    public void Refresh() => Ap = MaxAp;
}
