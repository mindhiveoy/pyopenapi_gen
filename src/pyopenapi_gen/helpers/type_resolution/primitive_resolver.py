"""Resolves IRSchema to Python primitive types."""

import logging
from typing import Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext

logger = logging.getLogger(__name__)


class PrimitiveTypeResolver:
    """Resolves IRSchema to Python primitive type strings."""

    def __init__(self, context: RenderContext):
        self.context = context

    def resolve(self, schema: IRSchema) -> Optional[str]:
        """
        Resolves an IRSchema to a Python primitive type string based on its 'type' and 'format'.

        Handles standard OpenAPI types:
        - integer -> "int"
        - number -> "float"
        - boolean -> "bool"
        - string -> "str"
        - string with format "date-time" -> "datetime" (imports `datetime.datetime`)
        - string with format "date" -> "date" (imports `datetime.date`)
        - string with format "binary" -> "bytes"
        - null -> "None" (the string literal "None")

        Args:
            schema: The IRSchema to resolve.

        Returns:
            The Python primitive type string if the schema matches a known primitive type/format,
            otherwise None.
        """
        primitive_type_map = {
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "string": "str",
        }
        if schema.type == "null":
            return "None"  # String literal "None"
        if schema.type == "string" and schema.format == "date-time":
            logger.debug(
                f"[PrimitiveTypeResolver] Matched date-time for schema: {schema.name or 'anonymous'}. Adding specific import."
            )
            self.context.add_import("datetime", "datetime")
            return "datetime"
        if schema.type == "string" and schema.format == "date":
            logger.debug(
                f"[PrimitiveTypeResolver] Matched date for schema: {schema.name or 'anonymous'}. Adding specific import."
            )
            self.context.add_import("datetime", "date")
            return "date"
        if schema.type == "string" and schema.format == "binary":
            return "bytes"
        if schema.type in primitive_type_map:
            return primitive_type_map[schema.type]
        return None
