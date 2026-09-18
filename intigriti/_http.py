"""Async HTTP transport for the Intigriti researcher API.

Wraps :mod:`httpx` with the base URL, version prefix, bearer authentication, JSON
decoding and error mapping the API expects. This module is private: its interface
may change between releases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import httpx

if TYPE_CHECKING:
    from types import TracebackType

from intigriti.exceptions import IntigritiAPIError, error_for_status

DEFAULT_BASE_URL = 'https://api.intigriti.com/external/researcher'
DEFAULT_API_VERSION = 'v1'
DEFAULT_TIMEOUT = 30.0
DEFAULT_USER_AGENT = 'intigriti.py'


class AsyncHTTPClient:
    """Thin async wrapper around :class:`httpx.AsyncClient`.

    Centralises base-URL resolution, versioning, authentication, JSON decoding and
    error mapping, so callers deal only with endpoint paths and decoded payloads.
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
                closed by this wrapper, and it must carry its own base URL and headers.
        """
        if not token:
            msg = 'A personal access token is required; generate one from your Intigriti account settings.'
            raise ValueError(msg)
        self._api_version = api_version.strip('/')
        self._base_url = base_url.rstrip('/').removesuffix(f'/{self._api_version}')
        self._token = token
        self._owns_client = client is None
        headers = {
            'Accept': 'application/json',
            'User-Agent': user_agent,
            'Authorization': f'Bearer {token}',
        }
        self._client = client or httpx.AsyncClient(
            base_url=self._api_root(),
            headers=headers,
            timeout=timeout,
            verify=verify,
        )

    def _api_root(self) -> str:
        return f'{self._base_url}/{self._api_version}'

    @property
    def base_url(self) -> str:
        """Root URL of the API, without the version segment."""
        return self._base_url

    @property
    def api_root(self) -> str:
        """Root URL of the API version in use, e.g. ``https://api.intigriti.com/external/researcher/v1``."""
        return self._api_root()

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
        """Close the underlying httpx client, unless the caller supplied their own."""
        if self._owns_client:
            await self._client.aclose()

    async def request(  # noqa: PLR0913
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Send a request to the API and return the raw response.

        Args:
            method: HTTP verb.
            path: Path relative to the API root, e.g. ``/programs``, or an absolute URL.
            params: Query parameters; ``None`` values are dropped.
            json: Request body, serialised as JSON.
            data: Form-encoded request body.
            files: Multipart payload.
            headers: Extra headers, merged over the client defaults.

        Raises:
            IntigritiAPIError: The API answered with a 4xx or 5xx status.
        """
        response = await self._client.request(
            method,
            path,
            params=_clean_params(params),
            json=json,
            data=data,
            files=files,
            headers=headers,
        )
        _raise_for_status(response)
        return response

    async def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Send a GET request to ``path`` and return the decoded body, or ``None`` when empty."""
        response = await self.request('GET', path, params=params)
        return _decode_json(response)

    async def post_json(
        self,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send a POST request to ``path`` with ``json`` as body and return the decoded body."""
        response = await self.request('POST', path, json=json, params=params)
        return _decode_json(response)

    async def patch_json(
        self,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send a PATCH request to ``path`` with ``json`` as body and return the decoded body."""
        response = await self.request('PATCH', path, json=json, params=params)
        return _decode_json(response)

    async def delete_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Send a DELETE request to ``path`` and return the decoded body, or ``None`` when empty."""
        response = await self.request('DELETE', path, params=params)
        return _decode_json(response)

    async def put_json(
        self,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send a PUT request to ``path`` with ``json`` as body and return the decoded body."""
        response = await self.request('PUT', path, json=json, params=params)
        return _decode_json(response)

    async def get_bytes(self, url: str) -> bytes:
        """Fetch raw bytes from an absolute URL (e.g. a rules-of-engagement attachment).

        Absolute URLs bypass the versioned base prefix configured on the underlying
        httpx client. Attachments are served from a different host than the API, so
        the ``Authorization`` header is dropped for off-host URLs: the personal access
        token must never leak to a third-party storage provider.
        """
        request = self._client.build_request('GET', url)
        if request.url.host != self._client.base_url.host:
            request.headers.pop('authorization', None)
        response = await self._client.send(request, follow_redirects=True)
        _raise_for_status(response)
        return response.content


def _clean_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if not params:
        return None
    return {k: v for k, v in params.items() if v is not None}


def _decode_json(response: httpx.Response) -> Any:
    if not response.content:
        return None
    return response.json()


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code >= httpx.codes.BAD_REQUEST:
        raise _exception_from_response(response)


def _retry_after(response: httpx.Response) -> float | None:
    """Read ``Retry-After`` as a delay in seconds; the HTTP-date form is ignored."""
    raw = response.headers.get('retry-after')
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _exception_from_response(response: httpx.Response) -> IntigritiAPIError:
    """Build the exception matching an error response, reading the API fault contract."""
    payload: Any = None
    message = ''
    code = ''
    identifier = ''
    extra_parameters: dict[str, Any] = {}
    try:
        payload = response.json()
    except ValueError:
        message = response.text
    else:
        if isinstance(payload, dict):
            message = str(payload.get('title') or payload.get('detail') or payload.get('message') or '')
            code = str(payload.get('code') or '')
            identifier = str(payload.get('identifier') or '')
            raw_extra = payload.get('extraParameters')
            if isinstance(raw_extra, dict):
                extra_parameters = raw_extra
    return error_for_status(
        status_code=response.status_code,
        message=message,
        code=code,
        identifier=identifier,
        extra_parameters=extra_parameters,
        payload=payload,
        retry_after=_retry_after(response),
    )
