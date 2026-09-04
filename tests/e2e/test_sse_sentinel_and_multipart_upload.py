"""E2E regression tests for generated SSE consumers and multipart uploads.

Covers the three defects reported by a downstream consumer while running an upload -> indexing
acceptance benchmark against a generated client:

1. ``iter_sse_events_text`` yielded the ``[DONE]`` termination sentinel, so every generated
   ``AsyncIterator[dict]`` endpoint blew up with ``json.JSONDecodeError`` on the last event.
2. Multipart bodies were pushed through the JSON ``DataclassSerializer`` (file tuple -> list,
   bytes -> base64) and every entry was sent as a file part, even plain string fields.
3. A transport-level default ``Content-Type: application/json`` overrode the multipart boundary
   header httpx derives from the body.
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

import httpx
import pytest

from pyopenapi_gen import generate_client

_SPEC: dict[str, Any] = {
    "openapi": "3.1.0",
    "info": {"title": "Bench API", "version": "1.0.0"},
    "paths": {
        "/chats/{chatId}/stream": {
            "get": {
                "operationId": "get_chat_stream",
                "tags": ["chats"],
                "parameters": [{"name": "chatId", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "200": {
                        "description": "SSE stream. Ends with a `[DONE]` line after the final message.",
                        "content": {"text/event-stream": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/attachments": {
            "post": {
                "operationId": "upload_attachment",
                "tags": ["attachments"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "mimeType": {"type": "string"},
                                    "chatId": {"type": "string"},
                                    "binary": {"type": "string", "format": "binary"},
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "Created",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Attachment"}}},
                    }
                },
            }
        },
    },
    "components": {
        "schemas": {
            "Attachment": {
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            }
        }
    },
}


@pytest.fixture(scope="module")
def generated_client_package() -> Iterator[str]:
    """Generate the client once for the module and make it importable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_file = project_root / "openapi.json"
        spec_file.write_text(json.dumps(_SPEC))
        generate_client(
            spec_path=str(spec_file),
            project_root=str(project_root),
            output_package="bench_client",
            force=True,
            no_postprocess=True,
        )
        sys.path.insert(0, str(project_root))
        try:
            yield "bench_client"
        finally:
            sys.path.remove(str(project_root))
            for name in [m for m in sys.modules if m == "bench_client" or m.startswith("bench_client.")]:
                del sys.modules[name]


def _sse_response(request: httpx.Request) -> httpx.Response:
    body = (
        'data: {"type": "STREAM_DATA", "data": {"content": "Hello"}}\n\n'
        ": keep-alive\n\n"
        'data: {"type": "STREAM_DATA", "data": {"content": " world"}}\n\n'
        "data: [DONE]\n\n"
    )
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body.encode())


@pytest.mark.asyncio
async def test_generated_sse_endpoint__stream_ending_with_done__parses_events_and_stops_cleanly(
    generated_client_package: str,
) -> None:
    """
    Scenario:
        A generated ``AsyncIterator[dict]`` endpoint consumes a stream that terminates with ``data: [DONE]``.
    Expected Outcome:
        The two real payloads are parsed into dicts; no JSONDecodeError; the sentinel is never yielded.
    """
    # Arrange
    import importlib

    chats_module = importlib.import_module(f"{generated_client_package}.endpoints.chats")
    transport_module = importlib.import_module(f"{generated_client_package}.core.http_transport")
    transport = transport_module.HttpxTransport(base_url="https://api.example.com")
    transport._client._transport = httpx.MockTransport(_sse_response)
    client = chats_module.ChatsClient(transport=transport, base_url="https://api.example.com")

    # Act
    events = [event async for event in client.get_chat_stream(chat_id="chat-1")]
    await transport.close()

    # Assert
    assert events == [
        {"type": "STREAM_DATA", "data": {"content": "Hello"}},
        {"type": "STREAM_DATA", "data": {"content": " world"}},
    ]


@pytest.mark.asyncio
async def test_generated_multipart_endpoint__mixed_fields_and_default_json_content_type__sends_valid_multipart(
    generated_client_package: str,
) -> None:
    """
    Scenario:
        A generated multipart endpoint is called with plain string fields plus a file tuple, through a
        transport configured with a default ``Content-Type: application/json`` header.
    Expected Outcome:
        The wire request is ``multipart/form-data`` with httpx's boundary, the plain fields are form
        fields (no synthetic filename), and the file part carries the original bytes unchanged.
    """
    # Arrange
    import importlib

    attachments_module = importlib.import_module(f"{generated_client_package}.endpoints.attachments")
    transport_module = importlib.import_module(f"{generated_client_package}.core.http_transport")
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["body"] = request.read()
        return httpx.Response(201, json={"id": "att-1"})

    transport = transport_module.HttpxTransport(
        base_url="https://api.example.com",
        default_headers={"Content-Type": "application/json", "x-my-token": "t"},
    )
    transport._client._transport = httpx.MockTransport(handler)
    client = attachments_module.AttachmentsClient(transport=transport, base_url="https://api.example.com")
    original_bytes = b"%PDF-1.4 fake pdf body"

    # Act
    result = await client.upload_attachment(
        files={
            "mimeType": "application/pdf",
            "chatId": "chat-1",
            "title": None,  # optional property left unset
            "binary": ("report.pdf", original_bytes, "application/pdf"),
        }
    )
    await transport.close()

    # Assert
    assert result.id_ == "att-1"  # generator renames `id` to avoid shadowing the builtin
    # The generated signature must admit tuples, bytes and plain fields, not only IO objects
    import inspect

    assert inspect.signature(client.upload_attachment).parameters["files"].annotation == dict[str, Any]
    headers = captured["headers"]
    body: bytes = captured["body"]
    assert headers["content-type"].startswith("multipart/form-data; boundary=")
    assert headers["x-my-token"] == "t"
    assert b'name="mimeType"\r\n\r\napplication/pdf' in body
    assert b'name="chatId"\r\n\r\nchat-1' in body
    assert b'name="title"' not in body
    assert b'filename="upload"' not in body
    assert b'name="binary"; filename="report.pdf"\r\nContent-Type: application/pdf' in body
    assert original_bytes in body
