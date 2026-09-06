using System.Collections.Generic;
using Hexcom.Core.Maps;

namespace Hexcom.Core.Vision;

/// <summary>
/// One wall standing between an observer and a target, and how much of the target it hides.
/// </summary>
/// <param name="Wall">The offending segment.</param>
/// <param name="Along">Where the crossing sits on the sight line, 0 at the eye and 1 at the target.</param>
/// <param name="HiddenFraction">
/// Share of the target silhouette this wall conceals, from 0 to 1. Reaching 1 means the whole
/// body is behind it.
/// </param>
/// <param name="WallTop">Height of the top of the wall, for debugging and interface readouts.</param>
/// <param name="DistanceToTarget">Ground distance from the crossing to the target, in metres.</param>
public sealed record Obstruction(
    WallSegment Wall,
    double Along,
    double HiddenFraction,
    double WallTop,
    double DistanceToTarget);

/// <summary>
/// The answer to "can this unit see that one, and how exposed is it".
/// </summary>
/// <param name="CanSee">
/// Whether any part of the target silhouette is visible. Cover does not imply invisibility: a
/// soldier crouched behind sandbags is in half cover and plainly in view.
/// </param>
/// <param name="Cover">The protection the target enjoys against a shot from this vantage.</param>
/// <param name="CoverSource">
/// The wall responsible for that grade, so the interface can point at the actual sandbag rather
/// than showing an abstract shield.
/// </param>
/// <param name="Exposure">
/// Share of the target silhouette a shooter can actually see, from 0 to 1. Drives hit chance
/// once shooting exists.
/// </param>
/// <param name="Blocker">The wall that hid the target, when nothing is visible.</param>
/// <param name="Distance">Straight-line distance between the two, in metres.</param>
/// <param name="HeightAdvantage">Floor height of the observer minus that of the target.</param>
/// <param name="Obstructions">Everything the line ran into, nearest the observer first.</param>
public sealed record SightResult(
    bool CanSee,
    CoverGrade Cover,
    WallSegment? CoverSource,
    double Exposure,
    WallSegment? Blocker,
    double Distance,
    double HeightAdvantage,
    IReadOnlyList<Obstruction> Obstructions)
{
    /// <summary>A clear view with nothing in the way.</summary>
    public bool IsClearShot => CanSee && Cover == CoverGrade.None;

    /// <summary>Looking down on the target from at least half a storey up.</summary>
    public bool HasHighGround => HeightAdvantage >= 1.5;

    internal static SightResult Hidden(
        WallSegment? blocker,
        double distance,
        double heightAdvantage,
        IReadOnlyList<Obstruction> obstructions)
        => new(false, CoverGrade.Full, blocker, 0, blocker, distance, heightAdvantage, obstructions);
}
