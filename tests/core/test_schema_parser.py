"""Unit tests for schema_parser.py."""

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema


def test_schema_parser_property_required_set() -> None:
    """Test for missing initialization of final_required_set in schema_parser.py."""
    # Create a schema with properties and required field to test
    schema_name = "TestSchema"
    schema_node = {
        "type": "object",
        "properties": {
            "prop1": {
                "type": "object",
                "properties": {"subprop": {"type": "string"}},
                "required": ["subprop"],  # This is what causes the issue
            },
            "prop2": {"type": "string"},
        },
        "required": ["prop1", "prop2"],
    }

    # Create a context to parse with
    context = ParsingContext(raw_spec_schemas={schema_name: schema_node}, raw_spec_components={})

    # This should not raise NameError with final_required_set
    schema_ir = _parse_schema(schema_name, schema_node, context)

    # Verify that we got a valid schema back
    assert isinstance(schema_ir, IRSchema)
    assert schema_ir.name == schema_name
    assert "prop1" in schema_ir.properties
    assert "prop2" in schema_ir.properties
    assert schema_ir.required == ["prop1", "prop2"]
