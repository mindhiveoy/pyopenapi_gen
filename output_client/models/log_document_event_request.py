from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LogDocumentEventRequest:
    """
    Data model for LogDocumentEventRequest

    Attributes:
        type (str): The type of event
        message (str): Human-readable description of the event
        metadata (Any): Additional metadata for the event
        document_id (Optional[str]): Optional reference to affected document
        error (Optional[str]): Optional error message if type is 'error'
        costs (Optional[Dict[str, Any]]): Cost tracking data
    """

    type: str
    message: str
    metadata: Any = None
    document_id: Optional[str] = None
    error: Optional[str] = None
    costs: Optional[Dict[str, Any]] = None
