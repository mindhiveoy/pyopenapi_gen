---
paths:
  - src/pyopenapi_gen/visit/**/*.py
---

# Visitor Pattern Rules

Pipeline: **Loading → Visiting → Emitting**

## Visitors

- `EndpointVisitor`: Generates endpoint client classes with async methods
- `ModelVisitor`: Generates dataclasses and enums from schemas

## Key Patterns

- Use `RenderContext` for state management
- Handle cycle detection via forward references
- Protocol/Mock support for testing generated clients

## Related Files

- `visit/model_visitor.py` - Dataclass generation
- `visit/endpoint_visitor.py` - Async method generation
