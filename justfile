default: build

build:
    uv run maturin develop --release

sync:
    uv sync --all-extras --dev

fmt:
    uv run ruff format nextools tests

fix-rs:
    cargo clippy --fix --allow-dirty --allow-staged --all-targets -- -D warnings

fmt-rs:
    just fix-rs
    cargo fmt --all

fmt-all: fmt fmt-rs

lint:
    uv run ruff check nextools
    uv run ruff format --check nextools
    cargo clippy --all-targets -- -D warnings
    cargo fmt --all -- --check

ty:
    uv run ty check

export BLENDER_PROBE_PROJECT_ROOT := justfile_directory()
test:
    cargo test --release
    uv run maturin develop --release
    blup run -- --background --factory-startup --python-exit-code 1 --python tests/run_tests.py -- tests

test-rs:
    cargo test
