import os
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path

from pyopenapi_gen import IROperation, IRParameter, IRRequestBody, IRSpec
from pyopenapi_gen.context.render_context import RenderContext

logger = logging.getLogger(__name__)

from ..core.utils import Formatter, NameSanitizer
from pyopenapi_gen.visit.endpoint.endpoint_visitor import EndpointVisitor

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

# Default tag for untagged operations
DEFAULT_TAG = "default"


def schema_to_type(schema: IRParameter) -> str:
    """Convert an IRParameter's schema to a Python type string."""
    s = schema.schema  # s is an IRSchema instance
    py_type: str = "Any"  # Default base type

    # 1. Determine base type (without Optional wrapper yet)
    # Format-specific override has highest precedence for base type determination
    if s.format and s.format in PARAM_FORMAT_MAPPING:
        py_type = PARAM_FORMAT_MAPPING[s.format]
    # Array handling
    elif s.type == "array" and s.items:
        # For array items, we recursively call schema_to_type.
        # The nullability of the item_type itself (e.g. List[Optional[int]])
        # will be handled by the recursive call based on s.items.is_nullable.
        item_schema_as_param = IRParameter(name="_item", param_in="_internal", required=False, schema=s.items)
        item_type_str = schema_to_type(item_schema_as_param)
        py_type = f"List[{item_type_str}]"
    # Default mapping based on s.type (primary type)
    elif s.type and s.type in PARAM_TYPE_MAPPING:
        py_type = PARAM_TYPE_MAPPING[s.type]
    # Fallback if type is None or not in mappings (and not format override/array)
    # If s.type is None and there was no format override, it defaults to "Any".
    # If s.type is something not recognized, it also defaults to "Any".
    elif not s.type and not s.format:  # Type is None, no format override
        py_type = "Any"
    elif s.type:  # Type is some string not in PARAM_TYPE_MAPPING and not an array handled above
        # This could be a reference to a model. For now, schema_to_type is simple and returns Any.
        # A more sophisticated version would return the schema name for model visitor to handle.
        # However, based on existing PARAM_TYPE_MAPPING, unknown types become "Any".
        py_type = "Any"
    # If py_type is still "Any" here, it means none of the above conditions strongly set a type.

    # 2. Apply nullability based on IRSchema's is_nullable field
    # This s.is_nullable should be the source of truth from the IR after parsing.
    if s.is_nullable:
        # Ensure "Any" also gets wrapped, e.g. Optional[Any]
        py_type = f"Optional[{py_type}]"

    return py_type


def _get_request_body_type(body: IRRequestBody) -> str:
    """Determine the Python type for a request body schema."""
    for mt, sch in body.content.items():
        if "json" in mt.lower():
            return schema_to_type(IRParameter(name="body", param_in="body", required=body.required, schema=sch))
    # Fallback to generic dict
    return "Dict[str, Any]"


def _deduplicate_tag_clients(client_classes: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """
    Deduplicate client class/module pairs by canonical module/class name.
    Returns a list of unique (class_name, module_name) pairs.
    """
    seen = set()
    unique = []
    for cls, mod in client_classes:
        key = (cls.lower(), mod.lower())
        if key not in seen:
            seen.add(key)
            unique.append((cls, mod))
    return unique


class EndpointsEmitter:
    """Generates endpoint modules organized by tag from IRSpec using the visitor/context architecture."""

    def __init__(self, context: RenderContext) -> None:
        self.context = context
        self.formatter = Formatter()
        self.visitor: Optional[EndpointVisitor] = None

    def _deduplicate_operation_ids(self, operations: List[IROperation]) -> None:
        """
        Ensures all operations have unique method names within a tag.

        Args:
            operations: List of operations for a single tag.
        """
        seen_methods: Dict[str, int] = {}
        for op in operations:
            method_name = NameSanitizer.sanitize_method_name(op.operation_id)
            if method_name in seen_methods:
                seen_methods[method_name] += 1
                new_op_id = f"{op.operation_id}_{seen_methods[method_name]}"
                op.operation_id = new_op_id
            else:
                seen_methods[method_name] = 1

    def emit(self, operations: List[IROperation], output_dir_str: str) -> List[str]:
        """Render endpoint client files per tag under <output_dir>/endpoints.
        Returns a list of generated file paths."""
        output_dir = Path(output_dir_str)
        endpoints_dir = output_dir / "endpoints"

        self.context.file_manager.ensure_dir(str(endpoints_dir))

        # Manage __init__.py and py.typed files
        common_files_to_ensure = [
            (endpoints_dir / "__init__.py", ""),
            (output_dir / "__init__.py", ""),  # Ensure root client package __init__.py
            (endpoints_dir / "py.typed", ""),
        ]
        for file_path, content in common_files_to_ensure:
            if not file_path.exists():
                self.context.file_manager.write_file(str(file_path), content)

        if not self.context.parsed_schemas:
            logger.error(
                "[EndpointsEmitter] RenderContext is missing parsed_schemas. Cannot initialize EndpointVisitor."
            )
            return []  # Or raise error

        if self.visitor is None:
            self.visitor = EndpointVisitor(self.context.parsed_schemas)

        tag_key_to_ops: Dict[str, List[IROperation]] = {}
        tag_key_to_candidates: Dict[str, List[str]] = {}
        for op in operations:
            tags = op.tags or [DEFAULT_TAG]
            for tag in tags:
                key = NameSanitizer.normalize_tag_key(tag)
                tag_key_to_ops.setdefault(key, []).append(op)
                tag_key_to_candidates.setdefault(key, []).append(tag)

        def tag_score(t: str) -> tuple[bool, int, int, str]:
            import re

            is_pascal = bool(re.search(r"[a-z][A-Z]", t)) or bool(re.search(r"[A-Z]{2,}", t))
            words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+", t)
            words += re.split(r"[_-]+", t)
            word_count = len([w for w in words if w])
            upper = sum(1 for c in t if c.isupper())
            return (is_pascal, word_count, upper, t)

        tag_map: Dict[str, str] = {}
        for key, candidates in tag_key_to_candidates.items():
            best_tag_for_key = DEFAULT_TAG  # Default if no candidates somehow
            if candidates:
                best_tag_for_key = max(candidates, key=tag_score)
            tag_map[key] = best_tag_for_key

        generated_files: List[str] = []
        client_classes: List[Tuple[str, str]] = []

        for key, ops_for_tag in tag_key_to_ops.items():
            canonical_tag_name = tag_map[key]
            module_name = NameSanitizer.sanitize_module_name(canonical_tag_name)
            class_name = NameSanitizer.sanitize_class_name(canonical_tag_name) + "Client"
            file_path = endpoints_dir / f"{module_name}.py"

            # This will set current_file and reset+reinit import_collector's context
            self.context.set_current_file(str(file_path))

            self._deduplicate_operation_ids(ops_for_tag)

            # EndpointVisitor must exist here due to check above
            assert self.visitor is not None, "EndpointVisitor not initialized"
            methods = [self.visitor.visit(op, self.context) for op in ops_for_tag]
            class_content = self.visitor.emit_endpoint_client_class(canonical_tag_name, methods, self.context)

            imports = self.context.render_imports()
            file_content = imports + "\n\n" + class_content
            self.context.file_manager.write_file(str(file_path), file_content)
            client_classes.append((class_name, module_name))
            generated_files.append(str(file_path))

        unique_clients = _deduplicate_tag_clients(client_classes)
        init_lines = []
        if unique_clients:
            all_list_items = sorted([f'"{cls}"' for cls, _ in unique_clients])
            init_lines.append(f"__all__ = [{', '.join(all_list_items)}]")
            for cls, mod in sorted(unique_clients):
                init_lines.append(f"from .{mod} import {cls}")

        endpoints_init_path = endpoints_dir / "__init__.py"
        self.context.file_manager.write_file(str(endpoints_init_path), "\n".join(init_lines) + "\n")
        if str(endpoints_init_path) not in generated_files:
            generated_files.append(str(endpoints_init_path))

        return generated_files
