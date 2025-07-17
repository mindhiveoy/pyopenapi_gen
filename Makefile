# Ensure Poetry uses local virtual environment
.PHONY: setup-poetry
setup-poetry:
	@echo "🔧 Configuring Poetry for local virtual environment..."
	poetry config virtualenvs.in-project true

# Check if virtual environment and dependencies are properly installed
.deps-installed: pyproject.toml poetry.lock setup-poetry
	@echo "📦 Installing dependencies with Python 3.12..."
	@if [ ! -d ".venv" ]; then \
		echo "🔨 Creating Python 3.12 virtual environment..."; \
		poetry env use 3.12; \
		poetry install --with dev; \
	else \
		echo "🔄 Updating dependencies..."; \
		poetry install --with dev; \
	fi
	@touch .deps-installed

# Ensure dependencies are installed
deps: .deps-installed

# Development setup (run this once for new environments)
dev-setup: clean setup-poetry
	@echo "🚀 Setting up development environment with Python 3.12..."
	poetry env use 3.12
	poetry install --with dev
	@touch .deps-installed
	@echo "✅ Development environment ready!"

# Clean environment
clean:
	@echo "🧹 Cleaning up..."
	rm -rf .venv/
	rm -rf .deps-installed
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage_reports/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Quality assurance commands
format: deps
	@echo "🎨 Formatting code..."
	poetry run black src/ tests/

format-check: deps
	@echo "🔍 Checking code formatting..."
	poetry run black --check src/ tests/

lint: deps
	@echo "🔍 Linting code..."
	poetry run ruff check src/ tests/

lint-fix: deps
	@echo "🔧 Auto-fixing linting issues..."
	poetry run ruff check --fix src/ tests/

typecheck: deps
	@echo "🔍 Type checking..."
	poetry run mypy src/ --strict

security: deps
	@echo "🔒 Running security checks..."
	poetry run bandit -r src/ -c pyproject.toml -f json -o coverage_reports/bandit.json || poetry run bandit -r src/ -c pyproject.toml

# Combined quality commands
quality-fix: format lint-fix
	@echo "✅ Auto-fixed all possible quality issues"

quality: format-check lint typecheck security
	@echo "✅ All quality checks passed"

# Testing commands
test: deps
	@echo "🧪 Running tests with coverage (requires 85%)..."
	poetry run pytest -n 2 --timeout=120 --cov=src --cov-report=term-missing --cov-report=xml:coverage_reports/coverage.xml --cov-fail-under=85

test-serial: deps
	@echo "🧪 Running tests sequentially..."
	poetry run pytest --timeout=120 --cov=src --cov-report=term-missing --cov-report=xml:coverage_reports/coverage.xml

test-no-cov: deps
	@echo "🧪 Running tests without coverage..."
	poetry run pytest

test-fast: deps
	@echo "🧪 Running tests (fast, stop on first failure)..."
	poetry run pytest -x

test-cov: deps
	@echo "🧪 Running tests with coverage report..."
	poetry run pytest -n 2 --cov=src --cov-report=term-missing --cov-report=html:coverage_reports/html

coverage-html: deps
	@echo "📊 Generating HTML coverage report..."
	poetry run pytest --cov=src --cov-report=html:coverage_reports/html
	@echo "📊 Coverage report: coverage_reports/html/index.html"

# Build commands
build: deps quality test
	@echo "📦 Building package..."
	poetry build

install: deps
	@echo "📦 Installing package in development mode..."
	poetry install

# Publishing commands
publish-check: deps
	@echo "🔍 Checking package for publishing..."
	poetry run twine check dist/*

publish-test: build publish-check
	@echo "🧪 Publishing to TestPyPI..."
	@PYPI_TOKEN=$$(cat "/Users/$(USER)/Library/Application Support/pypoetry/auth.toml" 2>/dev/null | grep 'password' | cut -d'"' -f2); \
	if [ -z "$$PYPI_TOKEN" ]; then \
		echo "❌ PyPI token not found in Poetry auth.toml"; \
		echo "Run: poetry config http-basic.pypi __token__ YOUR_TOKEN"; \
		exit 1; \
	fi; \
	poetry run twine upload --repository testpypi --username __token__ --password "$$PYPI_TOKEN" dist/*

publish: build publish-check
	@echo "🚀 Publishing to PyPI..."
	@PYPI_TOKEN=$$(cat "/Users/$(USER)/Library/Application Support/pypoetry/auth.toml" 2>/dev/null | grep 'password' | cut -d'"' -f2); \
	if [ -z "$$PYPI_TOKEN" ]; then \
		echo "❌ PyPI token not found in Poetry auth.toml"; \
		echo "Run: poetry config http-basic.pypi __token__ YOUR_TOKEN"; \
		exit 1; \
	fi; \
	poetry run twine upload --username __token__ --password "$$PYPI_TOKEN" dist/*

publish-force: deps
	@echo "🚀 Force publishing to PyPI (skips quality checks)..."
	@if [ ! -d "dist" ] || [ -z "$(shell ls -A dist/ 2>/dev/null)" ]; then \
		echo "📦 Building package..."; \
		poetry build; \
	fi
	@PYPI_TOKEN=$$(cat "/Users/$(USER)/Library/Application Support/pypoetry/auth.toml" 2>/dev/null | grep 'password' | cut -d'"' -f2); \
	if [ -z "$$PYPI_TOKEN" ]; then \
		echo "❌ PyPI token not found in Poetry auth.toml"; \
		exit 1; \
	fi; \
	poetry run twine upload --username __token__ --password "$$PYPI_TOKEN" dist/*

# Development commands
dev: dev-setup quality-fix test-fast
	@echo "🚀 Development environment ready and tested!"

# Help
help:
	@echo "Available commands:"
	@echo "  dev-setup     - Set up development environment with Python 3.12"
	@echo "  dev           - Quick development setup with basic tests"
	@echo "  deps          - Install/update dependencies"
	@echo "  clean         - Clean all build artifacts and virtual environment"
	@echo ""
	@echo "Quality commands:"
	@echo "  quality       - Run all quality checks (format, lint, typecheck, security)"
	@echo "  quality-fix   - Auto-fix formatting and linting issues"
	@echo "  format        - Format code with Black"
	@echo "  format-check  - Check code formatting"
	@echo "  lint          - Lint code with Ruff"
	@echo "  lint-fix      - Auto-fix linting issues"
	@echo "  typecheck     - Type check with mypy"
	@echo "  security      - Security scan with Bandit"
	@echo ""
	@echo "Testing commands:"
	@echo "  test          - Run all tests with coverage (parallel, 85% required)"
	@echo "  test-serial   - Run tests sequentially"
	@echo "  test-no-cov   - Run tests without coverage"
	@echo "  test-fast     - Run tests, stop on first failure"
	@echo "  test-cov      - Run tests with HTML coverage report"
	@echo ""
	@echo "Build commands:"
	@echo "  build         - Build package (runs quality + tests)"
	@echo "  install       - Install package in development mode"
	@echo ""
	@echo "Publishing commands:"
	@echo "  publish       - Publish to PyPI (runs build + quality + tests)"
	@echo "  publish-test  - Publish to TestPyPI for testing"
	@echo "  publish-check - Check package before publishing"
	@echo "  publish-force - Force publish (skips quality checks, for CI)"

.DEFAULT_GOAL := help 