"""
ClientGenerator: Encapsulates the OpenAPI client generation logic for use by CLI or other frontends.
"""

import shutil
import tempfile
import os
from pathlib import Path
from typing import Any, Optional, List

from pyopenapi_gen.core.loader import load_ir_from_spec
from pyopenapi_gen.core.postprocess_manager import PostprocessManager
from pyopenapi_gen.core.warning_collector import WarningCollector
from pyopenapi_gen.emitters.client_emitter import ClientEmitter
from pyopenapi_gen.emitters.core_emitter import CONFIG_TEMPLATE, CoreEmitter
from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter
from pyopenapi_gen.emitters.exceptions_emitter import ExceptionsEmitter
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter
from pyopenapi_gen.context.file_manager import FileManager


class GenerationError(Exception):
    """Raised when client generation fails due to errors or diffs."""

    pass


class ClientGenerator:
    """
    Generates a Python OpenAPI client package from a given OpenAPI spec file or URL.

    This class encapsulates all logic for code generation, diffing, post-processing, and output management.
    It is independent of any CLI or UI framework and can be used programmatically.
    """

    def __init__(self) -> None:
        pass

    def generate(
        self,
        spec_path: str,
        project_root: Path,
        output_package: str,
        force: bool = False,
        no_postprocess: bool = False,
        core_package: Optional[str] = None,
    ) -> List[Path]:
        """
        Generate the client code from the OpenAPI spec.

        Args:
            spec_path (str): Path or URL to the OpenAPI spec file.
            project_root (Path): Path to the root of the Python project (absolute or relative).
            output_package (str): Python package path for the generated client (e.g., 'pyapis.my_api_client').
            force (bool): Overwrite output without diff check.
            name (Optional[str]): Custom client package name (not used).
            docs (bool): Kept for interface compatibility.
            telemetry (bool): Kept for interface compatibility.
            auth (Optional[str]): Kept for interface compatibility.
            no_postprocess (bool): Skip post-processing (type checking, etc.).
            core_package (str): Python package path for the core package.

        Raises:
            GenerationError: If generation fails or diffs are found (when not forcing overwrite).
        """
        project_root = Path(project_root).resolve()
        spec_dict = self._load_spec(spec_path)
        ir = load_ir_from_spec(spec_dict)
        collector = WarningCollector()
        reports = collector.collect(ir)
        for report in reports:
            print(f"WARNING [{report.code}]: {report.message} (Hint: {report.hint})")

        # Resolve output and core directories from package paths
        def pkg_to_path(pkg: str) -> Path:
            return project_root.joinpath(*pkg.split("."))

        # Default output_package if not set
        if not output_package:
            raise ValueError("Output package name cannot be empty")
        out_dir = pkg_to_path(output_package)

        # --- Robust Defaulting for core_package ---
        if core_package is None:  # User did not specify, use default relative to output_package
            resolved_core_package_fqn = output_package + ".core"
        else:  # User specified something, use it as is
            resolved_core_package_fqn = core_package
        # --- End Robust Defaulting ---

        # Determine core_dir (physical path for CoreEmitter)
        core_dir = pkg_to_path(resolved_core_package_fqn)

        # The actual_core_module_name_for_emitter_init becomes resolved_core_package_fqn
        # The core_import_path_for_context also becomes resolved_core_package_fqn

        generated_files = []

        if not force and out_dir.exists():
            # --- Refactored Diff Logic ---
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_project_root_for_diff = Path(tmpdir)

                # Define temporary destination paths based on the temp project root
                def tmp_pkg_to_path(pkg: str) -> Path:
                    # Ensure the path is relative to the temp root, not the final project root
                    return tmp_project_root_for_diff.joinpath(*pkg.split("."))

                tmp_out_dir_for_diff = tmp_pkg_to_path(output_package)
                tmp_core_dir_for_diff = tmp_pkg_to_path(resolved_core_package_fqn)

                # Ensure temporary directories exist (FileManager used by emitters might handle this, but explicit is safer)
                tmp_out_dir_for_diff.mkdir(parents=True, exist_ok=True)
                # Ensure core temp dir exists *if* it's outside the main output package dir
                if not str(tmp_core_dir_for_diff).startswith(str(tmp_out_dir_for_diff)):
                    tmp_core_dir_for_diff.mkdir(parents=True, exist_ok=True)

                # --- Generate files into the temporary structure ---
                temp_generated_files = []  # Track files generated in temp dir

                # 1. CoreEmitter (emits core files to tmp_core_dir_for_diff)
                # Note: CoreEmitter copies files, RenderContext isn't strictly needed for it, but path must be correct.
                relative_core_path_for_emitter_init_temp = os.path.relpath(tmp_core_dir_for_diff, tmp_out_dir_for_diff)
                core_emitter = CoreEmitter(
                    core_dir=str(relative_core_path_for_emitter_init_temp), core_package=resolved_core_package_fqn
                )
                temp_generated_files += [Path(p) for p in core_emitter.emit(str(tmp_out_dir_for_diff))]

                # 2. ExceptionsEmitter (emits exception_aliases.py to tmp_core_dir_for_diff)
                exceptions_emitter = ExceptionsEmitter(
                    core_package_name=resolved_core_package_fqn,
                    overall_project_root=str(tmp_project_root_for_diff),  # Use temp project root for context
                )
                temp_generated_files += [
                    Path(p)
                    for p in exceptions_emitter.emit(ir, str(tmp_core_dir_for_diff))  # Emit TO temp core dir
                ]

                # 3. config.py (write to tmp_core_dir_for_diff using FileManager) - REMOVED, CoreEmitter handles this
                # fm = FileManager()
                # config_dst_temp = tmp_core_dir_for_diff / "config.py"
                # config_content = CONFIG_TEMPLATE
                # fm.write_file(str(config_dst_temp), config_content)
                # temp_generated_files.append(config_dst_temp)

                # 4. ModelsEmitter (emits models to tmp_out_dir_for_diff/models)
                models_emitter = ModelsEmitter(
                    overall_project_root=str(tmp_project_root_for_diff),  # Use temp project root for context
                    core_package_name=resolved_core_package_fqn,
                )
                temp_generated_files += [
                    Path(p)
                    for p in models_emitter.emit(ir, str(tmp_out_dir_for_diff))  # Emit TO temp output dir
                ]

                # 5. EndpointsEmitter (emits endpoints to tmp_out_dir_for_diff/endpoints)
                endpoints_emitter = EndpointsEmitter(
                    core_package=resolved_core_package_fqn,
                    overall_project_root=str(tmp_project_root_for_diff),  # Use temp project root
                )
                temp_generated_files += [
                    Path(p)
                    for p in endpoints_emitter.emit(ir, str(tmp_out_dir_for_diff))  # Emit TO temp output dir
                ]

                # 6. ClientEmitter (emits client.py to tmp_out_dir_for_diff)
                client_emitter = ClientEmitter(
                    core_package=resolved_core_package_fqn,
                    overall_project_root=str(tmp_project_root_for_diff),  # Use temp project root
                )
                temp_generated_files += [
                    Path(p)
                    for p in client_emitter.emit(ir, str(tmp_out_dir_for_diff))  # Emit TO temp output dir
                ]

                # Post-processing should run on the temporary files if enabled
                if not no_postprocess:
                    # Pass the temp project root to PostprocessManager
                    PostprocessManager(str(tmp_project_root_for_diff)).run([str(p) for p in temp_generated_files])

                # --- Compare final output dirs with the temp output dirs ---
                # Compare client package dir
                has_diff_client = self._show_diffs(str(out_dir), str(tmp_out_dir_for_diff))
                # Compare core package dir IF it's different from the client dir
                has_diff_core = False
                if core_dir != out_dir:
                    has_diff_core = self._show_diffs(str(core_dir), str(tmp_core_dir_for_diff))

                if has_diff_client or has_diff_core:
                    raise GenerationError("Differences found between generated and existing output.")

                # If no diffs, return the paths of the *existing* files (no changes made)
                # We need to collect the actual existing file paths corresponding to temp_generated_files
                # This is tricky because _show_diffs only returns bool.
                # A simpler approach if no diff: do nothing, return empty list? Or paths of existing files?
                # Let's return the existing paths for consistency with the `else` block.
                # Need to map temp_generated_files back to original project_root based paths.
                final_generated_files = []
                for tmp_file in temp_generated_files:
                    try:
                        # Find relative path from temp root
                        rel_path = tmp_file.relative_to(tmp_project_root_for_diff)
                        # Construct path relative to final project root
                        final_path = project_root / rel_path
                        if final_path.exists():  # Should exist if no diff
                            final_generated_files.append(final_path)
                    except ValueError:
                        # Should not happen if paths are constructed correctly
                        print(f"Warning: Could not map temporary file {tmp_file} back to project root {project_root}")
                generated_files = final_generated_files

            # --- End Refactored Diff Logic ---
        else:  # This is the force=True or first-run logic
            if out_dir.exists():
                shutil.rmtree(str(out_dir))
            # Ensure parent dirs exist before creating final output dir
            out_dir.parent.mkdir(parents=True, exist_ok=True)
            out_dir.mkdir(parents=True, exist_ok=True)  # Create final output dir

            # Ensure core dir exists if different from out_dir
            if core_dir != out_dir:
                core_dir.parent.mkdir(parents=True, exist_ok=True)
                core_dir.mkdir(parents=True, exist_ok=True)  # Create final core dir

            # Write root __init__.py if needed (handle nested packages like a.b.c)
            current = out_dir
            while current != project_root:
                init_path = current / "__init__.py"
                if not init_path.exists():
                    init_path.write_text("")
                if current.parent == current:  # Avoid infinite loop at root
                    break
                current = current.parent

            # If core_dir is outside out_dir structure, ensure its __init__.py exist too
            if not str(core_dir).startswith(str(out_dir)):
                current = core_dir
                while current != project_root:
                    init_path = current / "__init__.py"
                    if not init_path.exists():
                        init_path.write_text("")
                    if current.parent == current:
                        break
                    current = current.parent

            # --- Generate directly into final destination paths ---
            # 1. CoreEmitter
            relative_core_path_for_emitter_init_final = os.path.relpath(core_dir, out_dir)
            core_emitter = CoreEmitter(
                core_dir=str(relative_core_path_for_emitter_init_final), core_package=resolved_core_package_fqn
            )
            generated_files += [Path(p) for p in core_emitter.emit(str(out_dir))]

            # 2. ExceptionsEmitter
            exceptions_emitter = ExceptionsEmitter(
                core_package_name=resolved_core_package_fqn,
                overall_project_root=str(project_root),  # Use final project root
            )
            generated_files += [
                Path(p)
                for p in exceptions_emitter.emit(ir, str(core_dir))  # Emit to final core dir
            ]

            # 3. config.py (using FileManager) - REMOVED, CoreEmitter handles this
            # fm = FileManager()
            # config_dst = core_dir / "config.py"
            # config_content = CONFIG_TEMPLATE
            # fm.write_file(str(config_dst), config_content) # Use FileManager
            # generated_files.append(config_dst)

            # 4. ModelsEmitter
            models_emitter = ModelsEmitter(
                overall_project_root=str(project_root),  # Use final project root
                core_package_name=resolved_core_package_fqn,
            )
            generated_files += [
                Path(p)
                for p in models_emitter.emit(ir, str(out_dir))  # Emit to final output dir
            ]

            # 5. EndpointsEmitter
            endpoints_emitter = EndpointsEmitter(
                core_package=resolved_core_package_fqn,
                overall_project_root=str(project_root),  # Use final project root
            )
            generated_files += [
                Path(p)
                for p in endpoints_emitter.emit(ir, str(out_dir))  # Emit to final output dir
            ]

            # 6. ClientEmitter
            client_emitter = ClientEmitter(
                core_package=resolved_core_package_fqn,
                overall_project_root=str(project_root),  # Use final project root
            )
            generated_files += [
                Path(p)
                for p in client_emitter.emit(ir, str(out_dir))  # Emit to final output dir
            ]

            # Post-processing on the final generated files
            if not no_postprocess:
                PostprocessManager(str(project_root)).run([str(p) for p in generated_files])

        return generated_files

    def _load_spec(self, path_or_url: str) -> dict[str, Any]:
        """
        Load a spec from a file path or URL.
        Args:
            path_or_url (str): Path or URL to the OpenAPI spec.
        Returns:
            dict[str, Any]: Parsed OpenAPI spec.
        Raises:
            GenerationError: If loading fails or URL loading is not implemented.
        """
        if Path(path_or_url).exists():
            import yaml

            data = yaml.safe_load(Path(path_or_url).read_text())
            if not isinstance(data, dict):
                raise GenerationError("Loaded spec is not a dictionary.")
            return data
        raise GenerationError("URL loading not implemented")

    def _show_diffs(self, old_dir: str, new_dir: str) -> bool:
        """
        Compare two directories and print diffs, returning True if any differences.
        Args:
            old_dir (str): Path to the old directory.
            new_dir (str): Path to the new directory.
        Returns:
            bool: True if differences are found, False otherwise.
        """
        import difflib

        has_diff = False
        for new_file in Path(new_dir).rglob("*.py"):
            old_file = Path(old_dir) / new_file.relative_to(new_dir)
            if old_file.exists():
                old_lines = old_file.read_text().splitlines()
                new_lines = new_file.read_text().splitlines()
                diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=str(old_file), tofile=str(new_file)))
                if diff:
                    has_diff = True
                    print("\n".join(diff))
        return has_diff
