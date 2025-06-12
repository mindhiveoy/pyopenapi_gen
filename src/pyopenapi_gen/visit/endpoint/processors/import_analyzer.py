"""
Helper class for analyzing an IROperation and registering necessary imports.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional  # IO for multipart type hint

# Necessary helpers for type analysis
from pyopenapi_gen.helpers.endpoint_utils import (
    get_param_type,
    get_request_body_type,
)

if TYPE_CHECKING:
    from pyopenapi_gen import IROperation  # IRParameter for op.parameters type hint
    from pyopenapi_gen.context.render_context import RenderContext
    from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy

logger = logging.getLogger(__name__)


class EndpointImportAnalyzer:
    """Analyzes an IROperation to determine and register required imports."""

    def __init__(self, schemas: Optional[Dict[str, Any]] = None) -> None:
        self.schemas: Dict[str, Any] = schemas or {}

    def analyze_and_register_imports(
        self,
        op: IROperation,
        context: RenderContext,
        response_strategy: ResponseStrategy,
    ) -> None:
        """Analyzes the operation and registers imports with the RenderContext."""
        for param in op.parameters:  # op.parameters are IRParameter objects
            py_type = get_param_type(param, context, self.schemas)
            context.add_typing_imports_for_type(py_type)

        if op.request_body:
            content_types = op.request_body.content.keys()
            body_param_type: Optional[str] = None
            if "multipart/form-data" in content_types:
                # Type for multipart is Dict[str, IO[Any]] which requires IO and Any
                context.add_import("typing", "Dict")
                context.add_import("typing", "IO")
                context.add_import("typing", "Any")
                # The actual type string "Dict[str, IO[Any]]" will be handled by add_typing_imports_for_type if passed
                # but ensuring components are imported is key.
                body_param_type = "Dict[str, IO[Any]]"
            elif "application/json" in content_types:
                body_param_type = get_request_body_type(op.request_body, context, self.schemas)
            elif "application/x-www-form-urlencoded" in content_types:
                context.add_import("typing", "Dict")
                context.add_import("typing", "Any")
                body_param_type = "Dict[str, Any]"
            elif content_types:  # Fallback for other types like application/octet-stream
                body_param_type = "bytes"

            if body_param_type:
                context.add_typing_imports_for_type(body_param_type)

        # Use the response strategy's return type for import analysis
        return_type = response_strategy.return_type
        context.add_typing_imports_for_type(return_type)

        # Check for AsyncIterator in return type or parameter types
        async_iterator_found = "AsyncIterator" in return_type
        if not async_iterator_found:
            for param_spec in op.parameters:  # Iterate over IROperation's parameters
                param_py_type = get_param_type(param_spec, context, self.schemas)  # Re-check type for safety
                if "AsyncIterator" in param_py_type:
                    async_iterator_found = True
                    break

        if async_iterator_found:
            context.add_plain_import("collections.abc")
