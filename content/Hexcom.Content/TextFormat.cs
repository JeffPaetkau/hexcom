using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.RegularExpressions;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;

namespace Hexcom.Content;

/// <summary>
/// The lexical layer both content formats sit on: one statement per line, <c>#</c> to end of
/// line is a comment, and every coordinate reads the same way in both.
/// </summary>
/// <remarks>
/// <para>
/// A mission is not a map and the two share not one statement — <c>fill</c> means nothing to a
/// briefing and <c>deploy</c> means nothing to a battlefield. What they do share is everything
/// below the statement: how a line is split, what <c>-21,3</c> and <c>0,1@1</c> mean, what
/// <c>se</c> means, and what an error looks like when a line will not read. That is the part
/// worth having in one place, because it is the part a person carries from one file to the
/// other and would be furious to find subtly different.
/// </para>
/// <para>
/// So there are two readers and one lexer, rather than one reader with a mode flag. A shared
/// reader would need a statement table keyed on which kind of file it was halfway through,
/// which is the same shape of mistake as a <c>BattleMap</c> that knew about deployments.
/// </para>
/// </remarks>
internal abstract class TextFormatReader(string text)
{
    /// <summary>One-based, and settable so a check run after the file is read can blame a line.</summary>
    protected int LineNumber { get; set; }

    /// <summary>Read every line, handing each non-empty one to <see cref="Statement"/>.</summary>
    protected void ReadLines()
    {
        var lines = text.Split('\n');
        for (var i = 0; i < lines.Length; i++)
        {
            LineNumber = i + 1;
            var tokens = Tokenize(lines[i]);
            if (tokens.Length == 0) continue;
            Statement(new Cursor(tokens, Error));
        }
    }

    /// <summary>What one line of this format means.</summary>
    protected abstract void Statement(Cursor c);

    /// <summary>The exception this format throws, so the message names the right kind of file.</summary>
    protected abstract ContentFormatException Error(string message);

    private static string[] Tokenize(string line)
    {
        var hash = line.IndexOf('#');
        if (hash >= 0) line = line[..hash];
        return line.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
    }
}

/// <summary>Bearings as they are written in a content file, indexed by <see cref="HexDirection"/>.</summary>
internal static class Bearings
{
    internal static readonly string[] Names = ["ne", "n", "nw", "sw", "s", "se"];

    internal static bool TryParse(string token, out HexDirection direction)
    {
        var index = Array.IndexOf(Names, token);
        direction = (HexDirection)Math.Max(index, 0);
        return index >= 0;
    }
}

/// <summary>One line's tokens, consumed left to right, with errors that say what was wanted.</summary>
internal sealed class Cursor(string[] tokens, Func<string, ContentFormatException> error)
{
    private static readonly Regex CoordinatePattern = new(@"^(-?\d+),(-?\d+)(?:@(-?\d+))?$", RegexOptions.Compiled);
    private static readonly Regex CornerPairPattern = new(@"^([0-5])-([0-5])$", RegexOptions.Compiled);

    private int _position;

    public bool Done => _position >= tokens.Length;

    /// <summary>The next token without consuming it, or null at the end of the line.</summary>
    public string? Peek => Done ? null : tokens[_position];

    public string Next(string what)
    {
        if (Done) throw error($"Expected {what} but the line ended.");
        return tokens[_position++];
    }

    public string[] Rest()
    {
        var rest = tokens[_position..];
        _position = tokens.Length;
        return rest;
    }

    public void End()
    {
        if (!Done) throw error($"Unexpected '{tokens[_position]}'.");
    }

    public int Int(string what)
    {
        var token = Next(what);
        if (!int.TryParse(token, NumberStyles.Integer, CultureInfo.InvariantCulture, out var value))
            throw error($"Expected {what}, got '{token}'.");
        return value;
    }

    public double Double(string what)
    {
        var token = Next(what);
        if (!double.TryParse(token, NumberStyles.Float, CultureInfo.InvariantCulture, out var value))
            throw error($"Expected {what}, got '{token}'.");
        return value;
    }

    public T Enum<T>(string what) where T : struct, Enum
    {
        var token = Next(what);
        if (!System.Enum.TryParse<T>(token, ignoreCase: true, out var value))
            throw error($"Expected {what}, got '{token}'.");
        return value;
    }

    /// <summary>One of a fixed set of names, mapped to whatever it stands for.</summary>
    public T Named<T>(string what, IReadOnlyDictionary<string, T> known)
    {
        var token = Next(what);
        if (!known.TryGetValue(token, out var value))
            throw error($"Unknown {what} '{token}'. Known: {string.Join(", ", known.Keys.Order(StringComparer.Ordinal))}.");
        return value;
    }

    public HexDirection Direction(string what)
    {
        var token = Next(what);
        if (!Bearings.TryParse(token, out var direction))
            throw error($"Expected {what} (ne, n, nw, sw, s, se), got '{token}'.");
        return direction;
    }

    /// <summary>A hex with no layer: <c>q,r</c>.</summary>
    public Hex Coordinate()
    {
        var token = Next("a hex as q,r");
        if (!TryCoordinate(token, out var hex, out var layer))
            throw error($"Expected a hex as q,r, got '{token}'.");
        if (layer is not null)
            throw error($"'{token}' names a layer; a shape takes its layer afterwards, as 'layer N'.");
        return hex;
    }

    /// <summary>A tile: <c>q,r</c> or <c>q,r@layer</c>, layer 0 when omitted.</summary>
    public TileAddress Address()
    {
        var token = Next("a tile as q,r or q,r@layer");
        if (!TryCoordinate(token, out var hex, out var layer))
            throw error($"Expected a tile as q,r or q,r@layer, got '{token}'.");
        return new TileAddress(hex, layer ?? 0);
    }

    public (int A, int B) CornerPair()
    {
        var token = Next("a corner pair such as 0-2");
        if (!TryCornerPair(token, out var a, out var b))
            throw error($"Expected a corner pair such as 0-2, got '{token}'.");
        if (a == b) throw error($"A chord needs two different corners, not '{token}'.");
        return (a, b);
    }

    /// <summary>A set of hexes, in the order the shape produces them, without repeats.</summary>
    public List<Hex> Shape()
    {
        var keyword = Next("a shape: hex, hexes, line, disc or ring");
        IEnumerable<Hex> hexes = keyword switch
        {
            "hex" => [Coordinate()],
            "hexes" => Coordinates(),
            "line" => Line(),
            "disc" => Coordinate().WithinRange(Radius()),
            "ring" => Coordinate().Ring(Radius()),
            _ => throw error($"Expected a shape (hex, hexes, line, disc or ring), got '{keyword}'."),
        };
        return hexes.Distinct().ToList();
    }

    public static bool TryCornerPair(string token, out int a, out int b)
    {
        var match = CornerPairPattern.Match(token);
        a = b = 0;
        if (!match.Success) return false;
        a = int.Parse(match.Groups[1].Value, CultureInfo.InvariantCulture);
        b = int.Parse(match.Groups[2].Value, CultureInfo.InvariantCulture);
        return true;
    }

    public static bool TryCoordinate(string token, out Hex hex, out int? layer)
    {
        var match = CoordinatePattern.Match(token);
        hex = default;
        layer = null;
        if (!match.Success) return false;
        hex = new Hex(
            int.Parse(match.Groups[1].Value, CultureInfo.InvariantCulture),
            int.Parse(match.Groups[2].Value, CultureInfo.InvariantCulture));
        if (match.Groups[3].Success)
            layer = int.Parse(match.Groups[3].Value, CultureInfo.InvariantCulture);
        return true;
    }

    private List<Hex> Coordinates()
    {
        var hexes = new List<Hex> { Coordinate() };
        while (!Done && TryCoordinate(tokens[_position], out _, out _))
            hexes.Add(Coordinate());
        return hexes;
    }

    private IReadOnlyList<Hex> Line()
    {
        var from = Coordinate();
        var to = Next("'to'");
        if (to != "to") throw error($"Expected 'to' between the ends of a line, got '{to}'.");
        return from.LineTo(Coordinate());
    }

    private int Radius()
    {
        var r = Next("'r'");
        if (r != "r") throw error($"Expected 'r' before a radius, got '{r}'.");
        var radius = Int("a radius");
        if (radius < 0) throw error("A radius cannot be negative.");
        return radius;
    }
}
