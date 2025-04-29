from typing import Optional


class HTTPError(Exception):
    """Base HTTP error with status code and message."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code
        self.message = message


class ClientError(HTTPError):
    """4XX client error responses."""

    pass


class ServerError(HTTPError):
    """5XX server error responses."""

    pass
