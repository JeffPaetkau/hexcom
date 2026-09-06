using Hexcom.Core.Hexes;

namespace Hexcom.Core.Maps;

/// <summary>A hex at a given vertical layer. Layers are storeys, not fine elevation.</summary>
public readonly record struct TileAddress(Hex Hex, int Layer)
{
    public TileAddress Above => this with { Layer = Layer + 1 };
    public TileAddress Below => this with { Layer = Layer - 1 };

    public TileAddress Neighbor(HexDirection direction) => this with { Hex = Hex.Neighbor(direction) };

    public override string ToString() => $"{Hex}@{Layer}";
}

/// <summary>
/// The surface a unit walks on. Movement cost and noise are here rather than baked into the
/// traversal rules so content can add surfaces without touching code.
/// </summary>
/// <param name="Id">Stable identifier for content and save files.</param>
/// <param name="ExtraApCost">Added to the base walk cost when entering.</param>
/// <param name="NoiseFactor">Multiplier on the noise a moving unit makes. 1.0 is ordinary ground.</param>
/// <param name="Passable">Whether a unit can be here at all.</param>
public sealed record GroundType(string Id, int ExtraApCost, double NoiseFactor, bool Passable = true)
{
    public static readonly GroundType Floor = new("floor", 0, 1.0);
    public static readonly GroundType Grass = new("grass", 0, 0.7);
    public static readonly GroundType Gravel = new("gravel", 0, 1.6);
    public static readonly GroundType Rubble = new("rubble", 1, 1.8);
    public static readonly GroundType Mud = new("mud", 1, 0.8);
    public static readonly GroundType ShallowWater = new("shallow_water", 2, 2.0);
    public static readonly GroundType Void = new("void", 0, 0.0, Passable: false);
}

/// <summary>Authoring data for one walkable tile. Regions are derived, not stored here.</summary>
public sealed record Tile(TileAddress Address, double FloorHeight, GroundType Ground)
{
    public Tile(TileAddress address) : this(address, address.Layer * 3.0, GroundType.Floor) { }
}
