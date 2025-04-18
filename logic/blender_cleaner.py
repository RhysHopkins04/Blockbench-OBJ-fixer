import os
import sys
import subprocess
import tempfile
import webbrowser
import tkinter as tk
from tkinter import messagebox

TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "temp")
BLENDER_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "blender-3.6.22-windows-x64", "blender.exe")

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def prompt_blender_missing():
    root = tk.Tk()
    root.withdraw()
    if messagebox.askyesno("Missing Blender", "Blender was not found in the expected location.\nWould you like to download Blender 3.6.22 now?"):
        webbrowser.open("https://www.blender.org/download/lts/3.6/")
        messagebox.showinfo(
            "Download Instructions",
            "Please download the portable .zip and extract it to:\n\n  tools/blender-3.6.22-windows-x64\n\n"
            "⚠️ Make sure the folder contains blender.exe directly.\n"
            "If you see another folder inside with the same name, move its contents up one level."
        )
    else:
        messagebox.showwarning("Blender Required", "This tool requires Blender 3.6.22 to continue.")
    sys.exit(1)

def run_blender_cleaner(input_obj, enable_hbm=False):
    if not os.path.exists(BLENDER_PATH):
        prompt_blender_missing()

    blender_script = f"""
import bpy
import sys
import addon_utils
import math
from mathutils import Vector

addon_utils.enable("io_scene_obj")

argv = sys.argv
argv = argv[argv.index("--") + 1:]
input_path = argv[0]
output_path = argv[1]
hbm_mode = argv[2].lower() == "true" if len(argv) > 2 else False

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=input_path)

mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
if not mesh_objects:
    print("No mesh objects found.")
    sys.exit(1)

if hbm_mode:
    print("Applying HBM scaling and orientation to each object...")

    for obj in mesh_objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.transform.rotate(value=math.radians(180), orient_axis='X')
        bpy.ops.transform.rotate(value=math.radians(180), orient_axis='Z')
        bpy.ops.transform.resize(value=(16.0, 16.0, 16.0))
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    all_verts = [obj.matrix_world @ v.co for obj in mesh_objects for v in obj.data.vertices]
    min_x = min(v.x for v in all_verts)
    max_x = max(v.x for v in all_verts)
    min_y = min(v.y for v in all_verts)
    max_y = max(v.y for v in all_verts)
    min_z = min(v.z for v in all_verts)

    offset_x = -(min_x + max_x) / 2
    offset_y = -(min_y + max_y) / 2 + 0.4
    offset_z = -min_z - 9.1

    for obj in mesh_objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.transform.translate(value=(offset_x, offset_y, offset_z))
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        bpy.ops.object.mode_set(mode='OBJECT')

    # Ensure clean selection for export
    bpy.ops.object.select_all(action='DESELECT')
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]

bpy.ops.export_scene.obj(filepath=output_path, use_selection=True, use_materials=False)
"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", dir=TEMP_DIR, mode='w', encoding='utf-8') as temp_script:
        temp_script.write(blender_script)
        temp_script_path = temp_script.name

    output_obj = os.path.join(TEMP_DIR, os.path.basename(input_obj).replace(".obj", "_cleaned.obj"))

    try:
        subprocess.run([
            BLENDER_PATH, "--background", "--python", temp_script_path, "--",
            os.path.abspath(input_obj),
            os.path.abspath(output_obj),
            str(enable_hbm)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        os.remove(temp_script_path)

    if not os.path.exists(output_obj):
        raise RuntimeError("Blender did not produce the cleaned .obj file as expected.")

    return output_obj
