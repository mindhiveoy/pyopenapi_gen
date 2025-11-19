"""
cattrs converter utilities for generated clients.

This module provides cattrs converter functions for JSON serialisation/deserialisation
in generated API clients. It handles:
- Field name mapping (camelCase ↔ snake_case)
- base64 bytes encoding/decoding
- Optional fields
- Nested object structures
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any, TypeVar

from cattrs import Converter

if TYPE_CHECKING:
    from typing import Type

T = TypeVar("T")

# Global converter instance for generated clients
converter = Converter()


def structure_with_base64_bytes(data: str | bytes, _: Type[bytes]) -> bytes:
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


def structure_from_dict(data: dict[str, Any], cls: Type[T]) -> T:
    """
    Structure dict data into dataclass instance.

    Handles field name mapping if Meta.key_transform_with_load is present.

    Args:
        data: Dictionary data (from JSON)
        cls: Target dataclass type

    Returns:
        Instance of cls
    """
    # Check if class has field mapping metadata
    if hasattr(cls, "Meta") and hasattr(cls.Meta, "key_transform_with_load"):  # type: ignore[attr-defined]
        mappings = cls.Meta.key_transform_with_load  # type: ignore[attr-defined]
        # Transform keys according to mapping
        data = {mappings.get(k, k): v for k, v in data.items()}

    return converter.structure(data, cls)


def unstructure_to_dict(instance: Any) -> dict[str, Any]:
    """
    Unstructure dataclass instance to dict.

    Handles field name mapping if Meta.key_transform_with_dump is present.

    Args:
        instance: Dataclass instance

    Returns:
        Dictionary representation
    """
    data: dict[str, Any] = converter.unstructure(instance)

    # Check if class has field mapping metadata
    if hasattr(instance, "Meta") and hasattr(instance.Meta, "key_transform_with_dump"):
        mappings = instance.Meta.key_transform_with_dump
        # Transform keys according to mapping
        data = {mappings.get(k, k): v for k, v in data.items()}

    return data


__all__ = [
    "converter",
    "structure_from_dict",
    "unstructure_to_dict",
    "structure_with_base64_bytes",
    "unstructure_bytes_to_base64",
]
