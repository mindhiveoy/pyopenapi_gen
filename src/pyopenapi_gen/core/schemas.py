from dataclasses import MISSING, dataclass, fields
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


@dataclass
class BaseSchema:
    """Base class for all generated Pydantic models, providing basic validation and dict conversion."""

    @classmethod
    def model_validate(cls: Type[T], data: Dict[str, Any]) -> T:
        """Validate and create an instance from a dictionary, akin to Pydantic's model_validate."""
        if not isinstance(data, dict):
            raise TypeError(f"Input must be a dictionary, got {type(data).__name__}")

        kwargs: Dict[str, Any] = {}
        cls_fields = {f.name: f for f in fields(cls)}  # type: ignore[arg-type]

        for field_name, field_def in cls_fields.items():
            if field_name in data:
                kwargs[field_name] = data[field_name]
            elif field_def.default is MISSING and field_def.default_factory is MISSING:
                raise ValueError(f"Missing required field: '{field_name}' for class {cls.__name__}")

        extra_fields = set(data.keys()) - set(cls_fields.keys())
        if extra_fields:
            pass

        return cls(**kwargs)

    def model_dump(self, exclude_none: bool = False) -> Dict[str, Any]:
        """Convert the model instance to a dictionary, akin to Pydantic's model_dump."""
        result = {}
        for field_def in fields(self):
            value = getattr(self, field_def.name)
            if exclude_none and value is None:
                continue
            result[field_def.name] = value
        return result
