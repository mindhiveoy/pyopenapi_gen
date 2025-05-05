from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from .job_create_priority_enum import JobCreatePriorityEnum
from .job_create_status_enum import JobCreateStatusEnum
from .job_create_type_enum import JobCreateTypeEnum


@dataclass
class JobCreate:
    """
    Schema for creating a new job

    Attributes:
        name (str): Job name/identifier
        description (Optional[str]): Job description
        type (JobCreateTypeEnum): Type of job
        status (Optional[JobCreateStatusEnum]): Current status of the job
        queue (Optional[str]): Processing queue
        priority (Optional[JobCreatePriorityEnum]): Execution priority
        config (Optional[Any]): Job-specific configuration
        scheduled (Optional[bool]): Whether the job is scheduled to run periodically
        next_run (Optional[datetime]): Next scheduled run time
        last_run (Optional[datetime]): Last execution time
        max_attempts (Optional[int]): Maximum retry attempts
        timeout (Optional[int]): Timeout in seconds
        parent_job_id (Optional[str]): ID of the parent job if this is a sub-job
        agent_id (Optional[str]): ID of the agent associated with this job
        data_source_id (Optional[str]): ID of the data source associated with this job
        document_id (Optional[str]): ID of the document associated with this job
        error (Optional[str]): Error message if the job failed
        result (Optional[Any]): Result object for the job
    """

    name: str
    type: JobCreateTypeEnum
    description: Optional[str] = None
    status: Optional[JobCreateStatusEnum] = None
    queue: Optional[str] = None
    priority: Optional[JobCreatePriorityEnum] = None
    config: Optional[Any] = None
    scheduled: Optional[bool] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    max_attempts: Optional[int] = None
    timeout: Optional[int] = None
    parent_job_id: Optional[str] = None
    agent_id: Optional[str] = None
    data_source_id: Optional[str] = None
    document_id: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Any] = None
