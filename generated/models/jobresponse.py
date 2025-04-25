from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobResponse:
    """
    Job response with optional included relations
    """

    data: Optional[Job] = None  #
