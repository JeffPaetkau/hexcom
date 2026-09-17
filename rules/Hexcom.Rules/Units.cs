namespace Hexcom.Rules;

/// <summary>
/// Units, and the one piece of hex geometry the interface already has to agree with.
/// </summary>
/// <remarks>
/// One world unit is one metre. The ground is the XZ plane and up is +Y; north is -Z. The grid
/// is flat-topped, which puts its six neighbour directions 60 degrees apart with one of them
/// pointing north. The camera turns freely rather than resting on those bearings, so whatever
/// draws the grid must read from any angle. Rendering scale is never folded into these numbers:
/// a change here silently changes every distance the rules measure.
/// </remarks>
public static class Units
{
    /// <summary>
    /// Centre to neighbouring centre, metres: the run of every step, and the base the hex is
    /// sized from. One metre because that is the room a standing or crouching soldier takes,
    /// and neighbours a metre apart read as shoulder to shoulder. Centre to centre rather than
    /// centre to corner because it is the distance the rules measure with; the corner distance
    /// is only geometry, so it is derived.
    /// </summary>
    public const double Stride = 1.0;

    /// <summary>
    /// Centre to corner, metres, following from <see cref="Stride"/>: one over root three, 0.577,
    /// or 1.15 corner to corner. A double, and written out, so that a stride between two centres
    /// comes to exactly one metre rather than a float away from it, which a price on a rounding
    /// midpoint would notice.
    /// </summary>
    public const double HexSize = Stride * 0.57735026918962576;

    /// <summary>
    /// How long a turn stands for, seconds. Every price is a share of this, so it is the test
    /// a price is argued against: a stride at five points is half a second, two metres a
    /// second, a fast walk with the weapon up; turning on the spot at a few points is a few
    /// tenths. It is also the target the animations are timed to, so what the player watches
    /// takes as long as it is supposed to. Ten rather than six because the default move is a
    /// walk, not a run: running will be a choice that buys distance with noise.
    /// </summary>
    public const float TurnSeconds = 10f;

    /// <summary>The angle between neighbouring hex directions, degrees.</summary>
    public const float BearingStepDegrees = 60f;
}
