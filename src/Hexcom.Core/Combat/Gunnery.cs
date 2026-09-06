using System.Collections.Generic;
using Hexcom.Core.Hexes;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Combat;

/// <summary>The dials on shooting. All balance, no structure.</summary>
public sealed record GunneryModel
{
    public static readonly GunneryModel Default = new();

    /// <summary>Share of a weapon's accuracy that survives at its maximum range.</summary>
    public double LongRangeFloor { get; init; } = 0.40;

    /// <summary>Nothing is ever certain, however easy it looks.</summary>
    public double MaximumHitChance { get; init; } = 0.95;

    /// <summary>And nothing you can see at all is completely impossible.</summary>
    public double MinimumHitChance { get; init; } = 0.03;

    /// <summary>
    /// Penalty for a target that has cover, on top of the exposure the geometry already gives.
    /// </summary>
    /// <remarks>
    /// These are not double counting. Exposure says how much of the silhouette is physically
    /// visible; this says that a soldier who has something to hide behind is using it — moving
    /// with it, staying low, breaking up the shot. One is geometry, the other is behaviour.
    /// </remarks>
    public double LightCoverPenalty { get; init; } = 0.94;

    public double HalfCoverPenalty { get; init; } = 0.85;

    public double FullCoverPenalty { get; init; } = 0.72;

    /// <summary>Being low is steadier. Prone is slow and quiet and shoots well.</summary>
    public double CrouchingSteadiness { get; init; } = 1.08;

    public double ProneSteadiness { get; init; } = 1.15;
}

/// <summary>What a shot would look like, worked out before anyone commits to it.</summary>
/// <param name="FaceHit">Which of the target's faces the round would arrive at.</param>
/// <param name="Refusal">Why the shot cannot be taken, in words fit to show a player.</param>
public sealed record ShotPlan(
    Unit Shooter,
    Unit Target,
    WeaponProfile Weapon,
    FireMode Mode,
    SightResult Sight,
    double HitChance,
    int ApCost,
    HexDirection FaceHit,
    string? Refusal)
{
    public bool CanFire => Refusal is null;

    /// <summary>Expected damage through to the soldier, for an AI weighing options.</summary>
    public double ExpectedDamage => HitChance * Mode.Shots * Weapon.Damage;
}

/// <summary>One round, and what it did.</summary>
public sealed record ShotHit(bool Hit, double Roll, DamageTaken? Damage);

/// <summary>What happened when the trigger was pulled.</summary>
public sealed record ShotOutcome(
    bool Fired,
    IReadOnlyList<ShotHit> Shots,
    int ApSpent,
    double HitChance,
    bool TargetDown,
    string? Refusal)
{
    internal static ShotOutcome Refused(string why) => new(false, [], 0, 0, false, why);

    public int TotalDamage
    {
        get
        {
            var sum = 0;
            foreach (var shot in Shots) sum += shot.Damage?.ToVitality ?? 0;
            return sum;
        }
    }

    public bool AnyHit
    {
        get
        {
            foreach (var shot in Shots) if (shot.Hit) return true;
            return false;
        }
    }
}

/// <summary>
/// Works out whether a shot connects. Pure arithmetic over a sight trace, so it can be tested
/// and tuned without a battle around it.
/// </summary>
public sealed class Gunnery(GunneryModel? model = null)
{
    public GunneryModel Model { get; } = model ?? GunneryModel.Default;

    /// <summary>
    /// Chance a single round finds its target, from zero to one.
    /// </summary>
    /// <remarks>
    /// Elevation deliberately gets no bonus of its own. Shooting down already helps, because the
    /// sight trace reports more of the target exposed when a low wall stops protecting it, and
    /// paying twice for the same advantage would make high ground the only thing worth having.
    /// </remarks>
    public double HitChance(WeaponProfile weapon, FireMode mode, SightResult sight, Stance shooterStance)
    {
        if (!sight.CanSee) return 0;
        if (sight.Distance > weapon.MaxRange) return 0;
        if (sight.Exposure <= 0) return 0;

        var chance = weapon.Accuracy
                     * mode.Accuracy
                     * RangeFactor(weapon, sight.Distance)
                     * sight.Exposure
                     * CoverPenalty(sight.Cover)
                     * Steadiness(shooterStance);

        return Math.Clamp(chance, Model.MinimumHitChance, Model.MaximumHitChance);
    }

    /// <summary>Full accuracy out to the optimal range, then falling away to a floor at maximum.</summary>
    public double RangeFactor(WeaponProfile weapon, double distance)
    {
        if (distance <= weapon.OptimalRange) return 1.0;
        if (distance >= weapon.MaxRange) return Model.LongRangeFloor;

        var past = (distance - weapon.OptimalRange) / (weapon.MaxRange - weapon.OptimalRange);
        return 1.0 - (1.0 - Model.LongRangeFloor) * past;
    }

    public double CoverPenalty(Maps.CoverGrade cover) => cover switch
    {
        Maps.CoverGrade.Full => Model.FullCoverPenalty,
        Maps.CoverGrade.Half => Model.HalfCoverPenalty,
        Maps.CoverGrade.Light => Model.LightCoverPenalty,
        _ => 1.0,
    };

    public double Steadiness(Stance stance) => stance switch
    {
        Stance.Prone => Model.ProneSteadiness,
        Stance.Crouching => Model.CrouchingSteadiness,
        _ => 1.0,
    };
}
