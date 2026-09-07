namespace Hexcom.Core.Maps;

/// <summary>
/// How a unit gets from one place to the next.
/// </summary>
/// <remarks>
/// Movement is a graph of typed, individually priced links rather than a grid of equal steps.
/// That is what makes a ladder cost most of a turn while a stride across open floor costs
/// almost nothing, without any of it being special-cased in the pathfinder.
/// </remarks>
public enum TraversalKind
{
    /// <summary>An ordinary stride onto open ground.</summary>
    Walk,

    /// <summary>Broken or awkward footing.</summary>
    Rough,

    /// <summary>Over a waist-high obstacle.</summary>
    Vault,

    /// <summary>Up a ledge or over a head-high wall, hauling yourself with both hands.</summary>
    Climb,

    /// <summary>A fixed ladder. Deliberately expensive: one rung-to-rung move eats most of a turn.</summary>
    Ladder,

    /// <summary>Stairs or a ramp, cheap and safe.</summary>
    Stairs,

    /// <summary>Down a drop under your own control.</summary>
    Drop,

    /// <summary>Across a gap.</summary>
    Jump,

    /// <summary>Through a doorway, which may need opening.</summary>
    Door,

    /// <summary>Belly-crawling. Slow, quiet, and low enough to break line of sight.</summary>
    Crawl,
}

/// <summary>
/// Action point prices and the physical thresholds that decide which traversal applies.
/// </summary>
/// <remarks>
/// A stride costs five and a turn is fifty, so ten hexes of open ground is a turn spent doing
/// nothing else. Firing costs about half a turn, so the archetypal turn is move a little, shoot,
/// take cover.
/// <para>
/// The turn is fifty rather than ten because the cheapest action sets the resolution of
/// everything else. At a walk of one point nothing can be priced <em>below</em> a stride — so
/// turning on the spot cost a full step, and no per-soldier multiplier could make anyone quicker
/// over open ground, only slower. At five, turning is worth two, and a multiplier anywhere from
/// three fifths to double lands on a distinct number.
/// </para>
/// <para>
/// It matters twice over because action points are also time inside a reaction window. A ten
/// hex run is fifty ticks long rather than ten, so placing a shot to land just as somebody
/// clears a wall is a real choice rather than a rounding accident.
/// </para>
/// </remarks>
public sealed record MovementCosts
{
    public static readonly MovementCosts Default = new();

    /// <summary>Action points a typical unit receives each turn.</summary>
    public int ActionPointsPerTurn { get; init; } = 50;

    public int Walk { get; init; } = 5;
    public int Rough { get; init; } = 10;
    public int Vault { get; init; } = 15;
    public int Climb { get; init; } = 30;
    public int Ladder { get; init; } = 30;
    public int Stairs { get; init; } = 10;
    public int Drop { get; init; } = 5;
    public int Jump { get; init; } = 20;
    public int Door { get; init; } = 10;

    /// <summary>
    /// An authored crawl-space — a duct or a gap under a fence that can only be bellied through.
    /// </summary>
    /// <remarks>
    /// Moving prone in the open is not this: that is an ordinary traversal at the stance's own
    /// multiplier, which happens to come to about the same. This is for ground that <em>cannot</em>
    /// be crossed any other way.
    /// </remarks>
    public int Crawl { get; init; } = 15;

    /// <summary>
    /// Dropping to a crouch, going prone, or standing back up. Under half a stride, but the whole
    /// point of the stance system is that it costs you something to change your mind.
    /// </summary>
    public int ChangeStance { get; init; } = 2;

    /// <summary>
    /// Turning on the spot to look somewhere other than where you are going. Moving already
    /// turns you to face your line of travel for nothing; this is the price of watching one way
    /// while standing still, which is the decision facing is meant to create.
    /// </summary>
    public int TurnInPlace { get; init; } = 2;

    /// <summary>Height change a unit can absorb mid-stride without it counting as a climb.</summary>
    public double StepHeight { get; init; } = 0.4;

    /// <summary>Tallest ledge a unit can pull itself up.</summary>
    public double MaxClimb { get; init; } = 2.2;

    /// <summary>Furthest a unit will drop deliberately.</summary>
    public double MaxSafeDrop { get; init; } = 3.0;

    public int BaseCost(TraversalKind kind) => kind switch
    {
        TraversalKind.Walk => Walk,
        TraversalKind.Rough => Rough,
        TraversalKind.Vault => Vault,
        TraversalKind.Climb => Climb,
        TraversalKind.Ladder => Ladder,
        TraversalKind.Stairs => Stairs,
        TraversalKind.Drop => Drop,
        TraversalKind.Jump => Jump,
        TraversalKind.Door => Door,
        TraversalKind.Crawl => Crawl,
        _ => Walk,
    };
}
