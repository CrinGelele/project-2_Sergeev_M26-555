UV ?= uv
export UV_CACHE_DIR := $(CURDIR)/.local/uv-cache
export UV_PYTHON_INSTALL_DIR := $(CURDIR)/.local/python
export PYTHONDONTWRITEBYTECODE := 1

.PHONY: install run lint test build check demo
install:
	$(UV) sync --locked
run:
	$(UV) run --locked database
lint:
	$(UV) run --locked ruff check .
test:
	$(UV) run --locked python tests/check_scenarios.py
build:
	$(UV) build
check: build
	$(UV) tool run twine check dist/*
demo:
	$(UV) run --locked python demo/record.py
