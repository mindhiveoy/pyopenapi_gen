"""Tests for helpers.type_resolution.object_resolver module."""

from unittest.mock import Mock

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.type_resolution.object_resolver import ObjectTypeResolver


class TestObjectTypeResolver:
    """Test suite for ObjectTypeResolver."""

    def setup_method(self):
        """Set up test fixtures."""
        self.context = Mock(spec=RenderContext)
        # Configure the mock attributes that are accessed by the resolver
        self.context.package_root_for_generated_code = None
        self.context.overall_project_root = None
        self.context.get_current_module_dot_path.return_value = "current.module"

        self.all_schemas = {}
        self.main_resolver = Mock()
        self.resolver = ObjectTypeResolver(self.context, self.all_schemas, self.main_resolver)

    def test_object_resolver__init__stores_dependencies(self):
        """Scenario: Initialize ObjectTypeResolver.

        Expected Outcome: Dependencies are stored correctly.
        """
        # Assert
        assert self.resolver.context is self.context
        assert self.resolver.all_schemas is self.all_schemas
        assert self.resolver.main_resolver is self.main_resolver

    def test_object_resolver__additional_properties_true__returns_dict_str_any(self):
        """Scenario: Resolve object with additionalProperties: true.

        Expected Outcome: Returns Dict[str, Any] and adds imports.
        """
        # Arrange
        schema = IRSchema(name="TestObject", type="object", additional_properties=True)

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, Any]"
        self.context.add_import.assert_any_call("typing", "Dict")
        self.context.add_import.assert_any_call("typing", "Any")

    def test_object_resolver__additional_properties_schema_defined__returns_dict_with_type(self):
        """Scenario: Resolve object with additionalProperties as defined schema.

        Expected Outcome: Returns Dict[str, ResolvedType] and adds imports.
        """
        # Arrange
        ap_schema = IRSchema(name="AdditionalProp", type="string")
        schema = IRSchema(name="TestObject", type="object", additional_properties=ap_schema)
        self.main_resolver.resolve.return_value = "str"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, str]"
        self.context.add_import.assert_any_call("typing", "Dict")
        self.main_resolver.resolve.assert_called_once_with(ap_schema, required=True)

    def test_object_resolver__additional_properties_schema_with_format__returns_dict_with_type(self):
        """Scenario: Resolve object with additionalProperties schema that has format.

        Expected Outcome: Returns Dict[str, ResolvedType].
        """
        # Arrange
        ap_schema = IRSchema(name="AdditionalProp", format="date-time")
        schema = IRSchema(name="TestObject", type="object", additional_properties=ap_schema)
        self.main_resolver.resolve.return_value = "datetime"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, datetime]"
        self.main_resolver.resolve.assert_called_once_with(ap_schema, required=True)

    def test_object_resolver__additional_properties_schema_with_properties__returns_dict_with_type(self):
        """Scenario: Resolve object with additionalProperties schema that has properties.

        Expected Outcome: Returns Dict[str, ResolvedType].
        """
        # Arrange
        ap_schema = IRSchema(name="AdditionalProp", properties={"field": IRSchema(type="string")})
        schema = IRSchema(name="TestObject", type="object", additional_properties=ap_schema)
        self.main_resolver.resolve.return_value = "AdditionalPropModel"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, AdditionalPropModel]"

    def test_object_resolver__additional_properties_schema_with_items__returns_dict_with_type(self):
        """Scenario: Resolve object with additionalProperties schema that has items.

        Expected Outcome: Returns Dict[str, ResolvedType].
        """
        # Arrange
        ap_schema = IRSchema(name="AdditionalProp", items=IRSchema(type="string"))
        schema = IRSchema(name="TestObject", type="object", additional_properties=ap_schema)
        self.main_resolver.resolve.return_value = "List[str]"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, List[str]]"

    def test_object_resolver__additional_properties_schema_with_enum__returns_dict_with_type(self):
        """Scenario: Resolve object with additionalProperties schema that has enum.

        Expected Outcome: Returns Dict[str, ResolvedType].
        """
        # Arrange
        ap_schema = IRSchema(name="AdditionalProp", enum=["val1", "val2"])
        schema = IRSchema(name="TestObject", type="object", additional_properties=ap_schema)
        self.main_resolver.resolve.return_value = "TestEnum"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, TestEnum]"

    def test_object_resolver__additional_properties_schema_with_any_of__returns_dict_with_type(self):
        """Scenario: Resolve object with additionalProperties schema that has anyOf.

        Expected Outcome: Returns Dict[str, ResolvedType].
        """
        # Arrange
        ap_schema = IRSchema(name="AdditionalProp", any_of=[IRSchema(type="string"), IRSchema(type="integer")])
        schema = IRSchema(name="TestObject", type="object", additional_properties=ap_schema)
        self.main_resolver.resolve.return_value = "Union[str, int]"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, Union[str, int]]"

    def test_object_resolver__additional_properties_schema_with_one_of__returns_dict_with_type(self):
        """Scenario: Resolve object with additionalProperties schema that has oneOf.

        Expected Outcome: Returns Dict[str, ResolvedType].
        """
        # Arrange
        ap_schema = IRSchema(name="AdditionalProp", one_of=[IRSchema(type="string"), IRSchema(type="integer")])
        schema = IRSchema(name="TestObject", type="object", additional_properties=ap_schema)
        self.main_resolver.resolve.return_value = "Union[str, int]"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, Union[str, int]]"

    def test_object_resolver__additional_properties_schema_with_all_of__returns_dict_with_type(self):
        """Scenario: Resolve object with additionalProperties schema that has allOf.

        Expected Outcome: Returns Dict[str, ResolvedType].
        """
        # Arrange
        ap_schema = IRSchema(name="AdditionalProp", all_of=[IRSchema(type="string"), IRSchema(format="email")])
        schema = IRSchema(name="TestObject", type="object", additional_properties=ap_schema)
        self.main_resolver.resolve.return_value = "str"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, str]"

    def test_object_resolver__anonymous_object_with_properties_promoted__returns_promoted_name(self):
        """Scenario: Resolve anonymous object with properties that gets promoted.

        Expected Outcome: Returns promoted class name.
        """
        # Arrange
        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name=None, type="object", properties=properties)

        # Act
        result = self.resolver.resolve(schema, parent_schema_name_for_anon_promotion="Parent")

        # Assert
        assert result == "ParentItem"
        assert schema.name == "ParentItem"
        assert schema.generation_name == "ParentItem"
        assert schema.final_module_stem == "parent_item"
        assert "ParentItem" in self.all_schemas
        self.context.add_import.assert_called_with("models.parent_item", "ParentItem")

    def test_object_resolver__anonymous_object_with_properties_not_promoted__returns_dict(self):
        """Scenario: Resolve anonymous object with properties that cannot be promoted.

        Expected Outcome: Returns Dict[str, Any] with warning.
        """
        # Arrange
        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name=None, type="object", properties=properties)

        # Act
        result = self.resolver.resolve(schema)  # No parent name provided

        # Assert
        assert result == "Dict[str, Any]"
        self.context.add_import.assert_any_call("typing", "Dict")
        self.context.add_import.assert_any_call("typing", "Any")

    def test_object_resolver__promote_anonymous_object_with_collision__uses_counter(self):
        """Scenario: Promote anonymous object where name already exists.

        Expected Outcome: Uses counter to find unique name.
        """
        # Arrange
        # Pre-populate existing names
        self.all_schemas["ParentItem"] = IRSchema(name="ParentItem")
        self.all_schemas["ParentItem1"] = IRSchema(name="ParentItem1")

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name=None, type="object", properties=properties)

        # Act
        result = self.resolver.resolve(schema, parent_schema_name_for_anon_promotion="Parent")

        # Assert
        assert result == "ParentItem2"
        assert schema.name == "ParentItem2"

    def test_object_resolver__promote_anonymous_object_too_many_collisions__returns_none(self):
        """Scenario: Promote anonymous object but too many name collisions.

        Expected Outcome: Returns None after safety break.
        """
        # Arrange
        # Pre-populate many existing names
        for i in range(12):
            name = f"ParentItem{i}" if i > 0 else "ParentItem"
            self.all_schemas[name] = IRSchema(name=name)

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name=None, type="object", properties=properties)

        # Act
        result = self.resolver.resolve(schema, parent_schema_name_for_anon_promotion="Parent")

        # Assert
        assert result == "Dict[str, Any]"  # Fallback due to promotion failure

    def test_object_resolver__promote_anonymous_object_no_base_name__returns_none(self):
        """Scenario: Promote anonymous object with no base name provided.

        Expected Outcome: Returns None from promotion method.
        """
        # Arrange
        result = self.resolver._promote_anonymous_object_schema_if_needed(
            IRSchema(name=None, type="object"), None  # No proposed name base
        )

        # Assert
        assert result is None

    def test_object_resolver__named_object_with_properties_in_all_schemas__returns_class_name(self):
        """Scenario: Resolve named object with properties that exists in all_schemas.

        Expected Outcome: Returns class name and adds import.
        """
        # Arrange
        actual_schema = IRSchema(name="TestModel", generation_name="TestModel", final_module_stem="test_model")
        self.all_schemas["TestModel"] = actual_schema

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name="TestModel", type="object", properties=properties)
        self.context.get_current_module_dot_path.return_value = "current.module"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "TestModel"
        self.context.add_import.assert_called_with("models.test_model", "TestModel")

    def test_object_resolver__named_object_with_properties_not_in_all_schemas__returns_sanitized_name(self):
        """Scenario: Resolve named object with properties not in all_schemas.

        Expected Outcome: Returns sanitized class name with warning.
        """
        # Arrange
        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name="TestModel", type="object", properties=properties)

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "TestModel"

    def test_object_resolver__named_object_no_properties_in_all_schemas__returns_class_name(self):
        """Scenario: Resolve named object without properties that exists in all_schemas.

        Expected Outcome: Returns class name and adds import.
        """
        # Arrange
        actual_schema = IRSchema(name="EmptyModel", generation_name="EmptyModel", final_module_stem="empty_model")
        self.all_schemas["EmptyModel"] = actual_schema

        schema = IRSchema(name="EmptyModel", type="object", properties=None)
        self.context.get_current_module_dot_path.return_value = "current.module"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "EmptyModel"
        self.context.add_import.assert_called_with("models.empty_model", "EmptyModel")

    def test_object_resolver__named_object_no_properties_not_in_all_schemas__returns_dict(self):
        """Scenario: Resolve named object without properties not in all_schemas.

        Expected Outcome: Returns Dict[str, Any].
        """
        # Arrange
        schema = IRSchema(name="UnknownModel", type="object", properties=None)

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, Any]"
        self.context.add_import.assert_any_call("typing", "Dict")
        self.context.add_import.assert_any_call("typing", "Any")

    def test_object_resolver__anonymous_object_no_properties_additional_properties_none__returns_dict(self):
        """Scenario: Resolve anonymous object with no properties and additionalProperties None.

        Expected Outcome: Returns Dict[str, Any] (default OpenAPI behavior).
        """
        # Arrange
        schema = IRSchema(name=None, type="object", properties=None, additional_properties=None)

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Dict[str, Any]"
        self.context.add_import.assert_any_call("typing", "Dict")
        self.context.add_import.assert_any_call("typing", "Any")

    def test_object_resolver__anonymous_object_no_properties_additional_properties_false__returns_any(self):
        """Scenario: Resolve anonymous object with no properties and additionalProperties False.

        Expected Outcome: Returns Any (restrictive behavior).
        """
        # Arrange
        schema = IRSchema(name=None, type="object", properties=None, additional_properties=False)

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Any"
        self.context.add_import.assert_called_with("typing", "Any")

    def test_object_resolver__anonymous_object_no_properties_additional_properties_empty_schema__returns_any(self):
        """Scenario: Resolve anonymous object with no properties and empty additionalProperties schema.

        Expected Outcome: Returns Any.
        """
        # Arrange
        empty_schema = IRSchema()  # Empty schema (no type, format, etc.)
        schema = IRSchema(name=None, type="object", properties=None, additional_properties=empty_schema)

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "Any"
        self.context.add_import.assert_called_with("typing", "Any")

    def test_object_resolver__non_object_schema__returns_none(self):
        """Scenario: Resolve non-object schema.

        Expected Outcome: Returns None.
        """
        # Arrange
        schema = IRSchema(name="NotObject", type="string")

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result is None
        self.context.add_import.assert_not_called()

    def test_object_resolver__package_root_configuration_paths(self):
        """Scenario: Test different package root path configurations.

        Expected Outcome: Correct module paths are calculated.
        """
        # Arrange
        actual_schema = IRSchema(name="TestModel", generation_name="TestModel", final_module_stem="test_model")
        self.all_schemas["TestModel"] = actual_schema

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name="TestModel", type="object", properties=properties)

        # Test case 1: package_root is subdirectory of overall_project_root
        self.context.package_root_for_generated_code = "/project/src/pyapis"
        self.context.overall_project_root = "/project"
        self.context.get_current_module_dot_path.return_value = "different.module"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "TestModel"
        self.context.add_import.assert_called_with("src.pyapis.models.test_model", "TestModel")

    def test_object_resolver__package_root_equals_overall_root(self):
        """Scenario: Package root equals overall project root.

        Expected Outcome: Uses base model path without prefix.
        """
        # Arrange
        actual_schema = IRSchema(name="TestModel", generation_name="TestModel", final_module_stem="test_model")
        self.all_schemas["TestModel"] = actual_schema

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name="TestModel", type="object", properties=properties)

        self.context.package_root_for_generated_code = "/project"
        self.context.overall_project_root = "/project"
        self.context.get_current_module_dot_path.return_value = "different.module"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "TestModel"
        self.context.add_import.assert_called_with("models.test_model", "TestModel")

    def test_object_resolver__only_package_root_configured(self):
        """Scenario: Only package_root_for_generated_code is configured.

        Expected Outcome: Uses basename of package root as prefix.
        """
        # Arrange
        actual_schema = IRSchema(name="TestModel", generation_name="TestModel", final_module_stem="test_model")
        self.all_schemas["TestModel"] = actual_schema

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name="TestModel", type="object", properties=properties)

        self.context.package_root_for_generated_code = "/some/path/pyapis"
        self.context.overall_project_root = None
        self.context.get_current_module_dot_path.return_value = "different.module"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "TestModel"
        self.context.add_import.assert_called_with("pyapis.models.test_model", "TestModel")

    def test_object_resolver__package_root_basename_is_dot(self):
        """Scenario: Package root basename is '.' (current directory).

        Expected Outcome: Uses base model path without prefix.
        """
        # Arrange
        actual_schema = IRSchema(name="TestModel", generation_name="TestModel", final_module_stem="test_model")
        self.all_schemas["TestModel"] = actual_schema

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name="TestModel", type="object", properties=properties)

        self.context.package_root_for_generated_code = "."
        self.context.overall_project_root = None
        self.context.get_current_module_dot_path.return_value = "different.module"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "TestModel"
        self.context.add_import.assert_called_with("models.test_model", "TestModel")

    def test_object_resolver__avoid_self_imports(self):
        """Scenario: Current module equals model module path.

        Expected Outcome: No import is added to avoid self-imports.
        """
        # Arrange
        actual_schema = IRSchema(name="TestModel", generation_name="TestModel", final_module_stem="test_model")
        self.all_schemas["TestModel"] = actual_schema

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name="TestModel", type="object", properties=properties)

        # Same module path to trigger self-import avoidance
        self.context.get_current_module_dot_path.return_value = "models.test_model"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "TestModel"
        self.context.add_import.assert_not_called()  # No import should be added

    def test_object_resolver__schema_assertions_fail_generation_name(self):
        """Scenario: Schema in all_schemas missing generation_name.

        Expected Outcome: AssertionError is raised.
        """
        # Arrange
        actual_schema = IRSchema(
            name="TestModel", generation_name=None, final_module_stem="test_model"  # Missing generation_name
        )
        self.all_schemas["TestModel"] = actual_schema

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name="TestModel", type="object", properties=properties)

        # Act & Assert
        with pytest.raises(AssertionError, match="must have generation_name"):
            self.resolver.resolve(schema)

    def test_object_resolver__schema_assertions_fail_final_module_stem(self):
        """Scenario: Schema in all_schemas missing final_module_stem.

        Expected Outcome: AssertionError is raised.
        """
        # Arrange
        actual_schema = IRSchema(
            name="TestModel", generation_name="TestModel", final_module_stem=None  # Missing final_module_stem
        )
        self.all_schemas["TestModel"] = actual_schema

        properties = {"field1": IRSchema(type="string")}
        schema = IRSchema(name="TestModel", type="object", properties=properties)

        # Act & Assert
        with pytest.raises(AssertionError, match="must have final_module_stem"):
            self.resolver.resolve(schema)

    def test_object_resolver__schema_assertions_fail_no_properties_generation_name(self):
        """Scenario: Schema with no properties in all_schemas missing generation_name.

        Expected Outcome: AssertionError is raised.
        """
        # Arrange
        actual_schema = IRSchema(
            name="EmptyModel", generation_name=None, final_module_stem="empty_model"  # Missing generation_name
        )
        self.all_schemas["EmptyModel"] = actual_schema

        schema = IRSchema(name="EmptyModel", type="object", properties=None)

        # Act & Assert
        with pytest.raises(AssertionError, match="must have generation_name"):
            self.resolver.resolve(schema)

    def test_object_resolver__schema_assertions_fail_no_properties_final_module_stem(self):
        """Scenario: Schema with no properties in all_schemas missing final_module_stem.

        Expected Outcome: AssertionError is raised.
        """
        # Arrange
        actual_schema = IRSchema(
            name="EmptyModel", generation_name="EmptyModel", final_module_stem=None  # Missing final_module_stem
        )
        self.all_schemas["EmptyModel"] = actual_schema

        schema = IRSchema(name="EmptyModel", type="object", properties=None)

        # Act & Assert
        with pytest.raises(AssertionError, match="must have final_module_stem"):
            self.resolver.resolve(schema)

    def test_object_resolver__no_properties_package_root_configuration_paths(self):
        """Scenario: Test package root path configurations for objects without properties.

        Expected Outcome: Correct module paths are calculated for no-properties case.
        """
        # Arrange
        actual_schema = IRSchema(name="EmptyModel", generation_name="EmptyModel", final_module_stem="empty_model")
        self.all_schemas["EmptyModel"] = actual_schema

        schema = IRSchema(name="EmptyModel", type="object", properties=None)

        # Test the no-properties path with package root configuration
        self.context.package_root_for_generated_code = "/project/src/pyapis"
        self.context.overall_project_root = "/project"
        self.context.get_current_module_dot_path.return_value = "different.module"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "EmptyModel"
        self.context.add_import.assert_called_with("src.pyapis.models.empty_model", "EmptyModel")

    def test_object_resolver__no_properties_only_package_root_configured(self):
        """Scenario: No properties object with only package_root_for_generated_code configured.

        Expected Outcome: Uses basename of package root as prefix.
        """
        # Arrange
        actual_schema = IRSchema(name="EmptyModel", generation_name="EmptyModel", final_module_stem="empty_model")
        self.all_schemas["EmptyModel"] = actual_schema

        schema = IRSchema(name="EmptyModel", type="object", properties=None)

        self.context.package_root_for_generated_code = "/some/path/pyapis"
        self.context.overall_project_root = None
        self.context.get_current_module_dot_path.return_value = "different.module"

        # Act
        result = self.resolver.resolve(schema)

        # Assert
        assert result == "EmptyModel"
        self.context.add_import.assert_called_with("pyapis.models.empty_model", "EmptyModel")
