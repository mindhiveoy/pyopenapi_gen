"""Centralised OpenAPI specification loading from file paths or URLs.

This module provides utilities for loading OpenAPI specifications from both
local file paths and HTTP(S) URLs. It handles content parsing (JSON/YAML)
and provides meaningful error messages for common failure scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import yaml

from pyopenapi_gen.generator.exceptions import GenerationError


def is_url(path_or_url: str) -> bool:
    """Check if the input looks like an HTTP(S) URL.

    Args:
        path_or_url: String that may be a file path or URL.

    Returns:
        True if the string starts with http:// or https://, False otherwise.
    """
    return path_or_url.startswith(("http://", "https://"))


def fetch_spec(path_or_url: str, timeout: float = 30.0) -> dict[str, Any]:
    """Load an OpenAPI specification from a file path or URL.

    Supports both local file paths and HTTP(S) URLs. For URLs, the content
    type is inferred from the Content-Type header or URL extension.

    Args:
        path_or_url: Path to a local file or HTTP(S) URL to fetch.
        timeout: Timeout in seconds for HTTP requests (default: 30.0).

    Returns:
        Parsed OpenAPI specification as a dictionary.

    Raises:
        GenerationError: If loading or parsing fails.
    """
    if is_url(path_or_url):
        return _fetch_from_url(path_or_url, timeout)
    return _load_from_file(path_or_url)


def _fetch_from_url(url: str, timeout: float) -> dict[str, Any]:
    """Fetch and parse an OpenAPI spec from a URL.

    Args:
        url: HTTP(S) URL to fetch.
        timeout: Timeout in seconds for the request.

    Returns:
        Parsed specification dictionary.

    Raises:
        GenerationError: On network errors, HTTP errors, or parse failures.
    """
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise GenerationError(f"Failed to fetch spec from URL: connection timed out after {timeout}s")
    except httpx.HTTPStatusError as e:
        raise GenerationError(f"Failed to fetch spec from URL: HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise GenerationError(f"Failed to fetch spec from URL: {e}")

    content = response.text
    content_type = response.headers.get("content-type", "")

    return _parse_content(content, content_type, url)


def _load_from_file(path: str) -> dict[str, Any]:
    """Load and parse an OpenAPI spec from a local file.

    Args:
        path: Path to the local file.

    Returns:
        Parsed specification dictionary.

    Raises:
        GenerationError: If file doesn't exist, isn't a file, or parse fails.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise GenerationError(f"Specification file not found at {path}")

    if not file_path.is_file():
        raise GenerationError(f"Specified path {path} is not a file.")

    content = file_path.read_text()
    extension = file_path.suffix.lower()

    # Determine format from extension
    if extension == ".json":
        content_type = "application/json"
    else:
        content_type = "application/yaml"

    return _parse_content(content, content_type, path)


def _parse_content(content: str, content_type: str, source: str) -> dict[str, Any]:
    """Parse content as JSON or YAML.

    Args:
        content: Raw content string.
        content_type: MIME type hint (may be empty).
        source: Source path/URL for error messages.

    Returns:
        Parsed dictionary.

    Raises:
        GenerationError: If parsing fails or result is not a dictionary.
    """
    # Try JSON first if content type suggests it
    if "json" in content_type.lower():
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise GenerationError(f"Failed to parse spec: invalid JSON content - {e}")
    else:
        # Try YAML (which also handles JSON)
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            # Fallback to JSON in case content-type was misleading
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                raise GenerationError(f"Failed to parse spec: invalid YAML content - {e}")

    if not isinstance(data, dict):
        raise GenerationError(f"Loaded spec from {source} is not a dictionary (got {type(data).__name__}).")

    return data
