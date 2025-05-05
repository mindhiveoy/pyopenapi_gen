from typing import Any, Optional, cast

from ..core.http_transport import HttpTransport
from ..models.vector_index_list_response import VectorIndexListResponse
from ..models.vector_index_response import VectorIndexResponse
from ..models.vector_index_update import VectorIndexUpdate


class IndicesClient:
    """Client for Indices endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def get_vector_index(
        self,
        vector_database_id: str,
        index_id: str,
    ) -> VectorIndexResponse:
        """
        Get a specific vector index

        Returns a specific vector index. Only available to system users.

        Args:
            vectorDatabaseId (str)   : The ID of the vector database
            indexId (str)            : The ID of the vector index

        Returns:
            VectorIndexResponse: The vector index

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/vector-databases/{vector_database_id}/indices/{index_id}"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(VectorIndexResponse, response.json())

    async def update_vector_index(
        self,
        vector_database_id: str,
        index_id: str,
        body: VectorIndexUpdate,
    ) -> VectorIndexResponse:
        """
        Update a vector index

        Updates a vector index. Only available to system users.

        Args:
            vectorDatabaseId (str)   : The ID of the vector database
            indexId (str)            : The ID of the vector index
            body (VectorIndexUpdate) : Request body.

        Returns:
            VectorIndexResponse: Vector index updated successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/vector-databases/{vector_database_id}/indices/{index_id}"
        params: dict[str, Any] = {}
        json_body: VectorIndexUpdate = body
        response = await self._transport.request(
            "PUT",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(VectorIndexResponse, response.json())

    async def delete_vector_index(
        self,
        vector_database_id: str,
        index_id: str,
    ) -> None:
        """
        Delete a vector index

        Deletes a vector index. Only available to system users.

        Args:
            vectorDatabaseId (str)   : The ID of the vector database
            indexId (str)            : The ID of the vector index

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/vector-databases/{vector_database_id}/indices/{index_id}"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "DELETE",
            url,
            params=params,
        )
        # Parse response into correct return type
        return None

    async def list_vector_indices(
        self,
        vector_database_id: str,
        fields: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
        starts_with: Optional[str] = None,
        contains: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> VectorIndexListResponse:
        """
        List vector indices for a database

        Returns a paginated list of vector indices for a database. Only available to system
        users.

        Args:
            vectorDatabaseId (str)   : The ID of the vector database
            fields (Optional[str])   : Comma-separated list of fields to return
            sortBy (Optional[str])   : Field to sort by
            order (Optional[str])    : Sort order
            startsWith (Optional[str]): Filter items by name prefix (matches items that start
                                        with the given value)
            contains (Optional[str]) : Filter items by name substring (matches if name contains
                                       the given value)
            page (Optional[int])     : Page number for pagination
            limit (Optional[int])    : Number of items per page

        Returns:
            VectorIndexListResponse: List of indices with pagination

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/vector-databases/{vector_database_id}/indices"
        params: dict[str, Any] = {
            **({"fields": fields} if fields is not None else {}),
            **({"sortBy": sort_by} if sort_by is not None else {}),
            **({"order": order} if order is not None else {}),
            **({"startsWith": starts_with} if starts_with is not None else {}),
            **({"contains": contains} if contains is not None else {}),
            **({"page": page} if page is not None else {}),
            **({"limit": limit} if limit is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(VectorIndexListResponse, response.json())
