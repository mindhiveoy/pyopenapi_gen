"""Finalizes and cleans Python type strings."""

import logging
from typing import Dict, Optional as TypingOptional  # Alias to avoid clash

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.type_cleaner import TypeCleaner

logger = logging.getLogger(__name__)


class TypeFinalizer:
    """Handles final wrapping (Optional) and cleaning of type strings."""

    def __init__(self, context: RenderContext, all_schemas: TypingOptional[Dict[str, IRSchema]] = None):
        self.context = context
        self.all_schemas = all_schemas if all_schemas is not None else {}

    def finalize(self, py_type: TypingOptional[str], schema: IRSchema, required: bool) -> str:
        """Wraps with Optional if needed, cleans the type string, and ensures typing imports."""
        if py_type is None:
            logger.warning(
                f"[TypeFinalizer] Received None as py_type for schema '{schema.name or 'anonymous'}'. Defaulting to 'Any'."
            )
            self.context.add_import("typing", "Any")
            py_type = "Any"

        optional_type = self._wrap_with_optional_if_needed(py_type, schema, required)
        cleaned_type = self._clean_type(optional_type)

        # Ensure imports for common typing constructs that might have been introduced by cleaning
        if "Dict[" in cleaned_type or cleaned_type == "Dict":
            self.context.add_import("typing", "Dict")
        if "List[" in cleaned_type or cleaned_type == "List":
            self.context.add_import("typing", "List")
        if "Tuple[" in cleaned_type or cleaned_type == "Tuple":  # Tuple might also appear bare
            self.context.add_import("typing", "Tuple")
        if "Union[" in cleaned_type:
            self.context.add_import("typing", "Union")
        # Optional is now handled entirely by _wrap_with_optional_if_needed and not here
        if cleaned_type == "Any":  # Ensure Any is imported if it's the final type
            self.context.add_import("typing", "Any")

        return cleaned_type

    def _wrap_with_optional_if_needed(self, py_type: str, schema_being_wrapped: IRSchema, required: bool) -> str:
        """Wraps the Python type string with `Optional[...]` if necessary."""
        is_considered_optional_by_usage = not required or schema_being_wrapped.is_nullable is True

        if not is_considered_optional_by_usage:
            return py_type  # Not optional by usage, so don't wrap.

        # At this point, usage implies optional. Now check if py_type inherently is.

        if py_type == "Any":
            self.context.add_import("typing", "Optional")
            return "Optional[Any]"  # Any is special, always wrap if usage is optional.

        # If already Optional, don't add import again
        if py_type.startswith("Optional["):
            return py_type  # Already explicitly Optional.

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

        # Only now add the Optional import and wrap the type
        self.context.add_import("typing", "Optional")
        return f"Optional[{py_type}]"

    def _clean_type(self, type_str: str) -> str:
        """Cleans a Python type string using TypeCleaner."""
        return TypeCleaner.clean_type_parameters(type_str)
