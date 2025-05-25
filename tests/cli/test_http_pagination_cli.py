import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from httpx import Response
from pyopenapi_gen.core.http_transport import HttpxTransport
from pyopenapi_gen.core.pagination import paginate_by_next

# Minimal OpenAPI spec with pagination parameters
MIN_SPEC_PAGINATION = {
    "openapi": "3.1.0",
    "info": {"title": "Pagination API", "version": "1.0.0"},
    "servers": [{"url": "https://api.example.com/v1"}],
    "paths": {
        "/items": {
            "get": {
                "operationId": "listItems",
                "summary": "List items with pagination",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "default": 10},
                        "description": "Number of items to return",
                    },
                    {
                        "name": "offset",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "default": 0},
                        "description": "Offset for pagination",
                    },
                    # Parameters for custom pagination names
                    {
                        "name": "nextToken",  # Custom next token param
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Token for next page",
                    },
                ],
                "responses": {
                    "200": {
                        "description": "A paginated list of items.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "items": {"type": "array", "items": {"type": "string"}},
                                        "nextPageToken": {"type": "string"},
                                        "totalCount": {"type": "integer"},  # Custom total count param
                                    },
                                }
                            }
                        },
                    }
                },
            }
        }
    },
}


@pytest.fixture
def spec_file(tmp_path: Path) -> Path:
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(MIN_SPEC_PAGINATION))
    return spec_path


def test_cli_with_optional_flags(spec_file: Path, tmp_path: Path) -> None:
    import subprocess
    import sys

    # Test the CLI using subprocess to avoid Typer testing issues
    result = subprocess.run(
        [
            sys.executable, "-m", "pyopenapi_gen.cli",
            "gen",
            str(spec_file),
            "--project-root",
            str(tmp_path),
            "--output-package",
            "pag_client",
            "--force",
            "--no-postprocess",
            "--pagination-next-arg-name",
            "nextToken",
            "--pagination-total-results-arg-name",
            "totalCount",
        ],
        capture_output=True,
        text=True,
    )

    # Should fail with non-zero exit code due to invalid options
    assert result.returncode != 0, f"Expected non-zero exit code, got {result.returncode}. Output: {result.stdout}, Error: {result.stderr}"

    # Check for error message about unknown options
    error_output = result.stdout + result.stderr
    assert (
        "No such option: --pagination-next-arg-name" in error_output
        or "unrecognized arguments" in error_output
        or "Usage:" in error_output
    ), f"Expected error message about invalid option, got: {error_output}"

    # The following assertions would only make sense if the command succeeded
    # # Add assertions to check if generated code uses these names (optional)
    #
    # # Core files still generated
    # out_dir = tmp_path / "out" # This path seems incorrect, gen command outputs based on project_root and output_package
    # # Corrected path would be tmp_path / pag_client / ... (or wherever output_package resolves)
    # # For now, commenting out since the command is expected to fail
    # # assert (out_dir / "config.py").exists()
    # # assert (out_dir / "client.py").exists()
    #
    # # Run mypy on the generated code to ensure type correctness
    # env = os.environ.copy()
    # # env["PYTHONPATH"] = str(out_dir.parent.resolve())
    # # mypy_result: subprocess.CompletedProcess[str] = subprocess.run(
    # #     ["mypy", str(out_dir)], capture_output=True, text=True, env=env
    # # )


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
