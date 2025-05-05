from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Job:
    """
    Data model for Job

    Attributes:
        id (str): Unique identifier for the job
        name (str): Name of the job
        description (Optional[str]): Optional description of the job
        type (str): Type of the job
        status (str): Current status of the job
        queue (Optional[str]): Queue name for the job
        priority (Optional[str]): Priority level of the job
        config (Any): Job-specific configuration
        scheduled (Optional[bool]): Whether the job is scheduled to run periodically
        cron_string (Optional[str]): Cron expression for scheduled jobs
        max_attempts (Optional[int]): Maximum number of retry attempts
        timeout (Optional[int]): Timeout in seconds
        result (Any): Job execution result
        error (Optional[str]): Error message if job failed
        started_at (Optional[datetime]): When the job started executing
        completed_at (Optional[datetime]): When the job completed executing
        created_at (str): When the job was created
        updated_at (Optional[datetime]): When the job was last updated
    """

    id: str
    name: str
    type: str
    status: str
    created_at: str
    description: Optional[str] = None
    queue: Optional[str] = None
    priority: Optional[str] = None
    config: Any = None
    scheduled: Optional[bool] = None
    cron_string: Optional[str] = None
    max_attempts: Optional[int] = None
    timeout: Optional[int] = None
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
