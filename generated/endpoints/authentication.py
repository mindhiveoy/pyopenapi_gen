from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.changepasswordresponse import ChangePasswordResponse


class AuthenticationClient:
    """Client for operations under the 'Authentication' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def changePassword(
        self,
        body: Dict[str, Any],
    ) -> ChangePasswordResponse:
        """Change user password"""
        # Build URL
        url = f"{self.base_url}/auth/change-password"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        kwargs["json"] = body
        # Execute request
        resp = await self.client.post(url, **kwargs)
        return resp.json()
