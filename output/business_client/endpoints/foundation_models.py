from typing import Any, Callable, Dict, Optional, cast
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import iter_bytes
from .create_foundation_model_request import CreateFoundationModelRequest
from .list_foundation_models_response import ListFoundationModelsResponse
from .update_foundation_model_request import UpdateFoundationModelRequest

class FoundationModelsClient:
    """Client for Foundation Models endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def get_foundation_model(
        self,
        model_id: str,
    ) -> None:
        """
        Get a specific foundation model
        
        Returns a specific foundation model. Only system users can access this endpoint.
        
        Args:
            modelId (str)            : The ID of the foundation model
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/foundation-models/{model_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def update_foundation_model(
        self,
        model_id: str,
        body: UpdateFoundationModelRequest,
    ) -> None:
        """
        Update a foundation model
        
        Updates a specific foundation model. Only system users can access this endpoint.
        
        Args:
            modelId (str)            : The ID of the foundation model
            body (UpdateFoundationModelRequest)
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
        url = f"{self.base_url}/foundation-models/{model_id}"
        params: dict[str, Any] = {
        }
        json_body: UpdateFoundationModelRequest = body
        response = await self._transport.request(
            "PUT", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None
    
    async def delete_foundation_model(
        self,
        model_id: str,
    ) -> None:
        """
        Delete a foundation model
        
        Deletes a specific foundation model. Only system users can access this endpoint.
        
        Args:
            modelId (str)            : The ID of the foundation model
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/foundation-models/{model_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "DELETE", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def list_foundation_models(
        self,
    ) -> ListFoundationModelsResponse:
        """
        Get all foundation models
        
        Returns all foundation models. Only system users can access this endpoint.
        
        Returns:
            ListFoundationModelsResponse: List of foundation models
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/foundation-models"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return ListFoundationModelsResponse(**response.json())
    
    async def create_foundation_model(
        self,
        body: CreateFoundationModelRequest,
    ) -> None:
        """
        Create a new foundation model
        
        Creates a new foundation model. Only system users can access this endpoint.
        
        Args:
            body (CreateFoundationModelRequest)
                                     : Request body.
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/foundation-models"
        params: dict[str, Any] = {
        }
        json_body: CreateFoundationModelRequest = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None