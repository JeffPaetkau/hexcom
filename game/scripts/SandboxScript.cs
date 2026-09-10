using System.Collections.Generic;
using System.Linq;

namespace Hexcom.Game;

/// <summary>One thing to do, in the order it was typed.</summary>
/// <param name="Flag">The flag as written, including its dashes.</param>
/// <param name="Argument">What followed it, or null for a flag that takes nothing.</param>
public sealed record SandboxStep(string Flag, string? Argument)
{
    public override string ToString() => Argument is null ? Flag : $"{Flag} {Argument}";
}

/// <summary>
/// The command line as a list of things a person could have done at the keyboard.
/// </summary>
/// <remarks>
/// <para>
/// A capture is deaf on purpose — the window opens under whatever the pointer was already doing,
/// so a run that read the real mouse would not reproduce. <see cref="SandboxCapture"/> put the
/// cursor, the turn and the enemy's automation back as arguments, and that was enough to
/// photograph a situation the <em>AI</em> made. It was never enough to photograph one a
/// <em>person</em> made: nothing in a capture moved one of ours, fired, or changed a stance, so
/// every readout downstream of the player having done something — the reaction line above all —
/// was checkable only with a hand on the keyboard.
/// </para>
/// <para>
/// This is that hand, as an argument list. <b>Order is the whole of it</b>, which is why the
/// flags are parsed into a sequence rather than read one at a time: <c>--move</c> then
/// <c>--pass</c> is a different battle from <c>--pass</c> then <c>--move</c>, and a parser that
/// asks "was <c>--move</c> given?" cannot tell them apart. So everything that is not a setting
/// is a step, kept in the order it appears, and <see cref="HexSandbox"/> walks the list.
/// </para>
/// <para>
/// <b>It is a list of arguments and not a second input system.</b> Every step calls the same
/// method on <see cref="HexSandbox"/> that the corresponding key does — the same guards, the same
/// bookkeeping afterwards, the same one place that touches <c>Battle</c>. A script that could
/// reach the rules directly would be a way for a picture to show a state the keyboard cannot
/// reach, which is the opposite of what a harness is for.
/// </para>
/// <para>
/// Unrecognised flags are kept as steps and reported when they run rather than being dropped
/// here, so a typo produces a line in the log next to the steps that did work instead of a
/// picture that is quietly of the wrong thing.
/// </para>
/// </remarks>
public sealed class SandboxScript
{
    /// <summary>
    /// Flags that say what to open and where to write, rather than what to do.
    /// </summary>
    /// <remarks>
    /// The test for this list is whether a person at the keyboard could do it. They can move,
    /// fire and pass the turn; they cannot choose which map the scene booted with or where the
    /// PNG goes. Everything on the other side of that line is a step.
    /// </remarks>
    private static readonly Dictionary<string, bool> Settings = new()
    {
        ["--shot"] = true,          // true: takes a value
        ["--shot-after"] = true,
        ["--scenario"] = true,
        ["--ai"] = false,
        ["--windows"] = false,
    };

    /// <summary>Steps that take no argument, so the next word is not swallowed as one.</summary>
    private static readonly HashSet<string> Bare =
    [
        "--fit", "--arm", "--extract", "--resolve", "--ai-turn",
    ];

    private SandboxScript(IReadOnlyList<SandboxStep> steps) => Steps = steps;

    /// <summary>What to do, in the order it was typed.</summary>
    public IReadOnlyList<SandboxStep> Steps { get; }

    /// <summary>Whether there is anything to do at all.</summary>
    public bool IsEmpty => Steps.Count == 0;

    /// <summary>Split a user-argument list into the steps in it, dropping the settings.</summary>
    public static SandboxScript Parse(string[] args)
    {
        var steps = new List<SandboxStep>();

        for (var i = 0; i < args.Length; i++)
        {
            var (flag, joined) = Split(args[i]);
            if (!flag.StartsWith("--")) continue;

            if (Settings.TryGetValue(flag, out var takesValue))
            {
                if (takesValue && joined is null) i++;      // skip the value it owns
                continue;
            }

            if (Bare.Contains(flag)) { steps.Add(new SandboxStep(flag, joined)); continue; }

            // Everything else takes a value, which may be attached with = or be the next word.
            // A flag at the end of the line, or one immediately followed by another flag, gets
            // a null argument and the step that runs it says what it wanted.
            var argument = joined;
            if (argument is null && i + 1 < args.Length && !args[i + 1].StartsWith("--")) argument = args[++i];

            steps.Add(new SandboxStep(flag, argument));
        }

        return new SandboxScript(steps);
    }

    /// <summary>Reads <c>--flag value</c> and <c>--flag=value</c>, because both get typed.</summary>
    public static string? ValueOf(string[] args, string flag)
    {
        var joined = args.FirstOrDefault(a => a.StartsWith(flag + "="));
        if (joined is not null) return joined[(flag.Length + 1)..];

        var index = System.Array.IndexOf(args, flag);
        return index >= 0 && index + 1 < args.Length ? args[index + 1] : null;
    }

    private static (string Flag, string? Joined) Split(string argument)
    {
        var equals = argument.IndexOf('=');
        return equals < 0 ? (argument, null) : (argument[..equals], argument[(equals + 1)..]);
    }
}
