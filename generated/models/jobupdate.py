from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobUpdate:
    """
    Schema for updating an existing job
    """

    name: Optional[str] = None  # Job name/identifier
    description: Optional[str] = None  # Job description
    type: Optional[str] = None  # Type of job
    status: Optional[str] = None  # Current status of the job
    queue: Optional[str] = None  # Processing queue
    priority: Optional[Optional[int]] = None  # Execution priority
    config: Optional[Optional[Dict[str, Any]]] = None  # Job-specific configuration
    scheduled: Optional[bool] = None  # Whether the job is scheduled to run periodically
    nextRun: Optional[datetime] = None  # Next scheduled run time
    lastRun: Optional[datetime] = None  # Last execution time
    maxAttempts: Optional[int] = None  # Maximum retry attempts
    timeout: Optional[int] = None  # Timeout in seconds
    parentJobId: Optional[Optional[str]] = (
        None  # ID of the parent job if this is a sub-job
    )
    agentId: Optional[Optional[str]] = None  # ID of the agent associated with this job
    dataSourceId: Optional[Optional[str]] = None  # Associated data source ID
    documentId: Optional[Optional[str]] = (
        None  # ID of the document associated with this job
    )
    error: Optional[Optional[str]] = None  # Error message if the job failed
    result: Optional[Optional[Dict[str, Any]]] = None  # Result object for the job
    schedule: Optional[Optional[str]] = None  # Cron expression for recurring jobs
