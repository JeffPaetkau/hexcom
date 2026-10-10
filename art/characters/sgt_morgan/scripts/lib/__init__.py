"""The shared Blender-side library of the Sgt. Morgan pipeline (spec 18 §4.3).

Modules import only bpy, bmesh, mathutils and numpy, and import bpy inside the functions that need
it, so the plain-Python tools (scripts/tools/bl.py, build_all.py) can use env, log, the file helpers
of cache and interfaces without Blender. Every module has a selftest(), run inside Blender by
`python -I scripts/tools/bl.py selftest --lib`.
"""
