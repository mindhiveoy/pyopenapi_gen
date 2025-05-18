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
from typing import Dict, Optional, Set
from pathlib import Path

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
                                        (e.g., project_root/client_api or project_root/custom_core if emitting core
                                        itself). Used for calculating relative paths *within* this package.
        overall_project_root: Absolute path to the top-level project.
                            Used as the base for resolving absolute Python import paths,
                            especially for an external core_package.
        conditional_imports: Dictionary of conditional imports (e.g., under TYPE_CHECKING)
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
                                            (e.g., project_root/client_api or project_root/custom_core if emitting core
                                            itself). Used for calculating relative paths *within* this package.
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
        # Dictionary to store conditional imports, keyed by condition
        self.conditional_imports: Dict[str, Dict[str, Set[str]]] = {}

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
        self.import_collector.reset()

    def add_import(self, logical_module: str, name: Optional[str] = None, is_typing_import: bool = False) -> None:
        """
        Add an import to the collector.

        - Core package imports are always absolute using `core_package_name`.
        - Standard library imports are absolute.
        - Other internal package imports are made relative if possible.
        - Unknown modules are treated as absolute external imports.

        Args:
            logical_module: The logical module path to import from (e.g., "typing",
                            "shared_core.http_transport", "generated_client.models.mymodel",
                            "some_external_lib.api").
                            For internal modules, this should be the fully qualified path from project root.
            name:           The name to import from the module
            is_typing_import: Whether the import is a typing import
        """
        # ==== VECTOR_DATABASE TARGETED LOGGING START ====
        if name and name.lower() == "vectordatabase":
            logger.error(
                f"[RC_VD_TRACE] add_import called for VectorDatabase. Context file: {self.current_file}. "
                f"Details: logical_module='{logical_module}', name='{name}', is_typing_import={is_typing_import}"
            )
        # ==== VECTOR_DATABASE TARGETED LOGGING END ====

        if not logical_module:
            logger.error(f"Attempted to add import with empty module for name: {name}")
            return

        # 1. Special handling for typing imports if is_typing_import is True
        if is_typing_import and logical_module == "typing" and name:
            self.import_collector.add_typing_import(name)
            return

        # 2. Core module import?
        is_target_in_core_pkg_namespace = logical_module == self.core_package_name or logical_module.startswith(
            self.core_package_name + "."
        )
        if is_target_in_core_pkg_namespace:
            logger.debug(f"[add_import] Core package import: from {logical_module} import {name}")
            if name:
                self.import_collector.add_import(module=logical_module, name=name)
            else:
                self.import_collector.add_plain_import(module=logical_module)  # Core plain import
            return

        # 3. Stdlib/Builtin?
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
            if name:
                self.import_collector.add_import(module=logical_module, name=name)
            else:
                self.import_collector.add_plain_import(module=logical_module)  # Stdlib plain import
            return

        # 4. Known third-party?
        KNOWN_THIRD_PARTY = {"httpx", "pydantic"}
        if logical_module in KNOWN_THIRD_PARTY or top_level_module in KNOWN_THIRD_PARTY:
            logger.debug(f"[add_import] Known third-party library import: from {logical_module} import {name}")
            if name:
                self.import_collector.add_import(module=logical_module, name=name)
            else:
                self.import_collector.add_plain_import(module=logical_module)  # Third-party plain import
            return

        # 5. Internal to current generated package?
        current_gen_package_name_str = self.get_current_package_name_for_generated_code()

        is_internal_module_candidate = False  # Initialize here
        if current_gen_package_name_str:
            if logical_module == current_gen_package_name_str:  # e.g. importing current_gen_package_name_str itself
                is_internal_module_candidate = True
            elif logical_module.startswith(current_gen_package_name_str + "."):
                is_internal_module_candidate = True

        if is_internal_module_candidate:
            # It looks like an internal module.
            # First, check if it's a direct self-import of the full logical path.
            current_full_module_path = self.get_current_module_dot_path()
            if current_full_module_path == logical_module:
                logger.debug(f"[add_import] Direct self-import skipped: {logical_module}.{name if name else ''}")
                return  # Skip if it's a direct self-import

            # Determine module path relative to current generated package root
            module_relative_to_gen_pkg_root: str
            if logical_module == current_gen_package_name_str:  # Importing the root package itself
                # This case should likely be handled by calculate_relative_path based on current file
                # For now, let's treat it as a root module, and calculate_relative_path will see if it needs dots
                module_relative_to_gen_pkg_root = logical_module  # This might be too simplistic for root pkg itself
            elif current_gen_package_name_str:  # Should be true due to is_internal_module_candidate
                module_relative_to_gen_pkg_root = logical_module[len(current_gen_package_name_str) + 1 :]
            else:  # Should not happen if current_gen_package_name_str was required for is_internal_module_candidate
                module_relative_to_gen_pkg_root = logical_module

            logger.debug(
                f"[add_import] Identified as internal (prefix '{current_gen_package_name_str}'). "
                f"Rel part for calc: '{module_relative_to_gen_pkg_root}' from logical '{logical_module}'"
            )
            relative_path = self.calculate_relative_path_for_internal_module(module_relative_to_gen_pkg_root)

            if relative_path:
                if name is None:
                    logger.error(
                        f"[RC_TARGET_LOG] INTERNAL import: Relative path '{relative_path}' calculated but name is None. This should not happen for from-imports. Skipping."
                    )
                    return
                # ==== VECTOR_DATABASE TARGETED LOGGING FOR ADD_RELATIVE_IMPORT ====
                if name == "VectorDatabase":
                    logger.error(
                        f"!!!!!!!!!! [RC_VD_ADD_RELATIVE] About to add_relative_import for '{name}' from '{relative_path}'. Context file: {self.current_file} !!!!!!!!!!"
                    )
                # ==== END VECTOR_DATABASE TARGETED LOGGING ====
                self.import_collector.add_relative_import(relative_path, name)
                return
            else:
                # ==== TARGETED LOGGING START ====
                logger.critical(
                    f"[RC_TARGET_LOG] INTERNAL import - Fallback to ABSOLUTE for '{logical_module}' import {name if name else ''}"
                )
                # ==== TARGETED LOGGING END ====
                # ==== VECTOR_DATABASE TARGETED LOGGING FOR ADD_IMPORT (FALLBACK) ====
                if name == "VectorDatabase":
                    logger.error(
                        f"!!!!!!!!!! [RC_VD_ADD_IMPORT_FALLBACK] About to add_import (fallback) for '{name}' from '{logical_module}'. Context file: {self.current_file} !!!!!!!!!!"
                    )
                # ==== END VECTOR_DATABASE TARGETED LOGGING ====
                logger.warning(
                    f"[add_import] Failed to get relative path for presumed internal module {logical_module} (rel part {module_relative_to_gen_pkg_root}). "
                    f"Defaulting to absolute import: '{logical_module}' for '{name if name else '<module_itself>'}'"
                )
                # Fallback to absolute for this internal module.
                if name:
                    self.import_collector.add_import(module=logical_module, name=name)
                else:
                    self.import_collector.add_plain_import(module=logical_module)  # Internal fallback plain import
                return

        # 6. Fallback: Not core, not stdlib, not known third-party, and not prefixed like an internal module.
        #    This handles truly external libraries or potentially mis-formed internal logical_modules.
        # ==== TARGETED LOGGING START ====
        logger.critical(
            f"[RC_TARGET_LOG] Fallback to ABSOLUTE/EXTERNAL for '{logical_module}' import {name if name else ''}"
        )
        # ==== TARGETED LOGGING END ====
        # A final self-import check using the raw logical_module as if it were a file path from package_root.
        # This is a safeguard. The primary self-import is in calculate_relative_path_for_internal_module.
        skip_due_to_self_import = False
        if self.package_root_for_generated_code and self.current_file:
            try:
                current_file_path = Path(self.current_file)
                pkg_root_path = Path(self.package_root_for_generated_code)

                # Construct potential target file path from logical_module
                # e.g., logical_module = "pkg.models.user" -> pkg_root_path / "models" / "user.py"
                module_parts = logical_module.split(".")
                if module_parts[0] == self.get_current_package_name_for_generated_code():
                    target_rel_path_parts = module_parts[1:]  # e.g. ["models", "user"]
                    target_file_path = pkg_root_path.joinpath(*target_rel_path_parts).with_suffix(".py")

                    if current_file_path.resolve() == target_file_path.resolve():
                        skip_due_to_self_import = True
            except Exception as e:
                logger.debug(f"[RC_TARGET_LOG] Error during self-import check for absolute path: {e}")

        if not skip_due_to_self_import:
            # Pass name directly, ImportCollector.add_import handles Optional[str]
            if name:
                self.import_collector.add_import(module=logical_module, name=name)
            else:
                # If name is None, it's a plain import like 'import os'
                self.import_collector.add_plain_import(module=logical_module)

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
        Render all imports for the current file, including conditional imports.

        Returns:
            A string containing all import statements.
        """
        # Get standard imports
        regular_imports = self.import_collector.get_formatted_imports()

        # Handle conditional imports
        conditional_imports = []
        for condition, imports in self.conditional_imports.items():
            if imports:
                # Start the conditional block
                conditional_block = [f"\nif {condition}:"]

                # Add each import under the condition
                for module, names in sorted(imports.items()):
                    names_str = ", ".join(sorted(names))
                    conditional_block.append(f"    from {module} import {names_str}")

                conditional_imports.append("\n".join(conditional_block))

        # Combine all imports
        all_imports = regular_imports
        if conditional_imports:
            all_imports += "\n" + "\n".join(conditional_imports)

        return all_imports

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
                # Avoid adding `from datetime import date` if `datetime` (the class) was already
                # imported from `datetime`. This can happen if type_str is e.g. "Union[datetime, date]"
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
        Calculates a relative Python import path for a target module within the
        currently generated package, given the current file being rendered.

        Example:
            current_file: /project/out_pkg/endpoints/tags_api.py
            package_root_for_generated_code: /project/out_pkg
            target_logical_module_relative_to_gen_pkg_root: "models.tag_model"
            Returns: "..models.tag_model"

        Args:
            target_logical_module_relative_to_gen_pkg_root: The dot-separated path of the target module,
                relative to the `package_root_for_generated_code` (e.g., "models.user").

        Returns:
            The relative import string (e.g., ".sibling", "..models.user"), or None if a relative path
            cannot be determined (e.g., context not fully set, or target is current file).
        """
        logger.debug(
            f"[CalculateRelativePath_vOldLogic] Current: {self.current_file}, PkgRoot: {self.package_root_for_generated_code}, TargetRelToPkg: {target_logical_module_relative_to_gen_pkg_root}"
        )

        if not self.current_file or not self.package_root_for_generated_code:
            logger.debug("[CalculateRelativePath_vOldLogic] Context not fully set.")
            return None

        try:
            current_file_abs = os.path.abspath(self.current_file)
            package_root_abs = os.path.abspath(self.package_root_for_generated_code)
            current_dir_abs = os.path.dirname(current_file_abs)
        except Exception as e:
            logger.error(f"[CalculateRelativePath_vOldLogic] Error making paths absolute: {e}")
            return None

        target_parts = target_logical_module_relative_to_gen_pkg_root.split(".")

        # Construct potential absolute paths for the target (as a directory/package or as a .py file)
        target_as_dir_abs = os.path.join(package_root_abs, *target_parts)
        target_as_file_abs = os.path.join(package_root_abs, *target_parts) + ".py"

        target_abs_path: str
        is_target_package: bool  # True if target is a package (directory), False if a module (.py file)

        if os.path.isdir(target_as_dir_abs):
            target_abs_path = target_as_dir_abs
            is_target_package = True
            logger.debug(
                f"[CalculateRelativePath_vOldLogic] Target '{target_logical_module_relative_to_gen_pkg_root}' is a directory."
            )
        elif os.path.isfile(target_as_file_abs):
            target_abs_path = target_as_file_abs
            is_target_package = False
            logger.debug(
                f"[CalculateRelativePath_vOldLogic] Target '{target_logical_module_relative_to_gen_pkg_root}' is a file."
            )
        else:
            # Target does not exist. Assume it WILL be a .py module for path calculation.
            logger.debug(
                f"[CalculateRelativePath_vOldLogic] Target '{target_logical_module_relative_to_gen_pkg_root}' does not exist. Assuming it will be a .py module for path calculation."
            )
            target_abs_path = target_as_file_abs
            is_target_package = False  # Assume it's a module if it doesn't exist

        # Self-import check: if the resolved target_abs_path is the same as the current_file_abs.
        if current_file_abs == target_abs_path:
            logger.debug(
                f"[CalculateRelativePath_vOldLogic] Target '{target_logical_module_relative_to_gen_pkg_root}' resolved to current file. Skipping relative import (self-import)."
            )
            return None

        try:
            relative_file_path = os.path.relpath(target_abs_path, start=current_dir_abs)
        except ValueError:
            logger.warning(
                f"[CalculateRelativePath_vOldLogic] Could not determine relpath between '{current_dir_abs}' and '{target_abs_path}'. Defaulting to no relative path."
            )
            return None

        # If the target is a module file (not a package/directory), and the relative path ends with .py, remove it.
        if not is_target_package and relative_file_path.endswith(".py"):
            relative_file_path = relative_file_path[:-3]

        path_components = relative_file_path.split(os.sep)
        level = 0
        parts_after_pardir = []
        pardir_found_and_processed = False

        for part in path_components:
            if part == os.pardir:
                if not pardir_found_and_processed:
                    level += 1
            elif part == os.curdir:
                # If current dir '.' is the first part, it implies sibling, level remains 0.
                # If it appears after '..', it's unusual but we just ignore it.
                if not path_components[0] == os.curdir and not pardir_found_and_processed:
                    # This case ('.' after some actual path part) means we treat it as a path segment
                    parts_after_pardir.append(part)
            else:  # Actual path segment
                pardir_found_and_processed = True  # Stop counting '..' for level once a real segment is found
                parts_after_pardir.append(part)

        # If the path started with '..' (e.g. '../../foo'), level is correct.
        # If it started with 'foo' (sibling dir or file), level is 0.
        # num_dots_for_prefix: 0 for current dir, 1 for ./foo, 2 for ../foo, 3 for ../../foo
        if relative_file_path == os.curdir or not path_components or path_components == [os.curdir]:
            # This means target is current_dir itself (e.g. importing __init__.py)
            # This should ideally be caught by self-import if current_file is __init__.py itself
            # Or if target is __init__.py in current_dir. For this, we need just "."
            num_dots_for_prefix = 1
            parts_after_pardir = []  # No suffix needed for just "."
        elif level == 0 and (not parts_after_pardir or parts_after_pardir == [os.curdir]):
            # This condition implies relative_file_path was something like "." or empty after processing,
            # meaning it's in the current directory. If os.curdir was the only thing, it's handled above.
            # This is for safety, might be redundant with the direct os.curdir check.
            num_dots_for_prefix = 1
            parts_after_pardir = [
                comp for comp in parts_after_pardir if comp != os.curdir
            ]  # clean out curdir if it's there
        else:
            num_dots_for_prefix = level + 1

        leading_dots_str = "." * num_dots_for_prefix
        module_name_suffix = ".".join(p for p in parts_after_pardir if p)  # Filter out empty strings

        if module_name_suffix:
            final_relative_path = leading_dots_str + module_name_suffix
        else:
            # This happens if only dots are needed, e.g. `from .. import foo` would mean `target_abs_path` was `current_dir/../../foo.py`
            # and parts_after_pardir became ["foo"]. So `leading_dots_str` would be ".." and suffix "foo".
            # If parts_after_pardir is empty, it means `relative_file_path` was purely ".." or "."
            # If `leading_dots_str` is "." and `module_name_suffix` is empty, means "."
            # If `leading_dots_str` is ".." and `module_name_suffix` is empty, means ".." (importing parent package's __init__)
            # However, the module name (`target_parts[-1]`) needs to be appended if we are importing a module from parent.
            # This part of original logic was complex. Let's simplify: if suffix is empty, it's an import of a package itself.
            # The logic should result in: '.' for same dir package, '..' for parent package.
            # For example, if target is parent dir, relpath is '..', level 1, num_dots 2 -> '..'
            # If target is same dir (package itself), relpath is '.', level 0, num_dots 1 -> '.'
            if not leading_dots_str:  # Should not happen if num_dots_for_prefix is at least 1
                final_relative_path = "." + target_parts[-1]  # Fallback, should be caught by self-import or other logic
            elif (
                is_target_package and leading_dots_str.endswith(".") and len(leading_dots_str) > 1
            ):  # e.g. ".." or "..."
                final_relative_path = leading_dots_str[:-1]  # For package, remove trailing dot of `from .. import`
            elif is_target_package:  # e.g. "." for current package
                final_relative_path = leading_dots_str
            else:  # Importing a module from a parent, suffix should not be empty here in a valid case.
                # This case might be from ..module_name
                # The original logic was: `relative_module_path = leading_dots_str` if no suffix. Which is for packages.
                # If not a package and no suffix, it's like from .. import foo_module (suffix should be foo_module)
                # My loop for parts_after_pardir should have captured the module name.
                # This means the target_parts[-1] (original module name) needs to be the suffix.
                final_relative_path = leading_dots_str + target_parts[-1]

        logger.debug(f"[CalculateRelativePath_vOldLogic] Determined relative import: '{final_relative_path}'")
        return final_relative_path

    def get_current_module_dot_path(self) -> Optional[str]:
        if not self.current_file or not self.package_root_for_generated_code:
            logger.warning(
                "[RenderContext.get_current_module_dot_path] Current file or package_root_for_generated_code not set."
            )
            return None

        try:
            # Ensure both paths are absolute and normalized for reliable comparison/relpath
            abs_current_file = os.path.abspath(self.current_file)
            abs_package_root = os.path.abspath(self.package_root_for_generated_code)

            if not abs_current_file.startswith(abs_package_root):
                logger.error(
                    f"[RenderContext.get_current_module_dot_path] Current file '{abs_current_file}' "
                    f"is not under package root '{abs_package_root}'."
                )
                # Attempt to derive from overall_project_root if current_file is a direct module name perhaps
                if self.overall_project_root:
                    abs_overall_root = os.path.abspath(self.overall_project_root)
                    if abs_current_file.startswith(abs_overall_root):
                        # Path of current file relative to the overall project root
                        rel_to_project_root = os.path.relpath(abs_current_file, abs_overall_root)
                        module_path_from_project_root = os.path.splitext(rel_to_project_root)[0].replace(os.sep, ".")
                        logger.info(f"Deriving module path from overall project root: {module_path_from_project_root}")
                        return module_path_from_project_root
                return None

            # Path of current file relative to its package root
            # e.g., "models/user.py" or "client.py"
            rel_path_from_pkg_root = os.path.relpath(abs_current_file, abs_package_root)

            # Convert to module path (e.g., "models.user" or "client")
            module_sub_path = os.path.splitext(rel_path_from_pkg_root)[0].replace(os.sep, ".")

            # Determine the base package name if overall_project_root is set and is an ancestor
            # The base_package_name is the name of the package_root_for_generated_code itself.
            # e.g. if package_root_for_generated_code is ".../project/out", then base_package_name is "out"
            # This is relevant if the generated code is itself a package.
            base_package_name_parts = []
            if self.overall_project_root:
                abs_overall_root = os.path.abspath(self.overall_project_root)
                # Check if package_root is a sub-directory of overall_project_root or the same
                if abs_package_root.startswith(abs_overall_root) and abs_package_root != abs_overall_root:
                    # Path of package_root relative to project_root, e.g., "out" or "src/client"
                    rel_pkg_root_dir_to_project = os.path.relpath(abs_package_root, abs_overall_root)
                    base_package_name_parts = rel_pkg_root_dir_to_project.split(os.sep)

            if (
                not base_package_name_parts and os.path.basename(abs_package_root) != "."
            ):  # if not a sub-package, use its own name
                base_package_name_parts = [os.path.basename(abs_package_root)]

            full_module_parts = [part for part in base_package_name_parts if part and part != "."]

            # Append module_sub_path parts, carefully handling if module_sub_path is "." (e.g. for __init__.py at package root)
            if module_sub_path and module_sub_path != ".":
                full_module_parts.extend(module_sub_path.split("."))

            # Handle if current file is __init__.py: its module path is its parent dir's path
            if os.path.basename(abs_current_file) == "__init__.py":
                # full_module_parts should already represent the directory if module_sub_path was derived correctly
                # e.g. if current_file is "out/models/__init__.py", pkg_root is "out",
                # module_sub_path would be "models.__init__". After splitext: "models.__init__"
                # We want "out.models"
                # The logic above for module_sub_path results in "models.__init__"
                # If full_module_parts from base is ["out"], then we get ["out", "models", "__init__"]
                # So we need to remove the last "__init__" if present.
                if full_module_parts and full_module_parts[-1] == "__init__":
                    full_module_parts = full_module_parts[:-1]

            if (
                not full_module_parts
            ):  # case like current_file is __init__.py in project_root and pkg_root is project_root
                logger.debug(
                    f"Calculated empty module path for {abs_current_file}, perhaps it's a top-level __init__.py not in a package."
                )
                return None  # Or return "__main__" or similar if appropriate, but None signals cannot determine

            final_module_path = ".".join(filter(None, full_module_parts))
            logger.debug(
                f"Calculated module dot path for '{abs_current_file}' as '{final_module_path}' (pkg_root='{abs_package_root}')"
            )
            return final_module_path

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

    def add_conditional_import(self, condition: str, module: str, name: str) -> None:
        """
        Add an import that should be guarded by a condition (e.g., TYPE_CHECKING).

        Useful for forward references to avoid circular imports.

        Args:
            condition: The condition to guard the import (e.g., "TYPE_CHECKING")
            module: The module to import from (e.g., "models.pet")
            name: The name to import (e.g., "Pet")
        """
        if condition not in self.conditional_imports:
            self.conditional_imports[condition] = {}

        if module not in self.conditional_imports[condition]:
            self.conditional_imports[condition][module] = set()

        self.conditional_imports[condition][module].add(name)
        logger.debug(f"[add_conditional_import] Added conditional import: if {condition}: from {module} import {name}")

    def clear_imports(self) -> None:
        """Clear all imports for a new file."""
        self.import_collector = ImportCollector()
        self.conditional_imports = {}

    def get_current_package_name_for_generated_code(self) -> Optional[str]:
        """Derives the top-level package name of the generated code.

        E.g., if overall_project_root is '/tmp/myproj' and
        package_root_for_generated_code is '/tmp/myproj/client_output',
        this should return 'client_output'.

        If package_root_for_generated_code is directly under overall_project_root,
        it returns the basename. If they are the same, it might return an empty string
        or a specific marker if that's a valid scenario (currently implies direct generation
        into project root, which might be complex for packaging).

        Returns:
            The derived package name (e.g., "client_output") or None if roots are not set.
        """
        if not self.package_root_for_generated_code or not self.overall_project_root:
            logger.warning("[get_current_package_name_for_generated_code] Roots not set, cannot derive package name.")
            return None

        abs_gen_root = os.path.abspath(self.package_root_for_generated_code)
        abs_proj_root = os.path.abspath(self.overall_project_root)

        if not abs_gen_root.startswith(abs_proj_root):
            logger.error(
                f"[get_current_package_name_for_generated_code] Generated code root '{abs_gen_root}' "
                f"is not under overall project root '{abs_proj_root}'. Cannot derive package name."
            )
            return None  # Or raise error

        if abs_gen_root == abs_proj_root:
            # This case implies generating directly into the project root.
            # Depending on desired behavior, could return None, "" or a special marker.
            # For now, let's consider this an ambiguous case for package naming via this method.
            logger.info(
                "[get_current_package_name_for_generated_code] Generated code root is same as project root. "
                "Package name is ambiguous via this method."
            )
            # It might be better to return the basename of the project root itself if it's intended to be the package name.
            # For now, returning None to indicate ambiguity or that it's not a sub-package.
            # If the intention is to always have a sub-package, this indicates a config issue.
            return os.path.basename(abs_proj_root)  # Fallback to project root's name

        # Get the path of gen_root relative to proj_root
        relative_path = os.path.relpath(abs_gen_root, abs_proj_root)

        # The first component of this relative path is the package name
        # e.g., if relative_path is "client_output" or "client_output/something_else"
        # the package name is "client_output".
        package_name_parts = relative_path.split(os.sep)
        if package_name_parts:
            derived_pkg_name = package_name_parts[0]
            logger.debug(f"[get_current_package_name_for_generated_code] Derived package name: {derived_pkg_name}")
            return derived_pkg_name
        else:
            logger.warning(
                f"[get_current_package_name_for_generated_code] Could not derive package name from paths: "
                f"proj_root='{abs_proj_root}', gen_root='{abs_gen_root}'"
            )
            return None
