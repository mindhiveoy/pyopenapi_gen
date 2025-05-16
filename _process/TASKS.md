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

**Goal:** Break down the monolithic `_parse_schema` function into smaller, testable, and more maintainable helper functions, each responsible for a specific part of schema parsing. This will improve clarity, reduce complexity, and make future extensions (like advanced `allOf` or `oneOf` handling) easier.

**Approach:**
*   AI-Assisted: Use AI for boilerplate, test generation, and refactoring suggestions.
*   TDD-Lite: Write tests for each extracted block *before* or *during* extraction.
*   Incremental: Extract one logical block at a time, ensure tests pass, then commit/move to the next.
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
    *   (Moved to `src/pyopenapi_gen/core/parsing/ref_resolver.py`)
*   **[DONE] Task B3: Integrate and Verify `_resolve_schema_ref` helper.**

**C. `allOf` Merging Block**
*   **[DONE] Task C1: Define Test Cases & Write Unit Tests for `_process_all_of` helper.**
    *   (Helper in `src/pyopenapi_gen/core/parsing/all_of_merger.py`)
*   **[DONE] Task C2: Extract Logic to `_process_all_of` helper.**
*   **[DONE] Task C3: Integrate and Verify `_process_all_of` helper.**

**D. Zod-specific Structure Handling (`_def`, `~standard`)** (Initial thoughts: may be complex, might need its own sub-parser)
*   **Task D1: Define Test Cases & Write Unit Tests for Zod structure parsing.**
*   **Task D2: Extract Logic to a dedicated Zod parsing helper.**
*   **Task D3: Integrate and Verify Zod parsing helper.**

**E. Array Type Parsing (including `items`)**
*   **Task E1: Define Test Cases & Write Unit Tests for array/items parsing.**
*   **Task E2: Extract Logic to `_parse_array_items` helper.**
*   **Task E3: Integrate and Verify `_parse_array_items` helper.**

**F. Object Property Parsing (iterating `properties` and recursive calls)**
*   **Task F1: Define Test Cases & Write Unit Tests for object property iteration and parsing.**
*   **Task F2: Extract Logic for iterating/parsing properties to a helper.** (This might primarily involve orchestrating calls to `_parse_schema` for each property and then to inline promotion helpers).
*   **Task F3: Integrate and Verify object property parsing helper.**

**G. Inline Enum Extraction** (Depends on object property parsing helper - F)
*   **[DONE] Task G1: Define Test Cases & Write Unit Tests for inline enum extraction helper(s).**
*   **[DONE] Task G2: Refine/Extract inline enum extraction to helper function(s) in `inline_enum_extractor.py`.**
    *   Helper 1: `_extract_enum_from_property_node` (for enums within property definitions)
    *   Helper 2: `_process_standalone_inline_enum` (for enums that are direct schema definitions)
*   **[DONE] Task G3: Integrate and Verify inline enum extraction helper(s).**

**[NEXT] H. Inline Object (non-enum) Promotion** (Depends on object property parsing helper - F)
*   **[DONE] Task H1: Define Test Cases & Write Unit Tests for inline object promotion helper.**
    *   (Helper: `_attempt_promote_inline_object` in `src/pyopenapi_gen/core/parsing/inline_object_promoter.py`)
*   **[DONE] Task H2: Extract/Refine inline object promotion to `_attempt_promote_inline_object` helper.**
*   **Task H3: Integrate and Verify inline object promotion helper.** (Current focus due to `mypy` errors. Parameter `$ref` KeyError is fixed. `test_codegen_analytics_query_params` is fixed.)

**I. Primitive Type Parsing (string, number, integer, boolean)**
*   **Task I1: Define Test Cases & Write Unit Tests for basic primitive types.**
*   **Task I2: Ensure `extract_primary_type_and_nullability` (already in `type_parser.py`) and `_parse_schema` correctly handle these.** (May not need new extraction if current logic is sufficient).
*   **Task I3: Verify primitive type handling.**

**J. Composition (`anyOf`, `oneOf`)**
*   **Task J1: Define Test Cases & Write Unit Tests for `anyOf` and `oneOf`.**
*   **Task J2: Extract/Refine logic for `anyOf` / `oneOf` to dedicated helpers.**
*   **Task J3: Integrate and Verify `anyOf` / `oneOf` helpers.**

**K. Default and Example Value Handling**
*   **Task K1: Define Test Cases & Write Unit Tests for `default` and `example` keywords.**
*   **Task K2: Ensure these are correctly captured in `IRSchema` by `_parse_schema`.**
*   **Task K3: Verify handling.**

---
**Post-Refactoring Goal for `_parse_schema`:**
The `_parse_schema` function in `schema_parser.py` should become a higher-level orchestrator. It will:
1.  Handle initial checks (e.g., if node is None, already visited).
2.  Call `_resolve_schema_ref` if it's a `$ref`.
3.  Call `extract_primary_type_and_nullability`.
4.  Delegate to specialized helpers for `allOf`, `anyOf`, `oneOf`, arrays, objects (which in turn handle properties and their inline promotions), and standalone enums.
5.  Populate the `IRSchema` object with results from these helpers.
6.  Add the fully parsed schema to `context.parsed_schemas`.

## Phase 3: Finalization and Cleanup

7.  **Review and Refine `_parse_schema` Orchestrator**:
    *   Ensure the main `_parse_schema` function is clean, readable, and effectively orchestrates calls to the helpers.
8.  **Comprehensive Review of `loader.py`**:
    *   Check for clarity, consistency, and adherence to coding conventions.
    *   Ensure all new functions/methods have clear docstrings.
9.  **Final Integration Test Run**:
    *   Run all tests, including the full integration test suite, to confirm all `mypy` errors are resolved and functionality is preserved.
10. **Documentation Update**:
    *   Update any relevant internal documentation or comments if the refactoring changes how the loader is used or understood.

This plan is iterative. Tasks within Phase 2 can be reordered or parallelized where appropriate. The key is to make small, testable changes. 