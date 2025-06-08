"""
Pagination utilities for handling paginated API endpoints.

This module provides functions for working with paginated API responses,
turning them into convenient async iterators that automatically handle
fetching subsequent pages.
"""

from typing import Any, AsyncIterator, Awaitable, Callable, Dict


def paginate_by_next(
    fetch_page: Callable[..., Awaitable[Dict[str, Any]]],
    items_key: str = "items",
    next_key: str = "next",
    **params: Any,
) -> AsyncIterator[Any]:
    """
    Create an async iterator that yields items from paginated API responses.

    This function creates a paginator that automatically handles fetching
    subsequent pages of results by using a "next page token" pattern. It calls
    the provided `fetch_page` function repeatedly with the given parameters,
    updating the next token parameter between calls.

    Args:
        fetch_page: Async function to fetch a page of results
        items_key: The key in the response dict where items are located (default: "items")
        next_key: The key in the response dict for the next page token (default: "next")
        **params: Initial parameters to pass to fetch_page

    Returns:
        An AsyncIterator that yields individual items from all pages

    Example:
        ```python
        async def fetch_users_page(page_token=None, limit=100):
            url = f"/users?limit={limit}"
            if page_token:
                url += f"&page_token={page_token}"
            return await http_client.get(url)

        async for user in paginate_by_next(fetch_users_page,
                                          items_key="users",
                                          next_key="page_token",
                                          limit=50):
            print(user["name"])
        ```
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
