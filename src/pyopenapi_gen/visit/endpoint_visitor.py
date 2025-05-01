from typing import Any

from pyopenapi_gen import IROperation
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
        self._analyze_and_register_imports(op, context)
        writer = CodeWriter()
        ordered_params, body_type = self._prepare_parameters(op, context)
        self._write_method_signature(writer, op, context, ordered_params)
        self._write_docstring(writer, op, context)
        has_header_params = self._write_url_and_args(writer, op, context, ordered_params, body_type)
        self._write_request(writer, op, has_header_params)
        self._write_response_parsing(writer, op, context)
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
        params = get_params(op, context)
        extra_params = []
        body_type = None
        if op.request_body:
            body_type = get_request_body_type(op.request_body, context)
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
        return_type = get_return_type(op, context, self.schemas)
        context.add_typing_imports_for_type(return_type)
        # Ensure plain import for collections.abc if AsyncIterator is used
        if ("AsyncIterator" in return_type) or any(
            "AsyncIterator" in get_param_type(p, context) for p in op.parameters
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
            param_type = get_param_type(param, context)
            desc = param.description or ""
            args.append((param.name, param_type, desc))
        if op.request_body:
            body_type = get_request_body_type(op.request_body, context)
            desc = op.request_body.description or "Request body."
            args.append(("body", body_type, desc))
            if any("multipart/form-data" in mt for mt in op.request_body.content):
                args.append(("files", "Dict[str, IO[Any]]", "Multipart form files (if required)."))
        return_type = get_return_type(op, context, getattr(self, "schemas", {}))
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

    def _write_response_parsing(self, writer: CodeWriter, op: IROperation, context: RenderContext) -> None:
        """
        Write the response parsing and return statement for the endpoint method, based on the return type.

        Args:
            writer: The CodeWriter to emit code to.
            op: The IROperation node.
            context: The RenderContext for type resolution.
        """
        return_type = get_return_type(op, context, self.schemas)
        context.add_typing_imports_for_type(return_type)  # Ensure return type is registered
        writer.write_line("# Parse response into correct return type")
        if return_type.startswith("List["):
            writer.write_line("return [item for item in response.json()]")
        elif return_type in ("int", "float", "str", "bool"):
            writer.write_line(f"return {return_type}(response.json())")
        elif return_type.startswith("Dict["):
            writer.write_line("return response.json()")
        elif return_type == "None":
            writer.write_line("return None")
        elif return_type == "Any":
            writer.write_line("return response.json()")
        elif return_type.startswith("AsyncIterator["):
            # Use a helper function for streaming responses
            item_type = return_type[len("AsyncIterator[") : -1].strip()
            context.add_import(f"{context.core_package}.streaming_helpers", "iter_bytes")
            context.add_plain_import("json")  # import json
            # PATCH: Only import model if item_type is a real model class (not Dict[str, Any], str, etc.)
            if item_type not in (
                "Dict[str, Any]",
                "str",
                "int",
                "float",
                "bool",
                "Any",
                "bytes",
            ):
                context.add_import("..models", item_type)
            # Add explicit return type annotation to _stream
            writer.write_line(f"async def _stream() -> {return_type}:")
            writer.indent()
            writer.write_line("async for chunk in iter_bytes(response):")
            writer.indent()
            # PATCH: For Dict[str, Any], yield json.loads(chunk) directly
            if item_type == "Dict[str, Any]":
                writer.write_line("yield json.loads(chunk)")
            elif item_type == "bytes":
                writer.write_line("yield chunk")
            elif item_type in ("str", "int", "float", "bool"):
                writer.write_line(f"yield {item_type}(json.loads(chunk))")
            elif item_type == "Any":
                context.add_import("typing", "cast")
                writer.write_line("yield cast(Any, json.loads(chunk))")
            else:
                writer.write_line(f"yield {item_type}(**json.loads(chunk))")
            writer.dedent()
            writer.dedent()
            writer.write_line("return _stream()")
        else:
            writer.write_line(f"return {return_type}(**response.json())")
        writer.dedent()

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
        context.add_import(f"{context.core_package}.http_transport", "HttpTransport")
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
        for method in methods:
            writer.write_block(method)
        writer.dedent()
        return writer.get_code()

    def _analyze_and_register_imports(self, op: IROperation, context: RenderContext) -> None:
        # Analyze parameters
        for param in op.parameters:
            py_type = get_param_type(param, context)
            context.add_typing_imports_for_type(py_type)
        # Analyze request body
        if op.request_body:
            body_type = get_request_body_type(op.request_body, context)
            context.add_typing_imports_for_type(body_type)
            if any("multipart/form-data" in mt for mt in op.request_body.content):
                context.add_import("typing", "Dict")
                context.add_import("typing", "Any")
                context.add_import("typing", "IO")
        # Analyze return type
        return_type = get_return_type(op, context, self.schemas)
        context.add_typing_imports_for_type(return_type)
        # Ensure plain import for collections.abc if AsyncIterator is used
        if ("AsyncIterator" in return_type) or any(
            "AsyncIterator" in get_param_type(p, context) for p in op.parameters
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
        """
        Generate the endpoint method as a method of the endpoint client class.
        """
        self._analyze_and_register_imports(op, context)
        context.add_import("typing", "cast")
        context.add_import(f"{context.core_package}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package}.streaming_helpers", "iter_bytes")
        context.add_import("typing", "Callable")
        context.add_import("typing", "Optional")
        method_name = NameSanitizer.sanitize_method_name(op.operation_id)
        summary = op.summary or ""
        path = op.path

        # --- 1. Analyze and merge parameters ---
        params = get_params(op, context)
        extra_params = []

        if op.request_body:
            body_type = get_request_body_type(op.request_body, context)
            for mt, sch in op.request_body.content.items():
                if "json" in mt.lower() and hasattr(sch, "properties") and sch.properties:
                    params = merge_params_with_model_fields(op, sch, context)
                    break
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

        # --- 2. Build method signature ---
        args = ["self"]
        for p in ordered_params:
            arg = f"{p['name']}: {p['type']}"
            if p.get("default") is not None:
                arg += f" = {p['default']}"
            args.append(arg)
        writer = CodeWriter()
        writer.write_function_signature(
            method_name,
            args,
            return_type=get_return_type(op, context, self.schemas),
            async_=True,
        )
        writer.indent()
        # Always emit a docstring or pass to avoid empty method body
        if summary.strip():
            writer.write_line(f'"""{summary}"""')
        # --- 3. Build URL and request arguments ---
        context.add_import("typing", "Any")
        context.add_import("typing", "Dict")
        url_expr = self._build_url_with_path_vars(op.path)
        if url_expr:
            writer.write_line(f"url = {url_expr}")
        writer.write_line("params: dict[str, Any] = {")
        writer.indent()
        for p in ordered_params:
            if hasattr(op, "parameters"):
                for param in op.parameters:
                    if param.name == p["name"] and getattr(param, "in_", None) == "query":
                        if not param.required:
                            writer.write_line(
                                f'**({{"{param.name}": {p["name"]}}} if {p["name"]} is not None else {{}}),'
                            )
                        else:
                            writer.write_line(f'"{param.name}": {p["name"]},')
        writer.dedent()
        writer.write_line("}")
        # Check if there are any header parameters
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
        # --- 4. Make the HTTP request ---
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
        # --- 5. Handle errors ---
        writer.write_line("if response.status_code < 200 or response.status_code >= 300:")
        writer.indent()
        writer.write_line("raise HTTPError(response.status_code, response.text)")
        writer.dedent()
        # --- 6. Parse and return the response ---
        return_type = get_return_type(op, context, self.schemas)
        writer.write_line("# Parse response into correct return type")
        if return_type.startswith("List["):
            writer.write_line("return [item for item in response.json()]")
        elif return_type in ("int", "float", "str", "bool"):
            writer.write_line(f"return {return_type}(response.json())")
        elif return_type.startswith("Dict["):
            writer.write_line("return response.json()")
        elif return_type == "None":
            writer.write_line("return None")
        elif return_type == "Any":
            writer.write_line("return response.json()")
        elif return_type.startswith("AsyncIterator["):
            # Use a helper function for streaming responses
            item_type = return_type[len("AsyncIterator[") : -1].strip()
            context.add_import(f"{context.core_package}.streaming_helpers", "iter_bytes")
            context.add_plain_import("json")  # import json
            # PATCH: Only import model if item_type is a real model class (not Dict[str, Any], str, etc.)
            if item_type not in (
                "Dict[str, Any]",
                "str",
                "int",
                "float",
                "bool",
                "Any",
                "bytes",
            ):
                context.add_import("..models", item_type)
            # Add explicit return type annotation to _stream
            writer.write_line(f"async def _stream() -> {return_type}:")
            writer.indent()
            writer.write_line("async for chunk in iter_bytes(response):")
            writer.indent()
            # PATCH: For Dict[str, Any], yield json.loads(chunk) directly
            if item_type == "Dict[str, Any]":
                writer.write_line("yield json.loads(chunk)")
            elif item_type == "bytes":
                writer.write_line("yield chunk")
            elif item_type in ("str", "int", "float", "bool"):
                writer.write_line(f"yield {item_type}(json.loads(chunk))")
            elif item_type == "Any":
                context.add_import("typing", "cast")
                writer.write_line("yield cast(Any, json.loads(chunk))")
            else:
                writer.write_line(f"yield {item_type}(**json.loads(chunk))")
            writer.dedent()
            writer.dedent()
            writer.write_line("return _stream()")
        else:
            writer.write_line(f"return {return_type}(**response.json())")
        writer.dedent()
        return writer.get_code()
