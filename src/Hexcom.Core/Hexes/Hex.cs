using System.Collections.Generic;

namespace Hexcom.Core.Hexes;

/// <summary>
/// An axial hex coordinate. <c>Q</c> and <c>R</c> are stored; the third cube axis
/// <c>S = -Q - R</c> is derived.
/// </summary>
/// <remarks>
/// Axial neighbour offsets are independent of hex orientation — only the pixel layout
/// (see <see cref="HexLayout"/>) cares whether hexes are flat-top or pointy-top. This type
/// therefore has no orientation of its own; corner indices, however, do (see
/// <see cref="Corner"/>), and the core standardises on flat-top.
/// </remarks>
public readonly record struct Hex(int Q, int R)
{
    public static readonly Hex Zero = new(0, 0);

    /// <summary>The implicit third cube axis.</summary>
    public int S => -Q - R;

    public static Hex operator +(Hex a, Hex b) => new(a.Q + b.Q, a.R + b.R);
    public static Hex operator -(Hex a, Hex b) => new(a.Q - b.Q, a.R - b.R);
    public static Hex operator *(Hex a, int k) => new(a.Q * k, a.R * k);
    public static Hex operator *(int k, Hex a) => a * k;

    /// <summary>Number of hex steps from the origin.</summary>
    public int Length => (Math.Abs(Q) + Math.Abs(R) + Math.Abs(S)) / 2;

    /// <summary>Number of hex steps between two hexes, ignoring terrain.</summary>
    public int DistanceTo(Hex other) => (this - other).Length;

    public Hex Neighbor(HexDirection d) => this + d.Offset();

    /// <summary>The six neighbours, in counter-clockwise direction order.</summary>
    public IEnumerable<Hex> Neighbors()
    {
        foreach (var d in HexDirectionExtensions.All)
            yield return Neighbor(d);
    }

    /// <summary>The six neighbours paired with the direction that reaches them.</summary>
    public IEnumerable<(HexDirection Direction, Hex Hex)> NeighborsWithDirection()
    {
        foreach (var d in HexDirectionExtensions.All)
            yield return (d, Neighbor(d));
    }

    /// <summary>
    /// The direction from this hex to an adjacent one, or <c>null</c> if they are not adjacent.
    /// </summary>
    public HexDirection? DirectionTo(Hex other)
    {
        var delta = other - this;
        for (var i = 0; i < 6; i++)
            if (HexDirectionExtensions.Offsets[i] == delta)
                return (HexDirection)i;
        return null;
    }

    /// <summary>
    /// Canonical identity of one of this hex's six corners. Corner <c>i</c> sits at
    /// <c>60*i</c> degrees from the centre in a flat-top layout, so corner 0 is due east.
    /// Corners are shared between three hexes; this returns the shared identity, so the same
    /// physical corner always compares equal no matter which hex you ask through.
    /// </summary>
    public HexVertex Corner(int index)
    {
        var i = ((index % 6) + 6) % 6;
        return i switch
        {
            0 => new HexVertex(Q, R, VertexPole.East),
            1 => new HexVertex(Q + 1, R, VertexPole.West),
            2 => new HexVertex(Q - 1, R + 1, VertexPole.East),
            3 => new HexVertex(Q, R, VertexPole.West),
            4 => new HexVertex(Q - 1, R, VertexPole.East),
            _ => new HexVertex(Q + 1, R - 1, VertexPole.West),
        };
    }

    /// <summary>The six corners in counter-clockwise order starting due east.</summary>
    public HexVertex[] Corners()
    {
        var result = new HexVertex[6];
        for (var i = 0; i < 6; i++) result[i] = Corner(i);
        return result;
    }

    /// <summary>The corner index of <paramref name="vertex"/> on this hex, or -1 if not a corner of it.</summary>
    public int CornerIndexOf(HexVertex vertex)
    {
        for (var i = 0; i < 6; i++)
            if (Corner(i) == vertex) return i;
        return -1;
    }

    /// <summary>All hexes within <paramref name="radius"/> steps, including this one.</summary>
    public IEnumerable<Hex> WithinRange(int radius)
    {
        for (var dq = -radius; dq <= radius; dq++)
        {
            var lo = Math.Max(-radius, -dq - radius);
            var hi = Math.Min(radius, -dq + radius);
            for (var dr = lo; dr <= hi; dr++)
                yield return new Hex(Q + dq, R + dr);
        }
    }

    /// <summary>The hexes exactly <paramref name="radius"/> steps away, counter-clockwise.</summary>
    public IEnumerable<Hex> Ring(int radius)
    {
        if (radius < 0) yield break;
        if (radius == 0) { yield return this; yield break; }

        // Walking from the corner on spoke i in direction i+2 lands exactly on the corner
        // of spoke i+1, so six such runs trace the ring counter-clockwise.
        var hex = this + HexDirection.NorthEast.Offset() * radius;
        for (var i = 0; i < 6; i++)
        {
            var step = ((HexDirection)i).Rotate(2).Offset();
            for (var j = 0; j < radius; j++)
            {
                yield return hex;
                hex += step;
            }
        }
    }

    /// <summary>
    /// The hexes a straight line from here to <paramref name="other"/> passes through,
    /// inclusive of both ends. Ties are nudged consistently so the line never straddles.
    /// </summary>
    public IReadOnlyList<Hex> LineTo(Hex other)
    {
        var n = DistanceTo(other);
        var results = new List<Hex>(n + 1);
        if (n == 0) { results.Add(this); return results; }

        // Nudge both ends off the exact lattice to break ties deterministically.
        var a = new FractionalHex(Q + 1e-6, R + 1e-6);
        var b = new FractionalHex(other.Q + 2e-6, other.R - 1e-6);
        var step = 1.0 / n;
        for (var i = 0; i <= n; i++)
            results.Add(FractionalHex.Lerp(a, b, step * i).Round());
        return results;
    }

    public override string ToString() => $"({Q},{R})";
}
