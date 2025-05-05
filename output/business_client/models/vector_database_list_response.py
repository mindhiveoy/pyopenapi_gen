from dataclasses import dataclass, field
from typing import List
from .vector_database_response import VectorDatabaseResponse


@dataclass
class VectorDatabaseListResponse:
    """
    Data model for VectorDatabaseListResponse

    Attributes:
        data (List[VectorDatabaseResponse]): List of vector databases
    """
