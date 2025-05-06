from pathlib import Path
from typing import Dict, List, Optional, Set

from pyopenapi_gen import IRSchema, IRSpec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.visit.model_visitor import ModelVisitor
from pyopenapi_gen.visit.visitor import Visitor

from ..context.file_manager import FileManager
from ..core.utils import Formatter, NameSanitizer
from ..core.writers.code_writer import CodeWriter

# Removed OPENAPI_TO_PYTHON_TYPES, FORMAT_TYPE_MAPPING, and MODEL_TEMPLATE constants


class ModelsEmitter:
    """
    Orchestrates the generation of model files (dataclasses, enums, type aliases).

    Uses a ModelVisitor to render code for each schema and writes it to a file.
    Handles creation of __init__.py and py.typed files.
    """

    def __init__(
        self,
        visitor: Optional[Visitor[IRSchema, str]] = None,
        overall_project_root: Optional[str] = None,
        core_package_name: str = "core",
    ) -> None:
        self.visitor: Visitor[IRSchema, str] = visitor or ModelVisitor()
        self.formatter = Formatter()
        self.overall_project_root = overall_project_root
        self.core_package_name = core_package_name

    def emit(self, spec: IRSpec, output_dir_str: str) -> list[str]:
        """Render one model file per schema under <output_dir>/models using the visitor/context/registry pattern. Returns a list of generated file paths."""
        schemas: Dict[str, IRSchema] = spec.schemas
        output_dir_path: Path = Path(output_dir_str).resolve()
        models_dir: Path = output_dir_path / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        context = RenderContext(
            file_manager=FileManager(),
            core_package_name=self.core_package_name,
            package_root_for_generated_code=str(output_dir_path),
            overall_project_root=self.overall_project_root,
        )

        if isinstance(self.visitor, ModelVisitor):
            self.visitor.schemas = schemas

        generated_files: List[str] = []
        schema_names: Set[str] = {name for name in schemas.keys() if name}

        init_path = models_dir / "__init__.py"
        pytyped_path = models_dir / "py.typed"
        if not init_path.exists():
            context.file_manager.write_file(str(init_path), "")
        if not pytyped_path.exists():
            context.file_manager.write_file(str(pytyped_path), "")
        generated_files.extend([str(init_path), str(pytyped_path)])

        for name in schema_names:
            module_name = NameSanitizer.sanitize_module_name(name)
            file_path = models_dir / f"{module_name}.py"
            context.mark_generated_module(str(file_path))

        for name, schema in schemas.items():
            if not name:
                continue

            module_name = NameSanitizer.sanitize_module_name(name)
            file_path = models_dir / f"{module_name}.py"

            context.set_current_file(str(file_path))
            model_code = self.visitor.visit(schema, context)

            if model_code.strip():
                # Get imports collected FOR THIS FILE by the visitor
                imports_code = context.render_imports()
                full_content = f"{imports_code}\n\n{model_code}"

                generated_files.append(str(file_path))
                context.file_manager.write_file(str(file_path), full_content)  # Write imports + code
            else:
                context.generated_modules.discard(str(file_path))

        self._emit_models_init(models_dir, schemas, context)
        generated_files.append(str(models_dir / "__init__.py"))

        return generated_files

    def _emit_models_init(self, models_dir: Path, schemas: Dict[str, IRSchema], context: RenderContext) -> None:
        """Generates the models/__init__.py file with imports and __all__ for non-Enum models."""
        writer = CodeWriter()
        init_path = models_dir / "__init__.py"
        context.set_current_file(str(init_path))

        writer.write_line('"""Auto-generated models package."""')  # Docstring

        # Get generated schema names
        generated_schema_names = set()
        for gen_file_path_str in context.generated_modules:
            gen_file_path = Path(gen_file_path_str)
            if (
                gen_file_path.parent == models_dir
                and gen_file_path.name != "__init__.py"
                and gen_file_path.name != "py.typed"
            ):
                # Attempt to reverse sanitize the module name back to schema name
                # This is brittle; ideally, we'd track generated schema names directly
                module_name = gen_file_path.stem
                # Find original schema name (this assumes sanitization is reversible or unique enough)
                # A better approach would be to store a map {module_name: schema_name} during generation
                original_name = next(
                    (s_name for s_name in schemas if NameSanitizer.sanitize_module_name(s_name) == module_name), None
                )
                if original_name:
                    generated_schema_names.add(original_name)

        sorted_names = sorted(list(generated_schema_names))
        all_items = []
        import_lines = []
        for name in sorted_names:
            schema = schemas.get(name)
            if not schema:
                continue  # Should not happen if name came from generated_modules

            class_name = NameSanitizer.sanitize_class_name(name)
            module_name = NameSanitizer.sanitize_module_name(name)

            # Import everything that was generated
            import_lines.append(f"from .{module_name} import {class_name}")

            # --- Add ALL generated classes/enums to __all__ ---
            all_items.append(f'"{class_name}"')
            # --- End Change ---

        # Write imports first
        for line in import_lines:
            writer.write_line(line)

        # Write __all__ on a single line if items exist
        if all_items:
            writer.write_line("")  # Blank line before __all__
            writer.write_line(f"__all__ = [{', '.join(all_items)}]")

        context.file_manager.write_file(str(init_path), writer.get_code())
