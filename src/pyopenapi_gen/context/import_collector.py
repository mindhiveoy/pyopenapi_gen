"""
ImportCollector: Manages imports for generated Python modules.

This module provides the ImportCollector class, which collects, organizes, and formats
import statements for Python modules. It supports various import styles, including standard,
direct, relative, and plain imports, with methods to add and query import statements.
"""

import logging
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Set

# Initialize module logger
logger = logging.getLogger(__name__)

# Standard library modules for _is_stdlib check
COMMON_STDLIB = {
    "typing",
    "os",
    "sys",
    "re",
    "json",
    "collections",
    "datetime",
    "enum",
    "pathlib",
    "abc",
    "contextlib",
    "functools",
    "itertools",
    "logging",
    "math",
    "decimal",
    "dataclasses",
    "asyncio",
    "tempfile",
    "subprocess",
    "textwrap",
}

# Stdlib modules that should prefer \'import module\' over \'from module import module\'
# when add_import(module, module) is called.
STDLIB_MODULES_PREFER_PLAIN_IMPORT_WHEN_NAME_MATCHES = {
    "os",
    "sys",
    "re",
    "json",
    "contextlib",
    "functools",
    "itertools",
    "logging",
    "math",
    "asyncio",
    "tempfile",
    "subprocess",
    "textwrap",
}


def _is_stdlib(module_name: str) -> bool:
    """Check if a module is part of the standard library."""
    top_level_module = module_name.split(".")[0]
    return module_name in sys.builtin_module_names or module_name in COMMON_STDLIB or top_level_module in COMMON_STDLIB


def make_relative_import(current_module_dot_path: str, target_module_dot_path: str) -> str:
    """Generate a relative import path string from current_module to target_module."""
    current_parts = current_module_dot_path.split(".")
    target_parts = target_module_dot_path.split(".")

    current_dir_parts = current_parts[:-1]

    # Calculate common prefix length (L) between current_dir_parts and the full target_parts
    L = 0
    while L < len(current_dir_parts) and L < len(target_parts) and current_dir_parts[L] == target_parts[L]:
        L += 1

    # Number of levels to go "up" from current_module's directory to the common ancestor with target.
    up_levels = len(current_dir_parts) - L

    # The remaining components of the target path, after this common prefix L.
    remaining_target_components = target_parts[L:]

    if up_levels == 0:
        # This means the common prefix L makes current_dir_parts a prefix of (or same as)
        # target_parts's directory structure portion.
        # Or, target is in a subdirectory of current_dir_parts[L-1]

        # Special case for importing a submodule from its parent package's __init__.py
        # e.g. current="pkg.sub" (representing pkg/sub/__init__.py), target="pkg.sub.mod"
        # Expected: ".mod"
        is_direct_package_import = len(current_parts) < len(target_parts) and target_module_dot_path.startswith(
            current_module_dot_path + "."
        )

        if is_direct_package_import:
            # current_parts = [pkg, sub], target_parts = [pkg, sub, mod]
            # We want target_parts after current_parts, i.e., [mod]
            final_suffix_parts = target_parts[len(current_parts) :]
        else:
            # General case for up_levels == 0.
            # e.g. current="pkg.mod1" (dir pkg), target="pkg.mod2" (dir pkg)
            # current_dir_parts=[pkg], target_parts=[pkg,mod2]. L=1 (for pkg).
            # up_levels = 1-1=0. remaining_target_components=target_parts[1:]=[mod2]. -> .mod2
            # e.g. current="pkg.mod1" (dir pkg), target="pkg.sub.mod2" (dir pkg.sub)
            # current_dir_parts=[pkg], target_parts=[pkg,sub,mod2]. L=1.
            # up_levels = 0. remaining_target_components=target_parts[1:]=[sub,mod2]. -> .sub.mod2
            final_suffix_parts = remaining_target_components

        return "." + ".".join(final_suffix_parts)
    else:  # up_levels >= 1
        # up_levels = 1 means one step up ("..")
        # up_levels = N means N steps up (N+1 dots)
        return ("." * (up_levels + 1)) + ".".join(remaining_target_components)


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
        # self.direct_imports: Dict[str, Set[str]] = {} # Removed
        # Relative imports like 'from .models import Pet'
        self.relative_imports: defaultdict[str, set[str]] = defaultdict(set)
        # Plain imports like 'import json'
        self.plain_imports: set[str] = set()

        # Path information for the current file, used by get_formatted_imports
        self._current_file_module_dot_path: Optional[str] = None
        self._current_file_package_root: Optional[str] = None
        self._current_file_core_pkg_name_for_abs: Optional[str] = None

    def reset(self) -> None:
        """Reset the collector to its initial empty state."""
        # Use ERROR level for reset to make it highly visible in logs if it's unexpected
        logger.error(
            f"[ImportCollector.reset] RESETTING ImportCollector. Current imports: {self.imports}, relative_imports: {self.relative_imports}, plain_imports: {self.plain_imports}"
        )
        self.imports.clear()
        self.relative_imports.clear()
        self.plain_imports.clear()
        self._current_file_module_dot_path = None
        self._current_file_package_root = None
        self._current_file_core_pkg_name_for_abs = None

    def set_current_file_context_for_rendering(
        self,
        current_module_dot_path: Optional[str],
        package_root: Optional[str],
        core_package_name_for_absolute_treatment: Optional[str],
    ) -> None:
        """Set the context for the current file, used by get_formatted_imports."""
        self._current_file_module_dot_path = current_module_dot_path
        self._current_file_package_root = package_root
        self._current_file_core_pkg_name_for_abs = core_package_name_for_absolute_treatment

    def add_import(self, module: str, name: str) -> None:
        """
        Add an import from a specific module.

        Args:
            module: The module to import from (e.g., "typing")
            name: The name to import (e.g., "List")
        """
        logger.debug(
            f"[ImportCollector.add_import] Called with: module='{module}', name='{name}'. Current self.imports: {self.imports}"
        )
        # If module and name are the same, and it's a stdlib module
        # that typically uses plain import style (e.g., "import os").
        if module == name and module in STDLIB_MODULES_PREFER_PLAIN_IMPORT_WHEN_NAME_MATCHES:
            logger.debug(
                f"[ImportCollector.add_import] Treating '{module}' as plain import due to matching name and stdlib rule."
            )
            self.add_plain_import(module)
        else:
            if module not in self.imports:
                logger.debug(
                    f"[ImportCollector.add_import] Module '{module}' not in self.imports. Initializing new set for it."
                )
                self.imports[module] = set()
            self.imports[module].add(name)
            logger.debug(
                f"[ImportCollector.add_import] Added '{name}' to self.imports['{module}']. New set for module: {self.imports[module]}. All self.imports: {self.imports}"
            )

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

    def has_import(self, module: str, name: Optional[str] = None) -> bool:
        """Check if a specific module or name within a module is already imported."""
        if name:
            # Check absolute/standard imports
            if module in self.imports and name in self.imports[module]:
                return True
            # Check relative imports
            if module in self.relative_imports and name in self.relative_imports[module]:
                return True
        else:
            # Check plain imports (e.g. "import os" where module="os", name=None)
            if module in self.plain_imports:
                return True

        return False

    def get_import_statements(self) -> List[str]:
        """
        Generates a list of import statement strings.
        Order: plain, standard (from x import y), relative (from .x import y).
        Uses path context set by `set_current_file_context_for_rendering`.
        """
        # Use internal state for path context
        current_module_dot_path_to_use = self._current_file_module_dot_path
        package_root_to_use = self._current_file_package_root
        core_package_name_to_use = self._current_file_core_pkg_name_for_abs

        standard_import_lines: List[str] = []

        for module_name, names_set in sorted(self.imports.items()):
            names = sorted(list(names_set))
            is_stdlib_module = _is_stdlib(module_name)

            is_core_module_to_be_absolute = False
            if core_package_name_to_use and (
                module_name.startswith(core_package_name_to_use + ".") or module_name == core_package_name_to_use
            ):
                is_core_module_to_be_absolute = True

            if is_core_module_to_be_absolute:
                import_statement = f"from {module_name} import {', '.join(names)}"
                standard_import_lines.append(import_statement)
            elif is_stdlib_module:
                import_statement = f"from {module_name} import {', '.join(names)}"
                standard_import_lines.append(import_statement)
            elif (
                current_module_dot_path_to_use
                and package_root_to_use
                and module_name.startswith(package_root_to_use + ".")
            ):
                try:
                    relative_module = make_relative_import(current_module_dot_path_to_use, module_name)
                    import_statement = f"from {relative_module} import {', '.join(names)}"
                    standard_import_lines.append(import_statement)
                except ValueError as e:
                    import_statement = f"from {module_name} import {', '.join(names)}"
                    standard_import_lines.append(import_statement)
            else:
                import_statement = f"from {module_name} import {', '.join(names)}"
                standard_import_lines.append(import_statement)

        plain_import_lines: List[str] = []
        for module in sorted(self.plain_imports):
            plain_import_lines.append(f"import {module}")

        filtered_relative_imports: defaultdict[str, set[str]] = defaultdict(set)
        for module, names_to_import in self.relative_imports.items():
            # A module from self.relative_imports always starts with '.' (e.g., ".models")
            # Include it unless it's a self-import relative to a known current_module_dot_path.
            is_self_import = current_module_dot_path_to_use is not None and module == current_module_dot_path_to_use
            if not is_self_import:
                filtered_relative_imports[module].update(names_to_import)

        relative_import_lines: List[str] = []
        for module, imported_names in sorted(filtered_relative_imports.items()):
            names_str = ", ".join(sorted(list(imported_names)))
            relative_import_lines.append(f"from {module} import {names_str}")

        import_lines: List[str] = (
            list(sorted(plain_import_lines)) + list(sorted(standard_import_lines)) + list(sorted(relative_import_lines))
        )
        return import_lines

    def get_formatted_imports(self) -> str:
        """
        Get all imports as a formatted string.

        Returns:
            A newline-separated string of import statements
        """
        statements: List[str] = []

        # Standard library imports first
        stdlib_modules = sorted([m for m in self.imports.keys() if _is_stdlib(m)])

        for module in stdlib_modules:
            names = sorted(self.imports[module])
            statements.append(f"from {module} import {', '.join(names)}")

        # Then third-party and app imports
        other_modules = sorted([m for m in self.imports.keys() if not _is_stdlib(m)])

        if stdlib_modules and other_modules:
            statements.append("")  # Add a blank line between stdlib and other imports

        for module in other_modules:
            names = sorted(self.imports[module])
            statements.append(f"from {module} import {', '.join(names)}")

        # Then plain imports
        if self.plain_imports:
            if statements:  # Add blank line if we have imports already
                statements.append("")

            for module in sorted(self.plain_imports):
                statements.append(f"import {module}")

        # Then relative imports
        if self.relative_imports and (stdlib_modules or other_modules or self.plain_imports):
            statements.append("")  # Add a blank line before relative imports

        for module in sorted(self.relative_imports.keys()):
            names = sorted(self.relative_imports[module])
            statements.append(f"from {module} import {', '.join(names)}")

        return "\n".join(statements)

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
        for module, names in other.relative_imports.items():
            if module not in self.relative_imports:
                self.relative_imports[module] = set()
            self.relative_imports[module].update(names)
        for module in other.plain_imports:
            self.plain_imports.add(module)
