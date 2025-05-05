import collections.abc
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Dict, Optional, cast
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import handle_stream, iter_bytes
from .create_tenant_job_response import CreateTenantJobResponse
from .detect_platform_job_request import DetectPlatformJobRequest
from .get_tenant_job_response import GetTenantJobResponse
from .job_create import JobCreate
from .job_execution_create import JobExecutionCreate
from .job_execution_list_response import JobExecutionListResponse
from .job_execution_response import JobExecutionResponse
from .job_list_response import JobListResponse
from .job_response import JobResponse
from .job_status import JobStatus
from .job_type import JobType
from .job_update import JobUpdate
from .list_tenant_jobs_response import ListTenantJobsResponse

class JobsClient:
    """Client for Jobs endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def list_job_executions_by_job_id(
        self,
        job_id: str,
        limit: Optional[int] = None,
        status: Optional[JobStatus] = None,
    ) -> JobExecutionListResponse:
        """
        Get job execution history
        
        Returns the execution history of a specific job. System users can access any job's
        history, while other users can only access history of jobs from their tenant.
        
        Args:
            jobId (str)              : The ID of the job
            limit (Optional[int])    : Number of executions to return
            status (Optional[JobStatus])
                                     : Filter by execution status
        
        Returns:
            JobExecutionListResponse: List of job executions
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/jobs/{job_id}/executions"
        params: dict[str, Any] = {
            **({"limit": limit} if limit is not None else {}),
            **({"status": status} if status is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return JobExecutionListResponse(**response.json())
    
    async def get_job(
        self,
        job_id: str,
    ) -> JobResponse:
        """
        Get a specific job
        
        Returns a specific job. System users can access any job, while other users can only
        access jobs from their tenant.
        
        Args:
            jobId (str)              : The ID of the job
        
        Returns:
            JobResponse: Job details
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/jobs/{job_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return JobResponse(**response.json())
    
    async def update_job(
        self,
        job_id: str,
        body: JobUpdate,
    ) -> JobResponse:
        """
        Update a job
        
        Updates a job. System users can update any job, while other users can only update jobs
        from their tenant.
        
        Args:
            jobId (str)              : The ID of the job
            body (JobUpdate)         : Request body.
        
        Returns:
            JobResponse: Job updated successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/jobs/{job_id}"
        params: dict[str, Any] = {
        }
        json_body: JobUpdate = body
        response = await self._transport.request(
            "PUT", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return JobResponse(**response.json())
    
    async def delete_job(
        self,
        job_id: str,
    ) -> None:
        """
        Delete a job
        
        Deletes a job. System users can delete any job, while other users can only delete jobs
        from their tenant.
        
        Args:
            jobId (str)              : The ID of the job
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/jobs/{job_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "DELETE", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def detect_platform_job(
        self,
        body: DetectPlatformJobRequest,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Detect platform of a website
        
        Detects the platform/CMS used by a website with streaming progress updates. Returns a
        server-sent events stream with detection progress and results.
        
        Args:
            body (DetectPlatformJobRequest)
                                     : Request body.
        
        Returns:
            AsyncIterator[Dict[str, Any]]: Platform detection stream
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/jobs/platform-detector/detect"
        params: dict[str, Any] = {
        }
        json_body: DetectPlatformJobRequest = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return handle_stream(response, Dict[str, Any])
    
    async def list_system_jobs(
        self,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        status: Optional[JobStatus] = None,
        type: Optional[JobType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> JobListResponse:
        """
        List system-level jobs
        
        Returns a paginated list of system-level jobs. Only available to system users.
        
        Args:
            cursor (Optional[str])   : Pagination cursor
            limit (Optional[int])    : Number of items to return per page
            status (Optional[JobStatus])
                                     : Filter by job status
            type (Optional[JobType]) : Filter by job type
            fromDate (Optional[datetime])
                                     : Filter jobs after this date (ISO format)
            toDate (Optional[datetime])
                                     : Filter jobs before this date (ISO format)
        
        Returns:
            JobListResponse: List of system jobs with pagination
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/jobs"
        params: dict[str, Any] = {
            **({"cursor": cursor} if cursor is not None else {}),
            **({"limit": limit} if limit is not None else {}),
            **({"status": status} if status is not None else {}),
            **({"type": type} if type is not None else {}),
            **({"fromDate": from_date} if from_date is not None else {}),
            **({"toDate": to_date} if to_date is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return JobListResponse(**response.json())
    
    async def create_system_job(
        self,
        body: JobCreate,
    ) -> JobResponse:
        """
        Create a new system-level job
        
        Creates a new system-level job in the system. Only accessible to system users or
        internal services.
        
        Args:
            body (JobCreate)         : Request body.
        
        Returns:
            JobResponse: Job created successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/jobs"
        params: dict[str, Any] = {
        }
        json_body: JobCreate = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return JobResponse(**response.json())
    
    async def list_job_executions(
        self,
        tenant_id: str,
        job_id: str,
        fields: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
    ) -> JobExecutionListResponse:
        """
        Get job executions
        
        Returns all execution attempts for a specific job. System users can access any tenant's
        job executions, while other users can only access their own tenant's job executions.
        
        Args:
            tenantId (str)           : The ID of the tenant
            jobId (str)              : The ID of the job
            fields (Optional[str])   : Comma-separated list of fields to return. Available
                                       fields: id, jobId, attemptNumber, status, startedAt,
                                       completedAt, duration, error, logs, createdAt, updatedAt
            sortBy (Optional[str])   : Field to sort by (attemptNumber, status, startedAt,
                                       completedAt, createdAt)
            order (Optional[str])    : Sort order (asc or desc)
        
        Returns:
            JobExecutionListResponse: List of job executions
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/jobs/{job_id}/executions"
        params: dict[str, Any] = {
            **({"fields": fields} if fields is not None else {}),
            **({"sortBy": sort_by} if sort_by is not None else {}),
            **({"order": order} if order is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return JobExecutionListResponse(**response.json())
    
    async def create_job_execution(
        self,
        tenant_id: str,
        job_id: str,
        body: JobExecutionCreate,
        x_mainio_internal_token: Optional[str] = None,
    ) -> JobExecutionResponse:
        """
        Record a job execution attempt
        
        Records a new execution attempt for a job. Only accessible via internal API token.
        
        Args:
            tenantId (str)           : The ID of the tenant
            jobId (str)              : The ID of the job
            x-mainio-internal-token (Optional[str])
                                     : Internal API token for backend-to-backend communication
            body (JobExecutionCreate): Request body.
        
        Returns:
            JobExecutionResponse: Execution recorded successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/jobs/{job_id}/executions"
        params: dict[str, Any] = {
        }
        headers: dict[str, Any] = {
        }
        json_body: JobExecutionCreate = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            headers=headers,
            json=json_body,
        )
        # Parse response into correct return type
        return JobExecutionResponse(**response.json())
    
    async def get_tenant_job(
        self,
        tenant_id: str,
        job_id: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        executions_sort_by: Optional[str] = None,
        executions_order: Optional[str] = None,
    ) -> GetTenantJobResponse:
        """
        Get a specific job
        
        Returns a specific job for the tenant. System users can access any tenant's jobs, while
        other users can only access their own tenant's jobs. Supports including related data
        through the include query parameter. Supports selecting specific fields through the
        fields query parameter.
        
        Args:
            tenantId (str)           : The ID of the tenant
            jobId (str)              : The ID of the job
            include (Optional[str])  : Comma-separated list of relations to include
                                       (executions,tenant)
            fields (Optional[str])   : Comma-separated list of fields to return. Available
                                       fields: id, tenantId, name, type, description, queue,
                                       priority, config, scheduled, cronString, maxAttempts,
                                       timeout, createdAt, updatedAt
            executionsSortBy (Optional[str])
                                     : Field to sort executions by (createdAt, status)
            executionsOrder (Optional[str])
                                     : Sort order for executions (asc or desc)
        
        Returns:
            GetTenantJobResponse: The job
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/jobs/{job_id}"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
            **({"fields": fields} if fields is not None else {}),
            **({"executionsSortBy": executions_sort_by} if executions_sort_by is not None else {}),
            **({"executionsOrder": executions_order} if executions_order is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return GetTenantJobResponse(**response.json())
    
    async def update_tenant_job(
        self,
        tenant_id: str,
        job_id: str,
        body: JobUpdate,
        x_mainio_internal_token: Optional[str] = None,
    ) -> None:
        """
        Update a job
        
        Updates a job for the tenant. System users can update any tenant's jobs, while other
        users can only update their own tenant's jobs. Internal requests are also allowed with
        proper authentication.
        
        Args:
            tenantId (str)           : The ID of the tenant
            jobId (str)              : The ID of the job
            x-mainio-internal-token (Optional[str])
                                     : Internal API token for backend-to-backend communication
            body (JobUpdate)         : Request body.
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/jobs/{job_id}"
        params: dict[str, Any] = {
        }
        headers: dict[str, Any] = {
        }
        json_body: JobUpdate = body
        response = await self._transport.request(
            "PUT", url,
            params=params,
            headers=headers,
            json=json_body,
        )
        # Parse response into correct return type
        return None
    
    async def delete_tenant_job(
        self,
        tenant_id: str,
        job_id: str,
    ) -> None:
        """
        Delete a job
        
        Deletes a job for the tenant. System users can delete any tenant's jobs, while other
        users can only delete their own tenant's jobs.
        
        Args:
            tenantId (str)           : The ID of the tenant
            jobId (str)              : The ID of the job
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/jobs/{job_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "DELETE", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def list_tenant_jobs(
        self,
        tenant_id: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
        executions_sort_by: Optional[str] = None,
        executions_order: Optional[str] = None,
    ) -> ListTenantJobsResponse:
        """
        Get tenant jobs
        
        Returns all jobs for the specified tenant. System users can access any tenant's jobs,
        while other users can only access their own tenant's jobs. Supports including related
        data through the include query parameter.
        
        Args:
            tenantId (str)           : The ID of the tenant
            include (Optional[str])  : Comma-separated list of relations to include
                                       (executions,tenant)
            fields (Optional[str])   : Comma-separated list of fields to return. Available
                                       fields: id, tenantId, name, type, description, queue,
                                       priority, config, scheduled, cronString, maxAttempts,
                                       timeout, createdAt, updatedAt
            sortBy (Optional[str])   : Field to sort jobs by (createdAt, name, type, priority)
            order (Optional[str])    : Sort order (asc or desc)
            executionsSortBy (Optional[str])
                                     : Field to sort executions by (createdAt, status)
            executionsOrder (Optional[str])
                                     : Sort order for executions (asc or desc)
        
        Returns:
            ListTenantJobsResponse: List of jobs
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/jobs"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
            **({"fields": fields} if fields is not None else {}),
            **({"sortBy": sort_by} if sort_by is not None else {}),
            **({"order": order} if order is not None else {}),
            **({"executionsSortBy": executions_sort_by} if executions_sort_by is not None else {}),
            **({"executionsOrder": executions_order} if executions_order is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return ListTenantJobsResponse(**response.json())
    
    async def create_tenant_job(
        self,
        tenant_id: str,
        body: JobCreate,
        include: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> CreateTenantJobResponse:
        """
        Create a new job for a tenant
        
        Creates a new job for the specified tenant. System users can create jobs for any tenant,
        while other users can only create jobs for their own tenant.
        
        Args:
            tenantId (str)           : The ID of the tenant
            include (Optional[str])  : Comma-separated list of relations to include
                                       (executions,tenant)
            fields (Optional[str])   : Comma-separated list of fields to return. Available
                                       fields: id, tenantId, name, type, description, queue,
                                       priority, config, scheduled, cronString, maxAttempts,
                                       timeout, createdAt, updatedAt
            body (JobCreate)         : Request body.
        
        Returns:
            CreateTenantJobResponse: Job created successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/jobs"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
            **({"fields": fields} if fields is not None else {}),
        }
        json_body: JobCreate = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return CreateTenantJobResponse(**response.json())