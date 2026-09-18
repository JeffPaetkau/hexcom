using System;
using System.Collections.Generic;

namespace Hexcom.Rules;

/// <summary>
/// The dials on seeing: how far, how wide, and how much a soldier makes out of what is off to
/// the side or behind. Balance, not structure; every number here was set by reasoning.
/// </summary>
/// <remarks>
/// <para>
/// The eye and body heights are the ones the picture draws, since a body drawn any other size
/// would disagree with the rules about whether a bank hides it. The arcs and acuities are v1's,
/// where they were about how fast a sentry noticed you: a front arc watched properly, a
/// peripheral band where you are caught in the corner of an eye, and a rear where people do
/// turn round, but rarely. Here they say how clearly the ground in each direction is made out,
/// and the fog on screen is drawn from that, so a soldier's back is fogged and turning to look
/// is worth its four points.
/// </para>
/// <para>
/// The range is one number, the weather's: the distance at which a standing man in the open,
/// straight ahead, is half made out. Forty metres is a clear day; a foggy dawn is a fifth of
/// that. Smoke, night and the rest will thicken it locally or all over when they come.
/// </para>
/// </remarks>
public sealed record SightModel
{
    public static readonly SightModel Default = new();

    /// <summary>Where a standing soldier looks from, metres above the ground.</summary>
    public double EyeHeight { get; init; } = 1.65;

    /// <summary>The top of a standing soldier, metres above the ground: the last of them to vanish behind a bank.</summary>
    public double BodyHeight { get; init; } = 1.8;

    /// <summary>Metres at which a standing man in the open, straight ahead, is half made out.</summary>
    public double HalfSightMetres { get; init; } = 40;

    /// <summary>Total width of the arc a soldier is properly watching, degrees, centred on their facing.</summary>
    public double FrontArcDegrees { get; init; } = 120;

    /// <summary>Total width of the arc a soldier can see into at all before it is only their back.</summary>
    public double PeripheralArcDegrees { get; init; } = 200;

    /// <summary>Share of full clarity in the corner of the eye.</summary>
    public double PeripheralAcuity { get; init; } = 0.45;

    /// <summary>Share of full clarity behind: not nothing, since people do turn round, but not much.</summary>
    public double RearAcuity { get; init; } = 0.08;

    /// <summary>Degrees over which one band gives way to the next, so the fog has no hard spokes. Thirty: at twenty the edge of the front arc still read as a ray on the ground.</summary>
    public double ArcBlendDegrees { get; init; } = 30;

    /// <summary>Clarity from which a soldier standing on a hex is seen at all, and can be fired at.</summary>
    public double SeenAt { get; init; } = 0.1;

    /// <summary>Clarity below which a hex is not worth working out; the reach of a survey.</summary>
    public double Negligible { get; init; } = 0.02;
}

/// <summary>
/// How clearly a soldier makes out each hex around them: the fog of war, as a number per hex.
/// </summary>
/// <remarks>
/// <para>
/// Clarity is the answer to one question, "how well could I make out a standing man there",
/// from nothing to one, and it is three things multiplied. The ground: a line from the eye to
/// the man's feet, with every hex it crosses projecting the top of its ground onto him as a
/// waterline, so a bank hides him from the feet up and the share of him still showing is the
/// share of his height above the highest waterline. This is v1's sight trace with the ground
/// itself as the wall, and it is scale-free: elevation, banks and cliffs all fall out of it,
/// standing back from a cliff edge hides you from below, and from the top of one you see
/// everything. The air: clarity halves at the weather's distance and falls off on a bell,
/// <c>exp(-ln2 (d/half)^2)</c>, so it is gone within three halves and a survey has a finite
/// reach; a plain extinction along the line would tail on for ever, and when smoke comes it
/// will thicken this locally rather than replace it. The eye: full in the front arc, less to
/// the side, little behind, blended between the bands.
/// </para>
/// <para>
/// What is not here, on purpose: knowledge. What a soldier was told, saw last turn or heard is
/// not a clearing of the fog but a mark on the ground, and it will be kept elsewhere.
/// </para>
/// </remarks>
public sealed class Sight
{
    private readonly IGround _ground;
    private readonly Dictionary<Hex, double> _heights = new();

    public Sight(IGround ground, SightModel? model = null)
    {
        _ground = ground;
        Model = model ?? SightModel.Default;
    }

    public SightModel Model { get; }

    /// <summary>Metres beyond which nothing is made out at all, whichever way a soldier faces: where the bell falls to negligible.</summary>
    public double ReachMetres => Model.HalfSightMetres * Math.Sqrt(Math.Log(1 / Model.Negligible) / Math.Log(2));

    /// <summary>The same reach in hexes either way from the soldier, rounded out: the hexagon a survey works over.</summary>
    public int ReachHexes => (int)Math.Ceiling(ReachMetres / Units.Stride) + 1;

    /// <summary>The height of the ground at a hex's centre, remembered.</summary>
    public double HeightAt(Hex hex)
    {
        if (_heights.TryGetValue(hex, out var known)) return known;

        var (x, z) = hex.Centre;
        known = _ground.Height(x, z);
        _heights[hex] = known;
        return known;
    }

    /// <summary>
    /// The share of a standing man on one hex that the ground leaves showing from the eye of
    /// a soldier on another, from nothing to one. One for the same hex and the next.
    /// </summary>
    public double Exposure(Hex from, Hex to)
    {
        if (from == to) return 1;

        var eye = HeightAt(from) + Model.EyeHeight;
        var foot = HeightAt(to);
        var line = to == from ? Array.Empty<Hex>() : (IReadOnlyList<Hex>)from.LineTo(to);
        var n = line.Count - 1;

        // Each hex between projects its ground, seen from the eye, onto the man: the highest
        // such waterline is what he stands behind.
        var waterline = double.NegativeInfinity;
        for (var i = 1; i < n; i++)
        {
            var t = (double)i / n;
            var projected = eye + (HeightAt(line[i]) - eye) / t;
            if (projected > waterline) waterline = projected;
        }

        var hidden = Math.Clamp((waterline - foot) / Model.BodyHeight, 0, 1);
        return 1 - hidden;
    }

    /// <summary>How much the air leaves at a distance: one close by, a half at the weather's distance, nothing far off.</summary>
    public double RangeFactor(double metres)
    {
        var ratio = metres / Model.HalfSightMetres;
        return Math.Exp(-Math.Log(2) * ratio * ratio);
    }

    /// <summary>
    /// How much a soldier facing one way makes out at an angle off it: full in front, a share
    /// to the side, little behind, blended between.
    /// </summary>
    public double ArcFactor(double offDegrees)
    {
        var off = Math.Abs(offDegrees);
        var front = Model.FrontArcDegrees / 2;
        var side = Model.PeripheralArcDegrees / 2;
        var blend = Model.ArcBlendDegrees;

        if (off <= front) return 1;
        if (off <= front + blend) return Lerp(1, Model.PeripheralAcuity, (off - front) / blend);
        if (off <= side) return Model.PeripheralAcuity;
        if (off <= side + blend) return Lerp(Model.PeripheralAcuity, Model.RearAcuity, (off - side) / blend);
        return Model.RearAcuity;
    }

    /// <summary>Degrees between a facing and the bearing from one hex to another, from nothing to a hundred and eighty.</summary>
    public static double OffFacingDegrees(int facing, Hex from, Hex to)
    {
        var (x0, z0) = from.Centre;
        var (x1, z1) = to.Centre;
        var bearing = Math.Atan2(z1 - z0, x1 - x0) * 180 / Math.PI;
        var off = (bearing - Facing.BearingDegrees(facing)) % 360;
        if (off > 180) off -= 360;
        if (off < -180) off += 360;
        return Math.Abs(off);
    }

    /// <summary>How clearly a soldier on one hex, facing one way, makes out a standing man on another.</summary>
    public double Clarity(Hex from, int facing, Hex to)
    {
        if (from == to) return 1;

        var air = RangeFactor(Shooting.Range(from, to)) * ArcFactor(OffFacingDegrees(facing, from, to));
        if (air < Model.Negligible) return 0;

        return air * Exposure(from, to);
    }

    /// <summary>
    /// Everything a soldier makes out from a hex, facing one way: the clarity of every hex out
    /// to the reach of the air, with what is negligible left out.
    /// </summary>
    public View Survey(Hex from, int facing)
    {
        var clarity = new Dictionary<Hex, double> { [from] = 1 };
        var reach = ReachHexes;

        for (var dq = -reach; dq <= reach; dq++)
        for (var dr = Math.Max(-reach, -dq - reach); dr <= Math.Min(reach, -dq + reach); dr++)
        {
            var hex = new Hex(from.Q + dq, from.R + dr);
            if (hex == from) continue;

            var seen = Clarity(from, facing, hex);
            if (seen > 0) clarity[hex] = seen;
        }

        return new View(from, facing, Model, clarity);
    }

    private static double Lerp(double a, double b, double t) => a + (b - a) * t;
}

/// <summary>What one soldier makes out from where they stand: a clarity per hex, and which hexes count as seen.</summary>
public sealed class View
{
    private readonly SightModel _model;
    private readonly Dictionary<Hex, double> _clarity;

    internal View(Hex from, int facing, SightModel model, Dictionary<Hex, double> clarity)
    {
        From = from;
        Facing = facing;
        _model = model;
        _clarity = clarity;
    }

    public Hex From { get; }

    public int Facing { get; }

    /// <summary>How many hexes are made out at all.</summary>
    public int Count => _clarity.Count;

    /// <summary>Every hex made out at all, with its clarity.</summary>
    public IEnumerable<KeyValuePair<Hex, double>> Hexes => _clarity;

    /// <summary>How clearly a hex is made out, nothing for one that is not.</summary>
    public double ClarityAt(Hex hex) => _clarity.TryGetValue(hex, out var c) ? c : 0;

    /// <summary>Whether a soldier standing on a hex would be seen.</summary>
    public bool Sees(Hex hex) => ClarityAt(hex) >= _model.SeenAt;
}
