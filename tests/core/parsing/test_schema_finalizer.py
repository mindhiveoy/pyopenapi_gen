"""
Tests for the _finalize_schema_object function in schema_finalizer.py.
"""

import logging
import unittest
from typing import Any, Callable, Mapping, Optional, Set
from unittest.mock import MagicMock, patch

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_finalizer import _finalize_schema_object


class TestFinalizeSchemaObject(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = logging.getLogger("test_schema_finalizer")
        self.logger.setLevel(logging.CRITICAL)
        self.mock_parse_fn = MagicMock(
            spec=Callable[[str | None, Optional[Mapping[str, Any]], ParsingContext, int], IRSchema]
        )
        self.default_parse_fn_side_effect = lambda name, node, context, max_depth: IRSchema(
            name=name or "ParsedAnon", type="string"
        )
        self.mock_parse_fn.side_effect = self.default_parse_fn_side_effect
        self.context = ParsingContext(raw_spec_schemas={}, parsed_schemas={})
        self.patcher_process_enum = patch(
            "pyopenapi_gen.core.parsing.schema_finalizer._process_standalone_inline_enum",
            side_effect=lambda name, node, schema_obj, context, logger: schema_obj,
        )
        self.mock_process_enum = self.patcher_process_enum.start()
        self.addCleanup(self.patcher_process_enum.stop)

    def test_basic_object_creation_no_special_conditions(self) -> None:
        name = "MySimpleObject"
        node: dict[str, Any] = {"type": "object", "properties": {"id": {"type": "string"}}}
        schema_type = "object"
        final_properties_map = {"id": IRSchema(name="id", type="string")}
        merged_required_set: Set[str] = {"id"}
        schema_obj = _finalize_schema_object(
            name=name,
            node=node,
            context=self.context,
            schema_type=schema_type,
            is_nullable=False,
            any_of_schemas=None,
            one_of_schemas=None,
            parsed_all_of_components=None,
            final_properties_map=final_properties_map,
            merged_required_set=merged_required_set,
            final_items_schema=None,
            additional_properties_node=None,
            enum_node=None,
            format_node=None,
            description_node="A simple object.",
            from_unresolved_ref_node=False,
            max_depth=10,
            parse_fn=self.mock_parse_fn,
            logger=self.logger,
        )
        self.assertEqual(schema_obj.name, "MySimpleObject")
        self.assertEqual(schema_obj.type, "object")
        self.assertFalse(schema_obj.is_data_wrapper)
        self.assertIn("MySimpleObject", self.context.parsed_schemas)

    def test_is_data_wrapper_flag_true(self) -> None:
        name = "DataWrapperSchema"
        node: dict[str, Any] = {"type": "object", "properties": {"data": {"type": "string"}}, "required": ["data"]}
        schema_type = "object"
        final_properties_map = {"data": IRSchema(name="data", type="string")}
        merged_required_set: Set[str] = {"data"}
        schema_obj = _finalize_schema_object(
            name=name,
            node=node,
            context=self.context,
            schema_type=schema_type,
            is_nullable=False,
            any_of_schemas=None,
            one_of_schemas=None,
            parsed_all_of_components=None,
            final_properties_map=final_properties_map,
            merged_required_set=merged_required_set,
            final_items_schema=None,
            additional_properties_node=None,
            enum_node=None,
            format_node=None,
            description_node="A data wrapper.",
            from_unresolved_ref_node=False,
            max_depth=10,
            parse_fn=self.mock_parse_fn,
            logger=self.logger,
        )
        self.assertTrue(schema_obj.is_data_wrapper)

    def test_type_becomes_object_if_none_and_properties_exist(self) -> None:
        name = "InferredObject"
        node: dict[str, Any] = {"properties": {"key": {"type": "integer"}}}
        schema_type = None
        final_properties_map: dict[str, IRSchema] = {"key": IRSchema(name="key", type="integer")}
        schema_obj = _finalize_schema_object(
            name=name,
            node=node,
            context=self.context,
            schema_type=schema_type,
            is_nullable=False,
            any_of_schemas=None,
            one_of_schemas=None,
            parsed_all_of_components=None,
            final_properties_map=final_properties_map,
            merged_required_set=set(),
            final_items_schema=None,
            additional_properties_node=None,
            enum_node=None,
            format_node=None,
            description_node="Inferred object type.",
            from_unresolved_ref_node=False,
            max_depth=10,
            parse_fn=self.mock_parse_fn,
            logger=self.logger,
        )
        self.assertEqual(schema_obj.type, "object")

    def test_additional_properties_as_dict(self) -> None:
        name = "ObjWithAddProps"
        node: dict[str, Any] = {"type": "object"}
        additional_props_node_dict = {"type": "string", "format": "email"}
        expected_add_props_schema = IRSchema(name="ParsedAnon", type="string", format="email")

        def specific_parse_fn_side_effect(
            n_arg: str | None, nd_arg: Optional[Mapping[str, Any]], c_arg: ParsingContext, md_arg: int
        ) -> IRSchema:
            if nd_arg == additional_props_node_dict:
                return expected_add_props_schema
            return IRSchema(name=n_arg or "DefaultParsed", type="generic")

        self.mock_parse_fn.side_effect = specific_parse_fn_side_effect
        schema_obj = _finalize_schema_object(
            name=name,
            node=node,
            context=self.context,
            schema_type="object",
            is_nullable=False,
            any_of_schemas=None,
            one_of_schemas=None,
            parsed_all_of_components=None,
            final_properties_map={},
            merged_required_set=set(),
            final_items_schema=None,
            additional_properties_node=additional_props_node_dict,
            enum_node=None,
            format_node=None,
            description_node=None,
            from_unresolved_ref_node=False,
            max_depth=10,
            parse_fn=self.mock_parse_fn,
            logger=self.logger,
        )
        self.assertEqual(schema_obj.additional_properties, expected_add_props_schema)
        self.mock_parse_fn.assert_called_once_with(None, additional_props_node_dict, self.context, 10)
        self.mock_parse_fn.side_effect = self.default_parse_fn_side_effect  # Reset

    def test_updates_existing_typeless_schema_in_context(self) -> None:
        name = "ExistingSchema"
        node: dict[str, Any] = {"type": "integer"}
        schema_type = "integer"
        self.context.parsed_schemas[name] = IRSchema(name=name, type=None)
        schema_obj = _finalize_schema_object(
            name=name,
            node=node,
            context=self.context,
            schema_type=schema_type,
            is_nullable=False,
            any_of_schemas=None,
            one_of_schemas=None,
            parsed_all_of_components=None,
            final_properties_map={},
            merged_required_set=set(),
            final_items_schema=None,
            additional_properties_node=None,
            enum_node=None,
            format_node=None,
            description_node=None,
            from_unresolved_ref_node=False,
            max_depth=10,
            parse_fn=self.mock_parse_fn,
            logger=self.logger,
        )
        self.assertEqual(schema_obj.type, "integer")

    def test_type_becomes_object_for_zod_shape(self) -> None:
        name = "ZodSchema"
        node: dict[str, Any] = {"_def": {"typeName": "ZodObject", "shape": {"field1": {}}}}
        final_properties_map: dict[str, IRSchema] = {}
        schema_type = None
        schema_obj = _finalize_schema_object(
            name=name,
            node=node,
            context=self.context,
            schema_type=schema_type,
            is_nullable=False,
            any_of_schemas=None,
            one_of_schemas=None,
            parsed_all_of_components=None,
            final_properties_map=final_properties_map,
            merged_required_set=set(),
            final_items_schema=None,
            additional_properties_node=None,
            enum_node=None,
            format_node=None,
            description_node="Zod schema.",
            from_unresolved_ref_node=False,
            max_depth=10,
            parse_fn=self.mock_parse_fn,
            logger=self.logger,
        )
        self.assertEqual(schema_obj.type, "object")

    def test_inline_property_type_defaults_to_object(self) -> None:
        name = "Parent.InlineProp"
        node: dict[str, Any] = {}
        schema_type = None
        final_properties_map: dict[str, IRSchema] = {}
        schema_obj = _finalize_schema_object(
            name=name,
            node=node,
            context=self.context,
            schema_type=schema_type,
            is_nullable=False,
            any_of_schemas=None,
            one_of_schemas=None,
            parsed_all_of_components=None,
            final_properties_map=final_properties_map,
            merged_required_set=set(),
            final_items_schema=None,
            additional_properties_node=None,
            enum_node=None,
            format_node=None,
            description_node=None,
            from_unresolved_ref_node=False,
            max_depth=10,
            parse_fn=self.mock_parse_fn,
            logger=self.logger,
        )
        self.assertEqual(schema_obj.type, "object")

    def test_ensures_schema_in_context_is_updated_post_enum_processing(self) -> None:
        name = "EnumProcessedSchema"
        node: dict[str, Any] = {"type": "string", "enum": ["A", "B"]}
        schema_type = "string"
        initial_schema_obj_in_context = IRSchema(name=name, type=schema_type)
        self.context.parsed_schemas[name] = initial_schema_obj_in_context
        processed_enum_schema_obj = IRSchema(name=name, type=schema_type, description="Processed")
        self.mock_process_enum.side_effect = lambda n, nd, schema, ctx, log: processed_enum_schema_obj
        finalized_obj = _finalize_schema_object(
            name=name,
            node=node,
            context=self.context,
            schema_type=schema_type,
            is_nullable=False,
            any_of_schemas=None,
            one_of_schemas=None,
            parsed_all_of_components=None,
            final_properties_map={},
            merged_required_set=set(),
            final_items_schema=None,
            additional_properties_node=None,
            enum_node=["A", "B"],
            format_node=None,
            description_node="Original desc",
            from_unresolved_ref_node=False,
            max_depth=10,
            parse_fn=self.mock_parse_fn,
            logger=self.logger,
        )
        self.assertIs(finalized_obj, processed_enum_schema_obj)
        final_schema_in_context = self.context.parsed_schemas.get(name)
        self.assertIsNotNone(final_schema_in_context)
        assert final_schema_in_context is not None
        self.assertIs(final_schema_in_context, processed_enum_schema_obj)


if __name__ == "__main__":
    unittest.main()
