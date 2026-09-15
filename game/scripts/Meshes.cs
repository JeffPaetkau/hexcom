using System.Collections.Generic;
using Godot;

namespace Hexcom.Game;

/// <summary>Meshes built in code: the board-game piece and the flat white overlays on the ground.</summary>
public static class Meshes
{
    /// <summary>
    /// A flat-topped hexagonal prism with a chamfered top edge, standing on y = 0: a wooden
    /// board-game piece. Corners at 60-degree steps from +X, matching <c>Hex.Corner</c>.
    /// </summary>
    public static ArrayMesh HexPrism(float radius, float height, float chamfer, Material material)
    {
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);

        var inner = radius - chamfer;
        var shoulder = height - chamfer;

        for (var i = 0; i < 6; i++)
        {
            var a0 = Mathf.DegToRad(60f * i);
            var a1 = Mathf.DegToRad(60f * (i + 1));
            var c0 = new Vector3(Mathf.Cos(a0), 0f, Mathf.Sin(a0));
            var c1 = new Vector3(Mathf.Cos(a1), 0f, Mathf.Sin(a1));

            // Outward normal of this face, halfway between the two corners.
            var facing = (c0 + c1).Normalized();

            // Side, from the ground up to the shoulder.
            Quad(st, c1 * radius + Vector3.Up * shoulder, c0 * radius + Vector3.Up * shoulder, c0 * radius, c1 * radius, facing);

            // Chamfer, from the shoulder in and up to the top.
            var slope = (facing + Vector3.Up).Normalized();
            Quad(st, c1 * inner + Vector3.Up * height, c0 * inner + Vector3.Up * height,
                c0 * radius + Vector3.Up * shoulder, c1 * radius + Vector3.Up * shoulder, slope);

            // Top, a fan from the centre.
            st.SetNormal(Vector3.Up);
            st.AddVertex(Vector3.Up * height);
            st.AddVertex(c0 * inner + Vector3.Up * height);
            st.AddVertex(c1 * inner + Vector3.Up * height);
        }

        var mesh = st.Commit();
        mesh.SurfaceSetMaterial(0, material);
        return mesh;
    }

    /// <summary>A flat band along a polyline on the ground, or null for fewer than two points.</summary>
    public static ArrayMesh? Ribbon(IReadOnlyList<Vector3> points, float width, Material material)
        => Ribbons(new[] { points }, width, material);

    /// <summary>Flat bands along several polylines at once, or null if none has two points.</summary>
    public static ArrayMesh? Ribbons(IReadOnlyList<IReadOnlyList<Vector3>> polylines, float width, Material material)
    {
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);

        var any = false;
        foreach (var points in polylines)
        {
            if (points.Count < 2) continue;
            any = true;

            for (var i = 0; i + 1 < points.Count; i++) Band(st, points[i], points[i + 1], width);
            foreach (var point in points) Disc(st, point, width / 2f);
        }

        return any ? Finish(st, material) : null;
    }

    /// <summary>Flat bands along separate segments on the ground, or null for none.</summary>
    public static ArrayMesh? Segments(IReadOnlyList<(Vector3 A, Vector3 B)> segments, float width, Material material)
    {
        if (segments.Count == 0) return null;

        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);

        foreach (var (a, b) in segments)
        {
            Band(st, a, b, width);
            Disc(st, a, width / 2f);
            Disc(st, b, width / 2f);
        }

        return Finish(st, material);
    }

    /// <summary>A flat ring on the ground, centred on the origin.</summary>
    public static ArrayMesh Ring(float radius, float width, Material material)
    {
        const int sides = 48;
        var points = new List<Vector3>(sides + 1);
        for (var i = 0; i <= sides; i++)
        {
            var a = Mathf.Tau * i / sides;
            points.Add(new Vector3(Mathf.Cos(a) * radius, 0f, Mathf.Sin(a) * radius));
        }

        return Ribbon(points, width, material)!;
    }

    private static void Band(SurfaceTool st, Vector3 a, Vector3 b, float width)
    {
        var along = (b - a).Normalized();
        var across = new Vector3(-along.Z, 0f, along.X) * (width / 2f);
        Quad(st, a + across, b + across, b - across, a - across, Vector3.Up);
    }

    private static void Disc(SurfaceTool st, Vector3 centre, float radius)
    {
        const int sides = 10;
        st.SetNormal(Vector3.Up);
        for (var i = 0; i < sides; i++)
        {
            var a0 = Mathf.Tau * i / sides;
            var a1 = Mathf.Tau * (i + 1) / sides;
            st.AddVertex(centre);
            st.AddVertex(centre + new Vector3(Mathf.Cos(a0), 0f, Mathf.Sin(a0)) * radius);
            st.AddVertex(centre + new Vector3(Mathf.Cos(a1), 0f, Mathf.Sin(a1)) * radius);
        }
    }

    private static void Quad(SurfaceTool st, Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 normal)
    {
        st.SetNormal(normal);
        st.AddVertex(a);
        st.AddVertex(b);
        st.AddVertex(c);
        st.AddVertex(a);
        st.AddVertex(c);
        st.AddVertex(d);
    }

    private static ArrayMesh Finish(SurfaceTool st, Material material)
    {
        var mesh = st.Commit();
        mesh.SurfaceSetMaterial(0, material);
        return mesh;
    }
}
