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
        core_package_name: The full Python import path of the core package (e.g., "custom_core", "shared.my_core").
        package_root_for_generated_code: Absolute path to the root of the *currently emitting* package
                                        (e.g., project_root/client_api or project_root/custom_core if emitting core itself).
                                        Used for calculating relative paths *within* this package.
        overall_project_root: Absolute path to the top-level project.
                            Used as the base for resolving absolute Python import paths,
                            especially for an external core_package.
    """

    def __init__(
        self,
        file_manager: Optional[FileManager] = None,
        core_package_name: str = "core",
        package_root_for_generated_code: Optional[str] = None,
        overall_project_root: Optional[str] = None,
    ) -> None:
        """
        Initialize a new RenderContext.

        Args:
            file_manager: Utility for file operations (defaults to a new FileManager)
            core_package_name: The full Python import path of the core package (e.g., "custom_core", "shared.my_core").
            package_root_for_generated_code: Absolute path to the root of the *currently emitting* package
                                            (e.g., project_root/client_api or project_root/custom_core if emitting core itself).
                                            Used for calculating relative paths *within* this package.
            overall_project_root: Absolute path to the top-level project.
                                Used as the base for resolving absolute Python import paths,
                                especially for an external core_package.
        """
        self.file_manager = file_manager or FileManager()
        self.import_collector = ImportCollector()
        self.generated_modules: Set[str] = set()
        self.current_file: Optional[str] = None
        self.core_package_name: str = core_package_name
        self.package_root_for_generated_code: Optional[str] = package_root_for_generated_code
        self.overall_project_root: Optional[str] = overall_project_root or os.getcwd()
        if self.package_root_for_generated_code and not self.overall_project_root:
            pass

    def set_current_file(self, abs_path: str) -> None:
        """
        Set the absolute path of the file currently being rendered.

        This method also resets the import collector to ensure import isolation
        between different generated files.

        Args:
            abs_path: The absolute path of the file to set as current
        """
        logger.debug(
            f"[RenderContext.set_current_file] Setting current file to: {abs_path}. Resetting ImportCollector."
        )
        self.current_file = abs_path
        # Reset the import collector for each new file to ensure isolation
        self.import_collector = ImportCollector()

    def add_import(self, logical_module: str, name: str) -> None:
        """
        Add an import to the collector.

        - Core package imports are always absolute using `core_package_name`.
        - Standard library imports are absolute.
        - Other internal package imports are made relative if possible.

        Args:
            logical_module: The logical module path to import from (e.g., "typing", "shared_core.http_transport", "generated_client.models.mymodel")
            name: The name to import from the module
        """
        logger.debug(
            f"[RenderContext.add_import] Attempting for current_file='{self.current_file}': logical_module='{logical_module}', name='{name}'"
        )

        if not logical_module:
            logger.error(f"Attempted to add import with empty module for name: {name}")
            return

        # 1. Is the target module part of the configured core package?
        #    If so, treat it as an absolute import based on `self.core_package_name`.
        #    `logical_module` should already be correctly formed by the caller
        #    (e.g., "my_company.shared_core.exceptions" or "default_core_package.utils").
        is_target_in_core_pkg_namespace = logical_module == self.core_package_name or logical_module.startswith(
            self.core_package_name + "."
        )

        if is_target_in_core_pkg_namespace:
            logger.debug(f"[add_import] Core package import: from {logical_module} import {name}")
            self.import_collector.add_import(module=logical_module, name=name)
            return

        # 2. Is it a standard library or built-in module?
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
        top_level_module = logical_module.split(".")[0]
        if (
            logical_module in sys.builtin_module_names
            or logical_module in COMMON_STDLIB
            or top_level_module in COMMON_STDLIB
        ):
            logger.debug(f"[add_import] StdLib/Builtin import: from {logical_module} import {name}")
            self.import_collector.add_import(module=logical_module, name=name)
            return

        # 2.5. Is it a known third-party library that should always be absolute?
        KNOWN_THIRD_PARTY = {"httpx", "pydantic"}  # Add others as identified
        if logical_module in KNOWN_THIRD_PARTY or top_level_module in KNOWN_THIRD_PARTY:
            logger.debug(f"[add_import] Known third-party library import: from {logical_module} import {name}")
            self.import_collector.add_import(module=logical_module, name=name)
            return

        # 3. If not core or stdlib, assume it's an intra-package import within the generated client.
        #    Try to calculate a relative path.
        #    `logical_module` here is expected to be the absolute-like path from the
        #    perspective of the `package_root_for_generated_code` (e.g., "models.item" if root is "client_output").
        relative_path = self.calculate_relative_path_for_internal_module(logical_module)

        if relative_path:
            # Check for self-import via relative path as well.
            # calculate_relative_path_for_internal_module should ideally return None for self-imports.
            # If current_file is '.../package_root/models/foo.py' and logical_module is 'models.foo',
            # relative_path might become '.foo' or even just 'foo' if logic implies current dir.
            # A more robust self-import check is done within calculate_relative_path.
            logger.debug(f"[add_import] Relative internal non-core import: from {relative_path} import {name}")
            self.import_collector.add_relative_import(module=relative_path, name=name)
        else:
            # Fallback: If a relative path couldn't be determined (e.g., current_file not set,
            # or it's truly external and not caught by stdlib/core checks, or self-import detected by calc_relative).
            # This might be for actual third-party libs not in COMMON_STDLIB,
            # or a structural issue where relative path is not possible/desired.
            logger.warning(
                f"[add_import] Fallback to absolute for non-core/non-stdlib '{logical_module}' import {name} "
                f"(current_file: {self.current_file}, pkg_root: {self.package_root_for_generated_code}). "
                f"This could be a third-party lib or an unresolved internal path."
            )
            # Self-import check here for absolute fallback is a bit redundant if calc_relative handles it,
            # but kept for safety.
            expected_file_path = None
            if self.package_root_for_generated_code:
                module_parts = logical_module.split(".")
                expected_file_path = os.path.join(
                    self.package_root_for_generated_code, *module_parts[:-1], module_parts[-1] + ".py"
                )
            if (
                expected_file_path
                and self.current_file
                and os.path.normpath(expected_file_path) == os.path.normpath(self.current_file)
            ):
                logger.debug(
                    f"[add_import] Skipping self-import (absolute fallback) for {logical_module} in {self.current_file}"
                )
            else:
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
        current_module_dot_path = self.get_current_module_dot_path()
        # Pass core_package_name to influence import rendering strategy for core modules
        import_statements_list = self.import_collector.get_import_statements(
            current_module_dot_path,
            self.package_root_for_generated_code,
            self.core_package_name,  # Pass core_package_name
        )
        return "\n".join(import_statements_list)

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
            "TypeAlias",
        }

        # Regex: match all capitalized identifiers, which could be typing types
        matches = re.findall(r"\b([A-Z][A-Za-z0-9_]*)\b", type_str)

        # Add imports for any matches that are in our typing_types allowlist
        for match in set(matches):
            if match in typing_types:
                self.import_collector.add_typing_import(match)

        # Special handling for datetime and date if they appear in type strings
        if "datetime" in type_str:
            # Check for word boundaries to avoid matching substrings like "mydatetimefield"
            if re.search(r"\bdatetime\b", type_str):
                self.import_collector.add_import("datetime", "datetime")
        if "date" in type_str:
            if re.search(r"\bdate\b", type_str):
                # Avoid adding `from datetime import date` if `datetime` (the class) was already imported from `datetime`
                # This can happen if type_str is e.g. "Union[datetime, date]"
                # However, ImportCollector should handle duplicate `from datetime import date` gracefully.
                self.import_collector.add_import("datetime", "date")

    def add_plain_import(self, module: str) -> None:
        """
        Add a plain import (import x) to the current file's import collector.

        Args:
            module: The module to import
        """
        self.import_collector.add_plain_import(module)

    def calculate_relative_path_for_internal_module(
        self,
        target_logical_module_relative_to_gen_pkg_root: str,
    ) -> str | None:
        """
        Calculate relative import path for a module *within the same generated package*.
        target_logical_module_relative_to_gen_pkg_root: e.g., "models.item" or "endpoints.utils"
                                                       relative to self.package_root_for_generated_code
        """
        if not self.current_file or not self.package_root_for_generated_code:
            logger.warning(
                "Cannot calculate relative path: current_file or package_root_for_generated_code is not set."
            )
            return None

        target_parts = target_logical_module_relative_to_gen_pkg_root.split(".")
        target_abs_path_candidate1 = os.path.abspath(os.path.join(self.package_root_for_generated_code, *target_parts))
        target_abs_path_candidate2 = os.path.abspath(
            os.path.join(self.package_root_for_generated_code, *target_parts) + ".py"
        )

        if os.path.isdir(target_abs_path_candidate1):
            target_abs_path = target_abs_path_candidate1
            is_target_package = True
        elif os.path.isfile(target_abs_path_candidate2):
            target_abs_path = target_abs_path_candidate2
            is_target_package = False
        else:
            logger.debug(
                f"Target '{target_logical_module_relative_to_gen_pkg_root}' not found as dir/file. Assuming module path for relpath calculation."
            )
            # Fallback: assume it's a .py file path for relpath, even if it doesn't exist.
            # This allows calculation for modules yet to be generated.
            target_abs_path = target_abs_path_candidate2
            is_target_package = False

        # Explicitly check for self-import before path calculations
        # self.current_file is guaranteed to be non-None here by the initial check
        if os.path.abspath(self.current_file) == target_abs_path:
            logger.debug(
                f"Attempt to import self: {self.current_file} as {target_logical_module_relative_to_gen_pkg_root}"
            )
            return None

        current_dir = os.path.dirname(os.path.abspath(self.current_file))

        try:
            relative_file_path = os.path.relpath(target_abs_path, start=current_dir)
        except ValueError:
            logger.warning(f"Could not calculate relpath between {current_dir} and {target_abs_path}")
            return None

        if not is_target_package and relative_file_path.endswith(".py"):
            relative_file_path = relative_file_path[:-3]

        # `parts_after_pardir` will store path components after '..'
        # `level` will count the number of '..' (os.pardir)
        path_components = relative_file_path.split(os.sep)
        level = 0

        # Calculate level and the remaining path components after '..'
        parts_after_pardir = []
        pardir_found = False
        for part in path_components:
            if part == os.pardir:
                level += 1
                pardir_found = True
            elif pardir_found:  # Once we are past '..' parts, collect the rest
                parts_after_pardir.append(part)
            elif part != os.curdir:  # If not '..' and not '.', it's a direct child/sibling path part
                parts_after_pardir.append(part)

        # If relative_file_path was just '.', parts_after_pardir might be empty or ['.']
        # If it was '..', level=1, parts_after_pardir is empty.

        # Determine the number of dots for Python's relative import prefix
        # level 0 (e.g. 'foo/bar' or 'foo.py') -> 1 dot prefix '.'
        # level 1 (e.g. '../foo/bar') -> 2 dots prefix '..'
        # level N -> N+1 dots
        num_dots_for_prefix = level + 1

        leading_dots_str = "." * num_dots_for_prefix

        # Join the remaining path components (after '..' parts were processed for level)
        module_name_suffix = ".".join(p for p in parts_after_pardir if p and p != os.curdir)

        if module_name_suffix:
            relative_module_path = leading_dots_str + module_name_suffix
        else:
            # This case covers imports like 'from .. import foo' (where suffix is foo)
            # or 'from .. import' (which is not valid Python but implies importing parent package)
            # If module_name_suffix is empty, it means we're importing a package indicated by dots.
            # e.g., relpath '..', level=1, parts_after_pardir=[]. num_dots=2. result '..'
            # e.g., relpath '.', level=0, parts_after_pardir may be [] or ['.']. num_dots=1. result '.'
            relative_module_path = leading_dots_str

        # Final check: if the path calculation results in just "." and parts_after_pardir was empty or ["."],
        # and original relpath was also "." (importing current package's __init__ from a module in it),
        # then "." is correct. If original relpath was "foo.py" and parts_after_pardir became "foo",
        # then ".foo" is correct.
        # The self-import check at the beginning is more definitive for `target == current`.

        return relative_module_path

    def get_current_module_dot_path(self) -> Optional[str]:
        if not self.current_file or not self.package_root_for_generated_code:
            return None
        try:
            # Make current_file relative to overall_project_root if it's absolute
            if os.path.isabs(self.current_file) and self.overall_project_root:
                rel_current_file = os.path.relpath(self.current_file, self.overall_project_root)
            else:
                rel_current_file = self.current_file

            # Ensure it's under package_root_for_generated_code
            if not rel_current_file.startswith(self.package_root_for_generated_code):
                # If current file is not under package_root, it cannot be a module within it.
                # This can happen if current_file is outside, or package_root is deeper.
                # Example: current_file="src/file.py", package_root="output/package"
                # However, for client.py (current_file="out/client.py", pkg_root="out"), this path isn't hit.
                # If current_file is like "client.py" and package_root is "" (workspace root),
                # then rel_path_from_pkg_root should be "client.py"
                logger.debug(
                    f"Current file {rel_current_file} not under package root {self.package_root_for_generated_code}, cannot form module path."
                )
                return None  # Or handle as top-level module if package_root is effectively the project root itself

            # Path relative to the package root, e.g., "client.py" or "models/user.py"
            rel_path_from_pkg_root = os.path.relpath(rel_current_file, self.package_root_for_generated_code)

            # Remove .py extension
            module_parts = os.path.splitext(rel_path_from_pkg_root)[0].split(os.sep)

            # Prepend package_root_for_generated_code if it's not empty (it forms the base package name)
            base_package_parts = []
            if self.package_root_for_generated_code:  # e.g. "out" or "src/my_package"
                # Normalize package_root_for_generated_code, remove trailing slashes
                norm_pkg_root = self.package_root_for_generated_code.strip(os.sep)
                if norm_pkg_root:  # if it wasn't just "" or "/"
                    base_package_parts = norm_pkg_root.split(os.sep)

            full_module_parts = base_package_parts + module_parts

            # Handle __init__.py files by using the parent directory as module name
            if full_module_parts[-1] == "__init__":
                full_module_parts = full_module_parts[:-1]

            return ".".join(filter(None, full_module_parts))
        except Exception as e:
            logger.error(f"Error generating module dot path for {self.current_file}: {e}")
            return None

    def _add_typing_import_if_known(self, name: str, original_type_str: str) -> None:
        # original_type_str is for debugging context if needed
        # logger.debug(f"_add_typing_import_if_known: name='{name}', original_type_str='{original_type_str}', KNOWN_TYPING_IMPORTS: {name in KNOWN_TYPING_IMPORTS}")
        # if name in KNOWN_TYPING_IMPORTS:
        #     if name == "Any": # CRITICAL DEBUG
        #         logger.critical(f"[RenderContextCRITICAL_KNOWN_TYPING_ANY] ADDING 'typing.Any' for type string '{original_type_str}'. Current file: {self.current_file}")
        #     self.add_import("typing", name)
        # The above was incorrect as KNOWN_TYPING_IMPORTS is not in scope here.
        # The actual logic for this method is in add_typing_imports_for_type. This method is not used.
        pass  # This method seems to be unused and its previous logic was flawed.
