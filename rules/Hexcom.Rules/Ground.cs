namespace Hexcom.Rules;

/// <summary>What is underfoot at a point, as far as walking on it is concerned.</summary>
/// <remarks>
/// Three kinds because the landscape has three: fields, dirt tracks and paved roads. Rough
/// ground, rubble and scrub will be added when the ground can hold them; a price for a
/// surface that nothing produces yet would be a number nobody can check.
/// </remarks>
public enum Surface
{
    Open,
    Track,
    Paved,
}

/// <summary>
/// The ground as the rules see it: a height and a surface at every point on the plane.
/// </summary>
/// <remarks>
/// <see cref="Terrain"/> is the real one. The movement rules take the interface so a test
/// can hand them a slope or a road drawn by hand and check a price without a landscape.
/// </remarks>
public interface IGround
{
    /// <summary>The height of the ground at a point, metres.</summary>
    double Height(double x, double z);

    /// <summary>What a foot lands on at a point.</summary>
    Surface SurfaceAt(double x, double z);
}
