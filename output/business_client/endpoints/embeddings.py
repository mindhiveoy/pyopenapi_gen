from typing import Any, Callable, Dict, Optional, cast
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import iter_bytes
from .create_embedding_request import CreateEmbeddingRequest
from .list_embeddings_response import ListEmbeddingsResponse
from .update_embedding_request import UpdateEmbeddingRequest

class EmbeddingsClient:
    """Client for Embeddings endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def get_embedding(
        self,
        embed_model_id: str,
    ) -> None:
        """
        Get a specific embedding
        
        Returns a specific embedding. Only system users can access this endpoint.
        
        Args:
            embedModelId (str)       : The ID of the embedding
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/embeddings/{embed_model_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def update_embedding(
        self,
        embed_model_id: str,
        body: UpdateEmbeddingRequest,
    ) -> None:
        """
        Update an embedding
        
        Updates a specific embedding. Only system users can access this endpoint.
        
        Args:
            embedModelId (str)       : The ID of the embedding
            body (UpdateEmbeddingRequest)
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
        url = f"{self.base_url}/embeddings/{embed_model_id}"
        params: dict[str, Any] = {
        }
        json_body: UpdateEmbeddingRequest = body
        response = await self._transport.request(
            "PUT", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None
    
    async def delete_embedding(
        self,
        embed_model_id: str,
    ) -> None:
        """
        Delete an embedding
        
        Deletes a specific embedding. Only system users can access this endpoint.
        
        Args:
            embedModelId (str)       : The ID of the embedding
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/embeddings/{embed_model_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "DELETE", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def list_embeddings(
        self,
    ) -> ListEmbeddingsResponse:
        """
        Get all embeddings
        
        Returns all embeddings. Only system users can access this endpoint.
        
        Returns:
            ListEmbeddingsResponse: List of embeddings
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/embeddings"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return ListEmbeddingsResponse(**response.json())
    
    async def create_embedding(
        self,
        body: CreateEmbeddingRequest,
    ) -> None:
        """
        Create a new embedding
        
        Creates a new embedding. Only system users can access this endpoint.
        
        Args:
            body (CreateEmbeddingRequest)
                                     : Request body.
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/embeddings"
        params: dict[str, Any] = {
        }
        json_body: CreateEmbeddingRequest = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None