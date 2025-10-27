"""
ClientGenerator: Encapsulates the OpenAPI client generation logic for use by CLI or other frontends.
"""

import logging
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, List

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.core.postprocess_manager import PostprocessManager
from pyopenapi_gen.core.warning_collector import WarningCollector
from pyopenapi_gen.emitters.client_emitter import ClientEmitter
from pyopenapi_gen.emitters.core_emitter import CoreEmitter
from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter
from pyopenapi_gen.emitters.exceptions_emitter import ExceptionsEmitter
from pyopenapi_gen.emitters.mocks_emitter import MocksEmitter
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter

logger = logging.getLogger(__name__)


class GenerationError(Exception):
    """Raised when client generation fails due to errors or diffs."""

    pass


class ClientGenerator:
    """
    Generates a Python OpenAPI client package from a given OpenAPI spec file or URL.

    This class encapsulates all logic for code generation, diffing, post-processing, and output management.
    It is independent of any CLI or UI framework and can be used programmatically.
    """

    def __init__(self, verbose: bool = True) -> None:
        """
        Initialize the client generator.

        Args:
            verbose: Whether to output detailed progress information.
        """
        self.verbose = verbose
        self.start_time = time.time()
        self.timings: dict[str, float] = {}

    def _log_progress(self, message: str, stage: str | None = None) -> None:
        """
        Log a progress message with timestamp.

        Args:
            message: The progress message to log.
            stage: Optional name of the current stage for timing information.
        """
        if not self.verbose:
            return

        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S")

        if stage:
            # Mark stage start
            if stage not in self.timings:
                self.timings[stage] = time.time()
                stage_msg = f"[STARTING {stage}]"
            else:
                # Mark stage end
                stage_time = time.time() - self.timings[stage]
                stage_msg = f"[COMPLETED {stage} in {stage_time:.2f}s]"

            log_msg = f"{timestamp} ({elapsed:.2f}s) {stage_msg} {message}"
        else:
            log_msg = f"{timestamp} ({elapsed:.2f}s) {message}"

        logger.info(log_msg)
        # Also print to stdout for CLI users when verbose mode is enabled
        if self.verbose:
            print(log_msg)

    def generate(
        self,
        spec_path: str,
        project_root: Path,
        output_package: str,
        force: bool = False,
        no_postprocess: bool = False,
        core_package: str | None = None,
    ) -> List[Path]:
        """
        Generate the client code from the OpenAPI spec.

        Args:
            spec_path (str): Path or URL to the OpenAPI spec file.
            project_root (Path): Path to the root of the Python project (absolute or relative).
            output_package (str): Python package path for the generated client (e.g., 'pyapis.my_api_client').
            force (bool): Overwrite output without diff check.
            name (str | None): Custom client package name (not used).
            docs (bool): Kept for interface compatibility.
            telemetry (bool): Kept for interface compatibility.
            auth (str | None): Kept for interface compatibility.
            no_postprocess (bool): Skip post-processing (type checking, etc.).
            core_package (str): Python package path for the core package.

        Raises:
            GenerationError: If generation fails or diffs are found (when not forcing overwrite).
        """
        self._log_progress(f"Starting code generation for specification: {spec_path}", "GENERATION")
        project_root = Path(project_root).resolve()

        # Stage 1: Load Spec
        self._log_progress(f"Loading specification from {spec_path}", "LOAD_SPEC")
        spec_dict = self._load_spec(spec_path)
        self._log_progress(f"Loaded specification with {len(spec_dict)} top-level keys", "LOAD_SPEC")

        # Stage 2: Parse to IR
        self._log_progress(f"Parsing specification into intermediate representation", "PARSE_IR")
        ir = load_ir_from_spec(spec_dict)

        # Log stats about the IR
        schema_count = len(ir.schemas) if ir.schemas else 0
        operation_count = len(ir.operations) if ir.operations else 0
        self._log_progress(f"Parsed IR with {schema_count} schemas and {operation_count} operations", "PARSE_IR")

        # Stage 3: Collect warnings
        self._log_progress("Collecting warnings", "WARNINGS")
        collector = WarningCollector()
        reports = collector.collect(ir)
        for report in reports:
            warning_msg = f"WARNING [{report.code}]: {report.message} (Hint: {report.hint})"
            # print(warning_msg) # Changed to logger.warning
            logger.warning(warning_msg)
        self._log_progress(f"Found {len(reports)} warnings", "WARNINGS")

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

        self._log_progress(f"Output directory: {out_dir}", "CONFIG")
        self._log_progress(f"Core package: {resolved_core_package_fqn}", "CONFIG")

        generated_files = []

        # Create RenderContext once and populate its parsed_schemas for the force=True path
        # It will be used if not doing a diff, or after a successful diff.
        self._log_progress("Creating render context", "INIT")
        main_render_context = RenderContext(
            core_package_name=resolved_core_package_fqn,
            package_root_for_generated_code=str(out_dir),
            overall_project_root=str(project_root),
            parsed_schemas=ir.schemas,
            output_package_name=output_package,
        )

        if not force and out_dir.exists():
            self._log_progress("Checking for differences with existing output", "DIFF_CHECK")
            # --- Refactored Diff Logic ---
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_project_root_for_diff = Path(tmpdir)

                # Define temporary destination paths based on the temp project root
                def tmp_pkg_to_path(pkg: str) -> Path:
                    # Ensure the path is relative to the temp root, not the final project root
                    return tmp_project_root_for_diff.joinpath(*pkg.split("."))

                tmp_out_dir_for_diff = tmp_pkg_to_path(output_package)
                tmp_core_dir_for_diff = tmp_pkg_to_path(resolved_core_package_fqn)

                # Ensure temporary directories exist (FileManager used by emitters might handle this,
                # but explicit is safer)
                tmp_out_dir_for_diff.mkdir(parents=True, exist_ok=True)
                tmp_core_dir_for_diff.mkdir(parents=True, exist_ok=True)  # Ensure core temp dir always exists

                # --- Generate files into the temporary structure ---
                temp_generated_files = []  # Track files generated in temp dir

                # 1. ExceptionsEmitter (emits exception_aliases.py to tmp_core_dir_for_diff)
                self._log_progress("Generating exception files (temp)", "EMIT_EXCEPTIONS_TEMP")
                exceptions_emitter = ExceptionsEmitter(
                    core_package_name=resolved_core_package_fqn,
                    overall_project_root=str(tmp_project_root_for_diff),  # Use temp project root for context
                )
                exception_files_list, exception_alias_names = exceptions_emitter.emit(
                    ir, str(tmp_core_dir_for_diff), client_package_name=output_package
                )  # Emit TO temp core dir
                exception_files = [Path(p) for p in exception_files_list]
                temp_generated_files += exception_files
                self._log_progress(f"Generated {len(exception_files)} exception files (temp)", "EMIT_EXCEPTIONS_TEMP")

                # 2. CoreEmitter (emits core files to tmp_core_dir_for_diff)
                self._log_progress("Generating core files (temp)", "EMIT_CORE_TEMP")
                # Note: CoreEmitter copies files, RenderContext isn't strictly needed for it, but path must be correct.
                relative_core_path_for_emitter_init_temp = os.path.relpath(tmp_core_dir_for_diff, tmp_out_dir_for_diff)
                core_emitter = CoreEmitter(
                    core_dir=str(relative_core_path_for_emitter_init_temp),
                    core_package=resolved_core_package_fqn,
                    exception_alias_names=exception_alias_names,
                )
                core_files = [Path(p) for p in core_emitter.emit(str(tmp_out_dir_for_diff))]
                temp_generated_files += core_files
                self._log_progress(f"Generated {len(core_files)} core files (temp)", "EMIT_CORE_TEMP")

                # 3. config.py (write to tmp_core_dir_for_diff using FileManager) - REMOVED, CoreEmitter handles this
                # fm = FileManager()
                # config_dst_temp = tmp_core_dir_for_diff / "config.py"
                # config_content = CONFIG_TEMPLATE
                # fm.write_file(str(config_dst_temp), config_content)
                # temp_generated_files.append(config_dst_temp)

                # 4. ModelsEmitter (emits models to tmp_out_dir_for_diff/models)
                self._log_progress("Generating model files (temp)", "EMIT_MODELS_TEMP")
                # Create a temporary RenderContext for the diff path
                tmp_render_context_for_diff = RenderContext(
                    core_package_name=resolved_core_package_fqn,
                    package_root_for_generated_code=str(tmp_out_dir_for_diff),
                    overall_project_root=str(tmp_project_root_for_diff),
                    parsed_schemas=ir.schemas,
                    output_package_name=output_package,
                )
                models_emitter = ModelsEmitter(context=tmp_render_context_for_diff, parsed_schemas=ir.schemas)
                model_files_dict = models_emitter.emit(
                    ir, str(tmp_out_dir_for_diff)
                )  # ModelsEmitter.emit now takes IRSpec
                temp_generated_files += [
                    Path(p) for p_list in model_files_dict.values() for p in p_list
                ]  # Flatten list of lists
                schema_count = len(ir.schemas) if ir.schemas else 0
                self._log_progress(
                    f"Generated {len(model_files_dict)} model files for {schema_count} schemas (temp)",
                    "EMIT_MODELS_TEMP",
                )

                # 5. EndpointsEmitter (emits endpoints to tmp_out_dir_for_diff/endpoints)
                self._log_progress("Generating endpoint files (temp)", "EMIT_ENDPOINTS_TEMP")
                endpoints_emitter = EndpointsEmitter(context=tmp_render_context_for_diff)
                endpoint_files = [
                    Path(p)
                    for p in endpoints_emitter.emit(
                        ir.operations, str(tmp_out_dir_for_diff)
                    )  # emit takes ir.operations, str output_dir
                ]
                temp_generated_files += endpoint_files
                operation_count = len(ir.operations) if ir.operations else 0
                self._log_progress(
                    f"Generated {len(endpoint_files)} endpoint files for {operation_count} operations (temp)",
                    "EMIT_ENDPOINTS_TEMP",
                )

                # 6. ClientEmitter (emits client.py to tmp_out_dir_for_diff)
                self._log_progress("Generating client file (temp)", "EMIT_CLIENT_TEMP")
                client_emitter = ClientEmitter(context=tmp_render_context_for_diff)  # ClientEmitter now takes context
                client_files = [
                    Path(p) for p in client_emitter.emit(ir, str(tmp_out_dir_for_diff))  # emit takes ir, str output_dir
                ]
                temp_generated_files += client_files
                self._log_progress(f"Generated {len(client_files)} client files (temp)", "EMIT_CLIENT_TEMP")

                # 7. MocksEmitter (emits mock files to tmp_out_dir_for_diff)
                self._log_progress("Generating mock helper classes (temp)", "EMIT_MOCKS_TEMP")
                mocks_emitter = MocksEmitter(context=tmp_render_context_for_diff)
                mock_files = [Path(p) for p in mocks_emitter.emit(ir, str(tmp_out_dir_for_diff))]
                temp_generated_files += mock_files
                self._log_progress(f"Generated {len(mock_files)} mock files (temp)", "EMIT_MOCKS_TEMP")

                # Post-processing should run on the temporary files if enabled
                if not no_postprocess:
                    self._log_progress("Running post-processing on temporary files", "POSTPROCESS_TEMP")
                    # Pass the temp project root to PostprocessManager
                    PostprocessManager(str(tmp_project_root_for_diff)).run([str(p) for p in temp_generated_files])
                    self._log_progress(f"Post-processed {len(temp_generated_files)} files", "POSTPROCESS_TEMP")

                # --- Compare final output dirs with the temp output dirs ---
                self._log_progress("Comparing generated files with existing files", "DIFF")
                # Compare client package dir
                self._log_progress(f"Checking client package differences", "DIFF_CLIENT")
                has_diff_client = self._show_diffs(str(out_dir), str(tmp_out_dir_for_diff))

                # Compare core package dir IF it's different from the client dir
                has_diff_core = False
                if core_dir != out_dir:
                    self._log_progress(f"Checking core package differences", "DIFF_CORE")
                    has_diff_core = self._show_diffs(str(core_dir), str(tmp_core_dir_for_diff))

                if has_diff_client or has_diff_core:
                    self._log_progress("Differences found, not updating existing output", "DIFF_RESULT")
                    raise GenerationError("Differences found between generated and existing output.")

                self._log_progress("No differences found, using existing files", "DIFF_RESULT")
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
                self._log_progress(f"Mapped {len(generated_files)} existing files", "DIFF_COMPLETE")

            # --- End Refactored Diff Logic ---
        else:  # This is the force=True or first-run logic
            self._log_progress("Direct generation (force=True or first run)", "DIRECT_GEN")
            if out_dir.exists():
                self._log_progress(f"Removing existing directory: {out_dir}", "CLEANUP")
                shutil.rmtree(str(out_dir))
            # Ensure parent dirs exist before creating final output dir
            self._log_progress(f"Creating directory structure", "SETUP_DIRS")
            out_dir.parent.mkdir(parents=True, exist_ok=True)
            out_dir.mkdir(parents=True, exist_ok=True)  # Create final output dir

            # Ensure core dir exists if different from out_dir
            if core_dir != out_dir:
                core_dir.parent.mkdir(parents=True, exist_ok=True)
                core_dir.mkdir(parents=True, exist_ok=True)  # Create final core dir

            # Write root __init__.py if needed (handle nested packages like a.b.c)
            self._log_progress("Creating __init__.py files for package structure", "INIT_FILES")
            init_files_created = 0
            current = out_dir
            while current != project_root:
                init_path = current / "__init__.py"
                if not init_path.exists():
                    init_path.write_text("")
                    init_files_created += 1
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
                        init_files_created += 1
                    if current.parent == current:
                        break
                    current = current.parent

            self._log_progress(f"Created {init_files_created} __init__.py files", "INIT_FILES")

            # --- Generate directly into final destination paths ---
            self._log_progress("Starting direct file generation", "DIRECT_GEN_FILES")

            # 1. ExceptionsEmitter
            self._log_progress("Generating exception files", "EMIT_EXCEPTIONS")
            exceptions_emitter = ExceptionsEmitter(
                core_package_name=resolved_core_package_fqn,
                overall_project_root=str(project_root),
            )
            exception_files_list, exception_alias_names = exceptions_emitter.emit(
                ir, str(core_dir), client_package_name=output_package
            )
            generated_files += [Path(p) for p in exception_files_list]
            self._log_progress(f"Generated {len(exception_files_list)} exception files", "EMIT_EXCEPTIONS")

            # 2. CoreEmitter
            self._log_progress("Generating core files", "EMIT_CORE")
            relative_core_path_for_emitter_init = os.path.relpath(core_dir, out_dir)
            core_emitter = CoreEmitter(
                core_dir=str(relative_core_path_for_emitter_init),
                core_package=resolved_core_package_fqn,
                exception_alias_names=exception_alias_names,
            )
            generated_files += [Path(p) for p in core_emitter.emit(str(out_dir))]
            self._log_progress(f"Generated {len(core_emitter.emit(str(out_dir)))} core files", "EMIT_CORE")

            # 3. config.py (using FileManager) - REMOVED, CoreEmitter handles this
            # fm = FileManager()
            # config_dst = core_dir / "config.py"
            # config_content = CONFIG_TEMPLATE
            # fm.write_file(str(config_dst), config_content) # Use FileManager
            # generated_files.append(config_dst)

            # 4. ModelsEmitter
            self._log_progress("Generating model files", "EMIT_MODELS")
            models_emitter = ModelsEmitter(context=main_render_context, parsed_schemas=ir.schemas)
            model_files_dict = models_emitter.emit(ir, str(out_dir))  # ModelsEmitter.emit now takes IRSpec
            generated_files += [
                Path(p) for p_list in model_files_dict.values() for p in p_list
            ]  # Flatten list of lists
            schema_count = len(ir.schemas) if ir.schemas else 0
            self._log_progress(
                f"Generated {len(model_files_dict)} model files for {schema_count} schemas",
                "EMIT_MODELS",
            )

            # 5. EndpointsEmitter
            self._log_progress("Generating endpoint files", "EMIT_ENDPOINTS")
            endpoints_emitter = EndpointsEmitter(context=main_render_context)
            generated_files += [
                Path(p) for p in endpoints_emitter.emit(ir.operations, str(out_dir))
            ]  # emit takes ir.operations, str output_dir
            operation_count = len(ir.operations) if ir.operations else 0
            self._log_progress(
                f"Generated {len(endpoints_emitter.emit(ir.operations, str(out_dir)))} "
                f"endpoint files for {operation_count} operations",
                "EMIT_ENDPOINTS",
            )

            # 6. ClientEmitter
            self._log_progress("Generating client file", "EMIT_CLIENT")
            client_emitter = ClientEmitter(context=main_render_context)  # ClientEmitter now takes context
            client_files = [Path(p) for p in client_emitter.emit(ir, str(out_dir))]  # emit takes ir, str output_dir
            generated_files += client_files
            self._log_progress(f"Generated {len(client_files)} client files", "EMIT_CLIENT")

            # 7. MocksEmitter
            self._log_progress("Generating mock helper classes", "EMIT_MOCKS")
            mocks_emitter = MocksEmitter(context=main_render_context)
            mock_files = [Path(p) for p in mocks_emitter.emit(ir, str(out_dir))]
            generated_files += mock_files
            self._log_progress(f"Generated {len(mock_files)} mock files", "EMIT_MOCKS")

            # After all emitters, if core_package is specified (external core),
            # create a rich __init__.py in the client's output_package (out_dir).
            if core_package:  # core_package is the user-provided original arg
                client_init_py_path = out_dir / "__init__.py"
                self._log_progress(
                    f"Generating rich __init__.py for client package at {client_init_py_path}", "CLIENT_INIT"
                )

                # Core components to re-export.
                # resolved_core_package_fqn is the correct fully qualified name to use for imports.
                core_imports = [
                    f"from {resolved_core_package_fqn}.auth import BaseAuth, ApiKeyAuth, BearerAuth, OAuth2Auth",
                    f"from {resolved_core_package_fqn}.config import ClientConfig",
                    f"from {resolved_core_package_fqn}.exceptions import HTTPError, ClientError, ServerError",
                    f"from {resolved_core_package_fqn}.exception_aliases import *  # noqa: F401, F403",
                    f"from {resolved_core_package_fqn}.http_transport import HttpTransport, HttpxTransport",
                    f"from {resolved_core_package_fqn}.schemas import BaseSchema",
                ]

                client_imports = [
                    "from .client import APIClient",
                ]

                all_list = [
                    '"APIClient",',
                    '"BaseAuth", "ApiKeyAuth", "BearerAuth", "OAuth2Auth",',
                    '"ClientConfig",',
                    '"HTTPError", "ClientError", "ServerError",',
                    # Names from exception_aliases are available via star import
                    '"HttpTransport", "HttpxTransport",',
                    '"BaseSchema",',
                ]

                init_content_lines = [
                    "# Client package __init__.py",
                    "# Re-exports from core and local client.",
                    "",
                ]
                init_content_lines.extend(core_imports)
                init_content_lines.extend(client_imports)
                init_content_lines.append("")
                init_content_lines.append("__all__ = [")
                for item in all_list:
                    init_content_lines.append(f"    {item}")
                init_content_lines.append("]")
                init_content_lines.append("")  # Trailing newline

                # Use FileManager from the main_render_context if available, or create one.
                # For simplicity here, just write directly.
                try:
                    with open(client_init_py_path, "w") as f:
                        f.write("\\n".join(init_content_lines))
                    generated_files.append(client_init_py_path)  # Track this generated file
                    self._log_progress(f"Successfully wrote rich __init__.py to {client_init_py_path}", "CLIENT_INIT")
                except IOError as e:
                    self._log_progress(f"ERROR: Failed to write client __init__.py: {e}", "CLIENT_INIT")
                    # Optionally re-raise or handle as a generation failure
                    raise GenerationError(f"Failed to write client __init__.py: {e}") from e

            # Post-processing applies to all generated files
            if not no_postprocess:
                self._log_progress("Running post-processing on generated files", "POSTPROCESS")
                PostprocessManager(str(project_root)).run([str(p) for p in generated_files])
                self._log_progress(f"Post-processed {len(generated_files)} files", "POSTPROCESS")

        total_time = time.time() - self.start_time
        self._log_progress(
            f"Code generation completed successfully in {total_time:.2f}s, generated {len(generated_files)} files",
            "GENERATION",
        )

        # Print timing summary if verbose
        if self.verbose:
            self._log_progress("=== Generation Summary ===", None)
            for stage, start_time in sorted(self.timings.items()):
                # Only include stages that have both start and end times
                if f"{stage}_COMPLETE" in self.timings or stage in self.timings:
                    end_time = self.timings.get(f"{stage}_COMPLETE", time.time())
                    duration = end_time - start_time
                    self._log_progress(f"{stage}: {duration:.2f}s", None)

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
        spec_path_obj = Path(path_or_url)
        if spec_path_obj.exists() and spec_path_obj.is_file():  # Added is_file() check
            text = spec_path_obj.read_text()
            # Prefer JSON for .json files to avoid optional PyYAML dependency in tests
            if spec_path_obj.suffix.lower() == ".json":
                import json

                data = json.loads(text)
            else:
                try:
                    import yaml

                    data = yaml.safe_load(text)
                except ModuleNotFoundError:
                    # Fallback: attempt JSON parsing if YAML is unavailable
                    import json

                    data = json.loads(text)

            if not isinstance(data, dict):
                raise GenerationError("Loaded spec is not a dictionary.")
            return data
        elif not spec_path_obj.exists():
            raise GenerationError(f"Specification file not found at {path_or_url}")
        elif not spec_path_obj.is_file():
            raise GenerationError(f"Specified path {path_or_url} is not a file.")
        else:  # Fallback, should ideally not be reached with current checks
            raise GenerationError(
                f"Failed to load spec from {path_or_url}. URL loading not implemented or path is invalid."
            )

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
