from __future__ import annotations

import base64
import types
from dataclasses import MISSING, dataclass, fields
from typing import Any, Type, TypeVar, Union, get_args, get_origin, get_type_hints

T = TypeVar("T", bound="BaseSchema")


def _extract_base_type(field_type: Any) -> Any:
    """Extract the base type from Optional/Union types."""
    origin = get_origin(field_type)
    # Handle both typing.Union and types.UnionType (Python 3.10+ X | Y syntax)
    if origin is Union or isinstance(field_type, types.UnionType):
        # For T | None or Union[T, None], get the non-None type
        args = get_args(field_type)
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]
    return field_type


@dataclass
class BaseSchema:
    """Base class for all generated models, providing validation, dict conversion, and field mapping."""

    @classmethod
    def _get_field_mappings(cls) -> dict[str, str]:
        """Get field mappings from Meta class if defined. Returns API field -> Python field mappings."""
        if hasattr(cls, "Meta") and hasattr(cls.Meta, "key_transform_with_load"):
            return cls.Meta.key_transform_with_load  # type: ignore[no-any-return]
        return {}

    @classmethod
    def _get_reverse_field_mappings(cls) -> dict[str, str]:
        """Get reverse field mappings. Returns Python field -> API field mappings."""
        mappings = cls._get_field_mappings()
        return {python_field: api_field for api_field, python_field in mappings.items()}

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary with automatic field name mapping."""
        if not isinstance(data, dict):
            raise TypeError(f"Input must be a dictionary, got {type(data).__name__}")

        field_mappings = cls._get_field_mappings()  # API -> Python
        kwargs: dict[str, Any] = {}
        cls_fields = {f.name: f for f in fields(cls)}

        # Process each field in the data
        for api_field, value in data.items():
            # Map API field name to Python field name
            python_field = field_mappings.get(api_field, api_field)

            if python_field in cls_fields:
                # Handle nested objects that might also be BaseSchema instances
                field_def = cls_fields[python_field]
                field_type = field_def.type

                # Get type hints to handle forward references and generics properly
                try:
                    type_hints = get_type_hints(cls)
                    if python_field in type_hints:
                        field_type = type_hints[python_field]
                except (NameError, AttributeError):
                    # Fall back to raw annotation if get_type_hints fails
                    pass

                # Extract base type (handles Type | None -> Type)
                base_type = _extract_base_type(field_type)

                # Handle base64-encoded bytes (OpenAPI format: "byte")
                if base_type is bytes and isinstance(value, str):
                    kwargs[python_field] = base64.b64decode(value)
                elif base_type is not None and hasattr(base_type, "from_dict") and isinstance(value, dict):
                    # Recursively convert nested dictionaries
                    kwargs[python_field] = base_type.from_dict(value)
                elif get_origin(field_type) is list or get_origin(base_type) is list:
                    # Handle List[SomeModel] types
                    list_type = field_type if get_origin(field_type) is list else base_type
                    args = get_args(list_type)
                    if args and hasattr(args[0], "from_dict") and isinstance(value, list):
                        kwargs[python_field] = [
                            args[0].from_dict(item) if isinstance(item, dict) else item for item in value
                        ]
                    else:
                        kwargs[python_field] = value
                else:
                    kwargs[python_field] = value

        # Check for required fields
        for field_name, field_def in cls_fields.items():
            if field_name not in kwargs and field_def.default is MISSING and field_def.default_factory is MISSING:
                raise ValueError(f"Missing required field: '{field_name}' for class {cls.__name__}")

        return cls(**kwargs)

    def to_dict(self, exclude_none: bool = False) -> dict[str, Any]:
        """Convert the model instance to a dictionary with reverse field name mapping."""
        reverse_mappings = self._get_reverse_field_mappings()  # Python -> API
        result = {}

        for field_def in fields(self):
            value = getattr(self, field_def.name)
            if exclude_none and value is None:
                continue

            # Handle base64 encoding for bytes (OpenAPI format: "byte")
            if isinstance(value, bytes):
                value = base64.b64encode(value).decode("ascii")
            # Handle nested objects
            elif hasattr(value, "to_dict"):
                value = value.to_dict(exclude_none=exclude_none)
            elif isinstance(value, list) and value and hasattr(value[0], "to_dict"):
                value = [
                    item.to_dict(exclude_none=exclude_none) if hasattr(item, "to_dict") else item for item in value
                ]

            # Map Python field name back to API field name
            api_field = reverse_mappings.get(field_def.name, field_def.name)
            result[api_field] = value

        return result

    # Legacy aliases for backward compatibility
    @classmethod
    def model_validate(cls: Type[T], data: dict[str, Any]) -> T:
        """Legacy alias for from_dict."""
        return cls.from_dict(data)

    def model_dump(self, exclude_none: bool = False) -> dict[str, Any]:
        """Legacy alias for to_dict."""
        return self.to_dict(exclude_none=exclude_none)
