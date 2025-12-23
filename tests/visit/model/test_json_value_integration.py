"""
Integration tests for JsonValue wrapper data preservation.

Scenario: Verify that generated JsonValue wrapper classes correctly preserve
arbitrary JSON data during serialization and deserialization.

Expected Outcome: All data is preserved through round-trip conversions.
"""

from typing import Any

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.visit.model.dataclass_generator import DataclassGenerator


class TestJsonValueIntegration:
    """Integration tests for JsonValue wrapper data preservation."""

    def _execute_generated_code(self, code: str) -> dict[str, Any]:
        """
        Execute generated code and return the namespace.

        Args:
            code: Python code to execute.

        Returns:
            Dictionary containing the execution namespace.
        """
        # Import required modules for execution
        from dataclasses import dataclass, field

        from pyopenapi_gen.core.cattrs_converter import converter

        # Set up namespace with required imports
        namespace: dict[str, Any] = {
            "dataclass": dataclass,
            "field": field,
            "structure_from_dict": lambda data, cls: converter.structure(data, cls),
            "unstructure_to_dict": lambda instance: converter.unstructure(instance),
            "converter": converter,
            "Any": Any,
            "dict": dict,
        }
        exec(code, namespace)

        # Register hooks if they were generated
        for name, value in namespace.items():
            if name.startswith("_structure_") and callable(value):
                # Extract class name from hook name (e.g., "_structure_jsonvalue" -> "JsonValue")
                class_name_from_hook = name.replace("_structure_", "").title().replace("value", "Value")
                if class_name_from_hook in namespace:
                    cls = namespace[class_name_from_hook]
                    converter.register_structure_hook(cls, value)
            elif name.startswith("_unstructure_") and callable(value):
                class_name_from_hook = name.replace("_unstructure_", "").title().replace("value", "Value")
                if class_name_from_hook in namespace:
                    cls = namespace[class_name_from_hook]
                    converter.register_unstructure_hook(cls, value)

        return namespace

    def test_generated_wrapper__preserves_arbitrary_data(self) -> None:
        """
        Scenario: Generate wrapper class and test data preservation.
        Expected Outcome: All arbitrary data is preserved through cattrs structure/unstructure.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="JsonValue",
            type="object",
            properties={},
            required=[],
            additional_properties=True,
        )

        # Act: Generate the class
        generated_code = generator.generate(schema, "JsonValue", context)

        # Execute generated code to get the class
        namespace = self._execute_generated_code(generated_code)
        JsonValue = namespace["JsonValue"]
        structure_from_dict = namespace["structure_from_dict"]
        unstructure_to_dict = namespace["unstructure_to_dict"]

        # Test data preservation
        test_data = {
            "title": "Test Document",
            "author": "John Doe",
            "metadata": {"version": "1.0", "tags": ["test", "demo"]},
            "count": 42,
            "active": True,
            "nullable_field": None,
        }

        # Create instance using cattrs
        instance = structure_from_dict(test_data, JsonValue)

        # Assert: All data should be preserved
        assert instance.get("title") == "Test Document"
        assert instance.get("author") == "John Doe"
        assert instance.get("metadata") == {"version": "1.0", "tags": ["test", "demo"]}
        assert instance.get("count") == 42
        assert instance.get("active") is True
        assert instance.get("nullable_field") is None

        # Test round-trip conversion using cattrs
        output_data = unstructure_to_dict(instance)
        assert output_data == test_data

    def test_generated_wrapper__dict_like_access_works(self) -> None:
        """
        Scenario: Generate wrapper and test dict-like access methods.
        Expected Outcome: All dict operations work correctly.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="Metadata",
            type="object",
            properties={},
            required=[],
            additional_properties=True,
        )

        # Act: Generate and execute
        generated_code = generator.generate(schema, "Metadata", context)
        namespace = self._execute_generated_code(generated_code)
        Metadata = namespace["Metadata"]
        structure_from_dict = namespace["structure_from_dict"]

        # Create instance using cattrs
        data = {"key1": "value1", "key2": 123}
        instance = structure_from_dict(data, Metadata)

        # Assert: Dict-like access
        assert instance["key1"] == "value1"
        assert instance["key2"] == 123
        assert "key1" in instance
        assert "nonexistent" not in instance
        assert instance.get("nonexistent", "default") == "default"

        # Test iteration
        assert set(instance.keys()) == {"key1", "key2"}
        assert set(instance.values()) == {"value1", 123}
        assert set(instance.items()) == {("key1", "value1"), ("key2", 123)}

        # Test mutation
        instance["key3"] = "value3"
        assert instance["key3"] == "value3"
        assert "key3" in instance

    def test_generated_wrapper__empty_data_is_falsy(self) -> None:
        """
        Scenario: Generate wrapper and test truthiness behavior.
        Expected Outcome: Empty wrapper is falsy, non-empty is truthy.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="JsonValue",
            type="object",
            properties={},
            required=[],
            additional_properties=True,
        )

        # Act: Generate and execute
        generated_code = generator.generate(schema, "JsonValue", context)
        namespace = self._execute_generated_code(generated_code)
        JsonValue = namespace["JsonValue"]
        structure_from_dict = namespace["structure_from_dict"]

        # Assert: Truthiness using cattrs
        empty_instance = structure_from_dict({}, JsonValue)
        assert not empty_instance  # Should be falsy

        non_empty_instance = structure_from_dict({"key": "value"}, JsonValue)
        assert non_empty_instance  # Should be truthy

    def test_generated_wrapper__exclude_none_works(self) -> None:
        """
        Scenario: Generate wrapper and test serialisation with None values.
        Expected Outcome: None values are preserved in round-trip with cattrs.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="JsonValue",
            type="object",
            properties={},
            required=[],
            additional_properties=True,
        )

        # Act: Generate and execute
        generated_code = generator.generate(schema, "JsonValue", context)
        namespace = self._execute_generated_code(generated_code)
        JsonValue = namespace["JsonValue"]
        structure_from_dict = namespace["structure_from_dict"]
        unstructure_to_dict = namespace["unstructure_to_dict"]

        # Create instance with None values using cattrs
        data = {"key1": "value1", "key2": None, "key3": 123}
        instance = structure_from_dict(data, JsonValue)

        # Assert: cattrs preserves None values
        output_data = unstructure_to_dict(instance)
        assert output_data == data
        assert "key2" in output_data
        assert output_data["key2"] is None

    def test_generated_wrapper__nested_data_preserved(self) -> None:
        """
        Scenario: Generate wrapper and test with deeply nested data.
        Expected Outcome: All nested structures are preserved.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="JsonValue",
            type="object",
            properties={},
            required=[],
            additional_properties=True,
        )

        # Act: Generate and execute
        generated_code = generator.generate(schema, "JsonValue", context)
        namespace = self._execute_generated_code(generated_code)
        JsonValue = namespace["JsonValue"]
        structure_from_dict = namespace["structure_from_dict"]
        unstructure_to_dict = namespace["unstructure_to_dict"]

        # Complex nested data
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep",
                        "list": [1, 2, 3],
                        "dict": {"a": "b"},
                    }
                }
            },
            "array_of_objects": [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}],
        }

        # Create instance using cattrs
        instance = structure_from_dict(nested_data, JsonValue)

        # Assert: Nested access works
        assert instance.get("level1")["level2"]["level3"]["value"] == "deep"
        assert instance["array_of_objects"][0]["id"] == 1

        # Assert: Round-trip preserves structure with cattrs
        assert unstructure_to_dict(instance) == nested_data

    def test_generated_typed_wrapper__dataclass_values__deserialises_correctly(self) -> None:
        """
        Scenario: Generate typed wrapper with dataclass additionalProperties.
        Expected Outcome: Dict values are deserialised into proper dataclass instances.
        """
        # Arrange
        from collections.abc import ItemsView, KeysView, ValuesView
        from dataclasses import dataclass, field
        from typing import ClassVar, Iterator

        from pyopenapi_gen.core.cattrs_converter import (
            _register_structure_hooks_recursively,
            converter,
        )

        # Define the value type dataclass
        @dataclass
        class ToolConfig:
            """Tool configuration."""

            type_: str
            name: str
            description: str | None = None

            class Meta:
                key_transform_with_load = {"type": "type_"}
                key_transform_with_dump = {"type_": "type"}

        # Register structure hooks for ToolConfig
        _register_structure_hooks_recursively(ToolConfig)

        # Generate a typed wrapper schema
        renderer = PythonConstructRenderer()

        # Schema for the schemas registry (with generation_name set to indicate it's a named type)
        tool_config_schema_registry = IRSchema(
            name="ToolConfig",
            generation_name="ToolConfig",
            type="object",
            properties={
                "type": IRSchema(name=None, type="string"),
                "name": IRSchema(name=None, type="string"),
                "description": IRSchema(name=None, type="string"),
            },
            required=["type", "name"],
        )

        # Reference schema for additionalProperties (just name, no type - like a $ref)
        tool_config_ref_schema = IRSchema(
            name="ToolConfig",
            generation_name="ToolConfig",
        )

        generator = DataclassGenerator(renderer, {"ToolConfig": tool_config_schema_registry})
        # Set proper core_package_name for import resolution
        context = RenderContext(core_package_name="pyopenapi_gen.core")

        schema = IRSchema(
            name="ToolsConfig",
            type="object",
            properties={},
            required=[],
            additional_properties=tool_config_ref_schema,
        )

        # Act: Generate the typed wrapper class
        generated_code = generator.generate(schema, "ToolsConfig", context)

        # Verify it's a typed wrapper (has _value_type ClassVar)
        assert "_value_type" in generated_code
        assert "ToolConfig" in generated_code

        # Create namespace and execute
        namespace: dict[str, Any] = {
            "dataclass": dataclass,
            "field": field,
            "ClassVar": ClassVar,
            "Iterator": Iterator,
            "KeysView": KeysView,
            "ValuesView": ValuesView,
            "ItemsView": ItemsView,
            "ToolConfig": ToolConfig,
            "converter": converter,
            "_register_structure_hooks_recursively": _register_structure_hooks_recursively,
            "Any": Any,
            "dict": dict,
        }
        exec(generated_code, namespace)
        ToolsConfig = namespace["ToolsConfig"]

        # Register hooks
        structure_hook = namespace.get("_structure_toolsconfig")
        if structure_hook:
            converter.register_structure_hook(ToolsConfig, structure_hook)

        unstructure_hook = namespace.get("_unstructure_toolsconfig")
        if unstructure_hook:
            converter.register_unstructure_hook(ToolsConfig, unstructure_hook)

        # Test data
        test_data = {
            "tool1": {"type": "documentLookup", "name": "tool1", "description": "First tool"},
            "tool2": {"type": "ragSearch", "name": "tool2"},
        }

        # Act: Structure the data
        instance = converter.structure(test_data, ToolsConfig)

        # Assert: Values are ToolConfig instances, not raw dicts
        tool1 = instance["tool1"]
        assert isinstance(tool1, ToolConfig), f"Expected ToolConfig, got {type(tool1)}"
        assert tool1.type_ == "documentLookup"
        assert tool1.name == "tool1"
        assert tool1.description == "First tool"

        tool2 = instance["tool2"]
        assert isinstance(tool2, ToolConfig), f"Expected ToolConfig, got {type(tool2)}"
        assert tool2.type_ == "ragSearch"
        assert tool2.name == "tool2"
        assert tool2.description is None

    def test_generated_typed_wrapper__all_value_types__structured_correctly(self) -> None:
        """
        Scenario: Generate typed wrapper with primitive value type.
        Expected Outcome: All value types (primitives) are properly structured.
        """
        # Arrange
        from collections.abc import ItemsView, KeysView, ValuesView
        from dataclasses import dataclass, field
        from typing import ClassVar, Iterator

        from pyopenapi_gen.core.cattrs_converter import converter

        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        # Set proper core_package_name for import resolution
        context = RenderContext(core_package_name="pyopenapi_gen.core")

        # Schema with string additionalProperties
        string_value_schema = IRSchema(name=None, type="string")
        schema = IRSchema(
            name="StringDict",
            type="object",
            properties={},
            required=[],
            additional_properties=string_value_schema,
        )

        # Act: Generate the typed wrapper class
        generated_code = generator.generate(schema, "StringDict", context)

        # Verify it's a typed wrapper
        assert "_value_type" in generated_code
        assert "dict[str, str]" in generated_code

        # Create namespace and execute
        namespace: dict[str, Any] = {
            "dataclass": dataclass,
            "field": field,
            "ClassVar": ClassVar,
            "Iterator": Iterator,
            "KeysView": KeysView,
            "ValuesView": ValuesView,
            "ItemsView": ItemsView,
            "converter": converter,
            "_register_structure_hooks_recursively": lambda x: None,  # Not needed for primitives
            "Any": Any,
            "dict": dict,
            "str": str,
        }
        exec(generated_code, namespace)
        StringDict = namespace["StringDict"]

        # Register hooks
        structure_hook = namespace.get("_structure_stringdict")
        if structure_hook:
            converter.register_structure_hook(StringDict, structure_hook)

        # Test data
        test_data = {"key1": "value1", "key2": "value2"}

        # Act: Structure the data
        instance = converter.structure(test_data, StringDict)

        # Assert: Values are strings
        assert instance["key1"] == "value1"
        assert instance["key2"] == "value2"

        # Test iteration
        for key, value in instance.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
