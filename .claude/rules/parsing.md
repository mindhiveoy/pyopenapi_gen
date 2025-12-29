---
paths:
  - src/pyopenapi_gen/core/parsing/**/*.py
  - src/pyopenapi_gen/core/loader/**/*.py
---

# Parsing & Loading Rules

## Architecture

- `core/loader/` - Parse spec, extract operations
- `core/parsing/` - Schema parsing, cycle detection

## Key Components

- `unified_cycle_detection.py` - Handles circular references
- `schema_parser.py` - Core schema → IR conversion

## Environment Variables

- `PYOPENAPI_MAX_DEPTH`: Recursion limit (default: 150)
- `PYOPENAPI_MAX_CYCLES`: Cycle limit (default: 0, unlimited)
