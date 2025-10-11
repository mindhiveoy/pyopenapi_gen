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
            ("simple_dict", "dict[str, Any]", "dict[str, Any]"),
            ("simple_list", "List[str]", "List[str]"),
            ("simple_optional", "str | None", "str | None"),
            # Common error cases from OpenAPI 3.1 nullable handling
            ("dict_with_none", "dict[str, Any, None]", "dict[str, Any]"),
            ("list_with_none", "List[JsonValue, None]", "List[JsonValue]"),
            ("optional_with_none", "Optional[Any, None]", "Any | None"),
            # More complex nested types
            ("nested_dict", "dict[str, dict[str, Any, None]]", "dict[str, dict[str, Any]]"),
            ("nested_list", "List[List[str, None]]", "List[List[str]]"),
            (
                "complex_union",
                "Union[dict[str, Any, None], List[str, None], Optional[int, None]]",
                "Union[dict[str, Any], List[str], int | None]",
            ),
            # OpenAPI 3.1 complex nullable cases
            ("openapi_31_list_none", "List[Union[dict[str, Any], None]]", "List[Union[dict[str, Any], None]]"),
            ("list_with_multi_params", "List[str, int, bool, None]", "List[str]"),
            ("dict_with_multi_params", "dict[str, int, bool, None]", "dict[str, int]"),
            # Edge cases
            ("empty_string", "", ""),
            ("no_brackets", "AnyType", "AnyType"),
            ("incomplete_syntax", "dict[str,", "dict[str,"),
            ("empty_union", "Union[]", "Any"),
            ("optional_none", "Optional[None]", "Any | None"),
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
        complex_type = (
            "Union[dict[str, List[dict[str, Any, None], None]], "
            "List[Union[dict[str, Any, None], str, None]], "
            "Optional[dict[str, Union[str, int, None], None]]]"
        )

        expected = (
            "Union[dict[str, List[dict[str, Any]]], "
            "List[Union[dict[str, Any], str, None]], "
            "dict[str, Union[str, int, None]] | None]"
        )

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
            "dict[str, Any], "
            "List["
            "Union["
            "dict[str, Any], List[JsonValue], Any | None, bool, float, str, None"
            "], "
            "None"
            "], "
            "Any | None, "
            "bool, "
            "float, "
            "str"
            "]"
        )

        expected = (
            "Union["
            "dict[str, Any], "
            "List["
            "Union["
            "dict[str, Any], List[JsonValue], Any | None, bool, float, str, None"
            "]"
            "], "
            "Any | None, "
            "bool, "
            "float, "
            "str"
            "]"
        )

        result = TypeCleaner.clean_type_parameters(embedding_flat_type)

        assert result == expected, "Failed to clean EmbeddingFlat type string correctly"

    def test_unrecognized_container_type__returns_as_is(self) -> None:
        """
        Scenario:
            - Test with unrecognized container type that doesn't match Dict/List/Optional/Union

        Expected Outcome:
            - Should return the type string as-is
        """
        result = TypeCleaner.clean_type_parameters("CustomType[str, int]")
        assert result == "CustomType[str, int]"

    def test_no_container_found__returns_as_is(self) -> None:
        """
        Scenario:
            - Test with type string that has brackets but no recognizable container pattern

        Expected Outcome:
            - Should return the type string as-is
        """
        result = TypeCleaner.clean_type_parameters("123[invalid]")
        assert result == "123[invalid]"

    def test_clean_simple_patterns__dict_with_extra_params(self) -> None:
        """
        Scenario:
            - Test _clean_simple_patterns with Dict containing extra parameters

        Expected Outcome:
            - Should clean Dict to only have key and value types
        """
        # This tests the _clean_simple_patterns method which isn't directly exposed
        # but we can trigger it through specific input patterns
        result = TypeCleaner.clean_type_parameters("dict[str, int, bool, None]")
        assert result == "dict[str, int]"

    def test_clean_simple_patterns__list_with_extra_params(self) -> None:
        """
        Scenario:
            - Test _clean_simple_patterns with List containing extra parameters

        Expected Outcome:
            - Should clean List to only have item type
        """
        result = TypeCleaner.clean_type_parameters("List[str, int, bool]")
        assert result == "List[str]"

    def test_clean_simple_patterns__optional_with_none(self) -> None:
        """
        Scenario:
            - Test _clean_simple_patterns with Optional containing None parameter

        Expected Outcome:
            - Should clean Optional to only have the main type
        """
        result = TypeCleaner.clean_type_parameters("Optional[str, None]")
        assert result == "str | None"

    def test_union_edge_cases(self) -> None:
        """
        Scenario:
            - Test Union edge cases including empty members and single member

        Expected Outcome:
            - Should handle edge cases properly
        """
        # Test Union with single member after cleaning
        result = TypeCleaner.clean_type_parameters("Union[str]")
        assert result == "str"

        # Test Union with duplicate members
        result = TypeCleaner.clean_type_parameters("Union[str, str, str]")
        assert result == "str"

    def test_list_edge_cases(self) -> None:
        """
        Scenario:
            - Test List edge cases including empty List and complex nesting

        Expected Outcome:
            - Should handle edge cases with appropriate defaults
        """
        # Test empty List
        result = TypeCleaner.clean_type_parameters("List[]")
        assert result == "List[Any]"

        # Test List with empty string parameter (edge case)
        # This would require specific input to trigger the warning path

    def test_dict_edge_cases(self) -> None:
        """
        Scenario:
            - Test Dict edge cases including empty Dict and single parameter

        Expected Outcome:
            - Should handle edge cases with appropriate defaults
        """
        # Test empty Dict
        result = TypeCleaner.clean_type_parameters("dict[]")
        assert result == "dict[Any, Any]"

        # Test Dict with only key type
        result = TypeCleaner.clean_type_parameters("dict[str]")
        assert result == "dict[str, Any]"

        # Test Dict with more than 2 parameters
        result = TypeCleaner.clean_type_parameters("dict[str, int, bool, float]")
        assert result == "dict[str, int]"

    def test_optional_edge_cases(self) -> None:
        """
        Scenario:
            - Test Optional edge cases including empty Optional and multiple parameters

        Expected Outcome:
            - Should handle edge cases with appropriate defaults
        """
        # Test empty Optional
        result = TypeCleaner.clean_type_parameters("Optional[]")
        assert result == "Any | None"

        # Test Optional with multiple parameters
        result = TypeCleaner.clean_type_parameters("Optional[str, int, bool]")
        assert result == "str | None"

        # Test Optional[None] after cleaning
        result = TypeCleaner.clean_type_parameters("Optional[None]")
        assert result == "Any | None"

    def test_remove_none_from_lists__simple_case(self) -> None:
        """
        Scenario:
            - Test _remove_none_from_lists with simple List[Type, None] pattern

        Expected Outcome:
            - Should remove None parameter from List
        """
        # This method is called internally, test through clean_type_parameters
        result = TypeCleaner.clean_type_parameters("List[str, None]")
        assert result == "List[str]"

    def test_remove_none_from_lists__complex_nested(self) -> None:
        """
        Scenario:
            - Test _remove_none_from_lists with complex nested List patterns

        Expected Outcome:
            - Should handle complex nested patterns with None removal
        """
        # Test complex pattern that triggers the bracket counting logic
        result = TypeCleaner.clean_type_parameters("List[Union[str, int], None]")
        assert result == "List[Union[str, int]]"

        # Test deeply nested case
        result = TypeCleaner.clean_type_parameters("List[dict[str, List[int, None]], None]")
        assert result == "List[dict[str, List[int]]]"

    def test_get_container_type__edge_cases(self) -> None:
        """
        Scenario:
            - Test _get_container_type with various edge cases

        Expected Outcome:
            - Should return None for non-matching patterns
        """
        # Test the method indirectly through patterns that would return None
        result = TypeCleaner.clean_type_parameters("[no_container_prefix]")
        assert result == "[no_container_prefix]"  # Should return as-is

    def test_special_case_pattern_matching(self) -> None:
        """
        Scenario:
            - Test special case pattern matching in _handle_special_cases

        Expected Outcome:
            - Should match specific patterns and return predefined results
        """
        # Test the complex pattern matching logic
        complex_input = (
            "Union[dict[str, Any], List[Union[dict[str, Any], List[JsonValue], "
            "Any | None, bool, float, str, None], None], Any | None, bool, float, str]"
        )

        expected = (
            "Union[dict[str, Any], List[Union[dict[str, Any], List[JsonValue], "
            "Any | None, bool, float, str, None]], Any | None, bool, float, str]"
        )

        result = TypeCleaner.clean_type_parameters(complex_input)
        assert result == expected

    def test_recursive_cleaning(self) -> None:
        """
        Scenario:
            - Test recursive cleaning of nested structures

        Expected Outcome:
            - Should recursively clean all nested type parameters
        """
        # Test deeply nested structure that requires recursive cleaning
        nested_type = "Union[List[dict[str, Optional[Union[str, int, None], None], None], None], None]"
        result = TypeCleaner.clean_type_parameters(nested_type)

        # Should recursively clean each level
        assert "None], None" not in result or result.count("None") < nested_type.count("None")

    def test_clean_simple_patterns_direct_regex_cases(self) -> None:
        """
        Scenario:
            - Test specific regex patterns that clean dict/List/Optional with extra params

        Expected Outcome:
            - Should handle regex-based cleaning correctly through the full pipeline
        """
        # Test Dict pattern - use public API instead of internal _clean_simple_patterns
        from pyopenapi_gen.helpers.type_cleaner import TypeCleaner

        # Test Dict pattern with exact regex match
        result = TypeCleaner.clean_type_parameters("dict[key, value, extra, None]")
        assert result == "dict[key, value]"

        # Test List pattern with exact regex match
        result = TypeCleaner.clean_type_parameters("List[item, extra, None]")
        assert result == "List[item]"

        # Test Optional pattern with exact regex match - converts to union syntax
        result = TypeCleaner.clean_type_parameters("Optional[type, None]")
        assert result == "type | None"

    def test_union_empty_after_cleaning(self) -> None:
        """
        Scenario:
            - Test Union that becomes empty after member cleaning

        Expected Outcome:
            - Should default to Any for empty Union
        """
        # This is hard to trigger naturally, but we can test the logic
        # by understanding that if all members are cleaned to empty strings,
        # it should return "Any"
        result = TypeCleaner.clean_type_parameters("Union[]")
        assert result == "Any"

    def test_list_warning_cases(self) -> None:
        """
        Scenario:
            - Test List cases that trigger warning paths

        Expected Outcome:
            - Should handle edge cases and log warnings appropriately
        """
        # Test empty List which triggers the warning path
        result = TypeCleaner.clean_type_parameters("List[]")
        assert result == "List[Any]"

    def test_dict_warning_cases(self) -> None:
        """
        Scenario:
            - Test Dict cases that trigger warning paths

        Expected Outcome:
            - Should handle edge cases and log warnings appropriately
        """
        # Test Dict with more than 2 parameters (already covered but ensure warning path)
        result = TypeCleaner.clean_type_parameters("dict[a, b, c, d, e]")
        assert result == "dict[a, b]"

        # Test Dict with no parameters after split (edge case)
        result = TypeCleaner.clean_type_parameters("dict[]")
        assert result == "dict[Any, Any]"

    def test_optional_warning_cases(self) -> None:
        """
        Scenario:
            - Test Optional cases that trigger warning paths

        Expected Outcome:
            - Should handle edge cases and log warnings appropriately
        """
        # Test Optional with multiple parameters (warning case)
        result = TypeCleaner.clean_type_parameters("Optional[a, b, c]")
        assert result == "a | None"

        # Test Optional with no parameters after split (edge case)
        result = TypeCleaner.clean_type_parameters("Optional[]")
        assert result == "Any | None"

    def test_remove_none_from_lists_complex_bracket_counting(self) -> None:
        """
        Scenario:
            - Test _remove_none_from_lists with complex bracket counting logic

        Expected Outcome:
            - Should correctly identify and remove None from Lists with complex nesting
        """
        # Test the bracket counting logic with deeply nested structures
        complex_nested = "List[dict[str, List[Union[int, str], None]], None]"
        result = TypeCleaner.clean_type_parameters(complex_nested)

        # Should remove the outer None but preserve inner structure
        assert ", None]" not in result.split("List[", 1)[1].rsplit("]", 1)[0] if "List[" in result else True

        # Test case with multiple closing brackets
        multi_bracket = "List[Union[dict[str, int], List[str]], None]"
        result = TypeCleaner.clean_type_parameters(multi_bracket)
        expected = "List[Union[dict[str, int], List[str]]]"
        assert result == expected

    def test_special_none_removal_patterns(self) -> None:
        """
        Scenario:
            - Test specific None removal patterns in _remove_none_from_lists

        Expected Outcome:
            - Should handle specific OpenAPI 3.1 patterns correctly
        """
        # Test the pattern without Union in the split part
        simple_list_none = "List[SimpleType, None]"
        result = TypeCleaner.clean_type_parameters(simple_list_none)
        assert result == "List[SimpleType]"

        # Test pattern with Union that should NOT be modified by the special case
        union_list = "List[Union[str, int], None]"
        result = TypeCleaner.clean_type_parameters(union_list)
        assert result == "List[Union[str, int]]"

    def test_clean_type_parameters__modern_union_syntax_with_list__preserves_full_type(self) -> None:
        """
        Scenario:
            - Test modern Python union syntax (X | Y) with List types
            - This tests the fix for the truncation bug where "List[X] | None" became "List[X] | Non]"

        Expected Outcome:
            - Should preserve the full type string without truncation
            - The | None part should not be truncated by container cleaning
        """
        # Test the exact bug scenario that was fixed
        result = TypeCleaner.clean_type_parameters("List[DataSourceEvent] | None")
        assert result == "List[DataSourceEvent] | None"
        assert "Non]" not in result  # Ensure no truncation

        # Test with other complex types
        result = TypeCleaner.clean_type_parameters("List[dict[str, Any]] | None")
        assert result == "List[dict[str, Any]] | None"

        # Test with multiple union parts at top level
        result = TypeCleaner.clean_type_parameters("List[str] | int | None")
        assert result == "List[str] | int | None"

        # Note: Nested unions inside dict/List parameters have limitations
        # The primary fix was for top-level union syntax (List[X] | None)
        # which was the actual bug causing "List[X] | Non]" truncation

    def test_clean_type_parameters__modern_union_syntax_nested__handles_correctly(self) -> None:
        """
        Scenario:
            - Test modern union syntax in nested structures

        Expected Outcome:
            - Top-level modern union syntax is preserved (fixed)
            - Nested modern union inside containers may have limitations (known issue)
        """
        # Test top-level modern union - FIXED: should preserve full type
        result = TypeCleaner.clean_type_parameters("dict[str, User] | None")
        assert result == "dict[str, User] | None"

        # Test modern union at top level with List - FIXED
        result = TypeCleaner.clean_type_parameters("List[User] | Admin | None")
        assert result == "List[User] | Admin | None"

        # Note: Nested modern union inside container parameters is a known limitation
        # The primary fix was for top-level union syntax which was causing the
        # "List[X] | None" → "List[X] | Non]" truncation bug in business_swagger.json

    def test_handle_special_cases_pattern_matching_edge_case(self) -> None:
        """
        Scenario:
            - Test the complex pattern matching logic in _handle_special_cases

        Expected Outcome:
            - Should handle the specific string matching conditions
        """
        # Test the specific pattern matching condition on lines 109-127
        test_pattern = (
            "Union[dict[str, Any], List[Union[dict[str, Any], List[JsonValue], "
            "Any | None, bool, float, str, None], None], Any | None, bool, float, str]"
        )

        result = TypeCleaner.clean_type_parameters(test_pattern)

        # Should trigger the special case handling
        expected_pattern = (
            "Union["
            "dict[str, Any], "
            "List["
            "Union["
            "dict[str, Any], List[JsonValue], Any | None, bool, float, str, None"
            "]"
            "], "
            "Any | None, "
            "bool, "
            "float, "
            "str"
            "]"
        )
        assert result == expected_pattern
