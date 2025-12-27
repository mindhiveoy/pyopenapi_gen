# PyOpenAPI Generator

Async-first, strongly-typed Python client generator from OpenAPI specifications. Generated clients are fully independent with no runtime dependency on this generator.

## Critical Rules

- **Virtual environment**: Always `source .venv/bin/activate` before any commands
- **Temporal files**: Use `_process/` folder for AI agent files (plans, reports, drafts)
- **No file creation**: Edit existing files; never create new ones unless essential
- **No documentation creation**: Never create .md files unless explicitly requested
- **Zero tolerance**: 0 errors, 0 warnings on all quality gates

## Essential Commands

```bash
# ALWAYS activate first
source .venv/bin/activate

# Quality workflow (before committing)
make quality-fix          # Auto-fix formatting and linting
make quality              # Run all checks (format, lint, typecheck, security)

# Testing
make test                 # All tests, parallel, 85% coverage required (matches CI)
make test-fast            # Stop on first failure
pytest -xvs               # Verbose, stop on first failure
pytest tests/path.py::test_name  # Single test

# Individual quality checks
make format-check         # Black formatting
make lint                 # Ruff linting
make typecheck            # mypy strict
make security             # Bandit security scan
```

## Testing Standards

- **Framework**: pytest only (no unittest.TestCase)
- **Naming**: `test_<unit>__<condition>__<expected>()`
- **Structure**: Arrange/Act/Assert with comments
- **Coverage**: ≥85% branch coverage enforced
- **Assertions**: Plain `assert` statements
- **Exceptions**: `pytest.raises` context manager
- **Parameterisation**: `pytest.mark.parametrize` for variations
- **Mocking**: `unittest.mock` for external dependencies

## Commit Conventions

**NEVER use `chore(release):`** - reserved for semantic-release bot.

| Prefix | Version Bump | Example |
|--------|--------------|---------|
| `fix:` | Patch (1.0.0 → 1.0.1) | `fix(parser): resolve cycle detection` |
| `feat:` | Minor (1.0.0 → 1.1.0) | `feat(cli): add --dry-run option` |
| `BREAKING CHANGE:` in body | Major (1.0.0 → 2.0.0) | Major API changes |
| `chore:`, `docs:`, `test:` | None | No release triggered |

**Reserved prefixes** (automated tools only):
- `chore(release):` - semantic-release bot
- `chore(deps):` - dependabot

## Code Quality Standards

- **Formatting**: Black (120 char line length)
- **Linting**: Ruff for code quality and import sorting
- **Type Safety**: mypy strict mode
- **Compatibility**: Python 3.12+
- **Client Independence**: Generated clients are self-contained with no runtime dependency

## CLI Usage

```bash
# Basic generation
pyopenapi-gen input/openapi.yaml --project-root . --output-package pyapis.my_client

# With shared core (multi-client)
pyopenapi-gen api.yaml --project-root . --output-package pyapis.client --core-package pyapis.core

# Options
--force           # Overwrite without diff check
--no-postprocess  # Skip Black/mypy (faster iteration)
```

**Project root verification**: Generated code appears at `{project-root}/{output-package-as-path}`

## Architecture Overview

Three-stage pipeline: **Loading → Visiting → Emitting**

| Stage | Location | Purpose |
|-------|----------|---------|
| Loading | `core/loader/`, `core/parsing/` | Parse spec, detect cycles, resolve references, build IR |
| Type Resolution | `types/` | `UnifiedTypeService` for schema → Python type conversion |
| Visiting | `visit/` | Model/Endpoint/Client/Exception visitors generate code |
| Emitting | `emitters/` | Write files with proper package structure |

**Key components**:
- `types/services/` - `UnifiedTypeService` orchestrates all type resolution
- `core/parsing/unified_cycle_detection.py` - Handles circular references
- `visit/model_visitor.py` - Generates dataclasses and enums
- `visit/endpoint_visitor.py` - Creates async methods with Protocol/Mock support

## Environment Variables

- `PYOPENAPI_MAX_DEPTH`: Schema parsing recursion limit (default: 150)
- `PYOPENAPI_MAX_CYCLES`: Cycle detection limit (default: 0, unlimited)

## Poetry Lock Conflict Resolution (Dependabot PRs)

When `pyproject.toml` or `poetry.lock` has conflicts:

```bash
git fetch origin <branch-name> && git checkout <branch-name>
git fetch origin <base-branch> && git merge origin/<base-branch>
git checkout --theirs pyproject.toml  # Accept base, update specific dep
git checkout --theirs poetry.lock
poetry lock                            # CRITICAL: Regenerate lock
poetry install                         # MUST succeed
make quality && make test              # All gates must pass
git add pyproject.toml poetry.lock
git commit -m "chore(deps): resolve merge conflict - update to <package> <version>"
```

**Escalate to human review if**: Multiple deps, breaking changes, test failures, security issues, or conflicts beyond lock files.

## GitHub App Capabilities

Claude GitHub App has `contents:write`, `pull-requests:write`, `issues:write` permissions for:
- Automated PR review and fixes (formatting, linting, type errors, security)
- Quality assurance via `make quality` and `make test`
- Poetry lock conflict resolution
- Branch and release management

**Triggers**: Dependabot PRs, `[claude-review]` tag, `@claude` comments.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors after generation | Check project-root path matches package structure |
| Type checking failures | `make typecheck` then fix or regenerate |
| Large spec performance | Use `--no-postprocess` or increase `PYOPENAPI_MAX_DEPTH` |
| Circular reference errors | Check `--verbose` output; forward references auto-generated |
| Semantic release not triggering | Verify commit doesn't start with `chore(release):` |

## Extended Documentation

See `docs/` for detailed guides:
- `architecture.md` - System design and patterns
- `unified_type_resolution.md` - Type resolution system
- `protocol_and_mock_generation.md` - Testing support
- `ir_models.md` - Intermediate representation
- `model_visitor.md`, `endpoint_visitor.md` - Code generation
