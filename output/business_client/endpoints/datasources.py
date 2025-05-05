from typing import Any, Callable, Dict, Optional, cast
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import iter_bytes
from .data_source_create import DataSourceCreate
from .data_source_list_response import DataSourceListResponse
from .data_source_response import DataSourceResponse
from .data_source_update import DataSourceUpdate
from .get_data_source_events_response import GetDataSourceEventsResponse

class DatasourcesClient:
    """Client for Datasources endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def get_data_source_events(
        self,
        tenant_id: str,
        data_source_id: str,
        cursor: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> GetDataSourceEventsResponse:
        """
        Get events for a data source
        
        Returns paginated events for the specified data source. System users can access any
        tenant's events, while other users can only access their own tenant's events. Supports
        pagination and sorting by creation date.
        
        Args:
            tenantId (str)           : The ID of the tenant
            dataSourceId (str)       : The ID of the data source
            cursor (Optional[str])   : Cursor for pagination (event ID)
            limit (Optional[float])  : Number of events to return (default: 10, max: 50)
        
        Returns:
            GetDataSourceEventsResponse: List of events with pagination info
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/events"
        params: dict[str, Any] = {
            **({"cursor": cursor} if cursor is not None else {}),
            **({"limit": limit} if limit is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return GetDataSourceEventsResponse(**response.json())
    
    async def get_datasource(
        self,
        tenant_id: str,
        data_source_id: str,
        include: Optional[str] = None,
    ) -> DataSourceResponse:
        """
        Get a datasource
        
        Retrieves a specific datasource for the tenant. System users can get any tenant's
        datasources, while other users can only get their own tenant's datasources. Supports
        including related data through the include query parameter.
        
        Args:
            tenantId (str)           : The ID of the tenant
            dataSourceId (str)       : The ID of the datasource
            include (Optional[str])  : Comma-separated list of relations to include
                                       (vectorIndex, vectorDatabase, embedModel, tenant,
                                       documents, agents, events)
        
        Returns:
            DataSourceResponse: Datasource retrieved successfully
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return DataSourceResponse(**response.json())
    
    async def update_datasource(
        self,
        tenant_id: str,
        data_source_id: str,
        body: DataSourceUpdate,
    ) -> DataSourceResponse:
        """
        Update a datasource
        
        Updates a datasource for the tenant. System users can update any tenant's datasources,
        while other users can only update their own tenant's datasources.
        
        Args:
            tenantId (str)           : The ID of the tenant
            dataSourceId (str)       : The ID of the datasource
            body (DataSourceUpdate)  : Request body.
        
        Returns:
            DataSourceResponse: Datasource updated successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}"
        params: dict[str, Any] = {
        }
        json_body: DataSourceUpdate = body
        response = await self._transport.request(
            "PUT", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return DataSourceResponse(**response.json())
    
    async def list_datasources(
        self,
        tenant_id: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        documents_sort_by: Optional[str] = None,
        documents_order: Optional[str] = None,
        events_sort_by: Optional[str] = None,
        events_order: Optional[str] = None,
    ) -> DataSourceListResponse:
        """
        Get all data sources for a tenant
        
        Returns all data sources for the specified tenant. System users can access any tenant's
        data sources, while other users can only access their own tenant's data sources.
        Supports including related data through the include query parameter.
        
        Args:
            tenantId (str)           : The ID of the tenant
            include (Optional[str])  : Comma-separated list of relations to include
                                       (vectorDatabase,vectorIndex,embedModel,tenant,documents,a
                                       gents,events)
            fields (Optional[str])   : Comma-separated list of fields to return. Available
                                       fields: id, tenantId, name, type, description, config,
                                       createdAt, updatedAt
            documentsSortBy (Optional[str])
                                     : Field to sort documents by (createdAt, name)
            documentsOrder (Optional[str])
                                     : Sort order for documents (asc or desc)
            eventsSortBy (Optional[str])
                                     : Field to sort events by (createdAt, type)
            eventsOrder (Optional[str])
                                     : Sort order for events (asc or desc)
        
        Returns:
            DataSourceListResponse: List of data sources
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
            **({"fields": fields} if fields is not None else {}),
            **({"documentsSortBy": documents_sort_by} if documents_sort_by is not None else {}),
            **({"documentsOrder": documents_order} if documents_order is not None else {}),
            **({"eventsSortBy": events_sort_by} if events_sort_by is not None else {}),
            **({"eventsOrder": events_order} if events_order is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return DataSourceListResponse(**response.json())
    
    async def create_datasource(
        self,
        tenant_id: str,
        body: DataSourceCreate,
    ) -> DataSourceResponse:
        """
        Create a new datasource for a tenant
        
        Creates a new datasource for the specified tenant. System users can create datasources
        for any tenant.
        
        Args:
            tenantId (str)           : The ID of the tenant
            body (DataSourceCreate)  : Request body.
        
        Returns:
            DataSourceResponse: DataSource created successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources"
        params: dict[str, Any] = {
        }
        json_body: DataSourceCreate = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return DataSourceResponse(**response.json())