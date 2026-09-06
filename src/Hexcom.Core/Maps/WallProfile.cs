namespace Hexcom.Core.Maps;

/// <summary>How much protection a piece of terrain gives.</summary>
public enum CoverGrade
{
    None = 0,
    Light = 1,
    Half = 2,
    Full = 3,
}

/// <summary>
/// The physical character of a wall segment. Kept as data rather than an enum so map content
/// and balance can add new kinds without touching the rules.
/// </summary>
/// <param name="Id">Stable identifier for content and save files.</param>
/// <param name="HeightMetres">Height above the floor of the tile the segment sits on.</param>
/// <param name="Cover">Protection given to a unit hugging this segment.</param>
/// <param name="BlocksMovement">Whether a unit is stopped by it (before considering vaulting).</param>
/// <param name="Opaque">
/// Whether light passes through it. This is a property of the material, not of the situation:
/// a low wall is opaque, and whether you can see <em>over</em> it is decided by the geometry of
/// the sight line, not by this flag. A standing soldier is visible over a waist-high wall; the
/// same soldier prone behind it is not, and both fall out of the same trace.
/// </param>
/// <param name="Vaultable">Whether a unit can cross it by vaulting.</param>
/// <param name="Climbable">Whether a unit can climb onto or over it, at climb cost.</param>
/// <param name="Destructible">Whether fire can remove it.</param>
public sealed record WallProfile(
    string Id,
    double HeightMetres,
    CoverGrade Cover,
    bool BlocksMovement,
    bool Opaque,
    bool Vaultable,
    bool Climbable,
    bool Destructible = false)
{
    /// <summary>Waist-high: sandbags, a low wall, a car. Half cover, vault over it, see over it.</summary>
    public static readonly WallProfile Low = new(
        Id: "low",
        HeightMetres: 1.0,
        Cover: CoverGrade.Half,
        BlocksMovement: true,
        Opaque: true,
        Vaultable: true,
        Climbable: true,
        Destructible: true);

    /// <summary>Head-high: a concrete barrier or a garden wall. Full cover, climbable.</summary>
    public static readonly WallProfile High = new(
        Id: "high",
        HeightMetres: 2.0,
        Cover: CoverGrade.Full,
        BlocksMovement: true,
        Opaque: true,
        Vaultable: false,
        Climbable: true,
        Destructible: true);

    /// <summary>A building wall. Nothing goes through, over or past it at this layer.</summary>
    public static readonly WallProfile Solid = new(
        Id: "solid",
        HeightMetres: 3.0,
        Cover: CoverGrade.Full,
        BlocksMovement: true,
        Opaque: true,
        Vaultable: false,
        Climbable: false);

    /// <summary>Chain link or railing: stops you walking through, hides nothing at all.</summary>
    public static readonly WallProfile Railing = new(
        Id: "railing",
        HeightMetres: 1.2,
        Cover: CoverGrade.Light,
        BlocksMovement: true,
        Opaque: false,
        Vaultable: true,
        Climbable: true,
        Destructible: true);

    /// <summary>
    /// A sight-blocker you can walk through: smoke, a hedge, a curtain of hanging plastic.
    /// </summary>
    public static readonly WallProfile Screen = new(
        Id: "screen",
        HeightMetres: 2.0,
        Cover: CoverGrade.Light,
        BlocksMovement: false,
        Opaque: true,
        Vaultable: false,
        Climbable: false,
        Destructible: true);
}
