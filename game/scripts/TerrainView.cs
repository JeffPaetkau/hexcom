using System.Collections.Generic;
using System.Threading.Tasks;
using Godot;
using Hexcom.Game.Rules;

namespace Hexcom.Game;

/// <summary>
/// Draws the <see cref="Terrain"/> as a quadtree of mesh chunks around the camera: 32 by 32
/// quads each, a metre apart close in and doubling with every step out, to eight kilometres.
/// </summary>
/// <remarks>
/// Chunks are keyed by size and position and built once, so moving the camera only builds the
/// few that come into range. Heights and normals come from the height function itself rather
/// than from neighbouring vertices, which is why coarse and fine chunks shade alike where they
/// meet; a skirt hanging from every edge hides the hairline crack that different resolutions
/// leave between them.
/// </remarks>
public partial class TerrainView : Node3D
{
    private const float RootSize = 8192f;
    private const int Quads = 32;
    private const float LeafSize = 32f;

    /// <summary>A chunk splits while the camera focus is within this many chunk-widths of it.</summary>
    private const float SplitFactor = 1.5f;

    /// <summary>How far the focus moves before the chunk set is reconsidered, metres.</summary>
    private const float Refresh = 8f;

    private readonly Terrain _terrain;
    private readonly Material _material;
    private readonly Dictionary<(int Size, int Ix, int Iz), MeshInstance3D> _chunks = new();
    private Vector2? _lastFocus;

    public TerrainView(Terrain terrain, Material material)
    {
        _terrain = terrain;
        _material = material;
        Name = "Terrain";
    }

    /// <summary>Bring the chunk set up to date for a camera focus on the ground plane.</summary>
    public void Update(Vector2 focus)
    {
        if (_lastFocus is { } last && last.DistanceTo(focus) < Refresh) return;
        _lastFocus = focus;

        var wanted = new HashSet<(int, int, int)>();
        Select(-RootSize / 2f, -RootSize / 2f, RootSize, focus, wanted);

        foreach (var key in wanted)
        {
            if (_chunks.ContainsKey(key)) continue;
            var chunk = Build(key);
            _chunks[key] = chunk;
            AddChild(chunk);
        }

        var stale = new List<(int, int, int)>();
        foreach (var key in _chunks.Keys)
        {
            if (!wanted.Contains(key)) stale.Add(key);
        }
        foreach (var key in stale)
        {
            _chunks[key].QueueFree();
            _chunks.Remove(key);
        }
    }

    private static void Select(float x0, float z0, float size, Vector2 focus, HashSet<(int, int, int)> wanted)
    {
        var dx = Mathf.Max(Mathf.Max(x0 - focus.X, 0f), focus.X - (x0 + size));
        var dz = Mathf.Max(Mathf.Max(z0 - focus.Y, 0f), focus.Y - (z0 + size));
        var distance = Mathf.Sqrt(dx * dx + dz * dz);

        if (size > LeafSize && distance < size * SplitFactor)
        {
            var half = size / 2f;
            Select(x0, z0, half, focus, wanted);
            Select(x0 + half, z0, half, focus, wanted);
            Select(x0, z0 + half, half, focus, wanted);
            Select(x0 + half, z0 + half, half, focus, wanted);
            return;
        }

        wanted.Add(((int)size, Mathf.RoundToInt(x0 / size), Mathf.RoundToInt(z0 / size)));
    }

    private MeshInstance3D Build((int Size, int Ix, int Iz) key)
    {
        float size = key.Size;
        var x0 = key.Ix * size;
        var z0 = key.Iz * size;
        var spacing = size / Quads;
        var n = Quads + 1;
        var skirt = Mathf.Max(3f, size / 16f);

        var vertices = new List<Vector3>(n * n + 4 * n);
        var normals = new List<Vector3>(n * n + 4 * n);
        var indices = new List<int>(Quads * Quads * 6 + 4 * Quads * 6);

        for (var j = 0; j < n; j++)
        for (var i = 0; i < n; i++)
        {
            var x = x0 + i * spacing;
            var z = z0 + j * spacing;
            vertices.Add(new Vector3(x, (float)_terrain.Height(x, z), z));
            normals.Add(NormalAt(x, z));
        }

        for (var j = 0; j < Quads; j++)
        for (var i = 0; i < Quads; i++)
        {
            var a = j * n + i;
            var b = a + 1;
            var c = a + n;
            var d = c + 1;
            indices.AddRange(new[] { a, b, c, b, d, c });
        }

        // Skirts: a copy of each edge dropped straight down, joined to the edge by quads.
        Skirt(vertices, normals, indices, n, skirt, i => i);                    // south edge, j = 0
        Skirt(vertices, normals, indices, n, skirt, i => (n - 1) * n + i);      // north edge
        Skirt(vertices, normals, indices, n, skirt, j => j * n);                // west edge
        Skirt(vertices, normals, indices, n, skirt, j => j * n + n - 1);        // east edge

        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = vertices.ToArray();
        arrays[(int)Mesh.ArrayType.Normal] = normals.ToArray();
        arrays[(int)Mesh.ArrayType.Index] = indices.ToArray();

        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        mesh.SurfaceSetMaterial(0, _material);

        return new MeshInstance3D { Mesh = mesh, Name = $"chunk_{key.Size}_{key.Ix}_{key.Iz}" };
    }

    private static void Skirt(List<Vector3> vertices, List<Vector3> normals, List<int> indices, int n, float drop, System.Func<int, int> edgeIndex)
    {
        var first = vertices.Count;
        for (var k = 0; k < n; k++)
        {
            var top = edgeIndex(k);
            vertices.Add(vertices[top] - Vector3.Up * drop);
            normals.Add(normals[top]);
        }

        for (var k = 0; k + 1 < n; k++)
        {
            var a = edgeIndex(k);
            var b = edgeIndex(k + 1);
            var c = first + k;
            var d = first + k + 1;
            indices.AddRange(new[] { a, b, c, b, d, c });
        }
    }

    /// <summary>
    /// The height of the drawn ground at a point: the height function sampled on the finest
    /// chunk grid and interpolated across the same triangles the mesh is built from.
    /// </summary>
    /// <remarks>
    /// Marks laid on the true height function sink into the mesh wherever it cuts a curve
    /// straight, and drawing them without a depth test puts them in front of the pieces that
    /// stand on them. Following the mesh instead lets them be depth tested and lie flat on it.
    /// Exact within the finest chunks, which reach well beyond a turn's walk from the focus.
    /// </remarks>
    public static float MeshHeight(Terrain terrain, float x, float z)
    {
        const float spacing = LeafSize / Quads;
        var x0 = Mathf.Floor(x / spacing) * spacing;
        var z0 = Mathf.Floor(z / spacing) * spacing;
        var fx = (x - x0) / spacing;
        var fz = (z - z0) / spacing;

        // Each quad is split from its (x + 1, z) corner to its (x, z + 1) corner.
        var a = (float)terrain.Height(x0, z0);
        var b = (float)terrain.Height(x0 + spacing, z0);
        var c = (float)terrain.Height(x0, z0 + spacing);
        var d = (float)terrain.Height(x0 + spacing, z0 + spacing);
        return fx + fz <= 1f
            ? a + (b - a) * fx + (c - a) * fz
            : d + (c - d) * (1f - fx) + (b - d) * (1f - fz);
    }

    /// <summary>The ground normal from the height function's slope, the same at every resolution.</summary>
    private Vector3 NormalAt(float x, float z)
    {
        const float e = 0.5f;
        var dx = (float)(_terrain.Height(x + e, z) - _terrain.Height(x - e, z)) / (2 * e);
        var dz = (float)(_terrain.Height(x, z + e) - _terrain.Height(x, z - e)) / (2 * e);
        return new Vector3(-dx, 1f, -dz).Normalized();
    }

    /// <summary>
    /// The surface map the shader reads: how far outside the nearest paved edge and the
    /// nearest track edge each metre of ground is, over the authored area.
    /// </summary>
    /// <remarks>
    /// A signed distance survives bilinear filtering, so the shader can threshold it and get a
    /// crisp road edge at any zoom from a half-metre map. Stored as half floats in metres: a
    /// byte encoding put the edge on sixteen-centimetre steps and the line visibly jittered.
    /// </remarks>
    public static ImageTexture BakeSurfaceMap(Terrain terrain, int size = 4096)
    {
        var bytes = new byte[size * size * 4];
        var metresPerPixel = 2 * Terrain.MapHalfExtent / size;

        Parallel.For(0, size, j =>
        {
            var z = -Terrain.MapHalfExtent + (j + 0.5) * metresPerPixel;
            for (var i = 0; i < size; i++)
            {
                var x = -Terrain.MapHalfExtent + (i + 0.5) * metresPerPixel;
                var (paved, track) = terrain.EdgeDistances(x, z);
                var o = (j * size + i) * 4;
                Encode(bytes, o, paved);
                Encode(bytes, o + 2, track);
            }
        });

        var image = Image.CreateFromData(size, size, false, Image.Format.Rgh, bytes);
        return ImageTexture.CreateFromImage(image);
    }

    private static void Encode(byte[] bytes, int at, double metres)
    {
        var bits = System.BitConverter.HalfToInt16Bits((System.Half)metres);
        bytes[at] = (byte)(bits & 0xFF);
        bytes[at + 1] = (byte)((bits >> 8) & 0xFF);
    }
}
