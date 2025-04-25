from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobListResponse:
    data: List[Job] = field(default_factory=list)  # List of jobs
    meta: Dict[str, Any] = field(default_factory=dict)  #
