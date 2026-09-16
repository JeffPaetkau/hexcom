using System;

namespace Hexcom.Game.Rules;

/// <summary>
/// Seeded two-dimensional gradient noise, and a fractal sum of it. Deterministic: the same
/// seed gives the same landscape on every machine, which the rules will one day depend on.
/// </summary>
public sealed class Noise
{
    private static readonly (double X, double Y)[] Gradients =
    {
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071),
    };

    private readonly int[] _perm = new int[512];

    public Noise(int seed)
    {
        var table = new int[256];
        for (var i = 0; i < 256; i++) table[i] = i;

        var rng = new Random(seed);
        for (var i = 255; i > 0; i--)
        {
            var j = rng.Next(i + 1);
            (table[i], table[j]) = (table[j], table[i]);
        }

        for (var i = 0; i < 512; i++) _perm[i] = table[i & 255];
    }

    /// <summary>Smooth noise in roughly -1..1, with one feature per unit of distance.</summary>
    public double Sample(double x, double y)
    {
        var x0 = Math.Floor(x);
        var y0 = Math.Floor(y);
        var xi = (int)x0 & 255;
        var yi = (int)y0 & 255;
        var xf = x - x0;
        var yf = y - y0;

        var u = Fade(xf);
        var v = Fade(yf);

        var aa = _perm[_perm[xi] + yi];
        var ab = _perm[_perm[xi] + yi + 1];
        var ba = _perm[_perm[xi + 1] + yi];
        var bb = _perm[_perm[xi + 1] + yi + 1];

        var n00 = Dot(aa, xf, yf);
        var n10 = Dot(ba, xf - 1, yf);
        var n01 = Dot(ab, xf, yf - 1);
        var n11 = Dot(bb, xf - 1, yf - 1);

        return Lerp(Lerp(n00, n10, u), Lerp(n01, n11, u), v) * 1.4142;
    }

    /// <summary>Octaves of <see cref="Sample"/> summed, each twice the frequency and half the weight, normalised to about -1..1.</summary>
    public double Fbm(double x, double y, int octaves, double lacunarity = 2.0, double gain = 0.5)
    {
        double sum = 0, amplitude = 1, frequency = 1, norm = 0;
        for (var o = 0; o < octaves; o++)
        {
            sum += amplitude * Sample(x * frequency + 31.7 * o, y * frequency + 17.3 * o);
            norm += amplitude;
            amplitude *= gain;
            frequency *= lacunarity;
        }
        return sum / norm;
    }

    private static double Dot(int hash, double x, double y)
    {
        var (gx, gy) = Gradients[hash & 7];
        return gx * x + gy * y;
    }

    private static double Fade(double t) => t * t * t * (t * (t * 6 - 15) + 10);

    private static double Lerp(double a, double b, double t) => a + (b - a) * t;
}
