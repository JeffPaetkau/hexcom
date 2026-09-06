using Hexcom.Core.Movement;
using Hexcom.Core.Units;

namespace Hexcom.Core.Awareness;

/// <summary>
/// How much one unit knows about another.
/// </summary>
/// <remarks>
/// Deliberately not a switch between hidden and spotted. Being noticed is a process, and the
/// interesting play sits in the middle of it — the sentry who heard something and is coming to
/// look, but does not yet know what he is looking for.
/// </remarks>
public enum AwarenessState
{
    /// <summary>No idea this unit exists. Patrol behaviour.</summary>
    Unaware = 0,

    /// <summary>Something registered. Stops, scans, does not commit.</summary>
    Suspicious = 1,

    /// <summary>Holds a belief about where the subject was, and will go and check it.</summary>
    Searching = 2,

    /// <summary>Knows there is a threat here. Takes cover, calls it in.</summary>
    Alerted = 3,

    /// <summary>Has a live fix and is acting on it.</summary>
    Engaged = 4,
}

/// <summary>
/// What one unit currently believes about one other unit.
/// </summary>
/// <remarks>
/// <see cref="LastKnownPosition"/> is a belief, not a fact. It is where the subject was when
/// contact was last made, and it goes stale the moment they move. The gap between that marker
/// and the truth is the thing the stealth game is played in.
/// </remarks>
public sealed class Contact
{
    private readonly AwarenessModel _model;

    internal Contact(AwarenessModel model, UnitId observer, UnitId subject)
    {
        _model = model;
        Observer = observer;
        Subject = subject;
    }

    public UnitId Observer { get; }
    public UnitId Subject { get; }

    /// <summary>
    /// Accumulated certainty, from nothing up to the model ceiling.
    /// </summary>
    /// <remarks>
    /// For rules, AI and tests. Do <b>not</b> put this number in front of the player: what they
    /// get to infer about an enemy is the coarse <see cref="State"/>, through
    /// <see cref="AwarenessTracker.ReadoutFor"/>. Their own units' exposure is the figure they
    /// are allowed to see exactly.
    /// </remarks>
    public double Detection { get; internal set; }

    /// <summary>Where the observer last had contact. Wrong as soon as the subject moves.</summary>
    public NodeId? LastKnownPosition { get; internal set; }

    /// <summary>The round contact was last made, or zero if it never has been.</summary>
    public int LastContactRound { get; internal set; }

    /// <summary>Whether the observer can see the subject right now.</summary>
    public bool EyesOn { get; internal set; }

    /// <summary>
    /// The coarse state the rest of the game reasons in. Certainty alone is not enough to be
    /// engaged: lose sight of someone and you drop back to hunting them, however sure you are.
    /// </summary>
    public AwarenessState State
    {
        get
        {
            if (Detection >= _model.EngagedAt && EyesOn) return AwarenessState.Engaged;
            if (Detection >= _model.AlertedAt) return AwarenessState.Alerted;
            if (Detection >= _model.SearchingAt) return AwarenessState.Searching;
            if (Detection >= _model.SuspiciousAt) return AwarenessState.Suspicious;
            return AwarenessState.Unaware;
        }
    }

    /// <summary>True once the observer will act on this rather than ignore it.</summary>
    public bool IsContact => State >= AwarenessState.Searching;

    public override string ToString() => $"{Observer} on {Subject}: {State} ({Detection:0})";
}

/// <summary>
/// Everything the player is allowed to infer about how aware an enemy is.
/// </summary>
/// <remarks>
/// Coarse on purpose. An exact certainty figure would turn the approach into arithmetic and
/// drain the tension out of it; a five step ladder plus a stale marker keeps the player
/// guessing about the thing they should be guessing about. Their own exposure, by contrast, is
/// reported exactly — that is information about themselves, and hiding it would just be fog.
/// </remarks>
public readonly record struct AwarenessReadout(
    AwarenessState State,
    NodeId? LastKnownPosition,
    int RoundsSinceContact,
    bool EyesOn)
{
    public static readonly AwarenessReadout Nothing = new(AwarenessState.Unaware, null, 0, false);

    /// <summary>Whether the belief is old enough to be worth exploiting.</summary>
    public bool IsStale => RoundsSinceContact >= 2;
}
