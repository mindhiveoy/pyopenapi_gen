from typing import Any, List, Optional, cast

from ..core.http_transport import HttpTransport
from ..models.vector_database_create import VectorDatabaseCreate
from ..models.vector_database_response import VectorDatabaseResponse
from ..models.vector_index import VectorIndex
from ..models.vector_index_create import VectorIndexCreate


class VectorDatabasesClient:
    """Client for Vector Databases endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def create_vector_index(
        self,
        vector_database_id: str,
        body: VectorIndexCreate,
    ) -> VectorIndex:
        """
        Create a new vector index

        Creates a new vector index in the specified vector database. Only available to system
        users.

        Args:
            vectorDatabaseId (str)   : The ID of the vector database
            body (VectorIndexCreate) : Request body.

        Returns:
            VectorIndex: Vector index created successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error occurred while processing the request
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/vector-databases/{vector_database_id}/indices"
        params: dict[str, Any] = {}
        json_body: VectorIndexCreate = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(VectorIndex, response.json())

    async def list_vector_databases(
        self,
        fields: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
    ) -> List[VectorDatabaseResponse]:
        """
        Get all vector databases

        Returns all vector databases. Only available to system users.

        Args:
            fields (Optional[str])   : Comma-separated list of fields to return. Available
                                       fields: id, name, type, description, config, createdAt,
                                       updatedAt
            sortBy (Optional[str])   : Field to sort by (createdAt, name, type)
            order (Optional[str])    : Sort order (asc or desc)

        Returns:
            List[VectorDatabaseResponse]: List of vector databases

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/vector-databases"
        params: dict[str, Any] = {
            **({"fields": fields} if fields is not None else {}),
            **({"sortBy": sort_by} if sort_by is not None else {}),
            **({"order": order} if order is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(List[VectorDatabaseResponse], response.json())

    async def create_vector_database(
        self,
        body: VectorDatabaseCreate,
    ) -> VectorDatabaseResponse:
        """
        Create a new vector database

        Creates a new vector database. Only available to system users.

        Args:
            body (VectorDatabaseCreate)
                                     : Request body.

        Returns:
            VectorDatabaseResponse: Vector database created successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/vector-databases"
        params: dict[str, Any] = {}
        json_body: VectorDatabaseCreate = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(VectorDatabaseResponse, response.json())
