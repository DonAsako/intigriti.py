"""The public entry point of the library."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from intigriti._http import (
    DEFAULT_API_VERSION,
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    AsyncHTTPClient,
)
from intigriti.resources import Payouts, Programs

if TYPE_CHECKING:
    from types import TracebackType

    import httpx


class Client:
    """Async client for the Intigriti researcher API.

    Use it as a context manager so the underlying connection pool is closed::

        async with intigriti.Client(token) as client:
            page = await client.programs.list()

    """

    def __init__(  # noqa: PLR0913
        self,
        token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        api_version: str = DEFAULT_API_VERSION,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        verify: bool = True,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Build a client for the Intigriti researcher API.

        Args:
            token: Personal access token, generated from your Intigriti account settings.
            base_url: API root, with or without the trailing version segment.
            api_version: Version segment appended to the base URL; the API requires one.
            timeout: Per-request timeout, in seconds.
            user_agent: Value sent in the ``User-Agent`` header.
            verify: Whether to verify TLS certificates.
            client: Pre-built httpx client to use instead of an owned one. It is never
                closed by this client, and it must carry its own base URL and headers.

        Raises:
            ValueError: ``token`` is empty.
        """
        self._http = AsyncHTTPClient(
            token,
            base_url=base_url,
            api_version=api_version,
            timeout=timeout,
            user_agent=user_agent,
            verify=verify,
            client=client,
        )
        self.programs = Programs(self._http)
        self.payouts = Payouts(self._http)

    @property
    def api_root(self) -> str:
        """Root URL built from ``base_url`` and ``api_version``.

        An injected httpx client carries its own base URL, which this does not reflect.
        """
        return self._http.api_root

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying connection pool, unless the caller supplied their own client."""
        await self._http.aclose()
