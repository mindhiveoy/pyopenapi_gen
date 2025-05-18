"""Parameter parsing utilities.

Functions to extract and transform parameters from raw OpenAPI specifications.
"""

from __future__ import annotations

from .parser import parse_parameter, resolve_parameter_node_if_ref

__all__ = ["parse_parameter", "resolve_parameter_node_if_ref"]
