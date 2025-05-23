"""pyopenapi_gen – Core package

This package provides the internal representation (IR) dataclasses that act as an
intermediate layer between the parsed OpenAPI specification and the code
emitters.  The IR aims to be a *stable*, *fully‑typed* model that the rest of the
code‑generation pipeline can rely on.
"""

from __future__ import annotations

# Removed dataclasses, field, Enum, unique from here, they are in ir.py and http_types.py
from typing import (
    TYPE_CHECKING,
    Any,
    List,
)  # Kept Any, List, Optional, TYPE_CHECKING for __getattr__ and __dir__

# Import HTTPMethod from its canonical location
from .http_types import HTTPMethod

# Import IR classes from their canonical location
from .ir import (
    IROperation,
    IRParameter,
    IRRequestBody,
    IRResponse,
    IRSchema,
    IRSpec,
)

__all__ = [
    "HTTPMethod",
    "IRParameter",
    "IRResponse",
    "IROperation",
    "IRSchema",
    "IRSpec",
    "IRRequestBody",
    # Keep existing __all__ entries for lazy loaded items
    "load_ir_from_spec",
    "WarningCollector",
]

# Semantic version of the generator core – bumped manually for now.
__version__: str = "0.6.0"


# ---------------------------------------------------------------------------
# HTTP Method Enum - REMOVED FROM HERE
# ---------------------------------------------------------------------------

# @unique
# class HTTPMethod(str, Enum):
#     ...


# ---------------------------------------------------------------------------
# IR Dataclasses - REMOVED FROM HERE
# ---------------------------------------------------------------------------

# @dataclass(slots=True)
# class IRParameter:
#     ...

# @dataclass(slots=True)
# class IRResponse:
#     ...

# @dataclass(slots=True)
# class IRRequestBody:
#     ...

# @dataclass(slots=True)
# class IROperation:
#     ...

# @dataclass(slots=True)
# class IRSchema:
#     ...

# @dataclass(slots=True)
# class IRSpec:
#     ...


# ---------------------------------------------------------------------------
# Lazy-loading and autocompletion support (This part remains)
# ---------------------------------------------------------------------------
if TYPE_CHECKING:
    # Imports for static analysis
    from .core.loader.loader import load_ir_from_spec  # noqa: F401
    from .core.warning_collector import WarningCollector  # noqa: F401

# Expose loader and collector at package level
# __all__ is already updated above


def __getattr__(name: str) -> Any:
    # Lazy-import attributes for runtime, supports IDE completion via TYPE_CHECKING
    if name == "load_ir_from_spec":
        from .core.loader.loader import load_ir_from_spec as _func

        return _func
    if name == "WarningCollector":
        from .core.warning_collector import WarningCollector as _cls

        return _cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    # Ensure dir() and completion shows all exports
    return __all__.copy()
