import logging
from pathlib import Path
from typing import Dict, List, Set, Optional

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

    def _generate_model_file(self, schema_ir: IRSchema, models_dir: Path) -> Optional[str]:
        """Generates a single Python file for a given IRSchema."""
        if not schema_ir.name:
            logger.warning(f"Skipping model generation for schema without a name: {schema_ir}")
            return None

        module_name = NameSanitizer.sanitize_module_name(schema_ir.name)
        file_path = models_dir / f"{module_name}.py"

        self.context.set_current_file(str(file_path))

        visitor = ModelVisitor(schemas=self.parsed_schemas)
        rendered_model_str = visitor.visit(schema_ir, self.context)

        imports_str = self.context.render_imports()
        file_content = f"{imports_str}\n\n{rendered_model_str}"

        model_file_name = NameSanitizer.sanitize_filename(schema_ir.name)
        model_file_path = models_dir / model_file_name

        try:
            model_file_path.parent.mkdir(parents=True, exist_ok=True)

            model_file_path.write_text(file_content, encoding="utf-8")
            return str(model_file_path)
        except OSError as e:
            logger.error(
                f"Error writing model file {model_file_path if 'model_file_path' in locals() else 'UNKNOWN_PATH'}: {e}"
            )
            return None

    def _generate_init_py_content(self, generated_files_paths: List[str], models_dir: Path) -> str:
        """Generates the content for models/__init__.py."""
        init_writer = CodeWriter()

        # Only import List, which is needed for __all__
        init_writer.write_line("from typing import List")
        init_writer.write_line("")

        all_class_names: Set[str] = set()
        sorted_schema_items = sorted(self.parsed_schemas.items())

        for schema_key, s_schema in sorted_schema_items:
            if not s_schema.name:
                logger.warning(f"Schema with key '{schema_key}' has no name, skipping for __init__.py")
                continue

            if s_schema._from_unresolved_ref:
                logger.debug(f"Skipping schema '{s_schema.name}' in __init__ as it's an unresolved reference.")
                continue

            module_name = NameSanitizer.sanitize_module_name(s_schema.name)
            class_name = NameSanitizer.sanitize_class_name(s_schema.name)

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
        return generated_content

    def emit(self, spec: IRSpec, output_dir_str: str) -> list[str]:
        """Emits all model files and the models/__init__.py file."""
        logger.debug(f"ModelsEmitter.emit called. Processing {len(self.parsed_schemas)} schemas.")

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

        logger.debug(
            f"ModelsEmitter.emit: Starting loop to generate model files for {len(sorted_schemas_for_files)} sorted schemas."
        )

        for schema_ir in sorted_schemas_for_files:
            if not schema_ir.name:
                logger.debug(f"Skipping model file generation for schema without a name: {schema_ir!r}")
                continue

            if schema_ir._from_unresolved_ref or schema_ir._max_depth_exceeded:
                logger.debug(
                    f"Skipping file generation for schema: Name='{schema_ir.name}', "
                    f"IsRefPlaceholder='{schema_ir._from_unresolved_ref}', MaxDepthExceeded='{schema_ir._max_depth_exceeded}'"
                )
                continue

            generated_file: Optional[str] = None
            try:
                generated_file = self._generate_model_file(schema_ir, models_dir)
            except Exception as e:
                logger.error(
                    f"[ModelsEmitter.emit ERROR] Unhandled exception while generating model for '{schema_ir.name}'. Error: {type(e).__name__}: {e}",
                    exc_info=True,
                )

            if generated_file:
                generated_files_paths.append(generated_file)

        init_content = self._generate_init_py_content(generated_files_paths, models_dir)
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
