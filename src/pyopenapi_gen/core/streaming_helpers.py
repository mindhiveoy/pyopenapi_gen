import json
from typing import Any, AsyncIterator, List, Optional

import httpx


class SSEEvent:
    def __init__(
        self, data: str, event: Optional[str] = None, id: Optional[str] = None, retry: Optional[int] = None
    ) -> None:
        self.data: str = data
        self.event: Optional[str] = event
        self.id: Optional[str] = id
        self.retry: Optional[int] = retry

    def __repr__(self) -> str:
        return f"SSEEvent(data={self.data!r}, event={self.event!r}, id={self.id!r}, retry={self.retry!r})"


async def iter_bytes(response: httpx.Response) -> AsyncIterator[bytes]:
    async for chunk in response.aiter_bytes():
        yield chunk


async def iter_ndjson(response: httpx.Response) -> AsyncIterator[Any]:
    async for line in response.aiter_lines():
        line = line.strip()
        if line:
            yield json.loads(line)


async def iter_sse(response: httpx.Response) -> AsyncIterator[SSEEvent]:
    """Parse Server-Sent Events (SSE) from a streaming response."""
    event_lines: list[str] = []
    async for line in response.aiter_lines():
        if line == "":
            # End of event
            if event_lines:
                event = _parse_sse_event(event_lines)
                if event:
                    yield event
                event_lines = []
        else:
            event_lines.append(line)
    # Last event (if any)
    if event_lines:
        event = _parse_sse_event(event_lines)
        if event:
            yield event


def _parse_sse_event(lines: List[str]) -> SSEEvent:
    data = []
    event = None
    id = None
    retry = None
    for line in lines:
        if line.startswith(":"):
            continue  # comment
        if ":" in line:
            field, value = line.split(":", 1)
            value = value.lstrip()
            if field == "data":
                data.append(value)
            elif field == "event":
                event = value
            elif field == "id":
                id = value
            elif field == "retry":
                try:
                    retry = int(value)
                except ValueError:
                    pass
    return SSEEvent(data="\n".join(data), event=event, id=id, retry=retry)


async def iter_sse_events_text(response: httpx.Response) -> AsyncIterator[str]:
    """
    Parses a Server-Sent Events (SSE) stream and yields the `data` field content
    as a string for each event.
    This is specifically for cases where the event data is expected to be a
    single text payload (e.g., a JSON string) per event.
    """
    async for sse_event in iter_sse(response):
        if sse_event.data:  # Ensure data is not empty
            yield sse_event.data
