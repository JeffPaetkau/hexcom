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
/// <param name="BlocksSight">Whether it blocks line of sight for a standing unit.</param>
/// <param name="Vaultable">Whether a unit can cross it by vaulting.</param>
/// <param name="Climbable">Whether a unit can climb onto or over it, at climb cost.</param>
/// <param name="Destructible">Whether fire can remove it.</param>
public sealed record WallProfile(
    string Id,
    double HeightMetres,
    CoverGrade Cover,
    bool BlocksMovement,
    bool BlocksSight,
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
        BlocksSight: false,
        Vaultable: true,
        Climbable: true,
        Destructible: true);

    /// <summary>Head-high: a concrete barrier or a garden wall. Full cover, blocks sight, climbable.</summary>
    public static readonly WallProfile High = new(
        Id: "high",
        HeightMetres: 2.0,
        Cover: CoverGrade.Full,
        BlocksMovement: true,
        BlocksSight: true,
        Vaultable: false,
        Climbable: true,
        Destructible: true);

    /// <summary>A building wall. Nothing goes through or over it at this layer.</summary>
    public static readonly WallProfile Solid = new(
        Id: "solid",
        HeightMetres: 3.0,
        Cover: CoverGrade.Full,
        BlocksMovement: true,
        BlocksSight: true,
        Vaultable: false,
        Climbable: false);

    /// <summary>Chain link or railing: stops you walking through, hides nothing.</summary>
    public static readonly WallProfile Railing = new(
        Id: "railing",
        HeightMetres: 1.2,
        Cover: CoverGrade.Light,
        BlocksMovement: true,
        BlocksSight: false,
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
        BlocksSight: true,
        Vaultable: false,
        Climbable: false,
        Destructible: true);
}
