# Quality assurance commands
format:
	black src/ tests/

format-check:
	black --check --diff src/ tests/

lint:
	ruff check src/ tests/

lint-fix:
	ruff check --fix src/ tests/

typecheck:
	mypy src/ --strict --no-warn-no-return

security:
	bandit -r src/ -f txt -c .bandit

# Combined quality commands
quality-fix: format lint-fix
	@echo "✅ Auto-fixes completed!"

quality: format-check lint typecheck security
	@echo "✅ All quality checks passed!"

# Testing commands
test:
	pytest

test-cov:
	pytest --cov=src --cov-report=term-missing

test-fast:
	pytest -x

coverage-html:
	pytest --cov=src --cov-report=html
	open htmlcov/index.html

# Development workflow
dev-setup:
	pip install -e '.[dev]'

clean:
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build commands
build: clean
	python -m build

.PHONY: format format-check lint lint-fix typecheck security quality quality-fix test test-cov test-fast coverage-html dev-setup clean build 