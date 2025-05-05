# TASKS: Handling Complex Schema References

*Status: Phase 1 Started*

This task list outlines the steps required for the AI agent to verify and potentially enhance the generator's handling of complex OpenAPI schema references.

## Phase 0: Codebase Understanding and Documentation

*Goal: Gain a clear understanding of the `pyopenapi_gen` architecture and document key components.*
*Status: Completed*

*   [x] **Task 0.1: Study Architecture Rule & Existing Code**
    *   Action: Review the `architecture` rule provided in the custom instructions.
    *   Action: Browse the codebase structure, focusing on directories like `pyopenapi_gen/parser`, `pyopenapi_gen/models`, `pyopenapi_gen/visitors`, `pyopenapi_gen/emitters`.
    *   Output: A mental map of the core components and their interactions (Parser -> IR -> Visitors -> Emitters -> CodeWriter).
*   [x] **Task 0.2: Create/Update `docs/architecture.md`**
    *   Action: Create or update the file `docs/architecture.md`.
    *   Content: Summarize the core architectural concepts (IR, Visitors, Emitters, Helpers, Flow) based on Task 0.1 and the provided `architecture` rule.
    *   File to Create/Edit: `docs/architecture.md`
*   [x] **Task 0.3: Identify Key Modules for `$ref` Handling**
    *   Action: Based on the architecture study, pinpoint the specific modules most relevant to parsing OpenAPI schemas (`$ref`), building the Intermediate Representation (IR), and generating model/endpoint code where `$ref` resolution impacts types and logic.
    *   Likely Candidates: `SchemaParser`, `ModelVisitor`, `EndpointVisitor`, `IRSchema`, `IROperation`, `RenderContext`.
    *   Output: A list of key modules/classes critical for this task.
*   [x] **Task 0.4: Create Documentation Stubs for Key Modules**
    *   Action: For each key module/class identified in Task 0.3, create a basic markdown file in the `docs/` directory (e.g., `docs/parser.md`, `docs/model_visitor.md`).
    *   Content: Add a brief description of the module's purpose and its role in the overall generation process, especially concerning schema parsing and type generation.
    *   Files to Create: Placeholder files in `docs/`.

## Phase 1: Prerequisite - Input Specification Validation

*Goal: Ensure the input OpenAPI specification is valid before testing the generator.*
*Status: Completed (Input spec confirmed valid)*

*   [x] ~~**Task 1.1: Identify Unresolved References**~~ *(Skipped: Input spec is valid)*
    *   Action: Analyze the linter errors provided for `input/business_swagger.json`.
    *   Output: A list of all schema names mentioned in `Failed to resolve $ref` errors (e.g., `FoundationModelType`, `Embedding`, `JobUpdate`, etc.).
*   [x] ~~**Task 1.2: Add Missing Schema Definitions**~~ *(Skipped: Input spec is valid)*
    *   Action: Define the necessary schemas identified in Task 1.1 within the `components.schemas` section of `input/business_swagger.json`. *(Requires external knowledge or API documentation for accuracy. If unavailable, proceed with placeholder definitions for testing purposes, clearly marking them as such)*.
    *   File to Edit: `input/business_swagger.json`
*   [x] ~~**Task 1.3: Re-validate Specification**~~ *(Skipped: Input spec is valid)*
    *   Action: Run an OpenAPI linter/validator tool on the modified `input/business_swagger.json`.
    *   Verification: Confirm that no `$ref` resolution errors remain.

## Phase 2: Generator Verification and Enhancement

*Goal: Verify the generator correctly handles the patterns in the now-valid spec and enhance if necessary.*
*Status: In Progress*

*   [x] **Task 2.1: Generate Client Code**
    *   Action: Execute the `pyopenapi_gen` tool using the *fixed* `input/business_swagger.json` as input.
    *   Input: Valid `input/business_swagger.json`.
    *   Output: Generated client code package.
*   [ ] **Task 2.2: Analyze Model Generation Logic**
    *   Action: Review the code responsible for parsing schemas and generating model files.
    *   Files to Review (Likely): `pyopenapi_gen/parser/schema_parser.py`, `pyopenapi_gen/visitors/model_visitor.py`, `pyopenapi_gen/models/intermediate.py` (specifically `IRSchema`).
    *   Verify Handling Of:
        *   [x] Basic `$ref` (e.g., `#/components/schemas/User`).
        *   [x] Nullability (`type: [..., "null"]` -> `Optional[...]` or `Union[..., None]`).
        *   [x] Optionality (`anyOf` with null -> `Optional[...]` or `Union[..., None]`).
        *   [x] Arrays of `$ref` (`items: { $ref: ... }` -> `List[...]`).
        *   [x] General `anyOf`/`allOf` (if used for composition -> `Union` or other structures).
        *   [x] Circular dependencies (`from __future__ import annotations` or string literals).
    *   Status: Completed.
*   [ ] **Task 2.3: Analyze Endpoint/Response Generation Logic**
    *   Action: Review the code responsible for generating endpoint methods and handling responses.
    *   Files to Review (Likely): `pyopenapi_gen/visitors/endpoint_visitor.py`, `pyopenapi_gen/models/intermediate.py` (specifically `IROperation`, `IRResponse`).
    *   Verify Handling Of:
        *   [x] Client transport setup (implicitly addressed by fixing `HttpxTransport` instantiation).
        *   [ ] Response unwrapping (detecting `.data` wrappers like in `TenantResponse`).
        *   [ ] Method return type annotation matches the *unwrapped* type.
        *   [ ] Generated code includes logic to access the unwrapped data (e.g., `response.data`).
        *   [ ] List response unwrapping (e.g., `TenantListResponse` -> `List[Tenant]`).
*   [ ] **Task 2.4: Implement Fixes (If Necessary)**
    *   Action: Based on findings in Tasks 2.2 and 2.3, modify the generator code to correctly handle any identified shortcomings.
    *   Files to Edit: Files identified in Tasks 2.2 and 2.3.
    *   Status: Partially addressed for client transport setup.
*   [x] **Task 2.5: Perform Static Type Checking**
    *   Action: Run `mypy` on the root directory of the *generated client code* (output from Task 2.1 or after Task 2.4).
    *   Verification: Ensure `mypy` reports no errors related to the generated type hints or structures.
    *   Action: If `mypy` errors occur due to generator output, iterate back to Task 2.4 to fix the generator.

## Phase 3: Documentation and Testing (Future Work)

*Goal: Improve robustness and maintainability.*
*Status: In Progress*

*   [ ] **Task 3.1: Add Targeted Tests**
    *   Action: Create new test cases (unit or integration) with minimal OpenAPI specs demonstrating each complex `$ref` pattern handled.
    *   Location: `tests/` directory.
    *   Focus Areas (Current): Loader (`loader.py`) and ModelVisitor (`model_visitor.py`) handling of nullability, composition (`anyOf`, `oneOf`, `allOf`), default factories, and related type hints.
*   [ ] **Task 3.2: Update Documentation**
    *   Action: Update any relevant project documentation (`README.md`, docstrings) to reflect the confirmed capabilities and any limitations regarding schema references. 