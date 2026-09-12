using Hexcom.Core.Units;

namespace Hexcom.Core.Awareness;

/// <summary>
/// The moment a side's word got out: somebody carrying a set registered somebody and passed it on.
/// </summary>
/// <remarks>
/// <b>It lives in the awareness model and not on the mission, and that was the decision worth
/// making carefully.</b> A round limit is a property of a mission — a different briefing on the
/// same ground stops at a different hour. <em>The alarm went out</em> is not: it is a fact about
/// what one side knows and when it came to know it, produced by the same relay that already
/// carries a contact side-wide, and it would be true of this ground with no mission on it at all.
/// Putting the fact on the mission would have meant every future mission shape re-deriving it
/// from contacts, and putting the limit here would have meant the awareness model holding a
/// number that belongs to a briefing. See <c>docs/decisions.md</c> entry 030, which named the gap,
/// and <see cref="Battles.Deadline"/>, which is the other half.
/// <para>
/// <b>What counts is a set, not a shout.</b> <see cref="AwarenessTracker"/> relays through
/// whoever can be reached — a radio reaches the whole side, a voice reaches fifteen metres, and
/// seeing a comrade react reaches as far as you can see. Only the first of those is the alarm.
/// A sentry shouting to the man beside him has told one man; a sentry with a set has told the
/// garrison, and on this ground the barn and the tower are both outside earshot of the compound,
/// so which of the two happened decides whether there is a mission left at all.
/// </para>
/// <para>
/// <b>It is not forgotten when the man who raised it goes down.</b> <see cref="AwarenessTracker"/>
/// wipes every contact held by or about a departing unit, which is what makes silencing a witness
/// work — but word already sent cannot be unsent, and a squad that kills the signaller one second
/// too late has not bought back the second. That asymmetry is the whole of why the set is worth
/// killing first, and it is the counter-play to the same rule that makes the quiet kill good.
/// </para>
/// </remarks>
/// <param name="Side">Whose word it was.</param>
/// <param name="Round">The round it went out in.</param>
/// <param name="Raised">Who let it out.</param>
/// <param name="About">Which of the other side they had registered.</param>
public sealed record Alarm(Side Side, int Round, UnitId Raised, UnitId About)
{
    /// <summary>How many rounds it has been out, from the battle's current round.</summary>
    public int RoundsSince(int round) => Math.Max(0, round - Round);

    public override string ToString() => $"{Side} alarm in round {Round}, {Raised} about {About}";
}
