using System.Collections.Generic;
using System.Linq;


namespace Hexcom.Core.Combat;

/// <summary>What a unit carries into the fight.</summary>
/// <param name="ShieldPerFace">Force shield capacity on each of the six faces.</param>
/// <param name="ArmourPerFace">Ablative plate on each face. Does not come back.</param>
/// <param name="ShieldRecharge">Shield returned to every face at the start of the unit's turn.</param>
public sealed record Loadout(
    WeaponProfile Weapon,
    int ShieldPerFace = 0,
    int ArmourPerFace = 0,
    int ShieldRecharge = 2)
{
    public static readonly Loadout Rifleman = new(WeaponProfile.SlugRifle, ShieldPerFace: 6, ArmourPerFace: 8);

    public static readonly Loadout Beamer = new(WeaponProfile.PulseCarbine, ShieldPerFace: 10, ArmourPerFace: 3);

    public static readonly Loadout Heavy = new(WeaponProfile.Repeater, ShieldPerFace: 8, ArmourPerFace: 14, ShieldRecharge: 1);

    public static readonly Loadout Infiltrator = new(WeaponProfile.PowerBlade, ShieldPerFace: 4, ArmourPerFace: 2, ShieldRecharge: 3);

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

        // Away from zero, not the default banker's rounding: half a point of damage going
        // one way on even numbers and the other on odd is not something to explain to a player.
        var byShield = Math.Min(_shield[index], Round(damage * Mitigation.ShieldAgainst(kind)));
        _shield[index] -= byShield;
        var through = damage - byShield;

        var byArmour = Math.Min(_armour[index], Round(through * Mitigation.ArmourAgainst(kind)));
        _armour[index] -= byArmour;
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
