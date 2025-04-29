from pathlib import Path
from pyopenapi_gen import IRSpec, IROperation, IRResponse, HTTPMethod
from pyopenapi_gen.emitters.exceptions_emitter import ExceptionsEmitter


def test_exceptions_emitter_generates_aliases(tmp_path: Path) -> None:
    # Create IR operations with numeric response codes
    resp1 = IRResponse(status_code="404", description="Not found", content={})
    resp2 = IRResponse(status_code="500", description="Server err", content={})
    op1 = IROperation(
        operation_id="op1",
        method=HTTPMethod.GET,
        path="/x",
        summary="",
        description=None,
        parameters=[],
        request_body=None,
        responses=[resp1, resp2],
        tags=["t"],
    )
    spec = IRSpec(
        title="API",
        version="1.0",
        schemas={},
        operations=[op1],
        servers=["https://api.test"],
    )

    emitter = ExceptionsEmitter()
    out_dir = str(tmp_path / "out")
    emitter.emit(spec, out_dir)

    alias_file = Path(out_dir) / "exceptions.py"
    assert alias_file.exists(), "exceptions.py not generated"
    content = alias_file.read_text()
    # Should have aliases for 404 and 500
    assert "class Error404(ClientError)" in content
    assert "class Error500(ServerError)" in content
    # Should import HTTPError, ClientError, ServerError
    assert "from .exceptions import HTTPError, ClientError, ServerError" in content
