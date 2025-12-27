"""Resolves IRSchema to Python primitive types."""

import logging

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext

logger = logging.getLogger(__name__)


class PrimitiveTypeResolver:
    """Resolves IRSchema to Python primitive type strings."""

    def __init__(self, context: RenderContext):
        self.context = context

    def resolve(self, schema: IRSchema) -> str | None:
        """
        Resolves an IRSchema to a Python primitive type string based on its 'type' and 'format'.

        Handles standard OpenAPI types and formats:
        - integer -> "int" (also int32, int64 formats)
        - number -> "float" (also float, double formats)
        - boolean -> "bool"
        - string -> "str"
        - string with format "date-time" -> "datetime" (imports `datetime.datetime`)
        - string with format "date" -> "date" (imports `datetime.date`)
        - string with format "time" -> "time" (imports `datetime.time`)
        - string with format "duration" -> "timedelta" (imports `datetime.timedelta`)
        - string with format "uuid" -> "UUID" (imports `uuid.UUID`)
        - string with format "binary" or "byte" -> "bytes"
        - string with format "ipv4" -> "IPv4Address" (imports `ipaddress.IPv4Address`)
        - string with format "ipv6" -> "IPv6Address" (imports `ipaddress.IPv6Address`)
        - string with format "uri", "url", "email", "hostname", "password" -> "str"
        - null -> "None" (the string literal "None")

        Args:
            schema: The IRSchema to resolve.

        Returns:
            The Python primitive type string if the schema matches a known primitive type/format,
            otherwise None.
        """
        if schema.type == "null":
            return "None"

        # Handle string formats first (before falling through to generic string)
        if schema.type == "string" and schema.format:
            return self._resolve_string_format(schema.format)

        # Handle integer formats
        if schema.type == "integer":
            # int32 and int64 both map to Python int
            return "int"

        # Handle number formats
        if schema.type == "number":
            # float and double both map to Python float
            return "float"

        # Handle remaining primitive types
        primitive_type_map = {
            "boolean": "bool",
            "string": "str",
        }
        if schema.type in primitive_type_map:
            return primitive_type_map[schema.type]

        return None

    def _resolve_string_format(self, format_value: str) -> str:
        """Resolve string type with specific format to Python type."""
        # Date/time formats
        if format_value == "date-time":
            self.context.add_import("datetime", "datetime")
            return "datetime"
        if format_value == "date":
            self.context.add_import("datetime", "date")
            return "date"
        if format_value == "time":
            self.context.add_import("datetime", "time")
            return "time"
        if format_value == "duration":
            self.context.add_import("datetime", "timedelta")
            return "timedelta"

        # UUID format
        if format_value == "uuid":
            self.context.add_import("uuid", "UUID")
            return "UUID"

        # Binary formats
        if format_value in ("binary", "byte"):
            return "bytes"

        # IP address formats
        if format_value == "ipv4":
            self.context.add_import("ipaddress", "IPv4Address")
            return "IPv4Address"
        if format_value == "ipv6":
            self.context.add_import("ipaddress", "IPv6Address")
            return "IPv6Address"

        # String-based formats (no special Python type, just str)
        if format_value in ("uri", "url", "email", "hostname", "password"):
            return "str"

        # Unknown format - fall back to str
        return "str"
