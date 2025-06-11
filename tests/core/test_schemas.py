"""Tests for core.schemas module."""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
    tags: List[str] = field(default_factory=list)


@dataclass
class Address(BaseSchema):
    """Address dataclass for nested object testing."""

    street: str
    city: str
    postal_code: Optional[str] = None


@dataclass
class UserWithAddress(BaseSchema):
    """User with nested address object."""

    name: str
    address: Address


@dataclass
class Company(BaseSchema):
    """Company with list of employees."""

    name: str
    employees: List[User] = field(default_factory=list)


@dataclass
class ComplexData(BaseSchema):
    """Schema with all JSON types for comprehensive testing."""

    string_field: str
    int_field: int
    float_field: float
    bool_field: bool
    optional_field: Optional[str] = None
    list_field: List[str] = field(default_factory=list)
    dict_field: Dict[str, str] = field(default_factory=dict)


@dataclass
class UserWithMapping(BaseSchema):
    """User with field name mappings."""

    name: str
    age: int
    email: Optional[str] = None

    class Meta:
        key_transform_with_load = {"user_name": "name", "user_age": "age", "email_address": "email"}


class TestBaseSchema:
    """Test suite for BaseSchema functionality."""

    def test_from_dict__valid_dict__creates_instance(self) -> None:
        """Scenario: Validate valid dictionary data.

        Expected Outcome: Instance is created successfully.
        """
        # Arrange
        data = {"name": "John", "age": 25, "email": "john@example.com"}

        # Act
        user = User.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.name == "John"
        assert user.age == 25
        assert user.email == "john@example.com"
        assert user.active is True  # default value

    def test_from_dict__missing_optional_field__uses_default(self) -> None:
        """Scenario: Validate data missing optional field.

        Expected Outcome: Default value is used.
        """
        # Arrange
        data = {"name": "Jane", "age": 30}

        # Act
        user = User.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.name == "Jane"
        assert user.age == 30
        assert user.email is None  # default value
        assert user.active is True  # default value

    def test_from_dict__missing_required_field__raises_error(self) -> None:
        """Scenario: Validate data missing required field.

        Expected Outcome: ValueError is raised.
        """
        # Arrange
        data = {"name": "Bob"}  # missing required 'age'

        # Expected Outcome: ValueError is raised
        with pytest.raises(ValueError, match="Missing required field: 'age' for class User"):
            User.from_dict(data)  # type: ignore[attr-defined]

    def test_from_dict__non_dict_input__raises_type_error(self) -> None:
        """Scenario: Validate non-dictionary input.

        Expected Outcome: TypeError is raised.
        """
        # Expected Outcome: TypeError is raised
        with pytest.raises(TypeError, match="Input must be a dictionary, got str"):
            User.from_dict("not a dict")  # type: ignore[attr-defined]

    def test_from_dict__extra_fields__ignores_them(self) -> None:
        """Scenario: Validate data with extra fields.

        Expected Outcome: Extra fields are ignored.
        """
        # Arrange
        data = {"name": "Alice", "age": 28, "extra_field": "ignored", "another_extra": 123}

        # Act
        user = User.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.name == "Alice"
        assert user.age == 28
        assert not hasattr(user, "extra_field")
        assert not hasattr(user, "another_extra")

    def test_from_dict__with_factory_default__creates_instance(self) -> None:
        """Scenario: Validate data for class with factory default.

        Expected Outcome: Instance is created with factory default.
        """
        # Arrange
        data = {"name": "Charlie"}

        # Act
        user = UserWithFactory.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.name == "Charlie"
        assert user.tags == []  # default factory value

    def test_to_dict__basic_instance__returns_dict(self) -> None:
        """Scenario: Convert instance to dictionary.

        Expected Outcome: Dictionary with all field values.
        """
        # Arrange
        user = User(name="David", age=35, email="david@test.com", active=False)

        # Act
        result = user.to_dict()  # type: ignore[attr-defined]

        # Assert
        expected = {"name": "David", "age": 35, "email": "david@test.com", "active": False}
        assert result == expected

    def test_to_dict__exclude_none_false__includes_none_values(self) -> None:
        """Scenario: Convert instance to dict without excluding None.

        Expected Outcome: None values are included.
        """
        # Arrange
        user = User(name="Eve", age=40, email=None)

        # Act
        result = user.to_dict()  # type: ignore[attr-defined]

        # Assert
        assert result["email"] is None
        assert "email" in result

    def test_to_dict__exclude_none_true__excludes_none_values(self) -> None:
        """Scenario: Convert instance to dict excluding None values.

        Expected Outcome: None values are excluded.
        """
        # Arrange
        user = User(name="Frank", age=45, email=None)

        # Act
        result = user.to_dict(exclude_none=True)  # type: ignore[attr-defined]

        # Assert
        assert "email" not in result
        assert result == {"name": "Frank", "age": 45, "active": True}

    def test_from_dict__required_fields_only__creates_instance(self) -> None:
        """Scenario: Validate data for class with only required fields.

        Expected Outcome: Instance is created successfully.
        """
        # Arrange
        data = {"id": "prod-123", "price": 99.99}

        # Act
        product = Product.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert product.id == "prod-123"
        assert product.price == 99.99

    def test_round_trip__from_dict_then_to_dict__preserves_data(self) -> None:
        """Scenario: Create from dict then convert back to dict.

        Expected Outcome: Data is preserved through round trip.
        """
        # Arrange
        original_data = {"name": "Grace", "age": 29, "email": "grace@example.com"}

        # Act
        user = User.from_dict(original_data)  # type: ignore[attr-defined]
        dumped_data = user.to_dict()  # type: ignore[attr-defined]

        # Assert
        # Should have original data plus defaults
        expected = original_data.copy()
        expected["active"] = True  # default value added
        assert dumped_data == expected

    # Tests for legacy method compatibility
    def test_model_validate__legacy_alias__works_correctly(self) -> None:
        """Scenario: Use legacy model_validate method.

        Expected Outcome: Works the same as from_dict.
        """
        # Arrange
        data = {"name": "Legacy", "age": 25}

        # Act
        user = User.model_validate(data)

        # Assert
        assert user.name == "Legacy"
        assert user.age == 25

    def test_model_dump__legacy_alias__works_correctly(self) -> None:
        """Scenario: Use legacy model_dump method.

        Expected Outcome: Works the same as to_dict.
        """
        # Arrange
        user = User(name="Legacy", age=25)

        # Act
        result = user.model_dump()

        # Assert
        expected = {"name": "Legacy", "age": 25, "email": None, "active": True}
        assert result == expected


class TestJSONTypes:
    """Test suite for all JSON data types."""

    def test_from_dict__all_json_types__handles_correctly(self) -> None:
        """Scenario: Validate data with all JSON types.

        Expected Outcome: All types are handled correctly.
        """
        # Arrange
        data = {
            "string_field": "test_string",
            "int_field": 42,
            "float_field": 3.14159,
            "bool_field": True,
            "optional_field": "optional_value",
            "list_field": ["item1", "item2", "item3"],
            "dict_field": {"key1": "value1", "key2": "value2"},
        }

        # Act
        instance = ComplexData.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert instance.string_field == "test_string"
        assert instance.int_field == 42
        assert instance.float_field == 3.14159
        assert instance.bool_field is True
        assert instance.optional_field == "optional_value"
        assert instance.list_field == ["item1", "item2", "item3"]
        assert instance.dict_field == {"key1": "value1", "key2": "value2"}

    def test_to_dict__all_json_types__serializes_correctly(self) -> None:
        """Scenario: Convert instance with all JSON types to dict.

        Expected Outcome: All types are serialized correctly.
        """
        # Arrange
        instance = ComplexData(
            string_field="test_string",
            int_field=42,
            float_field=3.14159,
            bool_field=True,
            optional_field="optional_value",
            list_field=["item1", "item2", "item3"],
            dict_field={"key1": "value1", "key2": "value2"},
        )

        # Act
        result = instance.to_dict()  # type: ignore[attr-defined]

        # Assert
        expected = {
            "string_field": "test_string",
            "int_field": 42,
            "float_field": 3.14159,
            "bool_field": True,
            "optional_field": "optional_value",
            "list_field": ["item1", "item2", "item3"],
            "dict_field": {"key1": "value1", "key2": "value2"},
        }
        assert result == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("", ""),  # Empty string
            ("unicode_test_🌟", "unicode_test_🌟"),  # Unicode
            ("special\nchars\t", "special\nchars\t"),  # Special characters
        ],
    )
    def test_from_dict__string_edge_cases__handles_correctly(self, value: str, expected: str) -> None:
        """Scenario: Test string edge cases.

        Expected Outcome: All string variations handled correctly.
        """
        # Arrange
        data = {"name": value, "age": 25}

        # Act
        user = User.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.name == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            (0, 0),  # Zero
            (-1, -1),  # Negative
            (2**31 - 1, 2**31 - 1),  # Large positive
            (-(2**31), -(2**31)),  # Large negative
        ],
    )
    def test_from_dict__integer_edge_cases__handles_correctly(self, value: int, expected: int) -> None:
        """Scenario: Test integer edge cases.

        Expected Outcome: All integer variations handled correctly.
        """
        # Arrange
        data = {"name": "Test", "age": value}

        # Act
        user = User.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.age == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            (0.0, 0.0),  # Zero float
            (-0.0, -0.0),  # Negative zero
            (1e-10, 1e-10),  # Very small
            (1e10, 1e10),  # Very large
        ],
    )
    def test_from_dict__float_edge_cases__handles_correctly(self, value: float, expected: float) -> None:
        """Scenario: Test float edge cases.

        Expected Outcome: All float variations handled correctly.
        """
        # Arrange
        data = {"id": "test", "price": value}

        # Act
        product = Product.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert product.price == expected

    def test_from_dict__special_float_values__handles_correctly(self) -> None:
        """Scenario: Test special float values (inf, -inf, nan).

        Expected Outcome: Special values are preserved.
        """
        # Arrange & Act & Assert
        inf_data = {"id": "test", "price": float("inf")}
        inf_product = Product.from_dict(inf_data)  # type: ignore[attr-defined]
        assert math.isinf(inf_product.price) and inf_product.price > 0

        neg_inf_data = {"id": "test", "price": float("-inf")}
        neg_inf_product = Product.from_dict(neg_inf_data)  # type: ignore[attr-defined]
        assert math.isinf(neg_inf_product.price) and neg_inf_product.price < 0

        nan_data = {"id": "test", "price": float("nan")}
        nan_product = Product.from_dict(nan_data)  # type: ignore[attr-defined]
        assert math.isnan(nan_product.price)

    def test_from_dict__empty_collections__handles_correctly(self) -> None:
        """Scenario: Test empty collections.

        Expected Outcome: Empty collections are handled correctly.
        """
        # Arrange
        data = {
            "string_field": "test",
            "int_field": 1,
            "float_field": 1.0,
            "bool_field": True,
            "list_field": [],  # Empty list
            "dict_field": {},  # Empty dict
        }

        # Act
        instance = ComplexData.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert instance.list_field == []
        assert instance.dict_field == {}


class TestNestedObjects:
    """Test suite for nested BaseSchema objects."""

    def test_from_dict__nested_object__creates_correctly(self) -> None:
        """Scenario: Create instance with nested BaseSchema object.

        Expected Outcome: Nested object is created correctly.
        """
        # Arrange
        data = {"name": "John", "address": {"street": "123 Main St", "city": "Anytown", "postal_code": "12345"}}

        # Act
        user = UserWithAddress.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.name == "John"
        assert isinstance(user.address, Address)
        assert user.address.street == "123 Main St"
        assert user.address.city == "Anytown"
        assert user.address.postal_code == "12345"

    def test_to_dict__nested_object__serializes_correctly(self) -> None:
        """Scenario: Convert instance with nested object to dict.

        Expected Outcome: Nested object is serialized correctly.
        """
        # Arrange
        address = Address(street="456 Oak Ave", city="Somewhere", postal_code="67890")
        user = UserWithAddress(name="Jane", address=address)

        # Act
        result = user.to_dict()  # type: ignore[attr-defined]

        # Assert
        expected = {"name": "Jane", "address": {"street": "456 Oak Ave", "city": "Somewhere", "postal_code": "67890"}}
        assert result == expected

    def test_from_dict__nested_object_with_none__handles_correctly(self) -> None:
        """Scenario: Create nested object with None optional field.

        Expected Outcome: None values are handled correctly.
        """
        # Arrange
        data = {
            "name": "Bob",
            "address": {
                "street": "789 Pine St",
                "city": "Nowhere",
                # postal_code is missing (optional)
            },
        }

        # Act
        user = UserWithAddress.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.address.postal_code is None

    def test_to_dict__nested_object_exclude_none__works_correctly(self) -> None:
        """Scenario: Convert nested object to dict excluding None values.

        Expected Outcome: None values are excluded from nested objects.
        """
        # Arrange
        address = Address(street="789 Pine St", city="Nowhere", postal_code=None)
        user = UserWithAddress(name="Bob", address=address)

        # Act
        result = user.to_dict(exclude_none=True)  # type: ignore[attr-defined]

        # Assert
        expected = {
            "name": "Bob",
            "address": {
                "street": "789 Pine St",
                "city": "Nowhere",
                # postal_code excluded
            },
        }
        assert result == expected


class TestListOfObjects:
    """Test suite for lists containing BaseSchema objects."""

    def test_from_dict__list_of_objects__creates_correctly(self) -> None:
        """Scenario: Create instance with list of BaseSchema objects.

        Expected Outcome: List of objects is created correctly.
        """
        # Arrange
        data = {
            "name": "ACME Corp",
            "employees": [
                {"name": "Alice", "age": 30, "email": "alice@acme.com"},
                {"name": "Bob", "age": 25, "email": "bob@acme.com"},
            ],
        }

        # Act
        company = Company.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert company.name == "ACME Corp"
        assert len(company.employees) == 2
        assert all(isinstance(emp, User) for emp in company.employees)
        assert company.employees[0].name == "Alice"
        assert company.employees[1].name == "Bob"

    def test_to_dict__list_of_objects__serializes_correctly(self) -> None:
        """Scenario: Convert instance with list of objects to dict.

        Expected Outcome: List of objects is serialized correctly.
        """
        # Arrange
        employees = [
            User(name="Charlie", age=35, email="charlie@acme.com"),
            User(name="Diana", age=28, email="diana@acme.com"),
        ]
        company = Company(name="ACME Corp", employees=employees)

        # Act
        result = company.to_dict()  # type: ignore[attr-defined]

        # Assert
        expected = {
            "name": "ACME Corp",
            "employees": [
                {"name": "Charlie", "age": 35, "email": "charlie@acme.com", "active": True},
                {"name": "Diana", "age": 28, "email": "diana@acme.com", "active": True},
            ],
        }
        assert result == expected

    def test_from_dict__empty_list_of_objects__handles_correctly(self) -> None:
        """Scenario: Create instance with empty list of objects.

        Expected Outcome: Empty list is handled correctly.
        """
        # Arrange
        data = {"name": "Empty Corp", "employees": []}

        # Act
        company = Company.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert company.name == "Empty Corp"
        assert company.employees == []

    def test_from_dict__mixed_list__handles_primitives_correctly(self) -> None:
        """Scenario: Create instance with list containing non-BaseSchema objects.

        Expected Outcome: Primitive values in lists are preserved.
        """
        # Arrange
        data = {"name": "Test", "tags": ["tag1", "tag2", "tag3"]}

        # Act
        user = UserWithFactory.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.tags == ["tag1", "tag2", "tag3"]


class TestFieldMapping:
    """Test suite for field name mapping functionality."""

    def test_from_dict__with_field_mapping__maps_correctly(self) -> None:
        """Scenario: Create instance using field name mappings.

        Expected Outcome: API field names are mapped to Python field names.
        """
        # Arrange
        data = {"user_name": "Mapped User", "user_age": 30, "email_address": "mapped@example.com"}

        # Act
        user = UserWithMapping.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.name == "Mapped User"
        assert user.age == 30
        assert user.email == "mapped@example.com"

    def test_to_dict__with_field_mapping__maps_back_correctly(self) -> None:
        """Scenario: Convert instance to dict using reverse field mapping.

        Expected Outcome: Python field names are mapped back to API field names.
        """
        # Arrange
        user = UserWithMapping(name="Mapped User", age=30, email="mapped@example.com")

        # Act
        result = user.to_dict()  # type: ignore[attr-defined]

        # Assert
        expected = {"user_name": "Mapped User", "user_age": 30, "email_address": "mapped@example.com"}
        assert result == expected

    def test_from_dict__mixed_mapping__handles_correctly(self) -> None:
        """Scenario: Use mix of mapped and unmapped field names.

        Expected Outcome: Both mapped and direct field names work.
        """
        # Arrange - using direct Python field name for some fields
        data = {
            "user_name": "Mixed User",
            "age": 25,  # Direct field name, not mapped
            "email_address": "mixed@example.com",
        }

        # Act
        user = UserWithMapping.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert user.name == "Mixed User"
        assert user.age == 25
        assert user.email == "mixed@example.com"

    def test_round_trip__with_field_mapping__preserves_mapping(self) -> None:
        """Scenario: Round trip with field mapping.

        Expected Outcome: Data is preserved with correct field name mapping.
        """
        # Arrange
        original_data = {"user_name": "Round Trip", "user_age": 35, "email_address": "roundtrip@example.com"}

        # Act
        user = UserWithMapping.from_dict(original_data)  # type: ignore[attr-defined]
        result = user.to_dict()  # type: ignore[attr-defined]

        # Assert
        assert result == original_data


class TestErrorConditions:
    """Test suite for error conditions and edge cases."""

    def test_from_dict__none_input__raises_type_error(self) -> None:
        """Scenario: Pass None as input.

        Expected Outcome: TypeError is raised.
        """
        with pytest.raises(TypeError, match="Input must be a dictionary, got NoneType"):
            User.from_dict(None)  # type: ignore[attr-defined,arg-type]

    def test_from_dict__list_input__raises_type_error(self) -> None:
        """Scenario: Pass list as input.

        Expected Outcome: TypeError is raised.
        """
        with pytest.raises(TypeError, match="Input must be a dictionary, got list"):
            User.from_dict([1, 2, 3])  # type: ignore[attr-defined,arg-type]

    def test_from_dict__integer_input__raises_type_error(self) -> None:
        """Scenario: Pass integer as input.

        Expected Outcome: TypeError is raised.
        """
        with pytest.raises(TypeError, match="Input must be a dictionary, got int"):
            User.from_dict(123)  # type: ignore[attr-defined,arg-type]

    def test_from_dict__multiple_missing_required_fields__raises_error(self) -> None:
        """Scenario: Multiple required fields are missing.

        Expected Outcome: ValueError is raised for first missing field.
        """
        # Arrange - only providing optional field
        data = {"email": "test@example.com"}

        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field"):
            User.from_dict(data)  # type: ignore[attr-defined]

    def test_from_dict__nested_object_invalid_data__raises_error(self) -> None:
        """Scenario: Nested object has invalid data.

        Expected Outcome: Error is raised from nested object validation.
        """
        # Arrange - missing required field in nested object
        data = {
            "name": "Test User",
            "address": {
                "street": "123 Main St"
                # Missing required 'city' field
            },
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field: 'city' for class Address"):
            UserWithAddress.from_dict(data)  # type: ignore[attr-defined]

    def test_from_dict__type_hints_exception_fallback__handles_gracefully(self) -> None:
        """Scenario: Test type hints exception handling fallback.

        Expected Outcome: Falls back to raw annotation when get_type_hints fails.
        """
        # This is difficult to trigger directly, but we can test that the basic
        # functionality works even with complex type annotations

        # Create a schema with forward reference that might cause get_type_hints issues
        @dataclass
        class CircularTest(BaseSchema):
            name: str
            # Using string annotation that might cause get_type_hints to fail
            self_ref: Optional["CircularTest"] = None

        # Arrange
        data = {"name": "test"}

        # Act - this should work even if get_type_hints has issues
        result = CircularTest.from_dict(data)  # type: ignore[attr-defined]

        # Assert
        assert result.name == "test"
        assert result.self_ref is None
