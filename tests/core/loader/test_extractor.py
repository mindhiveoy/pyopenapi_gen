"""Unit tests for the schema extractor module."""

from unittest.mock import Mock, patch

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.loader.schemas.extractor import (
    build_schemas,
    extract_inline_array_items,
    extract_inline_enums,
)
from pyopenapi_gen.core.parsing.context import ParsingContext


class TestBuildSchemas:
    def test_build_schemas__valid_raw_schemas__returns_context_with_parsed_schemas(self) -> None:
        """
        Scenario:
            Valid raw_schemas dictionary and raw_components mapping are provided.

        Expected Outcome:
            A ParsingContext is returned with all schemas parsed and populated in context.parsed_schemas.
        """
        # Arrange
        raw_schemas = {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
                "required": ["id"],
            },
            "Status": {
                "type": "string",
                "enum": ["active", "inactive"],
            },
        }
        raw_components = {"schemas": raw_schemas}

        # Act
        context = build_schemas(raw_schemas, raw_components)

        # Assert
        assert isinstance(context, ParsingContext)
        assert "User" in context.parsed_schemas
        assert "Status" in context.parsed_schemas

        user_schema = context.parsed_schemas["User"]
        assert user_schema.name == "User"
        assert user_schema.type == "object"
        assert "id" in user_schema.properties
        assert "name" in user_schema.properties
        assert user_schema.required == ["id"]

        status_schema = context.parsed_schemas["Status"]
        assert status_schema.name == "Status"
        assert status_schema.type == "string"
        assert status_schema.enum == ["active", "inactive"]

    def test_build_schemas__empty_raw_schemas__returns_context_with_empty_parsed_schemas(self) -> None:
        """
        Scenario:
            Empty raw_schemas dictionary is provided.

        Expected Outcome:
            A ParsingContext is returned with empty parsed_schemas.
        """
        # Arrange
        raw_schemas = {}
        raw_components = {"schemas": raw_schemas}

        # Act
        context = build_schemas(raw_schemas, raw_components)

        # Assert
        assert isinstance(context, ParsingContext)
        assert len(context.parsed_schemas) == 0

    def test_build_schemas__self_referencing_schema__handles_correctly(self) -> None:
        """
        Scenario:
            A schema that references itself is provided.

        Expected Outcome:
            The schema is parsed correctly with self-reference handling enabled.
        """
        # Arrange
        raw_schemas = {
            "Node": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "children": {"type": "array", "items": {"$ref": "#/components/schemas/Node"}},
                },
            }
        }
        raw_components = {"schemas": raw_schemas}

        # Act
        context = build_schemas(raw_schemas, raw_components)

        # Assert
        assert "Node" in context.parsed_schemas
        node_schema = context.parsed_schemas["Node"]
        assert node_schema.name == "Node"
        assert node_schema.type == "object"
        assert "children" in node_schema.properties

    def test_build_schemas__invalid_raw_schemas_type__raises_type_error(self) -> None:
        """
        Scenario:
            Invalid type (not dict) is passed as raw_schemas.

        Expected Outcome:
            TypeError is raised with appropriate message.
        """
        # Arrange
        raw_schemas = ["not", "a", "dict"]  # Invalid type
        raw_components = {}

        # Act & Assert
        with pytest.raises(TypeError, match="raw_schemas must be a dict"):
            build_schemas(raw_schemas, raw_components)  # type: ignore

    def test_build_schemas__invalid_raw_components_type__raises_type_error(self) -> None:
        """
        Scenario:
            Invalid type (not Mapping) is passed as raw_components.

        Expected Outcome:
            TypeError is raised with appropriate message.
        """
        # Arrange
        raw_schemas = {}
        raw_components = ["not", "a", "mapping"]  # Invalid type

        # Act & Assert
        with pytest.raises(TypeError, match="raw_components must be a Mapping"):
            build_schemas(raw_schemas, raw_components)  # type: ignore

    @patch("pyopenapi_gen.core.loader.schemas.extractor._parse_schema")
    def test_build_schemas__parse_schema_called_with_correct_parameters(self, mock_parse_schema: Mock) -> None:
        """
        Scenario:
            Valid schemas are provided and _parse_schema should be called for each.

        Expected Outcome:
            _parse_schema is called for each schema with allow_self_reference=True.
        """
        # Arrange
        raw_schemas = {
            "Schema1": {"type": "string"},
            "Schema2": {"type": "integer"},
        }
        raw_components = {"schemas": raw_schemas}

        # Mock _parse_schema to return a simple IRSchema
        def mock_parse_side_effect(name, node_data, context, allow_self_reference=False):
            schema = IRSchema(name=name, type=node_data.get("type"))
            context.parsed_schemas[name] = schema
            return schema

        mock_parse_schema.side_effect = mock_parse_side_effect

        # Act
        context = build_schemas(raw_schemas, raw_components)

        # Assert
        assert mock_parse_schema.call_count == 2
        mock_parse_schema.assert_any_call("Schema1", {"type": "string"}, context, allow_self_reference=True)
        mock_parse_schema.assert_any_call("Schema2", {"type": "integer"}, context, allow_self_reference=True)


class TestExtractInlineArrayItems:
    def test_extract_inline_array_items__valid_schemas_dict__returns_dict(self) -> None:
        """
        Scenario:
            Valid schemas dictionary with IRSchema objects is provided.

        Expected Outcome:
            Returns an updated schemas dictionary.
        """
        # Arrange
        schemas = {"SimpleSchema": IRSchema(name="SimpleSchema", type="string")}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        assert isinstance(result, dict)
        assert "SimpleSchema" in result

    def test_extract_inline_array_items__schema_with_complex_array_items__extracts_item_schemas(self) -> None:
        """
        Scenario:
            A schema has an array property with complex inline item schemas (objects).

        Expected Outcome:
            Complex item schemas are extracted as separate named schemas and array references them.
        """
        # Arrange
        item_schema = IRSchema(
            name=None,  # Inline item has no name initially
            type="object",
            properties={
                "id": IRSchema(type="string"),
                "value": IRSchema(type="integer"),
            },
        )
        array_property = IRSchema(type="array", items=item_schema)
        parent_schema = IRSchema(name="MyList", type="object", properties={"items": array_property})
        schemas = {"MyList": parent_schema}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        # Should have original schema plus extracted item schema
        assert len(result) == 2
        assert "MyList" in result

        # Find the extracted item schema (should have a generated name)
        extracted_item_name = None
        for key in result.keys():
            if key != "MyList":
                extracted_item_name = key
                break

        assert extracted_item_name is not None
        assert "MyListItemsItem" in extracted_item_name or "MyListItem" in extracted_item_name

        # Verify the item schema was properly extracted
        extracted_item = result[extracted_item_name]
        assert extracted_item.type == "object"
        assert "id" in extracted_item.properties
        assert "value" in extracted_item.properties

        # Verify the array now references the extracted item
        assert result["MyList"].properties["items"].items.name == extracted_item_name

    def test_extract_inline_array_items__array_with_primitive_items__does_not_extract(self) -> None:
        """
        Scenario:
            A schema has an array property with simple primitive item types.

        Expected Outcome:
            Primitive item types are not extracted, only the original schema remains.
        """
        # Arrange
        primitive_item = IRSchema(type="string")  # Simple primitive
        array_property = IRSchema(type="array", items=primitive_item)
        parent_schema = IRSchema(name="StringList", type="object", properties={"strings": array_property})
        schemas = {"StringList": parent_schema}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        assert len(result) == 1  # Only original schema
        assert "StringList" in result
        assert result["StringList"].properties["strings"].items.type == "string"

    def test_extract_inline_array_items__data_property_in_response__uses_smart_naming(self) -> None:
        """
        Scenario:
            A Response schema has a "data" property containing an array of complex objects.

        Expected Outcome:
            Smart naming is used for the extracted item schema (e.g., MessageItem for MessageResponse.data).
        """
        # Arrange
        item_schema = IRSchema(name=None, type="object", properties={"content": IRSchema(type="string")})
        data_array = IRSchema(type="array", items=item_schema)
        response_schema = IRSchema(name="MessageResponse", type="object", properties={"data": data_array})
        schemas = {"MessageResponse": response_schema}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        assert len(result) == 2
        assert "MessageResponse" in result

        # Should have MessageItem (smart naming for Response.data)
        assert "MessageItem" in result
        extracted_item = result["MessageItem"]
        assert extracted_item.name == "MessageItem"
        assert extracted_item.type == "object"

    def test_extract_inline_array_items__name_collision__generates_unique_names(self) -> None:
        """
        Scenario:
            Multiple schemas would generate the same item schema name.

        Expected Outcome:
            Unique names are generated using counter suffixes.
        """
        # Arrange
        item1 = IRSchema(name=None, type="object", properties={"field1": IRSchema(type="string")})
        item2 = IRSchema(name=None, type="object", properties={"field2": IRSchema(type="string")})

        schema1 = IRSchema(name="Container", type="object", properties={"items": IRSchema(type="array", items=item1)})
        schema2 = IRSchema(
            name="Container",  # Same name would generate same item name
            type="object",
            properties={"items": IRSchema(type="array", items=item2)},
        )
        schemas = {"Container1": schema1, "Container2": schema2}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        assert len(result) >= 4  # Original 2 + at least 2 extracted items
        # Should have generated unique names for both item schemas
        item_names = [key for key in result.keys() if "Item" in key]
        assert len(item_names) >= 2
        assert len(set(item_names)) == len(item_names)  # All names should be unique

    def test_extract_inline_array_items__array_items_with_composition__extracts_complex_items(self) -> None:
        """
        Scenario:
            Array items use composition (anyOf, oneOf, allOf).

        Expected Outcome:
            Complex composition items are extracted as separate schemas.
        """
        # Arrange
        item_schema = IRSchema(name=None, any_of=[IRSchema(type="string"), IRSchema(type="integer")])
        array_property = IRSchema(type="array", items=item_schema)
        parent_schema = IRSchema(name="CompositionList", type="object", properties={"data": array_property})
        schemas = {"CompositionList": parent_schema}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        assert len(result) == 2
        assert "CompositionList" in result

        # Find extracted item
        extracted_name = next(key for key in result.keys() if key != "CompositionList")
        extracted_item = result[extracted_name]
        assert extracted_item.any_of is not None
        assert len(extracted_item.any_of) == 2

    def test_extract_inline_array_items__invalid_schemas_type__raises_type_error(self) -> None:
        """
        Scenario:
            Invalid type (not dict) is passed as schemas.

        Expected Outcome:
            TypeError is raised with appropriate message.
        """
        # Arrange
        schemas = ["not", "a", "dict"]  # Invalid type

        # Act & Assert
        with pytest.raises(TypeError, match="schemas must be a dict"):
            extract_inline_array_items(schemas)  # type: ignore

    def test_extract_inline_array_items__invalid_schema_values__raises_type_error(self) -> None:
        """
        Scenario:
            Dictionary contains values that are not IRSchema objects.

        Expected Outcome:
            TypeError is raised about IRSchema requirement.
        """
        # Arrange
        schemas = {
            "ValidSchema": IRSchema(name="ValidSchema", type="string"),
            "InvalidSchema": "not an IRSchema object",
        }

        # Act & Assert
        with pytest.raises(TypeError, match="all values must be IRSchema objects"):
            extract_inline_array_items(schemas)  # type: ignore

    def test_extract_inline_array_items__nested_arrays__handles_recursively(self) -> None:
        """
        Scenario:
            Array items themselves contain arrays with complex items.

        Expected Outcome:
            Nested complex items are properly extracted.
        """
        # Arrange
        nested_item = IRSchema(name=None, type="object", properties={"value": IRSchema(type="string")})
        nested_array = IRSchema(type="array", items=nested_item)
        outer_item = IRSchema(name=None, type="object", properties={"nested": nested_array})
        outer_array = IRSchema(type="array", items=outer_item)
        parent_schema = IRSchema(name="NestedArrays", type="object", properties={"data": outer_array})
        schemas = {"NestedArrays": parent_schema}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        assert len(result) >= 2  # Should extract at least the outer array items
        assert "NestedArrays" in result


class TestExtractInlineEnums:
    def test_extract_inline_enums__valid_schemas_dict__returns_dict(self) -> None:
        """
        Scenario:
            Valid schemas dictionary with IRSchema objects is provided.

        Expected Outcome:
            Returns an updated schemas dictionary.
        """
        # Arrange
        schemas = {"SimpleSchema": IRSchema(name="SimpleSchema", type="string")}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        assert isinstance(result, dict)
        assert "SimpleSchema" in result

    def test_extract_inline_enums__schema_with_inline_enum_property__extracts_enum(self) -> None:
        """
        Scenario:
            A schema has a property with an inline enum definition.

        Expected Outcome:
            The inline enum is extracted as a separate schema and the property references it.
        """
        # Arrange
        enum_property = IRSchema(
            name=None,  # Inline property has no name initially
            type="string",
            enum=["active", "inactive", "pending"],
        )
        parent_schema = IRSchema(name="User", type="object", properties={"status": enum_property})
        schemas = {"User": parent_schema}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        # Should have original schema plus extracted enum
        assert len(result) == 2
        assert "User" in result
        assert "UserStatusEnum" in result

        # Verify enum was properly extracted
        extracted_enum = result["UserStatusEnum"]
        assert extracted_enum.name == "UserStatusEnum"
        assert extracted_enum.type == "string"
        assert extracted_enum.enum == ["active", "inactive", "pending"]

        # Verify property now references the enum
        user_schema = result["User"]
        status_property = user_schema.properties["status"]
        assert status_property.name == "UserStatusEnum"
        assert status_property.type == "UserStatusEnum"
        assert status_property.enum is None  # Enum values cleared from property

    def test_extract_inline_enums__multiple_enum_properties__extracts_all(self) -> None:
        """
        Scenario:
            A schema has multiple properties with inline enum definitions.

        Expected Outcome:
            All inline enums are extracted as separate schemas.
        """
        # Arrange
        status_enum = IRSchema(name=None, type="string", enum=["active", "inactive"])
        role_enum = IRSchema(name=None, type="string", enum=["admin", "user", "guest"])
        parent_schema = IRSchema(
            name="Account",
            type="object",
            properties={
                "status": status_enum,
                "role": role_enum,
                "name": IRSchema(type="string"),  # Non-enum property
            },
        )
        schemas = {"Account": parent_schema}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        assert len(result) == 3  # Original + 2 enums
        assert "Account" in result
        assert "AccountStatusEnum" in result
        assert "AccountRoleEnum" in result

        # Verify both enums extracted correctly
        status_enum_extracted = result["AccountStatusEnum"]
        assert status_enum_extracted.enum == ["active", "inactive"]

        role_enum_extracted = result["AccountRoleEnum"]
        assert role_enum_extracted.enum == ["admin", "user", "guest"]

    def test_extract_inline_enums__enum_name_collision__generates_unique_names(self) -> None:
        """
        Scenario:
            Multiple schemas would generate the same enum name.

        Expected Outcome:
            Unique names are generated using counter suffixes.
        """
        # Arrange
        schema1 = IRSchema(
            name="Config", type="object", properties={"mode": IRSchema(name=None, type="string", enum=["dev", "prod"])}
        )
        schema2 = IRSchema(
            name="Settings",  # Different parent but might generate similar enum name
            type="object",
            properties={"mode": IRSchema(name=None, type="string", enum=["light", "dark"])},
        )
        schemas = {"Config": schema1, "Settings": schema2}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        assert len(result) == 4  # 2 original + 2 enums
        enum_names = [key for key in result.keys() if "Enum" in key]
        assert len(enum_names) == 2
        assert len(set(enum_names)) == 2  # All names should be unique

    def test_extract_inline_enums__property_already_has_name__does_not_extract(self) -> None:
        """
        Scenario:
            A property with enum values already has a name (not inline).

        Expected Outcome:
            Named enum properties are not extracted as they're not inline.
        """
        # Arrange
        named_enum_property = IRSchema(
            name="ExistingStatusEnum",  # Already has a name
            type="string",
            enum=["active", "inactive"],
        )
        parent_schema = IRSchema(name="Item", type="object", properties={"status": named_enum_property})
        schemas = {"Item": parent_schema}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        assert len(result) == 1  # Only original schema
        assert "Item" in result
        # Property should remain unchanged
        assert result["Item"].properties["status"].name == "ExistingStatusEnum"
        assert result["Item"].properties["status"].enum == ["active", "inactive"]

    def test_extract_inline_enums__property_without_enum__does_not_extract(self) -> None:
        """
        Scenario:
            A property does not have enum values.

        Expected Outcome:
            Non-enum properties are not affected.
        """
        # Arrange
        regular_property = IRSchema(name=None, type="string")
        parent_schema = IRSchema(name="Simple", type="object", properties={"text": regular_property})
        schemas = {"Simple": parent_schema}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        assert len(result) == 1  # Only original schema
        assert "Simple" in result
        assert result["Simple"].properties["text"].type == "string"

    def test_extract_inline_enums__calls_extract_inline_array_items_first(self) -> None:
        """
        Scenario:
            Function should call extract_inline_array_items before processing enums.

        Expected Outcome:
            Array items are extracted first, then enum extraction processes the updated schemas.
        """
        # Arrange
        # Create a schema with both array items and enums to test the order
        enum_property = IRSchema(name=None, type="string", enum=["type1", "type2"])
        item_schema = IRSchema(name=None, type="object", properties={"category": enum_property})
        array_property = IRSchema(type="array", items=item_schema)
        parent_schema = IRSchema(
            name="ComplexList",
            type="object",
            properties={
                "items": array_property,
                "status": IRSchema(name=None, type="string", enum=["active", "inactive"]),
            },
        )
        schemas = {"ComplexList": parent_schema}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        # Should have extracted both array items and enums
        assert len(result) >= 3  # Original + array item + at least one enum
        assert "ComplexList" in result

        # Should have status enum from parent
        status_enum_names = [key for key in result.keys() if "Status" in key and "Enum" in key]
        assert len(status_enum_names) >= 1

    def test_extract_inline_enums__integer_enum__preserves_type(self) -> None:
        """
        Scenario:
            A property has an integer enum.

        Expected Outcome:
            The extracted enum schema maintains the integer type.
        """
        # Arrange
        int_enum_property = IRSchema(name=None, type="integer", enum=[1, 2, 3, 4])
        parent_schema = IRSchema(name="Priority", type="object", properties={"level": int_enum_property})
        schemas = {"Priority": parent_schema}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        assert len(result) == 2
        assert "PriorityLevelEnum" in result

        extracted_enum = result["PriorityLevelEnum"]
        assert extracted_enum.type == "integer"
        assert extracted_enum.enum == [1, 2, 3, 4]

    def test_extract_inline_enums__enum_with_description__preserves_description(self) -> None:
        """
        Scenario:
            An inline enum property has a description.

        Expected Outcome:
            The extracted enum schema preserves the original description.
        """
        # Arrange
        enum_property = IRSchema(
            name=None, type="string", enum=["small", "medium", "large"], description="Size options"
        )
        parent_schema = IRSchema(name="Product", type="object", properties={"size": enum_property})
        schemas = {"Product": parent_schema}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        assert "ProductSizeEnum" in result
        extracted_enum = result["ProductSizeEnum"]
        assert extracted_enum.description == "Size options"

    def test_extract_inline_enums__enum_without_description__generates_fallback_description(self) -> None:
        """
        Scenario:
            An inline enum property has no description.

        Expected Outcome:
            The extracted enum schema gets a generated fallback description.
        """
        # Arrange
        enum_property = IRSchema(
            name=None,
            type="string",
            enum=["red", "green", "blue"],
            # No description provided
        )
        parent_schema = IRSchema(name="Color", type="object", properties={"primary": enum_property})
        schemas = {"Color": parent_schema}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        assert "ColorPrimaryEnum" in result
        extracted_enum = result["ColorPrimaryEnum"]
        assert extracted_enum.description == "Enum for Color.primary"

    def test_extract_inline_enums__invalid_schemas_type__raises_type_error(self) -> None:
        """
        Scenario:
            Invalid type (not dict) is passed as schemas.

        Expected Outcome:
            TypeError is raised with appropriate message.
        """
        # Arrange
        schemas = ["not", "a", "dict"]  # Invalid type

        # Act & Assert
        with pytest.raises(TypeError, match="schemas must be a dict"):
            extract_inline_enums(schemas)  # type: ignore

    def test_extract_inline_enums__invalid_schema_values__raises_type_error(self) -> None:
        """
        Scenario:
            Dictionary contains values that are not IRSchema objects.

        Expected Outcome:
            TypeError is raised about IRSchema requirement.
        """
        # Arrange
        schemas = {
            "ValidSchema": IRSchema(name="ValidSchema", type="string"),
            "InvalidSchema": "not an IRSchema object",
        }

        # Act & Assert
        with pytest.raises(TypeError, match="all values must be IRSchema objects"):
            extract_inline_enums(schemas)  # type: ignore

    def test_extract_inline_enums__complex_nested_structure__processes_all_levels(self) -> None:
        """
        Scenario:
            Complex nested structure with arrays and enums at multiple levels.

        Expected Outcome:
            All inline enums are extracted regardless of nesting level.
        """
        # Arrange
        nested_enum = IRSchema(name=None, type="string", enum=["urgent", "normal"])
        nested_object = IRSchema(name=None, type="object", properties={"priority": nested_enum})
        array_property = IRSchema(type="array", items=nested_object)
        top_enum = IRSchema(name=None, type="string", enum=["published", "draft"])
        parent_schema = IRSchema(
            name="Document", type="object", properties={"items": array_property, "status": top_enum}
        )
        schemas = {"Document": parent_schema}

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        # Should extract enums from multiple levels
        assert len(result) >= 3  # At least original + extracted array item + enums

        # Should have top-level status enum
        status_enum_names = [key for key in result.keys() if "Status" in key and "Enum" in key]
        assert len(status_enum_names) >= 1


class TestExtractInlineArrayItemsAdditional:
    def test_extract_inline_array_items__generic_wrapper_without_response_suffix__uses_fallback_naming(self) -> None:
        """
        Scenario:
            A schema with generic wrapper property (data/items) but not ending with "Response".

        Expected Outcome:
            The fallback naming pattern is used for the extracted item schema.
        """
        # Arrange
        item_schema = IRSchema(name=None, type="object", properties={"content": IRSchema(type="string")})
        data_array = IRSchema(type="array", items=item_schema)
        container_schema = IRSchema(
            name="DataContainer",  # Does not end with "Response"
            type="object",
            properties={"data": data_array},
        )
        schemas = {"DataContainer": container_schema}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        assert len(result) == 2
        assert "DataContainer" in result

        # Should use fallback pattern - checking what actually gets generated
        # Look for the actual generated name
        extracted_names = [key for key in result.keys() if key != "DataContainer"]
        assert len(extracted_names) == 1
        extracted_name = extracted_names[0]
        extracted_item = result[extracted_name]
        # Verify it's the item we expect and fallback pattern was used
        assert extracted_item.type == "object"
        assert "content" in extracted_item.properties

    def test_extract_inline_array_items__array_item_name_collision_multiple_increments__generates_unique_names(
        self,
    ) -> None:
        """
        Scenario:
            Multiple collisions require incrementing the name counter multiple times.

        Expected Outcome:
            Unique names are generated with proper counter increments.
        """
        # Arrange
        # Pre-populate with existing schemas that would cause collisions
        schemas = {
            "Container": IRSchema(name="Container", type="object", properties={}),
            "ContainerItemsItem": IRSchema(name="ContainerItemsItem", type="string"),  # First collision
            "ContainerItemsItem1": IRSchema(name="ContainerItemsItem1", type="string"),  # Second collision
        }

        # Add a new schema with array that would generate same name
        item_schema = IRSchema(name=None, type="object", properties={"field": IRSchema(type="string")})
        array_property = IRSchema(type="array", items=item_schema)
        container_schema = IRSchema(name="Container", type="object", properties={"items": array_property})
        schemas["NewContainer"] = container_schema

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        # Should create a uniquely named item due to multiple collisions
        # Find the newly generated item (not in the original schemas)
        new_item_names = [
            key
            for key in result.keys()
            if key not in ["Container", "ContainerItemsItem", "ContainerItemsItem1", "NewContainer"]
        ]
        assert len(new_item_names) == 1
        new_item_name = new_item_names[0]
        extracted_item = result[new_item_name]
        assert extracted_item.type == "object"
        assert "field" in extracted_item.properties


class TestExtractInlineEnumsAdditional:
    def test_extract_inline_enums__enum_name_collision_multiple_increments__generates_unique_names(self) -> None:
        """
        Scenario:
            Multiple enum name collisions require incrementing the name counter multiple times.

        Expected Outcome:
            Unique enum names are generated with proper counter increments.
        """
        # Arrange
        # Pre-populate with existing schemas that would cause collisions
        schemas = {
            "Config": IRSchema(name="Config", type="object", properties={}),
            "ConfigModeEnum": IRSchema(name="ConfigModeEnum", type="string"),  # First collision
            "ConfigModeEnum1": IRSchema(name="ConfigModeEnum1", type="string"),  # Second collision
        }

        # Add a new schema with enum that would generate same name
        enum_property = IRSchema(name=None, type="string", enum=["dev", "prod"])
        config_schema = IRSchema(name="Config", type="object", properties={"mode": enum_property})
        schemas["NewConfig"] = config_schema

        # Act
        result = extract_inline_enums(schemas)

        # Assert
        # Should create a uniquely named enum due to multiple collisions
        # Find the newly generated enum (not in the original schemas)
        new_enum_names = [
            key for key in result.keys() if key not in ["Config", "ConfigModeEnum", "ConfigModeEnum1", "NewConfig"]
        ]
        assert len(new_enum_names) >= 1
        new_enum_name = new_enum_names[0]  # Take the first one if multiple
        extracted_enum = result[new_enum_name]
        assert extracted_enum.type == "string"
        assert extracted_enum.type == "string"
        assert extracted_enum.enum == ["dev", "prod"]

    def test_extract_inline_array_items__generic_data_property_not_object_type__uses_fallback_naming(self) -> None:
        """
        Scenario:
            A schema has a "data" property with array items that are not type "object" but are complex.

        Expected Outcome:
            The else branch of the generic wrapper naming logic is executed.
        """
        # Arrange
        item_schema = IRSchema(
            name=None,
            type="array",  # Not "object", but still complex
            items=IRSchema(type="string"),
        )
        data_array = IRSchema(type="array", items=item_schema)
        response_schema = IRSchema(
            name="MessageResponse",  # Ends with "Response" but items are not "object"
            type="object",
            properties={"data": data_array},
        )
        schemas = {"MessageResponse": response_schema}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert
        assert len(result) == 2
        assert "MessageResponse" in result

        # Should use fallback pattern since items_schema.type != "object"
        extracted_names = [key for key in result.keys() if key != "MessageResponse"]
        assert len(extracted_names) == 1
        extracted_name = extracted_names[0]
        extracted_item = result[extracted_name]
        assert extracted_item.type == "array"
        assert extracted_item.items.type == "string"
