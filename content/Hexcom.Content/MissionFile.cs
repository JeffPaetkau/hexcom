using System.Collections.Generic;
using System.IO;
using System.Linq;
using Hexcom.Core.Awareness;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Units;

namespace Hexcom.Content;

/// <summary>
/// Reads the <c>.hexmission</c> text format into a <see cref="Mission"/>.
/// </summary>
/// <remarks>
/// <para>
/// A mission file names a map and adds the four things entry 030 says a map deliberately cannot
/// hold — somewhere to start with a facing, somewhere to end that is a named place, something to
/// do, and when it stops — plus the squads. Six statements do it: <c>mission</c> and <c>map</c>
/// say what this is and where; <c>brief</c> is the six-part briefing; <c>place</c> names ground;
/// <c>deploy</c> puts a soldier on it; <c>objective</c> gives a side something to do; and
/// <c>rounds</c> is the clock.
/// </para>
/// <para>
/// The same primitives-plus-shorthand discipline as the map format, and here there is very
/// little to lower: <c>place</c> takes the map format's shapes and <see cref="MissionWriter"/>
/// writes them back out as an explicit list of tiles. Everything else is already a primitive.
/// That the shorthand is nearly empty is the point — a mission is a dozen facts, not a
/// battlefield, and a format that made it feel like one would be the wrong format.
/// </para>
/// <para>
/// Order matters exactly where it should. A <c>place</c> has to be declared before the
/// <c>objective</c> that names it, the same rule a <c>profile</c> has in a map; nothing else
/// cares. The grammar is written out in <c>content/README.md</c>.
/// </para>
/// </remarks>
public static class MissionFile
{
    public const string Extension = ".hexmission";

    /// <summary>
    /// The <see cref="UnitStats"/> presets a mission may name. Omitting the role is the default
    /// soldier.
    /// </summary>
    /// <remarks>
    /// Named, never declared. A file that could write out its own action points and perception
    /// would be a balance change hiding in content, which is the line
    /// <c>docs/subprojects/content.md</c> draws and the same one that lets a map declare a hedge
    /// but not redefine what <c>low</c> means. Whether that line is in the right place is an open
    /// question in that doc, and it is not answered here.
    /// </remarks>
    public static IReadOnlyDictionary<string, UnitStats> Roles { get; } =
        new Dictionary<string, UnitStats>(StringComparer.Ordinal)
        {
            ["scout"] = UnitStats.Scout,
            ["trooper"] = UnitStats.Trooper,
            ["signaller"] = UnitStats.Signaller,
        };

    /// <summary>The <see cref="Loadout"/>s a mission may name. Omitting the kit is the default.</summary>
    public static IReadOnlyDictionary<string, Loadout> Kits { get; } =
        new Dictionary<string, Loadout>(StringComparer.Ordinal)
        {
            ["rifleman"] = Loadout.Rifleman,
            ["beamer"] = Loadout.Beamer,
            ["heavy"] = Loadout.Heavy,
            ["infiltrator"] = Loadout.Infiltrator,
            ["sidearm"] = Loadout.Sidearm,
        };

    /// <summary>The briefing parts as a file names them.</summary>
    public static IReadOnlyDictionary<string, BriefingPart> Parts { get; } =
        new Dictionary<string, BriefingPart>(StringComparer.Ordinal)
        {
            ["instrument"] = BriefingPart.Instrument,
            ["presence"] = BriefingPart.Presence,
            ["task"] = BriefingPart.Task,
            ["restraint"] = BriefingPart.Restraint,
            ["way-off"] = BriefingPart.WayOff,
            ["stop"] = BriefingPart.Stop,
        };

    /// <summary>A briefing part's name in a file, indexed by <see cref="BriefingPart"/>.</summary>
    public static string PartName(BriefingPart part) => Parts.First(p => p.Value == part).Key;

    /// <summary>Read a mission from a file on disk.</summary>
    public static Mission Load(string path)
        => Parse(File.ReadAllText(path), Path.GetFileName(path));

    /// <summary>Read a mission from its text. <paramref name="source"/> is only for error messages.</summary>
    public static Mission Parse(string text, string? source = null)
        => new Reader(text, source).Read();

    private sealed class Reader(string text, string? source) : TextFormatReader(text)
    {
        private readonly Dictionary<BriefingPart, List<string>> _brief = [];
        private readonly List<Deployment> _deployments = [];
        private readonly Dictionary<string, IReadOnlyList<TileAddress>> _places = new(StringComparer.Ordinal);
        private readonly List<ObjectiveOrder> _objectives = [];

        private string? _name;
        private string? _map;
        private int? _rounds;

        public Mission Read()
        {
            ReadLines();

            LineNumber = 0;
            if (_map is null) throw Error("A mission has to say which map it is fought on: 'map <name>'.");
            if (_deployments.Count == 0) throw Error("A mission with nobody on the ground is not a mission.");

            return new Mission(
                _name ?? source,
                _map,
                BuildBriefing(),
                _deployments,
                _places,
                _objectives,
                _rounds);
        }

        protected override ContentFormatException Error(string message)
            => new MissionFormatException(message, source, LineNumber);

        protected override void Statement(Cursor c)
        {
            var keyword = c.Next("a statement");
            switch (keyword)
            {
                case "mission": _name = string.Join(' ', c.Rest()); break;
                case "map": _map = c.Next("a map name"); c.End(); break;
                case "rounds": _rounds = Rounds(c); break;
                case "brief": Brief(c); break;
                case "place": Place(c); break;
                case "deploy": Deploy(c); break;
                case "objective": ObjectiveStatement(c); break;
                default: throw Error($"Unknown statement '{keyword}'.");
            }
        }

        private int Rounds(Cursor c)
        {
            var rounds = c.Int("a number of rounds");
            c.End();
            if (rounds <= 0) throw Error("A round limit has to be at least one round.");
            return rounds;
        }

        /// <summary>
        /// One line of the briefing. Repeating a part adds a line to it, which is how prose that
        /// does not fit in eighty columns is written down without a continuation character.
        /// </summary>
        private void Brief(Cursor c)
        {
            var part = c.Named("briefing part", Parts);
            var words = c.Rest();
            if (words.Length == 0) throw Error($"The '{PartName(part)}' line says nothing.");
            if (!_brief.TryGetValue(part, out var lines)) _brief[part] = lines = [];
            lines.Add(string.Join(' ', words));
        }

        private Briefing BuildBriefing()
        {
            var missing = Briefing.Order.Where(p => !_brief.ContainsKey(p)).ToList();
            if (missing.Count > 0)
                throw Error(
                    $"The briefing has no {string.Join(" or ", missing.Select(p => $"'{PartName(p)}'"))} line. " +
                    "Every briefing has all six parts.");

            string Text(BriefingPart part) => string.Join(' ', _brief[part]);

            return new Briefing(
                Text(BriefingPart.Instrument),
                Text(BriefingPart.Presence),
                Text(BriefingPart.Task),
                Text(BriefingPart.Restraint),
                Text(BriefingPart.WayOff),
                Text(BriefingPart.Stop));
        }

        /// <summary>A named piece of ground, as any shape the map format knows.</summary>
        private void Place(Cursor c)
        {
            var name = c.Next("a place name");
            if (Cursor.TryCoordinate(name, out _, out _))
                throw Error($"'{name}' is a coordinate, not a name. A place is named so a briefing can say it.");
            if (_places.ContainsKey(name)) throw Error($"There is already a place called '{name}'.");

            var hexes = c.Shape();
            var layer = 0;
            while (!c.Done)
            {
                var option = c.Next("'layer'");
                if (option != "layer") throw Error($"Unknown place option '{option}'. A place takes only 'layer N'.");
                layer = c.Int("a layer number");
            }

            _places[name] = hexes.Select(h => new TileAddress(h, layer)).ToList();
        }

        private void Deploy(Cursor c)
        {
            var name = c.Next("a soldier's name");
            if (_deployments.Any(d => d.Name == name))
                throw Error($"{name} has already been deployed.");

            var side = c.Enum<Side>("a side: player, hostile or neutral");
            var where = c.Address();

            var facing = HexDirection.NorthEast;
            string? role = null, kit = null;

            while (!c.Done)
            {
                var option = c.Next("an option");
                switch (option)
                {
                    case "facing": facing = c.Direction("a bearing"); break;
                    case "role": role = Known(c, Roles, "role"); break;
                    case "kit": kit = Known(c, Kits, "kit"); break;
                    default: throw Error($"Unknown deployment option '{option}'. Known: facing, role, kit.");
                }
            }

            _deployments.Add(new Deployment(name, side, where, facing, role, kit, LineNumber));
        }

        /// <summary>The name itself, having checked it is one the rules know.</summary>
        private string Known<T>(Cursor c, IReadOnlyDictionary<string, T> known, string what)
        {
            var token = c.Next(what);
            if (!known.ContainsKey(token))
                throw Error($"Unknown {what} '{token}'. Known: {string.Join(", ", known.Keys.Order(StringComparer.Ordinal))}.");
            return token;
        }

        private void ObjectiveStatement(Cursor c)
        {
            var kind = c.Enum<ObjectiveKind>(
                "a mission shape: withdrawal, reconnaissance, sabotage, extraction, denial or capture");
            var side = c.Enum<Side>("a side: player, hostile or neutral");

            if (_objectives.Any(o => o.Side == side))
                throw Error($"The {side} side already has an objective; a battle holds one per side.");

            if (kind != ObjectiveKind.Withdrawal)
                throw Error(
                    $"'{kind.ToString().ToLowerInvariant()}' is one of the six mission shapes, but the rules only " +
                    "have withdrawal so far. See docs/decisions.md entry 041.");

            _objectives.Add(Withdrawal(c, side));
        }

        private WithdrawalOrder Withdrawal(Cursor c, Side side)
        {
            string? place = null;
            var unnoticed = AwarenessState.Suspicious;

            while (!c.Done)
            {
                var option = c.Next("an option");
                switch (option)
                {
                    case "exit":
                        place = c.Next("a place name");
                        if (!_places.ContainsKey(place))
                            throw Error($"No place called '{place}' has been declared yet. A place comes before the objective that names it.");
                        break;
                    case "unnoticed":
                        unnoticed = c.Enum<AwarenessState>("an awareness rung: unaware, suspicious, searching, alerted or engaged");
                        break;
                    default:
                        throw Error($"Unknown withdrawal option '{option}'. Known: exit, unnoticed.");
                }
            }

            if (place is null) throw Error("A withdrawal needs somewhere to leave from: 'exit <place>'.");
            return new WithdrawalOrder(side, place, unnoticed, LineNumber);
        }
    }
}
