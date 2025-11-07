"""
Runtime execution tests for constraint validation.

These tests generate actual Python code, import it, and verify validation works.
This is NOT mock theatre - we're testing that validation actually catches invalid data.
"""

import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.visit.model.dataclass_generator import DataclassGenerator


def _create_module_from_code(code: str, module_name: str = "test_module"):
    """Create a Python module from generated code and import it."""
    # Write code to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        temp_path = Path(f.name)
        f.write(code)

    try:
        # Import module dynamically
        spec = importlib.util.spec_from_file_location(module_name, temp_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create module spec for {temp_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        # Clean up temp file
        temp_path.unlink(missing_ok=True)


def test_string_minlength__rejects_too_short():
    """Test string minLength validation rejects short strings.

    Scenario:
        Schema with minLength=3, create instance with 2-char string

    Expected Outcome:
        ValueError raised with descriptive message
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
            )
        },
        required=["username"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"User": schema})

    # Act - Generate code
    generated_code = generator.generate(schema, "User", context)

    # Add necessary imports
    full_code = (
        """
from dataclasses import dataclass
from typing import Any

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_minlength")

    # Assert - Invalid data raises ValueError
    with pytest.raises(ValueError) as exc_info:
        module.User(username="ab")  # Too short!

    assert "username" in str(exc_info.value)
    assert "3" in str(exc_info.value)  # Should mention minLength


def test_string_minlength__accepts_valid_length():
    """Test string minLength validation accepts valid strings.

    Scenario:
        Schema with minLength=3, create instance with 3+ char string

    Expected Outcome:
        Instance created successfully, no error
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
            )
        },
        required=["username"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"User": schema})

    # Act - Generate and execute
    generated_code = generator.generate(schema, "User", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_minlength_valid")

    # Assert - Valid data accepted
    user = module.User(username="abc")
    assert user.username == "abc"

    user2 = module.User(username="a_long_username")
    assert user2.username == "a_long_username"


def test_pattern_validation__rejects_invalid_pattern():
    """Test pattern validation rejects strings not matching regex.

    Scenario:
        Schema with pattern="^[a-z]+$", create instance with uppercase letters

    Expected Outcome:
        ValueError raised mentioning pattern mismatch
    """
    # Arrange
    schema = IRSchema(
        name="Tag",
        type="object",
        properties={
            "name": IRSchema(
                name="name",
                type="string",
                pattern="^[a-z]+$",  # Lowercase only
            )
        },
        required=["name"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Tag": schema})

    # Act - Generate and execute
    generated_code = generator.generate(schema, "Tag", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any
import re

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_pattern_invalid")

    # Assert - Invalid pattern rejected
    with pytest.raises(ValueError) as exc_info:
        module.Tag(name="ABC")  # Uppercase not allowed

    assert "name" in str(exc_info.value)
    assert "pattern" in str(exc_info.value).lower()


def test_pattern_validation__accepts_valid_pattern():
    """Test pattern validation accepts matching strings."""
    # Arrange
    schema = IRSchema(
        name="Tag",
        type="object",
        properties={
            "name": IRSchema(
                name="name",
                type="string",
                pattern="^[a-z]+$",
            )
        },
        required=["name"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Tag": schema})

    # Act
    generated_code = generator.generate(schema, "Tag", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any
import re

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_pattern_valid")

    # Assert
    tag = module.Tag(name="abc")
    assert tag.name == "abc"


def test_numeric_minimum__rejects_below_minimum():
    """Test numeric minimum validation rejects values below threshold."""
    # Arrange
    schema = IRSchema(
        name="Product",
        type="object",
        properties={
            "price": IRSchema(
                name="price",
                type="number",
                minimum=0.01,
            )
        },
        required=["price"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Product": schema})

    # Act
    generated_code = generator.generate(schema, "Product", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_minimum_invalid")

    # Assert
    with pytest.raises(ValueError) as exc_info:
        module.Product(price=0.0)  # Below minimum!

    assert "price" in str(exc_info.value)
    assert "0.01" in str(exc_info.value)


def test_numeric_minimum__accepts_valid_value():
    """Test numeric minimum validation accepts valid values."""
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

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Product": schema})

    # Act
    generated_code = generator.generate(schema, "Product", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_minimum_valid")

    # Assert
    product = module.Product(price=10.50)
    assert product.price == 10.50

    product2 = module.Product(price=0.01)  # Exactly at minimum
    assert product2.price == 0.01


def test_array_minitems__rejects_empty_array():
    """Test array minItems validation rejects arrays that are too small."""
    # Arrange
    schema = IRSchema(
        name="TagList",
        type="object",
        properties={
            "tags": IRSchema(
                name="tags",
                type="array",
                items=IRSchema(type="string"),
                min_items=1,
            )
        },
        required=["tags"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"TagList": schema})

    # Act
    generated_code = generator.generate(schema, "TagList", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any, List

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_minitems_invalid")

    # Assert
    with pytest.raises(ValueError) as exc_info:
        module.TagList(tags=[])  # Empty array!

    assert "tags" in str(exc_info.value)
    assert "1" in str(exc_info.value)


def test_unique_items__rejects_duplicates():
    """Test uniqueItems validation rejects arrays with duplicates."""
    # Arrange
    schema = IRSchema(
        name="UniqueList",
        type="object",
        properties={
            "values": IRSchema(
                name="values",
                type="array",
                items=IRSchema(type="integer"),
                unique_items=True,
            )
        },
        required=["values"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"UniqueList": schema})

    # Act
    generated_code = generator.generate(schema, "UniqueList", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any, List

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_unique_invalid")

    # Assert
    with pytest.raises(ValueError) as exc_info:
        module.UniqueList(values=[1, 2, 3, 2])  # Duplicate 2!

    assert "values" in str(exc_info.value)
    assert "unique" in str(exc_info.value).lower()


def test_unique_items__accepts_unique_values():
    """Test uniqueItems validation accepts arrays without duplicates."""
    # Arrange
    schema = IRSchema(
        name="UniqueList",
        type="object",
        properties={
            "values": IRSchema(
                name="values",
                type="array",
                items=IRSchema(type="integer"),
                unique_items=True,
            )
        },
        required=["values"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"UniqueList": schema})

    # Act
    generated_code = generator.generate(schema, "UniqueList", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any, List

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_unique_valid")

    # Assert
    obj = module.UniqueList(values=[1, 2, 3, 4])
    assert obj.values == [1, 2, 3, 4]


def test_optional_field__accepts_none_without_validation():
    """Test optional fields with constraints accept None without validation.

    Scenario:
        Optional string field with minLength constraint, pass None

    Expected Outcome:
        Instance created successfully, validation skipped for None
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
            )
        },
        required=[],  # bio is optional
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"User": schema})

    # Act
    generated_code = generator.generate(schema, "User", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_optional_none")

    # Assert - None accepted for optional field
    user = module.User(bio=None)
    assert user.bio is None


def test_optional_field__validates_when_provided():
    """Test optional fields with constraints validate when value is provided."""
    # Arrange
    schema = IRSchema(
        name="User",
        type="object",
        properties={
            "bio": IRSchema(
                name="bio",
                type="string",
                min_length=10,
            )
        },
        required=[],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"User": schema})

    # Act
    generated_code = generator.generate(schema, "User", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_optional_validate")

    # Assert - Short bio rejected even though optional
    with pytest.raises(ValueError) as exc_info:
        module.User(bio="short")  # Too short!

    assert "bio" in str(exc_info.value)
    assert "10" in str(exc_info.value)

    # Valid bio accepted
    user = module.User(bio="This is a long enough bio")
    assert "long enough" in user.bio


def test_multiple_constraints__all_validated():
    """Test that all constraints are checked, not just the first."""
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
                pattern="^[a-z0-9_]+$",
            )
        },
        required=["username"],
    )

    context = RenderContext(output_package_name="test_api", core_package_name="test_api.core")
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"User": schema})

    # Act
    generated_code = generator.generate(schema, "User", context)
    full_code = (
        """
from dataclasses import dataclass
from typing import Any
import re

class BaseSchema:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    def to_dict(self):
        return {}

"""
        + generated_code
    )

    module = _create_module_from_code(full_code, "test_multiple_constraints")

    # Assert - Length check fails first
    with pytest.raises(ValueError) as exc_info:
        module.User(username="ab")
    assert "3" in str(exc_info.value)

    # Assert - Pattern check fails
    with pytest.raises(ValueError) as exc_info:
        module.User(username="ABC")  # Valid length, invalid pattern
    assert "pattern" in str(exc_info.value).lower()

    # Assert - Valid username accepted
    user = module.User(username="john_doe_123")
    assert user.username == "john_doe_123"
