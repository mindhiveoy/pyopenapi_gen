import logging
import re
from pathlib import Path
from typing import List, Set, Tuple

from pyopenapi_gen.core.context import RenderContext
from pyopenapi_gen.core.utils import CodeWriter, NameSanitizer
from pyopenapi_gen.ir import IRSchema
from pyopenapi_gen.visit.model_visitor import ModelVisitor

logger = logging.getLogger(__name__)


class ModelsEmitter:
    """Emits model files (dataclasses, enums) from IRSchema definitions."""

    def __init__(self, context: RenderContext):
        self.context = context
        self.import_collector = context.import_collector
        self.writer = CodeWriter()

        # DEBUG: Check parsed_schemas at constructor time
        with open("models_emitter_constructor_debug.txt", "w", encoding="utf-8") as debug_f:
            debug_f.write(
                f"MODELS_EMITTER_CONSTRUCTOR_DEBUG: Parsed schemas count: {len(self.context.parsed_schemas)}\n"
            )
            for k in self.context.parsed_schemas.keys():
                debug_f.write(f"  SchemaKeyInConstructor: {k}\n")

    def _generate_model_file(self, schema_ir: IRSchema, models_dir: Path) -> None:
        """Generates a single Python file for a given IRSchema."""
        if not schema_ir.name:
            logger.warning(f"Skipping model generation for schema without a name: {schema_ir}")
            return

        module_name = NameSanitizer.sanitize_module_name(schema_ir.name)
        class_name = NameSanitizer.sanitize_class_name(schema_ir.name)
        file_path = models_dir / f"{module_name}.py"

        # Reset import collector for the new file
        self.import_collector.clear_current_file_imports()
        self.import_collector.set_current_file_path(file_path, self.context.package_name)

        # Instantiate ModelVisitor according to its __init__(schemas=...)
        visitor = ModelVisitor(schemas=self.context.parsed_schemas)

        # Call the generic visit method, assuming it dispatches to visit_IRSchema(schema, context)
        # ModelVisitor.visit_IRSchema returns the rendered code string.
        rendered_model_str = visitor.visit(schema_ir, self.context)

        # Get collected imports for the current file (ModelVisitor should have added to context.import_collector)
        imports_code = self.import_collector.render_imports_for_current_file()

        # The model_code is what the visitor returned.
        model_code = rendered_model_str

        full_code = imports_code + "\n\n" + model_code if imports_code else model_code

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            f.write(full_code)
        self.writer.clear()  # Clear ModelsEmitter's writer, as it's not used for model body here.
        logger.debug(f"Generated model file: {file_path} for schema: {schema_ir.name}")

    def _generate_init_py_content(self) -> str:
        """Generates the content for models/__init__.py."""
        # Reinitialize CodeWriter for __init__.py content
        init_writer = CodeWriter()

        # Standard imports often needed by generated models or __init__ itself
        init_writer.write_line("from typing import TYPE_CHECKING, List, Optional, Union, Any, Dict, Generic, TypeVar")
        init_writer.write_line("from dataclasses import dataclass, field")
        init_writer.write_line("")

        all_class_names: List[str] = []
        sorted_schema_items = sorted(self.context.parsed_schemas.items())

        for schema_key, s in sorted_schema_items:
            if not s.name:
                logger.warning(f"Schema with key '{schema_key}' has no name, skipping for __init__.py")
                continue

            module_name = NameSanitizer.sanitize_module_name(s.name)
            class_name = NameSanitizer.sanitize_class_name(s.name)

            # Print to a debug file
            with open("models_emitter_debug.txt", "a", encoding="utf-8") as debug_f:
                debug_f.write(
                    f"MODELS_EMITTER_INIT_PY_DEBUG: schema_key='{schema_key}', s.name='{s.name}', module_name='{module_name}', class_name='{class_name}'\n"
                )

            if module_name == "__init__":
                logger.warning(f"Skipping import for schema '{s.name}' as its module name is __init__.")
                continue

            init_writer.write_line(f"from .{module_name} import {class_name}")
            all_class_names.append(class_name)

        init_writer.write_line("")
        init_writer.write_line("__all__ = [")
        for name in sorted(all_class_names):
            init_writer.write_line(f"    '{name}',")
        init_writer.write_line("]")
        return str(init_writer)

    def emit_models(self, models_dir: Path) -> None:
        """Emits all model files and the models/__init__.py file."""
        models_dir.mkdir(parents=True, exist_ok=True)

        # First, generate all individual model files
        # Iterate over a copy of items in case parsing modifies the dict (should not happen here)
        sorted_schemas = sorted(self.context.parsed_schemas.values(), key=lambda s: s.name or "")

        for schema_ir in sorted_schemas:
            if schema_ir.name:  # Only generate for named schemas that are meant to be files
                self._generate_model_file(schema_ir, models_dir)
            else:
                logger.debug(f"Skipping file generation for unnamed schema: {schema_ir.type}")

        # DEBUG: Check parsed_schemas before generating __init__.py
        with open("models_emitter_emit_models_debug.txt", "w", encoding="utf-8") as debug_f:
            debug_f.write(
                f"EMIT_MODELS_DEBUG: About to generate __init__.py. Parsed schemas count: {len(self.context.parsed_schemas)}\n"
            )
            for k, v_schema in self.context.parsed_schemas.items():
                debug_f.write(f"  SchemaKey: {k}, SchemaName: {v_schema.name}, SchemaType: {v_schema.type}\n")

        # Then, generate the models/__init__.py file
        init_content = self._generate_init_py_content()
        init_file_path = models_dir / "__init__.py"
        with init_file_path.open("w", encoding="utf-8") as f:
            f.write(init_content)
        logger.info(f"Generated models/__init__.py at {init_file_path}")
