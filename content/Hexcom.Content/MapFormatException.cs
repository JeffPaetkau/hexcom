namespace Hexcom.Content;

/// <summary>
/// A map file that could not be read. Always names the line, because a map is a few hundred
/// lines of terse text and "unknown profile" without a line number is a search.
/// </summary>
public sealed class MapFormatException(string message, string? source, int line)
    : ContentFormatException(message, source, line, fallback: "map");
