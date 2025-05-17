# Tasks for Refactoring `src/pyopenapi_gen/core/loader.py`

This document outlines the specific tasks required to refactor the `_parse_schema` function and its related logic within `loader.py`.

## Phase 1: Analysis and Initial Setup

1.  **[DONE] Create Planning Documents**:
    *   Create `_process/PLAN.md` outlining the refactoring goals.
    *   Create `_process/TASKS.md` (this file) detailing the steps.
2.  **[IN PROGRESS] Detailed Analysis of `_parse_schema`**:
    *   Thoroughly review the current `_parse_schema` function.
    *   Identify and map out the distinct logical blocks (e.g., Zod handling, `$ref` resolution, `allOf` processing, type determination, property iteration, inline object promotion, inline enum extraction).
    *   **[NEXT]** Document the inputs, outputs, and side effects of each identified block (starting with `$ref` resolution).
3.  **[DONE] Define `ParsingContext` Structure (Initial Draft)**:
    *   Specified the potential structure of a `ParsingContext` class.
    *   Identified initial state to manage.

## Phase 1.5: Integrate `ParsingContext`

4.  **[DONE] Implement `ParsingContext` Dataclass**.
5.  **[DONE] Refactor `_parse_schema` and Callers to Use `ParsingContext`**.
6.  **[DONE] Verify `ParsingContext` Integration** (Unit tests pass, integration test has existing failures).

## Phase 2: Refactor `_parse_schema` in `loader.py` (Now `schema_parser.py`)

**Goal:** Break down the monolithic `_parse_schema` function into smaller, testable, and more maintainable helper functions, each responsible for a specific part of schema parsing. This process explicitly includes organizing these extracted components into distinct, logically-cohesive modules within a clear folder structure for the parsing domain (e.g., `core/parsing/keywords/`, `core/parsing/transformers/`, `core/parsing/common/`). This will improve clarity, reduce complexity, enhance separation of concerns, and make future extensions (like advanced `allOf` or `oneOf` handling) easier to implement and manage.

**Approach:**
*   AI-Assisted: Use AI for boilerplate, test generation, and refactoring suggestions.
*   TDD-Lite: Write tests for each extracted block *before* or *during* extraction. Code coverage will be monitored, aiming for high branch coverage on all new and refactored logic.
*   Incremental: Extract one logical block at a time, ensure tests pass, then commit/move to the next.
*   Modularity: As logical blocks are extracted, they will be placed into appropriate new or existing modules within a well-defined subdirectory structure under `src/pyopenapi_gen/core/parsing/` to ensure good separation of concerns and a clean architectural layout.
*   Validation: All new and refactored code must adhere to `coding-conventions.mdc`. The parsing logic must correctly interpret commonly used features of OpenAPI 3.0 and 3.1 specifications.
*   No strict time estimates per block, focus on correctness.

---

## Refactoring Blocks & Tasks:

**A. Parsing Context Introduction**
*   **[DONE] Task A1: Define `ParsingContext` dataclass.**
    *   (Moved to `src/pyopenapi_gen/core/parsing/context.py`)
*   **[DONE] Task A2: Refactor `_parse_schema` and callers to use `ParsingContext`.**
*   **[DONE] Task A3: Update Unit Tests to use `ParsingContext`.**

**B. `$ref` Resolution Block**
*   **[DONE] Task B1: Define Test Cases & Write Unit Tests for `_resolve_schema_ref` helper.**
*   **[DONE] Task B2: Extract Logic to `_resolve_schema_ref` helper.**
    *   (Moved to `src/pyopenapi_gen/core/parsing/common/ref_resolution/resolve_schema_ref.py`)
*   **[DONE] Task B3: Integrate and Verify `_resolve_schema_ref` helper.**

**C. `allOf` Merging Block**
*   **[DONE] Task C1: Define Test Cases & Write Unit Tests for `_process_all_of` helper.**
    *   (Moved to `src/pyopenapi_gen/core/parsing/keywords/all_of_parser.py`)
*   **[DONE] Task C2: Extract Logic to `_process_all_of` helper.**
*   **[DONE] Task C3: Integrate and Verify `_process_all_of` helper.**

**D. Composition Keywords (`anyOf`, `oneOf`)**
*   **[DONE] Task D1: Define Test Cases & Write Unit Tests for `anyOf` and `oneOf` parsing.**
*   **[DONE] Task D2: Extract Logic to dedicated helpers.**
    *   (Moved to `src/pyopenapi_gen/core/parsing/keywords/any_of_parser.py` and `one_of_parser.py`)
*   **[DONE] Task D3: Integrate and Verify composition keyword helpers.**

**E. Array Type Parsing (including `items`)**
*   **[DONE] Task E1: Define Test Cases & Write Unit Tests for array/items parsing.**
*   **[DONE] Task E2: Extract Logic to `_parse_array_items` helper.**
    *   (Moved to `src/pyopenapi_gen/core/parsing/keywords/array_items_parser.py`)
*   **[DONE] Task E3: Integrate and Verify `_parse_array_items` helper.**

**F. Object Property Parsing (iterating `properties` and recursive calls)**
*   **[DONE] Task F1: Define Test Cases & Write Unit Tests for object property iteration and parsing.**
*   **[DONE] Task F2: Extract Logic for iterating/parsing properties to a helper.**
    *   (Moved to `src/pyopenapi_gen/core/parsing/keywords/properties_parser.py`)
*   **[DONE] Task F3: Integrate and Verify object property parsing helper.**

**G. Inline Enum Extraction**
*   **[DONE] Task G1: Define Test Cases & Write Unit Tests for inline enum extraction helper(s).**
*   **[DONE] Task G2: Refine/Extract inline enum extraction to helper function(s).**
    *   (Moved to `src/pyopenapi_gen/core/parsing/transformers/inline_enum_extractor.py`)
*   **[DONE] Task G3: Integrate and Verify inline enum extraction helper(s).**

**H. Inline Object (non-enum) Promotion**
*   **[DONE] Task H1: Define Test Cases & Write Unit Tests for inline object promotion helper.**
*   **[DONE] Task H2: Extract/Refine inline object promotion to helper.**
    *   (Moved to `src/pyopenapi_gen/core/parsing/transformers/inline_object_promoter.py`)
*   **[DONE] Task H3: Integrate and Verify inline object promotion helper.**

**I. Primitive Type Parsing (string, number, integer, boolean)**
*   **[DONE] Task I1: Define Test Cases & Write Unit Tests for basic primitive types.**
*   **[DONE] Task I2: Ensure `extract_primary_type_and_nullability` correctly handles these.**
    *   (Moved to `src/pyopenapi_gen/core/parsing/common/type_parser.py`)
*   **[DONE] Task I3: Verify primitive type handling.**

**J. Schema Finalization**
*   **[DONE] Task J1: Define Test Cases & Write Unit Tests for schema finalization.**
*   **[DONE] Task J2: Extract finalization logic to dedicated module.**
    *   (Moved to `src/pyopenapi_gen/core/parsing/schema_finalizer.py`)
*   **[DONE] Task J3: Integrate and Verify schema finalization.**

## Phase 3: Finalization and Cleanup

1.  **[DONE] Review and Refine `_parse_schema` Orchestrator**:
    *   Extracted helper functions for better organization
    *   Improved error handling and type safety
    *   Enhanced logging and documentation
    *   Fixed all linter errors

2.  **[IN PROGRESS] Comprehensive Review of Parsing Modules**:
    *   **[DONE] Review of Core Modules**:
        *   `schema_parser.py`: Improved organization and error handling
        *   `schema_finalizer.py`: Verified proper schema finalization
        *   `context.py`: Confirmed proper state management
    *   **[DONE] Review of Keyword Parsers**:
        *   `all_of_parser.py`: Verified proper composition handling
        *   `array_items_parser.py`: Confirmed array type handling
        *   `properties_parser.py`: Checked property iteration
        *   `any_of_parser.py`: Verified union type handling
        *   `one_of_parser.py`: Confirmed choice type handling
    *   **[DONE] Review of Transformers**:
        *   `inline_object_promoter.py`: Verified object promotion logic
        *   `inline_enum_extractor.py`: Confirmed enum extraction
    *   **[DONE] Review of Common Utilities**:
        *   `type_parser.py`: Verified type determination
        *   `ref_resolution/`: Confirmed reference handling
    *   **[NEXT] Standardize Error Handling**:
        *   Add consistent error messages across all modules
        *   Ensure all error cases are properly logged
        *   Add appropriate assertions for pre/post conditions
    *   **[NEXT] Enhance Documentation**:
        *   Add module-level docstrings explaining purpose and usage
        *   Ensure all functions have complete Contracts sections
        *   Add examples in docstrings where helpful
    *   **[NEXT] Improve Type Safety**:
        *   Add missing type hints
        *   Fix any remaining mypy errors
        *   Add runtime type checks where needed

3.  **[NEXT] Final Integration Test Run**:
    *   Run all tests, including the full integration test suite
    *   Verify all `mypy` errors are resolved
    *   Confirm functionality is preserved across all test cases
    *   Check for any performance regressions

4.  **[NEXT] Documentation Update**:
    *   Update internal documentation to reflect the new module structure
    *   Add or update docstrings for all new modules and functions
    *   Document the parsing pipeline and how different components interact
    *   Add examples of common use cases

5.  **[NEXT] Verify Generated Client Characteristics**:
    *   Confirm the generated client still provides good documentation
    *   Ensure strict types for inputs and outputs are maintained
    *   Verify that API error states (non-2xx responses) are raised as exceptions
    *   Confirm only successful responses are returned normally by the client

This plan is iterative. Tasks within Phase 2 have been completed, and we are now moving into Phase 3 for finalization and cleanup. The focus is on ensuring the refactored code is robust, well-documented, and maintains all required functionality. 