"""Tests for helpers.type_resolution.named_resolver module."""

from unittest.mock import Mock

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.type_resolution.named_resolver import NamedTypeResolver


class TestNamedTypeResolver:
    """Test suite for NamedTypeResolver."""

    def setup_method(self):
        """Set up test fixtures."""
        self.context = Mock(spec=RenderContext)
        self.context.current_file = None
        self.context.get_current_package_name_for_generated_code.return_value = "myapi"

        self.all_schemas = {}
        self.resolver = NamedTypeResolver(self.context, self.all_schemas)

    def test_named_resolver__init__stores_dependencies(self):
        """Scenario: Initialize NamedTypeResolver.

        Expected Outcome: Dependencies are stored correctly.
        """
        # Assert
        assert self.resolver.context is self.context
        assert self.resolver.all_schemas is self.all_schemas

    def test_named_resolver__module_name_to_class_name__converts_snake_to_pascal(self):
        """Scenario: Convert snake_case module names to PascalCase class names.

        Expected Outcome: Correct PascalCase conversion.
        """
        # Act & Assert
        assert self.resolver._module_name_to_class_name("tree_node") == "TreeNode"
        assert self.resolver._module_name_to_class_name("message") == "Message"
        assert self.resolver._module_name_to_class_name("user_data") == "UserData"
        assert self.resolver._module_name_to_class_name("simple") == "Simple"
        assert self.resolver._module_name_to_class_name("multi_word_class_name") == "MultiWordClassName"

    def test_named_resolver__class_being_generated_matches__no_current_file__returns_false(self):
        """Scenario: Check class match when no current file is set.

        Expected Outcome: Returns False.
        """
        # Arrange
        self.context.current_file = None

        # Act
        result = self.resolver._class_being_generated_matches("SomeClass")

        # Assert
        assert result is False

    def test_named_resolver__class_being_generated_matches__matches_expected_class(self):
        """Scenario: Check class match when target matches expected class from file name.

        Expected Outcome: Returns True.
        """
        # Arrange
        self.context.current_file = "/path/to/tree_node.py"

        # Act
        result = self.resolver._class_being_generated_matches("TreeNode")

        # Assert
        assert result is True

    def test_named_resolver__class_being_generated_matches__does_not_match_expected_class(self):
        """Scenario: Check class match when target does not match expected class from file name.

        Expected Outcome: Returns False.
        """
        # Arrange
        self.context.current_file = "/path/to/tree_node.py"

        # Act
        result = self.resolver._class_being_generated_matches("SomeOtherClass")

        # Assert
        assert result is False

    def test_named_resolver__is_self_reference__no_current_file__returns_false(self):
        """Scenario: Check self reference when no current file is set.

        Expected Outcome: Returns False.
        """
        # Arrange
        self.context.current_file = None

        # Act
        result = self.resolver._is_self_reference("tree_node", "TreeNode")

        # Assert
        assert result is False

    def test_named_resolver__is_self_reference__different_module__returns_false(self):
        """Scenario: Check self reference with different module name.

        Expected Outcome: Returns False.
        """
        # Arrange
        self.context.current_file = "/path/to/tree_node.py"

        # Act
        result = self.resolver._is_self_reference("other_module", "TreeNode")

        # Assert
        assert result is False

    def test_named_resolver__is_self_reference__same_module_different_class__returns_false(self):
        """Scenario: Check self reference with same module but different class.

        Expected Outcome: Returns False.
        """
        # Arrange
        self.context.current_file = "/path/to/tree_node.py"

        # Act
        result = self.resolver._is_self_reference("tree_node", "OtherClass")

        # Assert
        assert result is False

    def test_named_resolver__is_self_reference__same_module_same_class__returns_true(self):
        """Scenario: Check self reference with same module and same class.

        Expected Outcome: Returns True.
        """
        # Arrange
        self.context.current_file = "/path/to/tree_node.py"

        # Act
        result = self.resolver._is_self_reference("tree_node", "TreeNode")

        # Assert
        assert result is True

    def test_named_resolver__resolve_unknown_schema__returns_none(self):
        """Scenario: Resolve schema that is not in all_schemas and has no enum.

        Expected Outcome: Returns None.
        """
        # Arrange
        schema = IRSchema(name="UnknownSchema", type="object")

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result is None

    def test_named_resolver__resolve_schema_reference__adds_import_returns_class_name(self):
        """Scenario: Resolve schema that references a known schema.

        Expected Outcome: Adds import and returns class name.
        """
        # Arrange
        ref_schema = IRSchema(name="User", generation_name="User", final_module_stem="user")
        self.all_schemas["User"] = ref_schema

        schema = IRSchema(name="User")

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "User"
        self.context.add_import.assert_called_with(logical_module="myapi.models.user", name="User")

    def test_named_resolver__resolve_schema_reference_self_reference__returns_quoted_name(self):
        """Scenario: Resolve schema that is a self-reference.

        Expected Outcome: Returns quoted type name without adding import.
        """
        # Arrange
        ref_schema = IRSchema(name="TreeNode", generation_name="TreeNode", final_module_stem="tree_node")
        self.all_schemas["TreeNode"] = ref_schema

        schema = IRSchema(name="TreeNode")
        self.context.current_file = "/path/to/tree_node.py"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == '"TreeNode"'
        self.context.add_import.assert_not_called()

    def test_named_resolver__resolve_schema_reference_resolve_alias_target_true_simple_alias__returns_none(self):
        """Scenario: Resolve schema reference with resolve_alias_target=True for simple alias.

        Expected Outcome: Returns None to signal structural resolution needed.
        """
        # Arrange
        ref_schema = IRSchema(
            name="StringAlias", type="string", generation_name="StringAlias", final_module_stem="string_alias"
        )
        # Simple alias has no properties, enum, or composition
        self.all_schemas["StringAlias"] = ref_schema

        schema = IRSchema(name="StringAlias")

        # Act
        result = self.resolver.resolve(schema, resolve_alias_target=True)

        # Assert
        assert result is None

    def test_named_resolver__resolve_schema_reference_resolve_alias_target_true_complex_schema__returns_class_name(
        self,
    ):
        """Scenario: Resolve schema reference with resolve_alias_target=True for complex schema.

        Expected Outcome: Adds import and returns class name.
        """
        # Arrange
        ref_schema = IRSchema(
            name="DataObject",
            type="object",
            generation_name="DataObject",
            final_module_stem="data_object",
            properties={"field": IRSchema(type="string")},  # Has properties - not simple alias
        )
        self.all_schemas["DataObject"] = ref_schema

        schema = IRSchema(name="DataObject")

        # Act
        result = self.resolver.resolve(schema, resolve_alias_target=True)

        # Assert
        assert result == "DataObject"
        self.context.add_import.assert_called_with(logical_module="myapi.models.data_object", name="DataObject")

    def test_named_resolver__resolve_schema_reference_resolve_alias_target_true_enum_schema__returns_class_name(self):
        """Scenario: Resolve schema reference with resolve_alias_target=True for enum schema.

        Expected Outcome: Adds import and returns class name.
        """
        # Arrange
        ref_schema = IRSchema(
            name="StatusEnum",
            type="string",
            generation_name="StatusEnum",
            final_module_stem="status_enum",
            enum=["active", "inactive"],  # Has enum - not simple alias
        )
        self.all_schemas["StatusEnum"] = ref_schema

        schema = IRSchema(name="StatusEnum")

        # Act
        result = self.resolver.resolve(schema, resolve_alias_target=True)

        # Assert
        assert result == "StatusEnum"
        self.context.add_import.assert_called_with(logical_module="myapi.models.status_enum", name="StatusEnum")

    def test_named_resolver__resolve_schema_reference_resolve_alias_target_true_any_of_schema__returns_class_name(self):
        """Scenario: Resolve schema reference with resolve_alias_target=True for anyOf schema.

        Expected Outcome: Adds import and returns class name.
        """
        # Arrange
        ref_schema = IRSchema(
            name="UnionType",
            generation_name="UnionType",
            final_module_stem="union_type",
            any_of=[IRSchema(type="string"), IRSchema(type="integer")],  # Has anyOf - not simple alias
        )
        self.all_schemas["UnionType"] = ref_schema

        schema = IRSchema(name="UnionType")

        # Act
        result = self.resolver.resolve(schema, resolve_alias_target=True)

        # Assert
        assert result == "UnionType"
        self.context.add_import.assert_called_with(logical_module="myapi.models.union_type", name="UnionType")

    def test_named_resolver__resolve_schema_reference_resolve_alias_target_true_one_of_schema__returns_class_name(self):
        """Scenario: Resolve schema reference with resolve_alias_target=True for oneOf schema.

        Expected Outcome: Adds import and returns class name.
        """
        # Arrange
        ref_schema = IRSchema(
            name="ChoiceType",
            generation_name="ChoiceType",
            final_module_stem="choice_type",
            one_of=[IRSchema(type="string"), IRSchema(type="integer")],  # Has oneOf - not simple alias
        )
        self.all_schemas["ChoiceType"] = ref_schema

        schema = IRSchema(name="ChoiceType")

        # Act
        result = self.resolver.resolve(schema, resolve_alias_target=True)

        # Assert
        assert result == "ChoiceType"
        self.context.add_import.assert_called_with(logical_module="myapi.models.choice_type", name="ChoiceType")

    def test_named_resolver__resolve_schema_reference_resolve_alias_target_true_all_of_schema__returns_class_name(self):
        """Scenario: Resolve schema reference with resolve_alias_target=True for allOf schema.

        Expected Outcome: Adds import and returns class name.
        """
        # Arrange
        ref_schema = IRSchema(
            name="CombinedType",
            generation_name="CombinedType",
            final_module_stem="combined_type",
            all_of=[
                IRSchema(type="object"),
                IRSchema(properties={"field": IRSchema(type="string")}),
            ],  # Has allOf - not simple alias
        )
        self.all_schemas["CombinedType"] = ref_schema

        schema = IRSchema(name="CombinedType")

        # Act
        result = self.resolver.resolve(schema, resolve_alias_target=True)

        # Assert
        assert result == "CombinedType"
        self.context.add_import.assert_called_with(logical_module="myapi.models.combined_type", name="CombinedType")

    def test_named_resolver__resolve_inline_named_enum__adds_import_returns_enum_name(self):
        """Scenario: Resolve inline enum with a name.

        Expected Outcome: Adds import and returns sanitized enum name.
        """
        # Arrange
        schema = IRSchema(name="StatusEnum", type="string", enum=["active", "inactive", "pending"])

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "StatusEnum"
        self.context.add_import.assert_called_with(logical_module="myapi.models.status_enum", name="StatusEnum")

    def test_named_resolver__resolve_inline_anonymous_enum_string__returns_str(self):
        """Scenario: Resolve inline anonymous enum of string type.

        Expected Outcome: Returns 'str'.
        """
        # Arrange
        schema = IRSchema(name=None, type="string", enum=["value1", "value2"])

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "str"
        self.context.add_import.assert_not_called()

    def test_named_resolver__resolve_inline_anonymous_enum_integer__returns_int(self):
        """Scenario: Resolve inline anonymous enum of integer type.

        Expected Outcome: Returns 'int'.
        """
        # Arrange
        schema = IRSchema(name=None, type="integer", enum=[1, 2, 3])

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "int"
        self.context.add_import.assert_not_called()

    def test_named_resolver__resolve_inline_anonymous_enum_number__returns_float(self):
        """Scenario: Resolve inline anonymous enum of number type.

        Expected Outcome: Returns 'float'.
        """
        # Arrange
        schema = IRSchema(name=None, type="number", enum=[1.5, 2.7, 3.14])

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "float"
        self.context.add_import.assert_not_called()

    def test_named_resolver__resolve_inline_anonymous_enum_no_type__returns_str_default(self):
        """Scenario: Resolve inline anonymous enum with no type specified.

        Expected Outcome: Returns 'str' as default.
        """
        # Arrange
        schema = IRSchema(name=None, enum=["value1", "value2"])  # No type specified

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "str"
        self.context.add_import.assert_not_called()

    def test_named_resolver__resolve_schema_reference_missing_generation_name__raises_assertion_error(self):
        """Scenario: Resolve schema reference where referenced schema lacks generation_name.

        Expected Outcome: AssertionError is raised.
        """
        # Arrange
        ref_schema = IRSchema(name="User", generation_name=None, final_module_stem="user")  # Missing generation_name
        self.all_schemas["User"] = ref_schema

        schema = IRSchema(name="User")

        # Act & Assert
        with pytest.raises(AssertionError, match="must have generation_name set"):
            self.resolver.resolve(schema)

    def test_named_resolver__resolve_schema_reference_missing_final_module_stem__raises_assertion_error(self):
        """Scenario: Resolve schema reference where referenced schema lacks final_module_stem.

        Expected Outcome: AssertionError is raised.
        """
        # Arrange
        ref_schema = IRSchema(name="User", generation_name="User", final_module_stem=None)  # Missing final_module_stem
        self.all_schemas["User"] = ref_schema

        schema = IRSchema(name="User")

        # Act & Assert
        with pytest.raises(AssertionError, match="must have final_module_stem set"):
            self.resolver.resolve(schema)

    def test_named_resolver__resolve_schema_reference_missing_ref_schema_name__raises_assertion_error(self):
        """Scenario: Resolve schema reference where referenced schema has None name.

        Expected Outcome: AssertionError is raised.
        """
        # Arrange
        ref_schema = IRSchema(name=None, generation_name="User", final_module_stem="user")  # None name
        self.all_schemas["User"] = ref_schema

        schema = IRSchema(name="User")

        # Act & Assert
        with pytest.raises(AssertionError, match="resolved to ref_schema with None name"):
            self.resolver.resolve(schema)

    def test_named_resolver__resolve_complex_package_path(self):
        """Scenario: Resolve schema with complex package path from context.

        Expected Outcome: Uses complex package path in import.
        """
        # Arrange
        self.context.get_current_package_name_for_generated_code.return_value = "myorg.services.userapi"

        ref_schema = IRSchema(name="User", generation_name="User", final_module_stem="user")
        self.all_schemas["User"] = ref_schema

        schema = IRSchema(name="User")

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "User"
        self.context.add_import.assert_called_with(logical_module="myorg.services.userapi.models.user", name="User")

    def test_named_resolver__resolve_with_sanitization(self):
        """Scenario: Resolve inline enum that requires name sanitization.

        Expected Outcome: Name is properly sanitized for class and module names.
        """
        # Arrange
        schema = IRSchema(
            name="Status-Enum-With-Dashes",
            type="string",
            enum=["active", "inactive"],  # Needs sanitization
        )

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "StatusEnumWithDashes"  # Should be sanitized
        # Verify the import uses sanitized module name
        expected_calls = self.context.add_import.call_args_list
        assert len(expected_calls) == 1
        call_args = expected_calls[0]
        logical_module = call_args[1]["logical_module"]
        assert "status_enum_with_dashes" in logical_module  # Module name should be snake_case

    def test_named_resolver__edge_case_empty_enum(self):
        """Scenario: Resolve schema with empty enum list.

        Expected Outcome: Empty enum is falsy, so falls through to None return.
        """
        # Arrange
        schema = IRSchema(name=None, type="string", enum=[])  # Empty enum - falsy in boolean context

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result is None  # Empty enum falls through to final return None
        self.context.add_import.assert_not_called()

    def test_named_resolver__resolve_with_none_schema_name_but_has_reference(self):
        """Scenario: Resolve schema where schema.name is None but exists in all_schemas.

        Expected Outcome: Returns None since schema.name is falsy.
        """
        # Arrange
        ref_schema = IRSchema(name="SomeModel", generation_name="SomeModel", final_module_stem="some_model")
        self.all_schemas["SomeModel"] = ref_schema

        schema = IRSchema(name=None)  # No name to look up

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result is None
        self.context.add_import.assert_not_called()
