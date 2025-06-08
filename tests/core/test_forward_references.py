"""Unit test for forward references in circular dependencies."""

import unittest
from typing import Dict

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.helpers.type_helper import TypeHelper


class TestForwardReferences(unittest.TestCase):
    """Test that circular dependencies are handled with forward references."""

    def test_circular_dependency_uses_forward_reference(self) -> None:
        """
        Scenario:
            When a schema references another schema that directly or indirectly
            references the original schema, a circular dependency is created.

        Expected Outcome:
            With the unified type system, circular references are handled by direct imports.
            The system generates proper relative imports for cross-references.
        """
        # Create two schemas with circular references
        schema_a = IRSchema(
            name="MessageA",
            type="object",
            properties={
                "b_ref": IRSchema(
                    name="b_ref",
                    type="MessageB",  # Reference to another schema
                )
            },
        )

        schema_b = IRSchema(
            name="MessageB",
            type="object",
            properties={
                "a_ref": IRSchema(
                    name="a_ref",
                    type="MessageA",  # Reference back to the first schema - circular!
                )
            },
        )

        # Create a dictionary of schemas
        all_schemas: Dict[str, IRSchema] = {"MessageA": schema_a, "MessageB": schema_b}

        # Prepare schemas with generation_name and final_module_stem
        for schema_name, schema_obj in all_schemas.items():
            if schema_obj.name:  # Should always be true here
                schema_obj.generation_name = NameSanitizer.sanitize_class_name(schema_obj.name)
                schema_obj.final_module_stem = NameSanitizer.sanitize_module_name(schema_obj.name)

        # Create a render context to track imports
        context = RenderContext()
        context.set_current_file("models/message_a.py")

        # Call TypeHelper to get Python type for schema_a.properties["b_ref"]
        # which references MessageB
        property_type = TypeHelper.get_python_type_for_schema(
            schema_a.properties["b_ref"], all_schemas, context, required=True, parent_schema_name="MessageA"
        )

        # The unified system should return the correct type name
        self.assertEqual(property_type, "MessageB")

        # Get the imports as a string
        imports_str = context.render_imports()

        # With unified system, we expect a direct relative import
        self.assertIn("from ..models.message_b import MessageB", imports_str)


if __name__ == "__main__":
    unittest.main()
