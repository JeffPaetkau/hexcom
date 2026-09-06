using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;

namespace Hexcom.Game;

/// <summary>
/// A flat debug view of the rules: click to place a unit, see exactly how far its action
/// points carry it, hover anywhere to read the route.
/// </summary>
/// <remarks>
/// Everything interesting here is a query against <c>Hexcom.Core</c>. This file draws and
/// reads input and does nothing else — no rule may be implemented in it, or the rules stop
/// being testable headless.
/// </remarks>
public partial class HexSandbox : Node2D
{
    [Export] public float HexSize { get; set; } = 46f;
    [Export] public int ActionPoints { get; set; } = 10;

    private static readonly Color Background = new("14171c");
    private static readonly Color FloorFill = new("2b3038");
    private static readonly Color RoughFill = new("3b332a");
    private static readonly Color TransitFill = new("3a2630");
    private static readonly Color ReachFill = new("1f4438");
    private static readonly Color RegionEdge = new("434a55");
    private static readonly Color PathColor = new("6fd3b0");
    private static readonly Color UnitColor = new("e8e4d8");
    private static readonly Color TextDim = new("8d96a5");
    private static readonly Color TextBright = new("dfe5ee");

    private readonly MovementCosts _costs = MovementCosts.Default;

    private BattleMap _map = null!;
    private HexLayout _layout = null!;
    private MovementGraph _graph = null!;
    private ReachabilityResult _reach = null!;
    private Font _font = null!;

    private NodeId _unit;
    private NodeId? _hover;
    private int _layer;

    public override void _Ready()
    {
        _font = ThemeDB.FallbackFont;
        _layout = new HexLayout(HexSize);
        _map = DemoMaps.Compound();
        _graph = MovementGraph.Build(_map, _costs);

        _unit = new NodeId(new Hex(-2, 0), 0);
        Position = GetViewportRect().Size * 0.5f;
        RecalculateReach();
    }

    private void RecalculateReach()
    {
        _reach = Pathfinder.Reachable(_graph, _unit, ActionPoints);
        QueueRedraw();
    }

    // ---- input -----------------------------------------------------------------

    public override void _UnhandledInput(InputEvent @event)
    {
        switch (@event)
        {
            case InputEventMouseMotion:
            {
                var node = NodeUnderMouse();
                if (node != _hover) { _hover = node; QueueRedraw(); }
                break;
            }

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }:
            {
                // Only somewhere the unit could actually stand.
                if (NodeUnderMouse() is { } node && _graph.CanEndTurn(node))
                {
                    _unit = node;
                    RecalculateReach();
                }
                break;
            }

            case InputEventKey { Pressed: true, Echo: false } key:
                HandleKey(key.Keycode);
                break;
        }
    }

    private void HandleKey(Key key)
    {
        switch (key)
        {
            case Key.Pageup or Key.E:
                _layer++;
                QueueRedraw();
                break;

            case Key.Pagedown or Key.Q:
                _layer--;
                QueueRedraw();
                break;

            case Key.Bracketleft:
                ActionPoints = Mathf.Max(1, ActionPoints - 1);
                RecalculateReach();
                break;

            case Key.Bracketright:
                ActionPoints++;
                RecalculateReach();
                break;

            case Key.R:
                _layer = 0;
                ActionPoints = _costs.ActionPointsPerTurn;
                _unit = new NodeId(new Hex(-2, 0), 0);
                RecalculateReach();
                break;
        }
    }

    /// <summary>
    /// Which region of which tile the cursor is over. Uses the actual region polygons, so a
    /// tile split by a barricade picks whichever side the cursor is really on.
    /// </summary>
    private NodeId? NodeUnderMouse()
    {
        var point = ToCore(GetLocalMousePosition());
        var address = new TileAddress(_layout.HexAt(point), _layer);
        if (!_map.HasTile(address)) return null;

        var regions = _map.RegionsOf(address);
        foreach (var region in regions)
            if (ContainsPoint(RegionPolygon(address, region, inset: 0f), ToScreen(point)))
                return new NodeId(address, region.Index);

        return new NodeId(address, regions[0].Index);
    }

    // ---- drawing ---------------------------------------------------------------

    public override void _Draw()
    {
        var view = GetViewportRect().Size;
        DrawRect(new Rect2(-Position, view), Background);

        DrawTiles();
        DrawWalls();
        DrawAuthoredLinks();
        DrawPath();
        DrawUnit();
        DrawHud();
    }

    private void DrawTiles()
    {
        foreach (var tile in _map.Tiles.Where(t => t.Address.Layer == _layer))
        foreach (var region in _map.RegionsOf(tile.Address))
        {
            var id = new NodeId(tile.Address, region.Index);
            var polygon = RegionPolygon(tile.Address, region, inset: 0.06f);

            DrawColoredPolygon(polygon, FillFor(tile, region, id));
            DrawPolyline([.. polygon, polygon[0]], RegionEdge, 1f, true);

            if (_reach.CostTo(id) is { } cost && id != _unit)
                DrawCentredText(Centroid(tile.Address, region), cost.ToString(), 15, TextDim);
        }
    }

    private Color FillFor(Tile tile, HexRegion region, NodeId id)
    {
        if (_reach.CanReach(id) && _graph.CanEndTurn(id)) return ReachFill;
        if (!region.Occupiable) return TransitFill;      // crossable, but nowhere to stand
        if (tile.Ground.ExtraApCost > 0) return RoughFill;
        return FloorFill;
    }

    private void DrawWalls()
    {
        foreach (var wall in _map.Walls.Where(w => w.Layer == _layer))
        {
            var (color, width) = StyleFor(wall.Profile);
            DrawLine(ToScreen(_layout.Position(wall.A)), ToScreen(_layout.Position(wall.B)), color, width, true);
        }
    }

    private static (Color Color, float Width) StyleFor(WallProfile profile) => profile.Id switch
    {
        "low" => (new Color("d8b25a"), 6f),      // waist high: half cover, vault it
        "high" => (new Color("d1743c"), 8f),     // head high: full cover, climb it
        "solid" => (new Color("e6e9ee"), 10f),   // building: nothing gets through
        "railing" => (new Color("6fa8c8"), 3f),  // light cover only
        "screen" => (new Color("74b06a"), 5f),   // blocks sight, not movement
        _ => (new Color("aaaaaa"), 4f),
    };

    private void DrawAuthoredLinks()
    {
        foreach (var link in _map.Links.Where(l => l.From.Layer == _layer || l.To.Layer == _layer))
        {
            var address = link.From.Layer == _layer ? link.From : link.To;
            var center = ToScreen(_layout.Center(address.Hex));
            var glyph = link.Kind == TraversalKind.Ladder ? "LADDER" : link.Kind.ToString().ToUpperInvariant();

            DrawCircle(center, HexSize * 0.30f, new Color("c8a24a", 0.28f));
            DrawCentredText(_layout.Center(address.Hex), glyph, 11, new Color("f0d190"));
        }
    }

    private void DrawPath()
    {
        if (_hover is not { } goal || !_reach.TryGetPath(goal, out var path) || path.Count == 0) return;

        var points = new List<Vector2> { ToScreen(NodeCentre(_unit)) };
        points.AddRange(path.Select(link => ToScreen(NodeCentre(link.To))));

        // Only the on-layer part of the route is drawable in a flat view.
        DrawPolyline([.. points], PathColor, 3f, true);

        foreach (var link in path.Where(l => l.Kind != TraversalKind.Walk))
            DrawCentredText(
                NodeCentre(link.To) + new CoreVec2(0, -HexSize * 0.30),
                link.Kind.ToString().ToUpperInvariant(),
                11,
                PathColor);
    }

    private void DrawUnit()
    {
        if (_unit.Layer != _layer) return;
        var center = ToScreen(NodeCentre(_unit));
        DrawCircle(center, HexSize * 0.26f, UnitColor);
        DrawCircle(center, HexSize * 0.26f, new Color("000000", 0.6f), false, 2f);
    }

    private void DrawHud()
    {
        var reachable = _reach.Destinations.Count();
        var lines = new[]
        {
            $"layer {_layer}    {ActionPoints} AP    {reachable} tiles in reach",
            _hover is { } h
                ? $"cursor {h}    {(_reach.CostTo(h) is { } c ? $"{c} AP" : "out of reach")}"
                : "cursor —",
            "click: move unit    Q/E: change layer    [ ]: change AP    R: reset",
        };

        var top = -Position + new Vector2(18, 30);
        for (var i = 0; i < lines.Length; i++)
            DrawString(_font, top + new Vector2(0, i * 20), lines[i],
                HorizontalAlignment.Left, -1, 14, i == 2 ? TextDim : TextBright);
    }

    // ---- geometry helpers ------------------------------------------------------

    private static Vector2 ToScreen(CoreVec2 v) => new((float)v.X, (float)-v.Y);

    private static CoreVec2 ToCore(Vector2 v) => new(v.X, -v.Y);

    private CoreVec2 Centroid(TileAddress address, HexRegion region)
        => _layout.Center(address.Hex) + region.LocalCentroid * _layout.Size;

    private CoreVec2 NodeCentre(NodeId id)
    {
        var regions = _map.RegionsOf(id.Tile);
        var region = regions.FirstOrDefault(r => r.Index == id.Region) ?? regions[0];
        return Centroid(id.Tile, region);
    }

    private Vector2[] RegionPolygon(TileAddress address, HexRegion region, float inset)
    {
        var center = _layout.Center(address.Hex);
        var centroid = Centroid(address, region);

        return region.CornerIndices
            .Select(i =>
            {
                var corner = center + HexPartition.UnitCorner(i) * _layout.Size;
                return ToScreen(corner + (centroid - corner) * inset);
            })
            .ToArray();
    }

    private void DrawCentredText(CoreVec2 worldPosition, string text, int size, Color color)
    {
        var at = ToScreen(worldPosition) + new Vector2(-HexSize, size * 0.36f);
        DrawString(_font, at, text, HorizontalAlignment.Center, HexSize * 2, size, color);
    }

    private static bool ContainsPoint(IReadOnlyList<Vector2> polygon, Vector2 point)
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
