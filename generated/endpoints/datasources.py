from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.createdatasourceresponse import CreateDatasourceResponse
from ..models.datasourcelistresponse import DataSourceListResponse
from ..models.datasourceresponse import DataSourceResponse
from ..models.getdatasourceresponse import GetDatasourceResponse
from ..models.listdatasourcesresponse import ListDatasourcesResponse
from ..models.updatedatasourceresponse import UpdateDatasourceResponse


class DatasourcesClient:
    """Client for operations under the 'Datasources' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getDatasource(
        self,
        tenantId: str,
        dataSourceId: str,
        include: Optional[str] = None,
    ) -> DataSourceResponse:
        """Get a datasource"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}"
        # Assemble request arguments
        kwargs = {}
        params = {"include": include}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateDatasource(
        self,
        tenantId: str,
        dataSourceId: str,
        body: Dict[str, Any],
    ) -> DataSourceResponse:
        """Update a datasource"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources/{dataSourceId}"
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

    async def listDatasources(
        self,
        tenantId: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        documentsSortBy: Optional[str] = None,
        documentsOrder: Optional[str] = None,
        eventsSortBy: Optional[str] = None,
        eventsOrder: Optional[str] = None,
    ) -> DataSourceListResponse:
        """Get all data sources for a tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources"
        # Assemble request arguments
        kwargs = {}
        params = {
            "include": include,
            "fields": fields,
            "documentsSortBy": documentsSortBy,
            "documentsOrder": documentsOrder,
            "eventsSortBy": eventsSortBy,
            "eventsOrder": eventsOrder,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createDatasource(
        self,
        tenantId: str,
        body: Dict[str, Any],
    ) -> DataSourceResponse:
        """Create a new datasource for a tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/datasources"
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
