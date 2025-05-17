"""
Tests for the cyclic properties helper in schema reference resolution.
"""

import unittest

from pyopenapi_gen.core.parsing.common.ref_resolution.helpers.cyclic_properties import mark_cyclic_property_references
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.ir import IRSchema


class TestMarkCyclicPropertyReferences(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test cases."""
        self.context = ParsingContext()
        self.ref_name = "TestSchema"

    def test_mark_cyclic_property_references__no_properties__no_changes(self) -> None:
        """
        Scenario:
            - A schema has no properties
        Expected Outcome:
            - No changes are made to the schema
        """
        # Arrange
        schema = IRSchema(name=self.ref_name, type="object")

        # Act
        mark_cyclic_property_references(schema, self.ref_name, self.context)

        # Assert
        self.assertEqual(schema.properties, {})

    def test_mark_cyclic_property_references__direct_cycle__marks_property(self) -> None:
        """
        Scenario:
            - A schema has a property that directly references itself
        Expected Outcome:
            - The property is marked as unresolved
        """
        # Arrange
        prop_schema = IRSchema(name="self", type=self.ref_name)
        prop_schema._refers_to_schema = schema = IRSchema(name=self.ref_name, type="object")
        schema.properties = {"self": prop_schema}

        # Act
        mark_cyclic_property_references(schema, self.ref_name, self.context)

        # Assert
        self.assertTrue(schema.properties["self"]._from_unresolved_ref)

    def test_mark_cyclic_property_references__indirect_cycle__marks_property(self) -> None:
        """
        Scenario:
            - A schema has a property that indirectly references itself through another schema
        Expected Outcome:
            - The property is marked as unresolved
        """
        # Arrange
        intermediate_schema = IRSchema(
            name="Intermediate",
            type="object",
            properties={
                "back": IRSchema(name="back", type=self.ref_name),
            },
        )
        intermediate_schema.properties["back"]._refers_to_schema = schema = IRSchema(
            name=self.ref_name,
            type="object",
        )
        self.context.parsed_schemas["Intermediate"] = intermediate_schema

        prop_schema = IRSchema(name="forward", type="Intermediate")
        prop_schema._refers_to_schema = intermediate_schema
        schema.properties = {"forward": prop_schema}

        # Act
        mark_cyclic_property_references(schema, self.ref_name, self.context)

        # Assert
        self.assertTrue(schema.properties["forward"]._from_unresolved_ref)

    def test_mark_cyclic_property_references__no_cycle__no_changes(self) -> None:
        """
        Scenario:
            - A schema has properties that don't form a cycle
        Expected Outcome:
            - No properties are marked as unresolved
        """
        # Arrange
        prop_schema = IRSchema(name="other", type="string")
        prop_schema._refers_to_schema = IRSchema(name="String", type="string")
        schema = IRSchema(
            name=self.ref_name,
            type="object",
            properties={"other": prop_schema},
        )

        # Act
        mark_cyclic_property_references(schema, self.ref_name, self.context)

        # Assert
        self.assertFalse(schema.properties["other"]._from_unresolved_ref)

    def test_mark_cyclic_property_references__multiple_cycles__marks_all_cyclic_properties(self) -> None:
        """
        Scenario:
            - A schema has multiple properties that form cycles
        Expected Outcome:
            - All properties involved in cycles are marked as unresolved
        """
        # Arrange
        schema = IRSchema(name=self.ref_name, type="object")
        prop1 = IRSchema(name="self", type=self.ref_name)
        prop1._refers_to_schema = schema
        prop2 = IRSchema(name="other", type="string")
        prop2._refers_to_schema = IRSchema(name="String", type="string")
        prop3 = IRSchema(name="cycle", type=self.ref_name)
        prop3._refers_to_schema = schema
        schema.properties = {
            "self": prop1,
            "other": prop2,
            "cycle": prop3,
        }

        # Act
        mark_cyclic_property_references(schema, self.ref_name, self.context)

        # Assert
        self.assertTrue(schema.properties["self"]._from_unresolved_ref)
        self.assertFalse(schema.properties["other"]._from_unresolved_ref)
        self.assertTrue(schema.properties["cycle"]._from_unresolved_ref)
