"""Tests for helpers.type_resolution.array_resolver module."""

from unittest.mock import Mock, call

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.type_resolution.array_resolver import ArrayTypeResolver


class TestArrayTypeResolver:
    """Test suite for ArrayTypeResolver."""

    def setup_method(self):
        """Set up test fixtures."""
        self.context = Mock(spec=RenderContext)
        self.all_schemas = {}
        self.main_resolver = Mock()
        self.resolver = ArrayTypeResolver(self.context, self.all_schemas, self.main_resolver)

    def test_array_resolver__init__stores_dependencies(self):
        """Scenario: Initialize ArrayTypeResolver.

        Expected Outcome: Dependencies are stored correctly.
        """
        # Assert
        assert self.resolver.context is self.context
        assert self.resolver.all_schemas is self.all_schemas
        assert self.resolver.main_resolver is self.main_resolver

    def test_array_resolver__resolve_array_with_items__returns_list_type(self):
        """Scenario: Resolve array schema with items.

        Expected Outcome: Returns List[ItemType] and adds imports.
        """
        # Arrange
        item_schema = IRSchema(name="Item", type="string")
        array_schema = IRSchema(name="ArrayField", type="array", items=item_schema)
        self.main_resolver.resolve.return_value = "str"

        # Act
        result = self.resolver.resolve(array_schema, parent_name_hint="Parent")

        # Assert
        assert result == "List[str]"
        self.context.add_import.assert_called_with("typing", "List")
        self.main_resolver.resolve.assert_called_once_with(
            item_schema, current_schema_context_name="Parent", resolve_alias_target=False
        )

    def test_array_resolver__resolve_array_without_items__returns_list_any(self):
        """Scenario: Resolve array schema without items.

        Expected Outcome: Returns List[Any] and adds imports with warning.
        """
        # Arrange
        array_schema = IRSchema(name="EmptyArray", type="array", items=None)

        # Act
        result = self.resolver.resolve(array_schema)

        # Assert
        assert result == "List[Any]"
        # Should add both List and Any imports
        expected_calls = [call("typing", "Any"), call("typing", "List")]
        self.context.add_import.assert_has_calls(expected_calls, any_order=True)

    def test_array_resolver__resolve_non_array_schema__returns_none(self):
        """Scenario: Resolve non-array schema.

        Expected Outcome: Returns None.
        """
        # Arrange
        string_schema = IRSchema(name="NotArray", type="string")

        # Act
        result = self.resolver.resolve(string_schema)

        # Assert
        assert result is None
        self.context.add_import.assert_not_called()
        self.main_resolver.resolve.assert_not_called()

    def test_array_resolver__resolve_with_resolve_alias_target__passes_flag(self):
        """Scenario: Resolve array with resolve_alias_target=True.

        Expected Outcome: Flag is passed to main resolver.
        """
        # Arrange
        item_schema = IRSchema(name="Item", type="object")
        array_schema = IRSchema(name="ArrayField", type="array", items=item_schema)
        self.main_resolver.resolve.return_value = "MyModel"

        # Act
        result = self.resolver.resolve(array_schema, resolve_alias_target=True)

        # Assert
        assert result == "List[MyModel]"
        self.main_resolver.resolve.assert_called_once_with(
            item_schema, current_schema_context_name=None, resolve_alias_target=True
        )

    def test_array_resolver__resolve_nested_array__handles_complex_types(self):
        """Scenario: Resolve array with complex item type.

        Expected Outcome: Returns List[ComplexType].
        """
        # Arrange
        inner_item = IRSchema(name="InnerItem", type="string")
        inner_array = IRSchema(name="InnerArray", type="array", items=inner_item)
        outer_array = IRSchema(name="OuterArray", type="array", items=inner_array)
        self.main_resolver.resolve.return_value = "List[str]"

        # Act
        result = self.resolver.resolve(outer_array, parent_name_hint="Parent")

        # Assert
        assert result == "List[List[str]]"
        self.context.add_import.assert_called_with("typing", "List")

    def test_array_resolver__resolve_array_with_object_items__returns_model_list(self):
        """Scenario: Resolve array with object items.

        Expected Outcome: Returns List[ModelName].
        """
        # Arrange
        object_schema = IRSchema(name="User", type="object")
        array_schema = IRSchema(name="Users", type="array", items=object_schema)
        self.main_resolver.resolve.return_value = "User"

        # Act
        result = self.resolver.resolve(array_schema)

        # Assert
        assert result == "List[User]"
        self.context.add_import.assert_called_with("typing", "List")

    def test_array_resolver__main_resolver_returns_none__returns_none(self):
        """Scenario: Main resolver returns None for item type.

        Expected Outcome: Returns None.
        """
        # Arrange
        item_schema = IRSchema(name="UnresolvableItem", type="unknown")
        array_schema = IRSchema(name="ArrayField", type="array", items=item_schema)
        self.main_resolver.resolve.return_value = None

        # Act
        result = self.resolver.resolve(array_schema)

        # Assert
        assert result is None
        self.context.add_import.assert_not_called()

    def test_array_resolver__with_all_parameters__uses_all_correctly(self):
        """Scenario: Resolve array with all parameters provided.

        Expected Outcome: All parameters are used correctly.
        """
        # Arrange
        item_schema = IRSchema(name="Item", type="string")
        array_schema = IRSchema(name="ArrayField", type="array", items=item_schema)
        self.main_resolver.resolve.return_value = "str"

        # Act
        result = self.resolver.resolve(array_schema, parent_name_hint="ParentModel", resolve_alias_target=True)

        # Assert
        assert result == "List[str]"
        self.main_resolver.resolve.assert_called_once_with(
            item_schema, current_schema_context_name="ParentModel", resolve_alias_target=True
        )
        self.context.add_import.assert_called_with("typing", "List")

    def test_array_resolver__array_with_empty_items_schema__logs_warning(self):
        """Scenario: Resolve array with None items (edge case).

        Expected Outcome: Warning is logged and List[Any] returned.
        """
        # Arrange
        array_schema = IRSchema(name="TestArray", type="array", items=None)

        # Act
        result = self.resolver.resolve(array_schema)

        # Assert
        assert result == "List[Any]"
        # Verify both imports are added
        expected_calls = [call("typing", "Any"), call("typing", "List")]
        self.context.add_import.assert_has_calls(expected_calls, any_order=True)
