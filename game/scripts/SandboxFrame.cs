using System.Collections.Generic;
using System.Linq;
using Hexcom.Content;
using Hexcom.Core.Awareness;
using Hexcom.Core.Battles;
using Hexcom.Core.Combat;
using Hexcom.Core.Movement;
using Hexcom.Core.Reactions;
using Hexcom.Core.Tactics;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Side = Hexcom.Core.Units.Side; // Godot has a Side enum of its own

namespace Hexcom.Game;

/// <summary>One turn <see cref="Commander"/> took in the sandbox, and what it chose to do with it.</summary>
/// <param name="Unit">Whose turn it was.</param>
/// <param name="Acts">What it did, in order, each carrying the order and what came of it.</param>
/// <param name="Banked">What it had left when the turn ended, which is what it can react with.</param>
/// <remarks>
/// <see cref="Order"/> already carries the reasoning; this only remembers whose it was, because
/// by the time the frame is drawn the unit has finished and the battle has moved on to somebody
/// else. The outcomes ride along since brief five: a shot at one of ours is something a player
/// perceived, and <see cref="Act.Fired"/> is the only place it is recorded.
/// </remarks>
public sealed record TakenTurn(Unit Unit, IReadOnlyList<Act> Acts, int Banked)
{
    /// <summary>The orders alone, which is what the instruments print.</summary>
    public IEnumerable<Order> Orders => Acts.Select(act => act.Order);
}

/// <summary>
/// One rung of a soldier's reserve: the fewest points it may end a turn holding and still bank
/// enough for something.
/// </summary>
/// <param name="Name">What the rung buys — <c>banks</c> for the floor, or a fire mode's name.</param>
/// <param name="Leftover">The fewest points left unspent that reach it.</param>
/// <param name="Banks">What ending the turn on exactly that many points carries into the reserve.</param>
/// <param name="Price">What the rung costs to use out of the reserve — this soldier's price for the mode, or nothing for the floor.</param>
public sealed record ReserveRung(string Name, int Leftover, int Banks, int Price);

/// <summary>
/// The rungs of one soldier's reserve, cheapest first: where stopping first banks anything, and
/// where the bank first affords each of the weapon's fire modes.
/// </summary>
/// <remarks>
/// <para>
/// <b>Entry 067, and brief one's one new figure.</b> The reserve is a ladder in the rules —
/// <see cref="Hexcom.Core.Reactions.ReactionModel.Banked"/> rounds a leftover below the floor to
/// nothing, and a bank only buys a reaction shot once it covers the soldier's own price for the
/// mode — and the panel used to print it as one number, which smoothed the two cliffs a player is
/// deciding against. Every rung here is found by asking <c>Banked</c>, never by multiplying by the
/// fraction: the panel did that inline for months, one rule with two implementations.
/// </para>
/// <para>
/// The price is <c>Stats.Costs.Fire(mode.ApCost)</c>, because that is what
/// <see cref="Tactician.AppraiseHolding"/> checks a bank against and what an overwatch option in a
/// window is filtered by. So what the ground and the soldier say a leftover buys is what the AI
/// believes it buys, which is contract 2.
/// </para>
/// </remarks>
public sealed record ReserveLadder(Unit Unit, IReadOnlyList<ReserveRung> Rungs)
{
    /// <summary>The floor: the fewest points left that bank anything at all. Null if no turn reaches it.</summary>
    public ReserveRung? Floor => Rungs.FirstOrDefault(rung => rung.Price == 0);

    /// <summary>The cheapest shot the bank can buy, which is the first rung worth shooting with.</summary>
    public ReserveRung? Cheapest => Rungs.Where(rung => rung.Price > 0).MinBy(rung => rung.Price);

    /// <summary>
    /// The first shot better than the cheapest — the rung from which the bank buys <i>the better
    /// one</i>. Every dearer mode is a better shot too, and shares its colour.
    /// </summary>
    /// <remarks>
    /// The brief's second cliff is <i>a shot and then the better one</i>, and a rifle has three modes.
    /// Which of the better ones a move can keep depends on where the soldier is going, so the ground
    /// draws the dearest it can keep and the bar names them all; what both agree on is that from this
    /// rung up, the shot banked is better than a snap.
    /// </remarks>
    public ReserveRung? Better
        => Cheapest is { } cheap
            ? Rungs.Where(rung => rung.Price > cheap.Price).MinBy(rung => rung.Price)
            : null;

    /// <summary>What ending a turn on this many points would bank.</summary>
    public int Banked(Battle battle, int leftover) => battle.Reactions.Banked(System.Math.Max(0, leftover));

    /// <summary>The ladder for a soldier, out to the most points it could hold.</summary>
    public static ReserveLadder Of(Battle battle, Unit unit)
    {
        var top = System.Math.Max(unit.Stats.ActionPoints, unit.ActionPoints);
        var rules = battle.Reactions;

        // The fewest leftover points whose bank reaches a figure. Banked only ever rises with the
        // leftover, so the first one found is the cliff.
        int? Reaching(int least)
        {
            for (var left = 0; left <= top; left++)
                if (rules.Banked(left) is var banks && banks > 0 && banks >= least) return left;
            return null;
        }

        var rungs = new List<ReserveRung>();
        if (Reaching(1) is { } floor) rungs.Add(new ReserveRung("banks", floor, rules.Banked(floor), 0));

        foreach (var mode in unit.Weapon.Modes.OrderBy(mode => mode.ApCost))
        {
            var price = unit.Stats.Costs.Fire(mode.ApCost);
            if (Reaching(price) is { } left) rungs.Add(new ReserveRung(mode.Name, left, rules.Banked(left), price));
        }

        return new ReserveLadder(unit, rungs);
    }
}

/// <summary>Everything the sandbox has worked out about the current moment, ready to be drawn.</summary>
/// <param name="Battle">The battle itself. Queried, never changed, by anything that takes a frame.</param>
/// <param name="Layer">Which storey is being looked at. Storeys above it are ghosted.</param>
/// <param name="Hover">The node under the cursor, if it is over the map at all.</param>
/// <param name="Reach">Where the active unit could get to, and for what.</param>
/// <param name="View">What the active unit can make out, per node on the current layer.</param>
/// <param name="LastWindow">What the last committed move got shot at with. Debug readout only.</param>
/// <param name="Turns">
/// The turns <see cref="Commander"/> has taken since a person last did anything, newest last.
/// Empty until somebody hands it a turn.
/// </param>
/// <param name="HostilesAutomatic">Whether every hostile turn goes to <see cref="Commander"/>.</param>
/// <param name="Scenario">The map and the deployment this battle was opened with.</param>
/// <param name="TileDetail">
/// Whether a tile is currently drawn close enough to carry its own labels and outlines. See
/// <see cref="SandboxCamera.LegibleAt"/>.
/// </param>
/// <param name="Open">
/// The reaction window waiting to be answered, if there is one.
/// </param>
/// <param name="Chooser">
/// Which of that window's <see cref="Answerable"/> offers the keyboard is pointed at. Meaningless
/// without one.
/// </param>
/// <param name="AnswerByHand">
/// Whether a move stops at its window rather than taking every recommendation.
/// </param>
/// <param name="Mission">
/// The mission this battle is, read from <c>content/</c>, or null for a bare map.
/// </param>
/// <param name="Briefing">Whether the full six-part briefing is on screen.</param>
/// <param name="OutOfTime">
/// Whether the mission's own round limit has passed. The rules have no clock, so this one is
/// applied by the thing running the battle — see <c>docs/decisions.md</c> entry 047.
/// </param>
/// <param name="Omniscient">
/// Whether the picture shows everything in play, or only what our side knows. See
/// <see cref="Sees"/>.
/// </param>
/// <param name="Knowledge">
/// What our side holds on each hostile in play: eyes on it, or a marker with a credence. A
/// hostile with no entry is one nobody of ours has heard a thing about.
/// </param>
/// <param name="Instruments">
/// Whether the instruments window is open, which is also what lets a player answer reactions for
/// the other side. See <see cref="Answerable"/>.
/// </param>
/// <param name="AimedAt">
/// Who the firing mode was last pointed at, as the node remembers it. Read <see cref="Aim"/>,
/// which is the same thing checked against the moment.
/// </param>
/// <param name="TheirGo">
/// How many seconds the <i>their go</i> banner has been up, or null when it is down. Always zero
/// in a capture, which has no dwell. See <see cref="HexSandbox.TheirGoDwell"/>.
/// </param>
/// <param name="Perceived">
/// What our side perceived of the other side's last go, a line per thing perceived. Empty when
/// nothing was — which is most of the time, and the honest answer.
/// </param>
/// <param name="Found">
/// Hostiles our side has laid eyes on since the last order of ours, so the strip can say a slot is
/// a discovery rather than bookkeeping.
/// </param>
/// <param name="Details">
/// Whether the held key for <i>everything at once</i> is down, so every figure on the map shows its
/// terms together rather than only its headline. See <see cref="BattleHud"/>.
/// </param>
/// <param name="TermsFolded">
/// Whether the player has folded the shot's terms away. Remembered across targets and soldiers,
/// the way the photographed game remembers its fold. Brief one's <i>Settling One</i>.
/// </param>
/// <remarks>
/// This exists so that drawing has no way to reach back into the node and ask another question.
/// A frame is assembled once, in <see cref="HexSandbox.Recalculate"/>, and everything drawn from
/// it is drawn from the same answers — which is also what stops the map and the readouts
/// disagreeing about a unit that a reaction moved half way through the frame.
/// <para>
/// The last two are the greybox's one decision that makes it a game, carried as data. The flat
/// sandbox drew every hostile in play because it was built to drive both sides; a playable view
/// draws our side's knowledge and nothing else. <see cref="Knowledge"/> is that knowledge —
/// <c>Tactician.Known</c> for each of ours, merged by taking the best any of them holds — and it
/// is the same list the scorer weighs, which is contract 2 in <c>docs/map.md</c> as a
/// dictionary. Nothing in the view may ask the battle about a hostile it cannot see through
/// this; that is what <see cref="Sees"/> is for.
/// </para>
/// </remarks>
public sealed record SandboxFrame(
    Battle Battle,
    int Layer,
    NodeId? Hover,
    ReachabilityResult Reach,
    IReadOnlyDictionary<NodeId, SightResult> View,
    string LastWindow,
    IReadOnlyList<TakenTurn> Turns,
    bool HostilesAutomatic,
    SandboxScenario Scenario,
    bool TileDetail,
    ReactionWindow? Open,
    int Chooser,
    bool AnswerByHand,
    Mission? Mission,
    bool Briefing,
    bool OutOfTime,
    bool Omniscient,
    IReadOnlyDictionary<UnitId, Threat> Knowledge,
    bool Instruments,
    Unit? AimedAt,
    double? TheirGo,
    IReadOnlyList<string> Perceived,
    IReadOnlySet<UnitId> Found,
    bool Details,
    bool TermsFolded)
{
    /// <summary>
    /// The active soldier's reserve ladder, or null when nobody is up or the picture must not
    /// describe whoever is. See <see cref="ReserveLadder"/>.
    /// </summary>
    /// <remarks>
    /// Read by both halves: the view cuts the move range into bands at these rungs and the HUD marks
    /// them on the soldier's points. One ladder for both is the same argument as
    /// <see cref="StagedShot"/> — two halves working it out separately is two chances to disagree.
    /// </remarks>
    public ReserveLadder? Ladder
        => !Withheld && Battle.Active is { } active ? ReserveLadder.Of(Battle, active) : null;

    /// <summary>
    /// Whether a hostile is up and the picture must not describe it: the AI is playing it and the
    /// instruments window is shut.
    /// </summary>
    /// <remarks>
    /// <b>Brief five's pause, from the other end.</b> A hostile turn stops on screen only at a window
    /// one of ours can answer, and until this the situation block then described the hostile — its
    /// reserve, its shot at us, and <i>you hold 63/100</i> on each of ours, which is its contact file
    /// as a number and exactly what contract 3 keeps a rung. What the hostile knows is its mind, so
    /// it is behind the same switch as the AI's orders. A side driven by hand is a person playing
    /// both sides, and that person is owed the block.
    /// </remarks>
    public bool Withheld
        => HostilesAutomatic && !Instruments && Battle.Active is { Side: Side.Hostile };

    /// <summary>
    /// The offers in the open window a player is handed: our own side's, or everybody's while the
    /// instruments are open. <see cref="Chooser"/> indexes into this.
    /// </summary>
    public IReadOnlyList<ReactionOffer> Answerable => Open is { } window ? AnswerableIn(window, Instruments) : [];

    /// <summary>The offers in a window a player is handed. See <see cref="Answerable"/>.</summary>
    /// <remarks>
    /// <b>Brief six: your own side only, and the other side's behind the same switch as the AI's
    /// orders.</b> A window used to offer every reactor in it whichever side they were on, which is
    /// right for a harness that drives both sides and wrong for a player on two counts. Answering
    /// the enemy's reaction is playing both sides of the fight; and the list itself was a leak, since
    /// a hostile offered a reaction is a hostile with a line on the mover and a reserve to spend,
    /// named, whether or not anybody of ours has found it. The hostile offers still exist and still
    /// get answered — by their recommendation, the same answer <c>Commander</c> would have given —
    /// they are just not put in front of a player unless the instruments window is.
    /// <para>
    /// Static as well as a property because the sandbox has to ask it of a window before that
    /// window is the open one, to decide whether to stop at it at all.
    /// </para>
    /// </remarks>
    public static IReadOnlyList<ReactionOffer> AnswerableIn(ReactionWindow window, bool instruments)
        => instruments ? window.Offers : window.Offers.Where(o => o.Reactor.Side == Side.Player).ToList();

    /// <summary>
    /// The hostile the active soldier is aiming at, if the firing mode is on and still makes sense.
    /// </summary>
    /// <remarks>
    /// Checked here rather than kept tidy wherever the moment changes, because the moment changes
    /// in more places than anybody would list: a window opening, the target dropping out of sight
    /// after a stance change, the picture going back from omniscient. An aim at a soldier the
    /// picture no longer shows is not an aim — it would put a line of fire on the map pointing at
    /// somebody the map is not drawing, which is the leak <see cref="Sees"/> exists to prevent.
    /// </remarks>
    public Unit? Aim
        => AimedAt is { InPlay: true } quarry
           && Open is null
           && Battle.Active is { } shooter
           && quarry.IsHostileTo(shooter)
           && Sees(quarry)
            ? quarry
            : null;

    /// <summary>The shot the active soldier would take at the aim, or at the cursor when nothing is aimed at.</summary>
    /// <remarks>
    /// The aim wins over the cursor so that a player can move the pointer — to orbit, to read a
    /// label, to look at the ground they would retreat to — without the terms they are about to
    /// confirm being replaced by somebody else's. In the frame rather than the HUD because the map
    /// marks the same shot's bill, and two halves planning the staged shot separately is two
    /// chances to plan different shots.
    /// <para>
    /// None while <see cref="Withheld"/>: a hostile's shot at whoever is under the cursor is the
    /// hostile's to plan, and its terms and its bill would both be drawn.
    /// </para>
    /// </remarks>
    public ShotPlan? StagedShot
        => !Withheld && Battle.Active is { } shooter && (Aim ?? HoveredUnit) is { } quarry && quarry.IsHostileTo(shooter)
            ? Battle.PlanShot(shooter, quarry)
            : null;

    /// <summary>
    /// Who taking the staged shot would tell about the shooter, target first and then by name.
    /// Empty when there is no shot to take.
    /// </summary>
    /// <remarks>
    /// <b>Brief four, and it is one call on Core, not a computation here.</b>
    /// <see cref="Battle.WouldAnnounce(ShotPlan)"/> is the preview of what <c>Battle.Fire</c> does
    /// when it announces a shot — the target's certainty settled, the bang heard at the weapon's
    /// <c>Loudness</c>, the flash seen at its <c>Flash</c> — and it is the same call the AI's scorer
    /// charges a shot's <c>GivenAway</c> by. A preview built from <c>WouldHear</c> and the weapon's
    /// loudness would have covered one of the three channels and been a second route to the same
    /// answer, which is the shape that agrees until somebody tunes one route and not the other.
    /// <para>
    /// What it does not cover is what the target then passes on to its own side, which Core
    /// deliberately leaves out of the preview; see <c>docs/decisions.md</c> for what that costs.
    /// </para>
    /// </remarks>
    public IReadOnlyList<Announcement> Giveaway
        => StagedShot is { CanFire: true } plan
            ? Battle.WouldAnnounce(plan)
                .OrderBy(word => word.Learner != plan.Target)
                .ThenBy(word => word.Learner.Name)
                .ToList()
            : [];

    /// <summary>
    /// Some units by name as the picture is allowed to name them: a hostile nobody of ours has eyes
    /// on is <i>somebody unseen</i>, however many of them there are.
    /// </summary>
    /// <remarks>
    /// The exposure line's rule — that a line exists is geometry and ours, which soldier is at the
    /// far end of it is theirs until we have eyes on them — with one tightening: the unseen are
    /// said once rather than once each, because how many hostiles we have not found are within
    /// earshot is a count of the other side's soldiers. Both the shot's bill and the move's noise
    /// go through this. The move's used to print every listener's name, found or not.
    /// </remarks>
    public string Names(IEnumerable<Unit> units)
    {
        var list = units.ToList();
        var named = list.Where(Sees).Select(u => u.Name).ToList();
        if (list.Any(u => !Sees(u))) named.Add("somebody unseen");
        return named.Count == 0 ? "nobody" : string.Join(", ", named);
    }

    /// <summary>
    /// Everybody the active soldier could aim at, nearest first: the hostiles the picture shows.
    /// </summary>
    /// <remarks>
    /// What <c>Tab</c> cycles, and a soldier the shot would be refused at is still on it — out of
    /// range is a reason worth being told, and the shot line says it. A ghost at a marker is not:
    /// firing needs eyes on, so a list that included ghosts would be offering shots it cannot take.
    /// </remarks>
    public IReadOnlyList<Unit> Targets
        => Battle.Active is not { } shooter
            ? []
            : Battle.InPlay
                .Where(u => u.IsHostileTo(shooter) && Sees(u))
                .OrderBy(u => SandboxGeometry.NodeScene(Battle.Map, u.Position)
                    .DistanceTo(SandboxGeometry.NodeScene(Battle.Map, shooter.Position)))
                .ThenBy(u => u.Name)
                .ToList();

    /// <summary>
    /// Where the subject of the open window is standing <em>now</em>, which is where it started.
    /// </summary>
    /// <remarks>
    /// The distinction the whole readout turns on. A committed move is paid for and not taken:
    /// the mover stands at the start until the window resolves and walks it along, so the dot on
    /// the map is where it is and the route drawn out of it is where it is going. Entry 040.
    /// </remarks>
    public NodeId? Committed => Open?.Move.Start;

    /// <summary>
    /// Whether a unit is drawn as a body where it actually stands, and may be pointed at.
    /// </summary>
    /// <remarks>
    /// Our own soldiers always; everybody, when the picture is omniscient; otherwise a hostile
    /// only while somebody of ours holds eyes on it. Contract 3 permits exactly this and forbids
    /// nothing else — the marker a hostile has moved away from is drawn as a ghost by the view,
    /// and a hostile nobody has heard a thing about is not drawn at all. The cursor goes through
    /// this too, so the shot line cannot quote a soldier the map is not showing.
    /// </remarks>
    public bool Sees(Unit unit)
        => Omniscient
           || unit.Side == Side.Player
           || (Knowledge.TryGetValue(unit.Id, out var held) && held.EyesOn);

    /// <summary>The unit under the cursor, if the picture is allowed to show one there.</summary>
    public Unit? HoveredUnit
        => Hover is { } node && Battle.UnitAt(node) is { } unit && Sees(unit) ? unit : null;
}
