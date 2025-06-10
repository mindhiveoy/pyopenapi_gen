import json
from pathlib import Path

import pytest

from pyopenapi_gen.generator.client_generator import ClientGenerator, GenerationError


def test_backup_diff_exits_non_zero_on_changes(tmp_path: Path) -> None:
    """Running gen twice without --force and modifying output should trigger diff and raise GenerationError."""
    # Prepare minimal spec
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Diff API", "version": "1.0.0"},
        "paths": {
            "/ping": {
                "get": {
                    "operationId": "ping",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))
    # Define output package and determine directory
    output_package = "my_client.api"
    project_root = tmp_path

    generator = ClientGenerator()
    # First run with force to create baseline
    generator.generate(
        spec_path=str(spec_file),
        project_root=project_root,
        output_package=output_package,
        core_package=None,  # Let it default to output_package + ".core"
        force=True,
        no_postprocess=True,
    )

    # Modify a generated file to simulate change
    resolved_core_package_fqn = output_package + ".core"  # Generator's default logic
    core_dir = project_root / Path(*resolved_core_package_fqn.split("."))  # Corrected
    config_py = core_dir / "config.py"
    assert config_py.exists(), f"Config file {config_py} was not generated in the expected location."
    original = config_py.read_text()
    config_py.write_text(original + "\n# changed by test")

    # Second run without force should detect diff and raise GenerationError
    with pytest.raises(GenerationError) as excinfo:
        generator.generate(
            spec_path=str(spec_file),
            project_root=project_root,
            output_package=output_package,
            core_package=None,  # Let it default to output_package + ".core"
            force=False,  # Important: force=False triggers diff check
            no_postprocess=True,
        )
    # Assert that the error message indicates differences were found
    assert "Differences found" in str(excinfo.value)
