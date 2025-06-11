"""
Tests for the _parse_array_items_schema helper function.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, cast
from unittest.mock import Mock

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext

# Updated import for the new location of array_items_parser
from pyopenapi_gen.core.parsing.keywords.array_items_parser import _parse_array_items_schema


@pytest.fixture
def mock_context() -> ParsingContext:
    """Provides a mock ParsingContext."""
    return Mock(spec=ParsingContext)


@pytest.fixture
def mock_parse_fn() -> Mock:
    """Provides a mock parse_fn that returns a basic IRSchema."""
    mock_fn = Mock(name="_parse_schema_mock")
    # Default behavior: return an IRSchema based on the name it was called with
    mock_fn.side_effect = lambda name, node_data, ctx, depth: IRSchema(name=name, type="string")
    return mock_fn


class TestParseArrayItemsSchema:
    def test_simple_item_type(self, mock_context: ParsingContext, mock_parse_fn: Mock) -> None:
        """
        Scenario:
            - The `items` keyword of an array schema contains a simple type definition (e.g., {"type": "integer"}).
            - A `parent_schema_name` is provided.
        Expected Outcome:
            - The `parse_fn` (recursive schema parser) is called once.
            - The `item_name_for_parse` passed to `parse_fn` is derived from `parent_schema_name` (e.g., "MyArrayItem").
            - The `items_node_data` is passed as is to `parse_fn`.
        """
        parent_name = "MyArray"
        items_data = {"type": "integer"}
        expected_item_name = "MyArrayItem"

        _parse_array_items_schema(parent_name, items_data, mock_context, mock_parse_fn, 10)

        mock_parse_fn.assert_called_once_with(expected_item_name, items_data, mock_context, 10)

    def test_item_type_is_ref(self, mock_context: ParsingContext, mock_parse_fn: Mock) -> None:
        """
        Scenario:
            - The `items` keyword of an array schema is a $ref to a schema in `#/components/schemas/`.
            - A `parent_schema_name` is provided.
        Expected Outcome:
            - The `parse_fn` is called once.
            - The `item_name_for_parse` passed to `parse_fn` is extracted directly from the $ref path
              (e.g., "ReferencedItem").
        """
        parent_name = "ArrayOfRefs"
        items_data = {"$ref": "#/components/schemas/ReferencedItem"}
        expected_item_name = "ReferencedItem"  # Name should be extracted from $ref

        _parse_array_items_schema(parent_name, items_data, mock_context, mock_parse_fn, 10)

        mock_parse_fn.assert_called_once_with(expected_item_name, items_data, mock_context, 10)

    def test_item_type_is_ref_no_parent_name(self, mock_context: ParsingContext, mock_parse_fn: Mock) -> None:
        """
        Scenario:
            - The `items` keyword is a $ref to `#/components/schemas/`.
            - `parent_schema_name` is None.
        Expected Outcome:
            - `parse_fn` is called once.
            - `item_name_for_parse` is extracted from the $ref path.
        """
        # Arrange
        items_data = {"$ref": "#/components/schemas/AnotherItem"}
        expected_item_name = "AnotherItem"

        # Act
        _parse_array_items_schema(None, items_data, mock_context, mock_parse_fn, 10)

        # Assert
        mock_parse_fn.assert_called_once_with(expected_item_name, items_data, mock_context, 10)

    def test_item_type_simple_no_parent_name(self, mock_context: ParsingContext, mock_parse_fn: Mock) -> None:
        """
        Scenario:
            - The `items` keyword contains a simple type definition.
            - `parent_schema_name` is None.
        Expected Outcome:
            - `parse_fn` is called once.
            - `item_name_for_parse` passed to `parse_fn` is None, as there is no parent name to derive
              from and it's not a $ref.
        """
        items_data = {"type": "boolean"}
        expected_item_name = None  # No parent name, not a ref -> item name is None

        _parse_array_items_schema(None, items_data, mock_context, mock_parse_fn, 10)

        mock_parse_fn.assert_called_once_with(expected_item_name, items_data, mock_context, 10)

    def test_items_node_data_not_mapping(self, mock_context: ParsingContext, mock_parse_fn: Mock) -> None:
        """
        Scenario:
            - The `items_node_data` provided to `_parse_array_items_schema` is not a dictionary (Mapping).
            - This could be due to an invalid OpenAPI spec (e.g., `items: "string"` or `items: [{"type": "string"}]`).
        Expected Outcome:
            - The function should return `None`.
            - The `parse_fn` should not be called.
        """
        # Arrange
        # Test with a list, which is not a Mapping for schema definition
        items_data_list = [{"type": "string"}]

        result = _parse_array_items_schema(
            None, cast(Mapping[str, Any], items_data_list), mock_context, mock_parse_fn, 10
        )

        assert result is None
        mock_parse_fn.assert_not_called()

        # Test with a string
        items_data_str = "thisisnotvalid"
        result_str = _parse_array_items_schema(
            None, cast(Mapping[str, Any], items_data_str), mock_context, mock_parse_fn, 10
        )
        assert result_str is None
        mock_parse_fn.assert_not_called()

    def test_returned_schema_is_from_parse_fn(self, mock_context: ParsingContext, mock_parse_fn: Mock) -> None:
        """
        Scenario:
            - `_parse_array_items_schema` is called with valid inputs that result in a call to `parse_fn`.
        Expected Outcome:
            - The IRSchema object returned by `_parse_array_items_schema` should be the exact same object
              returned by the mocked `parse_fn`.
        """
        parent_name = "MyArray"
        items_data = {"type": "object", "properties": {"id": {"type": "integer"}}}
        expected_item_name = "MyArrayItem"

        # Configure mock_parse_fn to return a specific, identifiable IRSchema
        expected_return_schema = IRSchema(name=expected_item_name, type="object", description="Mocked schema for items")
        mock_parse_fn.side_effect = lambda name, node_data, ctx, depth: expected_return_schema

        result = _parse_array_items_schema(parent_name, items_data, mock_context, mock_parse_fn, 10)

        assert result == expected_return_schema
        mock_parse_fn.assert_called_once_with(expected_item_name, items_data, mock_context, 10)

    def test_item_type_is_ref_not_to_components_schemas(
        self, mock_context: ParsingContext, mock_parse_fn: Mock
    ) -> None:
        """
        Scenario:
            - items_node_data is a $ref that does NOT point to '#/components/schemas/'.
            - parent_schema_name is provided.
        Expected Outcome:
            - parse_fn should be called with item_name_for_parse derived from parent_schema_name (e.g., ParentItem),
              NOT from the non-standard $ref path.
        """
        # Arrange
        parent_name = "MyArrayWithLocalRef"
        items_data = {"$ref": "#/definitions/LocalDefinition"}  # Not a components/schemas ref
        # Based on current logic, item_name_for_parse should be f"{parent_name}Item"
        expected_item_name_for_parse_fn = "MyArrayWithLocalRefItem"

        # Act
        _parse_array_items_schema(parent_name, items_data, mock_context, mock_parse_fn, 10)

        # Assert
        mock_parse_fn.assert_called_once_with(expected_item_name_for_parse_fn, items_data, mock_context, 10)

    def test_items_node_data_is_empty_dict(self, mock_context: ParsingContext, mock_parse_fn: Mock) -> None:
        """
        Scenario:
            - items_node_data is an empty dictionary {}.
            - parent_schema_name is provided.
        Expected Outcome:
            - parse_fn should be called with item_name_for_parse derived from parent_schema_name
              and the empty dict as node_data.
        """
        # Arrange
        parent_name = "MyArrayWithEmptyItem"
        items_data: Dict[str, Any] = {}  # Empty dictionary
        expected_item_name_for_parse_fn = "MyArrayWithEmptyItemItem"

        # Act
        _parse_array_items_schema(parent_name, items_data, mock_context, mock_parse_fn, 10)

        # Assert
        mock_parse_fn.assert_called_once_with(expected_item_name_for_parse_fn, items_data, mock_context, 10)
