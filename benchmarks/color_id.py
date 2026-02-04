import sys
from pathlib import Path

current_file = Path(__file__).resolve()
project_root = current_file.parent
dev_root = project_root.parent

if str(dev_root) not in sys.path:
    sys.path.append(str(dev_root))

import cProfile
import io
import pstats
import time

import bpy
from nextools.logic import color_id


def setup_test_scene(target_faces=100_000):
    if bpy.context.active_object and bpy.context.active_object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    print(f"\n--- Generating Test Mesh (Target: {target_faces} faces) ---")

    subdiv_level = 0
    base_faces = 576
    while base_faces * (4**subdiv_level) < target_faces:
        subdiv_level += 1

    bpy.ops.mesh.primitive_torus_add(
        major_segments=48, minor_segments=12, major_radius=1, minor_radius=0.25
    )
    obj = bpy.context.active_object

    if subdiv_level > 0:
        mod = obj.modifiers.new(name="Subsurf", type="SUBSURF")
        mod.levels = subdiv_level
        mod.render_levels = subdiv_level
        bpy.ops.object.modifier_apply(modifier="Subsurf")

    current_faces = len(obj.data.polygons)
    print(f"Mesh Generated: {current_faces:,} faces")

    print("Unwrapping UVs (Smart Project)... This may take a moment.")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)
    bpy.ops.object.mode_set(mode="OBJECT")

    return obj


def run_benchmark():
    TARGET_FACES = 1_000_000  # at least

    obj = setup_test_scene(TARGET_FACES)

    print("\n" + "=" * 60)
    print(f"START BENCHMARK: Color ID Baking on {len(obj.data.polygons):,} faces")
    print("=" * 60 + "\n")

    pr = cProfile.Profile()
    pr.enable()

    start_time = time.perf_counter()

    try:
        processed = color_id.apply_color_id_to_mesh(obj)
    except Exception as e:
        print(f"ERROR: {e}")
        return

    end_time = time.perf_counter()

    pr.disable()

    print(f"\n[Result] Processed {processed:,} faces in {end_time - start_time:.4f} sec")

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
    ps.print_stats(20)

    print("-" * 60)
    print(s.getvalue())
    print("-" * 60)


if __name__ == "__main__":
    run_benchmark()
