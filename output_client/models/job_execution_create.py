from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class JobExecutionCreate:
    """
    Schema for creating a new job execution

    Attributes:
        status (str): Initial status of the execution
        logs (Optional[str]): Initial execution logs
        job_id (Optional[str]): ID of the job this execution belongs to
        error (Optional[str]): Error message if the execution failed
        result (Any): Result object for the execution
    """

    status: str
    logs: Optional[str] = None
    job_id: Optional[str] = None
    error: Optional[str] = None
    result: Any = None
