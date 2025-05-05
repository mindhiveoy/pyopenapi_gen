from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from .vector_database_response_type_enum import VectorDatabaseResponseTypeEnum


@dataclass
class VectorDatabaseResponse:
    """
    Schema for vector database response

    Attributes:
        id (str): Unique identifier for the vector database
        name (str): Name of the vector database
        type (VectorDatabaseResponseTypeEnum): Type of the vector database
        description (Optional[str]): Description of the vector database
        config (Optional[Any]): Configuration for the vector database
        tenant_id (Optional[str]): ID of the tenant this vector database belongs to
        created_at (datetime): When the vector database was created
        updated_at (datetime): When the vector database was last updated
    """

    id: str
    name: str
    type: VectorDatabaseResponseTypeEnum
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    config: Optional[Any] = None
    tenant_id: Optional[str] = None
