# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .. import rust_bridge


# TODO: Using NumPy and minimal-copy would allow for further optimization.
def apply_color_id_to_mesh(obj: bpy.types.Object) -> int:
    """
    Bakes Color IDs onto the specified object's mesh using the Rust backend.

    Args:
        obj: The target object (must be of type MESH).

    Returns:
        int: The number of processed faces.

    Raises:
        ValueError: If the provided object is invalid.
        RuntimeError: If the calculation or data writing fails.
    """
    if not obj or obj.type != "MESH":
        raise ValueError("Target object must be a MESH.")

    mesh = obj.data

    if not mesh.uv_layers.active:
        raise ValueError("Active UV layer is required.")

    num_faces = len(mesh.polygons)
    num_loops = len(mesh.loops)

    poly_loop_starts = [0] * num_faces
    poly_loop_totals = [0] * num_faces
    loop_vert_indices = [0] * num_loops

    mesh.polygons.foreach_get("loop_start", poly_loop_starts)
    mesh.polygons.foreach_get("loop_total", poly_loop_totals)
    mesh.loops.foreach_get("vertex_index", loop_vert_indices)

    uv_coords = [0.0] * (num_loops * 2)
    mesh.uv_layers.active.data.foreach_get("uv", uv_coords)

    try:
        rgba_colors = rust_bridge.bake_color_id_all(
            num_faces, poly_loop_starts, poly_loop_totals, loop_vert_indices, uv_coords
        )
    except Exception as e:
        raise RuntimeError(f"Rust core calculation failed: {e}")

    color_layer_name = "Color_ID"

    if color_layer_name in mesh.color_attributes:
        vcol_layer = mesh.color_attributes[color_layer_name]
    else:
        vcol_layer = mesh.color_attributes.new(
            name=color_layer_name, type="BYTE_COLOR", domain="CORNER"
        )

    try:
        vcol_layer.data.foreach_set("color", rgba_colors)
    except Exception as e:
        raise RuntimeError(f"Failed to apply color data to mesh: {e}")

    mesh.update()

    attr_index = mesh.color_attributes.find(color_layer_name)
    if attr_index != -1:
        mesh.color_attributes.active_color_index = attr_index

    return num_faces
