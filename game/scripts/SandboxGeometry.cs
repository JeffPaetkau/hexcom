using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;

namespace Hexcom.Game;

/// <summary>
/// Where things are on the canvas: the shapes a tile, a region and a node occupy in pixels.
/// </summary>
/// <remarks>
/// Everything here is canvas-side by construction — it only ever reads
/// <see cref="SandboxScale.Canvas"/>, never <see cref="SandboxScale.World"/>. That is the
/// distinction entry 002 in <c>docs/decisions.md</c> is about, and keeping the pixel geometry in
/// one small type is what stops it blurring again.
/// </remarks>
public sealed class SandboxGeometry(SandboxScale scale)
{
    private readonly SandboxScale _scale = scale;

    /// <summary>Canvas position of a region's centre — where a soldier standing in it is drawn.</summary>
    public CoreVec2 Centroid(TileAddress address, HexRegion region)
        => _scale.Canvas.Center(address.Hex) + region.LocalCentroid * _scale.Canvas.Size;

    /// <summary>Canvas position of a graph node's centre.</summary>
    public CoreVec2 NodeCentre(BattleMap map, NodeId id)
    {
        var regions = map.RegionsOf(id.Tile);
        var region = regions.FirstOrDefault(r => r.Index == id.Region) ?? regions[0];
        return Centroid(id.Tile, region);
    }

    /// <summary>
    /// A region as a screen-space polygon, optionally pulled in towards its own centroid so
    /// neighbouring regions read as separate shapes rather than one field of colour.
    /// </summary>
    public Vector2[] RegionPolygon(TileAddress address, HexRegion region, float inset)
    {
        var center = _scale.Canvas.Center(address.Hex);
        var centroid = Centroid(address, region);

        return region.CornerIndices
            .Select(i =>
            {
                var corner = center + HexPartition.UnitCorner(i) * _scale.Canvas.Size;
                return SandboxScale.ToScreen(corner + (centroid - corner) * inset);
            })
            .ToArray();
    }

    /// <summary>Standard even-odd crossing test, for picking the region under the cursor.</summary>
    public static bool ContainsPoint(IReadOnlyList<Vector2> polygon, Vector2 point)
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
