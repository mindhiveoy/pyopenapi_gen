import json
from pathlib import Path
from typer.testing import CliRunner
import pytest

from pyopenapi_gen.cli import app

# Minimal spec for code generation
MIN_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Edge API", "version": "1.0.0"},
    "paths": {
        "/status": {
            "get": {
                "operationId": "get_status",
                "responses": {"200": {"description": "OK"}},
            }
        }
    },
}


def test_gen_nonexistent_spec_path(tmp_path: Path) -> None:
    """Invoking gen with a missing spec path should error with URL loading message."""
    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["gen", str(tmp_path / "missing.json"), "-o", str(out_dir), "--no-postprocess"],
    )
    assert result.exit_code == 1
    assert "URL loading not implemented" in result.stdout


def test_docs_nonexistent_spec_path(tmp_path: Path) -> None:
    """Invoking docs with a missing spec path should error with URL loading message."""
    out_dir = tmp_path / "docs"
    runner = CliRunner()
    result = runner.invoke(
        app, ["docs", str(tmp_path / "no_spec.json"), "-o", str(out_dir)]
    )
    assert result.exit_code == 1
    assert "URL loading not implemented" in result.stdout


def test_gen_with_docs_flag_does_not_break(tmp_path: Path) -> None:
    """Passing --docs to gen should not break generation."""
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(MIN_SPEC))
    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "gen",
            str(spec_file),
            "-o",
            str(out_dir),
            "--force",
            "--docs",
            "--no-postprocess",
        ],
    )
    assert result.exit_code == 0, result.stdout
    # Core files should still be generated
    assert (out_dir / "config.py").exists(), "config.py missing after gen --docs"
    assert (out_dir / "client.py").exists(), "client.py missing after gen --docs"


def test_cli_no_args_shows_help_and_exits_cleanly():
    """
    Scenario:
        Run the CLI with no arguments.
    Expected Outcome:
        The help message is printed and the exit code is 0 (no error, no 'Missing command').
    """
    runner = CliRunner()
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "COMMAND" in result.stdout
    assert "Missing command" not in result.stdout
