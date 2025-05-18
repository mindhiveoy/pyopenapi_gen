import logging
import os
from pathlib import Path
from typing import List

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import CodeWriter, NameSanitizer
from pyopenapi_gen.ir import IRSchema
from pyopenapi_gen.visit.model.model_visitor import ModelVisitor

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

        # Prepare current_ic for rendering imports by setting its path context.
        current_module_dot_path = self.context.get_current_module_dot_path()

        package_name_for_collector = None
        if self.context.package_root_for_generated_code and self.context.overall_project_root:
            abs_pkg_root = os.path.abspath(self.context.package_root_for_generated_code)
            abs_overall_root = os.path.abspath(self.context.overall_project_root)
            if abs_pkg_root.startswith(abs_overall_root) and abs_pkg_root != abs_overall_root:
                rel_pkg_root_dir = os.path.relpath(abs_pkg_root, abs_overall_root)
                if rel_pkg_root_dir and rel_pkg_root_dir != ".":
                    package_name_for_collector = rel_pkg_root_dir.replace(os.sep, ".")
            elif abs_pkg_root == abs_overall_root:  # Package root is the project root
                package_name_for_collector = None  # No base package prefix for module paths
            else:  # package_root is not under overall_project_root or is outside, use its own base name
                base_name = os.path.basename(abs_pkg_root)
                if base_name and base_name != ".":
                    package_name_for_collector = base_name
        elif self.context.package_root_for_generated_code:  # Only pkg root is given
            base_name = os.path.basename(os.path.abspath(self.context.package_root_for_generated_code))
            if base_name and base_name != ".":
                package_name_for_collector = base_name

        logger.debug(
            f"[ModelsEmitter] Setting ImportCollector context: mod_path='{current_module_dot_path}', pkg_root_for_ic='{package_name_for_collector}', core='{self.context.core_package_name}'"
        )
        current_ic.set_current_file_context_for_rendering(
            current_module_dot_path=current_module_dot_path,
            package_root=package_name_for_collector,
            core_package_name_for_absolute_treatment=self.context.core_package_name,
        )

        # Get collected imports for the current file.
        imports_list = current_ic.get_import_statements()
        imports_code = "\\n".join(imports_list)

        # The model_code is what the visitor returned.
        model_code = rendered_model_str

        full_code = imports_code + "\\n\\n" + model_code if imports_code else model_code

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            f.write(full_code)
        # self.writer.clear() # ModelsEmitter's self.writer is not used for individual model file body
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
