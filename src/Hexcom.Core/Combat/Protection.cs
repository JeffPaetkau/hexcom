using System.Collections.Generic;
using System.Linq;


namespace Hexcom.Core.Combat;

/// <summary>What a unit carries into the fight.</summary>
/// <param name="ShieldPerFace">Force shield capacity on each of the six faces.</param>
/// <param name="ArmourPerFace">Ablative plate on each face. Does not come back.</param>
/// <param name="ShieldRecharge">Shield returned to every face at the start of the unit's turn.</param>
/// <param name="Thrown">
/// The charge this soldier carries, if any. One kind: a soldier picking between a frag and a
/// plasma charge mid-firefight is a decision nothing in the game is ready to present.
/// </param>
/// <param name="Charges">
/// How many of them. Counted rather than assumed infinite, and that is load-bearing on the AI
/// rather than on realism — a commander that could throw every turn would, because a grenade
/// beats a rifle against anybody in cover, and the whole shape of a firefight would change.
/// Two is a soldier stock: enough that one is worth spending and not enough to lead with.
/// </param>
public sealed record Loadout(
    WeaponProfile Weapon,
    int ShieldPerFace = 0,
    int ArmourPerFace = 0,
    int ShieldRecharge = 2,
    ThrownProfile? Thrown = null,
    int Charges = 0)
{
    public static readonly Loadout Rifleman = new(
        WeaponProfile.SlugRifle, ShieldPerFace: 6, ArmourPerFace: 8,
        Thrown: ThrownProfile.FragGrenade, Charges: 2);

    /// <summary>Beams and a shaped charge: the whole kit is the answer to armour.</summary>
    public static readonly Loadout Beamer = new(
        WeaponProfile.PulseCarbine, ShieldPerFace: 10, ArmourPerFace: 3,
        Thrown: ThrownProfile.PlasmaCharge, Charges: 1);

    public static readonly Loadout Heavy = new(
        WeaponProfile.Repeater, ShieldPerFace: 8, ArmourPerFace: 14, ShieldRecharge: 1,
        Thrown: ThrownProfile.FragGrenade, Charges: 1);

    /// <summary>
    /// A blade and a satchel of mines. Nothing here makes a noise until it is meant to.
    /// </summary>
    public static readonly Loadout Infiltrator = new(
        WeaponProfile.PowerBlade, ShieldPerFace: 4, ArmourPerFace: 2, ShieldRecharge: 3,
        Thrown: ThrownProfile.Claymore, Charges: 2);

    public static readonly Loadout Sidearm = new(WeaponProfile.Sidearm, ShieldPerFace: 5, ArmourPerFace: 4);
}

/// <summary>How much of a hit each layer stops, by what hit it.</summary>
public static class Mitigation
{
    /// <summary>Shields are what beams are for. A solid object at speed barely notices them.</summary>
    public static double ShieldAgainst(DamageKind kind) => kind == DamageKind.Beam ? 1.00 : 0.15;

    /// <summary>Plate stops rounds. Under a sustained beam it simply cooks.</summary>
    public static double ArmourAgainst(DamageKind kind) => kind == DamageKind.Kinetic ? 1.00 : 0.25;
}

/// <summary>
/// A unit's shields and plate, tracked per face.
/// </summary>
/// <remarks>
/// Per face rather than as one pool, so flanking matters for damage as much as it does for
/// detection — the same walk round the back that buys an unnoticed approach also buys the thin
/// side of the armour. The two layers wear differently on purpose: shields recharge, so turning
/// a spent face away from the threat is a combat decision and not just a looking one, while
/// plate does not, so a unit slowly runs out of good sides to present.
/// </remarks>
public sealed class Protection
{
    private readonly int[] _shield = new int[6];
    private readonly int[] _armour = new int[6];

    public Protection(Loadout loadout)
    {
        Loadout = loadout;
        ShieldPerFace = loadout.ShieldPerFace;
        ArmourPerFace = loadout.ArmourPerFace;

        for (var i = 0; i < 6; i++)
        {
            _shield[i] = loadout.ShieldPerFace;
            _armour[i] = loadout.ArmourPerFace;
        }
    }

    public Loadout Loadout { get; }
    public int ShieldPerFace { get; }
    public int ArmourPerFace { get; }

    public int ShieldOn(BodyFace face) => _shield[(int)face];
    public int ArmourOn(BodyFace face) => _armour[(int)face];

    /// <summary>Shield left across all faces, for a summary readout.</summary>
    public int TotalShield => _shield.Sum();

    /// <summary>Plate left across all faces. Only ever goes down.</summary>
    public int TotalArmour => _armour.Sum();

    /// <summary>Faces with nothing left to stop a beam.</summary>
    public IEnumerable<BodyFace> BareFaces
        => BodyFaces.All.Where(d => ShieldOn(d) == 0);

    /// <summary>Bring every face back up, at the loadout rate. Called as a unit's turn starts.</summary>
    public void Recharge()
    {
        for (var i = 0; i < 6; i++)
            _shield[i] = Math.Min(ShieldPerFace, _shield[i] + Loadout.ShieldRecharge);
    }

    /// <summary>
    /// Put a hit through the layers on one face and report what got past.
    /// </summary>
    /// <remarks>
    /// Shields first, then plate, then flesh. Each layer stops only what it is good against, so
    /// the same eleven points of damage lands very differently depending on what threw it. Plate
    /// ablates as it works; shields deplete and will come back.
    /// </remarks>
    public DamageTaken Absorb(BodyFace face, DamageKind kind, int damage, double obliquityDegrees = 0)
    {
        var index = (int)face;
        return Through(ref _shield[index], ref _armour[index], face, kind, damage, obliquityDegrees);
    }

    /// <summary>
    /// What a run of identical hits on one face would get through, if every one of them landed.
    /// Changes nothing.
    /// </summary>
    /// <remarks>
    /// The question anyone weighing a shot has to ask, and it cannot be answered a round at a
    /// time: layers wear as they work, so the first round of a burst into a fresh face is stopped
    /// almost entirely and the second walks through the hole the first made. A model that priced
    /// every round against untouched plate would rate a burst at three times nothing.
    /// <para>
    /// Public because the interface needs it as much as the AI does — a player looking at a
    /// shielded target should be able to see that their beam will be soaked, rather than firing
    /// to find out. It is the same question, so it is the same query.
    /// </para>
    /// </remarks>
    public IReadOnlyList<DamageTaken> Preview(
        BodyFace face, DamageKind kind, int damage, int rounds, double obliquityDegrees = 0)
    {
        var shield = ShieldOn(face);
        var armour = ArmourOn(face);
        var run = new List<DamageTaken>(rounds);

        for (var i = 0; i < rounds; i++)
            run.Add(Through(ref shield, ref armour, face, kind, damage, obliquityDegrees));

        return run;
    }

    /// <summary>
    /// One hit through the two layers, wearing them as it goes. The arithmetic that
    /// <see cref="Absorb"/> and <see cref="Preview"/> share, so a forecast cannot drift from
    /// what actually happens.
    /// </summary>
    private static DamageTaken Through(
        ref int shield, ref int armour, BodyFace face, DamageKind kind, int damage, double obliquityDegrees)
    {
        // Away from zero, not the default banker's rounding: half a point of damage going
        // one way on even numbers and the other on odd is not something to explain to a player.
        var byShield = Math.Min(shield, Round(damage * Mitigation.ShieldAgainst(kind)));
        shield -= byShield;
        var through = damage - byShield;

        var byArmour = Math.Min(armour, Round(through * Mitigation.ArmourAgainst(kind)));
        armour -= byArmour;
        through -= byArmour;

        return new DamageTaken(face, kind, damage, byShield, byArmour, Math.Max(0, through), obliquityDegrees);
    }

    private static int Round(double value) => (int)Math.Round(value, MidpointRounding.AwayFromZero);
}

/// <summary>What one hit did on the way in.</summary>
/// <param name="Face">Which of the soldier's own sides took it.</param>
/// <param name="Incoming">
/// Damage arriving at the plate. A kinetic round that came in at an angle has already been
/// docked for skipping off, so this can be less than the weapon does.
/// </param>
/// <param name="StoppedByShield">Soaked by the force shield, which will recharge.</param>
/// <param name="StoppedByArmour">Soaked by plate, which ablated doing it.</param>
/// <param name="ToVitality">What reached the soldier.</param>
/// <param name="ObliquityDegrees">How far off square it arrived, for the readout.</param>
public sealed record DamageTaken(
    BodyFace Face,
    DamageKind Kind,
    int Incoming,
    int StoppedByShield,
    int StoppedByArmour,
    int ToVitality,
    double ObliquityDegrees = 0)
{
    public bool WasStopped => ToVitality == 0;

    /// <summary>Whether this one came in at enough of an angle to be worth mentioning.</summary>
    public bool WasGlancing => ObliquityDegrees >= BodyFaces.DegreesPerFace / 2;
}
