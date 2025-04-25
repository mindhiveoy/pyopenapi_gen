from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class LogDocumentEventRequest:
    type: str = field(default_factory=str)  # The type of event
    message: str = field(default_factory=str)  # Human-readable description of the event
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata for the event
    documentId: Optional[str] = None  # Optional reference to affected document
    error: Optional[str] = None  # Optional error message if type is 'error'
    costs: Optional[Dict[str, Any]] = None  # Cost tracking data
