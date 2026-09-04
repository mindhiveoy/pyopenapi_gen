import typing
from unittest.mock import MagicMock, patch

import httpx
import pytest

from pyopenapi_gen.core.http_transport import HttpxTransport, _prepare_multipart_parts


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


@pytest.mark.asyncio
async def test_request__non_2xx_response__returns_response_without_raising() -> None:
    """
    Scenario: Server responds with a non-2xx status code (e.g. 404).
    Expected Outcome: The transport returns the response unchanged instead of raising
        HTTPError, so endpoint methods can inspect the status code and raise the
        appropriate exception alias (see issue #344).
    """

    # Arrange
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "not found"})

    transport = httpx.MockTransport(handler)
    client = HttpxTransport(base_url="https://api.example.com")
    client._client._transport = transport

    # Act
    response = await client.request("GET", "/users/missing")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"message": "not found"}
    await client.close()


@pytest.mark.asyncio
async def test_request__redirect_response__returns_response_without_raising() -> None:
    """
    Scenario: Server responds with a 3xx status code (redirects are not followed by default).
    Expected Outcome: The transport returns the redirect response unchanged rather than raising,
        consistent with the contract that every response is returned to the caller.
    """

    # Arrange
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(301, headers={"Location": "https://api.example.com/new"})

    transport = httpx.MockTransport(handler)
    client = HttpxTransport(base_url="https://api.example.com")
    client._client._transport = transport

    # Act
    response = await client.request("GET", "/old")

    # Assert
    assert response.status_code == 301
    assert response.headers.get("Location") == "https://api.example.com/new"
    await client.close()


@pytest.mark.asyncio
async def test_request__server_error_response__returns_response_without_raising() -> None:
    """
    Scenario: Server responds with a 5xx status code.
    Expected Outcome: The transport returns the response unchanged; error handling is
        delegated to the generated endpoint methods.
    """

    # Arrange
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    transport = httpx.MockTransport(handler)
    client = HttpxTransport(base_url="https://api.example.com")
    client._client._transport = transport

    # Act
    response = await client.request("GET", "/health")

    # Assert
    assert response.status_code == 503
    assert response.text == "unavailable"
    await client.close()


def test_verify_ssl__default__ssl_verification_enabled() -> None:
    """
    Scenario: HttpxTransport created without verify_ssl parameter.
    Expected Outcome: SSL verification is enabled by default (verify=True passed to httpx).
    """
    # Arrange
    mock_client = MagicMock()

    # Act
    with patch("pyopenapi_gen.core.http_transport.httpx.AsyncClient", return_value=mock_client) as mock_async_client:
        HttpxTransport(base_url="https://api.example.com")

    # Assert
    mock_async_client.assert_called_once_with(base_url="https://api.example.com", timeout=None, verify=True)


def test_verify_ssl__disabled__ssl_verification_disabled() -> None:
    """
    Scenario: HttpxTransport created with verify_ssl=False for local development.
    Expected Outcome: SSL verification is disabled (verify=False passed to httpx).
    """
    # Arrange
    mock_client = MagicMock()

    # Act
    with patch("pyopenapi_gen.core.http_transport.httpx.AsyncClient", return_value=mock_client) as mock_async_client:
        HttpxTransport(base_url="https://api.example.com", verify_ssl=False)

    # Assert
    mock_async_client.assert_called_once_with(base_url="https://api.example.com", timeout=None, verify=False)


# ---------------------------------------------------------------------------
# Multipart handling: encode plain fields as form fields rather than file parts, keep the body
# multipart in every case, and never let a configured Content-Type override a body-derived one.
# ---------------------------------------------------------------------------


def _capturing_transport(captured: dict[str, object]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["body"] = request.read()
        return httpx.Response(201, json={"ok": True})

    return httpx.MockTransport(handler)


def test_prepare_multipart_parts__plain_strings_and_file_tuple__plain_become_filename_less_parts() -> None:
    """
    Scenario:
        A multipart dict mixes three plain string fields with one httpx file tuple.
    Expected Outcome:
        Plain fields become filename-less `(None, bytes)` parts (rendered by httpx as form fields);
        the file tuple is kept by identity so bytes are never re-encoded.
    """
    # Arrange
    binary = ("report.pdf", b"%PDF-1.4", "application/pdf")
    files = {"mimeType": "application/pdf", "filename": "report.pdf", "chatId": "chat-1", "binary": binary}

    # Act
    parts = _prepare_multipart_parts(files)

    # Assert
    assert parts == [
        ("mimeType", (None, b"application/pdf")),
        ("filename", (None, b"report.pdf")),
        ("chatId", (None, b"chat-1")),
        ("binary", binary),
    ]
    assert parts[3][1] is binary


def test_prepare_multipart_parts__bytes_bytearray_and_file_like__are_kept_as_file_parts() -> None:
    """
    Scenario:
        Values are raw bytes, a bytearray, a 2-tuple, and an object exposing .read().
    Expected Outcome:
        All are passed through untouched as file parts.
    """
    # Arrange
    import io

    raw = b"raw-bytes"
    arr = bytearray(b"arr")
    two_tuple = ("a.txt", b"abc")
    stream = io.BytesIO(b"stream")

    # Act
    parts = _prepare_multipart_parts({"raw": raw, "arr": arr, "two": two_tuple, "stream": stream})

    # Assert
    assert parts == [("raw", raw), ("arr", arr), ("two", two_tuple), ("stream", stream)]
    assert parts[3][1] is stream


def test_prepare_multipart_parts__none_values__are_omitted() -> None:
    """
    Scenario:
        An optional property was left as None by the caller.
    Expected Outcome:
        No part is emitted for it (sending "" would set the field to an empty string server-side).
    """
    # Act
    parts = _prepare_multipart_parts({"chatId": None, "binary": ("a.txt", b"x")})

    # Assert
    assert parts == [("binary", ("a.txt", b"x"))]


def test_prepare_multipart_parts__bool_int_float__use_json_style_primitives() -> None:
    """
    Scenario:
        Plain non-string primitives are supplied.
    Expected Outcome:
        Booleans become "true"/"false" (matching httpx's own form encoding); numbers are stringified.
    """
    # Act
    parts = _prepare_multipart_parts({"flag": True, "off": False, "count": 3, "ratio": 1.5})

    # Assert
    assert parts == [
        ("flag", (None, b"true")),
        ("off", (None, b"false")),
        ("count", (None, b"3")),
        ("ratio", (None, b"1.5")),
    ]


def test_prepare_multipart_parts__list_of_primitives__repeats_the_field() -> None:
    """
    Scenario:
        An array property of primitives is supplied as a list.
    Expected Outcome:
        One part per item under the same name (standard multipart array encoding).
    """
    # Act
    parts = _prepare_multipart_parts({"tags": ["a", "b"], "ids": [1, 2]})

    # Assert
    assert parts == [("tags", (None, b"a")), ("tags", (None, b"b")), ("ids", (None, b"1")), ("ids", (None, b"2"))]


def test_prepare_multipart_parts__mapping_and_dataclass__are_json_encoded_parts() -> None:
    """
    Scenario:
        An object-typed property is supplied as a dict, and another as a generated-style dataclass
        with API field-name mapping.
    Expected Outcome:
        Each becomes a single `application/json` part; the dataclass uses the API (camelCase) keys.
    """
    # Arrange
    from dataclasses import dataclass

    @dataclass
    class Meta:
        source_id: str

        class Meta:
            key_transform_with_dump = {"source_id": "sourceId"}

    # Act
    parts = _prepare_multipart_parts({"meta": {"k": 1, "nested": [1, 2]}, "typed": Meta(source_id="s-1")})

    # Assert
    assert parts == [
        ("meta", (None, b'{"k": 1, "nested": [1, 2]}', "application/json")),
        ("typed", (None, b'{"sourceId": "s-1"}', "application/json")),
    ]


def test_prepare_multipart_parts__list_of_objects__is_a_single_json_array_part() -> None:
    """
    Scenario:
        An array-of-objects property is supplied.
    Expected Outcome:
        Encoded as one `application/json` part holding the JSON array (OpenAPI default for complex parts).
    """
    # Act
    parts = _prepare_multipart_parts({"items": [{"a": 1}, {"a": 2}]})

    # Assert
    assert parts == [("items", (None, b'[{"a": 1}, {"a": 2}]', "application/json"))]


def test_prepare_multipart_parts__files_given_as_list_of_pairs__is_returned_unchanged() -> None:
    """
    Scenario:
        The caller used httpx's list-of-pairs form to upload several files under one name.
    Expected Outcome:
        The list is passed through untouched (no .items() crash, no re-shaping).
    """
    # Arrange
    pairs = [("f", ("a.txt", b"x")), ("f", ("b.txt", b"y"))]

    # Act
    result = _prepare_multipart_parts(pairs)

    # Assert
    assert result is pairs


def test_prepare_multipart_parts__unsupported_value_type__raises_type_error_naming_the_field() -> None:
    """
    Scenario:
        A value of a type that cannot be sent as a multipart part is supplied.
    Expected Outcome:
        A TypeError naming the offending field, instead of an obscure error deep inside httpx.
    """
    # Act / Assert
    with pytest.raises(TypeError, match="widget"):
        _prepare_multipart_parts({"widget": object()})


@pytest.mark.asyncio
async def test_request__multipart_with_only_plain_fields__is_still_sent_as_multipart() -> None:
    """
    Scenario:
        A multipart endpoint is called with plain fields only (e.g. the optional file was omitted).
    Expected Outcome:
        The body is still multipart/form-data, not application/x-www-form-urlencoded, so servers
        with a multipart-only body parser accept it.
    """
    # Arrange
    captured: dict[str, object] = {}
    client = HttpxTransport(base_url="https://api.example.com")
    client._client._transport = _capturing_transport(captured)

    # Act
    await client.request("POST", "/upload", files={"a": "1", "b": "2"})
    await client.close()

    # Assert
    headers = typing.cast(dict[str, str], captured["headers"])
    body = typing.cast(bytes, captured["body"])
    assert headers["content-type"].startswith("multipart/form-data; boundary=")
    assert b'name="a"\r\n\r\n1' in body
    assert b'name="b"\r\n\r\n2' in body


@pytest.mark.asyncio
async def test_request__multipart_with_separate_data_dict__both_reach_the_body() -> None:
    """
    Scenario:
        A caller passes both `files=` and a separate `data=` dict.
    Expected Outcome:
        Existing data fields and the multipart parts all appear in the multipart body.
    """
    # Arrange
    captured: dict[str, object] = {}
    client = HttpxTransport(base_url="https://api.example.com")
    client._client._transport = _capturing_transport(captured)

    # Act
    await client.request("POST", "/upload", data={"existing": "yes"}, files={"binary": ("a.txt", b"abc"), "note": "hi"})
    await client.close()

    # Assert
    body = typing.cast(bytes, captured["body"])
    assert b'name="existing"\r\n\r\nyes' in body
    assert b'name="note"\r\n\r\nhi' in body
    assert b'name="binary"; filename="a.txt"' in body


@pytest.mark.asyncio
async def test_request__form_urlencoded_with_default_json_content_type__drops_default_content_type() -> None:
    """
    Scenario:
        A generated application/x-www-form-urlencoded endpoint sends `data=<dict>` through a transport
        whose default headers carry Content-Type: application/json.
    Expected Outcome:
        httpx's body-derived urlencoded Content-Type wins (same defect class as the multipart case).
    """
    # Arrange
    captured: dict[str, object] = {}
    client = HttpxTransport(
        base_url="https://api.example.com",
        default_headers={"Content-Type": "application/json", "x-my-token": "t"},
    )
    client._client._transport = _capturing_transport(captured)

    # Act
    await client.request("POST", "/form", data={"a": "1"})
    await client.close()

    # Assert
    headers = typing.cast(dict[str, str], captured["headers"])
    assert headers["content-type"] == "application/x-www-form-urlencoded"
    assert headers["x-my-token"] == "t"
    assert captured["body"] == b"a=1"


@pytest.mark.asyncio
async def test_request__raw_bytes_body_with_default_content_type__keeps_default_content_type() -> None:
    """
    Scenario:
        A raw bytes body (e.g. application/octet-stream) is sent via `content=` with a default Content-Type.
    Expected Outcome:
        httpx derives nothing for raw bytes, so the caller-configured Content-Type must be kept.
    """
    # Arrange
    captured: dict[str, object] = {}
    client = HttpxTransport(
        base_url="https://api.example.com",
        default_headers={"Content-Type": "application/octet-stream"},
    )
    client._client._transport = _capturing_transport(captured)

    # Act
    await client.request("POST", "/blob", content=b"raw")
    await client.close()

    # Assert
    headers = typing.cast(dict[str, str], captured["headers"])
    assert headers["content-type"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_request__mixed_multipart_files__plain_fields_are_sent_as_form_fields_not_file_parts() -> None:
    """
    Scenario:
        A request carries a `files` dict mixing plain string fields with a real file tuple.
    Expected Outcome:
        httpx encodes the plain fields as form fields (no synthetic filename) and the tuple as a file part.
    """
    # Arrange
    captured: dict[str, object] = {}
    client = HttpxTransport(base_url="https://api.example.com")
    client._client._transport = _capturing_transport(captured)

    # Act
    await client.request(
        "POST",
        "/upload",
        files={"mimeType": "application/pdf", "binary": ("report.pdf", b"%PDF-1.4 body", "application/pdf")},
    )
    await client.close()

    # Assert
    body = typing.cast(bytes, captured["body"])
    headers = typing.cast(dict[str, str], captured["headers"])
    assert headers["content-type"].startswith("multipart/form-data; boundary=")
    assert b'name="mimeType"\r\n\r\napplication/pdf' in body
    assert b'filename="upload"' not in body
    assert b'name="binary"; filename="report.pdf"' in body
    assert b"%PDF-1.4 body" in body


@pytest.mark.asyncio
async def test_request__multipart_with_default_content_type__drops_content_type_and_keeps_other_defaults() -> None:
    """
    Scenario:
        The transport was built with default_headers containing Content-Type: application/json,
        and a request carries `files=`.
    Expected Outcome:
        httpx computes its own multipart boundary header; the other default header is still sent.
    """
    # Arrange
    captured: dict[str, object] = {}
    client = HttpxTransport(
        base_url="https://api.example.com",
        default_headers={"Content-Type": "application/json", "x-my-token": "t"},
    )
    client._client._transport = _capturing_transport(captured)

    # Act
    await client.request("POST", "/upload", files={"binary": ("report.pdf", b"data", "application/pdf")})
    await client.close()

    # Assert
    headers = typing.cast(dict[str, str], captured["headers"])
    assert headers["content-type"].startswith("multipart/form-data; boundary=")
    assert headers["x-my-token"] == "t"


@pytest.mark.asyncio
async def test_request__multipart_with_per_call_content_type__drops_it_too() -> None:
    """
    Scenario:
        A per-request headers= override supplies content-type (odd casing) on a multipart request.
    Expected Outcome:
        It is dropped so httpx can set the boundary header.
    """
    # Arrange
    captured: dict[str, object] = {}
    client = HttpxTransport(base_url="https://api.example.com")
    client._client._transport = _capturing_transport(captured)

    # Act
    await client.request(
        "POST",
        "/upload",
        headers={"CONTENT-TYPE": "application/json", "x-req": "1"},
        files={"binary": ("report.pdf", b"data", "application/pdf")},
    )
    await client.close()

    # Assert
    headers = typing.cast(dict[str, str], captured["headers"])
    assert headers["content-type"].startswith("multipart/form-data; boundary=")
    assert headers["x-req"] == "1"


@pytest.mark.asyncio
async def test_request__plain_json_with_default_content_type__keeps_default_content_type() -> None:
    """
    Scenario:
        Same transport defaults, but the request has no `files` kwarg.
    Expected Outcome:
        The default Content-Type is still sent (fix stays scoped to multipart).
    """
    # Arrange
    captured: dict[str, object] = {}
    client = HttpxTransport(
        base_url="https://api.example.com",
        default_headers={"Content-Type": "application/json", "x-my-token": "t"},
    )
    client._client._transport = _capturing_transport(captured)

    # Act
    await client.request("POST", "/items", json={"a": 1})
    await client.close()

    # Assert
    headers = typing.cast(dict[str, str], captured["headers"])
    assert headers["content-type"] == "application/json"
    assert headers["x-my-token"] == "t"
