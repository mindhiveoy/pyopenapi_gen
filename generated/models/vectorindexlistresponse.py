from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VectorIndexListResponse:
    """
    Schema for vector index list response
    """

    data: List[VectorIndexResponse] = field(
        default_factory=list
    )  # List of vector indices
    meta: Dict[str, Any] = field(default_factory=dict)  # Pagination metadata
