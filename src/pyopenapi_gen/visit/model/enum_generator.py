"""
Generates Python code for enums from IRSchema objects.
"""

import keyword
import logging
import re
from typing import List, Tuple

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer

logger = logging.getLogger(__name__)


class EnumGenerator:
    """Generates Python code for an enum."""

    def __init__(self, renderer: PythonConstructRenderer):
        # Pre-condition
        assert renderer is not None, "PythonConstructRenderer cannot be None"
        self.renderer = renderer

    def _generate_member_name_for_string_enum(self, value: str) -> str:
        """
        Generates a Python-valid member name from a string enum value.

        Contracts:
            Pre-conditions:
                - ``value`` is a string.
            Post-conditions:
                - Returns a non-empty string that is a valid Python identifier, typically uppercase.
        """
        assert isinstance(value, str), "Input value must be a string."
        base_member_name = str(value).upper().replace("-", "_").replace(" ", "_")
        sanitized_member_name = re.sub(r"[^A-Z0-9_]", "", base_member_name)

        if not sanitized_member_name:
            # Handle empty string or string that became empty after sanitization
            # Using a generic placeholder if original value was also effectively empty/non-descriptive
            # Or try to derive something if the original string had some content before stripping
            original_alnum = re.sub(r"[^A-Za-z0-9]", "", str(value))
            if not original_alnum:
                sanitized_member_name = "MEMBER_EMPTY_STRING"
            else:
                # Attempt to form a name from original alphanumeric chars if sanitization wiped it
                sanitized_member_name = f"MEMBER_{original_alnum.upper()}"
                if sanitized_member_name[0].isdigit():  # Check if this new form starts with a digit
                    sanitized_member_name = f"MEMBER_{sanitized_member_name}"  # MEMBER_MEMBER_... is ok
        elif sanitized_member_name[0].isdigit():
            sanitized_member_name = f"MEMBER_{sanitized_member_name}"

        if keyword.iskeyword(sanitized_member_name.lower()):  # Check lowercase version for keyword
            sanitized_member_name += "_"

        # Final check for safety: if it's still not a valid start (e.g. _MEMBER_...)
        if not re.match(r"^[A-Z_]", sanitized_member_name.upper()):
            sanitized_member_name = f"MEMBER_{sanitized_member_name}"

        assert sanitized_member_name and re.match(r"^[A-Z_][A-Z0-9_]*$", sanitized_member_name.upper()), (
            f"Generated string enum member name '{sanitized_member_name}' is not a valid Python identifier from value '{value}'."
        )
        return sanitized_member_name

    def _generate_member_name_for_integer_enum(self, value: str | int, int_value_for_fallback: int) -> str:
        """
        Generates a Python-valid member name from an integer enum value (or its string representation).

        Contracts:
            Pre-conditions:
                - ``value`` is a string or an int.
                - ``int_value_for_fallback`` is an int.
            Post-conditions:
                - Returns a non-empty string that is a valid Python identifier, typically uppercase.
        """
        assert isinstance(value, (str, int)), "Input value for integer enum naming must be str or int."
        assert isinstance(int_value_for_fallback, int), "Fallback integer value must be an int."

        name_basis = str(value)  # Use string representation as basis for name
        base_member_name = name_basis.upper().replace("-", "_").replace(" ", "_").replace(".", "_DOT_")
        sanitized_member_name = re.sub(r"[^A-Z0-9_]", "", base_member_name)

        if not sanitized_member_name:
            # If string value like "-" or "." became empty, use the int value directly
            if int_value_for_fallback < 0:
                sanitized_member_name = f"VALUE_NEG_{abs(int_value_for_fallback)}"
            else:
                sanitized_member_name = f"VALUE_{int_value_for_fallback}"
            # This form should be inherently valid (VALUE_ + digits or VALUE_NEG_ + digits)
        elif not re.match(r"^[A-Z_]", sanitized_member_name.upper()):  # Check if starts with letter/underscore
            # If it starts with a digit, or some other non-alpha (though re.sub should prevent others)
            sanitized_member_name = f"VALUE_{sanitized_member_name}"

        if keyword.iskeyword(sanitized_member_name.lower()):  # Check lowercase version
            sanitized_member_name += "_"

        # One final check: ensure it starts with an uppercase letter or underscore
        if not re.match(r"^[A-Z_]", sanitized_member_name.upper()):
            # This is a last resort, should be rare. Prefix to ensure validity.
            sanitized_member_name = f"ENUM_MEMBER_{sanitized_member_name}"
            # And re-sanitize this new prefixed name just in case the original had problematic chars
            sanitized_member_name = re.sub(r"[^A-Z0-9_]", "", sanitized_member_name.upper())
            if not sanitized_member_name:  # Should be impossible
                sanitized_member_name = f"ENUM_MEMBER_UNKNOWN_{abs(int_value_for_fallback)}"

        assert sanitized_member_name and re.match(r"^[A-Z_][A-Z0-9_]*$", sanitized_member_name.upper()), (
            f"Generated integer enum member name '{sanitized_member_name}' is not a valid Python identifier from value '{value}'."
        )
        return sanitized_member_name

    def generate(
        self,
        schema: IRSchema,
        base_name: str,  # This is the class name, will be sanitized by PythonConstructRenderer
        context: RenderContext,
    ) -> str:
        """
        Generates the Python code for an enum.

        Args:
            schema: The IRSchema for the enum.
            base_name: The base name for the enum class.
            context: The render context.

        Returns:
            The generated Python code string for the enum.

        Contracts:
            Pre-conditions:
                - ``schema`` is not None, ``schema.name`` is not None, and ``schema.enum`` is not None and not empty.
                - ``schema.type`` is either "string" or "integer".
                - ``base_name`` is a non-empty string.
                - ``context`` is not None.
            Post-conditions:
                - Returns a non-empty string containing valid Python code for an enum.
                - ``Enum`` from the ``enum`` module is imported in the context.
        """
        assert schema is not None, "Schema cannot be None for enum generation."
        assert schema.name is not None, "Schema name must be present for enum generation."
        assert base_name, "Base name cannot be empty for enum generation."
        assert context is not None, "RenderContext cannot be None."
        assert schema.enum, "Schema must have enum values for enum generation."
        assert schema.type in ("string", "integer"), "Enum schema type must be 'string' or 'integer'."

        enum_class_name = base_name  # PythonConstructRenderer will sanitize this class name
        base_type = "str" if schema.type == "string" else "int"
        values: List[Tuple[str, str | int]] = []
        processed_member_names = set()

        for val_from_spec in schema.enum:
            member_name: str
            member_value: str | int

            if base_type == "str":
                member_value = str(val_from_spec)
                member_name = self._generate_member_name_for_string_enum(member_value)
            else:  # Integer enum
                try:
                    actual_int_value = int(val_from_spec)
                except (ValueError, TypeError):
                    logger.warning(
                        f"EnumGenerator: Could not convert enum value '{val_from_spec}' to int for schema '{schema.name}'. Using value 0."
                    )
                    actual_int_value = 0  # Fallback value
                member_value = actual_int_value
                # Pass original spec value for naming, and the actual int value for fallback naming
                member_name = self._generate_member_name_for_integer_enum(val_from_spec, actual_int_value)

            # Handle duplicate member names by appending a counter
            unique_member_name = member_name
            counter = 1
            while unique_member_name in processed_member_names:
                unique_member_name = f"{member_name}_{counter}"
                counter += 1
            processed_member_names.add(unique_member_name)

            values.append((unique_member_name, member_value))

        # logger.debug(
        #     f"EnumGenerator: Preparing to render enum '{enum_class_name}' with base type '{base_type}' and members: {values}."
        # )
        rendered_code = self.renderer.render_enum(
            enum_name=enum_class_name,  # Pass the original base_name; renderer handles class name sanitization
            base_type=base_type,
            values=values,
            description=schema.description,
            context=context,
        )

        assert rendered_code.strip(), "Generated enum code cannot be empty."
        assert "enum" in context.import_collector.imports and "Enum" in context.import_collector.imports["enum"], (
            "Enum import was not added to context by renderer."
        )

        return rendered_code
