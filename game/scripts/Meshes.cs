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
        => HexPrism(radius, height, chamfer, material, null, 0f);

    /// <summary>
    /// The piece with a nose: a short bar out of the front face along +X at a given height,
    /// in its own material, so the piece has a way it is facing. Part of the one mesh rather
    /// than a child, so the portrait rendered from the mesh has it too.
    /// </summary>
    public static ArrayMesh HexPrism(float radius, float height, float chamfer, Material material, Material? nose, float noseHeight)
    {
        var mesh = Prism(radius, height, chamfer, material);
        if (nose is null) return mesh;

        // Out of the middle of the +X face, which lies at the apothem rather than the radius.
        var apothem = radius * 0.8660254f;
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        Box(st, new Vector3(apothem - NoseLength / 6f, noseHeight - NoseWidth / 2f, -NoseWidth / 2f),
            new Vector3(apothem + NoseLength, noseHeight + NoseWidth / 2f, NoseWidth / 2f));
        st.Commit(mesh);
        mesh.SurfaceSetMaterial(1, nose);
        return mesh;
    }

    /// <summary>The nose sticks this far out of the face; v1 found a bar this size the one mark that reads from every camera bearing.</summary>
    private const float NoseLength = 0.3f;
    private const float NoseWidth = 0.12f;

    private static ArrayMesh Prism(float radius, float height, float chamfer, Material material)
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

    /// <summary>The height of the ground at a point on the plane, for draping marks over it.</summary>
    public delegate float HeightAt(float x, float z);

    /// <summary>A flat band along a polyline on the ground, or null for fewer than two points.</summary>
    public static ArrayMesh? Ribbon(IReadOnlyList<Vector3> points, float width, Material material, HeightAt? drape = null)
        => Ribbons(new[] { points }, width, material, drape);

    /// <summary>
    /// Flat bands along several polylines at once, or null if none has two points. With a
    /// drape the bands follow the ground: long segments are cut into metre steps and every
    /// point takes the ground's height.
    /// </summary>
    public static ArrayMesh? Ribbons(IReadOnlyList<IReadOnlyList<Vector3>> polylines, float width, Material material, HeightAt? drape = null)
    {
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);

        var any = false;
        foreach (var polyline in polylines)
        {
            if (polyline.Count < 2) continue;
            any = true;

            var points = drape is null ? polyline : Draped(polyline, drape);
            for (var i = 0; i + 1 < points.Count; i++) Band(st, points[i], points[i + 1], width);
            foreach (var point in points) Disc(st, point, width / 2f);
        }

        return any ? Finish(st, material) : null;
    }

    private static List<Vector3> Draped(IReadOnlyList<Vector3> polyline, HeightAt drape)
    {
        var points = new List<Vector3>();
        for (var i = 0; i + 1 < polyline.Count; i++)
        {
            var a = polyline[i];
            var b = polyline[i + 1];
            var steps = Mathf.Max(1, Mathf.CeilToInt(new Vector2(b.X - a.X, b.Z - a.Z).Length()));
            for (var s = 0; s < steps; s++)
            {
                var t = (float)s / steps;
                var x = Mathf.Lerp(a.X, b.X, t);
                var z = Mathf.Lerp(a.Z, b.Z, t);
                points.Add(new Vector3(x, drape(x, z), z));
            }
        }

        var last = polyline[^1];
        points.Add(new Vector3(last.X, drape(last.X, last.Z), last.Z));
        return points;
    }

    /// <summary>A flat ring on the ground around a centre, draped over it if asked.</summary>
    public static ArrayMesh Ring(Vector3 centre, float radius, float width, Material material, HeightAt? drape = null)
    {
        const int sides = 48;
        var points = new List<Vector3>(sides + 1);
        for (var i = 0; i <= sides; i++)
        {
            var a = Mathf.Tau * i / sides;
            points.Add(centre + new Vector3(Mathf.Cos(a) * radius, 0f, Mathf.Sin(a) * radius));
        }

        return Ribbon(points, width, material, drape)!;
    }

    private static void Band(SurfaceTool st, Vector3 a, Vector3 b, float width)
    {
        var along = new Vector3(b.X - a.X, 0f, b.Z - a.Z).Normalized();
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

    /// <summary>An axis-aligned box between two opposite corners, faces outward.</summary>
    private static void Box(SurfaceTool st, Vector3 lo, Vector3 hi)
    {
        Vector3 P(bool x, bool y, bool z) => new(x ? hi.X : lo.X, y ? hi.Y : lo.Y, z ? hi.Z : lo.Z);

        Quad(st, P(true, false, false), P(true, true, false), P(true, true, true), P(true, false, true), Vector3.Right);
        Quad(st, P(false, false, true), P(false, true, true), P(false, true, false), P(false, false, false), Vector3.Left);
        Quad(st, P(false, true, false), P(false, true, true), P(true, true, true), P(true, true, false), Vector3.Up);
        Quad(st, P(false, false, true), P(false, false, false), P(true, false, false), P(true, false, true), Vector3.Down);
        Quad(st, P(false, false, true), P(true, false, true), P(true, true, true), P(false, true, true), Vector3.Back);
        Quad(st, P(true, false, false), P(false, false, false), P(false, true, false), P(true, true, false), Vector3.Forward);
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
