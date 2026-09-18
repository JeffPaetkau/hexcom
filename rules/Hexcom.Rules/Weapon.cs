namespace Hexcom.Rules;

/// <summary>A gun, as data: what a hit does, how many rounds it carries, how far it reaches and what a shot costs.</summary>
/// <remarks>
/// <para>
/// One weapon and one way of firing it, because the interface for shooting is being built
/// before the choices that will hang off it. Fire modes, reloading, armour and reactions are
/// all later; nothing here should be read as a decision against them.
/// </para>
/// <para>
/// Range is in metres between hex centres, the same metre the stride is. A shot at the next
/// hex, a stride away and the closest a target can be with one soldier to a hex, is certain:
/// nothing is in the way yet, and a player who watched that miss would be right to be upset.
/// From there the chance falls in a straight line to the accuracy at the optimal range, then
/// to <see cref="LongRangeFloor"/> of the accuracy at the maximum, past which the shot is
/// refused rather than merely unlikely, so a player is told the gun cannot reach rather than
/// shown a three per cent chance. Both were the user's calls on 2026-09-17, against a flat
/// eighty per cent at arm's length and then against a ninety-five per cent ceiling.
/// </para>
/// </remarks>
/// <param name="Damage">Hit points a hit takes off.</param>
/// <param name="Rounds">Rounds carried at the start. There is no reloading yet, so this is the whole supply.</param>
/// <param name="OptimalRange">Metres out to which the weapon is at its best.</param>
/// <param name="MaxRange">Metres beyond which it cannot be fired at all.</param>
/// <param name="Accuracy">Chance to hit at the optimal range, from zero to one.</param>
/// <param name="ShotCost">Action points a shot costs: the share of the ten-second turn spent shouldering, aiming and firing.</param>
public sealed record Weapon(
    string Name,
    int Damage,
    int Rounds,
    double OptimalRange,
    double MaxRange,
    double Accuracy,
    int ShotCost)
{
    /// <summary>The share of the accuracy left at maximum range.</summary>
    public const double LongRangeFloor = 0.4;

    /// <summary>Metres at and under which a shot cannot miss: the next hex, the closest a target can stand.</summary>
    public const double PointBlank = Units.Stride;

    /// <summary>
    /// The basic rifle. Three hits put down a soldier of <see cref="Unit.MaxHitPoints"/>; a shot
    /// is three and a half seconds of the turn, so a soldier can fire twice and still take a few
    /// strides, or fire once and walk thirteen metres. The ranges are v1's slug rifle.
    /// </summary>
    public static readonly Weapon Rifle = new(
        "Rifle", Damage: 10, Rounds: 12, OptimalRange: 20, MaxRange: 55, Accuracy: 0.80, ShotCost: 35);

    public bool Reaches(double metres) => metres <= MaxRange;

    /// <summary>The chance a round hits a target that many metres away, from zero to one.</summary>
    public double HitChance(double metres)
    {
        if (!Reaches(metres)) return 0;

        if (metres <= PointBlank) return 1;

        if (metres <= OptimalRange)
        {
            var closeness = (OptimalRange - metres) / (OptimalRange - PointBlank);
            return Accuracy + (1 - Accuracy) * closeness;
        }

        var beyond = (metres - OptimalRange) / (MaxRange - OptimalRange);
        return Accuracy * (1 - beyond * (1 - LongRangeFloor));
    }
}
