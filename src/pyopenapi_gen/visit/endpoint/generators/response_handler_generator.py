"""
Helper class for generating response handling logic for an endpoint method.
"""

from __future__ import annotations

import logging
import re  # For parsing Union types, etc.
from typing import TYPE_CHECKING, Any, Dict, Optional, TypedDict

from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.helpers.endpoint_utils import (
    _get_primary_response,
    get_return_type_unified,
    get_type_for_specific_response,  # Added new helper
)
from pyopenapi_gen.types.services.type_service import UnifiedTypeService

if TYPE_CHECKING:
    from pyopenapi_gen import IROperation, IRResponse
    from pyopenapi_gen.context.render_context import RenderContext
else:
    # For runtime, we need to import for TypedDict
    from pyopenapi_gen import IRResponse

logger = logging.getLogger(__name__)


class StatusCase(TypedDict):
    """Type definition for status code case data."""

    status_code: int
    type: str  # 'primary_success', 'success', or 'error'
    return_type: str
    needs_unwrap: bool
    response_ir: IRResponse


class DefaultCase(TypedDict):
    """Type definition for default case data."""

    response_ir: IRResponse
    return_type: str
    needs_unwrap: bool


class EndpointResponseHandlerGenerator:
    """Generates the response handling logic for an endpoint method."""

    def __init__(self, schemas: Optional[Dict[str, Any]] = None) -> None:
        self.schemas: Dict[str, Any] = schemas or {}

    def _should_use_json_wizard(self, type_name: str) -> bool:
        """
        Determine if a type should use JSONWizard deserialization.

        Args:
            type_name: The Python type name (e.g., "User", "List[User]", "Optional[User]")

        Returns:
            True if the type should use JSONWizard .from_dict() deserialization
        """
        # Extract the base type name from complex types
        base_type = type_name

        # Handle List[Type], Optional[Type], etc.
        if "[" in base_type and "]" in base_type:
            # Extract the inner type from List[Type], Optional[Type], etc.
            start_bracket = base_type.find("[")
            end_bracket = base_type.rfind("]")
            inner_type = base_type[start_bracket + 1 : end_bracket]

            # For Union types like Optional[User] -> Union[User, None], take the first type
            if ", " in inner_type:
                inner_type = inner_type.split(", ")[0]

            base_type = inner_type.strip()

        # Skip primitive types and built-ins
        if base_type in {"str", "int", "float", "bool", "bytes", "None", "Any", "Dict", "List"}:
            return False

        # Skip typing constructs
        if base_type.startswith(("Dict[", "List[", "Optional[", "Union[", "Tuple[")):
            return False

        # Check if it's a model type (contains a dot indicating it's from models package)
        # or if it's a simple class name that's likely a generated model (starts with uppercase)
        return "." in base_type or base_type[0].isupper()

    def _get_json_wizard_deserialization_code(self, return_type: str, data_expr: str) -> str:
        """
        Generate JSONWizard deserialization code for a given type.

        Args:
            return_type: The return type (e.g., "User", "List[User]")
            data_expr: The expression containing the raw data to deserialize

        Returns:
            Code string for deserializing the data using JSONWizard
        """
        if return_type.startswith("List["):
            # Handle List[Model] types
            item_type = return_type[5:-1]  # Remove 'List[' and ']'
            return f"[{item_type}.from_dict(item) for item in {data_expr}]"
        elif return_type.startswith("Optional["):
            # Handle Optional[Model] types
            inner_type = return_type[9:-1]  # Remove 'Optional[' and ']'
            return f"{inner_type}.from_dict({data_expr}) if {data_expr} is not None else None"
        else:
            # Handle simple Model types
            return f"{return_type}.from_dict({data_expr})"

    def _get_extraction_code(
        self,
        return_type: str,
        context: RenderContext,
        op: IROperation,
        needs_unwrap: bool,
        response_ir: Optional[IRResponse] = None,
    ) -> str:
        """Determines the code snippet to extract/transform the response body."""
        # Handle None, StreamingResponse, Iterator, etc.
        if return_type is None or return_type == "None":
            return "None"  # This will be directly used in the return statement

        # Handle streaming responses
        if return_type.startswith("AsyncIterator["):
            # Check if it's a bytes stream or other type of stream
            if return_type == "AsyncIterator[bytes]":
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_bytes")
                return "iter_bytes(response)"
            elif "Dict[str, Any]" in return_type or "dict" in return_type.lower():
                # For event streams that return Dict objects
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_sse_events_text")
                return "sse_json_stream_marker"  # Special marker handled by _write_parsed_return
            else:
                # Model streaming - likely an SSE model stream
                # Extract the model type and check if content type is text/event-stream
                model_type = return_type[13:-1]  # Remove 'AsyncIterator[' and ']'
                if response_ir and "text/event-stream" in response_ir.content:
                    context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_sse_events_text")
                    return "sse_json_stream_marker"  # Special marker for SSE

                # Default to bytes streaming for other types
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_bytes")
                return "iter_bytes(response)"

        # Special case for "data: Any" unwrapping when the actual schema has no fields/properties
        if return_type in {"Dict[str, Any]", "Dict[str, object]", "object", "Any"}:
            context.add_import("typing", "Dict")
            context.add_import("typing", "Any")

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
            context.add_typing_imports_for_type(return_type)  # Ensure model itself is imported

            # Check if we should use JSONWizard deserialization instead of cast()
            use_json_wizard = self._should_use_json_wizard(return_type)

            if not use_json_wizard:
                # Fallback to cast() for non-JSONWizard types
                context.add_import("typing", "cast")

            if needs_unwrap:
                # Special handling for List unwrapping - ensure we have the correct imports
                if return_type.startswith("List["):
                    # Extract the item type from List[ItemType]
                    item_type = return_type[5:-1]  # Remove 'List[' and ']'
                    context.add_import("typing", "List")
                    if "." in item_type:
                        # Ensure we have the proper import for the item type
                        context.add_typing_imports_for_type(item_type)

                    # Handle unwrapping of List with proper deserialization
                    if use_json_wizard:
                        deserialization_code = self._get_json_wizard_deserialization_code(return_type, "raw_data")
                        return (
                            f"raw_data = response.json().get('data')\n"
                            f"if raw_data is None:\n"
                            f"    raise ValueError(\"Expected 'data' key in response but found None\")\n"
                            f"return {deserialization_code}"
                        )
                    else:
                        return (
                            f"raw_data = response.json().get('data')\n"
                            f"if raw_data is None:\n"
                            f"    raise ValueError(\"Expected 'data' key in response but found None\")\n"
                            f"return cast({return_type}, raw_data)"
                        )

                # Standard unwrapping for single object
                if use_json_wizard:
                    deserialization_code = self._get_json_wizard_deserialization_code(return_type, "raw_data")
                    return (
                        f"raw_data = response.json().get('data')\n"
                        f"if raw_data is None:\n"
                        f"    raise ValueError(\"Expected 'data' key in response but found None\")\n"
                        f"return {deserialization_code}"
                    )
                else:
                    return (
                        f"raw_data = response.json().get('data')\n"
                        f"if raw_data is None:\n"
                        f"    raise ValueError(\"Expected 'data' key in response but found None\")\n"
                        f"return cast({return_type}, raw_data)"
                    )
            else:
                # No unwrapping needed - direct deserialization
                if use_json_wizard:
                    deserialization_code = self._get_json_wizard_deserialization_code(return_type, "response.json()")
                    return deserialization_code
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
            is_default_with_content = primary_success_ir.status_code == "default" and bool(
                primary_success_ir.content
            )  # Ensure this part is boolean
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

        # Collect all status codes and their handlers for the match statement
        status_cases: list[StatusCase] = []

        # 1. Handle primary success response IF IT IS TRULY A SUCCESS RESPONSE AND NUMERIC (2xx)
        if is_primary_handled_by_first_block:
            assert primary_success_ir is not None  # Add assertion to help linter
            # No try-except needed here as isdigit() and startswith("2") already checked
            status_code_val = int(primary_success_ir.status_code)

            # This is the return_type for the *entire operation*, based on its primary success response
            # First try the fallback method for backward compatibility
            return_type_for_op = get_return_type_unified(op, context, self.schemas)
            needs_unwrap_for_op = False  # Default to False

            # If we have proper schemas, try to get unwrapping information from unified service
            if self.schemas and hasattr(list(self.schemas.values())[0] if self.schemas else None, "type"):
                try:
                    type_service = UnifiedTypeService(self.schemas)
                    return_type_for_op, needs_unwrap_for_op = type_service.resolve_operation_response_with_unwrap_info(
                        op, context
                    )
                except Exception:
                    # Fall back to the original approach if there's an issue
                    needs_unwrap_for_op = False

            status_cases.append(
                StatusCase(
                    status_code=status_code_val,
                    type="primary_success",
                    return_type=return_type_for_op,
                    needs_unwrap=needs_unwrap_for_op,
                    response_ir=primary_success_ir,
                )
            )

        # 2. Handle other specific responses (other 2xx, then default, then errors)
        default_case: Optional[DefaultCase] = None
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
                    current_return_type_str = get_type_for_specific_response(
                        operation_path=getattr(op, "path", ""),
                        resp_ir=resp_ir,
                        all_schemas=self.schemas,
                        ctx=context,
                        return_unwrap_data_property=True,
                    )
                    current_needs_unwrap = (
                        "data" in current_return_type_str.lower() or "item" in current_return_type_str.lower()
                    )

            if resp_ir.status_code == "default":
                # Determine type for default response if it has content
                default_return_type_str = "None"
                default_needs_unwrap = False
                if resp_ir.content:
                    # If 'default' is primary success, get_return_type_unified(op,...) might give its type.
                    # We use the operation's global/primary return type if default has content.
                    op_global_return_type = get_return_type_unified(op, context, self.schemas)
                    op_global_needs_unwrap = False  # Unified service handles unwrapping internally
                    # Only use this if the global type is not 'None', otherwise keep default_return_type_str as 'None'.
                    if op_global_return_type != "None":
                        default_return_type_str = op_global_return_type
                        default_needs_unwrap = op_global_needs_unwrap

                default_case = DefaultCase(
                    response_ir=resp_ir, return_type=default_return_type_str, needs_unwrap=default_needs_unwrap
                )
                continue  # Handle default separately

            try:
                status_code_val = int(resp_ir.status_code)
                case_type = "success" if resp_ir.status_code.startswith("2") else "error"

                status_cases.append(
                    StatusCase(
                        status_code=status_code_val,
                        type=case_type,
                        return_type=current_return_type_str,
                        needs_unwrap=current_needs_unwrap,
                        response_ir=resp_ir,
                    )
                )
            except ValueError:
                logger.warning(f"Skipping non-integer status code in other_responses: {resp_ir.status_code}")

        # Generate the match statement
        if status_cases or default_case:
            writer.write_line("match response.status_code:")
            writer.indent()

            # Generate cases for specific status codes
            for case in status_cases:
                writer.write_line(f"case {case['status_code']}:")
                writer.indent()

                if case["type"] == "primary_success":
                    # If get_return_type determined a specific type (not "None"),
                    # we should attempt to parse the response accordingly. This handles cases
                    # where the type was inferred even if the spec lacked explicit content for the 2xx.
                    # If get_return_type says "None" (e.g., for a 204 or truly no content), then return None.
                    if case["return_type"] == "None":
                        writer.write_line("return None")
                    else:
                        self._write_parsed_return(
                            writer, op, context, case["return_type"], case["needs_unwrap"], case["response_ir"]
                        )
                elif case["type"] == "success":
                    # Other 2xx success
                    if case["return_type"] == "None" or not case["response_ir"].content:
                        writer.write_line("return None")
                    else:
                        self._write_parsed_return(
                            writer, op, context, case["return_type"], case["needs_unwrap"], case["response_ir"]
                        )
                elif case["type"] == "error":
                    # Error codes (3xx, 4xx, 5xx)
                    error_class_name = f"Error{case['status_code']}"
                    context.add_import(
                        f"{context.core_package_name}", error_class_name
                    )  # Import from top-level core package
                    writer.write_line(f"raise {error_class_name}(response=response)")

                writer.dedent()

            # Handle default case if it exists
            if default_case:
                # Default response case - catch all remaining status codes
                if default_case["response_ir"].content and default_case["return_type"] != "None":
                    # Default case with content (success)
                    writer.write_line("case _ if response.status_code >= 0:  # Default response catch-all")
                    writer.indent()
                    self._write_parsed_return(
                        writer,
                        op,
                        context,
                        default_case["return_type"],
                        default_case["needs_unwrap"],
                        default_case["response_ir"],
                    )
                    writer.dedent()
                else:
                    # Default case without content (error)
                    writer.write_line("case _:  # Default error response")
                    writer.indent()
                    context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")
                    default_description = default_case["response_ir"].description or "Unknown default error"
                    writer.write_line(
                        f"raise HTTPError(response=response, "
                        f'message="Default error: {default_description}", '
                        f"status_code=response.status_code)"
                    )
                    writer.dedent()
            else:
                # Final catch-all for unhandled status codes
                writer.write_line("case _:")
                writer.indent()
                context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")
                writer.write_line(
                    "raise HTTPError("
                    "response=response, "
                    'message="Unhandled status code", '
                    "status_code=response.status_code)"
                )
                writer.dedent()

            writer.dedent()  # End of match statement
        else:
            # Fallback if no responses are defined
            writer.write_line("match response.status_code:")
            writer.indent()
            writer.write_line("case _:")
            writer.indent()
            context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")
            writer.write_line(
                f'raise HTTPError(response=response, message="Unhandled status code", status_code=response.status_code)'
            )
            writer.dedent()
            writer.dedent()

        # All code paths should be covered by the match statement above
        # But add an explicit assertion for mypy's satisfaction
        writer.write_line("# All paths above should return or raise - this should never execute")
        context.add_import("typing", "NoReturn")
        writer.write_line("assert False, 'Unexpected code path'  # pragma: no cover")
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
                context.add_import("typing", "cast")
                writer.write_line(f"return cast(Any, response.json())")

        elif return_type == "None":  # Explicit None, e.g. for 204 or when specific response has no content
            writer.write_line("return None")
        elif is_op_with_inferred_type:  # This condition may need re-evaluation in this context
            context.add_typing_imports_for_type(return_type)

            # Check if we should use JSONWizard deserialization instead of cast()
            if self._should_use_json_wizard(return_type):
                deserialization_code = self._get_json_wizard_deserialization_code(return_type, "response.json()")
                writer.write_line(f"return {deserialization_code}")
            else:
                context.add_import("typing", "cast")
                writer.write_line(f"return cast({return_type}, response.json())")
        else:
            context.add_typing_imports_for_type(return_type)
            extraction_code_str = self._get_extraction_code(return_type, context, op, needs_unwrap, response_ir)

            if extraction_code_str == "sse_json_stream_marker":  # SSE handling
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
            elif extraction_code_str == "iter_bytes(response)" or (
                return_type.startswith("AsyncIterator[") and "Iterator" in return_type
            ):
                # Handle streaming responses - either binary (bytes) or event-stream (Dict[str, Any])
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_bytes")
                if return_type == "AsyncIterator[bytes]":
                    # Binary streaming
                    writer.write_line(f"async for chunk in iter_bytes(response):")
                    writer.indent()
                    writer.write_line("yield chunk")
                    writer.dedent()
                elif "Dict[str, Any]" in return_type or "dict" in return_type.lower():
                    # Event-stream or JSON streaming
                    context.add_plain_import("json")
                    context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_sse_events_text")
                    writer.write_line(f"async for chunk in iter_sse_events_text(response):")
                    writer.indent()
                    writer.write_line("yield json.loads(chunk)")
                    writer.dedent()
                else:
                    # Other streaming type
                    writer.write_line(f"async for chunk in iter_bytes(response):")
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
