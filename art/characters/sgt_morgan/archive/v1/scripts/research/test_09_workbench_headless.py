import bpy, time, sys
scene = bpy.context.scene
scene.render.resolution_x = 512; scene.render.resolution_y = 512
scene.render.image_settings.file_format = 'PNG'
engine = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'BLENDER_WORKBENCH'
scene.render.engine = engine
if engine == 'BLENDER_WORKBENCH':
    sh = scene.display.shading
    sh.light = 'MATCAP'; sh.color_type = 'SINGLE'; sh.show_cavity = True
    sh.cavity_type = 'BOTH'
# a smooth test object with form: subdivided monkey
bpy.ops.mesh.primitive_monkey_add(size=2)
m = bpy.context.object
bpy.ops.object.shade_smooth()
mod = m.modifiers.new('sub', 'SUBSURF'); mod.levels = 3; mod.render_levels = 3
scene.render.filepath = f'/home/user/sgt_morgan/renders/research/t09_{engine.lower()}.png'
t = time.time()
bpy.ops.render.render(write_still=True)
print(f'RENDER_OK {engine} {time.time()-t:.2f}s -> {scene.render.filepath}')
