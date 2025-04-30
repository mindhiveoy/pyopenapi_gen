import json
import os
import subprocess
from pathlib import Path

from pyopenapi_gen.cli import app
from typer.testing import CliRunner

# Minimal Petstore-like spec for integration test
MIN_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Demo API", "version": "1.0.0"},
    "paths": {
        "/pets": {
            "get": {
                "operationId": "list_pets",
                "summary": "List pets",
                "responses": {"200": {"description": "OK"}},
            }
        }
    },
}


def test_petstore_integration_with_tag(tmp_path: Path) -> None:
    """
    Scenario:
        Generate client for a minimal spec with a tag and verify output files.
    Expected Outcome:
        pets.py endpoint is generated and contains the list_pets method.
    """
    # Arrange
    spec = json.loads(json.dumps(MIN_SPEC))
    spec["paths"]["/pets"]["get"]["tags"] = ["pets"]
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))
    out_dir = tmp_path / "out"
    runner = CliRunner()
    # Act
    result = runner.invoke(
        app,
        ["gen", str(spec_file), "-o", str(out_dir), "--force", "--no-postprocess"],
    )
    # Assert
    assert result.exit_code == 0, result.stdout
    assert (out_dir / "config.py").exists(), "config.py not generated"
    assert (out_dir / "client.py").exists(), "client.py not generated"
    pets_file = out_dir / "endpoints" / "pets.py"
    assert pets_file.exists(), "pets.py endpoint not generated"
    content = pets_file.read_text()
    assert "async def list_pets" in content, "list_pets method missing in generated code"

    # Run mypy on the generated code to ensure type correctness
    env = os.environ.copy()
    # Add both the generated output parent and the real src directory to PYTHONPATH
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    env["PYTHONPATH"] = os.pathsep.join([str(out_dir.parent.resolve()), src_dir, env.get("PYTHONPATH", "")])
    mypy_result = subprocess.run(["mypy", str(out_dir)], capture_output=True, text=True, env=env)
    assert mypy_result.returncode == 0, f"mypy errors:\n{mypy_result.stdout}\n{mypy_result.stderr}"


def test_petstore_integration_no_tag(tmp_path: Path) -> None:
    """
    Scenario:
        Generate client for a minimal spec with no tags and verify output files.
    Expected Outcome:
        default.py endpoint is generated and contains the list_pets method.
    """
    # Arrange
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(MIN_SPEC))
    out_dir = tmp_path / "out"
    runner = CliRunner()
    # Act
    result = runner.invoke(
        app,
        ["gen", str(spec_file), "-o", str(out_dir), "--force", "--no-postprocess"],
    )
    # Assert
    assert result.exit_code == 0, result.stdout
    assert (out_dir / "config.py").exists(), "config.py not generated"
    assert (out_dir / "client.py").exists(), "client.py not generated"
    default_file = out_dir / "endpoints" / "default.py"
    assert default_file.exists(), "default.py endpoint not generated"
    content = default_file.read_text()
    assert "async def list_pets" in content, "list_pets method missing in generated code"

    # Run mypy on the generated code to ensure type correctness
    env = os.environ.copy()
    # Add both the generated output parent and the real src directory to PYTHONPATH
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    env["PYTHONPATH"] = os.pathsep.join([str(out_dir.parent.resolve()), src_dir, env.get("PYTHONPATH", "")])
    mypy_result = subprocess.run(["mypy", str(out_dir)], capture_output=True, text=True, env=env)
    assert mypy_result.returncode == 0, f"mypy errors:\n{mypy_result.stdout}\n{mypy_result.stderr}"
