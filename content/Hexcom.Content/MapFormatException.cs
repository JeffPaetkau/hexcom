namespace Hexcom.Content;

/// <summary>
/// A map file that could not be read. Always names the line, because a map is a few hundred
/// lines of terse text and "unknown profile" without a line number is a search.
/// </summary>
public sealed class MapFormatException : Exception
{
    public MapFormatException(string message, string? source, int line)
        : base($"{source ?? "map"}:{line}: {message}")
    {
        Source = source;
        Line = line;
    }

    /// <summary>The file the error was found in, if it came from one.</summary>
    public new string? Source { get; }

    /// <summary>One-based line number.</summary>
    public int Line { get; }
}
