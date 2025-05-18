"""Operation parsing utilities.

Functions to extract and transform operations from raw OpenAPI specifications.
"""

from __future__ import annotations

from .parser import parse_operations
from .post_processor import post_process_operation
from .request_body import parse_request_body

__all__ = ["parse_operations", "post_process_operation", "parse_request_body"]
