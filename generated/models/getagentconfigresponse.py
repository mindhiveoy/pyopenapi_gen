from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class GetAgentConfigResponse:
    """
    Schema for 404 Not Found error responses
    """

    error: str = field(
        default_factory=str
    )  # Error message indicating the resource was not found
    resourceType: Optional[Optional[str]] = None  # Type of resource that was not found
    resourceId: Optional[Optional[str]] = (
        None  # Identifier of the resource that was not found
    )
