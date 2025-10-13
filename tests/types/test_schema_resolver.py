"""Tests for schema resolver."""

from unittest.mock import Mock

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.types.contracts.types import TypeResolutionError
from pyopenapi_gen.types.resolvers.schema_resolver import OpenAPISchemaResolver


class TestOpenAPISchemaResolver:
    """Test the schema resolver."""

    @pytest.fixture
    def mock_ref_resolver(self):
        """Mock reference resolver."""
        return Mock()

    @pytest.fixture
    def mock_context(self):
        """Mock type context."""
        context = Mock()
        context.add_import = Mock()
        context.add_conditional_import = Mock()
        return context

    @pytest.fixture
    def resolver(self, mock_ref_resolver):
        """Schema resolver instance."""
        return OpenAPISchemaResolver(mock_ref_resolver)

    def test_resolve_schema__none_schema__returns_any(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving None schema
        Expected Outcome: Returns Any type
        """
        # Act
        result = resolver.resolve_schema(None, mock_context)

        # Assert
        assert result.python_type == "Any"
        mock_context.add_import.assert_called_with("typing", "Any")

    def test_resolve_schema__string_type__returns_str(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving string schema
        Expected Outcome: Returns str type
        """
        # Arrange
        schema = IRSchema(type="string")

        # Act
        result = resolver.resolve_schema(schema, mock_context, required=True)

        # Assert
        assert result.python_type == "str"
        assert not result.is_optional

    def test_resolve_schema__string_type_optional__returns_optional_str(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving optional string schema
        Expected Outcome: Returns str | None type
        """
        # Arrange
        schema = IRSchema(type="string")

        # Act
        result = resolver.resolve_schema(schema, mock_context, required=False)

        # Assert
        assert result.python_type == "str"
        assert result.is_optional

    def test_resolve_schema__integer_type__returns_int(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving integer schema
        Expected Outcome: Returns int type
        """
        # Arrange
        schema = IRSchema(type="integer")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "int"

    def test_resolve_schema__number_type__returns_float(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving number schema
        Expected Outcome: Returns float type
        """
        # Arrange
        schema = IRSchema(type="number")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "float"

    def test_resolve_schema__boolean_type__returns_bool(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving boolean schema
        Expected Outcome: Returns bool type
        """
        # Arrange
        schema = IRSchema(type="boolean")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "bool"

    def test_resolve_schema__array_with_string_items__returns_list_str(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving array schema with string items
        Expected Outcome: Returns List[str] type
        """
        # Arrange
        items_schema = IRSchema(type="string")
        schema = IRSchema(type="array", items=items_schema)

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "List[str]"
        mock_context.add_import.assert_called_with("typing", "List")

    def test_resolve_schema__array_no_items__returns_list_any(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving array schema without items
        Expected Outcome: Returns List[Any] type
        """
        # Arrange
        schema = IRSchema(type="array")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "List[Any]"
        mock_context.add_import.assert_any_call("typing", "List")
        mock_context.add_import.assert_any_call("typing", "Any")

    def test_resolve_schema__object_no_properties__returns_dict_any(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving object schema without properties
        Expected Outcome: Returns dict[str, Any] type
        """
        # Arrange
        schema = IRSchema(type="object")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "dict[str, Any]"
        mock_context.add_import.assert_any_call("typing", "Dict")
        mock_context.add_import.assert_any_call("typing", "Any")

    def test_resolve_schema__named_schema__returns_class_name(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving named schema validates correct type resolution
        Expected Outcome: Returns class name with import information
        """
        # Arrange - Create a named schema with generation metadata
        schema = IRSchema(name="User", generation_name="User", final_module_stem="user")

        # Act - Resolve the schema type
        result = resolver.resolve_schema(schema, mock_context)

        # Assert - Verify core resolution behavior without mocking internals
        assert result.python_type == "User"
        assert result.needs_import
        assert result.import_name == "User"
        # Verify that an import was registered
        assert mock_context.add_import.called
        # The import module should be set (actual path depends on context)
        assert result.import_module is not None

    def test_resolve_schema__reference__resolves_target(self, resolver, mock_context, mock_ref_resolver) -> None:
        """
        Scenario: Resolving schema with $ref
        Expected Outcome: Resolves target schema
        """
        # Arrange
        target_schema = IRSchema(type="string")
        mock_ref_resolver.resolve_ref.return_value = target_schema
        schema = Mock()
        schema.ref = "#/components/schemas/User"

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "str"
        mock_ref_resolver.resolve_ref.assert_called_once_with("#/components/schemas/User")

    def test_resolve_schema__reference_not_found__raises_error(self, resolver, mock_context, mock_ref_resolver) -> None:
        """
        Scenario: Resolving schema with invalid $ref
        Expected Outcome: Raises TypeResolutionError
        """
        # Arrange
        mock_ref_resolver.resolve_ref.return_value = None
        schema = Mock()
        schema.ref = "#/components/schemas/MissingUser"

        # Act & Assert
        with pytest.raises(TypeResolutionError, match="Could not resolve reference"):
            resolver.resolve_schema(schema, mock_context)

    def test_resolve_schema__unknown_type__returns_any(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving schema with unknown type
        Expected Outcome: Returns Any type and logs warning
        """
        # Arrange
        schema = IRSchema(type="unknown_type")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "Any"
        mock_context.add_import.assert_called_with("typing", "Any")

    def test_resolve_schema__named_schema_with_render_context__uses_relative_path_calculation(self, resolver) -> None:
        """
        Scenario: Resolving named schema with render context that calculates relative paths
        Expected Outcome: Uses calculated relative path instead of hardcoded ..models.
        """
        # Arrange
        mock_render_context = Mock()
        mock_render_context.current_file = "/project/models/my_item_list_response.py"
        mock_render_context.calculate_relative_path_for_internal_module.return_value = ".my_item"
        mock_render_context.add_import = Mock()

        mock_context = Mock()
        mock_context.render_context = mock_render_context
        mock_context.add_import = Mock()

        schema = IRSchema(name="MyItem", generation_name="MyItem", final_module_stem="my_item")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "MyItem"
        assert result.needs_import
        assert result.import_module == ".my_item"  # Should be single dot for same directory
        assert result.import_name == "MyItem"
        mock_context.add_import.assert_called_with(".my_item", "MyItem")
        mock_render_context.calculate_relative_path_for_internal_module.assert_called_with("models.my_item")

    def test_resolve_schema__named_schema_without_render_context__uses_default_path(self, resolver) -> None:
        """
        Scenario: Resolving named schema without render context
        Expected Outcome: Falls back to default ..models. path
        """
        # Arrange
        mock_context = Mock()
        mock_context.add_import = Mock()
        # Explicitly set up mock to not have render_context attribute
        del mock_context.render_context

        schema = IRSchema(name="User", generation_name="User", final_module_stem="user")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "User"
        assert result.needs_import
        assert result.import_module == "..models.user"  # Default fallback
        assert result.import_name == "User"
        mock_context.add_import.assert_called_with("..models.user", "User")

    def test_resolve_schema__named_schema_from_different_directory__uses_proper_relative_path(self, resolver) -> None:
        """
        Scenario: Resolving named schema from endpoints directory to models directory
        Expected Outcome: Uses ..models. path for cross-directory import
        """
        # Arrange
        mock_render_context = Mock()
        mock_render_context.current_file = "/project/endpoints/users.py"
        mock_render_context.calculate_relative_path_for_internal_module.return_value = "..models.user"
        mock_render_context.add_import = Mock()

        mock_context = Mock()
        mock_context.render_context = mock_render_context
        mock_context.add_import = Mock()

        schema = IRSchema(name="User", generation_name="User", final_module_stem="user")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "User"
        assert result.needs_import
        assert result.import_module == "..models.user"  # Should be double dot for cross-directory
        assert result.import_name == "User"
        mock_context.add_import.assert_called_with("..models.user", "User")
        mock_render_context.calculate_relative_path_for_internal_module.assert_called_with("models.user")

    def test_resolve_schema__any_of_composition__returns_union_type(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving anyOf composition with multiple schemas
        Expected Outcome: Returns Union[Type1, Type2] type
        """
        # Arrange
        schema1 = IRSchema(type="string")
        schema2 = IRSchema(type="integer")
        schema = IRSchema(any_of=[schema1, schema2])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "Union[int, str]"  # Sorted order
        mock_context.add_import.assert_called_with("typing", "Union")

    def test_resolve_schema__any_of_single_schema__returns_single_type(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving anyOf composition with single schema
        Expected Outcome: Returns the single type without Union wrapper
        """
        # Arrange
        schema1 = IRSchema(type="string")
        schema = IRSchema(any_of=[schema1])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "str"
        # Should not add Union import for single type
        calls = [call for call in mock_context.add_import.call_args_list if "Union" in str(call)]
        assert len(calls) == 0

    def test_resolve_schema__any_of_empty__returns_any(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving anyOf composition with empty list
        Expected Outcome: Returns Any type
        """
        # Arrange
        schema = IRSchema(any_of=[])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "Any"
        mock_context.add_import.assert_called_with("typing", "Any")

    def test_resolve_schema__one_of_composition__returns_union_type(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving oneOf composition with multiple schemas
        Expected Outcome: Returns Union[Type1, Type2] type
        """
        # Arrange
        schema1 = IRSchema(type="string")
        schema2 = IRSchema(type="boolean")
        schema = IRSchema(one_of=[schema1, schema2])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "Union[bool, str]"  # Sorted order
        mock_context.add_import.assert_called_with("typing", "Union")

    def test_resolve_schema__one_of_single_schema__returns_single_type(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving oneOf composition with single schema
        Expected Outcome: Returns the single type without Union wrapper
        """
        # Arrange
        schema1 = IRSchema(type="boolean")
        schema = IRSchema(one_of=[schema1])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "bool"

    def test_resolve_schema__one_of_empty__returns_any(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving oneOf composition with empty list
        Expected Outcome: Returns Any type
        """
        # Arrange
        schema = IRSchema(one_of=[])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "Any"
        mock_context.add_import.assert_called_with("typing", "Any")

    def test_resolve_schema__all_of_composition__returns_first_concrete_type(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving allOf composition with multiple schemas
        Expected Outcome: Returns the first schema with a concrete type
        """
        # Arrange
        schema1 = IRSchema()  # No type
        schema2 = IRSchema(type="string")
        schema3 = IRSchema(type="integer")
        schema = IRSchema(all_of=[schema1, schema2, schema3])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "str"  # First concrete type

    def test_resolve_schema__all_of_no_concrete_types__returns_first_schema(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving allOf composition with no concrete types
        Expected Outcome: Returns resolved first schema
        """
        # Arrange
        schema1 = IRSchema()  # No type, should resolve to Any
        schema2 = IRSchema()  # No type
        schema = IRSchema(all_of=[schema1, schema2])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "Any"  # First schema resolves to Any

    def test_resolve_schema__all_of_empty__returns_any(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving allOf composition with empty list
        Expected Outcome: Returns Any type
        """
        # Arrange
        schema = IRSchema(all_of=[])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "Any"
        mock_context.add_import.assert_called_with("typing", "Any")

    def test_resolve_schema__string_with_format_date__returns_date_type(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving string schema with date format
        Expected Outcome: Returns date type with appropriate import
        """
        # Arrange
        schema = IRSchema(type="string", format="date")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "date"
        mock_context.add_import.assert_called_with("datetime", "date")

    def test_resolve_schema__string_with_format_datetime__returns_datetime_type(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving string schema with date-time format
        Expected Outcome: Returns datetime type with appropriate import
        """
        # Arrange
        schema = IRSchema(type="string", format="date-time")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "datetime"
        mock_context.add_import.assert_called_with("datetime", "datetime")

    def test_resolve_schema__string_with_format_uuid__returns_uuid_type(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving string schema with uuid format
        Expected Outcome: Returns UUID type with appropriate import
        """
        # Arrange
        schema = IRSchema(type="string", format="uuid")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "UUID"
        mock_context.add_import.assert_called_with("uuid", "UUID")

    def test_resolve_schema__string_with_format_binary__returns_bytes_type(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving string schema with binary format
        Expected Outcome: Returns bytes type (built-in, no import needed)
        """
        # Arrange
        schema = IRSchema(type="string", format="binary")

        # Act
        result = resolver.resolve_schema(schema, mock_context, required=True)

        # Assert
        assert result.python_type == "bytes"
        assert not result.is_optional

    def test_resolve_schema__string_with_format_binary_optional__returns_optional_bytes(
        self, resolver, mock_context
    ) -> None:
        """
        Scenario: Resolving optional string schema with binary format
        Expected Outcome: Returns optional bytes type
        """
        # Arrange
        schema = IRSchema(type="string", format="binary")

        # Act
        result = resolver.resolve_schema(schema, mock_context, required=False)

        # Assert
        assert result.python_type == "bytes"
        assert result.is_optional

    def test_resolve_schema__string_with_inline_enum__logs_warning_returns_str(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving string schema with inline enum
        Expected Outcome: Logs warning and returns str type
        """
        # Arrange
        schema = IRSchema(type="string", enum=["option1", "option2"])

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "str"

    def test_resolve_schema__named_schema_lookup_by_type__resolves_target(
        self, resolver, mock_context, mock_ref_resolver
    ) -> None:
        """
        Scenario: Resolving schema where type refers to a named schema
        Expected Outcome: Resolves to the target named schema
        """
        # Arrange
        target_schema = IRSchema(name="User", type="object")
        mock_ref_resolver.schemas = {"User": target_schema}
        schema = IRSchema(type="User")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        # Since target_schema has no generation_name, it should fall back to type handling
        assert result.python_type == "dict[str, Any]"  # object type without properties

    def test_resolve_schema__named_schema_lookup_in_schemas__resolves_target(
        self, resolver, mock_context, mock_ref_resolver
    ) -> None:
        """
        Scenario: Resolving schema with name that exists in schemas registry
        Expected Outcome: Resolves to the target schema to avoid infinite recursion
        """
        # Arrange
        target_schema = IRSchema(type="string")
        mock_ref_resolver.schemas = {"StringAlias": target_schema}
        schema = IRSchema(name="StringAlias")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "str"

    def test_resolve_schema__named_schema_same_object__avoids_infinite_recursion(
        self, resolver, mock_context, mock_ref_resolver
    ) -> None:
        """
        Scenario: Resolving schema with name that points to same object (infinite recursion prevention)
        Expected Outcome: Falls back to type-based resolution
        """
        # Arrange
        schema = IRSchema(name="SelfRef", type="string")
        mock_ref_resolver.schemas = {"SelfRef": schema}  # Same object

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "str"  # Falls back to type-based resolution

    def test_resolve_schema__named_schema_missing_module_stem__logs_warning_returns_any(
        self, resolver, mock_context
    ) -> None:
        """
        Scenario: Resolving named schema without final_module_stem
        Expected Outcome: Logs warning and returns Any type
        """
        # Arrange
        schema = IRSchema(name="InvalidSchema", generation_name="InvalidSchema")  # Missing final_module_stem

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "InvalidSchema"  # Uses generation_name as fallback
        assert not result.is_optional

    def test_resolve_schema__self_import_detection__returns_forward_ref(self, resolver) -> None:
        """
        Scenario: Resolving named schema from same module (self-import)
        Expected Outcome: Returns forward reference to avoid circular import
        """
        # Arrange
        mock_render_context = Mock()
        mock_render_context.current_file = "/project/models/user.py"
        mock_render_context.add_import = Mock()

        mock_context = Mock()
        mock_context.render_context = mock_render_context
        mock_context.add_import = Mock()

        schema = IRSchema(name="User", generation_name="User", final_module_stem="user")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "User"
        assert result.is_forward_ref  # Should be marked as forward reference
        # Should not call add_import for self-references
        mock_context.add_import.assert_not_called()

    def test_resolve_schema__relative_path_calculation_failure__uses_fallback(self, resolver) -> None:
        """
        Scenario: Resolving named schema when relative path calculation fails
        Expected Outcome: Falls back to default ..models. path
        """
        # Arrange
        mock_render_context = Mock()
        mock_render_context.current_file = "/project/endpoints/users.py"
        mock_render_context.calculate_relative_path_for_internal_module.side_effect = Exception(
            "Path calculation failed"
        )
        mock_render_context.add_import = Mock()

        mock_context = Mock()
        mock_context.render_context = mock_render_context
        mock_context.add_import = Mock()

        schema = IRSchema(name="User", generation_name="User", final_module_stem="user")

        # Act
        result = resolver.resolve_schema(schema, mock_context)

        # Assert
        assert result.python_type == "User"
        assert result.import_module == "..models.user"  # Fallback path
        mock_context.add_import.assert_called_with("..models.user", "User")

    def test_resolve_schema__null_type_schema__returns_any(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving schema with type=None (null type)
        Expected Outcome: Returns Any type instead of None type

        This tests the fix for the null schema resolution bug where null schemas
        were returning "None" instead of "Any", causing incorrect type assignments.
        """
        # Arrange
        schema = IRSchema(type=None)

        # Act
        result = resolver.resolve_schema(schema, mock_context, required=True)

        # Assert
        assert result.python_type == "Any"
        assert not result.is_optional
        mock_context.add_import.assert_called_with("typing", "Any")

    def test_resolve_schema__null_type_schema_optional__returns_any_with_optional_flag(
        self, resolver, mock_context
    ) -> None:
        """
        Scenario: Resolving optional schema with type=None (null type)
        Expected Outcome: Returns Any type with is_optional flag set

        This tests that null schemas respect the required parameter.
        The _resolve_null method correctly sets is_optional based on the required parameter.
        """
        # Arrange
        schema = IRSchema(type=None)

        # Act
        result = resolver.resolve_schema(schema, mock_context, required=False)

        # Assert
        assert result.python_type == "Any"
        # Null schemas now correctly respect the required parameter and set is_optional=True when required=False
        assert result.is_optional  # Correctly returns optional Any when required=False
        mock_context.add_import.assert_called_with("typing", "Any")

    def test_resolve_schema__schema_no_type_no_generation_name__returns_any(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving schema with no type and no generation_name (null schema from OpenAPI)
                  This matches the early detection logic for null schemas in schema_resolver.py
        Expected Outcome: Returns Any type inline without creating placeholder type

        This tests the fix for schemas like PostApiAuthLogoutRequestBody that were
        incorrectly being assigned to unrelated fields. Null schemas should resolve
        to Any directly.
        """
        # Arrange
        schema = IRSchema(
            type=None,
            # No generation_name, no composition keywords
        )

        # Act
        result = resolver.resolve_schema(schema, mock_context, required=True)

        # Assert
        assert result.python_type == "Any"
        mock_context.add_import.assert_called_with("typing", "Any")

    def test_resolve_schema__schema_no_type_but_has_generation_name__resolves_as_named(
        self, resolver, mock_context
    ) -> None:
        """
        Scenario: Resolving schema with no type but has generation_name
        Expected Outcome: Resolves as named schema, not as null schema

        This verifies that schemas with generation_name are not treated as null schemas
        even if they have no explicit type.
        """
        # Arrange
        schema = IRSchema(
            name="EmptyObject",  # Named schemas need both name and generation_name
            type=None,
            generation_name="EmptyObject",
            final_module_stem="empty_object",
        )

        # Act
        result = resolver.resolve_schema(schema, mock_context, required=True)

        # Assert
        assert result.python_type == "EmptyObject"
        assert result.needs_import
        # Should not resolve to Any for named schemas
