using Godot;
using Hexcom.Core.Hexes;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;

namespace Hexcom.Game;

/// <summary>
/// The two scales the view lives between: the world the rules are computed in, in metres, and
/// the canvas they are drawn on, in pixels.
/// </summary>
/// <remarks>
/// <para>
/// A <see cref="HexLayout"/> looks like a drawing concern and is not one.
/// <c>SightSolver</c> builds a three-dimensional point from a layout position (X, Y) and a floor
/// height (Z) that is measured in metres, then takes distances across the result — so the
/// layout's horizontal units <i>are</i> metres, necessarily. The sandbox built one 44-unit
/// layout and used it for both jobs until this type existed, which told the rules that a hex was
/// 44 metres across while a solid wall was three metres tall. See <c>docs/decisions.md</c>
/// entries 002 and 005.
/// </para>
/// <para>
/// What that broke is worth being precise about, because the obvious guess is wrong. Sight and
/// cover are <b>unaffected</b>: the solver projects a wall top onto the target using the
/// fraction of the way along the sight line it sits at, and a fraction has no units, so the
/// silhouette arithmetic is the same at any horizontal scale. The cover radius is
/// <c>layout.Pitch</c>, which scales with the grid, so even which walls count as cover does not
/// move. Measured on the demo map, the cover grades at size 44 and size 1 are identical.
/// </para>
/// <para>
/// What breaks is everything priced in metres — detection, noise, voice, weapon range — because
/// those are absolute figures compared against a distance that is not. At size 44 the demo
/// compound is 914 metres across, every soldier on it is far beyond
/// <c>AwarenessModel.SightRangeMetres</c> of 45, and no enemy ever notices anybody: six turns in,
/// all three hostiles are still <c>Unaware</c>, where at size 1 the roof spotter reaches
/// <c>Searching</c>. A stealth game where nobody can be detected is the failure this type exists
/// to prevent, and it is invisible on screen — which is why it survived so long.
/// </para>
/// <para>
/// So there are two layouts and one rule about them: <see cref="World"/> is the only one that
/// may be handed to anything under <c>Hexcom.Core</c>, and <see cref="Canvas"/> is the only one
/// that may reach a draw call. Nothing converts between them, because nothing needs to — the
/// rules never hand back a position to be drawn, only distances to be read. If that ever changes,
/// convert here rather than at the call site.
/// </para>
/// </remarks>
public sealed class SandboxScale
{
    /// <summary>
    /// How many metres one hex radius is worth. <b>Interim.</b>
    /// </summary>
    /// <remarks>
    /// <para>
    /// Nobody has decided this number. 1.0 is what every test in <c>tests/</c> uses — a hex two
    /// metres corner to corner and 1.73 metres between centres — so adopting it here makes the
    /// sandbox agree with the only other place the question is answered, which is the most
    /// defensible thing to do while the question is open. It is an interim value, not a
    /// decision: the figure belongs to the content territory, and the open question is recorded
    /// in <c>docs/subprojects/content.md</c> and <c>docs/decisions.md</c> entry 002.
    /// </para>
    /// <para>
    /// It is deliberately a constant and not an <c>[Export]</c>, unlike the pixel size beside it.
    /// Rendering scale is a matter of taste and may be fiddled with per scene; world scale is a
    /// rule that the tests, the awareness ranges and eventually the art all have to agree on, and
    /// a value the inspector can quietly override is not a rule. When content settles the figure
    /// this is the one line that changes.
    /// </para>
    /// </remarks>
    public const double MetresPerHexSize = 1.0;

    /// <summary>Metres. The only layout <c>Hexcom.Core</c> is ever given.</summary>
    public HexLayout World { get; }

    /// <summary>Pixels. The only layout that reaches a draw call.</summary>
    public HexLayout Canvas { get; }

    /// <summary>Hex radius in pixels — the drawing figure the sandbox is laid out against.</summary>
    public float HexPixels { get; }

    public SandboxScale(float hexPixels)
    {
        HexPixels = hexPixels;
        World = new HexLayout(MetresPerHexSize);
        Canvas = new HexLayout(hexPixels);
    }

    /// <summary>Pixels to a metre, for drawing anything the rules measure in metres.</summary>
    public float PixelsPerMetre => (float)(HexPixels / MetresPerHexSize);

    /// <summary>A distance the rules quote in metres, as a length on the canvas.</summary>
    public float MetresToPixels(double metres) => (float)(metres * PixelsPerMetre);

    /// <summary>
    /// A length quoted in hex radii, as a length on the canvas. For figures chosen because they
    /// read well rather than because they mean anything — see <c>BattleView.ConeHexRadii</c>.
    /// </summary>
    /// <remarks>
    /// Takes and returns <c>float</c>, the width the drawing figures are written in, so that the
    /// arithmetic here is the same arithmetic as the <c>HexSize * 0.16f</c> it replaced. Nothing
    /// dramatic turns on it — the <c>double</c> form rendered identically when it was tried —
    /// but a conversion that cannot change a result is one less thing to rule out the next time
    /// a picture disagrees with the one before it.
    /// </remarks>
    public float HexRadiiToPixels(float radii) => radii * HexPixels;

    /// <summary>
    /// Canvas space to Godot's screen space. The grid is built with Y running up, the way the
    /// geometry in <c>Hexcom.Core</c> has it; Godot draws with Y running down.
    /// </summary>
    public static Vector2 ToScreen(CoreVec2 canvas) => new((float)canvas.X, (float)-canvas.Y);

    /// <summary>Godot's screen space back to canvas space, for hit-testing the cursor.</summary>
    public static CoreVec2 FromScreen(Vector2 screen) => new(screen.X, -screen.Y);
}
