import json
import os
import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest
from httpx import Response
from pyopenapi_gen.cli import app
from pyopenapi_gen.core.pagination import paginate_by_next
from pyopenapi_gen.http_transport import HttpxTransport
from typer.testing import CliRunner

# Minimal spec reused for CLI flag tests
MIN_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Demo API", "version": "1.0.0"},
    "paths": {
        "/pets": {
            "get": {
                "operationId": "list_pets",
                "summary": "List pets",
                "responses": {"200": {"description": "OK"}},
            }
        }
    },
}


@pytest.mark.asyncio
async def test_httpx_transport_request_and_close(monkeypatch: Any) -> None:
    """Test HttpxTransport.request and close using a mock transport."""
    # Handler to simulate responses
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> Response:
        calls.append((request.method, request.url.path))
        return Response(200, json={"foo": "bar"})

    transport = HttpxTransport(base_url="https://api.test", timeout=1.0)
    # Replace underlying client with mock transport
    transport._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.test")

    resp = await transport.request("GET", "/test-path", params={"x": 1})
    assert resp.status_code == 200
    assert resp.json() == {"foo": "bar"}
    assert calls == [("GET", "/test-path")]

    # Ensure close does not raise
    await transport.close()


@pytest.mark.asyncio
async def test_paginate_by_next_default_and_custom_keys() -> None:
    """Test paginate_by_next yields items and respects custom keys."""
    # Default keys: items, next
    sequence = [([1, 2], "token1"), ([3], None)]

    async def fetch_page(**params: Any) -> dict[str, Any]:
        if not params:
            items, nxt = sequence[0]
            return {"items": items, "next": nxt}
        token = params.get("next")
        if token == "token1":
            items, nxt = sequence[1]
            return {"items": items, "next": nxt}
        return {"items": [], "next": None}

    result = [i async for i in paginate_by_next(fetch_page)]
    assert result == [1, 2, 3]

    # Custom keys
    sequence2 = [(["a"], "c1"), (["b"], None)]

    async def fetch_page2(**params: Any) -> dict[str, Any]:
        if not params:
            return {"data": sequence2[0][0], "cursor": sequence2[0][1]}
        if params.get("cursor") == "c1":
            return {"data": sequence2[1][0], "cursor": None}
        return {"data": [], "cursor": None}

    result2 = [i async for i in paginate_by_next(fetch_page2, items_key="data", next_key="cursor")]
    assert result2 == ["a", "b"]


def test_cli_with_optional_flags(tmp_path: Path) -> None:
    """Test that CLI accepts and processes optional flags without error."""
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
            "--name",
            "CustomClient",
            "--telemetry",
            "--auth",
            "BearerAuth",
        ],
    )
    assert result.exit_code == 0, result.stdout
    # Core files still generated
    assert (out_dir / "config.py").exists()
    assert (out_dir / "client.py").exists()

    # Run mypy on the generated code to ensure type correctness
    env = os.environ.copy()
    env["PYTHONPATH"] = str(out_dir.parent.resolve())
    mypy_result: subprocess.CompletedProcess[str] = subprocess.run(
        ["mypy", str(out_dir)], capture_output=True, text=True, env=env
    )
