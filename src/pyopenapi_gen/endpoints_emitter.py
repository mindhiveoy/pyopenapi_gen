from jinja2 import Environment
import os
from typing import List, Dict, Any, Optional

from . import IRSpec, IROperation, IRParameter, IRRequestBody, IRResponse
from .utils import ImportCollector, NameSanitizer, TemplateRenderer, Formatter

# Basic OpenAPI schema to Python type mapping for parameters
PARAM_TYPE_MAPPING = {
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "string": "str",
    "array": "List",
    "object": "Dict[str, Any]",
}
# Format-specific overrides
PARAM_FORMAT_MAPPING = {
    "int32": "int",
    "int64": "int",
    "float": "float",
    "double": "float",
    "byte": "str",
    "binary": "bytes",
    "date": "date",
    "date-time": "datetime",
}

# Template for the endpoint client class methods
ENDPOINT_METHOD_TEMPLATE = '''
    async def {{ op.operation_id }}(
        self,
{% for param in op.parameters|selectattr('in_', 'equalto', 'path') %}
        {{ param.name }}: {{ get_param_type(param) }},{% endfor %}
{% for param in op.parameters|selectattr('in_', 'equalto', 'query') %}
        {{ param.name }}: Optional[{{ get_param_type(param) }}] = None,{% endfor %}
{% if op.request_body and 'application/json' in op.request_body.content %}
        body: {{ get_request_body_type(op.request_body) }},{% endif %}
    ) -> {{ op.responses | get_response_type }}:
        """{{ op.summary or '' }}
{% if op.responses|selectattr('stream')|list %}
        Stream format: {{ op.responses|selectattr('stream')|map(attribute='stream_format')|list|first or 'bytes' }}
        Use the appropriate streaming helper.
{% endif %}
        """
        # Build URL
        url = f"{self.base_url}{{ op.path }}"
        # Assemble request arguments
        kwargs = {}
{% if op.parameters|selectattr('in_', 'equalto', 'query') %}
        params = {
{% for param in op.parameters|selectattr('in_', 'equalto', 'query') %}
            '{{ param.name }}': {{ param.name }}{% if not loop.last %}, {% endif %}
{% endfor %}
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs['params'] = filtered
{% endif %}
{% if op.request_body and 'application/json' in op.request_body.content %}
        kwargs['json'] = body
{% endif %}
        # Execute request
        resp = await self.client.{{ op.method.value.lower() }}(url, **kwargs)
{% set stream_format = op.responses|selectattr('stream')|map(attribute='stream_format')|list|first %}
{% if stream_format == 'ndjson' %}
        async for obj in iter_ndjson(resp):
            yield obj
{% elif stream_format == 'event-stream' %}
        async for event in iter_sse(resp):
            yield event
{% elif op.responses|selectattr('stream')|list %}
        async for chunk in iter_bytes(resp):
            yield chunk
{% else %}
        return resp.json()
{% endif %}
'''

# Template for the class wrapper, using sanitize_class_name for valid Python class names
CLASS_TEMPLATE = '''
class {{ tag | sanitize_class_name }}Client:
    """Client for operations under the '{{ tag }}' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

{{ methods }}
'''

# Default tag for untagged operations
DEFAULT_TAG = "default"


def schema_to_type(schema: IRParameter) -> str:
    """Convert an IRParameter's schema to a Python type string."""
    s = schema.schema
    # Format-specific override
    if s.format in PARAM_FORMAT_MAPPING:
        return PARAM_FORMAT_MAPPING[s.format]
    # Handle case where s.type is a list (nullable types)
    s_type = s.type
    is_nullable = False
    if isinstance(s_type, list):
        types = [t for t in s_type if t != "null"]
        is_nullable = "null" in s_type
        s_type = types[0] if types else None
    # Array handling
    if s_type == "array" and s.items:
        item_type = schema_to_type(
            IRParameter(name="", in_="", required=False, schema=s.items)
        )
        py_type = f"List[{item_type}]"
    # Default mapping
    elif s_type in PARAM_TYPE_MAPPING:
        py_type = PARAM_TYPE_MAPPING[s_type]
    else:
        py_type = "Any"
    # If nullable, wrap with Optional
    if is_nullable:
        py_type = f"Optional[{py_type}]"
    return py_type


def _get_request_body_type(body: IRRequestBody) -> str:
    """Determine the Python type for a request body schema."""
    for mt, sch in body.content.items():
        if "json" in mt.lower():
            return schema_to_type(
                IRParameter(name="body", in_="body", required=body.required, schema=sch)
            )
    # Fallback to generic dict
    return "Dict[str, Any]"


class EndpointsEmitter:
    """Generates endpoint modules organized by tag from IRSpec."""

    def __init__(self) -> None:
        # Use centralized TemplateRenderer and Formatter for endpoint templates
        self.renderer = TemplateRenderer()
        self.formatter = Formatter()
        # Register filters and globals
        self.renderer.env.filters["get_param_type"] = self._get_param_type
        self.renderer.env.globals["get_request_body_type"] = _get_request_body_type  # type: ignore[assignment]
        # Register response type helper for strong typing
        self.renderer.env.filters["get_response_type"] = self._get_response_type

    def _get_param_type(self, param: IRParameter) -> str:
        """Get Python type annotation for a parameter."""
        return schema_to_type(param)

    def _get_response_type(self, responses: list[IRResponse]) -> str:
        """Determine the return type annotation for an operation based on responses."""
        # Streaming responses
        if any(resp.stream for resp in responses):
            return "AsyncIterator[bytes]"
        # JSON responses
        for resp in responses:
            for mt, sch in resp.content.items():
                if "json" in mt.lower():
                    # Named schema -> model class
                    if sch.name:
                        # Import model class for this response
                        return NameSanitizer.sanitize_class_name(sch.name)
                    # Fallback to primitive or collection
                    # Array handling
                    if sch.type == "array" and sch.items:
                        inner = sch.items.name if sch.items.name else None
                        if inner:
                            return f"list[{NameSanitizer.sanitize_class_name(inner)}]"
                    # Default type mapping
                    from .endpoints_emitter import PARAM_TYPE_MAPPING

                    return PARAM_TYPE_MAPPING.get(sch.type, "Any")
        # Default fallback
        return "Any"

    def _collect_imports(self, operations: List[IROperation]) -> ImportCollector:
        """Collect imports needed for the operations."""
        imports = ImportCollector()

        # Standard imports always needed
        imports.add_typing_import("Any")
        imports.add_typing_import("Dict")
        imports.add_typing_import("Optional")

        # Add httpx imports
        imports.add_direct_import("httpx", "AsyncClient")

        # Check for streaming operations and their formats
        has_streaming = any(
            any(resp.stream for resp in op.responses) for op in operations
        )
        if has_streaming:
            imports.add_typing_import("AsyncIterator")
            # Import streaming helpers as needed
            for op in operations:
                for resp in op.responses:
                    if resp.stream:
                        if resp.stream_format == "ndjson":
                            imports.add_direct_import(
                                "pyopenapi_gen.streaming_helpers", "iter_ndjson"
                            )
                        elif resp.stream_format == "event-stream":
                            imports.add_direct_import(
                                "pyopenapi_gen.streaming_helpers", "iter_sse"
                            )
                            imports.add_direct_import(
                                "pyopenapi_gen.streaming_helpers", "SSEEvent"
                            )
                        else:
                            imports.add_direct_import(
                                "pyopenapi_gen.streaming_helpers", "iter_bytes"
                            )

        # Check for file uploads
        has_file_upload = any(
            op.request_body
            and any(
                "multipart/form-data" in content_type
                for content_type in op.request_body.content.keys()
            )
            for op in operations
        )
        if has_file_upload:
            imports.add_typing_import("IO")

        # Import types based on parameter schemas
        for op in operations:
            for param in op.parameters:
                ptype = schema_to_type(param)
                # Optional enrichment
                if not param.required:
                    imports.add_typing_import("Optional")
                # List types
                if ptype.startswith("List["):
                    imports.add_typing_import("List")
                    inner = ptype[5:-1]
                    if inner.startswith("Dict["):
                        imports.add_typing_import("Dict")
                        imports.add_typing_import("Any")
                    if inner in ("date", "datetime"):
                        imports.add_direct_import("datetime", inner)
                # Dict types
                elif ptype.startswith("Dict["):
                    imports.add_typing_import("Dict")
                    imports.add_typing_import("Any")
                # date/datetime
                elif ptype in ("date", "datetime"):
                    imports.add_direct_import("datetime", ptype)

        # Import model classes for response types
        for op in operations:
            for resp in op.responses:
                for mt, sch in resp.content.items():
                    if not resp.stream and "json" in mt.lower() and sch.name:
                        module = NameSanitizer.sanitize_module_name(sch.name)
                        cls = NameSanitizer.sanitize_class_name(sch.name)
                        imports.add_relative_import(f"..models.{module}", cls)

        return imports

    def emit(self, spec: IRSpec, output_dir: str) -> None:
        """Render endpoint client files per tag under <output_dir>/endpoints."""
        endpoints_dir = os.path.join(output_dir, "endpoints")
        os.makedirs(endpoints_dir, exist_ok=True)

        # Create __init__.py to make it a proper package with sanitized names
        init_path = os.path.join(endpoints_dir, "__init__.py")
        with open(init_path, "w") as f:
            # Determine tags, fallback to first path segment if no tags
            tag_set = set()
            for op in spec.operations:
                if op.tags:
                    tag_set.update(op.tags)
                else:
                    # Use default tag for untagged operations
                    tag_set.add(DEFAULT_TAG)
            tags = sorted(tag_set)
            # Prepare exports with sanitized class names
            exports = [
                NameSanitizer.sanitize_class_name(tag) + "Client" for tag in tags if tag
            ]
            if exports:
                exports_str = ", ".join(f'"{name}"' for name in exports)
                f.write(f"__all__ = [{exports_str}]\n\n")
                # Import all clients with sanitized module names
                for tag in tags:
                    module = NameSanitizer.sanitize_module_name(tag)
                    class_name = NameSanitizer.sanitize_class_name(tag) + "Client"
                    f.write(f"from .{module} import {class_name}\n")

        # Prepare templates for rendering
        method_tpl = ENDPOINT_METHOD_TEMPLATE
        class_tpl = CLASS_TEMPLATE

        # Generate client modules by tag
        for tag in tags:
            # Collect operations for this tag, using fallback when no tags
            ops = []
            for op in spec.operations:
                # Use default tag for untagged operations
                op_tags = op.tags if op.tags else [DEFAULT_TAG]
                if tag in op_tags:
                    ops.append(op)
            if not ops:
                continue

            # Collect all imports for this tag's operations
            imports = self._collect_imports(ops)

            # Generate methods via TemplateRenderer (sanitize class name in CLASS_TEMPLATE)
            methods: List[str] = []
            for op in ops:
                method_content = self.renderer.render(
                    method_tpl,
                    op=op,
                    get_param_type=self._get_param_type,
                )
                methods.append(method_content)

            # Generate class with methods
            class_content = self.renderer.render(
                class_tpl,
                tag=tag,
                methods="\n".join(methods),
            )

            # Combine imports and class to create final content
            content = imports.get_formatted_imports() + "\n\n" + class_content
            # Format code using Formatter
            file_content = self.formatter.format(content)
            # Sanitize filename
            file_name = NameSanitizer.sanitize_filename(tag)
            file_path = os.path.join(endpoints_dir, file_name)
            with open(file_path, "w") as f:
                f.write(file_content)
