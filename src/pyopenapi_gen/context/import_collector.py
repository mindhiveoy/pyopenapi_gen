from collections import defaultdict
from typing import Dict, List, Set  # Added Set
import logging

# Get logger
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
        # # <<< DEBUG PRINT -> If re-enabled, ensure logger or sys is available >>>
        # print(f"DEBUG [add_relative_import]: Adding module='{module}', name='{name}'", file=sys.stderr)
        # # <<< END DEBUG >>>
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

        # # +++ Add logging +++
        # logger.debug(f"get_import_statements CALLED. self.imports = {self.imports}")
        # logger.debug(f"  self.plain_imports = {self.plain_imports}")
        # logger.debug(f"  self.relative_imports = {self.relative_imports}")
        # # +++ End logging +++

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

        # The HACK related to "union_agent_response_dict_str_any" should be permanently removed
        # as the underlying issue was fixed.

        filtered_relative_imports = defaultdict(set)
        for module, names in self.relative_imports.items():
            if not module.startswith(".") or module != current_module_path:  # Condition from original utils.py
                filtered_relative_imports[module].update(names)

        for module, names in sorted(filtered_relative_imports.items()):
            names_str = ", ".join(sorted(list(names)))
            # # ----> Add print right before formatting <---- (If re-enabled, ensure logger or sys)
            # print(
            #     f"DEBUG [get_import_statements]: Formatting relative import: module='{module}', names='{names_str}'",
            #     file=sys.stderr
            # )
            relative_import_lines.append(f"from {module} import {names_str}")

        import_lines = sorted(plain_import_lines) + sorted(standard_import_lines) + sorted(relative_import_lines)
        return import_lines

    def get_formatted_imports(self) -> str:
        """Return the import statements as a formatted string."""
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
