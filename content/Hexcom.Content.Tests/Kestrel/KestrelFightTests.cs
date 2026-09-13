using System.Linq;
using Xunit.Abstractions;

namespace Hexcom.Content.Tests.Kestrel;

/// <summary>
/// Kestrel Yard, fought over by the AI on both sides, and written down the way the waystation's
/// matches are. The same four environment variables steer it: <c>HEXCOM_SEEDS</c>,
/// <c>HEXCOM_SEED_FROM</c>, <c>HEXCOM_ROUNDS</c> and <c>HEXCOM_TRANSCRIPT</c>. Filter by class to
/// fight only this map.
/// </summary>
public class KestrelFightTests(ITestOutputHelper output)
{
    private static int Seeds => Env("HEXCOM_SEEDS", 1);
    private static int FirstSeed => Env("HEXCOM_SEED_FROM", 1);
    private static int Rounds => Env("HEXCOM_ROUNDS", KestrelFight.Rounds);

    private static int Env(string name, int fallback)
        => int.TryParse(Environment.GetEnvironmentVariable(name), out var n) && n > 0 ? n : fallback;

    [Fact]
    public void TheFightIsRecordedSeedBySeed()
    {
        foreach (var seed in Enumerable.Range(FirstSeed, Seeds))
        {
            var battle = KestrelFight.Start(seed);
            var report = MatchRecorder.Play(battle, seed, Rounds);
            output.WriteLine(MatchRecorder.Describe(report, KestrelFight.Landmarks));
            if (Environment.GetEnvironmentVariable("HEXCOM_TRANSCRIPT") == seed.ToString())
                output.WriteLine(MatchRecorder.Transcript(report));

            // The clock is on the objective, so every match settles by round 21 at the latest.
            Assert.True(report.Settled, $"seed {seed}: ran to the round cap with no verdict");
        }
    }
}
