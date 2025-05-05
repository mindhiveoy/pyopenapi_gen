from dataclasses import dataclass


@dataclass
class VectorIndexListResponse:
    """
    Schema for vector index list response

    Attributes:
        data (List[VectorIndexResponse]): List of vector indices
        meta (Dict[str, Any]): Pagination metadata
    """
