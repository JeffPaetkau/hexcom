using System.Linq;
using Godot;
using Hexcom.Core.Hexes;
using Hexcom.Core.Maps;
using CoreVec2 = Hexcom.Core.Geometry.Vec2;

namespace Hexcom.Game;

/// <summary>
/// Where the map is being looked at from, and how close: a focus point on the canvas and a hex
/// size in pixels.
/// </summary>
/// <remarks>
/// <para>
/// The sandbox had no camera because it never needed one. The demo compound is radius 6 and fits
/// in a viewport twice over at any sensible drawing scale, so the node sat at the middle of the
/// screen and every tile was on it. A map at the size <c>docs/decisions.md</c> entry 007 asks for
/// does not fit: the waystation is radius 24, and at the 44-pixel hex the compound was drawn
/// with it is about 3700 pixels across against a 1600 pixel viewport. So either the map gets
/// smaller or the view learns to move, and the map is the one that is right.
/// </para>
/// <para>
/// Zooming is what makes entry 006 solvable rather than merely stateable. The honest attention
/// cone reaches <c>AwarenessModel.SightRangeMetres</c>, 45 metres, which at 44 pixels to the
/// metre is 1980 pixels — the screen-filling wash that entry describes. It is not a wash at the
/// zoom the whole waystation is seen at, because at that zoom 45 metres is about half the width
/// of the map, which is exactly what it is. The cone was never too long; the view was too close.
/// </para>
/// <para>
/// <b>Zoom is a drawing figure and nothing else.</b> It moves
/// <see cref="SandboxScale.HexPixels"/> and never <see cref="SandboxScale.MetresPerHexSize"/>,
/// which is why the scale and the geometry are rebuilt here rather than mutated: a
/// <see cref="SandboxScale"/> is cheap, immutable, and the one place that holds the two apart.
/// Handing a zoomed layout to <c>Hexcom.Core</c> would be entry 002 all over again, one frame at
/// a time.
/// </para>
/// </remarks>
public sealed class SandboxCamera
{
    /// <summary>Closest the map may be drawn, in pixels to a hex radius.</summary>
    public const float Closest = 96f;

    /// <summary>Furthest out. Radius 24 fits a 1600-pixel viewport at about 18.</summary>
    public const float Furthest = 5f;

    /// <summary>
    /// Below this hex size a tile stops carrying its own detail — cost labels, cover outlines,
    /// the region inset.
    /// </summary>
    /// <remarks>
    /// An interface judgement rather than a performance one, though it is both. A two-digit AP
    /// cost set at 15 points does not fit inside a 14-pixel hex, and eighteen hundred of them
    /// overlapping is worse than nothing: the reader loses the map underneath and gains no
    /// number. What survives zoomed out is what is legible zoomed out — ground, walls, soldiers,
    /// and who is attending to where.
    /// </remarks>
    public const float LegibleAt = 22f;

    /// <summary>How much a wheel notch or a zoom key changes the hex size.</summary>
    private const float ZoomStep = 1.25f;

    public SandboxCamera(float hexPixels)
    {
        HexPixels = Mathf.Clamp(hexPixels, Furthest, Closest);
        Rebuild();
    }

    /// <summary>Hex radius in pixels. The drawing scale, and never the world one.</summary>
    public float HexPixels { get; private set; }

    /// <summary>
    /// The canvas point held at the centre of the viewport, in pixels at the current zoom.
    /// </summary>
    /// <remarks>
    /// Kept in canvas pixels rather than in hexes so that panning is the same arithmetic as the
    /// mouse drag that drives it. A zoom rescales it by the same factor it rescales everything
    /// else, which is what makes zooming leave the middle of the screen where it was.
    /// </remarks>
    public CoreVec2 Focus { get; private set; }

    /// <summary>The two layouts, rebuilt whenever the zoom moves.</summary>
    public SandboxScale Scale { get; private set; } = null!;

    /// <summary>Canvas geometry against the current zoom.</summary>
    public SandboxGeometry Geometry { get; private set; } = null!;

    /// <summary>Whether a tile is currently big enough to be worth labelling. See <see cref="LegibleAt"/>.</summary>
    public bool ShowsTileDetail => HexPixels >= LegibleAt;

    /// <summary>Where the node has to sit for <see cref="Focus"/> to land in the middle of the screen.</summary>
    public Vector2 ScreenOffset(Vector2 viewport)
        => viewport * 0.5f - SandboxScale.ToScreen(Focus);

    /// <summary>
    /// The canvas rectangle the viewport currently shows, in the screen space drawing works in,
    /// grown by a margin so that a shape whose centre is just outside still gets drawn.
    /// </summary>
    /// <remarks>
    /// Drawing culls against this. Eighteen hundred tiles is four thousand draw calls a frame
    /// for a map of which a twentieth is on screen, and the cull is one rectangle test — but the
    /// margin matters more than the saving: a soldier's attention field reaches 45 metres, so
    /// the unit casting it can be well off screen while the thing it is watching is not. The
    /// margin is therefore quoted in hex radii and the callers that need a long one ask for it.
    /// </remarks>
    public Rect2 Visible(Vector2 viewport, float marginHexRadii = 2f)
    {
        var margin = Scale.HexRadiiToPixels(marginHexRadii);
        return new Rect2(-ScreenOffset(viewport), viewport).Grow(margin);
    }

    /// <summary>Look at a point on the canvas.</summary>
    public void LookAt(CoreVec2 canvas) => Focus = canvas;

    /// <summary>Look at the middle of a hex.</summary>
    public void LookAt(Hex hex) => Focus = Scale.Canvas.Center(hex);

    /// <summary>Drag the map by a screen distance — the cursor keeps hold of the ground under it.</summary>
    public void Pan(Vector2 screen) => Focus -= SandboxScale.FromScreen(screen);

    /// <summary>One notch in or out, about the middle of the screen.</summary>
    public void ZoomBy(int notches) => ZoomTo(HexPixels * Mathf.Pow(ZoomStep, notches));

    /// <summary>
    /// Zoom keeping one canvas point where it is on screen — what a wheel over a map should do.
    /// </summary>
    /// <remarks>
    /// A zoom multiplies every canvas coordinate by the same factor, so the point <c>p</c> ends
    /// up at <c>p·k</c> and would only stay put if the focus went to <c>p·k - p + focus</c>.
    /// <see cref="ZoomTo"/> takes it to <c>focus·k</c>, so the correction is the difference,
    /// which is <c>(p - focus)(k - 1)</c> — and it has to be measured against the focus as it was
    /// before the zoom, not after.
    /// </remarks>
    public void ZoomAbout(int notches, CoreVec2 canvas)
    {
        var before = HexPixels;
        var focus = Focus;

        ZoomBy(notches);
        Focus += (canvas - focus) * (HexPixels / before - 1);
    }

    /// <summary>Zoom to a hex size, clamped, keeping the middle of the screen where it is.</summary>
    public void ZoomTo(float hexPixels)
    {
        var clamped = Mathf.Clamp(hexPixels, Furthest, Closest);
        if (Mathf.IsEqualApprox(clamped, HexPixels)) return;

        Focus *= clamped / HexPixels;
        HexPixels = clamped;
        Rebuild();
    }

    /// <summary>
    /// Pull back until the whole map is on screen at once.
    /// </summary>
    /// <remarks>
    /// Every storey, not the one being drawn. The storeys stack in the same footprint, so
    /// fitting the current one would mean that stepping up onto a roof of ten tiles slammed the
    /// zoom to its limit and lost the map underneath — and the roof is exactly where a player
    /// most wants to see what is around it.
    /// </remarks>
    public void Fit(BattleMap map, Vector2 viewport)
    {
        var hexes = map.Tiles.Select(t => t.Address.Hex).ToList();
        if (hexes.Count == 0) return;

        // In hex-radius units, so the answer does not depend on the zoom it was measured at.
        var unit = new HexLayout(1.0);
        var centres = hexes.Select(unit.Center).ToList();

        var left = centres.Min(c => c.X) - 1;
        var right = centres.Max(c => c.X) + 1;
        var bottom = centres.Min(c => c.Y) - 1;
        var top = centres.Max(c => c.Y) + 1;

        ZoomTo(Mathf.Min(viewport.X / (float)(right - left), viewport.Y / (float)(top - bottom)));
        LookAt(new CoreVec2((left + right) / 2, (bottom + top) / 2) * HexPixels);
    }

    private void Rebuild()
    {
        Scale = new SandboxScale(HexPixels);
        Geometry = new SandboxGeometry(Scale);
    }
}
