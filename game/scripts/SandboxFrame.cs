using System.Collections.Generic;
using Hexcom.Content;
using Hexcom.Core.Battles;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>One turn <see cref="Commander"/> took in the sandbox, and what it chose to do with it.</summary>
/// <param name="Unit">Whose turn it was.</param>
/// <param name="Orders">What it did, in order, each carrying the appraisal it was picked on.</param>
/// <param name="Banked">What it had left when the turn ended, which is what it can react with.</param>
/// <remarks>
/// <see cref="Order"/> already carries the reasoning; this only remembers whose it was, because
/// by the time the frame is drawn the unit has finished and the battle has moved on to somebody
/// else. What it does <b>not</b> carry is what the orders <em>did</em> — a move's reaction window,
/// a shot's outcome — because <c>Commander.TakeTurn</c> does not return those. See entry 022 in
/// <c>docs/decisions.md</c>.
/// </remarks>
public sealed record TakenTurn(Unit Unit, IReadOnlyList<Order> Orders, int Banked);

/// <summary>Everything the sandbox has worked out about the current moment, ready to be drawn.</summary>
/// <param name="Battle">The battle itself. Queried, never changed, by anything that takes a frame.</param>
/// <param name="Layer">Which storey is being looked at. Storeys above it are ghosted.</param>
/// <param name="Hover">The node under the cursor, if it is over the map at all.</param>
/// <param name="Reach">Where the active unit could get to, and for what.</param>
/// <param name="View">What the active unit can make out, per node on the current layer.</param>
/// <param name="LastWindow">What the last committed move got shot at with. Debug readout only.</param>
/// <param name="Turns">
/// The turns <see cref="Commander"/> has taken since a person last did anything, newest last.
/// Empty until somebody hands it a turn.
/// </param>
/// <param name="HostilesAutomatic">Whether every hostile turn goes to <see cref="Commander"/>.</param>
/// <param name="Scenario">The map and the deployment this battle was opened with.</param>
/// <param name="TileDetail">
/// Whether a tile is currently drawn close enough to carry its own labels and outlines. See
/// <see cref="SandboxCamera.LegibleAt"/>.
/// </param>
/// <param name="Open">
/// The reaction window waiting to be answered, if there is one.
/// </param>
/// <param name="Chooser">
/// Which of that window's offers the keyboard is pointed at. Meaningless without one.
/// </param>
/// <param name="AnswerByHand">
/// Whether a move stops at its window rather than taking every recommendation.
/// </param>
/// <param name="Mission">
/// The mission this battle is, read from <c>content/</c>, or null for a bare map.
/// </param>
/// <param name="Briefing">Whether the full six-part briefing is on screen.</param>
/// <param name="OutOfTime">
/// Whether the mission's own round limit has passed. The rules have no clock, so this one is
/// applied by the thing running the battle — see <c>docs/decisions.md</c> entry 047.
/// </param>
/// <param name="Omniscient">
/// Whether the picture shows everything in play, or only what our side knows. See
/// <see cref="Sees"/>.
/// </param>
/// <param name="Knowledge">
/// What our side holds on each hostile in play: eyes on it, or a marker with a credence. A
/// hostile with no entry is one nobody of ours has heard a thing about.
/// </param>
/// <remarks>
/// This exists so that drawing has no way to reach back into the node and ask another question.
/// A frame is assembled once, in <see cref="HexSandbox.Recalculate"/>, and everything drawn from
/// it is drawn from the same answers — which is also what stops the map and the readouts
/// disagreeing about a unit that a reaction moved half way through the frame.
/// <para>
/// The last two are the greybox's one decision that makes it a game, carried as data. The flat
/// sandbox drew every hostile in play because it was built to drive both sides; a playable view
/// draws our side's knowledge and nothing else. <see cref="Knowledge"/> is that knowledge —
/// <c>Tactician.Known</c> for each of ours, merged by taking the best any of them holds — and it
/// is the same list the scorer weighs, which is contract 2 in <c>docs/map.md</c> as a
/// dictionary. Nothing in the view may ask the battle about a hostile it cannot see through
/// this; that is what <see cref="Sees"/> is for.
/// </para>
/// </remarks>
public sealed record SandboxFrame(
    Battle Battle,
    int Layer,
    NodeId? Hover,
    ReachabilityResult Reach,
    IReadOnlyDictionary<NodeId, SightResult> View,
    string LastWindow,
    IReadOnlyList<TakenTurn> Turns,
    bool HostilesAutomatic,
    SandboxScenario Scenario,
    bool TileDetail,
    ReactionWindow? Open,
    int Chooser,
    bool AnswerByHand,
    Mission? Mission,
    bool Briefing,
    bool OutOfTime,
    bool Omniscient,
    IReadOnlyDictionary<UnitId, Threat> Knowledge)
{
    /// <summary>
    /// Where the subject of the open window is standing <em>now</em>, which is where it started.
    /// </summary>
    /// <remarks>
    /// The distinction the whole readout turns on. A committed move is paid for and not taken:
    /// the mover stands at the start until the window resolves and walks it along, so the dot on
    /// the map is where it is and the route drawn out of it is where it is going. Entry 040.
    /// </remarks>
    public NodeId? Committed => Open?.Move.Start;

    /// <summary>
    /// Whether a unit is drawn as a body where it actually stands, and may be pointed at.
    /// </summary>
    /// <remarks>
    /// Our own soldiers always; everybody, when the picture is omniscient; otherwise a hostile
    /// only while somebody of ours holds eyes on it. Contract 3 permits exactly this and forbids
    /// nothing else — the marker a hostile has moved away from is drawn as a ghost by the view,
    /// and a hostile nobody has heard a thing about is not drawn at all. The cursor goes through
    /// this too, so the shot line cannot quote a soldier the map is not showing.
    /// </remarks>
    public bool Sees(Unit unit)
        => Omniscient
           || unit.Side == Side.Player
           || (Knowledge.TryGetValue(unit.Id, out var held) && held.EyesOn);

    /// <summary>The unit under the cursor, if the picture is allowed to show one there.</summary>
    public Unit? HoveredUnit
        => Hover is { } node && Battle.UnitAt(node) is { } unit && Sees(unit) ? unit : null;
}
