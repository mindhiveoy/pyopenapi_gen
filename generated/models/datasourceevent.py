from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DataSourceEvent:
    """
    Data source event model for tracking operations performed on data
    sources, such as syncs, updates, or errors.
    """

    id: Optional[str] = None  # Unique identifier for the event
    dataSourceId: Optional[str] = None  # Associated data source ID
    type: Optional[str] = None  # Type of event that occurred
    status: Optional[str] = None  # Current status of the event
    message: Optional[str] = None  # Descriptive message about the event
    metadata: Optional[Optional[Dict[str, Any]]] = (
        None  # Additional contextual information about the event
    )
    createdAt: Optional[datetime] = None  # Event timestamp
    updatedAt: Optional[datetime] = None  # Last status update timestamp
