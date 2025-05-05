from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class JobUpdate:
    """
    Schema for updating an existing job

    Attributes:
        name (Optional[str]): Job name/identifier
        description (Optional[str]): Job description
        type (Optional[str]): Type of job
        status (Optional[str]): Current status of the job
        queue (Optional[str]): Processing queue
        priority (Optional[int]): Execution priority
        config (Any): Job-specific configuration
        scheduled (Optional[bool]): Whether the job is scheduled to run periodically
        next_run (Optional[datetime]): Next scheduled run time
        last_run (Optional[datetime]): Last execution time
        max_attempts (Optional[int]): Maximum retry attempts
        timeout (Optional[int]): Timeout in seconds
        parent_job_id (Optional[str]): ID of the parent job if this is a sub-job
        agent_id (Optional[str]): ID of the agent associated with this job
        data_source_id (Optional[str]): Associated data source ID
        document_id (Optional[str]): ID of the document associated with this job
        error (Optional[str]): Error message if the job failed
        result (Any): Result object for the job
        schedule (Optional[str]): Cron expression for recurring jobs
    """

    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    queue: Optional[str] = None
    priority: Optional[int] = None
    config: Any = None
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
    result: Any = None
    schedule: Optional[str] = None
