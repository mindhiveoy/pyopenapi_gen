import os
import re
from typing import Optional, Set

from ..core.utils import ImportCollector
from .file_manager import FileManager


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
    ):
        self.file_manager = file_manager or FileManager()
        self.import_collector = ImportCollector()
        self.generated_modules: Set[str] = set()  # abs_module_paths of generated files
        self.current_file: Optional[str] = None  # abs path of file being rendered
        self.core_package: str = core_package
        self.core_import_path: Optional[str] = core_import_path

    def set_current_file(self, abs_path: str) -> None:
        """Set the absolute path of the file currently being rendered."""
        self.current_file = abs_path

    def add_import(self, module: str, symbol: str) -> None:
        """
        Add an import of a symbol from a module (using module path).

        Parameters:
            module (str): The module path to import from. Must use dot notation (e.g., 'models.agent_history',
            'endpoints.analytics').
                - Do NOT use slashes or relative path notation (e.g., '../models/agent_history' is invalid).
                - For models, use 'models.<module>'
                - For endpoints, use 'endpoints.<module>'
                - For external packages, use the package/module name as usual (e.g., 'typing', 'dataclasses').
            symbol (str): The symbol (class, function, etc.) to import from the module.

        Examples:
            # Correct usage:
            add_import('models.agent_history', 'AgentHistory')
            add_import('endpoints.analytics', 'AnalyticsClient')
            add_import('typing', 'Optional')

            # Incorrect usage (will result in broken imports):
            add_import('../models/agent_history', 'AgentHistory')
            add_import('models/agent_history', 'AgentHistory')
        """
        # Handle core package imports
        rel_module: Optional[str] = None
        if module.startswith("core.") or module.startswith(f"{self.core_package}."):
            if self.core_import_path:
                # Use absolute import path for core
                abs_module = (
                    module.replace("core", self.core_import_path, 1)
                    if module.startswith("core.")
                    else module.replace(self.core_package, self.core_import_path, 1)
                )
                self.import_collector.add_import(abs_module, symbol)
                return
            if not self.current_file:
                raise RuntimeError("Current file not set in RenderContext.")
            current_dir = os.path.dirname(self.current_file)
            # Determine where we are: endpoints, models, core, or root
            if os.path.basename(current_dir) in ("endpoints", "models"):
                # Importing from endpoints/models to core: from ..core.<module> import ...
                mod = module.split(".", 1)[1] if "." in module else ""
                rel_module = f"..{self.core_package}.{mod}" if mod else f"..{self.core_package}"
            elif os.path.basename(current_dir) == self.core_package:
                # Importing from core to core: from .<module> import ...
                mod = module.split(".", 1)[1] if "." in module else ""
                rel_module = f".{mod}" if mod else "."
            else:
                # At root (e.g., client.py): from .core.<module> import ...
                mod = module.split(".", 1)[1] if "." in module else ""
                rel_module = f".{self.core_package}.{mod}" if mod else f".{self.core_package}"
            if rel_module and rel_module.strip("."):
                with open("/tmp/pyopenapi_gen_import_debug.log", "a") as debug_log:
                    debug_log.write(f"add_relative_import: rel_module={rel_module!r}, symbol={symbol!r}\n")
                self.import_collector.add_relative_import(rel_module, symbol)
            else:
                self.import_collector.add_import(module, symbol)
            return
        if module.startswith("models.") or module.startswith("endpoints."):
            if not self.current_file:
                raise RuntimeError("Current file not set in RenderContext.")
            current_dir = os.path.dirname(self.current_file)
            # Determine where we are: endpoints, models, or root
            if os.path.basename(current_dir) == "endpoints":
                # Importing from endpoints to models: from ..models.<module> import ...
                if module.startswith("models."):
                    mod = module[7:]
                    if mod:
                        rel_module = f"..models.{mod}"
                    else:
                        rel_module = "..models"  # fallback, should not happen
                else:
                    # Importing another endpoint (should be rare): from .<module> import ...
                    mod = module.split(".", 1)[1] if "." in module else ""
                    if mod:
                        rel_module = f".{mod}"
                    else:
                        rel_module = None  # fallback, should not happen
            elif os.path.basename(current_dir) == "models":
                # Importing from models to models: from .<module> import ...
                mod = module.split(".", 1)[1] if "." in module else ""
                if mod:
                    rel_module = f".{mod}"
                else:
                    rel_module = "."  # fallback, should not happen
            else:
                # At root (e.g., client.py): from .endpoints.<module> import ...
                if module.startswith("endpoints."):
                    mod = module[9:]
                    if mod:
                        # Remove leading dot if present
                        if mod.startswith("."):
                            mod = mod[1:]
                        rel_module = f".endpoints.{mod}"
                    else:
                        rel_module = ".endpoints"  # fallback, should not happen
                else:
                    rel_module = module  # fallback to absolute
            # Only add if rel_module is not just dots or empty
            if rel_module and rel_module.strip("."):
                with open("/tmp/pyopenapi_gen_import_debug.log", "a") as debug_log:
                    debug_log.write(f"add_relative_import: rel_module={rel_module!r}, symbol={symbol!r}\n")
                self.import_collector.add_relative_import(rel_module, symbol)
            elif rel_module is None:
                # Do not add fallback to '.' for models in endpoint files
                pass
            else:
                self.import_collector.add_import(module, symbol)
        else:
            self.import_collector.add_import(module, symbol)

    def mark_generated_module(self, abs_module_path: str) -> None:
        """Mark a module as being generated in this run (using abs module path)."""
        self.generated_modules.add(abs_module_path)

    def render_imports(self, package_root: str) -> str:
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
