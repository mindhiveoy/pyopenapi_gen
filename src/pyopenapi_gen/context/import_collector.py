"""
ImportCollector: Manages imports for generated Python modules.

This module provides the ImportCollector class, which collects, organizes, and formats
import statements for Python modules. It supports various import styles, including standard,
direct, relative, and plain imports, with methods to add and query import statements.
"""

from collections import defaultdict
from typing import Dict, List, Set
import logging

# Initialize module logger
logger = logging.getLogger(__name__)


class ImportCollector:
    """
    Manages imports for generated Python modules.
    
    This class collects and organizes imports in a structured way, ensuring
    consistency across all generated files. It provides methods to add different
    types of imports and generate properly formatted import statements.
    
    Attributes:
        imports: Dictionary mapping module names to sets of imported names
                (for standard imports like `from typing import List`)
        direct_imports: Dictionary for direct imports (similar to imports)
        relative_imports: Dictionary for relative imports (like `from .models import Pet`)
        plain_imports: Set of module names for plain imports (like `import json`)
    
    Example usage:
        imports = ImportCollector()
        imports.add_import("dataclasses", "dataclass")
        imports.add_typing_import("Optional")
        imports.add_typing_import("List")

        for statement in imports.get_import_statements():
            print(statement)
    """

    def __init__(self) -> None:
        """Initialize a new ImportCollector with empty collections for all import types."""
        # Standard imports (from x import y)
        self.imports: Dict[str, Set[str]] = {}
        # Direct imports like 'from datetime import date'
        self.direct_imports: Dict[str, Set[str]] = {}
        # Relative imports like 'from .models import Pet'
        self.relative_imports: defaultdict[str, set[str]] = defaultdict(set)
        # Plain imports like 'import json'
        self.plain_imports: set[str] = set()

    def add_import(self, module: str, name: str) -> None:
        """
        Add an import from a specific module.
        
        Args:
            module: The module to import from (e.g., "typing")
            name: The name to import (e.g., "List")
        """
        if module not in self.imports:
            self.imports[module] = set()
        self.imports[module].add(name)

    def add_imports(self, module: str, names: List[str]) -> None:
        """
        Add multiple imports from a module.
        
        Args:
            module: The module to import from
            names: List of names to import
        """
        for name in names:
            self.add_import(module, name)

    def add_typing_import(self, name: str) -> None:
        """
        Shortcut for adding typing imports.
        
        Args:
            name: The typing name to import (e.g., "List", "Optional")
        """
        self.add_import("typing", name)

    def add_direct_import(self, module: str, name: str) -> None:
        """
        Add direct import (from x import y).
        
        Args:
            module: The module to import from
            name: The name to import
        """
        if module not in self.direct_imports:
            self.direct_imports[module] = set()
        self.direct_imports[module].add(name)

    def add_relative_import(self, module: str, name: str) -> None:
        """
        Add a relative import module and name.
        
        Args:
            module: The relative module path (e.g., ".models")
            name: The name to import
        """
        if module not in self.relative_imports:
            self.relative_imports[module] = set()
        self.relative_imports[module].add(name)

    def add_plain_import(self, module: str) -> None:
        """
        Add a plain import (import x).
        
        Args:
            module: The module to import
        """
        self.plain_imports.add(module)

    def has_import(self, module: str, name: str) -> bool:
        """
        Check if a specific import exists.
        
        Args:
            module: The module to check
            name: The imported name to check
            
        Returns:
            True if the import exists, False otherwise
        """
        return module in self.imports and name in self.imports[module]

    def get_import_statements(self, current_module_path: str | None = None) -> list[str]:
        """
        Generate import statements, potentially filtering relative imports.
        
        This method generates properly formatted import statements for all
        registered imports, organized by type (plain, standard, relative)
        and sorted alphabetically.
        
        Args:
            current_module_path: Optional path of the current module, used to
                                filter out self-referential imports
            
        Returns:
            List of import statements as strings
        """
        # Standard imports (absolute)
        standard_import_lines = []
        for module, names in sorted(self.imports.items()):
            names_str = ", ".join(sorted(list(names)))
            standard_import_lines.append(f"from {module} import {names_str}")

        # Plain imports
        plain_import_lines = []
        for module in sorted(self.plain_imports):
            plain_import_lines.append(f"import {module}")

        # Relative imports - filter out self-referential imports
        filtered_relative_imports = defaultdict(set)
        for module, names in self.relative_imports.items():
            if not module.startswith(".") or module != current_module_path:
                filtered_relative_imports[module].update(names)

        # Format relative imports
        relative_import_lines = []
        for module, names in sorted(filtered_relative_imports.items()):
            names_str = ", ".join(sorted(list(names)))
            relative_import_lines.append(f"from {module} import {names_str}")

        # Combine all import lines in the proper order
        import_lines = sorted(plain_import_lines) + sorted(standard_import_lines) + sorted(relative_import_lines)
        return import_lines

    def get_formatted_imports(self) -> str:
        """
        Return the import statements as a formatted string.
        
        Returns:
            A newline-separated string of import statements
        """
        return "\n".join(self.get_import_statements())

    def merge(self, other: "ImportCollector") -> None:
        """
        Merge imports from another ImportCollector instance.
        
        This method combines all imports from the other collector into this one.
        
        Args:
            other: Another ImportCollector instance to merge imports from
        """
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
