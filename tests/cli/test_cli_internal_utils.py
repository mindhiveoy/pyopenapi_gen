import pytest
from pathlib import Path
from typer import Exit

from pyopenapi_gen.cli import _load_spec, _show_diffs


def test_load_spec_from_file(tmp_path: Path):
    """_load_spec should load YAML from a file path."""
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text("foo: bar")
    data = _load_spec(str(spec_file))
    assert data == {"foo": "bar"}


def test_load_spec_url_not_implemented(tmp_path: Path, capsys):
    """_load_spec should error for non-existent paths (URL loading path)."""
    url = "http://example.com/spec.yaml"
    with pytest.raises(Exit) as excinfo:
        _load_spec(url)
    assert excinfo.value.exit_code == 1
    # The error message should be printed to stderr
    captured = capsys.readouterr()
    assert "URL loading not implemented" in captured.err


def test_show_diffs_no_changes(tmp_path: Path, capsys):
    """_show_diffs returns False and prints nothing when directories match."""
    old = tmp_path / "old"
    new = tmp_path / "new"
    old.mkdir()
    new.mkdir()
    f_old = old / "file.py"
    f_new = new / "file.py"
    content = "hello\nworld"
    f_old.write_text(content)
    f_new.write_text(content)

    result = _show_diffs(str(old), str(new))
    assert result is False
    captured = capsys.readouterr()
    assert captured.out == ""


def test_show_diffs_detects_changes(tmp_path: Path, capsys):
    """_show_diffs returns True and prints diff when files differ."""
    old = tmp_path / "old"
    new = tmp_path / "new"
    old.mkdir()
    new.mkdir()
    f_old = old / "file.py"
    f_new = new / "file.py"
    f_old.write_text("line1\nline2")
    f_new.write_text("line1\nLINE2")

    result = _show_diffs(str(old), str(new))
    assert result is True
    captured = capsys.readouterr()
    # The diff should show -line2 and +LINE2
    assert "-line2" in captured.out
    assert "+LINE2" in captured.out
