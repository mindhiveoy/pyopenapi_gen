from pathlib import Path

import pytest
from pyopenapi_gen.cli import _load_spec
from typer import Exit


def test_load_spec_from_file(tmp_path: Path) -> None:
    """_load_spec should load YAML from a file path."""
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text("foo: bar")
    data = _load_spec(str(spec_file))
    assert data == {"foo": "bar"}


def test_load_spec_file_not_found() -> None:
    with pytest.raises(Exit) as exc_info:
        _load_spec("nonexistent_spec.json")
    assert exc_info.value.exit_code == 1


def test_load_spec_url_not_implemented() -> None:
    with pytest.raises(Exit) as exc_info:
        _load_spec("http://example.com/spec.json")
    assert exc_info.value.exit_code == 1


# Diffing tests are removed as the functionality is now internal to ClientGenerator
