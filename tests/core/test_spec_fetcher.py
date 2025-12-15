"""Tests for the spec_fetcher module.

Scenario: Testing URL detection and specification loading from both file paths and URLs.
Expected Outcome: The module correctly identifies URLs, loads specs from files and URLs,
and raises appropriate errors for invalid inputs.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from pyopenapi_gen.core.spec_fetcher import (
    _fetch_from_url,
    _load_from_file,
    _parse_content,
    fetch_spec,
    is_url,
)
from pyopenapi_gen.generator.client_generator import GenerationError


class TestIsUrl:
    """Tests for is_url function."""

    def test_is_url__http_url__returns_true(self) -> None:
        """
        Scenario: Check if http:// URL is detected.
        Expected Outcome: Returns True for http:// URLs.
        """
        # Arrange
        url = "http://localhost:5001/openapi.json"

        # Act
        result = is_url(url)

        # Assert
        assert result is True

    def test_is_url__https_url__returns_true(self) -> None:
        """
        Scenario: Check if https:// URL is detected.
        Expected Outcome: Returns True for https:// URLs.
        """
        # Arrange
        url = "https://api.example.com/openapi.json"

        # Act
        result = is_url(url)

        # Assert
        assert result is True

    def test_is_url__absolute_file_path__returns_false(self) -> None:
        """
        Scenario: Check if absolute file path is not detected as URL.
        Expected Outcome: Returns False for file paths.
        """
        # Arrange
        path = "/home/user/specs/openapi.yaml"

        # Act
        result = is_url(path)

        # Assert
        assert result is False

    def test_is_url__relative_file_path__returns_false(self) -> None:
        """
        Scenario: Check if relative file path is not detected as URL.
        Expected Outcome: Returns False for relative paths.
        """
        # Arrange
        path = "input/openapi.yaml"

        # Act
        result = is_url(path)

        # Assert
        assert result is False

    def test_is_url__windows_path__returns_false(self) -> None:
        """
        Scenario: Check if Windows path is not detected as URL.
        Expected Outcome: Returns False for Windows paths.
        """
        # Arrange
        path = r"C:\Users\spec\openapi.json"

        # Act
        result = is_url(path)

        # Assert
        assert result is False


class TestFetchSpec:
    """Tests for fetch_spec function."""

    def test_fetch_spec__valid_yaml_file__returns_dict(self, tmp_path: Path) -> None:
        """
        Scenario: Load a valid YAML specification file.
        Expected Outcome: Returns parsed dictionary.
        """
        # Arrange
        spec_content = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths: {}
"""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(spec_content)

        # Act
        result = fetch_spec(str(spec_file))

        # Assert
        assert isinstance(result, dict)
        assert result["openapi"] == "3.0.0"
        assert result["info"]["title"] == "Test API"

    def test_fetch_spec__valid_json_file__returns_dict(self, tmp_path: Path) -> None:
        """
        Scenario: Load a valid JSON specification file.
        Expected Outcome: Returns parsed dictionary.
        """
        # Arrange
        spec_content = '{"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}'
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(spec_content)

        # Act
        result = fetch_spec(str(spec_file))

        # Assert
        assert isinstance(result, dict)
        assert result["openapi"] == "3.0.0"

    @patch("pyopenapi_gen.core.spec_fetcher.httpx.get")
    def test_fetch_spec__valid_url__returns_dict(self, mock_get: MagicMock) -> None:
        """
        Scenario: Load a valid specification from URL.
        Expected Outcome: Returns parsed dictionary.
        """
        # Arrange
        url = "https://api.example.com/openapi.json"
        mock_response = MagicMock()
        mock_response.text = '{"openapi": "3.0.0", "info": {"title": "Test"}, "paths": {}}'
        mock_response.headers = {"content-type": "application/json"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act
        result = fetch_spec(url)

        # Assert
        assert isinstance(result, dict)
        assert result["openapi"] == "3.0.0"
        mock_get.assert_called_once_with(url, timeout=30.0, follow_redirects=True)

    def test_fetch_spec__nonexistent_file__raises_generation_error(self) -> None:
        """
        Scenario: Attempt to load from non-existent file.
        Expected Outcome: Raises GenerationError with descriptive message.
        """
        # Arrange
        path = "/nonexistent/path/to/spec.yaml"

        # Act & Assert
        with pytest.raises(GenerationError) as exc_info:
            fetch_spec(path)
        assert "Specification file not found" in str(exc_info.value)


class TestFetchFromUrl:
    """Tests for _fetch_from_url internal function."""

    @patch("pyopenapi_gen.core.spec_fetcher.httpx.get")
    def test_fetch_from_url__timeout__raises_generation_error(self, mock_get: MagicMock) -> None:
        """
        Scenario: HTTP request times out.
        Expected Outcome: Raises GenerationError with timeout message.
        """
        # Arrange
        url = "https://api.example.com/openapi.json"
        mock_get.side_effect = httpx.TimeoutException("Connection timed out")

        # Act & Assert
        with pytest.raises(GenerationError) as exc_info:
            _fetch_from_url(url, timeout=10.0)
        assert "connection timed out after 10.0s" in str(exc_info.value)

    @patch("pyopenapi_gen.core.spec_fetcher.httpx.get")
    def test_fetch_from_url__http_404__raises_generation_error(self, mock_get: MagicMock) -> None:
        """
        Scenario: Server returns 404 Not Found.
        Expected Outcome: Raises GenerationError with HTTP status.
        """
        # Arrange
        url = "https://api.example.com/openapi.json"
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        # Act & Assert
        with pytest.raises(GenerationError) as exc_info:
            _fetch_from_url(url, timeout=30.0)
        assert "HTTP 404" in str(exc_info.value)

    @patch("pyopenapi_gen.core.spec_fetcher.httpx.get")
    def test_fetch_from_url__http_500__raises_generation_error(self, mock_get: MagicMock) -> None:
        """
        Scenario: Server returns 500 Internal Server Error.
        Expected Outcome: Raises GenerationError with HTTP status.
        """
        # Arrange
        url = "https://api.example.com/openapi.json"
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )

        # Act & Assert
        with pytest.raises(GenerationError) as exc_info:
            _fetch_from_url(url, timeout=30.0)
        assert "HTTP 500" in str(exc_info.value)

    @patch("pyopenapi_gen.core.spec_fetcher.httpx.get")
    def test_fetch_from_url__connection_error__raises_generation_error(self, mock_get: MagicMock) -> None:
        """
        Scenario: Connection cannot be established.
        Expected Outcome: Raises GenerationError with error details.
        """
        # Arrange
        url = "https://api.example.com/openapi.json"
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        # Act & Assert
        with pytest.raises(GenerationError) as exc_info:
            _fetch_from_url(url, timeout=30.0)
        assert "Failed to fetch spec from URL" in str(exc_info.value)


class TestLoadFromFile:
    """Tests for _load_from_file internal function."""

    def test_load_from_file__directory_path__raises_generation_error(self, tmp_path: Path) -> None:
        """
        Scenario: Path points to a directory, not a file.
        Expected Outcome: Raises GenerationError indicating not a file.
        """
        # Arrange
        directory = tmp_path / "subdir"
        directory.mkdir()

        # Act & Assert
        with pytest.raises(GenerationError) as exc_info:
            _load_from_file(str(directory))
        assert "is not a file" in str(exc_info.value)

    def test_load_from_file__invalid_yaml__raises_generation_error(self, tmp_path: Path) -> None:
        """
        Scenario: File contains invalid YAML.
        Expected Outcome: Raises GenerationError with parse error.
        """
        # Arrange
        spec_file = tmp_path / "invalid.yaml"
        spec_file.write_text("invalid: yaml: content:")

        # Act & Assert
        with pytest.raises(GenerationError) as exc_info:
            _load_from_file(str(spec_file))
        assert "invalid YAML" in str(exc_info.value)

    def test_load_from_file__invalid_json__raises_generation_error(self, tmp_path: Path) -> None:
        """
        Scenario: JSON file contains invalid JSON.
        Expected Outcome: Raises GenerationError with parse error.
        """
        # Arrange
        spec_file = tmp_path / "invalid.json"
        spec_file.write_text("{invalid json}")

        # Act & Assert
        with pytest.raises(GenerationError) as exc_info:
            _load_from_file(str(spec_file))
        assert "invalid JSON" in str(exc_info.value)

    def test_load_from_file__non_dict_content__raises_generation_error(self, tmp_path: Path) -> None:
        """
        Scenario: File content is valid YAML but not a dictionary.
        Expected Outcome: Raises GenerationError indicating wrong type.
        """
        # Arrange
        spec_file = tmp_path / "array.yaml"
        spec_file.write_text("- item1\n- item2\n")

        # Act & Assert
        with pytest.raises(GenerationError) as exc_info:
            _load_from_file(str(spec_file))
        assert "is not a dictionary" in str(exc_info.value)


class TestParseContent:
    """Tests for _parse_content internal function."""

    def test_parse_content__json_content_type__parses_json(self) -> None:
        """
        Scenario: Content type indicates JSON.
        Expected Outcome: Content is parsed as JSON.
        """
        # Arrange
        content = '{"key": "value"}'
        content_type = "application/json"

        # Act
        result = _parse_content(content, content_type, "test")

        # Assert
        assert result == {"key": "value"}

    def test_parse_content__yaml_content_type__parses_yaml(self) -> None:
        """
        Scenario: Content type indicates YAML.
        Expected Outcome: Content is parsed as YAML.
        """
        # Arrange
        content = "key: value"
        content_type = "application/yaml"

        # Act
        result = _parse_content(content, content_type, "test")

        # Assert
        assert result == {"key": "value"}

    def test_parse_content__json_in_yaml_mode__parses_correctly(self) -> None:
        """
        Scenario: JSON content with YAML content type.
        Expected Outcome: YAML parser handles JSON correctly.
        """
        # Arrange
        content = '{"key": "value"}'
        content_type = "application/yaml"

        # Act
        result = _parse_content(content, content_type, "test")

        # Assert
        assert result == {"key": "value"}

    def test_parse_content__empty_content_type__uses_yaml(self) -> None:
        """
        Scenario: No content type provided.
        Expected Outcome: Defaults to YAML parsing.
        """
        # Arrange
        content = "key: value"
        content_type = ""

        # Act
        result = _parse_content(content, content_type, "test")

        # Assert
        assert result == {"key": "value"}

    @patch("pyopenapi_gen.core.spec_fetcher.httpx.get")
    def test_fetch_from_url__yaml_content_type__parses_yaml(self, mock_get: MagicMock) -> None:
        """
        Scenario: URL returns YAML with appropriate content type.
        Expected Outcome: Content is parsed as YAML.
        """
        # Arrange
        url = "https://api.example.com/openapi.yaml"
        mock_response = MagicMock()
        mock_response.text = "openapi: '3.0.0'\ninfo:\n  title: Test\n  version: '1.0'\npaths: {}"
        mock_response.headers = {"content-type": "application/yaml"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act
        result = _fetch_from_url(url, timeout=30.0)

        # Assert
        assert result["openapi"] == "3.0.0"
        assert result["info"]["title"] == "Test"
