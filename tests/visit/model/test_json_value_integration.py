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

        from pyopenapi_gen.core.schemas import BaseSchema

        # Set up namespace with required imports
        namespace: dict[str, Any] = {
            "dataclass": dataclass,
            "field": field,
            "BaseSchema": BaseSchema,
            "Any": Any,
            "dict": dict,
        }
        exec(code, namespace)
        return namespace

    def test_generated_wrapper__preserves_arbitrary_data(self) -> None:
        """
        Scenario: Generate wrapper class and test data preservation.
        Expected Outcome: All arbitrary data is preserved through from_dict/to_dict.
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

        # Test data preservation
        test_data = {
            "title": "Test Document",
            "author": "John Doe",
            "metadata": {"version": "1.0", "tags": ["test", "demo"]},
            "count": 42,
            "active": True,
            "nullable_field": None,
        }

        # Create instance from dict
        instance = JsonValue.from_dict(test_data)

        # Assert: All data should be preserved
        assert instance.get("title") == "Test Document"
        assert instance.get("author") == "John Doe"
        assert instance.get("metadata") == {"version": "1.0", "tags": ["test", "demo"]}
        assert instance.get("count") == 42
        assert instance.get("active") is True
        assert instance.get("nullable_field") is None

        # Test round-trip conversion
        output_data = instance.to_dict()
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

        # Create instance
        data = {"key1": "value1", "key2": 123}
        instance = Metadata.from_dict(data)

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

        # Assert: Truthiness
        empty_instance = JsonValue.from_dict({})
        assert not empty_instance  # Should be falsy

        non_empty_instance = JsonValue.from_dict({"key": "value"})
        assert non_empty_instance  # Should be truthy

    def test_generated_wrapper__exclude_none_works(self) -> None:
        """
        Scenario: Generate wrapper and test exclude_none in to_dict.
        Expected Outcome: None values are excluded when requested.
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

        # Create instance with None values
        data = {"key1": "value1", "key2": None, "key3": 123}
        instance = JsonValue.from_dict(data)

        # Assert: Default includes None
        output_with_none = instance.to_dict()
        assert output_with_none == data
        assert "key2" in output_with_none

        # Assert: exclude_none removes None values
        output_without_none = instance.to_dict(exclude_none=True)
        assert output_without_none == {"key1": "value1", "key3": 123}
        assert "key2" not in output_without_none

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

        instance = JsonValue.from_dict(nested_data)

        # Assert: Nested access works
        assert instance.get("level1")["level2"]["level3"]["value"] == "deep"
        assert instance["array_of_objects"][0]["id"] == 1

        # Assert: Round-trip preserves structure
        assert instance.to_dict() == nested_data
