namespace Hexcom.Rules;

/// <summary>
/// The price list for moving: what a stride costs on each surface, and what a slope adds.
/// </summary>
/// <remarks>
/// <para>
/// Every number here was set by reasoning, none by measurement. They live in one record so
/// that changing one is a decision made in one place and never a constant found in a search.
/// </para>
/// <para>
/// A stride is five on open ground, so ten of them are a turn. A paved road is four: twelve
/// strides a turn instead of ten, enough to make a road worth walking, which later makes it
/// worth watching. A dirt track is no faster than the field beside it; it is firm, but it is
/// not a road, and pricing it the same keeps the choice between a track and the field about
/// slope and cover rather than about the track.
/// </para>
/// <para>
/// Slope is priced by grade, rise over run between the two hex centres. Climbing adds ten
/// points per unit of grade: one in four, about fourteen degrees, adds half a stride, and one
/// in two, about twenty-seven degrees, adds a whole one. Descending adds three per unit of
/// grade, slower than the flat but well short of the climb. Past a grade of seven in ten, some
/// thirty-five degrees, a bank is taken with the hands, not walked, and until climbing is a
/// thing a soldier can do the step is refused.
/// </para>
/// </remarks>
public sealed record MovementCosts
{
    public static readonly MovementCosts Default = new();

    /// <summary>A stride across a field.</summary>
    public int Open { get; init; } = 5;

    /// <summary>A stride along a dirt track.</summary>
    public int Track { get; init; } = 5;

    /// <summary>A stride along a paved road.</summary>
    public int Paved { get; init; } = 4;

    /// <summary>Points added per unit of uphill grade.</summary>
    public double ClimbPerGrade { get; init; } = 10;

    /// <summary>Points added per unit of downhill grade.</summary>
    public double DescentPerGrade { get; init; } = 3;

    /// <summary>The steepest grade, up or down, a step will be taken on at all.</summary>
    public double MaxGrade { get; init; } = 0.7;

    /// <summary>The stride price for a surface.</summary>
    public int Stride(Surface surface) => surface switch
    {
        Surface.Paved => Paved,
        Surface.Track => Track,
        _ => Open,
    };
}
