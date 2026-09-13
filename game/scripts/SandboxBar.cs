using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Reactions;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Game;

/// <summary>One slot on the action bar, as the moment has it.</summary>
/// <param name="Id">What pressing it does, as <see cref="HexSandbox"/> dispatches it — <c>fire:snap</c>, <c>arc:narrow</c>, <c>end</c>.</param>
/// <param name="Group">Which run of slots it sits in, named over the run.</param>
/// <param name="Key">The key that presses it, as the keycap reads.</param>
/// <param name="Name">What it does, in a word or two.</param>
/// <param name="Price">What pressing it charges this soldier, or null for nothing.</param>
/// <param name="Affordable">Whether the soldier has the points.</param>
/// <param name="Reason">Why it would be refused for something other than points, or null.</param>
/// <param name="Lit">Whether it is the state the soldier is in: the fire mode being aimed, the arc held, the ambush armed.</param>
/// <param name="Hint">The one line pointing at it shows.</param>
public sealed record BarSlot(
    string Id,
    string Group,
    string Key,
    string Name,
    int? Price,
    bool Affordable,
    string? Reason,
    bool Lit,
    string Hint)
{
    /// <summary>Whether pressing it would do anything but say no.</summary>
    public bool Ready => Affordable && Reason is null;
}

/// <summary>
/// The action bar: a slot per thing the soldier whose go it is can do, each with its key and its
/// price, pressed by the key or by a click. Brief <c>view/action-bar</c>, entry 094 items 6, 9, 10
/// and 11.
/// </summary>
/// <remarks>
/// <para>
/// <b>Data here, drawing in <see cref="BattleHud"/>, pressing in <see cref="HexSandbox"/>.</b> The slots
/// are worked out once from the frame so that what a slot says and what pressing it does are asked of
/// the same answers — a slot drawn ready that the method then refuses is the bar lying.
/// </para>
/// <para>
/// <b>Every price is the one the rules will charge.</b> A fire mode is <c>Stats.Costs.Fire(mode.ApCost)</c>,
/// the figure <c>Battle.PlanShot</c> charges and the reserve ladder banks against, so the bar and the
/// ladder cannot disagree. The rest mirror what each <c>Battle</c> method takes off the soldier — the
/// posture keys through <c>Costs.Posturing</c>, an arc and an ambush at the flat
/// <see cref="ReactionModel"/> figures, declared along the facing so no turn is added. Core has no
/// <i>price of this action</i> query to ask instead; if one lands, these become calls to it.
/// </para>
/// <para>
/// <b>Unaffordable is dimmed with its price, and refused for another reason says the reason.</b> A
/// snap at 15 on a soldier with 9 answers the play-through's <i>how do I take a snap shot</i> without a
/// word of help text. The two are kept apart because they want different things of the player: points
/// are this turn gone, and a reason is usually something to change.
/// </para>
/// </remarks>
public static class ActionBar
{
    /// <summary>The number keys the fire modes take, cheapest first.</summary>
    public static readonly string[] FireKeys = ["1", "2", "3"];

    /// <summary>The number keys the three arcs take, narrowest first.</summary>
    public static readonly string[] ArcKeys = ["4", "5", "6"];

    /// <summary>
    /// The slots for the moment, or none when there is nothing a player may order: nobody up, a
    /// window open, or a hostile up under the AI.
    /// </summary>
    /// <remarks>
    /// <b>Empty while a window is open, not dimmed.</b> Inside a window the numbers are its answers,
    /// and a bar still showing keycaps <c>1</c> to <c>6</c> would be two meanings on one key drawn side
    /// by side. And empty while <see cref="SandboxFrame.Withheld"/>, since the hostile's options and
    /// their prices are its situation.
    /// </remarks>
    public static IReadOnlyList<BarSlot> Of(SandboxFrame frame)
    {
        if (frame.Open is not null || frame.Withheld || frame.OutOfTime) return [];
        if (frame.Battle.Active is not { } active || !frame.Battle.IsRunning) return [];

        var battle = frame.Battle;
        var slots = new List<BarSlot>();
        var points = active.ActionPoints;

        // ---- fire, cheapest first, which is the order the ladder over the soldier reads in
        var aim = frame.Aim;
        var modes = active.Weapon.Modes.OrderBy(mode => mode.ApCost).Take(FireKeys.Length).ToList();
        for (var i = 0; i < modes.Count; i++)
        {
            var mode = modes[i];
            var price = active.Stats.Costs.Fire(mode.ApCost);
            var lit = aim is not null && frame.Mode == mode;

            string? reason = null;
            if (aim is not null)
            {
                var plan = battle.PlanShot(active, aim, mode);
                if (points >= price && plan.Refusal is { } no) reason = no.TrimEnd('.');
            }
            else if (frame.Targets.Count == 0) reason = "nobody in sight";

            var rounds = mode.Shots > 1 ? $", {mode.Shots} rounds" : "";
            var hint = reason is not null ? $"{mode.Name}{rounds}: {reason}"
                : points < price ? $"{mode.Name}{rounds}: needs {price} points, {active.Name} has {points}"
                : lit ? $"{mode.Name}{rounds}: space or a second click on {aim!.Name} fires; press again to back out"
                : aim is not null ? $"{mode.Name}{rounds}: aim this at {aim.Name} instead"
                : $"{mode.Name}{rounds}: point it at a hostile — the one under the cursor or the nearest — then confirm";

            slots.Add(new BarSlot($"fire:{mode.Name}", "FIRE", FireKeys[i], mode.Name, price, points >= price, reason, lit, hint));
        }

        // ---- the arcs, as three slots rather than one that cycles: V cycled four states at a
        // point each with nothing saying which had landed, which is item 6.
        var arcPrice = battle.Reactions.OverwatchCost;
        for (var i = 0; i < OverwatchArc.All.Count; i++)
        {
            var arc = OverwatchArc.All[i];
            var held = active.Overwatch?.Arc == arc;
            var hint = held
                ? $"holding a {arc.Name} arc — press again to stop watching, which refunds nothing"
                : $"hold a {arc.Name} arc, {arc.Degrees:0}° about the way {active.Name} faces — what is left at the end of the go is what it shoots with";

            slots.Add(new BarSlot($"arc:{arc.Name}", "OVERWATCH", ArcKeys[i], arc.Name,
                held ? null : arcPrice, held || points >= arcPrice, null, held, hint));
        }

        // ---- posture: the body shows the stance and the facing, so one slot per key and each named
        // for what it does next rather than for the state it is in.
        var next = NextStance(active.Stance);
        var stancePrice = active.Stats.Costs.Posturing(battle.Costs.ChangeStance);
        slots.Add(new BarSlot("stance", "POSTURE", "C", StanceVerb(next), stancePrice, points >= stancePrice, null, false,
            $"go {next.ToString().ToLowerInvariant()}"));

        var turnPrice = active.Stats.Costs.Posturing(battle.Costs.TurnInPlace);
        slots.Add(new BarSlot("turn:left", "POSTURE", "Z", "turn left", turnPrice, points >= turnPrice, null, false,
            $"face {active.Facing.Rotate(1)}, on the spot"));
        slots.Add(new BarSlot("turn:right", "POSTURE", "X", "turn right", turnPrice, points >= turnPrice, null, false,
            $"face {active.Facing.Rotate(-1)}, on the spot"));

        // ---- the squad: an ambush, and a shout
        var prey = aim ?? (frame.HoveredUnit is { } hovered && hovered.IsHostileTo(active) ? hovered : null);
        if (active.Ambush is null)
        {
            var armPrice = battle.Reactions.AmbushCost;
            slots.Add(new BarSlot("ambush", "SQUAD", "B", "arm", armPrice, points >= armPrice, null, false,
                "arm an ambush on a standard arc — when one of you springs it, everybody armed fires in the same moment"));
        }
        else
        {
            slots.Add(new BarSlot("ambush", "SQUAD", "B", "spring", null, true, prey is null ? "aim first" : null, true,
                prey is null
                    ? "armed — aim at a hostile, then spring it on them"
                    : $"spring the ambush on {prey.Name}: everybody armed who can see them fires before they act"));
        }

        var about = ShoutSubject(frame, active);
        var shoutPrice = active.Stats.Costs.Posturing(battle.Costs.Shout);
        slots.Add(new BarSlot("shout", "SQUAD", "L", "call it in", shoutPrice, points >= shoutPrice,
            about is null ? "no contact" : null, false,
            about is null ? "nobody to call in — this soldier is taking nobody seriously" : $"call {frame.Names([about])} in to everybody who can hear"));

        // ---- the go itself
        var exit = battle.ObjectiveOf(active.Side) is Sortie sortie && sortie.IsExit(active.Position);
        slots.Add(new BarSlot("leave", "TURN", "T", "leave", null, true, exit ? null : "not an exit", false,
            exit ? $"walk {active.Name} off the field from here" : "only from the way out"));

        slots.Add(new BarSlot("end", "TURN", "Bksp", "end turn", null, true, null, false,
            $"end {active.Name}'s go — whatever is left over banks for reacting"));

        return slots;
    }

    /// <summary>Who <c>L</c> calls in: the aim, else the hostile under the cursor, else the contact the soldier takes most seriously.</summary>
    public static Unit? ShoutSubject(SandboxFrame frame, Unit active)
        => frame.Aim
           ?? (frame.HoveredUnit is { } hovered && hovered.IsHostileTo(active) ? hovered : null)
           ?? frame.Battle.Tactics.Known(active).Select(threat => threat.Unit).FirstOrDefault();

    /// <summary>The stance <c>C</c> goes to from this one.</summary>
    public static Stance NextStance(Stance stance) => stance switch
    {
        Stance.Standing => Stance.Crouching,
        Stance.Crouching => Stance.Prone,
        _ => Stance.Standing,
    };

    private static string StanceVerb(Stance stance) => stance switch
    {
        Stance.Crouching => "crouch",
        Stance.Prone => "go prone",
        _ => "stand",
    };
}
