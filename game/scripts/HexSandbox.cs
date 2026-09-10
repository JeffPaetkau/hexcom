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
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>
/// A flat debug view of a battle: click to move whoever is up, space to pass the turn, and
/// watch the order strip decide who goes next.
/// </summary>
/// <remarks>
/// <para>
/// Everything interesting here is a query against <c>Hexcom.Core</c>. This layer draws and reads
/// input and does nothing else — no rule may be implemented in it, or the rules stop being
/// testable headless.
/// </para>
/// <para>
/// The node keeps the input handling and the state of the moment; the map and the deployments
/// are <see cref="SandboxScenario"/>'s, and the drawing is split between
/// <see cref="BattleView"/> (the world) and <see cref="BattleHud"/> (the readouts), which are
/// presentation and interface respectively and are separate types so that two people can work on
/// them at once. Between the node and both of them sits <see cref="SandboxCamera"/>, which holds
/// the <see cref="SandboxScale"/> that is the only place knowing the difference between a metre
/// and a pixel.
/// </para>
/// </remarks>
public partial class HexSandbox : Node2D
{
    /// <summary>
    /// Hex radius in pixels — how big the map is drawn, and nothing else.
    /// </summary>
    /// <remarks>
    /// Exported because rendering scale is a matter of taste. It is emphatically <i>not</i> the
    /// world scale: that is <see cref="SandboxScale.MetresPerHexSize"/>, it is a constant, and
    /// changing this one must not move it. The two used to be the same number, which is the bug
    /// <c>docs/decisions.md</c> entry 002 describes.
    /// </remarks>
    [Export] public float HexSize { get; set; } = 44f;

    [Export] public int Seed { get; set; } = 7;

    /// <summary>
    /// Which of <see cref="SandboxScenario.All"/> to open with. Blank takes the first.
    /// </summary>
    /// <remarks>
    /// The waystation, by default. The compound is still here and still reachable, but every
    /// range in the game overshoots it by a factor of three — <c>docs/decisions.md</c> entry 007
    /// — so a sandbox that opens on it is a sandbox in which none of the distances mean anything.
    /// </remarks>
    [Export] public string Scenario { get; set; } = "";

    private readonly Dictionary<NodeId, SightResult> _sight = [];

    private Battle _battle = null!;
    private SandboxScenario _scenario = null!;
    private SandboxCamera _camera = null!;
    private BattleView _view = null!;
    private BattleHud _hud = null!;
    private SandboxCapture? _capture;

    private ReachabilityResult _reach = null!;
    private NodeId? _hover;
    private int _layer;

    /// <summary>Where a middle-button drag started, while one is in progress.</summary>
    private Vector2? _dragging;

    /// <summary>What the last committed move got shot at with, if anything. Debug readout only.</summary>
    private string _lastWindow = "";

    /// <summary>
    /// Whether the hostile side is being driven by <see cref="Commander"/> rather than by hand.
    /// </summary>
    /// <remarks>
    /// Off by default, because the sandbox exists to try things on both sides. Switching it on
    /// is the first time anybody watches the enemy behave like an enemy — entry 009 in
    /// <c>docs/decisions.md</c> — and what makes every readout in the HUD a readout of something
    /// the other side is visibly acting on rather than a figure with nothing to check it against.
    /// </remarks>
    private bool _auto;

    /// <summary>
    /// Whether a move stops with its reaction window open for somebody to answer by hand.
    /// </summary>
    /// <remarks>
    /// Off by default, so that every command and every habit from before the window existed
    /// still means what it meant: with it off a move is <c>Battle.Move</c>, which is
    /// <c>Commit</c> and <c>Resolve</c> with every recommendation taken between them. With it on
    /// the sandbox stops in the gap — see <see cref="Open"/> — and that gap is the whole of
    /// entry 040.
    /// </remarks>
    private bool _byHand;

    /// <summary>A move of ours that is paid for and not yet resolved.</summary>
    private MoveCommitment? _committed;

    /// <summary>A commander that stopped its turn at a window rather than answering it.</summary>
    private Commander? _handed;

    /// <summary>Which of the open window's offers the keyboard is pointed at.</summary>
    private int _chooser;

    /// <summary>
    /// The reaction window waiting to be answered, from whichever side opened it.
    /// </summary>
    /// <remarks>
    /// Two ways in and one way out. One of ours moves and we hold the commitment; or a hostile
    /// moves under a <see cref="Commander"/> built to hand its windows out, and we hold the
    /// commander. Everything downstream — the readout, the keys, the script steps — asks this
    /// and does not care which, because from the interface's side they are the same question:
    /// somebody is part way through a move that is already paid for, and the people who can
    /// answer it have not yet.
    /// </remarks>
    private ReactionWindow? Open => _committed?.Window ?? _handed?.Waiting;

    /// <summary>The turns the AI has taken since a person last did anything. Newest last.</summary>
    private readonly List<TakenTurn> _turns = [];

    public override void _Ready()
    {
        var font = ThemeDB.FallbackFont;

        _capture = SandboxCapture.Requested();
        _camera = new SandboxCamera(HexSize);
        _view = new BattleView(this, _camera, font);
        _hud = new BattleHud(this, font);

        // A capture has to be reproducible, and input is the one thing here that is not: the
        // window opens under whatever the pointer was already doing, so the cursor readout and
        // the previewed path land in the picture and two runs disagree. Capturing is therefore
        // deaf as well as brief.
        SetProcess(_capture is not null);
        SetProcessUnhandledInput(_capture is null);

        NewBattle();
    }

    public override void _Process(double delta) => _capture?.Tick(this);

    /// <summary>
    /// Load the scenario asked for and put everybody on it.
    /// </summary>
    /// <remarks>
    /// The map comes from <c>content/</c> and the deployments do not, because there is nowhere
    /// yet to put them. Both are <see cref="SandboxScenario"/>'s problem; this method's job is
    /// only to hand the rules the metres layout and never the pixels one, which is the single
    /// mistake this file has actually made. See <see cref="SandboxScale"/>.
    /// </remarks>
    private void NewBattle()
    {
        _scenario = SandboxScenario.ByName(_capture?.Scenario ?? (Scenario.Length > 0 ? Scenario : null));

        _battle = new Battle(_scenario.LoadMap(), _camera.Scale.World, seed: Seed);
        _scenario.DeployInto(_battle);
        _battle.Start();

        _auto = _capture?.Automatic ?? false;
        _byHand = _capture?.AnswerWindowsByHand ?? false;
        _turns.Clear();
        _committed = null;
        _handed = null;
        _chooser = 0;
        _lastWindow = "";
        _hover = null;

        Settle();

        _layer = _battle.Active?.Position.Layer ?? 0;

        // The waystation is 85 metres across and does not fit on a screen at a size anybody can
        // read a tile at, so a battle opens looking at whoever is up rather than at the origin,
        // which is only where the compound happened to be centred.
        if (_battle.Active is { } up) _camera.LookAt(up.Position.Tile.Hex);

        CameraMoved();
        Recalculate();

        // A capture is deaf, so everything a person would have done has to arrive as an argument
        // list. It runs here, after the deployment and against the same methods the keys call.
        if (_capture is { Script: var script } && !script.IsEmpty) Run(script);
    }

    /// <summary>
    /// Give every hostile turn that is up to the AI, if the hostile side is on automatic, and
    /// keep what it decided for the HUD.
    /// </summary>
    /// <remarks>
    /// The record is replaced rather than appended to, so what is on screen is always what the
    /// other side did <em>since you last acted</em> — several turns of it when the initiative
    /// order puts two or three of theirs together, which is exactly when a reader most needs to
    /// know which of them did what. Nothing is kept from before, because a readout that scrolls
    /// is a log, and the HUD is not one.
    /// <para>
    /// The battle does not stop when one side is gone; the survivors keep taking turns. So this
    /// has to, or a side on automatic with nobody left to fight would take turns forever. It
    /// stops for an open window too: a commander handing its windows out has paused mid-turn
    /// and the next thing that happens is a person answering it, not another soldier going.
    /// </para>
    /// </remarks>
    private void Settle(bool keepRecord = false)
    {
        if (Open is not null) return;
        if (!_auto || _battle.Active is not { Side: Side.Hostile }) return;

        if (!keepRecord) _turns.Clear();
        while (_auto && Open is null && !_battle.IsDecided && _battle.Active is { Side: Side.Hostile } unit)
            TakeTurnWithAi(unit);
    }

    /// <summary>
    /// Let <see cref="Commander"/> take the active unit's whole turn, and remember why.
    /// </summary>
    /// <remarks>
    /// The commander is built to hand its windows out whenever the sandbox is answering them by
    /// hand, which is the seam entry 022 asked for and entry 040 built: it stops with the window
    /// open, we hold the commander, and <see cref="ResolveOpenWindow"/> calls <c>Resume</c>. The
    /// turn is one turn either way; how many times it pauses inside is not the caller's problem.
    /// </remarks>
    private void TakeTurnWithAi(Unit unit)
    {
        var commander = new Commander(
            _battle, windows: _byHand ? WindowAnswer.HandedOut : WindowAnswer.Recommended);

        commander.TakeTurn();
        SkipEmptyWindows(commander);
        Record(unit, commander);
    }

    /// <summary>
    /// Run straight past any window nobody was offered anything in.
    /// </summary>
    /// <remarks>
    /// A commander handing its windows out stops at every one of them, which is right for Core —
    /// it cannot know whether the thing answering wants to look at an empty list — and wrong for
    /// a screen. Stopping to ask a question with no answers in it is a worse interface than not
    /// stopping, and it is the common case rather than the corner: most moves on a map this size
    /// are watched by nobody, so without this the sandbox stops twice a turn to say <em>0 of 0
    /// answered</em> and a script has to spell out a <c>--resolve</c> for each.
    /// </remarks>
    private static void SkipEmptyWindows(Commander commander)
    {
        while (commander.Waiting is { Offers.Count: 0 }) commander.Resume();
    }

    /// <summary>
    /// Write what a commander has done so far into the readout, replacing its own earlier entry.
    /// </summary>
    /// <remarks>
    /// <c>Commander.Taken</c> is cumulative across however many windows a turn stopped at, so
    /// resuming appends to the same list rather than starting a new one. The readout has to
    /// follow that or a turn interrupted twice shows up as three soldiers.
    /// </remarks>
    private void Record(Unit unit, Commander commander)
    {
        // Core hands back an Act per order now, with the outcome beside it. The readout still
        // wants only the orders; see decisions.md entry 022, where View asked for the outcomes.
        var turn = new TakenTurn(unit, [.. commander.Taken.Select(a => a.Order)], unit.Reserve);

        if (_turns.Count > 0 && _turns[^1].Unit == unit) _turns[^1] = turn;
        else _turns.Add(turn);

        if (commander.Waiting is not null) { _handed = commander; _chooser = 0; }
    }

    /// <summary>
    /// What follows anything a person did: the other side gets its go if it is on automatic,
    /// and the screen follows whoever is up next.
    /// </summary>
    private void AfterAction(bool keepRecord = false)
    {
        var before = _battle.Active;
        Settle(keepRecord);
        if (_battle.Active is { } next && next != before) _layer = next.Position.Layer;
        Recalculate();
        FollowActive();
    }

    /// <summary>
    /// Re-ask the rules everything the next frame will be drawn from. Called after anything that
    /// could have changed an answer, which is every committed action.
    /// </summary>
    /// <remarks>
    /// The sight sweep is the expensive part and it is proportional to the storey, not to what
    /// is on screen: eighteen hundred traces on the waystation's ground floor, measured at 25 ms
    /// once the code is warm. That is well inside a frame for something that runs on an action
    /// rather than on a redraw, which is why moving the camera does not trigger it — the camera
    /// changes what is drawn and never what is true, so panning and zooming only queue a redraw.
    /// </remarks>
    private void Recalculate()
    {
        var active = _battle.Active;
        _reach = active is null
            ? Pathfinder.Reachable(_battle.Graph, default, 0)
            : _battle.Reachable(active);

        _sight.Clear();
        if (active is not null)
        {
            foreach (var tile in _battle.Map.Tiles.Where(t => t.Address.Layer == _layer))
            foreach (var region in _battle.Map.RegionsOf(tile.Address))
            {
                var id = new NodeId(tile.Address, region.Index);
                _sight[id] = _battle.Sight.Trace(active.Vantage, new Vantage(id));
            }
        }

        QueueRedraw();
    }

    /// <summary>The moment as the drawing sees it. Assembled once, read by both halves.</summary>
    private SandboxFrame Frame()
        => new(
            _battle, _layer, _hover, _reach, _sight, _lastWindow, _turns, _auto,
            _scenario, _camera.Visible(GetViewportRect().Size), _camera.ShowsTileDetail,
            Open, _chooser, _byHand);

    // ---- actions ---------------------------------------------------------------
    //
    // Everything a person can do to the battle, one method each. The keys call these and so
    // does the script, which is what keeps a capture honest: a picture can only ever show a
    // state somebody at the keyboard could have reached, because there is no second way in.
    // Each guards itself rather than trusting its caller, since one of the two callers is a
    // string somebody typed.

    /// <summary>
    /// Move the active unit, stopping at the reaction window if we are answering those by hand.
    /// </summary>
    /// <remarks>
    /// Two shapes of the same action. With windows on the recommendation, this is
    /// <c>Battle.Move</c>, which is what it always was. With them answered by hand it is
    /// <c>Commit</c>, a pause, and later <c>Resolve</c> — and in the pause the mover is standing
    /// at the start of a walk it has paid for and not taken, which is the state entry 040 built
    /// and nothing could photograph.
    /// <para>
    /// A window nobody was offered anything in resolves at once. Stopping to ask a question with
    /// no answers in it is a worse interface than not stopping, and it is the common case: most
    /// moves on this map are watched by nobody.
    /// </para>
    /// </remarks>
    private string MoveTo(NodeId destination)
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is not { } mover) return "nobody is up";

        if (!_byHand)
        {
            var outcome = _battle.Move(destination);
            if (outcome.Refusal is { } no) return no;

            _lastWindow = BattleHud.Describe(outcome);
            AfterMove(mover);
            return $"moved to {destination}, {outcome.ApSpent} AP";
        }

        var commitment = _battle.Commit(destination);
        if (commitment.Refusal is { } refused) return refused;

        if (commitment.Window!.Offers.Count == 0)
        {
            _lastWindow = BattleHud.Describe(_battle.Resolve(commitment));
            AfterMove(mover);
            return $"moved to {destination}, {commitment.ApCost} AP, nobody could answer";
        }

        _committed = commitment;
        _chooser = 0;
        Recalculate();
        return $"committed to {destination}, {commitment.ApCost} AP, "
               + $"{commitment.Window.Offers.Count} offered a reaction";
    }

    /// <summary>What follows a move that actually resolved.</summary>
    /// <remarks>A reaction can drop the mover part way, which hands the turn straight on.</remarks>
    private void AfterMove(Unit mover)
    {
        if (_battle.Active is { } next && next != mover) _layer = next.Position.Layer;
        AfterAction();
    }

    private string FireAt(Unit quarry)
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is null) return "nobody is up";

        var outcome = _battle.Fire(quarry);
        AfterAction();

        return outcome is null
            ? $"no shot at {quarry.Name}"
            : $"fired at {quarry.Name}: " + (outcome.AnyHit ? $"hit for {outcome.TotalDamage}" : "missed");
    }

    private string SetStance(Stance stance)
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is null) return "nobody is up";

        var went = _battle.ChangeStance(stance);
        Recalculate();
        return went ? $"went {stance.ToString().ToLowerInvariant()}" : $"could not go {stance}";
    }

    private string FaceTo(HexDirection facing)
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is null) return "nobody is up";

        var turned = _battle.Face(facing);
        Recalculate();
        return turned ? $"faced {facing}" : $"could not face {facing}";
    }

    /// <summary>Declare an arc, or clear the one being held when handed null.</summary>
    private string HoldArc(OverwatchArc? arc)
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is null) return "nobody is up";

        if (arc is null) { _battle.ClearOverwatch(); Recalculate(); return "stopped watching"; }

        var held = _battle.SetOverwatch(arc);
        Recalculate();
        return held ? $"holding a {arc.Name} arc" : $"could not hold a {arc.Name} arc";
    }

    private string ArmAmbush()
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is null) return "nobody is up";

        var armed = _battle.Arm(OverwatchArc.Standard);
        Recalculate();
        return armed ? "armed" : "could not arm";
    }

    private string SpringAmbushOn(Unit prey)
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is not { Ambush: not null }) return "nobody is up with an ambush armed";

        _lastWindow = BattleHud.Describe(_battle.SpringAmbush(prey));
        AfterAction();
        return $"sprang on {prey.Name}";
    }

    /// <summary>
    /// Call a contact in, so that everybody who can hear knows about it.
    /// </summary>
    /// <remarks>
    /// The odd row of the interface audit, and it was odd because the gap was on both sides:
    /// <c>Tactician.AppraiseWord</c> scored a shout and <c>ReactionAction.Shout</c> used one
    /// inside a window, but no <c>Battle</c> action let anybody do it on their own turn — so the
    /// interface could not offer it and <c>Commander</c> could not generate it. Entry 012. Core
    /// has <c>Battle.Shout</c> now, so the offering half is this, and it is the whole of it.
    /// </remarks>
    private string ShoutAbout(Unit about)
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is not { } caller) return "nobody is up";

        if (!_battle.Shout(about)) return $"cannot call {about.Name} in";

        var heard = _battle.Awareness.Earshot(caller).Select(u => u.Name).ToList();
        Recalculate();

        return $"called {about.Name} in; heard by {(heard.Count == 0 ? "nobody" : string.Join(", ", heard))}";
    }

    /// <summary>Walk the active unit off the field, if it is standing somewhere its side may.</summary>
    private string LeaveTheField()
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is not { } leaver) return "nobody is up";

        if (!_battle.Extract()) return $"{leaver.Name} cannot leave from there";

        AfterAction();
        return $"{leaver.Name} left the field";
    }

    private string EndTurn()
    {
        if (Open is not null) return "a reaction window is open";
        if (!_battle.IsRunning) return "the battle is over";

        _battle.EndTurn();
        if (_battle.Active is { } next) _layer = next.Position.Layer;
        AfterAction();
        return _battle.Active is { } up ? $"passed to {up.Name}" : "passed, nobody left to act";
    }

    /// <summary>
    /// Hand this turn to the AI, whoever is up.
    /// </summary>
    /// <remarks>
    /// "What would you do here" is a question a player should be able to ask of their own
    /// soldier, and the answer is the same search the enemy runs.
    /// </remarks>
    private string GiveTurnToAi()
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is not { } soldier) return "nobody is up";

        _turns.Clear();
        TakeTurnWithAi(soldier);
        if (_battle.Active is { } next) _layer = next.Position.Layer;
        AfterAction(keepRecord: true);
        return Open is null ? $"{soldier.Name} took its own turn" : $"{soldier.Name} stopped at a window";
    }

    // ---- answering a window ----------------------------------------------------

    /// <summary>The offers of the open window, or nothing.</summary>
    private IReadOnlyList<ReactionOffer> Offers => Open?.Offers ?? [];

    /// <summary>Point the keyboard at the next reactor that has not answered yet.</summary>
    private void NextChooser()
    {
        var offers = Offers;
        if (offers.Count == 0) { _chooser = 0; return; }

        for (var i = 1; i <= offers.Count; i++)
        {
            var next = (_chooser + i) % offers.Count;
            if (!Answered(offers[next].Reactor)) { _chooser = next; return; }
        }

        _chooser = (_chooser + 1) % offers.Count;
    }

    private bool Answered(Unit reactor) => Open?.Placements.Any(p => p.Reactor == reactor) ?? false;

    /// <summary>
    /// Put one of a reactor's options on the timeline.
    /// </summary>
    /// <remarks>
    /// The placement has to come from an offer this window made — <c>ReactionWindow.Place</c>
    /// throws otherwise, and rightly, since an option carries the tick it starts on and the
    /// forecast it was planned against. So this indexes into the offer rather than building
    /// anything, and the index is what both a number key and a script step name.
    /// </remarks>
    private string PlaceReaction(Unit reactor, int option)
    {
        if (Open is not { } window) return "no window is open";

        var offer = window.Offers.FirstOrDefault(o => o.Reactor == reactor);
        if (offer is null) return $"{reactor.Name} was not offered a reaction";
        if (Answered(reactor)) return $"{reactor.Name} has already answered";
        if (option < 0 || option >= offer.Options.Count)
            return $"{reactor.Name} has {offer.Options.Count} options, not one numbered {option + 1}";

        var placement = offer.Options[option];
        window.Place(placement);
        NextChooser();
        QueueRedraw();

        return $"{reactor.Name}: {placement}";
    }

    /// <summary>
    /// Run the open window, with recommendations standing in for anybody who did not answer.
    /// </summary>
    /// <remarks>
    /// Not the same as placing nothing. <c>PlaceRecommended</c> skips reactors who already
    /// answered, so a player who chose for one soldier and left the rest gets their own choice
    /// plus the default for everybody else — which is the behaviour anybody would expect and is
    /// the reason that method skips rather than overwrites.
    /// </remarks>
    private string ResolveOpenWindow()
    {
        if (Open is not { } window) return "no window is open";

        window.PlaceRecommended();

        if (_committed is { } ours)
        {
            var mover = window.Mover;
            _committed = null;
            _chooser = 0;

            _lastWindow = BattleHud.Describe(_battle.Resolve(ours));
            AfterMove(mover);
            return "resolved";
        }

        var commander = _handed!;
        var unit = _turns.Count > 0 ? _turns[^1].Unit : window.Mover;

        _handed = null;
        _chooser = 0;

        commander.Resume();
        SkipEmptyWindows(commander);

        _lastWindow = BattleHud.Describe(window);
        Record(unit, commander);

        if (Open is null && _battle.Active is { } next) _layer = next.Position.Layer;
        AfterAction(keepRecord: true);
        return "resolved";
    }

    // ---- the script ------------------------------------------------------------

    /// <summary>
    /// Do what the command line said, in the order it said it, reporting each step.
    /// </summary>
    /// <remarks>
    /// Every branch calls a method above and none of them touches <c>Battle</c>, which is the
    /// property that makes a scripted capture worth trusting. The report goes to stdout because
    /// a harness that silently did nothing is the failure mode a deaf run is most prone to: a
    /// misspelt unit name would otherwise produce a perfectly good picture of the wrong moment.
    /// </remarks>
    private void Run(SandboxScript script)
    {
        foreach (var step in script.Steps) GD.Print($"{step}  ->  {Perform(step)}");
    }

    private string Perform(SandboxStep step)
    {
        switch (step.Flag)
        {
            case "--pass":
            {
                var times = step.Argument is null ? 1 : int.TryParse(step.Argument, out var n) ? n : 0;
                if (times <= 0) return "wanted a number of turns to pass";

                // A pass hands the turn on, and if the hostile side is automatic the other side
                // then takes its go — which can stop at a window. Report how far it got rather
                // than only where it ended, because "asked for six, took two" is the interesting
                // half and the picture cannot show it.
                var done = 0;
                for (; done < times && _battle.IsRunning && Open is null; done++) EndTurn();

                var where = _battle.Active is { } up ? $"now {up.Name}" : "nobody left to act";
                return done == times
                    ? $"passed {done}, {where}"
                    : $"passed {done} of {times}, {(Open is not null ? "stopped at a window" : where)}";
            }

            case "--until":
            {
                // Pass until a named soldier is up. Initiative is rolled per round, so counting
                // passes is a guess that goes wrong the moment anybody's roll changes — and a
                // script whose fourth flag lands on the wrong soldier produces a picture that is
                // wrong in a way nothing in it says. This is what the hand does anyway: press
                // space until my man is up.
                if (Named(step.Argument) is not { } wanted) return $"no unit called {step.Argument}";

                var passes = 0;
                while (_battle.Active is { } up && up != wanted && _battle.IsRunning && Open is null && passes < 24)
                {
                    EndTurn();
                    passes++;
                }

                if (Open is not null) return $"stopped at a window after {passes}";
                return _battle.Active == wanted
                    ? $"passed {passes}, now {wanted.Name}"
                    : $"passed {passes} and never reached {wanted.Name}";
            }

            case "--move":
                return ParseNode(step.Argument) is { } to ? MoveTo(to) : "wanted q,r[,layer[,region]]";

            case "--fire":
                return Named(step.Argument) is { } quarry ? FireAt(quarry) : $"no unit called {step.Argument}";

            case "--stance":
                return ParseStance(step.Argument) is { } stance ? SetStance(stance) : "wanted standing, crouching or prone";

            case "--face":
                return ParseFacing(step.Argument) is { } facing ? FaceTo(facing) : "wanted ne, n, nw, sw, s or se";

            case "--overwatch":
            {
                if (step.Argument is null) return "wanted narrow, standard, wide or none";
                if (step.Argument.Equals("none", System.StringComparison.OrdinalIgnoreCase)) return HoldArc(null);

                var arc = OverwatchArc.All.FirstOrDefault(
                    a => a.Name.Equals(step.Argument, System.StringComparison.OrdinalIgnoreCase));
                return arc is null ? $"no arc called {step.Argument}" : HoldArc(arc);
            }

            case "--arm":
                return ArmAmbush();

            case "--spring":
                return Named(step.Argument) is { } prey ? SpringAmbushOn(prey) : $"no unit called {step.Argument}";

            case "--shout":
                return Named(step.Argument) is { } about ? ShoutAbout(about) : $"no unit called {step.Argument}";

            case "--extract":
                return LeaveTheField();

            case "--ai-turn":
                return GiveTurnToAi();

            case "--hostiles":
            {
                // The H key, as an argument. Worth having because the interesting scripts turn
                // it off half way: the AI is the cheapest way to get an enemy alarmed enough to
                // hold an arc, and holding one where you want it is something only a hand does.
                if (step.Argument is not ("ai" or "hand")) return "wanted ai or hand";

                _auto = step.Argument == "ai";
                AfterAction();
                return _auto ? "hostiles to the AI" : "hostiles by hand";
            }

            case "--place":
            {
                // NAME:N, one-based the way the readout numbers them.
                var parts = step.Argument?.Split(':');
                if (parts is not [var who, var which] || !int.TryParse(which, out var index))
                    return "wanted NAME:N, N counting from one as the readout does";

                return Named(who) is { } reactor ? PlaceReaction(reactor, index - 1) : $"no unit called {who}";
            }

            case "--resolve":
                return ResolveOpenWindow();

            case "--hover":
                if (ParseNode(step.Argument) is not { } at) return "wanted q,r[,layer[,region]]";
                _hover = at;
                QueueRedraw();
                return $"cursor on {at}";

            case "--look":
                if (ParseNode(step.Argument) is not { } look) return "wanted q,r";
                _camera.LookAt(look.Tile.Hex);
                CameraMoved();
                return $"looking at {look.Tile.Hex}";

            case "--zoom":
                if (!float.TryParse(step.Argument, out var pixels)) return "wanted a hex radius in pixels";
                _camera.ZoomTo(pixels);
                CameraMoved();
                return $"{_camera.HexPixels:0.#} pixels to the hex";

            case "--fit":
                _camera.Fit(_battle.Map, GetViewportRect().Size);
                CameraMoved();
                return $"whole map, {_camera.HexPixels:0.#} pixels to the hex";

            case "--layer":
                if (!int.TryParse(step.Argument, out var layer)) return "wanted a storey number";
                _layer = layer;
                Recalculate();
                return $"storey {layer}";

            default:
                return "not a flag this sandbox knows";
        }
    }

    /// <summary>A unit by name, case-insensitively, whether or not it is still on the field.</summary>
    private Unit? Named(string? name)
        => name is null
            ? null
            : _battle.Units.FirstOrDefault(u => u.Name.Equals(name, System.StringComparison.OrdinalIgnoreCase));

    /// <summary><c>q,r</c>, or <c>q,r,layer</c>, or <c>q,r,layer,region</c>. Axial, as the maps are authored.</summary>
    private static NodeId? ParseNode(string? text)
    {
        if (text is null) return null;

        var parts = text.Split(',');
        if (parts.Length < 2) return null;
        if (!int.TryParse(parts[0], out var q) || !int.TryParse(parts[1], out var r)) return null;

        var layer = parts.Length > 2 && int.TryParse(parts[2], out var l) ? l : 0;
        var region = parts.Length > 3 && int.TryParse(parts[3], out var n) ? n : 0;

        return new NodeId(new Hex(q, r), layer, region);
    }

    private static Stance? ParseStance(string? text)
        => System.Enum.TryParse<Stance>(text, ignoreCase: true, out var stance) ? stance : null;

    private static HexDirection? ParseFacing(string? text)
        => text?.ToUpperInvariant() switch
        {
            "NE" => HexDirection.NorthEast,
            "N" => HexDirection.North,
            "NW" => HexDirection.NorthWest,
            "SW" => HexDirection.SouthWest,
            "S" => HexDirection.South,
            "SE" => HexDirection.SouthEast,
            _ => System.Enum.TryParse<HexDirection>(text, ignoreCase: true, out var d) ? d : null,
        };

    // ---- input -----------------------------------------------------------------

    public override void _UnhandledInput(InputEvent @event)
    {
        switch (@event)
        {
            case InputEventMouseMotion motion:
            {
                // A drag moves the map under the cursor and does not move the cursor's readout
                // with it: while the middle button is down the pointer is holding ground, not
                // pointing at it.
                if (_dragging is { } from)
                {
                    _camera.Pan(motion.Position - from);
                    _dragging = motion.Position;
                    CameraMoved();
                    break;
                }

                var node = NodeUnderMouse();
                if (node != _hover) { _hover = node; QueueRedraw(); }
                break;
            }

            case InputEventMouseButton { ButtonIndex: MouseButton.Middle } drag:
                _dragging = drag.Pressed ? drag.Position : null;
                break;

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.WheelUp or MouseButton.WheelDown } wheel:
                _camera.ZoomAbout(
                    wheel.ButtonIndex == MouseButton.WheelUp ? 1 : -1,
                    SandboxScale.FromScreen(GetLocalMousePosition()));
                CameraMoved();
                _hover = NodeUnderMouse();
                break;

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }:
                if (NodeUnderMouse() is { } target) MoveTo(target);
                break;

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Right }:
                if (HoveredUnit() is { } quarry) FireAt(quarry);
                break;

            case InputEventKey { Pressed: true, Echo: false } key:
                HandleKey(key.Keycode);
                break;
        }
    }

    private void HandleKey(Key key)
    {
        // A window is modal on purpose. It is a question with the battle held still around it —
        // somebody has paid for a walk they have not taken — and the answers are the only thing
        // the rules will accept next. The camera keys fall through, because looking is not
        // answering and the reactor being chosen for is usually somewhere else on the map.
        if (Open is not null && AnswerKey(key)) return;

        switch (key)
        {
            case Key.Space or Key.Enter:
                EndTurn();
                break;

            case Key.A:
                GiveTurnToAi();
                break;

            case Key.H:
                _auto = !_auto;
                AfterAction();
                break;

            case Key.W:
                _byHand = !_byHand;
                QueueRedraw();
                break;

            case Key.C:
                if (_battle.Active is { } unit)
                    SetStance(unit.Stance switch
                    {
                        Stance.Standing => Stance.Crouching,
                        Stance.Crouching => Stance.Prone,
                        _ => Stance.Standing,
                    });
                break;

            case Key.Z or Key.X:
                if (_battle.Active is { } turner) FaceTo(turner.Facing.Rotate(key == Key.Z ? 1 : -1));
                break;

            case Key.V:
                // Cycle none, narrow, standard, wide. Each declaration costs a point, which
                // is honest: changing your mind about what you are watching is not free.
                if (_battle.Active is { } watchman) HoldArc(NextArc(watchman.Overwatch?.Arc));
                break;

            case Key.B:
                // Arm against the arc already being watched, or spring it if already armed.
                if (_battle.Active is not { } trapper) break;
                if (trapper.Ambush is null) ArmAmbush();
                else if (HoveredUnit() is { } prey) SpringAmbushOn(prey);
                break;

            case Key.T:
                LeaveTheField();
                break;

            case Key.S:
                // Whoever is under the cursor, or the contact this soldier is taking most
                // seriously if the cursor is on nobody.
                if (HoveredUnit() is { } named) ShoutAbout(named);
                else if (_battle.Active is { } caller && _battle.Tactics.Known(caller).FirstOrDefault() is { } threat)
                    ShoutAbout(threat.Unit);
                break;

            case Key.Pageup or Key.E:
                _layer++;
                Recalculate();
                break;

            case Key.Pagedown or Key.Q:
                _layer--;
                Recalculate();
                break;

            case Key.Left or Key.Right or Key.Up or Key.Down:
                _camera.Pan(PanStep * key switch
                {
                    Key.Left => Vector2.Right,      // the map goes right, so the view goes left
                    Key.Right => Vector2.Left,
                    Key.Up => Vector2.Down,
                    _ => Vector2.Up,
                });
                CameraMoved();
                break;

            case Key.Equal or Key.KpAdd:
                _camera.ZoomBy(1);
                CameraMoved();
                break;

            case Key.Minus or Key.KpSubtract:
                _camera.ZoomBy(-1);
                CameraMoved();
                break;

            case Key.F:
                _camera.Fit(_battle.Map, GetViewportRect().Size);
                CameraMoved();
                break;

            case Key.G:
                if (_battle.Active is { } here)
                {
                    _camera.LookAt(here.Position.Tile.Hex);
                    CameraMoved();
                }
                break;

            case Key.R:
                NewBattle();
                break;
        }
    }

    /// <summary>How far one arrow key moves the view, in pixels.</summary>
    private const float PanStep = 160f;

    /// <summary>Point the node at wherever the camera now is, and redraw.</summary>
    /// <remarks>
    /// The node's own <c>Position</c> is the pan: the grid runs in both directions from the
    /// origin, so putting a canvas point in the middle of the viewport is a matter of offsetting
    /// the whole node. That is what the single <c>Position = viewport / 2</c> in <c>_Ready</c>
    /// used to do, for a map whose middle was the origin and which fitted on the screen anyway.
    /// The hit test reads <c>GetLocalMousePosition</c>, which is relative to this same offset,
    /// so it needs nothing said to it.
    /// </remarks>
    private void CameraMoved()
    {
        Position = _camera.ScreenOffset(GetViewportRect().Size);
        QueueRedraw();
    }

    /// <summary>
    /// Keep whoever is up on screen, and only if they are not already.
    /// </summary>
    /// <remarks>
    /// A camera that recentres after every action takes the map away from a player who was
    /// deliberately looking somewhere else — at the ground they are about to cross, usually. So
    /// the test is whether the next soldier is comfortably in shot rather than whether they are
    /// in the middle of it, and the margin is negative for that reason.
    /// </remarks>
    private void FollowActive()
    {
        if (_battle.Active is not { } up) return;
        if (up.Position.Layer != _layer) return;

        var at = SandboxScale.ToScreen(_camera.Geometry.NodeCentre(_battle.Map, up.Position));
        if (_camera.Visible(GetViewportRect().Size, marginHexRadii: -3f).HasPoint(at)) return;

        _camera.LookAt(up.Position.Tile.Hex);
        CameraMoved();
    }

    /// <summary>
    /// The keys that answer an open window. True when one of them was pressed and handled.
    /// </summary>
    /// <remarks>
    /// Tab picks whose answer you are giving and a number picks it, which is the shortest thing
    /// that works for a list of lists. The numbers are one-based because that is how the readout
    /// prints them and how <c>--place NAME:N</c> takes them; a reader should never have to know
    /// that the second option is index one.
    /// </remarks>
    private bool AnswerKey(Key key)
    {
        switch (key)
        {
            case Key.Space or Key.Enter:
                ResolveOpenWindow();
                return true;

            case Key.Tab:
                NextChooser();
                QueueRedraw();
                return true;

            case >= Key.Key1 and <= Key.Key9:
                if (_chooser < Offers.Count) PlaceReaction(Offers[_chooser].Reactor, (int)(key - Key.Key1));
                return true;

            default:
                return false;
        }
    }

    /// <summary>The next arc in the cycle, or null to stop holding one.</summary>
    private static OverwatchArc? NextArc(OverwatchArc? held)
    {
        if (held is null) return OverwatchArc.All[0];

        var index = OverwatchArc.All.ToList().IndexOf(held);
        return index >= 0 && index + 1 < OverwatchArc.All.Count ? OverwatchArc.All[index + 1] : null;
    }

    /// <summary>
    /// Which region of which tile the cursor is over. Uses the actual region polygons, so a
    /// tile split by a barricade picks whichever side the cursor is really on.
    /// </summary>
    private NodeId? NodeUnderMouse()
    {
        // Pixels throughout: the cursor is a screen thing, and the canvas layout is what turns
        // it into a hex. The rules are never asked where the mouse is.
        var screen = GetLocalMousePosition();
        var address = new TileAddress(_camera.Scale.Canvas.HexAt(SandboxScale.FromScreen(screen)), _layer);
        if (!_battle.Map.HasTile(address)) return null;

        var regions = _battle.Map.RegionsOf(address);
        foreach (var region in regions)
            if (SandboxGeometry.ContainsPoint(_camera.Geometry.RegionPolygon(address, region, inset: 0f), screen))
                return new NodeId(address, region.Index);

        return new NodeId(address, regions[0].Index);
    }

    private Unit? HoveredUnit() => _hover is { } node ? _battle.UnitAt(node) : null;

    // ---- drawing ---------------------------------------------------------------

    public override void _Draw()
    {
        var frame = Frame();

        DrawRect(new Rect2(-Position, GetViewportRect().Size), SandboxPalette.Background);

        _view.Draw(frame);

        // The node is offset by the camera so the grid can run in both directions, so the panels
        // have to be pushed back out to the corners they belong in. They are the one thing on
        // screen the camera must not move.
        _hud.Origin = -Position;
        _hud.Draw(frame, GetViewportRect().Size);
    }
}
