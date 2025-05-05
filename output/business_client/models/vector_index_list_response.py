from dataclasses import dataclass, field
from typing import Any, Dict, List
from .vector_index_response import VectorIndexResponse


@dataclass
class VectorIndexListResponse:
    """
    Schema for vector index list response

    Attributes:
        data (List[VectorIndexResponse]): List of vector indices
        meta (Dict[str, Any]): Pagination metadata
    """
