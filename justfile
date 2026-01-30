default: build

build:
    maturin develop --release

fmt:
    ruff format nextools tests
