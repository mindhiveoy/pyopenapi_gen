from typing import Any, AsyncIterator, Dict, IO, Optional

from httpx import AsyncClient
from pyopenapi_gen.streaming_helpers import SSEEvent, iter_bytes, iter_sse

from ..models.cleandocumentresponse import CleanDocumentResponse
from ..models.createdocumentresponse import CreateDocumentResponse
from ..models.deletedocumentresponse import DeleteDocumentResponse
from ..models.documentlistresponse import DocumentListResponse
from ..models.documentresponse import DocumentResponse
from ..models.getdocumentcountresponse import GetDocumentCountResponse
from ..models.getdocumentresponse import GetDocumentResponse
from ..models.indexdocumentresponse import IndexDocumentResponse
from ..models.indexdocumentsresponse import IndexDocumentsResponse
from ..models.listdocumentsresponse import ListDocumentsResponse
from ..models.logdocumenteventresponse import LogDocumentEventResponse
from ..models.splitdocumentresponse import SplitDocumentResponse
from ..models.updatedocumentresponse import UpdateDocumentResponse


class DocumentsClient:
    """Client for operations under the 'Documents' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def indexDocument(
        self,
        tenantId: str,
        dataSourceId: str,
        documentId: str,
        body: Dict[str, Any],
    ) -> IndexDocumentResponse:
        """Index a document's content into the vector database."""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/documents/{documentId}  /index"
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

    async def getDocument(
        self,
        tenantId: str,
        dataSourceId: str,
        documentId: str,
        include: Optional[str] = None,
        download: Optional[bool] = None,
    ) -> AsyncIterator[bytes]:
        """Get a specific document
        Stream format: octet-stream
        Use the appropriate streaming helper.
        """
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/documents/{documentId}"
        # Assemble request arguments
        kwargs = {}
        params = {"include": include, "download": download}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        async for chunk in iter_bytes(resp):
            yield chunk

    async def updateDocument(
        self,
        tenantId: str,
        dataSourceId: str,
        documentId: str,
        body: Dict[str, Any],
    ) -> UpdateDocumentResponse:
        """Update a document"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/documents/{documentId}"
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

    async def deleteDocument(
        self,
        tenantId: str,
        dataSourceId: str,
        documentId: str,
    ) -> DeleteDocumentResponse:
        """Delete a document"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/documents/{documentId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def splitDocument(
        self,
        tenantId: str,
        dataSourceId: str,
        documentId: str,
        body: Dict[str, Any],
    ) -> SplitDocumentResponse:
        """Split a document's markdown content into chunks"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/documents/{documentId}/split"
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

    async def getDocumentCount(
        self,
        tenantId: str,
        dataSourceId: str,
        status: Optional[str] = None,
    ) -> GetDocumentCountResponse:
        """Get document count"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/documents/count"
        # Assemble request arguments
        kwargs = {}
        params = {"status": status}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def indexDocuments(
        self,
        tenantId: str,
        dataSourceId: str,
        forceOverride: Optional[bool] = None,
    ) -> AsyncIterator[bytes]:
        """Stream document indexing progress
        Stream format: event-stream
        Use the appropriate streaming helper.
        """
        # Build URL
        url = f"{self.base_url}/api/tenants/{tenantId}/datasources/{dataSourceId}/documents/index/batch"
        # Assemble request arguments
        kwargs = {}
        params = {"forceOverride": forceOverride}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        async for event in iter_sse(resp):
            yield event

    async def logDocumentEvent(
        self,
        tenantId: str,
        dataSourceId: str,
        body: Dict[str, Any],
    ) -> LogDocumentEventResponse:
        """Log an event for a data source"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/documents/log"
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

    async def listDocuments(
        self,
        tenantId: str,
        dataSourceId: str,
        status: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        sortBy: Optional[str] = None,
        order: Optional[str] = None,
        startsWith: Optional[str] = None,
        contains: Optional[str] = None,
        fields: Optional[str] = None,
        include: Optional[str] = None,
    ) -> DocumentListResponse:
        """List documents for a datasource"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/documents"
        # Assemble request arguments
        kwargs = {}
        params = {
            "status": status,
            "page": page,
            "limit": limit,
            "sortBy": sortBy,
            "order": order,
            "startsWith": startsWith,
            "contains": contains,
            "fields": fields,
            "include": include,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createDocument(
        self,
        tenantId: str,
        dataSourceId: str,
        body: Dict[str, Any],
    ) -> DocumentResponse:
        """Create a new document for a datasource"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/documents"
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

    async def cleanDocument(
        self,
        tenantId: str,
        dataSourceId: str,
        body: Dict[str, Any],
    ) -> CleanDocumentResponse:
        """Clean and validate document content"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}/test/clean-document"
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
