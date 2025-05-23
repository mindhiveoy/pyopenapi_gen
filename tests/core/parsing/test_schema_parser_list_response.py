from typing import Any, Dict, Mapping

import yaml

from pyopenapi_gen import IRSchema

# Assuming build_schemas is the correct entry point for parsing schemas
from pyopenapi_gen.core.loader.schemas.extractor import build_schemas
from pyopenapi_gen.core.parsing.context import ParsingContext

MINIMAL_LIST_RESPONSE_SPEC_YAML = """
openapi: 3.0.0
info:
  title: List Response Test API
  version: v1
paths:
  /items:
    get:
      summary: Get a list of items
      operationId: listItems
      responses:
        '200':
          description: A list of items with metadata
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/MyItemListResponse"
components:
  schemas:
    MyItem:
      type: object
      description: "A simple item."
      required:
        - id
        - name
      properties:
        id:
          type: string
          description: Item ID
        name:
          type: string
          description: Item Name
    PaginationMeta:
      type: object
      description: "Metadata for pagination."
      required:
        - totalItems
        - totalPages
      properties:
        totalItems:
          type: integer
          description: Total items available
        totalPages:
          type: integer
          description: Total pages available
    MyItemListResponse:
      type: "object"
      description: "Response wrapper for a list of MyItem."
      required:
        - data
        - meta
      properties:
        data:
          type: "array"
          description: "List of items."
          items:
            $ref: "#/components/schemas/MyItem"
        meta:
          $ref: "#/components/schemas/PaginationMeta"
          description: "Metadata for pagination."
"""

MINIMAL_STRING_SCHEMA_YAML = """
openapi: 3.0.0
info:
  title: Minimal String Test
  version: v1
components:
  schemas:
    SimpleString:
      type: string
      description: A very simple string type.
      example: hello
"""


def test_parse_minimal_string_schema_to_ir() -> None:
    """
    Scenario:
        A minimal OpenAPI spec with only a single, simple string schema is parsed.
        The schema has type, description, and example.

    Expected Outcome:
        The IRSchema for SimpleString should be correctly populated with its type,
        description, and example, without triggering recursive parsing errors on its metadata.
    """
    # Arrange
    raw_spec: Dict[str, Any] = yaml.safe_load(MINIMAL_STRING_SCHEMA_YAML)
    raw_schemas: Dict[str, Mapping[str, Any]] = raw_spec.get("components", {}).get("schemas", {})
    raw_components: Mapping[str, Any] = raw_spec.get("components", {})

    # Act
    parsing_context: ParsingContext = build_schemas(raw_schemas=raw_schemas, raw_components=raw_components)
    parsed_schemas: Dict[str, IRSchema] = parsing_context.parsed_schemas

    # Assert
    assert "SimpleString" in parsed_schemas
    simple_string_ir = parsed_schemas["SimpleString"]

    assert simple_string_ir.name == "SimpleString"
    assert simple_string_ir.type == "string"
    assert simple_string_ir.description == "A very simple string type."
    assert simple_string_ir.example == "hello"
    assert not simple_string_ir.properties
    assert simple_string_ir.items is None


def test_parse_list_response_schema_to_ir() -> None:
    """
    Scenario:
        A minimal OpenAPI spec string defining a typical list response pattern
        (e.g., MyItemListResponse containing List[MyItem] and PaginationMeta)
        is parsed.

    Expected Outcome:
        The parsing process should correctly translate the YAML schema definitions
        into a dictionary of IRSchema objects, with:
        - Correct names for each top-level schema (MyItem, PaginationMeta, MyItemListResponse).
        - Correct types (e.g., "object", "array").
        - Correctly structured properties, including:
            - Names of properties matching the spec (e.g., "id", "data", "totalItems").
            - For array properties (like 'data'), the 'items' attribute should be an IRSchema
              correctly representing the referenced component type (e.g., MyItem).
            - For direct object reference properties (like 'meta'), the IRSchema for the property
              should correctly indicate the name and type of the referenced component (e.g., PaginationMeta).
        - Correct 'required' fields lists.
        - Descriptions preserved.
    """
    # Arrange
    raw_spec: Dict[str, Any] = yaml.safe_load(MINIMAL_LIST_RESPONSE_SPEC_YAML)
    raw_schemas: Dict[str, Mapping[str, Any]] = raw_spec.get("components", {}).get("schemas", {})
    raw_components: Mapping[str, Any] = raw_spec.get("components", {})

    # Act
    parsing_context: ParsingContext = build_schemas(raw_schemas=raw_schemas, raw_components=raw_components)
    parsed_schemas: Dict[str, IRSchema] = parsing_context.parsed_schemas

    # Assert
    assert "MyItem" in parsed_schemas
    assert "PaginationMeta" in parsed_schemas
    assert "MyItemListResponse" in parsed_schemas

    # 1. Validate MyItem IRSchema
    my_item_ir = parsed_schemas["MyItem"]
    assert my_item_ir.name == "MyItem"
    assert my_item_ir.type == "object"
    assert my_item_ir.description == "A simple item."
    assert "id" in my_item_ir.properties
    assert "name" in my_item_ir.properties
    assert my_item_ir.properties["id"].type == "string"
    assert my_item_ir.properties["id"].description == "Item ID"
    assert my_item_ir.properties["name"].type == "string"
    assert my_item_ir.properties["name"].description == "Item Name"
    assert my_item_ir.required == ["id", "name"]

    # 2. Validate PaginationMeta IRSchema
    pagination_meta_ir = parsed_schemas["PaginationMeta"]
    assert pagination_meta_ir.name == "PaginationMeta"
    assert pagination_meta_ir.type == "object"
    assert pagination_meta_ir.description == "Metadata for pagination."
    assert "totalItems" in pagination_meta_ir.properties
    assert "totalPages" in pagination_meta_ir.properties
    assert pagination_meta_ir.properties["totalItems"].type == "integer"
    assert pagination_meta_ir.properties["totalItems"].description == "Total items available"
    assert pagination_meta_ir.properties["totalPages"].type == "integer"
    assert pagination_meta_ir.properties["totalPages"].description == "Total pages available"
    assert pagination_meta_ir.required == ["totalItems", "totalPages"]

    # 3. Validate MyItemListResponse IRSchema
    my_item_list_response_ir = parsed_schemas["MyItemListResponse"]
    assert my_item_list_response_ir.name == "MyItemListResponse"
    assert my_item_list_response_ir.type == "object"
    assert my_item_list_response_ir.description == "Response wrapper for a list of MyItem."
    assert "data" in my_item_list_response_ir.properties
    assert "meta" in my_item_list_response_ir.properties
    assert my_item_list_response_ir.required == ["data", "meta"]

    # Validate 'data' property in MyItemListResponse 
    # Note: 'data' is now promoted to a schema reference due to name sanitization
    data_property_ir = my_item_list_response_ir.properties["data"]
    assert data_property_ir.type == "Data_"  # 'data' is sanitized and promoted
    assert data_property_ir.description == "List of items."
    # The actual array schema should be referenced
    if data_property_ir._refers_to_schema:
        referred_schema = data_property_ir._refers_to_schema
        assert referred_schema.type == "array"
        assert referred_schema.items is not None
        assert referred_schema.items.name == "MyItem"
        assert referred_schema.items.type == "object"

    # Validate 'meta' property in MyItemListResponse
    meta_property_ir = my_item_list_response_ir.properties["meta"]
    assert meta_property_ir.name == "PaginationMeta"
    assert meta_property_ir.type == "object"
    assert meta_property_ir.description == "Metadata for pagination."
