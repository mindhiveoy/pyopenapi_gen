import logging
from typing import Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.utils import NameSanitizer

from .context import ParsingContext

# Define module-level logger
logger = logging.getLogger(__name__)


def _handle_cycle_detection(
    original_name: str, cycle_path: str, context: ParsingContext, allow_self_reference: bool
) -> IRSchema:
    """Handle case where a cycle is detected in schema references.

    Contracts:
        Pre-conditions:
            - original_name is not None
            - context is a valid ParsingContext instance
            - allow_self_reference indicates if direct self-references are permitted without being treated as errors.
        Post-conditions:
            - Returns an IRSchema instance.
            - If not a permitted self-reference, it's marked as circular and registered.
            - If a permitted self-reference, a placeholder is returned and not marked as an error cycle.
    """
    schema_ir_name_attr = NameSanitizer.sanitize_class_name(original_name)

    # Check for direct self-reference when allowed
    path_parts = cycle_path.split(" -> ")
    is_direct_self_ref = len(path_parts) == 2 and path_parts[0] == original_name and path_parts[1] == original_name

    if allow_self_reference and is_direct_self_ref:
        # Permitted direct self-reference, creating placeholder without marking as error cycle
        if original_name not in context.parsed_schemas:
            # Create a basic placeholder. It will be fully populated when its real definition is parsed.
            # Key is NOT to mark _is_circular_ref = True here.
            schema = IRSchema(
                name=schema_ir_name_attr,
                type="object",  # Default type, might be refined if we parse its own definition later
                description=f"[Self-referential placeholder for {original_name}]",
                _from_unresolved_ref=False,  # Not unresolved in the error sense
                _is_self_referential_stub=True,  # New flag to indicate this state
            )
            context.parsed_schemas[original_name] = schema
            return schema
        else:
            # If it's already in parsed_schemas, it means we're re-entering it.
            # This could happen if it was created as a placeholder by another ref first.
            # Ensure it's marked as a self-referential stub if not already.
            existing_schema = context.parsed_schemas[original_name]
            if not getattr(existing_schema, "_is_self_referential_stub", False):
                existing_schema._is_self_referential_stub = True  # Mark it
            return existing_schema

    # If not a permitted direct self-reference, or if self-references are not allowed, proceed with error cycle handling
    if original_name not in context.parsed_schemas:
        schema = IRSchema(
            name=schema_ir_name_attr,
            type="object",
            description=f"[Circular reference detected: {cycle_path}]",
            _from_unresolved_ref=True,
            _circular_ref_path=cycle_path,
            _is_circular_ref=True,
        )
        context.parsed_schemas[original_name] = schema
    else:
        schema = context.parsed_schemas[original_name]
        schema._is_circular_ref = True
        schema._from_unresolved_ref = True
        schema._circular_ref_path = cycle_path
        if schema.name != schema_ir_name_attr:
            schema.name = schema_ir_name_attr

    context.cycle_detected = True
    return schema


def _handle_max_depth_exceeded(original_name: Optional[str], context: ParsingContext, max_depth: int) -> IRSchema:
    """Handle case where maximum recursion depth is exceeded.

    Contracts:
        Pre-conditions:
            - context is a valid ParsingContext instance
            - max_depth >= 0
        Post-conditions:
            - Returns an IRSchema instance marked with _max_depth_exceeded_marker=True
            - If original_name is provided, the schema is registered in context.parsed_schemas
    """
    schema_ir_name_attr = NameSanitizer.sanitize_class_name(original_name) if original_name else None

    # path_prefix = schema_ir_name_attr if schema_ir_name_attr else "<anonymous_schema>"
    # cycle_path_for_desc = f"{path_prefix} -> MAX_DEPTH_EXCEEDED"
    description = f"[Maximum recursion depth ({max_depth}) exceeded for '{original_name or "anonymous"}']"
    logger.warning(description)

    placeholder_schema = IRSchema(
        name=schema_ir_name_attr,
        type="object",  # Default type for a placeholder created due to depth
        description=description,
        _max_depth_exceeded_marker=True,
        # Do NOT set _is_circular_ref or _from_unresolved_ref here just for depth limit
    )

    if original_name is not None:
        if original_name not in context.parsed_schemas:
            context.parsed_schemas[original_name] = placeholder_schema
        else:
            # If a schema with this name already exists (e.g. a forward ref stub),
            # update it to mark that max depth was hit during its resolution attempt.
            # This is tricky because we don't want to overwrite a fully parsed schema.
            # For now, let's assume if we are here, the existing one is also some form of placeholder
            # or its parsing was interrupted to get here.
            existing_schema = context.parsed_schemas[original_name]
            existing_schema.description = description  # Update description
            existing_schema._max_depth_exceeded_marker = True
            # Avoid re-assigning to placeholder_schema directly to keep existing IR object if it was complex
            # and just needs this flag + description update.
            return existing_schema  # Return the (now updated) existing schema

    # context.cycle_detected = True # Max depth is not strictly a cycle in the schema definition itself
    return placeholder_schema
