import inspect
from typing import Any

import pytest

from pyopenapi_gen.core.auth.base import BaseAuth, CompositeAuth


def test_base_auth_method_signature() -> None:
    """BaseAuth should define authenticate_request(request_args: Dict[str, Any]) -> Dict[str, Any]"""
    sig = inspect.signature(BaseAuth.authenticate_request)
    params = sig.parameters
    assert list(params.keys()) == ["self", "request_args"]
    assert params["request_args"].annotation == dict[str, Any]
    assert sig.return_annotation == dict[str, Any]


class MockAuth:
    """Mock auth plugin for testing."""

    def __init__(self, header_name: str, header_value: str):
        self.header_name = header_name
        self.header_value = header_value

    async def authenticate_request(self, request_args: dict[str, Any]) -> dict[str, Any]:
        if "headers" not in request_args:
            request_args["headers"] = {}
        request_args["headers"][self.header_name] = self.header_value
        return request_args


class TestCompositeAuth:
    """Test suite for CompositeAuth."""

    def test_composite_auth__init__stores_plugins(self):
        """Scenario: Initialize CompositeAuth with plugins.

        Expected Outcome: Plugins are stored.
        """
        # Arrange
        auth1 = MockAuth("X-API-Key", "key1")
        auth2 = MockAuth("Authorization", "Bearer token")

        # Act
        composite = CompositeAuth(auth1, auth2)

        # Assert
        assert len(composite.plugins) == 2
        assert composite.plugins[0] is auth1
        assert composite.plugins[1] is auth2

    def test_composite_auth__empty_plugins__creates_empty_composite(self):
        """Scenario: Initialize CompositeAuth with no plugins.

        Expected Outcome: Empty plugins list.
        """
        # Act
        composite = CompositeAuth()

        # Assert
        assert len(composite.plugins) == 0

    @pytest.mark.asyncio
    async def test_composite_auth__authenticate_request__applies_all_plugins(self):
        """Scenario: Authenticate request with multiple plugins.

        Expected Outcome: All plugins are applied in sequence.
        """
        # Arrange
        auth1 = MockAuth("X-API-Key", "key123")
        auth2 = MockAuth("X-Client-ID", "client456")
        composite = CompositeAuth(auth1, auth2)
        request_args = {"url": "https://api.example.com"}

        # Act
        result = await composite.authenticate_request(request_args)

        # Assert
        assert result["url"] == "https://api.example.com"
        assert result["headers"]["X-API-Key"] == "key123"
        assert result["headers"]["X-Client-ID"] == "client456"

    @pytest.mark.asyncio
    async def test_composite_auth__no_plugins__returns_unchanged(self):
        """Scenario: Authenticate request with no plugins.

        Expected Outcome: Request args are returned unchanged.
        """
        # Arrange
        composite = CompositeAuth()
        request_args = {"url": "https://api.example.com", "method": "GET"}

        # Act
        result = await composite.authenticate_request(request_args)

        # Assert
        assert result is request_args  # Same object
        assert result == {"url": "https://api.example.com", "method": "GET"}

    @pytest.mark.asyncio
    async def test_composite_auth__overlapping_headers__later_plugin_overwrites(self):
        """Scenario: Multiple plugins setting same header.

        Expected Outcome: Later plugin overwrites earlier one.
        """
        # Arrange
        auth1 = MockAuth("Authorization", "Bearer token1")
        auth2 = MockAuth("Authorization", "Bearer token2")
        composite = CompositeAuth(auth1, auth2)
        request_args = {}

        # Act
        result = await composite.authenticate_request(request_args)

        # Assert
        assert result["headers"]["Authorization"] == "Bearer token2"
