using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;

namespace Hexcom.Content;

/// <summary>
/// The missions shipped inside this assembly, by name.
/// <c>content/missions/waystation.hexmission</c> is <c>"waystation"</c>.
/// </summary>
/// <remarks>
/// Embedded for the reason <see cref="MapLibrary"/> is: the game, the tests and a tool all run
/// from different working directories, and a mission that can only be found from one of them is
/// a mission the harness cannot fight. A mission and the map it names happen to share a name
/// here; nothing requires that, and the second mission on the same ground is when it stops being
/// true.
/// </remarks>
public static class MissionLibrary
{
    private const string Prefix = "missions/";

    private static readonly Assembly Assembly = typeof(MissionLibrary).Assembly;

    /// <summary>Names of every mission shipped in the assembly, sorted.</summary>
    public static IReadOnlyList<string> Names { get; } = Assembly
        .GetManifestResourceNames()
        .Where(n => n.StartsWith(Prefix, StringComparison.Ordinal) && n.EndsWith(MissionFile.Extension, StringComparison.Ordinal))
        .Select(n => n[Prefix.Length..^MissionFile.Extension.Length])
        .OrderBy(n => n, StringComparer.Ordinal)
        .ToList();

    /// <summary>The text of a shipped mission, exactly as checked in.</summary>
    public static string Source(string name)
    {
        using var stream = Assembly.GetManifestResourceStream(Prefix + name + MissionFile.Extension)
            ?? throw new FileNotFoundException($"No mission called '{name}' is shipped. Known: {string.Join(", ", Names)}.");
        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }

    /// <summary>Read a shipped mission.</summary>
    public static Mission Load(string name) => MissionFile.Parse(Source(name), name + MissionFile.Extension);
}
