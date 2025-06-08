"""Helper functions for determining Python types and managing related imports from IRSchema."""

import logging
import os
from typing import Dict, Optional, Set

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.type_resolution.finalizer import TypeFinalizer
from pyopenapi_gen.helpers.type_resolution.resolver import SchemaTypeResolver

logger = logging.getLogger(__name__)

# Define PRIMITIVE_TYPES here since it's not available from imports
PRIMITIVE_TYPES = {"string", "integer", "number", "boolean", "null", "object", "array"}


class TypeHelper:
    """
    Provides a method to determine appropriate Python type hints for IRSchema objects
    by delegating to the SchemaTypeResolver.
    All detailed type resolution logic has been moved to the `type_resolution` sub-package.
    """

    # Cache for circular references detection
    _circular_refs_cache: Dict[str, Set[str]] = {}

    @staticmethod
    def detect_circular_references(schemas: Dict[str, IRSchema]) -> Set[str]:
        """
        Detect circular references in a set of schemas.

        Args:
            schemas: Dictionary of all schemas

        Returns:
            Set of schema names that are part of circular references
        """
        # Use a cache key based on the schema names (order doesn't matter)
        cache_key = ",".join(sorted(schemas.keys()))
        if cache_key in TypeHelper._circular_refs_cache:
            return TypeHelper._circular_refs_cache[cache_key]

        circular_refs: Set[str] = set()
        visited: Dict[str, Set[str]] = {}

        def visit(schema_name: str, path: Set[str]) -> None:
            """Visit a schema and check for circular references."""
            if schema_name in path:
                # Found a circular reference
                circular_refs.add(schema_name)
                circular_refs.update(path)
                return

            if schema_name in visited:
                # Already visited this schema
                return

            # Mark as visited with current path
            visited[schema_name] = set(path)

            # Get the schema
            schema = schemas.get(schema_name)
            if not schema:
                return

            # Check all property references
            for prop_name, prop in schema.properties.items():
                if prop.type and prop.type in schemas:
                    # This property references another schema
                    new_path = set(path)
                    new_path.add(schema_name)
                    visit(prop.type, new_path)

        # Visit each schema
        for schema_name in schemas:
            visit(schema_name, set())

        # Cache the result
        TypeHelper._circular_refs_cache[cache_key] = circular_refs
        return circular_refs

    @staticmethod
    def get_python_type_for_schema(
        schema: Optional[IRSchema],
        all_schemas: Dict[str, IRSchema],
        context: RenderContext,
        required: bool,
        resolve_alias_target: bool = False,
        render_mode: str = "field",  # Literal["field", "alias_target"]
        parent_schema_name: Optional[str] = None,
    ) -> str:
        """
        Determines the Python type string for a given IRSchema.
        First, checks for a special case where schema.type directly refers to a named schema.
        Otherwise, delegates to the SchemaTypeResolver.
        Finally, uses TypeFinalizer to apply Optionality and other final touches.

        Args:
            schema: The IRSchema instance.
            all_schemas: All known (named) IRSchema instances.
            context: The RenderContext for managing imports.
            required: If the schema represents a required field/parameter.
            resolve_alias_target: If True, forces resolution to the aliased type.
            render_mode: The mode of rendering ("field" or "alias_target").
            parent_schema_name: The name of the parent schema for debug context.

        Returns:
            A string representing the Python type for the schema.
        """

        # Special case: if schema is None, default to Any
        if schema is None:
            context.add_import("typing", "Any")
            return "Any"

        # Special case: if schema.type refers directly to a named schema in all_schemas
        if (
            schema.type
            and schema.type in all_schemas
            and schema.type != "array"  # Not an array type itself
            and schema.type not in PRIMITIVE_TYPES  # Not a primitive type string
        ):
            # Detect if this is part of a circular reference
            schema_ref_name = schema.type
            is_circular = False

            # Only check for circularity if we're in a property of a named schema
            if parent_schema_name:
                # Get all circular references
                circular_refs = TypeHelper.detect_circular_references(all_schemas)

                # Check if both parent and referenced schema are in circular refs
                if parent_schema_name in circular_refs and schema_ref_name in circular_refs:
                    # This is a circular reference!
                    is_circular = True

            # Process the reference according to whether it's circular or not
            target_ir_schema = all_schemas.get(schema.type)
            if not target_ir_schema:
                logger.error(
                    f"Schema '{schema.type}' referenced by '{parent_schema_name}' not found in all_schemas. "
                    "This should not happen."
                )
                context.add_import("typing", "Any")
                return "Any"  # Fallback, though this indicates a deeper issue

            assert (
                target_ir_schema.generation_name is not None
            ), f"Target schema '{target_ir_schema.name}' must have generation_name set."
            assert (
                target_ir_schema.final_module_stem is not None
            ), f"Target schema '{target_ir_schema.name}' must have final_module_stem set."

            class_name_to_import = target_ir_schema.generation_name
            module_name_to_import_from = target_ir_schema.final_module_stem

            # Construct model_module_path:
            base_model_path_part = f"models.{module_name_to_import_from}"
            model_module_path = base_model_path_part

            if context.package_root_for_generated_code and context.overall_project_root:
                current_gen_pkg_name_from_proj_root = os.path.basename(
                    os.path.normpath(context.package_root_for_generated_code)
                )
                if current_gen_pkg_name_from_proj_root and current_gen_pkg_name_from_proj_root != ".":
                    model_module_path = f"{current_gen_pkg_name_from_proj_root}.{base_model_path_part}"

            elif context.package_root_for_generated_code:  # Only pkg_root is set
                current_gen_pkg_name_from_basename = os.path.basename(
                    os.path.normpath(context.package_root_for_generated_code)
                )
                if current_gen_pkg_name_from_basename and current_gen_pkg_name_from_basename != ".":
                    model_module_path = f"{current_gen_pkg_name_from_basename}.{base_model_path_part}"

            # Check if the target module is the current module being generated
            current_module_dot_path = context.get_current_module_dot_path()
            is_self_import = current_module_dot_path == model_module_path

            # Enhanced self-import detection: check if we're importing the same class from the same module
            is_same_class_self_import = False
            if context.current_file:
                current_file_name = context.current_file
                current_module_name = os.path.splitext(os.path.basename(current_file_name))[0]
                target_module_name = module_name_to_import_from

                # If we're in message.py trying to import Message from message module, skip it
                if (
                    current_module_name == target_module_name
                    and class_name_to_import == target_ir_schema.generation_name
                ):
                    is_same_class_self_import = True

            if is_self_import or is_same_class_self_import:
                pass  # Explicitly do nothing, was a log statement
            else:  # Not a self-import
                if is_circular:
                    context.add_import("typing", "TYPE_CHECKING")  # Ensure TYPE_CHECKING is imported
                    # Use add_conditional_import which applies the same unified import path logic
                    context.add_conditional_import("TYPE_CHECKING", model_module_path, class_name_to_import)
                else:
                    # Add a normal import if it's not circular and not a self-import
                    context.add_import(model_module_path, class_name_to_import)

            resolved_type_str = class_name_to_import
            final_type = TypeFinalizer(context, all_schemas).finalize(resolved_type_str, schema, required)

            # For self-references within the same class, quote the entire final type expression
            if is_same_class_self_import:
                final_type = f'"{final_type}"'

            return final_type

        resolver = SchemaTypeResolver(context=context, all_schemas=all_schemas)

        # The 'required' status is primarily for TypeFinalizer, but resolver might use it too.
        # current_schema_context_name is for promotion logic within ObjectTypeResolver.
        resolved_type_from_resolver = resolver.resolve(
            schema=schema,
            required=required,
            resolve_alias_target=resolve_alias_target,
            current_schema_context_name=parent_schema_name,
        )

        # TypeFinalizer handles Optionality, cleaning, etc. based on the resolved type and original schema.
        # It also provides a fallback to 'Any' if resolver returns None.
        return TypeFinalizer(context, all_schemas).finalize(resolved_type_from_resolver, schema, required)
