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
/// Multiplier on how hard the unit is to notice, for the detection model. Not used by the
/// sight trace itself, which is pure geometry.
/// </param>
public sealed record StanceProfile(Stance Stance, double EyeHeight, double BodyHeight, double ConcealmentBonus)
{
    /// <summary>Upright. Fast, and visible from a long way off.</summary>
    public static readonly StanceProfile Standing = new(Stance.Standing, 1.65, 1.80, 1.0);

    /// <summary>Crouched behind something. Still visible over waist-high cover, but only just.</summary>
    public static readonly StanceProfile Crouching = new(Stance.Crouching, 1.10, 1.25, 1.4);

    /// <summary>Flat. Nearly anything hides you, and you cannot see much either.</summary>
    public static readonly StanceProfile Prone = new(Stance.Prone, 0.35, 0.45, 2.2);

    /// <summary>The midpoint of the silhouette — what a shot is aimed at.</summary>
    public double CentreHeight => BodyHeight * 0.5;

    public static StanceProfile For(Stance stance) => stance switch
    {
        Stance.Crouching => Crouching,
        Stance.Prone => Prone,
        _ => Standing,
    };
}
