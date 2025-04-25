from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobExecutionResponse:
    id: str = field(default_factory=str)  # Unique identifier for the job execution
    jobId: str = field(default_factory=str)  # ID of the job this execution belongs to
    attemptNumber: int = field(default_factory=str)  # Number of this execution attempt
    status: str = field(default_factory=str)  # Current status of the job execution
    startedAt: Optional[Optional[datetime]] = None  # When the job execution started
    completedAt: Optional[Optional[datetime]] = None  # When the job execution completed
    duration: Optional[Optional[int]] = (
        None  # Duration of the job execution in milliseconds
    )
    error: Optional[Optional[str]] = None  # Error message if job execution failed
    result: Optional[Optional[Dict[str, Any]]] = None  # Result object for the execution
    logs: Optional[Optional[str]] = None  # Execution logs
    createdAt: datetime = field(
        default_factory=str
    )  # When the job execution was created
    updatedAt: Optional[datetime] = None  # When the job execution was last updated
