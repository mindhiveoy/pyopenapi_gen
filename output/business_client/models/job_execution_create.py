from dataclasses import dataclass
from typing import Any, Optional
from .job_execution_create_status_enum import JobExecutionCreateStatusEnum


@dataclass
class JobExecutionCreate:
    """
    Schema for creating a new job execution

    Attributes:
        status (JobExecutionCreateStatusEnum): Initial status of the execution
        logs (Optional[str]): Initial execution logs
        job_id (Optional[str]): ID of the job this execution belongs to
        error (Optional[str]): Error message if the execution failed
        result (Optional[Any]): Result object for the execution
    """

    status: JobExecutionCreateStatusEnum
    logs: Optional[str] = None
    job_id: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Any] = None
