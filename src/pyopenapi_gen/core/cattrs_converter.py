"""
cattrs converter utilities for generated clients.

This module provides cattrs converter functions for JSON serialization/deserialization
in generated API clients. It handles:
- Automatic camelCase ↔ snake_case transformation
- Python keyword conflicts (id → id_)
- base64 bytes encoding/decoding
- Nested object structures

The converter is configured globally to handle name transformations automatically
for all dataclasses, with no per-class metadata required.
"""

from __future__ import annotations

import base64
import dataclasses
import re
import types
from datetime import date, datetime
from typing import Any, Callable, TypeVar, Union, get_args, get_origin, get_type_hints

import cattrs
from cattrs.errors import BaseValidationError, ClassValidationError, IterableValidationError
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override

T = TypeVar("T")

# Python keywords that get '_' suffix in generated code
PYTHON_KEYWORDS = {
    "id",
    "type",
    "class",
    "def",
    "return",
    "if",
    "elif",
    "else",
    "for",
    "while",
    "import",
    "from",
    "as",
    "pass",
    "break",
    "continue",
}


def camel_to_snake(name: str) -> str:
    """
    Convert camelCase to snake_case.

    Scenario:
        Convert JSON field names (camelCase) to Python field names (snake_case).

    Expected Outcome:
        Proper snake_case transformation with special handling for Python keywords.

    Examples:
        "pageSize" → "page_size"
        "totalPages" → "total_pages"
        "hasNext" → "has_next"
        "id" → "id_" (Python keyword)
        "_count" → "count" (leading underscore preserved as-is in JSON, but mapped)
    """
    # Insert underscore before uppercase letters
    snake = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    snake = snake.lower()

    # Add trailing underscore for Python keywords
    if snake in PYTHON_KEYWORDS:
        snake = f"{snake}_"

    return snake


def snake_to_camel(name: str) -> str:
    """
    Convert snake_case to camelCase.

    Scenario:
        Convert Python field names (snake_case) back to JSON field names (camelCase).

    Expected Outcome:
        Proper camelCase transformation with special handling for Python keyword suffixes.

    Examples:
        "page_size" → "pageSize"
        "total_pages" → "totalPages"
        "has_next" → "hasNext"
        "id_" → "id" (remove trailing underscore from Python keyword)
        "count" → "_count" (if original JSON had leading underscore)
    """
    # Remove trailing underscore if it was added for Python keyword
    if name.endswith("_") and name[:-1] in PYTHON_KEYWORDS:
        name = name[:-1]

    # Convert snake_case to camelCase
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


# Global converter instance with automatic name transformation
converter = cattrs.Converter()


def _make_dataclass_structure_fn(cls: type[T]) -> Any:
    """
    Create a structure function for a dataclass with automatic name transformation.

    Scenario:
        Generate a structure function that automatically converts JSON keys
        (camelCase) to Python dataclass field names (snake_case).

    Expected Outcome:
        A function that cattrs can use to structure JSON into the dataclass,
        with automatic field name transformation.
    """
    # Get field renaming map (JSON key → Python field name)
    field_overrides: dict[str, Any] = {}
    if dataclasses.is_dataclass(cls):
        for field in dataclasses.fields(cls):
            python_name = field.name
            json_key = python_name  # Default: no transformation

            # Check if class has Meta with explicit mappings
            if hasattr(cls, "Meta") and hasattr(cls.Meta, "key_transform_with_load"):  # type: ignore[attr-defined]
                mappings: dict[str, str] = cls.Meta.key_transform_with_load  # type: ignore[attr-defined]
                # Meta.key_transform_with_load is: {"json_key": "python_field"}
                # Find the JSON key that maps to this Python field
                for jk, pf in mappings.items():
                    if pf == python_name:
                        json_key = jk
                        break
                else:
                    # If not in explicit mappings, try snake_to_camel conversion
                    json_key = snake_to_camel(python_name)
            else:
                # No Meta mappings, use automatic conversion
                json_key = snake_to_camel(python_name)

            # Only add override if JSON key differs from Python field name
            if json_key != python_name:
                field_overrides[python_name] = override(rename=json_key)

    # print(f"DEBUG: {cls.__name__} overrides: {field_overrides}")
    return make_dict_structure_fn(cls, converter, **field_overrides)


def _make_dataclass_unstructure_fn(cls: type[T]) -> Any:
    """
    Create an unstructure function for a dataclass with automatic name transformation.

    Scenario:
        Generate an unstructure function that automatically converts Python
        dataclass field names (snake_case) to JSON keys (camelCase).

    Expected Outcome:
        A function that cattrs can use to unstructure the dataclass into JSON,
        with automatic field name transformation.
    """
    # Get field renaming map (Python field name → JSON key)
    field_overrides: dict[str, Any] = {}
    if dataclasses.is_dataclass(cls):
        for field in dataclasses.fields(cls):
            python_name = field.name
            # Convert Python field name to JSON key
            json_key = snake_to_camel(python_name)

            # Check if class has Meta with explicit mappings
            if hasattr(cls, "Meta") and hasattr(cls.Meta, "key_transform_with_dump"):  # type: ignore[attr-defined]
                mappings: dict[str, str] = cls.Meta.key_transform_with_dump  # type: ignore[attr-defined]
                # Use explicit mapping if available
                json_key = mappings.get(python_name, json_key)

            # Only add override if JSON key differs from Python field name
            if json_key != python_name:
                field_overrides[python_name] = override(rename=json_key)

    return make_dict_unstructure_fn(cls, converter, **field_overrides)


def structure_with_base64_bytes(data: str | bytes, _: type[bytes]) -> bytes:
    """
    Structure hook for base64-encoded bytes.

    Handles OpenAPI format "byte" which is base64-encoded string.

    Args:
        data: Either base64 string or raw bytes
        _: Target type (bytes)

    Returns:
        Decoded bytes
    """
    if isinstance(data, str):
        return base64.b64decode(data)
    return data


def unstructure_bytes_to_base64(data: bytes) -> str:
    """
    Unstructure hook for bytes to base64 string.

    Args:
        data: Raw bytes

    Returns:
        base64-encoded string
    """
    return base64.b64encode(data).decode("utf-8")


# Register base64 bytes handling
converter.register_structure_hook(bytes, structure_with_base64_bytes)
converter.register_unstructure_hook(bytes, unstructure_bytes_to_base64)


def structure_datetime(data: str | datetime, _: type[datetime]) -> datetime:
    """
    Structure hook for datetime fields.

    Handles OpenAPI format "date-time" which is ISO 8601 string.

    Args:
        data: Either ISO 8601 string or datetime object
        _: Target type (datetime)

    Returns:
        datetime object

    Raises:
        ValueError: If string is not valid ISO 8601 format
    """
    if isinstance(data, datetime):
        return data
    if isinstance(data, str):
        # Try ISO 8601 format with timezone
        try:
            return datetime.fromisoformat(data.replace("Z", "+00:00"))
        except ValueError:
            # Try without timezone
            return datetime.fromisoformat(data)
    raise TypeError(f"Cannot convert {type(data)} to datetime")


def unstructure_datetime(data: datetime) -> str:
    """
    Unstructure hook for datetime to ISO 8601 string.

    Args:
        data: datetime object

    Returns:
        ISO 8601 formatted string
    """
    return data.isoformat()


def structure_date(data: str | date, _: type[date]) -> date:
    """
    Structure hook for date fields.

    Handles OpenAPI format "date" which is ISO 8601 date string.

    Args:
        data: Either ISO 8601 date string or date object
        _: Target type (date)

    Returns:
        date object

    Raises:
        ValueError: If string is not valid ISO 8601 date format
    """
    if isinstance(data, date):
        return data
    if isinstance(data, str):
        return date.fromisoformat(data)
    raise TypeError(f"Cannot convert {type(data)} to date")


def unstructure_date(data: date) -> str:
    """
    Unstructure hook for date to ISO 8601 string.

    Args:
        data: date object

    Returns:
        ISO 8601 formatted date string (YYYY-MM-DD)
    """
    return data.isoformat()


# Register datetime and date handling
converter.register_structure_hook(datetime, structure_datetime)
converter.register_unstructure_hook(datetime, unstructure_datetime)
converter.register_structure_hook(date, structure_date)
converter.register_unstructure_hook(date, unstructure_date)


# =============================================================================
# Union Type Structure Hook
# =============================================================================


def _is_union_type(t: Any) -> bool:
    """
    Check if a type is a Union type.

    Scenario:
        Detect Union types including both typing.Union and Python 3.10+ X | Y syntax.

    Expected Outcome:
        Returns True for Union types, False otherwise.
    """
    origin = get_origin(t)
    # Handle both typing.Union and types.UnionType (Python 3.10+ X | Y syntax)
    return origin is Union or (hasattr(types, "UnionType") and isinstance(t, types.UnionType))


def _structure_union(data: Any, union_type: type) -> Any:
    """
    Structure a Union type by trying each variant.

    Scenario:
        OpenAPI oneOf/anyOf schemas generate Union types. When deserialising
        API responses, we need to determine which variant matches the data.

    Expected Outcome:
        Returns the structured data as the first matching Union variant.

    Strategy:
        1. If data is None and NoneType is in the union, return None
        2. If data is a dict, try each dataclass variant
        3. Try structuring with other variants (generic types, registered hooks)
        4. Fall back to dict[str, Any] if present
        5. Raise error if no variant matches

    Args:
        data: The raw data to structure
        union_type: The Union type to structure into

    Returns:
        Structured data as one of the Union variants

    Raises:
        TypeError: If data is None but NoneType not in union
        ValueError: If no Union variant matches the data
    """
    args = get_args(union_type)

    # Handle None explicitly
    if data is None:
        if type(None) in args:
            return None
        raise TypeError(f"None is not valid for {union_type}")

    # Separate variants by type category
    dataclass_variants: list[type[Any]] = []
    dict_any_fallback = False
    other_variants: list[Any] = []  # Can include generic types like List[T]

    for arg in args:
        if arg is type(None):
            continue
        elif isinstance(arg, type) and dataclasses.is_dataclass(arg):
            dataclass_variants.append(arg)
        elif get_origin(arg) is dict:
            # Check if it's dict[str, Any] - our fallback type
            dict_args = get_args(arg)
            if dict_args == (str, Any):
                dict_any_fallback = True
            else:
                # Other dict types should be tried as variants
                other_variants.append(arg)
        else:
            # Includes plain types (str, int, datetime) and generic types (List[T])
            other_variants.append(arg)

    # If data is a dict, try dataclass variants first
    if isinstance(data, dict):
        errors: list[tuple[str, str]] = []
        for variant in dataclass_variants:
            try:
                # Ensure hooks are registered for this variant
                _register_structure_hooks_recursively(variant)
                return converter.structure(data, variant)
            except Exception as e:
                errors.append((variant.__name__, str(e)))
                continue

        # If no dataclass matched and dict fallback is available, return raw dict
        if dict_any_fallback:
            return data

        # All variants failed - provide helpful error
        if errors:
            error_details = "\n".join(f"  - {name}: {err}" for name, err in errors)
            raise ValueError(f"Could not structure dict into any variant of {union_type}:\n{error_details}")

    # Try other variants using converter.structure
    # This handles:
    # - Types with registered hooks (datetime, date, bytes, etc.)
    # - Generic types (List[T], Dict[K,V], etc.)
    # - Plain types (str, int, etc.)
    for variant in other_variants:
        try:
            return converter.structure(data, variant)
        except Exception:  # nosec B112 - intentional: trying variants until one succeeds
            continue

    # Last resort: if dict fallback is available and we have dict data
    if dict_any_fallback and isinstance(data, dict):
        return data

    raise TypeError(
        f"Cannot structure {type(data).__name__} into {union_type}. "
        f"Expected one of: {[arg for arg in args if arg is not type(None)]}"
    )


def _union_structure_hook(data: Any, union_type: type) -> Any:
    """
    Structure hook for Union types.

    This hook is called directly by cattrs when structuring a Union type.
    It delegates to _structure_union to handle the actual structuring logic.

    Args:
        data: The raw data to structure
        union_type: The Union type to structure into

    Returns:
        Structured data as one of the Union variants
    """
    return _structure_union(data, union_type)


def _register_union_structure_hook() -> None:
    """
    Register a structure hook for Union types.

    Scenario:
        cattrs doesn't natively handle Union types containing dataclasses.
        This registers a hook that enables structuring for all Union types.

    Expected Outcome:
        All Union types (from OpenAPI oneOf/anyOf) can be structured correctly.
    """

    def predicate(t: type) -> bool:
        return _is_union_type(t)

    converter.register_structure_hook_func(predicate, _union_structure_hook)


# Register the Union hook at module load time
_register_union_structure_hook()



def _register_structure_hooks_recursively(cls: type[Any], visited: set[type[Any]] | None = None) -> None:
    """
    Recursively register structure hooks for a dataclass and all its nested dataclass types.

    Scenario:
        Before structuring a dataclass, we need to register hooks for it and all
        nested data classes so that field name transformation works at all levels.

    Expected Outcome:
        All dataclass types in the object graph have structure hooks registered.

    Args:
        cls: The dataclass type to register hooks for
        visited: Set of already-visited types to avoid infinite recursion
    """
    if visited is None:
        visited = set()

    # Skip if already visited (avoid infinite recursion)
    if cls in visited:
        return

    visited.add(cls)

    # Only process dataclasses
    if not dataclasses.is_dataclass(cls):
        return

    # Register structure hook for this dataclass
    try:
        # Use closure to capture cls value
        def make_hook(captured_cls: type[Any]) -> Any:
            def hook(d: dict[str, Any] | None, t: type[Any]) -> Any:
                # Handle None input - cattrs passes None when JSON has null values
                # for non-optional dataclass fields. This prevents TypeError when
                # the generated structure function tries to check field presence
                # using 'field_name' in d (which fails when d is None).
                if d is None:
                    # None received for a non-optional field is a schema violation.
                    # This typically happens when:
                    # 1. OpenAPI schema marks field as required but API returns null
                    # 2. OpenAPI schema is missing 'nullable: true' for the field
                    raise TypeError(
                        f"Cannot structure None into {captured_cls.__name__}: "
                        f"Received null value for non-optional field. "
                        f"This is likely a schema mismatch - either the API is returning null "
                        f"for a required field, or the OpenAPI schema is missing 'nullable: true'. "
                        f"To fix: make the field optional in the OpenAPI spec by adding 'nullable: true' "
                        f"or removing it from the 'required' array."
                    )
                return _make_dataclass_structure_fn(captured_cls)(d, t)

            return hook

        def predicate(t: type[Any], captured_cls: type[Any] = cls) -> bool:
            return t is captured_cls

        converter.register_structure_hook_func(
            predicate,
            make_hook(cls),
        )
    except Exception:  # nosec B110
        # Hook might already be registered - this is expected and safe to ignore
        pass

    # Recursively register hooks for nested dataclass fields
    try:
        type_hints = get_type_hints(cls)
    except Exception:
        # If type hints cannot be resolved (e.g. missing imports), fall back to field.type
        type_hints = {}

    for field in dataclasses.fields(cls):
        # Use resolved type hint if available, otherwise raw field type
        field_type = type_hints.get(field.name, field.type)

        # Handle direct dataclass types
        if isinstance(field_type, type) and dataclasses.is_dataclass(field_type):
            _register_structure_hooks_recursively(field_type, visited)
            continue

        # Handle generic types (List[T], Optional[T], etc.) and Unions
        _register_hooks_for_nested_types(field_type, visited, _register_structure_hooks_recursively)


def _register_hooks_for_nested_types(
    type_hint: Any, visited: set[type], registrar: Callable[[type, set[type]], None]
) -> None:
    """
    Recursively inspect a type hint to find and register hooks for nested dataclasses.
    Handles Unions, Lists, Optionals, and other generic types.
    """
    from typing import get_args, get_origin

    # If it's a direct dataclass, register it
    if isinstance(type_hint, type) and dataclasses.is_dataclass(type_hint):
        registrar(type_hint, visited)
        return

    # If it's a generic type or Union, inspect its arguments
    origin = get_origin(type_hint)
    if origin is not None:
        for arg in get_args(type_hint):
            _register_hooks_for_nested_types(arg, visited, registrar)


def _extract_errors(e: BaseException | Exception, path: str = "") -> list[str]:
    """
    Recursively extract human-readable error messages from cattrs validation errors.

    Args:
        e: The exception to extract errors from
        path: The current path in the object structure (e.g. "items[0].id")

    Returns:
        List of formatted error messages
    """
    messages = []

    if isinstance(e, IterableValidationError):
        # Handle list/iterable errors
        for sub_exc in e.exceptions:
            # We don't have reliable index information from cattrs for which item failed
            # (it only returns the exceptions, not the indices), so we use [] to indicate
            # an item in the list without specifying a misleading index.
            new_path = f"{path}[]" if path else "[]"
            messages.extend(_extract_errors(sub_exc, new_path))

    elif isinstance(e, ClassValidationError):
        # Handle dataclass/object errors
        for sub_exc in e.exceptions:
            # ClassValidationError usually wraps other exceptions.
            # We try to find which field caused it by inspecting the notes attached by cattrs.
            # Notes format: "Structuring class {ClassName} @ attribute {AttributeName}"
            field_name = None
            if hasattr(sub_exc, "__notes__"):
                for note in sub_exc.__notes__:
                    match = re.search(r"Structuring class .* @ attribute (.*)", note)
                    if match:
                        field_name = match.group(1)
                        break

            if field_name:
                new_path = f"{path}.{field_name}" if path else field_name
                messages.extend(_extract_errors(sub_exc, new_path))
            else:
                messages.extend(_extract_errors(sub_exc, path))

    elif isinstance(e, ExceptionGroup):
        # Handle Python 3.11+ ExceptionGroup if cattrs uses it
        for sub_exc in e.exceptions:
            messages.extend(_extract_errors(sub_exc, path))

    else:
        # Leaf exception (ValueError, TypeError, etc.)
        msg = str(e)
        if path:
            messages.append(f"{path}: {msg}")
        else:
            messages.append(msg)

    return messages


def structure_from_dict(data: dict[str, Any], cls: type[T]) -> T:
    """
    Structure dict data into dataclass instance with automatic field name transformation.

    Scenario:
        Convert JSON response (with camelCase keys) into Python dataclass instance
        (with snake_case fields). Works recursively for nested dataclasses.

    Expected Outcome:
        Properly structured dataclass instance with all field names transformed
        automatically, including nested objects and lists.

    Args:
        data: Dictionary data (from JSON)
        cls: Target dataclass type

    Returns:
        Instance of cls
    """
    # Register structure hooks for this dataclass and all nested dataclasses
    if dataclasses.is_dataclass(cls):
        _register_structure_hooks_recursively(cls)

    try:
        return converter.structure(data, cls)
    except BaseValidationError as e:
        # Extract readable error messages
        error_msgs = _extract_errors(e)
        error_text = "\n".join(f"- {msg}" for msg in error_msgs)
        raise ValueError(f"Failed to convert data to {cls.__name__}:\n{error_text}") from e
    except Exception as e:
        # Fallback for other errors
        raise ValueError(f"Failed to convert data to {cls.__name__}: {e}") from e


def _register_unstructure_hooks_recursively(cls: type[Any], visited: set[type[Any]] | None = None) -> None:
    """
    Recursively register unstructure hooks for a dataclass and all its nested dataclass types.

    Scenario:
        Before unstructuring a dataclass, we need to register hooks for it and all
        nested data classes so that field name transformation works at all levels.

    Expected Outcome:
        All dataclass types in the object graph have unstructure hooks registered.

    Args:
        cls: The dataclass type to register hooks for
        visited: Set of already-visited types to avoid infinite recursion
    """
    if visited is None:
        visited = set()

    # Skip if already visited (avoid infinite recursion)
    if cls in visited:
        return

    visited.add(cls)

    # Only process dataclasses
    if not dataclasses.is_dataclass(cls):
        return

    # Register unstructure hook for this dataclass
    try:
        # Use closure to capture cls value
        def make_hook(captured_cls: type[Any]) -> Any:
            def hook(obj: Any) -> Any:
                return _make_dataclass_unstructure_fn(captured_cls)(obj)

            return hook

        def predicate(t: type[Any], captured_cls: type[Any] = cls) -> bool:
            return t is captured_cls

        converter.register_unstructure_hook_func(
            predicate,
            make_hook(cls),
        )
    except Exception:  # nosec B110
        # Hook might already be registered - this is expected and safe to ignore
        pass

    # Recursively register hooks for nested dataclass fields

    try:
        type_hints = get_type_hints(cls)
    except Exception:
        # If type hints cannot be resolved (e.g. missing imports), fall back to field.type
        type_hints = {}

    for field in dataclasses.fields(cls):
        # Use resolved type hint if available, otherwise raw field type
        field_type = type_hints.get(field.name, field.type)

        # Handle direct dataclass types
        if isinstance(field_type, type) and dataclasses.is_dataclass(field_type):
            _register_unstructure_hooks_recursively(field_type, visited)
            continue

        # Handle generic types (List[T], Optional[T], etc.) and Unions
        _register_hooks_for_nested_types(field_type, visited, _register_unstructure_hooks_recursively)


def unstructure_to_dict(instance: Any) -> dict[str, Any]:
    """
    Unstructure dataclass instance to dict with automatic field name transformation.

    Scenario:
        Convert Python dataclass instance (with snake_case fields) into JSON-ready
        dictionary (with camelCase keys). Works recursively for nested dataclasses.

    Expected Outcome:
        Dictionary with all field names transformed automatically to match JSON
        format, including nested objects and lists.

    Args:
        instance: Dataclass instance

    Returns:
        Dictionary representation
    """
    cls = type(instance)

    # Register unstructure hooks for this dataclass and all nested dataclasses
    if dataclasses.is_dataclass(cls):
        _register_unstructure_hooks_recursively(cls)

    result: dict[str, Any] = converter.unstructure(instance)
    return result


__all__ = [
    "converter",
    "structure_from_dict",
    "unstructure_to_dict",
    "structure_with_base64_bytes",
    "unstructure_bytes_to_base64",
    "structure_datetime",
    "unstructure_datetime",
    "structure_date",
    "unstructure_date",
    "camel_to_snake",
    "snake_to_camel",
]
