from typing import Any, Dict, Optional, cast

from ..core.http_transport import HttpTransport
from ..models.tenant_create import TenantCreate
from ..models.tenant_list_response import TenantListResponse
from ..models.tenant_update import TenantUpdate


class TenantsClient:
    """Client for Tenants endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def get_tenant(
        self,
        tenant_id: str,
        include: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a specific tenant by ID

        Returns a specific tenant. System users can access any tenant, while other users can
        only access their own tenant. Supports including related data through the include query
        parameter.

        Args:
            tenantId (str)           : ID of the tenant to fetch
            include (Optional[str])  : Comma-separated list of relations to include (users,
                                       agents, datasources)

        Returns:
            Dict[str, Any]: Tenant details

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(Dict[str, Any], response.json())

    async def update_tenant(
        self,
        tenant_id: str,
        body: TenantUpdate,
    ) -> Dict[str, Any]:
        """
        Update a specific tenant

        Updates a specific tenant. System users can update any tenant, while admin users can
        update only their own tenant with limitations, and regular users cannot update tenants.

        Args:
            tenantId (str)           : ID of the tenant to update
            body (TenantUpdate)      : Request body.

        Returns:
            Dict[str, Any]: Tenant updated successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}"
        params: dict[str, Any] = {}
        json_body: TenantUpdate = body
        response = await self._transport.request(
            "PUT",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(Dict[str, Any], response.json())

    async def delete_tenant(
        self,
        tenant_id: str,
    ) -> None:
        """
        Delete a tenant

        Deletes a specific tenant by ID. Only users with system role can delete tenants.

        Args:
            tenantId (str)           : ID of the tenant to delete

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "DELETE",
            url,
            params=params,
        )
        # Parse response into correct return type
        return None

    async def list_tenants(
        self,
        include: Optional[str] = None,
    ) -> TenantListResponse:
        """
        Get all tenants

        Returns all tenants for system users, or only the user's tenant for other roles.
        Supports including related data through the include query parameter.

        Args:
            include (Optional[str])  : Comma-separated list of relations to include
                                       (users,agents,dataSources)

        Returns:
            TenantListResponse: List of tenants

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(TenantListResponse, response.json())

    async def create_tenant(
        self,
        body: TenantCreate,
    ) -> Dict[str, Any]:
        """
        Create a new tenant

        Creates a new tenant. Only available to users with system role.

        Args:
            body (TenantCreate)      : Request body.

        Returns:
            Dict[str, Any]: Tenant created successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants"
        params: dict[str, Any] = {}
        json_body: TenantCreate = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(Dict[str, Any], response.json())
