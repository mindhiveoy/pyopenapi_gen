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
source .venv/bin/activate

make quality-fix    # Auto-fix formatting and linting
make quality        # Run all checks (format, lint, typecheck, security)
make test           # All tests, parallel, 85% coverage required
make test-fast      # Stop on first failure
```

## Commit Conventions

**NEVER use `chore(release):`** - reserved for semantic-release bot.

| Prefix                     | Version Bump | Example                                |
| -------------------------- | ------------ | -------------------------------------- |
| `fix:`                     | Patch        | `fix(parser): resolve cycle detection` |
| `feat:`                    | Minor        | `feat(cli): add --dry-run option`      |
| `BREAKING CHANGE:` in body | Major        | Major API changes                      |
| `chore:`, `docs:`, `test:` | None         | No release triggered                   |

## Code Quality

- **Formatting**: Black (120 char line length)
- **Linting**: Ruff for code quality and import sorting
- **Type Safety**: mypy strict mode
- **Compatibility**: Python 3.12+

## CLI Usage

```bash
pyopenapi-gen input/openapi.yaml --project-root . --output-package pyapis.my_client
pyopenapi-gen api.yaml --project-root . --output-package pyapis.client --core-package pyapis.core
```

## References

See `docs/` for detailed guides:

- `architecture.md` - System design and patterns
- `unified_type_resolution.md` - Type resolution system
- `protocol_and_mock_generation.md` - Testing support

Path-specific rules in `.claude/rules/` for testing, visitors, parsing, types, and dependencies.
