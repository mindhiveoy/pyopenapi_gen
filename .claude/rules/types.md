---
paths:
  - src/pyopenapi_gen/types/**/*.py
---

# Type Resolution Rules

## Architecture

`UnifiedTypeService` orchestrates all type resolution.

## Key Files

- `types/services/type_service.py` - Main orchestrator
- `types/resolvers/` - Schema, reference, response resolvers

## Patterns

- Schema → Python type conversion
- Handle Optional, List, Dict, Union types
- Forward reference generation for cycles
