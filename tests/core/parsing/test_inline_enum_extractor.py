import unittest
import logging  # Added for logger
from typing import Any, Dict, Optional, cast

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext

# Import the actual function to be tested
from pyopenapi_gen.core.parsing.inline_enum_extractor import (
    _extract_enum_from_property_node,
    _process_standalone_inline_enum,
)
# from pyopenapi_gen.core.utils import NameSanitizer - Not directly needed if logic is in func

# Create a logger for tests, can be a mock or a real one configured for testing
logger = logging.getLogger("test_inline_enum_extractor")
logger.setLevel(logging.DEBUG)  # Or whatever level is appropriate
# To prevent logs from appearing during tests unless explicitly desired:
# logger.addHandler(logging.NullHandler())


class TestExtractAndRegisterInlineEnum(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ParsingContext(raw_spec_schemas={}, parsed_schemas={}, visited_refs=set())
        # Reset parsed_schemas for each test to ensure isolation
        self.context.parsed_schemas.clear()

    def test_extract_inline_enum__simple_case__creates_global_enum_and_returns_ref_property(self) -> None:
        """
        Scenario:
            - A property node defines an inline enum.
        Expected Outcome:
            - A new global IRSchema for the enum is created and added to context.parsed_schemas.
            - The function returns an IRSchema for the property that now refers to the global enum by type.
        """
        # Arrange
        parent_schema_name = "MyObject"
        property_key = "status"
        property_node_data: Dict[str, Any] = {
            "type": "string",
            "enum": ["active", "inactive", "pending"],
            "description": "The status of the object",
        }

        expected_enum_name = "MyObjectStatusEnum"

        actual_prop_ir = _extract_enum_from_property_node(
            parent_schema_name, property_key, property_node_data, self.context, logger
        )

        # Assert for the returned property IRSchema
        self.assertIsNotNone(actual_prop_ir)
        actual_prop_ir = cast(IRSchema, actual_prop_ir)  # for type checker
        self.assertEqual(actual_prop_ir.name, property_key)
        self.assertEqual(actual_prop_ir.type, expected_enum_name)
        self.assertEqual(actual_prop_ir.description, "The status of the object")
        self.assertIsNone(actual_prop_ir.enum)  # Property itself should not have enum values now
        self.assertFalse(actual_prop_ir.is_nullable)  # Default, not specified as nullable

        # Assert for the globally registered enum schema
        self.assertIn(expected_enum_name, self.context.parsed_schemas)
        global_enum_schema = self.context.parsed_schemas[expected_enum_name]
        self.assertEqual(global_enum_schema.name, expected_enum_name)
        self.assertEqual(global_enum_schema.type, "string")
        self.assertEqual(global_enum_schema.enum, ["active", "inactive", "pending"])
        self.assertIsNotNone(global_enum_schema.description)
        # The global enum uses the property's description if available
        self.assertEqual(global_enum_schema.description, "The status of the object")

    def test_extract_inline_enum__name_collision__generates_unique_name(self) -> None:
        """
        Scenario:
            - An inline enum is extracted, but its default generated name collides with an existing schema.
        Expected Outcome:
            - A unique name (e.g., with a counter suffix) is generated for the new enum.
            - The property refers to this unique name.
        """
        # Arrange
        parent_schema_name = "MyObject"
        property_key = "type"

        colliding_name = "MyObjectTypeEnum"
        self.context.parsed_schemas[colliding_name] = IRSchema(name=colliding_name, type="integer", enum=[1, 2, 3])

        property_node_data: Dict[str, Any] = {
            "type": "string",
            "enum": ["hardcover", "paperback"],
            "description": "Book type",
        }

        expected_unique_enum_name = "MyObjectTypeEnum1"

        actual_prop_ir = _extract_enum_from_property_node(
            parent_schema_name, property_key, property_node_data, self.context, logger
        )

        # Assert
        self.assertIsNotNone(actual_prop_ir)
        actual_prop_ir = cast(IRSchema, actual_prop_ir)
        self.assertEqual(actual_prop_ir.type, expected_unique_enum_name)
        self.assertEqual(actual_prop_ir.name, property_key)

        self.assertIn(expected_unique_enum_name, self.context.parsed_schemas)
        global_enum_schema = self.context.parsed_schemas[expected_unique_enum_name]
        self.assertEqual(global_enum_schema.name, expected_unique_enum_name)
        self.assertEqual(global_enum_schema.type, "string")
        self.assertEqual(global_enum_schema.enum, ["hardcover", "paperback"])
        self.assertIsNotNone(global_enum_schema.description)
        # The global enum uses the property's description if available
        self.assertEqual(global_enum_schema.description, "Book type")

    def test_extract_inline_enum__no_enum_keyword__returns_none(self) -> None:
        """
        Scenario:
            - The property node does not contain an "enum" keyword.
        Expected Outcome:
            - The function should return None, indicating no enum was extracted.
        """
        # Arrange
        parent_schema_name = "MyObject"
        property_key = "name"
        property_node_data: Dict[str, Any] = {"type": "string", "description": "Object name"}

        actual_prop_ir = _extract_enum_from_property_node(
            parent_schema_name, property_key, property_node_data, self.context, logger
        )
        self.assertIsNone(actual_prop_ir)
        self.assertEqual(len(self.context.parsed_schemas), 0)  # No new global schemas

    def test_extract_inline_enum__node_is_ref__returns_none(self) -> None:
        """
        Scenario:
            - The property node is a $ref.
        Expected Outcome:
            - The function should return None.
        """
        # Arrange
        parent_schema_name = "MyObject"
        property_key = "category"
        property_node_data: Dict[str, Any] = {"$ref": "#/components/schemas/CategoryEnum"}

        actual_prop_ir = _extract_enum_from_property_node(
            parent_schema_name, property_key, property_node_data, self.context, logger
        )
        self.assertIsNone(actual_prop_ir)

    def test_extract_inline_enum__parent_name_is_none__uses_anonymous_prefix(self) -> None:
        """
        Scenario:
            - The parent schema name is None.
        Expected Outcome:
            - The generated enum name uses a prefix like "AnonymousSchema".
        """
        # Arrange
        parent_schema_name = None
        property_key = "format"
        property_node_data: Dict[str, Any] = {
            "type": "string",
            "enum": ["json", "xml"],
        }
        expected_enum_name = "AnonymousSchemaFormatEnum"

        actual_prop_ir = _extract_enum_from_property_node(
            parent_schema_name, property_key, property_node_data, self.context, logger
        )

        # Assert
        self.assertIsNotNone(actual_prop_ir)
        actual_prop_ir = cast(IRSchema, actual_prop_ir)
        self.assertEqual(actual_prop_ir.type, expected_enum_name)
        self.assertIn(expected_enum_name, self.context.parsed_schemas)
        global_enum_schema = self.context.parsed_schemas[expected_enum_name]
        self.assertEqual(global_enum_schema.name, expected_enum_name)
        self.assertEqual(global_enum_schema.enum, ["json", "xml"])
        self.assertIsNotNone(global_enum_schema.description)
        # property_node_data has no description, so fallback is used for global enum
        self.assertEqual(global_enum_schema.description, f"An enumeration for {property_key}")

    def test_extract_inline_enum__explicit_type_is_integer(self) -> None:
        """
        Scenario:
            - An inline enum has an explicit type of "integer".
        Expected Outcome:
            - The created global enum IRSchema has type "integer".
        """
        # Arrange
        parent_schema_name = "Config"
        property_key = "logLevel"
        property_node_data: Dict[str, Any] = {"type": "integer", "enum": [0, 1, 2, 3], "description": "Logging level"}
        expected_enum_name = "ConfigLogLevelEnum"

        actual_prop_ir = _extract_enum_from_property_node(
            parent_schema_name, property_key, property_node_data, self.context, logger
        )

        # Assert
        self.assertIsNotNone(actual_prop_ir)
        actual_prop_ir = cast(IRSchema, actual_prop_ir)
        self.assertEqual(actual_prop_ir.type, expected_enum_name)
        self.assertIn(expected_enum_name, self.context.parsed_schemas)
        global_enum_schema = self.context.parsed_schemas[expected_enum_name]
        self.assertEqual(global_enum_schema.type, "integer")
        self.assertEqual(global_enum_schema.enum, [0, 1, 2, 3])
        self.assertIsNotNone(global_enum_schema.description)
        self.assertEqual(global_enum_schema.description, "Logging level")

    def test_extract_inline_enum__property_is_explicitly_nullable(self) -> None:
        """
        Scenario:
            - A property node defines an inline enum and is also marked as nullable: true.
        Expected Outcome:
            - The returned property IRSchema (referencing the enum) should have is_nullable=True.
            - The global enum schema itself should not be nullable unless its type array includes "null".
        """
        # Arrange
        parent_schema_name = "MyObject"
        property_key = "optional_status"
        property_node_data: Dict[str, Any] = {
            "type": "string",
            "enum": ["active", "inactive"],
            "description": "The optional status",
            "nullable": True,
        }
        expected_enum_name = "MyObjectOptionalStatusEnum"

        actual_prop_ir = _extract_enum_from_property_node(
            parent_schema_name, property_key, property_node_data, self.context, logger
        )

        # Assert for the returned property IRSchema
        self.assertIsNotNone(actual_prop_ir)
        actual_prop_ir = cast(IRSchema, actual_prop_ir)
        self.assertEqual(actual_prop_ir.name, property_key)
        self.assertEqual(actual_prop_ir.type, expected_enum_name)
        self.assertTrue(actual_prop_ir.is_nullable)

        # Assert for the globally registered enum schema
        self.assertIn(expected_enum_name, self.context.parsed_schemas)
        global_enum_schema = self.context.parsed_schemas[expected_enum_name]
        self.assertEqual(global_enum_schema.name, expected_enum_name)
        self.assertEqual(global_enum_schema.type, "string")
        self.assertFalse(global_enum_schema.is_nullable)  # Enum itself is not nullable based on this

    def test_extract_inline_enum__enum_type_array_includes_null(self) -> None:
        """
        Scenario:
            - An inline enum has its type defined as ["string", "null"].
        Expected Outcome:
            - The created global enum IRSchema should have type "string" and is_nullable=True.
            - The returned property IRSchema (referencing the enum) should also have is_nullable=True.
        """
        # Arrange
        parent_schema_name = "MyObject"
        property_key = "status_or_null"
        property_node_data: Dict[str, Any] = {
            "type": ["string", "null"],
            "enum": ["active", "inactive", None],  # OpenAPI allows null in enum if type includes null
            "description": "Status or null",
        }
        expected_enum_name = "MyObjectStatusOrNullEnum"

        actual_prop_ir = _extract_enum_from_property_node(
            parent_schema_name, property_key, property_node_data, self.context, logger
        )

        # Assert for the returned property IRSchema
        self.assertIsNotNone(actual_prop_ir)
        actual_prop_ir = cast(IRSchema, actual_prop_ir)
        self.assertEqual(actual_prop_ir.name, property_key)
        self.assertEqual(actual_prop_ir.type, expected_enum_name)
        self.assertTrue(actual_prop_ir.is_nullable)

        # Assert for the globally registered enum schema
        self.assertIn(expected_enum_name, self.context.parsed_schemas)
        global_enum_schema = self.context.parsed_schemas[expected_enum_name]
        self.assertEqual(global_enum_schema.name, expected_enum_name)
        self.assertEqual(global_enum_schema.type, ["string", "null"])  # Type as defined
        self.assertEqual(global_enum_schema.enum, ["active", "inactive", None])
        # The is_nullable for the enum itself would be true if parsed with extract_primary_type_and_nullability
        # Our current _extract_enum_from_property_node does not directly set it on new_enum_ir but it is passed to IRSchema constructor
        # Let's assume IRSchema constructor handles list type correctly for its own is_nullable or ModelsVisitor does
        # For this test, we mainly care that the property_ir_referencing_enum.is_nullable is correctly set.


if __name__ == "__main__":
    unittest.main()


class TestProcessStandaloneInlineEnum(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ParsingContext(raw_spec_schemas={}, parsed_schemas={}, visited_refs=set())
        self.logger = logging.getLogger("test_standalone_enum_processor")
        self.logger.setLevel(logging.DEBUG)
        # self.logger.addHandler(logging.NullHandler()) # Keep logs quiet during tests

    def test_node_is_direct_enum__updates_schema_obj_and_context(self) -> None:
        """
        Scenario: A schema node passed to _parse_schema is itself an enum definition.
        Expected: _process_standalone_inline_enum updates the schema_obj with enum details
                  and registers it in the context with a sanitized name.
        """
        schema_name_hint = "MyTopLevelEnum"
        node_data: Dict[str, Any] = {
            "type": "string",
            "enum": ["ALPHA", "BRAVO", "CHARLIE"],
            "description": "A top-level enum",
        }
        # Initial schema_obj as _parse_schema might create it before enum-specific processing
        initial_schema_obj = IRSchema(name=schema_name_hint, type="string", description="A top-level enum")

        # Act
        processed_schema_obj = _process_standalone_inline_enum(
            schema_name_hint, node_data, initial_schema_obj, self.context, self.logger
        )

        # Assert
        self.assertIs(processed_schema_obj, initial_schema_obj)  # Should modify in place
        self.assertEqual(processed_schema_obj.name, "MyTopLevelEnum")  # Sanitized name
        self.assertEqual(processed_schema_obj.type, "string")
        self.assertEqual(processed_schema_obj.enum, ["ALPHA", "BRAVO", "CHARLIE"])
        self.assertEqual(processed_schema_obj.description, "A top-level enum")
        self.assertIn("MyTopLevelEnum", self.context.parsed_schemas)
        self.assertIs(self.context.parsed_schemas["MyTopLevelEnum"], processed_schema_obj)

    def test_node_is_direct_enum__no_initial_name__generates_name(self) -> None:
        """
        Scenario: An inline enum without a schema_name hint (e.g. from a request body).
        Expected: A unique name is generated.
        """
        schema_name_hint = None  # e.g. schema from requestBody/response
        node_data: Dict[str, Any] = {"type": "integer", "enum": [1, 2, 3]}
        initial_schema_obj = IRSchema(name=schema_name_hint, type="integer")  # Name is None initially

        processed_schema_obj = _process_standalone_inline_enum(
            schema_name_hint, node_data, initial_schema_obj, self.context, self.logger
        )

        self.assertIsNotNone(processed_schema_obj.name)
        # Cast to str after assertIsNotNone to satisfy linter for startswith
        processed_name = cast(str, processed_schema_obj.name)
        self.assertTrue(processed_name.startswith("UnnamedEnum"))
        self.assertEqual(processed_schema_obj.enum, [1, 2, 3])
        self.assertEqual(processed_schema_obj.type, "integer")
        self.assertIn(processed_schema_obj.name, self.context.parsed_schemas)

    def test_node_is_direct_enum__name_collision__renames_uniquely(self) -> None:
        schema_name_hint = "StatusEnum"
        node_data: Dict[str, Any] = {"type": "string", "enum": ["active", "inactive"]}
        # Pre-populate context with a different schema using the same name
        self.context.parsed_schemas["StatusEnum"] = IRSchema(name="StatusEnum", type="integer")

        initial_schema_obj = IRSchema(name="StatusEnum", type="string")

        processed_schema_obj = _process_standalone_inline_enum(
            schema_name_hint, node_data, initial_schema_obj, self.context, self.logger
        )

        self.assertEqual(processed_schema_obj.name, "StatusEnum1")
        self.assertEqual(processed_schema_obj.enum, ["active", "inactive"])
        self.assertIn("StatusEnum1", self.context.parsed_schemas)
        # The original colliding schema (the integer one) should still be in the context under its original name.
        self.assertIn("StatusEnum", self.context.parsed_schemas)
        self.assertIsNot(
            self.context.parsed_schemas["StatusEnum"], processed_schema_obj
        )  # Ensure it's not the one we just processed
        self.assertEqual(
            self.context.parsed_schemas["StatusEnum"].type, "integer"
        )  # Verify it is indeed the original int enum
        # More precise check: the object associated with StatusEnum1 should be our processed_schema_obj
        self.assertIs(self.context.parsed_schemas["StatusEnum1"], processed_schema_obj)

    def test_node_not_an_enum__returns_schema_obj_unchanged_if_no_enum_in_node(self) -> None:
        schema_name_hint = "MyObject"
        node_data: Dict[str, Any] = {"type": "object", "properties": {"id": {"type": "string"}}}
        initial_schema_obj = IRSchema(
            name="MyObject", type="object", properties={"id": IRSchema(name="id", type="string")}
        )
        # Add to context as if _parse_schema did it before calling our helper
        self.context.parsed_schemas["MyObject"] = initial_schema_obj

        processed_schema_obj = _process_standalone_inline_enum(
            schema_name_hint, node_data, initial_schema_obj, self.context, self.logger
        )

        self.assertIs(processed_schema_obj, initial_schema_obj)
        self.assertIsNone(processed_schema_obj.enum)
        self.assertEqual(self.context.parsed_schemas["MyObject"].properties["id"].type, "string")

    def test_schema_obj_already_has_enum_values__does_not_overwrite(self) -> None:
        """
        Scenario: The initial schema_obj already has enum values (e.g. set by earlier _parse_schema logic).
        Expected: _process_standalone_inline_enum should not overwrite them from node_data again.
                  It might still finalize/register the name.
        """
        schema_name_hint = "PreSetEnum"
        node_data: Dict[str, Any] = {
            "type": "string",
            "enum": ["SHOULD_BE_IGNORED_A", "SHOULD_BE_IGNORED_B"],  # Node has different enum
        }
        # schema_obj already has its enum values set
        initial_schema_obj = IRSchema(name="PreSetEnum", type="string", enum=["CorrectA", "CorrectB"])
        self.context.parsed_schemas["PreSetEnum"] = initial_schema_obj

        processed_schema_obj = _process_standalone_inline_enum(
            schema_name_hint, node_data, initial_schema_obj, self.context, self.logger
        )

        self.assertIs(processed_schema_obj, initial_schema_obj)
        self.assertEqual(processed_schema_obj.name, "PreSetEnum")
        self.assertEqual(processed_schema_obj.enum, ["CorrectA", "CorrectB"])  # Original enum values preserved
        self.assertIn("PreSetEnum", self.context.parsed_schemas)

    def test_enum_with_type_array_includes_null(self) -> None:
        """
        Scenario: An enum node has type: ["string", "null"]
        Expected: The schema_obj.type should be the primary type (e.g. "string"),
                  and is_nullable should be handled by earlier parsing stages.
        """
        schema_name_hint = "NullableEnum"
        node_data: Dict[str, Any] = {"type": ["string", "null"], "enum": ["value1", None]}
        # is_nullable might be set by extract_primary_type_and_nullability before this helper
        initial_schema_obj = IRSchema(name="NullableEnum", type=None, is_nullable=True)

        processed_schema_obj = _process_standalone_inline_enum(
            schema_name_hint, node_data, initial_schema_obj, self.context, self.logger
        )

        self.assertEqual(processed_schema_obj.type, "string")  # Primary type extracted
        self.assertEqual(processed_schema_obj.enum, ["value1", None])
        self.assertTrue(processed_schema_obj.is_nullable)  # Should be preserved
        self.assertIn("NullableEnum", self.context.parsed_schemas)
