from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class GetSystemHealthStatusResponse:
    """
    Data model for GetSystemHealthStatusResponse

    Attributes:
        uptime (Optional[float]): No description provided.
        timestamp (Optional[float]): No description provided.
        status (Optional[str]): No description provided.
        services (Optional[Dict[str, Any]]): No description provided.
    """

    uptime: Optional[float] = None
    timestamp: Optional[float] = None
    status: Optional[str] = None
    services: Optional[Dict[str, Any]] = None
