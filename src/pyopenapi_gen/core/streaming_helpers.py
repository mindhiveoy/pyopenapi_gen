import json
from typing import AsyncIterator, Any

import httpx


class SSEEvent:
    def __init__(self, data: str, event: str = None, id: str = None, retry: int = None):
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry

    def __repr__(self):
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
    event_lines = []
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


def _parse_sse_event(lines: list[str]) -> SSEEvent:
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
