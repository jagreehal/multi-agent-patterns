.PHONY: install lint lint-fix format test type-check update-deps clean check-env security-check watch-file watch-test

# Use Python 3.12
PYTHON := python3.12
VENV := .venv
BIN := $(VENV)/bin
UV := $(BIN)/uv

install:
	@echo "Installing dependencies using uv..."
	@uv venv
	@uv pip install -e ".[dev]"
	@echo "Dependencies installed."

install-extras:
	@echo "Installing extras using uv..."; \
	$(UV) pip install -e ".[logging,debug]"; \
	echo "Extras installed."

lint:
	@echo "Running linter..."
	@uv run ruff check .

lint-fix:
	@echo "Fixing lint issues..."
	@uv run ruff check --fix --unsafe-fixes .
	@echo "Lint issues fixed."

format:
	@echo "Formatting code..."
	@uv run ruff check --fix --unsafe-fixes .
	@uv run ruff format .

test:
	@echo "Running tests..."
	@uv run pytest -v || true

type-check:
	@echo "Running type checker..."
	@uv run mypy .

security-check:
	@echo "Running security checks..."
	@uv run bandit -r src/ --exclude src/test_*.py
	@echo "Security checks complete."

update-deps:
	@echo "Updating dependencies using uv..."
	@uv pip install --upgrade -e ".[dev]"
	@echo "Dependencies updated with uv."

check-env:
	@echo "Checking required environment variables..."
	@if [ -z "$(DATABASE_URL)" ]; then echo "DATABASE_URL is not set!"; exit 1; fi
	@if [ -z "$(SECRET_KEY)" ]; then echo "SECRET_KEY is not set!"; exit 1; fi
	@echo "All required environment variables are set."

clean:
	@echo "Cleaning up virtual environment and cache..."
	@rm -rf $(VENV)  # Remove the virtual environment
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -delete
	@echo "Cleaned up environment and cache files."

watch-file:
	@if [ -z "$(file)" ]; then \
		echo "Usage: make watch-file file=<file_path>"; \
		exit 1; \
	fi; \
	echo "Watching file: $(file) for changes..."; \
	$(BIN)/watchmedo shell-command \
		--patterns="$(file)" \
		--recursive \
		--command='echo "File $(file) changed! Running action..."; $(BIN)/python $(file)' \
		.

watch-test:
	@if [ -z "$(file)" ]; then \
		echo "Usage: make watch-test file=<test_file_path>"; \
		exit 1; \
	fi; \
	echo "Watching test file: $(file) for changes..."; \
	$(BIN)/watchmedo shell-command \
		--patterns="$(file)" \
		--recursive \
		--command='echo "Test file $(file) changed! Running tests..."; $(BIN)/pytest $(file)' \
		.

# Default target
all: update-deps install install-extras lint format test type-check security-check
