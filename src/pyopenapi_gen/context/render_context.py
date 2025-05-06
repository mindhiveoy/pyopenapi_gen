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
    Context object for tracking imports, generated modules, and the current file during code generation.
    All imports are stored as absolute (package-root-relative) module paths internally.
    At render time, imports are emitted as relative or absolute depending on whether the target is a generated module
    or an external dependency.
    """

    def __init__(
        self,
        file_manager: Optional[FileManager] = None,
        core_package: str = "core",
        core_import_path: Optional[str] = None,
        package_root: Optional[str] = None,
    ):
        self.file_manager = file_manager or FileManager()
        self.import_collector = ImportCollector()
        self.generated_modules: Set[str] = set()  # abs_module_paths of generated files
        self.current_file: Optional[str] = None  # abs path of file being rendered
        self.core_package: str = core_package
        self.core_import_path: Optional[str] = core_import_path
        self.package_root: Optional[str] = package_root

    def set_current_file(self, abs_path: str) -> None:
        """Set the absolute path of the file currently being rendered."""
        self.current_file = abs_path
        # Reset the import collector for each new file to ensure isolation
        self.import_collector = ImportCollector()

    def add_import(self, logical_module: str, name: str) -> None:
        """Adds an import to the collector, calculating if it should be relative."""
        if not logical_module:
            logger.error(f"Attempted to add import with empty module for name: {name}")
            return

        # # <<< DEBUG PRINT >>>
        # print(f"DEBUG add_import: logical_module='{logical_module}', name='{name}', current_file='{self.current_file}'", file=sys.stderr)
        # # <<< END DEBUG >>>

        # Simple check for stdlib/built-in
        is_stdlib_or_builtin = logical_module in sys.builtin_module_names or (
            "." not in logical_module and logical_module not in self.generated_modules
        )

        if is_stdlib_or_builtin:
            # Use the correct method name: add_import
            self.import_collector.add_import(module=logical_module, name=name)
            return

        logger.debug(
            f"[add_import] Attempting import: logical='{logical_module}', name='{name}', current='{self.current_file}', root='{self.package_root}'"
        )  # DEBUG

        # Calculate relative path for internal modules
        relative_module_path = self.calculate_relative_path(logical_module)
        logger.debug(
            f"[add_import] calculate_relative_path result for '{logical_module}': {relative_module_path}"
        )  # DEBUG

        if relative_module_path:
            # Use relative import for modules within the generated package
            self.import_collector.add_relative_import(module=relative_module_path, name=name)
        else:
            # Fallback to absolute import if relative path calculation fails or is not applicable
            logger.error(
                f"[add_import ELSE BLOCK] Relative path failed for '{logical_module}' from '{self.current_file}'. Using absolute fallback."
            )  # DEBUG
            logger.warning(
                f"Could not calculate relative path for '{logical_module}' from '{self.current_file}'. "
                f"Falling back to absolute path (may cause issues)."
            )
            # Use the correct method name: add_import
            self.import_collector.add_import(module=logical_module, name=name)

    def mark_generated_module(self, abs_module_path: str) -> None:
        """Mark a module as being generated in this run (using abs module path)."""
        self.generated_modules.add(abs_module_path)

    def render_imports(self) -> str:
        """
        Render all imports for the current file using ImportCollector.
        """
        return self.import_collector.get_formatted_imports()

    def add_typing_imports_for_type(self, type_str: str) -> None:
        """
        Adds imports for all typing types present in a type string, e.g. Optional, List, Dict, Set, Tuple, Union, Any,
        AsyncIterator, etc. Uses regex to match both generic and non-generic usages, including Any inside generics.
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
        # Regex: match all capitalized identifiers from typing, optionally followed by [ or , or ]
        matches = re.findall(r"\b([A-Z][A-Za-z0-9_]*)\b", type_str)
        for match in set(matches):
            if match in typing_types:
                self.import_collector.add_typing_import(match)

    def add_plain_import(self, module: str) -> None:
        """Add a plain import (import x) to the current file's import collector."""
        self.import_collector.add_plain_import(module)

    def calculate_relative_path(self, target_logical_module: str) -> str | None:
        """
        Calculates the relative Python import path from the current file to the target module.

        Args:
            target_logical_module: The dot-separated logical module path relative to the package root
                                    (e.g., 'core.http_transport', 'endpoints.users').

        Returns:
            The relative import string (e.g., '.core.http_transport', '..models.user')
            or None if calculation is not possible or not applicable (e.g., external lib).
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
            relative_file_path = os.path.relpath(target_abs_path, start=current_dir)
        except ValueError:
            logger.warning(f"Could not calculate relpath between {current_dir} and {target_abs_path}")
            return None

        if relative_file_path.endswith(".py"):
            relative_file_path = relative_file_path[:-3]

        if not relative_file_path:
            logger.error(f"Cannot import from the same file: {self.current_file}")
            return None

        # Revised Path Construction
        parts = relative_file_path.split(os.sep)
        level = 0
        while parts and parts[0] == os.pardir:
            parts.pop(0)
            level += 1

        if level == 0:
            relative_module_path = "." + ".".join(parts)
        else:
            leading_dots = "." * level
            if parts:
                relative_module_path = leading_dots + "." + ".".join(parts)
            else:
                relative_module_path = leading_dots

        return relative_module_path
