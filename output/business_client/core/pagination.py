from typing import AsyncIterator, Callable, Any, Dict, Awaitable


def paginate_by_next(
    fetch_page: Callable[..., Awaitable[Dict[str, Any]]],
    items_key: str = "items",
    next_key: str = "next",
    **params: Any,
) -> AsyncIterator[Any]:
    """
    Generic asynchronous paginator.

    Calls `fetch_page(**params)` repeatedly, yielding each element in the returned mapping under `items_key`.
    Uses mapping[next_key] to retrieve the token for the next page. Stops when no token is provided.
    """

    async def _paginate() -> AsyncIterator[Any]:
        while True:
            result = await fetch_page(**params)
            # result is expected to be a dict
            # (assumed since fetch_page is typed to return Dict[str, Any])
            items = result.get(items_key, [])
            for item in items:
                yield item
            token = result.get(next_key)
            if not token:
                break
            params[next_key] = token

    return _paginate()
