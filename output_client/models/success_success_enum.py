import json
from enum import Enum, unique

__all__ = ["SuccessSuccessEnum"]


@unique
class SuccessSuccessEnum(int, Enum):
    """Enum for Success.success"""

    @classmethod
    def from_json(cls, json_str: str) -> "SuccessSuccessEnum":
        """Create an instance from a JSON string"""
        return SuccessSuccessEnum(json.loads(json_str))
