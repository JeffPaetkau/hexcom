using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Content;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

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
public sealed class BattleHud(Font font)
{
    private readonly Font _font = font;

    /// <summary>The surface currently being drawn on. Set by whichever of the two entry points is running.</summary>
    private CanvasItem _canvas = null!;

    /// <summary>Where the panels hang, given the node's own offset. Screen space, not canvas space.</summary>
    public Vector2 Origin { get; set; }

    /// <summary>
    /// What a player sees: the mission, whose go it is, this soldier's situation, the cursor,
    /// the shot and what it is worth, and what happened while it was not your turn.
    /// </summary>
    /// <remarks>
    /// <b>The two halves of this class draw one frame between them, and that is load-bearing.</b>
    /// A frame is one moment's answers (<see cref="SandboxFrame"/>), and the play-through's first
    /// finding put the instruments in a second window — which is a second surface, redrawn on its
    /// own schedule, and therefore the first chance this code has ever had to show two moments at
    /// once. It cannot: the node assembles one frame and hands the same instance to both, so a
    /// number in the instruments window is the number the map beside it was drawn from.
    /// <para>
    /// The line between the two halves is the brief's test — <i>would a player who never presses
    /// <c>O</c> want it</i> — and it does not run where the file's own structure would have put
    /// it. The legend splits: where you are looking and what the soldier does are a player's, and
    /// what the run is set to is a tester's, which is the split <see cref="DrawLegend"/> already
    /// had for reasons of width. What moves out of the status line is only which mode the run is
    /// in; the round, the soldier and the weapon stay.
    /// </para>
    /// </remarks>
    public void Draw(CanvasItem canvas, SandboxFrame frame, Vector2 viewport)
    {
        _canvas = canvas;

        // The strip last, so that a long readout runs under it rather than over it.
        DrawLines(frame);
        DrawHappenings(frame, viewport);
        DrawLegend(viewport, PlayerKeys);
        DrawOrderStrip(frame, viewport);
    }

    /// <summary>
    /// What a tester sees: which mode the run is in, the keys that change it, and the AI's
    /// reasoning for every turn it has taken since a person last acted.
    /// </summary>
    /// <remarks>
    /// A window of its own, which the play-through asked for so it can sit on a second monitor.
    /// Everything here fails the test in <see cref="Draw"/>'s remarks: the orders block is the
    /// opponent's mind and entry 023 is the argument for it existing at all, and the mode line
    /// and the third rank of keys are about the harness rather than about the battle. A shipped
    /// interface is what is left when this window is closed, which is now a thing that can be
    /// looked at rather than argued about.
    /// <para>
    /// It draws from its own top-left rather than stacking off the bottom edge, because it is a
    /// panel of text on nothing rather than readouts over a map, and because the window is
    /// resizable and a block anchored to the bottom of a short one would run off the top.
    /// </para>
    /// </remarks>
    public void DrawInstruments(CanvasItem canvas, SandboxFrame frame, Vector2 window)
    {
        _canvas = canvas;
        _canvas.DrawRect(new Rect2(Vector2.Zero, window), SandboxPalette.Background);

        var lines = new List<string> { WhichBattle(frame), WhichMode(frame), "" };
        lines.AddRange(InstrumentKeys);
        lines.Add("");

        var orders = TurnLines(frame).ToList();
        lines.AddRange(orders.Count > 0 ? orders : ["the AI has not acted since you last did"]);

        var top = new Vector2(18, 30);
        for (var i = 0; i < lines.Count; i++)
            _canvas.DrawString(_font, top + new Vector2(0, i * LineHeight), lines[i],
                HorizontalAlignment.Left, -1, LineSize,
                i <= 1 ? SandboxPalette.TextBright : SandboxPalette.TextDim);
    }

    /// <summary>Which map and which deployment this is.</summary>
    /// <remarks>
    /// A picture that does not say which battle it is of cannot be checked against anything, and
    /// there is more than one map now. It is a line to itself rather than the head of the mode
    /// line because the two answer different questions and because one line carrying both ran off
    /// the right of the window — which is the failure the legend had for weeks before the key
    /// remap found it, and reintroducing it in the second week would be careless.
    /// </remarks>
    private static string WhichBattle(SandboxFrame frame)
        => $"{frame.Scenario.Name} — {frame.Scenario.Situation}    {frame.Battle.Map.Tiles.Count} tiles";

    /// <summary>Which of the run's switches are on.</summary>
    /// <remarks>
    /// An instrument in every clause. A capture with two hostiles on it means one thing if it
    /// shows everything and another if it shows what our side has found, and a session reading it
    /// months later has nothing else to tell them which.
    /// </remarks>
    private static string WhichMode(SandboxFrame frame)
        => (frame.Omniscient ? "seeing everything" : "seeing what our side knows")
           + (frame.HostilesAutomatic ? "    hostiles: AI" : "    hostiles: by hand")
           + (frame.AnswerByHand ? "    reactions: by hand" : "    reactions: recommended")
           + (frame.TileDetail ? "" : "    zoomed out: tile detail off");

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

            // A hostile nobody of ours has found keeps its place in the order and loses its
            // name, its roll and its reserve: that somebody acts here is known, because turns
            // are taken in the open; who, and with what in hand, is theirs. Whether even the
            // slot is too much is an open question in view.md.
            if (!frame.Sees(unit))
            {
                _canvas.DrawString(_font, box.Position + new Vector2(12, 16), "?",
                    HorizontalAlignment.Left, -1, 13, SandboxPalette.TextDim);
                continue;
            }

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

        // The mode line that used to open this block is in the instruments window now — which
        // map, which deployment and which switches are on are a tester's questions. What is left
        // is the battle: the mission, whose go it is, and what that soldier is carrying.
        var lines = new List<string>();
        lines.AddRange(MissionLines(frame));
        lines.Add(
            active is null || frame.OutOfTime
                ? $"{Clock(frame)}    {(frame.OutOfTime ? "out of time" : "nobody left to act")}"
                : $"{Clock(frame)}    {active.Name} ({active.Side})    "
                  + $"{active.ActionPoints}/{active.Stats.ActionPoints} AP    "
                  + $"{active.Stance.ToString().ToLowerInvariant()}    facing {active.Facing}    layer {frame.Layer}    "
                  + $"{WeaponLine(active)}");
        lines.Add(active is null ? "" : AlarmLine(frame, active));

        if (active is not null)
        {
            lines.AddRange(SeenLines(frame, active));
            lines.Add(ViewedLine(frame, active));
            lines.Add(ReserveLine(frame, active));
            lines.AddRange(PostureLines(frame, active));
        }
        lines.AddRange(new[]
        {
            frame.Hover is { } h
                ? $"cursor {h}    {(frame.Reach.CostTo(h) is { } c ? $"{c} AP" : "out of reach")}    "
                  + $"{SightLine(frame, h)}{AttentionLine(frame, h)}{NoiseLine(frame, h)}"
                : "cursor —",
            AimLine(frame),
            ShotLine(frame),
            WorthLine(frame),
        });
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
        // Stacked upwards from just above the legend, most recent nearest the bottom. The open
        // window goes on top of the pile because it is the only one of these that is a question
        // rather than a record, and the only one the next keystroke is about. The AI's orders
        // used to be on this pile and are in the instruments window now: what the other side
        // *did to you* is a player's, and why it decided to is not.
        var lines = new List<string> { frame.LastWindow };
        lines.RemoveAll(line => line.Length == 0);

        var next = DrawBlockAbove(viewport.Y - 22 - LegendLines * LineHeight - 14, lines);
        next = DrawBlockAbove(next, WindowLines(frame), SandboxPalette.OverwatchHue);
        DrawBlockAbove(next, BriefingLines(frame), SandboxPalette.TextDim);
    }

    /// <summary>
    /// Draw a block of lines whose last one sits at <paramref name="bottom"/>, and say where the
    /// next block up may end.
    /// </summary>
    private float DrawBlockAbove(float bottom, IReadOnlyList<string> lines, Color? hue = null)
    {
        if (lines.Count == 0) return bottom;

        var top = Origin + new Vector2(18, bottom - (lines.Count - 1) * LineHeight);
        Panel(top, lines);

        for (var i = 0; i < lines.Count; i++)
            _canvas.DrawString(_font, top + new Vector2(0, i * LineHeight), lines[i],
                HorizontalAlignment.Left, -1, LineSize, hue ?? SandboxPalette.TextBright);

        return bottom - lines.Count * LineHeight - 14;
    }

    /// <summary>
    /// The question an open reaction window is asking, and every answer it will accept.
    /// </summary>
    /// <remarks>
    /// <para>
    /// This is the readout entry 004 asked for and entry 040 made reachable. The state behind it
    /// is worth being precise about, because it is the one state in the game where the map is
    /// lying if you read it carelessly: the mover has <b>paid for a walk it has not taken</b>. It
    /// stands at the start of the route until the window resolves and walks it along, so the dot
    /// on the map is where the soldier is, the line out of it is where the soldier is going, and
    /// every option below is priced against where the soldier <em>will</em> be when it lands.
    /// </para>
    /// <para>
    /// Only the reactor being chosen for gets its options listed. A window with three reactors
    /// and four options each is twelve lines, which is a third of the screen for a question that
    /// is answered one soldier at a time; everybody else gets the line saying what they have
    /// already said, or nothing, which is what a player checking their own work needs.
    /// </para>
    /// <para>
    /// The scores are <c>ReactionWindow.Appraise</c> — the same call the recommendation is made
    /// with, so what a player is choosing between is exactly what the AI would have ranked. That
    /// is contract 2 at its narrowest, and it is why <em>hold fire</em> reads as <c>+0.00</c>
    /// rather than as an absence: an option worth nothing beats every option worth less, by
    /// arithmetic, and a player should be able to see that happen.
    /// </para>
    /// </remarks>
    private static IReadOnlyList<string> WindowLines(SandboxFrame frame)
    {
        if (frame.Open is not { } window) return [];

        var mover = window.Mover;
        var answered = window.Placements.Count;

        var what = window.IsAmbush
            ? $"{window.SprungBy!.Name} springs on {mover.Name}, standing at {mover.Position}"
            : $"{mover.Name} has paid for {window.Move.Start} to {window.Move.Destination}, "
              + $"{window.Move.Duration} ticks, and not walked it yet";

        var lines = new List<string>
        {
            $"WINDOW OPEN — {what}    {answered} of {window.Offers.Count} answered    "
            + "tab: whose answer    1-9: pick    space: resolve, recommending the rest",
        };

        for (var i = 0; i < window.Offers.Count; i++)
        {
            var offer = window.Offers[i];
            var chosen = i == frame.Chooser;
            var placed = window.Placements.FirstOrDefault(p => p.Reactor == offer.Reactor);

            var who = $"{(chosen ? ">" : " ")} {offer.Reactor.Name} ({offer.Kind.ToString().ToLowerInvariant()})"
                      + $"    reserve {offer.Reserve}, purse {offer.Purse}";

            if (placed is not null) { lines.Add($"{who}    ANSWERED: {placed}"); continue; }
            if (!chosen) { lines.Add($"{who}    {offer.Options.Count} options"); continue; }

            lines.Add(who);
            for (var n = 0; n < offer.Options.Count; n++)
            {
                var option = offer.Options[n];
                var worth = window.Appraise(option);

                lines.Add(
                    $"      {n + 1}  {option}    {worth.Score:+0.00;-0.00} ({Terms(worth)})"
                    + (option == offer.Recommended ? "    ← recommended" : ""));
            }
        }

        return lines;
    }

    /// <summary>
    /// The keys, parked along the bottom edge where there is nothing else to read.
    /// </summary>
    /// <remarks>
    /// <para>
    /// It used to be the last line of the status block, which put it straight through the top
    /// row of tile-cost labels: both were legible on their own and neither was legible together,
    /// in every capture anyone has ever taken. Moving it costs nothing — a legend is the one
    /// readout that never changes and so never needs to be near anything.
    /// </para>
    /// <para>
    /// <b>Three lines, split by what the key is for</b> — where you are looking, what the
    /// soldier does, and what the whole run is set to. As one line it ran off the right edge of
    /// a 1600-wide viewport and had done for some time, silently, which is the failure mode of a
    /// legend: the keys that fall off are the ones nobody has learned yet, so nobody misses
    /// them. Splitting by purpose rather than at whatever width happens to fit means each line
    /// is complete on its own, and the first one is the one a person reaches for first.
    /// </para>
    /// </remarks>
    /// <summary>
    /// The keys a player needs: where you are looking, and what the soldier does.
    /// </summary>
    /// <remarks>
    /// Two of the three ranks the legend has had since the key remap. The third went to the
    /// instruments window with the rest of the harness, which is what the play-through asked for
    /// and, more usefully, what the brief's own test gives: a player who never presses <c>O</c>
    /// wants to know how to move and how to look, and does not want to know how to hand the
    /// hostile side to the AI.
    /// <para>
    /// <b>Three lines of it since brief three</b>, and the new one is the orders. Right-click
    /// stopped firing and the shot became a mode, which is four gestures where there was one; on
    /// the line they used to share with the posture keys they ran towards the right edge, and
    /// splitting by purpose is the fix this legend has taken twice already.
    /// </para>
    /// </remarks>
    private static readonly string[] PlayerKeys =
    [
        "WASD or drag: pan    Q/E or right-drag: turn    wheel/+-: zoom    F: whole map    G: whoever is up    PgUp/PgDn: storey",
        "left-click: move, or aim at a hostile    1 or tab: aim, tab again for the next    "
            + "space: fire when aiming, else end turn    right-click or esc: back out",
        "C: stance    Z/X: turn on the spot    V: overwatch arc    B: arm/spring ambush    T: leave the field    L: call it in",
    ];

    /// <summary>The keys that change what kind of run this is. Instruments, by the same test.</summary>
    private static readonly string[] InstrumentKeys =
    [
        "H: hostiles to AI    J: AI takes this turn    K: answer windows by hand",
        "O: see everything    M: briefing    I: this window    R: new battle",
    ];

    private void DrawLegend(Vector2 viewport, IReadOnlyList<string> keys)
    {
        var top = Origin + new Vector2(18, viewport.Y - 22 - (keys.Count - 1) * LineHeight);
        Panel(top, keys);

        for (var i = 0; i < keys.Count; i++)
            _canvas.DrawString(_font, top + new Vector2(0, i * LineHeight), keys[i],
                HorizontalAlignment.Left, -1, LineSize, SandboxPalette.TextDim);
    }

    /// <summary>How many lines <see cref="DrawLegend"/> occupies, so that what stacks above it agrees.</summary>
    private static readonly int LegendLines = PlayerKeys.Length;

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
    /// The round, against the mission's own limit where there is one.
    /// </summary>
    /// <remarks>
    /// A fraction rather than a bare count whenever the file carries a clock, because a limit
    /// nobody can see is a limit that arrives as a surprise — and the sandbox is the thing
    /// applying it, since the rules have none of their own. Entry 047.
    /// </remarks>
    private static string Clock(SandboxFrame frame)
        => frame.Mission?.Rounds is { } limit
            ? $"round {frame.Battle.Round}/{limit}"
            : $"round {frame.Battle.Round}";

    /// <summary>
    /// What our side came to do, how it is going, and who is off the field.
    /// </summary>
    /// <remarks>
    /// Until entry 041 a battle ended one way — everybody on one side down — and the interface
    /// had nothing to say about it that the turn-order strip did not already say by being empty.
    /// Three things are worth reading now and all three are new. <c>Objective.Brief</c> is the
    /// orders in the words the rules judge by; <c>VerdictFor</c> is where they stand; and
    /// <c>Unit.Left</c> is the difference between a soldier who walked out and one who was
    /// carried, which the old model could not tell apart.
    /// <para>
    /// The reading beside a departure is the load-bearing part. A withdrawal is judged on the
    /// highest rung any enemy held on each soldier <em>at the moment it left</em> — sampled then,
    /// because asking afterwards reads Unaware for everybody, trivially and always — so the
    /// number that decides the mission is one a player can only see if it is printed here.
    /// </para>
    /// <para>
    /// It is our own side's objective and nobody else's. What the enemy is on the field to do is
    /// theirs to know; there is no line here for it and there should not be one.
    /// </para>
    /// </remarks>
    private static IEnumerable<string> MissionLines(SandboxFrame frame)
    {
        var battle = frame.Battle;
        if (battle.ObjectiveOf(Side.Player) is not { } objective) yield break;

        // The task, in the words the squad was given, and the rule the same thing turns into.
        // A mission file has six briefing parts and only one of them is a sentence about what to
        // do this turn; the other five are read once and are behind M. Where there is no file —
        // the compound fixture — the rule's own summary is all there is to say.
        var task = frame.Mission is { } mission ? mission.Brief.Task : objective.Brief;

        var verdict = battle.VerdictFor(Side.Player);
        yield return $"mission: {task}    {verdict.ToString().ToUpperInvariant()}";

        // One line each. A withdrawal ends with everybody off the field, so the case where this
        // matters most is the case where there are most of them, and joined into the line above
        // they ran under the turn-order strip on the first mission anybody actually won.
        var gone = battle.Units
            .Where(u => u.Side == Side.Player && u.Left is not null)
            .OrderBy(u => u.Left!.Round)
            .Select(u => $"{u.Name} {u.Left!.Kind.ToString().ToLowerInvariant()} in round {u.Left.Round}, "
                         + $"they had {u.Left.Noticed.ToString().ToUpperInvariant()}")
            .ToList();

        if (gone.Count == 0) yield break;
        if (gone.Count == 1) { yield return $"off the field: {gone[0]}"; yield break; }

        yield return "off the field:";
        foreach (var who in gone) yield return "    " + who;
    }

    /// <summary>
    /// The six parts of the briefing, as the squad was given them.
    /// </summary>
    /// <remarks>
    /// Behind a key rather than on screen, and that is the interface decision this readout is.
    /// The mission book's six parts are what a squad is told <em>before</em> it goes: the
    /// instrument it is filed under, what is thought to be there, the task, the restraint, the
    /// way off, and what ends it short. Exactly one of them — the task — is a sentence about what
    /// to do next, and it is the one on the status line. The other five are context a player
    /// reads once and refers back to, which is a page and not a line.
    /// <para>
    /// Printed in the file's own words rather than in the rules'. <c>Objective.Brief</c> says
    /// <em>leave by the exit with nobody above Suspicious</em>, which is what the rules judge;
    /// the briefing says not to be seen and not to fire and that the people in the cottages are
    /// not part of this, which is what the squad was actually told. Entry 048 is precisely the
    /// gap between those two, so showing both and keeping them apart is the honest thing.
    /// </para>
    /// </remarks>
    private static IReadOnlyList<string> BriefingLines(SandboxFrame frame)
    {
        if (!frame.Briefing || frame.Mission is not { } mission) return [];

        var lines = new List<string> { $"BRIEFING — {mission.Name ?? mission.MapName}    M to put it away" };

        foreach (var part in Briefing.Order)
        {
            var label = part.ToString().ToLowerInvariant();
            foreach (var (text, i) in Wrap(mission.Brief.Part(part), 108).Select((t, i) => (t, i)))
                lines.Add($"  {(i == 0 ? label.PadRight(11) : new string(' ', 11))}  {text}");
        }

        if (mission.Rounds is { } rounds)
            lines.Add($"  {"clock".PadRight(11)}  {rounds} rounds, applied by the sandbox because the rules have no clock");

        return lines;
    }

    /// <summary>Break a paragraph on word boundaries, because a briefing part is prose.</summary>
    private static IEnumerable<string> Wrap(string text, int width)
    {
        var line = new System.Text.StringBuilder();

        foreach (var word in text.Split(' ', System.StringSplitOptions.RemoveEmptyEntries))
        {
            if (line.Length > 0 && line.Length + 1 + word.Length > width)
            {
                yield return line.ToString();
                line.Clear();
            }

            if (line.Length > 0) line.Append(' ');
            line.Append(word);
        }

        if (line.Length > 0) yield return line.ToString();
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

        return $"reserve {active.Reserve}, {would} if you stop here    {holding}    {EarshotOf(frame, active)}";
    }

    /// <summary>
    /// Who would hear this soldier call a contact in, and how much of it would survive the trip.
    /// </summary>
    /// <remarks>
    /// Two audit rows in one clause, both of them gaps since the audit was written, and both
    /// unblocked by Core rather than by anything here: <c>Battle.Shout</c> exists now, so there
    /// is something to preview. <c>Awareness.Earshot</c> is the list — a radio reaches the whole
    /// side, a voice reaches <c>VoiceRangeMetres</c>, and seeing a comrade react counts too —
    /// and <c>RelayFraction</c> is what a second-hand contact is worth, which is why calling
    /// somebody in leaves the hearer hunting rather than immediately engaged.
    /// <para>
    /// Names and a fraction, both of them ours. What the shout does to each hearer's own contact
    /// file is a movement in a figure about our own side, so contract 3 permits it; it is left
    /// out because the interesting question before you shout is <em>who</em>, and the list is
    /// already the longest thing on this line.
    /// </para>
    /// </remarks>
    private static string EarshotOf(SandboxFrame frame, Unit active)
    {
        var heard = frame.Battle.Awareness.Earshot(active).Select(u => u.Name).ToList();
        var relay = frame.Battle.Awareness.Model.RelayFraction;

        return heard.Count == 0
            ? "a shout reaches nobody"
            : $"a shout reaches {string.Join(", ", heard)} at {relay:P0}";
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

    /// <summary>That the firing mode is up, at whom, and the three ways out of it.</summary>
    /// <remarks>
    /// A line of its own and in capitals, because a mode nobody can see they are in is the whole
    /// failure the genre's cancel convention exists to prevent: the space bar ends the turn when
    /// this line is absent and fires when it is present, and that is only fair if it is impossible
    /// to miss which. It says what confirms and what backs out in so many words, which is the brief's
    /// test — a player backs out of a half-entered order without having been told a key.
    /// </remarks>
    private static string AimLine(SandboxFrame frame)
    {
        if (frame.Aim is not { } quarry) return "";

        var targets = frame.Targets;
        var which = targets.Count > 1 ? $", {IndexOf(targets, quarry) + 1} of {targets.Count} in sight    tab: next" : "";

        return $"AIMING at {quarry.Name}{which}    space, enter or click them again: fire    right-click or esc: back out";
    }

    private static int IndexOf(IReadOnlyList<Unit> units, Unit unit)
    {
        for (var i = 0; i < units.Count; i++)
            if (units[i] == unit) return i;
        return -1;
    }

    /// <summary>The shot the active unit would take at whoever is aimed at, or else under the cursor.</summary>
    private static string ShotLine(SandboxFrame frame)
    {
        if (StagedShot(frame) is not { } plan) return "";

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
               + (frame.Aim is null ? "    click or 1: aim" : "");
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
        if (StagedShot(frame) is not { CanFire: true } plan) return "";

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
    /// The first half is <see cref="Tactician.Known"/>, which is the list the whole defensive
    /// half of the scorer is computed over — every posture the AI weighs is weighed against
    /// exactly these people — and until this line nothing on screen showed it. A threat in view
    /// is quoted where it stands; a threat remembered at a marker is quoted where it is
    /// <em>believed</em> to be, with the credence the scorer discounts it by, and never where it
    /// really is — the distance is traced to the marker for exactly that reason. Beside each is
    /// the worst single shot they could take at you from there, which is what
    /// <c>Tactician.Incoming</c> starts from. All of it is our own soldier's information: our own
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
    /// <remarks>
    /// One line each once there is more than one, rather than all of them joined. The joined
    /// version was already the longest line on the screen with two contacts on it and ran clean
    /// under the turn-order strip with three — which is the strip's own gotcha in
    /// <c>docs/subprojects/view.md</c>, and the reason the exposure half of this was split out
    /// into a line of its own once already. Splitting by contact rather than by field is the
    /// version that keeps working as contacts accumulate, which is the direction a battle only
    /// ever goes.
    /// </remarks>
    private static IEnumerable<string> SeenLines(SandboxFrame frame, Unit active)
    {
        var battle = frame.Battle;

        var threats = battle.Tactics.Known(active).Select(threat =>
        {
            var range = battle.Sight.Trace(active.Vantage, threat.Where.Vantage).Distance;
            var where = threat.EyesOn
                ? $"{threat.Unit.Name} {range:0.0} m {Held(battle, active, threat.Unit)}"
                : $"{threat.Unit.Name} believed at {threat.Where.Position} {range:0.0} m "
                  + $"x{threat.Credence:P0} {Held(battle, active, threat.Unit)}";

            return WorstShotAt(battle, threat, active) is { } worst
                ? $"{where}, worst {battle.Tactics.Worth(worst):0.0} "
                  + $"({worst.Mode.Name} {worst.Weapon.Name.ToLowerInvariant()} {worst.HitChance:P0})"
                : $"{where}, no shot on you";
        }).ToList();

        if (threats.Count == 0) { yield return "taking seriously: nobody"; yield break; }
        if (threats.Count == 1) { yield return $"taking seriously: {threats[0]}"; yield break; }

        yield return "taking seriously:";
        foreach (var threat in threats) yield return "    " + threat;
    }

    /// <summary>
    /// How much our own soldier has worked out about an enemy, exactly, against a full contact.
    /// </summary>
    /// <remarks>
    /// The audit row in <c>docs/subprojects/view.md</c> that sat open the longest, because the
    /// question was never how to format it. Contract 3 named two cases — your own exposure,
    /// exact; the enemy's alarm, a rung — and this is neither. Entry 042 settled it: the split is
    /// <b>whose knowledge it is</b> rather than what it is about, so your side's knowledge is
    /// yours in both directions, and blurring what your own soldier has worked out would be fog
    /// about yourself, which contract 3 already rejects for exposure in as many words.
    /// <para>
    /// Quoted against <c>Threshold(Engaged)</c>, the top of the ladder, because that is what the
    /// scorer scales its prospect term by — how much is still left to learn. A contact at 50 of
    /// 100 is a soldier who knows somebody is there and is still paying to find out more, and
    /// that is the figure a player weighing a look against a shot is short of.
    /// </para>
    /// </remarks>
    private static string Held(Battle battle, Unit observer, Unit subject)
    {
        var contact = battle.Awareness.Of(observer.Id, subject.Id);
        var full = battle.Awareness.Model.Threshold(AwarenessState.Engaged);

        return $"[you hold {contact.Detection:0}/{full:0}]";
    }

    /// <summary>Which enemies have a line to this soldier, and how much of it each can make out.</summary>
    /// <remarks>
    /// Its own line rather than the tail of <see cref="SeenLine"/>: with three contacts known
    /// the two together ran under the turn-order strip, and the strip is the thing nobody should
    /// have to read through.
    /// </remarks>
    /// <remarks>
    /// In the game an enemy nobody of ours has found is <em>somebody</em>: that a line exists is
    /// geometry and is ours, but which soldier is at the far end of it is theirs until we have
    /// eyes on them. Omniscient, the names are back.
    /// </remarks>
    private static string ViewedLine(SandboxFrame frame, Unit active)
    {
        var watchers = frame.Battle.Enemies(active)
            .Select(enemy => (enemy, sight: frame.Battle.Look(enemy, active)))
            .Where(pair => pair.sight.CanSee)
            .Select(pair => $"{(frame.Sees(pair.enemy) ? pair.enemy.Name : "somebody unseen")} ({pair.sight.Exposure:P0})")
            .ToList();

        return $"in view of: {(watchers.Count == 0 ? "nobody" : string.Join(", ", watchers))}";
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
    /// What the three posture keys would cost, and what the scorer makes of each.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <see cref="Tactician.AppraisePosture"/>, term by term, for the pose each key would leave
    /// this soldier in. <b>Spent</b> is quoted as <see cref="Battle.Costs"/> lists it because that
    /// is what <see cref="Battle.Face"/> and <see cref="Battle.ChangeStance"/> actually charge —
    /// see the note at the end of entry 012 in <c>docs/decisions.md</c>. <b>Prospect</b> is what
    /// the new pose would let this soldier notice, from our own attention, our own contact file
    /// and our best shot from there. <b>Spared</b> is what the pose keeps off us, and it was the
    /// term this line could not print when it was first drawn: it folded in how much each enemy
    /// had worked out about this soldier as a raw certainty, which contract 3 blurs. Entry 021
    /// made the scorer read that at the rung the interface shows, so the whole appraisal is now a
    /// figure the player is entitled to — and it is the same figure the AI ranks the same pose
    /// by. Harm is always nought for a posture and is not printed.
    /// </para>
    /// </remarks>
    private static IEnumerable<string> PostureLines(SandboxFrame frame, Unit active)
    {
        var battle = frame.Battle;
        var threats = battle.Tactics.Known(active).ToList();
        var here = UnitPose.Of(active);

        var next = active.Stance switch
        {
            Stance.Standing => Stance.Crouching,
            Stance.Crouching => Stance.Prone,
            _ => Stance.Standing,
        };
        var left = active.Facing.Rotate(1);
        var right = active.Facing.Rotate(-1);

        string Worth(UnitPose after, int cost)
        {
            var appraisal = battle.Tactics.AppraisePosture(active, after, cost, threats);
            return $"{appraisal.Score:+0.00;-0.00} ({Terms(appraisal)})";
        }

        var stance = battle.Costs.ChangeStance;
        var turn = battle.Costs.TurnInPlace;

        // Two lines, not one: three appraisals with their terms ran under the turn-order strip.
        yield return $"C: go {next.ToString().ToLowerInvariant()} for {stance} AP {Worth(here with { Stance = next }, stance)}";
        yield return $"Z: face {left} for {turn} AP {Worth(here with { Facing = left }, turn)}    "
                     + $"X: face {right} for {turn} AP {Worth(here with { Facing = right }, turn)}";
    }

    /// <summary>
    /// What walking to the place under the cursor would announce: how loud the route is, and who
    /// would hear it.
    /// </summary>
    /// <remarks>
    /// <see cref="Battle.Loudness"/> is the figure <see cref="Battle.Move"/> will charge for the
    /// same route, so what this line says a walk would make is what it makes, and
    /// <see cref="Hexcom.Core.Awareness.AwarenessTracker.WouldHear"/> is what the AI's own move
    /// appraisal folds into a route's score. Only the names of who would hear it are printed. The
    /// figures behind them are how far each listener's contact file on us would move, and while
    /// <see cref="Hexcom.Core.Awareness.Announcement"/> argues that is information about our own
    /// soldier, contract 3 has so far been read as blurring the enemy's file whichever way it is
    /// approached. Names are safe under either reading; a player who wants to know how much is
    /// told in what direction by the rung under the listener's feet on the next look.
    /// </remarks>
    private static string NoiseLine(SandboxFrame frame, NodeId node)
    {
        if (frame.Battle.Active is not { } active) return "";
        if (!frame.Reach.TryGetPath(node, out var path) || path.Count == 0) return "";

        var loudness = frame.Battle.Loudness(active, path);
        if (loudness <= 0) return "    silent";

        var listeners = frame.Battle.Awareness.WouldHear(active, node, loudness)
            .Select(word => word.Learner.Name)
            .ToList();

        return $"    noise {loudness:0}, heard by {(listeners.Count == 0 ? "nobody" : string.Join(", ", listeners))}";
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
        // Gated on the instruments window being open, and no longer on --omniscient as well.
        // Entry 023 made this an instrument and it still is; what changed is that there is now a
        // window that is nothing but instruments, so the gate can be *being in it*. Two gates
        // would have made watching the AI reason cost a change to the map — pressing O to read
        // the orders is exactly the thing that stops you seeing what a player would have seen —
        // and separating those two is most of the point of the second window.
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
        // Every kind, named. It used to end in a catch-all that read the stance, which was true
        // of the only kind left over at the time; three more have landed since and the first
        // grenade the AI threw in front of this readout brought the whole frame down with it.
        // A switch over somebody else's enum wants its default to be a sentence, not a guess.
        var what = order.Kind switch
        {
            OrderKind.Move => $"move to {order.MoveTo}",
            OrderKind.Fire => $"{order.Shot!.Mode.Name} at {order.Shot.Target.Name} ({order.Shot.HitChance:P0})",
            OrderKind.Overwatch => $"hold a {order.Arc!.Name} arc on {order.Facing}",
            OrderKind.Face => $"turn to {order.Facing}",
            OrderKind.Stance => $"go {order.Stance!.Value.ToString().ToLowerInvariant()}",
            OrderKind.Throw => $"throw {order.Throw!.Item.Name.ToLowerInvariant()} at {order.Throw.Aimed}",
            OrderKind.Shout => $"call in {order.About?.Name ?? "a contact"}",
            OrderKind.Leave => "walk off the field",
            _ => order.Kind.ToString().ToLowerInvariant(),
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

    /// <summary>The shot the active unit would take at the aim, or at the cursor when nothing is aimed at.</summary>
    /// <remarks>
    /// The aim wins over the cursor so that a player can move the pointer — to orbit, to read a
    /// label, to look at the ground they would retreat to — without the terms they are about to
    /// confirm being replaced by somebody else's.
    /// </remarks>
    private static ShotPlan? StagedShot(SandboxFrame frame)
    {
        if (frame.Battle.Active is not { } shooter) return null;
        if ((frame.Aim ?? HoveredUnit(frame)) is not { } quarry || !quarry.IsHostileTo(shooter)) return null;

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

    /// <remarks>
    /// Through the frame, so the shot line cannot quote a soldier the map is not showing: in
    /// the game a hostile nobody of ours has eyes on is not under the cursor, whatever is
    /// standing there.
    /// </remarks>
    private static Unit? HoveredUnit(SandboxFrame frame) => frame.HoveredUnit;

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
