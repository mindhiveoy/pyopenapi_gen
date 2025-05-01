"""pyopenapi_gen – Core package

This package provides the internal representation (IR) dataclasses that act as an
intermediate layer between the parsed OpenAPI specification and the code
emitters.  The IR aims to be a *stable*, *fully‑typed* model that the rest of the
code‑generation pipeline can rely on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, unique
from typing import TYPE_CHECKING, Any, Dict, List, Optional

__all__ = [
    "HTTPMethod",
    "IRParameter",
    "IRResponse",
    "IROperation",
    "IRSchema",
    "IRSpec",
    "IRRequestBody",
]

# Semantic version of the generator core – bumped manually for now.
__version__: str = "0.1.0"


# ---------------------------------------------------------------------------
# HTTP Method Enum
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# IR Dataclasses
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class IRParameter:
    """Represents an operation parameter (path/query/header/cookie)."""

    name: str
    in_: str  # one of: "query", "path", "header", "cookie"
    required: bool
    schema: "IRSchema"
    description: Optional[str] = None


@dataclass(slots=True)
class IRResponse:
    """Represents a single response entry for an operation.

    stream_format: Optional string indicating the type of stream (e.g., 'octet-stream', 'event-stream', 'ndjson').
    """

    status_code: str  # can be "default" or specific status like "200"
    description: Optional[str]
    content: Dict[str, "IRSchema"]  # media‑type → schema mapping
    stream: bool = False  # Indicates a binary or streaming response
    stream_format: Optional[str] = None  # Indicates the stream type (e.g., 'octet-stream', 'event-stream', etc.)


@dataclass(slots=True)
class IRRequestBody:
    """Represents an operation request body with multiple media types."""

    required: bool
    content: Dict[str, "IRSchema"]  # media‑type → schema mapping
    description: Optional[str] = None


@dataclass(slots=True)
class IROperation:
    """Represents a single OpenAPI operation (method + path)."""

    operation_id: str
    method: HTTPMethod  # Enforced via enum for consistency
    path: str  # e.g. "/pets/{petId}"
    summary: Optional[str]
    description: Optional[str]
    parameters: List[IRParameter] = field(default_factory=list)
    request_body: Optional[IRRequestBody] = None
    responses: List[IRResponse] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass(slots=True)
class IRSchema:
    """Represents a schema node.

    This model intentionally captures only the common subset required for code
    generation in the early slices.  More fields will be added as new features
    (e.g., oneOf/anyOf/allOf, discriminators) are implemented.
    """

    name: Optional[str]  # Name when part of the global components/schemas
    type: Optional[str] = None  # "object", "array", "string", ...
    format: Optional[str] = None
    required: List[str] = field(default_factory=list)
    properties: Dict[str, "IRSchema"] = field(default_factory=dict)
    items: Optional["IRSchema"] = None  # for array types
    enum: Optional[List[Any]] = None
    description: Optional[str] = None
    _from_unresolved_ref: bool = False  # Marker for unresolved $ref fallback


@dataclass(slots=True)
class IRSpec:
    """Top‑level container for all IR nodes extracted from the spec.

    Attributes:
        title: The API title from the OpenAPI info block.
        version: The API version from the OpenAPI info block.
        description: The API description from the OpenAPI info block, if present.
        schemas: All parsed schemas.
        operations: All parsed operations.
        servers: List of server URLs.
    """

    title: str
    version: str
    description: Optional[str] = None
    schemas: Dict[str, IRSchema] = field(default_factory=dict)
    operations: List[IROperation] = field(default_factory=list)
    servers: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Lazy-loading and autocompletion support
# ---------------------------------------------------------------------------
if TYPE_CHECKING:
    # Imports for static analysis
    from .core.loader import load_ir_from_spec  # noqa: F401
    from .core.warning_collector import WarningCollector  # noqa: F401

# Expose loader and collector at package level
__all__.extend(["load_ir_from_spec", "WarningCollector"])


def __getattr__(name: str) -> Any:
    # Lazy-import attributes for runtime, supports IDE completion via TYPE_CHECKING
    if name == "load_ir_from_spec":
        from .core.loader import load_ir_from_spec as _func

        return _func
    if name == "WarningCollector":
        from .core.warning_collector import WarningCollector as _cls

        return _cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    # Ensure dir() and completion shows all exports
    return __all__.copy()
