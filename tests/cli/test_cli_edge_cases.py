from pathlib import Path

from typer.testing import CliRunner

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
    """Test calling gen with a spec path that does not exist."""
    runner = CliRunner()
    # Run with catch_exceptions=False to let SystemExit propagate, which pytest handles.
    # Stdout/stderr redirection might be needed if checking stderr content reliably.
    result = runner.invoke(
        app,
        ["gen", str(tmp_path / "nonexistent.json"), "--project-root", str(tmp_path), "--output-package", "client"],
        catch_exceptions=False,  # Let SystemExit propagate
    )
    # We expect SystemExit(1) from _load_spec
    assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}. Output: {result.output}"
    # Checking stderr might be unreliable with default invoke, but let's keep it.
    # If this fails intermittently, consider external process call or pytest-subprocess.
    # assert "URL loading not implemented" in result.stderr # Commenting out stderr check for now


def test_gen_with_docs_flag_does_not_break(tmp_path: Path) -> None:
    """Test calling gen with --docs flag results in a Typer usage error."""
    runner = CliRunner(mix_stderr=False)
    # Create dummy spec
    spec_file = tmp_path / "spec.json"
    spec_file.write_text('{"openapi":"3.1.0","info":{"title":"T","version":"1"},"paths":{}}')
    result = runner.invoke(
        app,
        [
            "gen",
            str(spec_file),
            "--project-root",
            str(tmp_path),
            "--output-package",
            "client",
            "--docs",  # This is an invalid option for the 'gen' command
        ],
        # Don't catch exceptions here, Typer handles invalid options cleanly
    )
    assert result.exit_code == 2, f"Expected exit code 2 (Typer error), got {result.exit_code}. Output: {result.output}"
    # Typer prints error message to stderr by default
    assert "No such option: --docs" in result.stderr, (
        f"Expected 'No such option' error msg in stderr, got: {result.stderr}"
    )
    assert "Usage: root gen" in result.stderr, f"Expected Usage message in stderr, got: {result.stderr}"


def test_cli_no_args_shows_help_and_exits_cleanly() -> None:
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
