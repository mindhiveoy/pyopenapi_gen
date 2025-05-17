import logging
from pathlib import Path
from typing import Dict, List, Set

from pyopenapi_gen import IRSchema, IRSpec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.visit.model.model_visitor import ModelVisitor

# Removed OPENAPI_TO_PYTHON_TYPES, FORMAT_TYPE_MAPPING, and MODEL_TEMPLATE constants

logger = logging.getLogger(__name__)


class ModelsEmitter:
    """
    Orchestrates the generation of model files (dataclasses, enums, type aliases).

    Uses a ModelVisitor to render code for each schema and writes it to a file.
    Handles creation of __init__.py and py.typed files.
    """

    def __init__(self, context: RenderContext, parsed_schemas: Dict[str, IRSchema]):
        self.context: RenderContext = context
        self.parsed_schemas: Dict[str, IRSchema] = parsed_schemas
        self.import_collector = self.context.import_collector
        self.writer = CodeWriter()

        # DEBUG log for constructor
        with open("models_emitter_constructor_debug.txt", "w", encoding="utf-8") as debug_f:
            debug_f.write(f"MODELS_EMITTER_CONSTRUCTOR_DEBUG: Parsed schemas count: {len(self.parsed_schemas)}\n")
            for k, v_schema in self.parsed_schemas.items():
                debug_f.write(f"  SchemaKeyInConstructor: {k}, Name: {v_schema.name}, Type: {v_schema.type}\n")

    def _generate_model_file(self, schema_ir: IRSchema, models_dir: Path) -> None:
        """Generates a single Python file for a given IRSchema."""
        if not schema_ir.name:
            logger.warning(f"Skipping model generation for schema without a name: {schema_ir}")
            return

        module_name = NameSanitizer.sanitize_module_name(schema_ir.name)
        file_path = models_dir / f"{module_name}.py"

        self.context.set_current_file(str(file_path))

        visitor = ModelVisitor(schemas=self.parsed_schemas)
        rendered_model_str = visitor.visit(schema_ir, self.context)

        if not rendered_model_str.strip():
            logger.debug(f"ModelVisitor returned empty string for schema: {schema_ir.name}, skipping file generation.")
            return

        imports_str = self.context.render_imports()
        file_content = f"{imports_str}\n\n{rendered_model_str}"

        self.context.file_manager.write_file(str(file_path), file_content)
        logger.debug(f"Generated model file: {file_path} for schema: {schema_ir.name}")

    def _generate_init_py_content(self) -> str:
        """Generates the content for models/__init__.py."""
        init_writer = CodeWriter()

        # Only import List, which is needed for __all__
        init_writer.write_line("from typing import List")
        init_writer.write_line("")

        all_class_names: Set[str] = set()
        sorted_schema_items = sorted(self.parsed_schemas.items())

        with open("models_emitter_init_debug.txt", "w", encoding="utf-8") as debug_f:
            debug_f.write(
                f"MODELS_EMITTER_INIT_CONTENT_DEBUG: Processing {len(sorted_schema_items)} schemas for __init__.py\n"
            )

        for schema_key, s_schema in sorted_schema_items:
            if not s_schema.name:
                logger.warning(f"Schema with key '{schema_key}' has no name, skipping for __init__.py")
                continue

            if s_schema._from_unresolved_ref:
                logger.debug(f"Skipping schema '{s_schema.name}' in __init__ as it's an unresolved reference.")
                continue

            module_name = NameSanitizer.sanitize_module_name(s_schema.name)
            class_name = NameSanitizer.sanitize_class_name(s_schema.name)

            with open("models_emitter_init_debug.txt", "a", encoding="utf-8") as debug_f:
                debug_f.write(
                    f"  Processing for __init__: schema_key='{schema_key}', s.name='{s_schema.name}', module_name='{module_name}', class_name='{class_name}'\n"
                )

            if module_name == "__init__":
                logger.warning(f"Skipping import for schema '{s_schema.name}' as its module name became __init__.")
                continue

            init_writer.write_line(f"from .{module_name} import {class_name}")
            all_class_names.add(class_name)

        init_writer.write_line("")
        init_writer.write_line("__all__: List[str] = [")
        for name_to_export in sorted(list(all_class_names)):
            init_writer.write_line(f"    '{name_to_export}',")
        init_writer.write_line("]")

        generated_content = init_writer.get_code()

        # Write the exact generated content to a debug file for inspection
        with open("models_emitter_init_py_generated_content.txt", "w", encoding="utf-8") as debug_f:
            debug_f.write(f"--- START OF models/__init__.py CONTENT ---\n")
            debug_f.write(generated_content)
            debug_f.write(f"\n--- END OF models/__init__.py CONTENT ---")

        return generated_content

    def emit(self, spec: IRSpec, output_dir_str: str) -> list[str]:
        """Emits all model files and the models/__init__.py file."""
        models_dir = Path(output_dir_str) / "models"
        self.context.file_manager.ensure_dir(str(models_dir))

        root_init_path = Path(output_dir_str) / "__init__.py"
        if not root_init_path.exists():
            self.context.file_manager.write_file(str(root_init_path), "")

        py_typed_path = models_dir / "py.typed"
        if not py_typed_path.exists():
            self.context.file_manager.write_file(str(py_typed_path), "")

        generated_files_paths: List[str] = []

        sorted_schemas_for_files = sorted(self.parsed_schemas.values(), key=lambda s: s.name or "")

        for schema_ir_to_file in sorted_schemas_for_files:
            if schema_ir_to_file.name and not schema_ir_to_file._from_unresolved_ref:
                self._generate_model_file(schema_ir_to_file, models_dir)
                generated_files_paths.append(
                    str(models_dir / f"{NameSanitizer.sanitize_module_name(schema_ir_to_file.name)}.py")
                )
            else:
                logger.debug(
                    f"Skipping file generation for schema: name='{schema_ir_to_file.name}', "
                    f"type='{schema_ir_to_file.type}', is_ref='{schema_ir_to_file._from_unresolved_ref}'"
                )

        init_content = self._generate_init_py_content()
        init_py_path = models_dir / "__init__.py"
        self.context.file_manager.write_file(str(init_py_path), init_content)
        generated_files_paths.append(str(init_py_path))

        if not (models_dir / "py.typed").exists():
            self.context.file_manager.write_file(str(models_dir / "py.typed"), "")
        generated_files_paths.append(str(models_dir / "py.typed"))

        if not Path(output_dir_str, "__init__.py").exists():
            self.context.file_manager.write_file(str(Path(output_dir_str, "__init__.py")), "")
        generated_files_paths.append(str(Path(output_dir_str, "__init__.py")))

        return generated_files_paths
