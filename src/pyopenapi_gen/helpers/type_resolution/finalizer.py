"""Finalizes and cleans Python type strings."""

import logging

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.type_cleaner import TypeCleaner

logger = logging.getLogger(__name__)


class TypeFinalizer:
    """Handles final wrapping (Optional) and cleaning of type strings."""

    def __init__(self, context: RenderContext, all_schemas: dict[str, IRSchema] | None = None):
        self.context = context
        self.all_schemas = all_schemas if all_schemas is not None else {}

    def finalize(self, py_type: str | None, schema: IRSchema, required: bool) -> str:
        """Wraps with Optional if needed, cleans the type string, and ensures typing imports."""
        if py_type is None:
            logger.warning(
                f"[TypeFinalizer] Received None as py_type for schema "
                f"'{schema.name or 'anonymous'}'. Defaulting to 'Any'."
            )
            self.context.add_import("typing", "Any")
            py_type = "Any"

        # CRITICAL: Clean BEFORE wrapping to prevent TypeCleaner from breaking "Union[X] | None" patterns
        cleaned_type = self._clean_type(py_type)
        optional_type = self._wrap_with_optional_if_needed(cleaned_type, schema, required)

        # Ensure imports for common typing constructs that might have been introduced by cleaning or wrapping
        final_type = optional_type  # Use the wrapped type for import analysis
        if "dict[" in final_type or final_type == "Dict":
            self.context.add_import("typing", "Dict")
        if "List[" in final_type or final_type == "List":
            self.context.add_import("typing", "List")
        if "Tuple[" in final_type or final_type == "Tuple":  # Tuple might also appear bare
            self.context.add_import("typing", "Tuple")
        if "Union[" in final_type:
            self.context.add_import("typing", "Union")
        # Optional is now handled entirely by _wrap_with_optional_if_needed and not here
        if final_type == "Any" or final_type == "Any | None":  # Ensure Any is imported if it's the final type
            self.context.add_import("typing", "Any")

        return final_type

    def _wrap_with_optional_if_needed(self, py_type: str, schema_being_wrapped: IRSchema, required: bool) -> str:
        """Wraps the Python type string with `... | None` if necessary.

        Note: Modern Python 3.10+ uses X | None syntax exclusively.
        Optional[X] should NEVER appear here - our unified type system generates X | None directly.
        """
        is_considered_optional_by_usage = not required or schema_being_wrapped.is_nullable is True

        if not is_considered_optional_by_usage:
            return py_type  # Not optional by usage, so don't wrap.

        # At this point, usage implies optional. Now check if py_type inherently is.

        if py_type == "Any":
            # Modern Python 3.10+ doesn't need Optional import for | None syntax
            return "Any | None"  # Any is special, always wrap if usage is optional.

        # SANITY CHECK: Unified type system should never produce Optional[X]
        if py_type.startswith("Optional[") and py_type.endswith("]"):
            logger.error(
                f"❌ ARCHITECTURE VIOLATION: Received legacy Optional[X] type: {py_type}. "
                f"This should NEVER happen - unified type system generates X | None directly. "
                f"Schema: {schema_being_wrapped.name or 'anonymous'}. "
                f"This indicates a bug in the type resolution pipeline."
            )
            # Defensive conversion (but this indicates a serious bug upstream)
            inner_type = py_type[9:-1]  # Remove "Optional[" and "]"
            logger.warning(f"⚠️ Converted to modern syntax: {inner_type} | None")
            return f"{inner_type} | None"

        # If already has | None (modern style), don't add again
        if " | None" in py_type or py_type.endswith("| None"):
            return py_type  # Already has | None union syntax.

        is_union_with_none = "Union[" in py_type and (
            ", None]" in py_type or "[None," in py_type or ", None," in py_type or py_type == "Union[None]"
        )
        if is_union_with_none:
            return py_type  # Already a Union with None.

        # New check: if py_type refers to a named schema that IS ITSELF nullable,
        # its alias definition (if it's an alias) or its usage as a dataclass field type
        # will effectively be Optional. So, if field usage is optional, we don't ADD another Optional layer.
        if py_type in self.all_schemas:  # Check if py_type is a known schema name
            referenced_schema = self.all_schemas[py_type]
            # If the schema being referenced is itself nullable, its definition (if alias)
            # or its direct usage (if dataclass) will incorporate Optional via the resolver calling this finalizer.
            # Thus, we avoid double-wrapping if the *usage* of this type is also optional.
            if referenced_schema.is_nullable:
                return py_type

        # Wrap type with modern | None syntax (no Optional import needed in Python 3.10+)
        return f"{py_type} | None"

    def _clean_type(self, type_str: str) -> str:
        """Cleans a Python type string using TypeCleaner."""
        return TypeCleaner.clean_type_parameters(type_str)
