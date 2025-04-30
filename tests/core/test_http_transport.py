import typing

import httpx
import pytest
from pyopenapi_gen.http_transport import HttpxTransport


class DummyAuth:
    async def authenticate_request(self, request_args: dict[str, object]) -> dict[str, object]:
        headers = dict(typing.cast(dict[str, str], request_args.get("headers", {})))
        headers["Authorization"] = "Bearer dummy-token"
        request_args["headers"] = headers
        return request_args


@pytest.mark.asyncio
async def test_bearer_token_auth_sets_header() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = HttpxTransport(base_url="https://api.example.com", bearer_token="abc123")
    client._client._transport = transport  # monkeypatch
    await client.request("GET", "/test")
    assert captured["headers"].get("authorization") == "Bearer abc123"
    await client.close()


@pytest.mark.asyncio
async def test_baseauth_takes_precedence_over_bearer() -> None:
    captured: dict[str, object] = {}

    class CustomAuth:
        async def authenticate_request(self, request_args: dict[str, object]) -> dict[str, object]:
            headers = dict(typing.cast(dict[str, str], request_args.get("headers", {})))
            headers["Authorization"] = "Bearer custom"
            request_args["headers"] = headers
            return request_args

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers).copy()
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = HttpxTransport(
        base_url="https://api.example.com",
        auth=CustomAuth(),
        bearer_token="should-not-be-used",
    )
    client._client._transport = transport
    await client.request("GET", "/test")
    headers = typing.cast(dict[str, str], captured["headers"])
    assert headers.get("authorization") == "Bearer custom"
    await client.close()


@pytest.mark.asyncio
async def test_no_auth_no_header() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers).copy()
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = HttpxTransport(base_url="https://api.example.com")
    client._client._transport = transport
    await client.request("GET", "/test")
    headers = typing.cast(dict[str, str], captured["headers"])
    assert "authorization" not in headers
    await client.close()
