"""
Helper class for generating response handling logic for an endpoint method.
"""

from __future__ import annotations

import logging
import re  # For parsing Union types, etc.
from typing import TYPE_CHECKING, Any, Dict, Optional

from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.helpers.endpoint_utils import (
    _get_primary_response,
    get_return_type,
    get_type_for_specific_response,  # Added new helper
)

if TYPE_CHECKING:
    from pyopenapi_gen import IROperation, IRResponse
    from pyopenapi_gen.context.render_context import RenderContext

logger = logging.getLogger(__name__)


class EndpointResponseHandlerGenerator:
    """Generates the response handling logic for an endpoint method."""

    def __init__(self, schemas: Optional[Dict[str, Any]] = None) -> None:
        self.schemas: Dict[str, Any] = schemas or {}

    def _get_extraction_code(
        self,
        return_type: str,
        context: RenderContext,
        op: IROperation,
        needs_unwrap: bool,
        response_ir: Optional[IRResponse] = None,
    ) -> str:
        """Determines the code snippet to extract/transform the response body."""
        # Logic from EndpointMethodGenerator._get_extraction_code
        # Use response_ir to check for streaming if available, fallback to op for general streaming checks
        actual_response_for_streaming_check = response_ir if response_ir else op

        if return_type == "AsyncIterator[bytes]":
            context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_bytes")
            return "iter_bytes(response)"

        if return_type.startswith("AsyncIterator["):
            is_sse = False
            # Check content type of the specific response if provided, else from primary op response
            # This part needs careful handling: response_ir might not be the one defining the AsyncIterator type directly.
            # The get_return_type is usually based on the primary success response for the operation.
            # For now, assume if return_type is AsyncIterator, it's for an SSE stream if 'text/event-stream'
            primary_resp_obj = response_ir  # Check the specific response first
            if not primary_resp_obj:  # Fallback to operation's primary response
                primary_resp_obj = next((r for r in op.responses if r.status_code.startswith("2")), None)
                if not primary_resp_obj and op.responses:
                    primary_resp_obj = op.responses[0]  # Fallback further

            if primary_resp_obj and primary_resp_obj.content:
                if "text/event-stream" in primary_resp_obj.content:
                    is_sse = True
            if is_sse:
                return "sse_json_stream_marker"  # Marker to be handled by calling code

        if return_type == "str":
            return "response.text"
        elif return_type == "bytes":
            return "response.content"
        elif return_type == "Any":
            context.add_import("typing", "Any")
            return "response.json()  # Type is Any"
        elif return_type == "None":
            return "None"  # This will be handled by generate_response_handling directly
        else:  # Includes schema-defined models, List[], Dict[], Optional[]
            context.add_import("typing", "cast")
            context.add_typing_imports_for_type(return_type)  # Ensure model itself is imported

            if needs_unwrap:
                # Special handling for List unwrapping (List is imported already)
                if return_type.startswith("List["):
                    # Handle unwrapping of List directly
                    return (
                        "raw_data = response.json().get('data')\nif raw_data is None:\n    raise ValueError(\"Expected 'data' key in response but found None\")\nreturn cast("
                        + return_type
                        + ", raw_data)"
                    )
                # Standard unwrapping for single object
                return (
                    "raw_data = response.json().get('data')\nif raw_data is None:\n    raise ValueError(\"Expected 'data' key in response but found None\")\nreturn cast("
                    + return_type
                    + ", raw_data)"
                )
            else:
                return f"cast({return_type}, response.json())"

    def generate_response_handling(
        self,
        writer: CodeWriter,
        op: IROperation,
        context: RenderContext,
    ) -> None:
        """Writes the response parsing and return logic to the CodeWriter, including status code dispatch."""
        writer.write_line("# Check response status code and handle accordingly")

        # Sort responses: specific 2xx, then default (if configured for success), then errors
        # This simplified sorting might need adjustment based on how 'default' is treated
        # For now, we'll explicitly find the primary success path first.

        primary_success_ir = _get_primary_response(op)

        is_primary_actually_success = False
        if primary_success_ir:  # Explicit check for None to help linter
            is_2xx = primary_success_ir.status_code.startswith("2")
            is_default_with_content = (
                primary_success_ir.status_code == "default"
                and bool(primary_success_ir.content)  # Ensure this part is boolean
            )
            is_primary_actually_success = is_2xx or is_default_with_content

        # Determine if the primary success response will be handled by the first dedicated block
        # This first block only handles numeric (2xx) success codes.
        is_primary_handled_by_first_block = (
            primary_success_ir
            and is_primary_actually_success
            and primary_success_ir.status_code.isdigit()  # Key change: first block only for numeric codes
            and primary_success_ir.status_code.startswith("2")  # Ensure it's 2xx
        )

        other_responses = sorted(
            [
                r for r in op.responses if not (r == primary_success_ir and is_primary_handled_by_first_block)
            ],  # If primary is handled by first block, exclude it from others
            key=lambda r: (
                not r.status_code.startswith("2"),  # False for 2xx (comes first)
                r.status_code != "default",  # False for default (comes after 2xx, before errors)
                r.status_code,  # Then sort by status_code string
            ),
        )

        is_first_condition = True

        # 1. Handle primary success response IF IT IS TRULY A SUCCESS RESPONSE AND NUMERIC (2xx)
        if is_primary_handled_by_first_block:
            assert primary_success_ir is not None  # Add assertion to help linter
            # No try-except needed here as isdigit() and startswith("2") already checked
            status_code_val = int(primary_success_ir.status_code)
            condition = f"response.status_code == {status_code_val}"

            writer.write_line(f"if {condition}:")
            is_first_condition = False
            writer.indent()
            return_type, needs_unwrap = get_return_type(op, context, self.schemas)

            if return_type == "None" or not primary_success_ir.content:
                writer.write_line("return None")
            else:
                self._write_parsed_return(writer, op, context, return_type, needs_unwrap, primary_success_ir)
            writer.dedent()

        # 2. Handle other specific responses (other 2xx, then default, then errors)
        for resp_ir in other_responses:
            # Determine if this response IR defines a success type different from the primary
            # This is complex. For now, if it's 2xx, we'll try to parse it.
            # If it's an error, we raise.

            current_return_type_str: str = "None"  # Default for e.g. 204 or error cases
            current_needs_unwrap: bool = False

            if resp_ir.status_code.startswith("2"):
                if not resp_ir.content:  # e.g. 204
                    current_return_type_str = "None"
                else:
                    # We need a way to get the type for *this specific* resp_ir if its schema differs
                    # from the primary operation return type.
                    # Call the new helper for this specific response
                    specific_type, specific_unwrap = get_type_for_specific_response(resp_ir, context, self.schemas)
                    current_return_type_str = specific_type
                    current_needs_unwrap = specific_unwrap

            condition_prefix = "elif" if not is_first_condition else "if"
            is_first_condition = False

            if resp_ir.status_code == "default":
                # Determine type for default response if it has content
                default_return_type_str = "None"
                default_needs_unwrap = False
                if resp_ir.content:
                    # If 'default' is primary success, get_return_type(op,...) might give its type.
                    # We use the operation's global/primary return type if default has content.
                    op_global_return_type, op_global_needs_unwrap = get_return_type(op, context, self.schemas)
                    # Only use this if the global type is not 'None', otherwise keep default_return_type_str as 'None'.
                    if op_global_return_type != "None":
                        default_return_type_str = op_global_return_type
                        default_needs_unwrap = op_global_needs_unwrap

                writer.write_line(f"{condition_prefix} response.status_code >= 0: # Default response catch-all")
                writer.indent()
                if resp_ir.content and default_return_type_str != "None":
                    self._write_parsed_return(
                        writer, op, context, default_return_type_str, default_needs_unwrap, resp_ir
                    )
                else:  # Default implies error or no content
                    context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")
                    writer.write_line(
                        f'raise HTTPError(response=response, message="Default error: {resp_ir.description or "Unknown default error"}", status_code=response.status_code)'
                    )
                writer.dedent()
                continue  # Handled default, move to next

            try:
                status_code_val = int(resp_ir.status_code)
                writer.write_line(f"{condition_prefix} response.status_code == {status_code_val}:")
                writer.indent()

                if resp_ir.status_code.startswith("2"):  # Other 2xx success
                    if current_return_type_str == "None" or not resp_ir.content:
                        writer.write_line("return None")
                    else:
                        self._write_parsed_return(
                            writer, op, context, current_return_type_str, current_needs_unwrap, resp_ir
                        )
                else:  # Error codes (3xx, 4xx, 5xx)
                    error_class_name = f"Error{status_code_val}"
                    context.add_import(
                        f"{context.core_package_name}", error_class_name
                    )  # Import from top-level core package
                    writer.write_line(f"raise {error_class_name}(response=response)")
                writer.dedent()
            except ValueError:
                logger.warning(f"Skipping non-integer status code in other_responses: {resp_ir.status_code}")

        # 3. Final else for unhandled status codes
        if not is_first_condition:  # if any if/elif was written
            writer.write_line("else:")
        else:  # No conditions were written at all (e.g. op.responses was empty)
            writer.write_line("if True: # Should ideally not happen if responses are defined")  # Fallback
        writer.indent()
        context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")
        writer.write_line(
            f'raise HTTPError(response=response, message="Unhandled status code", status_code=response.status_code)'
        )
        writer.dedent()

        writer.write_line("")  # Add a blank line for readability

    def _write_parsed_return(
        self,
        writer: CodeWriter,
        op: IROperation,
        context: RenderContext,
        return_type: str,
        needs_unwrap: bool,
        response_ir: Optional[IRResponse] = None,
    ) -> None:
        """Helper to write the actual return statement with parsing/extraction logic."""

        # This section largely reuses the logic from the original generate_response_handling
        # adapted to be callable for a specific return_type and response context.

        is_op_with_inferred_type = return_type != "None" and not any(
            r.content for r in op.responses if r.status_code.startswith("2")
        )  # This might need adjustment if called for a specific non-primary response.

        if return_type.startswith("Union["):
            context.add_import("typing", "Union")
            context.add_import("typing", "cast")
            # Corrected regex to parse "Union[TypeA, TypeB]"
            match = re.match(r"Union\[([A-Za-z0-9_]+),\s*([A-Za-z0-9_]+)\]", return_type)
            if match:
                type1_str = match.group(1).strip()
                type2_str = match.group(2).strip()
                context.add_typing_imports_for_type(type1_str)
                context.add_typing_imports_for_type(type2_str)
                writer.write_line("try:")
                writer.indent()
                # Pass response_ir to _get_extraction_code if available
                extraction_code_type1 = self._get_extraction_code(type1_str, context, op, needs_unwrap, response_ir)
                if "\n" in extraction_code_type1:  # Multi-line extraction
                    lines = extraction_code_type1.split("\n")
                    for line in lines[:-1]:  # all but 'return ...'
                        writer.write_line(line)
                    writer.write_line(lines[-1].replace("return ", "return_value = "))
                    writer.write_line("return return_value")
                else:
                    writer.write_line(f"return {extraction_code_type1}")

                writer.dedent()
                writer.write_line("except Exception:  # Attempt to parse as the second type")
                writer.indent()
                extraction_code_type2 = self._get_extraction_code(type2_str, context, op, needs_unwrap, response_ir)
                if "\n" in extraction_code_type2:  # Multi-line extraction
                    lines = extraction_code_type2.split("\n")
                    for line in lines[:-1]:
                        writer.write_line(line)
                    writer.write_line(lines[-1].replace("return ", "return_value = "))
                    writer.write_line("return return_value")
                else:
                    writer.write_line(f"return {extraction_code_type2}")
                writer.dedent()
            else:
                logger.warning(
                    f"Could not parse Union components with regex: {return_type}. Falling back to cast(Any, ...)"
                )
                context.add_import("typing", "Any")
                writer.write_line(f"return cast(Any, response.json())")

        elif return_type == "None":  # Explicit None, e.g. for 204 or when specific response has no content
            writer.write_line("return None")
        elif is_op_with_inferred_type:  # This condition may need re-evaluation in this context
            context.add_typing_imports_for_type(return_type)
            context.add_import("typing", "cast")
            writer.write_line(f"return cast({return_type}, response.json())")
        else:
            context.add_typing_imports_for_type(return_type)
            extraction_code_str = self._get_extraction_code(return_type, context, op, needs_unwrap, response_ir)

            if extraction_code_str == "sse_json_stream_marker":  # Specific marker for SSE
                context.add_plain_import("json")
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_sse_events_text")
                # The actual yield loop must be outside, this function is about the *return value* for one branch.
                # This indicates that SSE streaming might need to be handled more holistically.
                # For now, if we hit this, it means get_return_type decided on AsyncIterator for an SSE.
                # The method signature is already async iterator.
                # The dispatcher should yield from the iter_sse_events_text.
                # This implies that the `if response.status_code == ...:` block itself needs to be `async for ... yield`
                # This refactoring is getting deeper.
                # Quick fix: if it's sse_json_stream_marker, we write the loop here.
                writer.write_line(f"async for chunk in iter_sse_events_text(response):")
                writer.indent()
                writer.write_line("yield json.loads(chunk)")  # Assuming item_type for SSE is JSON decodable
                writer.dedent()
                writer.write_line(
                    "return  # Explicit return for async generator"
                )  # Ensure function ends if it's a generator path
            elif extraction_code_str == "iter_bytes(response)":
                writer.write_line(f"async for chunk in {extraction_code_str}:")
                writer.indent()
                writer.write_line("yield chunk")
                writer.dedent()
                writer.write_line("return  # Explicit return for async generator")

            elif "\n" in extraction_code_str:  # Multi-line extraction code (e.g. data unwrap)
                # The _get_extraction_code for unwrap already includes "return cast(...)"
                for line in extraction_code_str.split("\n"):
                    writer.write_line(line)
            else:  # Single line extraction code
                if return_type != "None":  # Should already be handled, but as safety
                    writer.write_line(f"return {extraction_code_str}")
        # writer.write_line("") # Blank line might be added by the caller of this helper
