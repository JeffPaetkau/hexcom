using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Hexes;

namespace Hexcom.Core.Maps;

/// <summary>
/// A connection placed by hand rather than derived from geometry: ladders, stairwells,
/// hatches, ziplines, doors between rooms.
/// </summary>
public sealed record AuthoredLink(
    TileAddress From,
    TileAddress To,
    TraversalKind Kind,
    int FromRegion = 0,
    int ToRegion = 0,
    int? ApCost = null,
    bool Bidirectional = true);

/// <summary>
/// The authored state of one battlefield: tiles, walls and hand-placed connections.
/// </summary>
/// <remarks>
/// This is mutable authoring data. Derived structures — hex regions, and the movement graph —
/// are computed from it and cached, and invalidated whenever the geometry changes.
/// </remarks>
public sealed class BattleMap
{
    private readonly Dictionary<TileAddress, Tile> _tiles = [];
    private readonly Dictionary<(HexVertex A, HexVertex B, int Layer), WallSegment> _walls = [];
    private readonly Dictionary<(Hex Hex, int Layer), List<WallSegment>> _wallsByHex = [];
    private readonly Dictionary<TileAddress, IReadOnlyList<HexRegion>> _regionCache = [];
    private readonly List<AuthoredLink> _links = [];

    /// <summary>Share of a hex a region must hold before a unit can stand in it.</summary>
    public double OccupancyThreshold { get; init; } = HexPartition.DefaultOccupancyThreshold;

    /// <summary>Bumped whenever geometry changes, so derived structures know they are stale.</summary>
    public int Revision { get; private set; }

    public IReadOnlyCollection<Tile> Tiles => _tiles.Values;
    public IReadOnlyCollection<WallSegment> Walls => _walls.Values;
    public IReadOnlyList<AuthoredLink> Links => _links;

    // ---- tiles -----------------------------------------------------------------

    public Tile SetTile(Tile tile)
    {
        _tiles[tile.Address] = tile;
        Invalidate();
        return tile;
    }

    public Tile SetTile(TileAddress address, double floorHeight, GroundType? ground = null)
        => SetTile(new Tile(address, floorHeight, ground ?? GroundType.Floor));

    /// <summary>Fill a hex disc with flat floor at one layer. Handy for tests and greyboxing.</summary>
    public BattleMap FillDisc(Hex center, int radius, int layer = 0, double floorHeight = 0, GroundType? ground = null)
    {
        foreach (var hex in center.WithinRange(radius))
            SetTile(new TileAddress(hex, layer), floorHeight, ground);
        return this;
    }

    public Tile? GetTile(TileAddress address) => _tiles.GetValueOrDefault(address);

    public bool HasTile(TileAddress address) => _tiles.ContainsKey(address);

    // ---- walls -----------------------------------------------------------------

    /// <summary>
    /// Place a wall between two grid corners. The corners must belong to a common hex, which
    /// means the segment is either a hex side or one of that hex's interior chords.
    /// </summary>
    public WallSegment AddWall(HexVertex a, HexVertex b, int layer, WallProfile profile)
    {
        var hosts = a.SharedHexesWith(b).ToList();
        if (hosts.Count == 0)
            throw new ArgumentException($"{a} and {b} are not corners of a common hex, so no wall can join them.");

        var wall = new WallSegment(a, b, layer, profile);
        _walls[(wall.A, wall.B, wall.Layer)] = wall;

        foreach (var hex in hosts)
        {
            var key = (hex, layer);
            if (!_wallsByHex.TryGetValue(key, out var list)) _wallsByHex[key] = list = [];
            list.RemoveAll(w => w.A == wall.A && w.B == wall.B);
            list.Add(wall);
        }

        Invalidate();
        return wall;
    }

    /// <summary>Place a wall along the side of <paramref name="hex"/> facing <paramref name="direction"/>.</summary>
    public WallSegment AddSideWall(Hex hex, HexDirection direction, int layer, WallProfile profile)
    {
        var (a, b) = direction.Corners();
        return AddWall(hex.Corner(a), hex.Corner(b), layer, profile);
    }

    /// <summary>Place a wall across the inside of <paramref name="hex"/>, between two of its corners.</summary>
    public WallSegment AddChord(Hex hex, int cornerA, int cornerB, int layer, WallProfile profile)
        => AddWall(hex.Corner(cornerA), hex.Corner(cornerB), layer, profile);

    public bool RemoveWall(HexVertex a, HexVertex b, int layer)
    {
        var probe = new WallSegment(a, b, layer, WallProfile.Low);
        if (!_walls.Remove((probe.A, probe.B, layer))) return false;

        foreach (var list in _wallsByHex.Values)
            list.RemoveAll(w => w.A == probe.A && w.B == probe.B && w.Layer == layer);

        Invalidate();
        return true;
    }

    public WallSegment? GetWall(HexVertex a, HexVertex b, int layer)
    {
        var probe = new WallSegment(a, b, layer, WallProfile.Low);
        return _walls.TryGetValue((probe.A, probe.B, layer), out var wall) ? wall : null;
    }

    /// <summary>The wall on a hex side, if any. Shared with the neighbour across that side.</summary>
    public WallSegment? GetSideWall(Hex hex, HexDirection direction, int layer)
    {
        var (a, b) = direction.Corners();
        return GetWall(hex.Corner(a), hex.Corner(b), layer);
    }

    /// <summary>Every wall whose two corners both belong to this hex, sides included.</summary>
    public IReadOnlyList<WallSegment> WallsIn(Hex hex, int layer)
        => _wallsByHex.TryGetValue((hex, layer), out var list) ? list : [];

    // ---- authored links --------------------------------------------------------

    public AuthoredLink AddLink(AuthoredLink link)
    {
        _links.Add(link);
        Invalidate();
        return link;
    }

    /// <summary>A ladder joining two tiles, usually one directly above the other.</summary>
    public AuthoredLink AddLadder(TileAddress bottom, TileAddress top)
        => AddLink(new AuthoredLink(bottom, top, TraversalKind.Ladder));

    public AuthoredLink AddStairs(TileAddress from, TileAddress to)
        => AddLink(new AuthoredLink(from, to, TraversalKind.Stairs));

    // ---- derived ---------------------------------------------------------------

    /// <summary>
    /// The regions of a tile, after its interior walls have cut it up. Tiles with no interior
    /// walls have exactly one region covering the whole hex.
    /// </summary>
    public IReadOnlyList<HexRegion> RegionsOf(TileAddress address)
    {
        if (_regionCache.TryGetValue(address, out var cached)) return cached;

        var chords = new List<(int, int)>();
        foreach (var wall in WallsIn(address.Hex, address.Layer))
        {
            var ia = address.Hex.CornerIndexOf(wall.A);
            var ib = address.Hex.CornerIndexOf(wall.B);
            if (ia < 0 || ib < 0) continue;
            if (WallSegment.Classify(ia, ib) == ChordClass.Side) continue;
            chords.Add((ia, ib));
        }

        var regions = HexPartition.Compute(chords, OccupancyThreshold);
        _regionCache[address] = regions;
        return regions;
    }

    /// <summary>The region of a tile that borders a given side, if that side is reachable at all.</summary>
    public HexRegion? RegionOnSide(TileAddress address, HexDirection direction)
    {
        foreach (var region in RegionsOf(address))
            if (region.BoundsSide(direction)) return region;
        return null;
    }

    private void Invalidate()
    {
        _regionCache.Clear();
        Revision++;
    }
}
