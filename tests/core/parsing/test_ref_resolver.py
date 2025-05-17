"""
Tests for schema reference resolution.
"""

import unittest

from pyopenapi_gen.core.parsing.common.ref_resolution import resolve_schema_ref
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.ir import IRSchema


class TestRefResolver(unittest.TestCase):
    def test_resolve_ref__valid_schema__parses_schema(self) -> None:
        """
        Test that resolve_schema_ref parses the referenced schema.
        """
        context = ParsingContext()
        ref_value = "#/components/schemas/TestSchema"
        context.raw_spec_schemas = {"TestSchema": {"type": "object", "properties": {"name": {"type": "string"}}}}

        result_schema = resolve_schema_ref(ref_value, "TestSchema", context, 100, lambda x, y, z, w: IRSchema(name=x))

        self.assertIsInstance(result_schema, IRSchema)
        self.assertEqual(result_schema.name, "TestSchema")

    def test_resolve_ref__already_parsed__returns_cached(self) -> None:
        """
        Test that resolve_schema_ref returns the cached IRSchema directly.
        """
        context = ParsingContext()
        ref_value = "#/components/schemas/TestSchema"
        cached_schema = IRSchema(name="TestSchema")
        context.parsed_schemas["TestSchema"] = cached_schema

        result_schema = resolve_schema_ref(ref_value, "TestSchema", context, 100, lambda x, y, z, w: IRSchema(name=x))

        self.assertIs(result_schema, cached_schema)

    def test_resolve_ref__direct_cycle__returns_unresolved(self) -> None:
        """
        Test that resolve_schema_ref handles direct cycles.
        """
        context = ParsingContext()
        ref_to_A_from_B = "#/components/schemas/A"
        context.raw_spec_schemas = {
            "A": {"type": "object", "properties": {"b": {"$ref": "#/components/schemas/B"}}},
            "B": {"type": "object", "properties": {"a": {"$ref": "#/components/schemas/A"}}},
        }

        # First, resolve_schema_ref is called for 'A'.
        context.parsed_schemas["A"] = IRSchema(name="A")

        # Then, resolve_schema_ref is called for 'B', which references 'A'.
        result_schema = resolve_schema_ref(ref_to_A_from_B, "B", context, 100, lambda x, y, z, w: IRSchema(name=x))

        # The current resolve_schema_ref returns a basic IRSchema(name=ref_name) for cycles.
        self.assertIsInstance(result_schema, IRSchema)
        self.assertEqual(result_schema.name, "A")
        self.assertTrue(result_schema._from_unresolved_ref)

    def test_resolve_ref__missing_ref__returns_unresolved(self) -> None:
        """
        Test that resolve_schema_ref returns an IRSchema marked as _from_unresolved_ref=True.
        """
        context = ParsingContext()
        ref_value = "#/components/schemas/TestSchema"
        context.raw_spec_schemas = {}

        result_schema = resolve_schema_ref(ref_value, "TestSchema", context, 100, lambda x, y, z, w: IRSchema(name=x))

        self.assertIsInstance(result_schema, IRSchema)
        self.assertEqual(result_schema.name, "TestSchema")
        self.assertTrue(result_schema._from_unresolved_ref)

    def test_resolve_ref__non_component_ref__returns_unresolved(self) -> None:
        """
        Test that resolve_schema_ref should treat it as unresolvable.
        """
        context = ParsingContext()
        ref_value = "#/paths/~1users/get/parameters/0/schema"

        result_schema = resolve_schema_ref(ref_value, "TestSchema", context, 100, lambda x, y, z, w: IRSchema(name=x))

        self.assertIsInstance(result_schema, IRSchema)
        self.assertEqual(result_schema.name, "TestSchema")
        self.assertTrue(result_schema._from_unresolved_ref)

    def test_resolve_ref__valid_unparsed_schema__parses_schema(self) -> None:
        """
        Test that resolve_schema_ref is called for a valid, unparsed schema.
        """
        context = ParsingContext()
        ref_value = "#/components/schemas/TestCaller"
        context.raw_spec_schemas = {"TestCaller": {"type": "object", "properties": {"name": {"type": "string"}}}}

        resolved_schema = resolve_schema_ref(ref_value, "TestCaller", context, 100, lambda x, y, z, w: IRSchema(name=x))

        self.assertIsInstance(resolved_schema, IRSchema)
        self.assertEqual(resolved_schema.name, "TestCaller")
        self.assertFalse(resolved_schema._from_unresolved_ref)

    def test_resolve_ref__list_response_fallback__success(self) -> None:
        """
        Test that resolve_schema_ref successfully uses ListResponse fallback.
        """
        context = ParsingContext()
        ref_value = "#/components/schemas/UserListResponse"
        context.raw_spec_schemas = {"User": {"type": "object", "properties": {"name": {"type": "string"}}}}

        resolved_schema = resolve_schema_ref(
            ref_value, "UserListResponse", context, 100, lambda x, y, z, w: IRSchema(name=x)
        )

        self.assertIsInstance(resolved_schema, IRSchema)
        self.assertEqual(resolved_schema.name, "UserListResponse")
        self.assertEqual(resolved_schema.type, "array")
        self.assertIsInstance(resolved_schema.items, IRSchema)
        self.assertEqual(resolved_schema.items.name, "User")

    def test_resolve_ref__stripped_suffix_fallback__success(self) -> None:
        """
        Test that resolve_schema_ref successfully uses stripped suffix fallback.
        """
        context = ParsingContext()
        ref_value = "#/components/schemas/UserResponse"
        context.raw_spec_schemas = {"User": {"type": "object", "properties": {"name": {"type": "string"}}}}

        resolved_schema = resolve_schema_ref(
            ref_value, "UserResponse", context, 100, lambda x, y, z, w: IRSchema(name=x)
        )

        self.assertIsInstance(resolved_schema, IRSchema)
        self.assertEqual(resolved_schema.name, "UserResponse")
        self.assertFalse(resolved_schema._from_unresolved_ref)

    def test_resolve_ref__stripped_suffix_fallback__base_is_unresolved__returns_unresolved(self) -> None:
        """
        Test that resolve_schema_ref returns unresolved when base schema is unresolved.
        """
        context = ParsingContext()
        ref_value = "#/components/schemas/UserResponse"
        context.raw_spec_schemas = {}  # Empty schemas, so base "User" won't be found

        resolved_schema = resolve_schema_ref(
            ref_value, "UserResponse", context, 100, lambda x, y, z, w: IRSchema(name=x)
        )

        self.assertIsInstance(resolved_schema, IRSchema)
        self.assertEqual(resolved_schema.name, "UserResponse")
        self.assertTrue(resolved_schema._from_unresolved_ref)
