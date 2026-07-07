import subprocess
import sys
from pathlib import Path

from pyopenapi_gen.core.postprocess_manager import PostprocessManager


def test_remove_unused_imports_bulk__many_targets__uses_response_file(monkeypatch, tmp_path):
    """
    Scenario: Ruff receives many generated files during post-processing.
    Expected Outcome: File paths are passed through a response file, avoiding Windows command-line limits.
    """
    captured: dict[str, object] = {}
    targets = [tmp_path / f"generated_{index}.py" for index in range(3)]
    for target in targets:
        target.write_text("import os\n", encoding="utf-8")

    def fake_run(command, **kwargs):
        response_arg = command[-1]
        response_path = Path(response_arg[1:])
        captured["command"] = command
        captured["kwargs"] = kwargs
        captured["response_arg"] = response_arg
        captured["response_path"] = response_path
        captured["response_text"] = response_path.read_text(encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    PostprocessManager(str(tmp_path)).remove_unused_imports_bulk(targets)

    assert captured["command"][:-1] == [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--select=F401",
        "--fix",
    ]
    assert str(captured["response_arg"]).startswith("@")
    assert captured["response_text"] == "\n".join(str(target.resolve()) for target in targets)
    assert not Path(captured["response_path"]).exists()
    assert captured["kwargs"] == {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }


def test_format_code_bulk__many_targets__uses_response_file(monkeypatch, tmp_path):
    """
    Scenario: Ruff format receives many generated files during post-processing.
    Expected Outcome: Formatting uses the same response-file path transport as Ruff checks.
    """
    captured: dict[str, object] = {}
    target = tmp_path / "generated.py"
    target.write_text("x=1\n", encoding="utf-8")

    def fake_run(command, **kwargs):
        response_path = Path(command[-1][1:])
        captured["command"] = command
        captured["response_text"] = response_path.read_text(encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    PostprocessManager(str(tmp_path)).format_code_bulk([target])

    assert captured["command"][:-1] == [
        sys.executable,
        "-m",
        "ruff",
        "format",
    ]
    assert captured["response_text"] == str(target.resolve())
