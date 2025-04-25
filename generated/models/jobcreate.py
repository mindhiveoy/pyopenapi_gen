from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobCreate:
    """
    Schema for creating a new job
    """

    name: str = field(default_factory=str)  # Job name/identifier
    description: Optional[Optional[str]] = None  # Job description
    type: str = field(default_factory=str)  # Type of job
    status: Optional[str] = None  # Current status of the job
    queue: Optional[str] = None  # Processing queue
    priority: Optional[str] = None  # Execution priority
    config: Optional[Dict[str, Any]] = None  # Job-specific configuration
    scheduled: Optional[bool] = None  # Whether the job is scheduled to run periodically
    nextRun: Optional[Optional[datetime]] = None  # Next scheduled run time
    lastRun: Optional[Optional[datetime]] = None  # Last execution time
    maxAttempts: Optional[int] = None  # Maximum retry attempts
    timeout: Optional[int] = None  # Timeout in seconds
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
    error: Optional[Optional[str]] = None  # Error message if the job failed
    result: Optional[Optional[Dict[str, Any]]] = None  # Result object for the job
