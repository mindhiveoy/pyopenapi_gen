---
paths:
  - tests/**/*.py
---

# Testing Rules

- **Framework**: pytest only (no unittest.TestCase)
- **Naming**: `test_<unit>__<condition>__<expected>()`
- **Structure**: Arrange/Act/Assert with comments
- **Coverage**: ≥85% branch coverage enforced
- **Assertions**: Plain `assert` statements
- **Exceptions**: `pytest.raises` context manager
- **Parameterization**: `pytest.mark.parametrize` for variations
- **Mocking**: `unittest.mock` for external dependencies only
