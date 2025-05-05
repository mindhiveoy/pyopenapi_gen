from dataclasses import dataclass
from typing import Optional


@dataclass
class GetAgentConfigResponse:
    """
    Schema for 404 Not Found error responses

    Attributes:
        error (str): Error message indicating the resource was not found
        resource_type (Optional[str]): Type of resource that was not found
        resource_id (Optional[str]): Identifier of the resource that was not found
    """

    error: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
