using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Combat;

/// <summary>
/// Somebody a blast might catch, where they are believed to be, and how sure that is.
/// </summary>
/// <remarks>
/// The counterpart of <c>Threat</c> for something that is aimed at a place rather than at a
/// person, and it exists for the same reason: a soldier weighing up a grenade must weigh it
/// against the people it <em>believes</em> are there. Building the forecast from the field would
/// let a commander discover that a remembered enemy has moved by noticing that the grenade it was
/// about to throw would now catch nobody, which is exactly the cheat the whole scheme is built to
/// prevent.
/// <para>
/// Your own side is a different matter and is carried here at full credence. A soldier knows
/// where its squad is standing, and a scorer that did not count them would throw grenades into
/// its own people.
/// </para>
/// </remarks>
public readonly record struct BlastCandidate(Unit Unit, UnitPose Where, double Credence = 1.0)
{
    /// <summary>Somebody in plain view, standing exactly where they are.</summary>
    public static BlastCandidate At(Unit unit) => new(unit, UnitPose.Of(unit));

    public override string ToString() => $"{Unit.Name} at {Where} ({Credence:P0})";
}

/// <summary>
/// One soldier caught in a blast, and what it is expected to do to them.
/// </summary>
/// <param name="Share">
/// How much of the charge reaches them, from nought to one: distance from the burst, what stands
/// between, and how low they are carrying themselves, multiplied together.
/// </param>
/// <param name="Arriving">Damage arriving at the plate, before shields and armour.</param>
/// <param name="Friendly">Whether this is one of the thrower own side.</param>
/// <param name="Expectation">
/// What it does once the layers have had their say, in the same shape and the same currency a
/// shot reports — so a scorer can rank a grenade against a rifle without a second exchange rate.
/// </param>
public sealed record BlastEffect(
    Unit Caught,
    UnitPose Where,
    double Distance,
    double Share,
    int Arriving,
    IReadOnlyList<FacingAspect> Aspects,
    ShotExpectation Expectation,
    bool Friendly,
    double Credence = 1.0)
{
    public override string ToString()
        => $"{Caught.Name} at {Distance:0.0} m takes {Share:P0} of it ({Expectation})";
}

/// <summary>
/// A charge going off somewhere, worked out before anybody commits to it.
/// </summary>
/// <remarks>
/// The shape of a shot, for something that is not one. There is no target and no hit chance:
/// there is a place, everybody standing near enough to it, and what the layers on each of them
/// make of the wave. <see cref="Landing"/> is where it actually comes down, which is not always
/// where it was aimed — the arc has to clear the walls in between, and a throw that does not
/// drops short.
/// </remarks>
/// <param name="Thrower">Who threw it. Null for a mine, whose layer may be long gone.</param>
/// <param name="From">Which side it belongs to, which is what decides who counts as caught out.</param>
/// <param name="Lob">The arc it took. Null for a mine, which was never thrown anywhere.</param>
public sealed record BlastPlan(
    Unit? Thrower,
    Side From,
    ThrownProfile Item,
    NodeId Aimed,
    NodeId Landing,
    IReadOnlyList<BlastEffect> Caught,
    int ApCost,
    string? Refusal,
    LobResult? Lob = null)
{
    public bool CanThrow => Refusal is null;

    /// <summary>Whether it got over everything in the way and landed where it was meant to.</summary>
    public bool Clears => Lob?.Clears ?? true;

    /// <summary>Everybody caught who is not one of ours.</summary>
    public IEnumerable<BlastEffect> Enemies => Caught.Where(e => !e.Friendly);

    /// <summary>Everybody caught who is.</summary>
    public IEnumerable<BlastEffect> Friends => Caught.Where(e => e.Friendly);

    public override string ToString()
        => Refusal ?? $"{Item.Name} at {Landing}, catching {Caught.Count}";
}

/// <summary>One soldier, and what the blast actually did to them.</summary>
public sealed record BlastHit(Unit Caught, DamageTaken Damage, bool Down);

/// <summary>What happened when the thing went off.</summary>
public sealed record BlastOutcome(
    bool Went,
    NodeId Landing,
    IReadOnlyList<BlastHit> Hits,
    int ApSpent,
    string? Refusal)
{
    internal static BlastOutcome Refused(string why) => new(false, default, [], 0, why);

    public int TotalDamage
    {
        get
        {
            var sum = 0;
            foreach (var hit in Hits) sum += hit.Damage.ToVitality;
            return sum;
        }
    }

    public bool AnyDown
    {
        get
        {
            foreach (var hit in Hits) if (hit.Down) return true;
            return false;
        }
    }
}

/// <summary>
/// Works out what a charge going off does to the people near it. Pure arithmetic over a burst
/// point and a sight trace, so it can be tested and tuned without a battle around it.
/// </summary>
/// <remarks>
/// The counterpart of <see cref="Gunnery"/>, and it deliberately hands its answers back in the
/// same currency: a <see cref="ShotExpectation"/> per soldier, out of the same
/// <see cref="Protection.Preview"/> the rifles go through. Everything that ranks actions can then
/// weigh a grenade against a snap shot without knowing that one of them is a grenade.
/// </remarks>
public sealed class Ordnance(BlastModel? model = null)
{
    public BlastModel Model { get; } = model ?? BlastModel.Default;

    /// <summary>
    /// How much of a charge reaches somebody that far from it, before anything else.
    /// </summary>
    /// <remarks>
    /// Straight from full at the burst to nothing at the radius. A curve would be more physical
    /// and less playable: the radius is a ring on a map and a player has to be able to read the
    /// consequence of standing inside it off that ring alone.
    /// </remarks>
    public double Falloff(double distance, double radius)
        => radius <= 0 ? 0 : Math.Clamp(1.0 - distance / radius, 0, 1);

    /// <summary>
    /// What being low is worth against a blast, as a share of what a standing soldier catches.
    /// </summary>
    /// <remarks>
    /// Derived rather than dialled. A blast arrives as a wave and catches as much of a soldier as
    /// stands up into it, so the share is the silhouette height against a standing one: a quarter
    /// flat, a little over two thirds crouched. That makes getting down the right answer to a
    /// grenade without a rule saying so, and it keeps the figure tied to the stance heights the
    /// rest of the game — and the art — is already committed to.
    /// </remarks>
    public static double StanceShare(Stance stance)
        => StanceProfile.For(stance).BodyHeight / StanceProfile.Standing.BodyHeight;

    /// <summary>
    /// The whole share of a charge that reaches one soldier: distance, what is in the way, and
    /// how low they are.
    /// </summary>
    public double Share(double distance, ThrownProfile item, SightResult sight, Stance stance)
    {
        var reach = Falloff(distance, item.Radius);
        if (reach <= 0) return 0;

        var exposed = sight.CanSee ? sight.Exposure : Model.ShelteredShare;
        return reach * exposed * StanceShare(stance);
    }

    /// <summary>
    /// What a blast arriving at one soldier is expected to achieve, layers and all.
    /// </summary>
    /// <remarks>
    /// Simpler than a shot in the one way that matters: a blast does not miss, so there is no
    /// chance to weight the arithmetic by. What survives is the per-face average — a body is a
    /// hexagon to a grenade as much as to a rifle, and which plate the wave finds still depends
    /// on where the thing went off relative to the way the soldier is looking.
    /// <para>
    /// Nothing glances. Obliquity is a model of a solid object skipping off a plate it met
    /// edge-on, and a blast does not arrive as one object along one line; crediting a grenade
    /// with deflection off a shoulder would be borrowing arithmetic that is about something else.
    /// </para>
    /// </remarks>
    public ShotExpectation Expect(Unit caught, ThrownProfile item, int arriving, IReadOnlyList<FacingAspect> aspects)
    {
        if (arriving <= 0 || aspects.Count == 0) return ShotExpectation.Nothing;

        var vitality = 0.0;
        var plate = 0.0;
        var shield = 0.0;
        var down = 0.0;

        foreach (var aspect in aspects)
        {
            var run = caught.Protection.Preview(aspect.Face, item.Kind, arriving, 1);
            var got = Math.Min(run[0].ToVitality, caught.Vitality);

            vitality += aspect.Share * got;
            plate += aspect.Share * run[0].StoppedByArmour;
            shield += aspect.Share * run[0].StoppedByShield;
            if (got >= caught.Vitality) down += aspect.Share;
        }

        return new ShotExpectation(vitality, plate, shield, down);
    }
}
