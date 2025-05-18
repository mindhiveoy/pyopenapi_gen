# Analysis for `tests/core/parsing/common/ref_resolution/helpers/`

### `tests/core/parsing/common/ref_resolution/helpers/test_cyclic_properties.py`

- **Overall**: This file provides focused tests for the `mark_cyclic_property_references` helper function. The tests cover scenarios with no properties, direct cycles, indirect cycles, no cycles, and multiple cycles.
- **Test Naming and Structure**:
    - Test methods are clearly named, following the `test_` prefix convention.
    - Each test has a good docstring explaining the `Scenario` and `Expected Outcome`, aligning with G/W/T principles.
    - Uses `unittest.TestCase` as a base.
- **Test Logic**:
    - **`setUp`**: Initializes a `ParsingContext` and a reference name (`self.ref_name`) for use in tests.
    - **`test_mark_cyclic_property_references__no_properties__no_changes`**: Verifies that a schema with no properties remains unchanged.
    - **`test_mark_cyclic_property_references__direct_cycle__marks_property`**: Checks that a direct self-reference in a property leads to that property's schema being marked with `_from_unresolved_ref = True`.
    - **`test_mark_cyclic_property_references__indirect_cycle__marks_property`**: Tests an indirect cycle through an intermediate schema, ensuring the initial property is marked correctly.
    - **`test_mark_cyclic_property_references__no_cycle__no_changes`**: Confirms that a property referencing a non-cyclic schema is not marked.
    - **`test_mark_cyclic_property_references__multiple_cycles__marks_all_cyclic_properties`**: Ensures that in a schema with multiple properties, only those involved in cycles are marked, while others are not.
- **Clarity and Conciseness**:
    - The tests are generally easy to understand.
    - The arrangement of `IRSchema` objects to simulate cycles is clear.
    - Assertions directly check the `_from_unresolved_ref` attribute of the property schemas.
- **Alignment with `coding-conventions`**:
    - Good use of docstrings with Scenario/Expected Outcome.
    - Test names are descriptive.
    - G/W/T structure is evident within each test method.
- **Contradictory Expectations**: None identified. The tests consistently verify the expected behavior of marking cyclic property references.

### `tests/core/parsing/common/ref_resolution/helpers/test_direct_cycle.py`

- **Overall**: This file provides targeted tests for the `handle_direct_cycle` helper. It focuses on how this function retrieves an existing schema from the parsing context and marks it as part of an unresolved reference when a direct cycle is detected.
- **Test Naming and Structure**:
    - Clear, descriptive test method names (e.g., `test_handle_direct_cycle__existing_schema__marks_as_unresolved`).
    - Good use of docstrings with `Scenario` and `Expected Outcome`.
    - Utilizes `unittest.TestCase`.
- **Test Logic**:
    - **`setUp`**: Initializes a `ParsingContext` and pre-populates `context.parsed_schemas` with a basic `existing_schema`. This setup is crucial as `handle_direct_cycle` expects the schema to already be in the context.
    - **`test_handle_direct_cycle__existing_schema__marks_as_unresolved`**: Verifies the primary behavior: the function retrieves the schema and sets its `_from_unresolved_ref` flag to `True`.
    - **`test_handle_direct_cycle__schema_not_in_context__raises_key_error`**: Tests the precondition that the schema must exist in `context.parsed_schemas`. It correctly expects a `KeyError` if the schema is not found.
    - **`test_handle_direct_cycle__preserves_schema_properties`**: Ensures that when a schema involved in a direct cycle is processed, its existing properties, type, and other attributes (like `required`) are preserved, and only the `_from_unresolved_ref` flag is modified.
- **Clarity and Conciseness**:
    - The tests are straightforward and easy to follow.
    - The purpose of each test is clearly articulated in its docstring.
- **Alignment with `coding-conventions`**:
    - Adheres to G/W/T principles.
    - Docstrings are informative.
    - Test names clearly indicate the scenario being tested.
- **Contradictory Expectations**: None identified. The tests confirm that `handle_direct_cycle` correctly flags existing schemas involved in direct cycles while preserving their structure, and appropriately raises errors for missing schemas.

### `tests/core/parsing/common/ref_resolution/helpers/test_existing_schema.py`

- **Overall**: This file provides straightforward tests for the `handle_existing_schema` helper. It ensures that the function correctly retrieves a pre-parsed schema from the `ParsingContext` and handles cases where the schema is not found.
- **Test Naming and Structure**:
    - Test method names are clear and descriptive (e.g., `test_handle_existing_schema__returns_cached_schema`).
    - Docstrings clearly outline the `Scenario` and `Expected Outcome`.
    - Uses `unittest.TestCase`.
- **Test Logic**:
    - **`setUp`**: Initializes a `ParsingContext` and adds an `existing_schema` to `context.parsed_schemas`. This mimics the state where a schema has already been processed and cached.
    - **`test_handle_existing_schema__returns_cached_schema`**: Verifies the core functionality: the function returns the exact schema object that was previously stored in `context.parsed_schemas`.
    - **`test_handle_existing_schema__schema_not_in_context__raises_key_error`**: Tests the behavior when the requested schema name is not in `context.parsed_schemas`. It correctly asserts that a `KeyError` is raised, which is the expected precondition handling.
    - **`test_handle_existing_schema__preserves_schema_properties`**: Ensures that when an existing schema with properties and other attributes (like `required`) is retrieved, all these details are preserved. This confirms the function returns the cached object without modification.
- **Clarity and Conciseness**:
    - The tests are very clear and easy to understand due to their focused nature.
    - Each test targets a single aspect of the function's behavior.
- **Alignment with `coding-conventions`**:
    - Adheres well to G/W/T principles within each test method.
    - Informative docstrings are used.
    - Test names clearly reflect the tested scenarios.
- **Contradictory Expectations**: None identified. The tests confirm that `handle_existing_schema` reliably retrieves cached schemas and correctly handles missing schema lookups.

### `tests/core/parsing/common/ref_resolution/helpers/test_list_response.py`

- **Overall**: This file thoroughly tests the `try_list_response_fallback` helper function. It covers the successful application of the fallback logic, as well as several scenarios where the fallback should not apply or should fail gracefully.
- **Test Naming and Structure**:
    - Test method names are descriptive (e.g., `test_try_list_response_fallback__valid_list_response__returns_array_schema`).
    - Docstrings clearly explain the `Scenario` and `Expected Outcome` for each test.
    - Uses `unittest.TestCase`.
- **Test Logic**:
    - **`setUp`**: Initializes a `ParsingContext`, a sample reference name (`self.ref_name`), its value, max depth, and a `MagicMock` for the `parse_fn`. The `parse_fn` is crucial as the fallback logic relies on being able to parse the inferred base schema.
    - **`test_try_list_response_fallback__valid_list_response__returns_array_schema`**: This is the main success case.
        - It sets up the `context.raw_spec_schemas` with a base schema ("Test").
        - Mocks `parse_fn` to return a successfully parsed `IRSchema` for "Test".
        - Asserts that the `result` is an array `IRSchema` whose items are the parsed base schema.
        - Verifies that the new array schema is registered in `context.parsed_schemas`.
        - Checks that a warning about the fallback is added to `context.collected_warnings`.
    - **`test_try_list_response_fallback__not_list_response__returns_none`**: Tests that if the reference name doesn't end with "ListResponse", the function returns `None` and makes no changes to the context.
    - **`test_try_list_response_fallback__base_schema_not_found__returns_none`**: Tests the case where the reference name ends with "ListResponse", but the inferred base schema name (e.g., "Test" from "TestListResponse") is not found in `context.raw_spec_schemas`. Expects `None` and no context changes.
    - **`test_try_list_response_fallback__base_schema_unresolved__returns_none`**: Tests the scenario where the base schema exists in `raw_spec_schemas`, but the `parse_fn` (when trying to parse this base schema) returns an `IRSchema` marked as unresolved (`_from_unresolved_ref = True`). Expects `None` and no context changes, as the fallback cannot proceed with an unresolved base type.
- **Clarity and Conciseness**:
    - Tests are clear and focused.
    - The use of `MagicMock` for `parse_fn` effectively isolates the logic of `try_list_response_fallback`.
- **Alignment with `coding-conventions`**:
    - Follows G/W/T principles within each test.
    - Docstrings are informative and well-structured.
    - Test names clearly communicate the tested condition and expected result.
- **Contradictory Expectations**: None identified. The tests consistently verify the intended heuristic behavior and its boundary conditions.

### `tests/core/parsing/common/ref_resolution/helpers/test_missing_ref.py`

- **Overall**: This file effectively tests the `handle_missing_ref` function by mocking its internal fallback strategies (`try_list_response_fallback` and `try_stripped_suffix_fallback`). It verifies the behavior when fallbacks succeed or fail, and the preference order if multiple fallbacks could succeed.
- **Test Naming and Structure**:
    - Test method names are descriptive and clearly indicate the scenario (e.g., `test_handle_missing_ref__no_fallbacks_succeed__returns_unresolved_schema`).
    - Docstrings with `Scenario` and `Expected Outcome` are well-used.
    - Uses `unittest.TestCase`.
- **Test Logic**:
    - **`setUp`**: Initializes a `ParsingContext`, a sample reference value and name, max depth, and a `MagicMock` for the `parse_fn` (though `parse_fn` is passed to `handle_missing_ref`, it's the mocked fallbacks that are key in these tests).
    - **Patching**: The core of these tests relies on `unittest.mock.patch` to control the return values of the two fallback functions (`try_list_response_fallback` and `try_stripped_suffix_fallback`) that `handle_missing_ref` calls internally. This allows for isolated testing of `handle_missing_ref`'s orchestration logic.
    - **`test_handle_missing_ref__no_fallbacks_succeed__returns_unresolved_schema`**:
        - Mocks both fallbacks to return `None`.
        - Asserts that `handle_missing_ref` returns a new `IRSchema` instance.
        - This returned schema should have the original `ref_name`, be marked with `_from_unresolved_ref = True`, and be registered in `context.parsed_schemas`. This is the ultimate fallback: creating a placeholder unresolved schema.
    - **`test_handle_missing_ref__list_response_fallback_succeeds__returns_list_schema`**:
        - Mocks `try_list_response_fallback` to return a sample `list_response_schema`.
        - Mocks `try_stripped_suffix_fallback` to return `None`.
        - Asserts that the result from `handle_missing_ref` is the `list_response_schema`.
    - **`test_handle_missing_ref__stripped_suffix_fallback_succeeds__returns_stripped_schema`**:
        - Mocks `try_list_response_fallback` to return `None`.
        - Mocks `try_stripped_suffix_fallback` to return a sample `stripped_schema`.
        - Asserts that the result is the `stripped_schema`.
    - **`test_handle_missing_ref__both_fallbacks_succeed__prefers_list_response`**:
        - Mocks both fallbacks to return distinct successful schemas.
        - Asserts that the result is the `list_response_schema`, confirming that `try_list_response_fallback` is attempted first and its successful result is prioritized.
- **Clarity and Conciseness**:
    - The tests are very clear due to the effective use of patching to isolate the logic under test.
    - Each test focuses on a specific outcome based on the success/failure of the mocked fallbacks.
- **Alignment with `coding-conventions`**:
    - Excellent adherence to G/W/T, with clear Arrange (patching, mock setup), Act (calling `handle_missing_ref`), and Assert sections.
    - Docstrings are informative.
    - Test names are explicit.
- **Contradictory Expectations**: None identified. The tests systematically verify the fallback logic and prioritization within `handle_missing_ref`.

### `tests/core/parsing/common/ref_resolution/helpers/test_new_schema.py`

- **Overall**: This file provides comprehensive tests for the `parse_new_schema` helper. It covers successful parsing, handling of cyclic properties within the new schema, error handling when the underlying `parse_fn` fails, and preservation of metadata.
- **Test Naming and Structure**:
    - Test method names are clear and follow the convention (e.g., `test_parse_new_schema__creates_and_registers_schema`).
    - Docstrings with `Scenario` and `Expected Outcome` are well-defined.
    - Uses `unittest.TestCase`.
- **Test Logic**:
    - **`setUp`**: Initializes a `ParsingContext`, a reference name (`self.ref_name`), sample `node_data` (raw schema definition), max depth, and a `MagicMock` for `parse_fn`. The `parse_fn` is the actual parsing function that `parse_new_schema` will delegate to.
    - **`test_parse_new_schema__creates_and_registers_schema`**:
        - Mocks `parse_fn` to return a fully formed `parsed_schema`.
        - Calls `parse_new_schema`.
        - Asserts that the result is the `parsed_schema` returned by `mock_parse_fn`.
        - Verifies that this schema is registered in `context.parsed_schemas` under `self.ref_name`.
        - Ensures `mock_parse_fn` was called once with the correct arguments.
        - **Key Behavior Tested**: This implicitly tests the two-step process:
            1. `parse_new_schema` first puts a stub (empty `IRSchema` with just the name) into `context.parsed_schemas`.
            2. Then, it calls `parse_fn`.
            3. The result of `parse_fn` (which should be a fully populated `IRSchema`) is then used to update the stub in place (or the stub's attributes are updated from the parsed result). The test checks that the final object in `context.parsed_schemas` *is* the one returned by `parse_fn`.
    - **`test_parse_new_schema__handles_cyclic_properties`**:
        - Mocks `parse_fn` to return a schema (`cyclic_schema`) that has a property referencing itself, and this self-referencing property is already marked as `_from_unresolved_ref = True`.
        - Calls `parse_new_schema`.
        - Asserts that the result is the `cyclic_schema` and that the cyclic property within it is indeed marked. This test relies on the `mark_cyclic_property_references` function (tested separately) being called correctly by `parse_new_schema` after `parse_fn` completes.
    - **`test_parse_new_schema__handles_parse_fn_failure`**:
        - Mocks `parse_fn` to raise a `ValueError`.
        - Asserts that `parse_new_schema` propagates this exception.
        - Crucially, it also asserts that the initial stub schema (with just the name and `None` type) remains in `context.parsed_schemas`. This is important for breaking cycles if the parsing of a dependent schema fails.
    - **`test_parse_new_schema__preserves_schema_metadata`**:
        - Mocks `parse_fn` to return a schema rich with metadata (description, format, etc.).
        - Asserts that the returned schema from `parse_new_schema` contains all this metadata, confirming that the attributes from the `parse_fn`'s result are correctly transferred to the schema object that `parse_new_schema` manages.
- **Clarity and Conciseness**:
    - Tests are well-structured and clear.
    - The mocking of `parse_fn` allows for focused testing of `parse_new_schema`'s orchestration role.
- **Alignment with `coding-conventions`**:
    - Adheres to G/W/T principles.
    - Docstrings are informative.
    - Test names are descriptive.
- **Contradictory Expectations**: None identified. The tests confirm the critical role of `parse_new_schema` in the recursive parsing process, including stubbing for cycle prevention, delegation, and error handling.

### `tests/core/parsing/common/ref_resolution/helpers/test_stripped_suffix.py`

- **Overall**: This file comprehensively tests the `try_stripped_suffix_fallback` helper. It covers successful fallback for known suffixes ("Response", "Request"), cases where no suffix matches, and scenarios where the inferred base schema cannot be found or resolved.
- **Test Naming and Structure**:
    - Method names are descriptive (e.g., `test_try_stripped_suffix_fallback__valid_response_suffix__returns_schema`).
    - Docstrings clearly explain the `Scenario` and `Expected Outcome`.
    - Uses `unittest.TestCase`.
- **Test Logic**:
    - **`setUp`**: Initializes `ParsingContext`, a sample `ref_name` (e.g., "TestResponse"), `ref_value`, `max_depth`, and a `MagicMock` for the `parse_fn`. The `parse_fn` is used by the fallback to attempt parsing the schema after stripping the suffix.
    - **`test_try_stripped_suffix_fallback__valid_response_suffix__returns_schema`**:
        - Sets up `context.raw_spec_schemas` with the base schema ("Test").
        - Mocks `parse_fn` to return a successfully parsed `resolved_schema` (representing "Test").
        - Calls the fallback function.
        - Asserts that the `result` is the `resolved_schema`.
        - Verifies that the *original* reference name ("TestResponse") is used to register the `resolved_schema` in `context.parsed_schemas`. This is important: the fallback resolves to the base schema, but this resolved schema now represents the original suffixed reference.
        - Checks for a warning about the fallback in `context.collected_warnings`.
    - **`test_try_stripped_suffix_fallback__valid_request_suffix__returns_schema`**: Similar to the "Response" suffix test, but for "Request". It confirms the same logic applies.
    - **`test_try_stripped_suffix_fallback__no_matching_suffix__returns_none`**: Tests that if the `ref_name` doesn't end with any of the recognized suffixes, the function returns `None` and makes no changes to the context.
    - **`test_try_stripped_suffix_fallback__base_schema_not_found__returns_none`**: Tests the case where a suffix is matched and stripped, but the resulting base name (e.g., "Test") is not found in `context.raw_spec_schemas`. Expects `None` and no context changes.
    - **`test_try_stripped_suffix_fallback__base_schema_unresolved__returns_none`**: Tests the scenario where the base schema is found in `raw_spec_schemas`, but the `parse_fn` (when attempting to parse this base schema) returns an `IRSchema` marked as unresolved (`_from_unresolved_ref = True`). Expects `None` and no context changes.
- **Clarity and Conciseness**:
    - Tests are clear and well-focused.
    - The mocking of `parse_fn` effectively isolates the fallback logic.
- **Alignment with `coding-conventions`**:
    - Adheres well to G/W/T principles.
    - Docstrings are informative and structured.
    - Test names clearly communicate the tested behavior.
- **Contradictory Expectations**: None identified. The tests consistently verify the suffix-stripping heuristic and its various success and failure conditions. 