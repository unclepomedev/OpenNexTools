default: build

build:
    maturin develop --release

fmt:
    ruff format nextools tests

fix-rs:
    cargo clippy --fix --allow-dirty --allow-staged --all-targets -- -D warnings

fmt-rs:
    just fix-rs
    cargo fmt --all

fmt-all: fmt fmt-rs
