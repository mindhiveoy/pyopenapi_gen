import os
import subprocess
from pathlib import Path

import yaml
from pyopenapi_gen.core.loader import load_ir_from_spec
from pyopenapi_gen.emitters.client_emitter import ClientEmitter
from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter


def test_business_swagger_generation(tmp_path: Path) -> None:
    """
    Scenario:
        - Generate the client for the business_swagger.json spec using direct emitter calls.
        - Verify all expected files are generated.
    Expected Outcome:
        - config.py, client.py, and endpoint modules are present and correct.
    """
    # Arrange
    spec_source = Path(__file__).parent / "input" / "business_swagger.json"
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(spec_source.read_text())
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    # Act
    spec_dict = yaml.safe_load(spec_file.read_text())
    ir = load_ir_from_spec(spec_dict)
    ModelsEmitter().emit(ir, str(out_dir))
    EndpointsEmitter().emit(ir, str(out_dir))
    ClientEmitter().emit(ir, str(out_dir))

    # Assert
    assert (out_dir / "config.py").exists(), "config.py not generated"
    assert (out_dir / "client.py").exists(), "client.py not generated"
    endpoints_dir = out_dir / "endpoints"
    assert endpoints_dir.exists(), "endpoints directory not generated"
    assert (endpoints_dir / "__init__.py").exists(), "__init__.py missing in endpoints"
    py_files = [p for p in endpoints_dir.glob("*.py") if p.name != "__init__.py"]
    assert py_files, "no endpoint modules generated"

    # Run mypy on the generated code to ensure type correctness
    env = os.environ.copy()
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    env["PYTHONPATH"] = os.pathsep.join([str(out_dir.parent.resolve()), src_dir, env.get("PYTHONPATH", "")])
    result = subprocess.run(["mypy", str(out_dir)], capture_output=True, text=True, env=env)
    assert result.returncode == 0, f"mypy errors:\n{result.stdout}\n{result.stderr}"


def test_generated_agent_datasources_imports_are_valid(tmp_path: Path) -> None:
    """
    Scenario:
        - Generate the business_swagger client as in the main test.
        - Read the generated agent_datasources.py file.
    Expected Outcome:
        - The first import line is a valid Python import (no slashes, starts with 'from ..models.' or 'from .').
    """
    # Copy the provided business_swagger.json into a temporary spec file
    spec_source = Path(__file__).parent / "input" / "business_swagger.json"
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(spec_source.read_text())

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    spec_dict = yaml.safe_load(spec_file.read_text())
    ir = load_ir_from_spec(spec_dict)
    ModelsEmitter().emit(ir, str(out_dir))
    EndpointsEmitter().emit(ir, str(out_dir))
    ClientEmitter().emit(ir, str(out_dir))

    assert (out_dir / "endpoints" / "agent_datasources.py").exists(), "agent_datasources.py not generated"
    content = (out_dir / "endpoints" / "agent_datasources.py").read_text().splitlines()
    # Find the first non-empty, non-comment line that is a relative import
    first_relative_import = next(
        (line for line in content if line.strip().startswith("from ..models.") or line.strip().startswith("from .")),
        "",
    )
    assert first_relative_import, "No relative import found in agent_datasources.py"
    assert "/" not in first_relative_import, f"Relative import line contains a slash: {first_relative_import}"
