"""
Integration Edge Case Testing for PyOpenAPI Generator

This module tests edge cases that occur when different components of the system
interact, including complex real-world scenarios and integration points.
"""

import json
import tempfile
from pathlib import Path

import pytest
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter
from pyopenapi_gen.generator.client_generator import ClientGenerator


class TestComplexSchemaInteractions:
    """Test complex interactions between different schema types and patterns."""

    def test_deeply_nested_composition_schemas(self) -> None:
        """Test deeply nested allOf/anyOf/oneOf compositions."""
        complex_composition_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Complex Composition API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "BaseSchema": {"type": "object", "properties": {"base_field": {"type": "string"}}},
                    "MiddleSchema": {
                        "allOf": [
                            {"$ref": "#/components/schemas/BaseSchema"},
                            {"type": "object", "properties": {"middle_field": {"type": "integer"}}},
                        ]
                    },
                    "ComplexSchema": {
                        "anyOf": [
                            {"$ref": "#/components/schemas/MiddleSchema"},
                            {
                                "oneOf": [
                                    {"type": "object", "properties": {"option_a": {"type": "string"}}},
                                    {"type": "object", "properties": {"option_b": {"type": "boolean"}}},
                                ]
                            },
                        ]
                    },
                    "UltraComplexSchema": {
                        "allOf": [
                            {"$ref": "#/components/schemas/ComplexSchema"},
                            {
                                "anyOf": [
                                    {
                                        "type": "object",
                                        "properties": {
                                            "ultra_field": {
                                                "oneOf": [
                                                    {"type": "string"},
                                                    {"type": "integer"},
                                                    {"$ref": "#/components/schemas/BaseSchema"},
                                                ]
                                            }
                                        },
                                    }
                                ]
                            },
                        ]
                    },
                }
            },
        }

        result = load_ir_from_spec(complex_composition_spec)
        assert result is not None
        assert len(result.schemas) >= 4

        # Should handle the complex composition without errors
        ultra_complex = result.schemas.get("UltraComplexSchema")
        assert ultra_complex is not None

    def test_circular_references_in_compositions(self) -> None:
        """Test circular references within composition schemas."""
        circular_composition_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Circular Composition API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "CircularA": {
                        "allOf": [
                            {"type": "object", "properties": {"field_a": {"type": "string"}}},
                            {"$ref": "#/components/schemas/CircularB"},
                        ]
                    },
                    "CircularB": {
                        "anyOf": [
                            {"type": "object", "properties": {"field_b": {"type": "integer"}}},
                            {"$ref": "#/components/schemas/CircularC"},
                        ]
                    },
                    "CircularC": {
                        "oneOf": [
                            {"type": "object", "properties": {"field_c": {"type": "boolean"}}},
                            {"$ref": "#/components/schemas/CircularA"},
                        ]
                    },
                }
            },
        }

        result = load_ir_from_spec(circular_composition_spec)
        assert result is not None
        # Should handle circular references in compositions gracefully

    def test_arrays_with_complex_item_schemas(self) -> None:
        """Test arrays with complex item definitions."""
        array_complexity_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Array Complexity API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "ArrayOfArrays": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                    },
                    "ArrayOfComplexObjects": {
                        "type": "array",
                        "items": {
                            "allOf": [
                                {"type": "object", "properties": {"id": {"type": "integer"}}},
                                {
                                    "anyOf": [
                                        {"properties": {"type_a": {"type": "string"}}},
                                        {"properties": {"type_b": {"type": "boolean"}}},
                                    ]
                                },
                            ]
                        },
                    },
                    "ArrayWithSelfReference": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ArrayWithSelfReference"},
                    },
                }
            },
        }

        result = load_ir_from_spec(array_complexity_spec)
        assert result is not None
        assert len(result.schemas) >= 3


class TestNameCollisionEdgeCases:
    """Test edge cases around name collisions and resolution."""

    def test_massive_name_collision_scenario(self) -> None:
        """Test handling of many schemas with names that would collide."""
        collision_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Name Collision API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }

        # Create many schemas with colliding names
        collision_patterns = [
            "User",
            "user",
            "USER",
            "User_",
            "User__",
            "_User",
            "__User__",
            "UserModel",
            "UserSchema",
            "UserData",
            "UserInfo",
            "UserDetails",
            "User1",
            "User2",
            "User3",
            "User01",
            "User02",
            "User03",
            "User-Model",
            "User_Model",
            "User.Model",
            "User@Model",
            "UserType",
            "user_type",
            "USER_TYPE",
            "UserType_",
            "_UserType",
        ]

        for i, name in enumerate(collision_patterns):
            collision_spec["components"]["schemas"][name] = {
                "type": "object",
                "properties": {"id": {"type": "integer"}, f"field_{i}": {"type": "string"}},
            }

        result = load_ir_from_spec(collision_spec)
        assert result is not None

        # With unified system, primitive properties remain as properties (not extracted as schemas)
        # We should have roughly the same number of schemas as collision patterns,
        # but some may have been deduplicated due to name sanitization

        # Basic sanity checks - should have schemas for the main object types
        assert len(result.schemas) >= len(collision_patterns) // 2, "Should have reasonable number of schemas"
        assert len(result.schemas) <= len(collision_patterns) + 10, "Should not have excessive schemas"

        # Verify that major object schemas exist (allowing for name sanitization)
        found_schemas = 0
        for pattern in collision_patterns:
            # Find schemas that could represent this pattern (accounting for name sanitization)
            sanitized_name = pattern.replace("-", "_").replace(".", "_").replace("@", "_")
            for schema_name in result.schemas:
                if (
                    schema_name == pattern
                    or schema_name == sanitized_name
                    or schema_name.lower().replace("_", "") == pattern.lower().replace("_", "")
                ):
                    found_schemas += 1
                    break

        # Should find most of the patterns (some may be deduplicated)
        assert (
            found_schemas >= len(collision_patterns) // 2
        ), f"Should find most collision patterns, found {found_schemas} out of {len(collision_patterns)}"

        # At the parsing level, we expect duplicate names since collision resolution
        # happens during code generation in the emitter, not during parsing.
        # However, we can test that collision resolution works by running the emitter.

        with tempfile.TemporaryDirectory() as temp_dir:
            context = RenderContext(
                overall_project_root=temp_dir,
                package_root_for_generated_code=temp_dir,
                core_package_name="test_core",
                parsed_schemas=result.schemas,
            )

            emitter = ModelsEmitter(context=context, parsed_schemas=result.schemas)
            emitter.emit(result, temp_dir)

            # After emitter runs collision resolution, all generation_names should be unique
            generation_names = set()
            for schema in result.schemas.values():
                if hasattr(schema, "generation_name") and schema.generation_name:
                    assert (
                        schema.generation_name not in generation_names
                    ), f"Duplicate generation_name after collision resolution: {schema.generation_name}"
                    generation_names.add(schema.generation_name)

            # Verify models directory was created with files
            models_dir = Path(temp_dir) / "models"
            if models_dir.exists():
                model_files = list(models_dir.glob("*.py"))
                # Should have generated files for object schemas (not all 55 schemas generate files)
                assert len(model_files) >= 10  # At least some files should be generated

    def test_collision_with_python_builtins_and_keywords(self) -> None:
        """Test collisions with Python builtins and keywords."""
        builtin_collision_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Builtin Collision API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }

        # Names that would collide with Python builtins/keywords
        problematic_names = [
            "type",
            "int",
            "str",
            "list",
            "dict",
            "set",
            "tuple",
            "bool",
            "object",
            "float",
            "complex",
            "bytes",
            "bytearray",
            "range",
            "class",
            "def",
            "if",
            "else",
            "for",
            "while",
            "try",
            "except",
            "import",
            "from",
            "as",
            "with",
            "lambda",
            "return",
            "yield",
            "print",
            "len",
            "max",
            "min",
            "sum",
            "abs",
            "all",
            "any",
            "id",
            "input",
            "open",
            "file",
            "exec",
            "eval",
            "compile",
        ]

        for name in problematic_names:
            builtin_collision_spec["components"]["schemas"][name] = {
                "type": "object",
                "properties": {"value": {"type": "string"}},
            }

        result = load_ir_from_spec(builtin_collision_spec)
        assert result is not None

        # All schemas should be properly sanitized
        for schema_name, schema in result.schemas.items():
            sanitized_name = schema.name
            # Should not conflict with Python builtins/keywords
            assert sanitized_name != schema_name or schema_name not in problematic_names


class TestRealWorldComplexityScenarios:
    """Test scenarios based on real-world API complexity."""

    def test_large_scale_microservice_spec(self) -> None:
        """Test a large spec resembling a microservice architecture."""
        microservice_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Microservice API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }

        # Create schemas for different domains
        domains = ["User", "Product", "Order", "Payment", "Inventory", "Shipping"]
        operations = ["Create", "Update", "Delete", "List", "Get"]
        types = ["Request", "Response", "Data", "Meta", "Error"]

        schema_count = 0
        for domain in domains:
            for operation in operations:
                for type_suffix in types:
                    schema_name = f"{domain}{operation}{type_suffix}"
                    microservice_spec["components"]["schemas"][schema_name] = {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            f"{domain.lower()}_data": {
                                "type": "object",
                                "properties": {f"{operation.lower()}_field": {"type": "string"}},
                            },
                        },
                    }
                    schema_count += 1

        # Add cross-references between domains
        microservice_spec["components"]["schemas"]["OrderCreateData"]["properties"]["user"] = {
            "$ref": "#/components/schemas/UserCreateData"
        }
        microservice_spec["components"]["schemas"]["OrderCreateData"]["properties"]["products"] = {
            "type": "array",
            "items": {"$ref": "#/components/schemas/ProductCreateData"},
        }

        result = load_ir_from_spec(microservice_spec)
        assert result is not None

        # After refactoring, inline properties are extracted as separate schemas:
        # - 150 original object schemas
        # - 1 shared 'id' schema (string)
        # - 1 shared 'timestamp' schema (string with date-time format)
        # - 5 operation field schemas (create_field, update_field, delete_field, list_field, get_field)
        # - 150+ domain_data schemas (nested objects)
        # - Plus a few extra from cross-references
        # Total: ~308 schemas
        expected_min_schemas = schema_count * 2  # At least double due to inline extraction
        assert len(result.schemas) >= expected_min_schemas

    def test_api_with_many_optional_and_required_fields(self) -> None:
        """Test API with complex required/optional field patterns."""
        complex_fields_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Complex Fields API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "ComplexEntity": {
                        "type": "object",
                        "required": ["id", "name", "critical_field"],
                        "properties": {
                            # Required fields
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "critical_field": {"type": "string"},
                            # Optional fields with various types
                            "optional_string": {"type": "string"},
                            "optional_integer": {"type": "integer"},
                            "optional_boolean": {"type": "boolean"},
                            "optional_array": {"type": "array", "items": {"type": "string"}},
                            "optional_object": {"type": "object", "properties": {"nested_field": {"type": "string"}}},
                            "optional_ref": {"$ref": "#/components/schemas/ReferencedSchema"},
                            "optional_enum": {"type": "string", "enum": ["option1", "option2", "option3"]},
                            # Fields with complex constraints
                            "constrained_string": {
                                "type": "string",
                                "minLength": 5,
                                "maxLength": 100,
                                "pattern": "^[A-Za-z0-9_-]+$",
                            },
                            "constrained_number": {"type": "number", "minimum": 0, "maximum": 1000, "multipleOf": 0.01},
                            "constrained_array": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "minItems": 1,
                                "maxItems": 10,
                                "uniqueItems": True,
                            },
                        },
                    },
                    "ReferencedSchema": {
                        "type": "object",
                        "properties": {"ref_id": {"type": "string"}, "ref_data": {"type": "string"}},
                    },
                }
            },
        }

        result = load_ir_from_spec(complex_fields_spec)
        assert result is not None

        complex_entity = result.schemas.get("ComplexEntity")
        assert complex_entity is not None
        assert sorted(complex_entity.required) == sorted(["id", "name", "critical_field"])
        assert complex_entity.properties is not None
        assert len(complex_entity.properties) >= 10


class TestErrorHandlingIntegration:
    """Test error handling across component integration points."""

    def test_cascading_error_recovery(self) -> None:
        """Test recovery from cascading errors across components."""
        error_prone_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Error Prone API", "version": "1.0.0"},
            "paths": {
                "/endpoint1": {
                    "get": {
                        "operationId": "getEndpoint1",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {"schema": {"$ref": "#/components/schemas/InvalidRef1"}}
                                },
                            }
                        },
                    }
                },
                "/endpoint2": {
                    "post": {
                        "operationId": "postEndpoint2",
                        "requestBody": {
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ValidSchema"}}}
                        },
                        "responses": {
                            "201": {
                                "description": "Created",
                                "content": {
                                    "application/json": {"schema": {"$ref": "#/components/schemas/InvalidRef2"}}
                                },
                            }
                        },
                    }
                },
            },
            "components": {
                "schemas": {
                    "ValidSchema": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                    }
                    # Note: InvalidRef1 and InvalidRef2 are missing - this should cause errors
                }
            },
        }

        # Should handle missing references gracefully
        result = load_ir_from_spec(error_prone_spec)
        assert result is not None
        # Should have at least the valid schema
        assert "ValidSchema" in result.schemas
        # Should have operations even with some invalid references
        assert len(result.operations) >= 1

    def test_partial_code_generation_with_errors(self) -> None:
        """Test that code generation continues even with some problematic schemas."""
        mixed_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Mixed Valid/Invalid API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "ValidSchema1": {"type": "object", "properties": {"field1": {"type": "string"}}},
                    "ValidSchema2": {"type": "object", "properties": {"field2": {"type": "integer"}}},
                    "ProblematicSchema": {
                        "type": "object",
                        "properties": {"bad_ref": {"$ref": "#/components/schemas/DoesNotExist"}},
                    },
                }
            },
        }

        result = load_ir_from_spec(mixed_spec)
        assert result is not None

        with tempfile.TemporaryDirectory() as temp_dir:
            context = RenderContext(
                overall_project_root=temp_dir, package_root_for_generated_code=temp_dir, core_package_name="test_core"
            )

            emitter = ModelsEmitter(context=context, parsed_schemas=result.schemas)

            # Should generate code for valid schemas even if some are problematic
            emitter.emit(result, temp_dir)

            models_dir = Path(temp_dir) / "models"
            assert models_dir.exists()

            # Should have files for valid schemas
            generated_files = list(models_dir.glob("*.py"))
            assert len(generated_files) >= 2  # At least for ValidSchema1 and ValidSchema2


class TestMemoryAndPerformanceEdgeCases:
    """Test memory usage and performance edge cases."""

    def test_memory_efficiency_with_duplicate_schemas(self) -> None:
        """Test memory efficiency when many schemas are very similar."""
        duplicate_heavy_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Duplicate Heavy API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }

        # Create many very similar schemas (testing memory efficiency)
        base_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                    },
                },
            },
        }

        # Create 200 nearly identical schemas
        for i in range(200):
            schema_copy = json.loads(json.dumps(base_schema))  # Deep copy
            schema_copy["properties"][f"unique_field_{i}"] = {"type": "string"}
            duplicate_heavy_spec["components"]["schemas"][f"SimilarSchema{i}"] = schema_copy

        result = load_ir_from_spec(duplicate_heavy_spec)
        assert result is not None

        # With unified system, we extract nested objects but keep primitive properties inline:
        # - 200 original object schemas (SimilarSchema0-199)
        # - 200 metadata object schemas (nested objects extracted)
        # - Primitive properties (id, name, description, unique_field_X) remain inline
        # Total: ~400 schemas
        expected_min_schemas = 200 * 2  # Main schemas + nested metadata objects
        expected_max_schemas = 200 * 3  # Allow some additional extraction
        assert (
            len(result.schemas) >= expected_min_schemas
        ), f"Expected at least {expected_min_schemas}, got {len(result.schemas)}"
        assert (
            len(result.schemas) <= expected_max_schemas
        ), f"Expected at most {expected_max_schemas}, got {len(result.schemas)}"

    def test_processing_time_with_complex_references(self) -> None:
        """Test processing time with complex reference patterns."""
        import time

        complex_ref_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Complex Reference API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }

        # Create a web of interconnected references
        schema_count = 100
        for i in range(schema_count):
            schema = {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}}

            # Add references to other schemas
            for j in range(min(5, schema_count)):  # Reference up to 5 other schemas
                ref_target = (i + j + 1) % schema_count
                schema["properties"][f"ref_{j}"] = {"$ref": f"#/components/schemas/RefSchema{ref_target}"}

            complex_ref_spec["components"]["schemas"][f"RefSchema{i}"] = schema

        start_time = time.time()
        result = load_ir_from_spec(complex_ref_spec)
        end_time = time.time()

        processing_time = end_time - start_time
        assert processing_time < 10.0, f"Processing took {processing_time:.2f}s, should be under 10s"
        assert result is not None

        # After refactoring, inline properties are extracted as separate schemas:
        # - 100 original object schemas
        # - Shared property schemas (id, name)
        # - Additional schemas from complex references
        # The exact count depends on how many properties get extracted
        expected_min_schemas = schema_count  # At least the original schemas
        assert len(result.schemas) >= expected_min_schemas


class TestCodeGenerationIntegrationEdgeCases:
    """Test edge cases in complete code generation pipeline."""

    def test_full_client_generation_with_edge_cases(self) -> None:
        """Test complete client generation with various edge cases."""
        edge_case_api_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Edge Case Complete API", "version": "1.0.0"},
            "paths": {
                "/users/{user-id}": {  # Hyphenated parameter
                    "get": {
                        "operationId": "getUser",
                        "parameters": [
                            {"name": "user-id", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {
                            "200": {
                                "description": "User found",
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}},
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "required": ["id", "name"],
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "preferences": {"$ref": "#/components/schemas/UserPreferences"},
                        },
                    },
                    "UserPreferences": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string", "enum": ["light", "dark", "auto"]},
                            "notifications": {"type": "boolean"},
                            "user_ref": {"$ref": "#/components/schemas/User"},  # Circular reference
                        },
                    },
                }
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Write spec to temporary file
            import json

            spec_file = Path(temp_dir) / "test_spec.json"
            with open(spec_file, "w") as f:
                json.dump(edge_case_api_spec, f)

            # Should generate complete client without errors
            generator = ClientGenerator(verbose=False)
            generator.generate(spec_path=str(spec_file), project_root=Path(temp_dir), output_package="edge_case_client")

            # Verify basic structure was created
            client_dir = Path(temp_dir) / "edge_case_client"
            assert client_dir.exists()

            models_dir = client_dir / "models"
            if models_dir.exists():
                model_files = list(models_dir.glob("*.py"))
                assert len(model_files) >= 2  # User and UserPreferences

    def test_import_resolution_with_name_collisions(self) -> None:
        """Test import resolution when there are name collisions."""
        collision_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Import Collision API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "Type": {"type": "string"},  # Conflicts with Python 'type'
                    "List": {"type": "string"},  # Conflicts with Python 'list'
                    "Dict": {"type": "string"},  # Conflicts with Python 'dict'
                    "String": {"type": "string"},  # Conflicts with Python 'str'
                    "Model": {
                        "type": "object",
                        "properties": {
                            "type_field": {"$ref": "#/components/schemas/Type"},
                            "list_field": {"$ref": "#/components/schemas/List"},
                            "dict_field": {"$ref": "#/components/schemas/Dict"},
                            "string_field": {"$ref": "#/components/schemas/String"},
                        },
                    },
                }
            },
        }

        result = load_ir_from_spec(collision_spec)
        assert result is not None

        with tempfile.TemporaryDirectory() as temp_dir:
            context = RenderContext(
                overall_project_root=temp_dir, package_root_for_generated_code=temp_dir, core_package_name="test_core"
            )

            emitter = ModelsEmitter(context=context, parsed_schemas=result.schemas)
            emitter.emit(result, temp_dir)

            # Should generate files with properly resolved imports
            models_dir = Path(temp_dir) / "models"
            if models_dir.exists():
                model_files = list(models_dir.glob("*.py"))
                assert len(model_files) >= 5  # All schemas should generate files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
