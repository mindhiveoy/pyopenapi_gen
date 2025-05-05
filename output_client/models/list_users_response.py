from dataclasses import dataclass
from typing import Optional


@dataclass
class ListUsersResponse:
    """
    Schema for 500 Internal Server Error responses

    Attributes:
        error (str): General error message
        message (Optional[str]): Detailed error information when available
        request_id (Optional[str]): Unique identifier for the failed request for troubleshooting
    """

    error: str
    message: Optional[str] = None
    request_id: Optional[str] = None
