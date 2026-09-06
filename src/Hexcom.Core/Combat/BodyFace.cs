using System.Collections.Generic;
using System.Linq;

namespace Hexcom.Core.Combat;

/// <summary>
/// One of the six sides of a soldier, named relative to the way they are looking.
/// </summary>
/// <remarks>
/// Body-relative, not compass-relative. The plate that took a round from the north-east is the
/// plate on whichever side was pointing north-east <em>at the time</em>; turn round and it is
/// somewhere else. That is what makes turning to present a fresh side a real decision, and what
/// makes a unit slowly run out of good sides to show.
/// <para>
/// The numbering follows the hex directions, which run counter-clockwise, so a positive step is
/// a step to the soldier's left.
/// </para>
/// </remarks>
public enum BodyFace
{
    /// <summary>The side they are looking over.</summary>
    Front = 0,
    FrontLeft = 1,
    RearLeft = 2,
    Rear = 3,
    RearRight = 4,
    FrontRight = 5,
}

/// <summary>
/// One face as seen from somewhere: how much of the silhouette it accounts for, and how squarely
/// it is being met.
/// </summary>
/// <param name="Share">
/// Fraction of the presented width this face accounts for, from zero to one. The shares of every
/// face in view sum to one, so this is the chance a round arriving from that bearing finds it.
/// </param>
/// <param name="ObliquityDegrees">
/// How far off square the round arrives, from zero head-on to ninety edge-on. A kinetic round
/// meeting a plate at an angle skips off it; a beam does not care.
/// </param>
public readonly record struct FacingAspect(BodyFace Face, double Share, double ObliquityDegrees)
{
    public override string ToString() => $"{Face} {Share:P0} at {ObliquityDegrees:0} deg";
}

/// <summary>
/// Which sides of a soldier something arriving from a given bearing can actually reach.
/// </summary>
/// <remarks>
/// A body is a hexagon, so it never presents one flat face to anybody. Stand in front of someone
/// and you are looking at their front plate square on <em>and</em> a sliver of each shoulder;
/// stand toward a corner and you get two plates at equal, awkward angles. Weighting by how wide
/// each face looks from where you are standing is the whole model, and it produces the shares
/// exactly: a half and two quarters head-on, two halves corner-on.
/// <para>
/// The consequence worth naming is that a defender facing a threat squarely takes half its
/// rounds on an unangled plate, while one showing a corner takes all of them at a slight angle.
/// Which is better depends on the weapon, and choosing costs a point to turn.
/// </para>
/// </remarks>
public static class BodyFaces
{
    /// <summary>Angle between one face normal and the next.</summary>
    public const double DegreesPerFace = 60.0;

    /// <summary>
    /// Slack on the edge-on case. A hexagon met at exactly thirty degrees off a face normal
    /// presents two faces and two more precisely edge-on, and edge-on is a real case on this
    /// grid rather than a rare one — <c>cos 90</c> comes back as 6e-17 rather than zero, and
    /// without slack that sliver becomes a face that can be hit.
    /// </summary>
    private const double EdgeTolerance = 1e-9;

    public static readonly IReadOnlyList<BodyFace> All =
    [
        BodyFace.Front, BodyFace.FrontLeft, BodyFace.RearLeft,
        BodyFace.Rear, BodyFace.RearRight, BodyFace.FrontRight,
    ];

    /// <summary>
    /// Every face something at <paramref name="angleOffFacing"/> can reach, widest first.
    /// </summary>
    /// <param name="angleOffFacing">
    /// Bearing to the threat measured from the way the unit is looking, in degrees, positive to
    /// the unit's left. Zero means directly in front.
    /// </param>
    public static IReadOnlyList<FacingAspect> Presented(double angleOffFacing)
    {
        var found = new List<(BodyFace Face, double Width, double Obliquity)>(3);
        var total = 0.0;

        for (var k = 0; k < 6; k++)
        {
            var obliquity = Math.Abs(Normalise(angleOffFacing - DegreesPerFace * k));
            var width = Math.Cos(obliquity * Math.PI / 180.0);
            if (width <= EdgeTolerance) continue;

            found.Add(((BodyFace)k, width, obliquity));
            total += width;
        }

        return found
            .OrderByDescending(f => f.Width)
            .ThenBy(f => (int)f.Face)
            .Select(f => new FacingAspect(f.Face, f.Width / total, f.Obliquity))
            .ToList();
    }

    /// <summary>The face most squarely presented to something at this bearing.</summary>
    public static BodyFace Nearest(double angleOffFacing)
    {
        var index = (int)Math.Round(angleOffFacing / DegreesPerFace, MidpointRounding.AwayFromZero);
        return (BodyFace)(((index % 6) + 6) % 6);
    }

    /// <summary>Fold an angle in degrees onto the range (-180, 180].</summary>
    private static double Normalise(double degrees)
    {
        var folded = degrees % 360.0;
        if (folded > 180.0) folded -= 360.0;
        if (folded <= -180.0) folded += 360.0;
        return folded;
    }
}
