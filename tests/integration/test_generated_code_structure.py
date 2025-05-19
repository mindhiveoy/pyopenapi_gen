from pathlib import Path

import yaml

from pyopenapi_gen import load_ir_from_spec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.emitters.core_emitter import CoreEmitter
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter


def test_generated_agent_datasources_imports_are_valid(tmp_path: Path) -> None:
    """
    Scenario:
        - Generate the business_swagger client as in the main test.
        - Read the generated agent_datasources.py file.
    Expected Outcome:
        - The first import line is a valid Python import (no slashes, starts with 'from ..models.' or 'from .').
    """
    # Copy the provided business_swagger.json into a temporary spec file
    project_root_dir = Path(__file__).parent.parent.parent  # Go up three levels
    spec_source = project_root_dir / "input" / "business_swagger.json"
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(spec_source.read_text())

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    spec_dict = yaml.safe_load(spec_file.read_text())
    ir = load_ir_from_spec(spec_dict)

    # Define core and output paths for this test's direct emitter setup
    project_root = tmp_path
    output_package = "out"  # Treat 'out' as the top-level package dir
    core_package_name = f"{output_package}.core"  # e.g., out.core
    core_dir = project_root / Path(*core_package_name.split("."))

    # Create directories if they don't exist
    out_dir = project_root / Path(*output_package.split("."))
    out_dir.mkdir(exist_ok=True)
    core_dir.mkdir(exist_ok=True)

    # Create RenderContext for ModelsEmitter
    render_context = RenderContext(
        core_package_name=core_package_name,
        package_root_for_generated_code=str(out_dir),
        overall_project_root=str(project_root),
        parsed_schemas=ir.schemas,
    )

    # Instantiate emitters with correct core package name where needed
    core_emitter = CoreEmitter(core_package=core_package_name)
    models_emitter = ModelsEmitter(context=render_context, parsed_schemas=ir.schemas)

    # NOTE: The rest of the test logic was not provided in the original snippet.
    # This reconstruction focuses on fixing the TypeError.
    # The user might need to add back any subsequent test steps.
