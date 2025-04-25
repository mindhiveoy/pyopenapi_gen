import pytest

from pyopenapi_gen.loader import _parse_schema, _build_schemas
from pyopenapi_gen import IRSchema


def test_parse_schema_null_node():
    """Parsing a None node returns an IRSchema with just the name."""
    schema = _parse_schema("MySchema", None, {}, {})
    assert isinstance(schema, IRSchema)
    assert schema.name == "MySchema"
    assert schema.type is None
    assert schema.properties == {}
    assert schema.items is None
    assert schema.enum is None


def test_build_schemas_and_ref_resolution():
    """_build_schemas should preload named schemas and resolve $ref chains."""
    raw_schemas = {
        "A": {
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "enum": ["a", "b"],
        },
        "B": {"$ref": "#/components/schemas/A"},
    }
    schemas = _build_schemas(raw_schemas)
    # 'A' prebuilt
    assert "A" in schemas
    # 'B' not prebuilt until referenced
    assert isinstance(schemas["A"], IRSchema)

    # Resolve B reference via parse
    b_schema = _parse_schema(
        None, {"$ref": "#/components/schemas/B"}, raw_schemas, schemas
    )
    # Should end up being same object as schemas['A']
    assert b_schema is schemas.get("B") or b_schema.name == "A"
    # Properties and enum preserved
    assert b_schema.properties.get("x").type == "string"
    assert b_schema.enum == ["a", "b"]


def test_parse_schema_with_properties_and_items():
    """_parse_schema should handle object properties and array items correctly."""
    raw_schemas = {
        "Item": {"type": "integer", "format": "int32"},
    }
    schemas = _build_schemas(raw_schemas)
    # Object with nested properties
    node_obj = {
        "type": "object",
        "properties": {"id": {"$ref": "#/components/schemas/Item"}},
    }
    obj_schema = _parse_schema(None, node_obj, raw_schemas, schemas)
    assert obj_schema.type == "object"
    assert obj_schema.properties["id"] is schemas["Item"]

    # Array of items
    node_arr = {"type": "array", "items": {"$ref": "#/components/schemas/Item"}}
    arr_schema = _parse_schema(None, node_arr, raw_schemas, schemas)
    assert arr_schema.type == "array"
    assert arr_schema.items is schemas["Item"]


def test_parse_schema_enum_and_description():
    """_parse_schema should capture enum and description fields."""
    raw_schemas = {}
    node = {"enum": [1, 2, 3], "description": "Test enum"}
    enum_schema = _parse_schema("E", node, raw_schemas, {})
    assert enum_schema.name == "E"
    assert enum_schema.enum == [1, 2, 3]
    assert enum_schema.description == "Test enum"


def test_parse_schema_cycle_ref():
    """_parse_schema should guard against infinite recursion in cyclic refs."""
    raw_schemas = {
        "C1": {"$ref": "#/components/schemas/C2"},
        "C2": {"$ref": "#/components/schemas/C1"},
    }
    schemas = {}
    # Should not infinite-loop
    c1 = _parse_schema("C1", raw_schemas["C1"], raw_schemas, schemas)
    c2 = _parse_schema("C2", raw_schemas["C2"], raw_schemas, schemas)
    # Should yield distinct IRSchema instances or handled gracefully
    assert isinstance(c1, IRSchema)
    assert isinstance(c2, IRSchema)
