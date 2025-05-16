# Refactoring Plan for `src/pyopenapi_gen/core/loader.py`

## 0. Context

This refactoring plan is a collaborative effort between a human developer and an AI coding assistant. As such, traditional project management artifacts like detailed time estimations are not a primary focus. The process will be iterative and guided by the AI's ability to rapidly implement and test changes.

The implementation will strictly follow a **Test-Driven Development (TDD)** approach. For each logical component extracted or modified, unit tests will be written *before* or *concurrently with* the implementation to ensure correctness and guide the refactoring process.

## 1. Goal

The primary goal of this refactoring effort is to improve the `src/pyopenapi_gen/core/loader.py` module, particularly the `_parse_schema` function, by separating its complex logic into smaller, more focused, and independently testable components.

This will lead to:

*   **Improved Readability & Maintainability**: Smaller functions with clear responsibilities are easier to understand, modify, and debug.
*   **Enhanced Testability**: Each distinct piece of logic (e.g., `$ref` resolution, `allOf` merging, inline schema promotion) can be unit-tested in isolation, making it easier to verify correctness and pinpoint issues.
*   **Increased Extensibility**: Adding support for new OpenAPI features or custom schema extensions will be simpler and less error-prone.
*   **Better Debugging**: Isolating functionality will help in diagnosing issues like the current problems with inline schema promotion and extraction.

## 2. Desired State

The `_parse_schema` function will be refactored into an orchestrator that calls a series of well-defined helper functions or methods of helper classes. These helpers will handle specific aspects of schema parsing:

*   Initial schema normalization (e.g., Zod-specific structures).
*   `$ref` resolution and fallbacks.
*   `allOf` schema merging.
*   Determination of fundamental IR types and basic attribute parsing.
*   Recursive parsing of properties for object schemas.
*   Dedicated handling for inline schema promotion (for objects) and extraction (for enums).

A `ParsingContext` object may be introduced to manage shared state like global schema dictionaries, visited references, and naming collision trackers.

## 3. Success Criteria

*   The refactored `loader.py` produces the same `IRSchema` output for the existing test suite (including `business_swagger.json`) as the current version.
*   All `mypy` errors related to missing model files (due to failed promotion/extraction) in the `test_business_swagger_generation` integration test are resolved.
*   New unit tests are created for each major refactored component, demonstrating their correct behavior in isolation.
*   The overall complexity of `_parse_schema` is visibly reduced, and the new helper functions are clear and well-documented. 