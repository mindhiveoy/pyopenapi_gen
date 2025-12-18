"""Generator for @overload signatures when operations have multiple content types."""

import logging
from typing import Any

from pyopenapi_gen import IROperation

from ....context.render_context import RenderContext
from ....core.utils import NameSanitizer
from ....core.writers.code_writer import CodeWriter
from ..processors.parameter_processor import EndpointParameterProcessor
from .docstring_generator import EndpointDocstringGenerator
from .signature_generator import EndpointMethodSignatureGenerator

logger = logging.getLogger(__name__)


class OverloadMethodGenerator:
    """
    Generates @overload signatures for operations with multiple content types.

    When an operation's request body accepts multiple content types
    (e.g., application/json and multipart/form-data), this generator creates
    type-safe @overload signatures following PEP 484.
    """

    def __init__(self, schemas: dict[str, Any] | None = None) -> None:
        self.schemas = schemas or {}
        self.parameter_processor = EndpointParameterProcessor(self.schemas)
        self.signature_generator = EndpointMethodSignatureGenerator(self.schemas)
        self.docstring_generator = EndpointDocstringGenerator(self.schemas)

    def has_multiple_content_types(self, op: IROperation) -> bool:
        """
        Check if operation request body has multiple content types.

        Args:
            op: The operation to check

        Returns:
            True if operation has request body with multiple content types
        """
        if not op.request_body:
            return False
        return len(op.request_body.content) > 1

    def generate_overload_signatures(
        self, op: IROperation, context: RenderContext, response_strategy: Any
    ) -> list[str]:
        """
        Generate @overload signatures for each content type.

        Args:
            op: The operation with multiple content types
            context: Render context for import tracking
            response_strategy: Response strategy for return type resolution

        Returns:
            List of @overload signature code strings
        """
        if not self.has_multiple_content_types(op):
            return []

        # Ensure typing.overload is imported
        context.add_import("typing", "overload")
        context.add_import("typing", "Literal")
        context.add_import("typing", "IO")
        context.add_import("typing", "Any")

        overload_signatures = []

        # Type narrowing: request_body is guaranteed to exist by has_multiple_content_types check
        assert (
            op.request_body is not None
        ), "request_body should not be None after has_multiple_content_types check"  # nosec B101 - Type narrowing for mypy, validated by has_multiple_content_types

        for content_type, schema in op.request_body.content.items():
            signature_code = self._generate_single_overload(op, content_type, schema, context, response_strategy)
            overload_signatures.append(signature_code)

        return overload_signatures

    def _generate_single_overload(
        self,
        op: IROperation,
        content_type: str,
        schema: Any,
        context: RenderContext,
        response_strategy: Any,
    ) -> str:
        """
        Generate a single @overload signature for one content type.

        Args:
            op: The operation
            content_type: The media type (e.g., "application/json")
            schema: The schema for this content type
            context: Render context
            response_strategy: Response strategy for return type

        Returns:
            @overload signature code as string
        """
        writer = CodeWriter()

        # Write @overload decorator
        writer.write_line("@overload")

        # Determine parameter name and type based on content type
        param_info = self._get_content_type_param_info(content_type, schema, context)

        # Build parameter list from operation parameters directly
        param_parts = ["self"]

        # Add path, query, and header parameters from operation
        if op.parameters:
            from ....types.services.type_service import UnifiedTypeService

            type_service = UnifiedTypeService(self.schemas)

            for param in op.parameters:
                if param.param_in in ("path", "query", "header"):
                    param_type = type_service.resolve_schema_type(param.schema, context, required=param.required)
                    sanitized_name = NameSanitizer.sanitize_method_name(param.name)
                    param_parts.append(f"{sanitized_name}: {param_type}")

        # Add keyword-only separator
        param_parts.append("*")

        # Add content-type-specific parameter
        param_parts.append(f"{param_info['name']}: {param_info['type']}")

        # Add content_type parameter with Literal type
        param_parts.append(f'content_type: Literal["{content_type}"] = "{content_type}"')

        # Get return type from response strategy
        return_type = response_strategy.return_type

        # Sanitize method name to snake_case
        method_name = NameSanitizer.sanitize_method_name(op.operation_id)

        # Write signature
        params_str = ",\n    ".join(param_parts)
        writer.write_line(f"async def {method_name}(")
        writer.indent()
        writer.write_line(params_str)
        writer.dedent()
        writer.write_line(f") -> {return_type}: ...")

        return writer.get_code()

    def _get_content_type_param_info(self, content_type: str, schema: Any, context: RenderContext) -> dict[str, str]:
        """
        Get parameter name and type hint for a content type.

        Args:
            content_type: Media type string
            schema: Schema for this content type
            context: Render context for type resolution

        Returns:
            Dictionary with 'name' and 'type' keys
        """
        from ....types.services.type_service import UnifiedTypeService

        type_service = UnifiedTypeService(self.schemas)

        # Map content types to parameter names and base types
        if content_type == "application/json":
            # For JSON, resolve the actual schema type
            type_hint = type_service.resolve_schema_type(schema, context, required=True)
            return {"name": "body", "type": type_hint}

        elif content_type == "multipart/form-data":
            # For multipart, always use files dict
            return {"name": "files", "type": "dict[str, IO[Any]]"}

        elif content_type == "application/x-www-form-urlencoded":
            # For form data, use dict
            return {"name": "data", "type": "dict[str, str]"}

        else:
            # Default: use body with Any type
            logger.warning(f"Unknown content type {content_type}, using body: Any")
            return {"name": "body", "type": "Any"}

    def generate_implementation_signature(self, op: IROperation, context: RenderContext, response_strategy: Any) -> str:
        """
        Generate the actual implementation method signature with optional parameters.

        This signature accepts all possible content-type parameters as optional,
        and includes runtime dispatch logic.

        Args:
            op: The operation
            context: Render context
            response_strategy: Response strategy for return type

        Returns:
            Implementation method signature code
        """
        writer = CodeWriter()

        # Build parameter list
        param_parts = ["self"]

        # Add path, query, and header parameters from operation
        if op.parameters:
            from ....types.services.type_service import UnifiedTypeService

            type_service = UnifiedTypeService(self.schemas)

            for param in op.parameters:
                if param.param_in in ("path", "query", "header"):
                    param_type = type_service.resolve_schema_type(param.schema, context, required=param.required)
                    sanitized_name = NameSanitizer.sanitize_method_name(param.name)
                    param_parts.append(f"{sanitized_name}: {param_type}")

        # Add keyword-only separator
        param_parts.append("*")

        # Add all possible content-type parameters as optional
        if op.request_body:
            param_types_seen = set()

            for content_type, schema in op.request_body.content.items():
                param_info = self._get_content_type_param_info(content_type, schema, context)

                # Avoid duplicate parameters (e.g., if multiple JSON variants)
                param_key = param_info["name"]
                if param_key not in param_types_seen:
                    param_parts.append(f"{param_info['name']}: {param_info['type']} | None = None")
                    param_types_seen.add(param_key)

        # Add content_type parameter (no Literal, just str)
        param_parts.append('content_type: str = "application/json"')

        # Get return type
        return_type = response_strategy.return_type

        # Sanitize method name to snake_case
        method_name = NameSanitizer.sanitize_method_name(op.operation_id)

        # Write signature
        params_str = ",\n    ".join(param_parts)
        writer.write_line(f"async def {method_name}(")
        writer.indent()
        writer.write_line(params_str)
        writer.dedent()
        writer.write_line(f") -> {return_type}:")

        return writer.get_code()
