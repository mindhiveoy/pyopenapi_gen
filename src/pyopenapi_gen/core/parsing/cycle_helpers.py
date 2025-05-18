import logging
from typing import Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.utils import NameSanitizer

from .context import ParsingContext

# Define module-level logger
logger = logging.getLogger(__name__)


def _handle_cycle_detection(original_name: str, cycle_path: str, context: ParsingContext) -> IRSchema:
    """Handle case where a cycle is detected in schema references.

    Contracts:
        Pre-conditions:
            - original_name is not None (guaranteed by caller in _parse_schema for now)
            - context is a valid ParsingContext instance
        Post-conditions:
            - Returns an IRSchema instance marked as circular
            - The schema is registered in context.parsed_schemas using original_name as key
            - Both _is_circular_ref and _from_unresolved_ref flags are set
    """

    schema_ir_name_attr = NameSanitizer.sanitize_class_name(original_name)
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
            - Returns an IRSchema instance marked as circular
            - If original_name is provided, the schema is registered in context.parsed_schemas
            - Both _is_circular_ref and _from_unresolved_ref flags are set
    """
    schema_ir_name_attr = NameSanitizer.sanitize_class_name(original_name) if original_name else None

    path_prefix = schema_ir_name_attr if schema_ir_name_attr else "<anonymous_schema>"
    cycle_path_for_desc = f"{path_prefix} -> MAX_DEPTH_EXCEEDED"
    description = f"[Maximum recursion depth ({max_depth}) exceeded for '{original_name or 'anonymous'}']"
    logger.warning(description)

    if original_name is not None:
        if original_name not in context.parsed_schemas:
            schema = IRSchema(
                name=schema_ir_name_attr,
                type="object",
                description=description,
                _from_unresolved_ref=True,
                _circular_ref_path=cycle_path_for_desc,
                _is_circular_ref=True,
            )
            context.parsed_schemas[original_name] = schema
        else:
            schema = context.parsed_schemas[original_name]
            schema._is_circular_ref = True
            schema._from_unresolved_ref = True
            schema._circular_ref_path = cycle_path_for_desc
            if schema.name != schema_ir_name_attr:
                schema.name = schema_ir_name_attr
    else:
        schema = IRSchema(
            name=None,
            type="object",
            description=description,
            _from_unresolved_ref=True,
            _circular_ref_path=cycle_path_for_desc,
            _is_circular_ref=True,
        )

    context.cycle_detected = True
    return schema
