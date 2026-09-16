using System;
using System.Collections.Generic;
using Godot;

namespace Hexcom.Game;

/// <summary>
/// Turns the hex-edge boundary of a region into the line drawn round it: the same edges,
/// set a little inside the region, with the corners rounded.
/// </summary>
/// <remarks>
/// Works in ground-plane coordinates (x, z). The input is the set of hex edges that face out
/// of the region, each oriented the same way round its hex, so they link into closed loops;
/// a region with a hole gives two. The line follows the edges rather than straightening
/// them: a priced reach is genuinely notched, and a line cut across the notches ran through
/// hexes and matched nothing on the ground. Kept just inside the edges, the line never sits
/// on a grid line and every hex inside it is plainly inside it.
/// </remarks>
public static class Outline
{
    /// <param name="edges">Outward-facing hex edges, oriented consistently.</param>
    /// <param name="inset">How far the line sits inside the edges.</param>
    /// <param name="cornerRadius">The radius every corner is rounded to.</param>
    public static List<List<Vector2>> Smooth(IReadOnlyList<(Vector2 A, Vector2 B)> edges, float inset, float cornerRadius)
    {
        var loops = new List<List<Vector2>>();
        foreach (var loop in Link(edges))
        {
            if (loop.Count < 3) continue;
            loops.Add(Fillet(Inset(Tidy(loop), inset), cornerRadius));
        }
        return loops;
    }

    /// <summary>Chain edges end to start into closed loops.</summary>
    private static List<List<Vector2>> Link(IReadOnlyList<(Vector2 A, Vector2 B)> edges)
    {
        var byStart = new Dictionary<(int, int), List<int>>();
        for (var i = 0; i < edges.Count; i++)
        {
            var key = Key(edges[i].A);
            if (!byStart.TryGetValue(key, out var list)) byStart[key] = list = new List<int>();
            list.Add(i);
        }

        var used = new bool[edges.Count];
        var loops = new List<List<Vector2>>();

        for (var start = 0; start < edges.Count; start++)
        {
            if (used[start]) continue;

            // Walk from edge to the edge that begins where it ends, until the trail runs out,
            // which on a closed boundary is back at the start.
            var loop = new List<Vector2>();
            var at = start;
            while (at >= 0 && !used[at])
            {
                used[at] = true;
                loop.Add(edges[at].A);

                var endKey = Key(edges[at].B);
                at = -1;
                if (byStart.TryGetValue(endKey, out var next))
                {
                    foreach (var candidate in next)
                    {
                        if (!used[candidate]) { at = candidate; break; }
                    }
                }
            }

            loops.Add(loop);
        }

        return loops;
    }

    private static (int, int) Key(Vector2 p) => (Mathf.RoundToInt(p.X * 1000f), Mathf.RoundToInt(p.Y * 1000f));

    /// <summary>Merge runs of collinear edges into one, so a straight side is one segment.</summary>
    private static List<Vector2> Tidy(List<Vector2> loop)
    {
        var points = new List<Vector2>(loop);
        for (var i = 0; i < points.Count && points.Count > 3; i++)
        {
            var a = points[(i + points.Count - 1) % points.Count];
            var v = points[i];
            var b = points[(i + 1) % points.Count];
            if (Mathf.Abs((v - a).Normalized().Cross((b - v).Normalized())) < 1e-4f)
            {
                points.RemoveAt(i);
                i--;
            }
        }
        return points;
    }

    private static float SignedArea(List<Vector2> poly)
    {
        var area = 0f;
        for (var i = 0; i < poly.Count; i++) area += poly[i].Cross(poly[(i + 1) % poly.Count]);
        return area;
    }

    /// <summary>Move every edge inward by a distance and re-intersect the neighbours.</summary>
    private static List<Vector2> Inset(List<Vector2> poly, float distance)
    {
        var n = poly.Count;
        if (n < 3 || distance == 0f) return poly;

        var inwardIsLeft = SignedArea(poly) > 0f;

        var origins = new Vector2[n];
        var directions = new Vector2[n];
        for (var i = 0; i < n; i++)
        {
            var d = (poly[(i + 1) % n] - poly[i]).Normalized();
            var normal = inwardIsLeft ? new Vector2(-d.Y, d.X) : new Vector2(d.Y, -d.X);
            origins[i] = poly[i] + normal * distance;
            directions[i] = d;
        }

        var result = new List<Vector2>(n);
        for (var i = 0; i < n; i++)
        {
            var prev = (i + n - 1) % n;
            var cross = directions[prev].Cross(directions[i]);
            if (Mathf.Abs(cross) < 1e-6f)
            {
                result.Add(origins[i]);
                continue;
            }

            var t = (origins[i] - origins[prev]).Cross(directions[i]) / cross;
            result.Add(origins[prev] + directions[prev] * t);
        }
        return result;
    }

    /// <summary>Round every corner with an arc, shrinking the radius where an edge is too short for it.</summary>
    private static List<Vector2> Fillet(List<Vector2> poly, float radius)
    {
        var n = poly.Count;
        var result = new List<Vector2>();

        for (var i = 0; i < n; i++)
        {
            var a = poly[(i + n - 1) % n];
            var v = poly[i];
            var b = poly[(i + 1) % n];

            var u = (v - a).Normalized();
            var w = (b - v).Normalized();

            var angle = Mathf.Acos(Mathf.Clamp((-u).Dot(w), -1f, 1f));
            if (angle > Mathf.Pi - 0.01f || angle < 0.01f)
            {
                result.Add(v);
                continue;
            }

            var half = angle / 2f;
            var tangent = radius / Mathf.Tan(half);
            var room = Mathf.Min(v.DistanceTo(a), v.DistanceTo(b)) / 2f;
            if (tangent > room)
            {
                tangent = room;
                radius = tangent * Mathf.Tan(half);
            }

            var p1 = v - u * tangent;
            var p2 = v + w * tangent;
            var bisector = (w - u).Normalized();
            var centre = v + bisector * (radius / Mathf.Sin(half));

            var a1 = (p1 - centre).Angle();
            var a2 = (p2 - centre).Angle();
            var sweep = Mathf.Wrap(a2 - a1, -Mathf.Pi, Mathf.Pi);
            var steps = Math.Max(2, Mathf.CeilToInt(Mathf.Abs(sweep) / Mathf.DegToRad(10f)));

            for (var s = 0; s <= steps; s++)
            {
                var t = a1 + sweep * s / steps;
                result.Add(centre + new Vector2(Mathf.Cos(t), Mathf.Sin(t)) * radius);
            }
        }

        return result;
    }
}
