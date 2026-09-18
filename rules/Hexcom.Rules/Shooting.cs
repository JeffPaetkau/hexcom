using System;

namespace Hexcom.Rules;

/// <summary>
/// Simple shooting: one soldier fires one round at another, the distance says how likely it
/// is to land, and a hit takes a fixed bite out of the target. Full awareness and no cover,
/// because sight and fog of war come later and the interface for a shot comes first.
/// </summary>
/// <remarks>
/// The rules never throw the dice. A shot is planned so the interface can show what it would
/// cost and how likely it is, and fired with a roll handed in, so a run of the game can be
/// replayed from a seed and a picture of a hit can be taken without luck.
/// </remarks>
public static class Shooting
{
    /// <summary>Metres between two hexes, centre to centre across the ground plane.</summary>
    /// <remarks>
    /// Across the plane rather than through the air: a rise of three metres over twenty adds
    /// a fifth of a metre, less than the width of the soldier, and keeps the question free of
    /// the ground so a test can ask it of any two hexes.
    /// </remarks>
    public static double Range(Hex from, Hex to)
    {
        var (x0, z0) = from.Centre;
        var (x1, z1) = to.Centre;
        return Math.Sqrt((x1 - x0) * (x1 - x0) + (z1 - z0) * (z1 - z0));
    }

    /// <summary>What a shot from one soldier at another would be: its range, chance, cost and damage, or why it is refused.</summary>
    /// <param name="seen">Whether the shooter can see the target; a soldier fires only at what they themselves see.</param>
    public static Shot Plan(Unit shooter, Unit target, bool seen = true)
    {
        var weapon = shooter.Weapon;
        var range = Range(shooter.Position, target.Position);

        // The refusals come in the order a player would want to hear them: nothing about the
        // gun matters if there is nothing to shoot at.
        string? refusal = null;
        if (shooter.IsDown) refusal = "DOWN";
        else if (target.IsDown) refusal = "TARGET DOWN";
        else if (shooter.Side == target.Side) refusal = "FRIENDLY";
        else if (!seen) refusal = "NOT IN SIGHT";
        else if (!weapon.Reaches(range)) refusal = "OUT OF RANGE";
        else if (shooter.Rounds <= 0) refusal = "NO ROUNDS";
        else if (!shooter.CanAfford(weapon.ShotCost)) refusal = "NOT ENOUGH POINTS";

        return new Shot(range, weapon.HitChance(range), weapon.ShotCost, weapon.Damage, refusal);
    }

    /// <summary>
    /// Fire: pay for the shot, spend the round, and hit if the roll comes under the chance.
    /// Null if the shot is refused, and nothing is spent.
    /// </summary>
    /// <param name="roll">A throw of the dice from zero up to one.</param>
    public static ShotResult? Fire(Unit shooter, Unit target, double roll, bool seen = true)
    {
        var shot = Plan(shooter, target, seen);
        if (!shot.CanFire) return null;

        shooter.Spend(shot.Cost);
        shooter.SpendRound();

        // A soldier faces what they fire at. The turn is inside the shot's price: three and a
        // half seconds is time enough to come round and aim, and a shot that also charged for
        // the turn would make firing at what is beside you dearer than at what is in front.
        shooter.Facing = Facing.Toward(shooter.Position, target.Position) ?? shooter.Facing;

        var hit = roll < shot.HitChance;
        if (hit) target.Hurt(shot.Damage);

        return new ShotResult(hit, hit ? shot.Damage : 0, target.IsDown);
    }
}

/// <summary>A shot worked out before anyone commits to it.</summary>
/// <param name="Range">Metres to the target.</param>
/// <param name="HitChance">From zero to one; zero when out of range.</param>
/// <param name="Cost">Action points the shot would take.</param>
/// <param name="Damage">Hit points a hit would take off.</param>
/// <param name="Refusal">Why the shot cannot be taken, in words fit to show a player, or null.</param>
public sealed record Shot(double Range, double HitChance, int Cost, int Damage, string? Refusal)
{
    public bool CanFire => Refusal is null;
}

/// <summary>What one round did.</summary>
public readonly record struct ShotResult(bool Hit, int Damage, bool TargetDown);
