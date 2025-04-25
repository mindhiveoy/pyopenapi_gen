"""Utilities for pyopenapi_gen.

This module contains utility classes and functions used across the code generation process.
"""

from typing import Dict, List, Set

import re
import keyword
from jinja2 import Environment


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
        self.relative_imports: Dict[str, Set[str]] = {}

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
        """Add relative import (from .x import y)."""
        if module not in self.relative_imports:
            self.relative_imports[module] = set()
        self.relative_imports[module].add(name)

    def has_import(self, module: str, name: str) -> bool:
        """Check if a specific import exists."""
        return module in self.imports and name in self.imports[module]

    def get_import_statements(self) -> List[str]:
        """Generate the import statements in the correct order."""
        statements: List[str] = []

        # Standard library imports first (sorted)
        if self.imports:
            for module in sorted(self.imports.keys()):
                names = sorted(self.imports[module])
                if len(names) == 1 and names[0] == module:
                    statements.append(f"import {module}")
                else:
                    names_str = ", ".join(sorted(names))
                    statements.append(f"from {module} import {names_str}")

        # Then direct imports
        if self.direct_imports:
            if statements:  # Add separator if we already have imports
                statements.append("")  # Empty line separator
            for module in sorted(self.direct_imports.keys()):
                names = sorted(self.direct_imports[module])
                names_str = ", ".join(names)
                statements.append(f"from {module} import {names_str}")

        # Finally relative imports
        if self.relative_imports:
            if statements:  # Add separator if we already have imports
                statements.append("")  # Empty line separator
            for module in sorted(self.relative_imports.keys()):
                names = sorted(self.relative_imports[module])
                names_str = ", ".join(names)
                statements.append(f"from {module} import {names_str}")

        return statements

    def get_formatted_imports(self) -> str:
        """Return the import statements as a formatted string."""
        return "\n".join(self.get_import_statements())


class NameSanitizer:
    """Helper to sanitize spec names into valid Python identifiers and filenames."""

    @staticmethod
    def sanitize_module_name(name: str) -> str:
        """Convert a raw name into a valid Python module name in snake_case."""
        # Replace non-alphanumeric characters with underscores
        module = re.sub(r"\W+", "_", name)
        # Strip leading/trailing underscores and lowercase
        module = module.strip("_").lower()
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
        # Split on non-word characters (underscores preserved)
        parts = re.split(r"\W+", name)
        # Capitalize first letter of each part
        cls_name = "".join(p[:1].upper() + p[1:] for p in parts if p)
        # If it starts with a digit, prefix with underscore
        if cls_name and cls_name[0].isdigit():
            cls_name = "_" + cls_name
        # Avoid Python keywords
        if keyword.iskeyword(cls_name):
            cls_name += "_"
        return cls_name

    @staticmethod
    def sanitize_filename(name: str, suffix: str = ".py") -> str:
        """Generate a valid Python filename from raw name in snake_case."""
        module = NameSanitizer.sanitize_module_name(name)
        return module + suffix


class ParamSubstitutor:
    """Helper for rendering path templates with path parameters."""

    @staticmethod
    def render_path(template: str, values: Dict[str, any]) -> str:
        """Replace placeholders in a URL path template using provided values."""
        rendered = template
        for key, val in values.items():
            rendered = rendered.replace(f"{{{key}}}", str(val))
        return rendered


class KwargsBuilder:
    """Builder for assembling HTTP request keyword arguments."""

    def __init__(self) -> None:
        self._kwargs: Dict[str, any] = {}

    def with_params(self, **params: any) -> "KwargsBuilder":
        """Add query parameters, skipping None values."""
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            self._kwargs["params"] = filtered
        return self

    def with_json(self, body: any) -> "KwargsBuilder":
        """Add a JSON body to the request."""
        self._kwargs["json"] = body
        return self

    def build(self) -> Dict[str, any]:
        """Return the assembled kwargs dictionary."""
        return self._kwargs


class TemplateRenderer:
    """Centralized Jinja2 template renderer with shared filters and globals."""

    def __init__(self) -> None:
        # Create a shared environment for all templates
        self.env = Environment(trim_blocks=True, lstrip_blocks=True)
        # Register sanitization filters
        self.env.filters["sanitize_module_name"] = NameSanitizer.sanitize_module_name

        # Register class name sanitization filter (custom Jinja version splits on underscores too)
        def jinja_sanitize_class(name: str) -> str:
            parts = re.split(r"[\W_]+", name)
            cls = "".join(p[:1].upper() + p[1:] for p in parts if p)
            if cls and cls[0].isdigit():
                cls = "_" + cls
            if keyword.iskeyword(cls):
                cls += "_"
            return cls

        self.env.filters["sanitize_class_name"] = jinja_sanitize_class
        # Register path rendering filter
        self.env.filters["render_path"] = ParamSubstitutor.render_path
        # Expose helpers and global functions
        self.env.globals["KwargsBuilder"] = KwargsBuilder
        self.env.globals["NameSanitizer"] = NameSanitizer
        self.env.globals["render_path"] = ParamSubstitutor.render_path

    def render(self, template_str: str, **context) -> str:
        """Render a template string with the shared environment."""
        template = self.env.from_string(template_str)
        return template.render(**context)


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
        if self._format_str and self._file_mode:
            try:
                return self._format_str(code, mode=self._file_mode)
            except Exception:
                # On any Black formatting error, return original code
                return code
        return code
