"""
Integration tests for constraint validation feature.

Tests the end-to-end flow of parsing constraints from OpenAPI specs
and generating validation code in dataclasses.
"""

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.visit.model.dataclass_generator import DataclassGenerator
from pyopenapi_gen.visit.model.validation_generator import ValidationCodeGenerator


def test_string_constraints_parsing__minlength_maxlength_pattern__generates_validation():
    """Test string constraint validation code generation.

    Scenario:
        Schema with minLength, maxLength, and pattern constraints

    Expected Outcome:
        Generated __post_init__ validates string length and pattern
    """
    # Arrange
    schema = IRSchema(
        name="User",
        type="object",
        properties={
            "username": IRSchema(
                name="username",
                type="string",
                min_length=3,
                max_length=20,
                pattern="^[a-zA-Z0-9_]+$",
            )
        },
        required=["username"],
    )

    sanitized_field_names = {"username": "username"}
    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")

    # Act
    validation_method = ValidationCodeGenerator.generate_validation_method(schema, sanitized_field_names, context)

    # Assert
    assert validation_method is not None
    assert "__post_init__" in validation_method
    assert "len(self.username)" in validation_method
    assert "re.match" in validation_method
    # Pattern should be included in validation
    assert "^[a-zA-Z0-9_]+$" in validation_method or "[a-zA-Z0-9_]" in validation_method


def test_numeric_constraints__minimum_maximum__generates_validation():
    """Test numeric constraint validation code generation.

    Scenario:
        Schema with minimum and maximum constraints

    Expected Outcome:
        Generated __post_init__ validates numeric range
    """
    # Arrange
    schema = IRSchema(
        name="Product",
        type="object",
        properties={
            "price": IRSchema(
                name="price",
                type="number",
                minimum=0.01,
                maximum=999999.99,
            )
        },
        required=["price"],
    )

    sanitized_field_names = {"price": "price"}
    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")

    # Act
    validation_method = ValidationCodeGenerator.generate_validation_method(schema, sanitized_field_names, context)

    # Assert
    assert validation_method is not None
    assert "__post_init__" in validation_method
    assert "0.01" in validation_method
    assert "999999.99" in validation_method
    assert "self.price" in validation_method


def test_array_constraints__minitems_maxitems__generates_validation():
    """Test array constraint validation code generation.

    Scenario:
        Schema with minItems and maxItems constraints

    Expected Outcome:
        Generated __post_init__ validates array length
    """
    # Arrange
    schema = IRSchema(
        name="Tags",
        type="object",
        properties={
            "tags": IRSchema(
                name="tags",
                type="array",
                items=IRSchema(type="string"),
                min_items=1,
                max_items=10,
            )
        },
        required=["tags"],
    )

    sanitized_field_names = {"tags": "tags"}
    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")

    # Act
    validation_method = ValidationCodeGenerator.generate_validation_method(schema, sanitized_field_names, context)

    # Assert
    assert validation_method is not None
    assert "__post_init__" in validation_method
    assert "len(self.tags)" in validation_method
    assert "1" in validation_method  # minItems
    assert "10" in validation_method  # maxItems


def test_optional_field_with_constraints__wraps_in_none_check():
    """Test optional fields with constraints are wrapped in None check.

    Scenario:
        Optional field (not in required) with constraints

    Expected Outcome:
        Validation wrapped in 'if self.field is not None' check
    """
    # Arrange
    schema = IRSchema(
        name="User",
        type="object",
        properties={
            "bio": IRSchema(
                name="bio",
                type="string",
                min_length=10,
                max_length=500,
            )
        },
        required=[],  # bio is optional
    )

    sanitized_field_names = {"bio": "bio"}
    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")

    # Act
    validation_method = ValidationCodeGenerator.generate_validation_method(schema, sanitized_field_names, context)

    # Assert
    assert validation_method is not None
    assert "if self.bio is not None:" in validation_method


def test_no_constraints__returns_none():
    """Test schema without constraints returns None.

    Scenario:
        Schema with no validation constraints

    Expected Outcome:
        No __post_init__ method generated (returns None)
    """
    # Arrange
    schema = IRSchema(
        name="User",
        type="object",
        properties={
            "name": IRSchema(
                name="name",
                type="string",
                # No constraints
            )
        },
        required=["name"],
    )

    sanitized_field_names = {"name": "name"}
    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")

    # Act
    validation_method = ValidationCodeGenerator.generate_validation_method(schema, sanitized_field_names, context)

    # Assert
    assert validation_method is None


def test_exclusive_minimum_maximum__generates_correct_operators():
    """Test exclusive minimum/maximum use correct comparison operators.

    Scenario:
        Schema with exclusiveMinimum and exclusiveMaximum

    Expected Outcome:
        Generated code uses < and > instead of <= and >=
    """
    # Arrange
    schema = IRSchema(
        name="Score",
        type="object",
        properties={
            "value": IRSchema(
                name="value",
                type="number",
                minimum=0,
                maximum=100,
                exclusive_minimum=True,
                exclusive_maximum=True,
            )
        },
        required=["value"],
    )

    sanitized_field_names = {"value": "value"}
    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")

    # Act
    validation_method = ValidationCodeGenerator.generate_validation_method(schema, sanitized_field_names, context)

    # Assert
    assert validation_method is not None
    # Should use < and > for exclusive bounds
    assert "0 < self.value < 100" in validation_method


def test_dataclass_generator__includes_validation_in_output():
    """Test DataclassGenerator includes validation method in generated code.

    Scenario:
        Generate dataclass from schema with constraints

    Expected Outcome:
        Generated class includes __post_init__ method with validation
    """
    # Arrange
    from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer

    schema = IRSchema(
        name="User",
        type="object",
        properties={
            "username": IRSchema(
                name="username",
                type="string",
                min_length=3,
                max_length=20,
            ),
            "age": IRSchema(
                name="age",
                type="integer",
                minimum=0,
                maximum=150,
            ),
        },
        required=["username", "age"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"User": schema})

    # Act
    generated_code = generator.generate(schema, "User", context)

    # Assert
    assert "__post_init__" in generated_code
    assert "len(self.username)" in generated_code
    assert "self.age" in generated_code
    assert "ValueError" in generated_code
