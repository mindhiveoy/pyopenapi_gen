import json
from enum import Enum, unique

__all__ = ["VectorIndexCreateMetricEnum"]


@unique
class VectorIndexCreateMetricEnum(str, Enum):
    """Distance metric used for similarity search"""

    COSINE = "cosine"
    DOT = "dot"
    L2 = "l2"
    L1 = "l1"

    @classmethod
    def from_json(cls, json_str: str) -> "VectorIndexCreateMetricEnum":
        """Create an instance from a JSON string"""
        return VectorIndexCreateMetricEnum(json.loads(json_str))
