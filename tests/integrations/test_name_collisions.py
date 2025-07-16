import logging
import os
import re
import subprocess
from pathlib import Path

import yaml

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.emitters.client_emitter import ClientEmitter
from pyopenapi_gen.emitters.core_emitter import CoreEmitter
from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter
from pyopenapi_gen.emitters.exceptions_emitter import ExceptionsEmitter
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("pyopenapi_gen")
# logger.setLevel(logging.DEBUG)  # Uncomment for detailed logs during debugging


def test_name_collision_generation(tmp_path: Path) -> None:
    """
    Scenario:
        - Generate client from 'test_name_collision_spec.json'.
        - This spec contains schema names that would collide after sanitization.
    Expected Outcome:
        - The generator should handle these collisions gracefully, producing unique file/class names.
        - All internal references should be updated to the unique names.
        - mypy checks on the generated code should pass.
    """
    project_root_dir = Path(__file__).parent.parent.parent
    spec_source = project_root_dir / "input" / "test_name_collision_spec.json"

    assert spec_source.exists(), f"Test spec not found at {spec_source}"

    spec_file = tmp_path / "spec.json"
    spec_file.write_text(spec_source.read_text())
    out_dir_name = "collision_client"
    out_dir = tmp_path / out_dir_name
    out_dir.mkdir()

    spec_dict = yaml.safe_load(spec_file.read_text())
    ir = load_ir_from_spec(spec_dict)

    project_root_for_gen = tmp_path
    output_package = out_dir_name
    core_package_name = f"{output_package}.core"
    core_dir = project_root_for_gen / Path(*core_package_name.split("."))

    out_pkg_dir = project_root_for_gen / Path(*output_package.split("."))
    out_pkg_dir.mkdir(exist_ok=True)
    core_dir.mkdir(exist_ok=True)

    render_context = RenderContext(
        core_package_name=core_package_name,
        package_root_for_generated_code=str(out_pkg_dir),
        overall_project_root=str(project_root_for_gen),
        parsed_schemas=ir.schemas,  # Ensure parsed_schemas is passed
    )

    exceptions_emitter = ExceptionsEmitter(
        core_package_name=core_package_name, overall_project_root=str(project_root_for_gen)
    )
    _, exception_alias_names = exceptions_emitter.emit(ir, str(core_dir))

    core_emitter = CoreEmitter(core_package=core_package_name, exception_alias_names=exception_alias_names)
    # Pass ir.schemas directly to ModelsEmitter as it's expected to be non-Optional
    models_emitter = ModelsEmitter(context=render_context, parsed_schemas=ir.schemas)
    endpoints_emitter = EndpointsEmitter(context=render_context)
    client_emitter = ClientEmitter(context=render_context)

    core_emitter.emit(str(out_pkg_dir))
    models_emitter.emit(ir, str(out_pkg_dir))  # ModelsEmitter takes ir and output_dir
    endpoints_emitter.emit(ir.operations, str(out_pkg_dir))
    client_emitter.emit(ir, str(out_pkg_dir))

    # Assert basic file generation (more specific checks after collision strategy)
    assert (core_dir / "__init__.py").exists(), "core/__init__.py not generated"
    assert (out_pkg_dir / "client.py").exists(), "client.py not generated"
    models_path = out_pkg_dir / "models"
    assert models_path.exists(), "models directory not generated"
    assert (models_path / "__init__.py").exists(), "models/__init__.py not generated"

    # Expected sanitized module names (before collision handling adds suffixes)
    expected_raw_module_foo = NameSanitizer.sanitize_module_name("Foo-Bar")  # Should be foo_bar
    expected_raw_module_user = NameSanitizer.sanitize_module_name("user")  # Should be user

    # Assert that collision handling created distinct files
    # Example: foo_bar.py and foo_bar_2.py (or similar for user)
    # These assertions will FAIL until collision handling is implemented
    assert (models_path / f"{expected_raw_module_foo}.py").exists(), "Expected base model file foo_bar.py not found"
    assert (
        models_path / f"{expected_raw_module_foo}_2.py"
    ).exists(), "Expected collision-handled model file foo_bar_2.py not found"
    assert (models_path / f"{expected_raw_module_user}.py").exists(), "Expected base model file user.py not found"
    assert (
        models_path / f"{expected_raw_module_user}_2.py"
    ).exists(), "Expected collision-handled model file user_2.py not found"

    # Check __init__.py for exports (names will depend on class name sanitization strategy)
    # e.g., from .foo_bar import FooBar; from .foo_bar_2 import FooBar2
    init_content = (models_path / "__init__.py").read_text()
    assert "from .foo_bar import FooBar" in init_content  # This will likely need adjustment
    assert "from .foo_bar_2 import FooBar2" in init_content  # This will likely need adjustment
    assert "from .user import User" in init_content  # This will likely need adjustment
    assert "from .user_2 import User2" in init_content  # This will likely need adjustment

    all_export_names = []
    # Use regex to find the __all__ list, allowing for optional type hint
    match = re.search(r"__all__(?::\s*List\[str\])?\s*=\s*\[([^\]]*)\]", init_content)
    if match:
        all_section = match.group(1)
        all_export_names = [name.strip().strip('"').strip("'") for name in all_section.split(",") if name.strip()]

    assert "FooBar" in all_export_names, f"'FooBar' not in __all__: {all_export_names}"
    assert "FooBar2" in all_export_names  # This will likely need adjustment
    assert "User" in all_export_names
    assert "User2" in all_export_names  # This will likely need adjustment

    model_files = list(models_path.glob("*.py"))
    assert any(f.name != "__init__.py" for f in model_files), "No model .py files generated in models/"

    logger.info(f"Generated files in models dir: {[f.name for f in model_files]}")

    # Run mypy
    env = os.environ.copy()
    # Adjust PYTHONPATH to include the root of the generated package and the project's src
    src_dir_path = project_root_dir / "src"
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(tmp_path.resolve()),  # Root of generated client 'collision_client'
            str(src_dir_path.resolve()),  # Project src for pyopenapi_gen itself if needed by generated core utils
            env.get("PYTHONPATH", ""),
        ]
    )

    packages_to_check = [output_package.split(".")[0]]  # e.g., ['collision_client']

    mypy_output_log_dir = project_root_dir / "test_outputs"
    mypy_output_log_dir.mkdir(parents=True, exist_ok=True)
    mypy_output_filename = mypy_output_log_dir / "mypy_name_collision_errors.txt"

    mypy_command = ["mypy", "--strict"] + packages_to_check
    logger.info(f"Running mypy command: {' '.join(mypy_command)} from cwd: {tmp_path}")
    logger.info(f"PYTHONPATH for mypy: {env.get('PYTHONPATH')}")

    mypy_result = subprocess.run(
        mypy_command,
        capture_output=True,
        text=True,  # Changed to True for easier string handling
        env=env,
        cwd=tmp_path,  # Run mypy from the directory containing 'collision_client'
    )

    mypy_output_content = f"Mypy STDOUT:\n{mypy_result.stdout}\n\nMypy STDERR:\n{mypy_result.stderr}"
    Path(mypy_output_filename).write_text(mypy_output_content, encoding="utf-8")

    assert (
        mypy_result.returncode == 0
    ), f"mypy errors (see full output in {mypy_output_filename.relative_to(project_root_dir)}):\n{mypy_output_content}"
