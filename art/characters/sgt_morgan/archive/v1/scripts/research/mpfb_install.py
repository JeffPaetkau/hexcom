"""Install MPFB2 extension headless into Blender 4.5 and save user prefs.
Usage: blender -b --python mpfb_install.py -- /path/to/add-on-mpfb-vX.zip
"""
import bpy, sys, os, time

t0 = time.time()
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
zip_path = argv[0] if argv else "/home/user/sgt_morgan/assets/mpfb/add-on-mpfb-v2.0.17.zip"

print("Blender", bpy.app.version_string)
print("user extensions dir:", bpy.utils.user_resource('EXTENSIONS'))
print("user scripts dir:", bpy.utils.user_resource('SCRIPTS'))
print("config dir:", bpy.utils.user_resource('CONFIG'))

# Make sure the online-access/extension repo system is sane for headless use
prefs = bpy.context.preferences
try:
    prefs.system.use_online_access = True
except Exception as e:
    print("online access flag:", e)

repos = prefs.extensions.repos
print("repos:", [(r.name, r.module, r.use_remote_url, r.directory) for r in repos])

# install from file into user_default repo
res = bpy.ops.extensions.package_install_files(
    filepath=zip_path,
    repo="user_default",
    enable_on_install=True,
    overwrite=True,
)
print("package_install_files ->", res)

# ensure the module is enabled
mod_name = "bl_ext.user_default.mpfb"
try:
    bpy.ops.preferences.addon_enable(module=mod_name)
    print("addon_enable ok")
except Exception as e:
    print("addon_enable failed:", e)

print("enabled addons with mpfb:", [a.module for a in prefs.addons if "mpfb" in a.module])
bpy.ops.wm.save_userpref()
print("saved userpref. elapsed %.1fs" % (time.time() - t0))
