# PLAN: Handling Complex Schema References in OpenAPI Generator

## 1. Goal

Enhance the Python OpenAPI client generator (`pyopenapi_gen`) to reliably and correctly handle complex schema referencing patterns as observed in specifications like `input/business_swagger.json`. This includes:

*   [x] **Resolving standard `#/components/schemas/...` references.** (Verified)
*   [x] **Generating correct Python types for arrays of referenced schemas (`List[Type]`).** (Verified)
*   [x] **Handling nullability defined via `type: [..., "null"]` or `anyOf: [{...}, {"type": "null"}]` by generating `Optional[Type]` or `Union[Type, None]`.** (Verified via Mypy)
*   [x] **Correctly interpreting `anyOf` / `allOf` for schema composition (generating `Union`).** (Verified via Mypy, `allOf` treated as `Union`)
*   [ ] **Implementing response unwrapping in endpoint methods** (e.g., returning the inner `data` type like `Tenant` from a `TenantResponse` schema). *(Next major task)*
*   [x] **Managing potential circular dependencies between schemas using forward references or string literals.** (Handled via `from __future__ import annotations`)
*   [x] **Ensuring the generator works correctly with *valid* OpenAPI specifications employing these patterns.** (Verified via Mypy)

## 2. Verification Strategy

Successful completion will be verified by:

1.  **Prerequisite Met**: Confirming that the input OpenAPI specification (e.g., `input/business_swagger.json`) is *valid* and all `$ref` targets are defined. *(This fix is external to the generator itself)*.
2.  **Generator Execution**: Successfully running `pyopenapi_gen` against the *valid* OpenAPI specification. *(Verified)*
3.  **Code Inspection (Models)**: Manually reviewing the generated files in the `models/` directory to ensure:
    *   Correct type hints are used (`Optional`, `List`, `Union`). *(Verified)*
    *   Referenced types are correctly named. *(Verified)*
    *   Forward references (e.g., `'TypeName'`) or `from __future__ import annotations` are used appropriately for circular dependencies. *(Verified)*
4.  **Code Inspection (Endpoints)**: Manually reviewing generated files in the `endpoints/` directory to confirm that client methods:
    *   Declare return types corresponding to the *unwrapped* data schema (e.g., `-> Tenant` instead of `-> TenantResponse`). *(Pending verification/implementation)*
    *   Include logic to extract the relevant data from the response structure (e.g., accessing the `.data` attribute). *(Pending verification/implementation)*
5.  **Static Analysis**: Running `mypy` on the entire generated client package to ensure it passes type checking without errors caused by the generator's output. *(Verified)*
6.  **Error Handling**: Verifying that if the generator encounters *new* unsupported patterns in a *valid* specification, it produces clear and informative error messages rather than crashing or generating incorrect code. *(Partially addressed)*

## 3. Areas for Further Development (Post-Goal)

*   **Advanced `$ref` Support**: Investigate and potentially implement support for more complex `$ref` paths, such as external file references (`$ref: 'external_schemas.yaml#/components/schemas/SharedType'`).
*   **Dedicated Testing**: Create specific unit and integration tests covering various `$ref` scenarios (`anyOf`, `allOf`, arrays, circular dependencies, nullability patterns, response unwrapping) using minimal, targeted OpenAPI specs.
*   **Input Validation Reporting**: Enhance the generator's initial parsing phase to detect and report issues in the input OpenAPI spec more clearly (e.g., specifically listing all unresolved `$ref`s found).
*   **Alternative Model Generation**: Explore options for generating Pydantic models instead of or in addition to standard dataclasses, which could offer more advanced validation capabilities if required by users.
*   **Configuration**: Add configuration options to control aspects like response unwrapping behavior if needed. 