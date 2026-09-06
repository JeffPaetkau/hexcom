using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Geometry;
using Hexcom.Core.Hexes;
using Xunit;

namespace Hexcom.Core.Tests;

/// <summary>
/// The corner model underpins the whole cover system, so these tests prove the two claims it
/// rests on: a corner has one identity no matter which of its three hexes names it, and that
/// identity really does land on the same point in the world.
/// </summary>
public class HexVertexTests
{
    private static IEnumerable<Hex> Patch(int radius = 3) => Hex.Zero.WithinRange(radius);

    [Fact]
    public void AHexHasSixDistinctCorners()
    {
        foreach (var hex in Patch())
            Assert.Equal(6, hex.Corners().Distinct().Count());
    }

    [Fact]
    public void EveryCornerIsSharedByExactlyThreeHexesThatAllAgreeOnIt()
    {
        foreach (var hex in Patch())
        foreach (var vertex in hex.Corners())
        {
            var incident = vertex.IncidentCorners().ToList();

            Assert.Equal(3, incident.Count);
            Assert.Equal(3, incident.Select(i => i.Hex).Distinct().Count());
            Assert.Contains(hex, incident.Select(i => i.Hex));

            // Asking any of the three hexes for that corner index gives the same vertex back.
            foreach (var (owner, cornerIndex) in incident)
                Assert.Equal(vertex, owner.Corner(cornerIndex));
        }
    }

    [Fact]
    public void CornerNamesArePoleUniqueAcrossThePlane()
    {
        // Each corner is the east corner of exactly one hex or the west corner of exactly one
        // hex, never both. That is what makes two poles per hex enough to name them all.
        var byOwner = new Dictionary<HexVertex, int>();

        foreach (var hex in Patch(5))
        foreach (var vertex in hex.Corners())
            byOwner[vertex] = byOwner.GetValueOrDefault(vertex) + 1;

        Assert.All(byOwner.Keys, v => Assert.Equal(v, new Hex(v.Q, v.R).Corner(v.Pole == VertexPole.East ? 0 : 3)));
    }

    [Fact]
    public void CornerIndexOfIsTheInverseOfCorner()
    {
        foreach (var hex in Patch())
        {
            for (var i = 0; i < 6; i++)
                Assert.Equal(i, hex.CornerIndexOf(hex.Corner(i)));

            // A corner of a hex three steps away is not a corner of this one.
            Assert.Equal(-1, hex.CornerIndexOf(new Hex(hex.Q + 3, hex.R).Corner(0)));
        }
    }

    [Fact]
    public void SideIIsBoundedByCornersIAndIPlusOne()
    {
        foreach (var direction in HexDirectionExtensions.All)
        {
            var (a, b) = direction.Corners();
            Assert.Equal((int)direction, a);
            Assert.Equal(((int)direction + 1) % 6, b);
        }
    }

    [Fact]
    public void AdjacentHexesShareExactlyTheTwoCornersOfTheirCommonSide()
    {
        var hex = new Hex(1, -2);

        foreach (var direction in HexDirectionExtensions.All)
        {
            var neighbour = hex.Neighbor(direction);
            var shared = hex.Corners().Intersect(neighbour.Corners()).ToList();

            Assert.Equal(2, shared.Count);

            var (a, b) = direction.Corners();
            Assert.Contains(hex.Corner(a), shared);
            Assert.Contains(hex.Corner(b), shared);

            // And the neighbour reaches the same two corners through its opposite side.
            var (na, nb) = direction.Opposite().Corners();
            Assert.Equal(
                new HashSet<HexVertex>(shared),
                new HashSet<HexVertex> { neighbour.Corner(na), neighbour.Corner(nb) });
        }
    }

    [Fact]
    public void SharedHexesCountDistinguishesSidesFromChords()
    {
        var hex = new Hex(0, 0);

        // Adjacent corners bound a side, so two hexes host that segment.
        Assert.Equal(2, hex.Corner(0).SharedHexesWith(hex.Corner(1)).Count());

        // Chords live inside a single hex.
        Assert.Equal(hex, Assert.Single(hex.Corner(0).SharedHexesWith(hex.Corner(2))));
        Assert.Equal(hex, Assert.Single(hex.Corner(0).SharedHexesWith(hex.Corner(3))));
    }

    [Fact]
    public void ThreeHexesNamingOneCornerPutItInTheSameWorldPosition()
    {
        var layout = new HexLayout(size: 1.0);

        foreach (var hex in Patch())
        foreach (var vertex in hex.Corners())
        {
            var positions = vertex.IncidentCorners()
                .Select(i => layout.Corner(i.Hex, i.CornerIndex))
                .ToList();

            foreach (var position in positions)
                Assert.True(
                    Vec2.Distance(positions[0], position) < 1e-9,
                    $"{vertex} disagreed: {positions[0]} vs {position}");

            Assert.True(Vec2.Distance(positions[0], layout.Position(vertex)) < 1e-9);
        }
    }

    [Fact]
    public void CornersSitOnTheCircumcircleAtSixtyDegreeSteps()
    {
        var layout = new HexLayout(size: 2.0);
        var hex = new Hex(-2, 1);
        var center = layout.Center(hex);

        for (var i = 0; i < 6; i++)
        {
            var offset = layout.Corner(hex, i) - center;
            Assert.Equal(2.0, offset.Length, 9);
            Assert.Equal(Geometry2D.NormalizeAngle(Math.PI / 3 * i), Geometry2D.NormalizeAngle(offset.Angle), 9);
        }
    }
}
