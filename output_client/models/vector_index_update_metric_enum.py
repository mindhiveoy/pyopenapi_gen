import json
from enum import Enum, unique

__all__ = ["VectorIndexUpdateMetricEnum"]


@unique
class VectorIndexUpdateMetricEnum(str, Enum):
    """Distance metric used for similarity search"""

    COSINE = "cosine"
    DOT = "dot"
    L2 = "l2"
    L1 = "l1"

    @classmethod
    def from_json(cls, json_str: str) -> "VectorIndexUpdateMetricEnum":
        """Create an instance from a JSON string"""
        return VectorIndexUpdateMetricEnum(json.loads(json_str))
