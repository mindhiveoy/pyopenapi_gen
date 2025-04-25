from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class GetTenantJobResponse:
    """
    Schema for 500 Internal Server Error responses
    """

    error: str = field(default_factory=str)  # General error message
    message: Optional[Optional[str]] = None  # Detailed error information when available
    requestId: Optional[Optional[str]] = (
        None  # Unique identifier for the failed request for troubleshooting
    )
