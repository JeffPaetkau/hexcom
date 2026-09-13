using System.Collections.Generic;
using System.Linq;
using Godot;
using Hexcom.Content;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>
/// The greybox: a battle as boxes on the ground the rules describe. Click to move whoever is up,
/// order the rest from the action bar, and watch the order strip decide who goes next.
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
/// <see cref="BattleView"/> (the world, as meshes and map labels) and <see cref="BattleHud"/>
/// (the readouts), which are presentation and interface respectively and are separate types so
/// that two people can work on them at once. The camera is <see cref="SandboxCamera"/>, and the
/// layout the battle is given is <see cref="SandboxScale.World"/>, which nothing here may build
/// a second copy of.
/// </para>
/// <para>
/// <b>The picture shows our side's knowledge and nothing else, unless told otherwise.</b> That
/// is the first decision in the greybox brief and the whole of what makes this a game: a
/// hostile is a body while somebody of ours has eyes on it, a ghost at its marker otherwise,
/// and nothing at all before anybody has heard a thing. <c>O</c> or <c>--omniscient</c> puts
/// everything back, because the capture harness is an instrument. The instruments window says
/// which is on.
/// </para>
/// <para>
/// <b>The keys open on the game and the capture harness opens on its own defaults.</b> A person
/// double-clicking the build is playing the waystation against <see cref="Commander"/>, with
/// reaction windows handed out and the other side hidden until found; a capture opens with all
/// three of those off, so <c>--ai</c>, <c>--windows</c> and <c>--omniscient</c> still mean what
/// they meant and every capture command in <c>view.md</c> still opens the run it was written
/// against. Entry 066 in <c>docs/decisions.md</c> is the argument.
/// </para>
/// </remarks>
public partial class HexSandbox : Node3D
{
    /// <summary>
    /// How far back the camera starts, in metres. A drawing figure and nothing else.
    /// </summary>
    /// <remarks>
    /// Exported because viewing distance is a matter of taste. It is emphatically <i>not</i> the
    /// world scale: that is <see cref="SandboxScale.MetresPerHexSize"/>, it is a constant, and
    /// nothing the camera does can move it. The two were once the same number, which is the bug
    /// <c>docs/decisions.md</c> entry 002 describes.
    /// </remarks>
    [Export] public float Distance { get; set; } = 36f;

    [Export] public int Seed { get; set; } = 7;

    /// <summary>
    /// Whether the camera turns and soldiers walk over time, rather than arriving at once.
    /// </summary>
    /// <remarks>
    /// <b>This is the one settle mechanism, and it is a switch rather than a wait.</b> The play-
    /// through asked for a smooth camera and a walked route (entry 057, items 2 and 6) and the
    /// brief attached one condition to both: nothing may animate in a capture, or <c>--yaw N</c>
    /// stops landing on the frame it names and entry 053's determinism goes with it. Two ways to
    /// keep that — settle every animation before the picture, or never start one — and this is
    /// the second, because it leaves a capture on exactly the code path it was measured
    /// byte-deterministic on rather than on a new one that has to be re-measured.
    /// <para>
    /// So it is false for the whole of any run with <c>--shot</c> on it, and <c>--still</c> turns
    /// it off for a person as well. Everything that animates asks <see cref="Animated"/> and
    /// lands on its end state within the call when the answer is no.
    /// </para>
    /// </remarks>
    [Export] public bool Animate { get; set; } = true;

    /// <summary>
    /// Whether the pointer resting near an edge of the window pushes the view that way.
    /// </summary>
    /// <remarks>
    /// <b>Off, and that is the genre's answer rather than a shortcut.</b> Brief Zero in
    /// <c>docs/interface/briefs.md</c> asks for edge-pan as a setting defaulting off, and the
    /// reason is that it is the one camera gesture that happens when the hand is doing nothing:
    /// a pointer parked near an edge while a player reads the panel moves the map out from under
    /// what they were reading. A player who wants it can have it; a player who has never heard of
    /// it should not meet it by accident.
    /// <para>
    /// There is no options screen to keep it in yet, so the switch is <c>--edge-pan</c> and this
    /// property. When there is one, this is the setting it holds and the flag becomes the way a
    /// capture reaches it.
    /// </para>
    /// </remarks>
    [Export] public bool EdgePanning { get; set; }

    /// <summary>
    /// Which of <see cref="SandboxScenario.All"/> to open with. Blank takes the first.
    /// </summary>
    [Export] public string Scenario { get; set; } = "";

    private readonly Dictionary<NodeId, SightResult> _sight = [];
    private readonly Dictionary<UnitId, Threat> _knowledge = [];

    private Battle _battle = null!;
    private SandboxScenario _scenario = null!;
    private SandboxCamera _camera = null!;
    private BattleView _view = null!;
    private BattleHud _hud = null!;
    private SandboxCanvas _labels = null!;
    private SandboxCanvas _readouts = null!;
    private SandboxCapture? _capture;

    /// <summary>The instruments window, and the surface inside it. Built closed. See <see cref="BuildInstrumentsWindow"/>.</summary>
    private Window _instruments = null!;
    private SandboxCanvas _instrumentPanel = null!;

    private ReachabilityResult _reach = null!;
    private NodeId? _hover;
    private int _layer;

    /// <summary>Where a middle-button drag was last seen, while one is in progress.</summary>
    private Vector2? _dragging;

    /// <summary>Where a right-button drag was last seen, while one is in progress.</summary>
    private Vector2? _orbiting;

    /// <summary>
    /// How far the pointer has travelled since the right button went down.
    /// </summary>
    /// <remarks>
    /// The right button does two jobs — it backs out of a half-entered order, and it orbits — so
    /// the two are told apart by whether the pointer moved. Under <see cref="ClickSlop"/> pixels
    /// between press and release it was a click; over it, a drag. So the click is acted on at
    /// <em>release</em>, which is the only moment the two are distinguishable.
    /// <para>
    /// <b>This was expected to be a deletion and it is not, but its stakes went to nothing.</b>
    /// While right-click fired, a drag misread as a click was a shot nobody meant and could not
    /// take back. Now it is an aim dropped, which costs no point and is one key to pick up again.
    /// Cancelling on the press instead would have been simpler and would mean that turning the
    /// camera to get a better look at a target throws the aim away — the one moment a player
    /// most wants to look round is while they are deciding whether to fire.
    /// </para>
    /// </remarks>
    private float _orbitTravel;

    /// <summary>
    /// Who the firing mode is pointed at, or null when it is off. Read through
    /// <see cref="SandboxFrame.Aim"/>, which checks it is still a shot worth describing.
    /// </summary>
    /// <remarks>
    /// <b>Firing is a mode, and that is brief three.</b> Right-click used to fire, which put the
    /// most irreversible action in the game on the button every player of the genre presses to
    /// back out of something — ten games of ten spend it on cancel. So a shot is now two
    /// gestures: point the mode at somebody (<c>1</c>, <c>Tab</c>, or a left-click on a hostile),
    /// read the terms, and confirm (space, enter, or a click on the same hostile). Right-click and
    /// escape drop it. <b>Nothing else acquired a confirmation</b>: a move is still one click and
    /// there is still no undo, because entry 077 found that a game lets a player take something
    /// back exactly as far as it told them the truth, and this one hides things. The confirm lives
    /// on the shot because the shot is what announces you.
    /// </remarks>
    private Unit? _aim;

    /// <summary>
    /// The fire mode picked from the bar for the aim, or null for the weapon's default. Read through
    /// <see cref="SandboxFrame.Mode"/>; cleared wherever <see cref="_aim"/> is.
    /// </summary>
    /// <remarks>
    /// <b>Ability first, and the one-click habit kept.</b> The genre picks the ability, then the target,
    /// then confirms — so a fire slot enters the mode in that mode, and pointing it at somebody else
    /// keeps it. A click on a hostile with no slot picked still aims, in the default, and the default's
    /// slot is lit, so the gesture brief three settled survives and the bar says what it did.
    /// </remarks>
    private FireMode? _mode;

    /// <summary>The action bar slot under the pointer, by id, or null when the pointer is on the map.</summary>
    private string? _pointing;

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

    /// <summary>
    /// Whether the picture shows every unit in play, or only what our side knows.
    /// </summary>
    /// <remarks>
    /// Off by default: the keys open on the game. A capture that wants the instrument says
    /// <c>--omniscient</c>, and a person at the keyboard presses <c>O</c>. The frame carries it
    /// and the frame's <see cref="SandboxFrame.Sees"/> is the one question the view and the HUD
    /// ask, so there is no second place a hostile could leak through.
    /// </remarks>
    private bool _omniscient;

    /// <summary>The route a walk is being drawn along, as plane points with the floor under each.</summary>
    private readonly List<(CoreVec2 At, double Floor, NodeId Node)> _walkRoute = [];

    /// <summary>Whose walk it is, or null when nobody is part way along one.</summary>
    private UnitId? _walking;

    /// <summary>Seconds into the walk, and how many it lasts.</summary>
    private double _walkElapsed, _walkSeconds;

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

    /// <summary>The mission this battle is, or null for a bare map with people put on it here.</summary>
    private Mission? _mission;

    /// <summary>Whether the full six-part briefing is on screen.</summary>
    private bool _briefing;

    /// <summary>The turns the AI has taken since a person last did anything. Newest last.</summary>
    private readonly List<TakenTurn> _turns = [];

    /// <summary>
    /// The least time the <i>their go</i> banner stays up, in seconds. <b>Measured.</b>
    /// </summary>
    /// <remarks>
    /// Brief five and entry 065 argued 0.6 to 1.2 seconds from the games that do this, and this
    /// shipped at 0.9, the middle of that range, as a provisional figure. Capture C7 replaced it:
    /// Invisible, Inc.'s corporate-turn banner, the closest shipped relative, measured frame by frame
    /// at <b>at least 1.43 seconds</b> — it was already up on the clip's first frame — so the floor
    /// is 1.4. Entry 089, item 6. Without a floor a stretch that resolves in one frame — which is
    /// every stretch the AI plays without stopping — would flash the banner, and that is worse than
    /// drawing nothing.
    /// <para>
    /// A floor and not a length: the banner stays up for as long as the stretch actually lasts,
    /// which is longer whenever it stops at a window or a hostile is walked. A capture has no dwell
    /// at all, by the rule every other animation here keeps — see <see cref="Animated"/>.
    /// </para>
    /// </remarks>
    [Export] public double TheirGoDwell { get; set; } = 1.4;

    /// <summary>Whether the held key for every figure's terms is down. See <see cref="SandboxFrame.Details"/>.</summary>
    private bool _details;

    /// <summary>Whether the player has folded the shot's terms away. Kept for the run, across targets and soldiers.</summary>
    private bool _termsFolded;

    /// <summary>Seconds the banner has been up, or null when it is down.</summary>
    private double? _theirGo;

    /// <summary>What our side held when the current stretch of their go began, or null outside one.</summary>
    private Dictionary<UnitId, Threat>? _heldBefore;

    /// <summary>What our side perceived of the other side's last go. See <see cref="Perceive"/>.</summary>
    private readonly List<string> _perceived = [];

    /// <summary>Hostiles laid eyes on since the last order of ours. See <see cref="SandboxFrame.Found"/>.</summary>
    private readonly HashSet<UnitId> _found = [];

    /// <summary>
    /// Whether the mission's own clock has run out.
    /// </summary>
    /// <remarks>
    /// <b>The clock is the sandbox's to apply, and that is not an oversight in either direction.</b>
    /// A mission file carries a round limit — the waystation's is thirty, *before first light* —
    /// and nothing in the rules reads it: entry 047 says whatever runs the battle applies it, and
    /// entry 030 has the missing clock as Core's outstanding work. So this is a view enforcing a
    /// content figure until there is a rule to enforce it, and the one thing it must not do is
    /// enforce it quietly.
    /// <para>
    /// It stops the turns and it does not invent a verdict. <c>Withdrawal.Judge</c> reads
    /// <c>Undecided</c> while anybody is still on the field, and that is the honest answer here:
    /// the squad did not get out, the rules have not settled it, and a sandbox that made up an
    /// <c>Abandoned</c> would be putting a rule in <c>game/</c>.
    /// </para>
    /// </remarks>
    private bool OutOfTime => _mission?.Rounds is { } limit && _battle.Round > limit;

    private Vector2 Viewport => GetViewport().GetVisibleRect().Size;

    /// <summary>
    /// Read the command line and move the window before anything else this run does.
    /// </summary>
    /// <remarks>
    /// <b>The earliest hook there is, and it is still not early enough to be invisible.</b> Godot
    /// creates and maps the window while it is bringing the display server up, which is before any
    /// script exists to have an opinion, so a window put aside from inside the process is always a
    /// window that appeared somewhere else first. What this buys is the difference between moving
    /// after the scene is built and moving before it: everything below <see cref="_Ready"/> —
    /// building the world, loading the mission, the opening sight sweep — now happens on the
    /// monitor it is going to stay on. See <see cref="SandboxAside"/> for the rest of it.
    /// </remarks>
    public override void _EnterTree()
    {
        var args = OS.GetCmdlineUserArgs();

        _capture = SandboxCapture.Requested();

        // A capture is always a session's, so it is put aside whether it said so or not.
        _aside = _capture is not null || System.Array.IndexOf(args, AsideFlag) >= 0;
        if (_aside) SandboxAside.Place(GetWindow());
    }

    public override void _Ready()
    {
        var font = ThemeDB.FallbackFont;

        BuildScene();

        _camera = new SandboxCamera(GetNode<Camera3D>("Camera"), Distance);
        _view = new BattleView(GetNode<Node3D>("World"), _labels, _camera, font);
        _hud = new BattleHud(font, _camera, _view.Crown);

        // One frame, two surfaces. Both painters build it from the same call, in the same tick,
        // so the instruments window can never be showing a moment the map is not — which is the
        // condition the brief attached to splitting the HUD at all.
        _labels.Painter = _view.DrawLabels;
        _readouts.Painter = canvas => _hud.Draw(canvas, Frame(), Viewport);
        _instrumentPanel.Painter = canvas => _hud.DrawInstruments(canvas, Frame(), _instruments.Size);

        var args = OS.GetCmdlineUserArgs();

        if (System.Array.IndexOf(args, EdgePanFlag) >= 0) EdgePanning = true;

        if (SandboxScript.ValueOf(args, PaceFlag) is { } pace
            && double.TryParse(pace, out var metresASecond) && metresASecond > 0)
            WalkPace = metresASecond;

        if (System.Array.IndexOf(args, InstrumentsFlag) >= 0) ShowInstruments(true);

        if (System.Array.IndexOf(args, StillFlag) >= 0) Animate = false;

        // A capture has to be reproducible, and input is the one thing here that is not: the
        // window opens under whatever the pointer was already doing, so the cursor readout and
        // the previewed path land in the picture and two runs disagree. Capturing is therefore
        // deaf as well as brief. It processes all the same — a capture is the thing counting
        // frames down — and so does an interactive run now, for the animation and the edge pan.
        SetProcess(true);
        SetProcessUnhandledInput(_capture is null);

        NewBattle();
    }

    /// <summary>
    /// The fixed furniture: a camera, a light, an environment, a root for the world's meshes,
    /// and two flat canvases over it all.
    /// </summary>
    /// <remarks>
    /// Built in code rather than in the scene file so that the scene stays one node with one
    /// script, which is what the capture path opens and what <c>--headless --quit-after</c>
    /// checks. Two canvases rather than one, on purpose: the map's labels belong to the view and
    /// the readouts belong to the HUD, and giving each its own surface is what keeps either from
    /// drawing on the other's — see entry 014 in <c>docs/decisions.md</c>.
    /// <para>
    /// The light is one directional source from the south-west and above, with shadows, and a
    /// flat ambient under it. Shadows are the cheapest depth cue a blockout can have — a wall
    /// with no shadow is a stripe on the ground from most angles — and they are the one thing
    /// here a capture could find non-deterministic; <c>view.md</c> says what was found.
    /// </para>
    /// </remarks>
    private void BuildScene()
    {
        AddChild(new Camera3D { Name = "Camera", Current = true });

        var light = new DirectionalLight3D
        {
            Name = "Sun",
            RotationDegrees = new Vector3(-52f, -35f, 0f),
            LightEnergy = 1.4f,
            ShadowEnabled = true,
        };
        AddChild(light);

        AddChild(new WorldEnvironment
        {
            Name = "Environment",
            Environment = new Environment
            {
                BackgroundMode = Environment.BGMode.Color,
                BackgroundColor = SandboxPalette.Background,
                AmbientLightSource = Environment.AmbientSource.Color,
                AmbientLightColor = new Color("aab4c4"),
                AmbientLightEnergy = 0.9f,
            },
        });

        AddChild(new Node3D { Name = "World" });

        var labels = new CanvasLayer { Name = "Labels", Layer = 1 };
        _labels = new SandboxCanvas { Name = "Canvas" };
        labels.AddChild(_labels);
        AddChild(labels);

        var readouts = new CanvasLayer { Name = "Hud", Layer = 2 };
        _readouts = new SandboxCanvas { Name = "Canvas" };
        readouts.AddChild(_readouts);
        AddChild(readouts);

        BuildInstrumentsWindow();
    }

    /// <summary>How big the instruments window opens, in pixels.</summary>
    private static readonly Vector2I InstrumentsSize = new(1120, 620);

    /// <summary>
    /// The second window: a surface for everything a player of a shipped game would never see.
    /// </summary>
    /// <remarks>
    /// A real <c>Window</c> rather than a panel in a corner, which is the play-through's first
    /// finding and the only shape that answers it — the point is that it can be dragged onto
    /// another monitor, and nothing inside one viewport can be. It is built closed and shown by
    /// <c>I</c> or <c>--instruments</c>, so a person who opens the game gets the game.
    /// <para>
    /// <b>Closing it with the system button hides it rather than freeing it.</b> A window that
    /// destroyed itself would take its canvas with it and <c>I</c> would have to build a second
    /// one, which is a second place the split between the two halves is decided. There is one.
    /// </para>
    /// </remarks>
    private void BuildInstrumentsWindow()
    {
        _instruments = new Window
        {
            Name = "Instruments",
            Title = "Hexcom — instruments",
            Size = InstrumentsSize,
            Visible = false,
            Unresizable = false,
            Transient = false,
        };

        var canvas = new SandboxCanvas { Name = "Canvas" };
        _instrumentPanel = canvas;
        _instruments.AddChild(canvas);
        AddChild(_instruments);

        _instruments.CloseRequested += () => ShowInstruments(false);
    }

    /// <summary>Turns off the camera turn and the walk for a whole run. See <see cref="Animate"/>.</summary>
    private const string StillFlag = "--still";

    /// <summary>Opens the second window on a run started from the command line. Interactively it is <c>I</c>.</summary>
    private const string InstrumentsFlag = "--instruments";

    /// <summary>Opens every window this run has on the leftmost monitor. See <see cref="SandboxAside"/>.</summary>
    private const string AsideFlag = "--aside";

    /// <summary>Turns the edge push on for a run. See <see cref="EdgePanning"/>.</summary>
    private const string EdgePanFlag = "--edge-pan";

    /// <summary>Sets the walking pace in metres a second. See <see cref="WalkPace"/>.</summary>
    private const string PaceFlag = "--pace";

    /// <summary>Whether this run's windows belong on the leftmost monitor, including any opened later.</summary>
    private bool _aside;

    /// <summary>Whether anything may take time. False for the whole of a capture, by <see cref="Animate"/>'s remarks.</summary>
    private bool Animated => _capture is null && Animate;

    public override void _Process(double delta)
    {
        if (Animated)
        {
            var moved = _camera.Advance(delta);
            moved |= AdvanceWalk(delta);
            if (moved) CameraMoved();

            EdgePan(delta);

            // The banner's dots move, so it redraws while it is up; and it comes down here once
            // the stretch is over and the dwell has run.
            if (_theirGo is { } shown)
            {
                _theirGo = shown + delta;
                _readouts.QueueRedraw();
            }
        }

        LowerBanner();

        _capture?.Tick(this, _instruments);
    }

    /// <summary>How far from an edge the pointer starts pushing the view, in pixels.</summary>
    private const float EdgeMargin = 24f;

    /// <summary>How fast the view runs when the pointer is right against an edge, pixels of ground per second.</summary>
    private const float EdgePanRate = 900f;

    /// <summary>
    /// Push the view when the pointer sits near an edge of the window.
    /// </summary>
    /// <remarks>
    /// The third of the three mouse gestures the play-through asked for, and the one with a
    /// habit of firing when nobody wanted it: a pointer resting outside the window, or on the
    /// instruments window next door, must not drag the map along behind it. So it runs only
    /// while the pointer is genuinely inside the viewport and no drag is already holding the
    /// ground. The rate is proportional to how far into the margin the pointer has gone, which
    /// is what makes a slow nudge at the edge possible at all.
    /// <para>
    /// And it runs only when it has been asked for at all — see <see cref="EdgePanning"/>, which
    /// is off. The habit described above is the reason the genre makes this a setting.
    /// </para>
    /// </remarks>
    private void EdgePan(double delta)
    {
        if (!EdgePanning || _dragging is not null || _orbiting is not null) return;

        var viewport = Viewport;
        var at = GetViewport().GetMousePosition();
        if (at.X < 0 || at.Y < 0 || at.X > viewport.X || at.Y > viewport.Y) return;

        var push = new Vector2(
            Depth(at.X, viewport.X),
            Depth(at.Y, viewport.Y));

        if (push == Vector2.Zero) return;

        // Pan takes the screen distance the ground moved, so pushing right moves the ground left.
        _camera.Pan(-push * EdgePanRate * (float)delta, viewport);
        CameraMoved();

        static float Depth(float at, float extent)
            => at < EdgeMargin ? (at - EdgeMargin) / EdgeMargin
             : at > extent - EdgeMargin ? (at - (extent - EdgeMargin)) / EdgeMargin
             : 0f;
    }

    /// <summary>
    /// Load the scenario asked for and put everybody on it.
    /// </summary>
    /// <remarks>
    /// The whole of the waystation — the ground, who stands where facing which way, the objective
    /// and the clock — comes from <c>content/</c>, and this method's remaining job is to hand
    /// the rules the metres layout, which is the only one there is now and is still the single
    /// mistake this file has actually made. See <see cref="SandboxScale"/>.
    /// </remarks>
    private void NewBattle()
    {
        _scenario = SandboxScenario.ByName(_capture?.Scenario ?? (Scenario.Length > 0 ? Scenario : null));

        _mission = _scenario.LoadMission();
        _battle = _scenario.Open(_mission, SandboxScale.World, Seed);

        // The keys open on the game and the capture harness opens on its own defaults, which is
        // the whole of the play-through's fourth finding. A person double-clicking the build is
        // playing the mission against Commander, with the windows handed out and the other side
        // hidden until found; they should not have to press H and K first to be playing at all.
        // A capture keeps every default it had, because six flags and every capture command in
        // view.md were written against them — --ai and --windows would stop meaning anything the
        // day they became the default of the thing they switch on.
        _auto = _capture?.Automatic ?? true;
        _byHand = _capture?.AnswerWindowsByHand ?? true;
        _omniscient = _capture?.Omniscient ?? false;
        _turns.Clear();
        _committed = null;
        _handed = null;
        _chooser = 0;
        _aim = null;
        _mode = null;
        _pointing = null;
        _lastWindow = "";
        _hover = null;
        _theirGo = null;
        _heldBefore = null;
        _perceived.Clear();
        _knowledge.Clear();

        Settle();

        _layer = _battle.Active?.Position.Layer ?? 0;

        // The waystation is 85 metres across and does not fit on a screen at a distance anybody
        // can read a tile at, so a battle opens looking at whoever is up rather than at the
        // origin, which is only where the compound happened to be centred.
        if (_battle.Active is { } up) _camera.LookAt(_battle.Map, up.Position.Tile.Hex, up.Position.Layer);

        Recalculate();
        Perceive();
        LowerBanner();

        // Whoever is in sight at the opening was deployed there, not discovered.
        _found.Clear();

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
        if (Open is not null || OutOfTime) return;
        if (!_auto || _battle.Active is not { Side: Side.Hostile }) return;

        if (!keepRecord) _turns.Clear();
        if (_battle.IsDecided) return;

        // Control is leaving our side, so the banner goes up — once for the whole run of their
        // turns, however many there are and whoever takes them. A window part way through does not
        // end the stretch; it pauses it, and resolving that window comes back through here with the
        // banner still up and the snapshot still the one taken when control first left.
        if (_theirGo is null)
        {
            _theirGo = 0;
            _heldBefore = GatherKnowledge();
        }

        while (_auto && Open is null && !OutOfTime && !_battle.IsDecided
               && _battle.Active is { Side: Side.Hostile } unit)
            TakeTurnWithAi(unit);
    }

    /// <summary>
    /// Whether the other side's go is still going on: paused at a window of ours to answer, or a
    /// hostile's move still being walked.
    /// </summary>
    private bool TheirGoHolding
        => _handed?.Waiting?.Mover.Side == Side.Hostile
           || _walking is { } walker && _battle.GetUnit(walker)?.Side == Side.Hostile;

    /// <summary>
    /// Take the banner down if the stretch is over and it has been up long enough to have been read.
    /// </summary>
    private void LowerBanner()
    {
        if (_theirGo is not { } shown || TheirGoHolding) return;
        if (Animated && shown < TheirGoDwell) return;

        _theirGo = null;
        _readouts.QueueRedraw();
    }

    /// <summary>
    /// Write down what our side perceived of the stretch so far, and close the stretch's books if it
    /// is over.
    /// </summary>
    /// <remarks>
    /// Called after the frame's knowledge is gathered, so the comparison is between what our side
    /// held when control left it and what it holds now. <see cref="BattleHud.Perceived"/> decides
    /// what counts; this only keeps the result, frozen, so that a stance change of ours afterwards
    /// cannot be misread as something that happened while it was their go.
    /// </remarks>
    private void Perceive()
    {
        if (_heldBefore is null) return;

        _perceived.Clear();
        _perceived.AddRange(BattleHud.Perceived(Frame(), _heldBefore));

        if (_handed?.Waiting is null) _heldBefore = null;
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
        SkipUnanswerableWindows(commander);
        Record(unit, commander);
    }

    /// <summary>
    /// Run straight past any window with nothing in it for a player to answer, taking the
    /// recommendation for whoever was offered something.
    /// </summary>
    /// <remarks>
    /// A commander handing its windows out stops at every one of them, which is right for Core —
    /// it cannot know whether the thing answering wants to look at an empty list — and wrong for
    /// a screen. Stopping to ask a question with no answers in it is a worse interface than not
    /// stopping, and it is the common case rather than the corner: most moves on a map this size
    /// are watched by nobody, so without this the sandbox stops twice a turn to say <em>0 of 0
    /// answered</em> and a script has to spell out a <c>--resolve</c> for each.
    /// <para>
    /// <b>Since brief six "nothing to answer" includes "nothing of ours to answer"</b> — see
    /// <see cref="SandboxFrame.AnswerableIn"/>. The recommendations have to be placed before
    /// resuming, and that is not tidiness: <c>Commander.Resume</c> treats a window with nothing
    /// placed as everybody holding fire, so skipping one the way an empty one is skipped would
    /// quietly switch the other side's reactions off.
    /// </para>
    /// </remarks>
    private void SkipUnanswerableWindows(Commander commander)
    {
        while (commander.Waiting is { } window && SandboxFrame.AnswerableIn(window, _instruments.Visible).Count == 0)
        {
            window.PlaceRecommended();
            commander.Resume();

            // A window somebody was offered something in did something, and what the other side did
            // about a move of ours is a player's to read — it is what stopping at the window used to
            // put on screen, and skipping it must not take the reaction line away with the question.
            // An empty window did nothing and leaves the last one standing, as it always has.
            if (window.Offers.Count > 0) _lastWindow = BattleHud.Describe(window);
        }
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
        // Core hands back an Act per order, with the outcome beside it. The instruments want only
        // the orders; what a player perceived of the turn wants the outcomes — a shot at one of ours.
        var turn = new TakenTurn(unit, [.. commander.Taken], unit.Reserve);

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
        // Any order that goes through here — a move, a shot, a pass, a turn handed to the AI —
        // abandons an aim. The ones that do not come through here are the ones taken on the spot
        // (stance, facing, an arc, a shout), and an aim survives those on purpose: crouching to
        // see whether the shot gets better is part of deciding to take it, and the shot line
        // re-plans from the new stance.
        _aim = null;
        _mode = null;

        // An order of ours ends whatever was being said about their last go: the banner, if it was
        // still dwelling, and the account of what we perceived, which is *since you last acted*.
        // The one thing that comes through here in the middle of their go is a window of theirs
        // being run, and the snapshot being held is how that is told apart — not keepRecord, which
        // a turn of ours handed to the AI sets too.
        if (_heldBefore is null)
        {
            if (!TheirGoHolding) _theirGo = null;
            _perceived.Clear();
            _found.Clear();
        }

        var before = _battle.Active;
        Settle(keepRecord);
        if (_battle.Active is { } next && next != before) _layer = next.Position.Layer;
        Recalculate();
        Perceive();
        LowerBanner();
        FollowActive();
    }

    /// <summary>
    /// Re-ask the rules everything the next frame will be drawn from, and rebuild the world from
    /// the answers. Called after anything that could have changed an answer, which is every
    /// committed action.
    /// </summary>
    /// <remarks>
    /// The sight sweep is the expensive part and it is proportional to the storey, not to what
    /// is on screen: eighteen hundred traces on the waystation's ground floor, measured at 25 ms
    /// once the code is warm. That is well inside a frame for something that runs on an action
    /// rather than on a redraw, which is why moving the camera does not trigger it — the camera
    /// changes what is drawn and never what is true, so panning and zooming only re-project the
    /// labels.
    /// <para>
    /// The knowledge our side holds is gathered here too: <c>Tactician.Known</c> for each of
    /// ours, merged by keeping the best any of them has on each hostile — eyes on beats a
    /// marker, a fresher marker beats a staler one. It is the list the scorer weighs, which is
    /// why it is the list the picture draws.
    /// </para>
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

        // A hostile our side has eyes on now and did not the last time the knowledge was gathered is
        // a discovery, and stays one until our next order — see SandboxFrame.Found.
        var seenBefore = _knowledge.Values.Where(t => t.EyesOn).Select(t => t.Unit.Id).ToHashSet();

        _knowledge.Clear();
        foreach (var (id, threat) in GatherKnowledge()) _knowledge[id] = threat;

        foreach (var threat in _knowledge.Values)
        {
            if (!threat.EyesOn) _found.Remove(threat.Unit.Id);
            else if (!seenBefore.Contains(threat.Unit.Id)) _found.Add(threat.Unit.Id);
        }
        _found.RemoveWhere(id => !_knowledge.ContainsKey(id));

        _view.Rebuild(Frame());
        _readouts.QueueRedraw();

        // The instruments follow the rules changing and not the cursor moving, which is why
        // HoverChanged leaves them alone: nothing in that window is a question about a tile.
        if (_instruments.Visible) _instrumentPanel.QueueRedraw();
    }

    /// <summary>What our side holds on each hostile, merged by keeping the best any of ours holds.</summary>
    private Dictionary<UnitId, Threat> GatherKnowledge()
    {
        var knowledge = new Dictionary<UnitId, Threat>();
        foreach (var mine in _battle.InPlay.Where(u => u.Side == Side.Player))
        foreach (var threat in _battle.Tactics.Known(mine))
        {
            if (!knowledge.TryGetValue(threat.Unit.Id, out var held) || Better(threat, held))
                knowledge[threat.Unit.Id] = threat;
        }
        return knowledge;
    }

    private static bool Better(Threat candidate, Threat held)
        => candidate.EyesOn && !held.EyesOn
           || candidate.EyesOn == held.EyesOn && candidate.Credence > held.Credence;

    /// <summary>Redraw the readouts and the labels from the state as it is, without re-asking the rules.</summary>
    private void Redraw()
    {
        _labels.QueueRedraw();
        _readouts.QueueRedraw();
        if (_instruments.Visible) _instrumentPanel.QueueRedraw();
    }

    /// <summary>Open or close the instruments window.</summary>
    /// <remarks>
    /// Shown and hidden rather than built and freed, so that the split between the two halves of
    /// the HUD is decided in one place — see <see cref="BuildInstrumentsWindow"/>. Opening it
    /// redraws it at once: it has been hidden, so nothing has been queueing its redraws, and a
    /// window that opened blank until the next action would look broken.
    /// </remarks>
    private void ShowInstruments(bool open)
    {
        _instruments.Visible = open;

        // The window's list of answerable offers just grew or shrank, so the keyboard is pointed
        // again from the top rather than at an index that now means somebody else. A window left
        // with nothing of ours in it stays open: closing a window of instruments is not an answer,
        // and the readout says space runs it.
        if (Open is not null)
        {
            _chooser = -1;
            NextChooser();
            Redraw();
        }

        if (!open) return;

        // Placed on opening rather than on building: a hidden window has no position worth
        // setting, and this one can be opened from the keyboard long after _Ready.
        if (_aside) SandboxAside.Place(_instruments);
        _instrumentPanel.QueueRedraw();
    }

    /// <summary>The cursor moved: rebuild what follows it and redraw what quotes it.</summary>
    private void HoverChanged()
    {
        _view.RebuildCursor(Frame());
        _readouts.QueueRedraw();
    }

    /// <summary>The moment as the drawing sees it. Assembled once, read by both halves.</summary>
    private SandboxFrame Frame()
        => new(
            _battle, _layer, _hover, _reach, _sight, _lastWindow, _turns, _auto,
            _scenario, _camera.ShowsTileDetail,
            Open, _chooser, _byHand, _mission, _briefing, OutOfTime,
            _omniscient, _knowledge, _instruments.Visible, _aim,
            _theirGo, _perceived, _found, _details, _termsFolded, _mode, _pointing);

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
            AfterMove(mover, outcome.Path);
            return $"moved to {destination}, {outcome.ApSpent} AP";
        }

        var commitment = _battle.Commit(destination);
        if (commitment.Refusal is { } refused) return refused;

        if (commitment.Window!.Offers.Count == 0)
        {
            _lastWindow = BattleHud.Describe(_battle.Resolve(commitment));
            AfterMove(mover, commitment.Path);
            return $"moved to {destination}, {commitment.ApCost} AP, nobody could answer";
        }

        // Somebody could answer, and none of them is a player's to answer: the other side takes its
        // recommendations and the move goes through, exactly as if windows were not handed out.
        // See SandboxFrame.AnswerableIn for why their offers are not put in front of anybody.
        if (SandboxFrame.AnswerableIn(commitment.Window, _instruments.Visible).Count == 0)
        {
            commitment.Window.PlaceRecommended();
            _lastWindow = BattleHud.Describe(_battle.Resolve(commitment));
            AfterMove(mover, commitment.Path);
            return $"moved to {destination}, {commitment.ApCost} AP, nobody of ours could answer";
        }

        _committed = commitment;
        _chooser = 0;
        Recalculate();
        return $"committed to {destination}, {commitment.ApCost} AP, "
               + $"{commitment.Window.Offers.Count} offered a reaction";
    }

    /// <summary>What follows a move that actually resolved.</summary>
    /// <remarks>A reaction can drop the mover part way, which hands the turn straight on.</remarks>
    private void AfterMove(Unit mover, IReadOnlyList<TraversalLink> path)
    {
        if (_battle.Active is { } next && next != mover) _layer = next.Position.Layer;
        AfterAction();
        BeginWalk(mover, path);
    }

    // ---- the walk ----------------------------------------------------------------

    /// <summary>Metres a second a soldier covers when it is not being hurried.</summary>
    /// <remarks>
    /// <b>Ten, and it is the first interface figure in this project that was watched rather than
    /// argued.</b> Brief Zero in <c>docs/interface/briefs.md</c> asks for the pace to be priced in
    /// metres a second rather than seconds a move — which is what stops a two-hex step and an
    /// eight-hex step looking equally urgent — and puts the figure at 1.4 for a tactical walk and
    /// 2.5 for a hustle. The rule is kept and the figure is not: the user watched it at several
    /// paces and said ten, which is nearly three times the top of that range and half as fast
    /// again as the seven it shipped at. See <c>docs/decisions.md</c> entry 080.
    /// <para>
    /// The reason the sheet was wrong is that its figures say how fast a soldier moves, which is a
    /// claim about the world, where this number says how long a player watches a transition before
    /// it stops being a transition. At ten a hex goes by in about a sixth of a second and the
    /// longest walk 50 action points can buy — ten hexes of flat ground, 17 metres — is under two.
    /// </para>
    /// <para>
    /// <c>--pace N</c> stays, because the next person to disagree should be able to show it rather
    /// than argue it.
    /// </para>
    /// </remarks>
    [Export] public double WalkPace { get; set; } = 10.0;

    /// <summary>
    /// Start drawing a move that has already happened in the rules.
    /// </summary>
    /// <remarks>
    /// <b>Nothing about the battle is pending here.</b> Entry 040 is precise about it: the mover
    /// has not stepped until the window resolves, and by the time this is called the window has
    /// resolved, every reaction has been taken and the soldier is standing at the far end. What
    /// walks is the drawing. So the route is truncated at wherever the unit actually ended up —
    /// a reaction that dropped it part way leaves it short of the destination, and a picture that
    /// walked the whole planned route would be showing a walk the rules refused.
    /// <para>
    /// It is skipped whole when <see cref="Animated"/> is false, so a capture and a headless run
    /// see exactly what they saw before there was a walk at all.
    /// </para>
    /// </remarks>
    private void BeginWalk(Unit mover, IReadOnlyList<TraversalLink> path)
    {
        if (path.Count == 0) { EndWalk(); return; }

        var nodes = new List<NodeId> { path[0].From };
        nodes.AddRange(path.Select(link => link.To));
        BeginWalk(mover, nodes);
    }

    /// <inheritdoc cref="BeginWalk(Unit, IReadOnlyList{TraversalLink})"/>
    private void BeginWalk(Unit mover, IReadOnlyList<NodeId> walked)
    {
        EndWalk();
        if (!Animated || walked.Count < 2 || !mover.InPlay) return;

        var map = _battle.Map;
        var route = new List<NodeId>();
        foreach (var node in walked)
        {
            route.Add(node);
            if (node != walked[0] && node == mover.Position) break;   // dropped en route, or arrived
        }

        if (route.Count < 2) return;

        foreach (var node in route)
            _walkRoute.Add((SandboxGeometry.NodePlane(map, node), SandboxGeometry.FloorOf(map, node), node));

        var metres = 0.0;
        for (var i = 0; i + 1 < _walkRoute.Count; i++)
            metres += CoreVec2.Distance(_walkRoute[i].At, _walkRoute[i + 1].At);

        _walking = mover.Id;
        _walkElapsed = 0;
        // No ceiling on the duration. A cap is seconds-a-move wearing a metres-a-second coat:
        // above it a long route and a short one arrive together again, which is the one thing
        // pricing the walk in metres exists to prevent. Somebody who does not want to watch it
        // has --still, which is the genre's instant setting and the sheet's own escape hatch.
        _walkSeconds = metres / WalkPace;

        if (_walkSeconds <= 0) { EndWalk(); return; }

        AdvanceWalk(0);
    }

    /// <summary>Move a walk along by one frame, and say whether it is still going.</summary>
    private bool AdvanceWalk(double delta)
    {
        if (_walking is not { } mover) return false;

        _walkElapsed += delta;
        if (_walkElapsed >= _walkSeconds) { EndWalk(); return false; }

        // Distance rather than time per leg, so a long hop across a gap does not take the same
        // quarter second as a step between neighbours.
        var wanted = _walkElapsed / _walkSeconds * TotalMetres();
        var run = 0.0;

        for (var i = 0; i + 1 < _walkRoute.Count; i++)
        {
            var (from, to) = (_walkRoute[i], _walkRoute[i + 1]);
            var span = CoreVec2.Distance(from.At, to.At);

            if (run + span < wanted) { run += span; continue; }

            var into = span <= 0 ? 1.0 : (wanted - run) / span;
            var step = to.At - from.At;

            _view.Walk = new UnitWalk(
                mover,
                from.At + step * into,
                from.Floor + (to.Floor - from.Floor) * into,
                System.Math.Atan2(step.Y, step.X),
                _walkRoute.Skip(i + 1).Select(point => point.Node).ToList());

            _view.RebuildBodies(Frame());
            _view.RebuildCursor(Frame());
            return true;
        }

        EndWalk();
        return false;
    }

    private double TotalMetres()
    {
        var metres = 0.0;
        for (var i = 0; i + 1 < _walkRoute.Count; i++)
            metres += CoreVec2.Distance(_walkRoute[i].At, _walkRoute[i + 1].At);
        return metres;
    }

    /// <summary>Put the soldier back where the rules have had it standing all along.</summary>
    private void EndWalk()
    {
        var was = _walking;
        _walking = null;
        _walkRoute.Clear();
        _view.Walk = null;

        if (was is null) return;
        _view.RebuildBodies(Frame());
        _view.RebuildCursor(Frame());
    }

    /// <remarks>
    /// A shot may only be asked for at a soldier the picture shows. That is an interface
    /// restriction and not a rule — the rules would refuse a shot with no line to it anyway —
    /// but a script that could name a hidden hostile would be a way of finding out where one
    /// is, and the whole point of the picture is that a player cannot.
    /// </remarks>
    private string FireAt(Unit quarry, FireMode? mode = null)
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is null) return "nobody is up";
        if (!Frame().Sees(quarry)) return $"nobody of ours can see {quarry.Name}";

        var shooter = _battle.Active;
        var before = HeldOn(shooter);

        var outcome = _battle.Fire(quarry, mode);

        // Who actually learned something, read straight off the contact files either side of the
        // shot and before anybody else acts — the other half of the check brief four set, whose
        // first half is the bill --aim prints. Named the way the picture names them.
        var told = Frame().Names(TellingSince(shooter, before));
        AfterAction();

        return outcome is null
            ? $"no shot at {quarry.Name}"
            : $"fired {(mode ?? shooter.Weapon.DefaultMode).Name} at {quarry.Name} for {outcome.ApSpent} AP: "
              + (outcome.AnyHit ? $"hit for {outcome.TotalDamage}" : "missed")
              + $"; told {told}";
    }

    /// <summary>What each of a soldier's enemies holds on that soldier right now.</summary>
    /// <remarks>
    /// <b>An instrument, and it never reaches the screen.</b> This is the enemy's contact file as a
    /// number, which contract 3 keeps off the picture. It is read only to report, on the command
    /// line, who a shot actually told — so that the bill on screen can be checked against what the
    /// rules did rather than against what the preview says the rules would do.
    /// </remarks>
    private Dictionary<Unit, double> HeldOn(Unit subject)
        => _battle.Enemies(subject).ToDictionary(
            enemy => enemy,
            enemy => _battle.Awareness.ContactsFor(enemy.Id).FirstOrDefault(c => c.Subject == subject.Id)?.Detection ?? 0);

    /// <summary>The enemies whose file on a soldier has risen since <paramref name="before"/>, target first then by name.</summary>
    private IEnumerable<Unit> TellingSince(Unit subject, Dictionary<Unit, double> before)
        => HeldOn(subject)
            .Where(pair => pair.Value > before.GetValueOrDefault(pair.Key))
            .Select(pair => pair.Key)
            .OrderBy(unit => unit.Name);

    // ---- the firing mode --------------------------------------------------------
    //
    // A shot is two gestures: point the mode at somebody, then confirm. See _aim for why. These
    // four stage a shot and FireAt above takes it; --fire NAME still goes straight there, which
    // for any shot the rules allow is the same as --aim NAME --confirm, and is kept so that no
    // script written before the mode existed changes meaning.

    /// <summary>
    /// Point the firing mode at a hostile the picture shows: the one named, or failing that whoever
    /// is under the cursor, or failing that the nearest.
    /// </summary>
    /// <remarks>
    /// The fallbacks are what make <c>1</c> one key rather than two. A player with the cursor on a
    /// hostile means that one; a player without means <i>somebody</i>, and the nearest is the
    /// answer that needs no explaining. <c>Tab</c> is there for when it is the wrong one.
    /// </remarks>
    /// <param name="mode">
    /// The fire mode to aim in, from a bar slot. Null keeps the mode of an aim already up — pointing a
    /// snap at somebody else is still a snap — and otherwise aims in the weapon's default.
    /// </param>
    private string AimAt(Unit? quarry, FireMode? mode = null)
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is not { } shooter) return "nobody is up";

        var frame = Frame();
        quarry ??= frame.HoveredUnit is { } hovered && hovered.IsHostileTo(shooter)
            ? hovered
            : frame.Targets.FirstOrDefault();

        if (quarry is null) return "nobody in sight to aim at";
        if (!quarry.IsHostileTo(shooter)) return $"{quarry.Name} is not a hostile";
        if (!frame.Sees(quarry)) return $"nobody of ours can see {quarry.Name}";

        if (mode is not null) _mode = mode;
        else if (frame.Aim is null) _mode = null;

        _aim = quarry;

        // Keep the target on screen, and only if it is not already — the same test FollowActive
        // uses, for the same reason. A left-click aim is already under the pointer and never moves
        // the view; a Tab to somebody behind the camera has to.
        if (!_camera.Frames(SandboxGeometry.NodeScene(_battle.Map, quarry.Position), Viewport))
        {
            _camera.LookAt(_battle.Map, quarry.Position.Tile.Hex, quarry.Position.Layer);
            CameraMoved();
        }

        HoverChanged();
        return Aiming();
    }

    /// <summary>What the staged aim is, as a script step reports it: the mode, the odds, the price and who it would tell.</summary>
    private string Aiming()
    {
        var frame = Frame();
        if (frame.Aim is not { } quarry || frame.StagedShot is not { } plan) return "not aiming at anybody";

        return plan.CanFire
            ? $"aiming {plan.Mode.Name} at {quarry.Name}: {plan.HitChance:P0} for {plan.ApCost} AP; "
              + $"would tell {frame.Names(_battle.WouldAnnounce(plan).Select(word => word.Learner).OrderBy(unit => unit.Name))}"
            : $"aiming {plan.Mode.Name} at {quarry.Name}: {plan.Refusal}";
    }

    /// <summary>
    /// A fire slot: enter the firing mode in that mode, or change the mode of the aim already up, or —
    /// on the slot already lit — back out.
    /// </summary>
    /// <remarks>
    /// The lit slot backs out rather than fires, and that is the safe way round: a double tap on a
    /// number key is a player who has changed their mind or fumbled, and the reference set is
    /// unanimous that the gesture which cancels never spends a point. The confirm stays where brief
    /// three put it — space, enter, or a second click on the body.
    /// </remarks>
    private string PressFire(FireMode mode)
    {
        var frame = Frame();
        if (frame.Aim is null) return AimAt(null, mode);
        if (frame.Mode == mode) return BackOut();

        _mode = mode;
        HoverChanged();
        return Aiming();
    }

    /// <summary>Aim at the next hostile in sight, nearest first, wrapping round.</summary>
    /// <remarks>
    /// <b>Built for this game's reason and not the genre's.</b> The brief called <c>Tab</c> the
    /// convention and the reference set says otherwise — XCOM 2 cycles and nine games of ten
    /// expect the player to point at the body. What this game has that they do not is a cursor
    /// that picks only on the storey being looked at: a hostile on a roof cannot be clicked from
    /// the ground floor at all without <c>PgUp</c> first, and at the distance a rifle reaches a body
    /// is a few pixels behind a ghosted wall. The cycle never goes near the cursor, so it reaches
    /// both. It does not cycle through ghosts at markers — see <see cref="SandboxFrame.Targets"/>.
    /// </remarks>
    private string NextTarget()
    {
        if (Open is not null) return "a reaction window is open";
        if (_battle.Active is null) return "nobody is up";

        var frame = Frame();
        var targets = frame.Targets;
        if (targets.Count == 0) return "nobody in sight to aim at";

        var at = frame.Aim is { } current ? targets.ToList().IndexOf(current) : -1;
        return AimAt(targets[(at + 1) % targets.Count]);
    }

    /// <summary>Fire at whoever the mode is aimed at. The confirm, and the only one in the game.</summary>
    /// <remarks>
    /// A shot the rules would refuse stays aimed and says why, rather than dropping the mode: the
    /// player asked to fire, the answer is no, and what they most likely want next is to change
    /// something — a stance, a target — and try again, not to start the gesture over.
    /// </remarks>
    private string ConfirmShot()
    {
        var frame = Frame();
        if (frame.Aim is not { } quarry) return "not aiming at anybody";

        var plan = _battle.PlanShot(_battle.Active!, quarry, frame.Mode);
        if (!plan.CanFire) return $"no shot at {quarry.Name}: {plan.Refusal}";

        return FireAt(quarry, frame.Mode);
    }

    /// <summary>
    /// Back out of whatever is half entered, spending nothing: the aim, or else the briefing.
    /// </summary>
    /// <remarks>
    /// <b>Never a spent point</b>, which is the one thing the reference set is unanimous on. So an
    /// open reaction window is not something to back out of — the move in it is paid for, and a
    /// cancel that refunded it would be the undo entry 077 rules out — and this says so rather
    /// than doing nothing, since right-click on a window is exactly what a player will try.
    /// </remarks>
    private string BackOut()
    {
        if (Frame().Aim is { } was)
        {
            _aim = null;
            _mode = null;
            HoverChanged();
            return $"stopped aiming at {was.Name}";
        }

        _aim = null;
        _mode = null;

        if (_briefing)
        {
            _briefing = false;
            Redraw();
            return "put the briefing away";
        }

        return Open is not null ? "a move already paid for cannot be backed out of" : "nothing to back out of";
    }

    /// <summary>
    /// A left-click. Aims at a hostile, fires at the one already aimed at, and otherwise moves —
    /// unless an aim is up, when a click on the ground only drops it.
    /// </summary>
    /// <remarks>
    /// The last clause is the one that needed deciding. A click on the ground while aiming is a
    /// player who has changed their mind about the shot, and it would be a strange cancel that
    /// also walked the soldier somewhere and spent the points. So it backs out and does nothing
    /// else, and the path preview is not drawn while aiming because it would be promising a move
    /// the click will not make.
    /// </remarks>
    private void LeftClick()
    {
        // The fold switch in the docked terms is the one thing on the HUD a click is for, and it is
        // only up while aiming — when a click anywhere else backs out. Folding is not backing out.
        if (Frame().Aim is not null && _hud.FoldSwitch.HasPoint(GetViewport().GetMousePosition()))
        {
            FoldTerms();
            return;
        }

        // A click on the bar is a slot pressed and never a click on the ground under it. Pressing a
        // slot is not backing out either, so it comes before the aim's click-anywhere-else rule.
        if (_hud.SlotAt(GetViewport().GetMousePosition()) is { } slot)
        {
            PressSlot(slot);
            return;
        }

        var frame = Frame();
        var hostile = frame.HoveredUnit is { } unit && _battle.Active is { } shooter && unit.IsHostileTo(shooter)
            ? unit
            : null;

        if (frame.Aim is { } aim)
        {
            if (hostile == aim) ConfirmShot();
            else if (hostile is not null) AimAt(hostile);
            else BackOut();
            return;
        }

        if (hostile is not null) AimAt(hostile);
        else if (NodeUnderMouse() is { } target) MoveTo(target);
    }

    /// <summary>
    /// Press a slot on the action bar — by its id, its key or its name, first match in that order —
    /// and do what it says, or say why not.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The one way in for the key, the click and the script.</b> Each of the three used to call the
    /// action methods directly, which is fine while the only thing between them is a keycode; with a
    /// slot drawn that says <i>ready</i> or <i>needs 15</i>, the press has to be refused by the same
    /// answer the slot was drawn from, or the bar is a picture of a different rule from the one the
    /// key obeys. So this reads <see cref="SandboxFrame.Bar"/> and refuses what it shows refused, and
    /// every slot still ends in the one method per action that touches the battle.
    /// </para>
    /// <para>
    /// A name is ambiguous where a fire mode and an arc share one — <c>standard</c> — and resolves to
    /// the fire mode, which comes first on the bar; <c>arc:standard</c> says the other.
    /// </para>
    /// </remarks>
    private string PressSlot(string wanted)
    {
        var frame = Frame();
        var bar = frame.Bar;

        if (FindSlot(bar, wanted) is not { } slot)
            return Open is not null ? "a reaction window is open"
                : _battle.Active is null ? "nobody is up"
                : bar.Count == 0 ? "nothing to order now"
                : $"no slot {wanted} on the bar";

        var active = _battle.Active!;
        if (!slot.Affordable) return $"{slot.Name} needs {slot.Price} points, {active.Name} has {active.ActionPoints}";
        if (slot.Reason is { } no) return $"{slot.Name}: {no}";

        var colon = slot.Id.IndexOf(':');
        var (kind, argument) = colon < 0 ? (slot.Id, "") : (slot.Id[..colon], slot.Id[(colon + 1)..]);

        switch (kind)
        {
            case "fire":
                return active.Weapon.Mode(argument) is { } mode ? PressFire(mode) : $"{active.Weapon.Name} has no {argument}";

            case "arc":
                // The lit arc stops watching; any other declares, replacing the one held.
                return slot.Lit ? HoldArc(null) : HoldArc(OverwatchArc.All.First(arc => arc.Name == argument));

            case "stance":
                return SetStance(ActionBar.NextStance(active.Stance));

            case "turn":
                return FaceTo(active.Facing.Rotate(argument == "left" ? 1 : -1));

            case "ambush":
                if (active.Ambush is null) return ArmAmbush();
                return (frame.Aim ?? frame.HoveredUnit) is { } prey ? SpringAmbushOn(prey) : "aim at somebody to spring it on";

            case "shout":
                return ActionBar.ShoutSubject(frame, active) is { } about ? ShoutAbout(about) : "nobody to call in";

            case "leave":
                return LeaveTheField();

            case "end":
                return EndTurn();

            default:
                return $"the bar has no action {slot.Id}";
        }
    }

    /// <summary>A slot by id, else by key, else by name, case-insensitively.</summary>
    private static BarSlot? FindSlot(IReadOnlyList<BarSlot> bar, string wanted)
        => bar.FirstOrDefault(s => s.Id.Equals(wanted, System.StringComparison.OrdinalIgnoreCase))
           ?? bar.FirstOrDefault(s => s.Key.Equals(wanted, System.StringComparison.OrdinalIgnoreCase))
           ?? bar.FirstOrDefault(s => s.Name.Equals(wanted, System.StringComparison.OrdinalIgnoreCase));

    /// <summary>Point at a slot, or at nothing, and redraw the line pointing shows.</summary>
    private void PointAt(string? slot)
    {
        if (slot == _pointing) return;
        _pointing = slot;
        _readouts.QueueRedraw();
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
        if (!Frame().Sees(prey)) return $"nobody of ours can see {prey.Name}";

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
        if (OutOfTime) return $"the mission's {_mission!.Rounds} rounds are up";

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

    /// <summary>The offers of the open window a player may answer, or nothing. See <see cref="SandboxFrame.AnswerableIn"/>.</summary>
    private IReadOnlyList<ReactionOffer> Offers
        => Open is { } window ? SandboxFrame.AnswerableIn(window, _instruments.Visible) : [];

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

        var offer = Offers.FirstOrDefault(o => o.Reactor == reactor);
        if (offer is null)
            return window.Offers.Any(o => o.Reactor == reactor)
                ? $"{reactor.Name} is not ours to answer; the instruments window answers for both sides"
                : $"{reactor.Name} was not offered a reaction";
        if (Answered(reactor)) return $"{reactor.Name} has already answered";
        if (option < 0 || option >= offer.Options.Count)
            return $"{reactor.Name} has {offer.Options.Count} options, not one numbered {option + 1}";

        var placement = offer.Options[option];
        window.Place(placement);
        NextChooser();
        Redraw();

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
            AfterMove(mover, ours.Path);
            return "resolved";
        }

        var commander = _handed!;
        var unit = _turns.Count > 0 ? _turns[^1].Unit : window.Mover;

        // The route the hostile is about to walk, taken before it walks it. This is the only
        // hostile move the view can draw travelling: the window carries its steps, and the
        // sandbox is holding the resolution rather than watching it go past. A hostile move that
        // nobody could have reacted to opens no window, is resumed past by SkipUnanswerableWindows, and
        // jumps — see the note for Core in decisions entry 066.
        var hostile = window.Mover;
        var route = window.Move.Steps.Select(step => step.Node).ToList();

        _handed = null;
        _chooser = 0;

        // Their go resumes, and the banner the window stood aside for comes back with a fresh
        // dwell, or a stretch finishing in this frame would flash it.
        if (_theirGo is not null) _theirGo = 0;

        commander.Resume();
        SkipUnanswerableWindows(commander);

        _lastWindow = BattleHud.Describe(window);
        Record(unit, commander);

        if (Open is null && _battle.Active is { } next) _layer = next.Position.Layer;
        AfterAction(keepRecord: true);
        BeginWalk(hostile, route);
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
        foreach (var step in script.Steps)
        {
            var perceived = _perceived.ToList();
            GD.Print($"{step}  ->  {Perform(step)}");

            // What a player would read about their go, whenever a step changed it — so the account
            // of a pause can be checked across a whole mission without a picture per turn. It is
            // the player's own readout, so printing it is no instrument. Brief five.
            if (!perceived.SequenceEqual(_perceived) && _perceived.Count > 0)
                foreach (var line in _perceived) GD.Print($"    perceived:{line}");
        }
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
                for (; done < times && _battle.IsRunning && Open is null && !OutOfTime; done++) EndTurn();

                var where = OutOfTime ? $"the mission's {_mission!.Rounds} rounds are up"
                    : Open is not null ? "stopped at a window"
                    : _battle.Active is { } up ? $"now {up.Name}"
                    : "nobody left to act";

                return done == times ? $"passed {done}, {where}" : $"passed {done} of {times}, {where}";
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
                while (_battle.Active is { } up && up != wanted
                       && _battle.IsRunning && Open is null && !OutOfTime && passes < 24)
                {
                    EndTurn();
                    passes++;
                }

                if (Open is not null) return $"stopped at a window after {passes}";
                if (OutOfTime) return $"the mission's {_mission!.Rounds} rounds ran out after {passes}";

                return _battle.Active == wanted
                    ? $"passed {passes}, now {wanted.Name}"
                    : $"passed {passes} and never reached {wanted.Name}";
            }

            case "--move":
                return ParseNode(step.Argument) is { } to ? MoveTo(to) : "wanted q,r[,layer[,region]]";

            case "--fire":
                return Named(step.Argument) is { } quarry ? FireAt(quarry) : $"no unit called {step.Argument}";

            case "--aim":
            {
                // Bare, it aims the way a click on a body does: the hovered hostile or the nearest, in
                // the default mode. Named, it is a left-click on that soldier, without having to
                // --hover one first. NAME:MODE is a fire slot pressed and then the click, which is
                // the mode-first gesture in one step; :MODE alone is the slot pressed.
                var parts = (step.Argument ?? "").Split(':');
                FireMode? mode = null;
                if (parts.Length > 1)
                {
                    if (_battle.Active?.Weapon.Mode(parts[1]) is not { } picked)
                        return $"{_battle.Active?.Weapon.Name ?? "nobody's weapon"} has no mode called {parts[1]}";
                    mode = picked;
                }

                if (parts[0].Length == 0) return mode is null ? AimAt(null) : PressSlot($"fire:{mode.Name}");
                if (Named(parts[0]) is not { } target) return $"no unit called {parts[0]}";

                // The slot's price is checked as pressing it would; pressing it outright would back
                // out of an aim already in that mode, which is not what naming a target asks for.
                if (mode is not null && FindSlot(Frame().Bar, $"fire:{mode.Name}") is { Affordable: false } dear)
                    return $"{dear.Name} needs {dear.Price} points, {_battle.Active!.Name} has {_battle.Active.ActionPoints}";
                return AimAt(target, mode);
            }

            case "--slot":
                // A slot pressed, by id, key or name — the key or the click, as a step.
                return step.Argument is null ? "wanted a slot: its id, its key or its name" : PressSlot(step.Argument);

            case "--point":
            {
                // The pointer resting on a slot, so the line it shows can be photographed.
                if (step.Argument is null) return "wanted a slot: its id, its key or its name";
                if (FindSlot(Frame().Bar, step.Argument) is not { } slot) return $"no slot {step.Argument} on the bar";

                _hover = null;
                HoverChanged();
                PointAt(slot.Id);
                return $"pointing at {slot.Name}: {slot.Hint}";
            }

            case "--next-target":
                return NextTarget();

            case "--confirm":
                return ConfirmShot();

            case "--back-out":
                return BackOut();

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

            case "--brief":
                _briefing = true;
                Redraw();
                return _mission is null ? "this scenario has no mission to brief" : "briefing on screen";

            case "--details":
                // Ctrl held down for the rest of the run, since a capture is deaf and cannot let go.
                return HoldDetails(true);

            case "--fold":
                return FoldTerms();

            case "--hover":
                if (ParseNode(step.Argument) is not { } at) return "wanted q,r[,layer[,region]]";
                _hover = at;
                HoverChanged();
                return $"cursor on {at}";

            case "--look":
                if (ParseNode(step.Argument) is not { } look) return "wanted q,r";
                _camera.LookAt(_battle.Map, look.Tile.Hex, _layer);
                CameraMoved();
                return $"looking at {look.Tile.Hex}";

            case "--zoom":
                if (!float.TryParse(step.Argument, out var metres)) return "wanted a distance in metres";
                _camera.ZoomTo(metres);
                CameraMoved();
                return $"{_camera.Distance:0.#} m back";

            case "--yaw":
                if (!int.TryParse(step.Argument, out var yaw)) return "wanted a bearing, 0 to 5";
                _camera.TurnTo(yaw);
                CameraMoved();
                return $"looking {(HexDirection)_camera.Yaw}";

            case "--fit":
                _camera.Fit(_battle.Map, Viewport);
                CameraMoved();
                return $"whole map, {_camera.Distance:0.#} m back";

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
                // A drag moves the ground under the cursor and does not move the cursor's
                // readout with it: while the button is down the pointer is holding the view,
                // not pointing at it.
                if (_dragging is { } from)
                {
                    _camera.Pan(motion.Position - from, Viewport);
                    _dragging = motion.Position;
                    CameraMoved();
                    break;
                }

                if (_orbiting is { } held)
                {
                    var travel = motion.Position - held;
                    _orbitTravel += travel.Length();
                    _camera.Orbit(-travel.X * OrbitPerPixel);
                    _orbiting = motion.Position;
                    CameraMoved();
                    break;
                }

                // The bar sits over the map, so a pointer on a slot is on the slot and not on the tile
                // under it: no cursor tag, no path preview, and no shot staged at whoever stands there.
                var slot = _hud.SlotAt(motion.Position);
                PointAt(slot);

                var node = slot is null ? NodeUnderMouse() : null;
                if (node != _hover) { _hover = node; HoverChanged(); }
                break;
            }

            case InputEventMouseButton { ButtonIndex: MouseButton.Middle } drag:
                _dragging = drag.Pressed ? drag.Position : null;
                break;

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.WheelUp or MouseButton.WheelDown } wheel:
                _camera.ZoomBy(wheel.ButtonIndex == MouseButton.WheelUp ? 1 : -1);
                CameraMoved();
                _hover = NodeUnderMouse();
                HoverChanged();
                break;

            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }:
                LeftClick();
                break;

            // The right button orbits and backs out, told apart by whether the pointer moved —
            // so the back-out happens on release, which is the only moment that is known. It
            // never fires. See _orbitTravel and _aim.
            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Right } press:
                _orbiting = press.Position;
                _orbitTravel = 0f;
                break;

            case InputEventMouseButton { Pressed: false, ButtonIndex: MouseButton.Right }:
                var wasClick = _orbiting is not null && _orbitTravel < ClickSlop;
                _orbiting = null;
                if (wasClick) BackOut();
                break;

            // Held, not pressed: the terms are up for exactly as long as the key is down. Echoes
            // arrive while it is held and change nothing.
            case InputEventKey { Keycode: Key.Ctrl } ctrl:
                if (ctrl.Pressed != _details) HoldDetails(ctrl.Pressed);
                break;

            case InputEventKey { Pressed: true, Echo: false } key:
                HandleKey(key.Keycode);
                break;
        }
    }

    /// <summary>
    /// A window that loses focus with <c>Ctrl</c> down never hears it come up, so it lets go here
    /// rather than leaving every figure's terms stuck on the map.
    /// </summary>
    public override void _Notification(int what)
    {
        if (what == NotificationWMWindowFocusOut && _details) HoldDetails(false);
    }

    /// <summary>Hold or release the key for every figure's terms at once. See <see cref="BattleHud"/>.</summary>
    private string HoldDetails(bool held)
    {
        _details = held;
        Redraw();
        return held ? "every figure's terms on the map" : "headlines only";
    }

    /// <summary>Fold or unfold the shot's docked terms, which stays as it is left.</summary>
    private string FoldTerms()
    {
        // Folded or not is a preference kept for the run, so it can be set before there is a shot to
        // see it on; the readout only draws the switch when there is.
        _termsFolded = !_termsFolded;
        Redraw();
        return _termsFolded ? "the shot's terms folded" : "the shot's terms open";
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
            // Space and enter confirm whatever is up and do nothing else: they resolve a window and
            // fire an aim, and with neither they do nothing at all. They used to end the turn with
            // nothing to confirm, which put the pass on the key a player presses to fire — one aim
            // dropped a moment early and the go was gone. Entry 094, item 10; XCOM 2's binding.
            case Key.Space or Key.Enter:
                if (Frame().Aim is not null) ConfirmShot();
                break;

            // Ending the go has a key of its own and a slot of its own, and nothing else is on either.
            case Key.Backspace:
                PressSlot("end");
                break;

            // The number keys are the bar's fire modes and arcs, and they are live only outside a
            // window — AnswerKey has already taken them if one is open, and the bar is empty while
            // one is, so a number never has two meanings at once. The window keeps its numbers
            // because the readout prints them and --place NAME:N takes them.
            case >= Key.Key1 and <= Key.Key6:
                PressSlot(((int)(key - Key.Key1) + 1).ToString());
                break;

            case Key.Tab:
                NextTarget();
                break;

            case Key.Escape:
                BackOut();
                break;

            case Key.J:
                GiveTurnToAi();
                break;

            case Key.H:
                _auto = !_auto;
                AfterAction();
                break;

            case Key.K:
                _byHand = !_byHand;
                Redraw();
                break;

            case Key.O:
                // See everything, or only what our side knows. The world has to be rebuilt,
                // because which soldiers are bodies is a question about the meshes.
                _omniscient = !_omniscient;
                Recalculate();
                break;

            // The letters on the bar press their slots, so a key refuses exactly what the slot is
            // drawn refusing. V is gone: it cycled four arcs at a point each with nothing saying which
            // one had landed, which is item 6, and 4, 5 and 6 are the three arcs as slots.
            case Key.C or Key.Z or Key.X or Key.B or Key.T or Key.L:
                PressSlot(key.ToString());
                break;

            case Key.M:
                _briefing = !_briefing;
                Redraw();
                break;

            case Key.I:
                ShowInstruments(!_instruments.Visible);
                break;

            case Key.P:
                FoldTerms();
                break;

            case Key.Pageup:
                _layer++;
                Recalculate();
                break;

            case Key.Pagedown:
                _layer--;
                Recalculate();
                break;

            // Pan, in screen terms and not in the map's: W moves the view up the screen from
            // whichever of the six bearings the camera is on, which is what a person means by
            // up. The conversion back into the rules' plane is the camera's and happens once,
            // in Pan, so nothing here knows which way north is.
            case Key.W or Key.A or Key.S or Key.D or Key.Left or Key.Right or Key.Up or Key.Down:
                _camera.Pan(PanStep * key switch
                {
                    Key.A or Key.Left => Vector2.Right,     // the ground goes right, so the view goes left
                    Key.D or Key.Right => Vector2.Left,
                    Key.W or Key.Up => Vector2.Down,
                    _ => Vector2.Up,
                }, Viewport);
                CameraMoved();
                break;

            // Q and E turn the camera, and , and . still do the same thing for anybody who
            // learned them before the remap. The turn is the one camera move that takes time,
            // so it is the one that has to be landed by hand when nothing is driving it — with
            // animation off _Process never calls Advance, and a target nothing advances towards
            // is a key that does nothing at all.
            case Key.Q or Key.E or Key.Comma or Key.Period:
                _camera.Turn(key is Key.Q or Key.Comma ? 1 : -1);
                if (!Animated) _camera.Settle();
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
                _camera.Fit(_battle.Map, Viewport);
                CameraMoved();
                break;

            case Key.G:
                if (_battle.Active is { } here)
                {
                    _camera.LookAt(_battle.Map, here.Position.Tile.Hex, here.Position.Layer);
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

    /// <summary>How far a right-drag turns the camera, radians per pixel of pointer travel.</summary>
    /// <remarks>
    /// A third of a screen's width comes to about a bearing, so the gesture a person makes to
    /// turn one face of the map towards them is the same size as the one <c>Q</c> makes for them.
    /// </remarks>
    private const float OrbitPerPixel = 0.006f;

    /// <summary>How far the pointer may travel between press and release and still count as a click.</summary>
    private const float ClickSlop = 6f;

    /// <summary>The camera moved: nothing is true that was not, so only the labels and the readouts re-project.</summary>
    private void CameraMoved()
    {
        _hover = _capture is null ? NodeUnderMouse() : _hover;
        HoverChanged();
        _labels.QueueRedraw();

        // The one thing a camera move can change about the world mesh. Bodies carry rings that
        // are drawn wider once the camera is far enough back to have given up on tile detail
        // (see BattleView.Rings), so crossing that threshold has to rebuild them — and only
        // crossing it, because otherwise every wheel notch would rebuild the bodies for nothing.
        var detail = _camera.ShowsTileDetail;
        if (detail == _tileDetail) return;

        _tileDetail = detail;
        _view.RebuildBodies(Frame());
    }

    /// <summary>Whether the camera was close enough for tile detail last time it moved. See <see cref="CameraMoved"/>.</summary>
    private bool _tileDetail = true;

    /// <summary>
    /// Keep whoever is up on screen, and only if they are not already.
    /// </summary>
    /// <remarks>
    /// A camera that recentres after every action takes the map away from a player who was
    /// deliberately looking somewhere else — at the ground they are about to cross, usually. So
    /// the test is whether the next soldier is comfortably in shot rather than whether they are
    /// in the middle of it, and the margin is generous for that reason.
    /// </remarks>
    private void FollowActive()
    {
        if (_battle.Active is not { } up) return;
        if (_camera.Frames(SandboxGeometry.NodeScene(_battle.Map, up.Position), Viewport)) return;

        _camera.LookAt(_battle.Map, up.Position.Tile.Hex, up.Position.Layer);
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
                Redraw();
                return true;

            case >= Key.Key1 and <= Key.Key9:
                if (_chooser < Offers.Count) PlaceReaction(Offers[_chooser].Reactor, (int)(key - Key.Key1));
                return true;

            default:
                return false;
        }
    }

    /// <summary>
    /// Which region of which tile the cursor is over, by casting a ray from the camera through
    /// it and asking which floor on the current storey it lands on.
    /// </summary>
    private NodeId? NodeUnderMouse()
    {
        var (origin, direction) = _camera.Ray(GetViewport().GetMousePosition());
        return SandboxGeometry.Pick(_battle.Map, origin, direction, _layer);
    }
}
