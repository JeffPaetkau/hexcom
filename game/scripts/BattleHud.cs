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
/// <para>
/// <b>Brief one: the readouts go on the things they describe.</b> Every figure used to be a line in
/// a panel at the top left, and a game whose subject is information cannot teach a player to read a
/// battlefield with a readout that makes them look away from it. So the panel keeps what has no
/// place on the map — the mission, the clock, the weapon — and everything else hangs from a soldier,
/// a target or the tile under the cursor, projected like the map's own labels.
/// </para>
/// <para>
/// <b>Headline and terms, with the gesture for <i>on demand</i> picked once.</b> Each thing carries
/// one figure. Its terms come two ways and only two, both from the reference set's pictures (entry
/// 089): the shot's terms <b>open for as long as the player is aiming</b>, docked at the right edge
/// with a fold the game remembers — which is what both photographed games do — and <b>holding
/// <c>Ctrl</c> shows every thing's terms at once</b>, which is the job the set uses a held key for.
/// There is no hover card per figure, because a second modal readout per figure is how this ends up
/// worse than the panel it replaces.
/// </para>
/// </remarks>
public sealed class BattleHud(Font font, SandboxCamera camera, System.Func<SandboxFrame, Unit, Vector2?> crown)
{
    private readonly Font _font = font;

    /// <summary>Where a scene point lands on screen. The HUD asks it of tiles.</summary>
    private readonly SandboxCamera _camera = camera;

    /// <summary>
    /// Where a unit's labels hang from on screen — <see cref="BattleView.Crown"/>, handed in so that a
    /// readout hangs from the body the name hangs from, walk and all, without this class knowing a
    /// walk exists.
    /// </summary>
    private readonly System.Func<SandboxFrame, Unit, Vector2?> _crown = crown;

    /// <summary>
    /// Where the fold switch in the docked shot terms was last drawn, so a click on it can be told
    /// from a click on the map. Empty when the terms are not up.
    /// </summary>
    public Rect2 FoldSwitch { get; private set; }

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

        // What hangs on the map first, so every panel sits over it rather than under it: a tag
        // projected under the top block is the tag that has to give way.
        DrawInPlace(frame);

        // The strip last, so that a long readout runs under it rather than over it; the banner
        // before it, since it is up for a second and the strip is the thing it is standing in for.
        DrawLines(frame);
        DrawHappenings(frame, viewport);
        DrawTerms(frame, viewport, viewport.Y - 22 - LegendLines * LineHeight - 14);
        DrawLegend(viewport, PlayerKeys);
        DrawTheirGo(frame, viewport);
        DrawOrderStrip(frame, viewport);
    }

    /// <summary>How many dots the banner's activity indicator has, and how fast one goes round, in seconds.</summary>
    private const int BannerDots = 3;
    private const double BannerDotPeriod = 0.9;

    /// <summary>
    /// <i>Their go</i>, across the screen, for as long as control is off our side and at least
    /// <see cref="HexSandbox.TheirGoDwell"/>.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Entry 065 and brief five. Dropping the unfound hostile's slot leaves its turn passing with
    /// nothing on screen while time moves, which reads as a bug, so the pause gets an account. <b>One
    /// banner for a whole run of the other side's turns, never one per turn</b>: a player who counts
    /// banners over a round would otherwise have the enemy's count and their places in the order
    /// back, and a banner shown only for unfound hostiles would make its presence the tell. So it is
    /// the same for every hostile turn, found actor or not, and it names nobody.
    /// </para>
    /// <para>
    /// <b>The genre's answer rather than a consolation.</b> The amendment to brief five found this is
    /// the one turn-order element with positive evidence anywhere: XCOM 2 says <i>enemy turn</i>
    /// over the whole phase, and Into the Breach draws a full-width bar across the middle of the
    /// screen with the roster still visible beside it. This is that bar, with the strip beside it.
    /// </para>
    /// <para>
    /// <b>A message with an activity indicator inside it.</b> A spinner alone says the software is
    /// busy, which is a bug report; the words say somebody else is playing. In a capture the dots
    /// stand still at their first frame, because nothing animates while a picture is taken.
    /// </para>
    /// <para>
    /// <b>It stands aside while a window of ours is open</b>, and comes back when the window is run:
    /// the window is a question to us in the middle of their go, and it has its own block.
    /// </para>
    /// <para>
    /// A band across the width at a third of the way down, rather than dead centre: the camera
    /// follows whoever is up, so the middle of the screen is where our own soldier stands, and
    /// during a paused window the reactor is what a player is looking at.
    /// </para>
    /// </remarks>
    private void DrawTheirGo(SandboxFrame frame, Vector2 viewport)
    {
        // A window of ours is control coming back for the length of a question, and the window
        // block is the account of that moment; a band saying THEIR GO over the question would be
        // asking and refusing at once. The top block still says it is their go.
        if (frame.TheirGo is not { } shown || frame.Open is not null) return;

        const string words = "THEIR GO";
        const int size = 26;

        var band = new Rect2(Origin + new Vector2(0, viewport.Y * 0.34f), new Vector2(viewport.X, 46));
        _canvas.DrawRect(band, SandboxPalette.Panel);
        _canvas.DrawRect(new Rect2(band.Position, new Vector2(band.Size.X, 2)), SandboxPalette.SideHue(Side.Hostile));
        _canvas.DrawRect(new Rect2(band.Position + new Vector2(0, band.Size.Y - 2), new Vector2(band.Size.X, 2)),
            SandboxPalette.SideHue(Side.Hostile));

        var width = _font.GetStringSize(words, HorizontalAlignment.Left, -1, size).X;
        var dots = BannerDots * 14f;
        var left = band.Position.X + (band.Size.X - width - 18 - dots) / 2;
        var baseline = band.Position.Y + 33;

        _canvas.DrawString(_font, new Vector2(left, baseline), words, HorizontalAlignment.Left, -1, size,
            SandboxPalette.TextBright);

        var lit = (int)(shown / BannerDotPeriod * BannerDots) % BannerDots;
        for (var i = 0; i < BannerDots; i++)
            _canvas.DrawCircle(new Vector2(left + width + 18 + 7 + i * 14, baseline - 9), 4,
                i == lit ? SandboxPalette.TextBright : SandboxPalette.TextDim);
    }

    /// <summary>
    /// What our side perceived of the other side's go, as lines: who we found and lost sight of,
    /// where our side now has a contact marked, and every shot or burst that came our way.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Brief five's <i>settle first</i>: anything a hostile turn does that a player can perceive has
    /// to register, or the banner is a pause with no account. <b>These are countable on purpose.</b>
    /// A player genuinely perceived each of them, so a line per event is the game working; the banner
    /// is what is not counted. A stretch nobody of ours perceived anything of leaves nothing to read.
    /// </para>
    /// <para>
    /// <b>Read off our side's own knowledge, not off what the other side did.</b> The comparison is
    /// <see cref="SandboxFrame.Knowledge"/> — <c>Tactician.Known</c> merged across our soldiers, the
    /// list the picture is drawn from and the scorer weighs — as it stood when control left our
    /// side and as it stands now. A noise heard, a shot taken at one of ours, a comrade's call: each
    /// of them lands in that list or it was not perceived, so this cannot report something the rules
    /// say our side does not know. A marker is a place and never a name — the map draws it as an
    /// unnamed ghost — so a hostile we hold only a marker on is <i>somebody unseen</i>.
    /// </para>
    /// <para>
    /// The one thing read off the turns themselves is a shot or a burst at our own soldiers, because
    /// being shot at is perceived by being shot at whether or not it moves anybody's knowledge. The
    /// shooter goes through <see cref="SandboxFrame.Names"/>.
    /// </para>
    /// </remarks>
    public static IEnumerable<string> Perceived(SandboxFrame frame, IReadOnlyDictionary<UnitId, Threat> before)
    {
        foreach (var (id, now) in frame.Knowledge.OrderBy(pair => pair.Value.EyesOn ? 0 : 1)
                     .ThenBy(pair => pair.Value.EyesOn ? pair.Value.Unit.Name : pair.Value.Where.Position.ToString()))
        {
            before.TryGetValue(id, out var was);
            var held = before.ContainsKey(id);

            if (now.EyesOn)
            {
                if (!held || !was.EyesOn) yield return $"  found {now.Unit.Name} at {now.Unit.Position}";
                continue;
            }

            if (held && was.EyesOn)
            {
                yield return $"  lost sight of {now.Unit.Name}, last seen at {now.Where.Position}";
                continue;
            }

            if (!held || was.Where.Position != now.Where.Position || now.Credence > was.Credence)
                yield return $"  somebody unseen, marked at {now.Where.Position}";
        }

        // Somebody we could see before and hold nothing on at all now is gone from our side's file.
        foreach (var (id, was) in before.Where(pair => pair.Value.EyesOn && !frame.Knowledge.ContainsKey(pair.Key)))
            if (was.Unit.InPlay) yield return $"  lost track of {was.Unit.Name}";

        foreach (var turn in frame.Turns.Where(turn => turn.Unit.Side == Side.Hostile))
        foreach (var act in turn.Acts)
        {
            if (act.Fired is { Fired: true } shot && act.Order.Shot?.Target is { Side: Side.Player } target)
            {
                var hits = shot.Shots.Count(round => round.Hit);
                var result = hits == 0 ? "missed" : $"hit {hits} of {shot.Shots.Count} for {shot.TotalDamage}";
                yield return $"  {target.Name} shot at by {frame.Names([turn.Unit])}: {result}{(shot.TargetDown ? ", down" : "")}";
            }

            // A burst is perceived by whoever of ours it catches. One that catches nobody of ours is
            // a noise like any other, and lands in the knowledge above if anybody heard it; and who
            // else it caught is the other side's business.
            if (act.Threw is { Went: true } blast
                && blast.Hits.Where(hit => hit.Caught.Side == Side.Player).ToList() is { Count: > 0 } ours)
                yield return $"  a blast at {blast.Landing} caught "
                             + string.Join(", ", ours.Select(hit => $"{hit.Caught.Name} for {hit.Damage.ToVitality}{(hit.Down ? ", down" : "")}"))
                             + $", thrown by {frame.Names([turn.Unit])}";
        }
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

    /// <summary>How many bookings the strip shows.</summary>
    private const int StripSlots = 6;

    /// <summary>
    /// The next few bookings of soldiers the player knows about, with the round boundary marked, so
    /// the player can see the interleaving coming and how long it holds.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>A hostile nobody of ours has eyes on holds no slot at all</b> — entry 064, the user's
    /// decision, and brief five. It used to hold one reading <c>?</c>, which told a player that an
    /// enemy existed, how many there were, and roughly when each acted. The strip asks
    /// <see cref="SandboxFrame.Sees"/> and nothing else, so it has no opinion of its own about who
    /// is known. The genre is no help either way: none of the ten reference games draws a per-unit
    /// initiative strip at all, so this is a choice where the genre is silent rather than a
    /// departure from a standard.
    /// </para>
    /// <para>
    /// The slots are the first <see cref="StripSlots"/> <em>visible</em> bookings, so the strip is
    /// the same picture whether an unfound hostile is booked among them or not. Its reserve and its
    /// roll went with its name.
    /// </para>
    /// <para>
    /// <b>The round mark.</b> Initiative is rolled again every round, so an order read past the
    /// boundary is a guess the dice will revise; without the mark the whole strip reads as durable.
    /// Core books one turn ahead per soldier and the round is the booking's tick over
    /// <see cref="Battle.TicksPerRound"/>, so the mark is drawn before the first booking in a later
    /// round than the one being played. Where it falls among the visible slots says how many of the
    /// soldiers we know of are still to go this round, which is ours; an unfound hostile moves
    /// nothing.
    /// </para>
    /// <para>
    /// <b>A hostile found since our last order is outlined</b>, so a slot appearing mid-round reads
    /// as a discovery rather than as the strip rearranging itself.
    /// </para>
    /// </remarks>
    private void DrawOrderStrip(SandboxFrame frame, Vector2 viewport)
    {
        var origin = Origin + new Vector2(viewport.X - 190, 26);
        _canvas.DrawString(_font, origin, "TURN ORDER", HorizontalAlignment.Left, -1, 11, SandboxPalette.TextDim);

        var slots = frame.Battle.TurnOrder
            .Select(slot => (slot, unit: frame.Battle.GetUnit(slot.Unit)))
            .Where(pair => pair.unit is { InPlay: true } && frame.Sees(pair.unit))
            .Take(StripSlots)
            .ToList();

        var y = 12f;
        var marked = false;
        foreach (var (slot, unit) in slots)
        {
            var round = (int)(slot.ActAt / Battle.TicksPerRound);
            if (!marked && round > frame.Battle.Round)
            {
                marked = true;
                var rule = origin + new Vector2(0, y + 8);
                _canvas.DrawLine(rule, rule + new Vector2(170, 0), SandboxPalette.TextDim, 1);
                var label = $"round {round}";
                var width = _font.GetStringSize(label, HorizontalAlignment.Left, -1, 11).X;
                _canvas.DrawRect(new Rect2(rule + new Vector2(85 - width / 2 - 6, -7), new Vector2(width + 12, 14)),
                    SandboxPalette.Background);
                _canvas.DrawString(_font, rule + new Vector2(85 - width / 2, 4), label,
                    HorizontalAlignment.Left, -1, 11, SandboxPalette.TextBright);
                y += 18;
            }

            var box = new Rect2(origin + new Vector2(0, y), new Vector2(170, 22));
            y += 26;

            _canvas.DrawRect(box, SandboxPalette.Panel);
            _canvas.DrawRect(new Rect2(box.Position, new Vector2(4, box.Size.Y)), SandboxPalette.SideHue(unit!.Side));
            if (frame.Found.Contains(unit.Id))
                _canvas.DrawRect(box, SandboxPalette.SideHue(unit.Side), filled: false, width: 2);

            _canvas.DrawString(_font, box.Position + new Vector2(12, 16), unit.Name,
                HorizontalAlignment.Left, -1, 13, SandboxPalette.TextBright);
            _canvas.DrawString(_font, box.Position + new Vector2(120, 16), $"init {slot.Roll}",
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

        // A hostile up under the AI is the other side's situation, not ours: its reserve, its
        // shots, what it holds on each of ours, and everything the cursor line would measure from
        // its eyes. The clock and the fact that it is their go are all of it a player gets, found
        // hostile or not, so that what is left out cannot itself say which. SandboxFrame.Withheld.
        if (frame.Withheld)
        {
            lines.Add($"{Clock(frame)}    their go");
            DrawBlock(lines);
            return;
        }

        // Brief one: the mission, the clock and the weapon have no place on the map, and that is
        // the whole of what stays. The soldier's points, stance, facing and exposure are on the
        // soldier; the contacts are on the contacts; the cursor's figures are at the cursor; the
        // shot's terms are docked while aiming. The name stays beside the weapon because the weapon
        // is somebody's, and the storey because it is the camera's and hangs from nothing.
        lines.Add(
            active is null || frame.OutOfTime
                ? $"{Clock(frame)}    {(frame.OutOfTime ? "out of time" : "nobody left to act")}"
                : $"{Clock(frame)}    {active.Name}    {WeaponLine(active)}    storey {frame.Layer}");
        DrawBlock(lines);
    }

    // ---- on the things they describe ---------------------------------------------------

    /// <summary>Point sizes for what hangs on the map: a headline, and the terms under it.</summary>
    private const int HeadlineSize = 16;
    private const int TagSize = 11;
    private const int TagStep = 14;

    /// <summary>How wide the points bar under a soldier is, in pixels, for a full turn's allowance.</summary>
    private const float BarWidth = 150f;

    /// <summary>
    /// Everything that hangs from something on the map: the active soldier's points and exposure,
    /// what each contact is to that soldier, the shot's headline at its target, and the tile under the
    /// cursor.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Nothing is drawn while <see cref="SandboxFrame.Withheld"/>: a hostile up under the AI is the
    /// other side's situation, and every figure here would be it described from its own eyes.
    /// </para>
    /// <para>
    /// <b>Offsets are in pixels from the point the name label hangs from</b>, as the bill's glyphs
    /// are, and for the reason view.md gives for those: placed in metres, a tag lands on the name at
    /// any distance a rifle shot is taken from. The name sits just above that point and a hostile's
    /// rung just below it, so what describes a soldier stacks downwards from under the rung and a
    /// shot's headline sits above the name.
    /// </para>
    /// </remarks>
    private void DrawInPlace(SandboxFrame frame)
    {
        if (frame.Withheld || frame.Battle.Active is not { } active) return;

        // The cursor's tag last, so it is on top: it is where the eye already is, and with the held
        // key down the soldier's terms are a large block that would otherwise sit over it.
        DrawContacts(frame, active);
        DrawShotHeadline(frame);
        DrawSoldier(frame, active);
        DrawCursorTag(frame, active);
    }

    /// <summary>A plate's left edge and top pulled back inside the screen, so a tag near an edge is cut by nothing.</summary>
    private Vector2 Inside(Vector2 topLeft, Vector2 size)
    {
        var screen = _canvas.GetViewportRect().Size;
        return new Vector2(
            Mathf.Clamp(topLeft.X, 4, Mathf.Max(4, screen.X - size.X - 4)),
            Mathf.Clamp(topLeft.Y, 4, Mathf.Max(4, screen.Y - size.Y - 4)));
    }

    /// <summary>
    /// Under the soldier whose go it is: the points it has as a bar cut at the reserve's rungs, what
    /// each rung lets it spend, and how exposed it stands. Its terms under that while <c>Ctrl</c> is held.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The one figure that changes shape rather than only place — entry 067.</b> The panel printed
    /// <c>reserve 24, 17 if you stop here</c>, a slope, and the rules made the reserve a ladder with
    /// two cliffs in it: the point below which stopping banks nothing, and the point at which the bank
    /// first affords a shot and then the better one. Pips are the genre's answer for a handful of
    /// points; a turn here is fifty of them and the cliffs fall between pips, so this is a bar with a
    /// segment per rung in the rung's own colour, and the line under it says each cliff as <i>spend up
    /// to this much</i>. The ground's band edges are the same rungs in the same colours
    /// (<see cref="BattleView"/>), so the bar is the legend for them.
    /// </para>
    /// <para>
    /// A player who has spent nothing reads <i>aimed ≤5</i> and knows a five-point move is the most
    /// they may take and still hold an aimed shot, which is the brief's third test. The reserve the
    /// soldier already holds is not shown: it expires the moment its own turn comes round, so on
    /// the soldier whose go it is it reads nought, always, and the panel printing <c>reserve 0</c> for
    /// months was a figure with nothing in it.
    /// </para>
    /// </remarks>
    private void DrawSoldier(SandboxFrame frame, Unit active)
    {
        if (_crown(frame, active) is not { } crown || !_canvas.GetViewportRect().HasPoint(crown)) return;

        // Above the name, stacked upwards: the crown is just over the head, so anything hung below
        // it is drawn across the soldier it describes. The bar on top, the exposure nearest the name.
        var y = crown.Y - 22 - TagStep * 2 - 8;
        var left = crown.X - BarWidth / 2;

        var ladder = frame.Ladder;
        var top = System.Math.Max(active.Stats.ActionPoints, active.ActionPoints);
        float At(int points) => left + BarWidth * points / System.Math.Max(1, top);

        // The plate, the unspent points coloured by what stopping on them would bank, and a tick at
        // every rung — including the modes between the cheapest and the dearest, which the ground
        // does not carry.
        _canvas.DrawRect(new Rect2(left - 6, y - 4, BarWidth + 12, 16 + TagStep * 2), SandboxPalette.Panel);
        _canvas.DrawRect(new Rect2(left, y, BarWidth, 8), SandboxPalette.UnitShadow);

        for (var point = 0; point < active.ActionPoints; point++)
            _canvas.DrawRect(new Rect2(At(point), y, At(point + 1) - At(point) + 0.5f, 8), RungHue(ladder, point));

        foreach (var rung in ladder?.Rungs ?? [])
            _canvas.DrawLine(new Vector2(At(rung.Leftover), y - 3), new Vector2(At(rung.Leftover), y + 11),
                RungHue(ladder, rung.Leftover), 2);

        // The cliffs as moves: how much may be spent and still leave each rung. Dearest first, since
        // it is the one a player is most likely to be deciding against.
        var runs = new List<(string, Color)> { ($"{active.ActionPoints} AP", SandboxPalette.TextBright) };
        foreach (var rung in (ladder?.Rungs ?? []).OrderByDescending(rung => rung.Leftover))
        {
            var spend = active.ActionPoints - rung.Leftover;
            if (spend < 0) continue;
            runs.Add(("  ·  ", SandboxPalette.TextDim));
            runs.Add(($"{rung.Name} ≤{spend}", RungHue(ladder, rung.Leftover)));
        }
        DrawRuns(new Vector2(crown.X, y + 8 + TagStep), runs);

        // Our own exposure is exact and the rung the other side has reached is a rung: contract 3's
        // two halves on one line, which is where they always sat.
        var noticed = frame.Battle.HighestAwarenessOf(active);
        DrawRuns(new Vector2(crown.X, y + 8 + TagStep * 2),
        [
            ($"exposed {frame.Battle.ExposureOf(active):P0}", SandboxPalette.TextBright),
            ("  ·  they are ", SandboxPalette.TextDim),
            (noticed.ToString().ToUpperInvariant(), SandboxPalette.AlarmHue(noticed)),
        ]);

        if (frame.Details)
            DrawTag(new Vector2(crown.X, y - 12), SoldierTerms(frame, active).ToList(), lift: true);
    }

    /// <summary>A rung's colour, for a point on the bar: which band stopping with that many left falls in.</summary>
    private static Color RungHue(ReserveLadder? ladder, int leftover)
    {
        if (ladder is null) return SandboxPalette.TextDim;
        if (ladder.Better is { } better && leftover >= better.Leftover) return SandboxPalette.BandHue(SandboxPalette.Band.Better);
        if (ladder.Cheapest is { } cheap && leftover >= cheap.Leftover) return SandboxPalette.BandHue(SandboxPalette.Band.Cheapest);
        if (ladder.Floor is { } floor && leftover >= floor.Leftover) return SandboxPalette.BandHue(SandboxPalette.Band.Floor);
        return SandboxPalette.TextDim;
    }

    /// <summary>
    /// The active soldier's terms, for the held key: the bar they act from, what it holds, who a shout
    /// reaches, who has a line on it, and what the three posture keys would buy.
    /// </summary>
    private static IEnumerable<string> SoldierTerms(SandboxFrame frame, Unit active)
    {
        yield return $"they act from {frame.Battle.Tactics.Model.ActsOn.ToString().ToUpperInvariant()}";
        yield return HoldingLine(active);
        yield return EarshotOf(frame, active);
        yield return ViewedLine(frame, active);
        if (!frame.Battle.Tactics.Known(active).Any()) yield return "taking nobody seriously";
        foreach (var line in PostureLines(frame, active)) yield return line;
    }

    /// <summary>
    /// What each hostile the active soldier is taking seriously is to it — only while <c>Ctrl</c> is
    /// held, and hung from the hostile or from the ghost at its marker.
    /// </summary>
    /// <remarks>
    /// The headline on a contact is already there and is the map's: its name, its vitality and, under
    /// them, how far the other side has got — a rung. What was a line per contact in the panel is its
    /// terms: how far, how much of it this soldier has worked out, the worst it could do from there,
    /// and how much of this soldier it can make out. See <see cref="SeenLines"/> for why each is ours
    /// to show.
    /// </remarks>
    private void DrawContacts(SandboxFrame frame, Unit active)
    {
        if (!frame.Details) return;

        var battle = frame.Battle;
        foreach (var threat in battle.Tactics.Known(active))
        {
            var lines = SeenLines(frame, active, threat).ToList();

            if (threat.EyesOn && frame.Sees(threat.Unit))
            {
                if (_crown(frame, threat.Unit) is not { } crown) continue;

                // Under the rung, and under the bill's mark when this is the one a shot would tell.
                var marked = frame.StagedShot is { CanFire: true } plan && plan.Target == threat.Unit
                             && frame.Giveaway.Any(word => word.Learner != plan.Target);
                DrawTag(crown + new Vector2(0, marked ? 50 : 26), lines);
            }
            else if (_camera.Project(SandboxGeometry.NodeScene(battle.Map, threat.Where.Position)
                                     + Vector3.Up * (float)(StanceProfile.Standing.BodyHeight + 0.4)) is { } ghost)
            {
                // The view's ghost label hangs from this point; the terms go under it.
                DrawTag(ghost + new Vector2(0, 16), lines);
            }
        }
    }

    /// <summary>
    /// At the target, over its name: the shot's hit chance, and under it what the shot costs and what
    /// it is worth — or why there is no shot.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The brief's first test: with the cursor on a hostile the hit chance, the worth and the cost are
    /// readable without the eye leaving the target. Both photographed games keep exactly one figure at
    /// the body and dock the rest (<i>Settling One</i>), and the amendment's distance rule is why the
    /// figure is here: this is where the cursor already is.
    /// </para>
    /// <para>
    /// <b>Named <c>HIT</c>, and nothing under it is called hit.</b> Warhounds calls its headline
    /// <c>PRECISION</c> and one of its terms <c>Precision</c>, which is the naming warning the reference
    /// set has now found twice.
    /// </para>
    /// </remarks>
    private void DrawShotHeadline(SandboxFrame frame)
    {
        if (frame.StagedShot is not { } plan || _crown(frame, plan.Target) is not { } crown) return;
        if (!_canvas.GetViewportRect().HasPoint(crown)) return;

        if (!plan.CanFire)
        {
            DrawTag(crown + new Vector2(0, -30), [$"no shot: {plan.Refusal}"], centreOn: true, lift: true);
            return;
        }

        var worth = frame.Battle.Tactics.Appraise(plan);
        var sub = $"{plan.ApCost} AP  ·  worth {worth.Score:+0.00;-0.00}";
        var subWidth = _font.GetStringSize(sub, HorizontalAlignment.Left, -1, TagSize).X;
        var head = $"HIT {plan.HitChance:P0}";
        var headWidth = _font.GetStringSize(head, HorizontalAlignment.Left, -1, HeadlineSize).X;
        var width = Mathf.Max(subWidth, headWidth);

        var bottom = crown.Y - 24;
        _canvas.DrawRect(new Rect2(crown.X - width / 2 - 6, bottom - HeadlineSize - TagStep - 4, width + 12, HeadlineSize + TagStep + 8),
            SandboxPalette.Panel);
        _canvas.DrawString(_font, new Vector2(crown.X - headWidth / 2, bottom - TagStep), head,
            HorizontalAlignment.Left, -1, HeadlineSize, SandboxPalette.AimColor);
        _canvas.DrawString(_font, new Vector2(crown.X - subWidth / 2, bottom), sub,
            HorizontalAlignment.Left, -1, TagSize, SandboxPalette.TextBright);
    }

    /// <summary>
    /// Beside the tile under the cursor: what getting there costs, what stopping there would bank,
    /// and who would hear the walk. Its sight terms while <c>Ctrl</c> is held.
    /// </summary>
    /// <remarks>
    /// <para>
    /// This was the cursor line, and it was the clearest case of the amendment's distance complaint:
    /// a figure about the tile the player is pointing at, printed in the corner of the screen. Beside
    /// the tile rather than on it, since the tile carries its cost label already and the tag would sit
    /// on top of it.
    /// </para>
    /// <para>
    /// <b>The bank is the decision, and it is said in the band's colour.</b> The cost is how far; what
    /// the soldier will hold on arriving is whether to go — the same question the ground's band edges
    /// answer for every tile at once, asked of this one. Who would hear the walk stays on the default
    /// face of the tag because it is the warning a stealth game draws at the destination, and brief
    /// four's amendment found it drawn there in every one that draws it.
    /// </para>
    /// <para>
    /// Not drawn while aiming: a click on the ground then backs out and moves nobody, so a tag pricing
    /// the move would be promising one — the path preview is withheld for the same reason. Nor over a
    /// soldier the picture shows, since a hostile there has the shot's headline and one of ours has
    /// its own figures.
    /// </para>
    /// </remarks>
    private void DrawCursorTag(SandboxFrame frame, Unit active)
    {
        if (frame.Aim is not null || frame.Hover is not { } node || frame.HoveredUnit is not null) return;
        if (_camera.Project(SandboxGeometry.NodeScene(frame.Battle.Map, node)) is not { } at) return;

        var lines = new List<(string Text, Color Hue)>();

        if (node != active.Position)
        {
            if (frame.Reach.CostTo(node) is { } cost)
            {
                var left = active.ActionPoints - cost;
                var banks = frame.Battle.Reactions.Banked(left);
                var affords = frame.Ladder?.Rungs.Where(rung => rung.Price > 0 && left >= rung.Leftover).MaxBy(rung => rung.Price);
                lines.Add(($"{cost} AP", SandboxPalette.TextBright));
                lines.Add((banks == 0 ? "then banks nothing" : $"then banks {banks}{(affords is null ? "" : $": {affords.Name}")}",
                    RungHue(frame.Ladder, left)));

                if (NoiseLine(frame, node) is { Length: > 0 } heard) lines.Add((heard, SandboxPalette.OverwatchHue));
            }
            else lines.Add(("out of reach", SandboxPalette.TextDim));
        }

        if (frame.Details)
        {
            lines.Add((SightLine(frame, node), SandboxPalette.TextDim));
            if (AttentionLine(frame, node) is { Length: > 0 } attention) lines.Add((attention, SandboxPalette.TextDim));
            if (LoudnessLine(frame, node) is { Length: > 0 } loud) lines.Add((loud, SandboxPalette.TextDim));
        }

        if (lines.Count == 0) return;
        DrawTagLeft(at + new Vector2(22, -TagStep), lines);
    }

    /// <summary>A block of small lines centred under a point, on a plate.</summary>
    /// <param name="centreOn">Centre every line, rather than centre the block and set its lines flush left.</param>
    /// <param name="lift">Hang the block upwards from the point rather than down from it.</param>
    private void DrawTag(Vector2 at, IReadOnlyList<string> lines, bool centreOn = false, bool lift = false)
    {
        // A tag whose thing is off the screen is not drawn at all, rather than pulled in to an edge:
        // pinned there it would describe something the picture is not showing, attached to nothing.
        if (lines.Count == 0 || !_canvas.GetViewportRect().HasPoint(at)) return;

        var width = lines.Max(line => _font.GetStringSize(line, HorizontalAlignment.Left, -1, TagSize).X);
        var top = lift ? at.Y - (lines.Count - 1) * TagStep : at.Y;

        var size = new Vector2(width + 12, lines.Count * TagStep + 5);
        var wanted = new Vector2(at.X - width / 2 - 6, top - TagSize - 1);
        var plate = Inside(wanted, size);
        var shift = plate - wanted;

        _canvas.DrawRect(new Rect2(plate, size), SandboxPalette.Panel);

        for (var i = 0; i < lines.Count; i++)
        {
            var x = centreOn
                ? at.X - _font.GetStringSize(lines[i], HorizontalAlignment.Left, -1, TagSize).X / 2
                : at.X - width / 2;
            _canvas.DrawString(_font, new Vector2(x, top + i * TagStep) + shift, lines[i],
                HorizontalAlignment.Left, -1, TagSize, SandboxPalette.TextBright);
        }
    }

    /// <summary>A block of small coloured lines, flush left from a point, on a plate.</summary>
    private void DrawTagLeft(Vector2 at, IReadOnlyList<(string Text, Color Hue)> lines)
    {
        if (!_canvas.GetViewportRect().HasPoint(at)) return;

        var width = lines.Max(line => _font.GetStringSize(line.Text, HorizontalAlignment.Left, -1, TagSize).X);
        var size = new Vector2(width + 12, lines.Count * TagStep + 5);
        var wanted = new Vector2(at.X - 6, at.Y - TagSize - 1);
        var plate = Inside(wanted, size);
        var shift = plate - wanted;

        _canvas.DrawRect(new Rect2(plate, size), SandboxPalette.Panel);

        for (var i = 0; i < lines.Count; i++)
            _canvas.DrawString(_font, at + shift + new Vector2(0, i * TagStep), lines[i].Text,
                HorizontalAlignment.Left, -1, TagSize, lines[i].Hue);
    }

    /// <summary>One line of differently coloured pieces, centred on a point, on a plate of its own.</summary>
    private void DrawRuns(Vector2 centre, IReadOnlyList<(string Text, Color Hue)> runs)
    {
        var widths = runs.Select(run => _font.GetStringSize(run.Text, HorizontalAlignment.Left, -1, TagSize).X).ToList();
        var size = new Vector2(widths.Sum() + 12, TagStep + 5);
        var wanted = new Vector2(centre.X - widths.Sum() / 2 - 6, centre.Y - TagSize - 1);
        var plate = Inside(wanted, size);
        var x = plate.X + 6;
        centre.Y += plate.Y - wanted.Y;

        _canvas.DrawRect(new Rect2(plate, size), SandboxPalette.Panel);

        for (var i = 0; i < runs.Count; i++)
        {
            _canvas.DrawString(_font, new Vector2(x, centre.Y), runs[i].Text, HorizontalAlignment.Left, -1, TagSize, runs[i].Hue);
            x += widths[i];
        }
    }

    // ---- the shot's terms, docked ------------------------------------------------------

    /// <summary>How many characters a line of the docked terms runs to before it wraps.</summary>
    private const int TermsWrap = 72;

    /// <summary>
    /// The shot's terms, docked at the right edge above the legend, for as long as the player is
    /// aiming: the mode and the ways out of it, the headline, and — unless folded — the price, the
    /// plates, who it tells and what it achieves.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b><i>Settling One</i>, and it overturned the amendment.</b> The amendment said a held key for
    /// <i>show me the terms</i>. Both games photographed while aiming open the breakdown the moment the
    /// firing mode is entered, with no further input, and dock it away from the target: XCOM 2 at the
    /// bottom centre, Warhounds at the right edge. Firing is a mode here already (entry 084), so this
    /// hangs on it. The right edge is Warhounds' place and the one this screen has free — the bottom
    /// centre is under the legend.
    /// </para>
    /// <para>
    /// <b>The fold is a preference, not a gesture per shot</b>, which is the whole of what XCOM 2 gives
    /// a player over its breakdown: fold it once and it stays folded for the next target, and here for
    /// the next soldier too. <c>P</c> or a click on the switch. Folded, the mode line and the headline
    /// stay: the <c>AIMING</c> line is what tells a player space fires, and a fold that hid it would
    /// put a shot on the key a player presses to pass.
    /// </para>
    /// </remarks>
    private void DrawTerms(SandboxFrame frame, Vector2 viewport, float bottom)
    {
        FoldSwitch = new Rect2();
        if (frame.Aim is null || frame.StagedShot is not { } plan) return;

        var lines = new List<(string Text, Color Hue)>();
        foreach (var line in AimLines(frame)) lines.Add((line, SandboxPalette.AimColor));

        if (!plan.CanFire)
        {
            lines.Add(($"NO SHOT — {plan.Refusal}", SandboxPalette.TextBright));
        }
        else
        {
            var listed = plan.ApCost == plan.Mode.ApCost ? "" : $" (list {plan.Mode.ApCost})";
            lines.Add(($"HIT {plan.HitChance:P0}    for {plan.ApCost} AP{listed}", SandboxPalette.TextBright));

            if (!frame.TermsFolded)
            {
                foreach (var line in ShotLines(plan)) lines.Add((line, SandboxPalette.TextDim));
                foreach (var line in BillLines(frame)) lines.Add((line, SandboxPalette.OverwatchHue));
                foreach (var line in WorthLines(frame)) lines.Add((line, SandboxPalette.TextDim));
            }
        }

        // A refused shot has no terms to fold, and a switch that did nothing would be a lie.
        var fold = !plan.CanFire ? "" : frame.TermsFolded ? "P: show the terms" : "P: fold the terms";
        if (fold.Length > 0) lines.Add((fold, SandboxPalette.TextDim));

        var widest = lines.Max(line => _font.GetStringSize(line.Text, HorizontalAlignment.Left, -1, LineSize).X);
        var left = Origin.X + viewport.X - 28 - widest;
        var top = Origin.Y + bottom - (lines.Count - 1) * LineHeight;

        _canvas.DrawRect(new Rect2(left - 10, top - LineSize - 2, widest + 20, lines.Count * LineHeight + 10), SandboxPalette.Panel);
        _canvas.DrawRect(new Rect2(left - 10, top - LineSize - 2, widest + 20, 2), SandboxPalette.AimColor);

        for (var i = 0; i < lines.Count; i++)
            _canvas.DrawString(_font, new Vector2(left, top + i * LineHeight), lines[i].Text,
                HorizontalAlignment.Left, -1, LineSize, lines[i].Hue);

        if (fold.Length == 0) return;
        var last = top + (lines.Count - 1) * LineHeight;
        var foldWidth = _font.GetStringSize(fold, HorizontalAlignment.Left, -1, LineSize).X;
        FoldSwitch = new Rect2(left - 4, last - LineSize - 2, foldWidth + 8, LineHeight);
    }

    /// <summary>The top block: whatever lines are not empty, on a panel, from the top-left.</summary>
    private void DrawBlock(List<string> lines)
    {
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

        // What our side perceived while it was their go goes nearest the legend, under the reaction
        // line, because it is the account of the pause the banner covered. A line per thing
        // perceived, and no block at all when nothing was — see Perceived.
        if (frame.Perceived.Count > 0)
            lines.InsertRange(0, frame.Perceived.Prepend("WHILE IT WAS THEIR GO"));

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
        var offers = frame.Answerable;
        var answered = offers.Count(o => window.Placements.Any(p => p.Reactor == o.Reactor));

        // Named as the picture names them: a hostile mover nobody of ours has eyes on is somebody
        // unseen here as everywhere else, since the window is part of the pause brief five is about.
        var what = window.IsAmbush
            ? $"{frame.Names([window.SprungBy!])} springs on {frame.Names([mover])}, standing at {mover.Position}"
            : $"{frame.Names([mover])} has paid for {window.Move.Start} to {window.Move.Destination}, "
              + $"{window.Move.Duration} ticks, and not walked it yet";

        // Only the offers a player is handed, counted and listed — see SandboxFrame.Answerable. A
        // count of everybody's would say how many of the other side have a line on the mover.
        var lines = new List<string> { $"WINDOW OPEN — {what}" };

        if (offers.Count == 0)
        {
            lines.Add("nothing here is yours to answer    space: run it");
            return lines;
        }

        lines.Add($"space: run it — every answer not changed stands    1-9: change {offers[Chosen(frame, offers)].Reactor.Name}'s    "
                  + (offers.Count > 1 ? "tab: somebody else's    " : "")
                  + $"{answered} of {offers.Count} changed");

        for (var i = 0; i < offers.Count; i++)
        {
            var offer = offers[i];
            var chosen = i == Chosen(frame, offers);
            var placed = window.Placements.FirstOrDefault(p => p.Reactor == offer.Reactor);

            var who = $"{(chosen ? ">" : " ")} {offer.Reactor.Name} ({offer.Kind.ToString().ToLowerInvariant()})"
                      + $"    reserve {offer.Reserve}, purse {offer.Purse}";

            // The default is drawn as the answer each soldier is already giving, not as a suggestion
            // beside a question. That is the brief: the genre's overwatch is a state and not an
            // interaction, and the window recovers it as a default — a soldier on the arc does what
            // it was set up to do unless somebody says otherwise, and space is saying nothing.
            if (placed is not null) { lines.Add($"{who}    CHANGED TO: {placed}"); continue; }
            if (!chosen) { lines.Add($"{who}    will: {offer.Recommended}"); continue; }

            lines.Add(who);
            for (var n = 0; n < offer.Options.Count; n++)
            {
                var option = offer.Options[n];
                var worth = window.Appraise(option);

                lines.Add(
                    $"      {n + 1}  {option}    {worth.Score:+0.00;-0.00} ({Terms(worth)})"
                    + (option == offer.Recommended ? "    ← will, unless changed" : ""));
            }
        }

        return lines;
    }

    /// <summary>The chooser, kept inside the list it indexes — it can outlive a change in that list's length by a frame.</summary>
    private static int Chosen(SandboxFrame frame, IReadOnlyList<ReactionOffer> offers)
        => System.Math.Clamp(frame.Chooser, 0, offers.Count - 1);

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
            + "space: fire when aiming, else end turn    right-click or esc: back out    P: fold the shot's terms",
        "C: stance    Z/X: turn on the spot    V: overwatch arc    B: arm/spring ambush    T: leave the field    L: call it in"
            + "    hold Ctrl: every figure's terms",
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

    /// <summary>What the soldier is holding, and what having it already pointed is worth.</summary>
    /// <remarks>
    /// <b>How exposed this soldier is and how alarmed the other side has become</b> sit on one line
    /// under the soldier — see <see cref="DrawSoldier"/> — because they are the two halves of contract 3
    /// side by side, which is the clearest place to see what the asymmetry actually is: exposure is our
    /// own silhouette to the percent, the alarm is a rung and never the certainty behind it.
    /// <para>
    /// The bar the rung is read against is one of the soldier's terms rather than its headline, and it
    /// is named because a rung on its own does not say what it means. <c>SEARCHING</c> is not a mood: it
    /// is the point at which <see cref="Hexcom.Core.Tactics.UtilityModel.ActsOn"/> says a soldier who
    /// could shoot at you will.
    /// </para>
    /// </remarks>
    private static string HoldingLine(Unit active)
        => active.Overwatch is { } order
            ? $"holding a {order.Arc.Name} arc {order.Centre} (x{order.Arc.AimBonus:0.00} to hit)"
            : "watching nothing in particular";

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

        return $"your attention {frame.Battle.Awareness.AttentionOn(active, node):P0}";
    }

    /// <summary>That the firing mode is up, at whom, and the three ways out of it — the head of the docked terms.</summary>
    /// <remarks>
    /// A line of its own and in capitals, because a mode nobody can see they are in is the whole
    /// failure the genre's cancel convention exists to prevent: the space bar ends the turn when
    /// this line is absent and fires when it is present, and that is only fair if it is impossible
    /// to miss which. It says what confirms and what backs out in so many words, which is the brief's
    /// test — a player backs out of a half-entered order without having been told a key.
    /// <para>
    /// Two lines since it was docked: the dock is narrower than the panel was, and splitting who from
    /// how-to is splitting by purpose, which is the fix every legend in this file has taken.
    /// </para>
    /// </remarks>
    private static IEnumerable<string> AimLines(SandboxFrame frame)
    {
        if (frame.Aim is not { } quarry) yield break;

        var targets = frame.Targets;
        var which = targets.Count > 1 ? $", {IndexOf(targets, quarry) + 1} of {targets.Count} in sight    tab: next" : "";

        yield return $"AIMING at {quarry.Name}{which}";
        yield return "space, enter or click them again: fire    right-click or esc: back out";
    }

    private static int IndexOf(IReadOnlyList<Unit> units, Unit unit)
    {
        for (var i = 0; i < units.Count; i++)
            if (units[i] == unit) return i;
        return -1;
    }

    /// <summary>The shot as a physical event, under the headline: the weapon, how much of it lands, and the plates it can reach.</summary>
    private static IEnumerable<string> ShotLines(ShotPlan plan)
    {
        var armour = plan.Target.Protection;

        var glancing = plan.GlancingFactor < 0.995
            ? $"    {plan.GlancingFactor:P0} of it lands"
            : "";
        yield return $"{plan.Mode.Name} with the {plan.Weapon.Name} ({plan.Weapon.Kind}){glancing}";

        // A body is a hexagon, so a shot is never at one plate. Show the spread and what each is
        // still carrying, because which side is worn is what turning is for.
        var faces = string.Join("  ·  ", plan.Aspects.Select(a =>
            $"{a.Face} {a.Share:P0} s{armour.ShieldOn(a.Face)}/p{armour.ArmourOn(a.Face)}"));
        foreach (var line in Wrap(faces, TermsWrap)) yield return "  " + line;
    }

    /// <summary>
    /// Who the shot would give the shooter away to — the bill beside the price. Brief four.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The oldest open gap in the interface audit, entry 012's second item. The worth line has
    /// always charged a shot for what it announces, inside its spared term, and nothing said to
    /// whom: the player saw the price and not the bill. XCOM warns before concealment breaks and
    /// does not say who hears it; this is the game where the <em>who</em> matters most, because
    /// the fight is decided by who found whom first.
    /// </para>
    /// <para>
    /// <b>Names, not figures</b>, for the reason <see cref="NoiseLine"/> gives: the figures behind
    /// them are how far each hostile's file on us would move, and that stays a rung. And a hostile
    /// nobody of ours has eyes on is <i>somebody unseen</i> — see <see cref="SandboxFrame.Names"/>.
    /// The target is named first and marked, since being shot at tells the target outright whether
    /// or not a round lands, and a bill that listed only bystanders would read as though the target
    /// might not notice.
    /// </para>
    /// <para>
    /// It says <i>tells</i> rather than <i>wakes</i> on purpose. Everyone named gains certainty
    /// about the shooter; whether it carries any of them over a rung is the enemy's arithmetic, and
    /// the rung under their feet says so on the next look.
    /// </para>
    /// </remarks>
    private static IEnumerable<string> BillLines(SandboxFrame frame)
    {
        if (frame.StagedShot is not { CanFire: true } plan) yield break;

        var told = frame.Giveaway.Select(word => word.Learner).ToList();
        if (told.Count == 0) { yield return "it tells nobody anything they do not already know"; yield break; }

        var others = told.Where(u => u != plan.Target).ToList();
        var target = told.Contains(plan.Target) ? $"{plan.Target.Name} (shot at)" : "";

        // The last clause is the preview's honest limit rather than decoration. Being shot at makes
        // the target pass word to whoever it can reach, and Core's preview leaves that relay out —
        // measured on the waystation, a shot at Teague told Cobb as well as the three it named. Until
        // the preview includes it (decisions.md), the line says there is more rather than guess who.
        var bill = "it tells " + string.Join(", ",
                       new[] { target, others.Count > 0 ? frame.Names(others) : "" }.Where(part => part.Length > 0))
                   + $" — and whoever {plan.Target.Name} passes it on to";

        foreach (var (line, i) in Wrap(bill, TermsWrap).Select((line, i) => (line, i)))
            yield return i == 0 ? line : "  " + line;
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
    /// <b>Every term, as the scorer kept them.</b> This line used to say <i>harm less spent</i> in so
    /// many words, which was true when a shot's appraisal was those two and stopped being true when
    /// Core priced what a shot gives away — <c>Tactician.Appraise</c> now carries it in
    /// <b>Spared</b>, and what it costs the mission in <b>Prospect</b>. Brief one found it by moving
    /// the line: on the waystation a shot read <i>worth −57.98 (harm 3.67 less spent 1.25)</i>, a sum
    /// its own terms could not make. Both new terms are priced from announcements to named listeners
    /// and the rung the mission is lost at, which the bill line already shows, so there is nothing in
    /// them contract 3 keeps back.
    /// </para>
    /// </remarks>
    private static IEnumerable<string> WorthLines(SandboxFrame frame)
    {
        if (frame.StagedShot is not { CanFire: true } plan) yield break;

        var expect = frame.Battle.Gunnery.Expect(plan);
        var worth = frame.Battle.Tactics.Appraise(plan);

        yield return $"it achieves {expect.Vitality:0.0} vitality  ·  {expect.PlateStripped:0.0} plate  ·  "
                     + $"{expect.ShieldStripped:0.0} shield  ·  {expect.DownChance:P0} down";
        yield return $"  worth {worth.Score:+0.00;-0.00} ({Terms(worth)})";
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
    /// A tag on the contact now, which was always the argument's conclusion: one line per contact in
    /// the panel was the fix for the joined version running under the strip, and splitting by contact
    /// was the version that kept working as contacts accumulated. Hung from the contact, the split is
    /// the map's and there is no list to overflow. A contact believed at a marker hangs from the ghost
    /// at the marker, where the credence already is; its distance is traced to the marker for the
    /// reason above.
    /// <para>
    /// Whether it can see this soldier goes on the same tag, since <see cref="ViewedLine"/> is naming
    /// which enemy the exposure is to and that enemy is right here. One nobody of ours has eyes on is
    /// named on the soldier's own terms instead, as <i>somebody unseen</i>.
    /// </para>
    /// </remarks>
    private static IEnumerable<string> SeenLines(SandboxFrame frame, Unit active, Threat threat)
    {
        var battle = frame.Battle;

        var range = battle.Sight.Trace(active.Vantage, threat.Where.Vantage).Distance;
        yield return $"{range:0.0} m  ·  {Held(battle, active, threat.Unit)}";

        yield return WorstShotAt(battle, threat, active) is { } worst
            ? $"worst on you {battle.Tactics.Worth(worst):0.0} ({worst.Mode.Name} {worst.HitChance:P0})"
            : "no shot on you";

        if (threat.EyesOn && frame.Sees(threat.Unit) && battle.Look(threat.Unit, active) is { CanSee: true } sight)
            yield return $"sees you {sight.Exposure:P0}";
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

        return $"you hold {contact.Detection:0}/{full:0}";
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
        if (loudness <= 0) return "";

        // Through Names, so a listener nobody of ours has found is somebody unseen. This line used
        // to name every listener in earshot, found or not, which on the waystation read out most of
        // the garrison's names from the first move of the mission. Brief four found it copying it.
        var listeners = frame.Battle.Awareness.WouldHear(active, node, loudness).Select(word => word.Learner).ToList();

        return listeners.Count == 0 ? "" : $"heard by {frame.Names(listeners)}";
    }

    /// <summary>How loud the walk to a place would be — one of the cursor's terms, since who hears it is the headline.</summary>
    private static string LoudnessLine(SandboxFrame frame, NodeId node)
    {
        if (frame.Battle.Active is not { } active) return "";
        if (!frame.Reach.TryGetPath(node, out var path) || path.Count == 0) return "";

        var loudness = frame.Battle.Loudness(active, path);
        return loudness <= 0 ? "silent" : $"noise {loudness:0}";
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
            if (turn.Acts.Count == 0)
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
