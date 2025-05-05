from dataclasses import dataclass
from typing import Any


@dataclass
class JobExecutionResponse:
    """
    Job execution details with optional included relations

    Attributes:
        data (Any): No description provided.
    """

    data: Any
