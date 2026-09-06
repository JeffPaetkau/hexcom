namespace Hexcom.Core.Vision;

/// <summary>How a unit is carrying itself, which decides how much of it is exposed.</summary>
public enum Stance
{
    Standing,
    Crouching,
    Prone,
}

/// <summary>
/// The measurements a stance contributes to sight and cover, in metres above the floor.
/// </summary>
/// <param name="EyeHeight">Where the unit looks from.</param>
/// <param name="BodyHeight">Top of the silhouette — the last part of a unit to disappear behind cover.</param>
/// <param name="ConcealmentBonus">
/// Divisor on how readily the unit is noticed, for the detection model. Not used by the sight
/// trace itself, which is pure geometry.
/// </param>
/// <param name="NoiseFactor">Multiplier on the racket the unit makes moving about.</param>
public sealed record StanceProfile(
    Stance Stance,
    double EyeHeight,
    double BodyHeight,
    double ConcealmentBonus,
    double NoiseFactor)
{
    /// <summary>Upright. Fast, loud, and visible from a long way off.</summary>
    public static readonly StanceProfile Standing = new(Stance.Standing, 1.65, 1.80, 1.0, 1.0);

    /// <summary>Crouched behind something. Still visible over waist-high cover, but only just.</summary>
    public static readonly StanceProfile Crouching = new(Stance.Crouching, 1.10, 1.25, 1.4, 0.55);

    /// <summary>Flat. Nearly anything hides you, you make almost no noise, and you see little.</summary>
    public static readonly StanceProfile Prone = new(Stance.Prone, 0.35, 0.45, 2.2, 0.3);

    /// <summary>The midpoint of the silhouette — what a shot is aimed at.</summary>
    public double CentreHeight => BodyHeight * 0.5;

    public static StanceProfile For(Stance stance) => stance switch
    {
        Stance.Crouching => Crouching,
        Stance.Prone => Prone,
        _ => Standing,
    };
}
