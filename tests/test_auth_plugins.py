import pytest
from pyopenapi_gen.auth.plugins import BearerAuth, HeadersAuth
from typing import Dict, Any


@pytest.mark.asyncio
async def test_bearer_auth_adds_authorization_header():
    auth = BearerAuth("token123")
    request_args: Dict[str, Any] = {}
    result = await auth.authenticate_request(request_args)
    assert "headers" in result
    assert result["headers"]["Authorization"] == "Bearer token123"


@pytest.mark.asyncio
async def test_headers_auth_merges_headers():
    initial_headers = {"Existing": "val"}
    auth = HeadersAuth({"X-Test": "value", "Y-Other": "otherv"})
    request_args: Dict[str, Any] = {"headers": initial_headers.copy()}
    result = await auth.authenticate_request(request_args)
    assert result["headers"]["Existing"] == "val"
    assert result["headers"]["X-Test"] == "value"
    assert result["headers"]["Y-Other"] == "otherv"


@pytest.mark.asyncio
async def test_auth_composition():
    ba = BearerAuth("tok")
    ha = HeadersAuth({"X-A": "1"})
    request_args: Dict[str, Any] = {}
    result1 = await ba.authenticate_request(request_args)
    result2 = await ha.authenticate_request(result1)
    assert result2["headers"]["Authorization"] == "Bearer tok"
    assert result2["headers"]["X-A"] == "1"
