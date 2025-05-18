import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from pyopenapi_gen import IRSchema, IRSpec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.loader.schemas.extractor import extract_inline_array_items, extract_inline_enums
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

        # Add support for handling arrays properly by ensuring items schema is processed
        if schema_ir.type == "array" and schema_ir.items is not None:
            # Check if the array items schema is complex and needs its own model file
            items_schema = schema_ir.items
            if items_schema.name and items_schema.type == "object" and items_schema.properties:
                # Ensure the items schema has a proper file generated if needed
                items_module_name = NameSanitizer.sanitize_module_name(items_schema.name)
                items_file_path = models_dir / f"{items_module_name}.py"
                if not items_file_path.exists() and items_schema.name in self.parsed_schemas:
                    # Recursively generate the items schema file
                    self._generate_model_file(items_schema, models_dir)

        visitor = ModelVisitor(schemas=self.parsed_schemas)
        rendered_model_str = visitor.visit(schema_ir, self.context)

        imports_str = self.context.render_imports()
        file_content = f"{imports_str}\n\n{rendered_model_str}"

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_content, encoding="utf-8")
            return str(file_path)
        except OSError as e:
            logger.error(f"Error writing model file {file_path if 'file_path' in locals() else 'UNKNOWN_PATH'}: {e}")
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

    def emit(self, spec: IRSpec, output_root: str) -> Dict[str, List[str]]:
        """Emits all model files derived from IR schemas.

        Contracts:
            Preconditions:
                - spec is a valid IRSpec
                - output_root is a valid directory path
            Postconditions:
                - All schema models are emitted to {output_root}/models/
                - All models are properly formatted and type-annotated
                - Returns a list of file paths generated
        """
        assert isinstance(spec, IRSpec), "spec must be an IRSpec"
        assert output_root, "output_root must be a non-empty string"

        # Ensure models directory exists
        output_dir = Path(output_root.rstrip("/"))
        models_dir = output_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        # Add init files to ensure models are importable
        init_path = models_dir / "__init__.py"
        if not init_path.exists():
            init_path.write_text('"""Models generated from the OpenAPI specification."""\n')

        # Extract inline array items first, then extract enums
        schemas_with_extracted_items = extract_inline_array_items(self.parsed_schemas)
        schemas_with_extracted_enums = extract_inline_enums(schemas_with_extracted_items)

        # Write a file for each schema
        generated_files = []

        # Process schemas in dependency order to ensure imports work correctly
        all_schema_names = list(schemas_with_extracted_enums.keys())
        processed_schema_names: set[str] = set()

        # Process schemas with a simple heuristic to handle dependencies:
        # 1. First pass: Handle schemas without references to other schemas
        # 2. Second pass: Handle schemas with references to already processed schemas
        # 3. Repeat until all schemas are processed

        while processed_schema_names != set(all_schema_names):
            something_processed_this_round = False

            for schema_name in all_schema_names:
                if schema_name in processed_schema_names:
                    continue  # Already processed

                schema_ir = schemas_with_extracted_enums[schema_name]
                file_path = self._generate_model_file(schema_ir, models_dir)

                if file_path is not None:
                    generated_files.append(file_path)
                    processed_schema_names.add(schema_name)
                    something_processed_this_round = True

            # If we can't process any more schemas in this round, break to avoid infinite loop
            if not something_processed_this_round:
                # There might be circular dependencies; process remaining schemas anyway
                for schema_name in set(all_schema_names) - processed_schema_names:
                    schema_ir = schemas_with_extracted_enums[schema_name]
                    file_path = self._generate_model_file(schema_ir, models_dir)
                    if file_path is not None:
                        generated_files.append(file_path)
                    processed_schema_names.add(schema_name)
                break

        # Generate or update the __init__.py file with imports for all generated models
        init_content = self._generate_init_py_content(generated_files, models_dir)
        init_path.write_text(init_content)

        return {"models": generated_files}
