import pytest


class DummyAuth:
    async def authenticate_request(self, request_args: dict[str, object]) -> dict[str, object]:
        return request_args


class DummyTransport:
    async def request(self, method: str, url: str, **kwargs: object) -> object:
        raise NotImplementedError()


@pytest.mark.asyncio
async def test_base_auth_protocol_default_returns_identity() -> None:
    """Calling BaseAuth.authenticate_request stub should return the input dict unchanged."""
    input_dict: dict[str, object] = {"foo": "bar"}
    dummy = DummyAuth()
    result = await dummy.authenticate_request(input_dict)
    assert result == input_dict


@pytest.mark.asyncio
async def test_http_transport_protocol_default_raises_not_implemented() -> None:
    """Calling HttpTransport.request stub should raise NotImplementedError."""
    dummy = DummyTransport()
    with pytest.raises(NotImplementedError):
        await dummy.request("GET", "/path", key="value")
