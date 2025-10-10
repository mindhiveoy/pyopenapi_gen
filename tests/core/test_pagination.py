"""
Tests for the pagination module that provides utilities for paginated API endpoints.
"""

from typing import Any, List
from unittest.mock import AsyncMock

import pytest

from pyopenapi_gen.core.pagination import paginate_by_next


@pytest.mark.asyncio
async def test_paginate_by_next__iterates_through_single_page() -> None:
    """
    Scenario:
        paginate_by_next iterates through a single page of items
    Expected Outcome:
        All items from the single page are yielded
    """
    # Mock a fetch_page function that returns a single page
    items = [{"id": 1}, {"id": 2}, {"id": 3}]
    mock_fetch = AsyncMock(return_value={"items": items, "next": None})

    # Use the paginate_by_next function with the mock
    collected_items: List[dict[str, Any]] = []
    async for item in paginate_by_next(mock_fetch, items_key="items", next_key="next"):
        collected_items.append(item)

    # Verify results
    assert collected_items == items
    mock_fetch.assert_called_once_with()


@pytest.mark.asyncio
async def test_paginate_by_next__iterates_through_multiple_pages() -> None:
    """
    Scenario:
        paginate_by_next iterates through multiple pages of items
    Expected Outcome:
        All items from all pages are yielded in order
    """
    # Create a side effect function that simulates pagination
    pages = [
        {"items": [{"id": 1}, {"id": 2}], "next": "page2"},
        {"items": [{"id": 3}, {"id": 4}], "next": "page3"},
        {"items": [{"id": 5}, {"id": 6}], "next": None},
    ]
    page_index = 0

    async def fetch_page_side_effect(**kwargs: Any) -> dict[str, Any]:
        nonlocal page_index
        next_token = kwargs.get("next")
        if page_index == 0:
            assert next_token is None
        else:
            assert next_token == f"page{page_index + 1}"
        result = pages[page_index]
        page_index += 1
        return result

    mock_fetch = AsyncMock(side_effect=fetch_page_side_effect)

    # Use the paginate_by_next function with the mock
    collected_items: List[dict[str, Any]] = []
    async for item in paginate_by_next(mock_fetch, items_key="items", next_key="next"):
        collected_items.append(item)

    # Verify results
    assert collected_items == [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}, {"id": 6}]
    assert mock_fetch.call_count == 3


@pytest.mark.asyncio
async def test_paginate_by_next__empty_page_returns_empty_iterator() -> None:
    """
    Scenario:
        paginate_by_next receives an empty page
    Expected Outcome:
        Empty iterator without errors
    """
    mock_fetch = AsyncMock(return_value={"items": [], "next": None})

    # Use the paginate_by_next function with the mock
    collected_items: List[dict[str, Any]] = []
    async for item in paginate_by_next(mock_fetch):
        collected_items.append(item)

    # Verify results
    assert collected_items == []
    mock_fetch.assert_called_once_with()


@pytest.mark.asyncio
async def test_paginate_by_next__with_custom_key_names() -> None:
    """
    Scenario:
        paginate_by_next uses custom key names for items and next token
    Expected Outcome:
        Iterator correctly reads from custom keys
    """
    # Mock a fetch_page function that uses custom keys
    items = [{"id": 1}, {"id": 2}]
    mock_fetch = AsyncMock(return_value={"data": items, "page_token": None})

    # Use the paginate_by_next function with custom key names
    collected_items: List[dict[str, Any]] = []
    async for item in paginate_by_next(mock_fetch, items_key="data", next_key="page_token"):
        collected_items.append(item)

    # Verify results
    assert collected_items == items
    mock_fetch.assert_called_once_with()


@pytest.mark.asyncio
async def test_paginate_by_next__passes_parameters_to_fetch_function() -> None:
    """
    Scenario:
        paginate_by_next passes additional parameters to the fetch function
    Expected Outcome:
        Parameters are correctly passed through
    """
    mock_fetch = AsyncMock(return_value={"items": [{"id": 1}], "next": None})

    # Use the paginate_by_next function with additional parameters
    async for _ in paginate_by_next(mock_fetch, limit=10, order_by="name"):
        pass

    # Verify results
    mock_fetch.assert_called_once_with(limit=10, order_by="name")


@pytest.mark.asyncio
async def test_paginate_by_next__updates_next_token_between_calls() -> None:
    """
    Scenario:
        paginate_by_next updates the next token for subsequent calls
    Expected Outcome:
        Next token is updated correctly between calls
    """
    # Create a sequence of pages with next tokens
    pages = [
        {"items": [{"id": 1}], "next": "token1"},
        {"items": [{"id": 2}], "next": "token2"},
        {"items": [{"id": 3}], "next": None},
    ]

    # Track the calls to verify parameters
    calls: List[dict[str, Any]] = []

    async def fetch_page_side_effect(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs.copy())
        if len(calls) == 1:
            return pages[0]
        elif len(calls) == 2:
            return pages[1]
        else:
            return pages[2]

    mock_fetch = AsyncMock(side_effect=fetch_page_side_effect)

    # Use the paginate_by_next function
    collected_items: List[dict[str, Any]] = []
    async for item in paginate_by_next(mock_fetch):
        collected_items.append(item)

    # Verify call parameters
    assert len(calls) == 3
    assert calls[0] == {}  # First call has no next token
    assert calls[1] == {"next": "token1"}  # Second call has next token from first page
    assert calls[2] == {"next": "token2"}  # Third call has next token from second page


@pytest.mark.asyncio
async def test_paginate_by_next__missing_items_key_returns_empty_list() -> None:
    """
    Scenario:
        paginate_by_next receives response without the items key
    Expected Outcome:
        Treats as empty list without errors
    """
    mock_fetch = AsyncMock(return_value={"meta": {}, "next": None})  # No items key

    # Use the paginate_by_next function
    collected_items: List[dict[str, Any]] = []
    async for item in paginate_by_next(mock_fetch):
        collected_items.append(item)

    # Verify results
    assert collected_items == []
    mock_fetch.assert_called_once_with()


def test_paginate_by_next__returns_async_iterator() -> None:
    """
    Scenario:
        Check that paginate_by_next returns an async iterator
    Expected Outcome:
        The return value can be used with async for
    """
    mock_fetch = AsyncMock(return_value={"items": [], "next": None})

    # Get the iterator but don't run it
    iterator = paginate_by_next(mock_fetch)

    # Verify it has the expected async iterator methods
    assert hasattr(iterator, "__aiter__")
    assert hasattr(iterator, "__anext__")
