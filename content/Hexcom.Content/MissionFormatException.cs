namespace Hexcom.Content;

/// <summary>
/// A mission file that could not be read.
/// </summary>
/// <remarks>
/// A mission is a dozen statements rather than a few hundred, so the line number matters less
/// here than it does for a map — but the failures are worse. A misspelt place name or a
/// deployment on a hex nobody can stand on is a battle that will not start, and the person
/// reading the message is the person who typed the line.
/// </remarks>
public sealed class MissionFormatException(string message, string? source, int line)
    : ContentFormatException(message, source, line, fallback: "mission");
