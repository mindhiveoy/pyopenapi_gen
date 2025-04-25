from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.checktenantuseremailresponse import CheckTenantUserEmailResponse
from ..models.createtenantuserresponse import CreateTenantUserResponse
from ..models.createuserresponse import CreateUserResponse
from ..models.deletetenantuserresponse import DeleteTenantUserResponse
from ..models.deleteuserresponse import DeleteUserResponse
from ..models.gettenantuserresponse import GetTenantUserResponse
from ..models.getuserresponse import GetUserResponse
from ..models.listtenantusersresponse import ListTenantUsersResponse
from ..models.listusersresponse import ListUsersResponse
from ..models.updatetenantuserresponse import UpdateTenantUserResponse
from ..models.updateuserresponse import UpdateUserResponse
from ..models.userlistresponse import UserListResponse
from ..models.userresponse import UserResponse


class UsersClient:
    """Client for operations under the 'Users' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getTenantUser(
        self,
        tenantId: str,
        id: str,
    ) -> GetTenantUserResponse:
        """Get a specific user"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/users/{id}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateTenantUser(
        self,
        tenantId: str,
        id: str,
        body: Dict[str, Any],
    ) -> UpdateTenantUserResponse:
        """Update a specific user"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/users/{id}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        kwargs["json"] = body
        # Execute request
        resp = await self.client.put(url, **kwargs)
        return resp.json()

    async def deleteTenantUser(
        self,
        tenantId: str,
        id: str,
    ) -> DeleteTenantUserResponse:
        """Delete a specific user"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/users/{id}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def checkTenantUserEmail(
        self,
        tenantId: str,
        email: Optional[str] = None,
    ) -> CheckTenantUserEmailResponse:
        """Check if an email is available (not in use) within a tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/users/check-email"
        # Assemble request arguments
        kwargs = {}
        params = {"email": email}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def listTenantUsers(
        self,
        tenantId: str,
    ) -> ListTenantUsersResponse:
        """List users in a tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/users"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createTenantUser(
        self,
        tenantId: str,
        body: Dict[str, Any],
    ) -> CreateTenantUserResponse:
        """Create a new user"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/users"
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

    async def getUser(
        self,
        userId: str,
    ) -> UserResponse:
        """Get a specific user"""
        # Build URL
        url = f"{self.base_url}/users/{userId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateUser(
        self,
        userId: str,
        body: Dict[str, Any],
    ) -> UserResponse:
        """Update a specific user"""
        # Build URL
        url = f"{self.base_url}/users/{userId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        kwargs["json"] = body
        # Execute request
        resp = await self.client.put(url, **kwargs)
        return resp.json()

    async def deleteUser(
        self,
        userId: str,
    ) -> DeleteUserResponse:
        """Delete a specific user"""
        # Build URL
        url = f"{self.base_url}/users/{userId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def listUsers(
        self,
        page: Optional[int] = None,
        pageSize: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> UserListResponse:
        """Get all users"""
        # Build URL
        url = f"{self.base_url}/users"
        # Assemble request arguments
        kwargs = {}
        params = {"page": page, "pageSize": pageSize, "sort": sort}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createUser(
        self,
        body: Dict[str, Any],
    ) -> UserResponse:
        """Create a new user"""
        # Build URL
        url = f"{self.base_url}/users"
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
