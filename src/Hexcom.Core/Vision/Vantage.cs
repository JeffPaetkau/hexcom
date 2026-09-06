using Hexcom.Core.Movement;

namespace Hexcom.Core.Vision;

/// <summary>
/// Somewhere a unit is, and how it is standing there. Everything the sight trace needs to know
/// about a participant, without needing a unit to exist yet.
/// </summary>
public readonly record struct Vantage(NodeId Node, Stance Stance = Stance.Standing)
{
    public StanceProfile Profile => StanceProfile.For(Stance);

    public Vantage Crouched() => this with { Stance = Stance.Crouching };
    public Vantage Prone() => this with { Stance = Stance.Prone };

    public override string ToString() => $"{Node} ({Stance})";
}
