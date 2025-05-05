"""Utilities for pyopenapi_gen.

This module contains utility classes and functions used across the code generation process.
"""

import keyword
import re
from typing import Any, Dict, List, Set
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ImportCollector:
    """Manages imports for generated Python modules.

    This class helps collect and organize imports in a structured way,
    ensuring consistency across all generated files.

    Example usage:
        imports = ImportCollector()
        imports.add_import("dataclasses", "dataclass")
        imports.add_typing_import("Optional")
        imports.add_typing_import("List")

        for statement in imports.get_import_statements():
            print(statement)
    """

    def __init__(self) -> None:
        # Standard imports (import x or from x import y)
        self.imports: Dict[str, Set[str]] = {}
        # Direct imports like 'from datetime import date'
        self.direct_imports: Dict[str, Set[str]] = {}
        # Relative imports like 'from .models import Pet'
        self.relative_imports: defaultdict[str, set[str]] = defaultdict(set)
        # Plain imports like 'import json'
        self.plain_imports: set[str] = set()

    def add_import(self, module: str, name: str) -> None:
        """Add an import from a specific module."""
        if module not in self.imports:
            self.imports[module] = set()
        self.imports[module].add(name)

    def add_imports(self, module: str, names: List[str]) -> None:
        """Add multiple imports from a module."""
        for name in names:
            self.add_import(module, name)

    def add_typing_import(self, name: str) -> None:
        """Shortcut for adding typing imports."""
        self.add_import("typing", name)

    def add_direct_import(self, module: str, name: str) -> None:
        """Add direct import (from x import y)."""
        if module not in self.direct_imports:
            self.direct_imports[module] = set()
        self.direct_imports[module].add(name)

    def add_relative_import(self, module: str, name: str) -> None:
        """Add a relative import module and name."""
        # <<< DEBUG PRINT >>>
        print(f"DEBUG [add_relative_import]: Adding module='{module}', name='{name}'")
        # <<< END DEBUG >>>
        if module not in self.relative_imports:
            self.relative_imports[module] = set()
        self.relative_imports[module].add(name)

    def add_plain_import(self, module: str) -> None:
        """Add a plain import (import x)."""
        self.plain_imports.add(module)

    def has_import(self, module: str, name: str) -> bool:
        """Check if a specific import exists."""
        return module in self.imports and name in self.imports[module]

    def get_import_statements(self, current_module_path: str | None = None) -> list[str]:
        """Generate import statements, potentially filtering relative imports."""
        import_lines = []

        # Standard imports (absolute)
        standard_import_lines = []
        for module, names in sorted(self.imports.items()):
            names_str = ", ".join(sorted(list(names)))
            standard_import_lines.append(f"from {module} import {names_str}")

        # Plain imports
        plain_import_lines = []
        for module in sorted(self.plain_imports):
            plain_import_lines.append(f"import {module}")

        # Relative imports
        relative_import_lines = []
        # print(f"DEBUG [get_import_statements]: Processing relative imports for {current_module_path}") # DEBUG REMOVE
        # print(f"DEBUG [get_import_statements]: Raw relative_imports dict: {self.relative_imports}") # DEBUG REMOVE

        filtered_relative_imports = defaultdict(set)
        for module, names in self.relative_imports.items():
            if not module.startswith(".") or module != current_module_path:
                filtered_relative_imports[module].update(names)

        for module, names in sorted(filtered_relative_imports.items()):
            names_str = ", ".join(sorted(list(names)))
            # ----> Add print right before formatting <----
            print(
                f"DEBUG [get_import_statements]: Formatting relative import: module='{module}', names='{names_str}'"
            )  # ADD THIS
            relative_import_lines.append(f"from {module} import {names_str}")

        # print(f"DEBUG [get_import_statements]: Generated relative import lines: {relative_import_lines}") # DEBUG REMOVE

        # Combine and sort imports according to PEP 8 recommendations (stdlib, third-party, local)
        # Note: This simple sorting might not perfectly adhere to PEP 8 grouping.
        import_lines = sorted(plain_import_lines) + sorted(standard_import_lines) + sorted(relative_import_lines)

        # Add future import for annotations if needed (typically handled by CodeWriter)
        # if self.needs_future_annotations:
        #     import_lines.insert(0, "from __future__ import annotations")

        return import_lines

    def get_formatted_imports(self) -> str:
        """Return the import statements as a formatted string."""
        # <<< DEBUG PRINT >>>
        # Temporarily add print to check internal state just before formatting
        # print(f"DEBUG [get_formatted_imports]: Raw self.imports = {self.imports}") # COMMENTED
        # print(f"DEBUG [get_formatted_imports]: Raw self.relative_imports = {self.relative_imports}") # COMMENTED
        # print(f"DEBUG [get_formatted_imports]: Raw self.plain_imports = {self.plain_imports}") # COMMENTED
        # <<< END DEBUG >>>
        return "\n".join(self.get_import_statements())

    def merge(self, other: "ImportCollector") -> None:
        """Merge imports from another ImportCollector instance."""
        for module, names in other.imports.items():
            if module not in self.imports:
                self.imports[module] = set()
            self.imports[module].update(names)
        for module, names in other.direct_imports.items():
            if module not in self.direct_imports:
                self.direct_imports[module] = set()
            self.direct_imports[module].update(names)
        for module, names in other.relative_imports.items():
            if module not in self.relative_imports:
                self.relative_imports[module] = set()
            self.relative_imports[module].update(names)


class NameSanitizer:
    """Helper to sanitize spec names and tags into valid Python identifiers and filenames."""

    @staticmethod
    def sanitize_module_name(name: str) -> str:
        """Convert a raw name into a valid Python module name in snake_case, splitting camel case and PascalCase."""
        # # <<< Add Check for problematic input >>>
        # if '[' in name or ']' in name or ',' in name:
        #     logger.error(f"sanitize_module_name received potentially invalid input: '{name}'")
        #     # Optionally, return a default/error value or raise exception
        #     # For now, just log and continue
        # # <<< End Check >>>

        # Split on non-alphanumeric and camel case boundaries
        words = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", name)
        if not words:
            # fallback: split on non-alphanumerics
            words = re.split(r"\W+", name)
        module = "_".join(word.lower() for word in words if word)
        # If it starts with a digit, prefix with underscore
        if module and module[0].isdigit():
            module = "_" + module
        # Avoid Python keywords
        if keyword.iskeyword(module):
            module += "_"
        return module

    @staticmethod
    def sanitize_class_name(name: str) -> str:
        """Convert a raw name into a valid Python class name in PascalCase."""
        # Split on non-word characters and underscores
        parts = re.split(r"[\W_]+", name)
        # Capitalize first letter of each part
        cls_name = "".join(p[:1].upper() + p[1:] for p in parts if p)
        # If it starts with a digit, prefix with underscore
        if cls_name and cls_name[0].isdigit():
            cls_name = "_" + cls_name
        # Avoid Python keywords (case-insensitive)
        if keyword.iskeyword(cls_name.lower()):
            cls_name += "_"
        return cls_name

    @staticmethod
    def sanitize_tag_class_name(tag: str) -> str:
        """Sanitize a tag for use as a PascalCase client class name (e.g., DataSourcesClient)."""
        words = re.split(r"[\W_]+", tag)
        return "".join(word.capitalize() for word in words if word) + "Client"

    @staticmethod
    def sanitize_tag_attr_name(tag: str) -> str:
        """Sanitize a tag for use as a snake_case attribute name (e.g., data_sources)."""
        attr = re.sub(r"[\W]+", "_", tag).lower()
        return attr.strip("_")

    @staticmethod
    def normalize_tag_key(tag: str) -> str:
        """Normalize a tag for case-insensitive uniqueness (e.g., datasources)."""
        return re.sub(r"[\W_]+", "", tag).lower()

    @staticmethod
    def sanitize_filename(name: str, suffix: str = ".py") -> str:
        """Generate a valid Python filename from raw name in snake_case."""
        module = NameSanitizer.sanitize_module_name(name)
        return module + suffix

    @staticmethod
    def sanitize_method_name(name: str) -> str:
        """Convert a raw name into a valid Python method name in snake_case, splitting camelCase and PascalCase."""
        # Remove curly braces
        name = re.sub(r"[{}]", "", name)
        # Split camelCase and PascalCase to snake_case
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        # Replace non-alphanumerics with underscores
        name = re.sub(r"[^0-9a-zA-Z_]", "_", name)
        # Lowercase and collapse multiple underscores
        name = re.sub(r"_+", "_", name).strip("_").lower()
        # If it starts with a digit, prefix with underscore
        if name and name[0].isdigit():
            name = "_" + name
        # Avoid Python keywords
        if keyword.iskeyword(name):
            name += "_"
        return name


class ParamSubstitutor:
    """Helper for rendering path templates with path parameters."""

    @staticmethod
    def render_path(template: str, values: Dict[str, Any]) -> str:
        """Replace placeholders in a URL path template using provided values."""
        rendered = template
        for key, val in values.items():
            rendered = rendered.replace(f"{{{key}}}", str(val))
        return rendered


class KwargsBuilder:
    """Builder for assembling HTTP request keyword arguments."""

    def __init__(self) -> None:
        self._kwargs: Dict[str, Any] = {}

    def with_params(self, **params: Any) -> "KwargsBuilder":
        """Add query parameters, skipping None values."""
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            self._kwargs["params"] = filtered
        return self

    def with_json(self, body: Any) -> "KwargsBuilder":
        """Add a JSON body to the request."""
        self._kwargs["json"] = body
        return self

    def build(self) -> Dict[str, Any]:
        """Return the assembled kwargs dictionary."""
        return self._kwargs


class Formatter:
    """Helper to format code using Black, falling back to unformatted content if Black is unavailable or errors."""

    def __init__(self) -> None:
        try:
            from black import FileMode, format_str

            # Initialize Black formatter
            self._file_mode = FileMode()
            self._format_str = format_str
        except ImportError:
            self._file_mode = None  # type: ignore[assignment]
            self._format_str = None  # type: ignore[assignment]

    def format(self, code: str) -> str:
        """Format the given code string with Black if possible."""
        if self._format_str is not None and self._file_mode is not None:
            try:
                return self._format_str(code, mode=self._file_mode)
            except Exception:
                # On any Black formatting error, return original code
                return code
        return code
