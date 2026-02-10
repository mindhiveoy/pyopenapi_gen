"""Utilities for pyopenapi_gen.

This module contains utility classes and functions used across the code generation process.
"""

import base64
import dataclasses
import keyword
import logging
import re
from typing import Any, Set, Type, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")


class NameSanitizer:
    """Helper to sanitize spec names and tags into valid Python identifiers and filenames."""

    # Python built-ins and common problematic names that should be avoided in module names
    RESERVED_NAMES = {
        # Built-in types
        "type",
        "int",
        "str",
        "float",
        "bool",
        "list",
        "dict",
        "set",
        "tuple",
        "bytes",
        "object",
        "complex",
        "frozenset",
        "bytearray",
        "memoryview",
        "range",
        # Built-in functions
        "abs",
        "all",
        "any",
        "bin",
        "callable",
        "chr",
        "classmethod",
        "compile",
        "delattr",
        "dir",
        "divmod",
        "enumerate",
        "eval",
        "exec",
        "filter",
        "format",
        "getattr",
        "globals",
        "hasattr",
        "hash",
        "help",
        "hex",
        "id",
        "input",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "locals",
        "map",
        "max",
        "min",
        "next",
        "oct",
        "open",
        "ord",
        "pow",
        "print",
        "property",
        "repr",
        "reversed",
        "round",
        "setattr",
        "slice",
        "sorted",
        "staticmethod",
        "sum",
        "super",
        "vars",
        "zip",
        # Common standard library modules
        "os",
        "sys",
        "json",
        "time",
        "datetime",
        "math",
        "random",
        "string",
        "collections",
        "itertools",
        "functools",
        "typing",
        "pathlib",
        "logging",
        "urllib",
        "http",
        "email",
        "uuid",
        "hashlib",
        "base64",
        "copy",
        "re",
        # Other problematic names
        "data",
        "model",
        "models",
        "client",
        "api",
        "config",
        "utils",
        "helpers",
    }

    @staticmethod
    def sanitize_module_name(name: str) -> str:
        """Convert a raw name into a valid Python module name in snake_case,
        splitting camel case and PascalCase."""
        # # <<< Add Check for problematic input >>>
        # if '[' in name or ']' in name or ',' in name:
        #     logger.error(f"sanitize_module_name received potentially invalid input: '{name}'")
        #     # Optionally, return a default/error value or raise exception
        #     # For now, just log and continue
        # # <<< End Check >>>

        # Split on non-alphanumeric and camel case boundaries
        words = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", name)
        if not words:
            # fallback: split on non-alphanumerics
            words = re.split(r"\W+", name)
        module = "_".join(word.lower() for word in words if word)
        # If it starts with a digit, prefix with underscore
        if module and module[0].isdigit():
            module = "_" + module
        # Avoid Python keywords and reserved names
        if keyword.iskeyword(module) or module in NameSanitizer.RESERVED_NAMES:
            module += "_"
        return module

    @staticmethod
    def sanitize_class_name(name: str) -> str:
        """Convert a raw name into a valid Python class name in PascalCase."""
        # Split on non-alphanumeric and camel case boundaries
        words = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", name)
        if not words:  # Fallback if findall is empty (e.g. if name was all symbols)
            # Basic split on non-alphanumeric as a last resort if findall yields nothing
            words = [part for part in re.split(r"[^a-zA-Z0-9]+", name) if part]

        # Capitalize each word and join
        cls_name = "".join(word.capitalize() for word in words if word)

        if not cls_name:  # If name was e.g. "-" or "_"
            cls_name = "UnnamedClass"  # Or some other default

        # If it starts with a digit, prefix with underscore
        if cls_name[0].isdigit():  # Check after ensuring cls_name is not empty
            cls_name = "_" + cls_name
        # Avoid Python keywords and reserved names (case-insensitive)
        if keyword.iskeyword(cls_name.lower()) or cls_name.lower() in NameSanitizer.RESERVED_NAMES:
            cls_name += "_"
        return cls_name

    @staticmethod
    def sanitize_tag_class_name(tag: str) -> str:
        """Sanitize a tag for use as a PascalCase client class name (e.g., DataSourcesClient)."""
        words = re.split(r"[\W_]+", tag)
        return "".join(word.capitalize() for word in words if word) + "Client"

    @staticmethod
    def sanitize_tag_attr_name(tag: str) -> str:
        """Sanitize a tag for use as a snake_case attribute name (e.g., data_sources)."""
        attr = re.sub(r"[\W]+", "_", tag).lower()
        return attr.strip("_")

    @staticmethod
    def normalize_tag_key(tag: str) -> str:
        """Normalize a tag for case-insensitive uniqueness (e.g., datasources)."""
        return re.sub(r"[\W_]+", "", tag).lower()

    @staticmethod
    def sanitize_filename(name: str, suffix: str = ".py") -> str:
        """Generate a valid Python filename from raw name in snake_case."""
        module = NameSanitizer.sanitize_module_name(name)
        return module + suffix

    @staticmethod
    def sanitize_method_name(name: str) -> str:
        """Convert a raw name into a valid Python method name in snake_case,
        splitting camelCase and PascalCase."""
        # Remove curly braces
        name = re.sub(r"[{}]", "", name)
        # Split camelCase and PascalCase to snake_case
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        # Replace non-alphanumerics with underscores
        name = re.sub(r"[^0-9a-zA-Z_]", "_", name)
        # Lowercase and collapse multiple underscores
        name = re.sub(r"_+", "_", name).strip("_").lower()
        # If it starts with a digit, prefix with underscore
        if name and name[0].isdigit():
            name = "_" + name
        # Avoid Python keywords and reserved names
        if keyword.iskeyword(name) or name in NameSanitizer.RESERVED_NAMES:
            name += "_"
        return name

    @staticmethod
    def clean_auto_generated_operation_id(operation_id: str, http_method: str, path: str) -> str:
        """Strip FastAPI auto-generated suffixes from an operationId.

        FastAPI generates operationIds like ``create_details_details_post``
        from handler ``create_details`` at ``POST /details``. This method
        detects that pattern and returns just ``create_details``.

        If the pattern is not detected the original *operation_id* is
        returned unchanged.
        """
        method_lower = http_method.lower()
        method_suffix = f"_{method_lower}"

        # 1. operationId must end with _{method}
        if not operation_id.lower().endswith(method_suffix):
            return operation_id

        # 2. Strip the method suffix (preserve original casing of the prefix)
        without_method = operation_id[: -len(method_suffix)]

        # 3. Normalise path to the FastAPI segment format.
        #    FastAPI replaces all non-word characters (\W) with underscores,
        #    so we must do the same to match paths with hyphens, dots, etc.
        normalized_path = path.strip("/")
        normalized_path = re.sub(r"[{}]", "", normalized_path)
        normalized_path = re.sub(r"[^0-9a-zA-Z_]", "_", normalized_path)
        normalized_path = re.sub(r"_+", "_", normalized_path).strip("_").lower()

        # 4. Check for _{normalized_path} suffix
        if not normalized_path:
            return operation_id

        path_suffix = f"_{normalized_path}"
        if without_method.lower().endswith(path_suffix):
            prefix = without_method[: -len(path_suffix)]
            # 5. Guard against empty result
            if prefix:
                return prefix

        return operation_id

    @staticmethod
    def is_valid_python_identifier(name: str) -> bool:
        """Check if a string is a valid Python identifier."""
        if not isinstance(name, str) or not name:
            return False
        # Check if it's a keyword
        if keyword.iskeyword(name):
            return False
        # Check pattern: starts with letter/underscore, then letter/digit/underscore
        return re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name) is not None


class ParamSubstitutor:
    """Helper for rendering path templates with path parameters."""

    @staticmethod
    def render_path(template: str, values: dict[str, Any]) -> str:
        """Replace placeholders in a URL path template using provided values."""
        rendered = template
        for key, val in values.items():
            rendered = rendered.replace(f"{{{key}}}", str(val))
        return rendered


class KwargsBuilder:
    """Builder for assembling HTTP request keyword arguments."""

    def __init__(self) -> None:
        self._kwargs: dict[str, Any] = {}

    def with_params(self, **params: Any) -> "KwargsBuilder":
        """Add query parameters, skipping None values."""
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            self._kwargs["params"] = filtered
        return self

    def with_json(self, body: Any) -> "KwargsBuilder":
        """Add a JSON body to the request."""
        self._kwargs["json"] = body
        return self

    def build(self) -> dict[str, Any]:
        """Return the assembled kwargs dictionary."""
        return self._kwargs


class Formatter:
    """Helper to format code using Black, falling back to unformatted content if
    Black is unavailable or errors."""

    def __init__(self) -> None:
        from typing import Any, Callable

        self._file_mode: Any | None = None
        self._format_str: Callable[..., str] | None = None
        try:
            from black import FileMode, format_str

            # Suppress blib2to3 debug logging that floods output during formatting
            blib2to3_logger = logging.getLogger("blib2to3")
            blib2to3_logger.setLevel(logging.WARNING)

            # Also suppress the driver logger specifically
            driver_logger = logging.getLogger("blib2to3.pgen2.driver")
            driver_logger.setLevel(logging.WARNING)

            # Initialize Black formatter
            self._file_mode = FileMode()
            self._format_str = format_str
        except ImportError:
            self._file_mode = None
            self._format_str = None

    def format(self, code: str) -> str:
        """Format the given code string with Black if possible."""
        if self._format_str is not None and self._file_mode is not None:
            try:
                formatted: str = self._format_str(code, mode=self._file_mode)
                return formatted
            except Exception:
                # On any Black formatting error, return original code
                return code
        return code


# --- Casting Helper ---


def safe_cast(expected_type: Type[T], data: Any) -> T:
    """
    Performs a cast for the type checker using object cast.
    (Validation temporarily removed).
    """
    # No validation for now
    # Cast to object first, then to expected_type
    return cast(expected_type, cast(object, data))  # type: ignore[valid-type]


class DataclassSerializer:
    """Utility for converting dataclass instances to dictionaries for API serialisation.

    This is a convenience wrapper around cattrs unstructure_to_dict() with
    circular reference protection. All serialisation is delegated to cattrs which provides:
    - Custom unstructure hooks for correct handling of generated types
    - Field name transformation (snake_case → camelCase)
    - Type-specific handling (datetime, bytes, enums)
    - Recursive nested dataclass handling

    Circular reference protection is provided by tracking visited objects and
    post-processing cattrs output to ensure complete dict conversion.

    Note: This class is maintained for backward compatibility.
    New code should use unstructure_to_dict() directly from cattrs_converter.
    """

    @staticmethod
    def serialize(obj: Any) -> Any:
        """Convert dataclass instances to dictionaries using cattrs with circular ref protection.

        Uses cattrs converter which respects custom unstructure hooks
        for correct handling of all generated types, with additional circular
        reference tracking to ensure JSON-safe output.

        Args:
            obj: The object to serialise. Can be a dataclass, list, dict, or primitive.

        Returns:
            The serialised object with dataclasses converted to dictionaries.
            Guaranteed to be JSON-serializable (no dataclass instances in output).

        Handles:
        - Dataclass instances with Meta.key_transform_with_dump: Applies field
          name mapping (snake_case → camelCase)
        - Regular dataclass instances: Converted to dictionaries using field names
        - Lists: Recursively serialise each item
        - Dictionaries: Recursively serialise values
        - datetime: Convert to ISO format string
        - Enums: Convert to their value
        - bytes/bytearray: Convert to base64-encoded ASCII string
        - Primitives: Return unchanged
        - None values: Excluded from output
        - Circular references: Handled gracefully (returns None for cycles)
        - Custom cattrs hooks: Applied automatically for types with registered hooks
        """
        return DataclassSerializer._serialize_with_tracking(obj, set())

    @staticmethod
    def _serialize_with_tracking(obj: Any, visited: Set[int]) -> Any:
        """Internal serialisation with circular reference tracking.

        This wraps cattrs.unstructure_to_dict() with:
        - Circular reference detection (prevents infinite recursion)
        - Post-processing to ensure complete dict conversion

        cattrs handles:
        - Custom unstructure hooks (critical for types with _data fields)
        - Field name transformations (Meta.key_transform_with_dump)
        - Type-specific conversions (datetime, enum, bytes)

        Args:
            obj: The object to serialise
            visited: Set of object IDs currently being processed

        Returns:
            Serialised object with all dataclasses converted to dicts
        """
        from .cattrs_converter import unstructure_to_dict

        # Handle primitives early (no tracking needed)
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle circular references
        obj_id = id(obj)
        if obj_id in visited:
            # Return None for circular refs (JSON-safe, avoids infinite recursion)
            return None

        # Special handling for bytearray (cattrs handles bytes but not bytearray)
        if isinstance(obj, bytearray):
            return base64.b64encode(bytes(obj)).decode("ascii")

        # Handle lists - recurse on each item
        if isinstance(obj, list):
            visited.add(obj_id)
            try:
                return [DataclassSerializer._serialize_with_tracking(item, visited) for item in obj]
            finally:
                visited.remove(obj_id)

        # For dataclasses, track and use cattrs
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            visited.add(obj_id)
            try:
                # Let cattrs do the heavy lifting (respects custom hooks, field mappings, etc.)
                result = unstructure_to_dict(obj)

                # Post-process to ensure nested dataclasses are fully converted
                result = DataclassSerializer._ensure_all_dicts(result, visited)

                # Filter None values (maintains API compatibility)
                return DataclassSerializer._remove_none_values(result)
            finally:
                visited.remove(obj_id)

        # For everything else (dicts, primitives, etc.), let cattrs handle it
        result = unstructure_to_dict(obj)
        return DataclassSerializer._remove_none_values(result)

    @staticmethod
    def _ensure_all_dicts(obj: Any, visited: Set[int]) -> Any:
        """Post-process cattrs output to ensure nested dataclasses are dicts.

        cattrs sometimes leaves nested dataclass instances unconverted in circular
        reference scenarios. This recursively ensures all dataclasses become dicts.

        Args:
            obj: The object from cattrs (dict, list, or primitive)
            visited: Set of object IDs already being processed

        Returns:
            Object with all nested dataclasses converted to dicts
        """
        # If we encounter a dataclass instance, it wasn't properly unstructured by cattrs
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            # Recurse through serialize to handle it properly
            return DataclassSerializer._serialize_with_tracking(obj, visited)

        # Recursively process dict values
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if value is not None:  # Skip None values
                    processed = DataclassSerializer._ensure_all_dicts(value, visited)
                    if processed is not None:  # Only include if not None after processing
                        result[key] = processed
            return result

        # Recursively process list items
        if isinstance(obj, list):
            return [DataclassSerializer._ensure_all_dicts(item, visited) for item in obj]

        # Primitives pass through
        return obj

    @staticmethod
    def _remove_none_values(obj: Any) -> Any:
        """Recursively remove None values from dictionaries and lists.

        Args:
            obj: The object to filter (dict, list, or other)

        Returns:
            The object with None values removed from dicts
        """
        if isinstance(obj, dict):
            return {k: DataclassSerializer._remove_none_values(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [DataclassSerializer._remove_none_values(item) for item in obj]
        else:
            return obj
