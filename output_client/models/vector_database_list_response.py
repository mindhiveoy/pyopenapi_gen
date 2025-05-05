from dataclasses import dataclass


@dataclass
class VectorDatabaseListResponse:
    """
    Data model for VectorDatabaseListResponse

    Attributes:
        data (List[VectorDatabaseResponse]): List of vector databases
    """
