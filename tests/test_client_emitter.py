from pathlib import Path
from pyopenapi_gen import IRSpec
from pyopenapi_gen.client_emitter import ClientEmitter


def test_client_emitter_creates_core_files(tmp_path: Path) -> None:
    """ClientEmitter should generate config.py and client.py with expected content."""
    out_dir = tmp_path / "out"
    # Dummy spec (not used by emitter)
    spec = IRSpec(
        title="TestAPI",
        version="1.0",
        schemas={},
        operations=[],
        servers=["https://api.test"],
    )
    emitter = ClientEmitter()
    emitter.emit(spec, str(out_dir))

    config_file = out_dir / "config.py"
    client_file = out_dir / "client.py"

    # Files should exist
    assert config_file.exists(), "config.py was not generated"
    assert client_file.exists(), "client.py was not generated"

    # Check config.py content
    cfg = config_file.read_text()
    assert "class ClientConfig" in cfg
    assert "self.base_url" in cfg
    assert "self.timeout" in cfg

    # Check client.py content
    cli = client_file.read_text()
    assert "class APIClient" in cli
    assert "HttpxTransport" in cli
    assert "def close" in cli
