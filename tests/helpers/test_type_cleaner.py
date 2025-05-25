"""
Tests for the TypeCleaner class, which cleans malformed type expressions.
"""


import pytest
from pyopenapi_gen.helpers.type_cleaner import TypeCleaner


class TestTypeCleaner:
    """Tests for the TypeCleaner class."""

    @pytest.mark.parametrize(
        "test_id, input_type, expected_type",
        [
            # Simple cases
            ("simple_dict", "Dict[str, Any]", "Dict[str, Any]"),
            ("simple_list", "List[str]", "List[str]"),
            ("simple_optional", "Optional[str]", "Optional[str]"),
            # Common error cases from OpenAPI 3.1 nullable handling
            ("dict_with_none", "Dict[str, Any, None]", "Dict[str, Any]"),
            ("list_with_none", "List[JsonValue, None]", "List[JsonValue]"),
            ("optional_with_none", "Optional[Any, None]", "Optional[Any]"),
            # More complex nested types
            ("nested_dict", "Dict[str, Dict[str, Any, None]]", "Dict[str, Dict[str, Any]]"),
            ("nested_list", "List[List[str, None]]", "List[List[str]]"),
            (
                "complex_union",
                "Union[Dict[str, Any, None], List[str, None], Optional[int, None]]",
                "Union[Dict[str, Any], List[str], Optional[int]]",
            ),
            # OpenAPI 3.1 complex nullable cases
            ("openapi_31_list_none", "List[Union[Dict[str, Any], None]]", "List[Union[Dict[str, Any], None]]"),
            ("list_with_multi_params", "List[str, int, bool, None]", "List[str]"),
            ("dict_with_multi_params", "Dict[str, int, bool, None]", "Dict[str, int]"),
            # Edge cases
            ("empty_string", "", ""),
            ("no_brackets", "AnyType", "AnyType"),
            ("incomplete_syntax", "Dict[str,", "Dict[str,"),
            ("empty_union", "Union[]", "Any"),
            ("optional_none", "Optional[None]", "Optional[Any]"),
        ],
    )
    def test_clean_type_parameters(self, test_id: str, input_type: str, expected_type: str) -> None:
        """
        Scenario:
            - Test clean_type_parameters with various invalid type strings
            - Verify it correctly removes extraneous None parameters

        Expected Outcome:
            - Properly cleaned type strings with no invalid None parameters
        """
        result = TypeCleaner.clean_type_parameters(input_type)
        assert result == expected_type, f"[{test_id}] Failed to clean type string correctly"

    def test_clean_nested_types_with_complex_structures(self) -> None:
        """
        Scenario:
            - Test the class with complex nested structures

        Expected Outcome:
            - Should handle deeply nested structures correctly
        """
        # The exact string with no whitespace between parts
        complex_type = "Union[Dict[str, List[Dict[str, Any, None], None]], List[Union[Dict[str, Any, None], str, None]], Optional[Dict[str, Union[str, int, None], None]]]"

        expected = "Union[Dict[str, List[Dict[str, Any]]], List[Union[Dict[str, Any], str, None]], Optional[Dict[str, Union[str, int, None]]]]"

        result = TypeCleaner.clean_type_parameters(complex_type)

        assert result == expected, "Failed to clean complex nested type correctly"

    def test_real_world_cases(self) -> None:
        """
        Scenario:
            - Test the class with real-world problem cases

        Expected Outcome:
            - Should handle problematic real-world type strings correctly
        """
        # Case from EmbeddingFlat.py that caused the linter error
        embedding_flat_type = (
            "Union["
            "Dict[str, Any], "
            "List["
            "Union["
            "Dict[str, Any], List[JsonValue], Optional[Any], bool, float, str, None"
            "], "
            "None"
            "], "
            "Optional[Any], "
            "bool, "
            "float, "
            "str"
            "]"
        )

        expected = (
            "Union["
            "Dict[str, Any], "
            "List["
            "Union["
            "Dict[str, Any], List[JsonValue], Optional[Any], bool, float, str, None"
            "]"
            "], "
            "Optional[Any], "
            "bool, "
            "float, "
            "str"
            "]"
        )

        result = TypeCleaner.clean_type_parameters(embedding_flat_type)

        assert result == expected, "Failed to clean EmbeddingFlat type string correctly"
