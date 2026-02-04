import cProfile
import pstats
import io
import functools
import os

ENABLE_PROFILING = os.getenv("NEXTOOLS_PROFILE", "false").lower() == "true"

if ENABLE_PROFILING:

    def profile_execution(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[NexTools] Profiling enabled for: {func.__name__}")
            pr = cProfile.Profile()
            pr.enable()
            try:
                return func(*args, **kwargs)
            finally:
                pr.disable()
                s = io.StringIO()
                ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
                print(f"\n{'=' * 20} Profile Report: {func.__name__} {'=' * 20}")
                ps.print_stats(20)
                print(s.getvalue())
                print(f"{'=' * 60}\n")

        return wrapper

else:

    def profile_execution(func):
        return func
