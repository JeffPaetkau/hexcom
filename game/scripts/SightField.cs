using System;
using Godot;
using Hexcom.Rules;

namespace Hexcom.Game;

/// <summary>
/// The active unit's view as a texture for the fog pass: one texel per hex holding how clearly
/// the unit makes it out and the height of its ground, recentred on the unit each time the
/// view is replaced, and crossfaded from the last view so the fog re-forms rather than jumps
/// when the turn passes or the unit moves.
/// </summary>
/// <remarks>
/// The same shape as <see cref="HexMarks"/>, and for the same reason: the shader already finds
/// the hex under every pixel, so a per-hex number is a texel. Two floats a texel because the
/// fog thins with height above the ground and the pass has only the pixel's own height to go on;
/// the ground under a piece is the ground of its hex.
/// </remarks>
public sealed class SightField
{
    /// <summary>Texels a side: a view can reach this many hexes either way from the unit, less half. The sight's reach is under a hundred metres.</summary>
    private const int Size = 256;

    /// <summary>How long the fog takes to re-form from one view to the next.</summary>
    public const float FadeSeconds = 0.5f;

    /// <summary>The ground height of a hex past the sight's reach: higher than anything, so no pixel is above it.</summary>
    private const float UnknownGround = 1e6f;

    private readonly ShaderMaterial _fog;
    private readonly ImageTexture _texture;
    private float[] _from = new float[Size * Size];
    private float[] _to = new float[Size * Size];
    private float[] _now = new float[Size * Size];
    private float[] _ground = new float[Size * Size];
    private readonly float[] _packed = new float[Size * Size * 2];
    private readonly byte[] _bytes = new byte[Size * Size * 2 * sizeof(float)];
    private Hex _origin;
    private float _fade = 1f;

    public SightField(ShaderMaterial fog)
    {
        _fog = fog;
        _texture = ImageTexture.CreateFromImage(Image.CreateEmpty(Size, Size, false, Image.Format.Rgf));
        _fog.SetShaderParameter("field", _texture);
        _fog.SetShaderParameter("field_origin", new Vector2I(_origin.Q, _origin.R));
    }

    /// <summary>Replace the view: crossfade to it from what is shown now, or show it at once.</summary>
    /// <param name="groundHeight">The height of a hex's ground, asked for every hex within the reach.</param>
    /// <param name="reachHexes">How far the sight reaches in hexes; ground is known that far and no further.</param>
    public void Show(View view, Func<Hex, double> groundHeight, int reachHexes, bool fade)
    {
        var origin = new Hex(view.From.Q - Size / 2, view.From.R - Size / 2);

        // What is on screen now, re-indexed to the new origin, is where the fade starts from.
        var from = new float[Size * Size];
        var shift = (Q: origin.Q - _origin.Q, R: origin.R - _origin.R);
        for (var y = 0; y < Size; y++)
        for (var x = 0; x < Size; x++)
        {
            var ox = x + shift.Q;
            var oy = y + shift.R;
            if (ox >= 0 && ox < Size && oy >= 0 && oy < Size) from[y * Size + x] = _now[oy * Size + ox];
        }

        // Ground heights are known as far as the sight reaches, unseen hexes included, since
        // the fog thins with height above the ground and a hill behind the unit must not stand
        // out of it for want of a height. Past the reach the ground is unknown, and is marked
        // so high that nothing is ever above it: the fog there sits at the cap whatever the
        // height. (A tall thing standing out of fog past the reach is the map layer's to draw,
        // when there is one.)
        var to = new float[Size * Size];
        var ground = new float[Size * Size];
        Array.Fill(ground, UnknownGround);
        for (var dq = -reachHexes; dq <= reachHexes; dq++)
        for (var dr = Math.Max(-reachHexes, -dq - reachHexes); dr <= Math.Min(reachHexes, -dq + reachHexes); dr++)
        {
            var hex = new Hex(view.From.Q + dq, view.From.R + dr);
            var x = hex.Q - origin.Q;
            var y = hex.R - origin.R;
            if (x < 0 || x >= Size || y < 0 || y >= Size) continue;
            to[y * Size + x] = (float)view.ClarityAt(hex);
            ground[y * Size + x] = (float)groundHeight(hex);
        }

        _origin = origin;
        _from = from;
        _to = to;
        _ground = ground;
        _fade = fade ? 0f : 1f;
        _now = fade ? from : to;
        _fog.SetShaderParameter("field_origin", new Vector2I(origin.Q, origin.R));
        Upload();
    }

    /// <summary>Advance the crossfade by a frame's time.</summary>
    public void Tick(float delta)
    {
        if (_fade >= 1f) return;

        _fade = Mathf.Min(1f, _fade + delta / FadeSeconds);
        var t = Mathf.SmoothStep(0f, 1f, _fade);
        for (var i = 0; i < _now.Length; i++) _now[i] = Mathf.Lerp(_from[i], _to[i], t);
        Upload();
    }

    private void Upload()
    {
        for (var i = 0; i < _now.Length; i++)
        {
            _packed[2 * i] = _now[i];
            _packed[2 * i + 1] = _ground[i];
        }

        Buffer.BlockCopy(_packed, 0, _bytes, 0, _bytes.Length);
        _texture.Update(Image.CreateFromData(Size, Size, false, Image.Format.Rgf, _bytes));
    }
}
