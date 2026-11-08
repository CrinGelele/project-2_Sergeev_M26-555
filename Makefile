UV ?= uv

.PHONY: install run lint build
install:
	$(UV) sync --locked
run:
	$(UV) run database
lint:
	$(UV) run ruff check .
build:
	$(UV) build
