import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import httpx

from pyopenapi_gen.core.streaming_helpers import (
    DEFAULT_SSE_DONE_SENTINEL,
    SSEEvent,
    _parse_sse_event,
    iter_bytes,
    iter_ndjson,
    iter_sse,
    iter_sse_events_text,
)


def test_sse_event__repr__outputs_expected() -> None:
    """
    Scenario:
        Construct an SSEEvent and check its __repr__ output.
    Expected Outcome:
        __repr__ returns a string with all fields present.
    """
    event = SSEEvent(data="foo", event="bar", id="baz", retry=123)
    r = repr(event)
    assert "SSEEvent(" in r and "foo" in r and "bar" in r and "baz" in r and "123" in r


def test_iter_bytes__yields_chunks() -> None:
    """
    Scenario:
        iter_bytes yields all byte chunks from a streaming response.
    Expected Outcome:
        All chunks are yielded in order.
    """
    chunks = [b"a", b"b", b"c"]
    response = MagicMock(spec=httpx.Response)
    response.aiter_bytes = AsyncMock(return_value=iter(chunks))

    # Patch aiter_bytes to be async iterable
    async def aiter() -> AsyncGenerator[bytes, None]:
        for c in chunks:
            yield c

    response.aiter_bytes = aiter
    out = []

    async def run() -> None:
        async for chunk in iter_bytes(response):
            out.append(chunk)

    asyncio.run(run())
    assert out == chunks


def test_iter_ndjson__yields_json_objects() -> None:
    """
    Scenario:
        iter_ndjson yields parsed JSON objects from each non-empty line.
    Expected Outcome:
        All JSON objects are yielded in order.
    """
    lines = [' {"a": 1} ', "", '{"b": 2}']
    response = MagicMock(spec=httpx.Response)

    async def aiter_lines() -> AsyncGenerator[str, None]:
        for line in lines:
            yield line

    response.aiter_lines = aiter_lines
    out = []

    async def run() -> None:
        async for obj in iter_ndjson(response):
            out.append(obj)

    asyncio.run(run())
    assert out == [{"a": 1}, {"b": 2}]


def test_iter_sse__yields_events() -> None:
    """
    Scenario:
        iter_sse yields SSEEvent objects for each event in the stream.
    Expected Outcome:
        All events are yielded in order, with correct fields.
    """
    # Simulate two events
    lines = [
        "data: foo",
        "event: bar",
        "id: 1",
        "",  # first event
        "data: baz",
        "id: 2",
        "retry: 100",
        "",  # second event
    ]
    response = MagicMock(spec=httpx.Response)

    async def aiter_lines() -> AsyncGenerator[str, None]:
        for line in lines:
            yield line

    response.aiter_lines = aiter_lines
    out = []

    async def run() -> None:
        async for event in iter_sse(response):
            out.append(event)

    asyncio.run(run())
    assert len(out) == 2
    assert out[0].data == "foo"
    assert out[0].event == "bar"
    assert out[0].id == "1"
    assert out[1].data == "baz"
    assert out[1].id == "2"
    assert out[1].retry == 100


def test_parse_sse_event__parses_fields() -> None:
    """
    Scenario:
        _parse_sse_event parses all SSE fields from lines.
    Expected Outcome:
        SSEEvent fields are set correctly.
    """
    lines = [
        "data: hello",
        "event: update",
        "id: 42",
        "retry: 500",
        ": this is a comment",
    ]
    event = _parse_sse_event(lines)
    assert event.data == "hello"
    assert event.event == "update"
    assert event.id == "42"
    assert event.retry == 500


def test_parse_sse_event__handles_missing_fields() -> None:
    """
    Scenario:
        _parse_sse_event handles missing optional fields.
    Expected Outcome:
        Only present fields are set; others are None.
    """
    lines = ["data: x"]
    event = _parse_sse_event(lines)
    assert event.data == "x"
    assert event.event is None
    assert event.id is None
    assert event.retry is None


def _fake_line_response(lines: list[str]) -> httpx.Response:
    """Build a response double whose aiter_lines() replays the given SSE lines."""
    response = MagicMock(spec=httpx.Response)

    async def aiter_lines() -> AsyncGenerator[str, None]:
        for line in lines:
            yield line

    response.aiter_lines = aiter_lines
    return response


def _collect_sse_text(response: httpx.Response, done_sentinel: str | None = DEFAULT_SSE_DONE_SENTINEL) -> list[str]:
    out: list[str] = []

    async def run() -> None:
        async for chunk in iter_sse_events_text(response, done_sentinel=done_sentinel):
            out.append(chunk)

    asyncio.run(run())
    return out


def test_iter_sse_events_text__done_sentinel__stops_cleanly_without_yielding_it() -> None:
    """
    Scenario:
        A stream sends two JSON payloads, a keep-alive comment, then the `data: [DONE]` sentinel.
    Expected Outcome:
        Exactly the two real payloads are yielded; the sentinel ends iteration and is never yielded.
    """
    # Arrange
    response = _fake_line_response(
        [
            'data: {"type": "STREAM_DATA", "data": {"content": "Hello"}}',
            "",
            ": keep-alive",
            "",
            'data: {"type": "STREAM_DATA", "data": {"content": " world"}}',
            "",
            "data: [DONE]",
            "",
            'data: {"type": "SHOULD_NOT_BE_SEEN"}',
            "",
        ]
    )

    # Act
    out = _collect_sse_text(response)

    # Assert
    assert out == [
        '{"type": "STREAM_DATA", "data": {"content": "Hello"}}',
        '{"type": "STREAM_DATA", "data": {"content": " world"}}',
    ]


def test_iter_sse_events_text__no_sentinel_in_stream__yields_all_events() -> None:
    """
    Scenario:
        A stream never sends the termination sentinel.
    Expected Outcome:
        Every payload is yielded (guards against over-eager filtering).
    """
    # Arrange
    response = _fake_line_response(['data: {"a": 1}', "", 'data: {"b": 2}', "", 'data: {"c": 3}'])

    # Act
    out = _collect_sse_text(response)

    # Assert
    assert out == ['{"a": 1}', '{"b": 2}', '{"c": 3}']


def test_iter_sse_events_text__custom_sentinel__stops_on_custom_value_only() -> None:
    """
    Scenario:
        The caller declares a non-default termination sentinel.
    Expected Outcome:
        The default `[DONE]` literal is treated as a normal payload; the custom sentinel ends the stream.
    """
    # Arrange
    response = _fake_line_response(["data: [DONE]", "", "data: <<END>>", "", 'data: {"x": 1}', ""])

    # Act
    out = _collect_sse_text(response, done_sentinel="<<END>>")

    # Assert
    assert out == ["[DONE]"]


def test_iter_sse_events_text__sentinel_disabled__yields_done_literal() -> None:
    """
    Scenario:
        The caller disables sentinel detection with done_sentinel=None.
    Expected Outcome:
        `[DONE]` is yielded like any other payload.
    """
    # Arrange
    response = _fake_line_response(['data: {"x": 1}', "", "data: [DONE]", ""])

    # Act
    out = _collect_sse_text(response, done_sentinel=None)

    # Assert
    assert out == ['{"x": 1}', "[DONE]"]


def test_iter_sse_events_text__sentinel_is_last_line_without_trailing_blank__stops_cleanly() -> None:
    """
    Scenario:
        The connection closes right after `data: [DONE]` with no terminating blank line.
    Expected Outcome:
        The sentinel is still recognised via the last-event path and not yielded.
    """
    # Arrange
    response = _fake_line_response(['data: {"a": 1}', "", "data: [DONE]"])

    # Act
    out = _collect_sse_text(response)

    # Assert
    assert out == ['{"a": 1}']


def test_iter_sse_events_text__sentinel_with_surrounding_whitespace__still_recognised() -> None:
    """
    Scenario:
        A server emits `data: [DONE] ` with trailing whitespace (or a stray carriage return).
    Expected Outcome:
        Whitespace-only differences do not defeat sentinel detection.
    """
    # Arrange
    response = _fake_line_response(['data: {"a": 1}', "", "data: [DONE] \r", ""])

    # Act
    out = _collect_sse_text(response)

    # Assert
    assert out == ['{"a": 1}']


def test_iter_sse_events_text__sentinel_with_event_field__stops_cleanly() -> None:
    """
    Scenario:
        The terminating event also carries `event:` and `id:` fields.
    Expected Outcome:
        Only the data field matters for sentinel detection.
    """
    # Arrange
    response = _fake_line_response(['data: {"a": 1}', "", "event: done", "id: 42", "data: [DONE]", ""])

    # Act
    out = _collect_sse_text(response)

    # Assert
    assert out == ['{"a": 1}']
