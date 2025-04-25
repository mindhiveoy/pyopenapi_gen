from typing import Any, AsyncIterator, Dict, Optional

from datetime import datetime
from httpx import AsyncClient
from pyopenapi_gen.streaming_helpers import SSEEvent, iter_sse

from ..models.createjobexecutionresponse import CreateJobExecutionResponse
from ..models.createsystemjobresponse import CreateSystemJobResponse
from ..models.createtenantjobresponse import CreateTenantJobResponse
from ..models.deletejobresponse import DeleteJobResponse
from ..models.deletetenantjobresponse import DeleteTenantJobResponse
from ..models.detectplatformjobresponse import DetectPlatformJobResponse
from ..models.getjobresponse import GetJobResponse
from ..models.gettenantjobresponse import GetTenantJobResponse
from ..models.jobexecutionlistresponse import JobExecutionListResponse
from ..models.jobexecutionresponse import JobExecutionResponse
from ..models.joblistresponse import JobListResponse
from ..models.jobresponse import JobResponse
from ..models.listjobexecutionsbyjobidresponse import ListJobExecutionsByJobIdResponse
from ..models.listjobexecutionsresponse import ListJobExecutionsResponse
from ..models.listsystemjobsresponse import ListSystemJobsResponse
from ..models.listtenantjobsresponse import ListTenantJobsResponse
from ..models.updatejobresponse import UpdateJobResponse
from ..models.updatetenantjobresponse import UpdateTenantJobResponse


class JobsClient:
    """Client for operations under the 'Jobs' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def listJobExecutionsByJobId(
        self,
        jobId: str,
        limit: Optional[int] = None,
        status: Optional[str] = None,
    ) -> JobExecutionListResponse:
        """Get job execution history"""
        # Build URL
        url = f"{self.base_url}/jobs/{jobId}/executions"
        # Assemble request arguments
        kwargs = {}
        params = {"limit": limit, "status": status}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def getJob(
        self,
        jobId: str,
    ) -> JobResponse:
        """Get a specific job"""
        # Build URL
        url = f"{self.base_url}/jobs/{jobId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateJob(
        self,
        jobId: str,
        body: Dict[str, Any],
    ) -> JobResponse:
        """Update a job"""
        # Build URL
        url = f"{self.base_url}/jobs/{jobId}"
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

    async def deleteJob(
        self,
        jobId: str,
    ) -> DeleteJobResponse:
        """Delete a job"""
        # Build URL
        url = f"{self.base_url}/jobs/{jobId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def detectPlatformJob(
        self,
        body: Dict[str, Any],
    ) -> AsyncIterator[bytes]:
        """Detect platform of a website
        Stream format: event-stream
        Use the appropriate streaming helper.
        """
        # Build URL
        url = f"{self.base_url}/jobs/platform-detector/detect"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        kwargs["json"] = body
        # Execute request
        resp = await self.client.post(url, **kwargs)
        async for event in iter_sse(resp):
            yield event

    async def listSystemJobs(
        self,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,
        fromDate: Optional[datetime] = None,
        toDate: Optional[datetime] = None,
    ) -> JobListResponse:
        """List system-level jobs"""
        # Build URL
        url = f"{self.base_url}/jobs"
        # Assemble request arguments
        kwargs = {}
        params = {
            "cursor": cursor,
            "limit": limit,
            "status": status,
            "type": type,
            "fromDate": fromDate,
            "toDate": toDate,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createSystemJob(
        self,
        body: Dict[str, Any],
    ) -> JobResponse:
        """Create a new system-level job"""
        # Build URL
        url = f"{self.base_url}/jobs"
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

    async def listJobExecutions(
        self,
        tenantId: str,
        jobId: str,
        fields: Optional[str] = None,
        sortBy: Optional[str] = None,
        order: Optional[str] = None,
    ) -> JobExecutionListResponse:
        """Get job executions"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/jobs/{jobId}/executions"
        # Assemble request arguments
        kwargs = {}
        params = {"fields": fields, "sortBy": sortBy, "order": order}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createJobExecution(
        self,
        tenantId: str,
        jobId: str,
        body: Dict[str, Any],
    ) -> JobExecutionResponse:
        """Record a job execution attempt"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/jobs/{jobId}/executions"
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

    async def getTenantJob(
        self,
        tenantId: str,
        jobId: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        executionsSortBy: Optional[str] = None,
        executionsOrder: Optional[str] = None,
    ) -> GetTenantJobResponse:
        """Get a specific job"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/jobs/{jobId}"
        # Assemble request arguments
        kwargs = {}
        params = {
            "include": include,
            "fields": fields,
            "executionsSortBy": executionsSortBy,
            "executionsOrder": executionsOrder,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateTenantJob(
        self,
        tenantId: str,
        jobId: str,
        body: Dict[str, Any],
    ) -> UpdateTenantJobResponse:
        """Update a job"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/jobs/{jobId}"
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

    async def deleteTenantJob(
        self,
        tenantId: str,
        jobId: str,
    ) -> DeleteTenantJobResponse:
        """Delete a job"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/jobs/{jobId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def listTenantJobs(
        self,
        tenantId: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        sortBy: Optional[str] = None,
        order: Optional[str] = None,
        executionsSortBy: Optional[str] = None,
        executionsOrder: Optional[str] = None,
    ) -> ListTenantJobsResponse:
        """Get tenant jobs"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/jobs"
        # Assemble request arguments
        kwargs = {}
        params = {
            "include": include,
            "fields": fields,
            "sortBy": sortBy,
            "order": order,
            "executionsSortBy": executionsSortBy,
            "executionsOrder": executionsOrder,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createTenantJob(
        self,
        tenantId: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        body: Dict[str, Any],
    ) -> CreateTenantJobResponse:
        """Create a new job for a tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/jobs"
        # Assemble request arguments
        kwargs = {}
        params = {"include": include, "fields": fields}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        kwargs["json"] = body
        # Execute request
        resp = await self.client.post(url, **kwargs)
        return resp.json()
