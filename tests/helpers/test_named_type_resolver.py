import pytest
from pathlib import Path

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.type_resolution.named_resolver import NamedTypeResolver


class TestNamedTypeResolver:
    @pytest.fixture
    def render_context(self, tmp_path: Path) -> RenderContext:
        # Setup RenderContext with pytest's tmp_path
        project_root = tmp_path
        gen_pkg_root = project_root / "out_pkg"  # Name of the generated package
        gen_pkg_root.mkdir(parents=True, exist_ok=True)

        context = RenderContext(
            package_root_for_generated_code=str(gen_pkg_root),
            overall_project_root=str(project_root),
            core_package_name="out_pkg.core",  # Example core package name
        )
        return context

    def test_resolve_direct_named_schema_adds_correct_relative_import(
        self, render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Tests that resolving a schema definition (like ChildSchema) which is a named object type,
        results in its class name and adds a relative import for it.
        Current file: /tmp/pytest-of-user/pytest-current/test_.../out_pkg/models/parent_schema.py
        Target model: ChildSchema (in out_pkg.models.child_schema)
        Expected import: from .child_schema import ChildSchema
        """
        assert render_context.package_root_for_generated_code is not None
        gen_pkg_root_path = Path(render_context.package_root_for_generated_code)
        models_dir = gen_pkg_root_path / "models"
        models_dir.mkdir(exist_ok=True)

        # Current file where the import will be generated
        current_generating_file = models_dir / "parent_schema.py"
        current_generating_file.touch()
        render_context.set_current_file(str(current_generating_file))

        # Target schema file that needs to be imported (must exist for RenderContext)
        target_child_schema_file = models_dir / "child_schema.py"
        target_child_schema_file.touch()

        child_schema_definition = IRSchema(
            name="ChildSchema", type="object", properties={"field1": IRSchema(type="string")}
        )
        all_schemas = {"ChildSchema": child_schema_definition}

        resolver = NamedTypeResolver(context=render_context, all_schemas=all_schemas)

        # Act: Resolve the ChildSchema definition itself.
        resolved_class_name = resolver.resolve(child_schema_definition)

        # Assert name resolution
        assert resolved_class_name == "ChildSchema", "Resolved class name should be correct."

        # Assert import collection
        # NamedTypeResolver constructs logical_module as "out_pkg.models.child_schema"
        # RenderContext should make this ".child_schema"
        expected_module_import_path = ".child_schema"
        expected_class_name_to_import = "ChildSchema"

        relative_imports_collected = render_context.import_collector.relative_imports
        assert expected_module_import_path in relative_imports_collected, (
            f"Module '{expected_module_import_path}' not found in relative imports. Found: {list(relative_imports_collected.keys())}"
        )
        assert expected_class_name_to_import in relative_imports_collected[expected_module_import_path], (
            f"Class '{expected_class_name_to_import}' not found for module '{expected_module_import_path}'. Found: {relative_imports_collected[expected_module_import_path]}"
        )
