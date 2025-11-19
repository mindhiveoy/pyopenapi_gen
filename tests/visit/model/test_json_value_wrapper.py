"""
Unit tests for JsonValue wrapper functionality in DataclassGenerator.

Scenario: Test the generation of JsonValue wrapper classes for arbitrary JSON objects
with no defined properties but additionalProperties enabled.

Expected Outcome: Generated classes preserve all JSON data and provide dict-like access.
"""

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.visit.model.dataclass_generator import DataclassGenerator


class TestJsonValueWrapper:
    """Test JsonValue wrapper generation for arbitrary JSON objects."""

    def test_generate__object_with_additional_properties_true__generates_wrapper_class(self) -> None:
        """
        Scenario: Generate dataclass for object with additionalProperties: true and no properties.
        Expected Outcome: Wrapper class that preserves all data, not an empty dataclass.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="JsonValue",
            type="object",
            properties={},  # No defined properties
            required=[],
            additional_properties=True,  # Allows arbitrary properties
        )

        # Act
        result = generator.generate(schema, "JsonValue", context)

        # Assert
        assert "class JsonValue:" in result
        assert "_data: dict[str, Any] = field(default_factory=dict, repr=False)" in result
        assert "def from_dict(cls, data: dict[str, Any])" in result
        assert "def to_dict(self" in result
        assert "def get(self, key: str, default: Any = None)" in result
        assert "def __getitem__(self, key: str)" in result
        assert "def __setitem__(self, key: str, value: Any)" in result
        assert "def __contains__(self, key: str)" in result
        assert "def __bool__(self)" in result
        assert "def keys(self)" in result
        assert "def values(self)" in result
        assert "def items(self)" in result

        # Should not be empty with just pass
        assert "pass" not in result or "pass" in result and len(result.split("pass")) == 1

    def test_generate__object_with_additional_properties_schema__generates_wrapper_class(self) -> None:
        """
        Scenario: Generate dataclass for object with additionalProperties as schema and no properties.
        Expected Outcome: Wrapper class that preserves all data.
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
            additional_properties=IRSchema(type="string"),  # Additional props are strings
        )

        # Act
        result = generator.generate(schema, "JsonValue", context)

        # Assert
        assert "class JsonValue:" in result
        assert "_data: dict[str, Any]" in result
        assert "from_dict" in result
        assert "to_dict" in result

    def test_generate__object_with_properties__generates_normal_dataclass(self) -> None:
        """
        Scenario: Generate dataclass for object with defined properties.
        Expected Outcome: Normal dataclass with fields, not a wrapper.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="User",
            type="object",
            properties={
                "name": IRSchema(name="name", type="string"),
                "age": IRSchema(name="age", type="integer"),
            },
            required=["name"],
            additional_properties=True,
        )

        # Act
        result = generator.generate(schema, "User", context)

        # Assert
        assert "class User:" in result
        assert "name: str" in result
        assert "age: int | None" in result
        # Should NOT be a wrapper since it has properties
        assert "_data: dict[str, Any]" not in result

    def test_generate__object_with_additional_properties_false__generates_normal_dataclass(self) -> None:
        """
        Scenario: Generate dataclass for object with additionalProperties: false and no properties.
        Expected Outcome: Normal empty dataclass, not a wrapper (no additional properties allowed).
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="Empty",
            type="object",
            properties={},
            required=[],
            additional_properties=False,  # No additional properties allowed
        )

        # Act
        result = generator.generate(schema, "Empty", context)

        # Assert
        assert "class Empty:" in result
        # Should NOT be a wrapper since additional properties are forbidden
        assert "_data: dict[str, Any]" not in result
        # Should have pass or docstring
        assert "pass" in result or "No properties defined" in result

    def test_generate__wrapper_class__adds_required_imports(self) -> None:
        """
        Scenario: Generate wrapper class and verify required imports.
        Expected Outcome: Proper imports for dict, Any, field, etc.
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

        # Act
        generator.generate(schema, "JsonValue", context)

        # Assert
        imports = context.import_collector.imports
        assert "typing" in imports
        assert "Any" in imports["typing"]
        assert "dataclasses" in imports
        assert "field" in imports["dataclasses"]
        assert "dataclass" in imports["dataclasses"]

    def test_generate__object_with_none_additional_properties__generates_normal_dataclass(self) -> None:
        """
        Scenario: Generate dataclass for object with additionalProperties: None (default OpenAPI).
        Expected Outcome: Normal empty dataclass (OpenAPI default allows additional props in validation but not in schema).
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="Default",
            type="object",
            properties={},
            required=[],
            additional_properties=None,  # Default OpenAPI behavior
        )

        # Act
        result = generator.generate(schema, "Default", context)

        # Assert
        assert "class Default:" in result
        # OpenAPI default (None) should NOT generate wrapper
        # because it's semantically different from explicit true
        assert "_data: dict[str, Any]" not in result

    def test_generate__object_with_nullable_additional_properties_schema__generates_wrapper_class(self) -> None:
        """
        Scenario: Generate dataclass for object with additionalProperties as nullable schema object.
                  This matches the real-world JsonValue schema from business_swagger.json:
                  {"type": "object", "additionalProperties": {"nullable": true}}
        Expected Outcome: Wrapper class that preserves all data with nullable value support.
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
            additional_properties=IRSchema(
                type=None,  # Nullable schema has no explicit type
                is_nullable=True,
            ),
        )

        # Act
        result = generator.generate(schema, "JsonValue", context)

        # Assert
        assert "class JsonValue:" in result
        assert "_data: dict[str, Any] = field(default_factory=dict, repr=False)" in result
        assert "def from_dict(cls, data: dict[str, Any])" in result
        assert "def to_dict(self" in result
        assert "def get(self, key: str, default: Any = None)" in result
        assert "def __getitem__(self, key: str)" in result
        assert "def keys(self)" in result
        assert "def values(self)" in result
        assert "def items(self)" in result
