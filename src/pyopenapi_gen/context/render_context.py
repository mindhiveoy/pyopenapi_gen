"""
RenderContext: Central context manager for Python code generation.

This module provides the RenderContext class, which serves as the central state
management object during code generation. It tracks imports, generated modules,
and the current file being processed, ensuring proper relative/absolute import
handling and maintaining consistent state across the generation process.
"""

import logging
import os
import re
import sys
from typing import Optional, Set

from .file_manager import FileManager
from .import_collector import ImportCollector

logger = logging.getLogger(__name__)


class RenderContext:
    """
    Central context manager for tracking state during code generation.
    
    This class serves as the primary state container during code generation,
    managing imports, tracking generated modules, and calculating import paths.
    All imports are stored as absolute (package-root-relative) module paths internally
    and converted to appropriate relative or absolute imports at render time.
    
    Attributes:
        file_manager: Utility for writing files to disk
        import_collector: Manages imports for the current file being rendered
        generated_modules: Set of absolute paths to modules generated in this run
        current_file: Absolute path of the file currently being rendered
        core_package: Name of the core package (for imports)
        core_import_path: Import path to the core package
        package_root: Root directory of the package being generated
    """

    def __init__(
        self,
        file_manager: Optional[FileManager] = None,
        core_package: str = "core",
        core_import_path: Optional[str] = None,
        package_root: Optional[str] = None,
    ) -> None:
        """
        Initialize a new RenderContext.
        
        Args:
            file_manager: Utility for file operations (defaults to a new FileManager)
            core_package: Name of the core package (defaults to "core")
            core_import_path: Import path to the core package (optional)
            package_root: Root directory of the package being generated (optional)
        """
        self.file_manager = file_manager or FileManager()
        self.import_collector = ImportCollector()
        self.generated_modules: Set[str] = set()  # abs_module_paths of generated files
        self.current_file: Optional[str] = None  # abs path of file being rendered
        self.core_package: str = core_package
        self.core_import_path: Optional[str] = core_import_path
        self.package_root: Optional[str] = package_root

    def set_current_file(self, abs_path: str) -> None:
        """
        Set the absolute path of the file currently being rendered.
        
        This method also resets the import collector to ensure import isolation
        between different generated files.
        
        Args:
            abs_path: The absolute path of the file to set as current
        """
        self.current_file = abs_path
        # Reset the import collector for each new file to ensure isolation
        self.import_collector = ImportCollector()

    def add_import(self, logical_module: str, name: str) -> None:
        """
        Add an import to the collector, automatically determining if it should be relative.
        
        This method adds an import to the current file's import collector, calculating
        whether it should be a relative import (for modules within the generated package)
        or an absolute import (for external/stdlib modules).
        
        Args:
            logical_module: The logical module path to import from (e.g., "typing", "core.http_transport")
            name: The name to import from the module
        """
        if not logical_module:
            logger.error(f"Attempted to add import with empty module for name: {name}")
            return

        # Simple check for stdlib/built-in modules
        is_stdlib_or_builtin = logical_module in sys.builtin_module_names or (
            "." not in logical_module and logical_module not in self.generated_modules
        )

        if is_stdlib_or_builtin:
            # Use absolute import for stdlib/built-in modules
            self.import_collector.add_import(module=logical_module, name=name)
            return

        logger.debug(
            f"[add_import] Attempting import: logical='{logical_module}', name='{name}', current='{self.current_file}', root='{self.package_root}'"
        )

        # Calculate relative path for internal modules
        relative_module_path = self.calculate_relative_path(logical_module)
        logger.debug(
            f"[add_import] calculate_relative_path result for '{logical_module}': {relative_module_path}"
        )

        if relative_module_path:
            # Use relative import for modules within the generated package
            self.import_collector.add_relative_import(module=relative_module_path, name=name)
        else:
            # Fallback to absolute import if relative path calculation fails
            logger.warning(
                f"Could not calculate relative path for '{logical_module}' from '{self.current_file}'. "
                f"Falling back to absolute path (may cause issues)."
            )
            self.import_collector.add_import(module=logical_module, name=name)

    def mark_generated_module(self, abs_module_path: str) -> None:
        """
        Mark a module as being generated in the current run.
        
        This helps track which modules are part of the current generation
        process, which is important for determining import paths.
        
        Args:
            abs_module_path: The absolute path of the module file
        """
        self.generated_modules.add(abs_module_path)

    def render_imports(self) -> str:
        """
        Render all imports for the current file as a formatted string.
        
        Returns:
            A newline-separated string of import statements
        """
        return self.import_collector.get_formatted_imports()

    def add_typing_imports_for_type(self, type_str: str) -> None:
        """
        Add imports for all typing types found in a type string.
        
        This method analyzes a type string (e.g., "Optional[List[str]]") and
        automatically adds imports for any typing types it contains (e.g., "Optional", "List").
        It uses regex pattern matching to identify potential typing types.
        
        Args:
            type_str: The type string to analyze for typing imports
        """
        # Allowlist of typing types to import
        typing_types = {
            "List",
            "Optional",
            "Dict",
            "Set",
            "Tuple",
            "Union",
            "Any",
            "AsyncIterator",
            "Iterator",
            "Sequence",
            "Mapping",
            "Type",
            "Literal",
            "TypedDict",
            "DefaultDict",
            "Deque",
            "Counter",
            "ChainMap",
            "NoReturn",
            "Generator",
            "Awaitable",
            "Callable",
            "Protocol",
            "runtime_checkable",
            "Self",
            "ClassVar",
            "Final",
            "Required",
            "NotRequired",
            "Annotated",
            "TypeGuard",
            "SupportsIndex",
            "SupportsAbs",
            "SupportsBytes",
            "SupportsComplex",
            "SupportsFloat",
            "SupportsInt",
            "SupportsRound",
        }
        
        # Regex: match all capitalized identifiers, which could be typing types
        matches = re.findall(r"\b([A-Z][A-Za-z0-9_]*)\b", type_str)
        
        # Add imports for any matches that are in our typing_types allowlist
        for match in set(matches):
            if match in typing_types:
                self.import_collector.add_typing_import(match)

    def add_plain_import(self, module: str) -> None:
        """
        Add a plain import (import x) to the current file's import collector.
        
        Args:
            module: The module to import
        """
        self.import_collector.add_plain_import(module)

    def calculate_relative_path(self, target_logical_module: str) -> str | None:
        """
        Calculate the relative Python import path from the current file to the target module.
        
        This method converts a logical module path into a proper relative import path
        that can be used in the current file. It handles calculating the correct number
        of dot prefixes and path segments based on the filesystem structure.

        Args:
            target_logical_module: The dot-separated logical module path relative to the package root
                                   (e.g., 'core.http_transport', 'endpoints.users')

        Returns:
            The relative import string (e.g., '.core.http_transport', '..models.user')
            or None if calculation is not possible or not applicable
        """
        if not self.current_file or not self.package_root:
            logger.warning("Cannot calculate relative path: current_file or package_root is not set.")
            return None

        # Convert logical module path to absolute file path
        target_parts = target_logical_module.split(".")
        target_file_rel_path = os.path.join(*target_parts) + ".py"
        target_abs_path = os.path.abspath(os.path.join(self.package_root, target_file_rel_path))

        current_dir = os.path.dirname(os.path.abspath(self.current_file))

        try:
            # Calculate the relative path from the current file to the target
            relative_file_path = os.path.relpath(target_abs_path, start=current_dir)
        except ValueError:
            logger.warning(f"Could not calculate relpath between {current_dir} and {target_abs_path}")
            return None

        # Remove .py extension if present
        if relative_file_path.endswith(".py"):
            relative_file_path = relative_file_path[:-3]

        # Cannot import from the same file
        if not relative_file_path:
            logger.error(f"Cannot import from the same file: {self.current_file}")
            return None

        # Convert file system path to Python import path
        parts = relative_file_path.split(os.sep)
        level = 0
        
        # Count parent directory traversals
        while parts and parts[0] == os.pardir:
            parts.pop(0)
            level += 1

        # Construct the final relative import path
        if level == 0:
            # Same directory import
            relative_module_path = "." + ".".join(parts)
        else:
            # Parent directory import
            leading_dots = "." * level
            if parts:
                relative_module_path = leading_dots + "." + ".".join(parts)
            else:
                relative_module_path = leading_dots

        return relative_module_path
