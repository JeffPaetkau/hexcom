using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;

namespace Hexcom.Core.Movement;

/// <summary>A place a unit can be: a tile, plus which region of it when walls divide the hex.</summary>
public readonly record struct NodeId(TileAddress Tile, int Region)
{
    public NodeId(Hex hex, int layer, int region = 0) : this(new TileAddress(hex, layer), region) { }

    public Hex Hex => Tile.Hex;
    public int Layer => Tile.Layer;

    public override string ToString() => Region == 0 ? Tile.ToString() : $"{Tile}#{Region}";
}

/// <param name="CanEndTurn">
/// Whether a unit may stop here. False for offcuts and the halves of a bisected hex: you can
/// vault across such a tile, but there is nowhere in it to stand.
/// </param>
public sealed record MovementNode(NodeId Id, bool CanEndTurn, double FloorHeight, double AreaFraction);

/// <param name="HeightDelta">Metres gained (positive) or lost (negative) making this move.</param>
public sealed record TraversalLink(NodeId From, NodeId To, TraversalKind Kind, int ApCost, double HeightDelta);

/// <summary>
/// The movement graph derived from a <see cref="BattleMap"/>: every place a unit can stand or
/// pass through, and every priced way of getting between them.
/// </summary>
public sealed class MovementGraph
{
    private readonly Dictionary<NodeId, MovementNode> _nodes;
    private readonly Dictionary<NodeId, List<TraversalLink>> _outgoing;
    private readonly Dictionary<NodeId, List<TraversalLink>> _incoming;

    private MovementGraph(
        Dictionary<NodeId, MovementNode> nodes,
        Dictionary<NodeId, List<TraversalLink>> outgoing,
        MovementCosts costs,
        int mapRevision)
    {
        _nodes = nodes;
        _outgoing = outgoing;
        Costs = costs;
        MapRevision = mapRevision;

        _incoming = [];
        foreach (var link in outgoing.Values.SelectMany(l => l))
        {
            if (!_incoming.TryGetValue(link.To, out var list)) _incoming[link.To] = list = [];
            list.Add(link);
        }
    }

    public MovementCosts Costs { get; }

    /// <summary>The <see cref="BattleMap.Revision"/> this graph was built from.</summary>
    public int MapRevision { get; }

    public IReadOnlyCollection<MovementNode> Nodes => _nodes.Values;

    public IEnumerable<TraversalLink> AllLinks => _outgoing.Values.SelectMany(l => l);

    public MovementNode? GetNode(NodeId id) => _nodes.GetValueOrDefault(id);

    public bool Contains(NodeId id) => _nodes.ContainsKey(id);

    public bool CanEndTurn(NodeId id) => _nodes.TryGetValue(id, out var n) && n.CanEndTurn;

    public IReadOnlyList<TraversalLink> LinksFrom(NodeId id)
        => _outgoing.TryGetValue(id, out var links) ? links : [];

    /// <summary>
    /// Every link that <em>arrives</em> at a node.
    /// </summary>
    /// <remarks>
    /// The graph is directed and not always symmetric — a drop you can take is not a climb you
    /// can make — so walking it backwards needs the reverse adjacency rather than the forward
    /// one read the other way. Built once beside the forward index, because the only thing that
    /// wants it wants the whole of it: asking what it costs to reach a place from everywhere is
    /// one search backwards from that place, and doing it forwards would be one search per
    /// starting point.
    /// </remarks>
    public IReadOnlyList<TraversalLink> LinksTo(NodeId id)
        => _incoming.TryGetValue(id, out var links) ? links : [];

    /// <summary>The largest region of a tile, which is where a unit normally stands.</summary>
    public NodeId PrimaryNode(TileAddress address) => new(address, 0);

    public static MovementGraph Build(BattleMap map, MovementCosts? costs = null)
        => new MovementGraphBuilder(map, costs ?? MovementCosts.Default).Build();

    private sealed class MovementGraphBuilder(BattleMap map, MovementCosts costs)
    {
        private readonly Dictionary<NodeId, MovementNode> _nodes = [];
        private readonly Dictionary<NodeId, List<TraversalLink>> _outgoing = [];

        public MovementGraph Build()
        {
            foreach (var tile in map.Tiles) AddNodes(tile);
            foreach (var tile in map.Tiles) AddIntraTileLinks(tile);
            foreach (var tile in map.Tiles) AddNeighbourLinks(tile);
            AddAuthoredLinks();
            return new MovementGraph(_nodes, _outgoing, costs, map.Revision);
        }

        private void AddNodes(Tile tile)
        {
            if (!tile.Ground.Passable) return;

            foreach (var region in map.RegionsOf(tile.Address))
            {
                var id = new NodeId(tile.Address, region.Index);
                _nodes[id] = new MovementNode(id, region.Occupiable, tile.FloorHeight, region.AreaFraction);
            }
        }

        /// <summary>
        /// Links between regions of the same hex. These exist only where a wall cuts the hex,
        /// and are what lets a unit vault a barricade running across a tile.
        /// </summary>
        private void AddIntraTileLinks(Tile tile)
        {
            var regions = map.RegionsOf(tile.Address);
            if (regions.Count < 2) return;

            foreach (var region in regions)
            foreach (var chord in region.Chords)
            {
                var other = regions.FirstOrDefault(r => r.Index != region.Index && r.Chords.Contains(chord));
                if (other is null) continue;

                var wall = map.GetWall(
                    tile.Address.Hex.Corner(chord.A),
                    tile.Address.Hex.Corner(chord.B),
                    tile.Address.Layer);
                if (wall is null) continue;

                if (!TryKindForWall(wall.Value.Profile, out var kind)) continue;

                AddLink(new TraversalLink(
                    new NodeId(tile.Address, region.Index),
                    new NodeId(tile.Address, other.Index),
                    kind,
                    costs.BaseCost(kind),
                    0));
            }
        }

        /// <summary>
        /// Links across hex sides. Neighbours one layer up or down are considered too, so a
        /// low roof can be stepped onto and a ledge walked off without any authored link.
        /// </summary>
        private void AddNeighbourLinks(Tile tile)
        {
            if (!tile.Ground.Passable) return;

            foreach (var region in map.RegionsOf(tile.Address))
            foreach (var direction in region.Sides)
            {
                var neighbourHex = tile.Address.Hex.Neighbor(direction);

                for (var layerDelta = -1; layerDelta <= 1; layerDelta++)
                {
                    var target = new TileAddress(neighbourHex, tile.Address.Layer + layerDelta);
                    var targetTile = map.GetTile(target);
                    if (targetTile is null || !targetTile.Ground.Passable) continue;

                    var targetRegion = map.RegionOnSide(target, direction.Opposite());
                    if (targetRegion is null) continue;

                    var wall = map.GetSideWall(tile.Address.Hex, direction, tile.Address.Layer)
                               ?? (layerDelta != 0 ? map.GetSideWall(tile.Address.Hex, direction, target.Layer) : null);

                    var delta = targetTile.FloorHeight - tile.FloorHeight;
                    if (!TryKindForCrossing(wall?.Profile, delta, out var kind)) continue;

                    var cost = costs.BaseCost(kind) + targetTile.Ground.ExtraApCost;
                    if (kind == TraversalKind.Walk && targetTile.Ground.ExtraApCost > 0)
                        kind = TraversalKind.Rough; // label only; the surcharge is already in the cost

                    AddLink(new TraversalLink(
                        new NodeId(tile.Address, region.Index),
                        new NodeId(target, targetRegion.Index),
                        kind,
                        cost,
                        delta));
                }
            }
        }

        private void AddAuthoredLinks()
        {
            foreach (var link in map.Links)
            {
                var from = new NodeId(link.From, link.FromRegion);
                var to = new NodeId(link.To, link.ToRegion);
                if (!_nodes.ContainsKey(from) || !_nodes.ContainsKey(to)) continue;

                var cost = link.ApCost ?? costs.BaseCost(link.Kind);
                var delta = _nodes[to].FloorHeight - _nodes[from].FloorHeight;

                AddLink(new TraversalLink(from, to, link.Kind, cost, delta));
                if (link.Bidirectional)
                    AddLink(new TraversalLink(to, from, link.Kind, cost, -delta));
            }
        }

        /// <summary>What it takes to get past a wall standing between two places.</summary>
        private static bool TryKindForWall(WallProfile profile, out TraversalKind kind)
        {
            if (!profile.BlocksMovement) { kind = TraversalKind.Walk; return true; }
            if (profile.Vaultable) { kind = TraversalKind.Vault; return true; }
            if (profile.Climbable) { kind = TraversalKind.Climb; return true; }
            kind = default;
            return false;
        }

        /// <summary>What the change in floor height alone demands, ignoring any wall.</summary>
        private bool TryKindForHeight(double heightDelta, out TraversalKind kind)
        {
            var rise = Math.Abs(heightDelta);
            if (rise <= costs.StepHeight) { kind = TraversalKind.Walk; return true; }
            if (heightDelta > 0 && heightDelta <= costs.MaxClimb) { kind = TraversalKind.Climb; return true; }
            if (heightDelta < 0 && rise <= costs.MaxSafeDrop) { kind = TraversalKind.Drop; return true; }

            kind = default;
            return false;
        }

        /// <summary>
        /// What it takes to cross a hex side, given both any wall and the drop or rise.
        /// </summary>
        /// <remarks>
        /// Both must be satisfiable, and the harder of the two wins. A wall never makes an
        /// otherwise impossible crossing possible: a parapet three metres above your head is
        /// not something you vault from the ground, whatever its profile says.
        /// </remarks>
        private bool TryKindForCrossing(WallProfile? profile, double heightDelta, out TraversalKind kind)
        {
            if (!TryKindForHeight(heightDelta, out var byHeight)) { kind = default; return false; }
            if (profile is null) { kind = byHeight; return true; }
            if (!TryKindForWall(profile, out var byWall)) { kind = default; return false; }

            kind = costs.BaseCost(byWall) > costs.BaseCost(byHeight) ? byWall : byHeight;
            return true;
        }

        private void AddLink(TraversalLink link)
        {
            if (!_nodes.ContainsKey(link.From) || !_nodes.ContainsKey(link.To)) return;
            if (!_outgoing.TryGetValue(link.From, out var list)) _outgoing[link.From] = list = [];
            list.Add(link);
        }
    }
}
