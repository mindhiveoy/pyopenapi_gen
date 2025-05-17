"""
Tests for the extract_primary_type_and_nullability helper function.
"""

from typing import Any, List, Optional

import pytest

# Import the function to be tested
from pyopenapi_gen.core.parsing.common.type_parser import extract_primary_type_and_nullability


class TestExtractPrimaryTypeAndNullability:
    @pytest.mark.parametrize(
        "test_id, node_type_field, schema_name, expected_type, expected_nullable, expected_warnings_count, expected_warning_substring",
        [
            (
                "simple_string",
                "string",
                None,
                "string",
                False,
                0,
                None,
            ),
            (
                "simple_null_string",
                "null",
                None,
                None,
                True,
                0,
                None,
            ),
            (
                "list_string_null",
                ["string", "null"],
                None,
                "string",
                True,
                0,
                None,
            ),
            (
                "list_null_integer",
                ["null", "integer"],
                None,
                "integer",
                True,
                0,
                None,
            ),
            (
                "list_single_string",
                ["string"],
                None,
                "string",
                False,
                0,
                None,
            ),
            (
                "list_single_null",
                ["null"],
                None,
                None,
                True,
                1,
                "Only 'null' type in array",
            ),
            (
                "list_multiple_non_null",
                ["string", "integer", "null"],
                "MySchema",
                "string",
                True,
                1,
                "Multiple types in array",
            ),
            (
                "list_multiple_non_null_order",
                ["integer", "string"],
                "AnotherSchema",
                "integer",
                False,
                1,
                "Multiple types in array",
            ),
            (
                "empty_list",
                [],
                None,
                None,
                False,
                1,
                "Empty type array",
            ),
            ("none_input", None, None, None, False, 0, None),
            (
                "dict_input_ignored",
                {"type": "string"},
                None,
                None,
                False,
                1,  # Now expecting a warning with our enhanced validation
                "Invalid type value",
            ),
            # New OpenAPI 3.1 test cases
            (
                "openapi_3_1_single_null_array",
                ["null"],
                "NullOnlySchema",
                None,
                True,
                1,
                "Only 'null' type in array",
            ),
            (
                "openapi_3_1_null_with_primitive",
                ["null", "string"],
                "NullableStringSchema",
                "string",
                True,
                0,
                None,
            ),
            (
                "openapi_3_1_null_last",
                ["string", "null"],
                "StringNullableSchema",
                "string",
                True,
                0,
                None,
            ),
            (
                "openapi_3_1_array_of_types",
                ["string", "integer", "null"],
                "MultiTypeNullableSchema",
                "string",
                True,
                1,
                "Multiple types in array",
            ),
            # Edge cases
            (
                "openapi_3_1_empty_array",
                [],
                "EmptyTypeSchema",
                None,
                False,
                1,
                "Empty type array",
            ),
            (
                "boolean_type_value",
                True,
                "BooleanTypeSchema",
                None,
                False,
                1,
                "Invalid type value",
            ),
            (
                "number_type_value",
                42.0,
                "NumberTypeSchema",
                None,
                False,
                1,
                "Invalid type value",
            ),
        ],
    )
    def test_extract_type_and_nullability(
        self,
        test_id: str,
        node_type_field: Any,
        schema_name: Optional[str],
        expected_type: Optional[str],
        expected_nullable: bool,
        expected_warnings_count: int,
        expected_warning_substring: Optional[str],
    ) -> None:
        """
        Scenario:
            - Test extract_primary_type_and_nullability with various inputs for the 'type' field.
            - Covers simple strings, null, lists with null, lists with multiple types, and invalid inputs.
            - Includes OpenAPI 3.1 specific cases with type arrays.

        Expected Outcome:
            - The function should correctly return the determined schema type (or None),
              a boolean indicating nullability, and a list of warnings.
            - Warnings should be generated for multiple non-null types in a list.
            - The function should correctly handle OpenAPI 3.1 nullable types.
        """
        # Arrange (already done by parametrize)
        # Act
        actual_type: Optional[str]
        actual_nullable: bool
        actual_warnings: List[str]
        actual_type, actual_nullable, actual_warnings = extract_primary_type_and_nullability(
            node_type_field, schema_name
        )

        # Assert
        assert actual_type == expected_type, f"[{test_id}] Type mismatch"
        assert actual_nullable == expected_nullable, f"[{test_id}] Nullability mismatch"
        assert len(actual_warnings) == expected_warnings_count, (
            f"[{test_id}] Warnings count mismatch. Got: {actual_warnings}"
        )
        if expected_warning_substring:
            assert any(expected_warning_substring.lower() in warning.lower() for warning in actual_warnings), (
                f"[{test_id}] Expected warning substring '{expected_warning_substring}' not found in {actual_warnings}"
            )
