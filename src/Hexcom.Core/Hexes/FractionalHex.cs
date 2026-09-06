namespace Hexcom.Core.Hexes;

/// <summary>A hex coordinate with continuous components, used for rounding and interpolation.</summary>
public readonly record struct FractionalHex(double Q, double R)
{
    public double S => -Q - R;

    /// <summary>Snap to the nearest whole hex, preserving the cube constraint.</summary>
    public Hex Round()
    {
        var q = (int)Math.Round(Q);
        var r = (int)Math.Round(R);
        var s = (int)Math.Round(S);

        var dq = Math.Abs(q - Q);
        var dr = Math.Abs(r - R);
        var ds = Math.Abs(s - S);

        // Discard whichever axis moved furthest and rebuild it from the other two.
        if (dq > dr && dq > ds) q = -r - s;
        else if (dr > ds) r = -q - s;

        return new Hex(q, r);
    }

    public static FractionalHex Lerp(FractionalHex a, FractionalHex b, double t)
        => new(a.Q + (b.Q - a.Q) * t, a.R + (b.R - a.R) * t);
}
