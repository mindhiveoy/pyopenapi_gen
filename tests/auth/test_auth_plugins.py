from typing import Any, Dict

import pytest
from pyopenapi_gen.core.auth.plugins import BearerAuth, HeadersAuth


@pytest.mark.asyncio
async def test_bearer_auth_adds_authorization_header() -> None:
    auth = BearerAuth("token123")
    request_args: Dict[str, Any] = {}
    result = await auth.authenticate_request(request_args)
    assert "headers" in result
    assert result["headers"]["Authorization"] == "Bearer token123"


@pytest.mark.asyncio
async def test_headers_auth_merges_headers() -> None:
    initial_headers = {"Existing": "val"}
    auth = HeadersAuth({"X-Test": "value", "Y-Other": "otherv"})
    request_args: Dict[str, Any] = {"headers": initial_headers.copy()}
    result = await auth.authenticate_request(request_args)
    assert result["headers"]["Existing"] == "val"
    assert result["headers"]["X-Test"] == "value"
    assert result["headers"]["Y-Other"] == "otherv"


@pytest.mark.asyncio
async def test_auth_composition() -> None:
    ba = BearerAuth("tok")
    ha = HeadersAuth({"X-A": "1"})
    request_args: Dict[str, Any] = {}
    result1 = await ba.authenticate_request(request_args)
    result2 = await ha.authenticate_request(result1)
    assert result2["headers"]["Authorization"] == "Bearer tok"
    assert result2["headers"]["X-A"] == "1"


@pytest.mark.asyncio
async def test_apikey_auth__header_location__sets_header() -> None:
    """
    Scenario:
        API key is set to be sent in the header. The plugin should add the key to the correct header.
    Expected Outcome:
        The header is present and has the correct value.
    """
    from pyopenapi_gen.core.auth.plugins import ApiKeyAuth

    auth = ApiKeyAuth("mykey", location="header", name="X-API-Key")
    result = await auth.authenticate_request({})
    assert result["headers"]["X-API-Key"] == "mykey"


@pytest.mark.asyncio
async def test_apikey_auth__query_location__sets_query_param() -> None:
    """
    Scenario:
        API key is set to be sent as a query parameter. The plugin should add the key to the query params.
    Expected Outcome:
        The query param is present and has the correct value.
    """
    from pyopenapi_gen.core.auth.plugins import ApiKeyAuth

    auth = ApiKeyAuth("mykey", location="query", name="api_key")
    result = await auth.authenticate_request({})
    assert result["params"]["api_key"] == "mykey"


@pytest.mark.asyncio
async def test_apikey_auth__cookie_location__sets_cookie() -> None:
    """
    Scenario:
        API key is set to be sent as a cookie. The plugin should add the key to the cookies dict.
    Expected Outcome:
        The cookie is present and has the correct value.
    """
    from pyopenapi_gen.core.auth.plugins import ApiKeyAuth

    auth = ApiKeyAuth("mykey", location="cookie", name="sessionid")
    result = await auth.authenticate_request({})
    assert result["cookies"]["sessionid"] == "mykey"


@pytest.mark.asyncio
async def test_apikey_auth__invalid_location__raises_value_error() -> None:
    """
    Scenario:
        API key is set to an invalid location. The plugin should raise ValueError.
    Expected Outcome:
        ValueError is raised.
    """
    from pyopenapi_gen.core.auth.plugins import ApiKeyAuth

    auth = ApiKeyAuth("mykey", location="invalid", name="foo")
    with pytest.raises(ValueError):
        await auth.authenticate_request({})


@pytest.mark.asyncio
async def test_oauth2_auth__simple_token__sets_bearer_header() -> None:
    """
    Scenario:
        OAuth2Auth is used with a static access token. The plugin should set the Authorization header.
    Expected Outcome:
        The Authorization header is set to 'Bearer <token>'.
    """
    from pyopenapi_gen.core.auth.plugins import OAuth2Auth

    auth = OAuth2Auth("abc123")
    result = await auth.authenticate_request({})
    assert result["headers"]["Authorization"] == "Bearer abc123"


@pytest.mark.asyncio
async def test_oauth2_auth__refresh_callback__updates_token() -> None:
    """
    Scenario:
        OAuth2Auth is used with a refresh_callback that returns a new token.
        The plugin should update the token and use it.
    Expected Outcome:
        The Authorization header is set to the new token after refresh.
    """
    from pyopenapi_gen.core.auth.plugins import OAuth2Auth

    async def refresh_cb(old_token: str) -> str:
        return "newtoken"

    auth = OAuth2Auth("oldtoken", refresh_callback=refresh_cb)
    result = await auth.authenticate_request({})
    assert result["headers"]["Authorization"] == "Bearer newtoken"
    # Token should be updated for next call
    result2 = await auth.authenticate_request({})
    assert result2["headers"]["Authorization"] == "Bearer newtoken"
