from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class JobExecutionCreate:
    """
    Schema for creating a new job execution
    """

    status: str = field(default_factory=str)  # Initial status of the execution
    logs: Optional[str] = None  # Initial execution logs
    jobId: Optional[Optional[str]] = None  # ID of the job this execution belongs to
    error: Optional[Optional[str]] = None  # Error message if the execution failed
    result: Optional[Optional[Dict[str, Any]]] = None  # Result object for the execution
