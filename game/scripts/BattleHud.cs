using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
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
        DrawHappenings(frame, viewport);
        DrawLegend(viewport);
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

    /// <summary>Point size every readout is set in, and the step between two of them.</summary>
    private const int LineSize = 14;
    private const int LineHeight = 20;

    private void DrawLines(SandboxFrame frame)
    {
        var battle = frame.Battle;
        var active = battle.Active;

        var hostiles = frame.HostilesAutomatic ? "hostiles: AI" : "hostiles: by hand";

        var lines = new List<string>
        {
            active is null
                ? $"round {battle.Round}    nobody left to act    {hostiles}"
                : $"round {battle.Round}    {active.Name} ({active.Side})    "
                  + $"{active.ActionPoints}/{active.Stats.ActionPoints} AP    "
                  + $"{active.Stance.ToString().ToLowerInvariant()}    facing {active.Facing}    layer {frame.Layer}    "
                  + $"{WeaponLine(active)}    {hostiles}",
            active is null ? "" : AlarmLine(frame, active),
            active is null ? "" : SeenLine(frame, active),
            active is null ? "" : ReserveLine(frame, active),
            active is null ? "" : PostureLine(frame, active),
            frame.Hover is { } h
                ? $"cursor {h}    {(frame.Reach.CostTo(h) is { } c ? $"{c} AP" : "out of reach")}    "
                  + $"{SightLine(frame, h)}{AttentionLine(frame, h)}"
                : "cursor —",
            ShotLine(frame),
            WorthLine(frame),
        };
        lines.RemoveAll(line => line.Length == 0);

        var top = Origin + new Vector2(18, 30);
        Panel(top, lines);

        for (var i = 0; i < lines.Count; i++)
            _canvas.DrawString(_font, top + new Vector2(0, i * LineHeight), lines[i],
                HorizontalAlignment.Left, -1, LineSize, SandboxPalette.TextBright);
    }

    /// <summary>
    /// What happened while it was not your go: the last reaction window, and every turn the AI
    /// has taken since you last did anything.
    /// </summary>
    /// <remarks>
    /// A block of its own, along the bottom edge above the legend, rather than more lines on the
    /// block at the top. The top block is the active soldier's situation and grows with what is
    /// under the cursor; this one is a record of other people's turns and grows with how many
    /// of them there were. Stacked together they reached a third of the way down the screen and
    /// sat squarely on the roof, which is where the demo's most interesting soldier stands. The
    /// bottom rows of the map are open ground with cost labels on them, and cost labels are the
    /// cheapest thing on the screen to cover.
    /// </remarks>
    private void DrawHappenings(SandboxFrame frame, Vector2 viewport)
    {
        var lines = new List<string> { frame.LastWindow };
        lines.AddRange(TurnLines(frame));
        lines.RemoveAll(line => line.Length == 0);
        if (lines.Count == 0) return;

        var top = Origin + new Vector2(18, viewport.Y - 22 - LineHeight - 14 - (lines.Count - 1) * LineHeight);
        Panel(top, lines);

        for (var i = 0; i < lines.Count; i++)
            _canvas.DrawString(_font, top + new Vector2(0, i * LineHeight), lines[i],
                HorizontalAlignment.Left, -1, LineSize, SandboxPalette.TextBright);
    }

    /// <summary>
    /// The keys, parked along the bottom edge where there is nothing else to read.
    /// </summary>
    /// <remarks>
    /// It used to be the last line of the status block, which put it straight through the top
    /// row of tile-cost labels: both were legible on their own and neither was legible together,
    /// in every capture anyone has ever taken. Moving it costs nothing — a legend is the one
    /// readout that never changes and so never needs to be near anything.
    /// </remarks>
    private void DrawLegend(Vector2 viewport)
    {
        const string keys =
            "left-click: move    right-click: fire    space: end turn    C: stance    Z/X: turn    "
            + "V: overwatch arc    B: arm/spring ambush    Q/E: layer    A: AI takes this turn    "
            + "H: hostiles to AI    R: new battle";

        var at = Origin + new Vector2(18, viewport.Y - 22);
        Panel(at, [keys]);
        _canvas.DrawString(_font, at, keys, HorizontalAlignment.Left, -1, LineSize, SandboxPalette.TextDim);
    }

    /// <summary>
    /// A backing plate under a run of lines, sized to the widest of them.
    /// </summary>
    /// <remarks>
    /// The readouts sit over the map rather than beside it, so without this they are drawn on
    /// top of whatever the map happens to have there — which for the top block is the tile-cost
    /// labels, and the two together were unreadable in every capture anyone ever took.
    /// <para>
    /// It is <see cref="SandboxPalette.Panel"/>, the same plate the turn-order strip is on, so
    /// the two blocks read as the same furniture. Nearly opaque rather than fully: the map still
    /// shows through faintly, which is enough to say the panel is floating over the world and
    /// not a hole cut in it, and nowhere near enough to compete with the text.
    /// </para>
    /// </remarks>
    private void Panel(Vector2 top, IReadOnlyList<string> lines)
    {
        var widest = 0f;
        foreach (var line in lines)
            widest = Mathf.Max(widest, _font.GetStringSize(line, HorizontalAlignment.Left, -1, LineSize).X);

        _canvas.DrawRect(
            new Rect2(
                top + new Vector2(-10, -LineSize - 2),
                new Vector2(widest + 20, lines.Count * LineHeight + 10)),
            SandboxPalette.Panel);
    }

    /// <summary>
    /// How exposed this soldier is, and how alarmed the other side has become about them.
    /// </summary>
    /// <remarks>
    /// The two halves of contract 3 in <c>docs/map.md</c>, side by side, which is the clearest
    /// place to see what the asymmetry actually is. Exposure is our own soldier's silhouette and
    /// is quoted to the percent; the alarm is what the enemy has worked out and is quoted as a
    /// rung, never as the certainty behind it.
    /// <para>
    /// The bar is named because a rung on its own does not say what it means. <c>SEARCHING</c>
    /// is not a mood: it is the point at which <see cref="Hexcom.Core.Tactics.UtilityModel.ActsOn"/>
    /// says a soldier who could shoot at you will. A player who cannot see where that line falls
    /// is reading the one number this screen shows about the enemy without being told what it
    /// is for.
    /// </para>
    /// </remarks>
    private static string AlarmLine(SandboxFrame frame, Unit active)
    {
        var bar = frame.Battle.Tactics.Model.ActsOn;

        return $"exposed {frame.Battle.ExposureOf(active):P0}    "
               + $"they are: {frame.Battle.HighestAwarenessOf(active).ToString().ToUpperInvariant()}    "
               + $"(they act from {bar.ToString().ToUpperInvariant()})";
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

    /// <summary>
    /// How much of the active soldier's attention the place under the cursor has.
    /// </summary>
    /// <remarks>
    /// Our own soldier's attention, so contract 3 says it is reported exactly. The watch cone on
    /// the map answers this as a yes or a no; the model does not — a place is attended to fully,
    /// at the corner of the eye, or barely, and the difference between the last two is what makes
    /// a flank worth walking. Entry 006 in <c>docs/decisions.md</c> blocks drawing the cone at
    /// its true reach until the ranges and the map agree; it does not block quoting the figure,
    /// which is the half of the gap that was never gated on anything.
    /// </remarks>
    private static string AttentionLine(SandboxFrame frame, NodeId node)
    {
        if (frame.Battle.Active is not { } active) return "";
        if (node == active.Position) return "";

        return $"    your attention {frame.Battle.Awareness.AttentionOn(active, node):P0}";
    }

    /// <summary>The shot the active unit would take at whoever is under the cursor.</summary>
    private static string ShotLine(SandboxFrame frame)
    {
        if (HoveredShot(frame) is not { } plan) return "";

        var quarry = plan.Target;
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
    /// What that shot is expected to <i>achieve</i>, and what the scorer therefore makes of it.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The line above it is the shot as a physical event — a chance, a price, a spread of plates.
    /// This one is the shot as a decision, and the two come apart much further than they look.
    /// <c>ShotPlan.ExpectedDamage</c> is damage arriving at the plate; a beam landing squarely on
    /// a full shield reads beautifully there and achieves precisely nothing.
    /// <see cref="Hexcom.Core.Combat.Gunnery.Expect"/> puts the rounds through the layers they
    /// will actually meet, and it is the figure the AI ranks by.
    /// </para>
    /// <para>
    /// Showing the appraisal beside it is the point of entry 003 in <c>docs/decisions.md</c>:
    /// the terms are kept apart in <see cref="Appraisal"/> so that an interface can say
    /// <em>why</em> one option beats another. Until this line existed nothing in the interface
    /// showed a single term of the model the AI decides on, which is contract 2 failing in the
    /// direction it was written to catch.
    /// </para>
    /// <para>
    /// A shot's appraisal is <b>Harm</b> against <b>Spent</b> and nothing else, and both are
    /// facts about our own soldier and their target's armour, which this screen already quotes
    /// plate by plate. The other two terms are not shown here and one of them cannot be — see
    /// the audit in <c>docs/subprojects/view.md</c>.
    /// </para>
    /// </remarks>
    private static string WorthLine(SandboxFrame frame)
    {
        if (HoveredShot(frame) is not { CanFire: true } plan) return "";

        var expect = frame.Battle.Gunnery.Expect(plan);
        var worth = frame.Battle.Tactics.Appraise(plan);

        return $"it achieves: {expect.Vitality:0.0} vitality    {expect.PlateStripped:0.0} plate    "
               + $"{expect.ShieldStripped:0.0} shield    {expect.DownChance:P0} down    "
               + $"— worth {worth.Score:+0.00;-0.00} "
               + $"(harm {worth.Harm:0.00} less spent {worth.Spent:0.00})";
    }

    /// <summary>
    /// Who this soldier is taking seriously and what each of them could do about it, and who has
    /// eyes on this soldier right now.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The first half is <see cref="Tactician.Seen"/>, which is the list the whole defensive
    /// half of the scorer is computed over — every posture the AI weighs is weighed against
    /// exactly these people — and until this line nothing on screen showed it. Beside each is the
    /// worst single shot they could take at you from where they stand, which is what
    /// <c>Tactician.Incoming</c> starts from. Both are facts about our own soldier: our own
    /// contact file, their weapon, our exposure, our plate.
    /// </para>
    /// <para>
    /// The second half is the other direction, and it is the line contract 3 in
    /// <c>docs/map.md</c> would seem to forbid and does not. Whether an enemy has a line to you is
    /// geometry, and it is already on screen as the exposure figure on the line above — that
    /// figure <em>is</em> the worst of these. Naming which enemy the exposure is to, and how much
    /// of you each can make out, decomposes a number the player already has. What it does not say
    /// is whether any of them has <em>noticed</em>; that stays a rung.
    /// </para>
    /// </remarks>
    private static string SeenLine(SandboxFrame frame, Unit active)
    {
        var battle = frame.Battle;

        var threats = battle.Tactics.Seen(active).Select(threat =>
        {
            var range = battle.Look(active, threat.Unit).Distance;
            return WorstShotAt(battle, threat, active) is { } worst
                ? $"{threat.Unit.Name} {range:0.0} m (worst shot {battle.Tactics.Worth(worst):0.0}: "
                  + $"{worst.Mode.Name} {worst.Weapon.Name.ToLowerInvariant()} at {worst.HitChance:P0})"
                : $"{threat.Unit.Name} {range:0.0} m (no shot on you)";
        }).ToList();

        var watchers = battle.Enemies(active)
            .Select(enemy => (enemy, sight: battle.Look(enemy, active)))
            .Where(pair => pair.sight.CanSee)
            .Select(pair => $"{pair.enemy.Name} ({pair.sight.Exposure:P0})")
            .ToList();

        return $"taking seriously: {(threats.Count == 0 ? "nobody" : string.Join(", ", threats))}    "
               + $"in view of: {(watchers.Count == 0 ? "nobody" : string.Join(", ", watchers))}";
    }

    /// <summary>The single shot from this threat that would cost the target most, if it has one.</summary>
    private static ShotPlan? WorstShotAt(Battle battle, Threat threat, Unit target)
    {
        ShotPlan? worst = null;
        var most = 0.0;

        foreach (var mode in threat.Unit.Weapon.Modes)
        {
            var plan = battle.PlanThreat(threat.Unit, threat.Where, target, UnitPose.Of(target), mode);
            if (!plan.CanFire) continue;

            var worth = battle.Tactics.Worth(plan);
            if (worst is null || worth > most) (worst, most) = (plan, worth);
        }

        return worst;
    }

    /// <summary>
    /// What the three posture keys would cost, and what each would open up.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <see cref="Tactician.AppraisePosture"/> has four terms and this line shows two of them.
    /// <b>Spent</b> is the price, quoted as <see cref="Battle.Costs"/> lists it because that is
    /// what <see cref="Battle.Face"/> and <see cref="Battle.ChangeStance"/> actually charge — see
    /// the note at the end of entry 012 in <c>docs/decisions.md</c>. <b>Prospect</b> is what the
    /// new pose would let this soldier notice, and it is built entirely from our own side of the
    /// ledger: our attention, our contact file, our best shot from there.
    /// </para>
    /// <para>
    /// <b>Spared is deliberately not shown</b>, and the line says so rather than leaving a reader
    /// to assume the appraisal is complete. It carries how much each enemy has already worked out
    /// about this soldier as a raw certainty — entry 011 — and a score with that number folded
    /// into it is a leak with extra steps. When Core resolves 011 this line grows a term; until
    /// then it is honest about being half an appraisal. Harm is always nought for a posture and
    /// is not printed.
    /// </para>
    /// </remarks>
    private static string PostureLine(SandboxFrame frame, Unit active)
    {
        var battle = frame.Battle;
        var threats = battle.Tactics.Seen(active).ToList();
        var here = UnitPose.Of(active);

        var next = active.Stance switch
        {
            Stance.Standing => Stance.Crouching,
            Stance.Crouching => Stance.Prone,
            _ => Stance.Standing,
        };
        var left = active.Facing.Rotate(1);
        var right = active.Facing.Rotate(-1);

        string Opens(UnitPose after, int cost)
            => battle.Tactics.AppraisePosture(active, after, cost, threats).Prospect.ToString("+0.00;-0.00");

        var stance = battle.Costs.ChangeStance;
        var turn = battle.Costs.TurnInPlace;

        return $"C: go {next.ToString().ToLowerInvariant()} for {stance} AP, opens {Opens(here with { Stance = next }, stance)}    "
               + $"Z: face {left} for {turn} AP, opens {Opens(here with { Facing = left }, turn)}    "
               + $"X: face {right} for {turn} AP, opens {Opens(here with { Facing = right }, turn)}    "
               + "(what each spares you is withheld: entry 011)";
    }

    /// <summary>
    /// What the AI did with the turns it was handed, and why.
    /// </summary>
    /// <remarks>
    /// <para>
    /// One line per order, each with its score broken into the terms it was ranked on. Entry 009
    /// in <c>docs/decisions.md</c> says an <see cref="Order"/> is meant to be displayed and that
    /// a sandbox printing only the score would be a finding; so <see cref="Order.Worth"/> and
    /// <see cref="Order.Opens"/> are both printed, each with its own terms, because a move is
    /// almost always worth less than nothing on its own and is taken for the shot at the end of
    /// it. A reader who sees only the sum cannot tell a soldier moving to shoot from a soldier
    /// moving to hide.
    /// </para>
    /// <para>
    /// <b>This is the enemy's mind, and a shipped interface would never show it.</b> The audit in
    /// <c>docs/subprojects/view.md</c> withholds <see cref="UtilityModel"/> on exactly those
    /// grounds. It is shown here because the sandbox exists to check the AI, and an AI can only be
    /// checked by somebody who can see what it thought — the same reason the seed is on the
    /// command line. One term of it is not even a fact the player could hold: a hostile's
    /// <b>Prospect</b> is scaled by how much that hostile has already worked out about the
    /// soldier it is turning towards, which is the number contract 3 blurs. That is fine for the
    /// AI, whose own contact file it is, and it is one more reason this readout is an instrument
    /// rather than an entitlement.
    /// </para>
    /// </remarks>
    private static IEnumerable<string> TurnLines(SandboxFrame frame)
    {
        foreach (var turn in frame.Turns)
        {
            if (turn.Orders.Count == 0)
            {
                yield return $"{turn.Unit.Name} (AI): nothing worth doing, banked {turn.Banked}";
                continue;
            }

            yield return $"{turn.Unit.Name} (AI), banked {turn.Banked}:";
            foreach (var order in turn.Orders) yield return "    " + Describe(order);
        }
    }

    /// <summary>One order, with what it was ranked on laid out term by term.</summary>
    public static string Describe(Order order)
    {
        var what = order.Kind switch
        {
            OrderKind.Move => $"move to {order.MoveTo}",
            OrderKind.Fire => $"{order.Shot!.Mode.Name} at {order.Shot.Target.Name} ({order.Shot.HitChance:P0})",
            OrderKind.Overwatch => $"hold a {order.Arc!.Name} arc on {order.Facing}",
            OrderKind.Face => $"turn to {order.Facing}",
            _ => $"go {order.Stance!.Value.ToString().ToLowerInvariant()}",
        };

        var text = $"{what}    {order.Score:+0.00;-0.00} = worth {order.Worth.Score:+0.00;-0.00} ({Terms(order.Worth)})";
        if (order.Opens is { } opens) text += $" + opens {opens.Score:+0.00;-0.00} ({Terms(opens)})";
        return text;
    }

    /// <summary>The non-zero terms of an appraisal, named. A term left out is nought.</summary>
    private static string Terms(Appraisal appraisal)
    {
        var terms = new List<string>();
        if (appraisal.Harm != 0) terms.Add($"harm {appraisal.Harm:0.00}");
        if (appraisal.Spared != 0) terms.Add($"spared {appraisal.Spared:+0.00;-0.00}");
        if (appraisal.Prospect != 0) terms.Add($"prospect {appraisal.Prospect:+0.00;-0.00}");
        if (appraisal.Spent != 0) terms.Add($"spent {appraisal.Spent:0.00}");
        return terms.Count == 0 ? "nothing" : string.Join(", ", terms);
    }

    /// <summary>The shot the active unit would take at the cursor, planned once for both lines.</summary>
    private static ShotPlan? HoveredShot(SandboxFrame frame)
    {
        if (frame.Battle.Active is not { } shooter) return null;
        if (HoveredUnit(frame) is not { } quarry || !quarry.IsHostileTo(shooter)) return null;

        return frame.Battle.PlanShot(shooter, quarry);
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

        return $"{cover}    {seen.Exposure:P0} exposed    {seen.Distance:0.0} m, {RangeBand(frame, seen.Distance)}";
    }

    /// <summary>
    /// Where the place under the cursor falls in the active soldier's weapon's range bands.
    /// </summary>
    /// <remarks>
    /// The refusal line says <i>out of range at 14 m</i> only once the shot is already
    /// impossible, and nothing said anything at all about the long stretch between optimal and
    /// maximum where the weapon still fires and fires worse. Which band a target sits in is what
    /// decides whether to close, so it is quoted for any node, not only for one with a soldier on
    /// it — the question is usually about a hex nobody is standing on yet. The bands themselves
    /// are on the status line beside the weapon, so the figure here can stay short.
    /// </remarks>
    private static string RangeBand(SandboxFrame frame, double distance)
    {
        if (frame.Battle.Active is not { } active) return "";

        var weapon = active.Weapon;
        if (distance <= weapon.OptimalRange) return "in optimal range";
        if (distance > weapon.MaxRange) return "out of range";

        return $"long range, x{frame.Battle.Gunnery.RangeFactor(weapon, distance):0.00} to hit";
    }

    /// <summary>The active soldier's weapon and its two range bands, in metres.</summary>
    private static string WeaponLine(Unit active)
        => $"{active.Weapon.Name} {active.Weapon.OptimalRange:0}/{active.Weapon.MaxRange:0} m";

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
