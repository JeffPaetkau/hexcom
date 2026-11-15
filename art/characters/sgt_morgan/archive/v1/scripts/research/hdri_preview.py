"""Tonemapped side-by-side preview of the three HDRIs (Blender headless): load .hdr, scale to 1024x512,
save as PNG via a Compositor-free path: set the image as the world, render a plain emission? Simpler: use
Image.save_render through the scene's view settings (AgX, exposure 0)."""
import bpy, sys, os
argv = sys.argv[sys.argv.index("--") + 1:]
hdri_dir, out_dir = argv[0], argv[1]
os.makedirs(out_dir, exist_ok=True)
scene = bpy.context.scene
scene.view_settings.view_transform = "AgX"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
for f in sorted(os.listdir(hdri_dir)):
    if not f.endswith(".hdr"): continue
    img = bpy.data.images.load(os.path.join(hdri_dir, f))
    w, h = img.size
    img.scale(1024, 512)
    out = os.path.join(out_dir, f.replace(".hdr", "_preview.png"))
    img.save_render(out, scene=scene)   # applies the scene view transform (linear .hdr -> display)
    print(f"PREVIEW {f}: src {w}x{h} float={img.is_float} -> {out}")
