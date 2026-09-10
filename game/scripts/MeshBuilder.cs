using System.Collections.Generic;
using Godot;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;

namespace Hexcom.Game;

/// <summary>
/// Accumulates coloured triangles and hands them back as one mesh.
/// </summary>
/// <remarks>
/// <para>
/// A blockout is boxes, and eighteen hundred tiles as eighteen hundred nodes is the wrong shape
/// for the engine: a node per prism costs a draw call and a transform each, and rebuilding two
/// thousand of them after every action is the slow path. One mesh with a colour per vertex is
/// a single draw call, and rebuilding it is a few arrays — measured well under a frame for the
/// whole waystation, which matters because the ground is recoloured every time the active
/// soldier changes.
/// </para>
/// <para>
/// Every face carries its own normal and every triangle is emitted with its own three
/// vertices, so there is nothing to weld and no face inherits its neighbour's shading. Winding
/// is not relied on either: the materials in <see cref="SandboxPalette"/> cull nothing, so a
/// polygon handed in clockwise draws the same as one handed in counter-clockwise, and a session
/// that gets a hex's corner order backwards produces a picture rather than a hole.
/// </para>
/// </remarks>
public sealed class MeshBuilder
{
    private readonly List<Vector3> _vertices = [];
    private readonly List<Vector3> _normals = [];
    private readonly List<Color> _colors = [];

    /// <summary>Whether anything has been added. An empty surface is refused by the engine.</summary>
    public bool IsEmpty => _vertices.Count == 0;

    /// <summary>One triangle, with the normal it should be lit by.</summary>
    public void Triangle(Vector3 a, Vector3 b, Vector3 c, Vector3 normal, Color color)
    {
        _vertices.Add(a); _vertices.Add(b); _vertices.Add(c);
        _normals.Add(normal); _normals.Add(normal); _normals.Add(normal);
        _colors.Add(color); _colors.Add(color); _colors.Add(color);
    }

    /// <summary>A flat polygon in the scene, fanned from its first corner. Convex polygons only.</summary>
    public void Polygon(IReadOnlyList<Vector3> corners, Vector3 normal, Color color)
    {
        for (var i = 1; i + 1 < corners.Count; i++)
            Triangle(corners[0], corners[i], corners[i + 1], normal, color);
    }

    /// <summary>A horizontal polygon on the rules' plane, at a height, facing up.</summary>
    public void Flat(IReadOnlyList<CoreVec2> outline, double height, Color color)
    {
        var corners = new Vector3[outline.Count];
        for (var i = 0; i < outline.Count; i++) corners[i] = SandboxScale.ToScene(outline[i], height);
        Polygon(corners, Vector3.Up, color);
    }

    /// <summary>
    /// A vertical-sided prism over an outline on the plane, from one height to another: a tile
    /// at its floor height, a plinth, a body.
    /// </summary>
    /// <param name="sides">
    /// The colour of the walls of the prism. Darker than the top by default, so a raised tile
    /// reads as raised even before the light gets to it.
    /// </param>
    public void Prism(IReadOnlyList<CoreVec2> outline, double bottom, double top, Color color, Color? sides = null)
    {
        var flank = sides ?? color.Darkened(0.35f);
        var n = outline.Count;

        Flat(outline, top, color);

        for (var i = 0; i < n; i++)
        {
            var a = outline[i];
            var b = outline[(i + 1) % n];
            var edge = b - a;
            var normal = SandboxScale.ToScene(new CoreVec2(edge.Y, -edge.X).Normalized, 0);

            Polygon(
                [
                    SandboxScale.ToScene(a, bottom), SandboxScale.ToScene(b, bottom),
                    SandboxScale.ToScene(b, top), SandboxScale.ToScene(a, top),
                ],
                normal,
                flank);
        }
    }

    /// <summary>
    /// A box standing on the plane: its footprint is a rectangle of the given length along a
    /// bearing and the given width across it, centred on a point.
    /// </summary>
    public void Box(CoreVec2 centre, double bearingRadians, double length, double width, double bottom, double top, Color color, Color? sides = null)
    {
        var along = new CoreVec2(System.Math.Cos(bearingRadians), System.Math.Sin(bearingRadians)) * (length / 2);
        var across = new CoreVec2(-System.Math.Sin(bearingRadians), System.Math.Cos(bearingRadians)) * (width / 2);

        Prism([centre + along + across, centre - along + across, centre - along - across, centre + along - across],
            bottom, top, color, sides);
    }

    /// <summary>A wall: a thin box from one plane point to another, between two heights.</summary>
    public void Slab(CoreVec2 a, CoreVec2 b, double thickness, double bottom, double top, Color color)
    {
        var edge = b - a;
        Box((a + b) / 2, edge.Angle, edge.Length, thickness, bottom, top, color);
    }

    /// <summary>A cylinder standing on the plane. Twelve sides is round enough for a body.</summary>
    public void Cylinder(CoreVec2 centre, double radius, double bottom, double top, Color color, int segments = 12)
    {
        var outline = new CoreVec2[segments];
        for (var i = 0; i < segments; i++)
        {
            var angle = System.Math.Tau * i / segments;
            outline[i] = centre + new CoreVec2(System.Math.Cos(angle), System.Math.Sin(angle)) * radius;
        }
        Prism(outline, bottom, top, color);
    }

    /// <summary>
    /// A flat ribbon along a run of scene points, lying on the ground with the given width. For
    /// routes, outlines and anything the flat view drew as a polyline.
    /// </summary>
    /// <remarks>
    /// Each segment is a quad on its own and the joins are left to overlap, which is invisible
    /// at the widths drawn here and saves a mitre. A closed loop is the same call with the first
    /// point repeated at the end.
    /// </remarks>
    public void Ribbon(IReadOnlyList<Vector3> points, float width, Color color)
    {
        for (var i = 0; i + 1 < points.Count; i++)
        {
            var a = points[i];
            var b = points[i + 1];
            var run = new Vector3(b.X - a.X, 0, b.Z - a.Z);
            if (run.LengthSquared() < 1e-8f) continue;

            var side = new Vector3(-run.Z, 0, run.X).Normalized() * (width / 2);
            Polygon([a + side, b + side, b - side, a - side], Vector3.Up, color);
        }
    }

    /// <summary>Everything added so far, as one mesh with one surface.</summary>
    public ArrayMesh Build()
    {
        var mesh = new ArrayMesh();
        if (IsEmpty) return mesh;

        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = _vertices.ToArray();
        arrays[(int)Mesh.ArrayType.Normal] = _normals.ToArray();
        arrays[(int)Mesh.ArrayType.Color] = _colors.ToArray();

        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        return mesh;
    }
}
