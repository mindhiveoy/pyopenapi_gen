import asyncio
from pyopenapi_gen.core.streaming_helpers import (
    SSEEvent,
    iter_bytes,
    iter_ndjson,
    iter_sse,
    _parse_sse_event,
)
from unittest.mock import AsyncMock, MagicMock
import httpx


def test_sse_event__repr__outputs_expected():
    """
    Scenario:
        Construct an SSEEvent and check its __repr__ output.
    Expected Outcome:
        __repr__ returns a string with all fields present.
    """
    event = SSEEvent(data="foo", event="bar", id="baz", retry=123)
    r = repr(event)
    assert "SSEEvent(" in r and "foo" in r and "bar" in r and "baz" in r and "123" in r


def test_iter_bytes__yields_chunks():
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
    async def aiter():
        for c in chunks:
            yield c

    response.aiter_bytes = aiter
    out = []

    async def run():
        async for chunk in iter_bytes(response):
            out.append(chunk)

    asyncio.run(run())
    assert out == chunks


def test_iter_ndjson__yields_json_objects():
    """
    Scenario:
        iter_ndjson yields parsed JSON objects from each non-empty line.
    Expected Outcome:
        All JSON objects are yielded in order.
    """
    lines = [' {"a": 1} ', "", '{"b": 2}']
    response = MagicMock(spec=httpx.Response)

    async def aiter_lines():
        for l in lines:
            yield l

    response.aiter_lines = aiter_lines
    out = []

    async def run():
        async for obj in iter_ndjson(response):
            out.append(obj)

    asyncio.run(run())
    assert out == [{"a": 1}, {"b": 2}]


def test_iter_sse__yields_events():
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

    async def aiter_lines():
        for l in lines:
            yield l

    response.aiter_lines = aiter_lines
    out = []

    async def run():
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


def test_parse_sse_event__parses_fields():
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


def test_parse_sse_event__handles_missing_fields():
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
