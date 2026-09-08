namespace Hexcom.Core.Tactics;

/// <summary>
/// What one action is worth, and where the worth came from.
/// </summary>
/// <remarks>
/// A single number would rank options perfectly well and tell nobody anything. The terms are kept
/// apart because the interface has to be able to say <em>why</em> one option beats another — "he
/// shoots because the shot is worth four and the dive is worth one" is a sentence a player can
/// argue with, and "he shoots because 4.1 &gt; 1.2" is not.
/// <para>
/// It is also the honest way to keep the AI and the interface reading the same page. If a term
/// cannot be shown to a player it should not be in here, and if it can be shown it is available
/// to both.
/// </para>
/// </remarks>
/// <param name="Harm">
/// Vitality expected off the enemy now, with plate worn through and shields soaked counted at
/// what they are worth, and putting them down counted at what <em>that</em> is worth.
/// </param>
/// <param name="Spared">
/// Vitality expected to stay on us because of how this leaves the soldier standing. Discounted:
/// it is next round's saving, and next round may not come to that.
/// </param>
/// <param name="Prospect">
/// Vitality this sets up rather than delivers — a shot it opens for you next round because you
/// are now looking the right way, or one it opens for somebody you called the contact in to.
/// Discounted the same way.
/// </param>
/// <param name="Spent">The points it costs, priced in the same currency as everything else.</param>
public readonly record struct Appraisal(double Harm, double Spared, double Prospect, double Spent)
{
    public static readonly Appraisal Nothing = new(0, 0, 0, 0);

    /// <summary>What the whole thing comes to. This is what gets ranked.</summary>
    public double Score => Harm + Spared + Prospect - Spent;

    /// <summary>True when the action is worth more than the points it burns.</summary>
    public bool WorthDoing => Score > 0;

    /// <summary>Add two appraisals term by term, for an action that does more than one thing.</summary>
    public static Appraisal operator +(Appraisal a, Appraisal b)
        => new(a.Harm + b.Harm, a.Spared + b.Spared, a.Prospect + b.Prospect, a.Spent + b.Spent);

    public override string ToString()
        => $"{Score:+0.00;-0.00} (harm {Harm:0.00}, spared {Spared:0.00}, prospect {Prospect:0.00}, spent {Spent:0.00})";
}
