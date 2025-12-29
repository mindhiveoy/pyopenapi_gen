---
paths:
  - pyproject.toml
  - poetry.lock
---

# Dependency Management

## Poetry Lock Conflict Resolution

When conflicts occur:

1. Fetch and checkout the branch
2. Merge base branch
3. Accept theirs for pyproject.toml and poetry.lock
4. Run `poetry lock` (CRITICAL)
5. Run `poetry install`
6. Verify: `make quality && make test`
7. Commit with `chore(deps):` prefix

## Escalate If

- Multiple deps conflicting
- Breaking changes detected
- Test failures
- Security issues
