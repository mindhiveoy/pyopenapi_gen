from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pyopenapi_gen import IRSpec
from pyopenapi_gen.context.file_manager import FileManager
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.emitters.client_emitter import ClientEmitter


@pytest.fixture
def mock_render_context() -> MagicMock:
    ctx = MagicMock(spec=RenderContext)
    ctx.parsed_schemas = {}
    # Configure file_manager to actually write files for .exists() checks
    actual_fm = FileManager()  # Create a real FileManager
    ctx.file_manager = MagicMock(spec=FileManager)
    ctx.file_manager.write_file.side_effect = actual_fm.write_file
    ctx.file_manager.ensure_dir.side_effect = actual_fm.ensure_dir

    ctx.import_collector = MagicMock()
    ctx.import_collector.render_imports.return_value = "# Mocked imports\nfrom typing import Any"
    ctx.render_imports.return_value = "# Mocked imports\nfrom typing import Any"
    ctx.core_package_name = "test_client.core"
    return ctx


def test_client_emitter__simple_api_spec__generates_client_py_with_imports(
    tmp_path: Path, mock_render_context: MagicMock
) -> None:
    """
    Scenario:
        ClientEmitter processes a simple IRSpec with basic API information
        (title, version, servers).

    Expected Outcome:
        The emitter should generate a client.py file with the proper API client
        class and necessary imports for the core functionality.
    """
    out_dir = tmp_path / "out"
    # Dummy spec (not used by emitter)
    spec = IRSpec(
        title="TestAPI",
        version="1.0",
        schemas={},
        operations=[],
        servers=["https://api.test"],
    )
    emitter = ClientEmitter(context=mock_render_context)
    emitter.emit(spec, str(out_dir))

    client_file = out_dir / "client.py"

    # File should exist
    assert client_file.exists(), "client.py was not generated"

    # Check client.py content
    cli = client_file.read_text()
    assert "class APIClient" in cli
    assert "HttpxTransport" in cli
    assert "def close" in cli
