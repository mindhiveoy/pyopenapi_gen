from typing import Any, AsyncIterator, cast

from ..core.http_transport import HttpTransport
from ..models.simple_model import SimpleModel


class DefaultClient:
    """Client for default endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def get_string(
        self,
    ) -> str:
        """
        Returns a string

        Returns:
            str: A plain string response

        Raises:
            HttpError:
                HTTPError: If the server returns a non-2xx HTTP response.
        """
        url = f"{self.base_url}/string"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return response.text

    async def get_bytes(
        self,
    ) -> AsyncIterator[str]:
        """
        Returns raw bytes

        Returns:
            AsyncIterator[str]: Raw byte stream

        Raises:
            HttpError:
                HTTPError: If the server returns a non-2xx HTTP response.
        """
        url = f"{self.base_url}/bytes"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(AsyncIterator[str], response.json())

    async def get_none(
        self,
    ) -> None:
        """
        Returns nothing

        Raises:
            HttpError:
                HTTPError: If the server returns a non-2xx HTTP response.
        """
        url = f"{self.base_url}/none"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return None

    async def get_model(
        self,
    ) -> SimpleModel:
        """
        Returns a SimpleModel

        Returns:
            SimpleModel: A SimpleModel object

        Raises:
            HttpError:
                HTTPError: If the server returns a non-2xx HTTP response.
        """
        url = f"{self.base_url}/model"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(SimpleModel, response.json())

    async def get_union(
        self,
    ) -> SimpleModel:
        """
        Returns a Union type

        Returns:
            SimpleModel: Either SimpleModel or a generic dictionary

        Raises:
            HttpError:
                HTTPError: If the server returns a non-2xx HTTP response.
        """
        url = f"{self.base_url}/union"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(SimpleModel, response.json())
