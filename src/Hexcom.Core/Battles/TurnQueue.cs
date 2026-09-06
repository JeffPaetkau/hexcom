using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Hexcom.Core.Units;

namespace Hexcom.Core.Battles;

/// <summary>
/// A booked turn: which unit acts, at what point on the battle clock, and what it rolled.
/// </summary>
/// <param name="ActAt">Position on the battle clock. Lower goes first.</param>
/// <param name="Roll">The initiative result behind the booking, for the interface to show.</param>
public readonly record struct TurnSlot(UnitId Unit, long ActAt, int Roll)
{
    public override string ToString() => $"{Unit}@{ActAt} (rolled {Roll})";
}

/// <summary>
/// Who acts next, ordered by a clock rather than by side.
/// </summary>
/// <remarks>
/// A queue over act times, rather than a list of sides taking it in turns, is what produces the
/// interleaved order: one of yours, two of theirs, one of yours. It is also the structure a
/// continuous time-unit system needs — the kind where a cheap action brings you round sooner.
/// Shipping round-based initiative on top of it costs nothing now and leaves that door open.
/// <para>
/// Kept as a sorted list rather than a heap, because a squad fight holds a couple of dozen
/// bookings and the interface wants to read the whole order out, not just the head.
/// </para>
/// </remarks>
public sealed class TurnQueue
{
    private readonly List<TurnSlot> _slots = [];

    public int Count => _slots.Count;

    /// <summary>Everything booked, soonest first.</summary>
    public IReadOnlyList<TurnSlot> Upcoming => _slots;

    /// <summary>Book a unit to act at a point on the clock.</summary>
    public void Schedule(TurnSlot slot)
    {
        var index = _slots.FindIndex(s => Compare(slot, s) < 0);
        if (index < 0) _slots.Add(slot);
        else _slots.Insert(index, slot);
    }

    public bool TryDequeue([NotNullWhen(true)] out TurnSlot slot)
    {
        if (_slots.Count == 0)
        {
            slot = default;
            return false;
        }

        slot = _slots[0];
        _slots.RemoveAt(0);
        return true;
    }

    /// <summary>Cancel every booking for a unit, for when it leaves the fight.</summary>
    public int Remove(UnitId unit) => _slots.RemoveAll(s => s.Unit == unit);

    public void Clear() => _slots.Clear();

    /// <summary>The next booking for a unit, if it has one.</summary>
    public TurnSlot? Next(UnitId unit) => _slots.Cast<TurnSlot?>().FirstOrDefault(s => s!.Value.Unit == unit);

    /// <summary>
    /// Earlier clock time wins; then the higher roll; then unit id, so a fight replays
    /// identically from the same seed.
    /// </summary>
    private static int Compare(TurnSlot a, TurnSlot b)
    {
        var byTime = a.ActAt.CompareTo(b.ActAt);
        if (byTime != 0) return byTime;

        var byRoll = b.Roll.CompareTo(a.Roll);
        if (byRoll != 0) return byRoll;

        return a.Unit.Value.CompareTo(b.Unit.Value);
    }
}
