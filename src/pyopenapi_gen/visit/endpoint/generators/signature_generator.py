"""
Helper class for generating the method signature for an endpoint.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.core.writers.code_writer import CodeWriter

# Import necessary helpers from endpoint_utils if they were used directly or indirectly
from pyopenapi_gen.helpers.endpoint_utils import get_param_type, get_return_type  # Added

if TYPE_CHECKING:
    from pyopenapi_gen import IROperation
    from pyopenapi_gen.context.render_context import RenderContext

logger = logging.getLogger(__name__)


class EndpointMethodSignatureGenerator:
    """Generates the Python method signature for an endpoint operation."""

    def __init__(self, schemas: Optional[Dict[str, Any]] = None) -> None:
        self.schemas: Dict[str, Any] = schemas or {}

    def generate_signature(
        self,
        writer: CodeWriter,
        op: IROperation,
        context: RenderContext,
        ordered_params: List[Dict[str, Any]],
    ) -> None:
        """Writes the method signature to the provided CodeWriter."""
        # Logic from EndpointMethodGenerator._write_method_signature
        for p_info in ordered_params:  # Renamed p to p_info to avoid conflict if IRParameter is named p
            context.add_typing_imports_for_type(p_info["type"])

        return_type, _ = get_return_type(op, context, self.schemas)
        context.add_typing_imports_for_type(return_type)

        # Check if AsyncIterator is in return_type or any parameter type
        # Note: op.parameters contains IRParameter objects, not the dicts in ordered_params directly
        # We need to re-calculate param_type for op.parameters if we want to be fully independent here
        # For now, assuming ordered_params covers all type information needed for imports or that context handles it.
        # If direct access to op.parameters schema is needed, get_param_type might be called again here.
        # For simplicity, this check will just look at the final return_type string for now.
        # A more robust solution might involve a richer parameter object passed to this generator.
        if "AsyncIterator" in return_type:
            context.add_plain_import("collections.abc")
        # A more complete check for AsyncIterator in parameters:
        for param_spec in op.parameters:  # Iterate over IROperation's parameters
            # This get_param_type call might be redundant if ordered_params already has fully resolved types
            # and context.add_typing_imports_for_type(p_info["type"]) handled it.
            # However, to be safe and explicit about where AsyncIterator might come from:
            param_py_type = get_param_type(param_spec, context, self.schemas)
            if "AsyncIterator" in param_py_type:
                context.add_plain_import("collections.abc")
                break  # Found one, no need to check further

        args = ["self"]
        for p_orig in ordered_params:
            p = p_orig.copy()  # Work with a copy
            arg_str = f"{NameSanitizer.sanitize_method_name(p['name'])}: {p['type']}"  # Ensure param name is sanitized
            if not p.get("required", False):
                # Default value handling: if default is None, it should be ' = None'
                # If default is a string, it should be ' = "default_value"'
                # Otherwise, ' = default_value'
                default_val = p.get("default")
                if default_val is None and not p.get("required", False):  # Explicitly check for None for Optional types
                    arg_str += f" = None"
                elif default_val is not None:  # Only add if default is not None
                    if isinstance(default_val, str):
                        arg_str += f' = "{default_val}"'
                    else:
                        arg_str += f" = {default_val}"
            args.append(arg_str)

        actual_return_type = return_type
        writer.write_function_signature(
            NameSanitizer.sanitize_method_name(op.operation_id),
            args,
            return_type=actual_return_type,
            async_=True,
        )
        writer.indent()  # Keep the indent call as the original method did
