from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobExecution:
    """
    Job execution model for tracking individual run instances of scheduled
    or triggered jobs.
    """

    id: Optional[str] = None  # Unique identifier for the job execution
    jobId: Optional[Optional[str]] = None  # ID of the job this execution belongs to
    attemptNumber: Optional[int] = None  # Attempt sequence number
    status: Optional[str] = None  # Current status of this execution
    startedAt: Optional[Optional[datetime]] = None  # Execution start timestamp
    completedAt: Optional[datetime] = None  # Execution completion timestamp
    duration: Optional[int] = None  # Execution duration in seconds
    logs: Optional[Optional[str]] = None  # Execution logs
    error: Optional[Optional[str]] = None  # Error message if the execution failed
    result: Optional[Optional[Dict[str, Any]]] = None  # Result object for the execution
    tenantId: Optional[str] = None  # Associated tenant ID
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
