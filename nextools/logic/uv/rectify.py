import bmesh
import bpy
from bmesh.types import BMesh
from bpy.types import Object


def align_uv_rectify(obj: Object, bm: BMesh, uv_layer_name: str):
    """
    Rectify logic as a wrapper for Blender's native 'follow_active_quads'.

    Algorithm:
    1. Determines the best active face (Prioritizes Quads over Triangles).
    2. Force-aligns the active face to a perfect square (or right-triangle) in UV space.
    3. Performs the standard unwrap using the aligned face as a reference.
    4. Normalizes the resulting UV coordinates to fit within the 0-1 range.
    """
    mesh_data = obj.data
    uv_layer = bm.loops.layers.uv.get(uv_layer_name)
    if uv_layer is None:
        print(f"Error: UV layer '{uv_layer_name}' not found.")
        return False

    selected_faces = [f for f in bm.faces if f.select]
    if not selected_faces:
        return False

    active_face = bm.faces.active
    if not active_face or not active_face.select:
        active_face = selected_faces[0]
        bm.faces.active = active_face

    if len(active_face.verts) != 4:
        quads = [f for f in selected_faces if len(f.verts) == 4]
        if quads:
            active_face = quads[0]
            bm.faces.active = active_face

    loops = active_face.loops
    num_verts = len(active_face.verts)

    if num_verts == 4:
        # Quad: Square (0,0) -> (1,0) -> (1,1) -> (0,1)
        loops[0][uv_layer].uv = (0, 0)
        loops[1][uv_layer].uv = (1, 0)
        loops[2][uv_layer].uv = (1, 1)
        loops[3][uv_layer].uv = (0, 1)

    elif num_verts == 3:
        # Triangle: Right Triangle (Half-Square)
        loops[0][uv_layer].uv = (0, 0)
        loops[1][uv_layer].uv = (1, 0)
        loops[2][uv_layer].uv = (0, 1)

    else:
        # N-gon: Not supported
        print(f"Error: Active face has {num_verts} vertices. Must be Quad or Triangle.")
        return False

    bmesh.update_edit_mesh(mesh_data)

    if num_verts == 4:
        try:
            bpy.ops.uv.follow_active_quads(mode="EVEN")
        except RuntimeError:
            print("Failed to run Follow Active Quads. Selection might not be contiguous.")
            return False

    returned_bmesh: BMesh = bmesh.from_edit_mesh(mesh_data)
    uv_layer = returned_bmesh.loops.layers.uv.get(uv_layer_name)
    selected_faces = [f for f in returned_bmesh.faces if f.select]

    min_x, max_x = float("inf"), float("-inf")
    min_y, max_y = float("inf"), float("-inf")

    has_verts = False
    for face in selected_faces:
        for loop in face.loops:
            u, v = loop[uv_layer].uv
            if u < min_x:
                min_x = u
            if u > max_x:
                max_x = u
            if v < min_y:
                min_y = v
            if v > max_y:
                max_y = v
            has_verts = True

    if not has_verts:
        return True

    width = max_x - min_x
    height = max_y - min_y
    if width == 0:
        width = 1
    if height == 0:
        height = 1

    for face in selected_faces:
        for loop in face.loops:
            u, v = loop[uv_layer].uv
            loop[uv_layer].uv = ((u - min_x) / width, (v - min_y) / height)

    bmesh.update_edit_mesh(mesh_data)
    return True
