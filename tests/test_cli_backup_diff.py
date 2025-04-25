import json
from pathlib import Path
from typer.testing import CliRunner
from pyopenapi_gen.cli import app


def test_backup_diff_exits_non_zero_on_changes(tmp_path: Path):
    """Running gen twice without --force and modifying output should trigger diff and exit non-zero."""
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
    out_dir = tmp_path / "out"
    runner = CliRunner()

    # First run with force to create baseline
    result1 = runner.invoke(
        app,
        ["gen", str(spec_file), "-o", str(out_dir), "--force"],
    )
    assert result1.exit_code == 0, result1.stdout

    # Modify a generated file to simulate change
    client_py = out_dir / "client.py"
    original = client_py.read_text()
    client_py.write_text(original + "\n# changed by test")

    # Second run without force should detect diff and exit 1
    result2 = runner.invoke(
        app,
        ["gen", str(spec_file), "-o", str(out_dir)],
    )
    assert result2.exit_code == 1
    # Diff output should include our change marker
    assert "# changed by test" in result2.stdout
