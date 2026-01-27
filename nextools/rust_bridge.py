try:
    from . import nt_rust_core
except ImportError as e:
    print(f"NexTools Critical Error: Rust core module not found. {e}")
    raise e


def solve_heavy_math(a: int, b: int) -> int:
    return nt_rust_core.solve_heavy_math(a, b)
