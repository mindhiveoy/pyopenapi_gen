from typing import Any

import httpx


class Protocol:
    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Sends an asynchronous HTTP request.
        """
        raise NotImplementedError
