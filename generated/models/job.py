from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Job:
    id: str = field(default_factory=str)  # Unique identifier for the job
    name: str = field(default_factory=str)  # Name of the job
    description: Optional[str] = None  # Optional description of the job
    type: str = field(default_factory=str)  # Type of the job
    status: str = field(default_factory=str)  # Current status of the job
    queue: Optional[str] = None  # Queue name for the job
    priority: Optional[str] = None  # Priority level of the job
    config: Optional[Dict[str, Any]] = None  # Job-specific configuration
    scheduled: Optional[bool] = None  # Whether the job is scheduled to run periodically
    cronString: Optional[str] = None  # Cron expression for scheduled jobs
    maxAttempts: Optional[int] = None  # Maximum number of retry attempts
    timeout: Optional[int] = None  # Timeout in seconds
    result: Optional[Optional[Dict[str, Any]]] = None  # Job execution result
    error: Optional[Optional[str]] = None  # Error message if job failed
    startedAt: Optional[datetime] = None  # When the job started executing
    completedAt: Optional[Optional[datetime]] = None  # When the job completed executing
    createdAt: datetime = field(default_factory=str)  # When the job was created
    updatedAt: Optional[datetime] = None  # When the job was last updated
    parentJobId: Optional[Optional[str]] = (
        None  # ID of the parent job if this is a sub-job
    )
    agentId: Optional[Optional[str]] = None  # ID of the agent associated with this job
    dataSourceId: Optional[Optional[str]] = (
        None  # ID of the data source associated with this job
    )
    documentId: Optional[Optional[str]] = (
        None  # ID of the document associated with this job
    )
