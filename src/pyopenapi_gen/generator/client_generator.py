"""
ClientGenerator: Encapsulates the OpenAPI client generation logic for use by CLI or other frontends.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional

from pyopenapi_gen.core.loader import load_ir_from_spec
from pyopenapi_gen.core.postprocess_manager import PostprocessManager
from pyopenapi_gen.core.warning_collector import WarningCollector
from pyopenapi_gen.emitters.client_emitter import ClientEmitter
from pyopenapi_gen.emitters.core_emitter import CONFIG_TEMPLATE, CoreEmitter
from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter


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
        core_package: str = "core",
    ) -> None:
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
            output_package = "client"
        out_dir = pkg_to_path(output_package)

        # Determine core_dir for correct subfolder logic
        shared_core = core_package and core_package != output_package + ".core"
        if not core_package:
            core_package = output_package + ".core"
        if shared_core:
            core_dir = pkg_to_path(core_package)
        else:
            core_dir = out_dir / "core"
        generated_files = []

        if not force and out_dir.exists():
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_output = Path(tmpdir) / "out"
                tmp_output.mkdir(parents=True, exist_ok=True)
                root_init_path = tmp_output / "__init__.py"
                if not root_init_path.exists():
                    root_init_path.write_text("")
                generated_files += [
                    Path(p)
                    for p in CoreEmitter(
                        core_dir="",
                        core_package=core_package,
                    ).emit(str(core_dir))
                ]
                # Write config.py to the core directory (not client root)
                config_dst = core_dir / "config.py"
                config_dst.write_text(CONFIG_TEMPLATE)
                generated_files.append(config_dst)
                generated_files += [
                    Path(p) for p in ModelsEmitter(core_import_path=core_package).emit(ir, str(out_dir))
                ]
                generated_files += [
                    Path(p) for p in EndpointsEmitter(core_import_path=core_package).emit(ir, str(out_dir))
                ]
                generated_files += [
                    Path(p)
                    for p in ClientEmitter(core_package=core_package, core_import_path=core_package).emit(
                        ir, str(out_dir)
                    )
                ]
                if not no_postprocess:
                    PostprocessManager().run([str(p) for p in generated_files])
                has_diff = self._show_diffs(str(out_dir), str(tmp_output))
                if has_diff:
                    raise GenerationError("Differences found between generated and existing output.")
                shutil.rmtree(str(out_dir))
                shutil.copytree(str(tmp_output), str(out_dir))
        else:
            if out_dir.exists():
                shutil.rmtree(str(out_dir))
            out_dir.mkdir(parents=True, exist_ok=True)
            root_init_path = out_dir / "__init__.py"
            if not root_init_path.exists():
                root_init_path.write_text("")
            generated_files += [
                Path(p)
                for p in CoreEmitter(
                    core_dir="",
                    core_package=core_package,
                ).emit(str(core_dir))
            ]
            # Write config.py to the core directory (not client root)
            config_dst = core_dir / "config.py"
            config_dst.write_text(CONFIG_TEMPLATE)
            generated_files.append(config_dst)
            generated_files += [Path(p) for p in ModelsEmitter(core_import_path=core_package).emit(ir, str(out_dir))]
            generated_files += [Path(p) for p in EndpointsEmitter(core_import_path=core_package).emit(ir, str(out_dir))]
            generated_files += [
                Path(p)
                for p in ClientEmitter(core_package=core_package, core_import_path=core_package).emit(ir, str(out_dir))
            ]
            if not no_postprocess:
                PostprocessManager().run([str(p) for p in generated_files])

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
