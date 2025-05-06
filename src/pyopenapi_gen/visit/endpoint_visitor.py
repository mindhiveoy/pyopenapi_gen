import logging
from typing import Any, Optional
import re

from pyopenapi_gen import IROperation, IRSchema
from pyopenapi_gen.helpers.endpoint_utils import (
    get_param_type,
    get_params,
    get_request_body_type,
    get_return_type,
    merge_params_with_model_fields,
)
from pyopenapi_gen.helpers.url_utils import extract_url_variables

from ..context.render_context import RenderContext
from ..core.utils import Formatter, NameSanitizer
from ..core.writers.code_writer import CodeWriter
from ..core.writers.documentation_writer import DocumentationBlock, DocumentationWriter
from .visitor import Visitor

# Get logger instance
logger = logging.getLogger(__name__)


class EndpointVisitor(Visitor[IROperation, str]):
    """
    Visitor for rendering a Python endpoint client method/class from an IROperation.
    Only adds imports/types to the context if they are actually used in the rendered code for the module.
    Returns the rendered code as a string (does not write files).
    """

    def __init__(self, schemas: dict[str, Any] | None = None) -> None:
        self.formatter = Formatter()
        self.schemas = schemas or {}

    def visit_IROperation(self, op: IROperation, context: RenderContext) -> str:
        """
        Generate a fully functional async endpoint method for the given operation.
        Returns only the method code (not the class).
        """
        # Add core imports needed by every method
        context.add_import(f"{context.core_package}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package}.exceptions", "ApiError")
        context.add_import(f"{context.core_package}.schemas", "ApiResponse")

        self._analyze_and_register_imports(op, context)
        writer = CodeWriter()
        ordered_params, body_type = self._prepare_parameters(op, context)
        self._write_method_signature(writer, op, context, ordered_params)
        self._write_docstring(writer, op, context)
        has_header_params = self._write_url_and_args(writer, op, context, ordered_params, body_type)
        self._write_request(writer, op, has_header_params)
        # Get return type and whether it needs unwrapping
        return_type, needs_unwrap = get_return_type(op, context, self.schemas)

        writer.write_line("# Parse response into correct return type")

        # Change: Use improved regex to parse Union components
        match = re.match(r"Union\[(.*?)\s*,\s*(.*)\]", return_type)
        if match:
            type1_str = match.group(1).strip()
            type2_str = match.group(2).strip()

            # Import the component types explicitly
            context.add_typing_imports_for_type(type1_str)
            context.add_typing_imports_for_type(type2_str)

            writer.write_line("try:")
            writer.indent()
            # Change: Restore specific cast
            writer.write_line(f"    return cast({type1_str}, response.json())")
            writer.dedent()
            writer.write_line("except Exception: # TODO: More specific exception handling")
            writer.indent()
            # Change: Restore specific cast
            writer.write_line(f"    return cast({type2_str}, response.json())")
            writer.dedent()
        elif return_type == "None":
            writer.write_line("return None")
        else:
            context.add_typing_imports_for_type(return_type)
            extraction_code = self._get_extraction_code(return_type, context, op, needs_unwrap)
            writer.write_line(f"return {extraction_code}")

        # Dedent from method body
        writer.dedent()
        return writer.get_code()

    def _prepare_parameters(self, op: IROperation, context: RenderContext) -> tuple[list[dict[str, Any]], str | None]:
        """
        Analyze and merge parameters for the endpoint method, including request body and files if present.
        Ensures all path variables are present as function arguments and orders required/optional params.

        Args:
            op: The IROperation node representing the endpoint.
            context: The RenderContext for import tracking.

        Returns:
            ordered_params: List of all parameters, required first, then optional.
            body_type: The Python type for the request body, if any.
        """
        params = get_params(op, context, self.schemas)
        extra_params = []
        body_type = None
        if op.request_body:
            body_type = get_request_body_type(op.request_body, context, self.schemas)
            # Only add a single 'body' param, do NOT merge model fields
            extra_params.append({
                "name": "body",
                "type": body_type,
                "default": None if op.request_body.required else "None",
                "required": op.request_body.required,
            })
            if any("multipart/form-data" in mt for mt in op.request_body.content):
                extra_params.append({
                    "name": "files",
                    "type": "Dict[str, IO[Any]]",
                    "default": None if op.request_body.required else "None",
                    "required": op.request_body.required,
                })
        all_params = params + extra_params
        all_params = self._ensure_path_variables_as_params(op, all_params)
        required_params = [p for p in all_params if p.get("required", True)]
        optional_params = [p for p in all_params if not p.get("required", True)]
        ordered_params = required_params + optional_params
        return ordered_params, body_type

    def _write_method_signature(
        self,
        writer: CodeWriter,
        op: IROperation,
        context: RenderContext,
        ordered_params: list[dict[str, Any]],
    ) -> None:
        """
        Write the async method signature for the endpoint, including type annotations.

        Args:
            writer: The CodeWriter to emit code to.
            op: The IROperation node.
            context: The RenderContext for type resolution.
            ordered_params: List of parameters for the method signature.
        """
        # Ensure all types in the signature are registered for import
        for p in ordered_params:
            context.add_typing_imports_for_type(p["type"])
        # Pass self.schemas to get_return_type
        return_type, _ = get_return_type(op, context, self.schemas)
        context.add_typing_imports_for_type(return_type)
        # Ensure plain import for collections.abc if AsyncIterator is used
        # Pass self.schemas when calling get_param_type indirectly
        # Note: get_params needs modification to accept schemas
        if ("AsyncIterator" in return_type) or any(
            "AsyncIterator" in get_param_type(p, context, self.schemas) for p in op.parameters
        ):
            context.add_plain_import("collections.abc")
        # Build argument list for signature
        args = ["self"]
        for p in ordered_params:
            arg = f"{p['name']}: {p['type']}"
            if p.get("default") is not None:
                arg += f" = {p['default']}"
            args.append(arg)
        writer.write_function_signature(
            NameSanitizer.sanitize_method_name(op.operation_id),
            args,
            return_type=return_type,
            async_=True,
        )
        writer.indent()

    def _write_docstring(self, writer: CodeWriter, op: IROperation, context: RenderContext) -> None:
        """
        Write a comprehensive Google-style docstring for the endpoint method using DocumentationWriter.
        """

        # Build DocumentationBlock
        summary = op.summary or None
        description = op.description or None
        args: list[tuple[str, str, str] | tuple[str, str]] = []
        for param in op.parameters:
            # Pass self.schemas down to get_param_type
            param_type = get_param_type(param, context, self.schemas)
            desc = param.description or ""
            args.append((param.name, param_type, desc))
        if op.request_body:
            # Pass self.schemas down to get_request_body_type
            body_type = get_request_body_type(op.request_body, context, self.schemas)
            desc = op.request_body.description or "Request body."
            args.append(("body", body_type, desc))
            if any("multipart/form-data" in mt for mt in op.request_body.content):
                args.append(("files", "Dict[str, IO[Any]]", "Multipart form files (if required)."))
        # Pass self.schemas to get_return_type
        return_type, _ = get_return_type(op, context, self.schemas)
        # Find the best response description
        response_desc = None
        for code in ("200", "201", "202", "default"):
            resp = next((r for r in op.responses if r.status_code == code), None)
            if resp and resp.description:
                response_desc = resp.description.strip()
                break
        if not response_desc:
            for resp in op.responses:
                if resp.description:
                    response_desc = resp.description.strip()
                    break
        returns = (return_type, response_desc or "Response object.") if return_type and return_type != "None" else None
        # Raises
        error_codes = [r for r in op.responses if r.status_code.isdigit() and int(r.status_code) >= 400]
        raises = []
        if error_codes:
            for resp in error_codes:
                code = "HTTPError"
                desc = f"{resp.status_code}: {resp.description.strip() if resp.description else 'HTTP error.'}"
                raises.append((code, desc))
        else:
            raises.append(("HTTPError", "If the server returns a non-2xx HTTP response."))
        doc_block = DocumentationBlock(
            summary=summary,
            description=description,
            args=args,
            returns=returns,
            raises=raises,
        )
        docstring = DocumentationWriter(width=88).render_docstring(doc_block, indent=0)
        for line in docstring.splitlines():
            writer.write_line(line)

    @staticmethod
    def _wrap_docstring(prefix: str, text: str, width: int = 88) -> str:
        import textwrap

        if not text:
            return prefix.rstrip()
        initial_indent = prefix
        subsequent_indent = " " * len(prefix)
        wrapped = textwrap.wrap(text, width=width, initial_indent=initial_indent, subsequent_indent=subsequent_indent)
        return "\n    ".join(wrapped)

    def _write_url_and_args(
        self,
        writer: CodeWriter,
        op: IROperation,
        context: RenderContext,
        ordered_params: list[dict[str, Any]],
        body_type: str | None,
    ) -> bool:
        """
        Write the URL construction, params, headers, and request body/file setup for the endpoint method.
        """
        context.add_import("typing", "Any")
        context.add_import("typing", "Dict")
        url_expr = self._build_url_with_path_vars(op.path)
        if url_expr:
            writer.write_line(f"url = {url_expr}")
        writer.write_line("params: dict[str, Any] = {")
        writer.indent()
        self._write_query_params(writer, op, ordered_params)
        writer.dedent()
        writer.write_line("}")
        has_header_params = any(getattr(param, "in_", None) == "header" for param in op.parameters)
        if has_header_params:
            writer.write_line("headers: dict[str, Any] = {")
            writer.indent()
            self._write_header_params(writer, op, ordered_params)
            writer.dedent()
            writer.write_line("}")
        if op.request_body and any("json" in mt.lower() for mt in op.request_body.content):
            writer.write_line(f"json_body: {body_type} = body")
        if op.request_body and any("multipart/form-data" in mt for mt in op.request_body.content):
            writer.write_line("files_data: Dict[str, IO[Any]] = files")
        return has_header_params

    def _write_query_params(self, writer: CodeWriter, op: IROperation, ordered_params: list[dict[str, Any]]) -> None:
        """
        Write the query parameters dictionary for the endpoint method.

        Args:
            writer: The CodeWriter to emit code to.
            op: The IROperation node.
            ordered_params: List of parameters for the method.
        """
        from ..core.utils import NameSanitizer

        for param in op.parameters:
            if getattr(param, "in_", None) == "query":
                var_name = NameSanitizer.sanitize_method_name(param.name)
                if not param.required:
                    writer.write_line(f'**({{"{param.name}": {var_name}}} if {var_name} is not None else {{}}),')
                else:
                    writer.write_line(f'"{param.name}": {var_name},')

    def _write_header_params(self, writer: CodeWriter, op: IROperation, ordered_params: list[dict[str, Any]]) -> None:
        """
        Write the header parameters dictionary for the endpoint method.

        Args:
            writer: The CodeWriter to emit code to.
            op: The IROperation node.
            ordered_params: List of parameters for the method.
        """
        for p in ordered_params:
            if hasattr(op, "parameters"):
                for param in op.parameters:
                    if param.name == p["name"] and getattr(param, "in_", None) == "header":
                        writer.write_line(f'"{param.name}": {p["name"]},')

    def _write_request(self, writer: CodeWriter, op: IROperation, has_header_params: bool) -> None:
        """
        Write the HTTP request invocation for the endpoint method.
        """
        writer.write_line("response = await self._transport.request(")
        writer.indent()
        writer.write_line(f'"{op.method.upper()}", url,')
        writer.write_line("params=params,")
        if has_header_params:
            writer.write_line("headers=headers,")
        if op.request_body and any("json" in mt.lower() for mt in op.request_body.content):
            writer.write_line("json=json_body,")
        if op.request_body and any("multipart/form-data" in mt for mt in op.request_body.content):
            writer.write_line("files=files_data,")
        writer.dedent()
        writer.write_line(")")

    def emit_endpoint_client_class(
        self,
        tag: str,
        methods: list[str],
        context: RenderContext,
    ) -> str:
        """
        Emit the endpoint client class for a tag, aggregating all endpoint methods.
        The generated class is fully type-annotated and uses HttpTransport for HTTP communication.
        Args:
            tag: The tag name for the endpoint group.
            methods: List of method code blocks as strings.
            context: The RenderContext for import tracking.
        """
        context.add_import("typing", "cast")
        # Import core transport and streaming helpers
        context.add_import(f"{context.core_package}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package}.streaming_helpers", "iter_bytes")
        context.add_import("typing", "Callable")
        context.add_import("typing", "Optional")
        writer = CodeWriter()
        class_name = NameSanitizer.sanitize_class_name(tag) + "Client"
        writer.write_line(f"class {class_name}:")
        writer.indent()
        writer.write_line(f'"""Client for {tag} endpoints. Uses HttpTransport for all HTTP and header management."""')
        writer.write_line("")
        writer.write_line("def __init__(self, transport: HttpTransport, base_url: str) -> None:")
        writer.indent()
        writer.write_line("self._transport = transport")
        writer.write_line("self.base_url: str = base_url")
        writer.dedent()
        writer.write_line("")
        for i, method in enumerate(methods):
            writer.write_block(method)
            if i < len(methods) - 1:
                writer.write_line("")
        writer.dedent()
        return writer.get_code()

    def _analyze_and_register_imports(self, op: IROperation, context: RenderContext) -> None:
        # Analyze parameters
        for param in op.parameters:
            py_type = get_param_type(param, context, self.schemas)
            context.add_typing_imports_for_type(py_type)
        # Analyze request body
        if op.request_body:
            body_type = get_request_body_type(op.request_body, context, self.schemas)
            context.add_typing_imports_for_type(body_type)
            if any("multipart/form-data" in mt for mt in op.request_body.content):
                context.add_import("typing", "Dict")
                context.add_import("typing", "Any")
                context.add_import("typing", "IO")
        # Analyze return type
        return_type, _ = get_return_type(op, context, self.schemas)
        context.add_typing_imports_for_type(return_type)
        # Ensure plain import for collections.abc if AsyncIterator is used
        if ("AsyncIterator" in return_type) or any(
            "AsyncIterator" in get_param_type(p, context, self.schemas) for p in op.parameters
        ):
            context.add_plain_import("collections.abc")

    def _ensure_path_variables_as_params(
        self, op: IROperation, all_params: list[dict[str, Any]]
    ) -> list[dict[str, object]]:
        """
        Ensure all path variables from the path template are present as function arguments.
        """
        url_vars = extract_url_variables(op.path)
        param_names = {p["name"] for p in all_params}
        for var in url_vars:
            sanitized_var = NameSanitizer.sanitize_method_name(var)
            if sanitized_var not in param_names:
                all_params.append({
                    "name": sanitized_var,
                    "type": "str",
                    "default": None,
                    "required": True,
                })
                param_names.add(sanitized_var)
        return all_params

    def _build_url_with_path_vars(self, path: str) -> str:
        """
        Build a URL f-string expression referencing sanitized path variable names.
        """
        url_vars = extract_url_variables(path)
        for var in url_vars:
            sanitized_var = NameSanitizer.sanitize_method_name(var)
            path = path.replace(f"{{{var}}}", f"{{{sanitized_var}}}")
        return f'f"{{self.base_url}}{path}"'

    def _generate_endpoint_method(self, op: IROperation, context: RenderContext, class_name: str) -> str:
        """Generate the full Python code string for a single endpoint method."""
        method_name = NameSanitizer.sanitize_method_name(op.operation_id)
        writer = CodeWriter()
        # Prepare parameters and determine body type
        ordered_params, body_type = self._prepare_parameters(op, context)
        # Write method signature
        self._write_method_signature(writer, op, context, ordered_params)
        # Write docstring
        self._write_docstring(writer, op, context)
        # Write URL, params, headers, body setup
        has_header_params = self._write_url_and_args(writer, op, context, ordered_params, body_type)
        # Write request call
        self._write_request(writer, op, has_header_params)
        # Get the return type, unwrapping flag, and component types
        return_type, needs_unwrap = get_return_type(op, context, self.schemas)

        writer.write_line("# Parse response into correct return type")

        if return_type.startswith("Union["):
            context.add_import("typing", "Union")
            context.add_import("typing", "cast")
            context.add_import("typing", "Dict")
            context.add_import("typing", "Any")

            # Change: Use improved regex to parse Union components
            match = re.match(r"Union\[(.*?)\s*,\s*(.*)\]", return_type)
            if match:
                type1_str = match.group(1).strip()
                type2_str = match.group(2).strip()

                # Import the component types explicitly
                context.add_typing_imports_for_type(type1_str)
                context.add_typing_imports_for_type(type2_str)

                writer.write_line("try:")
                writer.indent()
                # Change: Restore specific cast
                writer.write_line(f"    return cast({type1_str}, response.json())")
                writer.dedent()
                writer.write_line("except Exception: # TODO: More specific exception handling")
                writer.indent()
                # Change: Restore specific cast
                writer.write_line(f"    return cast({type2_str}, response.json())")
                writer.dedent()
            else:
                # Fallback if regex fails - cast to Any to avoid syntax error
                # Log a warning here?
                logger.warning(
                    f"Could not parse Union components with regex: {return_type}. Falling back to cast(Any, ...)"
                )
                writer.write_line(f"return cast(Any, response.json())")

        elif return_type == "None":
            writer.write_line("return None")
        else:
            context.add_typing_imports_for_type(return_type)
            extraction_code = self._get_extraction_code(return_type, context, op, needs_unwrap)
            writer.write_line(f"return {extraction_code}")

        # Dedent from method body
        writer.dedent()
        return writer.get_code()

    def _get_extraction_code(
        self, return_type: str, context: RenderContext, op: IROperation, needs_unwrap: bool
    ) -> str:
        """Generate the Python code snippet to parse the httpx.Response into the target return_type."""
        # Restore original logic
        if return_type == "str":
            return "response.text"
        elif return_type == "bytes":
            return "response.content"
        elif return_type == "Any":
            context.add_import("typing", "Any")
            return "response.json() # Type is Any"
        elif return_type == "None":
            return "None"
        else:
            # Assumes it's a model, list, dict, or primitive parsable from JSON
            context.add_import("typing", "cast")
            context.add_typing_imports_for_type(return_type)
            if needs_unwrap:
                # Access the 'data' attribute after parsing the JSON
                # Assuming response.json() returns a dict-like structure
                return f"cast({return_type}, response.json().get('data'))"
            else:
                # Original logic for non-unwrapped types
                return f"cast({return_type}, response.json())"

    def _get_response_schema(self, op: IROperation) -> Any:
        # Prefer 200, then first 2xx, then default, then any
        resp = None
        for code in (
            ["200"]
            + [r.status_code for r in op.responses if r.status_code.startswith("2") and r.status_code != "200"]
            + ["default"]
        ):
            resp = next((r for r in op.responses if r.status_code == code), None)
            if resp:
                break
        if not resp and op.responses:
            resp = op.responses[0]
        if not resp or not resp.content:
            return None
        # Pick first content type (prefer application/json, then event-stream, then any)
        content_types = list(resp.content.keys())
        mt = next(
            (ct for ct in content_types if "json" in ct),
            next((ct for ct in content_types if "event-stream" in ct), content_types[0]),
        )
        return resp.content[mt]
