import logging
from pathlib import Path
from typing import List, Set

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

    def __init__(
        self,
        context: RenderContext,
        parsed_schemas: dict[str, IRSchema],
        discriminator_skip_list: set[str] | None = None,
    ):
        self.context: RenderContext = context
        # Store a reference to the schemas that were passed in.
        # These schemas will have their .generation_name and .final_module_stem updated.
        self.parsed_schemas: dict[str, IRSchema] = parsed_schemas
        self.discriminator_skip_list: set[str] = discriminator_skip_list or set()
        self.import_collector = self.context.import_collector
        self.writer = CodeWriter()

    def _generate_model_file(self, schema_ir: IRSchema, models_dir: Path) -> str | None:
        """Generates a single Python file for a given IRSchema."""
        if not schema_ir.name:  # Original name, used for logging/initial identification
            logger.warning(f"Skipping model generation for schema without an original name: {schema_ir}")
            return None

        # logger.debug(
        #     f"_generate_model_file processing schema: original_name='{schema_ir.name}', "
        #     f"generation_name='{schema_ir.generation_name}', final_module_stem='{schema_ir.final_module_stem}'"
        # )

        # Assert that de-collided names have been set by the emit() method's preprocessing.
        if schema_ir.generation_name is None:
            raise RuntimeError(f"Schema '{schema_ir.name}' must have generation_name set before file generation.")
        if schema_ir.final_module_stem is None:
            raise RuntimeError(f"Schema '{schema_ir.name}' must have final_module_stem set before file generation.")

        file_path = models_dir / f"{schema_ir.final_module_stem}.py"

        self.context.set_current_file(str(file_path))

        # Add support for handling arrays properly by ensuring items schema is processed
        # This part might need to ensure that items_schema also has its generation_name/final_module_stem set
        # if it's being recursively generated here. The main emit loop should handle all schemas.
        if schema_ir.type == "array" and schema_ir.items is not None:
            items_schema = schema_ir.items
            if items_schema.name and items_schema.type == "object" and items_schema.properties:
                if (
                    items_schema.name in self.parsed_schemas and items_schema.final_module_stem
                ):  # Check if it's a managed schema
                    items_file_path = models_dir / f"{items_schema.final_module_stem}.py"
                    if not items_file_path.exists():
                        # This recursive call might be problematic if items_schema wasn't fully preprocessed.
                        # The main emit loop is preferred for driving generation.
                        # For now, assuming items_schema has its names set if it's a distinct schema.
                        # logger.debug(f"Potentially generating item schema {items_schema.name} recursively.")
                        # self._generate_model_file(items_schema, models_dir) # Re-evaluating recursive call here.
                        # Better to rely on main loop processing all schemas.
                        pass

        # ModelVisitor should use schema_ir.generation_name for the class name.
        # We'll need to verify ModelVisitor's behavior.
        # For now, ModelVisitor.visit uses schema.name as base_name_for_construct if not schema.generation_name.
        # If schema.generation_name is set, it should be preferred. Let's assume ModelVisitor handles this,
        # or we ensure schema.name is updated to schema.generation_name before visitor.
        # The IRSchema.__post_init__ already sanitizes schema.name.
        # The ModelVisitor's `visit_IRSchema` uses schema.name for `base_name_for_construct`.
        # So, `schema.generation_name` should be used by the visitor.
        # For now, the visitor logic uses schema.name. We must ensure that the `generation_name` (decollided)
        # is what the visitor uses for the class definition.
        # A temporary workaround could be:
        # original_ir_name = schema_ir.name
        # schema_ir.name = schema_ir.generation_name # Temporarily set for visitor
        visitor = ModelVisitor(
            schemas=self.parsed_schemas, discriminator_skip_list=self.discriminator_skip_list
        )  # Pass all schemas for reference

        rendered_model_str = visitor.visit(schema_ir, self.context)
        imports_str = self.context.render_imports()

        # Guard: if rendered content is empty, generate a str TypeAlias fallback
        # so consuming modules that import from this file don't get ImportError.
        if not rendered_model_str.strip():
            class_name = schema_ir.generation_name or schema_ir.name or "Unknown"
            logger.warning(
                f"Empty model content for schema '{schema_ir.name}' "
                f"(generation_name='{class_name}'). "
                f"Generating str TypeAlias to prevent broken imports."
            )
            file_content = (
                f"from typing import TypeAlias\n\n" f'__all__ = ["{class_name}"]\n\n' f"{class_name}: TypeAlias = str\n"
            )
        else:
            file_content = f"{imports_str}\n\n{rendered_model_str}"

        try:
            # Ensure parent directory exists with more defensive handling
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Verify the directory was actually created before writing
            if not file_path.parent.exists():
                logger.error(f"Failed to create directory {file_path.parent}")
                return None

            # Write with atomic operation to prevent partial writes
            temp_file = file_path.with_suffix(".tmp")
            temp_file.write_text(file_content, encoding="utf-8")
            temp_file.rename(file_path)

            # Verify the file was actually written
            if not file_path.exists():
                logger.error(f"File {file_path} was not created successfully")
                return None

            logger.debug(f"Successfully created model file: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error writing model file {file_path}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _generate_init_py_content(self) -> str:  # Removed generated_files_paths, models_dir args
        """Generates the content for models/__init__.py."""
        init_writer = CodeWriter()
        init_writer.write_line("from typing import List")
        init_writer.write_line("")

        all_class_names_to_export: Set[str] = set()

        # Iterate over the schemas that were processed for name generation
        # to ensure we use the final, de-collided names.
        # Sort by original schema name for deterministic __init__.py content.
        sorted_schemas_for_init = sorted(
            [s for s in self.parsed_schemas.values() if s.name and s.generation_name and s.final_module_stem],
            key=lambda s: s.name,  # type: ignore
        )

        for s_schema in sorted_schemas_for_init:
            # These should have been set in the emit() preprocessing step.
            if s_schema.generation_name is None:
                raise RuntimeError(f"Schema '{s_schema.name}' missing generation_name in __init__ generation.")
            if s_schema.final_module_stem is None:
                raise RuntimeError(f"Schema '{s_schema.name}' missing final_module_stem in __init__ generation.")

            if s_schema._from_unresolved_ref:  # Check this flag if it's relevant
                # logger.debug(
                #     f"Skipping schema '{s_schema.generation_name}' in __init__ as it's an unresolved reference."
                # )
                continue

            class_name_to_import = s_schema.generation_name
            module_name_to_import_from = s_schema.final_module_stem

            if module_name_to_import_from == "__init__":
                logger.warning(
                    f"Skipping import for schema class '{class_name_to_import}' as its module name became __init__."
                )
                continue

            init_writer.write_line(f"from .{module_name_to_import_from} import {class_name_to_import}")
            all_class_names_to_export.add(class_name_to_import)

        init_writer.write_line("")
        init_writer.write_line("__all__: List[str] = [")
        for name_to_export in sorted(list(all_class_names_to_export)):
            init_writer.write_line(f"    '{name_to_export}',")
        init_writer.write_line("]")

        generated_content = init_writer.get_code()
        return generated_content

    def emit(self, spec: IRSpec, output_root: str) -> dict[str, List[str]]:
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
        if not isinstance(spec, IRSpec):
            raise TypeError("spec must be an IRSpec")
        if not output_root:
            raise ValueError("output_root must be a non-empty string")

        output_dir = Path(output_root.rstrip("/"))
        models_dir = output_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        init_path = models_dir / "__init__.py"
        # Initial __init__.py content, will be overwritten later with actual imports.
        if not init_path.exists():
            init_path.write_text('"""Models generated from the OpenAPI specification."""\n')

        # 1. Extract all inline schemas first.
        # self.parsed_schemas initially comes from the spec.
        # extract_inline_array_items might add new named schemas to the collection it returns.
        # These new schemas are instances created by promoting anonymous ones.
        # It's important that these extractors operate on and return a comprehensive
        # dictionary of *all* schemas that should potentially be generated.
        # The `self.parsed_schemas` (which is `spec.schemas` passed in constructor)
        # should be updated or replaced by the result of these extractions if they modify
        # or add to the set of schemas to be processed.

        # Let's assume extractors return a new dict containing original and newly promoted schemas.
        # The `parsed_schemas` in `RenderContext` also needs to be aware of all schemas for type resolution.
        # The ModelsEmitter was initialized with `parsed_schemas=ir.schemas`.
        # If extractors modify these in place (e.g., add new IRSchema to ir.schemas), then all good.
        # If they return a *new* dict, then self.parsed_schemas needs to be updated.
        # Current `extract_inline_array_items` and `extract_inline_enums` take `parsed_schemas` (a Dict)
        # and return a new Dict.

        # So, the source of truth for schemas to generate becomes the result of these extractions.
        schemas_after_item_extraction = extract_inline_array_items(self.parsed_schemas)
        all_schemas_for_generation = extract_inline_enums(schemas_after_item_extraction)

        # Update self.parsed_schemas to this complete list, as this is what subsequent
        # operations (like _generate_init_py_content) will iterate over.
        # Also, RenderContext needs the most up-to-date list of all schemas.
        self.parsed_schemas = all_schemas_for_generation
        self.context.parsed_schemas = all_schemas_for_generation  # Correctly update the attribute

        # --- Name de-collision pre-processing ---
        # This step ensures each schema that will generate a file
        # has a unique class name (generation_name) and a unique module stem (final_module_stem).
        # This should run on ALL schemas that are candidates for file generation.

        assigned_class_names: Set[str] = set()
        assigned_module_stems: Set[str] = set()

        # Iterate over the values of all_schemas_for_generation
        # Sort by original name for deterministic suffixing if collisions occur.
        # Filter for schemas that actually have a name, as unnamed schemas don't get their own files.
        # A schema created by extraction (e.g. PetListItemsItem) will have a .name.

        # logger.debug(
        #     f"ModelsEmitter: Schemas considered for naming/de-collision (pre-filter): "
        #     f"{ {k: v.name for k, v in all_schemas_for_generation.items()} }"
        # )

        # Filter out only the most basic primitive schemas to reduce clutter
        # Be conservative to avoid breaking existing functionality
        def should_generate_file(schema: IRSchema) -> bool:
            """Determine if a schema should get its own generated file."""
            if not schema.name or not schema.name.strip():
                return False

            # Only filter out the most basic primitive type aliases with very common names
            # that are clearly just artifacts of the parsing process
            is_basic_primitive_artifact = (
                schema.type in ["string", "integer", "number", "boolean"]
                and not schema.enum
                and not schema.properties
                and not schema.any_of
                and not schema.one_of
                and not schema.all_of
                and not schema.description
                and
                # Only filter very common property names that are likely artifacts
                schema.name.lower() in ["id", "name", "text", "content", "value", "type", "status"]
                and
                # And only if the schema name ends with underscore (indicating sanitization)
                schema.name.endswith("_")
            )

            if is_basic_primitive_artifact:
                return False

            return True

        # Filter the main schemas dict to only include schemas that should generate files
        filtered_schemas_for_generation = {
            k: v for k, v in all_schemas_for_generation.items() if should_generate_file(v)
        }

        # Update the main reference to use filtered schemas
        all_schemas_for_generation = filtered_schemas_for_generation

        # Collect all nested schemas from oneOf/anyOf/allOf that need naming
        def collect_nested_schemas(schema: IRSchema, collected: dict[int, IRSchema], visited_ids: Set[int]) -> None:
            """Recursively collect all nested schemas that need generation_name."""
            schema_id = id(schema)
            if schema_id in visited_ids:
                return  # Avoid infinite loops

            visited_ids.add(schema_id)
            if schema.name:  # Only collect schemas with names
                collected[schema_id] = schema

            # Process oneOf variants
            if schema.one_of:
                for variant in schema.one_of:
                    if variant.name and id(variant) not in visited_ids:
                        collect_nested_schemas(variant, collected, visited_ids)

            # Process anyOf variants
            if schema.any_of:
                for variant in schema.any_of:
                    if variant.name and id(variant) not in visited_ids:
                        collect_nested_schemas(variant, collected, visited_ids)

            # Process allOf components (though they typically merge, not union)
            if schema.all_of:
                for component in schema.all_of:
                    if component.name and id(component) not in visited_ids:
                        collect_nested_schemas(component, collected, visited_ids)

        # Collect all schemas including nested ones
        # Deduplicate schemas by ID first - same schema object may appear under multiple keys
        unique_schemas_by_id = {id(s): s for s in all_schemas_for_generation.values()}
        all_schemas_including_nested: dict[int, IRSchema] = {}
        visited_schema_ids: Set[int] = set()
        for schema in unique_schemas_by_id.values():
            collect_nested_schemas(schema, all_schemas_including_nested, visited_schema_ids)

        schemas_to_name_decollision = sorted(
            list(all_schemas_including_nested.values()),
            key=lambda s: s.name if s.name else "",
        )

        logger.debug(
            f"ModelsEmitter: Schemas to actually de-collide (post-filter by s.name): "
            f"{[(s.name, id(s)) for s in schemas_to_name_decollision]}"
        )

        for schema_for_naming in schemas_to_name_decollision:  # Use the comprehensive list
            original_schema_name = schema_for_naming.name
            if not original_schema_name:
                continue  # Should be filtered

            # 1. Determine unique class name (schema_for_naming.generation_name)
            base_class_name = NameSanitizer.sanitize_class_name(original_schema_name)
            final_class_name = base_class_name
            class_suffix = 1
            while final_class_name in assigned_class_names:
                class_suffix += 1
                # Handle reserved names that already have trailing underscores
                # Instead of "Email_2", we want "Email2"
                if base_class_name.endswith("_"):
                    # Remove trailing underscore and append number
                    final_class_name = f"{base_class_name[:-1]}{class_suffix}"
                else:
                    final_class_name = f"{base_class_name}{class_suffix}"
            assigned_class_names.add(final_class_name)
            schema_for_naming.generation_name = final_class_name
            # logger.debug(f"Resolved class name for original '{original_schema_name}': '{final_class_name}'")

            # 2. Determine unique module stem (schema_for_naming.final_module_stem)
            base_module_stem = NameSanitizer.sanitize_module_name(original_schema_name)
            final_module_stem = base_module_stem
            module_suffix = 1

            if final_module_stem in assigned_module_stems:
                module_suffix = 2
                final_module_stem = f"{base_module_stem}_{module_suffix}"
                while final_module_stem in assigned_module_stems:
                    module_suffix += 1
                    final_module_stem = f"{base_module_stem}_{module_suffix}"

            assigned_module_stems.add(final_module_stem)
            schema_for_naming.final_module_stem = final_module_stem
            # logger.debug(
            #     f"Resolved module stem for original '{original_schema_name}' "
            #     f"(class '{final_class_name}'): '{final_module_stem}'"
            # )
        # --- End of Name de-collision ---

        generated_files = []
        # Iterate using the keys from `all_schemas_for_generation` as it's the definitive list.
        all_schema_keys_to_emit = list(all_schemas_for_generation.keys())
        processed_schema_original_keys: set[str] = set()

        max_processing_rounds = len(all_schema_keys_to_emit) + 5
        rounds = 0

        while len(processed_schema_original_keys) < len(all_schema_keys_to_emit) and rounds < max_processing_rounds:
            rounds += 1
            something_processed_this_round = False
            # logger.debug(
            #     f"ModelsEmitter: Starting processing round {rounds}. "
            #     f"Processed: {len(processed_schema_original_keys)}/{len(all_schema_keys_to_emit)}"
            # )

            for schema_key in all_schema_keys_to_emit:
                if schema_key in processed_schema_original_keys:
                    continue

                # Fetch the schema_ir object using the key from all_schemas_for_generation
                # This ensures we are working with the potentially newly created & named schemas.
                current_schema_ir_obj: IRSchema | None = all_schemas_for_generation.get(schema_key)

                if not current_schema_ir_obj:
                    logger.warning(f"Schema key '{schema_key}' from all_schemas_for_generation not found. Skipping.")
                    processed_schema_original_keys.add(schema_key)
                    something_processed_this_round = True
                    continue

                schema_ir: IRSchema = current_schema_ir_obj

                if not schema_ir.name:
                    # logger.debug(
                    #     f"Skipping file generation for unnamed schema (original key '{schema_key}'). IR: {schema_ir}"
                    # )
                    processed_schema_original_keys.add(schema_key)
                    something_processed_this_round = True
                    continue

                if not schema_ir.generation_name or not schema_ir.final_module_stem:
                    logger.error(
                        f"Schema '{schema_ir.name}' (original key '{schema_key}') is missing de-collided names. "
                        f"GenName: {schema_ir.generation_name}, "
                        f"ModStem: {schema_ir.final_module_stem}. Skipping file gen. IR: {schema_ir}"
                    )
                    processed_schema_original_keys.add(schema_key)
                    something_processed_this_round = True
                    continue

                file_path_str = self._generate_model_file(schema_ir, models_dir)

                if file_path_str is not None:
                    generated_files.append(file_path_str)
                    processed_schema_original_keys.add(schema_key)
                    something_processed_this_round = True
                # If file_path_str is None, it means an error occurred,
                # but we still mark as processed to avoid infinite loop.
                elif schema_ir.name:  # Only mark as processed if it was a schema we attempted to generate
                    processed_schema_original_keys.add(schema_key)
                    something_processed_this_round = True  # Also count this as processed for loop termination

            if not something_processed_this_round and len(processed_schema_original_keys) < len(
                all_schema_keys_to_emit
            ):
                logger.warning(
                    f"ModelsEmitter: No schemas processed in round {rounds}, but not all schemas are done. "
                    f"Processed: {len(processed_schema_original_keys)}/{len(all_schema_keys_to_emit)}. "
                    f"Remaining: {set(all_schema_keys_to_emit) - processed_schema_original_keys}. "
                    f"Breaking to avoid infinite loop."
                )
                # Process any remaining ones that were not touched, to ensure they are marked as "processed"
                for schema_key_rem in set(all_schema_keys_to_emit) - processed_schema_original_keys:
                    s_rem = all_schemas_for_generation.get(schema_key_rem)
                    logger.error(
                        f"Force marking remaining schema "
                        f"'{s_rem.name if s_rem else schema_key_rem}' as processed due to loop break."
                    )
                    processed_schema_original_keys.add(schema_key_rem)
                break

        if rounds >= max_processing_rounds:
            logger.error(
                f"ModelsEmitter: Exceeded max processing rounds ({max_processing_rounds}). "
                f"Processed: {len(processed_schema_original_keys)}/{len(all_schema_keys_to_emit)}. "
                f"Remaining: {set(all_schema_keys_to_emit) - processed_schema_original_keys}."
            )

        init_content = self._generate_init_py_content()
        init_path.write_text(init_content, encoding="utf-8")
        # py.typed file to indicate type information is available
        (models_dir / "py.typed").write_text("")  # Ensure empty content, encoding defaults to utf-8

        return {"models": generated_files}
