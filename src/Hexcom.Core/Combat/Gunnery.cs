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

    /// <summary>
    /// How much of a kinetic round is lost skipping off a plate it met edge-on rather than
    /// square. Half at ninety degrees, and a quarter at the sixty degrees a shoulder presents.
    /// </summary>
    /// <remarks>
    /// Kinetic only, and that asymmetry is the point. A solid object arriving at an angle
    /// deflects; a beam lands wherever it lands and burns. So the geometry of an approach reads
    /// differently depending on what is being carried, which is one more reason a squad wants
    /// both families rather than settling on one.
    /// </remarks>
    public double GlancingPenalty { get; init; } = 0.5;

    /// <summary>
    /// Whether to flatten the glancing average so the bearing you approach from does not change
    /// how much damage you expect to do.
    /// </summary>
    /// <remarks>
    /// It should not. A hexagon is a bookkeeping device for which plate wears, not a claim that
    /// soldiers are hexagonal, and without this the arithmetic leaks: met square on, half the
    /// rounds find an unangled plate and half skip off a shoulder, while met on a corner every
    /// round arrives mildly angled — which averages out slightly better for the shooter. That is
    /// an artefact of the abstraction rather than anything anyone should be playing around.
    /// <para>
    /// Normalising against the head-on case keeps every individual hit honest — the plate you
    /// catch square still takes the worst of it — while making the expectation the same from
    /// every bearing. Which side gets worn still depends entirely on where you are standing,
    /// and that is the part worth having.
    /// </para>
    /// </remarks>
    public bool NormaliseGlancing { get; init; } = true;

    /// <summary>
    /// What picking your spot costs in accuracy, for the soldiers who can do it at all.
    /// </summary>
    public double CalledShotAccuracy { get; init; } = 0.80;
}

/// <summary>What a shot would look like, worked out before anyone commits to it.</summary>
/// <param name="Aspects">
/// Which of the target's own sides this shot can reach and how squarely, widest first. A body is
/// a hexagon, so there is never just one: head-on it is half the front plate and a quarter of
/// each shoulder, and which one a given round finds is rolled when it is fired.
/// </param>
/// <param name="Refusal">Why the shot cannot be taken, in words fit to show a player.</param>
/// <param name="AimBonus">
/// Multiplier from having the weapon already pointed the right way. One for an ordinary shot;
/// more for one taken off an overwatch, and sharper the narrower the arc being held.
/// </param>
/// <param name="TargetPose">
/// Where the target is being shot at, which inside a reaction window is where it <em>will</em>
/// be when the round lands rather than where it stands now.
/// </param>
public sealed record ShotPlan(
    Unit Shooter,
    Unit Target,
    WeaponProfile Weapon,
    FireMode Mode,
    SightResult Sight,
    double HitChance,
    int ApCost,
    IReadOnlyList<FacingAspect> Aspects,
    string? Refusal,
    double AimBonus = 1.0,
    UnitPose? TargetPose = null,
    ApSource Paying = ApSource.Turn,
    double GlancingFactor = 1.0,
    double GlancingScale = 1.0,
    BodyFace? CalledAt = null)
{
    public bool CanFire => Refusal is null;

    /// <summary>The side the shot is most likely to find. What an interface points at.</summary>
    public BodyFace LikeliestFace => CalledAt ?? (Aspects.Count > 0 ? Aspects[0].Face : BodyFace.Front);

    /// <summary>Whether the shooter picked the plate rather than taking what they were given.</summary>
    public bool IsCalledShot => CalledAt is not null;

    /// <summary>
    /// Expected damage arriving at the plate, for an AI weighing options.
    /// </summary>
    /// <remarks>
    /// <see cref="GlancingFactor"/> is the average share of a round that survives the angle it
    /// arrives at, weighted by how likely each face is to be the one hit — normalised, so it is
    /// the same from every bearing. Which side gets worn still depends entirely on where the
    /// shooter is standing; how much gets through does not.
    /// </remarks>
    public double ExpectedDamage => HitChance * Mode.Shots * Weapon.Damage * GlancingFactor;
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
    /// <param name="aimBonus">
    /// What having the weapon already pointed there is worth. It multiplies rather than adds,
    /// so overwatching pays best on a shot that was plausible anyway and does not turn a
    /// hopeless one into a good one.
    /// </param>
    public double HitChance(
        WeaponProfile weapon,
        FireMode mode,
        SightResult sight,
        Stance shooterStance,
        double aimBonus = 1.0)
    {
        if (!sight.CanSee) return 0;
        if (sight.Distance > weapon.MaxRange) return 0;
        if (sight.Exposure <= 0) return 0;

        var chance = weapon.Accuracy
                     * mode.Accuracy
                     * RangeFactor(weapon, sight.Distance)
                     * sight.Exposure
                     * CoverPenalty(sight.Cover)
                     * Steadiness(shooterStance)
                     * aimBonus;

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

    /// <summary>
    /// Share of a round's damage that survives arriving at <paramref name="obliquityDegrees"/>
    /// off square. One for a beam, which does not skip.
    /// </summary>
    public double GlancingFactor(DamageKind kind, double obliquityDegrees)
    {
        if (kind != DamageKind.Kinetic) return 1.0;

        var squareness = Math.Cos(obliquityDegrees * Math.PI / 180.0);
        return 1.0 - Model.GlancingPenalty * (1.0 - Math.Clamp(squareness, 0, 1));
    }

    /// <summary>
    /// What a round actually arrives with after skipping, given which face it found and the
    /// normalising scale for the bearing it came from.
    /// </summary>
    public int DamageAt(WeaponProfile weapon, double obliquityDegrees, double scale = 1.0)
        => (int)Math.Round(
            weapon.Damage * GlancingFactor(weapon.Kind, obliquityDegrees) * scale,
            MidpointRounding.AwayFromZero);

    /// <summary>
    /// The glancing average of a soldier met head-on, which every other bearing is normalised to.
    /// </summary>
    /// <remarks>
    /// Head-on is half the front plate square and a quarter of each shoulder at sixty degrees,
    /// so the reference is fixed by the shape of a hexagon rather than by the situation.
    /// </remarks>
    public double ReferenceGlancingFactor(DamageKind kind)
        => 0.5 * GlancingFactor(kind, 0)
           + 0.5 * GlancingFactor(kind, BodyFaces.DegreesPerFace);

    /// <summary>
    /// Scale that makes the expected damage from this bearing match the head-on case, so which
    /// way round a hexagonal abstraction happens to be turned costs the shooter nothing.
    /// </summary>
    public double NormalisingScale(DamageKind kind, IReadOnlyList<FacingAspect> aspects)
    {
        if (!Model.NormaliseGlancing || aspects.Count == 0) return 1.0;

        var mean = 0.0;
        foreach (var aspect in aspects)
            mean += aspect.Share * GlancingFactor(kind, aspect.ObliquityDegrees);

        return mean <= 0 ? 1.0 : ReferenceGlancingFactor(kind) / mean;
    }
}
