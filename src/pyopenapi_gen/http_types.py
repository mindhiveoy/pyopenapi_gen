from enum import Enum, unique


@unique
class HTTPMethod(str, Enum):
    """Canonical HTTP method names supported by OpenAPI.

    Implemented as `str` subclass to allow seamless usage anywhere a plain
    string is expected (e.g., httpx, logging), while still providing strict
    enumeration benefits.
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    TRACE = "TRACE"
