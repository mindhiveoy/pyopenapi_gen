"""Tests for core.schemas module."""

from dataclasses import dataclass, field
from typing import Optional

import pytest

from pyopenapi_gen.core.schemas import BaseSchema


@dataclass
class User(BaseSchema):
    """User dataclass for BaseSchema testing."""

    name: str
    age: int
    email: Optional[str] = None
    active: bool = True


@dataclass
class Product(BaseSchema):
    """Product dataclass with required fields only."""

    id: str
    price: float


@dataclass
class UserWithFactory(BaseSchema):
    """User dataclass with default factory."""

    name: str
    tags: list = field(default_factory=list)


class TestBaseSchema:
    """Test suite for BaseSchema functionality."""

    def test_model_validate__valid_dict__creates_instance(self):
        """Scenario: Validate valid dictionary data.

        Expected Outcome: Instance is created successfully.
        """
        # Arrange
        data = {"name": "John", "age": 25, "email": "john@example.com"}

        # Act
        user = User.model_validate(data)

        # Assert
        assert user.name == "John"
        assert user.age == 25
        assert user.email == "john@example.com"
        assert user.active is True  # default value

    def test_model_validate__missing_optional_field__uses_default(self):
        """Scenario: Validate data missing optional field.

        Expected Outcome: Default value is used.
        """
        # Arrange
        data = {"name": "Jane", "age": 30}

        # Act
        user = User.model_validate(data)

        # Assert
        assert user.name == "Jane"
        assert user.age == 30
        assert user.email is None  # default value
        assert user.active is True  # default value

    def test_model_validate__missing_required_field__raises_error(self):
        """Scenario: Validate data missing required field.

        Expected Outcome: ValueError is raised.
        """
        # Arrange
        data = {"name": "Bob"}  # missing required 'age'

        # Expected Outcome: ValueError is raised
        with pytest.raises(ValueError, match="Missing required field: 'age' for class User"):
            User.model_validate(data)

    def test_model_validate__non_dict_input__raises_type_error(self):
        """Scenario: Validate non-dictionary input.

        Expected Outcome: TypeError is raised.
        """
        # Expected Outcome: TypeError is raised
        with pytest.raises(TypeError, match="Input must be a dictionary, got str"):
            User.model_validate("not a dict")

    def test_model_validate__extra_fields__ignores_them(self):
        """Scenario: Validate data with extra fields.

        Expected Outcome: Extra fields are ignored.
        """
        # Arrange
        data = {"name": "Alice", "age": 28, "extra_field": "ignored", "another_extra": 123}

        # Act
        user = User.model_validate(data)

        # Assert
        assert user.name == "Alice"
        assert user.age == 28
        assert not hasattr(user, "extra_field")
        assert not hasattr(user, "another_extra")

    def test_model_validate__with_factory_default__creates_instance(self):
        """Scenario: Validate data for class with factory default.

        Expected Outcome: Instance is created with factory default.
        """
        # Arrange
        data = {"name": "Charlie"}

        # Act
        user = UserWithFactory.model_validate(data)

        # Assert
        assert user.name == "Charlie"
        assert user.tags == []  # default factory value

    def test_model_dump__basic_instance__returns_dict(self):
        """Scenario: Convert instance to dictionary.

        Expected Outcome: Dictionary with all field values.
        """
        # Arrange
        user = User(name="David", age=35, email="david@test.com", active=False)

        # Act
        result = user.model_dump()

        # Assert
        expected = {"name": "David", "age": 35, "email": "david@test.com", "active": False}
        assert result == expected

    def test_model_dump__exclude_none_false__includes_none_values(self):
        """Scenario: Convert instance to dict without excluding None.

        Expected Outcome: None values are included.
        """
        # Arrange
        user = User(name="Eve", age=40, email=None)

        # Act
        result = user.model_dump(exclude_none=False)

        # Assert
        assert result["email"] is None
        assert "email" in result

    def test_model_dump__exclude_none_true__excludes_none_values(self):
        """Scenario: Convert instance to dict excluding None values.

        Expected Outcome: None values are excluded.
        """
        # Arrange
        user = User(name="Frank", age=45, email=None)

        # Act
        result = user.model_dump(exclude_none=True)

        # Assert
        assert "email" not in result
        assert result == {"name": "Frank", "age": 45, "active": True}

    def test_model_validate__required_fields_only__creates_instance(self):
        """Scenario: Validate data for class with only required fields.

        Expected Outcome: Instance is created successfully.
        """
        # Arrange
        data = {"id": "prod-123", "price": 99.99}

        # Act
        product = Product.model_validate(data)

        # Assert
        assert product.id == "prod-123"
        assert product.price == 99.99

    def test_round_trip__validate_then_dump__preserves_data(self):
        """Scenario: Validate data then dump it back to dict.

        Expected Outcome: Data is preserved through round trip.
        """
        # Arrange
        original_data = {"name": "Grace", "age": 29, "email": "grace@example.com"}

        # Act
        user = User.model_validate(original_data)
        dumped_data = user.model_dump()

        # Assert
        # Should have original data plus defaults
        expected = original_data.copy()
        expected["active"] = True  # default value added
        assert dumped_data == expected
