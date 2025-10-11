"""
Finalization an IRSchema object during OpenAPI parsing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List, Mapping, Set, Union

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.utils import NameSanitizer

from .context import ParsingContext

# Specific helpers needed
from .transformers.inline_enum_extractor import _process_standalone_inline_enum

# Note: _parse_schema will be passed as parse_fn, not imported directly

if TYPE_CHECKING:
    pass


def _finalize_schema_object(
    name: str | None,
    node: Mapping[str, Any],
    context: ParsingContext,
    schema_type: str | None,
    is_nullable: bool,
    any_of_schemas: List[IRSchema] | None,
    one_of_schemas: List[IRSchema] | None,
    parsed_all_of_components: List[IRSchema] | None,
    final_properties_map: dict[str, IRSchema],
    merged_required_set: Set[str],
    final_items_schema: IRSchema | None,
    additional_properties_node: Union[bool, Mapping[str, Any]] | None,
    enum_node: List[Any] | None,
    format_node: str | None,
    description_node: str | None,
    from_unresolved_ref_node: bool,
    max_depth: int,
    parse_fn: Callable[[str | None, Mapping[str, Any] | None, ParsingContext, int], IRSchema],
    logger: Any,  # Changed to Any to support both real and mock loggers
) -> IRSchema:
    """Constructs the IRSchema object, performs final adjustments, and updates context.

    Contracts:
        Pre-conditions:
            - All input arguments are appropriately populated.
            - context is valid.
            - parse_fn is a callable for parsing (e.g. additionalProperties).
            - logger is a logging.Logger instance or a mock logger for testing.
        Post-conditions:
            - Returns a finalized IRSchema instance.
            - If schema has a name and isn't a placeholder, it's in context.parsed_schemas.
    """
    if not isinstance(node, Mapping):
        raise TypeError("node must be a Mapping")
    if not isinstance(context, ParsingContext):
        raise TypeError("context must be a ParsingContext instance")
    if not callable(parse_fn):
        raise TypeError("parse_fn must be callable")
    # Remove logger type check to support mock loggers in tests

    # If a placeholder for this schema name already exists due to a cycle detected deeper,
    # return that placeholder immediately to preserve the cycle information.
    if name and name in context.parsed_schemas:
        existing_schema = context.parsed_schemas[name]
        if getattr(existing_schema, "_is_circular_ref", False) or getattr(
            existing_schema, "_from_unresolved_ref", False
        ):
            # Early return of cycle placeholder
            return existing_schema

    final_enum_values: List[Any] | None = enum_node if isinstance(enum_node, list) else None
    final_required_fields_list: List[str] = sorted(list(merged_required_set))

    final_additional_properties: Union[bool, IRSchema] | None = None
    if isinstance(additional_properties_node, bool):
        final_additional_properties = additional_properties_node
    elif isinstance(additional_properties_node, dict):
        final_additional_properties = parse_fn(None, additional_properties_node, context, max_depth)

    final_schema_name_for_obj = NameSanitizer.sanitize_class_name(name) if name else None
    current_schema_type = schema_type
    if current_schema_type is None and final_properties_map:
        current_schema_type = "object"

    is_data_wrapper_flag = (
        current_schema_type == "object"
        and "data" in final_properties_map
        and "data" in final_required_fields_list
        and len(final_properties_map) == 1
    )

    schema_obj = IRSchema(
        name=final_schema_name_for_obj,
        type=current_schema_type,
        format=format_node,
        description=description_node,
        required=final_required_fields_list,
        properties=final_properties_map,
        items=final_items_schema,
        enum=final_enum_values,
        additional_properties=final_additional_properties,
        is_nullable=is_nullable,
        any_of=any_of_schemas,
        one_of=one_of_schemas,
        all_of=parsed_all_of_components,
        is_data_wrapper=is_data_wrapper_flag,
        _from_unresolved_ref=from_unresolved_ref_node,
    )

    if (
        schema_obj.name
        and schema_obj.name in context.parsed_schemas
        and context.parsed_schemas[schema_obj.name].type is None
        and schema_obj.type is not None
    ):
        # Named schema in context has no type, adopting type
        # schema_obj will be placed in context later, overwriting if necessary.
        pass

    if schema_obj.type is None and (
        schema_obj.properties
        or (
            isinstance(node.get("_def"), dict)
            and node["_def"].get("typeName") == "ZodObject"
            and node["_def"].get("shape")
        )
    ):
        # Schema has properties but no type; setting to 'object'
        schema_obj.type = "object"

    if name and "." in name:
        is_explicitly_simple = node.get("type") in ["string", "integer", "number", "boolean", "array"]
        is_explicitly_enum = "enum" in node
        if schema_obj.type is None and not is_explicitly_simple and not is_explicitly_enum:
            # Inline property lacks complex type, defaulting to 'object'
            schema_obj.type = "object"

    # Update the context with the finalized schema object
    # This should only happen if we didn't return an existing placeholder above.
    if name:
        # Never overwrite a cycle placeholder!
        if name in context.parsed_schemas and (
            getattr(context.parsed_schemas[name], "_is_circular_ref", False)
            or getattr(context.parsed_schemas[name], "_from_unresolved_ref", False)
        ):
            # Not overwriting cycle placeholder
            pass  # Do not overwrite
        elif name not in context.parsed_schemas:
            context.parsed_schemas[name] = schema_obj
        # If name is in context and is already a full schema, and schema_obj is also full,
        # current one is considered fresher.
        elif not (
            getattr(context.parsed_schemas[name], "_is_circular_ref", False)
            or getattr(context.parsed_schemas[name], "_from_unresolved_ref", False)
        ):
            context.parsed_schemas[name] = schema_obj  # Overwrite existing full with new full

    if schema_obj:
        schema_obj = _process_standalone_inline_enum(name, node, schema_obj, context, logger)

    if schema_obj and schema_obj.name and context.parsed_schemas.get(schema_obj.name) is not schema_obj:
        context.parsed_schemas[schema_obj.name] = schema_obj
        # Ensured schema is in context post-standalone-enum processing

    # Returning finalized schema object
    return schema_obj
