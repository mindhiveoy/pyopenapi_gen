from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from .job_priority_enum import JobPriorityEnum
from .job_status_enum import JobStatusEnum
from .job_type_enum import JobTypeEnum


@dataclass
class Job:
    """
    Data model for Job

    Attributes:
        id (str): Unique identifier for the job
        name (str): Name of the job
        description (Optional[str]): Optional description of the job
        type (JobTypeEnum): Type of the job
        status (JobStatusEnum): Current status of the job
        queue (Optional[str]): Queue name for the job
        priority (Optional[JobPriorityEnum]): Priority level of the job
        config (Optional[Any]): Job-specific configuration
        scheduled (Optional[bool]): Whether the job is scheduled to run periodically
        cron_string (Optional[str]): Cron expression for scheduled jobs
        max_attempts (Optional[int]): Maximum number of retry attempts
        timeout (Optional[int]): Timeout in seconds
        result (Optional[Any]): Job execution result
        error (Optional[str]): Error message if job failed
        started_at (Optional[datetime]): When the job started executing
        completed_at (Optional[datetime]): When the job completed executing
        created_at (str): When the job was created
        updated_at (Optional[datetime]): When the job was last updated
    """

    id: str
    name: str
    type: JobTypeEnum
    status: JobStatusEnum
    created_at: str
    description: Optional[str] = None
    queue: Optional[str] = None
    priority: Optional[JobPriorityEnum] = None
    config: Optional[Any] = None
    scheduled: Optional[bool] = None
    cron_string: Optional[str] = None
    max_attempts: Optional[int] = None
    timeout: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
