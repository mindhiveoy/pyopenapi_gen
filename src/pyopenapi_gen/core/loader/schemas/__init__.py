"""Schema parsing and transformation utilities.

Functions to extract schemas from raw OpenAPI specifications and convert them
into IR format.
"""

from __future__ import annotations

from .extractor import build_schemas, extract_inline_enums

__all__ = ["extract_inline_enums", "build_schemas"]
