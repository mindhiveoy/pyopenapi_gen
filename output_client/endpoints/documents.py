from typing import IO, Any, AsyncIterator, Dict, Optional, cast

from ..core.http_transport import HttpTransport
from ..models.clean_document_request import CleanDocumentRequest
from ..models.clean_document_response import CleanDocumentResponse
from ..models.create_document_request import CreateDocumentRequest
from ..models.data_source_event import DataSourceEvent
from ..models.document import Document
from ..models.document_list_response import DocumentListResponse
from ..models.index_document_request import IndexDocumentRequest
from ..models.log_document_event_request import LogDocumentEventRequest
from ..models.split_document_request import SplitDocumentRequest
from ..models.update_document_request import UpdateDocumentRequest


class DocumentsClient:
    """Client for Documents endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def index_document(
        self,
        tenant_id: str,
        data_source_id: str,
        document_id: str,
        body: IndexDocumentRequest,
    ) -> None:
        """
        Index a document's content into the vector database.

        Forwards the indexing request to the jobs service to index the combined document
        content. Note: This endpoint is restricted to system-level access only.

        Args:
            tenantId (str)           : Tenant identifier.
            dataSourceId (str)       : Data source identifier.
            documentId (str)         : Document identifier.
            body (IndexDocumentRequest)
                                     : Contains the document and datasource details for
                                       indexing.

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/documents/{document_id}  /index"
        params: dict[str, Any] = {}
        json_body: IndexDocumentRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None

    async def get_document(
        self,
        tenant_id: str,
        data_source_id: str,
        document_id: str,
        include: Optional[str] = None,
        download: Optional[bool] = None,
    ) -> Document:
        """
        Get a specific document

        Returns a specific document by ID. System users can access any tenant's document, while
        other users can only access their own tenant's documents. Supports including related
        data through the "include" query parameter. If the "download" query parameter is
        provided, the response returns the document content as a downloadable file (using the
        document's "html" field if available, or falling back to "markdown") instead of the JSON
        object.

        Args:
            tenantId (str)           : The ID of the tenant
            dataSourceId (str)       : The ID of the data source
            documentId (str)         : The ID of the document
            include (Optional[str])  : Comma-separated list of relations to include (e.g.,
                                       dataSource, tenant, chunks)
            download (Optional[bool]): If true, returns the document content as a downloadable
                                       file (using the "html" or "markdown" field) instead of a
                                       JSON response.

        Returns:
            Document: Returns the document details in JSON format, or the document file as a
                      downloadable stream if the "download" query parameter is provided.

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/documents/{document_id}"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
            **({"download": download} if download is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(Document, response.json())

    async def update_document(
        self,
        tenant_id: str,
        data_source_id: str,
        document_id: str,
        body: UpdateDocumentRequest,
    ) -> None:
        """
        Update a document

        Updates a document for the datasource. System users can update any tenant's documents,
        while other users can only update their own tenant's documents.

        Args:
            tenantId (str)           : The ID of the tenant
            dataSourceId (str)       : The ID of the datasource
            documentId (str)         : The ID of the document
            body (UpdateDocumentRequest)
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
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/documents/{document_id}"
        params: dict[str, Any] = {}
        json_body: UpdateDocumentRequest = body
        response = await self._transport.request(
            "PUT",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None

    async def delete_document(
        self,
        tenant_id: str,
        data_source_id: str,
        document_id: str,
    ) -> None:
        """
        Delete a document

        Deletes an existing document. Only available to tenant admins and system users.

        Args:
            tenantId (str)           : The ID of the tenant
            dataSourceId (str)       : The ID of the datasource
            documentId (str)         : The ID of the document

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/documents/{document_id}"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "DELETE",
            url,
            params=params,
        )
        # Parse response into correct return type
        return None

    async def split_document(
        self,
        tenant_id: str,
        data_source_id: str,
        document_id: str,
        body: SplitDocumentRequest,
    ) -> None:
        """
        Split a document's markdown content into chunks

        Forwards the parsing request to the jobs service and returns the split chunks along with
        statistics. Note: This endpoint is restricted to system-level access only.

        Args:
            tenantId (str)           : Tenant identifier.
            dataSourceId (str)       : Data source identifier.
            documentId (str)         : Document identifier.
            body (SplitDocumentRequest)
                                     : Markdown content with optional splitting configuration.

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/documents/{document_id}/split"
        params: dict[str, Any] = {}
        json_body: SplitDocumentRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None

    async def get_document_count(
        self,
        tenant_id: str,
        data_source_id: str,
        status: Optional[str] = None,
    ) -> None:
        """
        Get document count

        Returns the total count of documents in the datasource or with a specific status.

        Args:
            tenantId (str)           :
            dataSourceId (str)       :
            status (Optional[str])   :

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/documents/count"
        params: dict[str, Any] = {
            **({"status": status} if status is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return None

    async def index_documents(
        self,
        tenant_id: str,
        data_source_id: str,
        force_override: Optional[bool] = None,
    ) -> AsyncIterator[str]:
        """
        Stream document indexing progress

        Streams real-time updates about the document indexing process for a specific tenant and
        data source.

        Args:
            tenantId (str)           : Unique identifier of the tenant
            dataSourceId (str)       : Unique identifier of the data source
            forceOverride (Optional[bool])
                                     : Whether to force override existing indexed documents

        Returns:
            AsyncIterator[str]: Stream of document indexing progress events

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/api/tenants/{tenant_id}/datasources/{data_source_id}/documents/index/batch"
        params: dict[str, Any] = {
            **({"forceOverride": force_override} if force_override is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(AsyncIterator[str], response.json())

    async def log_document_event(
        self,
        tenant_id: str,
        data_source_id: str,
        body: LogDocumentEventRequest,
    ) -> DataSourceEvent:
        """
        Log an event for a data source

        Creates a new event log entry for the data source. System users can log events for any
        tenant's data source, while other users can only log events for their own tenant's data
        sources.

        Args:
            tenantId (str)           : The ID of the tenant
            dataSourceId (str)       : The ID of the data source
            body (LogDocumentEventRequest)
                                     : Request body.

        Returns:
            DataSourceEvent: Event logged successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/documents/log"
        params: dict[str, Any] = {}
        json_body: LogDocumentEventRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(DataSourceEvent, response.json())

    async def list_documents(
        self,
        tenant_id: str,
        data_source_id: str,
        status: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
        starts_with: Optional[str] = None,
        contains: Optional[str] = None,
        fields: Optional[str] = None,
        include: Optional[str] = None,
    ) -> DocumentListResponse:
        """
        List documents for a datasource

        Returns a paginated list of documents for the specified datasource

        Args:
            tenantId (str)           : ID of the tenant
            dataSourceId (str)       : ID of the datasource
            status (Optional[str])   : Filter documents by status
            page (Optional[int])     : Page number
            limit (Optional[int])    : Number of items per page
            sortBy (Optional[str])   : Field to sort by
            order (Optional[str])    : Sort order
            startsWith (Optional[str]): Filter documents where URL starts with this value
            contains (Optional[str]) : Filter documents where URL contains this value
            fields (Optional[str])   : Comma-separated list of fields to include in the response
            include (Optional[str])  : Comma-separated list of relations to include
                                       (vectorIndex, vectorDatabase, embedModel, tenant,
                                       documents, agents, events)

        Returns:
            DocumentListResponse: List of documents

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/documents"
        params: dict[str, Any] = {
            **({"status": status} if status is not None else {}),
            **({"page": page} if page is not None else {}),
            **({"limit": limit} if limit is not None else {}),
            **({"sortBy": sort_by} if sort_by is not None else {}),
            **({"order": order} if order is not None else {}),
            **({"startsWith": starts_with} if starts_with is not None else {}),
            **({"contains": contains} if contains is not None else {}),
            **({"fields": fields} if fields is not None else {}),
            **({"include": include} if include is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(DocumentListResponse, response.json())

    async def create_document(
        self,
        tenant_id: str,
        data_source_id: str,
        body: CreateDocumentRequest,
        files: Dict[str, IO[Any]],
    ) -> Document:
        """
        Create a new document for a datasource

        Creates a new document for the specified datasource. System users can create documents
        for any tenant.

        Args:
            tenantId (str)           : ID of the tenant
            dataSourceId (str)       : Document identifier.
            body (CreateDocumentRequest)
                                     : Request body.
            files (Dict[str, IO[Any]]): Multipart form files (if required).

        Returns:
            Document: Document created successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error occurred while processing the request
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/documents"
        params: dict[str, Any] = {}
        json_body: CreateDocumentRequest = body
        files_data: Dict[str, IO[Any]] = files
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
            files=files_data,
        )
        # Parse response into correct return type
        return cast(Document, response.json())

    async def clean_document(
        self,
        tenant_id: str,
        data_source_id: str,
        body: CleanDocumentRequest,
    ) -> CleanDocumentResponse:
        """
        Clean and validate document content

        Proxies document cleaning request to jobs service

        Args:
            tenantId (str)           :
            dataSourceId (str)       :
            body (CleanDocumentRequest)
                                     : Request body.

        Returns:
            CleanDocumentResponse: Cleaned document result

        Raises:
            HttpError:
                HTTPError: 400: Validation error occurred while processing the request
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/datasources/{data_source_id}/test/clean-document"
        params: dict[str, Any] = {}
        json_body: CleanDocumentRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(CleanDocumentResponse, response.json())
