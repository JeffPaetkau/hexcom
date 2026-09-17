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
/// A stride is a metre and costs five on open ground, so a turn of a hundred is twenty of
/// them: two metres a second over the ten seconds a turn stands for
/// (<see cref="Units.TurnSeconds"/>), a fast walk with the weapon up, the pace a soldier
/// keeps when they are moving rather than running. A paved road is four: twenty-five strides
/// a turn instead of twenty, enough to make a road worth walking, which later makes it worth
/// watching. A dirt track is no faster than the field beside it; it is firm, but it is not a
/// road, and pricing it the same keeps the choice between a track and the field about slope and
/// cover rather than about the track.
/// </para>
/// <para>
/// Slope is priced by grade, rise over run between the two hex centres. Climbing adds ten
/// points per unit of grade: one in four, about fourteen degrees, adds half a stride, and one
/// in two, about twenty-seven degrees, adds a whole one. Descending adds three per unit of
/// grade, slower than the flat but well short of the climb. These scale with the stride, not
/// the turn: the cost of a hillside is the slope price times its height over one stride, so a
/// shorter stride with the same slope price would make every hill dearer. Past a grade of seven
/// in ten, some thirty-five degrees, a bank is taken with the hands, not walked, and until
/// climbing is a thing a soldier can do the step is refused.
/// </para>
/// <para>
/// Going downhill is two things once the ground is steep enough. The careful way is the
/// descent price above. The hurried way takes three points off per unit of grade instead of
/// adding three, so a one-in-two slope is walked down for seven and run down for four, and
/// every hurried step carries a chance of a fall of a tenth per unit of grade: one in twenty
/// on that slope, compounding along the run, so a long fast descent is a gamble and a short
/// one is not much of one. A fall costs the rest of the turn. Below a grade of one in four
/// there is no hurried way: the ground is not steep enough for running to be anything but
/// running, which is a matter of pace for later.
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

    /// <summary>
    /// The steepest grade, up or down, a step will be taken on at all, and the steepest ground
    /// a soldier will stand on: a hex whose own slope is past it is refused however level the
    /// step onto it.
    /// </summary>
    public double MaxGrade { get; init; } = 0.7;

    /// <summary>The descent grade from which a step can be hurried: taken at a run, for less, at the risk of a fall.</summary>
    public double HurryGrade { get; init; } = 0.25;

    /// <summary>Points taken off a hurried descent per unit of grade.</summary>
    public double HurryPerGrade { get; init; } = 3;

    /// <summary>The chance that a hurried step ends in a fall, per unit of grade.</summary>
    public double TripPerGrade { get; init; } = 0.1;

    /// <summary>The stride price for a surface.</summary>
    public int Stride(Surface surface) => surface switch
    {
        Surface.Paved => Paved,
        Surface.Track => Track,
        _ => Open,
    };
}
