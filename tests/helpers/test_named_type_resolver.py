import unittest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.type_resolution.named_resolver import NamedTypeResolver


class TestNamedTypeResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.render_context = RenderContext()
        # Simulate that the generated code root is /tmp/out. This is needed for RenderContext
        # to correctly calculate relative paths from the current_file.
        self.render_context.package_root_for_generated_code = "/tmp/out"

    def test_resolve_direct_named_schema_adds_correct_relative_import(self) -> None:
        """
        Tests that resolving a schema definition (like ChildSchema) which is a named object type,
        results in its class name and adds a relative import for it if RenderContext is set correctly.
        """
        # Current file where the import will be generated
        # e.g., parent_schema.py needs to import ChildSchema
        current_generating_file_abs_path = "/tmp/out/models/parent_schema.py"
        self.render_context.set_current_file(current_generating_file_abs_path)

        child_schema_definition = IRSchema(
            name="ChildSchema", type="object", properties={"field1": IRSchema(type="string")}
        )

        all_schemas = {"ChildSchema": child_schema_definition}

        resolver = NamedTypeResolver(context=self.render_context, all_schemas=all_schemas)

        # Act: Resolve the ChildSchema definition itself.
        # This simulates SchemaTypeResolver having identified ChildSchema as the target type
        # and now calling NamedTypeResolver to get its Python class name and ensure importability.
        resolved_class_name = resolver.resolve(child_schema_definition)

        # Assert name resolution
        self.assertEqual(resolved_class_name, "ChildSchema", "Resolved class name should be correct.")

        # Assert import collection
        # NamedTypeResolver calls: context.add_import("models.child_schema", "ChildSchema")
        # RenderContext, with current_file="/tmp/out/models/parent_schema.py" and pkg_root="/tmp/out",
        # should convert "models.child_schema" to ".child_schema" for a relative import.

        expected_module_import_path = ".child_schema"  # Relative path for models.child_schema from models.parent_schema
        expected_class_name_to_import = "ChildSchema"

        # Check relative_imports directly from the collector
        relative_imports_collected = self.render_context.import_collector.relative_imports
        self.assertIn(
            expected_module_import_path,
            relative_imports_collected,
            f"Module '{expected_module_import_path}' not found in relative imports. Found: {relative_imports_collected.keys()}",
        )
        self.assertIn(
            expected_class_name_to_import,
            relative_imports_collected[expected_module_import_path],
            f"Class '{expected_class_name_to_import}' not found in relative import for module '{expected_module_import_path}'. "
            f"Found: {relative_imports_collected.get(expected_module_import_path)}",
        )


if __name__ == "__main__":
    unittest.main()
