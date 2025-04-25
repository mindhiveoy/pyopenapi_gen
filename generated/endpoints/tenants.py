from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.createtenantresponse import CreateTenantResponse
from ..models.deletetenantresponse import DeleteTenantResponse
from ..models.gettenantresponse import GetTenantResponse
from ..models.listtenantsresponse import ListTenantsResponse
from ..models.tenantlistresponse import TenantListResponse
from ..models.tenantresponse import TenantResponse
from ..models.updatetenantresponse import UpdateTenantResponse


class TenantsClient:
    """Client for operations under the 'Tenants' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getTenant(
        self,
        tenantId: str,
        include: Optional[str] = None,
    ) -> TenantResponse:
        """Get a specific tenant by ID"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}"
        # Assemble request arguments
        kwargs = {}
        params = {"include": include}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateTenant(
        self,
        tenantId: str,
        body: Dict[str, Any],
    ) -> TenantResponse:
        """Update a specific tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}"
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

    async def deleteTenant(
        self,
        tenantId: str,
    ) -> DeleteTenantResponse:
        """Delete a tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def listTenants(
        self,
        include: Optional[str] = None,
    ) -> TenantListResponse:
        """Get all tenants"""
        # Build URL
        url = f"{self.base_url}/tenants"
        # Assemble request arguments
        kwargs = {}
        params = {"include": include}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createTenant(
        self,
        body: Dict[str, Any],
    ) -> TenantResponse:
        """Create a new tenant"""
        # Build URL
        url = f"{self.base_url}/tenants"
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
