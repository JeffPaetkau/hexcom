using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Battles;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;
using Xunit.Abstractions;

namespace Hexcom.Content.Tests.Kestrel;

/// <summary>
/// What Kestrel Yard offers the mission written on it, measured before the map was called drawn.
/// </summary>
/// <remarks>
/// The waystation's lesson, applied from the start: a map can be wrong about what it offers for a
/// long time without anybody noticing, so the mission book's question for a reconnaissance — is
/// there anywhere to look at the place <em>from</em> — is asked of the node the objective aims at,
/// not of the drawing. Entries 059 and 081 for the waystation; the entry that lands this map for
/// Kestrel.
/// <para>
/// Two things the answers below lean on are the rules' and not the map's, and both are written up
/// for Core. <b>A floor is not a ceiling</b>: sight is stopped by walls and nothing else, so the
/// shed's roof, which the file says is glazing nobody can stand on, hides nothing from anyone
/// higher than its walls. <b>Two storeys of wall are not one wall</b>: a trace takes the largest
/// share any single wall hides, so a line that passes the seam between a ground-floor wall and the
/// one above it sees a sliver through both. The tests assert what is the map's and print what is
/// the rules'.
/// </para>
/// </remarks>
public class KestrelGroundTests(ITestOutputHelper output)
{
    private static Mission Mission => KestrelFight.Mission;

    private readonly Battle _battle = KestrelFight.Start(seed: 1);
    private readonly SightSolver _sight = new(KestrelFight.LoadMap(), Mission.Metres);

    private MovementGraph Graph => _battle.Graph;
    private Reconnaissance Recce => (Reconnaissance)_battle.ObjectiveOf(Side.Player)!;
    private NodeId Target => Recce.Place!.Value;
    private Unit Soldier(string name) => _battle.Units.Single(u => u.Name == name);

    private List<NodeId> Standable => Graph.Nodes.Where(n => n.CanEndTurn).Select(n => n.Id).ToList();

    private List<(NodeId At, double Metres)> Looks()
        => Standable
            .Select(n => (n, t: _sight.Trace(new Vantage(n), new Vantage(Target))))
            .Where(x => x.t.CanSee)
            .Select(x => (x.n, x.t.Distance))
            .ToList();

    private static bool InOffice(NodeId n) => n.Hex.Q is >= 7 and <= 11 && 2 * n.Hex.R + n.Hex.Q is >= -5 and <= 9;

    [Fact]
    public void TheMapDrawnInCharacters()
    {
        var map = KestrelFight.LoadMap();
        for (var layer = 0; layer <= 2; layer++)
            output.WriteLine($"---- storey {layer}\n{MapSketch.Draw(map, layer, Mission)}");
    }

    [Fact]
    public void TheLoadingFloorIsAPlaceInsideAnotherPlace()
    {
        var floor = Mission.NodesOf("loading-floor", Graph);
        var shed = Mission.NodesOf("shed", Graph);

        Assert.Equal(18, floor.Count);
        Assert.All(floor, n => Assert.Contains(n, shed));

        // Its middle is where the objective aims, and the man who sleeps beside it is standing a
        // stride away from it.
        Assert.Equal(new NodeId(new Hex(1, 5), 0), Target);
        Assert.Equal(1, Soldier("Rask").Position.Hex.DistanceTo(Target.Hex));
    }

    /// <summary>
    /// Within the rule's twelve metres the loading floor is looked at from three places: inside
    /// the shed, the yard through the roller door, and the office — the upstairs window and the
    /// roof's west edge. Nothing outside the compound but the office reaches it.
    /// </summary>
    [Fact]
    public void TheLookIsTakenFromTheShedTheYardOrTheOfficeAndFromNowhereElse()
    {
        var shed = Mission.NodesOf("shed", Graph).ToHashSet();
        var yard = Mission.NodesOf("yard", Graph).ToHashSet();

        var close = Looks().Where(l => l.Metres <= Recce.Within).ToList();
        var fromShed = close.Where(l => shed.Contains(l.At)).ToList();
        var fromYard = close.Where(l => yard.Contains(l.At)).ToList();
        var fromOffice = close.Where(l => InOffice(l.At) && l.At.Layer > 0).ToList();

        output.WriteLine($"{close.Count} places within {Recce.Within:0} m have a line to {Target}: " +
                         $"{fromShed.Count} in the shed, {fromYard.Count} in the yard, {fromOffice.Count} in the office");
        foreach (var (at, metres) in fromYard.Concat(fromOffice).OrderBy(l => l.Metres))
            output.WriteLine($"  {at} at {metres:0.0} m");

        Assert.Equal(close.Count, fromShed.Count + fromYard.Count + fromOffice.Count);
        Assert.NotEmpty(fromYard);

        // The yard's looks are all through the roller door: every one of them is east of the
        // shed's middle, in front of the opening.
        Assert.All(fromYard, l => Assert.True(l.At.Hex.Q >= 2, $"{l.At} looks in from the yard west of the door"));

        // The office's are the window the garrison already stands at and the edge of the roof
        // above it, which is the only look anybody can take from outside the wall.
        Assert.Contains(fromOffice, l => l.At.Layer == 1);
        Assert.Contains(fromOffice, l => l.At.Layer == 2);
        Assert.All(fromOffice, l => Assert.Equal(7, l.At.Hex.Q));
    }

    /// <summary>
    /// The duct lands behind the racking, with no line to the floor, one stride from places that
    /// have one — the waystation's drain, again, and not drawn to be.
    /// </summary>
    [Fact]
    public void TheDuctLandsBehindTheRackingOneStrideFromALook()
    {
        var duct = new NodeId(new Hex(-5, 12), 0);
        var boiler = new NodeId(new Hex(-5, 13), 0);

        Assert.True(Graph.CanEndTurn(duct), "the duct does not open anywhere anybody can stand");
        Assert.Contains(Graph.LinksFrom(boiler), l => l.To == duct && l.Kind == TraversalKind.Crawl);

        var looks = Looks().Where(l => l.Metres <= Recce.Within).Select(l => l.At).ToHashSet();
        Assert.DoesNotContain(duct, looks);
        Assert.Contains(looks, n => n.Layer == 0 && n.Hex.DistanceTo(duct.Hex) == 1);
    }

    /// <summary>
    /// The side door is the one place with a line to the floor that no post can see — and it is
    /// a stride and a half past the rule's twelve metres, so it is a look that does not count.
    /// </summary>
    [Fact]
    public void TheOnlyUnwatchedLineToTheFloorIsThroughTheSideDoorAndItIsTooFar()
    {
        var posts = _battle.Units.Where(u => u.Side == Side.Hostile).Select(u => new Vantage(u.Position)).ToList();

        var unwatched = Looks()
            .Where(l => !posts.Any(p => _sight.CanSee(p, new Vantage(l.At))))
            .ToList();

        foreach (var (at, metres) in unwatched) output.WriteLine($"unwatched line to the floor from {at} at {metres:0.0} m");

        var alley = Assert.Single(unwatched);
        Assert.Equal(new NodeId(new Hex(-8, 9), 0), alley.At);
        Assert.True(alley.Metres > Recce.Within, $"the side door look is {alley.Metres:0.0} m, inside the rule's {Recce.Within} m");
    }

    [Fact]
    public void TheGateCannotSeeRoundTheCornerToWhereTheSquadStarts()
    {
        var duvall = Soldier("Duvall");
        foreach (var ours in _battle.Units.Where(u => u.Side == Side.Player))
            Assert.False(_battle.CanSee(duvall, ours), $"the gate can see {ours.Name} at the start");
    }

    [Fact]
    public void TheExitIsUpstairsAndTheStepsAreTheOnlyWayUpToIt()
    {
        var exit = Mission.NodesOf("footbridge", Graph);
        Assert.Equal(3, exit.Count);
        Assert.All(exit, n => Assert.Equal(1, n.Layer));
        Assert.True(Recce.IsExit(exit[0]));

        var from = Soldier("Tolliver").Position;
        var reach = Pathfinder.Reachable(Graph, from, int.MaxValue);
        Assert.All(exit, n => Assert.True(reach.CanReach(n), $"{n} cannot be walked to"));

        var up = Graph.AllLinks.Where(l => exit.Contains(l.To) && l.From.Layer == 0).ToList();
        var step = Assert.Single(up);
        Assert.Equal(TraversalKind.Stairs, step.Kind);
    }

    [Fact]
    public void TheFireEscapeGoesPastTheUpperFloorWithoutAWayIn()
    {
        var landing = new NodeId(new Hex(12, -4), 1);
        var into = Graph.LinksFrom(landing).Where(l => l.To.Layer == 1 && InOffice(l.To)).ToList();
        Assert.Empty(into);
        Assert.Contains(Graph.LinksFrom(landing), l => l.To.Layer == 2 && l.Kind == TraversalKind.Ladder);
    }

    // ---- the size question -------------------------------------------------------------

    /// <summary>
    /// What a map a little over half as far across does to the ranges, side by side with the
    /// waystation, from each garrison post: how much of the standable ground it has a line to,
    /// and how far the longest of those lines is.
    /// </summary>
    [Fact]
    public void ATownShortensEveryLineThePostsHave()
    {
        var kestrel = Reach(KestrelFight.Mission);
        var waystation = Reach(MissionLibrary.Load("waystation"));

        foreach (var (name, lines) in new[] { ("kestrel", kestrel), ("waystation", waystation) })
        {
            output.WriteLine(name);
            foreach (var p in lines)
                output.WriteLine($"  {p.Name,-8} sees {p.Seen,5} of {p.Of} places ({100.0 * p.Seen / p.Of:0}%), longest {p.Longest:0.0} m, within sight range {p.WithinRange}");
        }

        Assert.True(kestrel.Max(p => p.Longest) < waystation.Max(p => p.Longest));
    }

    private sealed record PostReach(string Name, int Seen, int Of, double Longest, int WithinRange);

    private static List<PostReach> Reach(Mission mission)
    {
        var battle = mission.Begin(seed: 1);
        var sight = new SightSolver(mission.LoadMap(), Mission.Metres);
        var range = battle.Awareness.Model.SightRangeMetres;
        var standable = battle.Graph.Nodes.Where(n => n.CanEndTurn).Select(n => n.Id).ToList();

        return battle.Units.Where(u => u.Side == Side.Hostile).Select(post =>
        {
            var lines = standable
                .Where(n => n != post.Position)
                .Select(n => sight.Trace(new Vantage(post.Position), new Vantage(n)))
                .Where(t => t.CanSee)
                .ToList();
            return new PostReach(post.Name, lines.Count, standable.Count, lines.Max(t => t.Distance), lines.Count(t => t.Distance <= range));
        }).ToList();
    }
}
