namespace Hexcom.Content;

/// <summary>
/// A content file that could not be read. Always names the line, because these are terse text
/// formats and "unknown profile" without a line number is a search.
/// </summary>
/// <remarks>
/// One base for the two formats because the lexical layer is one thing — the same tokeniser, the
/// same comment rule, the same coordinate syntax, the same message shape. A caller that wants to
/// report "this file is wrong" without caring which kind of file it was catches this; the two
/// subclasses exist so that one that does care can say so.
/// </remarks>
public abstract class ContentFormatException : Exception
{
    protected ContentFormatException(string message, string? source, int line, string fallback)
        : base($"{source ?? fallback}:{line}: {message}")
    {
        Source = source;
        Line = line;
    }

    /// <summary>The file the error was found in, if it came from one.</summary>
    public new string? Source { get; }

    /// <summary>One-based line number.</summary>
    public int Line { get; }
}
