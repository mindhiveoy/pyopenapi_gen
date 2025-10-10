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
from pathlib import Path
from typing import Set

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.utils import NameSanitizer

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
        parsed_schemas: Optional dictionary of all parsed IRSchema objects, keyed by their original names.
        conditional_imports: Dictionary of conditional imports (e.g., under TYPE_CHECKING)
    """

    def __init__(
        self,
        file_manager: FileManager | None = None,
        core_package_name: str = "core",
        package_root_for_generated_code: str | None = None,
        overall_project_root: str | None = None,
        parsed_schemas: dict[str, IRSchema] | None = None,
        use_absolute_imports: bool = True,
        output_package_name: str | None = None,
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
            parsed_schemas: Optional dictionary of all parsed IRSchema objects.
            use_absolute_imports: Whether to use absolute imports instead of relative imports for internal modules.
            output_package_name: The full output package name (e.g., "pyapis.business") for generating absolute imports.
        """
        self.file_manager = file_manager or FileManager()
        self.import_collector = ImportCollector()
        self.generated_modules: Set[str] = set()
        self.current_file: str | None = None
        self.core_package_name: str = core_package_name
        self.package_root_for_generated_code: str | None = package_root_for_generated_code
        self.overall_project_root: str | None = overall_project_root or os.getcwd()
        self.parsed_schemas: dict[str, IRSchema] | None = parsed_schemas
        self.use_absolute_imports: bool = use_absolute_imports
        self.output_package_name: str | None = output_package_name
        # Dictionary to store conditional imports, keyed by condition
        self.conditional_imports: dict[str, dict[str, Set[str]]] = {}

    def set_current_file(self, abs_path: str) -> None:
        """
        Set the absolute path of the file currently being rendered.

        This method also resets the import collector and immediately re-initializes
        its file context for subsequent import additions.

        Args:
            abs_path: The absolute path of the file to set as current
        """
        self.current_file = abs_path
        # Reset the import collector for each new file to ensure isolation
        self.import_collector.reset()

        # Immediately set the new context on the import_collector
        current_module_dot_path = self.get_current_module_dot_path()
        package_root_for_collector = self.get_current_package_name_for_generated_code()

        self.import_collector.set_current_file_context_for_rendering(
            current_module_dot_path=current_module_dot_path,
            package_root=package_root_for_collector,
            core_package_name_for_absolute_treatment=self.core_package_name,
        )

    def add_import(self, logical_module: str, name: str | None = None, is_typing_import: bool = False) -> None:
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
        if not logical_module:
            return

        # Fix incomplete module paths for absolute imports
        if self.use_absolute_imports and self.output_package_name:
            # Detect incomplete paths like "business.models.agent" that should be "pyapis.business.models.agent"
            root_package = self.output_package_name.split(".")[0]  # "pyapis" from "pyapis.business"
            package_suffix = ".".join(self.output_package_name.split(".")[1:])  # "business" from "pyapis.business"

            # Check if this is an incomplete internal module path
            if package_suffix and logical_module.startswith(f"{package_suffix}."):
                # This is an incomplete path like "business.models.agent"
                # Convert to complete path like "pyapis.business.models.agent"
                logical_module = f"{root_package}.{logical_module}"

        # 1. Special handling for typing imports if is_typing_import is True
        if is_typing_import and logical_module == "typing" and name:
            self.import_collector.add_typing_import(name)
            return

        # 2. Core module import?
        is_target_in_core_pkg_namespace = logical_module == self.core_package_name or logical_module.startswith(
            self.core_package_name + "."
        )
        if is_target_in_core_pkg_namespace:
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
            if name:
                self.import_collector.add_import(module=logical_module, name=name)
            else:
                self.import_collector.add_plain_import(module=logical_module)  # Stdlib plain import
            return

        # 4. Known third-party?
        KNOWN_THIRD_PARTY = {"httpx", "pydantic"}
        if logical_module in KNOWN_THIRD_PARTY or top_level_module in KNOWN_THIRD_PARTY:
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

            # For internal modules, try to use relative imports when appropriate
            relative_path = self.calculate_relative_path_for_internal_module(module_relative_to_gen_pkg_root)

            if relative_path:
                # Use relative imports for internal modules when possible
                if name is None:
                    return
                self.import_collector.add_relative_import(relative_path, name)
                return
            else:
                # Fall back to absolute imports for internal modules that can't use relative paths
                if name:
                    self.import_collector.add_import(module=logical_module, name=name)
                else:
                    self.import_collector.add_plain_import(module=logical_module)
                return

        # 6. Default: External library, add as absolute.
        if name:
            self.import_collector.add_import(module=logical_module, name=name)
        else:
            # If name is None, it's a plain import like 'import os'
            self.import_collector.add_plain_import(module=logical_module)

    def mark_generated_module(self, abs_module_path: str) -> None:
        """
        Mark a module as generated in this run.
        This helps in determining if an import is for a locally generated module.

        Args:
            abs_module_path: The absolute path of the generated module
        """
        self.generated_modules.add(abs_module_path)

    def add_conditional_import(self, condition: str, module: str, name: str) -> None:
        """
        Add a conditional import (e.g., under TYPE_CHECKING).

        Args:
            condition: The condition for the import (e.g., "TYPE_CHECKING")
            module: The module to import from
            name: The name to import
        """
        # Apply the same unified import path correction logic as add_import
        logical_module = module

        # Fix incomplete module paths for absolute imports
        if self.use_absolute_imports and self.output_package_name:
            # Detect incomplete paths like "business.models.agent" that should be "pyapis.business.models.agent"
            root_package = self.output_package_name.split(".")[0]  # "pyapis" from "pyapis.business"
            package_suffix = ".".join(self.output_package_name.split(".")[1:])  # "business" from "pyapis.business"

            # Check if this is an incomplete internal module path
            if package_suffix and logical_module.startswith(f"{package_suffix}."):
                # This is an incomplete path like "business.models.agent"
                # Convert to complete path like "pyapis.business.models.agent"
                logical_module = f"{root_package}.{logical_module}"

        if condition not in self.conditional_imports:
            self.conditional_imports[condition] = {}
        if logical_module not in self.conditional_imports[condition]:
            self.conditional_imports[condition][logical_module] = set()
        self.conditional_imports[condition][logical_module].add(name)

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
        has_type_checking_imports = False

        for condition, imports in self.conditional_imports.items():
            if imports:
                # Check if this uses TYPE_CHECKING
                if condition == "TYPE_CHECKING":
                    has_type_checking_imports = True

                # Start the conditional block
                conditional_block = [f"\nif {condition}:"]

                # Add each import under the condition
                for module, names in sorted(imports.items()):
                    names_str = ", ".join(sorted(names))
                    conditional_block.append(f"    from {module} import {names_str}")

                conditional_imports.append("\n".join(conditional_block))

        # Add TYPE_CHECKING import if needed but not already present
        if has_type_checking_imports and not self.import_collector.has_import("typing", "TYPE_CHECKING"):
            self.import_collector.add_typing_import("TYPE_CHECKING")
            # Re-generate regular imports to include TYPE_CHECKING
            regular_imports = self.import_collector.get_formatted_imports()

        # Combine all imports
        all_imports = regular_imports
        if conditional_imports:
            all_imports += "\n" + "\n".join(conditional_imports)

        return all_imports

    def add_typing_imports_for_type(self, type_str: str) -> None:
        """
        Add necessary typing imports for a given type string.

        Args:
            type_str: The type string to parse for typing imports
        """
        # Handle datetime.date and datetime.datetime explicitly
        # Regex to find "datetime.date" or "datetime.datetime" as whole words
        datetime_specific_matches = re.findall(r"\b(datetime\.(?:date|datetime))\b", type_str)
        for dt_match in datetime_specific_matches:
            module_name, class_name = dt_match.split(".")
            self.add_import(module_name, class_name, is_typing_import=False)

        # Remove datetime.xxx parts to avoid matching 'date' or 'datetime' as typing members
        type_str_for_typing_search = re.sub(r"\bdatetime\.(?:date|datetime)\b", "", type_str)

        # General regex for other potential typing names (words)
        all_words_in_type_str = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", type_str_for_typing_search)
        potential_names_to_import = set(all_words_in_type_str)

        # Names that were part of datetime.date or datetime.datetime (e.g., "date", "datetime")
        # These should not be re-imported from typing or as models if already handled by specific datetime import
        handled_datetime_parts = set()
        for dt_match in datetime_specific_matches:  # e.g., "datetime.date"
            parts = dt_match.split(".")  # ["datetime", "date"]
            handled_datetime_parts.update(parts)

        known_typing_constructs = {
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

        for name in potential_names_to_import:
            if name in handled_datetime_parts and name in {"date", "datetime"}:
                # If 'date' or 'datetime' were part of 'datetime.date' or 'datetime.datetime'
                # they were handled by add_import(module_name, class_name) earlier. Skip further processing.
                continue

            if name in known_typing_constructs:
                self.add_import("typing", name, is_typing_import=True)
                continue  # Successfully handled as a typing import

            # Check if 'name' is a known schema (model)
            if self.parsed_schemas:
                found_schema_obj = None
                # schema_obj.name is the Python class name (e.g., VectorDatabase)
                for schema_obj in self.parsed_schemas.values():
                    if schema_obj.name == name:
                        found_schema_obj = schema_obj
                        break

                if found_schema_obj:
                    # Use the generation_name if available, fallback to name
                    schema_class_name = found_schema_obj.generation_name or found_schema_obj.name
                    if schema_class_name is None:
                        logger.warning(f"Skipping import generation for an unnamed schema: {found_schema_obj}")
                        continue  # Skip to the next name if schema_class_name is None

                    # Use the final_module_stem if available, otherwise sanitize the class name
                    if found_schema_obj.final_module_stem:
                        schema_file_name_segment = found_schema_obj.final_module_stem
                    else:
                        # Fallback to sanitizing the class name
                        schema_file_name_segment = NameSanitizer.sanitize_filename(schema_class_name, suffix="")

                    current_gen_pkg_base_name = self.get_current_package_name_for_generated_code()

                    if current_gen_pkg_base_name:
                        # Models are typically in <current_gen_pkg_base_name>.models.<schema_file_name>
                        model_module_logical_path = f"{current_gen_pkg_base_name}.models.{schema_file_name_segment}"

                        current_rendering_module_logical_path = self.get_current_module_dot_path()

                        # Avoid self-importing if the model is defined in the current file being rendered
                        if current_rendering_module_logical_path != model_module_logical_path:
                            self.add_import(logical_module=model_module_logical_path, name=schema_class_name)
                        # else:
                        #     logger.debug(f"Skipping import of {schema_class_name} from "
                        #                  f"{model_module_logical_path} as it's the current module.")
                        continue  # Successfully handled (or skipped self-import) as a model import
                    else:
                        logger.warning(
                            f"Cannot determine current generated package name for schema '{schema_class_name}'. "
                            f"Import for it might be missing in {self.current_file}."
                        )
            # Fall-through: if name is not a typing construct, not datetime part, and not a parsed schema,
            # it will be ignored by this function. Other import mechanisms might handle it (e.g. primitives like 'str').

    def add_plain_import(self, module: str) -> None:
        """Add a plain import statement (e.g., `import os`)."""
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
        if not self.current_file or not self.package_root_for_generated_code:
            return None

        try:
            current_file_abs = os.path.abspath(self.current_file)
            package_root_abs = os.path.abspath(self.package_root_for_generated_code)
            current_dir_abs = os.path.dirname(current_file_abs)
        except Exception:  # Was error logging here
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
        elif os.path.isfile(target_as_file_abs):
            target_abs_path = target_as_file_abs
            is_target_package = False
        else:
            # Target does not exist. Assume it WILL be a .py module for path calculation.
            target_abs_path = target_as_file_abs
            is_target_package = False  # Assume it's a module if it doesn't exist

        # Self-import check: if the resolved target_abs_path is the same as the current_file_abs.
        if current_file_abs == target_abs_path:
            return None

        try:
            relative_file_path = os.path.relpath(target_abs_path, start=current_dir_abs)
        except ValueError:  # Was warning logging here
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
            # This happens if only dots are needed, e.g. `from .. import foo` (suffix is empty, path is just dots)
            # or `from . import bar`
            final_relative_path = leading_dots_str

        return final_relative_path

    def get_current_package_name_for_generated_code(self) -> str | None:
        """
        Get the current package name for the generated code.

        Returns:
            The current package name for the generated code, or None if not set.
        """
        # If we have the full output package name, use it for absolute imports
        if self.output_package_name:
            return self.output_package_name

        # Fallback to deriving from filesystem path (legacy behavior)
        return self.package_root_for_generated_code.split(os.sep)[-1] if self.package_root_for_generated_code else None

    def get_current_module_dot_path(self) -> str | None:
        """
        Get the current module dot path relative to the overall project root.
        Example: if current_file is /project/pkg/sub/mod.py and package_root_for_generated_code is /project/pkg,
                 and overall_project_root is /project, this should attempt to return pkg.sub.mod
        """
        if not self.current_file or not self.overall_project_root:
            return None

        try:
            abs_current_file = Path(self.current_file).resolve()
            abs_overall_project_root = Path(self.overall_project_root).resolve()

            # Get the relative path of the current file from the overall project root
            relative_path_from_project_root = abs_current_file.relative_to(abs_overall_project_root)

            # Remove .py extension
            module_parts = list(relative_path_from_project_root.parts)
            if module_parts[-1].endswith(".py"):
                module_parts[-1] = module_parts[-1][:-3]

            # Handle __init__.py cases: if the last part is __init__, it refers to the directory itself as the module
            if module_parts[-1] == "__init__":
                module_parts.pop()

            return ".".join(module_parts)

        except ValueError:  # If current_file is not under overall_project_root
            return None
