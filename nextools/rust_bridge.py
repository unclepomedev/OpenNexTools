# SPDX-License-Identifier: GPL-3.0-or-later

try:
    from . import nt_rust_core
except ImportError as e:
    print(f"NexTools Critical Error: Rust core module not found. {e}")
    raise e


def solve_heavy_math(a: int, b: int) -> int:
    return nt_rust_core.solve_heavy_math(a, b)


def bake_color_id_all(
    num_faces: int,
    poly_loop_starts: list[int],
    poly_loop_totals: list[int],
    loop_vert_indices: list[int],
    uv_coords: list[float],
) -> list[float]:
    return nt_rust_core.bake_color_id_all(
        num_faces, poly_loop_starts, poly_loop_totals, loop_vert_indices, uv_coords
    )
