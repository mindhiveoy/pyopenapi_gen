import logging
import unittest
from typing import cast

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.inline_object_promoter import _attempt_promote_inline_object

logger = logging.getLogger("test_inline_object_promoter")
logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.NullHandler())


class TestAttemptPromoteInlineObject(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ParsingContext(raw_spec_schemas={}, parsed_schemas={}, visited_refs=set())
        # Clear parsed_schemas for each test for isolation
        self.context.parsed_schemas.clear()

    def test_promote_simple_inline_object__success(self) -> None:
        """
        Scenario: A property is an inline object.
        Expected: It's promoted to a global schema, and the property now refers to it.
        """
        parent_schema_name = "ParentObject"
        property_key = "config"
        inline_object_schema = IRSchema(
            name="ParentObject.config",  # Initial contextual name from _parse_schema
            type="object",
            properties={"settingA": IRSchema(name="settingA", type="string")},
            description="Inline configuration object",
            is_nullable=False,
        )

        expected_promoted_name = "Config"
        # Simulate NameSanitizer.sanitize_class_name("config") -> "Config"
        # The actual promoter will use NameSanitizer

        promoted_property_ref_ir = _attempt_promote_inline_object(
            parent_schema_name,
            property_key,
            inline_object_schema,  # The actual object to be promoted
            self.context,
            logger,
        )

        self.assertIsNotNone(promoted_property_ref_ir)
        promoted_property_ref_ir = cast(IRSchema, promoted_property_ref_ir)
        self.assertEqual(promoted_property_ref_ir.name, property_key)
        self.assertEqual(promoted_property_ref_ir.type, expected_promoted_name)
        self.assertEqual(promoted_property_ref_ir.description, "Inline configuration object")
        self.assertEqual(promoted_property_ref_ir.is_nullable, False)
        self.assertIs(promoted_property_ref_ir._refers_to_schema, inline_object_schema)

        self.assertIn(expected_promoted_name, self.context.parsed_schemas)
        global_schema = self.context.parsed_schemas[expected_promoted_name]
        self.assertIs(global_schema, inline_object_schema)
        self.assertEqual(global_schema.name, expected_promoted_name)
        self.assertIsNotNone(global_schema.properties)
        self.assertEqual(global_schema.properties["settingA"].type, "string")

    def test_promote_inline_object__name_collision__generates_unique_name(self) -> None:
        parent_schema_name = "Order"
        property_key = "item"
        inline_object_schema = IRSchema(
            name="Order.item", type="object", properties={"id": IRSchema(name="id", type="integer")}
        )

        # Pre-populate context with a conflicting name "Item"
        self.context.parsed_schemas["Item"] = IRSchema(name="Item", type="string")
        # Pre-populate context with a conflicting name "OrderItem"
        self.context.parsed_schemas["OrderItem"] = IRSchema(name="OrderItem", type="boolean")

        expected_promoted_name = "OrderItem1"  # or Item1 depending on sanitizer and preference order

        promoted_property_ref_ir = _attempt_promote_inline_object(
            parent_schema_name, property_key, inline_object_schema, self.context, logger
        )

        self.assertIsNotNone(promoted_property_ref_ir)
        promoted_property_ref_ir = cast(IRSchema, promoted_property_ref_ir)
        self.assertEqual(promoted_property_ref_ir.type, expected_promoted_name)

        self.assertIn(expected_promoted_name, self.context.parsed_schemas)
        global_schema = self.context.parsed_schemas[expected_promoted_name]
        self.assertIs(global_schema, inline_object_schema)
        self.assertEqual(global_schema.name, expected_promoted_name)

    def test_promote_inline_object__not_object_type__does_not_promote(self) -> None:
        parent_schema_name = "Resource"
        property_key = "status"
        # Property is a string, not an object
        property_schema = IRSchema(name="Resource.status", type="string")

        promoted_property_ref_ir = _attempt_promote_inline_object(
            parent_schema_name, property_key, property_schema, self.context, logger
        )

        self.assertIsNone(promoted_property_ref_ir)
        self.assertEqual(len(self.context.parsed_schemas), 0)

    def test_promote_inline_object__already_ref__does_not_promote(self) -> None:
        parent_schema_name = "Container"
        property_key = "content"
        # Property schema is already a reference (simulated by type being a string that looks like a schema name)
        property_schema = IRSchema(name="Container.content", type="GlobalContentType")
        property_schema._from_unresolved_ref = True  # Or it has a $ref attribute in real IRSchema

        promoted_property_ref_ir = _attempt_promote_inline_object(
            parent_schema_name, property_key, property_schema, self.context, logger
        )

        self.assertIsNone(promoted_property_ref_ir)
        self.assertEqual(len(self.context.parsed_schemas), 0)

    def test_promote_inline_object__is_enum__does_not_promote(self) -> None:
        """Enums are handled by enum extractor, not object promoter."""
        parent_schema_name = "Choice"
        property_key = "option"
        property_schema = IRSchema(name="Choice.option", type="object", enum=["A", "B"])
        # Note: the type might be set to "object" by schema_parser if it's an inline enum without explicit type sometimes.
        # The promoter should specifically check `schema_obj.enum is None`.

        promoted_property_ref_ir = _attempt_promote_inline_object(
            parent_schema_name, property_key, property_schema, self.context, logger
        )

        self.assertIsNone(promoted_property_ref_ir)
        self.assertEqual(len(self.context.parsed_schemas), 0)

    def test_promote_inline_object__no_parent_name__promotes_using_prop_key(self) -> None:
        """Test that an inline object is promoted using property key if parent name is None."""
        parent_schema_name = None  # No parent context name
        property_key = "config"
        inline_object_schema = IRSchema(
            name="config", type="object", properties={"settingA": IRSchema(name="settingA", type="string")}
        )

        expected_promoted_name = "Config"  # Sanitized property_key

        promoted_property_ref_ir = _attempt_promote_inline_object(
            parent_schema_name, property_key, inline_object_schema, self.context, logger
        )

        self.assertIsNotNone(promoted_property_ref_ir)  # Expect promotion
        promoted_property_ref_ir = cast(IRSchema, promoted_property_ref_ir)
        self.assertEqual(promoted_property_ref_ir.name, property_key)
        self.assertEqual(promoted_property_ref_ir.type, expected_promoted_name)
        self.assertIs(promoted_property_ref_ir._refers_to_schema, inline_object_schema)

        self.assertIn(expected_promoted_name, self.context.parsed_schemas)
        global_schema = self.context.parsed_schemas[expected_promoted_name]
        self.assertIs(global_schema, inline_object_schema)
        self.assertEqual(global_schema.name, expected_promoted_name)


if __name__ == "__main__":
    unittest.main()
