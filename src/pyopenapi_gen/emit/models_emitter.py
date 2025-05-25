import logging
from pathlib import Path
from typing import List, Optional

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.ir import IRSchema
from pyopenapi_gen.visit.model.model_visitor import ModelVisitor

logger = logging.getLogger(__name__)


class ModelsEmitter:
    """Emits model files (dataclasses, enums) from IRSchema definitions."""

    def __init__(self, context: RenderContext):
        self.context = context
        # self.import_collector is available via self.context.import_collector
        # self.writer an instance CodeWriter() here seems unused globally for this emitter.
        # Each file generation part either writes directly or uses a local CodeWriter.

    def _generate_model_file(self, schema_ir: IRSchema, models_dir: Path) -> Optional[str]:
        """Generates a single Python file for a given IRSchema. Returns file path if generated."""
        if not schema_ir.name:
            logger.warning(f"Skipping model generation for schema without a name: {schema_ir}")
            return None

        # Ensure context has parsed_schemas before ModelVisitor uses it
        if not self.context.parsed_schemas:
            logger.error(
                "[ModelsEmitter._generate_model_file] RenderContext is missing parsed_schemas. Cannot generate model."
            )
            return None

        module_name = NameSanitizer.sanitize_module_name(schema_ir.name)
        # class_name = NameSanitizer.sanitize_class_name(schema_ir.name) # Not directly used here for file content
        file_path = models_dir / f"{module_name}.py"

        # Set current file on RenderContext. This also resets its internal ImportCollector.
        self.context.set_current_file(str(file_path))

        # ModelsEmitter's import_collector should be the same instance as RenderContext's.
        # The line `self.import_collector = self.context.import_collector` was added in __init__
        # or after set_current_file previously. Let's ensure it's correctly synced if there was any doubt.
        current_ic = self.context.import_collector  # Use the collector from the context

        # Instantiate ModelVisitor
        # ModelVisitor will use self.context (and thus current_ic) to add imports.
        visitor = ModelVisitor(schemas=self.context.parsed_schemas)
        rendered_model_str = visitor.visit(schema_ir, self.context)

        # Get collected imports for the current file.
        imports_list = current_ic.get_import_statements()
        imports_code = "\n".join(imports_list)

        # The model_code is what the visitor returned.
        model_code = rendered_model_str

        full_code = imports_code + "\n\n" + model_code if imports_code else model_code

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            f.write(full_code)
        # self.writer.clear() # ModelsEmitter's self.writer is not used for individual model file body
        # logger.debug(f"Generated model file: {file_path} for schema: {schema_ir.name}")
        return str(file_path)

    def _generate_init_py(self, models_dir: Path) -> str:
        """Generates the models/__init__.py file and returns its path."""
        init_writer = CodeWriter()
        # ... (content generation as before) ...
        all_class_names: List[str] = []
        # Ensure self.context.parsed_schemas is not None before iterating
        if not self.context.parsed_schemas:
            logger.warning("No parsed schemas found in context for generating models/__init__.py")
            # Still create an empty __init__.py with basic imports
            init_writer.write_line(
                "from typing import List, Optional, Union, Any, Dict, Generic, TypeVar"
            )
            init_writer.write_line("from dataclasses import dataclass, field")
            init_writer.write_line("__all__ = []")
            init_content = str(init_writer)
            init_file_path = models_dir / "__init__.py"
            with init_file_path.open("w", encoding="utf-8") as f:
                f.write(init_content)
            return str(init_file_path)

        # This point onwards, self.context.parsed_schemas is guaranteed to be non-None
        sorted_schema_items = sorted(self.context.parsed_schemas.items())

        for schema_key, s in sorted_schema_items:
            if not s.name:
                logger.warning(f"Schema with key '{schema_key}' has no name, skipping for __init__.py")
                continue
            module_name = NameSanitizer.sanitize_module_name(s.name)
            class_name = NameSanitizer.sanitize_class_name(s.name)
            if module_name == "__init__":
                logger.warning(f"Skipping import for schema '{s.name}' as its module name is __init__.")
                continue
            init_writer.write_line(f"from .{module_name} import {class_name}")
            all_class_names.append(class_name)

        init_writer.write_line("from typing import List, Optional, Union, Any, Dict, Generic, TypeVar")
        init_writer.write_line("from dataclasses import dataclass, field")
        init_writer.write_line("")

        # Re-add imports for each class to ensure they are structured correctly by CodeWriter
        # This is a bit redundant if CodeWriter handles sections, but safe.
        # For __init__.py, it might be simpler to just list exports.

        init_writer.write_line("")
        init_writer.write_line("__all__ = [")
        for name in sorted(all_class_names):
            init_writer.write_line(f"    '{name}',")
        init_writer.write_line("]")
        init_content = str(init_writer)  # This needs to be CodeWriter.render() or similar if sections are used

        init_file_path = models_dir / "__init__.py"
        with init_file_path.open("w", encoding="utf-8") as f:
            f.write(init_content)
        return str(init_file_path)

    def emit(self, output_base_dir: Path) -> List[str]:
        """Emits all model files and the models/__init__.py file into <output_base_dir>/models/."""
        models_dir = output_base_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        generated_files: List[str] = []

        if not self.context.parsed_schemas:
            logger.warning("No parsed schemas found in context. Skipping model file generation.")
        else:
            sorted_schemas = sorted(self.context.parsed_schemas.values(), key=lambda s: s.name or "")
            for schema_ir in sorted_schemas:
                if schema_ir.name:
                    file_path = self._generate_model_file(schema_ir, models_dir)
                    if file_path:
                        generated_files.append(file_path)
                else:
                    # logger.debug(f"Skipping file generation for unnamed schema: {schema_ir.type}")
                    pass  # Schema has no name, already warned in _generate_model_file or skipped if truly unnamed

        init_py_path = self._generate_init_py(models_dir)
        generated_files.append(init_py_path)
        return generated_files
