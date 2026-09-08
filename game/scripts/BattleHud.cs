using System.Linq;
using Godot;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Game;

/// <summary>
/// The readouts: turn order, the active soldier's situation, what the shot under the cursor
/// would cost, and what the last reaction window did.
/// </summary>
/// <remarks>
/// <para>
/// Interface rather than presentation — the distinction <c>docs/subprojects/view.md</c> draws.
/// <see cref="BattleView"/> consumes the rules; this class <i>constrains</i> them, because the
/// build order's standing rule is that if the AI needs information the interface cannot show,
/// the interface is wrong. Every line here is therefore a claim about what a player is entitled
/// to know, and adding one is a design decision rather than a formatting one.
/// </para>
/// <para>
/// Contract 3 in <c>docs/map.md</c> is the rule this file has to keep: a unit's own exposure is
/// reported exactly, because that is information about yourself, while what the enemy has worked
/// out is reported as a rung on a ladder and never as a number. Both appear below, and the
/// asymmetry between them is deliberate. Do not "improve" the coarse one.
/// </para>
/// </remarks>
public sealed class BattleHud(CanvasItem canvas, Font font)
{
    private readonly CanvasItem _canvas = canvas;
    private readonly Font _font = font;

    /// <summary>Where the panels hang, given the node's own offset. Screen space, not canvas space.</summary>
    public Vector2 Origin { get; set; }

    public void Draw(SandboxFrame frame, Vector2 viewport)
    {
        DrawOrderStrip(frame, viewport);
        DrawLines(frame);
    }

    /// <summary>The next few bookings, so the player can see the interleaving coming.</summary>
    private void DrawOrderStrip(SandboxFrame frame, Vector2 viewport)
    {
        var origin = Origin + new Vector2(viewport.X - 190, 26);
        _canvas.DrawString(_font, origin, "TURN ORDER", HorizontalAlignment.Left, -1, 11, SandboxPalette.TextDim);

        var slots = frame.Battle.TurnOrder.Take(6).ToList();
        for (var i = 0; i < slots.Count; i++)
        {
            var unit = frame.Battle.GetUnit(slots[i].Unit);
            if (unit is null) continue;

            var box = new Rect2(origin + new Vector2(0, 12 + i * 26), new Vector2(170, 22));
            _canvas.DrawRect(box, SandboxPalette.Panel);
            _canvas.DrawRect(new Rect2(box.Position, new Vector2(4, box.Size.Y)), SandboxPalette.SideHue(unit.Side));
            _canvas.DrawString(_font, box.Position + new Vector2(12, 16), unit.Name,
                HorizontalAlignment.Left, -1, 13, SandboxPalette.TextBright);
            _canvas.DrawString(_font, box.Position + new Vector2(120, 16), $"init {slots[i].Roll}",
                HorizontalAlignment.Left, -1, 11, SandboxPalette.TextDim);

            // What this one could still answer a move with, and whether it is holding an arc.
            if (unit.Reserve > 0)
                _canvas.DrawString(_font, box.Position + new Vector2(80, 16),
                    unit.Overwatch is { } held ? $"{unit.Reserve}▸{held.Arc.Name[..1]}" : $"{unit.Reserve}•",
                    HorizontalAlignment.Left, -1, 11, SandboxPalette.OverwatchHue);
        }
    }

    private void DrawLines(SandboxFrame frame)
    {
        var battle = frame.Battle;
        var active = battle.Active;

        var lines = new[]
        {
            active is null
                ? $"round {battle.Round}    nobody left to act"
                : $"round {battle.Round}    {active.Name} ({active.Side})    "
                  + $"{active.ActionPoints}/{active.Stats.ActionPoints} AP    "
                  + $"{active.Stance.ToString().ToLowerInvariant()}    facing {active.Facing}    layer {frame.Layer}",
            active is null
                ? ""
                : $"exposed {battle.ExposureOf(active):P0}    "
                  + $"they are: {battle.HighestAwarenessOf(active).ToString().ToUpperInvariant()}",
            active is null ? "" : ReserveLine(frame, active),
            frame.Hover is { } h
                ? $"cursor {h}    {(frame.Reach.CostTo(h) is { } c ? $"{c} AP" : "out of reach")}    {SightLine(frame, h)}"
                : "cursor —",
            ShotLine(frame),
            frame.LastWindow,
            "left-click: move    right-click: fire    space: end turn    C: stance    Z/X: turn    "
            + "V: overwatch arc    B: arm/spring ambush    Q/E: layer    R: new battle",
        }.Where(line => line.Length > 0).ToArray();

        var top = Origin + new Vector2(18, 30);
        for (var i = 0; i < lines.Length; i++)
            _canvas.DrawString(_font, top + new Vector2(0, i * 20), lines[i],
                HorizontalAlignment.Left, -1, 14,
                i == lines.Length - 1 ? SandboxPalette.TextDim : SandboxPalette.TextBright);
    }

    /// <summary>
    /// What ending the turn now would leave this unit to answer other people's moves with, and
    /// what it is holding. The reserve is the whole reason to stop moving early.
    /// </summary>
    private static string ReserveLine(SandboxFrame frame, Unit active)
    {
        var model = frame.Battle.Reactions;
        var would = (int)(active.ActionPoints * model.ReserveFraction);
        if (would < model.ReserveFloor) would = 0;

        var holding = active.Overwatch is { } order
            ? $"holding a {order.Arc.Name} arc {order.Centre} (x{order.Arc.AimBonus:0.00} to hit)"
            : "watching nothing in particular";

        return $"reserve {active.Reserve}, {would} if you stop here    {holding}";
    }

    /// <summary>The shot the active unit would take at whoever is under the cursor.</summary>
    private static string ShotLine(SandboxFrame frame)
    {
        if (frame.Battle.Active is not { } shooter) return "";
        if (HoveredUnit(frame) is not { } quarry || !quarry.IsHostileTo(shooter)) return "";

        var plan = frame.Battle.PlanShot(shooter, quarry);
        if (!plan.CanFire) return $"shot at {quarry.Name}: {plan.Refusal}";

        var armour = plan.Target.Protection;

        // A body is a hexagon, so a shot is never at one plate. Show the spread and what each is
        // still carrying, because which side is worn is what turning is for.
        var faces = string.Join(", ", plan.Aspects.Select(a =>
            $"{a.Face} {a.Share:P0} (s{armour.ShieldOn(a.Face)}/p{armour.ArmourOn(a.Face)})"));

        var glancing = plan.GlancingFactor < 0.995
            ? $"    {plan.GlancingFactor:P0} of it lands"
            : "";

        // What this soldier pays, which is not always what the mode lists.
        var listed = plan.ApCost == plan.Mode.ApCost ? "" : $" (list {plan.Mode.ApCost})";

        return $"shot at {quarry.Name}: {plan.HitChance:P0} for {plan.ApCost} AP{listed}    "
               + $"{plan.Weapon.Name} ({plan.Weapon.Kind}){glancing}    "
               + faces
               + "    right-click to fire";
    }

    /// <summary>
    /// What the active unit can make out at the cursor, and what is protecting it.
    /// </summary>
    /// <remarks>
    /// The distance is quoted in metres straight from the sight trace, so it is also the
    /// cheapest way to tell whether the world scale is right: adjacent hexes should read
    /// 1.7 m apart, not 76. Until the two layouts were separated it read in pixels, which is how
    /// entry 002 in <c>docs/decisions.md</c> was found.
    /// </remarks>
    private static string SightLine(SandboxFrame frame, NodeId node)
    {
        if (!frame.View.TryGetValue(node, out var seen)) return "no sight data";
        if (!seen.CanSee) return $"hidden by {seen.Blocker?.Profile.Id ?? "terrain"}";

        var cover = seen.Cover == CoverGrade.None
            ? "in the open"
            : $"{seen.Cover.ToString().ToLowerInvariant()} cover behind {seen.CoverSource?.Profile.Id}";

        return $"{cover}    {seen.Exposure:P0} exposed    {seen.Distance:0.0} m";
    }

    private static Unit? HoveredUnit(SandboxFrame frame)
        => frame.Hover is { } node ? frame.Battle.UnitAt(node) : null;

    /// <summary>What a reaction window did, whether a move opened it or somebody sprang it.</summary>
    public static string Describe(MoveOutcome outcome) => Describe(outcome.Reactions);

    /// <summary>What a reaction window did, whether a move opened it or somebody sprang it.</summary>
    public static string Describe(ReactionWindow? window)
    {
        if (window is null) return "";
        if (window.Resolutions.Count == 0) return "";

        var answers = window.Resolutions.Select(r =>
        {
            var who = $"t{r.At} {r.Placement.Reactor.Name} ({r.Placement.Kind.ToString().ToLowerInvariant()})";

            if (r.Outcome is not { } shot)
                return r.Placement.Action switch
                {
                    ReactionAction.Turn => $"{who} spins to {r.Placement.Facing}",
                    ReactionAction.Drop => $"{who} goes {r.Placement.Stance}",
                    _ => $"{who} calls it in",
                };

            var landed = shot.Shots.FirstOrDefault(s => s.Hit)?.Damage;
            var where = landed is null
                ? ""
                : $" {landed.Face}{(landed.WasGlancing ? " glancing" : "")}";

            return $"{who} {r.Placement.Mode?.Name} at {r.Caught}: "
                   + (shot.AnyHit ? $"hit{where} for {shot.TotalDamage}" : "missed")
                   + (shot.TargetDown ? ", down" : "");
        });

        var heading = window.IsAmbush ? "ambush" : "reactions";
        return heading + " — " + string.Join("    ", answers);
    }
}
