from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VectorDatabaseListResponse:
    data: List[VectorDatabaseResponse] = field(
        default_factory=list
    )  # List of vector databases
