"""
Tests for array item schema parsing to ensure item schemas are not incorrectly marked as self-referencing.

This test suite verifies that when parsing array type aliases (e.g., AgentListResponse = List[AgentListResponseItem]),
the item schema (AgentListResponseItem) is properly parsed with all its properties intact, not marked as self-referencing.
"""

from pyopenapi_gen.core.loader.loader import SpecLoader


class TestArrayItemSchemaParsing:
    """Test array item schemas are parsed correctly without false positive self-reference detection."""

    def test_array_type_alias_item_schema__simple_properties__parses_all_properties(self):
        """
        Scenario: OpenAPI spec has AgentListResponse (array) referencing AgentListResponseItem (object with properties).
        Expected Outcome: AgentListResponseItem is parsed with all properties, NOT marked as self-referencing.
        """
        # Arrange
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/agents": {
                    "get": {
                        "operationId": "listAgents",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {"schema": {"$ref": "#/components/schemas/AgentListResponse"}}
                                },
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "AgentListResponse": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/AgentListResponseItem"},
                        "description": "List of agents",
                    },
                    "AgentListResponseItem": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "createdAt": {"type": "string", "format": "date-time"},
                        },
                        "required": ["id", "name", "createdAt"],
                    },
                }
            },
        }

        # Act
        loader = SpecLoader(spec_dict)
        ir_spec = loader.load_ir()

        # Assert
        # Check that AgentListResponseItem schema was parsed
        assert "AgentListResponseItem" in ir_spec.schemas

        item_schema = ir_spec.schemas["AgentListResponseItem"]

        # Should NOT be marked as self-referencing
        assert not getattr(
            item_schema, "_is_self_referential_stub", False
        ), "AgentListResponseItem should not be marked as self-referential stub"

        # Should NOT have self-referencing marker in description
        assert "Self-referencing schema" not in (
            item_schema.description or ""
        ), "Description should not contain 'Self-referencing schema'"

        # Should have all 3 properties
        assert item_schema.properties is not None, "Properties should not be None"
        assert len(item_schema.properties) == 3, f"Expected 3 properties, got {len(item_schema.properties)}"

        # Verify specific properties exist
        assert "id_" in item_schema.properties or "id" in item_schema.properties, "Should have 'id' property"
        assert "name" in item_schema.properties, "Should have 'name' property"
        assert (
            "created_at" in item_schema.properties or "createdAt" in item_schema.properties
        ), "Should have 'createdAt' property"

        # Should have type="object"
        assert item_schema.type == "object", f"Expected type='object', got '{item_schema.type}'"

    def test_array_type_alias_item_schema__complex_properties__parses_all_properties(self):
        """
        Scenario: Item schema has complex properties including nested objects and arrays.
        Expected Outcome: All properties are parsed correctly, not marked as self-referencing.
        """
        # Arrange
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/agents": {
                    "get": {
                        "operationId": "listAgents",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {"schema": {"$ref": "#/components/schemas/AgentListResponse"}}
                                },
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "AgentListResponse": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/AgentListResponseItem"},
                    },
                    "AgentListResponseItem": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "config": {"$ref": "#/components/schemas/AgentConfig"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["id", "name"],
                    },
                    "AgentConfig": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "string"},
                            "temperature": {"type": "number"},
                        },
                    },
                }
            },
        }

        # Act
        loader = SpecLoader(spec_dict)
        ir_spec = loader.load_ir()

        # Assert
        item_schema = ir_spec.schemas["AgentListResponseItem"]

        # Should NOT be marked as self-referencing
        assert not getattr(item_schema, "_is_self_referential_stub", False)

        # Should have all 4 properties
        assert item_schema.properties is not None
        assert len(item_schema.properties) >= 4, f"Expected at least 4 properties, got {len(item_schema.properties)}"

    def test_array_response_directly_in_response__parses_inline_item_schema(self):
        """
        Scenario: Response directly specifies array with inline item schema (no named type alias).
        Expected Outcome: Inline item schema is parsed correctly.
        """
        # Arrange
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "listUsers",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string"},
                                                    "email": {"type": "string"},
                                                },
                                                "required": ["id", "email"],
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
            "components": {"schemas": {}},
        }

        # Act
        loader = SpecLoader(spec_dict)
        ir_spec = loader.load_ir()

        # Assert
        # Check operation response
        list_users_op = next(op for op in ir_spec.operations if op.operation_id == "listUsers")
        response_200 = next(r for r in list_users_op.responses if r.status_code == "200")

        assert response_200.content is not None
        json_schema = response_200.content.get("application/json")
        assert json_schema is not None

        # Should be array type
        assert json_schema.type == "array"

        # Items should have properties (might be in _refers_to_schema for promoted inline objects)
        assert json_schema.items is not None

        # For promoted inline objects, properties are in _refers_to_schema
        actual_item_schema = (
            json_schema.items._refers_to_schema
            if hasattr(json_schema.items, "_refers_to_schema") and json_schema.items._refers_to_schema
            else json_schema.items
        )

        assert actual_item_schema.properties is not None
        assert len(actual_item_schema.properties) >= 2
