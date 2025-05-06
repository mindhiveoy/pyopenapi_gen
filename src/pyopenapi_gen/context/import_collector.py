"""
ImportCollector: Manages imports for generated Python modules.

This module provides the ImportCollector class, which collects, organizes, and formats
import statements for Python modules. It supports various import styles, including standard,
direct, relative, and plain imports, with methods to add and query import statements.
"""

import sys
import os
from collections import defaultdict
from typing import Dict, List, Set, Optional
import logging

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
        # This means the common prefix L makes current_dir_parts a prefix of (or same as) target_parts's directory structure portion.
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

    def get_import_statements(
        self,
        current_module_dot_path: Optional[str] = None,
        package_root: Optional[str] = None,
        core_package_name_for_absolute_treatment: Optional[str] = None,
    ) -> List[str]:
        """
        Generates a list of import statement strings.
        Order: plain, standard (from x import y), relative (from .x import y).
        Relative imports are generated if current_module_dot_path and package_root are provided.
        Core package imports are treated as absolute if core_package_name_for_absolute_treatment is provided.
        """
        logger.debug(
            f"[ImportCollector] get_import_statements called. Current module: {current_module_dot_path}, Package root: {package_root}, Core pkg for abs: {core_package_name_for_absolute_treatment}"
        )
        logger.debug(f"[ImportCollector] Raw self.imports: {self.imports}")
        standard_import_lines: List[str] = []

        for module_name, names_set in sorted(self.imports.items()):
            names = sorted(list(names_set))
            is_stdlib_module = _is_stdlib(module_name)
            logger.debug(
                f"[ImportCollector] Processing module: '{module_name}', names: {names}, is_stdlib: {is_stdlib_module}"
            )

            is_core_module_to_be_absolute = False
            if core_package_name_for_absolute_treatment and (
                module_name.startswith(core_package_name_for_absolute_treatment + ".")
                or module_name == core_package_name_for_absolute_treatment
            ):
                is_core_module_to_be_absolute = True

            logger.debug(
                f"[ImportCollector] For '{module_name}', is_core_module_to_be_absolute: {is_core_module_to_be_absolute}"
            )

            if is_core_module_to_be_absolute:
                import_statement = f"from {module_name} import {', '.join(names)}"
                logger.debug(f"[ImportCollector] -> Core/Absolute import: {import_statement}")
            elif is_stdlib_module:
                import_statement = f"from {module_name} import {', '.join(names)}"
                logger.debug(f"[ImportCollector] -> StdLib/Absolute import: {import_statement}")
            elif current_module_dot_path and package_root and module_name.startswith(package_root + "."):
                try:
                    relative_module = make_relative_import(current_module_dot_path, module_name)
                    import_statement = f"from {relative_module} import {', '.join(names)}"
                    logger.debug(f"[ImportCollector] -> Relative import: {import_statement}")
                except ValueError as e:
                    import_statement = f"from {module_name} import {', '.join(names)}"
                    logger.warning(
                        f"[ImportCollector] Failed to make '{module_name}' relative to '{current_module_dot_path}', using absolute. Error: {e}"
                    )
            else:
                import_statement = f"from {module_name} import {', '.join(names)}"
                logger.debug(
                    f"[ImportCollector] -> Fallback/Absolute import: {import_statement} (current_path: {current_module_dot_path}, pkg_root: {package_root}, mod_starts_pkg_root: {module_name.startswith(package_root + '.') if package_root else False})"
                )

            standard_import_lines.append(import_statement)

        plain_import_lines: List[str] = []
        for module in sorted(self.plain_imports):
            plain_import_lines.append(f"import {module}")

        filtered_relative_imports: defaultdict[str, set[str]] = defaultdict(set)
        for module, names_to_import in self.relative_imports.items():
            # A module from self.relative_imports always starts with '.' (e.g., ".models")
            # Include it unless it's a self-import relative to a known current_module_dot_path.
            is_self_import = current_module_dot_path is not None and module == current_module_dot_path
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
        for module, names in other.relative_imports.items():
            if module not in self.relative_imports:
                self.relative_imports[module] = set()
            self.relative_imports[module].update(names)
        for module in other.plain_imports:
            self.plain_imports.add(module)
