"""
Tests for TypeHelper methods that support type conversion and cleaning.
"""

import pytest
from typing import Dict, List, Any, Optional, Union

from pyopenapi_gen.helpers.type_helper import TypeHelper
from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext


class TestTypeHelperCleanTypeParameters:
    """Tests for the _clean_type_parameters function in TypeHelper."""

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
            ("complex_union", "Union[Dict[str, Any, None], List[str, None], Optional[int, None]]", 
             "Union[Dict[str, Any], List[str], Optional[int]]"),
            
            # OpenAPI 3.1 complex nullable cases
            ("openapi_31_list_none", "List[Union[Dict[str, Any], None]]", "List[Union[Dict[str, Any], None]]"),
            ("list_with_multi_params", "List[str, int, bool, None]", "List[str]"),
            ("dict_with_multi_params", "Dict[str, int, bool, None]", "Dict[str, int]"),
            
            # Deeply nested structures
            ("deep_nested_union", 
             "Union[Dict[str, List[Dict[str, Any, None], None]], List[Dict[str, Any, None], None]]",
             "Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]"),
            
            # Real-world complex cases from the errors we've encountered
            ("embedding_flat_case", 
             "Union[Dict[str, Any], List[Union[Dict[str, Any], List[JsonValue], Optional[Any], bool, float, str, None], None], Optional[Any], bool, float, str]",
             "Union[Dict[str, Any], List[Union[Dict[str, Any], List[JsonValue], Optional[Any], bool, float, str, None]], Optional[Any], bool, float, str]"),
            
            # Edge cases
            ("empty_string", "", ""),
            ("no_brackets", "AnyType", "AnyType"),
            ("incomplete_syntax", "Dict[str,", "Dict[str,"),
            ("empty_union", "Union[]", "Any"),
            ("optional_none", "Optional[None]", "Optional[Any]"),
        ],
    )
    def test_clean_type_parameters(self, test_id, input_type, expected_type):
        """
        Scenario:
            - Test _clean_type_parameters with various invalid type strings
            - Verify it correctly removes extraneous None parameters
            
        Expected Outcome:
            - Properly cleaned type strings with no invalid None parameters
        """
        # Act
        result = TypeHelper._clean_type_parameters(input_type)
        
        # Assert
        assert result == expected_type, f"[{test_id}] Failed to clean type string correctly"

    def test_clean_nested_types_with_complex_structures(self):
        """
        Scenario:
            - Test the clean_nested_types method with complex nested structures
            
        Expected Outcome:
            - Should handle deeply nested structures correctly
        """
        # The exact string with no whitespace between parts
        complex_type = "Union[Dict[str, List[Dict[str, Any, None], None]], List[Union[Dict[str, Any, None], str, None]], Optional[Dict[str, Union[str, int, None], None]]]"
        
        expected = "Union[Dict[str, List[Dict[str, Any]]], List[Union[Dict[str, Any], str, None]], Optional[Dict[str, Union[str, int, None]]]]"
        
        result = TypeHelper._clean_type_parameters(complex_type)
        
        assert result == expected, "Failed to clean complex nested type correctly"

    def test_real_world_cases(self):
        """
        Scenario:
            - Test the clean_nested_types method with real-world problem cases
            
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
        
        result = TypeHelper._clean_type_parameters(embedding_flat_type)
        
        assert result == expected, "Failed to clean EmbeddingFlat type string correctly"
        

class TestTypeHelperWithIRSchema:
    """Tests TypeHelper's schema handling with IRSchema objects."""
    
    def test_finalize_type_with_optional(self):
        """
        Scenario:
            - Test _finalize_type_with_optional with different type strings
            - Test with both nullable and non-nullable schemas
            
        Expected Outcome:
            - Properly wrapped types with Optional when needed
        """
        # Setup test context
        context = RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )
        
        # Test cases
        nullable_schema = IRSchema(name="TestSchema", is_nullable=True)
        non_nullable_schema = IRSchema(name="TestSchema", is_nullable=False)
        
        # Case 1: Simple type with nullable schema
        result = TypeHelper._finalize_type_with_optional("str", nullable_schema, True, context)
        assert result == "Optional[str]", "Failed to wrap simple type with Optional for nullable schema"
        
        # Case 2: Simple type with non-nullable schema but not required
        result = TypeHelper._finalize_type_with_optional("str", non_nullable_schema, False, context)
        assert result == "Optional[str]", "Failed to wrap Optional for non-required field"
        
        # Case 3: Already Optional type doesn't get double-wrapped
        result = TypeHelper._finalize_type_with_optional("Optional[str]", nullable_schema, True, context)
        assert result == "Optional[str]", "Double-wrapped Optional type"
        
        # Case 4: Union type gets None added
        result = TypeHelper._finalize_type_with_optional("Union[str, int]", non_nullable_schema, False, context)
        assert "Union[str, int, None]" == result, "Failed to add None to Union for optional field"
        
        # Case 5: Any type becomes Optional[Any]
        result = TypeHelper._finalize_type_with_optional("Any", nullable_schema, True, context)
        assert result == "Optional[Any]", "Failed to convert Any to Optional[Any]"
        
        # Case 6: Union type with None already doesn't get modified
        result = TypeHelper._finalize_type_with_optional("Union[str, int, None]", nullable_schema, True, context)
        assert result == "Union[str, int, None]", "Modified Union that already had None"
        
        # Case 7: Nullable Union gets properly wrapped with Optional
        result = TypeHelper._finalize_type_with_optional("Union[str, int]", nullable_schema, True, context)
        assert result == "Optional[Union[str, int]]", "Failed to wrap Union with Optional for nullable schema"

    def test_openapi31_nullable_handling(self):
        """
        Scenario:
            - Test the combination of type_parser.extract_primary_type_and_nullability
              and TypeHelper._finalize_type_with_optional with OpenAPI 3.1 nullable types
            
        Expected Outcome:
            - Properly handles OpenAPI 3.1 nullable array types
        """
        # This is an end-to-end test for the changes to both modules
        # We can't directly test extract_primary_type_and_nullability here as it's in a different module
        # But we can verify the expected behavior of the fixed functions working together
        
        # Setup test context
        context = RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )
        
        # Create a schema with nullable=True (as would be set by extract_primary_type_and_nullability)
        nullable_schema = IRSchema(name="NullableArray", is_nullable=True, type="array")
        
        # Test complex list type that should be wrapped with Optional
        result = TypeHelper._finalize_type_with_optional("List[Dict[str, Any]]", nullable_schema, True, context)
        assert result == "Optional[List[Dict[str, Any]]]", "Failed to properly handle nullable array"
        
        # Test multiple-type Union that should be wrapped with Optional
        result = TypeHelper._finalize_type_with_optional(
            "Union[Dict[str, Any], List[str], int]", 
            nullable_schema, 
            True, 
            context
        )
        assert result == "Optional[Union[Dict[str, Any], List[str], int]]", "Failed to properly handle nullable Union" 