"""Walking the API's ``limit``/``offset`` collections."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable

    from intigriti.models import Page

DEFAULT_PAGE_SIZE = 50
"""Number of records the API returns when ``limit`` is omitted."""

MAX_PAGE_SIZE = 500
"""Largest ``limit`` the API accepts."""


async def iterate_records[ItemT](
    fetch: Callable[[int, int], Awaitable[Page[ItemT]]],
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> AsyncIterator[ItemT]:
    """Yield every record of a paginated collection, one request at a time.

    Args:
        fetch: Coroutine called as ``fetch(limit, offset)`` to retrieve one page.
        page_size: Records per request, between 1 and :data:`MAX_PAGE_SIZE`.

    Yields:
        Each record, in the order the API returns them.

    Raises:
        ValueError: ``page_size`` falls outside the range the API accepts.
    """
    if not 1 <= page_size <= MAX_PAGE_SIZE:
        msg = f'page_size must be between 1 and {MAX_PAGE_SIZE}, got {page_size}'
        raise ValueError(msg)

    offset = 0
    while True:
        page = await fetch(page_size, offset)
        for record in page.records:
            yield record
        offset += len(page.records)
        # A short page is the last one, and an empty page guards against a max_count
        # that would otherwise keep us requesting forever.
        if not page.records or len(page.records) < page_size or offset >= page.max_count:
            return
