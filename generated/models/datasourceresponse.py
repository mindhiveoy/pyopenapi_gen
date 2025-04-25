from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DataSourceResponse:
    """
    Data source response with optional included relations
    """

    data: Optional[DataSource] = (
        None  # Data source model for managing different types of knowledge sources. Manages content repositories, their configurations, and integration settings for AI access.
    )
