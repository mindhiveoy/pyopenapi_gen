from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobExecutionListResponse:
    data: List[JobExecutionResponse] = field(
        default_factory=list
    )  # List of job executions
