using System.Collections.Generic;
using System.IO;
using System.Linq;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;

namespace Hexcom.Content;

/// <summary>
/// Reads the <c>.hexmap</c> text format into a <see cref="BattleMap"/>.
/// </summary>
/// <remarks>
/// <para>
/// The format is the corner graph, written down, plus shorthand. Three statements are
/// primitives and between them can express anything a <see cref="BattleMap"/> can hold:
/// <c>tile</c> (one hex at one layer), <c>chord</c> (a wall between two corners of one hex —
/// sides included, since a side is the chord between adjacent corners) and <c>link</c> (an
/// authored connection). Everything else — <c>fill</c>, <c>wall</c>, <c>enclose</c>,
/// <c>breach</c>, <c>ladder</c> — is a loop over those three, and <see cref="MapWriter"/> can
/// lower any map back to primitives alone. So nothing legal is inexpressible, which was the
/// risk of a friendlier format, and nothing is unpleasant to author, which was the cost of an
/// honest one.
/// </para>
/// <para>
/// One statement per line, <c>#</c> to end of line is a comment, and any statement that
/// declares a profile, a ground type or a map setting has to come before the first tile or wall
/// that would use it. Order otherwise matters only where it should: a later <c>fill</c> paints
/// over an earlier one, and a <c>breach</c> removes a wall that must already be there. The
/// grammar is written out in <c>content/README.md</c>.
/// </para>
/// </remarks>
public static class MapFile
{
    public const string Extension = ".hexmap";

    /// <summary>The wall profiles every map can name without declaring them.</summary>
    public static IReadOnlyDictionary<string, WallProfile> BuiltInProfiles { get; } =
        new[] { WallProfile.Low, WallProfile.High, WallProfile.Solid, WallProfile.Railing, WallProfile.Screen }
            .ToDictionary(p => p.Id, StringComparer.Ordinal);

    /// <summary>The ground types every map can name without declaring them.</summary>
    public static IReadOnlyDictionary<string, GroundType> BuiltInGrounds { get; } =
        new[]
        {
            GroundType.Floor, GroundType.Grass, GroundType.Gravel, GroundType.Rubble,
            GroundType.Mud, GroundType.ShallowWater, GroundType.Void,
        }.ToDictionary(g => g.Id, StringComparer.Ordinal);

    /// <summary>Read a map from a file on disk.</summary>
    public static MapDocument Load(string path)
        => Parse(File.ReadAllText(path), Path.GetFileName(path));

    /// <summary>Read a map from its text. <paramref name="source"/> is only for error messages.</summary>
    public static MapDocument Parse(string text, string? source = null)
        => new Reader(text, source).Read();

    /// <summary>Bearing names as they appear in a map file, indexed by <see cref="HexDirection"/>.</summary>
    public static string DirectionName(HexDirection direction) => Bearings.Names[(int)direction];

    private sealed class Reader(string text, string? source) : TextFormatReader(text)
    {
        private readonly Dictionary<string, WallProfile> _profiles = new(BuiltInProfiles, StringComparer.Ordinal);
        private readonly Dictionary<string, GroundType> _grounds = new(BuiltInGrounds, StringComparer.Ordinal);

        /// <summary>The last line that put an interior chord in each hex, so a crossing can be blamed on one.</summary>
        private readonly Dictionary<(Hex, int), int> _chordLines = [];

        private string? _name;
        private double _occupancy = HexPartition.DefaultOccupancyThreshold;
        private double _layerHeight = 3.0;
        private BattleMap? _map;

        private BattleMap Map => _map ??= new BattleMap { OccupancyThreshold = _occupancy, LayerHeight = _layerHeight };

        public MapDocument Read()
        {
            ReadLines();
            CheckPartitions();
            return new MapDocument(_name ?? source, Map, _profiles, _grounds);
        }

        protected override ContentFormatException Error(string message)
            => new MapFormatException(message, source, LineNumber);

        // ---- statements ------------------------------------------------------------

        protected override void Statement(Cursor c)
        {
            var keyword = c.Next("a statement");
            switch (keyword)
            {
                case "map": _name = string.Join(' ', c.Rest()); break;
                case "occupancy": Setting(c, v => _occupancy = v); break;
                case "layer-height": Setting(c, v => _layerHeight = v); break;
                case "profile": Profile(c); break;
                case "ground": Ground(c); break;
                case "tile": TileStatement(c); break;
                case "fill": Fill(c); break;
                case "chord": Chord(c); break;
                case "wall": Wall(c); break;
                case "enclose": Enclose(c); break;
                case "breach": Breach(c); break;
                case "link": Link(c, TraversalKindOf(c)); break;
                case "ladder": Link(c, TraversalKind.Ladder); break;
                case "stairs": Link(c, TraversalKind.Stairs); break;
                case "door": Link(c, TraversalKind.Door); break;
                default: throw Error($"Unknown statement '{keyword}'.");
            }
        }

        private void Setting(Cursor c, Action<double> apply)
        {
            if (_map is not null)
                throw Error("Map settings have to come before the first tile, wall or link.");
            apply(c.Double("a number"));
            c.End();
        }

        /// <summary>A wall profile by name: built-in, or one this file declared earlier.</summary>
        private WallProfile ProfileOf(Cursor c) => c.Named("wall profile", _profiles);

        private static TraversalKind TraversalKindOf(Cursor c)
            => c.Enum<TraversalKind>("a traversal kind: walk, vault, climb, ladder, stairs, drop, jump, door or crawl");

        private void Profile(Cursor c)
        {
            var id = c.Next("a profile name");
            if (_profiles.ContainsKey(id))
                throw Error(BuiltInProfiles.ContainsKey(id)
                    ? $"'{id}' is a built-in profile and cannot be redefined."
                    : $"Profile '{id}' is already declared.");

            double? height = null;
            CoverGrade? cover = null;
            bool blocks = true, opaque = true, vault = false, climb = false, destructible = false;

            while (!c.Done)
            {
                var option = c.Next("an option");
                switch (option)
                {
                    case "height": height = c.Double("a height in metres"); break;
                    case "cover": cover = c.Enum<CoverGrade>("a cover grade: none, light, half or full"); break;
                    case "blocks": blocks = true; break;
                    case "passable": blocks = false; break;
                    case "opaque": opaque = true; break;
                    case "clear": opaque = false; break;
                    case "vault": vault = true; break;
                    case "novault": vault = false; break;
                    case "climb": climb = true; break;
                    case "noclimb": climb = false; break;
                    case "destructible": destructible = true; break;
                    case "permanent": destructible = false; break;
                    default: throw Error($"Unknown profile option '{option}'.");
                }
            }

            if (height is null) throw Error($"Profile '{id}' needs a height.");
            if (cover is null) throw Error($"Profile '{id}' needs a cover grade.");

            _profiles[id] = new WallProfile(id, height.Value, cover.Value, blocks, opaque, vault, climb, destructible);
        }

        private void Ground(Cursor c)
        {
            var id = c.Next("a ground name");
            if (_grounds.ContainsKey(id))
                throw Error(BuiltInGrounds.ContainsKey(id)
                    ? $"'{id}' is a built-in ground and cannot be redefined."
                    : $"Ground '{id}' is already declared.");

            var cost = 0;
            var noise = 1.0;
            var passable = true;

            while (!c.Done)
            {
                var option = c.Next("an option");
                switch (option)
                {
                    case "cost": cost = c.Int("an action point cost"); break;
                    case "noise": noise = c.Double("a noise factor"); break;
                    case "impassable": passable = false; break;
                    default: throw Error($"Unknown ground option '{option}'.");
                }
            }

            _grounds[id] = new GroundType(id, cost, noise, passable);
        }

        private void TileStatement(Cursor c)
        {
            var address = c.Address();
            var (height, ground, layer) = TileOptions(c, allowLayer: false);
            if (layer is not null) throw Error("A tile takes its layer from its address, as q,r@layer.");
            Paint(address, height, ground);
        }

        private void Fill(Cursor c)
        {
            var hexes = c.Shape();
            var (height, ground, layer) = TileOptions(c, allowLayer: true);
            foreach (var hex in hexes)
                Paint(new TileAddress(hex, layer ?? 0), height, ground);
        }

        /// <summary>
        /// Set a tile, keeping whatever the statement did not mention. A second <c>fill</c> over
        /// the same ground with only a ground type therefore repaints without flattening it.
        /// </summary>
        private void Paint(TileAddress address, double? height, GroundType? ground)
        {
            var existing = Map.GetTile(address);
            Map.SetTile(
                address,
                height ?? existing?.FloorHeight ?? address.Layer * _layerHeight,
                ground ?? existing?.Ground ?? GroundType.Floor);
        }

        private (double? Height, GroundType? Ground, int? Layer) TileOptions(Cursor c, bool allowLayer)
        {
            double? height = null;
            GroundType? ground = null;
            int? layer = null;

            while (!c.Done)
            {
                var option = c.Next("an option");
                if (option == "h") height = c.Double("a floor height in metres");
                else if (option == "layer" && allowLayer) layer = c.Int("a layer number");
                else if (_grounds.TryGetValue(option, out var g)) ground = g;
                else throw Error($"'{option}' is not a ground type or a tile option (h, layer).");
            }

            return (height, ground, layer);
        }

        private void Chord(Cursor c)
        {
            var profile = ProfileOf(c);
            var address = c.Address();
            var (a, b) = c.CornerPair();
            c.End();
            AddChord(address, a, b, profile);
        }

        private void AddChord(TileAddress address, int a, int b, WallProfile profile)
        {
            Map.AddChord(address.Hex, a, b, address.Layer, profile);
            if (WallSegment.Classify(a, b) != ChordClass.Side)
                _chordLines[(address.Hex, address.Layer)] = LineNumber;
        }

        private void Wall(Cursor c)
        {
            var profile = ProfileOf(c);
            var hexes = c.Shape();
            var (directions, layer) = Directions(c);
            if (directions.Count == 0) throw Error("A wall needs at least one side: ne, n, nw, sw, s, se or all.");

            foreach (var hex in hexes)
            foreach (var direction in directions)
                Map.AddSideWall(hex, direction, layer, profile);
        }

        /// <summary>Walls along every side of a shape that faces out of it: a building in one line.</summary>
        private void Enclose(Cursor c)
        {
            var profile = ProfileOf(c);
            var hexes = c.Shape();
            var (directions, layer) = Directions(c);
            if (directions.Count != 0) throw Error("'enclose' works out its own sides; it takes only an optional layer.");

            var inside = hexes.ToHashSet();
            foreach (var hex in hexes)
            foreach (var direction in HexDirectionExtensions.All)
                if (!inside.Contains(hex.Neighbor(direction)))
                    Map.AddSideWall(hex, direction, layer, profile);
        }

        private void Breach(Cursor c)
        {
            var address = c.Address();
            var removed = 0;

            while (!c.Done)
            {
                var token = c.Next("a side or a corner pair");
                HexVertex a, b;
                if (Bearings.TryParse(token, out var direction))
                {
                    var (ia, ib) = direction.Corners();
                    (a, b) = (address.Hex.Corner(ia), address.Hex.Corner(ib));
                }
                else if (Cursor.TryCornerPair(token, out var ia2, out var ib2))
                {
                    (a, b) = (address.Hex.Corner(ia2), address.Hex.Corner(ib2));
                }
                else
                {
                    throw Error($"'{token}' is not a side (ne, n, nw, sw, s, se) or a corner pair (0-3).");
                }

                if (!Map.RemoveWall(a, b, address.Layer))
                    throw Error($"There is no wall on {token} of {address} to breach.");
                removed++;
            }

            if (removed == 0) throw Error("A breach needs at least one side to remove.");
        }

        private void Link(Cursor c, TraversalKind kind)
        {
            var from = c.Address();
            var to = c.Address();
            int? cost = null;
            var bidirectional = true;
            int fromRegion = 0, toRegion = 0;

            while (!c.Done)
            {
                var option = c.Next("an option");
                switch (option)
                {
                    case "cost": cost = c.Int("an action point cost"); break;
                    case "one-way": bidirectional = false; break;
                    case "regions":
                        fromRegion = c.Int("the region index at the near end");
                        toRegion = c.Int("the region index at the far end");
                        break;
                    default: throw Error($"Unknown link option '{option}'.");
                }
            }

            Map.AddLink(new AuthoredLink(from, to, kind, fromRegion, toRegion, cost, bidirectional));
        }

        private (List<HexDirection> Directions, int Layer) Directions(Cursor c)
        {
            var directions = new List<HexDirection>();
            var layer = 0;

            while (!c.Done)
            {
                var token = c.Next("a side or 'layer'");
                if (token == "layer") layer = c.Int("a layer number");
                else if (token == "all") directions.AddRange(HexDirectionExtensions.All);
                else if (Bearings.TryParse(token, out var direction)) directions.Add(direction);
                else throw Error($"'{token}' is not a side (ne, n, nw, sw, s, se, all) or 'layer'.");
            }

            return (directions.Distinct().ToList(), layer);
        }

        /// <summary>
        /// Regions are computed lazily, so two chords crossing inside one hex would otherwise
        /// surface as an exception from the movement graph long after the file was read.
        /// </summary>
        private void CheckPartitions()
        {
            if (_map is null) return;
            foreach (var tile in _map.Tiles)
            {
                try
                {
                    _map.RegionsOf(tile.Address);
                }
                catch (HexPartitionException e)
                {
                    LineNumber = _chordLines.GetValueOrDefault((tile.Address.Hex, tile.Address.Layer));
                    throw Error($"{tile.Address}: {e.Message}");
                }
            }
        }
    }
}
