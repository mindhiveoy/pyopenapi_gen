from typing import Any, Callable, Dict, Optional, cast
from .change_password_request import ChangePasswordRequest
from .change_password_response import ChangePasswordResponse
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import iter_bytes

class AuthenticationClient:
    """Client for Authentication endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def change_password(
        self,
        body: ChangePasswordRequest,
    ) -> ChangePasswordResponse:
        """
        Change user password
        
        Updates a user's password after validating their current password. Requires
        authentication and can only be used to change the authenticated user's own password.
        
        Args:
            body (ChangePasswordRequest)
                                     : Request body.
        
        Returns:
            ChangePasswordResponse: Password successfully updated
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/auth/change-password"
        params: dict[str, Any] = {
        }
        json_body: ChangePasswordRequest = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return ChangePasswordResponse(**response.json())