"""Schema type resolver implementation."""

import logging

from pyopenapi_gen import IRSchema

from ..contracts.protocols import ReferenceResolver, SchemaTypeResolver, TypeContext
from ..contracts.types import ResolvedType, TypeResolutionError

logger = logging.getLogger(__name__)


class OpenAPISchemaResolver(SchemaTypeResolver):
    """Resolves IRSchema objects to Python types."""

    def __init__(self, ref_resolver: ReferenceResolver):
        """
        Initialize schema resolver.

        Args:
            ref_resolver: Reference resolver for handling $ref
        """
        self.ref_resolver = ref_resolver

    def resolve_schema(
        self, schema: IRSchema, context: TypeContext, required: bool = True, resolve_underlying: bool = False
    ) -> ResolvedType:
        """
        Resolve a schema to a Python type.

        Args:
            schema: The schema to resolve
            context: Type resolution context
            required: Whether the field is required
            resolve_underlying: If True, resolve underlying type for aliases instead of schema name

        Returns:
            Resolved Python type information
        """
        if not schema:
            return self._resolve_any(context)

        # Handle references
        if hasattr(schema, "ref") and schema.ref:
            return self._resolve_reference(schema.ref, context, required, resolve_underlying)

        # Handle null schemas (schemas with no type and no generation_name) - resolve to Any inline
        # These are schemas from null schema nodes in the OpenAPI spec
        schema_type = getattr(schema, "type", None)
        if (
            schema_type is None
            and not (hasattr(schema, "generation_name") and schema.generation_name)
            and not (hasattr(schema, "any_of") and schema.any_of)
            and not (hasattr(schema, "one_of") and schema.one_of)
            and not (hasattr(schema, "all_of") and schema.all_of)
        ):
            # This is a null schema - resolve to Any directly
            return self._resolve_any(context)

        # Handle named schemas with generation_name (fully processed schemas)
        if schema.name and hasattr(schema, "generation_name") and schema.generation_name:
            # If resolve_underlying is True, skip named schema resolution for type aliases
            # and resolve the underlying primitive type instead
            if not resolve_underlying:
                return self._resolve_named_schema(schema, context, required)

        # Handle composition types (any_of, all_of, one_of)
        # These are processed for inline compositions or when generating the alias for a named composition
        # Check for the attribute existence, not just truthiness, to handle empty lists
        if hasattr(schema, "any_of") and schema.any_of is not None:
            return self._resolve_any_of(schema, context, required, resolve_underlying)
        elif hasattr(schema, "all_of") and schema.all_of is not None:
            return self._resolve_all_of(schema, context, required, resolve_underlying)
        elif hasattr(schema, "one_of") and schema.one_of is not None:
            return self._resolve_one_of(schema, context, required, resolve_underlying)

        # Handle named schemas without generation_name (fallback for references)
        if schema.name and schema.name in self.ref_resolver.schemas:
            target_schema = self.ref_resolver.schemas[schema.name]
            # Avoid infinite recursion if it's the same object
            if target_schema is not schema:
                return self.resolve_schema(target_schema, context, required, resolve_underlying)

        # Handle by type
        schema_type = getattr(schema, "type", None)

        # Check if schema.type refers to a named schema (backward compatibility)
        if (
            schema_type
            and hasattr(self.ref_resolver, "schemas")
            and hasattr(self.ref_resolver.schemas, "__contains__")
            and schema_type in self.ref_resolver.schemas
        ):
            target_schema = self.ref_resolver.schemas[schema_type]
            if target_schema and hasattr(target_schema, "name") and target_schema.name:  # It's a named schema reference
                return self.resolve_schema(target_schema, context, required, resolve_underlying)

        if schema_type == "string":
            return self._resolve_string(schema, context, required)
        elif schema_type == "integer":
            return self._resolve_integer(context, required)
        elif schema_type == "number":
            return self._resolve_number(context, required)
        elif schema_type == "boolean":
            return self._resolve_boolean(context, required)
        elif schema_type == "array":
            return self._resolve_array(schema, context, required, resolve_underlying)
        elif schema_type == "object":
            return self._resolve_object(schema, context, required)
        elif schema_type == "null":
            return self._resolve_null(context, required)
        else:
            # Gather detailed information about the problematic schema
            schema_details = {
                "type": schema_type,
                "name": getattr(schema, "name", None),
                "ref": getattr(schema, "ref", None),
                "properties": list(getattr(schema, "properties", {}).keys()) if hasattr(schema, "properties") else None,
                "enum": getattr(schema, "enum", None),
                "description": getattr(schema, "description", None),
                "generation_name": getattr(schema, "generation_name", None),
                "is_nullable": getattr(schema, "is_nullable", None),
                "any_of": len(getattr(schema, "any_of", []) or []) if hasattr(schema, "any_of") else 0,
                "all_of": len(getattr(schema, "all_of", []) or []) if hasattr(schema, "all_of") else 0,
                "one_of": len(getattr(schema, "one_of", []) or []) if hasattr(schema, "one_of") else 0,
            }

            # Remove None values for cleaner output
            schema_details = {k: v for k, v in schema_details.items() if v is not None}

            # Create detailed error message
            error_msg = f"Unknown schema type '{schema_type}' encountered."
            if schema_details.get("name"):
                error_msg += f" Schema name: '{schema_details['name']}'."
            if schema_details.get("ref"):
                error_msg += f" Reference: '{schema_details['ref']}'."

            # Log full details with actionable advice
            logger.warning(f"{error_msg} Full details: {schema_details}")

            # Provide specific guidance based on the unknown type
            if schema_type == "Any":
                logger.info(
                    "Schema type 'Any' will be mapped to typing.Any. Consider using a more specific type in your OpenAPI spec."
                )
            elif schema_type == "None" or schema_type is None:
                logger.info(
                    "Schema type 'None' detected - likely an optional field or null type. This will be mapped to Any | None."
                )
                return self._resolve_null(context, required)
            elif schema_type and isinstance(schema_type, str):
                # Unknown string type - provide helpful suggestions
                logger.info(f"Unknown type '{schema_type}' - common issues:")
                logger.info("  1. Typo in type name (should be: string, integer, number, boolean, array, object)")
                logger.info("  2. Using a schema name as type (should use $ref instead)")
                logger.info("  3. Custom type not supported by OpenAPI (consider using allOf/oneOf/anyOf)")
                logger.info(f"  Location: Check your OpenAPI spec for schemas with type='{schema_type}'")

            return self._resolve_any(context)

    def _resolve_reference(
        self, ref: str, context: TypeContext, required: bool, resolve_underlying: bool = False
    ) -> ResolvedType:
        """Resolve a $ref to its target schema."""
        target_schema = self.ref_resolver.resolve_ref(ref)
        if not target_schema:
            raise TypeResolutionError(f"Could not resolve reference: {ref}")

        return self.resolve_schema(target_schema, context, required, resolve_underlying)

    def _resolve_named_schema(self, schema: IRSchema, context: TypeContext, required: bool) -> ResolvedType:
        """Resolve a named schema (model/enum)."""
        class_name = schema.generation_name
        module_stem = getattr(schema, "final_module_stem", None)

        if not module_stem:
            logger.warning(f"Named schema '{schema.name}' missing final_module_stem attribute.")
            logger.info(f"  This usually means the schema wasn't properly processed during parsing.")
            logger.info(
                f"  Check if '{schema.name}' is defined in components/schemas or if it's an inline schema that should be promoted."
            )
            logger.info(f"  The schema will be treated as 'Any' type for now.")
            return ResolvedType(python_type=class_name or "Any", is_optional=not required)

        # Check if we're trying to import from the same module (self-import)
        # This only applies when using a RenderContextAdapter with a real RenderContext
        current_file = None
        try:
            # Only check for self-import if we have a RenderContextAdapter with real RenderContext
            if (
                hasattr(context, "render_context")
                and hasattr(context.render_context, "current_file")
                and
                # Ensure this is not a mock by checking if it has the expected methods
                hasattr(context.render_context, "add_import")
            ):
                current_file = context.render_context.current_file
        except (AttributeError, TypeError):
            # If anything goes wrong with attribute access, assume not a self-reference
            current_file = None

        # Only treat as self-reference if we have a real file path that matches
        if current_file and isinstance(current_file, str) and current_file.endswith(f"{module_stem}.py"):
            # This is a self-import (importing from the same file), so skip the import
            # and mark as forward reference to require quoting
            return ResolvedType(python_type=class_name or "Any", is_optional=not required, is_forward_ref=True)

        # Use the render context's relative path calculation to determine proper import path
        import_module = f"..models.{module_stem}"  # Default fallback

        # If we have access to RenderContext, use its proper relative path calculation
        if hasattr(context, "render_context") and hasattr(
            context.render_context, "calculate_relative_path_for_internal_module"
        ):
            try:
                # Calculate relative path from current location to the target model module
                target_module_relative = f"models.{module_stem}"
                relative_path = context.render_context.calculate_relative_path_for_internal_module(
                    target_module_relative
                )
                if relative_path:
                    import_module = relative_path
            except Exception as e:
                # If relative path calculation fails, fall back to the default
                logger.debug(f"Failed to calculate relative path for {module_stem}, using default: {e}")

        context.add_import(import_module, class_name or "Any")

        return ResolvedType(
            python_type=class_name or "Any",
            needs_import=True,
            import_module=import_module,
            import_name=class_name or "Any",
            is_optional=not required,
        )

    def _resolve_string(self, schema: IRSchema, context: TypeContext, required: bool) -> ResolvedType:
        """Resolve string type, handling enums and formats."""
        # Check if this is a properly processed enum (has generation_name)
        if hasattr(schema, "enum") and schema.enum:
            # Check if this enum was properly processed (has generation_name)
            if hasattr(schema, "generation_name") and schema.generation_name:
                # This is a properly processed enum, it should have been handled earlier
                # by _resolve_named_schema. If we're here, it might be during initial processing.
                # Return the enum type name
                return ResolvedType(python_type=schema.generation_name, is_optional=not required)
            else:
                # This is an unprocessed inline enum - log warning with details
                enum_values = schema.enum[:5] if len(schema.enum) > 5 else schema.enum
                more = f" (and {len(schema.enum) - 5} more)" if len(schema.enum) > 5 else ""
                context_info = f"name='{schema.name}'" if schema.name else "unnamed"
                logger.warning(
                    f"Found inline enum in string schema that wasn't promoted: "
                    f"{context_info}, type={schema.type}, enum_values={enum_values}{more}. "
                    f"This will be treated as plain 'str' instead of a proper Enum type."
                )
                return ResolvedType(python_type="str", is_optional=not required)

        # Handle string formats
        format_type = getattr(schema, "format", None)
        if format_type:
            format_mapping = {
                "date": "date",
                "date-time": "datetime",
                "time": "time",
                "uuid": "UUID",
                "email": "str",
                "uri": "str",
                "hostname": "str",
                "ipv4": "str",
                "ipv6": "str",
            }

            python_type = format_mapping.get(format_type, "str")

            # Add appropriate imports for special types
            if python_type == "date":
                context.add_import("datetime", "date")
            elif python_type == "datetime":
                context.add_import("datetime", "datetime")
            elif python_type == "time":
                context.add_import("datetime", "time")
            elif python_type == "UUID":
                context.add_import("uuid", "UUID")

            return ResolvedType(python_type=python_type, is_optional=not required)

        return ResolvedType(python_type="str", is_optional=not required)

    def _resolve_integer(self, context: TypeContext, required: bool) -> ResolvedType:
        """Resolve integer type."""
        return ResolvedType(python_type="int", is_optional=not required)

    def _resolve_number(self, context: TypeContext, required: bool) -> ResolvedType:
        """Resolve number type."""
        return ResolvedType(python_type="float", is_optional=not required)

    def _resolve_boolean(self, context: TypeContext, required: bool) -> ResolvedType:
        """Resolve boolean type."""
        return ResolvedType(python_type="bool", is_optional=not required)

    def _resolve_null(self, context: TypeContext, required: bool) -> ResolvedType:
        """Resolve null type.

        When a schema has type=null or no type defined (None), we map it to Python's Any type
        because null schemas represent unknown/arbitrary data rather than the None value.
        """
        context.add_import("typing", "Any")
        return ResolvedType(python_type="Any", is_optional=not required)

    def _resolve_array(
        self, schema: IRSchema, context: TypeContext, required: bool, resolve_underlying: bool = False
    ) -> ResolvedType:
        """Resolve array type."""
        items_schema = getattr(schema, "items", None)
        if not items_schema:
            schema_name = getattr(schema, "name", "unnamed")
            logger.warning(f"Array schema '{schema_name}' missing 'items' definition.")
            logger.info("  Arrays in OpenAPI must define the type of items they contain.")
            logger.info('  Example: { "type": "array", "items": { "type": "string" } }')
            logger.info("  This will be mapped to List[Any] - consider fixing the OpenAPI spec.")
            context.add_import("typing", "List")
            context.add_import("typing", "Any")
            return ResolvedType(python_type="List[Any]", is_optional=not required)

        # For array items, we generally want to preserve model references unless the item itself is a primitive alias
        # Only resolve underlying for primitive type aliases, not for actual models that should be generated
        items_resolve_underlying = (
            resolve_underlying
            and getattr(items_schema, "name", None)
            and not getattr(items_schema, "properties", None)
            and getattr(items_schema, "type", None) in ("string", "integer", "number", "boolean")
        )
        item_type = self.resolve_schema(
            items_schema, context, required=True, resolve_underlying=bool(items_resolve_underlying)
        )
        context.add_import("typing", "List")

        # Format the item type properly, handling forward references
        item_type_str = item_type.python_type
        if item_type.is_forward_ref and not item_type_str.startswith('"'):
            item_type_str = f'"{item_type_str}"'

        return ResolvedType(python_type=f"List[{item_type_str}]", is_optional=not required)

    def _resolve_object(self, schema: IRSchema, context: TypeContext, required: bool) -> ResolvedType:
        """Resolve object type."""
        properties = getattr(schema, "properties", None)

        if not properties:
            # Generic object
            context.add_import("typing", "Dict")
            context.add_import("typing", "Any")
            return ResolvedType(python_type="dict[str, Any]", is_optional=not required)

        # Object with properties - should be promoted to named type
        logger.warning("Found object with properties - should be promoted to named type")
        context.add_import("typing", "Dict")
        context.add_import("typing", "Any")
        return ResolvedType(python_type="dict[str, Any]", is_optional=not required)

    def _resolve_any(self, context: TypeContext) -> ResolvedType:
        """Resolve to Any type."""
        context.add_import("typing", "Any")
        return ResolvedType(python_type="Any")

    def _resolve_any_of(
        self, schema: IRSchema, context: TypeContext, required: bool, resolve_underlying: bool = False
    ) -> ResolvedType:
        """Resolve anyOf composition to Union type."""
        if not schema.any_of:
            return self._resolve_any(context)

        resolved_types = []
        for sub_schema in schema.any_of:
            # For union components, preserve model references unless it's a primitive type alias
            sub_resolve_underlying = (
                resolve_underlying
                and getattr(sub_schema, "name", None)
                and not getattr(sub_schema, "properties", None)
                and getattr(sub_schema, "type", None) in ("string", "integer", "number", "boolean")
            )
            sub_resolved = self.resolve_schema(
                sub_schema, context, required=True, resolve_underlying=bool(sub_resolve_underlying)
            )
            # Format sub-types properly, handling forward references
            sub_type_str = sub_resolved.python_type
            if sub_resolved.is_forward_ref and not sub_type_str.startswith('"'):
                sub_type_str = f'"{sub_type_str}"'
            resolved_types.append(sub_type_str)

        if len(resolved_types) == 1:
            return ResolvedType(python_type=resolved_types[0], is_optional=not required)

        # Sort types for consistent ordering
        resolved_types.sort()
        context.add_import("typing", "Union")
        union_type = f"Union[{', '.join(resolved_types)}]"

        return ResolvedType(python_type=union_type, is_optional=not required)

    def _resolve_all_of(
        self, schema: IRSchema, context: TypeContext, required: bool, resolve_underlying: bool = False
    ) -> ResolvedType:
        """Resolve allOf composition."""
        # For allOf, we typically need to merge the schemas
        # For now, we'll use the first schema if it has a clear type
        if not schema.all_of:
            return self._resolve_any(context)

        # Simple implementation: use the first concrete schema
        for sub_schema in schema.all_of:
            if hasattr(sub_schema, "type") and sub_schema.type:
                return self.resolve_schema(sub_schema, context, required, resolve_underlying)

        # Fallback - if no schema has a concrete type, return Any
        # Don't recurse into schemas with no type as that causes warnings
        return self._resolve_any(context)

    def _resolve_one_of(
        self, schema: IRSchema, context: TypeContext, required: bool, resolve_underlying: bool = False
    ) -> ResolvedType:
        """Resolve oneOf composition to Union type."""
        if not schema.one_of:
            return self._resolve_any(context)

        resolved_types = []
        for sub_schema in schema.one_of:
            # For union components, preserve model references unless it's a primitive type alias
            sub_resolve_underlying = (
                resolve_underlying
                and getattr(sub_schema, "name", None)
                and not getattr(sub_schema, "properties", None)
                and getattr(sub_schema, "type", None) in ("string", "integer", "number", "boolean")
            )
            sub_resolved = self.resolve_schema(
                sub_schema, context, required=True, resolve_underlying=bool(sub_resolve_underlying)
            )
            # Format sub-types properly, handling forward references
            sub_type_str = sub_resolved.python_type
            if sub_resolved.is_forward_ref and not sub_type_str.startswith('"'):
                sub_type_str = f'"{sub_type_str}"'
            resolved_types.append(sub_type_str)

        if len(resolved_types) == 1:
            return ResolvedType(python_type=resolved_types[0], is_optional=not required)

        # Sort types for consistent ordering
        resolved_types.sort()
        context.add_import("typing", "Union")
        union_type = f"Union[{', '.join(resolved_types)}]"

        return ResolvedType(python_type=union_type, is_optional=not required)
