from pathlib import Path
from pyopenapi_gen.emitters.config_emitter import ConfigEmitter


def test_config_emitter_creates_config_file(tmp_path: Path) -> None:
    """ConfigEmitter should generate config.py with expected content."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    emitter = ConfigEmitter()
    emitter.emit(str(out_dir))

    config_file = out_dir / "config.py"
    assert config_file.exists(), "config.py was not generated"

    cfg = config_file.read_text()
    assert "class ClientConfig" in cfg
    assert "base_url" in cfg
    assert "timeout" in cfg
