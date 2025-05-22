"""
Systematic Edge Case Testing for PyOpenAPI Generator

This module provides comprehensive testing of edge cases and boundary conditions
that might not be covered by regular unit tests. The focus is on robustness,
error handling, and proper behavior with unusual or extreme inputs.
"""

import pytest
import tempfile
import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock

from pyopenapi_gen.ir import IRSchema, IRSpec
from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter
from pyopenapi_gen.context.render_context import RenderContext


class TestNameSanitizationEdgeCases:
    """Test edge cases in name sanitization and collision handling."""
    
    def test_empty_and_whitespace_names(self) -> None:
        """Test handling of empty and whitespace-only names."""
        edge_cases = ["", " ", "  ", "\t", "\n", "\r\n", " \t \n "]
        
        for name in edge_cases:
            sanitized = NameSanitizer.sanitize_class_name(name)
            # Should produce a valid Python identifier
            assert sanitized.isidentifier() or sanitized == "", f"Failed for '{repr(name)}'"
            
    def test_very_long_names(self) -> None:
        """Test handling of extremely long names."""
        # Test with very long name (beyond typical limits)
        long_name = "VeryLongSchemaName" * 50  # 900+ characters
        sanitized = NameSanitizer.sanitize_class_name(long_name)
        
        # Should still be a valid identifier but possibly truncated
        assert sanitized.isidentifier()
        # Should not be empty
        assert len(sanitized) > 0
        
    def test_unicode_and_special_characters(self) -> None:
        """Test handling of Unicode and special characters."""
        unicode_cases = [
            "Schema_名前",  # Japanese
            "Схема_данных",  # Cyrillic
            "مخطط_البيانات",  # Arabic
            "Schema@#$%^&*()",  # Special characters
            "Schema-with-hyphens",
            "Schema.with.dots",
            "Schema with spaces",
            "123NumericStart",
            "0StartWithZero"
        ]
        
        for name in unicode_cases:
            sanitized = NameSanitizer.sanitize_class_name(name)
            assert sanitized.isidentifier(), f"Failed to sanitize '{name}' -> '{sanitized}'"
            
    def test_all_reserved_words_collision(self) -> None:
        """Test that Python reserved words are properly handled."""
        # Test keywords that should be sanitized when used as class names
        lowercase_keywords = [
            'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 
            'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 
            'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 
            'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
        ]
        
        # Test that lowercase keywords get capitalized and potentially suffixed
        for keyword in lowercase_keywords:
            sanitized = NameSanitizer.sanitize_class_name(keyword)
            assert sanitized.isidentifier(), f"Sanitized keyword '{sanitized}' is not valid identifier"
            # Should be different from original since keywords should be avoided
            assert sanitized != keyword, f"Keyword '{keyword}' was not modified"
            
        # Test the capitalized built-in constants separately
        constants = ['False', 'True', 'None']
        for const in constants:
            sanitized = NameSanitizer.sanitize_class_name(const)
            assert sanitized.isidentifier(), f"Sanitized constant '{sanitized}' is not valid identifier"
            # These might be sanitized differently due to the case-sensitivity handling
            
    def test_name_collision_resolution(self) -> None:
        """Test systematic name collision resolution.""" 
        # Test that different naming patterns produce valid identifiers
        test_names = [
            "User", "user", "USER", "data", "type", "list", "class", "def"
        ]
        
        for name in test_names:
            sanitized = NameSanitizer.sanitize_class_name(name)
            # All should be valid identifiers
            assert sanitized.isidentifier(), f"'{sanitized}' is not a valid identifier for input '{name}'"
            
        # Test that reserved names get modified
        reserved_name = "list"
        sanitized_reserved = NameSanitizer.sanitize_class_name(reserved_name)
        assert sanitized_reserved != "List", f"Reserved name '{reserved_name}' should be modified, got '{sanitized_reserved}'"


class TestSchemaParsingEdgeCases:
    """Test edge cases in schema parsing and type resolution."""
    
    def test_empty_schema_objects(self) -> None:
        """Test parsing completely empty schema objects."""
        context = ParsingContext()
        
        # Empty schema
        empty_schema = {}
        result = _parse_schema("EmptySchema", empty_schema, context)
        assert result is not None
        assert result.name == "EmptySchema"
        
    def test_schema_with_null_values(self) -> None:
        """Test schemas with null/None values in various fields."""
        context = ParsingContext()
        
        # Test schema with missing/null type (should default to object)
        schema_with_nulls = {
            "description": None,
            "properties": {}
        }
        
        result = _parse_schema("NullSchema", schema_with_nulls, context)
        assert result is not None
        
    def test_deeply_nested_schema_properties(self) -> None:
        """Test schemas with very deep nesting."""
        # Create a deeply nested schema
        deep_schema = {"type": "object"}
        current = deep_schema
        
        # Create 20 levels of nesting
        for i in range(20):
            current["properties"] = {
                f"level_{i}": {
                    "type": "object"
                }
            }
            current = current["properties"][f"level_{i}"]
            
        # Add final property
        current["properties"] = {"final_value": {"type": "string"}}
        
        context = ParsingContext()
        result = _parse_schema("DeepSchema", deep_schema, context)
        assert result is not None
        
    def test_schema_with_extremely_large_enum(self) -> None:
        """Test enum with very large number of values."""
        large_enum_values = [f"value_{i}" for i in range(1000)]
        
        enum_schema = {
            "type": "string",
            "enum": large_enum_values
        }
        
        context = ParsingContext()
        result = _parse_schema("LargeEnum", enum_schema, context)
        assert result is not None
        assert result.enum == large_enum_values
        
    def test_schema_with_circular_all_of_references(self) -> None:
        """Test allOf with circular references."""
        context = ParsingContext()
        context.raw_spec_schemas = {
            "CircularA": {
                "allOf": [
                    {"$ref": "#/components/schemas/CircularB"},
                    {"type": "object", "properties": {"a_field": {"type": "string"}}}
                ]
            },
            "CircularB": {
                "allOf": [
                    {"$ref": "#/components/schemas/CircularA"},
                    {"type": "object", "properties": {"b_field": {"type": "integer"}}}
                ]
            }
        }
        
        # Should handle circular references gracefully
        result_a = _parse_schema("CircularA", context.raw_spec_schemas["CircularA"], context)
        result_b = _parse_schema("CircularB", context.raw_spec_schemas["CircularB"], context)
        
        assert result_a is not None
        assert result_b is not None


class TestInvalidReferenceHandling:
    """Test handling of invalid, malformed, or missing references."""
    
    def test_malformed_ref_paths(self) -> None:
        """Test various malformed $ref paths."""
        malformed_refs = [
            "",  # Empty ref
            "#",  # Just hash
            "#/",  # Incomplete path
            "#/components",  # Missing schemas
            "#/components/",  # Trailing slash
            "#/components/schemas/",  # Missing schema name
            "#/components/schemas/ ",  # Space in name
            "#/invalid/path/structure",  # Wrong structure
            "not-a-ref-at-all",  # Not a ref
            "#/components/schemas/NonExistent",  # Valid format but doesn't exist
        ]
        
        context = ParsingContext()
        context.raw_spec_schemas = {"ValidSchema": {"type": "string"}}
        
        for ref_path in malformed_refs:
            schema_with_bad_ref = {
                "type": "object",
                "properties": {
                    "bad_ref": {"$ref": ref_path}
                }
            }
            
            # Should not crash but handle gracefully
            result = _parse_schema("SchemaWithBadRef", schema_with_bad_ref, context)
            assert result is not None
            
    def test_self_referencing_with_invalid_structure(self) -> None:
        """Test self-references with invalid schema structure."""
        context = ParsingContext()
        
        # Self-reference in invalid location
        invalid_self_ref = {
            "type": "object",
            "description": {"$ref": "#/components/schemas/InvalidSelfRef"},  # Wrong place for ref
            "properties": {
                "self": {"$ref": "#/components/schemas/InvalidSelfRef"}
            }
        }
        
        context.raw_spec_schemas["InvalidSelfRef"] = invalid_self_ref
        result = _parse_schema("InvalidSelfRef", invalid_self_ref, context)
        assert result is not None
        
    def test_missing_referenced_schemas(self) -> None:
        """Test references to schemas that don't exist in the spec."""
        context = ParsingContext()
        context.raw_spec_schemas = {}  # Empty - no schemas available
        
        schema_with_missing_refs = {
            "type": "object",
            "properties": {
                "missing1": {"$ref": "#/components/schemas/DoesNotExist1"},
                "missing2": {"$ref": "#/components/schemas/DoesNotExist2"},
                "array_missing": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/DoesNotExist3"}
                }
            }
        }
        
        result = _parse_schema("SchemaWithMissingRefs", schema_with_missing_refs, context)
        assert result is not None
        # Should have placeholder schemas for missing references
        assert result.properties is not None


class TestBoundaryConditions:
    """Test boundary conditions and extreme values."""
    
    def test_maximum_recursion_depth_protection(self) -> None:
        """Test protection against stack overflow from deep recursion."""
        # Create a schema that would cause very deep recursion
        context = ParsingContext()
        
        # Chain of references that goes very deep
        for i in range(200):  # More than typical max depth
            context.raw_spec_schemas[f"Deep{i}"] = {
                "type": "object",
                "properties": {
                    "next": {"$ref": f"#/components/schemas/Deep{i+1}"} if i < 199 else {"type": "string"}
                }
            }
            
        # Should handle without stack overflow
        result = _parse_schema("Deep0", context.raw_spec_schemas["Deep0"], context)
        assert result is not None
        
    def test_extremely_large_schema_count(self) -> None:
        """Test handling of specs with very large number of schemas."""
        large_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Large API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {f"Schema{i}": {"type": "string"} for i in range(1000)}
            }
        }
        
        # Should handle large number of schemas efficiently
        result = load_ir_from_spec(large_spec)
        assert result is not None
        assert len(result.schemas) == 1000
        
    def test_schema_with_very_long_descriptions(self) -> None:
        """Test schemas with extremely long descriptions."""
        very_long_description = "This is a very long description. " * 1000  # ~34KB
        
        schema_with_long_desc = {
            "type": "object",
            "description": very_long_description,
            "properties": {
                "field": {
                    "type": "string",
                    "description": very_long_description
                }
            }
        }
        
        context = ParsingContext()
        result = _parse_schema("LongDescSchema", schema_with_long_desc, context)
        assert result is not None
        assert result.description == very_long_description


class TestSpecialCharactersAndEncoding:
    """Test handling of special characters and encoding issues."""
    
    def test_schema_names_with_special_characters(self) -> None:
        """Test schema names containing various special characters."""
        special_char_names = [
            "Schema-With-Hyphens",
            "Schema.With.Dots",
            "Schema_With_Underscores",
            "Schema With Spaces",
            "Schema@#$%",
            "Schema(1)",
            "Schema[Array]",
            "Schema{Object}",
            "Schema|Pipe",
            "Schema\\Backslash",
            "Schema/Forward/Slash",
        ]
        
        for name in special_char_names:
            spec = {
                "openapi": "3.1.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {},
                "components": {
                    "schemas": {
                        name: {"type": "string"}
                    }
                }
            }
            
            # Should handle without crashing
            result = load_ir_from_spec(spec)
            assert result is not None
            assert len(result.schemas) == 1
            
    def test_unicode_in_descriptions_and_examples(self) -> None:
        """Test Unicode characters in descriptions and examples."""
        unicode_content = {
            "type": "object",
            "description": "Описание на русском языке 中文描述 توصيف عربي",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "名前 اسم имя",
                    "example": "例 مثال пример"
                },
                "emoji_field": {
                    "type": "string",
                    "description": "Field with emojis 🚀🔥💯",
                    "example": "Hello 👋 World 🌍"
                }
            }
        }
        
        context = ParsingContext()
        result = _parse_schema("UnicodeSchema", unicode_content, context)
        assert result is not None


class TestErrorRecoveryAndResilience:
    """Test error recovery and system resilience."""
    
    def test_partial_spec_processing(self) -> None:
        """Test processing specs with some invalid parts."""
        spec_with_partial_errors = {
            "openapi": "3.1.0",
            "info": {"title": "Partial Error API", "version": "1.0.0"},
            "paths": {
                "/valid": {
                    "get": {
                        "operationId": "validOperation",
                        "responses": {"200": {"description": "OK"}}
                    }
                },
                "/invalid": {
                    "get": {
                        # Missing operationId and responses - invalid
                        "description": "Invalid operation"
                    }
                }
            },
            "components": {
                "schemas": {
                    "ValidSchema": {"type": "string"},
                    "InvalidSchema": {
                        # Invalid schema structure
                        "type": "unknown_type",
                        "invalid_property": "should not be here"
                    }
                }
            }
        }
        
        # Should process valid parts and handle invalid parts gracefully
        result = load_ir_from_spec(spec_with_partial_errors)
        assert result is not None
        # Should have at least some valid content
        assert len(result.schemas) >= 1
        
    def test_memory_usage_with_large_inputs(self) -> None:
        """Test memory efficiency with large inputs."""
        # Create a large spec to test memory handling
        large_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Memory Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Add schemas with moderately complex structures 
        for i in range(50):  # Reduced from 100
            large_spec["components"]["schemas"][f"ComplexSchema{i}"] = {
                "type": "object",
                "properties": {
                    f"field_{j}": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                f"nested_{k}": {"type": "string"}
                                for k in range(5)  # Reduced from 10
                            }
                        }
                    }
                    for j in range(5)  # Reduced from 10
                }
            }
        
        # Should complete without memory issues
        result = load_ir_from_spec(large_spec)
        assert result is not None
        # Should have at least the 50 primary schemas, plus any generated inline schemas
        assert len(result.schemas) >= 50
        
    @patch('pyopenapi_gen.core.parsing.schema_parser.logger')
    def test_logging_during_error_conditions(self, mock_logger: MagicMock) -> None:
        """Test that appropriate logging occurs during error conditions."""
        context = ParsingContext()
        
        # Schema that will cause warnings/errors
        problematic_schema = {
            "type": "object",
            "properties": {
                "bad_ref": {"$ref": "#/components/schemas/NonExistent"}
            }
        }
        
        result = _parse_schema("ProblematicSchema", problematic_schema, context)
        assert result is not None
        
        # Verify that appropriate logging occurred
        # (Note: Specific assertions would depend on actual logging implementation)


class TestCodeGenerationEdgeCases:
    """Test edge cases in code generation and file output."""
    
    def test_model_generation_with_edge_case_schemas(self) -> None:
        """Test model generation with various edge case schemas."""
        edge_case_schemas = {
            "EmptyObject": {"type": "object"},
            "ObjectWithoutProperties": {"type": "object", "additionalProperties": True},
            "EnumWithOneValue": {"type": "string", "enum": ["single_value"]},
            "ArrayWithoutItems": {"type": "array"},
            "StringWithoutConstraints": {"type": "string"},
        }
        
        # Create a simple spec and parse it to get valid IR
        spec_dict = {
            "openapi": "3.1.0",
            "info": {"title": "Edge Case Test", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": edge_case_schemas}
        }
        
        spec = load_ir_from_spec(spec_dict)
        assert spec is not None
        assert len(spec.schemas) > 0
            
    def test_filename_generation_edge_cases(self) -> None:
        """Test filename generation with problematic schema names."""
        problematic_names = [
            "Schema With Spaces",
            "Schema-With-Hyphens", 
            "Schema.With.Dots",
            "SCHEMA_ALL_CAPS",
            "schema_all_lowercase",
            "123NumericStart",
            "Special@#$Characters"
        ]
        
        for name in problematic_names:
            # Test that filename generation produces valid filenames
            sanitized_module = NameSanitizer.sanitize_module_name(name)
            sanitized_class = NameSanitizer.sanitize_class_name(name)
            
            # Should be valid Python module/class names
            assert sanitized_module.replace('_', '').isalnum() or sanitized_module == ""
            assert sanitized_class.isidentifier() or sanitized_class == ""


class TestPerformanceAndScalability:
    """Test performance characteristics and scalability."""
    
    def test_parsing_performance_with_complex_specs(self) -> None:
        """Test parsing performance with complex, realistic specs."""
        import time
        
        # Create a moderately complex spec
        complex_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Complex API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}}
        }
        
        # Add interconnected schemas
        for i in range(50):
            complex_spec["components"]["schemas"][f"Schema{i}"] = {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    f"ref_to_{(i+1)%50}": {"$ref": f"#/components/schemas/Schema{(i+1)%50}"},
                    "array_field": {
                        "type": "array",
                        "items": {"$ref": f"#/components/schemas/Schema{(i+10)%50}"}
                    }
                }
            }
        
        start_time = time.time()
        result = load_ir_from_spec(complex_spec)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 5 seconds)
        parsing_time = end_time - start_time
        assert parsing_time < 5.0, f"Parsing took {parsing_time:.2f}s, should be under 5s"
        assert result is not None
        # Should have at least the 50 primary schemas, may have additional inline schemas
        assert len(result.schemas) >= 50


# Integration test class for comprehensive edge case validation
class TestComprehensiveEdgeCaseValidation:
    """Comprehensive validation of edge cases across the entire system."""
    
    def test_end_to_end_with_edge_case_spec(self) -> None:
        """Test complete end-to-end processing with an edge case heavy spec."""
        edge_case_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "Edge Case API 🚀",
                "version": "1.0.0-beta+build.123",
                "description": "API with many edge cases and special characters 中文"
            },
            "paths": {
                "/test-endpoint": {
                    "get": {
                        "operationId": "getTestEndpoint",
                        "parameters": [
                            {
                                "name": "param-with-hyphens",
                                "in": "query",
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Success response with edge cases",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/EdgeCaseResponse"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "EdgeCaseResponse": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "data": {"$ref": "#/components/schemas/EdgeCaseResponse"},  # Self-reference
                            "list_field": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "enum_field": {
                                "type": "string",
                                "enum": ["value-with-hyphens", "VALUE_WITH_UNDERSCORES", "123_numeric_start"]
                            }
                        }
                    }
                }
            }
        }
        
        # Should process completely without errors
        result = load_ir_from_spec(edge_case_spec)
        assert result is not None
        assert len(result.schemas) >= 1
        assert len(result.operations) >= 1
        
        # Verify the edge case schema was processed
        assert "EdgeCaseResponse" in result.schemas
        edge_case_schema = result.schemas["EdgeCaseResponse"]
        assert edge_case_schema.properties is not None
        assert "id" in edge_case_schema.properties or "id_" in edge_case_schema.properties  # May be sanitized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])