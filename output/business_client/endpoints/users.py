from typing import Any, Callable, Dict, Optional, cast
from .check_tenant_user_email_response import CheckTenantUserEmailResponse
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import iter_bytes
from .create_tenant_user_request import CreateTenantUserRequest
from .update_tenant_user_request import UpdateTenantUserRequest
from .user_create import UserCreate
from .user_list_response import UserListResponse
from .user_response import UserResponse
from .user_update import UserUpdate

class UsersClient:
    """Client for Users endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def get_tenant_user(
        self,
        tenant_id: str,
        id: str,
    ) -> None:
        """
        Get a specific user
        
        Retrieves information for a specific user within a tenant. System users have full
        access, admin users can access only users in their tenant, and regular users can only
        access their own user record.
        
        Args:
            tenantId (str)           : The ID of the tenant
            id (str)                 : The ID of the user to retrieve
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/users/{id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def update_tenant_user(
        self,
        tenant_id: str,
        id: str,
        body: UpdateTenantUserRequest,
    ) -> None:
        """
        Update a specific user
        
        Updates information for a specific user within a tenant. System users can update any
        user, admin users can update users only in their tenant, and regular users can only
        update their own information.
        
        Args:
            tenantId (str)           : The ID of the tenant
            id (str)                 : The ID of the user to update
            body (UpdateTenantUserRequest)
                                     : Request body.
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/users/{id}"
        params: dict[str, Any] = {
        }
        json_body: UpdateTenantUserRequest = body
        response = await self._transport.request(
            "PUT", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None
    
    async def delete_tenant_user(
        self,
        tenant_id: str,
        id: str,
    ) -> None:
        """
        Delete a specific user
        
        Deletes a specific user from a tenant. Only system and admin roles are permitted to
        delete users. Admin users can only delete users within their own tenant.
        
        Args:
            tenantId (str)           : The ID of the tenant
            id (str)                 : The ID of the user to delete
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/users/{id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "DELETE", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def check_tenant_user_email(
        self,
        tenant_id: str,
        email: str,
    ) -> CheckTenantUserEmailResponse:
        """
        Check if an email is available (not in use) within a tenant
        
        Checks if an email address is available for use within a specific tenant. Returns true
        if the email is available, false if it's already in use.
        
        Args:
            tenantId (str)           : The ID of the tenant
            email (str)              : The email address to check
        
        Returns:
            CheckTenantUserEmailResponse: Email availability check completed
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/users/check-email"
        params: dict[str, Any] = {
            "email": email,
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return CheckTenantUserEmailResponse(**response.json())
    
    async def list_tenant_users(
        self,
        tenant_id: str,
    ) -> None:
        """
        List users in a tenant
        
        Retrieves a list of users within a specific tenant. Regular users can only see their own
        record, while admin and system roles can see all users in the tenant.
        
        Args:
            tenantId (str)           : The ID of the tenant
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/users"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def create_tenant_user(
        self,
        tenant_id: str,
        body: CreateTenantUserRequest,
    ) -> None:
        """
        Create a new user
        
        Creates a new user within a specific tenant. Only system and admin roles are allowed to
        create users. Admin users can only create users in their own tenant.
        
        Args:
            tenantId (str)           : The ID of the tenant
            body (CreateTenantUserRequest)
                                     : Request body.
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/users"
        params: dict[str, Any] = {
        }
        json_body: CreateTenantUserRequest = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None
    
    async def get_user(
        self,
        user_id: str,
    ) -> UserResponse:
        """
        Get a specific user
        
        Returns a specific user. System users can access any user, while other users can only
        access users from their tenant.
        
        Args:
            userId (str)             : The ID of the user
        
        Returns:
            UserResponse: The user details
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/users/{user_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return UserResponse(**response.json())
    
    async def update_user(
        self,
        user_id: str,
        body: UserUpdate,
    ) -> UserResponse:
        """
        Update a specific user
        
        Updates a user. System users can update any user, while other users can only update
        users from their tenant.
        
        Args:
            userId (str)             : The ID of the user
            body (UserUpdate)        : Request body.
        
        Returns:
            UserResponse: User updated successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/users/{user_id}"
        params: dict[str, Any] = {
        }
        json_body: UserUpdate = body
        response = await self._transport.request(
            "PUT", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return UserResponse(**response.json())
    
    async def delete_user(
        self,
        user_id: str,
    ) -> None:
        """
        Delete a specific user
        
        Deletes a user. System users can delete any user, while admin users can only delete
        users from their tenant.
        
        Args:
            userId (str)             : The ID of the user
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/users/{user_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "DELETE", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def list_users(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> UserListResponse:
        """
        Get all users
        
        Returns all users. System users can see all users, while other users can only see users
        from their tenant.
        
        Args:
            page (Optional[int])     : Page number for pagination
            pageSize (Optional[int]) : Number of items per page
            sort (Optional[str])     : Sort field and direction in format "field:direction".
                                       Available fields: id, name, email, role, tenantId,
                                       createdAt, updatedAt
        
        Returns:
            UserListResponse: List of users
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/users"
        params: dict[str, Any] = {
            **({"page": page} if page is not None else {}),
            **({"pageSize": page_size} if page_size is not None else {}),
            **({"sort": sort} if sort is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return UserListResponse(**response.json())
    
    async def create_user(
        self,
        body: UserCreate,
    ) -> UserResponse:
        """
        Create a new user
        
        Creates a new user. System users can create users for any tenant, while admin users can
        only create users for their own tenant.
        
        Args:
            body (UserCreate)        : Request body.
        
        Returns:
            UserResponse: User created successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/users"
        params: dict[str, Any] = {
        }
        json_body: UserCreate = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return UserResponse(**response.json())