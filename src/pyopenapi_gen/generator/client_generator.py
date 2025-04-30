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
from pyopenapi_gen.emitters.core_emitter import CoreEmitter
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
        output: Path,
        force: bool = False,
        name: Optional[str] = None,
        docs: bool = False,  # Kept for interface compatibility
        telemetry: bool = False,  # Kept for interface compatibility
        auth: Optional[str] = None,  # Kept for interface compatibility
        no_postprocess: bool = False,
        core_package: str = "core",
    ) -> None:
        """
        Generate the client code from the OpenAPI spec.

        Args:
            spec_path (str): Path or URL to the OpenAPI spec file.
            output (Path): Output directory for the generated client.
            force (bool): Overwrite output without diff check.
            name (Optional[str]): Custom client package name (not used).
            docs (bool): Kept for interface compatibility.
            telemetry (bool): Kept for interface compatibility.
            auth (Optional[str]): Kept for interface compatibility.
            no_postprocess (bool): Skip post-processing (type checking, etc.).
            core_package (str): Name of the core package/folder.

        Raises:
            GenerationError: If generation fails or diffs are found (when not forcing overwrite).
        """
        spec_dict = self._load_spec(spec_path)
        ir = load_ir_from_spec(spec_dict)
        collector = WarningCollector()
        reports = collector.collect(ir)
        for report in reports:
            print(f"WARNING [{report.code}]: {report.message} (Hint: {report.hint})")

        out_dir = str(output)
        generated_files = []

        if not force and output.exists():
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_output = Path(tmpdir) / "out"
                tmp_output.mkdir(parents=True, exist_ok=True)
                root_init_path = tmp_output / "__init__.py"
                if not root_init_path.exists():
                    root_init_path.write_text("")
                generated_files += [
                    Path(p) for p in CoreEmitter(core_dir=core_package, core_package=core_package).emit(str(tmp_output))
                ]
                generated_files += [Path(p) for p in ModelsEmitter().emit(ir, str(tmp_output))]
                generated_files += [Path(p) for p in EndpointsEmitter().emit(ir, str(tmp_output))]
                generated_files += [Path(p) for p in ClientEmitter(core_package=core_package).emit(ir, str(tmp_output))]
                if not no_postprocess:
                    PostprocessManager().run([str(p) for p in generated_files])
                has_diff = self._show_diffs(str(output), str(tmp_output))
                if has_diff:
                    raise GenerationError("Differences found between generated and existing output.")
                shutil.rmtree(out_dir)
                shutil.copytree(str(tmp_output), out_dir)
        else:
            if output.exists():
                shutil.rmtree(out_dir)
            output.mkdir(parents=True, exist_ok=True)
            root_init_path = output / "__init__.py"
            if not root_init_path.exists():
                root_init_path.write_text("")
            generated_files += [
                Path(p) for p in CoreEmitter(core_dir=core_package, core_package=core_package).emit(out_dir)
            ]
            generated_files += [Path(p) for p in ModelsEmitter().emit(ir, out_dir)]
            generated_files += [Path(p) for p in EndpointsEmitter().emit(ir, out_dir)]
            generated_files += [Path(p) for p in ClientEmitter(core_package=core_package).emit(ir, out_dir)]
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
