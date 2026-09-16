namespace Hexcom.Rules;

/// <summary>
/// Units, and the one piece of hex geometry the interface already has to agree with.
/// </summary>
/// <remarks>
/// One world unit is one metre. The ground is the XZ plane and up is +Y; north is -Z. Nothing
/// draws a hex yet, but the grid that will arrive is flat-topped with a one-metre centre-to-corner
/// size, which puts its six neighbour directions 60 degrees apart with one of them pointing
/// north. The camera turns freely rather than resting on those bearings, so whatever draws the
/// grid must read from any angle. Rendering scale is never folded into these numbers: a change
/// here silently changes every distance the rules will one day measure.
/// </remarks>
public static class Units
{
    /// <summary>Centre to corner, metres. Two metres corner to corner, 1.73 between neighbouring centres.</summary>
    public const float HexSize = 1.0f;

    /// <summary>The angle between neighbouring hex directions, degrees.</summary>
    public const float BearingStepDegrees = 60f;
}
