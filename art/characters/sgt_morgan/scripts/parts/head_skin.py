"""The head's skin, round 2 (scripts/parts/head.md §6): the skin's subsurface and tone, the stubble as a shading of
the skin, and the eyes. Functions for base.py to call on Body.Mesh (wiring in head.md §6); scripts/parts/head.py
--dev calls the same on a development copy until then.

- skin: round 1's Cycles skin read orange and over-saturated in the half-lit zones (head.md §5.4): the hue of
  the lit skin was about 20-21 degrees against the reference's 15-17, and the terminator and the cheek hollow went to
  saturation 0.55-0.6 against 0.35-0.4. MPFB's ENHANCED_SSS group carries a red subsurface radius of 5 mm (R 1.0 x
  radius scale 0.1 x Subsurface Scale 0.05 m) at weight 0.2 x sss.png. The fix: a shorter, less red-biased
  radius, a lower weight, and a pinker, less saturated albedo; measured, not chosen (head.md §6).
- stubble: the round-1 shell (Head.Stubble, 0.8 mm off the skin) had a hard edge. Now two point attributes on
  Body.Mesh, `stubble_density` (head.py's density field, smoothed further so it fades over ~15 mm) and
  `stubble_grey` (the chin and soul patch: the analysis's 20-30 % grey hairs), drive a mix in the skin's own
  colour chain: a fine dot noise (0.6 mm, the hair stubs) times the density darkens the skin towards the stubble
  colour, greyed on the chin, and roughens it. No geometry, no edge.
- eyes: round 1's eyes read dark in Cycles; the sclera and iris are lifted towards the analysis's values (§5:
  sclera albedo about #e6e0da in strong occlusion; iris #5b4a3e) and the cornea's roughness kept glossy.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# measured in head.md §6 (hero crop, the evaluation lights): see calibrate notes there
SSS_STRENGTH = 0.06            # MPFB 0.2: the subsurface weight (x sss.png)
SSS_RADIUS_SCALE = 0.05        # MPFB 0.1: red 2.5 mm, green 0.9, blue 0.5 after Subsurface Scale 0.05
SSS_RADIUS_RGB = (1.0, 0.35, 0.2)   # MPFB (1.0, 0.2, 0.1): less red-biased bleed
SKIN_ALBEDO_R2 = "#a5746f"     # round 1 #ab7d71 (hue 13): pinker (hue 6), the 4500 K key adds ~10 degrees
STUBBLE_HEX = "#2c1f18"        # analysis §9 hairs #3b2a22, darker: the mix stands for hair over skin in shadow
STUBBLE_GREY_HEX = "#8c8580"   # the grey hairs on the chin
STUBBLE_COVER = 1.0            # the darkening at density 1 x the dots (mean ~0.75)
SCLERA_R2, IRIS_R2, IRIS_MINOR_R2 = "#e6e0da", "#6a5646", "#3f322a"
OUTER_LAYER = {"OuterLayerTransmission": 0.0, "OuterLayerAlpha": 0.25, "OuterLayerRoughness": 0.02,
               "OuterLayerColor": (0.0, 0.0, 0.0, 1.0)}   # a dark, glossy veil: the wet catchlight without milk
LASHES_R2 = "eyelashes01/eyelashes01.mhclo"   # base.py's eyelashes02 are long, curled cards; the analysis: short, 3-4 mm


def srgb_lin(h):
    c = [int(h.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def skin(mat, old_albedo="#ab7d71", albedo=SKIN_ALBEDO_R2, sss=SSS_STRENGTH, scale=SSS_RADIUS_SCALE, rgb=SSS_RADIUS_RGB):
    """Retune MPFB's ENHANCED_SSS skin (Body.Skin, as base.py's skin_material left it): the subsurface weight
    and radii, and the tone moved from old_albedo to albedo (base.py's tone is albedo / texture mean, so the new
    tone is the old one times the ratio). Returns what was set."""
    grp = next(n for n in mat.node_tree.nodes if n.type == "GROUP")
    gi = grp.inputs
    gi["SSS strength"].default_value = sss
    gi["SSS radius scale"].default_value = scale
    for k, v in zip(("SSS radius R", "SSS radius G", "SSS radius B"), rgb):
        gi[k].default_value = v
    old = np.array(srgb_lin(old_albedo))
    new = np.array(srgb_lin(albedo))
    tone = np.array(gi["colorMixIn"].default_value[:3]) * new / old
    gi["colorMixIn"].default_value = (*[float(v) for v in tone], 1.0)
    mat.diffuse_color = (*new, 1.0)
    return {"sss_strength": sss, "sss_radius_scale": scale, "sss_radius_rgb": list(rgb), "albedo": albedo,
            "tone_linear": [round(float(v), 4) for v in tone]}


def stubble_fields(body, marks):
    """Per-vertex stubble density and grey share on Body.Mesh (all vertices, helpers 0): head.py's density map
    (analysis §9), smoothed so it fades over about 15 mm; the grey share is the chin and soul patch."""
    import common as C
    import head as H
    bd = C.body_data(body)
    E = C.edges_of(bd["F"])
    dens = H.stubble_density(C, bd, marks)
    dens = np.clip(1.3 * C.smooth_field(dens, E, iters=8, lam=0.5), 0, 1)
    dens[bd["groups"]["lips"] > 0.3] = 0.0
    dens[~bd["in_body"]] = 0.0
    V = bd["V"]
    chin = np.array(marks["chin"]["rest_mm"])
    L = V[(bd["groups"]["lips"] > 0.3) & bd["in_body"]]
    lip_bot = L[:, 2].min() if len(L) else chin[2] + 35.0
    zone = (V[:, 2] < lip_bot + 2.0) & (np.abs(V[:, 0]) < 32.0) & (V[:, 2] > chin[2] - 15.0)
    grey = np.clip(C.smooth_field(zone.astype(float), E, iters=10, lam=0.5), 0, 1) * dens
    return dens, grey


MASK_DIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "cache", "head_r2")
MASK_PX = 2048                 # the stubble mask's size on MPFB's 0-1 UV square


def mask_image(body, fields, name="Body.StubbleMask", size=MASK_PX):
    """Per-vertex fields (up to 3, e.g. density and grey) rasterised into a UV image (R, G, B), packed into the
    file: Cycles read the per-vertex attributes as 0 inside MPFB's skin group (tried, round 2), and a texture
    also travels to the glTF export. Faces with a non-zero field only, then blurred and dilated by a few px."""
    import bpy
    me = body.data
    uv = me.uv_layers.active.data
    img_arr = np.zeros((size, size, 3), np.float32)
    cover = np.zeros((size, size), bool)
    F = np.stack([f for f in fields] + [np.zeros_like(fields[0])] * (3 - len(fields)), 1)
    for poly in me.polygons:
        vs = list(poly.vertices)
        if F[vs].max() <= 1e-3:
            continue
        L = list(poly.loop_indices)
        U = np.array([uv[l].uv[:] for l in L]) * (size - 1)
        for j in range(1, len(vs) - 1):
            tri = [0, j, j + 1]
            P = U[tri]
            val = F[[vs[k] for k in tri]]
            x0, y0 = np.floor(P.min(0)).astype(int)
            x1, y1 = np.ceil(P.max(0)).astype(int)
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            q = np.stack([xs.ravel(), ys.ravel()], 1).astype(float)
            T = np.array([P[1] - P[0], P[2] - P[0]]).T
            if abs(np.linalg.det(T)) < 1e-9:
                continue
            ab = np.linalg.solve(T, (q - P[0]).T).T
            w = np.stack([1 - ab.sum(1), ab[:, 0], ab[:, 1]], 1)
            ok = (w >= -0.02).all(1)
            qi = q[ok].astype(int)
            qi = qi[(qi[:, 0] >= 0) & (qi[:, 0] < size) & (qi[:, 1] >= 0) & (qi[:, 1] < size)]
            wv = w[ok][: len(qi)]
            img_arr[qi[:, 1], qi[:, 0]] = wv @ val
            cover[qi[:, 1], qi[:, 0]] = True
    def blur(a, r=2):                        # a separable box blur, twice (Blender's Python has no scipy)
        for _ in range(2):
            for ax in (0, 1):
                a = sum(np.roll(a, k, ax) for k in range(-r, r + 1)) / (2 * r + 1)
        return a

    def dilate(a, n=4):
        for _ in range(n):
            a = np.maximum.reduce([a, np.roll(a, 1, 0), np.roll(a, -1, 0), np.roll(a, 1, 1), np.roll(a, -1, 1)])
        return a
    for c in range(3):
        ch = img_arr[..., c]
        img_arr[..., c] = blur(np.where(cover, ch, dilate(ch)), 1)
    # a generated image regenerates (black) when Blender frees its buffer (a render engine switch did), so the
    # mask goes through a PNG file, loaded back as a file image and packed into the .blend
    tmp = bpy.data.images.new(name + ".tmp", size, size, alpha=False, float_buffer=False)
    rgba = np.concatenate([np.clip(img_arr, 0, 1), np.ones((size, size, 1), np.float32)], 2)
    tmp.pixels.foreach_set(rgba.ravel())
    path = os.path.join(MASK_DIR, name + ".png")
    os.makedirs(MASK_DIR, exist_ok=True)
    tmp.filepath_raw, tmp.file_format = path, "PNG"
    tmp.save()
    bpy.data.images.remove(tmp)
    old = bpy.data.images.get(name)
    if old is not None:
        bpy.data.images.remove(old)
    img = bpy.data.images.load(path)
    img.name = name
    img.colorspace_settings.name = "Non-Color"
    img.pack()
    return img


def _sock(sockets, ident):
    """A socket by identifier (ShaderNodeMix has several sockets named "A", one per data type)."""
    return next(x for x in sockets if x.identifier == ident)


def stubble(body, mat, marks):
    """Write the stubble attributes on Body.Mesh and add the stubble mix to the skin group's colour chain."""
    import bpy
    dens, grey = stubble_fields(body, marks)
    me = body.data
    for nm, val in (("stubble_density", dens), ("stubble_grey", grey)):
        if nm in me.attributes:
            me.attributes.remove(me.attributes[nm])
        at = me.attributes.new(nm, "FLOAT", "POINT")
        at.data.foreach_set("value", val.astype(np.float32))
    grp = next(n for n in mat.node_tree.nodes if n.type == "GROUP")
    nt = grp.node_tree
    if "Stubble.Mix" in nt.nodes:
        mask_image(body, [dens, grey])
        return {"vertices": int((dens > 0.05).sum())}
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    src = bsdf.inputs["Base Color"].links[0].from_socket
    N = nt.nodes.new
    img = mask_image(body, [dens, grey])
    uvn = N("ShaderNodeUVMap")
    tex = N("ShaderNodeTexImage")
    tex.image, tex.name, tex.interpolation = img, "Stubble.Mask", "Linear"
    nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
    sep = N("ShaderNodeSeparateColor")
    nt.links.new(tex.outputs["Color"], sep.inputs["Color"])

    class _Out:                              # the mask's channels where the attributes were
        def __init__(self, sock):
            self.outputs = {"Fac": sock}
    att, attg = _Out(sep.outputs["Red"]), _Out(sep.outputs["Green"])
    tc = N("ShaderNodeTexCoord")
    noise = N("ShaderNodeTexNoise")
    noise.name = "Stubble.Dots"
    noise.inputs["Scale"].default_value = 1100.0          # object space metres: ~0.9 mm clumps of stubs
    noise.inputs["Detail"].default_value = 1.0
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = N("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.38, (0.45, 0.45, 0.45, 1)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.62, (1, 1, 1, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    fac = N("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    nt.links.new(att.outputs["Fac"], fac.inputs[0])
    nt.links.new(ramp.outputs["Color"], fac.inputs[1])
    fac2 = N("ShaderNodeMath")
    fac2.operation, fac2.use_clamp = "MULTIPLY", True
    fac2.inputs[1].default_value = STUBBLE_COVER
    nt.links.new(fac.outputs[0], fac2.inputs[0])
    hair = N("ShaderNodeMix")
    hair.data_type, hair.name = "RGBA", "Stubble.HairColour"
    _sock(hair.inputs, "A_Color").default_value = (*srgb_lin(STUBBLE_HEX), 1.0)
    _sock(hair.inputs, "B_Color").default_value = (*srgb_lin(STUBBLE_GREY_HEX), 1.0)
    gm = N("ShaderNodeMath")
    gm.operation, gm.use_clamp = "MULTIPLY", True
    gm.inputs[1].default_value = 0.45                     # up to ~45 % grey on the chin
    nt.links.new(attg.outputs["Fac"], gm.inputs[0])
    nt.links.new(gm.outputs[0], _sock(hair.inputs, "Factor_Float"))
    mix = N("ShaderNodeMix")
    mix.data_type, mix.name = "RGBA", "Stubble.Mix"
    nt.links.new(fac2.outputs[0], _sock(mix.inputs, "Factor_Float"))
    nt.links.new(src, _sock(mix.inputs, "A_Color"))
    nt.links.new(_sock(hair.outputs, "Result_Color"), _sock(mix.inputs, "B_Color"))
    nt.links.new(_sock(mix.outputs, "Result_Color"), bsdf.inputs["Base Color"])
    # a little rougher where the stubble is
    rsock = bsdf.inputs["Roughness"]
    if rsock.is_linked:
        rsrc = rsock.links[0].from_socket
        radd = N("ShaderNodeMath")
        radd.operation, radd.use_clamp = "MULTIPLY_ADD", True
        radd.inputs[1].default_value = 0.25
        nt.links.new(att.outputs["Fac"], radd.inputs[0])
        nt.links.new(rsrc, radd.inputs[2])
        nt.links.new(radd.outputs[0], rsock)
    return {"vertices": int((dens > 0.05).sum()), "cover": STUBBLE_COVER, "colour": STUBBLE_HEX, "grey": STUBBLE_GREY_HEX}


def eyes(ob):
    """Lift the eyes (EnhancedEye group inputs: sclera, iris colours); viewport colours too."""
    out = {}
    if ob is None:
        return out
    for m in ob.data.materials:
        grp = next((n for n in m.node_tree.nodes if n.type == "GROUP"), None)
        if grp is None:
            continue
        for k, v in (("IrisMajorColor", IRIS_R2), ("IrisMinorColor", IRIS_MINOR_R2), ("EyeWhiteColor", SCLERA_R2)):
            if k in grp.inputs:
                grp.inputs[k].default_value = (*srgb_lin(v), 1.0)
                out[k] = v
        # the black eyes: EnhancedEye's outer layer (the cornea shell over the whole eye) is a refracting glass
        # (transmission 1, IOR 1.33), so no direct light reaches the sclera and iris under it in Cycles (no
        # caustics) and the eye renders as a dark hole. The shell becomes a mostly transparent clear coat: light
        # passes, the wet catchlight stays.
        for k, v in OUTER_LAYER.items():
            if k in grp.inputs:
                grp.inputs[k].default_value = v
                out[k] = v
        m.diffuse_color = (*srgb_lin(IRIS_R2 if m.name.endswith("Iris") else SCLERA_R2), 1.0)
    return out


def apply(body, marks, eyes_ob=None):
    """All of it, for base.py (after landmarks(), which `marks` are): the skin retune, the stubble attributes and
    shading, the eyes. Returns a record for base.json."""
    mat = body.data.materials[0]
    rec = {"skin": skin(mat), "stubble": stubble(body, mat, marks)}
    if eyes_ob is not None:
        rec["eyes"] = eyes(eyes_ob)
    return rec
