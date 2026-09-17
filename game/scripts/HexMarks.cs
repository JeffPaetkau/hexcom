using System.Collections.Generic;
using Godot;
using Hexcom.Rules;

namespace Hexcom.Game;

/// <summary>
/// The marks on hexes, painted by the ground's own shader: one texel per hex holding a mark's
/// colour and strength, and the shader draws a disc of the cursor's size about the hex centre
/// wherever the texel says so.
/// </summary>
/// <remarks>
/// <para>
/// Painted rather than built, because a mark built as a mesh has to lie on the drawn ground
/// and never quite does: on a bank the ground rises through it in slivers, and lifting it
/// higher only moves the slivers to steeper creases. The shader already finds the hex under
/// every pixel for the grid, so the ground can mark itself, exactly, at any slope and zoom,
/// and a fade is a texel changing rather than a mesh regrouped.
/// </para>
/// <para>
/// The texture is re-centred on a hex each time the marks are replaced, so it need only be
/// as wide as a reach can be. Colours are stored as the palette gives them, in sRGB, and
/// the shader blends them in that space so a strength reads as the fraction it says.
/// </para>
/// </remarks>
public sealed class HexMarks
{
    /// <summary>Texels a side: a mark can lie this many hexes either way from the centre, less half.</summary>
    private const int Size = 128;

    private readonly Image _image = Image.CreateEmpty(Size, Size, false, Image.Format.Rgba8);
    private readonly ImageTexture _texture;
    private readonly ShaderMaterial _surface;
    private readonly Dictionary<Hex, (Color Colour, float Total, float Left)> _fading = new();
    private Hex _origin;
    private bool _dirty;

    public HexMarks(ShaderMaterial surface, float radius)
    {
        _surface = surface;
        _texture = ImageTexture.CreateFromImage(_image);
        _surface.SetShaderParameter("marks", _texture);
        _surface.SetShaderParameter("mark_radius", radius);
        Recentre(new Hex(0, 0));
    }

    /// <summary>Replace every mark: these hexes in these colours, with the texture centred on a hex.</summary>
    public void Set(Hex around, IEnumerable<(Hex Hex, Color Colour)> marks)
    {
        _fading.Clear();
        _image.Fill(Colors.Transparent);
        Recentre(around);

        foreach (var (hex, colour) in marks) Paint(hex, colour);

        _dirty = true;
        Upload();
    }

    /// <summary>Start fading these hexes out, to nothing over some seconds.</summary>
    public void Fade(IEnumerable<Hex> hexes, float seconds)
    {
        foreach (var hex in hexes)
        {
            if (Texel(hex) is not { } t) continue;
            _fading[hex] = (_image.GetPixel(t.X, t.Y), seconds, seconds);
        }
    }

    /// <summary>Advance the fades by a frame.</summary>
    public void Tick(float delta)
    {
        if (_fading.Count == 0) return;

        foreach (var hex in new List<Hex>(_fading.Keys))
        {
            var (colour, total, left) = _fading[hex];
            left -= delta;

            if (left <= 0)
            {
                Paint(hex, Colors.Transparent);
                _fading.Remove(hex);
            }
            else
            {
                Paint(hex, new Color(colour, colour.A * left / total));
                _fading[hex] = (colour, total, left);
            }
        }

        Upload();
    }

    private void Recentre(Hex around)
    {
        _origin = new Hex(around.Q - Size / 2, around.R - Size / 2);
        _surface.SetShaderParameter("marks_origin", new Vector2I(_origin.Q, _origin.R));
    }

    private Vector2I? Texel(Hex hex)
    {
        var x = hex.Q - _origin.Q;
        var y = hex.R - _origin.R;
        return x >= 0 && y >= 0 && x < Size && y < Size ? new Vector2I(x, y) : null;
    }

    private void Paint(Hex hex, Color colour)
    {
        if (Texel(hex) is not { } t) return;
        _image.SetPixel(t.X, t.Y, colour);
        _dirty = true;
    }

    private void Upload()
    {
        if (!_dirty) return;
        _texture.Update(_image);
        _dirty = false;
    }
}
