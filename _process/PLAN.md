# Refactoring Plan for `src/pyopenapi_gen/core/loader.py`

## 0. Context

This refactoring plan is a collaborative effort between a human developer and an AI coding assistant. As such, traditional project management artifacts like detailed time estimations are not a primary focus. The process will be iterative and guided by the AI's ability to rapidly implement and test changes.

The implementation will strictly follow a **Test-Driven Development (TDD)** approach. For each logical component extracted or modified, unit tests will be written *before* or *concurrently with* the implementation to ensure correctness and guide the refactoring process. We will actively monitor **code coverage**, aiming for high branch coverage to ensure all logical paths are tested.

## 1. Goal

The primary goal of this refactoring effort is to improve the `src/pyopenapi_gen/core/loader.py` module, particularly the `_parse_schema` function, by separating its complex logic into smaller, more focused, and independently testable components. This includes organizing these components into meaningful modules with a clear folder structure to enhance the overall architecture of the parsing domain.

The generator must be able to correctly interpret standard **OpenAPI 3.0 and 3.1 specification documents**, at least for all commonly used features. All development will adhere to the project's **`coding-conventions.mdc`**.

This will lead to:

*   **Improved Readability & Maintainability**: Smaller functions with clear responsibilities, organized into logical modules, are easier to understand, modify, and debug.
*   **Enhanced Testability**: Each distinct piece of logic (e.g., `$ref` resolution, `allOf` merging, inline schema promotion) can be unit-tested in isolation, making it easier to verify correctness and pinpoint issues.
*   **Increased Extensibility**: Adding support for new OpenAPI features or custom schema extensions will be simpler and less error-prone within a well-structured modular design.
*   **Better Debugging**: Isolating functionality within specific modules will help in diagnosing issues like the current problems with inline schema promotion and extraction.

## 2. Desired State

The `_parse_schema` function will be refactored into an orchestrator that calls a series of well-defined helper functions or methods of helper classes. These helpers will handle specific aspects of schema parsing and will be organized into distinct modules within a clear folder structure for the parsing domain. For example:

*   A module for `$ref` resolution and fallbacks.
*   A module for `allOf` schema merging.
*   A module for basic type determination and attribute parsing.
*   A module for orchestrating property parsing for object schemas.
*   Dedicated modules for inline schema promotion (for objects) and extraction (for enums).

A `ParsingContext` object may be introduced to manage shared state like global schema dictionaries, visited references, and naming collision trackers.

## 3. Success Criteria

*   The refactored `loader.py` produces the same `IRSchema` output for the existing test suite (including `business_swagger.json`) as the current version.
*   All `mypy` errors related to missing model files (due to failed promotion/extraction) in the `test_business_swagger_generation` integration test are resolved.
*   New unit tests are created for each major refactored component, demonstrating their correct behavior in isolation and achieving high branch coverage.
*   The overall complexity of `_parse_schema` is visibly reduced, and the new helper functions are clear and well-documented, adhering to `coding-conventions.mdc`.
*   The generated client maintains its key characteristics:
    *   Provides good, clear documentation.
    *   Enforces strict types for all inputs and outputs.
    *   Raises exceptions for all API error states (non-2xx/3xx responses).
    *   Returns normally only for successful (2xx) responses. 