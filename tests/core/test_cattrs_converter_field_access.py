"""
Tests for direct field access on structured dataclasses without defensive checks.

These tests validate that JSON is correctly structured into dataclasses and that
generated client code can access fields directly without getattr(), has attr(),
try/except blocks, or other defensive programming patterns.

The philosophy: If cattrs successfully structures the JSON, the fields MUST exist
with correct types. No defensive coding needed.
"""

from dataclasses import dataclass, field
from typing import List

import pytest

from pyopenapi_gen.core.cattrs_converter import structure_from_dict


@dataclass
class Product:
    """Simple product model."""

    product_id: int
    product_name: str
    unit_price: float
    in_stock: bool

    class Meta:
        key_transform_with_load = {
            "productId": "product_id",
            "productName": "product_name",
            "unitPrice": "unit_price",
            "inStock": "in_stock",
        }


@dataclass
class OrderItem:
    """Order item with nested product."""

    item_id: int
    product_info: Product
    order_quantity: int

    class Meta:
        key_transform_with_load = {
            "itemId": "item_id",
            "productInfo": "product_info",
            "orderQuantity": "order_quantity",
        }


@dataclass
class Order:
    """Order with list of items."""

    order_id: int
    customer_name: str
    order_items: List[OrderItem] = field(default_factory=list)

    class Meta:
        key_transform_with_load = {
            "orderId": "order_id",
            "customerName": "customer_name",
            "orderItems": "order_items",
        }


def test_direct_field_access__structured_object__no_defensive_checks_needed():
    """
    Test that structured objects allow direct field access without defensive checks.

    Scenario:
        Generated client code should be able to access fields directly:
        - order.order_id (not getattr(order, 'order_id', None))
        - order.customer_name (not order.__dict__.get('customer_name'))
        - No try/except needed
        - No hasattr() needed

    Expected Outcome:
        All fields are directly accessible with correct types and values.
    """
    # Arrange
    json_response = {
        "orderId": 12345,
        "customerName": "John Smith",
        "orderItems": [
            {
                "itemId": 1,
                "productInfo": {
                    "productId": 101,
                    "productName": "Widget",
                    "unitPrice": 29.99,
                    "inStock": True,
                },
                "orderQuantity": 2,
            },
            {
                "itemId": 2,
                "productInfo": {
                    "productId": 102,
                    "productName": "Gadget",
                    "unitPrice": 49.99,
                    "inStock": False,
                },
                "orderQuantity": 1,
            },
        ],
    }

    # Act
    order = structure_from_dict(json_response, Order)

    # Assert: Direct field access at all levels (no defensive checks)

    # Level 1: Root object fields
    assert order.order_id == 12345
    assert order.customer_name == "John Smith"
    assert len(order.order_items) == 2

    # Level 2: Array access and nested object fields
    first_item = order.order_items[0]
    assert first_item.item_id == 1
    assert first_item.order_quantity == 2

    # Level 3: Deeply nested object fields
    first_product = first_item.product_info
    assert first_product.product_id == 101
    assert first_product.product_name == "Widget"
    assert first_product.unit_price == 29.99
    assert first_product.in_stock is True

    # Second item
    second_item = order.order_items[1]
    assert second_item.item_id == 2
    assert second_item.product_info.product_id == 102
    assert second_item.product_info.product_name == "Gadget"


def test_direct_field_access__type_safety__correct_types_guaranteed():
    """
    Test that structured fields have correct Python types.

    Scenario:
        Generated client code relies on type hints being accurate:
        - int fields are int, not str
        - bool fields are bool, not int
        - float fields are float, not str
        - No type checking or casting needed in client code

    Expected Outcome:
        All fields have correct Python types matching the dataclass definition.
    """
    # Arrange
    json_response = {
        "orderId": 12345,  # Will be int
        "customerName": "John Smith",  # Will be str
        "orderItems": [
            {
                "itemId": 1,  # Will be int
                "productInfo": {
                    "productId": 101,  # Will be int
                    "productName": "Widget",  # Will be str
                    "unitPrice": 29.99,  # Will be float
                    "inStock": True,  # Will be bool
                },
                "orderQuantity": 2,  # Will be int
            }
        ],
    }

    # Act
    order = structure_from_dict(json_response, Order)

    # Assert: Exact type checks (not isinstance checks - exact type)
    assert type(order.order_id) is int
    assert type(order.customer_name) is str
    assert type(order.order_items) is list

    item = order.order_items[0]
    assert type(item.item_id) is int
    assert type(item.order_quantity) is int

    product = item.product_info
    assert type(product.product_id) is int
    assert type(product.product_name) is str
    assert type(product.unit_price) is float
    assert type(product.in_stock) is bool


def test_direct_field_access__arithmetic_operations__work_directly():
    """
    Test that numeric fields can be used directly in arithmetic operations.

    Scenario:
        Client code should be able to perform calculations directly on fields:
        - total_price = item.unit_price * item.quantity
        - No type casting or conversion needed
        - No defensive checks for numeric types

    Expected Outcome:
        Arithmetic operations work directly on structured numeric fields.
    """
    # Arrange
    json_response = {
        "orderId": 100,
        "customerName": "Alice",
        "orderItems": [
            {
                "itemId": 1,
                "productInfo": {
                    "productId": 201,
                    "productName": "Item A",
                    "unitPrice": 25.50,
                    "inStock": True,
                },
                "orderQuantity": 3,
            },
            {
                "itemId": 2,
                "productInfo": {
                    "productId": 202,
                    "productName": "Item B",
                    "unitPrice": 15.75,
                    "inStock": True,
                },
                "orderQuantity": 2,
            },
        ],
    }

    # Act
    order = structure_from_dict(json_response, Order)

    # Assert: Direct arithmetic operations (no type checking/casting)

    # Calculate total for first item
    item1 = order.order_items[0]
    item1_total = item1.product_info.unit_price * item1.order_quantity
    assert item1_total == 76.50  # 25.50 * 3

    # Calculate total for second item
    item2 = order.order_items[1]
    item2_total = item2.product_info.unit_price * item2.order_quantity
    assert item2_total == 31.50  # 15.75 * 2

    # Calculate order total
    order_total = sum(item.product_info.unit_price * item.order_quantity for item in order.order_items)
    assert order_total == 108.00  # 76.50 + 31.50

    # Direct comparison operations
    assert order.order_items[0].product_info.unit_price > order.order_items[1].product_info.unit_price
    assert order.order_items[0].order_quantity > order.order_items[1].order_quantity


def test_direct_field_access__boolean_operations__work_directly():
    """
    Test that boolean fields can be used directly in conditionals.

    Scenario:
        Client code should be able to use boolean fields in conditions:
        - if product.in_stock: ...
        - No defensive: if product.in_stock is True: ...
        - No defensive: if getattr(product, 'in_stock', False): ...

    Expected Outcome:
        Boolean fields work directly in if/while/and/or conditions.
    """
    # Arrange
    json_response = {
        "orderId": 200,
        "customerName": "Bob",
        "orderItems": [
            {
                "itemId": 1,
                "productInfo": {
                    "productId": 301,
                    "productName": "Available Item",
                    "unitPrice": 10.00,
                    "inStock": True,
                },
                "orderQuantity": 1,
            },
            {
                "itemId": 2,
                "productInfo": {
                    "productId": 302,
                    "productName": "Unavailable Item",
                    "unitPrice": 20.00,
                    "inStock": False,
                },
                "orderQuantity": 1,
            },
        ],
    }

    # Act
    order = structure_from_dict(json_response, Order)

    # Assert: Direct boolean usage in conditions

    # Filter available items
    available_items = [item for item in order.order_items if item.product_info.in_stock]
    assert len(available_items) == 1
    assert available_items[0].product_info.product_name == "Available Item"

    # Filter unavailable items
    unavailable_items = [item for item in order.order_items if not item.product_info.in_stock]
    assert len(unavailable_items) == 1
    assert unavailable_items[0].product_info.product_name == "Unavailable Item"

    # Boolean operations
    all_in_stock = all(item.product_info.in_stock for item in order.order_items)
    assert all_in_stock is False

    any_in_stock = any(item.product_info.in_stock for item in order.order_items)
    assert any_in_stock is True


def test_direct_field_access__string_operations__work_directly():
    """
    Test that string fields support direct string operations.

    Scenario:
        Client code should be able to perform string operations directly:
        - customer_name.upper()
        - customer_name.split()
        - f"Hello {customer_name}"
        - No None checks needed

    Expected Outcome:
        String methods work directly on structured string fields.
    """
    # Arrange
    json_response = {
        "orderId": 300,
        "customerName": "Charlie Brown",
        "orderItems": [
            {
                "itemId": 1,
                "productInfo": {
                    "productId": 401,
                    "productName": "Test Product",
                    "unitPrice": 5.00,
                    "inStock": True,
                },
                "orderQuantity": 1,
            }
        ],
    }

    # Act
    order = structure_from_dict(json_response, Order)

    # Assert: Direct string operations (no defensive checks)

    # String methods
    assert order.customer_name.upper() == "CHARLIE BROWN"
    assert order.customer_name.lower() == "charlie brown"
    assert order.customer_name.split() == ["Charlie", "Brown"]
    assert order.customer_name.startswith("Charlie")
    assert order.customer_name.endswith("Brown")

    # String formatting
    greeting = f"Hello {order.customer_name}"
    assert greeting == "Hello Charlie Brown"

    # Product name operations
    product_name = order.order_items[0].product_info.product_name
    assert product_name.replace("Test", "Demo") == "Demo Product"
    assert len(product_name) == 12
    assert "Product" in product_name


def test_direct_field_access__list_operations__work_directly():
    """
    Test that list fields support direct list operations.

    Scenario:
        Client code should be able to use list operations directly:
        - len(order.order_items)
        - order.order_items[0]
        - for item in order.order_items: ...
        - No defensive: order.order_items or []

    Expected Outcome:
        List operations work directly on structured list fields.
    """
    # Arrange
    json_response = {
        "orderId": 400,
        "customerName": "Diana",
        "orderItems": [
            {
                "itemId": 1,
                "productInfo": {"productId": 501, "productName": "Item 1", "unitPrice": 10.00, "inStock": True},
                "orderQuantity": 1,
            },
            {
                "itemId": 2,
                "productInfo": {"productId": 502, "productName": "Item 2", "unitPrice": 20.00, "inStock": True},
                "orderQuantity": 2,
            },
            {
                "itemId": 3,
                "productInfo": {"productId": 503, "productName": "Item 3", "unitPrice": 30.00, "inStock": True},
                "orderQuantity": 3,
            },
        ],
    }

    # Act
    order = structure_from_dict(json_response, Order)

    # Assert: Direct list operations (no defensive checks)

    # Length
    assert len(order.order_items) == 3

    # Indexing
    assert order.order_items[0].item_id == 1
    assert order.order_items[1].item_id == 2
    assert order.order_items[2].item_id == 3

    # Slicing
    first_two = order.order_items[:2]
    assert len(first_two) == 2
    assert first_two[0].item_id == 1
    assert first_two[1].item_id == 2

    # Iteration
    item_ids = [item.item_id for item in order.order_items]
    assert item_ids == [1, 2, 3]

    # List methods
    assert order.order_items[0] in order.order_items

    # Filtering
    high_quantity_items = [item for item in order.order_items if item.order_quantity > 1]
    assert len(high_quantity_items) == 2


def test_direct_field_access__empty_list__is_list_not_none():
    """
    Test that empty lists are structured as empty lists, not None.

    Scenario:
        Client code should be able to safely iterate empty lists:
        - for item in order.order_items: ... (no items, but no error)
        - len(order.order_items) == 0 (not None)
        - No defensive: order.order_items or []

    Expected Outcome:
        Empty JSON arrays become empty Python lists, safe for direct iteration.
    """
    # Arrange
    json_response = {"orderId": 500, "customerName": "Eve", "orderItems": []}

    # Act
    order = structure_from_dict(json_response, Order)

    # Assert: Empty list is list, not None

    # Type check
    assert type(order.order_items) is list
    assert order.order_items is not None

    # Length
    assert len(order.order_items) == 0

    # Iteration (should not raise error)
    count = 0
    for item in order.order_items:
        count += 1
    assert count == 0

    # List operations work
    assert order.order_items == []
    assert not order.order_items  # Empty list is falsy, but is still a list


def test_direct_field_access__nested_field_chain__no_intermediate_checks():
    """
    Test that deeply nested field access works without intermediate defensive checks.

    Scenario:
        Client code should be able to chain field access deeply:
        - order.order_items[0].product_info.product_name
        - No defensive checks at each level
        - No try/except blocks
        - If cattrs structured it, all fields exist

    Expected Outcome:
        Deep field chains work directly without defensive programming.
    """
    # Arrange
    json_response = {
        "orderId": 600,
        "customerName": "Frank",
        "orderItems": [
            {
                "itemId": 1,
                "productInfo": {"productId": 701, "productName": "Deep Nested Item", "unitPrice": 99.99, "inStock": True},
                "orderQuantity": 5,
            }
        ],
    }

    # Act
    order = structure_from_dict(json_response, Order)

    # Assert: Deep field chains work directly (no intermediate checks)

    # Single expression with multiple levels of nesting
    product_name = order.order_items[0].product_info.product_name
    assert product_name == "Deep Nested Item"

    # Even deeper chaining with method calls
    uppercase_name = order.order_items[0].product_info.product_name.upper()
    assert uppercase_name == "DEEP NESTED ITEM"

    # Arithmetic on deeply nested fields
    total_price = order.order_items[0].product_info.unit_price * order.order_items[0].order_quantity
    assert total_price == 499.95

    # Boolean operations on deeply nested fields
    is_available = order.order_items[0].product_info.in_stock
    assert is_available is True


@dataclass
class OptionalFieldsModel:
    """Model with optional fields."""

    required_field: str
    optional_field: str | None = None
    optional_number: int | None = None

    class Meta:
        key_transform_with_load = {
            "requiredField": "required_field",
            "optionalField": "optional_field",
            "optionalNumber": "optional_number",
        }


def test_direct_field_access__optional_fields__explicit_none_handling():
    """
    Test that optional fields are explicit about None vs missing.

    Scenario:
        Optional fields (field: Type | None) explicitly allow None:
        - If field is optional, client code MUST handle None case explicitly
        - if optional_field is not None: ...
        - optional_field or "default"
        - This is intentional - optional means "handle None"

    Expected Outcome:
        Optional fields are None when missing, and client code explicitly handles it.
    """
    # Arrange: JSON without optional fields
    json_response = {"requiredField": "required value"}

    # Act
    result = structure_from_dict(json_response, OptionalFieldsModel)

    # Assert: Optional fields are None, requiring explicit handling

    # Required field is directly accessible
    assert result.required_field == "required value"

    # Optional fields are None (explicit None, not missing attribute)
    assert result.optional_field is None
    assert result.optional_number is None

    # Client code explicitly handles None case
    display_text = result.optional_field if result.optional_field is not None else "N/A"
    assert display_text == "N/A"

    # Or with default
    display_number = result.optional_number or 0
    assert display_number == 0
