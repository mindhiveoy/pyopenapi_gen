import os
import logging
from typing import Dict, List, Optional, Tuple, Any, Set

from pyopenapi_gen import IROperation, IRParameter, IRRequestBody, IRSpec
from pyopenapi_gen.context.render_context import RenderContext

logger = logging.getLogger(__name__)

from ..core.utils import Formatter, NameSanitizer
from ..visit.endpoint_visitor import EndpointVisitor

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
        item_type = schema_to_type(IRParameter(name="", param_in="", required=False, schema=s.items))
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

    def __init__(
        self,
        core_package: str = "core",
        overall_project_root: Optional[str] = None,
    ) -> None:
        self.formatter = Formatter()
        self.visitor: EndpointVisitor = None  # type: ignore
        self.core_package = core_package
        self.overall_project_root = overall_project_root
        
    def _deduplicate_operation_ids(self, operations: List[IROperation]) -> None:
        """
        Ensures all operations have unique method names within a tag.
        
        Args:
            operations: List of operations for a single tag.
        """
        # Track sanitized method names
        seen_methods: Dict[str, int] = {}
        
        for op in operations:
            # Get the sanitized method name
            method_name = NameSanitizer.sanitize_method_name(op.operation_id)
            
            # If this method name already exists
            if method_name in seen_methods:
                # Increment the counter for this name
                seen_methods[method_name] += 1
                
                # Create a new unique operation ID with suffix
                new_op_id = f"{op.operation_id}_{seen_methods[method_name]}"
                
                # Log a warning about the duplicate
                logger.warning(
                    f"Duplicate operation ID detected: '{op.operation_id}' (sanitized to '{method_name}'). "
                    f"Renaming to '{new_op_id}'"
                )
                
                # Update the operation ID
                op.operation_id = new_op_id
            else:
                # First time seeing this method name
                seen_methods[method_name] = 1

    def emit(self, spec: IRSpec, output_dir: str) -> List[str]:
        """Render endpoint client files per tag under <output_dir>/endpoints using the visitor/context/registry
        pattern. Returns a list of generated file paths."""
        endpoints_dir = os.path.join(output_dir, "endpoints")
        context = RenderContext(
            core_package_name=self.core_package,
            package_root_for_generated_code=output_dir,
            overall_project_root=self.overall_project_root,
        )
        context.file_manager.ensure_dir(endpoints_dir)
        # Always create an empty __init__.py to ensure package
        empty_init_path = os.path.join(endpoints_dir, "__init__.py")
        if not os.path.exists(empty_init_path):
            context.file_manager.write_file(empty_init_path, "")
        # Ensure root __init__.py for output_dir
        root_init_path = os.path.join(output_dir, "__init__.py")
        if not os.path.exists(root_init_path):
            context.file_manager.write_file(root_init_path, "")
        # Ensure py.typed marker for mypy
        pytyped_path = os.path.join(endpoints_dir, "py.typed")
        if not os.path.exists(pytyped_path):
            context.file_manager.write_file(pytyped_path, "")

        # Always use schemas from the current spec
        if self.visitor is None:
            self.visitor = EndpointVisitor(spec.schemas)

        # Group operations by normalized tag key
        tag_key_to_ops: Dict[str, List[IROperation]] = {}
        tag_key_to_candidates: Dict[str, List[str]] = {}
        for op in spec.operations:
            tags = op.tags or [DEFAULT_TAG]
            for tag in tags:
                key = NameSanitizer.normalize_tag_key(tag)
                tag_key_to_ops.setdefault(key, []).append(op)
                tag_key_to_candidates.setdefault(key, []).append(tag)

        # For each normalized tag, pick a canonical tag (best formatted)
        def tag_score(t: str) -> tuple[bool, int, int, str]:
            import re

            is_pascal = bool(re.search(r"[a-z][A-Z]", t)) or bool(re.search(r"[A-Z]{2,}", t))
            words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+", t)
            words += re.split(r"[_-]+", t)
            word_count = len([w for w in words if w])
            upper = sum(1 for c in t if c.isupper())
            return (is_pascal, word_count, upper, t)

        tag_map = {}
        for key, candidates in tag_key_to_candidates.items():
            best = max(candidates, key=tag_score)
            tag_map[key] = best

        # Prepare context and mark all generated modules (one per normalized tag)
        for key, ops in tag_key_to_ops.items():
            tag = tag_map[key]
            module_name = NameSanitizer.sanitize_module_name(tag)
            file_path = os.path.join(endpoints_dir, f"{module_name}.py")
            context.mark_generated_module(file_path)

        generated_files: List[str] = []
        client_classes: List[Tuple[str, str]] = []
        # Generate endpoint files per canonical tag
        for key, ops in tag_key_to_ops.items():
            tag = tag_map[key]
            module_name = NameSanitizer.sanitize_module_name(tag)
            class_name = NameSanitizer.sanitize_class_name(tag) + "Client"
            file_path = os.path.join(endpoints_dir, f"{module_name}.py")
            context.set_current_file(file_path)
            
            # Ensure operations have unique method names
            self._deduplicate_operation_ids(ops)
            
            # Render all methods for this tag
            methods = [self.visitor.visit(op, context) for op in ops]
            # Compose class content
            class_content = self.visitor.emit_endpoint_client_class(tag, methods, context)

            # Render imports for this file
            imports = context.render_imports()

            # Write the file
            file_content = imports + "\n\n" + class_content
            # file_content = self.formatter.format(file_content)
            context.file_manager.write_file(file_path, file_content)
            client_classes.append((class_name, module_name))
            generated_files.append(file_path)

        # Deduplicate client classes by canonical name
        unique_clients = _deduplicate_tag_clients(client_classes)

        # Write __init__.py with __all__ and imports for all unique client classes
        init_lines = []
        if unique_clients:
            all_list = ", ".join(f'"{cls}"' for cls, _ in unique_clients)
            init_lines.append(f"__all__ = [{all_list}]")
            for cls, mod in unique_clients:
                init_lines.append(f"from .{mod} import {cls}")
        context.file_manager.write_file(os.path.join(endpoints_dir, "__init__.py"), "\n".join(init_lines) + "\n")
        generated_files.append(os.path.join(endpoints_dir, "__init__.py"))
        return generated_files
