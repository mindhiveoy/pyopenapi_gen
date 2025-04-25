from pathlib import Path
from typer.testing import CliRunner
import json

from pyopenapi_gen.cli import app

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


def test_petstore_integration(tmp_path: Path) -> None:
    """End‑to‑end test: generate client for a minimal spec and verify output files."""
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(MIN_SPEC))
    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["gen", str(spec_file), "-o", str(out_dir), "--force"],
    )
    # CLI should succeed
    assert result.exit_code == 0, result.stdout

    # Check core files
    assert (out_dir / "config.py").exists(), "config.py not generated"
    assert (out_dir / "client.py").exists(), "client.py not generated"
    # Check endpoints for pets
    pets_file = out_dir / "endpoints" / "pets.py"
    assert pets_file.exists(), "pets.py endpoint not generated"
    content = pets_file.read_text()
    assert (
        "async def list_pets" in content
    ), "list_pets method missing in generated code"
