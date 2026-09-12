using Xunit;

namespace Hexcom.Core.Tests.Measured;

/// <summary>
/// A test that only runs when somebody asked for a batch.
/// </summary>
/// <remarks>
/// A run of matches is minutes where the rest of the suite is milliseconds, and a suite nobody
/// runs because it is slow is a suite that stops catching things. So the batch is checked in,
/// reproducible and off by default: set <c>HEXCOM_BATCH=1</c> to run it, and <c>HEXCOM_SEEDS</c>
/// to say how many matches per arm.
/// <para>
/// Checked in rather than thrown away with the figures it produced, because the point of a
/// measurement is that the next person can take it again. A number in <c>docs/decisions.md</c>
/// with no way to reproduce it is an argument that has been rounded.
/// </para>
/// </remarks>
public sealed class BatchFactAttribute : FactAttribute
{
    public BatchFactAttribute()
    {
        if (Measurement.Asked) return;

        Skip = "Set HEXCOM_BATCH=1 to run. A batch of matches is minutes, not milliseconds.";
    }
}

/// <summary>How many matches an arm runs, and whether anybody asked for one.</summary>
public static class Measurement
{
    public static bool Asked => Environment.GetEnvironmentVariable("HEXCOM_BATCH") is not (null or "" or "0");

    /// <summary>Matches per arm. Paired across arms, so the same seeds are played every time.</summary>
    public static int Seeds =>
        int.TryParse(Environment.GetEnvironmentVariable("HEXCOM_SEEDS"), out var n) && n > 0 ? n : 100;
}
