import logging
import unittest
from typing import cast

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema

logger = logging.getLogger(__name__)
# Basic logging setup for tests if needed, e.g. to see promoter logs
# logging.basicConfig(level=logging.DEBUG)


class TestSchemaParserInlineObjectPromotion(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ParsingContext()
        # Ensure logger for parsing modules is also available for debugging if needed
        # logging.getLogger('pyopenapi_gen.core.parsing').setLevel(logging.DEBUG)

    def test_parse_schema_with_inline_object_property__promotes_and_updates_context(self) -> None:
        """
        Scenario:
            An OuterSchema has a property 'details' which is an inline object.
            This inline object is not an enum and not a $ref.
        Expected Outcome:
            - The 'details' inline object is promoted to a new global schema (e.g., 'Details' or 'OuterSchemaDetails').
            - This new global schema is added to context.parsed_schemas.
            - The 'OuterSchema.properties["details"]' IRSchema now refers to this new global schema by type.
            - The original OuterSchema is also in context.parsed_schemas.
        """
        # Arrange
        schema_name = "OuterSchema"
        openapi_node = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "details": {  # This is the inline object to be promoted
                    "type": "object",
                    "properties": {
                        "fieldA": {"type": "string", "description": "Field A"},
                        "fieldB": {"type": "integer", "description": "Field B"},
                    },
                    "required": ["fieldA"],
                    "description": "Inline details object",
                },
            },
            "required": ["id", "details"],
        }

        # Act
        outer_schema_ir = _parse_schema(schema_name, openapi_node, self.context)

        # Assert
        self.assertIsNotNone(outer_schema_ir, "Parsed outer schema IR should not be None")
        # outer_schema_ir is known to be IRSchema here by the type checker

        self.assertEqual(outer_schema_ir.name, "OuterSchema")
        self.assertEqual(outer_schema_ir.type, "object")
        self.assertIn("OuterSchema", self.context.parsed_schemas, "OuterSchema should be in context.parsed_schemas")
        self.assertIs(self.context.parsed_schemas["OuterSchema"], outer_schema_ir)

        # Check the 'details' property in OuterSchema
        details_property_ir_maybe_none = outer_schema_ir.properties.get("details")
        self.assertIsNotNone(details_property_ir_maybe_none, "Details property IR should exist in OuterSchema")
        # Now we are sure details_property_ir_maybe_none is not None, we can assign it to a new var or cast
        details_property_ir = cast(IRSchema, details_property_ir_maybe_none)

        # The .type of the property IR should be the name of the promoted schema.
        promoted_schema_name = details_property_ir.type  # This should be safe now
        self.assertIsNotNone(promoted_schema_name, "Details property IR should have a type (the promoted name)")
        # promoted_schema_name could still be None if details_property_ir.type is Optional[str]
        # So, casting to str after assertIsNotNone is appropriate.
        promoted_schema_name_str = cast(str, promoted_schema_name)

        self.assertIn(
            promoted_schema_name_str,
            self.context.parsed_schemas,
            f"Promoted schema '{promoted_schema_name_str}' not found in parsed_schemas. Keys: {list(self.context.parsed_schemas.keys())}",
        )

        promoted_schema_ir = self.context.parsed_schemas[promoted_schema_name_str]

        self.assertEqual(promoted_schema_ir.name, promoted_schema_name_str)
        self.assertEqual(promoted_schema_ir.type, "object", "Promoted schema should be of type 'object'")
        # The description of the inline object should be on the *promoted* schema.
        self.assertEqual(
            promoted_schema_ir.description,
            "Inline details object",
            "Description of promoted schema should match inline object's description",
        )

        # Verify properties of the promoted schema
        self.assertIn("fieldA", promoted_schema_ir.properties, "fieldA should be a property of the promoted schema")
        self.assertEqual(promoted_schema_ir.properties["fieldA"].type, "string")
        self.assertEqual(promoted_schema_ir.properties["fieldA"].description, "Field A")
        self.assertIn("fieldB", promoted_schema_ir.properties, "fieldB should be a property of the promoted schema")
        self.assertEqual(promoted_schema_ir.properties["fieldB"].type, "integer")
        self.assertEqual(promoted_schema_ir.properties["fieldB"].description, "Field B")
        self.assertEqual(promoted_schema_ir.required, ["fieldA"], "Required fields of promoted schema not as expected")

        # Verify the property in the parent schema now refers to the promoted one
        self.assertIs(
            details_property_ir._refers_to_schema,
            promoted_schema_ir,  # This should be safe
            "Details property IR should internally refer to the promoted schema object",
        )
        # The description on the *property reference* IR should also be consistent.
        self.assertEqual(
            details_property_ir.description,
            "Inline details object",  # This should be safe
            "Description on the property reference IR should match original inline object's description",
        )


if __name__ == "__main__":
    unittest.main()
