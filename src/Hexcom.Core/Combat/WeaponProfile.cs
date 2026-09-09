using System.Collections.Generic;
using System.Linq;

namespace Hexcom.Core.Combat;

/// <summary>
/// The two weapon families, and the whole point of the setting.
/// </summary>
/// <remarks>
/// Each defeats what the other cannot. Force shields soak energy and shrug at solid objects;
/// ablative armour stops rounds and cooks under a sustained beam. Neither is a general answer,
/// so a squad wants both and the enemy composition decides which matters today.
/// <para>
/// They also give you away through different channels. A slugthrower is silent until it fires
/// and then everyone within a hundred metres knows roughly where you are. A beam makes no sound
/// and paints a bright line straight back to you for anyone facing your way.
/// </para>
/// </remarks>
public enum DamageKind
{
    /// <summary>Phasers, blasters, powered blades. Stopped by shields, goes through plate.</summary>
    Beam,

    /// <summary>Slugthrowers, railguns, autocannon. Stopped by plate, goes through shields.</summary>
    Kinetic,
}

/// <summary>
/// One way of firing a weapon: how long it takes and what that buys in accuracy.
/// </summary>
/// <remarks>
/// The cheap modes exist because of the reaction window. Inside one, action points are time: a
/// three point snap shot resolves three ticks into the target's move, while it is still crossing
/// open ground, and a seven point aimed shot resolves after it has arrived in cover. A snap shot
/// that is merely a worse aimed shot would never be chosen. A snap shot that is the only one
/// which connects is a real decision.
/// </remarks>
/// <param name="ApCost">Action points, and therefore ticks inside a reaction window.</param>
/// <param name="Accuracy">Multiplier on the weapon's base accuracy.</param>
/// <param name="Shots">Rounds sent. Each is resolved separately.</param>
public sealed record FireMode(string Name, int ApCost, double Accuracy, int Shots = 1)
{
    public static readonly FireMode Snap = new("snap", 15, 0.70);
    public static readonly FireMode Standard = new("standard", 25, 1.00);
    public static readonly FireMode Aimed = new("aimed", 35, 1.25);
    public static readonly FireMode Burst = new("burst", 30, 0.62, Shots: 3);
    public static readonly FireMode Strike = new("strike", 20, 1.10);
}

/// <summary>
/// How far a weapon reaches, and by what instrument the question is settled.
/// </summary>
/// <remarks>
/// Nearly everything is measured in metres, eye to centre of mass, along the same line the sight
/// trace runs. A blade is not, and measuring one that way was a bug rather than a rule: the line
/// gets <em>longer</em> as the target gets lower, so a two metre reach covered an adjacent
/// standing soldier at 1.89 m and failed against the same soldier prone at 2.24 m. The blade
/// reached worst exactly when the target was least able to avoid it, and the hex size was
/// silently voting on whether melee worked at all.
/// <para>
/// So melee means <b>adjacent</b> and not two metres. The movement graph already answers that
/// question, and answers it with the walls and the storeys included: there is no link through a
/// building wall, and none up a three metre face, so a blade cannot reach through either. A low
/// ledge you could climb is a low ledge you could stab somebody on, which is roughly where
/// measuring in metres landed by accident and is now there on purpose. See
/// <c>docs/decisions.md</c>, entry 008.
/// </para>
/// </remarks>
public enum WeaponReach
{
    /// <summary>Metres, from the eye to the centre of mass. Everything that is fired or thrown.</summary>
    Ranged,

    /// <summary>One traversal away. Not a distance at all — the graph decides.</summary>
    Adjacent,
}

/// <summary>
/// A weapon, as data. Content and balance, not rules.
/// </summary>
/// <param name="Damage">Damage a single round does before anything stops it.</param>
/// <param name="OptimalRange">Metres out to which the weapon is at its best.</param>
/// <param name="MaxRange">Metres beyond which it cannot be fired at all.</param>
/// <param name="Accuracy">Chance to hit a fully exposed target at optimal range, before modes.</param>
/// <param name="Loudness">
/// Noise a shot makes, in the same units movement uses. Kinetic weapons are loud and heard
/// through walls; beams make no sound at all.
/// </param>
/// <param name="Flash">
/// Visual signature. A beam draws a line back to the shooter for anyone looking that way; a
/// slugthrower shows a muzzle flash and little else.
/// </param>
/// <param name="Reach">
/// Which instrument settles whether the weapon can reach. Metres for everything that is fired;
/// adjacency for a blade, whose ranges below are then descriptive rather than load-bearing.
/// </param>
public sealed record WeaponProfile(
    string Id,
    string Name,
    DamageKind Kind,
    int Damage,
    double OptimalRange,
    double MaxRange,
    double Accuracy,
    IReadOnlyList<FireMode> Modes,
    double Loudness,
    double Flash,
    WeaponReach Reach = WeaponReach.Ranged)
{
    /// <summary>
    /// Whether a target that far away is one this weapon could reach, as far as metres can say.
    /// </summary>
    /// <remarks>
    /// An adjacency weapon always passes here, because metres are the wrong instrument for it and
    /// this is the only one available: the graph test that actually decides lives on
    /// <see cref="Battles.Battle.InReach"/>, which has the map to hand. Anything asking this
    /// question about a blade without going through the battle is asking the wrong question.
    /// </remarks>
    public bool Reaches(double metres) => Reach == WeaponReach.Adjacent || metres <= MaxRange;

    /// <summary>The mode used when the caller does not name one.</summary>
    public FireMode DefaultMode => Modes.FirstOrDefault(m => m.Name == "standard") ?? Modes[0];

    public FireMode? Mode(string name) => Modes.FirstOrDefault(m => m.Name == name);

    /// <summary>The cheapest way to get a round off, which is what a reaction usually wants.</summary>
    public FireMode QuickestMode => Modes.OrderBy(m => m.ApCost).First();

    private static readonly IReadOnlyList<FireMode> Rifle = [FireMode.Snap, FireMode.Standard, FireMode.Aimed];

    /// <summary>Standard issue beam weapon. Silent, and unmissable to anyone facing your way.</summary>
    public static readonly WeaponProfile PulseCarbine = new(
        Id: "pulse_carbine",
        Name: "Pulse carbine",
        Kind: DamageKind.Beam,
        Damage: 8,
        OptimalRange: 14,
        MaxRange: 42,
        Accuracy: 0.86,
        Modes: Rifle,
        Loudness: 0,
        Flash: 1.0);

    /// <summary>Slugthrower. Hits harder and further, and tells the whole compound about it.</summary>
    public static readonly WeaponProfile SlugRifle = new(
        Id: "slug_rifle",
        Name: "Slug rifle",
        Kind: DamageKind.Kinetic,
        Damage: 11,
        OptimalRange: 20,
        MaxRange: 55,
        Accuracy: 0.80,
        Modes: Rifle,
        Loudness: 45,
        Flash: 0.2);

    /// <summary>Kinetic repeater. Three rounds a burst, none of them well aimed.</summary>
    public static readonly WeaponProfile Repeater = new(
        Id: "repeater",
        Name: "Repeater",
        Kind: DamageKind.Kinetic,
        Damage: 6,
        OptimalRange: 11,
        MaxRange: 30,
        Accuracy: 0.72,
        Modes: [FireMode.Snap, FireMode.Burst],
        Loudness: 65,
        Flash: 0.3);

    /// <summary>Beam sidearm. Cheap to fire, short reach, better than nothing.</summary>
    public static readonly WeaponProfile Sidearm = new(
        Id: "sidearm",
        Name: "Beam sidearm",
        Kind: DamageKind.Beam,
        Damage: 5,
        OptimalRange: 8,
        MaxRange: 20,
        Accuracy: 0.78,
        Modes: [FireMode.Snap, FireMode.Standard],
        Loudness: 0,
        Flash: 0.7);

    /// <summary>
    /// A powered blade. Beam family, so it goes straight through plate, and the only way to kill
    /// somebody without telling anyone — though a lit blade is not nothing to look at.
    /// </summary>
    /// <remarks>
    /// The two ranges are what an arm is, roughly, and nothing reads them: a blade reaches what
    /// is adjacent, and <see cref="WeaponReach.Adjacent"/> says why the metres had to go.
    /// </remarks>
    public static readonly WeaponProfile PowerBlade = new(
        Id: "power_blade",
        Name: "Power blade",
        Kind: DamageKind.Beam,
        Damage: 16,
        OptimalRange: 2.0,
        MaxRange: 2.0,
        Accuracy: 0.92,
        Modes: [FireMode.Strike],
        Loudness: 0,
        Flash: 0.25,
        Reach: WeaponReach.Adjacent);
}
