using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Hexcom.Core.Maps;

namespace Hexcom.Content;

/// <summary>
/// The maps shipped inside this assembly, by name. <c>content/maps/compound.hexmap</c> is
/// <c>"compound"</c>.
/// </summary>
/// <remarks>
/// A file on disk needs a working directory to be found from, and the game, the tests and a
/// tool all run from different ones. Embedding the maps means <c>MapLibrary.Load("compound")</c>
/// works from any of them, and it is still the same text that is checked in — edit the file,
/// rebuild, and the change is in every caller.
/// </remarks>
public static class MapLibrary
{
    private const string Prefix = "maps/";

    private static readonly Assembly Assembly = typeof(MapLibrary).Assembly;

    /// <summary>Names of every map shipped in the assembly, sorted.</summary>
    public static IReadOnlyList<string> Names { get; } = Assembly
        .GetManifestResourceNames()
        .Where(n => n.StartsWith(Prefix, StringComparison.Ordinal) && n.EndsWith(MapFile.Extension, StringComparison.Ordinal))
        .Select(n => n[Prefix.Length..^MapFile.Extension.Length])
        .OrderBy(n => n, StringComparer.Ordinal)
        .ToList();

    /// <summary>The text of a shipped map, exactly as checked in.</summary>
    public static string Source(string name)
    {
        using var stream = Assembly.GetManifestResourceStream(Prefix + name + MapFile.Extension)
            ?? throw new FileNotFoundException($"No map called '{name}' is shipped. Known: {string.Join(", ", Names)}.");
        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }

    /// <summary>Read a shipped map.</summary>
    public static MapDocument Read(string name) => MapFile.Parse(Source(name), name + MapFile.Extension);

    /// <summary>Read a shipped map and hand back just the battlefield.</summary>
    public static BattleMap Load(string name) => Read(name).Map;
}
