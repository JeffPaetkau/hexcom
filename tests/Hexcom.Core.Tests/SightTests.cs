using System.Linq;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using Hexcom.Core.Movement;
using Hexcom.Core.Vision;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// Sight and cover come out of one trace, so these tests read as situations rather than as
/// unit tests of separate methods: who is where, standing how, with what between them.
/// </summary>
public class SightTests
{
    /// <summary>One metre from centre to corner, so a hex is two metres across and units stand a stride apart.</summary>
    private static HexLayout Layout => new(size: 1.0);

    private static Vantage At(int q, int r, Stance stance = Stance.Standing, int layer = 0)
        => new(new NodeId(new Hex(q, r), layer), stance);

    private static (BattleMap Map, SightSolver Sight) OpenGround(int radius = 8)
    {
        var map = new BattleMap().FillDisc(Hex.Zero, radius);
        return (map, new SightSolver(map, Layout));
    }

    /// <summary>
    /// Puts a wall on the side of the target hex facing the shooter. The shooter sits along the
    /// north-east spoke, so the wall goes on the target's north-east face.
    /// </summary>
    private static (BattleMap Map, SightSolver Sight) Barrier(WallProfile profile, int layer = 0)
    {
        var (map, _) = OpenGround();
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, layer, profile);
        return (map, new SightSolver(map, Layout));
    }

    // ---- nothing in the way ----------------------------------------------------

    [Fact]
    public void AcrossOpenGroundEveryoneSeesEveryone()
    {
        var (_, sight) = OpenGround();
        var result = sight.Trace(At(4, 0), At(0, 0));

        Assert.True(result.CanSee);
        Assert.Equal(CoverGrade.None, result.Cover);
        Assert.Null(result.CoverSource);
        Assert.True(result.IsClearShot);
        Assert.Equal(1.0, result.Exposure, 6);
        Assert.Empty(result.Obstructions);
    }

    [Fact]
    public void DistanceIsMeasuredInMetresThroughTheAir()
    {
        var (_, sight) = OpenGround();

        var result = sight.Trace(At(4, 0), At(0, 0));

        // Four hexes along a spoke is four times the centre pitch on the ground, but the
        // reported distance is eye to centre of mass, so it also climbs down 0.75 m.
        var ground = 4 * Layout.Pitch;
        var drop = StanceProfile.Standing.EyeHeight - StanceProfile.Standing.CentreHeight;
        Assert.Equal(Math.Sqrt(ground * ground + drop * drop), result.Distance, 6);
        Assert.True(result.Distance > ground);
    }

    [Fact]
    public void SightIsSymmetric()
    {
        var (_, sight) = Barrier(WallProfile.Solid);

        Assert.Equal(
            sight.CanSee(At(3, 0), At(0, 0)),
            sight.CanSee(At(0, 0), At(3, 0)));
    }

    // ---- opaque walls ----------------------------------------------------------

    [Fact]
    public void ABuildingWallHidesWhoeverIsBehindIt()
    {
        var (_, sight) = Barrier(WallProfile.Solid);
        var result = sight.Trace(At(3, 0), At(0, 0));

        Assert.False(result.CanSee);
        Assert.NotNull(result.Blocker);
        Assert.Equal("solid", result.Blocker!.Value.Profile.Id);
        Assert.Equal(0, result.Exposure);
    }

    [Fact]
    public void SmokeHidesYouEvenThoughYouCanWalkThroughIt()
    {
        var (_, sight) = Barrier(WallProfile.Screen);
        Assert.False(sight.CanSee(At(3, 0), At(0, 0)));
    }

    [Fact]
    public void ChainLinkHidesNothing()
    {
        var (_, sight) = Barrier(WallProfile.Railing);
        var result = sight.Trace(At(3, 0), At(0, 0));

        Assert.True(result.CanSee);
        Assert.Equal(1.0, result.Exposure, 6); // see-through, so nothing of the target is concealed
        Assert.Equal(CoverGrade.Light, result.Cover); // but it will still stop a round or two
    }

    // ---- waist-high cover ------------------------------------------------------

    [Fact]
    public void StandingBehindSandbagsIsHalfCoverAndStillPlainlyVisible()
    {
        var (_, sight) = Barrier(WallProfile.Low);
        var result = sight.Trace(At(3, 0), At(0, 0));

        Assert.True(result.CanSee);
        Assert.Equal(CoverGrade.Half, result.Cover);
        Assert.Equal("low", result.CoverSource!.Value.Profile.Id);
        Assert.InRange(result.Exposure, 0.3, 0.7);
    }

    [Fact]
    public void GoingProneBehindSandbagsTakesYouOutOfSightAltogether()
    {
        var (_, sight) = Barrier(WallProfile.Low);

        Assert.True(sight.CanSee(At(3, 0), At(0, 0)));
        Assert.True(sight.CanSee(At(3, 0), At(0, 0, Stance.Crouching)));
        Assert.False(sight.CanSee(At(3, 0), At(0, 0, Stance.Prone)));
    }

    [Fact]
    public void CrouchingLowersYourProfileBehindTheSameWall()
    {
        var (_, sight) = Barrier(WallProfile.Low);

        var standing = sight.Trace(At(3, 0), At(0, 0));
        var crouching = sight.Trace(At(3, 0), At(0, 0, Stance.Crouching));

        Assert.True(crouching.Exposure < standing.Exposure);
        Assert.True(crouching.CanSee);
    }

    [Fact]
    public void AWallFarDownTheLineIsNotYourCover()
    {
        // Sandbags around the shooter, not the target: the line clears them immediately.
        var (map, _) = OpenGround();
        map.AddSideWall(new Hex(6, 0), HexDirection.SouthWest, 0, WallProfile.Low);
        var sight = new SightSolver(map, Layout);

        var result = sight.Trace(At(6, 0), At(0, 0));

        Assert.True(result.CanSee);
        Assert.Equal(CoverGrade.None, result.Cover);
    }

    [Fact]
    public void AnAttackerAtPointBlankShootsDownOverTheWall()
    {
        var (_, sight) = Barrier(WallProfile.Low);

        var distant = sight.Trace(At(4, 0), At(0, 0));
        var adjacent = sight.Trace(At(1, 0), At(0, 0));

        Assert.Equal(CoverGrade.Half, distant.Cover);
        Assert.True(adjacent.Cover < distant.Cover);
    }

    // ---- height ----------------------------------------------------------------

    [Fact]
    public void ShootingDownFromARoofCancelsWaistHighCover()
    {
        var (map, _) = OpenGround();
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.Low);
        map.SetTile(new TileAddress(new Hex(3, 0), 1), 3.5); // a rooftop overlooking the position
        var sight = new SightSolver(map, Layout);

        var fromGround = sight.Trace(At(3, 0), At(0, 0));
        var fromRoof = sight.Trace(At(3, 0, layer: 1), At(0, 0));

        Assert.Equal(CoverGrade.Half, fromGround.Cover);
        Assert.Equal(CoverGrade.None, fromRoof.Cover);
        Assert.True(fromRoof.HasHighGround);
        Assert.Equal(3.5, fromRoof.HeightAdvantage, 6);
    }

    [Fact]
    public void AHeadHighWallStillCoversYouFromAbove()
    {
        var (map, _) = OpenGround();
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 0, WallProfile.High);
        map.SetTile(new TileAddress(new Hex(3, 0), 1), 3.5);
        var sight = new SightSolver(map, Layout);

        var fromRoof = sight.Trace(At(3, 0, layer: 1), At(0, 0));

        // High ground buys you the shot, but not an unobstructed one.
        Assert.True(fromRoof.CanSee);
        Assert.Equal(CoverGrade.Full, fromRoof.Cover);
    }

    [Fact]
    public void AHeadHighWallHidesYouCompletelyFromLevelGround()
    {
        var (_, sight) = Barrier(WallProfile.High);
        Assert.False(sight.CanSee(At(3, 0), At(0, 0)));
    }

    [Fact]
    public void AWallOnAnUpperStoreyDoesNotBlockTheGroundFloor()
    {
        var (map, _) = OpenGround();
        map.SetTile(new TileAddress(new Hex(1, 0), 1), 3.5);
        map.SetTile(new TileAddress(Hex.Zero, 1), 3.5);
        map.AddSideWall(Hex.Zero, HexDirection.NorthEast, 1, WallProfile.Solid);
        var sight = new SightSolver(map, Layout);

        // The wall is a storey up; the sight line passes underneath it.
        Assert.True(sight.CanSee(At(3, 0), At(0, 0)));

        // And still does its job for anyone up there.
        Assert.False(sight.CanSee(At(1, 0, layer: 1), At(0, 0, layer: 1)));
    }

    // ---- walls inside a hex ----------------------------------------------------

    [Fact]
    public void ABarricadeAcrossTheTargetTileCoversThem()
    {
        var (map, _) = OpenGround();
        map.AddChord(Hex.Zero, 5, 1, 0, WallProfile.Low); // clips the north-east corner
        var sight = new SightSolver(map, Layout);

        var result = sight.Trace(At(4, 0), At(0, 0));

        Assert.True(result.CanSee);
        Assert.Equal(CoverGrade.Half, result.Cover);
    }

    // ---- the demo map ----------------------------------------------------------

    [Fact]
    public void TheCompoundWallBlocksSightJustAsItBlocksMovement()
    {
        var map = DemoMaps.Compound();
        var sight = new SightSolver(map, Layout);

        // Level with the unbroken part of the wall.
        Assert.False(sight.CanSee(At(0, 2), At(4, 2)));

        // Level with the breach, where the wall is missing.
        Assert.True(sight.CanSee(At(0, 0), At(4, 0)));
    }

    [Fact]
    public void TheHedgeBlocksSightWhileLettingPeopleThrough()
    {
        var map = DemoMaps.Compound();
        var sight = new SightSolver(map, Layout);
        var graph = MovementGraph.Build(map);

        var behind = new NodeId(new Hex(0, -2), 0);
        var infront = new NodeId(new Hex(-1, -2), 0);

        Assert.False(sight.CanSee(new Vantage(infront), new Vantage(behind)));
        Assert.Contains(graph.LinksFrom(infront), l => l.To == behind);
    }

    [Fact]
    public void TheRoofOverlooksTheGroundItStandsOver()
    {
        var map = DemoMaps.Compound();
        var sight = new SightSolver(map, Layout);

        var ground = Hex.Zero.WithinRange(6)
            .Select(h => new Vantage(new NodeId(h, 0)))
            .Where(v => map.HasTile(v.Node.Tile))
            .ToList();

        var fromRoof = ground.Count(v => sight.CanSee(new Vantage(new NodeId(new Hex(4, 0), layer: 1)), v));
        var fromStreet = ground.Count(v => sight.CanSee(new Vantage(new NodeId(new Hex(4, 0), 0)), v));

        // Climbing the ladder is what buys the overwatch position its value.
        Assert.True(fromRoof > fromStreet, $"roof saw {fromRoof}, street saw {fromStreet}");

        // But not everything: the compound wall is three metres tall and still blocks some of it.
        Assert.True(fromRoof < ground.Count);
    }

    // ---- api -------------------------------------------------------------------

    [Fact]
    public void VisibleFiltersACandidateList()
    {
        var (_, sight) = Barrier(WallProfile.Solid);
        var observer = At(3, 0);
        var candidates = new[] { At(0, 0), At(3, 1), At(2, 0) };

        var seen = sight.Visible(observer, candidates).ToList();

        Assert.DoesNotContain(At(0, 0), seen);
        Assert.Contains(At(3, 1), seen);
    }

    [Fact]
    public void AUnitCanAlwaysSeeItself()
    {
        var (_, sight) = Barrier(WallProfile.Solid);
        var result = sight.Trace(At(0, 0), At(0, 0));

        Assert.True(result.CanSee);
        Assert.Equal(CoverGrade.None, result.Cover);
    }

    [Fact]
    public void TracingFromNowhereIsAnError()
    {
        var (_, sight) = OpenGround(radius: 1);
        Assert.Throws<ArgumentException>(() => sight.Trace(At(20, 0), At(0, 0)));
    }

    [Fact]
    public void StanceProfilesDescendInOrder()
    {
        Assert.True(StanceProfile.Standing.EyeHeight > StanceProfile.Crouching.EyeHeight);
        Assert.True(StanceProfile.Crouching.EyeHeight > StanceProfile.Prone.EyeHeight);
        Assert.True(StanceProfile.Standing.BodyHeight > StanceProfile.Crouching.BodyHeight);
        Assert.True(StanceProfile.Prone.ConcealmentBonus > StanceProfile.Standing.ConcealmentBonus);
        Assert.Equal(StanceProfile.Crouching, StanceProfile.For(Stance.Crouching));
    }
}
