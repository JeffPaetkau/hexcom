namespace Hexcom.Core.Awareness;

/// <summary>
/// The dials on the detection model. All of it is balance, none of it is structure.
/// </summary>
/// <remarks>
/// Certainty runs on a nominal hundred point scale. An average soldier standing in the open at
/// close range is worth roughly half of it per look, so being careless gets you found in about
/// two of the enemy's turns. Prone behind cover at distance is worth a couple of points, which
/// is the difference the whole approach phase is played over.
/// </remarks>
public sealed record AwarenessModel
{
    public static readonly AwarenessModel Default = new();

    // ---- the ladder ------------------------------------------------------------

    public double SuspiciousAt { get; init; } = 25;
    public double SearchingAt { get; init; } = 50;
    public double AlertedAt { get; init; } = 75;
    public double EngagedAt { get; init; } = 100;

    /// <summary>Certainty stops climbing here, so a long look does not bank infinite margin.</summary>
    public double Ceiling { get; init; } = 130;

    // ---- looking ---------------------------------------------------------------

    /// <summary>Certainty a perfect look is worth: close, unobstructed, against someone upright.</summary>
    public double LookGain { get; init; } = 55;

    /// <summary>How far a unit can make anything out at all, in metres.</summary>
    public double SightRangeMetres { get; init; } = 45;

    /// <summary>Certainty shed each turn a unit fails to find what it is looking for.</summary>
    public double DecayPerTurn { get; init; } = 15;

    // ---- listening -------------------------------------------------------------

    /// <summary>Metres a sound carries per point of loudness.</summary>
    public double NoiseMetresPerPoint { get; init; } = 2.0;

    /// <summary>Certainty a sound is worth at its source.</summary>
    public double NoiseGain { get; init; } = 30;

    // ---- passing it on ---------------------------------------------------------

    /// <summary>How far a shout carries, in metres.</summary>
    public double VoiceRangeMetres { get; init; } = 15;

    /// <summary>
    /// Share of the caller's certainty that survives being passed on. Second-hand information
    /// is worth less than seeing it yourself, so a relayed contact leaves the receiver hunting
    /// rather than immediately engaged.
    /// </summary>
    public double RelayFraction { get; init; } = 0.6;
}
