import pytest
import httpx
import asyncio
from pyopenapi_gen.http_transport import HttpxTransport
from pyopenapi_gen.auth.base import BaseAuth


class DummyAuth:
    async def authenticate_request(self, request_args):
        headers = dict(request_args.get("headers", {}))
        headers["Authorization"] = "Bearer dummy-token"
        request_args["headers"] = headers
        return request_args


@pytest.mark.asyncio
async def test_bearer_token_auth_sets_header():
    captured = {}

    def handler(request):
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = HttpxTransport(base_url="https://api.example.com", bearer_token="abc123")
    client._client._transport = transport  # monkeypatch
    await client.request("GET", "/test")
    assert captured["headers"].get("authorization") == "Bearer abc123"
    await client.close()


@pytest.mark.asyncio
async def test_baseauth_takes_precedence_over_bearer():
    captured = {}

    class CustomAuth:
        async def authenticate_request(self, request_args):
            headers = dict(request_args.get("headers", {}))
            headers["Authorization"] = "Bearer custom"
            request_args["headers"] = headers
            return request_args

    def handler(request):
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = HttpxTransport(
        base_url="https://api.example.com",
        auth=CustomAuth(),
        bearer_token="should-not-be-used",
    )
    client._client._transport = transport
    await client.request("GET", "/test")
    assert captured["headers"].get("authorization") == "Bearer custom"
    await client.close()


@pytest.mark.asyncio
async def test_no_auth_no_header():
    captured = {}

    def handler(request):
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = HttpxTransport(base_url="https://api.example.com")
    client._client._transport = transport
    await client.request("GET", "/test")
    # Should not set Authorization header
    assert "authorization" not in captured["headers"]
    await client.close()
