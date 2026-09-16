using System;
using System.Collections.Generic;

namespace Hexcom.Rules;

/// <summary>
/// A hex on the grid, in axial coordinates. Flat-topped, <see cref="Units.HexSize"/> metres
/// from centre to corner, with north (-Z) along one of the six neighbour directions.
/// </summary>
/// <remarks>
/// Plain C#: nothing here knows about the engine, so it can move into the rules library
/// untouched. Corner <c>i</c> sits at <c>60i</c> degrees from +X towards +Z; the edge from
/// corner <c>i</c> to corner <c>i + 1</c> faces neighbour <c>Directions[i]</c>.
/// </remarks>
public readonly record struct Hex(int Q, int R)
{
    private const double Sqrt3 = 1.7320508075688772;

    /// <summary>The six neighbours, in order of the edge that faces them.</summary>
    public static readonly Hex[] Directions =
    {
        new(1, 0), new(0, 1), new(-1, 1), new(-1, 0), new(0, -1), new(1, -1),
    };

    public int S => -Q - R;

    public Hex Neighbour(int direction)
    {
        var d = Directions[direction];
        return new Hex(Q + d.Q, R + d.R);
    }

    public int DistanceTo(Hex other)
        => (Math.Abs(Q - other.Q) + Math.Abs(R - other.R) + Math.Abs(S - other.S)) / 2;

    /// <summary>The centre on the ground plane, metres.</summary>
    public (double X, double Z) Centre
        => (Units.HexSize * 1.5 * Q, Units.HexSize * Sqrt3 * (R + Q / 2.0));

    /// <summary>Corner <c>i</c> on the ground plane, metres.</summary>
    public (double X, double Z) Corner(int i)
    {
        var (cx, cz) = Centre;
        var angle = i * Math.PI / 3;
        return (cx + Units.HexSize * Math.Cos(angle), cz + Units.HexSize * Math.Sin(angle));
    }

    /// <summary>The hex containing a point on the ground plane.</summary>
    public static Hex At(double x, double z)
    {
        var q = 2.0 / 3.0 * x / Units.HexSize;
        var r = (-1.0 / 3.0 * x + Sqrt3 / 3.0 * z) / Units.HexSize;
        return Round(q, r);
    }

    /// <summary>
    /// The hexes on the straight line from here to another, both ends included. On open
    /// ground this is the path; anything with obstacles will need a real pathfinder.
    /// </summary>
    public IReadOnlyList<Hex> LineTo(Hex other)
    {
        var n = DistanceTo(other);
        var line = new List<Hex>(n + 1);

        // A hair off-centre so a point exactly between two hexes always rounds the same way.
        double q0 = Q + 1e-6, r0 = R + 1e-6, q1 = other.Q + 1e-6, r1 = other.R + 1e-6;

        for (var i = 0; i <= n; i++)
        {
            var t = n == 0 ? 0.0 : (double)i / n;
            line.Add(Round(q0 + (q1 - q0) * t, r0 + (r1 - r0) * t));
        }

        return line;
    }

    private static Hex Round(double q, double r)
    {
        var s = -q - r;
        double rq = Math.Round(q), rr = Math.Round(r), rs = Math.Round(s);
        double dq = Math.Abs(rq - q), dr = Math.Abs(rr - r), ds = Math.Abs(rs - s);

        if (dq > dr && dq > ds) rq = -rr - rs;
        else if (dr > ds) rr = -rq - rs;

        return new Hex((int)rq, (int)rr);
    }

    public override string ToString() => $"({Q}, {R})";
}
