using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;

namespace Hexcom.Game;

/// <summary>
/// Where things are in the scene: the footprint a tile, a region and a node occupy, at the
/// height the map puts them, and which of them a ray from the camera lands on.
/// </summary>
/// <remarks>
/// <para>
/// Everything here reads <see cref="SandboxScale.World"/> and the map's own floor heights, and
/// nothing else — there is no second layout to confuse it with any more, which is the whole of
/// what the greybox changed about this file. The map is the authority on height: a tile is
/// drawn at <c>Tile.FloorHeight</c> and a wall from <c>BattleMap.WallBaseHeight</c> to
/// <c>WallTopHeight</c>, which are the figures <c>SightSolver</c> traces against, so what is on
/// screen is the geometry the rules judge by and not an illustration of it.
/// </para>
/// <para>
/// Picking is by ray rather than by polygon. The flat view asked which hex the cursor's canvas
/// point fell in; a pitched camera has no canvas point, only a line through the scene, and the
/// hex under the cursor is wherever that line first meets a floor. Floors sit at a handful of
/// distinct heights on any map — the waystation has the ground, a ridge, a roof and a tower —
/// so the ray is intersected with each height's plane and the nearest tile that is actually at
/// that height wins. No physics bodies, no collision layers: a blockout that had to be kept in
/// step with a physics world would be two copies of the map.
/// </para>
/// </remarks>
public static class SandboxGeometry
{
    private static HexLayout Layout => SandboxScale.World;

    /// <summary>The six corners of a hex on the rules' plane, counter-clockwise from due east.</summary>
    public static CoreVec2[] Corners(Hex hex) => Layout.Corners(hex);

    /// <summary>A region's corners on the plane, optionally pulled in towards its own centroid.</summary>
    public static CoreVec2[] RegionOutline(TileAddress address, HexRegion region, double inset = 0)
    {
        var centre = Layout.Center(address.Hex);
        var centroid = Centroid(address, region);

        return region.CornerIndices
            .Select(i =>
            {
                var corner = centre + HexPartition.UnitCorner(i) * Layout.Size;
                return corner + (centroid - corner) * inset;
            })
            .ToArray();
    }

    /// <summary>Plane position of a region's centre — where a soldier standing in it stands.</summary>
    public static CoreVec2 Centroid(TileAddress address, HexRegion region)
        => Layout.Center(address.Hex) + region.LocalCentroid * Layout.Size;

    /// <summary>Plane position of a graph node's centre.</summary>
    public static CoreVec2 NodePlane(BattleMap map, NodeId id)
    {
        var regions = map.RegionsOf(id.Tile);
        var region = regions.FirstOrDefault(r => r.Index == id.Region) ?? regions[0];
        return Centroid(id.Tile, region);
    }

    /// <summary>The floor height of a node, from the map. A node on no tile is at its layer's nominal height.</summary>
    public static double FloorOf(BattleMap map, NodeId id)
        => map.GetTile(id.Tile)?.FloorHeight ?? id.Tile.Layer * map.LayerHeight;

    /// <summary>A node's centre in the scene, on the floor.</summary>
    public static Vector3 NodeScene(BattleMap map, NodeId id)
        => SandboxScale.ToScene(NodePlane(map, id), FloorOf(map, id));

    /// <summary>
    /// The node a ray from the camera lands on, looking only at one storey.
    /// </summary>
    /// <param name="origin">Where the ray starts, in the scene.</param>
    /// <param name="direction">Where it goes. Need not be normalised.</param>
    /// <param name="layer">The storey being looked at; other storeys are transparent to the cursor.</param>
    /// <remarks>
    /// Tiles on the storey are grouped by floor height, the ray is met with each height's plane,
    /// and the nearest hit that lands on a tile actually at that height is the answer. The
    /// region is then the one whose outline contains the hit, so a tile split by a barricade
    /// picks whichever side the cursor is really on — the same even-odd test the flat view used,
    /// on the plane rather than the canvas.
    /// </remarks>
    public static NodeId? Pick(BattleMap map, Vector3 origin, Vector3 direction, int layer)
    {
        if (System.Math.Abs(direction.Y) < 1e-6f) return null;

        NodeId? best = null;
        var nearest = float.MaxValue;

        foreach (var height in map.Tiles.Where(t => t.Address.Layer == layer).Select(t => t.FloorHeight).Distinct())
        {
            var t = ((float)height - origin.Y) / direction.Y;
            if (t <= 0 || t >= nearest) continue;

            var hit = origin + direction * t;
            var plane = SandboxScale.ToPlane(hit);
            var address = new TileAddress(Layout.HexAt(plane), layer);

            var tile = map.GetTile(address);
            if (tile is null || System.Math.Abs(tile.FloorHeight - height) > 1e-6) continue;

            nearest = t;
            best = new NodeId(address, RegionAt(map, address, plane).Index);
        }

        return best;
    }

    private static HexRegion RegionAt(BattleMap map, TileAddress address, CoreVec2 plane)
    {
        var regions = map.RegionsOf(address);
        foreach (var region in regions)
            if (Contains(RegionOutline(address, region), plane)) return region;
        return regions[0];
    }

    /// <summary>Standard even-odd crossing test.</summary>
    public static bool Contains(IReadOnlyList<CoreVec2> polygon, CoreVec2 point)
    {
        var inside = false;
        for (int i = 0, j = polygon.Count - 1; i < polygon.Count; j = i++)
        {
            var a = polygon[i];
            var b = polygon[j];
            if (a.Y > point.Y != b.Y > point.Y &&
                point.X < (b.X - a.X) * (point.Y - a.Y) / (b.Y - a.Y) + a.X)
                inside = !inside;
        }
        return inside;
    }
}
