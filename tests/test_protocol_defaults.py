import pytest
from pyopenapi_gen.auth.base import BaseAuth
from pyopenapi_gen.http_transport import HttpTransport


@pytest.mark.asyncio
async def test_base_auth_protocol_default_returns_ellipsis():
    """Calling BaseAuth.authenticate_request stub should return Ellipsis."""
    result = await BaseAuth.authenticate_request(None, {})
    assert result is Ellipsis


@pytest.mark.asyncio
async def test_http_transport_protocol_default_returns_ellipsis():
    """Calling HttpTransport.request stub should return Ellipsis."""
    result = await HttpTransport.request(None, "GET", "/path", key="value")
    assert result is Ellipsis
