from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VectorDatabaseResponse:
    """
    Schema for vector database response
    """

    id: str = field(default_factory=str)  # Unique identifier for the vector database
    name: str = field(default_factory=str)  # Name of the vector database
    type: str = field(default_factory=str)  # Type of the vector database
    description: Optional[Optional[str]] = None  # Description of the vector database
    config: Optional[Dict[str, Any]] = None  # Configuration for the vector database
    tenantId: Optional[Optional[str]] = (
        None  # ID of the tenant this vector database belongs to
    )
    createdAt: datetime = field(
        default_factory=str
    )  # When the vector database was created
    updatedAt: datetime = field(
        default_factory=str
    )  # When the vector database was last updated
