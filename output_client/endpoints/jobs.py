from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, cast

from ..core.http_transport import HttpTransport
from ..models.detect_platform_job_request import DetectPlatformJobRequest
from ..models.job import Job
from ..models.job_create import JobCreate
from ..models.job_execution_create import JobExecutionCreate
from ..models.job_execution_list_response import JobExecutionListResponse
from ..models.job_list_response import JobListResponse
from ..models.job_status import JobStatus
from ..models.job_type import JobType
from ..models.job_update import JobUpdate


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
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(JobExecutionListResponse, response.json())

    async def get_job(
        self,
        job_id: str,
    ) -> Dict[str, Any]:
        """
        Get a specific job

        Returns a specific job. System users can access any job, while other users can only
        access jobs from their tenant.

        Args:
            jobId (str)              : The ID of the job

        Returns:
            Dict[str, Any]: Job details

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/jobs/{job_id}"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(Dict[str, Any], response.json())

    async def update_job(
        self,
        job_id: str,
        body: JobUpdate,
    ) -> Dict[str, Any]:
        """
        Update a job

        Updates a job. System users can update any job, while other users can only update jobs
        from their tenant.

        Args:
            jobId (str)              : The ID of the job
            body (JobUpdate)         : Request body.

        Returns:
            Dict[str, Any]: Job updated successfully

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
        params: dict[str, Any] = {}
        json_body: JobUpdate = body
        response = await self._transport.request(
            "PUT",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(Dict[str, Any], response.json())

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
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "DELETE",
            url,
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
        params: dict[str, Any] = {}
        json_body: DetectPlatformJobRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(AsyncIterator[Dict[str, Any]], response.json())

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
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(JobListResponse, response.json())

    async def create_system_job(
        self,
        body: JobCreate,
    ) -> Dict[str, Any]:
        """
        Create a new system-level job

        Creates a new system-level job in the system. Only accessible to system users or
        internal services.

        Args:
            body (JobCreate)         : Request body.

        Returns:
            Dict[str, Any]: Job created successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/jobs"
        params: dict[str, Any] = {}
        json_body: JobCreate = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(Dict[str, Any], response.json())

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
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(JobExecutionListResponse, response.json())

    async def create_job_execution(
        self,
        tenant_id: str,
        job_id: str,
        body: JobExecutionCreate,
        x_mainio_internal_token: Optional[str] = None,
    ) -> Any:
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
            Any: Execution recorded successfully

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
        params: dict[str, Any] = {}
        headers: dict[str, Any] = {}
        json_body: JobExecutionCreate = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            headers=headers,
            json=json_body,
        )
        # Parse response into correct return type
        return response.json()  # Type is Any

    async def get_tenant_job(
        self,
        tenant_id: str,
        job_id: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        executions_sort_by: Optional[str] = None,
        executions_order: Optional[str] = None,
    ) -> Job:
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
            Job: The job

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
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(Job, response.json())

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
        params: dict[str, Any] = {}
        headers: dict[str, Any] = {}
        json_body: JobUpdate = body
        response = await self._transport.request(
            "PUT",
            url,
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
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "DELETE",
            url,
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
    ) -> List[Job]:
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
            List[Job]: List of jobs

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
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(List[Job], response.json())

    async def create_tenant_job(
        self,
        tenant_id: str,
        body: JobCreate,
        include: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> Job:
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
            Job: Job created successfully

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
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(Job, response.json())
