from dataclasses import dataclass
from typing import Any, Optional
from .vector_database_create_type_enum import VectorDatabaseCreateTypeEnum


@dataclass
class VectorDatabaseCreate:
    """
    Schema for creating a new vector database

    Attributes:
        name (str): Name of the vector database
        type (VectorDatabaseCreateTypeEnum): Type of vector database
        description (Optional[str]): Description of the vector database
        config (Optional[Any]): Configuration for the vector database
    """

    name: str
    type: VectorDatabaseCreateTypeEnum
    description: Optional[str] = None
    config: Optional[Any] = None
