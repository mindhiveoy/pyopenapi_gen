# Model Visitor (`visit/model_visitor.py`)

This visitor is responsible for translating the `IRSchema` nodes from the Intermediate Representation into concrete Python code, specifically generating dataclasses and enums that represent the API's data structures.

Traverses `IRSchema` nodes from the Intermediate Representation.

Responsibilities:
*   Generates Python dataclasses or Enums based on `IRSchema` details.
*   Determines correct Python type hints, mapping OpenAPI types/formats and IR structure to Python types (`str`, `int`, `bool`, `datetime`, `List`, `Optional`, `Union`, etc.).
*   Handles references to other schemas by using the correct generated class name.
*   Manages potential circular dependencies using forward references (string literals or `from __future__ import annotations`).
*   Uses `CodeWriter` helper to construct the Python code. 